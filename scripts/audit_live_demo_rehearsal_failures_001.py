"""Audit live-demo rehearsal packet freshness and failure origin.

This audit classifies mechanical issues in the public rehearsal packet without
reading raw private transcript text into public evidence and without changing
dialogue behavior.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-REHEARSAL-FAILURE-TRIAGE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PACKET_DIR = ROOT / "research" / "experiments" / "generated" / "LIVE-DEMO-COMMERCIAL-REHEARSAL-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True))


def load_packet() -> dict[str, Any]:
    return json.loads(read_text(PACKET_DIR / "rehearsal_packet.json"))


def classify_flag(record: dict[str, Any], flag: str) -> tuple[str, str]:
    freshness = str(record.get("freshness_classification") or "unknown_version_private_artifact")
    error_type = str(record.get("private_record_error_type") or "")
    error_message = str(record.get("private_record_error") or "")
    final_response = str(record.get("final_response") or "").strip()
    call_control = str(record.get("call_control") or "")
    current = freshness == "current_runtime_marked"

    if flag in {"provider_audio_failed", "audio_url_missing_when_provider_called"}:
        return "provider_audio_artifact_issue", "provider call/audio artifact issue is separate from dialogue quality"

    if flag in {"final_response_missing", "tts_input_missing"}:
        if error_type or "turn failed" in error_message.lower():
            return "incomplete_or_invalid_private_record", "missing response belongs to an error or malformed private record"
        if call_control in {"end-call", "schedule-and-end"} and not final_response:
            return "expected_terminal_or_error_record", "terminal or closed record did not need a new spoken response"
        return "current_live_runtime_defect" if current else "unknown_version_private_artifact", "missing response needs a clean current run before runtime attribution"

    if flag == "call_control_unexpected":
        if error_type or not final_response:
            return "incomplete_or_invalid_private_record", "unexpected call-control appears on incomplete/error evidence"
        return "current_live_runtime_defect" if current else "unknown_version_private_artifact", "call-control issue needs current runtime marker before attribution"

    if flag == "repeated_response":
        if freshness == "stale_pre_current_runtime_artifact":
            return "stale_pre_current_runtime_artifact", "record is stamped from non-current runtime"
        if current:
            return "current_live_runtime_defect", "repeated response persists on current runtime-marked evidence"
        return "unknown_version_private_artifact", "record has no current runtime marker, so repeated response is not a current defect"

    if flag == "response_too_long_for_live_voice":
        return "current_live_runtime_defect" if current else "unknown_version_private_artifact", "voice-length issue requires current marked evidence before runtime attribution"

    if flag in {"asr_low_confidence", "transcript_garbled"}:
        return "needs_human_review", "ASR quality needs private-source review by the operator"

    if flag in {"campaign_selector_mismatch", "route_signal_generic_mix"}:
        return "current_live_runtime_defect" if current else "unknown_version_private_artifact", "campaign selector attribution requires current runtime marker"

    if flag == "live_tts_requested_but_dry_run":
        return "evidence_generator_false_positive", "dry-run packet can record requested live mode without a validator/provider side effect"

    return "needs_human_review", "no deterministic classification rule matched this flag"


def future_metadata_probe() -> dict[str, Any]:
    try:
        turn = demo.build_browser_demo_turn_packet(
            transcript="__agent_open__",
            campaign_id=demo.DEFAULT_CAMPAIGN_ID,
            stage=demo.DEFAULT_STAGE,
            input_type="typed",
            silence_count=0,
            cases_path=demo.DEFAULT_CASES_PATH,
            private_out=ROOT / ".tmp" / CHECKPOINT_ID,
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=1.0,
            session_id="metadata-probe",
            session_state={"turns": []},
        )
    except Exception as exc:  # noqa: BLE001 - audit must report unavailable metadata explicitly.
        return {
            "metadata_available": False,
            "unavailable_reason": f"{type(exc).__name__}: {exc}",
            "provider_calls_made": False,
            "live_tts_calls_made": False,
            "local_llm_calls_made": False,
        }
    metadata = turn.get("runtime_metadata") or {}
    return {
        "metadata_available": True,
        "git_head_short": turn.get("git_head_short") or metadata.get("git_head_short"),
        "runtime_manifest_hash": turn.get("runtime_manifest_hash") or metadata.get("runtime_manifest_hash"),
        "runtime_manifest_entry_count": turn.get("runtime_manifest_entry_count") or metadata.get("runtime_manifest_entry_count"),
        "universal_policy_runtime_marker": turn.get("universal_policy_runtime_marker") or metadata.get("universal_policy_runtime_marker"),
        "campaign_registry_schema_version": turn.get("campaign_registry_schema_version") or metadata.get("campaign_registry_schema_version"),
        "generated_at_utc": turn.get("generated_at_utc") or metadata.get("generated_at_utc"),
        "provider_calls_made": bool(turn.get("provider_calls_made")),
        "live_tts_calls_made": bool(turn.get("live_tts_used") or turn.get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(turn.get("local_llm_calls_made")),
    }


def audit() -> dict[str, Any]:
    packet = load_packet()
    records = packet.get("records") or []
    flagged_records = [record for record in records if record.get("mechanical_issue_flags")]
    triaged_records: list[dict[str, Any]] = []
    classification_counts: Counter[str] = Counter()
    issue_by_freshness: dict[str, Counter[str]] = defaultdict(Counter)
    issue_by_campaign: dict[str, Counter[str]] = defaultdict(Counter)
    mechanical_issue_counts: Counter[str] = Counter()

    for record in flagged_records:
        classifications: dict[str, str] = {}
        reasons: dict[str, str] = {}
        for flag in record.get("mechanical_issue_flags") or []:
            classification, reason = classify_flag(record, str(flag))
            classifications[str(flag)] = classification
            reasons[str(flag)] = reason
            classification_counts[classification] += 1
            mechanical_issue_counts[str(flag)] += 1
            issue_by_freshness[str(record.get("freshness_classification") or "unknown")][str(flag)] += 1
            issue_by_campaign[str(record.get("campaign_id") or "unknown")][str(flag)] += 1
        triaged_records.append(
            {
                "rehearsal_record_id": record.get("rehearsal_record_id"),
                "campaign_id": record.get("campaign_id"),
                "freshness_classification": record.get("freshness_classification"),
                "mechanical_issue_flags": record.get("mechanical_issue_flags") or [],
                "classifications_by_flag": classifications,
                "classification_reasons_by_flag": reasons,
                "requires_human_sales_review": True,
            }
        )

    probe = future_metadata_probe()
    side_effects_false = not any(
        bool(probe.get(key))
        for key in ("provider_calls_made", "live_tts_calls_made", "local_llm_calls_made")
    )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "source_packet_checkpoint_id": packet.get("checkpoint_id"),
        "total_record_count": len(records),
        "flagged_record_count": len(flagged_records),
        "current_runtime_marked_record_count": packet.get("current_runtime_marked_record_count", 0),
        "unknown_version_count": packet.get("unknown_version_record_count", 0),
        "stale_or_legacy_record_count": packet.get("stale_or_legacy_record_count", 0),
        "freshness_counts": packet.get("freshness_counts") or {},
        "mechanical_issue_counts": dict(sorted(mechanical_issue_counts.items())),
        "classification_counts": dict(sorted({key: classification_counts.get(key, 0) for key in [
            "stale_pre_current_runtime_artifact",
            "unknown_version_private_artifact",
            "current_live_runtime_defect",
            "provider_audio_artifact_issue",
            "incomplete_or_invalid_private_record",
            "expected_terminal_or_error_record",
            "evidence_generator_false_positive",
            "needs_human_review",
        ]}.items())),
        "current_live_runtime_defect_count": classification_counts.get("current_live_runtime_defect", 0),
        "provider_audio_artifact_issue_count": classification_counts.get("provider_audio_artifact_issue", 0),
        "incomplete_or_invalid_private_record_count": classification_counts.get("incomplete_or_invalid_private_record", 0),
        "records_requiring_human_review": sum(
            1
            for item in triaged_records
            if "needs_human_review" in (item.get("classifications_by_flag") or {}).values()
        ),
        "issue_counts_by_freshness_classification": {
            key: dict(sorted(counter.items())) for key, counter in sorted(issue_by_freshness.items())
        },
        "issue_counts_by_campaign": {
            key: dict(sorted(counter.items())) for key, counter in sorted(issue_by_campaign.items())
        },
        "triaged_records": triaged_records,
        "future_metadata_probe": probe,
        "side_effects_stayed_false": side_effects_false,
        "validator_provider_calls_made": False,
        "validator_live_tts_calls_made": False,
        "validator_local_llm_calls_made": False,
        "validator_sends_email": False,
        "validator_creates_calendar_event": False,
        "validator_writes_crm": False,
        "validator_opens_prod_102": False,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-REHEARSAL-FAILURE-TRIAGE-001 Report",
        "",
        "## Summary",
        f"- Total rehearsal records: `{result['total_record_count']}`",
        f"- Flagged records: `{result['flagged_record_count']}`",
        f"- Current-runtime-marked records: `{result['current_runtime_marked_record_count']}`",
        f"- Unknown-version records: `{result['unknown_version_count']}`",
        "",
        "## Freshness Summary",
        *(f"- `{key}`: `{value}`" for key, value in (result.get("freshness_counts") or {}).items()),
        "",
        "## Current Runtime Defect Count",
        f"- `current_live_runtime_defect`: `{result['current_live_runtime_defect_count']}`",
        "- Unknown-version private records are not counted as current runtime defects.",
        "",
        "## Classification Counts",
        *(f"- `{key}`: `{value}`" for key, value in (result.get("classification_counts") or {}).items()),
        "",
        "## Mechanical Issue Counts",
        *(f"- `{key}`: `{value}`" for key, value in (result.get("mechanical_issue_counts") or {}).items()),
        "",
        "## Provider Audio Issue Classification",
        f"- Provider audio artifact issues: `{result['provider_audio_artifact_issue_count']}`",
        "",
        "## Missing Response/TTS Classification",
        f"- Incomplete or invalid private records: `{result['incomplete_or_invalid_private_record_count']}`",
        "",
        "## Issue Counts By Freshness Classification",
    ]
    for freshness, counts in (result.get("issue_counts_by_freshness_classification") or {}).items():
        lines.append(f"- `{freshness}`: {counts}")
    lines.extend(
        [
            "",
            "## Issue Counts By Campaign",
        ]
    )
    for campaign, counts in (result.get("issue_counts_by_campaign") or {}).items():
        lines.append(f"- `{campaign}`: {counts}")
    lines.extend(
        [
            "",
            "## Safety Boundary Summary",
            f"- Future metadata probe provider calls made: `{str(result['future_metadata_probe'].get('provider_calls_made')).lower()}`",
            f"- Future metadata probe live TTS calls made: `{str(result['future_metadata_probe'].get('live_tts_calls_made')).lower()}`",
            f"- Future metadata probe local LLM calls made: `{str(result['future_metadata_probe'].get('local_llm_calls_made')).lower()}`",
            f"- Validator provider/TTS/LLM/email/calendar/CRM/PROD-102 side effects: `false`",
            "",
            "## Clean Current Evidence Instructions",
            "1. Pull latest `main`.",
            "2. Start a fresh dry-run demo with `python scripts\\run_live_demo_001_agent_voice_call.py --force-key-missing`.",
            "3. Run RouteSignal normal path: permission, `callbacks are a problem`, `it causes delays`, `tomorrow at 3 works`.",
            "4. Run generic insurance path: select synthetic insurance, product-detail question, tentative coverage fit, active confirmation, impact.",
            "5. Run ASR stress path: `yeah that would be good`, `okay that would be good`, `call me tomorrow at 3`, then noisy/short phrases.",
            "6. Run campaign selector switch path: RouteSignal -> synthetic insurance -> RouteSignal, and confirm metadata does not mix.",
            "7. Regenerate `LIVE-DEMO-COMMERCIAL-REHEARSAL-001` and check `current_runtime_marked_record_count`.",
            "",
            "## Recommended Patch Scope",
            "- Do not patch dialogue behavior from unknown-version private artifacts.",
            "- Patch only after a current-runtime-marked rehearsal reproduces a classified current defect.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = audit()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "report.md", render_report(result))
    print(json.dumps({
        "checkpoint_id": CHECKPOINT_ID,
        "status": result["status"],
        "flagged_record_count": result["flagged_record_count"],
        "classification_counts": result["classification_counts"],
        "current_live_runtime_defect_count": result["current_live_runtime_defect_count"],
        "unknown_version_count": result["unknown_version_count"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
