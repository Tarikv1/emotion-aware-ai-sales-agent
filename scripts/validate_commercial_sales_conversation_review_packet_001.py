"""Validate the commercial sales conversation review packet.

This validator checks packet completeness, parseability, coverage, redaction,
human-review boundaries, and provider side-effect boundaries. It does not judge
commercial sales quality.
"""

from __future__ import annotations

from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "COMMERCIAL-SALES-CONVERSATION-REVIEW-001"
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
    "smooth_qualified_appointment",
    "time_pressure",
    "tentative_pain",
    "direct_question",
    "objection",
    "trust_challenge",
    "confusion_loop_resistance",
    "social_conversation_management",
    "asr_garble",
    "no_fit_stop",
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
    "Opening clarity",
    "Permission handling",
    "Buyer acknowledgement",
    "Direct question answering",
    "Pain discovery quality",
    "Implication / consequence development",
    "Objection handling and reframing",
    "Trust / transparency",
    "Conversation control",
    "Appointment-readiness timing",
    "Close / next-step strength",
    "Naturalness and human feel",
    "Safety and claim discipline",
    "Memory / no-loop behavior",
    "Commercial usefulness",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
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
    conversations = packet.get("conversations") or []
    drift_findings = packet.get("universalization_drift_findings") or []

    jsonl_records: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_text(OUT_DIR / "review_packet.jsonl").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            jsonl_records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            add_failure(failures, f"review_packet.jsonl line {line_number} does not parse: {exc}")

    if len(conversations) < 50:
        add_failure(failures, f"expected at least 50 conversations, got {len(conversations)}")
    if len(jsonl_records) != len(conversations):
        add_failure(
            failures,
            f"expected JSONL conversation count {len(conversations)}, got {len(jsonl_records)}",
        )

    campaigns = {str(item.get("campaign_id") or "") for item in conversations}
    missing_campaigns = sorted(REQUIRED_CAMPAIGNS - campaigns)
    if missing_campaigns:
        add_failure(failures, f"missing campaign coverage: {missing_campaigns}")

    arcs = {str(item.get("arc_type") or "") for item in conversations}
    missing_arcs = sorted(REQUIRED_ARCS - arcs)
    if missing_arcs:
        add_failure(failures, f"missing arc coverage: {missing_arcs}")

    turn_count = sum(len(item.get("turns") or []) for item in conversations)
    if turn_count < 250:
        add_failure(failures, f"expected at least 250 turn-level records, got {turn_count}")

    for conversation in conversations:
        conversation_id = str(conversation.get("conversation_id") or "<missing>")
        if conversation.get("requires_human_sales_review") is not True:
            add_failure(failures, f"{conversation_id}: requires_human_sales_review is not true")
        if conversation.get("codex_assigned_final_sales_quality") is not False:
            add_failure(failures, f"{conversation_id}: Codex assigned final sales quality")
        scorecard = conversation.get("human_sales_quality_scorecard") or {}
        if scorecard.get("qualitative_label") is not None:
            add_failure(failures, f"{conversation_id}: qualitative label was prefilled")
        if "final_sales_quality_pass" in conversation or "final_sales_quality_fail" in conversation:
            add_failure(failures, f"{conversation_id}: final sales-quality pass/fail field present")
        failures.extend(side_effect_failures(conversation, conversation_id))
        for turn in conversation.get("turns") or []:
            turn_id = f"{conversation_id}/turn-{turn.get('turn_index')}"
            failures.extend(side_effect_failures(turn, turn_id))

    packet_text = all_packet_text()
    if EMAIL_PATTERN.search(packet_text):
        add_failure(failures, "raw email-like value found in packet")
    for pattern in SECRET_PATTERNS:
        if pattern.search(packet_text):
            add_failure(failures, f"secret-looking pattern found: {pattern.pattern}")

    if redaction.get("raw_email_like_values_found") not in (0, [], None):
        add_failure(failures, "redaction report found raw email-like values")
    if redaction.get("secret_like_values_found") not in (0, [], None):
        add_failure(failures, "redaction report found secret-like values")

    review_packet_md = read_text(OUT_DIR / "review_packet.md")
    if "Rubric Summary" not in review_packet_md:
        add_failure(failures, "review_packet.md missing rubric summary")
    if "Conversation Index" not in review_packet_md:
        add_failure(failures, "review_packet.md missing conversation index")

    rubric_md = read_text(OUT_DIR / "rubric.md")
    for dimension in RUBRIC_DIMENSIONS:
        if dimension not in rubric_md:
            add_failure(failures, f"rubric.md missing scoring dimension: {dimension}")

    warning_counts = Counter()
    for conversation in conversations:
        warning_counts.update(conversation.get("mechanical_warning_flags") or [])
        for turn in conversation.get("turns") or []:
            warning_counts.update(turn.get("mechanical_warning_flags") or [])

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "conversation_count": len(conversations),
        "turn_count": turn_count,
        "campaigns": sorted(campaigns),
        "arc_types": sorted(arcs),
        "mechanical_warning_counts": dict(sorted(warning_counts.items())),
        "strongest_looking_conversations_by_mechanical_signals_only": packet.get(
            "strongest_looking_conversations_by_mechanical_signals_only"
        )
        or [],
        "most_concerning_conversations_by_mechanical_signals_only": packet.get(
            "most_concerning_conversations_by_mechanical_signals_only"
        )
        or [],
        "universalization_drift_findings": drift_findings,
        "side_effect_flags_all_false": not any("side-effect flag true" in failure for failure in failures),
        "human_review_required_for_all": all(
            conversation.get("requires_human_sales_review") is True for conversation in conversations
        ),
        "codex_final_sales_quality_assigned": any(
            conversation.get("codex_assigned_final_sales_quality") is not False for conversation in conversations
        ),
        "redaction": redaction,
    }


def write_validation_report(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## 1. Summary",
        "Validated a dry-run commercial sales conversation packet for human review. Codex did not assign final sales-quality scores.",
        f"- Validation status: `{result['status']}`",
        "",
        "## 2. Packet Size",
        f"- Conversations: `{result.get('conversation_count', 0)}`",
        f"- Turn records: `{result.get('turn_count', 0)}`",
        "",
        "## 3. Campaign Coverage",
    ]
    lines.extend(f"- `{campaign}`" for campaign in result.get("campaigns", []))
    lines.extend(["", "## 4. Arc Coverage"])
    lines.extend(f"- `{arc}`" for arc in result.get("arc_types", []))
    lines.extend(["", "## 5. Mechanical Warning Counts"])
    warning_counts = result.get("mechanical_warning_counts") or {}
    if warning_counts:
        lines.extend(f"- `{key}`: `{value}`" for key, value in warning_counts.items())
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## 6. Strongest-Looking Conversations By Mechanical Signals Only"])
    for item in result.get("strongest_looking_conversations_by_mechanical_signals_only") or []:
        lines.append(
            f"- `{item.get('conversation_id')}`: `{item.get('mechanical_warning_count')}` warnings"
        )
    lines.extend(["", "## 7. Most Concerning Conversations By Mechanical Signals Only"])
    for item in result.get("most_concerning_conversations_by_mechanical_signals_only") or []:
        lines.append(
            f"- `{item.get('conversation_id')}`: `{item.get('mechanical_warning_count')}` warnings; flags `{', '.join(item.get('mechanical_warning_flags') or []) or 'none'}`"
        )
    redaction = result.get("redaction") or {}
    lines.extend(
        [
            "",
            "## 8. Safety Boundary Summary",
            f"- Provider calls made: `{str(redaction.get('provider_calls_made', False)).lower()}`",
            f"- Local LLM calls made: `{str(redaction.get('local_llm_calls_made', False)).lower()}`",
            f"- Live TTS used: `{str(redaction.get('live_tts_used', False)).lower()}`",
            f"- Sends email: `{str(redaction.get('sends_email', False)).lower()}`",
            f"- Creates calendar event: `{str(redaction.get('creates_calendar_event', False)).lower()}`",
            f"- Writes CRM: `{str(redaction.get('writes_crm', False)).lower()}`",
            f"- Opens PROD-102: `{str(redaction.get('opens_prod_102', False)).lower()}`",
            f"- Customer audio uploaded to Python server: `{str(redaction.get('customer_audio_uploaded_to_python_server', False)).lower()}`",
            f"- Customer audio uploaded to TTS provider: `{str(redaction.get('customer_audio_uploaded_to_tts_provider', False)).lower()}`",
            f"- Raw email-like values found: `{redaction.get('raw_email_like_values_found', 0)}`",
            f"- Secret-like values found: `{redaction.get('secret_like_values_found', 0)}`",
            "",
            "## Universalization Drift Risks",
        ]
    )
    for finding in result.get("universalization_drift_findings") or []:
        lines.extend(
            [
                f"- `{finding.get('id')}` `{finding.get('classification')}`: {finding.get('title')}",
                f"  - File: `{finding.get('file')}` lines `{', '.join(str(line) for line in finding.get('line_numbers') or []) or 'n/a'}`",
                f"  - Risk: {finding.get('risk')}",
                f"  - Follow-up: {finding.get('recommended_follow_up')}",
            ]
        )
    lines.extend(
        [
            "",
            "## 9. What ChatGPT/Human Reviewer Should Evaluate Next",
            "- Whether skeptical buyers would trust the agent after identity, privacy, and challenge turns.",
            "- Whether pain implication questions feel commercially useful rather than scripted.",
            "- Whether appointment asks arrive after enough consequence has been established.",
            "- Whether social and ASR recovery turns preserve control without sounding evasive.",
            "",
            "## 10. Recommended Next Likely Implementation Area",
            "Preliminary only: social and conversation-management repair remains the most likely next implementation slice, because current matrix evidence still clusters there. Human review should confirm before implementation.",
        ]
    )
    if result.get("failures"):
        lines.extend(["", "## Failures"])
        lines.extend(f"- {failure}" for failure in result["failures"])
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    result = validate()
    write_validation_report(result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
