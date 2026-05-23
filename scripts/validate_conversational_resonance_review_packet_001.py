"""Validate the conversational resonance review packet.

The validator checks packet completeness, parseability, coverage, redaction,
side-effect boundaries, and human-review boundaries. It does not judge final
resonance or commercial quality.
"""

from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "CONVERSATIONAL-RESONANCE-REVIEW-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = [
    "review_packet.md",
    "review_packet.json",
    "review_packet.jsonl",
    "review_index.md",
    "rubric.md",
    "redaction_report.json",
    "result.json",
    "report.md",
]

REQUIRED_CAMPAIGNS = {
    "routesignal_live_demo",
    "synthetic-insurance-review",
    "synthetic-b2b-saas-operations",
    "synthetic-automotive-service-review",
    "synthetic-home-services-estimate",
}

REQUIRED_ARCS = {
    "casual_small_talk",
    "busy_distracted",
    "serious_hardship_bad_timing",
    "financial_stress_budget_emotion",
    "prior_bad_experience",
    "family_stakeholder_context",
    "joking_sarcasm",
    "emotional_frustration_venting",
    "irrelevant_story_off_topic_ramble",
    "sensitive_personal_data_boundary",
    "b2c_home_life_interruption",
    "b2b_workplace_interruption",
}

SIDE_EFFECT_KEYS = {
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
}

RUBRIC_DIMENSIONS = [
    "Human acknowledgement",
    "Emotional appropriateness",
    "Timing sensitivity",
    "Trust preservation",
    "Sales control",
    "Relevance bridge quality",
    "No over-sharing / no probing",
    "Sensitive data boundary",
    "Stop/continue judgment",
    "Naturalness and human feel",
    "Commercial usefulness",
]

SENSITIVE_PLACEHOLDERS = [
    "[REDACTED_MEDICAL_DETAIL]",
    "[REDACTED_ACCOUNT_NUMBER]",
    "[REDACTED_PERSONAL_ID]",
    "[REDACTED_FAMILY_DETAIL]",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]

RAW_SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    re.compile(r"(?i)\baccount number is\s+\d+"),
    re.compile(r"(?i)\bpersonal id is\s+\d+"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def all_packet_text() -> str:
    chunks: list[str] = []
    for name in REQUIRED_FILES:
        path = OUT_DIR / name
        if path.exists():
            chunks.append(read_text(path))
    return "\n".join(chunks)


def side_effect_failures(record: dict[str, Any], prefix: str) -> list[str]:
    failures: list[str] = []
    flags = record.get("side_effect_flags") or {}
    for key in SIDE_EFFECT_KEYS:
        if bool(flags.get(key)):
            failures.append(f"{prefix}: side-effect flag true: {key}")
    return failures


def validate() -> dict[str, Any]:
    failures: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (OUT_DIR / name).exists()]
    for name in missing:
        add_failure(failures, f"missing required output file: {name}")
    if missing:
        return {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "failed",
            "failures": failures,
            "conversation_count": 0,
            "turn_count": 0,
        }

    packet = load_json(OUT_DIR / "review_packet.json")
    redaction = load_json(OUT_DIR / "redaction_report.json")
    result = load_json(OUT_DIR / "result.json")
    conversations = packet.get("conversations") or []

    jsonl_records: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_text(OUT_DIR / "review_packet.jsonl").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            jsonl_records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            add_failure(failures, f"review_packet.jsonl line {line_number} does not parse: {exc}")

    if len(conversations) < 60:
        add_failure(failures, f"expected at least 60 conversations, got {len(conversations)}")

    campaigns = {str(item.get("campaign_id") or "") for item in conversations}
    missing_campaigns = sorted(REQUIRED_CAMPAIGNS - campaigns)
    if missing_campaigns:
        add_failure(failures, f"missing campaign coverage: {missing_campaigns}")

    arcs = {str(item.get("arc_type") or "") for item in conversations}
    missing_arcs = sorted(REQUIRED_ARCS - arcs)
    if missing_arcs:
        add_failure(failures, f"missing arc coverage: {missing_arcs}")

    turn_count = sum(len(item.get("turns") or []) for item in conversations)
    if turn_count < 300:
        add_failure(failures, f"expected at least 300 turn-level records, got {turn_count}")
    if len(jsonl_records) < 300:
        add_failure(failures, f"expected at least 300 JSONL turn records, got {len(jsonl_records)}")

    for conversation in conversations:
        conversation_id = str(conversation.get("conversation_id") or "<missing>")
        if conversation.get("requires_human_sales_review") is not True:
            add_failure(failures, f"{conversation_id}: requires_human_sales_review is not true")
        if conversation.get("codex_assigned_final_resonance_quality") is not False:
            add_failure(failures, f"{conversation_id}: Codex assigned final resonance quality")
        if conversation.get("codex_assigned_final_sales_quality") is not False:
            add_failure(failures, f"{conversation_id}: Codex assigned final sales quality")
        scorecard = conversation.get("human_resonance_scorecard") or {}
        if scorecard.get("qualitative_label") is not None:
            add_failure(failures, f"{conversation_id}: qualitative label was prefilled")
        if "final_resonance_pass" in conversation or "final_resonance_fail" in conversation:
            add_failure(failures, f"{conversation_id}: final resonance pass/fail field present")
        if "final_sales_quality_pass" in conversation or "final_sales_quality_fail" in conversation:
            add_failure(failures, f"{conversation_id}: final sales-quality pass/fail field present")
        failures.extend(side_effect_failures(conversation, conversation_id))
        for turn in conversation.get("turns") or []:
            turn_id = f"{conversation_id}/turn-{turn.get('turn_index')}"
            if turn.get("requires_human_sales_review") is not True:
                add_failure(failures, f"{turn_id}: requires_human_sales_review is not true")
            failures.extend(side_effect_failures(turn, turn_id))

    packet_text = all_packet_text()
    if EMAIL_PATTERN.search(packet_text):
        add_failure(failures, "raw email-like value found in packet")
    for pattern in SECRET_PATTERNS:
        if pattern.search(packet_text):
            add_failure(failures, f"secret-looking pattern found: {pattern.pattern}")
    for pattern in RAW_SENSITIVE_PATTERNS:
        if pattern.search(packet_text):
            add_failure(failures, f"raw sensitive-looking pattern found: {pattern.pattern}")
    for placeholder in SENSITIVE_PLACEHOLDERS:
        if placeholder not in packet_text:
            add_failure(failures, f"sensitive placeholder missing: {placeholder}")
        if placeholder not in (redaction.get("redactions_applied") or []):
            add_failure(failures, f"redaction report missing placeholder: {placeholder}")

    if redaction.get("raw_email_like_values_found") not in (0, [], None):
        add_failure(failures, "redaction report found raw email-like values")
    if redaction.get("secret_like_values_found") not in (0, [], None):
        add_failure(failures, "redaction report found secret-like values")
    for key in SIDE_EFFECT_KEYS:
        if bool(redaction.get(key)):
            add_failure(failures, f"redaction side-effect flag true: {key}")

    rubric_md = read_text(OUT_DIR / "rubric.md")
    for dimension in RUBRIC_DIMENSIONS:
        if dimension not in rubric_md:
            add_failure(failures, f"rubric.md missing scoring dimension: {dimension}")

    review_packet_md = read_text(OUT_DIR / "review_packet.md")
    if "Rubric Summary" not in review_packet_md:
        add_failure(failures, "review_packet.md missing rubric summary")
    if "Conversation Index" not in review_packet_md:
        add_failure(failures, "review_packet.md missing conversation index")

    report_md = read_text(OUT_DIR / "report.md")
    for required in [
        "## 5. Resonance Warning Counts",
        "## 7. Most Concerning Conversations By Mechanical Signals Only",
        "## 8. Safety Boundary Summary",
        "## 10. Preliminary Recommendation Only",
    ]:
        if required not in report_md:
            add_failure(failures, f"report.md missing section: {required}")

    if result.get("codex_did_not_assign_final_resonance_quality") is not True:
        add_failure(failures, "result did not preserve resonance human-review boundary")
    if result.get("codex_did_not_assign_final_sales_quality") is not True:
        add_failure(failures, "result did not preserve sales human-review boundary")

    warning_counts = Counter()
    for conversation in conversations:
        warning_counts.update(conversation.get("resonance_warning_flags") or [])
        for turn in conversation.get("turns") or []:
            warning_counts.update(turn.get("resonance_warning_flags") or [])

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "conversation_count": len(conversations),
        "turn_count": turn_count,
        "jsonl_record_count": len(jsonl_records),
        "campaigns": sorted(campaigns),
        "arc_types": sorted(arcs),
        "resonance_warning_counts": dict(sorted(warning_counts.items())),
        "side_effect_flags_all_false": not any(
            bool((conversation.get("side_effect_flags") or {}).get(key))
            for conversation in conversations
            for key in SIDE_EFFECT_KEYS
        ),
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
