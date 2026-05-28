from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any


TRAINING_DIR = Path(__file__).resolve().parent / "training"
LIVE_ACTION_CONTRACT_PATH = TRAINING_DIR / "qwen_live_action_contract.json"

REQUIRED_FIELDS = ("action_id", "slots", "memory_updates", "uncertainty", "say")
OPTIONAL_FIELDS = ("needs_facts", "blocked_routes", "replan_reason", "emotion_hint", "confidence")
RAW_URL_RE = re.compile(r"https?://\S+", re.I)
INTERNAL_LANGUAGE_RE = re.compile(
    r"\b(semantic|schema|intent classifier|verifier|policy|route|classification|confidence score)\b|"
    r"not confident enough to classify",
    re.I,
)
SIDE_EFFECT_RE = re.compile(
    r"\b(sent|emailed|created|booked|scheduled|updated|logged|bought|purchased|submitted)\b"
    r".{0,56}\b(email|calendar|invite|crm|hubspot|salesforce|ticket|record|purchase|order|tts|audio)\b",
    re.I,
)
UNSUPPORTED_ABSOLUTE_RE = re.compile(
    r"\b(guarantee|guaranteed|unlimited access|always gives|every newest model|100%|"
    r"will definitely|automatically upgrades|no limits)\b",
    re.I,
)
PRODUCT_TERMS_RE = re.compile(r"\b(chatgpt|free|plus|pro|business|enterprise|plan|plans|price|cost)\b", re.I)
FACTUAL_VERB_RE = re.compile(r"\b(is|are|has|have|includes|offers|costs|gives|supports|lets|allows)\b", re.I)
TEAM_LANGUAGE_RE = re.compile(r"\b(your team|for the team|team plan|business workspace|team workspace)\b", re.I)


@dataclass(frozen=True)
class LiveActionVerification:
    status: str
    valid: bool
    replan_required: bool
    hard_block: bool
    errors: list[str]
    replan_reasons: list[str]
    hard_block_reasons: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "valid": self.valid,
            "replan_required": self.replan_required,
            "hard_block": self.hard_block,
            "errors": self.errors,
            "replan_reasons": self.replan_reasons,
            "hard_block_reasons": self.hard_block_reasons,
            "warnings": self.warnings,
        }


def _read_contract() -> dict[str, Any]:
    payload = json.loads(LIVE_ACTION_CONTRACT_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def allowed_live_action_ids() -> tuple[str, ...]:
    action_space = _read_contract().get("action_space")
    if not isinstance(action_space, dict):
        return ()
    values = action_space.get("semantic_reusable_action_ids")
    return tuple(str(item) for item in values or [] if isinstance(item, str))


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def signature(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).casefold()


def response_signature(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_text(text)).strip()


def parse_live_action_json(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    stripped = str(text or "").strip()
    if not stripped:
        return None, ["empty_output"]
    decoder = json.JSONDecoder()
    start = stripped.find("{")
    if start < 0:
        return None, ["no_json_object"]
    try:
        payload, end = decoder.raw_decode(stripped[start:])
    except json.JSONDecodeError as exc:
        return None, [f"invalid_json:{exc}"]
    if not isinstance(payload, dict):
        return None, ["json_output_not_object"]
    if stripped[start + end :].strip():
        return payload, ["extra_text_after_json"]
    return payload, []


def _known_slot_present(memory: dict[str, Any], key: str) -> bool:
    known = memory.get("known_slots")
    if not isinstance(known, dict):
        return False
    value = known.get(key)
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return value is not None


def _team_state_is_not_team(memory: dict[str, Any]) -> bool:
    known = memory.get("known_slots")
    if not isinstance(known, dict):
        return False
    for key in ("team", "team_state", "is_team", "not_team"):
        if key not in known:
            continue
        value = known.get(key)
        if key == "not_team" and value is True:
            return True
        if value is False:
            return True
        if isinstance(value, str) and normalize_text(value) in {"not team", "no team", "personal", "individual", "by myself"}:
            return True
    return False


def _has_supported_facts(say: str, approved_fact_ids: list[str] | None, approved_fact_summaries: dict[str, str] | None) -> bool:
    if not PRODUCT_TERMS_RE.search(say) or not FACTUAL_VERB_RE.search(say):
        return True
    if approved_fact_ids:
        return True
    summary_text = normalize_text(" ".join((approved_fact_summaries or {}).values()))
    if not summary_text:
        return False
    mentioned = [term for term in ("chatgpt", "free", "plus", "pro", "business", "enterprise") if term in normalize_text(say)]
    return all(term in summary_text for term in mentioned)


def _schema_errors(payload: dict[str, Any], allowed_action_ids: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    actual = set(payload)
    required = set(REQUIRED_FIELDS)
    allowed = required | set(OPTIONAL_FIELDS)
    missing = sorted(required - actual)
    extra = sorted(actual - allowed)
    if missing:
        errors.append(f"missing_required_fields:{missing}")
    if extra:
        errors.append(f"unsupported_fields:{extra}")
    if not isinstance(payload.get("action_id"), str) or not str(payload.get("action_id") or "").strip():
        errors.append("action_id_must_be_non_empty_string")
    elif payload["action_id"] not in allowed_action_ids:
        errors.append(f"action_id_not_allowed:{payload['action_id']}")
    if not isinstance(payload.get("slots"), dict):
        errors.append("slots_must_be_object")
    if not isinstance(payload.get("memory_updates"), dict):
        errors.append("memory_updates_must_be_object")
    if not isinstance(payload.get("uncertainty"), str):
        errors.append("uncertainty_must_be_string")
    if not isinstance(payload.get("say"), str) or not str(payload.get("say") or "").strip():
        errors.append("say_must_be_non_empty_string")
    confidence = payload.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool)):
        errors.append("confidence_must_be_number_when_present")
    return errors


def verify_live_action_output(
    payload: dict[str, Any],
    *,
    memory: dict[str, Any] | None = None,
    approved_fact_ids: list[str] | None = None,
    approved_fact_summaries: dict[str, str] | None = None,
    allowed_action_ids: list[str] | tuple[str, ...] | None = None,
) -> LiveActionVerification:
    resolved_action_ids = tuple(allowed_action_ids or allowed_live_action_ids())
    ledger = memory or {}
    errors = _schema_errors(payload, resolved_action_ids)
    replan_reasons: list[str] = []
    hard_block_reasons: list[str] = []
    warnings: list[str] = []
    say = str(payload.get("say") or "")
    action_id = str(payload.get("action_id") or "")
    slots = payload.get("slots") if isinstance(payload.get("slots"), dict) else {}
    current_slot_signature = signature(slots)
    last_slot_signature = str(ledger.get("last_action_slot_signature") or "").casefold()
    buyer_text = normalize_text(ledger.get("current_buyer_utterance") or "")

    if INTERNAL_LANGUAGE_RE.search(say):
        replan_reasons.append("internal_language_in_say")
    if RAW_URL_RE.search(say) and ledger.get("raw_url_speech_allowed") is not True:
        replan_reasons.append("raw_url_speech")
    if SIDE_EFFECT_RE.search(say):
        hard_block_reasons.append("fake_side_effect_claim")
    if UNSUPPORTED_ABSOLUTE_RE.search(say):
        hard_block_reasons.append("unsupported_absolute_claim")
    if not _has_supported_facts(say, approved_fact_ids, approved_fact_summaries):
        hard_block_reasons.append("unsupported_product_fact")

    if " and " in buyer_text and " or " in normalize_text(say) and " and " not in normalize_text(say):
        replan_reasons.append("and_or_drift")
    if " or " in buyer_text and " and " in normalize_text(say) and " or " not in normalize_text(say):
        replan_reasons.append("or_and_drift")
    if "voice" in buyer_text and "writing" in normalize_text(say) and "voice" not in normalize_text(say):
        replan_reasons.append("voice_writing_drift")
    if _team_state_is_not_team(ledger) and TEAM_LANGUAGE_RE.search(say):
        replan_reasons.append("not_team_team_drift")

    if action_id == ledger.get("last_action_id") and current_slot_signature == last_slot_signature:
        if ledger.get("new_buyer_info_since_last_action") is not True:
            replan_reasons.append("repeated_action_and_slots_without_new_info")
    if response_signature(say) and response_signature(say) == response_signature(str(ledger.get("last_response_signature") or "")):
        replan_reasons.append("repeated_say")
    if action_id == "ask_use_case_gap" and _known_slot_present(ledger, "use_case"):
        replan_reasons.append("asked_use_case_after_known")
    if ledger.get("buyer_said_already_told_you") is True and action_id.startswith("ask_"):
        replan_reasons.append("buyer_already_told_you")
    if ledger.get("terminal_acceptance_seen") is True and action_id != "terminal_close":
        replan_reasons.append("terminal_acceptance_not_closed")
    if ledger.get("price_answered") is True and action_id == "answer_price" and ledger.get("new_buyer_info_since_last_action") is not True:
        replan_reasons.append("price_answer_repeated_without_new_context")
    if ledger.get("recommendation_given") and action_id in {"answer_plan_fit", "compare_plus_vs_pro"}:
        if ledger.get("new_buyer_info_since_last_action") is not True:
            replan_reasons.append("recommendation_repeated_without_new_context")
    frame = normalize_text(ledger.get("current_decision_frame") or "")
    if ("confus" in frame or "understand" in frame) and response_signature(say) == response_signature(str(ledger.get("last_response_signature") or "")):
        replan_reasons.append("confused_buyer_same_explanation")

    if errors:
        status = "invalid"
    elif hard_block_reasons:
        status = "hard_block"
    elif replan_reasons:
        status = "replan_required"
    else:
        status = "pass"
    return LiveActionVerification(
        status=status,
        valid=not errors and not hard_block_reasons and not replan_reasons,
        replan_required=bool(replan_reasons) and not hard_block_reasons,
        hard_block=bool(hard_block_reasons),
        errors=errors,
        replan_reasons=sorted(set(replan_reasons)),
        hard_block_reasons=sorted(set(hard_block_reasons)),
        warnings=warnings,
    )
