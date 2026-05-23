"""Validate live-demo rehearsal failure freshness triage evidence.

This validator checks that every flagged public rehearsal record has a
freshness/failure-origin classification. It does not call providers, live TTS,
LLMs, email, calendar, CRM, or PROD-102.
"""

from __future__ import annotations

from collections import Counter
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TRIAGE_ID = "LIVE-DEMO-REHEARSAL-FAILURE-TRIAGE-001"
TRIAGE_DIR = ROOT / "research" / "experiments" / "generated" / TRIAGE_ID
PACKET_DIR = ROOT / "research" / "experiments" / "generated" / "LIVE-DEMO-COMMERCIAL-REHEARSAL-001"

REQUIRED_FILES = ["result.json", "report.md"]

CLASSIFICATIONS = {
    "stale_pre_current_runtime_artifact",
    "unknown_version_private_artifact",
    "current_live_runtime_defect",
    "provider_audio_artifact_issue",
    "incomplete_or_invalid_private_record",
    "expected_terminal_or_error_record",
    "evidence_generator_false_positive",
    "needs_human_review",
}

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]
RAW_AUDIO_PATTERN = re.compile(r"(?i)data[/\\]private[/\\].*\.(wav|mp3|webm|m4a)\b")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def packet_text() -> str:
    chunks: list[str] = []
    for path in list(TRIAGE_DIR.glob("*")) + list(PACKET_DIR.glob("*")):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md"}:
            chunks.append(read_text(path))
    return "\n".join(chunks)


def validate() -> dict[str, Any]:
    failures: list[str] = []
    missing = [name for name in REQUIRED_FILES if not (TRIAGE_DIR / name).exists()]
    for name in missing:
        add_failure(failures, f"missing required audit output file: {name}")
    if missing:
        return {"checkpoint_id": TRIAGE_ID, "status": "failed", "failures": failures}

    result = load_json(TRIAGE_DIR / "result.json")
    packet = load_json(PACKET_DIR / "rehearsal_packet.json")
    packet_records = packet.get("records") or []
    flagged_packet_ids = {
        str(record.get("rehearsal_record_id"))
        for record in packet_records
        if record.get("mechanical_issue_flags")
    }
    triaged_records = result.get("triaged_records") or []
    triaged_by_id = {str(item.get("rehearsal_record_id")): item for item in triaged_records}

    missing_triage = sorted(flagged_packet_ids - set(triaged_by_id))
    if missing_triage:
        add_failure(failures, f"flagged records missing triage classification: {missing_triage[:10]}")

    for record_id in sorted(flagged_packet_ids & set(triaged_by_id)):
        item = triaged_by_id[record_id]
        classifications = item.get("classifications_by_flag") or {}
        packet_record = next((record for record in packet_records if record.get("rehearsal_record_id") == record_id), {})
        for flag in packet_record.get("mechanical_issue_flags") or []:
            classification = classifications.get(flag)
            if classification not in CLASSIFICATIONS:
                add_failure(failures, f"{record_id}/{flag}: invalid or missing classification {classification!r}")

    classification_counts = result.get("classification_counts") or {}
    if "current_live_runtime_defect" not in classification_counts:
        add_failure(failures, "current_live_runtime_defect count missing")
    if result.get("unknown_version_count", 0) and result.get("unknown_version_count") == result.get("current_live_runtime_defect_count"):
        add_failure(failures, "unknown-version records appear to be treated as current defects")

    required_flag_families = [
        "provider_audio_failed",
        "audio_url_missing_when_provider_called",
        "final_response_missing",
        "tts_input_missing",
        "repeated_response",
    ]
    flag_counts = Counter()
    for item in triaged_records:
        flag_counts.update((item.get("classifications_by_flag") or {}).keys())
    for flag in required_flag_families:
        if flag in result.get("mechanical_issue_counts", {}) and flag not in flag_counts:
            add_failure(failures, f"{flag} records were not classified")

    metadata_probe = result.get("future_metadata_probe") or {}
    required_probe_fields = [
        "git_head_short",
        "runtime_manifest_hash",
        "runtime_manifest_entry_count",
        "universal_policy_runtime_marker",
        "generated_at_utc",
    ]
    if metadata_probe.get("metadata_available") is not True:
        add_failure(failures, "future metadata probe did not report metadata_available true")
    for field in required_probe_fields:
        value = metadata_probe.get(field)
        if value in (None, ""):
            add_failure(failures, f"future metadata probe missing field: {field}")

    text = packet_text()
    if EMAIL_PATTERN.search(text):
        add_failure(failures, "raw email-like value found in public evidence")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            add_failure(failures, f"secret-looking pattern found in public evidence: {pattern.pattern}")
    if RAW_AUDIO_PATTERN.search(text):
        add_failure(failures, "raw customer audio path found in public evidence")
    if '"transcript":' in text or '"buyer_utterance":' in text:
        add_failure(failures, "raw transcript field found in public evidence")

    for key in [
        "validator_provider_calls_made",
        "validator_live_tts_calls_made",
        "validator_local_llm_calls_made",
        "validator_sends_email",
        "validator_creates_calendar_event",
        "validator_writes_crm",
        "validator_opens_prod_102",
    ]:
        if bool(result.get(key)):
            add_failure(failures, f"validator side-effect boundary true: {key}")

    report = read_text(TRIAGE_DIR / "report.md")
    for section in [
        "Current Runtime Defect Count",
        "Freshness Summary",
        "Clean Current Evidence Instructions",
        "Safety Boundary Summary",
    ]:
        if section not in report:
            add_failure(failures, f"report.md missing section: {section}")

    return {
        "checkpoint_id": TRIAGE_ID,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "flagged_record_count": len(flagged_packet_ids),
        "triaged_record_count": len(triaged_records),
        "classification_counts": classification_counts,
        "current_live_runtime_defect_count": result.get("current_live_runtime_defect_count"),
        "unknown_version_count": result.get("unknown_version_count"),
        "side_effect_boundary": {
            "validator_provider_calls_made": False,
            "validator_live_tts_calls_made": False,
            "validator_local_llm_calls_made": False,
            "validator_sends_email": False,
            "validator_creates_calendar_event": False,
            "validator_writes_crm": False,
            "validator_opens_prod_102": False,
        },
    }


def main() -> None:
    result = validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
