#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_registry  # noqa: E402
from runtime.voice.runtime_tts_delivery import provider_for_key  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-TTS-GATE-AUDIT-001"
CURRENT_COMMIT = "729d06e"
FIXTURE_RELATIVE = "runtime/campaigns/examples/public-openai-chatgpt-plans.json"
FIXTURE_PATH = ROOT / FIXTURE_RELATIVE
PRIVATE_ROOT = ROOT / "data" / "private"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SIDE_EFFECTS = {
    "provider_calls_made_by_audit": False,
    "local_llm_calls_made_by_audit": False,
    "live_tts_calls_made_by_audit": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
}


def project_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "git_unavailable"


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def selected_config(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("selected_campaign_config") if isinstance(payload.get("selected_campaign_config"), dict) else {}


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("summary") if isinstance(payload.get("summary"), dict) else {}


def packet(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("packet") if isinstance(payload.get("packet"), dict) else {}


def tts(payload: dict[str, Any]) -> dict[str, Any]:
    body = packet(payload)
    return body.get("tts_delivery") if isinstance(body.get("tts_delivery"), dict) else {}


def campaign_path(payload: dict[str, Any]) -> str:
    selected = selected_config(payload)
    return str(payload.get("campaign_config_path") or selected.get("config_path") or "").replace("\\", "/")


def generated_at(payload: dict[str, Any]) -> str | None:
    value = payload.get("generated_at_utc") or payload.get("generated_at")
    return str(value) if value else None


def sort_dt(record: dict[str, Any]) -> datetime:
    parsed = parse_dt(generated_at(record["payload"]))
    if parsed:
        return parsed
    return datetime.fromtimestamp(record["mtime"], tz=timezone.utc)


def provider_calls(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("provider_calls_made") or sumry.get("tts_provider_calls_made"))


def audio_created(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("audio_file_created") or sumry.get("tts_audio_file_created"))


def live_tts_used(payload: dict[str, Any]) -> bool:
    return bool(payload.get("live_tts_used") or (provider_calls(payload) and audio_created(payload)))


def dry_run(payload: dict[str, Any]) -> bool:
    selected = selected_config(payload)
    delivery = tts(payload)
    mode = f"{payload.get('mode') or ''} {selected.get('mode') or ''} {delivery.get('fallback_reason') or ''}".lower()
    return "dry-run" in mode or "dry-run-mode" in mode


def private_packets() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not PRIVATE_ROOT.exists():
        return records
    for root in PRIVATE_ROOT.glob("live-demo-*"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.json"):
            payload = load_json(path)
            if not payload or campaign_path(payload) != FIXTURE_RELATIVE:
                continue
            records.append({"path": path, "payload": payload, "mtime": path.stat().st_mtime})
    return sorted(records, key=sort_dt, reverse=True)


def current_threshold(records: list[dict[str, Any]]) -> datetime | None:
    current_times = [sort_dt(record) for record in records if str(record["payload"].get("git_head_short") or "") == CURRENT_COMMIT]
    if current_times:
        return min(current_times)
    live_times = [sort_dt(record) for record in records if live_tts_used(record["payload"])]
    return min(live_times) if live_times else None


def is_current(record: dict[str, Any], threshold: datetime | None) -> bool:
    payload = record["payload"]
    if str(payload.get("git_head_short") or "") == CURRENT_COMMIT:
        return True
    if payload.get("git_head_short"):
        return False
    return bool(threshold and sort_dt(record) >= threshold and live_tts_used(payload))


def latest_current_packet(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    threshold = current_threshold(records)
    current = [record for record in records if is_current(record, threshold)]
    if not current:
        return None
    preferred = [record for record in current if live_tts_used(record["payload"])]
    return (preferred or current)[0]


def classify(payload: dict[str, Any] | None) -> tuple[str, str, dict[str, Any]]:
    if payload is None:
        return "unknown", "No current OpenAI live-demo packet was found.", {}

    selected = selected_config(payload)
    delivery = tts(payload)
    sumry = summary(payload)
    fallback = delivery.get("fallback_reason") or sumry.get("tts_fallback_reason")
    live_enabled = bool(selected.get("live_tts_enabled") or delivery.get("live_call_requested") or payload.get("mode") == "live-tts")
    provider_made = provider_calls(payload)
    audio_made = audio_created(payload)
    generic_allowed = bool(payload.get("generic_selected_campaign_live_tts_allowed") or selected.get("live_tts_enabled"))
    elevenlabs_call_made = bool(provider_made and str(delivery.get("provider_id") or "").lower().startswith("elevenlabs"))

    fields = {
        "selected_campaign_path": campaign_path(payload),
        "selected_campaign_id": selected.get("campaign_id"),
        "selected_mode": selected.get("mode") or payload.get("mode"),
        "live_tts_enabled": live_enabled,
        "live_tts_used": live_tts_used(payload),
        "elevenlabs_call_made": elevenlabs_call_made,
        "tts_provider_calls_made": provider_made,
        "audio_file_created": audio_made,
        "generic_live_tts_allowed": generic_allowed,
        "fallback_reason": fallback,
        "provider_id": delivery.get("provider_id"),
        "http_status": delivery.get("http_status"),
        "response_content_type": delivery.get("response_content_type"),
    }

    if campaign_path(payload) != FIXTURE_RELATIVE:
        return "unknown", "The latest packet does not use the expected OpenAI public fixture path.", fields
    if dry_run(payload) and str(payload.get("git_head_short") or "") != CURRENT_COMMIT:
        return "stale_pre_fix_dry_run_record", "Latest matching packet is an older dry-run record.", fields
    if not live_enabled:
        return "missing_live_tts_flag", "--live-tts did not reach the selected campaign packet.", fields
    if not generic_allowed:
        return "missing_allow_generic_live_tts", "--allow-generic-live-tts did not reach the generic campaign gate.", fields
    if fallback in {"missing-elevenlabs-api-key", "forced-key-missing"}:
        return "missing_consent_confirmed", "Live TTS was requested but provider preflight was blocked before a call.", fields
    if fallback in {"missing-elevenlabs-voice-id"}:
        return "provider_audio_failure", f"Live TTS was requested but provider voice resolution failed: {fallback}.", fields
    if fallback:
        return "provider_audio_failure", f"Live TTS reported fallback: {fallback}.", fields
    if not provider_made or not elevenlabs_call_made or not audio_made:
        return "provider_audio_failure", "Live TTS was enabled but provider call/audio artifact evidence is incomplete.", fields
    return "none", "Live TTS gate, ElevenLabs call, and audio artifact evidence are present.", fields


def command_for_live_tts() -> str:
    return (
        "python scripts\\run_live_demo_001_agent_voice_call.py "
        "--campaign-config runtime/campaigns/examples/public-openai-chatgpt-plans.json "
        "--live-tts --consent-confirmed --allow-generic-live-tts"
    )


def env_requirements() -> list[str]:
    provider = provider_for_key("elevenlabs")
    return [
        provider["api_key_env_var"],
        provider["language_voice_id_env_vars"]["en"],
        provider["default_voice_id_env_var"],
        "runtime/config/local/voice_ids.json",
        "config/local/voice_ids.json",
    ]


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Classification: `{result['classification']}`",
            f"- Reason: {result['classification_reason']}",
            f"- Latest current packet: `{result['latest_current_packet_path']}`",
            f"- Matching packet count: `{result['matching_packet_count']}`",
            f"- Current packet count: `{result['current_packet_count']}`",
            f"- Live TTS enabled: `{str(result['live_tts_enabled']).lower()}`",
            f"- Live TTS used: `{str(result['live_tts_used']).lower()}`",
            f"- ElevenLabs call made: `{str(result['elevenlabs_call_made']).lower()}`",
            f"- TTS provider calls made: `{str(result['tts_provider_calls_made']).lower()}`",
            f"- Audio file created: `{str(result['audio_file_created']).lower()}`",
            f"- Generic live TTS allowed: `{str(result['generic_live_tts_allowed']).lower()}`",
            f"- Fallback reason: `{result['fallback_reason']}`",
            "",
            "## Gate Fields",
            "",
            "```json",
            json.dumps(result["gate_fields"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    fixture = campaign_registry.load_campaign_config(FIXTURE_PATH)
    packets = private_packets()
    threshold = current_threshold(packets)
    current = [record for record in packets if is_current(record, threshold)]
    latest = latest_current_packet(packets)
    payload = latest["payload"] if latest else None
    classification, reason, gate_fields = classify(payload)
    fields = gate_fields
    result = {
        "status": "pass" if classification == "none" else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "git_head_short": git_head(),
        "current_commit_marker": CURRENT_COMMIT,
        "selected_campaign_id": fixture.get("campaign_id"),
        "campaign_config_path": FIXTURE_RELATIVE,
        "latest_current_packet_path": project_relative(latest["path"]) if latest else None,
        "latest_current_packet_hash": sha_file(latest["path"]) if latest else None,
        "latest_current_generated_at": generated_at(payload or {}),
        "matching_packet_count": len(packets),
        "current_packet_count": len(current),
        "stale_pre_fix_dry_run_count": sum(1 for record in packets if not is_current(record, threshold) and dry_run(record["payload"])),
        "selected_mode": fields.get("selected_mode"),
        "live_tts_enabled": bool(fields.get("live_tts_enabled")),
        "live_tts_used": bool(fields.get("live_tts_used")),
        "elevenlabs_call_made": bool(fields.get("elevenlabs_call_made")),
        "tts_provider_calls_made": bool(fields.get("tts_provider_calls_made")),
        "audio_file_created": bool(fields.get("audio_file_created")),
        "generic_live_tts_allowed": bool(fields.get("generic_live_tts_allowed")),
        "fallback_reason": fields.get("fallback_reason"),
        "classification": classification,
        "classification_reason": reason,
        "gate_fields": gate_fields,
        "required_command": command_for_live_tts(),
        "required_env_or_config": env_requirements(),
        "raw_private_transcript_copied_to_public_evidence": False,
        **SIDE_EFFECTS,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "classification": classification,
                "live_tts_used": result["live_tts_used"],
                "elevenlabs_call_made": result["elevenlabs_call_made"],
                "audio_file_created": result["audio_file_created"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
