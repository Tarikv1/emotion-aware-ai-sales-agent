#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-REHEARSAL-001"
FIXTURE_RELATIVE = "runtime/campaigns/examples/public-openai-chatgpt-plans.json"
PRIVATE_ROOT = ROOT / "data" / "private"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

LEGACY_RE = re.compile(r"legacy compatibility|appointment_target", re.I)
OWNER_RE = re.compile(r"human_followup_owner|demo operator", re.I)
ROUTESIGNAL_RE = re.compile(r"routesignal|northstar|handoff|callback|workflow review", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm)\b", re.I)
SOURCE_CLAIM_RE = re.compile(r"\bguarantee|better than|superior|gpt-5\.5\b", re.I)


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def git_head() -> str:
    completed = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False, timeout=3)
    return completed.stdout.strip() if completed.returncode == 0 else "git_unavailable"


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def matching_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not PRIVATE_ROOT.exists():
        return records
    for path in PRIVATE_ROOT.rglob("*.json"):
        payload = load_json(path)
        if not payload:
            continue
        selected = payload.get("selected_campaign_config") or {}
        config_path = str(payload.get("campaign_config_path") or selected.get("config_path") or "").replace("\\", "/")
        if config_path != FIXTURE_RELATIVE:
            continue
        stat = path.stat()
        records.append({"path": path, "payload": payload, "mtime": stat.st_mtime})
    return sorted(records, key=lambda item: item["mtime"])


def response_text(payload: dict[str, Any]) -> str:
    return str((payload.get("summary") or {}).get("final_response") or ((payload.get("packet") or {}).get("final_response")) or "")


def tts(payload: dict[str, Any]) -> dict[str, Any]:
    return (payload.get("packet") or {}).get("tts_delivery") or {}


def quality_gate(payload: dict[str, Any]) -> dict[str, Any]:
    return ((payload.get("asr") or {}).get("quality_gate") or {})


def main() -> None:
    records = matching_records()
    head = git_head()
    counts = Counter()
    traces: list[dict[str, Any]] = []
    for record in records:
        payload = record["payload"]
        text = response_text(payload)
        delivery = tts(payload)
        summary = payload.get("summary") or {}
        live_used = bool(payload.get("live_tts_used") or delivery.get("provider_calls_made") and delivery.get("audio_file_created"))
        dry_run = str(payload.get("mode") or "").lower() == "dry-run" or str((payload.get("selected_campaign_config") or {}).get("mode") or "").lower().endswith("dry-run")
        issues: list[str] = []
        if live_used:
            counts["live_tts_used"] += 1
        if dry_run:
            counts["dry_run"] += 1
        if dry_run and (payload.get("selected_campaign_config") or {}).get("live_tts_enabled") is not True:
            counts["live_tts_gate_issue"] += 1
            issues.append("live_tts_gate_issue")
        if delivery.get("voice_id_diagnostics", {}).get("raw_value_logged") is True:
            counts["voice_resolution_issue"] += 1
            issues.append("voice_resolution_issue")
        if LEGACY_RE.search(text):
            counts["legacy_compatibility_leakage"] += 1
            issues.append("legacy_compatibility_leakage")
        if OWNER_RE.search(text):
            counts["human_followup_owner_leakage"] += 1
            issues.append("human_followup_owner_leakage")
        if ROUTESIGNAL_RE.search(text):
            counts["RouteSignal_contamination"] += 1
            issues.append("RouteSignal_contamination")
        if RAW_URL_RE.search(text):
            counts["raw_URL_spoken"] += 1
            issues.append("raw_URL_spoken")
        if FAKE_SIDE_EFFECT_RE.search(text):
            counts["fake_side_effect_claim"] += 1
            issues.append("fake_side_effect_claim")
        if SOURCE_CLAIM_RE.search(text):
            counts["source_claim_issue"] += 1
            issues.append("source_claim_issue")
        if not quality_gate(payload).get("accepted", True):
            counts["current_live_openai_asr_issue"] += 1
            issues.append("current_live_openai_asr_issue")
        if bool(delivery.get("live_call_requested")) and not bool(delivery.get("audio_file_created")):
            counts["current_live_openai_tts_audio_issue"] += 1
            issues.append("current_live_openai_tts_audio_issue")
        if issues:
            counts["current_live_openai_runtime_defect"] += 1
            counts["needs_human_review"] += 1
        traces.append(
            {
                "path": project_relative(record["path"]),
                "git_head_short": payload.get("git_head_short"),
                "record_patch_status": "current_git_head_but_runtime_may_be_pre_patch" if payload.get("git_head_short") == head else "pre_patch_or_other_git_head",
                "mode": payload.get("mode"),
                "selected_mode": (payload.get("selected_campaign_config") or {}).get("mode"),
                "live_tts_used": live_used,
                "dry_run": dry_run,
                "response_hash": __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()[:12],
                "issues": issues,
            }
        )

    result = {
        "status": "pass",
        "checkpoint_id": CHECKPOINT_ID,
        "git_head_short": head,
        "current_openai_live_records_found": len(records),
        "records": traces,
        "live_tts_used_count": counts["live_tts_used"],
        "dry_run_count": counts["dry_run"],
        "live_tts_gate_issue_count": counts["live_tts_gate_issue"],
        "voice_resolution_issue_count": counts["voice_resolution_issue"],
        "legacy_compatibility_leakage_count": counts["legacy_compatibility_leakage"],
        "human_followup_owner_leakage_count": counts["human_followup_owner_leakage"],
        "RouteSignal_contamination_count": counts["RouteSignal_contamination"],
        "raw_URL_spoken_count": counts["raw_URL_spoken"],
        "fake_side_effect_claim_count": counts["fake_side_effect_claim"],
        "source_claim_issue_count": counts["source_claim_issue"],
        "current_live_openai_runtime_defect_count": counts["current_live_openai_runtime_defect"],
        "current_live_openai_asr_issue_count": counts["current_live_openai_asr_issue"],
        "current_live_openai_tts_audio_issue_count": counts["current_live_openai_tts_audio_issue"],
        "needs_human_review_count": counts["needs_human_review"],
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        "\n".join(
            [
                f"# {CHECKPOINT_ID}",
                "",
                f"- Status: `{result['status']}`",
                f"- Current OpenAI live records found: `{len(records)}`",
                f"- Live TTS used count: `{result['live_tts_used_count']}`",
                f"- Dry-run count: `{result['dry_run_count']}`",
                f"- Runtime defect count: `{result['current_live_openai_runtime_defect_count']}`",
                f"- Needs human review count: `{result['needs_human_review_count']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"status": "pass", "records": len(records), "runtime_defects": result["current_live_openai_runtime_defect_count"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
