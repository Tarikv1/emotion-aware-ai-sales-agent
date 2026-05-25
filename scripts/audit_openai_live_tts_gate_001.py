#!/usr/bin/env python3
from __future__ import annotations

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
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
PRIVATE_ROOTS = [
    ROOT / "data" / "private" / "live-demo-001",
    ROOT / "data" / "private" / "live-demo-003",
]
RUNNER_PATH = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SIDE_EFFECTS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
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


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def is_structured_turn_packet(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("selected_campaign_config")
        or payload.get("summary")
        or ((payload.get("packet") or {}).get("tts_delivery") if isinstance(payload.get("packet"), dict) else None)
    )


def private_packets() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root in PRIVATE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            payload = load_json(path)
            if not payload:
                continue
            config_path = str(payload.get("campaign_config_path") or "")
            selected = payload.get("selected_campaign_config") or {}
            selected_path = str(selected.get("config_path") or "")
            if config_path.replace("\\", "/") != project_relative(FIXTURE_PATH) and selected_path.replace("\\", "/") != project_relative(FIXTURE_PATH):
                continue
            stat = path.stat()
            records.append(
                {
                    "path": path,
                    "mtime": stat.st_mtime,
                    "structured_turn_packet": is_structured_turn_packet(payload),
                    "payload": payload,
                }
            )
    return sorted(records, key=lambda item: (item["structured_turn_packet"], item["mtime"]), reverse=True)


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


def packet_tts(packet: dict[str, Any]) -> dict[str, Any]:
    body = packet.get("packet") or {}
    return body.get("tts_delivery") or {}


def packet_summary(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("summary") or {}


def classify(packet: dict[str, Any] | None) -> tuple[str, str, dict[str, Any]]:
    if packet is None:
        return "unknown", "No matching private OpenAI live-demo packet was found.", {}

    selected = packet.get("selected_campaign_config") or {}
    summary = packet_summary(packet)
    tts = packet_tts(packet)
    mode = str(selected.get("mode") or packet.get("mode") or "")
    selected_live = bool(selected.get("live_tts_enabled"))
    live_requested = bool(tts.get("live_call_requested") or selected_live or mode == "live-tts")
    provider_calls = bool(tts.get("provider_calls_made") or summary.get("tts_provider_calls_made"))
    audio_created = bool(tts.get("audio_file_created") or summary.get("tts_audio_file_created"))
    fallback = str(tts.get("fallback_reason") or summary.get("tts_fallback_reason") or "")

    fields = {
        "mode": mode,
        "selected_live_tts_enabled": selected_live,
        "packet_mode": packet.get("mode"),
        "tts_live_call_requested": bool(tts.get("live_call_requested")),
        "tts_provider_calls_made": provider_calls,
        "audio_file_created": audio_created,
        "fallback_reason": fallback or None,
        "generic_selected_campaign_live_tts_allowed": bool(packet.get("generic_selected_campaign_live_tts_allowed")),
    }

    if not live_requested and "generic config dry-run" in mode:
        return "missing_live_tts_flag", "The selected generic campaign option was dry-run; live TTS gate flags were not active for this run.", fields
    if not live_requested and fallback == "dry-run-mode":
        return "missing_live_tts_flag", "The TTS packet reports dry-run-mode, so --live-tts was not effective for this turn.", fields
    if live_requested and not selected_live and str(packet.get("campaign_selector_mode")) == "generic_config":
        return "missing_allow_generic_live_tts", "Generic campaign live TTS was requested without the generic live-TTS allow gate.", fields
    if live_requested and fallback in {"forced-key-missing", "missing-elevenlabs-api-key", "missing-elevenlabs-voice-id"}:
        return "force_key_missing_or_preflight_disabled", f"Live TTS was requested but preflight/provider requirements blocked audio: {fallback}.", fields
    if live_requested and not provider_calls and not audio_created:
        return "current_live_tts_gate_bug", "All visible live flags suggest live TTS, but no provider call or audio artifact was produced.", fields
    if provider_calls and audio_created:
        return "none", "Live TTS provider call and audio artifact are present.", fields
    return "unknown", "The packet does not expose enough gate metadata to classify the dry-run cause.", fields


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Classification: `{result['classification']}`",
            f"- Behavior: `{result['behavior_assessment']}`",
            f"- Matching packets: `{result['matching_packet_count']}`",
            f"- Selected mode: `{result['selected_mode']}`",
            f"- Live TTS enabled: `{str(result['live_tts_enabled']).lower()}`",
            f"- Live TTS used: `{str(result['live_tts_used']).lower()}`",
            f"- Required command: `{result['required_command']}`",
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
    latest = packets[0] if packets else None
    packet = latest["payload"] if latest else None
    classification, reason, gate_fields = classify(packet)
    selected = (packet or {}).get("selected_campaign_config") or {}
    summary = packet_summary(packet or {})
    tts = packet_tts(packet or {})
    live_tts_used = bool((packet or {}).get("live_tts_used") or summary.get("tts_provider_calls_made") and summary.get("tts_audio_file_created"))
    behavior_assessment = "intended_gate_behavior" if classification in {"missing_live_tts_flag", "missing_allow_generic_live_tts", "force_key_missing_or_preflight_disabled"} else classification
    result = {
        "status": "pass",
        "checkpoint_id": CHECKPOINT_ID,
        "git_head_short": git_head(),
        "selected_campaign_id": fixture.get("campaign_id"),
        "campaign_config_path": project_relative(FIXTURE_PATH),
        "latest_packet_path": project_relative(latest["path"]) if latest else None,
        "matching_packet_count": len(packets),
        "selected_mode": selected.get("mode") or (packet or {}).get("mode"),
        "live_tts_enabled": bool(selected.get("live_tts_enabled") or tts.get("live_call_requested")),
        "live_tts_used": live_tts_used,
        "provider_boundary_flags": {
            **SIDE_EFFECTS,
            "tts_provider_calls_made": bool(tts.get("provider_calls_made") or summary.get("tts_provider_calls_made")),
            "audio_file_created": bool(tts.get("audio_file_created") or summary.get("tts_audio_file_created")),
            "customer_audio_uploaded_to_python_server": bool((packet or {}).get("customer_audio_uploaded_to_python_server")),
            "customer_audio_uploaded_to_tts_provider": bool((packet or {}).get("customer_audio_uploaded_to_tts_provider") or tts.get("customer_audio_uploaded")),
        },
        "gate_fields": gate_fields,
        "gate_fields_present_missing": {
            "campaign_config_path": bool((packet or {}).get("campaign_config_path")),
            "selected_campaign_config": bool(selected),
            "selected_config_live_tts_enabled": "live_tts_enabled" in selected,
            "tts_live_call_requested": "live_call_requested" in tts,
            "tts_fallback_reason": bool(tts.get("fallback_reason") or summary.get("tts_fallback_reason")),
            "browser_payload_live_tts_flag_visible": False,
        },
        "classification": classification,
        "classification_reason": reason,
        "behavior_assessment": behavior_assessment,
        "required_command": command_for_live_tts(),
        "required_env_or_config": env_requirements(),
        "raw_private_transcript_copied_to_public_evidence": False,
        **SIDE_EFFECTS,
    }
    write_evidence(result)
    print(json.dumps({"status": result["status"], "classification": classification, "behavior_assessment": behavior_assessment}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
