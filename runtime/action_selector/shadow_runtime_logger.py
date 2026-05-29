from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.action_selector.action_selector_contract import action_labels, normalize_text, validate_selector_output
from runtime.action_selector.non_llm_action_selector import RuleBasedActionSelector
from runtime.action_selector.shadow_mode_evaluator import classify_shadow_agreement


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().parent / "shadow_runtime_logging_config.json"

FALSE_RUNTIME_FLAGS = {
    "side_effects_allowed": False,
    "buyer_facing_text_generated": False,
    "live_runtime_wiring_allowed": False,
    "response_text_changed": False,
    "runtime_behavior_changed": False,
    "memory_mutation_allowed": False,
    "provider_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "audio_data_used": False,
    "raw_private_data": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_shadow_runtime_logging_config() -> dict[str, Any]:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _context_payload(turn_context: dict[str, Any]) -> dict[str, Any]:
    context = turn_context.get("context") if isinstance(turn_context.get("context"), dict) else {}
    known_context = turn_context.get("known_context") if isinstance(turn_context.get("known_context"), dict) else {}
    merged = dict(context)
    merged.update(known_context)
    return merged


def _buyer_text(turn_context: dict[str, Any]) -> str:
    return _string(
        turn_context.get("buyer_utterance_text_sanitized")
        or turn_context.get("buyer_utterance_text")
        or turn_context.get("transcript")
    )


def _selector_payload(turn_context: dict[str, Any]) -> dict[str, Any]:
    context = _context_payload(turn_context)
    buyer_text = _buyer_text(turn_context)
    normalized = _string(turn_context.get("normalized_buyer_text") or context.get("normalized_buyer_text")) or normalize_text(buyer_text)
    return {
        "buyer_utterance_text": buyer_text,
        "context": {
            "buyer_utterance_text": buyer_text,
            "normalized_buyer_text": normalized,
            "memory_summary": _string(turn_context.get("memory_summary") or turn_context.get("context_summary") or context.get("memory_summary")),
            "known_use_case": context.get("known_use_case") or [],
            "known_tools": context.get("known_tools") or [],
            "known_plan_interest": context.get("known_plan_interest") or "",
            "known_team_status": context.get("known_team_status") or "",
            "buyer_emotion": context.get("buyer_emotion") or "",
            "buyer_confusion_level": context.get("buyer_confusion_level") or "",
            "buyer_skepticism_level": context.get("buyer_skepticism_level") or "",
            "buyer_engagement_level": context.get("buyer_engagement_level") or "",
            "last_action_id": _string(turn_context.get("previous_action_id") or context.get("last_action_id")),
            "last_answered_topic": _string(turn_context.get("previous_answered_topic") or context.get("last_answered_topic")),
            "safety_boundary_detected": turn_context.get("safety_boundary_detected") is True
            or context.get("safety_boundary_detected") is True,
        },
    }


def _context_summary(turn_context: dict[str, Any]) -> str:
    existing = _string(turn_context.get("context_summary"))
    if existing:
        return existing
    context = _context_payload(turn_context)
    compact = context.get("compact_target") if isinstance(context.get("compact_target"), dict) else {}
    parts = [
        f"team={context.get('known_team_status') or ''}",
        "use=" + ",".join(str(item) for item in context.get("known_use_case", []) if str(item or "").strip())
        if isinstance(context.get("known_use_case"), list)
        else "",
        "tools=" + ",".join(str(item) for item in context.get("known_tools", []) if str(item or "").strip())
        if isinstance(context.get("known_tools"), list)
        else "",
        f"safety={context.get('safety_boundary_detected') is True}",
        f"compact_action={compact.get('action') or ''}",
        f"compact_sub={compact.get('sub') or ''}",
    ]
    return "; ".join(part for part in parts if part and not part.endswith("="))


def _shadow_record_id(turn_context: dict[str, Any], selector_action_id: str) -> str:
    source = "|".join(
        [
            _string(turn_context.get("mode")),
            _string(turn_context.get("evidence_source") or turn_context.get("source_file")),
            _string(turn_context.get("turn_id") or turn_context.get("replay_case_id") or turn_context.get("case_id")),
            _buyer_text(turn_context),
            selector_action_id,
        ]
    )
    return "runtime_shadow_" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]


def _is_private_source(record: dict[str, Any]) -> bool:
    source = _string(record.get("evidence_source")).replace("\\", "/").casefold()
    return "data/private" in source or "private-restricted" in source or record.get("raw_private_data") is True


def build_shadow_runtime_record(
    turn_context: dict[str, Any],
    *,
    selector_output: dict[str, Any],
    expected_action_id: str = "",
    mode: str = "offline_replay_shadow",
) -> dict[str, Any]:
    context = deepcopy(turn_context)
    action_id = _string(selector_output.get("action_id"))
    safety_status = "safe"
    if selector_output.get("safety_block") is True:
        safety_status = "boundary_safe"
    if action_id not in action_labels():
        safety_status = "unsafe_uncontrolled_action"
    runtime_action_id = _string(context.get("runtime_action_id_if_available") or context.get("existing_runtime_action_id"))
    classification = classify_shadow_agreement(
        selector_action_id=action_id,
        runtime_action_id=runtime_action_id,
        expected_action_id=expected_action_id,
        safety_status=safety_status,
        fallback_required=selector_output.get("fallback_required") is True,
    )
    record = {
        "shadow_record_id": "",
        "timestamp": utc_now(),
        "mode": mode,
        "evidence_source": _string(context.get("evidence_source") or context.get("source_file")),
        "campaign_id": _string(context.get("campaign_id")),
        "turn_id": _string(context.get("turn_id") or context.get("replay_case_id") or context.get("case_id")),
        "buyer_utterance_text_sanitized": _buyer_text(context),
        "context_summary": _context_summary(context),
        "runtime_response_text_available": bool(
            context.get("runtime_response_text_available")
            or context.get("existing_runtime_response_text_available")
            or context.get("existing_runtime_response_text")
        ),
        "runtime_action_id_if_available": runtime_action_id,
        "expected_action_id": expected_action_id,
        "selector_action_id": action_id,
        "selector_confidence": round(float(selector_output.get("confidence") or 0.0), 4),
        "selector_reasons": [str(item) for item in selector_output.get("reasons") or []],
        "selector_matched_features": [str(item) for item in selector_output.get("matched_features") or []],
        "agreement_classification": classification["disagreement_type"],
        "agreement_with_expected": action_id == expected_action_id if expected_action_id else None,
        "agreement_with_runtime": classification["agreement_with_runtime"],
        "safety_status": safety_status,
        "possible_improvement": classification["disagreement_type"] == "selector_possible_improvement",
        "possible_regression": classification["disagreement_type"] == "selector_possible_regression",
        "validation_errors": [],
        "should_not_change_runtime": True,
        "public_evidence_sanitized": True,
        **FALSE_RUNTIME_FLAGS,
    }
    record["shadow_record_id"] = _shadow_record_id(context, action_id)
    record["validation_errors"] = validate_shadow_runtime_record(record)
    return record


def run_shadow_selector_read_only(
    turn_context: dict[str, Any],
    *,
    expected_action_id: str = "",
    selector: Any | None = None,
    mode: str = "offline_replay_shadow",
) -> dict[str, Any]:
    context = deepcopy(turn_context)
    resolved_selector = selector or RuleBasedActionSelector()
    selector_output = resolved_selector.select(_selector_payload(context)).to_dict()
    return build_shadow_runtime_record(
        context,
        selector_output=selector_output,
        expected_action_id=expected_action_id,
        mode=mode,
    )


def validate_shadow_runtime_record(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = {
        "shadow_record_id",
        "timestamp",
        "mode",
        "evidence_source",
        "campaign_id",
        "turn_id",
        "buyer_utterance_text_sanitized",
        "context_summary",
        "runtime_response_text_available",
        "runtime_action_id_if_available",
        "selector_action_id",
        "selector_confidence",
        "selector_reasons",
        "selector_matched_features",
        "agreement_classification",
        "safety_status",
        "possible_improvement",
        "possible_regression",
        "validation_errors",
        "should_not_change_runtime",
        "live_runtime_wiring_allowed",
        "response_text_changed",
        "runtime_behavior_changed",
    }
    missing = sorted(required - set(record))
    if missing:
        failures.append(f"missing_required_fields:{missing}")
    config = load_shadow_runtime_logging_config()
    allowed_modes = set(config.get("allowed_modes") or [])
    if record.get("mode") not in allowed_modes:
        failures.append(f"mode_not_allowed:{record.get('mode')}")
    for key, expected in FALSE_RUNTIME_FLAGS.items():
        if record.get(key) is not expected:
            failures.append(f"{key}_must_be_false")
    if record.get("should_not_change_runtime") is not True:
        failures.append("should_not_change_runtime_must_be_true")
    selector_payload = {
        "action_id": record.get("selector_action_id"),
        "confidence": record.get("selector_confidence", 0.0),
        "reasons": record.get("selector_reasons") or [],
        "matched_features": record.get("selector_matched_features") or [],
        "side_effects_allowed": False,
        "live_runtime_wiring_allowed": False,
    }
    failures.extend(validate_selector_output(selector_payload))
    forbidden_text_keys = {"response_text", "buyer_facing_response", "draft_response", "say"}
    extra = sorted(forbidden_text_keys & set(record))
    if extra:
        failures.append(f"record_contains_buyer_facing_text:{extra}")
    if _is_private_source(record):
        failures.append("record_references_private_source")
    return failures


def redact_shadow_record_for_public_evidence(record: dict[str, Any]) -> dict[str, Any]:
    redacted = deepcopy(record)
    if _is_private_source(redacted) or redacted.get("mode") != "offline_replay_shadow":
        redacted["buyer_utterance_text_sanitized"] = "[REDACTED_PRIVATE_OR_LIVE_TEXT]"
    redacted["public_evidence_sanitized"] = True
    redacted["raw_private_data"] = False
    return redacted


def append_shadow_record_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    output_path = Path(path)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.open("a", encoding="utf-8").write(
        json.dumps(redact_shadow_record_for_public_evidence(record), ensure_ascii=False, separators=(",", ":")) + "\n"
    )
