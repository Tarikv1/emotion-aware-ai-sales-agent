"""Validate the live-demo commercial rehearsal review packet.

The validator checks packet completeness, parseability, redaction, human-review
boundaries, and tool side-effect boundaries. It does not call providers, run
TTS, or judge final live-call quality.
"""

from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-DEMO-COMMERCIAL-REHEARSAL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = [
    "rehearsal_packet.md",
    "rehearsal_packet.json",
    "rehearsal_packet.jsonl",
    "rehearsal_index.md",
    "rubric.md",
    "redaction_report.json",
    "result.json",
    "report.md",
]

RUBRIC_DIMENSIONS = [
    "ASR transcript accuracy",
    "Turn-taking / interruption handling",
    "TTS playback reliability",
    "Voice naturalness",
    "Campaign selection correctness",
    "Buyer acknowledgement",
    "Direct question answering",
    "Pain discovery and implication quality",
    "Rapport / human-context handling",
    "Objection handling",
    "Trust and AI transparency",
    "Close / next-step strength",
    "Safety and claim discipline",
    "Overall commercial usefulness",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]
RAW_AUDIO_PATTERNS = [
    re.compile(r"(?i)data[/\\]private[/\\].*\.(wav|mp3|webm|m4a)\b"),
    re.compile(r"(?i)\b(audio_bytes|audio_base64|customer_audio_path)\b"),
]

FORBIDDEN_FINAL_FIELDS = {
    "final_live_quality_label",
    "final_live_quality_pass",
    "final_live_quality_fail",
    "final_sales_quality_pass",
    "final_sales_quality_fail",
}


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
            "private_input_discovery_count": 0,
            "rehearsal_record_count": 0,
        }

    packet = load_json(OUT_DIR / "rehearsal_packet.json")
    redaction = load_json(OUT_DIR / "redaction_report.json")
    result = load_json(OUT_DIR / "result.json")
    records = packet.get("records") or []

    jsonl_records: list[dict[str, Any]] = []
    for line_number, line in enumerate(read_text(OUT_DIR / "rehearsal_packet.jsonl").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            jsonl_records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            add_failure(failures, f"rehearsal_packet.jsonl line {line_number} does not parse: {exc}")

    if len(jsonl_records) != len(records):
        add_failure(failures, f"expected JSONL record count {len(records)}, got {len(jsonl_records)}")

    private_input_count = int(packet.get("private_input_discovery_count") or 0)
    packet_status = str(packet.get("status") or "")
    current_only_mode = bool(packet.get("current_only_mode"))
    if private_input_count > 0 and not records and not current_only_mode:
        add_failure(failures, "private inputs exist but packet has no records")
    if private_input_count == 0 and packet_status != "no_private_input_found":
        add_failure(failures, "packet with no private inputs must use status no_private_input_found")
    if private_input_count == 0 and "no private input found" not in read_text(OUT_DIR / "report.md").lower():
        add_failure(failures, "empty packet report missing no-private-input instructions")

    for record in records:
        record_id = str(record.get("rehearsal_record_id") or "<missing>")
        if record.get("requires_human_sales_review") is not True:
            add_failure(failures, f"{record_id}: requires_human_sales_review is not true")
        if record.get("codex_assigned_final_live_quality") is not False:
            add_failure(failures, f"{record_id}: Codex assigned final live quality")
        if record.get("human_live_quality_scorecard", {}).get("qualitative_label") is not None:
            add_failure(failures, f"{record_id}: qualitative label was prefilled")
        for field in FORBIDDEN_FINAL_FIELDS:
            if field in record:
                add_failure(failures, f"{record_id}: forbidden final quality field present: {field}")
        if "transcript" in record or "buyer_utterance" in record:
            add_failure(failures, f"{record_id}: raw private transcript field present")
        if not record.get("transcript_hash") and private_input_count > 0:
            add_failure(failures, f"{record_id}: missing transcript hash")
        for field in [
            "private_source_file_mtime_utc",
            "private_source_file_hash",
            "freshness_classification",
            "current_runtime_marker_present",
            "generator_seen_as_current_candidate",
        ]:
            if field not in record:
                add_failure(failures, f"{record_id}: missing freshness metadata field: {field}")
        if record.get("freshness_classification") not in {
            "current_runtime_marked",
            "unknown_version_private_artifact",
            "stale_pre_current_runtime_artifact",
        }:
            add_failure(failures, f"{record_id}: invalid freshness_classification")

    for field in [
        "current_runtime_reference",
        "freshness_counts",
        "current_runtime_marked_record_count",
        "unknown_version_record_count",
        "stale_or_legacy_record_count",
        "current_only_evidence_available",
    ]:
        if field not in packet:
            add_failure(failures, f"packet missing freshness summary field: {field}")

    packet_text = all_packet_text()
    if EMAIL_PATTERN.search(packet_text):
        add_failure(failures, "raw email-like value found in packet")
    for pattern in SECRET_PATTERNS:
        if pattern.search(packet_text):
            add_failure(failures, f"secret-looking pattern found: {pattern.pattern}")
    for pattern in RAW_AUDIO_PATTERNS:
        if pattern.search(packet_text):
            add_failure(failures, f"raw customer audio reference found: {pattern.pattern}")

    for key in [
        "generator_provider_calls_made",
        "validator_provider_calls_made",
        "validator_live_tts_calls_made",
        "validator_local_llm_calls_made",
        "validator_sends_email",
        "validator_creates_calendar_event",
        "validator_writes_crm",
        "validator_opens_prod_102",
    ]:
        if bool(redaction.get(key)):
            add_failure(failures, f"redaction report side-effect boundary true: {key}")

    if redaction.get("raw_email_like_values_found") not in (0, [], None):
        add_failure(failures, "redaction report found raw email-like values")
    if redaction.get("secret_like_values_found") not in (0, [], None):
        add_failure(failures, "redaction report found secret-like values")
    if redaction.get("raw_customer_audio_found") is not False:
        add_failure(failures, "redaction report raw customer audio boundary is not false")

    rubric_md = read_text(OUT_DIR / "rubric.md")
    for dimension in RUBRIC_DIMENSIONS:
        if dimension not in rubric_md:
            add_failure(failures, f"rubric.md missing scoring dimension: {dimension}")
    for label in [
        "live_ready_strong",
        "live_ready_with_minor_polish",
        "not_live_ready_voice_issue",
        "not_live_ready_dialogue_issue",
        "not_live_ready_asr_issue",
        "unsafe_or_unusable",
    ]:
        if label not in rubric_md:
            add_failure(failures, f"rubric.md missing qualitative label: {label}")

    report_md = read_text(OUT_DIR / "report.md")
    for section in [
        "Recommended Live Rehearsal Scenarios",
        "What ChatGPT/human reviewer should evaluate next",
        "Safety Boundary Summary",
    ]:
        if section not in report_md:
            add_failure(failures, f"report.md missing section: {section}")

    warning_counts = Counter()
    for record in records:
        warning_counts.update(record.get("mechanical_issue_flags") or [])

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "packet_status": packet_status,
        "current_only_mode": current_only_mode,
        "private_input_discovery_count": private_input_count,
        "rehearsal_record_count": len(records),
        "current_runtime_marked_record_count": packet.get("current_runtime_marked_record_count"),
        "unknown_version_record_count": packet.get("unknown_version_record_count"),
        "freshness_counts": packet.get("freshness_counts") or {},
        "campaign_coverage_found": sorted({str(r.get("campaign_id") or "") for r in records if r.get("campaign_id")}),
        "mechanical_issue_counts": dict(sorted(warning_counts.items())),
        "side_effect_boundary": {
            "validator_provider_calls_made": False,
            "validator_live_tts_calls_made": False,
            "validator_local_llm_calls_made": False,
            "validator_sends_email": False,
            "validator_creates_calendar_event": False,
            "validator_writes_crm": False,
            "validator_opens_prod_102": False,
        },
        "result_status": result.get("status"),
    }


def main() -> None:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
