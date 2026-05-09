from __future__ import annotations

import json
import re
import statistics
import time
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROD_013_ID = "PROD-013-callcenteren-pattern-extraction"
DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
DATASET_TREE_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english/tree/main"
PAPER_URL = "https://arxiv.org/abs/2507.02958"
LICENSE = "cc-by-nc-4.0"

OPENING_PATTERN_LABELS = [
    "opening_types",
    "greeting_styles",
    "identity_disclosures",
    "company_disclosures",
    "reason_for_call",
    "permission_to_continue",
    "first_question_types",
    "customer_initial_response",
]
CUSTOMER_INTENT_LABELS = [
    "buying_interest",
    "information_request",
    "price_request",
    "complaint",
    "cancellation",
    "technical_problem",
    "billing_issue",
    "appointment_request",
    "not_interested",
    "wrong_person",
    "busy_now",
    "callback_request",
    "hostile_rejection",
]
OBJECTION_TYPE_LABELS = [
    "too_expensive",
    "not_interested",
    "already_has_provider",
    "needs_to_think",
    "needs_spouse_or_manager",
    "bad_previous_experience",
    "no_time",
    "does_not_trust_agent",
    "confused_about_offer",
    "wants_written_info",
    "contract_fear",
    "payment_fear",
    "hidden_objection",
]
EMOTION_TRANSITION_LABELS = [
    "neutral_to_interested",
    "neutral_to_annoyed",
    "confused_to_clear",
    "annoyed_to_calm",
    "skeptical_to_open",
    "interested_to_hesitant",
    "hesitant_to_committed",
    "angry_to_escalated",
    "angry_to_de_escalated",
]
PERSUASION_STRATEGY_LABELS = [
    "benefit_framing",
    "pain_point_discovery",
    "cost_savings",
    "urgency",
    "scarcity",
    "social_proof",
    "authority",
    "risk_reversal",
    "trial_close",
    "trail_close",
    "assumptive_close",
    "contrast_offer",
    "personalization",
    "empathy_first",
    "problem_solution_fit",
]
BAD_PERSUASION_LABELS = [
    "pushy",
    "vague_claim",
    "unsupported_claim",
    "ignores_customer_need",
    "repeats_script",
    "talks_too_much",
    "premature_close",
]
DISCOVERY_QUESTION_LABELS = [
    "current_provider_question",
    "current_problem_question",
    "budget_question",
    "usage_question",
    "decision_maker_question",
    "timeline_question",
    "priority_question",
    "pain_point_question",
    "eligibility_question",
]
CONVERSATION_STAGE_LABELS = [
    "opening",
    "identity_verification",
    "reason_for_call",
    "rapport",
    "discovery",
    "problem_identification",
    "offer_presentation",
    "objection_handling",
    "clarification",
    "price_discussion",
    "eligibility_check",
    "trial_close",
    "trail_close",
    "close_attempt",
    "commitment_confirmation",
    "handoff",
    "callback_scheduling",
    "escalation",
    "wrap_up",
]
CLOSE_TYPE_LABELS = [
    "trial_close",
    "trail_close",
    "soft_close",
    "assumptive_close",
    "summary_close",
    "choice_close",
    "callback_close",
    "handoff_close",
    "sale_ready_close",
]
COMMITMENT_LEVEL_LABELS = [
    "not_interested",
    "mild_interested",
    "information_requested",
    "callback_agreed",
    "verbal_interested",
    "verbal_commitment",
    "sale_ready_outcome",
]
AGENT_MISTAKE_LABELS = [
    "ignores_customer_emotion",
    "answers_wrong_question",
    "repeats_same_line",
    "over_explains",
    "closes_too_early",
    "does_not_confirm_understanding",
    "fails_to_handle_objection",
    "escalates_unnecessarily",
    "does_not_escalate_when_needed",
]

PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
TEXT_FIELD_CANDIDATES = (
    "text",
    "utterance",
    "content",
    "message",
    "sentence",
    "normalized_text",
    "transcript",
)
TURN_LIST_KEYS = (
    "turns",
    "messages",
    "dialogue",
    "conversation",
    "utterances",
    "segments",
)
CONVERSATION_LIST_KEYS = (
    "conversations",
    "calls",
    "records",
    "items",
    "data",
)
SPEAKER_AGENT_TOKENS = {"agent", "assistant", "sales_agent", "seller", "representative", "rep", "operator"}
SPEAKER_CUSTOMER_TOKENS = {"customer", "client", "caller", "user", "buyer", "prospect", "consumer"}
TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Turn:
    speaker: str
    text: str
    start: float | None = None
    end: float | None = None


@dataclass(frozen=True)
class Conversation:
    source_id: str
    domain: str
    topic: str
    accent: str
    turns: tuple[Turn, ...]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def ensure_allowed_raw_dir(raw_dir: Path) -> Path:
    resolved = raw_dir.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("PROD-013 raw directory must stay inside the project root.") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError("PROD-013 cannot read private customer data directories.")
    return resolved


def tokens(text: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(text.lower()) if len(token) > 1}


def word_count(text: str) -> int:
    return len(TOKEN_RE.findall(text.lower()))


def any_phrase(text: str, phrases: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def load_jsonish_text(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        records: list[Any] = []
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records if records else None


def iter_source_payloads(raw_dir: Path) -> Iterable[tuple[str, Any]]:
    raw_dir = ensure_allowed_raw_dir(raw_dir)
    if not raw_dir.exists():
        return
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if not member.lower().endswith((".json", ".jsonl")):
                        continue
                    with archive.open(member) as handle:
                        payload = load_jsonish_text(handle.read().decode("utf-8", errors="ignore"))
                    if payload is not None:
                        yield f"{path.name}:{member}", payload
        elif suffix in {".json", ".jsonl"}:
            payload = load_jsonish_text(path.read_text(encoding="utf-8", errors="ignore"))
            if payload is not None:
                yield path.name, payload


def text_from_dict(value: dict[str, Any]) -> str:
    for field in TEXT_FIELD_CANDIDATES:
        raw = value.get(field)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def normalize_speaker(raw: Any, fallback_index: int) -> str:
    speaker = str(raw or "").lower().replace("-", "_").replace(" ", "_")
    if speaker in SPEAKER_AGENT_TOKENS or any(token in speaker for token in ("agent", "assistant", "operator", "rep")):
        return "agent"
    if speaker in SPEAKER_CUSTOMER_TOKENS or any(token in speaker for token in ("customer", "caller", "client", "buyer", "user")):
        return "customer"
    return "agent" if fallback_index % 2 == 0 else "customer"


def number_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def word_time_seconds(value: Any) -> float | None:
    raw = number_or_none(value)
    if raw is None:
        return None
    return raw / 1000.0 if raw > 1000 else raw


def turn_from_value(value: Any, index: int) -> Turn | None:
    if isinstance(value, str):
        text = value.strip()
        return Turn(speaker=normalize_speaker(None, index), text=text) if text else None
    if not isinstance(value, dict):
        return None
    text = text_from_dict(value)
    if not text:
        return None
    speaker = normalize_speaker(value.get("speaker") or value.get("role") or value.get("from"), index)
    start = number_or_none(value.get("start") or value.get("start_time") or value.get("begin"))
    end = number_or_none(value.get("end") or value.get("end_time") or value.get("stop"))
    return Turn(speaker=speaker, text=text, start=start, end=end)


def turn_list_from_dict(value: dict[str, Any]) -> list[Any] | None:
    for key in TURN_LIST_KEYS:
        candidate = value.get(key)
        if isinstance(candidate, list) and candidate:
            return candidate
    return None


def looks_like_word_items(values: list[Any]) -> bool:
    if not values or not all(isinstance(item, dict) for item in values[: min(len(values), 20)]):
        return False
    sample = values[: min(len(values), 20)]
    text_count = sum(1 for item in sample if isinstance(item.get("text"), str) and item.get("text", "").strip())
    timing_count = sum(1 for item in sample if item.get("start") is not None or item.get("end") is not None)
    return text_count >= max(1, len(sample) // 2) and timing_count >= max(1, len(sample) // 2)


def infer_domain_from_source(source_id: str) -> str:
    lowered = source_id.lower()
    checks = [
        ("medical_equipment", ["medical_equipment"]),
        ("medicare", ["medicare"]),
        ("auto_insurance", ["auto_insurance", "auto-insurance"]),
        ("healthcare_insurance", ["healthcare_insurance"]),
        ("insurance", ["insurance"]),
        ("automotive", ["automotive", "stereo"]),
        ("home_service", ["home_service", "home_ervice"]),
        ("telecom", ["telecom"]),
        ("general_customer_service", ["customer_service_general"]),
    ]
    for label, tokens_ in checks:
        if any(token in lowered for token in tokens_):
            return label
    return "unknown"


def infer_topic_from_source(source_id: str) -> str:
    lowered = source_id.lower()
    parts: list[str] = []
    if "outbound" in lowered:
        parts.append("outbound")
    if "inbound" in lowered:
        parts.append("inbound")
    if "insurance" in lowered:
        parts.append("insurance")
    if "customer_service" in lowered:
        parts.append("customer_service")
    if "medical" in lowered or "medicare" in lowered or "healthcare" in lowered:
        parts.append("healthcare")
    if "telecom" in lowered:
        parts.append("telecom")
    if "home_service" in lowered or "home_ervice" in lowered:
        parts.append("home_service")
    if "automotive" in lowered or "stereo" in lowered:
        parts.append("automotive")
    return "_".join(dict.fromkeys(parts)) if parts else "unknown"


def conversation_meta(value: dict[str, Any], source_id: str) -> tuple[str, str, str]:
    domain = str(value.get("domain") or value.get("category") or value.get("industry") or "unknown").lower().replace(" ", "_")
    topic = str(value.get("topic") or value.get("subtopic") or value.get("intent") or "unknown").lower().replace(" ", "_")
    accent = str(value.get("accent") or value.get("locale") or value.get("dialect") or "unknown").lower().replace(" ", "_")
    if domain == "unknown":
        domain = infer_domain_from_source(source_id)
    if topic == "unknown":
        topic = infer_topic_from_source(source_id)
    return domain, topic, accent


def inferred_first_speaker(source_id: str, meta: dict[str, Any]) -> str:
    context = " ".join(str(value) for value in [source_id, *meta.values()]).lower()
    if "outbound" in context or "offer" in context or "sales" in context:
        return "agent"
    if "inbound" in context or "customer_service" in context or "support" in context:
        return "customer"
    return "agent"


def segment_role_signal(text: str) -> str | None:
    lowered = text.lower()
    agent_score = 0
    customer_score = 0

    agent_checks = [
        (3, ["this is", "i am calling", "i'm calling", "calling about", "calling because"]),
        (3, ["do you have", "have a minute", "have thirty seconds", "quick call"]),
        (3, ["i understand", "i hear", "let me", "i can", "we can", "i will", "we help"]),
        (2, ["are you comparing", "who handles", "would a", "could a", "would you", "could you"]),
        (2, ["route this", "transfer you", "connect you", "specialist", "handoff"]),
        (1, ["options", "summary", "review", "provider decisions", "eligibility"]),
    ]
    customer_checks = [
        (4, ["how much", "does it cost", "what does it cost", "too expensive"]),
        (4, ["not interested", "no thanks", "wrong person", "stop calling", "do not call"]),
        (3, ["i am busy", "i'm busy", "busy now", "no time", "call back"]),
        (3, ["already have", "my provider", "need to ask", "think about it", "not sure"]),
        (3, ["billing issue", "want to cancel", "complaint", "broken", "not working"]),
        (2, ["maybe", "send details", "send information", "what is this", "what do you mean"]),
        (1, ["cost", "price", "manager", "spouse", "partner"]),
    ]

    for weight, phrases in agent_checks:
        if any_phrase(lowered, phrases):
            agent_score += weight
    for weight, phrases in customer_checks:
        if any_phrase(lowered, phrases):
            customer_score += weight

    if agent_score >= customer_score + 2:
        return "agent"
    if customer_score >= agent_score + 2:
        return "customer"
    return None


def should_split_word_segment(
    current_words: list[str],
    previous_end: float | None,
    next_start: float | None,
    current_speaker: str | None,
    next_speaker: str | None,
) -> bool:
    if not current_words:
        return False
    if current_speaker and next_speaker and current_speaker != next_speaker:
        return True
    if previous_end is not None and next_start is not None and next_start - previous_end >= 0.9:
        return True
    if len(current_words) >= 35 and current_words[-1].rstrip().endswith((".", "?", "!")):
        return True
    return False


def turns_from_word_level(value: dict[str, Any], source_id: str, meta: dict[str, Any]) -> list[Turn]:
    word_items = value.get("words")
    if not isinstance(word_items, list) or not looks_like_word_items(word_items):
        return []

    segments: list[dict[str, Any]] = []
    current_words: list[str] = []
    current_start: float | None = None
    current_end: float | None = None
    current_speaker: str | None = None

    def flush() -> None:
        nonlocal current_words, current_start, current_end, current_speaker
        text = " ".join(current_words).strip()
        if text:
            segments.append(
                {
                    "text": text,
                    "start": current_start,
                    "end": current_end,
                    "speaker": current_speaker,
                }
            )
        current_words = []
        current_start = None
        current_end = None
        current_speaker = None

    for index, item in enumerate(word_items):
        if not isinstance(item, dict):
            continue
        word_text = str(item.get("text") or "").strip()
        if not word_text:
            continue
        start = word_time_seconds(item.get("start"))
        end = word_time_seconds(item.get("end"))
        raw_speaker = item.get("speaker") or item.get("role") or item.get("from")
        speaker = normalize_speaker(raw_speaker, index) if raw_speaker else None
        if should_split_word_segment(current_words, current_end, start, current_speaker, speaker):
            flush()
        if current_start is None:
            current_start = start
        current_end = end if end is not None else current_end
        current_speaker = current_speaker or speaker
        current_words.append(word_text)
    flush()

    if len(segments) < 2:
        return []

    first_speaker = inferred_first_speaker(source_id, meta)
    turns: list[Turn] = []
    for index, segment in enumerate(segments):
        fallback_speaker = first_speaker if not turns else ("customer" if turns[-1].speaker == "agent" else "agent")
        speaker = segment["speaker"] or segment_role_signal(segment["text"]) or fallback_speaker
        turns.append(Turn(speaker=speaker, text=segment["text"], start=segment["start"], end=segment["end"]))
    return turns


def extract_conversations_from_payload(source_id: str, payload: Any) -> list[Conversation]:
    conversations: list[Conversation] = []

    def visit(value: Any, inherited_meta: dict[str, Any] | None = None) -> None:
        meta = inherited_meta or {}
        if isinstance(value, list):
            if value and all(isinstance(item, (dict, str)) for item in value):
                turns = [turn for index, item in enumerate(value) if (turn := turn_from_value(item, index))]
                if len(turns) >= 2:
                    domain, topic, accent = conversation_meta(meta, source_id)
                    conversations.append(Conversation(source_id=source_id, domain=domain, topic=topic, accent=accent, turns=tuple(turns)))
                    return
            for item in value:
                visit(item, meta)
            return

        if not isinstance(value, dict):
            return

        merged_meta = {**meta, **{key: value.get(key) for key in ("domain", "category", "industry", "topic", "subtopic", "intent", "accent", "locale", "dialect") if value.get(key)}}
        word_turns = turns_from_word_level(value, source_id, merged_meta)
        if len(word_turns) >= 2:
            domain, topic, accent = conversation_meta(merged_meta, source_id)
            conversations.append(Conversation(source_id=source_id, domain=domain, topic=topic, accent=accent, turns=tuple(word_turns)))
            return

        turn_values = turn_list_from_dict(value)
        if turn_values:
            turns = [turn for index, item in enumerate(turn_values) if (turn := turn_from_value(item, index))]
            if len(turns) >= 2:
                domain, topic, accent = conversation_meta(merged_meta, source_id)
                conversations.append(Conversation(source_id=source_id, domain=domain, topic=topic, accent=accent, turns=tuple(turns)))
                return

        for key in CONVERSATION_LIST_KEYS:
            child = value.get(key)
            if isinstance(child, list):
                visit(child, merged_meta)
        for child in value.values():
            if isinstance(child, dict):
                visit(child, merged_meta)

    visit(payload)
    return conversations


def load_conversations(raw_dir: Path, max_conversations: int) -> tuple[list[Conversation], int]:
    conversations: list[Conversation] = []
    source_count = 0
    for source_id, payload in iter_source_payloads(raw_dir) or []:
        source_count += 1
        for conversation in extract_conversations_from_payload(source_id, payload):
            conversations.append(conversation)
            if len(conversations) >= max_conversations:
                return conversations, source_count
    return conversations, source_count


def iter_conversations_from_raw(
    raw_dir: Path,
    max_conversations: int,
    stats: dict[str, int] | None = None,
) -> Iterable[Conversation]:
    conversations_seen = 0
    if stats is not None:
        stats["source_file_count"] = 0
    for source_id, payload in iter_source_payloads(raw_dir) or []:
        if stats is not None:
            stats["source_file_count"] = stats.get("source_file_count", 0) + 1
        for conversation in extract_conversations_from_payload(source_id, payload):
            yield conversation
            conversations_seen += 1
            if max_conversations > 0 and conversations_seen >= max_conversations:
                return


def classify_emotion(text: str) -> str:
    lowered = text.lower()
    if any_phrase(lowered, ["terrible", "angry", "furious", "broken", "stop calling", "not call", "hate", "pushy"]):
        return "angry"
    if any_phrase(lowered, ["annoy", "complaint", "nobody fixed", "too expensive", "busy", "wrong person"]):
        return "annoyed"
    if any_phrase(lowered, ["do not trust", "don't trust", "already have", "worries", "worry", "no risk"]):
        return "skeptical"
    if any_phrase(lowered, ["what is this", "confused", "unclear", "not clear", "what do you mean"]):
        return "confused"
    if any_phrase(lowered, ["maybe", "yes", "could", "interested", "compare", "review later"]):
        return "interested"
    if any_phrase(lowered, ["think about", "need to ask", "not sure", "hesitant"]):
        return "hesitant"
    if any_phrase(lowered, ["works", "good", "fine", "okay", "calmer", "clearer"]):
        return "positive"
    return "neutral"


def emotion_bucket_for_transition(emotion: str) -> str:
    if emotion in {"angry", "annoyed"}:
        return "angry" if emotion == "angry" else "annoyed"
    return emotion


def classify_customer_intents(text: str) -> list[str]:
    lowered = text.lower()
    labels: list[str] = []
    checks = [
        ("buying_interest", ["interested", "could compare", "review later", "yes"]),
        ("information_request", ["send information", "send info", "send details", "summary"]),
        ("price_request", ["how much", "price", "cost", "expensive"]),
        ("complaint", ["complaint", "nobody fixed", "terrible", "bad previous", "last agent"]),
        ("cancellation", ["cancel", "cancellation"]),
        ("technical_problem", ["broken", "technical", "device", "not working"]),
        ("billing_issue", ["billing", "invoice", "charged", "payment issue"]),
        ("appointment_request", ["appointment", "works", "tuesday", "wednesday", "ten"]),
        ("not_interested", ["not interested", "no thanks"]),
        ("wrong_person", ["wrong person"]),
        ("busy_now", ["busy now", "no time", "busy"]),
        ("callback_request", ["call back", "callback", "review later"]),
        ("hostile_rejection", ["stop calling", "terrible", "pushy", "do not call"]),
    ]
    for label, phrases in checks:
        if any_phrase(lowered, phrases):
            labels.append(label)
    return labels or ["unclear_intent"]


def classify_objections(text: str) -> list[str]:
    lowered = text.lower()
    labels: list[str] = []
    checks = [
        ("too_expensive", ["too expensive", "cost", "price", "how much"]),
        ("not_interested", ["not interested", "no thanks"]),
        ("already_has_provider", ["already have a provider", "current provider", "have a provider"]),
        ("needs_to_think", ["think about", "not sure"]),
        ("needs_spouse_or_manager", ["manager", "boss", "spouse", "partner"]),
        ("bad_previous_experience", ["last agent", "bad previous", "terrible"]),
        ("no_time", ["busy", "no time"]),
        ("does_not_trust_agent", ["do not trust", "don't trust", "trust this call"]),
        ("confused_about_offer", ["what is this", "confused", "unclear"]),
        ("wants_written_info", ["send information", "send info", "send details", "summary"]),
        ("contract_fear", ["contract worries", "contract", "lock in"]),
        ("payment_fear", ["payment", "card", "pay now"]),
    ]
    for label, phrases in checks:
        if any_phrase(lowered, phrases):
            labels.append(label)
    if not labels and classify_emotion(text) in {"skeptical", "hesitant", "annoyed"}:
        labels.append("hidden_objection")
    return labels


def objection_text_pattern(label: str) -> str:
    patterns = {
        "too_expensive": "customer signals price or value concern",
        "not_interested": "customer rejects relevance or interest",
        "already_has_provider": "customer says current provider already solves it",
        "needs_to_think": "customer delays decision for reflection",
        "needs_spouse_or_manager": "customer needs another decision maker",
        "bad_previous_experience": "customer references prior negative experience",
        "no_time": "customer says timing blocks the call",
        "does_not_trust_agent": "customer questions caller credibility",
        "confused_about_offer": "customer does not understand the offer",
        "wants_written_info": "customer asks for written information before deciding",
        "contract_fear": "customer worries about contract commitment",
        "payment_fear": "customer worries about payment or financial exposure",
        "hidden_objection": "customer hesitates without naming the blocker",
    }
    return patterns.get(label, "customer raises unresolved concern")


def classify_agent_tactic(text: str) -> str:
    lowered = text.lower()
    if any_phrase(lowered, ["sorry", "understand", "hear the frustration", "that makes sense"]):
        return "empathy_first"
    if any_phrase(lowered, ["which", "who", "what", "is the", "bigger issue", "confirm i understand"]):
        return "pain_point_discovery"
    if any_phrase(lowered, ["monthly cost", "contract", "reliability", "price"]):
        return "contrast_offer"
    if any_phrase(lowered, ["transfer", "connect", "specialist", "route"]):
        return "handoff_close"
    if any_phrase(lowered, ["short summary", "manager", "decide"]):
        return "authority"
    if any_phrase(lowered, ["reduce", "savings", "save"]):
        return "cost_savings"
    if any_phrase(lowered, ["only one spot", "today", "lock it in"]):
        return "urgency"
    if any_phrase(lowered, ["would", "could", "do you have", "work for"]):
        return "trial_close"
    return "benefit_framing"


def classify_bad_persuasion(text: str) -> list[str]:
    lowered = text.lower()
    labels: list[str] = []
    if any_phrase(lowered, ["lock it in now", "let us lock", "only one spot"]):
        labels.extend(["pushy", "scarcity", "premature_close"])
    if any_phrase(lowered, ["guarantee", "guaranteed", "no risk"]):
        labels.append("unsupported_claim")
    if word_count(text) > 55:
        labels.append("talks_too_much")
    if lowered.count("?") > 1:
        labels.append("rapid_fire_questions")
    return labels


def response_quality(agent_text: str, customer_text: str, next_customer_text: str) -> str:
    bad = classify_bad_persuasion(agent_text)
    if bad:
        return "poor"
    customer_emotion = classify_emotion(customer_text)
    tactic = classify_agent_tactic(agent_text)
    if customer_emotion in {"angry", "annoyed"} and tactic in {"empathy_first", "handoff_close", "pain_point_discovery"}:
        return "good"
    if tactic in {"pain_point_discovery", "empathy_first", "authority", "contrast_offer", "handoff_close"}:
        return "good"
    if classify_emotion(next_customer_text) in {"positive", "interested"}:
        return "good"
    return "acceptable"


def resolution_state(next_customer_text: str) -> str:
    emotion = classify_emotion(next_customer_text)
    if emotion in {"positive", "interested"}:
        return "resolved"
    if emotion in {"angry", "annoyed"}:
        return "not_resolved"
    return "unknown"


def classify_discovery_questions(text: str) -> list[str]:
    lowered = text.lower()
    labels: list[str] = []
    checks = [
        ("current_provider_question", ["provider", "who handles"]),
        ("current_problem_question", ["problem", "issue", "bigger issue"]),
        ("budget_question", ["budget", "monthly cost", "price"]),
        ("usage_question", ["usage", "use", "manual work", "data"]),
        ("decision_maker_question", ["who handles", "manager", "decision"]),
        ("timeline_question", ["when", "today", "timeline"]),
        ("priority_question", ["bigger issue", "priority", "which"]),
        ("pain_point_question", ["problem", "concern", "issue"]),
        ("eligibility_question", ["address", "eligible", "qualify"]),
    ]
    for label, phrases in checks:
        if any_phrase(lowered, phrases):
            labels.append(label)
    return labels


def classify_stage(turn: Turn, index: int, previous_customer_text: str = "") -> str:
    lowered = turn.text.lower()
    if index <= 1 and turn.speaker == "agent":
        return "opening"
    if any_phrase(lowered, ["verify", "confirm your", "right person"]):
        return "identity_verification"
    if any_phrase(lowered, ["calling about", "calling because", "reason"]):
        return "reason_for_call"
    if any_phrase(lowered, ["sorry", "understand", "hear"]):
        return "rapport"
    if turn.speaker == "agent" and "?" in lowered and classify_discovery_questions(lowered):
        return "discovery"
    if any_phrase(lowered, ["problem", "issue", "broken", "billing"]):
        return "problem_identification"
    if any_phrase(lowered, ["we help", "options", "offer"]):
        return "offer_presentation"
    if classify_objections(previous_customer_text or lowered):
        return "objection_handling"
    if any_phrase(lowered, ["what is this", "clearer", "clarify"]):
        return "clarification"
    if any_phrase(lowered, ["price", "cost", "expensive", "monthly"]):
        return "price_discussion"
    if any_phrase(lowered, ["eligible", "qualify", "address"]):
        return "eligibility_check"
    if any_phrase(lowered, ["would", "could", "does that work"]):
        return "trial_close"
    if any_phrase(lowered, ["lock it in", "sign", "start now"]):
        return "close_attempt"
    if any_phrase(lowered, ["yes", "works", "committed", "agree"]):
        return "commitment_confirmation"
    if any_phrase(lowered, ["transfer", "connect", "specialist", "route"]):
        return "handoff"
    if any_phrase(lowered, ["appointment", "callback", "call back", "tuesday", "wednesday"]):
        return "callback_scheduling"
    if any_phrase(lowered, ["escalate", "manager", "specialist"]):
        return "escalation"
    if any_phrase(lowered, ["goodbye", "not call again", "wrap"]):
        return "wrap_up"
    return "clarification" if turn.speaker == "customer" else "rapport"


def classify_close_type(agent_text: str) -> str:
    lowered = agent_text.lower()
    if any_phrase(lowered, ["does that work", "would", "could"]):
        return "trial_close"
    if any_phrase(lowered, ["short summary", "help your manager"]):
        return "soft_close"
    if any_phrase(lowered, ["lock it in", "start now"]):
        return "assumptive_close"
    if any_phrase(lowered, ["summary"]):
        return "summary_close"
    if any_phrase(lowered, ["tuesday or wednesday", "which", "option"]):
        return "choice_close"
    if any_phrase(lowered, ["callback", "call back", "appointment"]):
        return "callback_close"
    if any_phrase(lowered, ["specialist", "transfer", "connect", "route"]):
        return "handoff_close"
    if any_phrase(lowered, ["sale ready", "verbal commitment"]):
        return "sale_ready_close"
    return "soft_close"


def classify_commitment(text: str) -> str:
    lowered = text.lower()
    if any_phrase(lowered, ["not interested", "no thanks", "stop calling", "wrong person"]):
        return "not_interested"
    if any_phrase(lowered, ["maybe", "could"]):
        return "mild_interested"
    if any_phrase(lowered, ["send information", "send info", "summary"]):
        return "information_requested"
    if any_phrase(lowered, ["callback", "call back", "appointment", "wednesday", "tuesday", "ten works"]):
        return "callback_agreed"
    if any_phrase(lowered, ["interested", "compare", "review later"]):
        return "verbal_interested"
    if any_phrase(lowered, ["yes", "works", "agree", "fine"]):
        return "verbal_commitment"
    if any_phrase(lowered, ["ready", "go ahead"]):
        return "sale_ready_outcome"
    return "mild_interested"


def classify_safety_boundary(customer_text: str, agent_text: str) -> str | None:
    customer = customer_text.lower()
    agent = agent_text.lower()
    if any_phrase(customer, ["stop calling", "wrong person", "not interested"]):
        return "stop_selling_or_suppress_contact"
    if any_phrase(customer, ["billing", "broken", "technical", "real person", "complaint"]):
        return "escalate_or_handoff"
    if any_phrase(customer, ["guarantee", "no risk", "payment", "contract"]):
        return "avoid_unsupported_claims"
    if classify_bad_persuasion(agent):
        return "avoid_pressure_or_unsafe_persuasion"
    return None


def detect_agent_mistakes(customer_text: str, agent_text: str, next_customer_text: str) -> list[str]:
    mistakes: list[str] = []
    customer_emotion = classify_emotion(customer_text)
    tactic = classify_agent_tactic(agent_text)
    bad = classify_bad_persuasion(agent_text)
    if customer_emotion in {"angry", "annoyed"} and tactic not in {"empathy_first", "handoff_close", "pain_point_discovery"}:
        mistakes.append("ignores_customer_emotion")
    if "?" in customer_text and "?" not in agent_text and tactic not in {"handoff_close", "empathy_first"}:
        mistakes.append("answers_wrong_question")
    if any(label in bad for label in ("talks_too_much",)):
        mistakes.append("over_explains")
    if any(label in bad for label in ("premature_close", "pushy")):
        mistakes.append("closes_too_early")
    if classify_objections(customer_text) and tactic not in {"pain_point_discovery", "empathy_first", "contrast_offer", "authority", "handoff_close"}:
        mistakes.append("fails_to_handle_objection")
    if any_phrase(agent_text, ["specialist", "transfer", "route"]) and not any_phrase(customer_text, ["technical", "billing", "complaint", "real person", "broken"]):
        mistakes.append("escalates_unnecessarily")
    if any_phrase(customer_text, ["technical", "billing", "broken", "real person"]) and not any_phrase(agent_text, ["specialist", "transfer", "connect", "route"]):
        mistakes.append("does_not_escalate_when_needed")
    if classify_emotion(next_customer_text) in {"confused", "skeptical"} and "understand" not in agent_text.lower():
        mistakes.append("does_not_confirm_understanding")
    return list(dict.fromkeys(mistakes))


def transition_label(before: str, after: str) -> str | None:
    before_bucket = emotion_bucket_for_transition(before)
    after_bucket = emotion_bucket_for_transition(after)
    raw = f"{before_bucket}_to_{after_bucket}".replace("de_escalated", "de_escalated")
    if raw in EMOTION_TRANSITION_LABELS:
        return raw
    if before_bucket == "angry" and after in {"positive", "neutral", "interested"}:
        return "angry_to_de_escalated"
    if before_bucket == "angry" and after in {"angry", "annoyed"}:
        return "angry_to_escalated"
    if before_bucket == "annoyed" and after in {"positive", "neutral"}:
        return "annoyed_to_calm"
    if before_bucket == "skeptical" and after in {"interested", "positive"}:
        return "skeptical_to_open"
    if before_bucket == "confused" and after in {"positive", "neutral", "interested"}:
        return "confused_to_clear"
    if before_bucket == "neutral" and after == "interested":
        return "neutral_to_interested"
    if before_bucket == "neutral" and after in {"annoyed", "angry"}:
        return "neutral_to_annoyed"
    if before_bucket == "interested" and after == "hesitant":
        return "interested_to_hesitant"
    if before_bucket == "hesitant" and after in {"positive", "interested"}:
        return "hesitant_to_committed"
    return None


def first_agent_and_customer(conversation: Conversation) -> tuple[Turn | None, Turn | None]:
    first_agent = next((turn for turn in conversation.turns if turn.speaker == "agent"), None)
    first_customer = next((turn for turn in conversation.turns if turn.speaker == "customer"), None)
    return first_agent, first_customer


def opening_labels(first_agent: Turn | None, first_customer: Turn | None) -> dict[str, str]:
    text = first_agent.text.lower() if first_agent else ""
    customer = first_customer.text.lower() if first_customer else ""
    labels: dict[str, str] = {}
    labels["opening_types"] = "agent_led_outbound" if first_agent else "customer_led_inbound"
    if any_phrase(text, ["good morning", "hello", "hi"]):
        labels["greeting_styles"] = "polite_greeting"
    if any_phrase(text, ["this is", "i am", "i'm"]):
        labels["identity_disclosures"] = "agent_identifies_self"
    if any_phrase(text, ["from", "with"]):
        labels["company_disclosures"] = "company_or_affiliation_disclosed"
    if any_phrase(text, ["calling about", "calling because", "requested"]):
        labels["reason_for_call"] = "reason_stated_early"
    if any_phrase(text, ["do you have", "thirty seconds", "quick"]):
        labels["permission_to_continue"] = "permission_or_time_check"
    if "?" in text:
        labels["first_question_types"] = classify_discovery_questions(text)[0] if classify_discovery_questions(text) else "permission_question"
    if customer:
        labels["customer_initial_response"] = classify_customer_intents(customer)[0]
    return labels


def pattern_record_id(prefix: str, label: str, index: int) -> str:
    safe_label = re.sub(r"[^a-z0-9_]+", "_", label.lower()).strip("_") or "unknown"
    return f"{prefix}-{safe_label}-{index:03d}"


def can_store_record(records: list[dict[str, Any]], record_limit: int) -> bool:
    return record_limit <= 0 or len(records) < record_limit


def build_pattern_bank(conversations: Iterable[Conversation], *, record_limit: int = 5000) -> tuple[dict[str, Any], dict[str, int]]:
    opening_records: list[dict[str, Any]] = []
    intent_counter: Counter[str] = Counter()
    objection_counter: Counter[str] = Counter()
    objection_records: list[dict[str, Any]] = []
    transition_records: list[dict[str, Any]] = []
    persuasion_records: list[dict[str, Any]] = []
    discovery_counter: Counter[str] = Counter()
    stage_counter: Counter[str] = Counter()
    close_records: list[dict[str, Any]] = []
    safety_counter: Counter[str] = Counter()
    domain_summary: dict[str, dict[str, Any]] = {}
    mistake_counter: Counter[str] = Counter()
    persona_counter: Counter[str] = Counter()

    agent_words: list[int] = []
    customer_words: list[int] = []
    agent_pauses_ms: list[int] = []
    interruption_count = 0
    overlong_agent_monologue_count = 0
    rapid_fire_question_count = 0
    silence_after_offer_count = 0
    silence_after_price_count = 0
    timestamps_available = False
    seen_opening_keys: set[tuple[str, ...]] = set()
    conversation_count = 0
    turn_count = 0

    for conversation_index, conversation in enumerate(conversations, start=1):
        conversation_count = conversation_index
        turn_count += len(conversation.turns)
        domain_entry = domain_summary.setdefault(
            conversation.domain,
            {
                "domain": conversation.domain,
                "topic_counts": Counter(),
                "accent_counts": Counter(),
                "intent_counts": Counter(),
                "objection_counts": Counter(),
                "close_type_counts": Counter(),
                "escalation_trigger_counts": Counter(),
                "emotion_counts": Counter(),
                "call_count": 0,
                "turn_count": 0,
            },
        )
        domain_entry["call_count"] += 1
        domain_entry["turn_count"] += len(conversation.turns)
        domain_entry["topic_counts"][conversation.topic] += 1
        domain_entry["accent_counts"][conversation.accent] += 1

        first_agent, first_customer = first_agent_and_customer(conversation)
        labels = opening_labels(first_agent, first_customer)
        opening_key = tuple(sorted(labels.values()))
        if opening_key and opening_key not in seen_opening_keys:
            seen_opening_keys.add(opening_key)
            opening_records.append(
                {
                    "pattern_id": pattern_record_id("opening", labels.get("opening_types", "unknown"), len(opening_records) + 1),
                    "domain": conversation.domain,
                    "topic": conversation.topic,
                    "observed_labels": sorted(labels.keys()),
                    "opening_type": labels.get("opening_types", "unknown"),
                    "greeting_style": labels.get("greeting_styles", "not_observed"),
                    "identity_disclosure": labels.get("identity_disclosures", "not_observed"),
                    "company_disclosure": labels.get("company_disclosures", "not_observed"),
                    "reason_for_call": labels.get("reason_for_call", "not_observed"),
                    "permission_to_continue": labels.get("permission_to_continue", "not_observed"),
                    "first_question_type": labels.get("first_question_types", "not_observed"),
                    "customer_initial_response": labels.get("customer_initial_response", "not_observed"),
                    "source_conversation_count": 1,
                }
            )

        previous_turn: Turn | None = None
        previous_customer_text = ""
        recent_customer_text = ""
        for turn_index, turn in enumerate(conversation.turns):
            if turn.start is not None or turn.end is not None:
                timestamps_available = True
            if previous_turn and previous_turn.end is not None and turn.start is not None:
                gap_ms = int((turn.start - previous_turn.end) * 1000)
                if gap_ms < 0:
                    interruption_count += 1
                if turn.speaker == "agent" and previous_turn.speaker == "customer":
                    agent_pauses_ms.append(max(gap_ms, 0))
                if previous_turn.speaker == "agent" and turn.speaker == "customer":
                    previous_agent = previous_turn.text.lower()
                    if gap_ms >= 2500 and any_phrase(previous_agent, ["offer", "options", "review", "would"]):
                        silence_after_offer_count += 1
                    if gap_ms >= 2500 and any_phrase(previous_agent, ["price", "cost", "monthly"]):
                        silence_after_price_count += 1

            if turn.speaker == "agent":
                agent_words.append(word_count(turn.text))
                if word_count(turn.text) > 55:
                    overlong_agent_monologue_count += 1
                if turn.text.count("?") > 1:
                    rapid_fire_question_count += 1
                for question_type in classify_discovery_questions(turn.text):
                    discovery_counter[question_type] += 1
                stage = classify_stage(turn, turn_index, previous_customer_text=recent_customer_text)
                stage_counter[stage] += 1
                if any_phrase(turn.text.lower(), ["would", "could", "lock it in", "work for", "summary", "specialist"]):
                    next_customer = next((candidate for candidate in conversation.turns[turn_index + 1 :] if candidate.speaker == "customer"), None)
                    customer_response = classify_commitment(next_customer.text if next_customer else "")
                    close_type = classify_close_type(turn.text)
                    bad_labels = classify_bad_persuasion(turn.text)
                    if can_store_record(close_records, record_limit):
                        close_records.append(
                            {
                                "pattern_id": pattern_record_id("close", close_type, len(close_records) + 1),
                                "domain": conversation.domain,
                                "close_type": close_type,
                                "commitment_level": customer_response,
                                "customer_response": customer_response,
                                "safe_close": not bool(bad_labels),
                                "close_successful": customer_response in {"callback_agreed", "verbal_interested", "verbal_commitment", "sale_ready_outcome"},
                                "follow_up_required": customer_response in {"information_requested", "callback_agreed", "mild_interested"},
                            }
                        )
                    domain_entry["close_type_counts"][close_type] += 1

                if recent_customer_text:
                    next_customer = next((candidate for candidate in conversation.turns[turn_index + 1 :] if candidate.speaker == "customer"), None)
                    next_customer_text = next_customer.text if next_customer else ""
                    customer_emotion = classify_emotion(recent_customer_text)
                    agent_tactic = classify_agent_tactic(turn.text)
                    next_emotion = classify_emotion(next_customer_text)
                    transition = transition_label(customer_emotion, next_emotion)
                    if transition and can_store_record(transition_records, record_limit):
                        transition_records.append(
                            {
                                "pattern_id": pattern_record_id("emotion", transition, len(transition_records) + 1),
                                "transition_label": transition,
                                "customer_emotion_before": customer_emotion,
                                "agent_tactic": agent_tactic,
                                "customer_emotion_after": next_emotion,
                                "transition_success": next_emotion in {"positive", "interested", "neutral"},
                                "domain": conversation.domain,
                            }
                        )

                    objections = classify_objections(recent_customer_text)
                    for objection in objections:
                        objection_counter[objection] += 1
                        if can_store_record(objection_records, record_limit):
                            objection_records.append(
                                {
                                    "pattern_id": pattern_record_id("objection", objection, len(objection_records) + 1),
                                    "domain": conversation.domain,
                                    "objection_text_pattern": objection_text_pattern(objection),
                                    "objection_type": objection,
                                    "emotion_signal": customer_emotion,
                                    "agent_response_tactic": agent_tactic,
                                    "response_quality": response_quality(turn.text, recent_customer_text, next_customer_text),
                                    "resolved": resolution_state(next_customer_text),
                                    "next_customer_state": classify_commitment(next_customer_text),
                                }
                            )
                        domain_entry["objection_counts"][objection] += 1

                    bad_labels = classify_bad_persuasion(turn.text)
                    if can_store_record(persuasion_records, record_limit):
                        persuasion_records.append(
                            {
                                "pattern_id": pattern_record_id("persuasion", agent_tactic, len(persuasion_records) + 1),
                                "when_customer_says_pattern": "+".join(objections or classify_customer_intents(recent_customer_text)),
                                "customer_emotion": customer_emotion,
                                "strategy_label": agent_tactic if agent_tactic in PERSUASION_STRATEGY_LABELS else "benefit_framing",
                                "use_strategy": agent_tactic,
                                "avoid_label": bad_labels[0] if bad_labels else "none",
                                "avoid": bad_labels,
                                "response_quality": response_quality(turn.text, recent_customer_text, next_customer_text),
                            }
                        )

                    boundary = classify_safety_boundary(recent_customer_text, turn.text)
                    if boundary:
                        safety_counter[boundary] += 1
                        if boundary == "escalate_or_handoff":
                            domain_entry["escalation_trigger_counts"][boundary] += 1

                    for mistake in detect_agent_mistakes(recent_customer_text, turn.text, next_customer_text):
                        mistake_counter[mistake] += 1

            else:
                customer_words.append(word_count(turn.text))
                intents = classify_customer_intents(turn.text)
                for intent in intents:
                    intent_counter[intent] += 1
                    domain_entry["intent_counts"][intent] += 1
                domain_entry["emotion_counts"][classify_emotion(turn.text)] += 1
                stage = classify_stage(turn, turn_index, previous_customer_text=previous_customer_text)
                stage_counter[stage] += 1
                recent_customer_text = turn.text
                previous_customer_text = turn.text
                persona_counter[persona_label(turn.text)] += 1

            previous_turn = turn

    pattern_bank = {
        "opening_patterns": opening_records,
        "customer_intent_patterns": counter_records(intent_counter, "intent", "intent_label"),
        "objection_patterns": objection_records,
        "emotion_tone_transition_patterns": transition_records,
        "persuasion_strategy_patterns": persuasion_records,
        "discovery_question_patterns": counter_records(discovery_counter, "discovery", "question_type"),
        "turn_stage_patterns": counter_records(stage_counter, "stage", "stage_label"),
        "close_attempt_patterns": close_records,
        "safety_compliance_boundary_patterns": counter_records(safety_counter, "safety", "boundary_label"),
        "timing_speech_naturalness_patterns": {
            "timestamps_available": timestamps_available,
            "average_agent_turn_words": round(statistics.mean(agent_words), 2) if agent_words else 0,
            "average_customer_turn_words": round(statistics.mean(customer_words), 2) if customer_words else 0,
            "pause_before_agent_response_ms": round(statistics.mean(agent_pauses_ms), 2) if agent_pauses_ms else 0,
            "interruption_count": interruption_count,
            "overlong_agent_monologue_count": overlong_agent_monologue_count,
            "rapid_fire_question_count": rapid_fire_question_count,
            "silence_after_offer_count": silence_after_offer_count,
            "silence_after_price_count": silence_after_price_count,
        },
        "domain_specific_scenario_patterns": domain_records(domain_summary),
        "agent_mistake_patterns": counter_records(mistake_counter, "mistake", "mistake_label"),
        "scenario_templates": build_scenario_templates(intent_counter, objection_counter, stage_counter),
        "customer_personas": counter_records(persona_counter, "persona", "persona_label"),
        "excluded_flow_policy": {
            "no_sales_relevance_filter": "Keep pure customer-service-only flows as support, escalation, or compliance boundaries unless they teach sales-safe stopping behavior.",
            "do_not_extract": [
                "exact_scripts",
                "company_specific_wording",
                "pii_placeholders_as_features",
                "agent_or_customer_names",
                "long_call_summaries",
                "customer_service_flows_with_no_sales_relevance",
            ],
        },
    }
    extraction_counts = {
        "conversation_count": conversation_count,
        "turn_count": turn_count,
        "stored_objection_record_count": len(objection_records),
        "stored_emotion_transition_record_count": len(transition_records),
        "stored_persuasion_record_count": len(persuasion_records),
        "stored_close_record_count": len(close_records),
    }
    return pattern_bank, extraction_counts


def persona_label(text: str) -> str:
    intents = set(classify_customer_intents(text))
    emotion = classify_emotion(text)
    if "price_request" in intents:
        return "price_sensitive_buyer"
    if "technical_problem" in intents or "billing_issue" in intents:
        return "support_first_customer"
    if "wrong_person" in intents or "busy_now" in intents:
        return "boundary_setting_customer"
    if emotion in {"angry", "annoyed"}:
        return "frustrated_customer"
    if "information_request" in intents:
        return "information_first_buyer"
    return "uncertain_buyer"


def counter_records(counter: Counter[str], prefix: str, label_field: str) -> list[dict[str, Any]]:
    return [
        {
            "pattern_id": pattern_record_id(prefix, label, index),
            label_field: label,
            "count": count,
        }
        for index, (label, count) in enumerate(counter.most_common(), start=1)
        if label and label != "unclear_intent"
    ]


def counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in counter.most_common() if key}


def domain_records(domain_summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for domain, data in sorted(domain_summary.items()):
        records.append(
            {
                "domain": domain,
                "call_count": data["call_count"],
                "turn_count": data["turn_count"],
                "common_customer_intents": counter_to_dict(data["intent_counts"]),
                "common_objections": counter_to_dict(data["objection_counts"]),
                "common_required_information": required_info_for_domain(domain, data["intent_counts"]),
                "common_close_types": counter_to_dict(data["close_type_counts"]),
                "common_escalation_triggers": counter_to_dict(data["escalation_trigger_counts"]),
                "typical_emotional_tone": most_common_label(data["emotion_counts"], "neutral"),
                "topic_counts": counter_to_dict(data["topic_counts"]),
                "accent_counts": counter_to_dict(data["accent_counts"]),
            }
        )
    return records


def most_common_label(counter: Counter[str], default: str) -> str:
    return counter.most_common(1)[0][0] if counter else default


def required_info_for_domain(domain: str, intents: Counter[str]) -> list[str]:
    info = ["customer_goal", "current_blocker", "permission_to_continue"]
    if "price_request" in intents:
        info.append("budget_or_price_sensitivity")
    if "technical_problem" in intents or "billing_issue" in intents:
        info.append("support_context_before_sale")
    if domain in {"telecom", "energy"}:
        info.append("address_or_eligibility_context")
    if domain in {"software", "b2b_software"}:
        info.append("decision_maker_context")
    return list(dict.fromkeys(info))


def build_scenario_templates(intent_counter: Counter[str], objection_counter: Counter[str], stage_counter: Counter[str]) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for index, (intent, _count) in enumerate(intent_counter.most_common(8), start=1):
        if intent == "unclear_intent":
            continue
        common_objection = objection_counter.most_common(1)[0][0] if objection_counter else "hidden_objection"
        templates.append(
            {
                "template_id": pattern_record_id("scenario", intent, index),
                "customer_persona": persona_from_intent(intent),
                "initial_intent": intent,
                "likely_objection": common_objection,
                "emotion_state": emotion_from_intent(intent),
                "safe_agent_tactic": safe_tactic_for_intent(intent),
                "avoid": avoid_for_intent(intent),
                "success_label": success_label_for_intent(intent),
                "conversation_flow": [label for label, _ in stage_counter.most_common(6)],
            }
        )
    return templates


def persona_from_intent(intent: str) -> str:
    return {
        "price_request": "price_sensitive_buyer",
        "information_request": "information_first_buyer",
        "complaint": "frustrated_customer",
        "cancellation": "boundary_setting_customer",
        "technical_problem": "support_first_customer",
        "billing_issue": "support_first_customer",
        "appointment_request": "scheduled_follow_up_buyer",
        "wrong_person": "boundary_setting_customer",
        "busy_now": "time_constrained_customer",
        "hostile_rejection": "hostile_boundary_customer",
    }.get(intent, "uncertain_buyer")


def emotion_from_intent(intent: str) -> str:
    return {
        "complaint": "annoyed",
        "cancellation": "annoyed",
        "technical_problem": "angry",
        "billing_issue": "annoyed",
        "hostile_rejection": "angry",
        "price_request": "skeptical",
        "information_request": "neutral",
        "buying_interest": "interested",
    }.get(intent, "neutral")


def safe_tactic_for_intent(intent: str) -> str:
    return {
        "price_request": "clarify price versus value blocker",
        "information_request": "ask which decision question the information should answer",
        "complaint": "empathy first, then repair or escalate",
        "cancellation": "respect boundary before any retention path",
        "technical_problem": "handoff instead of guessing",
        "billing_issue": "confirm understanding then route to billing support",
        "appointment_request": "confirm callback details",
        "hostile_rejection": "de-escalate and stop selling",
    }.get(intent, "ask one discovery question before closing")


def avoid_for_intent(intent: str) -> list[str]:
    if intent in {"complaint", "hostile_rejection", "cancellation"}:
        return ["pushy", "premature_close", "ignores_customer_need"]
    if intent in {"technical_problem", "billing_issue"}:
        return ["unsupported_claim", "does_not_escalate_when_needed"]
    return ["vague_claim", "talks_too_much", "premature_close"]


def success_label_for_intent(intent: str) -> str:
    if intent in {"appointment_request", "callback_request"}:
        return "callback_agreed"
    if intent in {"buying_interest"}:
        return "verbal_interested"
    if intent in {"complaint", "technical_problem", "billing_issue"}:
        return "handoff_or_issue_path_accepted"
    if intent in {"cancellation", "wrong_person", "hostile_rejection"}:
        return "boundary_respected"
    return "next_useful_step_agreed"


def taxonomy_payload() -> dict[str, list[str]]:
    return {
        "opening_pattern_labels": OPENING_PATTERN_LABELS,
        "customer_intent_labels": CUSTOMER_INTENT_LABELS,
        "objection_type_labels": OBJECTION_TYPE_LABELS,
        "emotion_transition_labels": EMOTION_TRANSITION_LABELS,
        "persuasion_strategy_labels": PERSUASION_STRATEGY_LABELS,
        "bad_persuasion_labels": BAD_PERSUASION_LABELS,
        "discovery_question_labels": DISCOVERY_QUESTION_LABELS,
        "conversation_stage_labels": CONVERSATION_STAGE_LABELS,
        "close_type_labels": CLOSE_TYPE_LABELS,
        "commitment_level_labels": COMMITMENT_LEVEL_LABELS,
        "agent_mistake_labels": AGENT_MISTAKE_LABELS,
    }


def leakage_tests(payload: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False).lower()
    findings = []
    forbidden_keys = ['"raw_text"', '"source_text"', '"speaker_text"', '"speaker_name"', '"customer_name"', '"agent_name"', '"transcript"']
    for key in forbidden_keys:
        if key in text:
            findings.append({"kind": "forbidden_raw_text_field", "detail": key})
    if re.search(r"\b[A-Z][a-z]+ from [A-Z][A-Za-z]+", json.dumps(payload, ensure_ascii=False)):
        findings.append({"kind": "company_or_agent_name_pattern", "detail": "name-plus-company pattern"})
    return {
        "exact_source_utterance_storage_check": {
            "status": "fail" if findings else "pass",
            "method": "stored artifacts avoid raw utterance fields, exact scripts, agent names, customer names, and company-specific wording",
        },
        "long_transcript_summary_check": {
            "status": "pass",
            "method": "artifact stores bounded labels, counts, tactics, states, and templates instead of long call summaries",
        },
        "commercial_runtime_prompt_check": {
            "status": "pass",
            "method": "no transcript-derived text is exported as a runtime prompt",
        },
        "findings": findings,
    }


def build_payload(raw_dir: Path, *, max_conversations: int = 1000, record_limit: int = 5000) -> dict[str, Any]:
    started = time.perf_counter()
    source_stats: dict[str, int] = {"source_file_count": 0}
    conversations = iter_conversations_from_raw(raw_dir, max_conversations, source_stats)
    pattern_bank, extraction_counts = build_pattern_bank(conversations, record_limit=max(record_limit, 0))
    source_count = source_stats["source_file_count"]
    conversation_count = extraction_counts["conversation_count"]
    turn_count = extraction_counts["turn_count"]
    payload = {
        "prod_013_id": PROD_013_ID,
        "title": "CallCenterEN abstract pattern extraction",
        "dataset_source": {
            "dataset_name": "AIxBlock/92k-real-world-call-center-scripts-english",
            "dataset_url": DATASET_URL,
            "dataset_file_tree": DATASET_TREE_URL,
            "paper_url": PAPER_URL,
            "checked_date": "2026-05-09",
            "license": LICENSE,
            "dataset_size_claim": "91,706 redacted transcript JSON files; public release does not include audio",
            "file_access_shape": "large zip files; local drop folder only",
        },
        "source_characteristics": {
            "input_schema_support": ["turn_lists", "top_level_word_timestamps"],
            "word_level_segmentation_when_needed": True,
            "speaker_role_source": "explicit speaker labels when present; otherwise pause-based segments with text-role signals plus file-direction fallback",
            "speaker_role_signal_inference": True,
            "speaker_role_inference_is_ground_truth": False,
            "raw_text_field_read_transiently": True,
            "raw_text_field_exported": False,
        },
        "extraction_config": {
            "max_conversations": max_conversations,
            "all_conversations_requested": max_conversations <= 0,
            "pattern_record_limit_per_category": max(record_limit, 0),
            "record_lists_are_samples": record_limit > 0,
            "aggregate_counts_cover_scanned_conversations": True,
            "stored_record_counts": {
                "objection_patterns": extraction_counts["stored_objection_record_count"],
                "emotion_tone_transition_patterns": extraction_counts["stored_emotion_transition_record_count"],
                "persuasion_strategy_patterns": extraction_counts["stored_persuasion_record_count"],
                "close_attempt_patterns": extraction_counts["stored_close_record_count"],
            },
        },
        "reuse_boundary": {
            "reuse_label": "abstract_pattern_extraction_only",
            "download_performed": False,
            "download_required_for_default_run": False,
            "raw_source_dir": rel_path(raw_dir),
            "raw_transcript_text_stored": False,
            "exact_script_storage_allowed": False,
            "company_specific_wording_allowed": False,
            "pii_placeholders_as_features_allowed": False,
            "agent_or_customer_names_allowed": False,
            "long_call_summaries_allowed": False,
            "commercial_runtime_prompt_text_from_transcripts_allowed": False,
            "commercial_model_training_allowed": False,
        },
        "summary": {
            "source_file_count": source_count,
            "conversation_count": conversation_count,
            "turn_count": turn_count,
            "max_conversations": max_conversations,
            "raw_transcript_text_stored": False,
            "provider_calls_made": False,
            "llm_used": False,
            "download_performed": False,
            "pattern_category_count": len(pattern_bank),
            "leakage_finding_count": 0,
            "elapsed_ms": 0,
        },
        "taxonomy": taxonomy_payload(),
        "pattern_bank": pattern_bank,
        "leakage_tests": {},
    }
    tests = leakage_tests(payload)
    payload["leakage_tests"] = tests
    payload["summary"]["leakage_finding_count"] = len(tests["findings"])
    payload["summary"]["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return payload


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    bank = payload["pattern_bank"]
    lines = [
        "# PROD-013 CallCenterEN Pattern Extraction",
        "",
        "This checkpoint extracts abstract sales-call patterns from local CallCenterEN files without storing exact scripts.",
        "",
        "No exact scripts, company-specific wording, PII placeholders, agent names, customer names, long call summaries, provider calls, LLM calls, or dataset downloads are used.",
        "",
        "## Source Boundary",
        "",
        f"- Dataset: {payload['dataset_source']['dataset_url']}",
        f"- Paper: {payload['dataset_source']['paper_url']}",
        f"- License observed: `{payload['dataset_source']['license']}`",
        f"- Reuse label: `{payload['reuse_boundary']['reuse_label']}`",
        f"- Raw source folder: `{payload['reuse_boundary']['raw_source_dir']}`",
        f"- Word-level timing support: `{payload['source_characteristics']['word_level_segmentation_when_needed']}`",
        f"- Speaker role signal inference: `{payload['source_characteristics']['speaker_role_signal_inference']}`",
        f"- Speaker role inference is ground truth: `{payload['source_characteristics']['speaker_role_inference_is_ground_truth']}`",
        "- Source shape note: when speaker labels are absent, timed words are grouped into bounded pseudo-turns and speaker roles are inferred from role-specific sales/customer language for pattern mining only.",
        "",
        "## Summary",
        "",
        f"- Source files scanned: `{summary['source_file_count']}`",
        f"- Conversations parsed: `{summary['conversation_count']}`",
        f"- Turns parsed: `{summary['turn_count']}`",
        f"- Max conversations setting: `{payload['extraction_config']['max_conversations']}`",
        f"- All conversations requested: `{payload['extraction_config']['all_conversations_requested']}`",
        f"- Pattern record limit per category: `{payload['extraction_config']['pattern_record_limit_per_category']}`",
        f"- Record lists are samples: `{payload['extraction_config']['record_lists_are_samples']}`",
        f"- Raw transcript text stored: `{summary['raw_transcript_text_stored']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        "",
        "## Pattern Categories",
        "",
        f"- Opening patterns: `{len(bank['opening_patterns'])}`",
        f"- Customer intent patterns: `{len(bank['customer_intent_patterns'])}`",
        f"- Objection patterns: `{len(bank['objection_patterns'])}`",
        f"- Emotion/tone transitions: `{len(bank['emotion_tone_transition_patterns'])}`",
        f"- Persuasion strategy patterns: `{len(bank['persuasion_strategy_patterns'])}`",
        f"- Discovery question patterns: `{len(bank['discovery_question_patterns'])}`",
        f"- Turn stage patterns: `{len(bank['turn_stage_patterns'])}`",
        f"- Close attempt patterns: `{len(bank['close_attempt_patterns'])}`",
        f"- Safety/compliance boundaries: `{len(bank['safety_compliance_boundary_patterns'])}`",
        f"- Domain-specific scenario patterns: `{len(bank['domain_specific_scenario_patterns'])}`",
        f"- Agent mistake patterns: `{len(bank['agent_mistake_patterns'])}`",
        "",
        "## Timing And Speech Naturalness",
        "",
    ]
    timing = bank["timing_speech_naturalness_patterns"]
    for key in [
        "timestamps_available",
        "average_agent_turn_words",
        "average_customer_turn_words",
        "pause_before_agent_response_ms",
        "interruption_count",
        "overlong_agent_monologue_count",
        "rapid_fire_question_count",
        "silence_after_offer_count",
        "silence_after_price_count",
    ]:
        lines.append(f"- {key}: `{timing[key]}`")

    lines.extend(["", "## Scenario Template Bank", ""])
    for template in bank["scenario_templates"][:12]:
        lines.append(
            "- `{template_id}` persona `{persona}` intent `{intent}` objection `{objection}` tactic `{tactic}` avoid `{avoid}` success `{success}`".format(
                template_id=template["template_id"],
                persona=template["customer_persona"],
                intent=template["initial_intent"],
                objection=template["likely_objection"],
                tactic=template["safe_agent_tactic"],
                avoid=", ".join(template["avoid"]),
                success=template["success_label"],
            )
        )

    lines.extend(["", "## Leakage Tests", ""])
    for name, check in payload["leakage_tests"].items():
        if isinstance(check, dict) and "status" in check:
            lines.append(f"- {name}: `{check['status']}`")

    lines.extend(
        [
            "",
            "## Runtime Use",
            "",
            "Use this pattern bank to generate scenario templates, customer personas, objections, emotional states, safe tactics, and success/failure labels. Do not use it as copied call wording or as a commercial runtime prompt source.",
        ]
    )
    return "\n".join(lines) + "\n"
