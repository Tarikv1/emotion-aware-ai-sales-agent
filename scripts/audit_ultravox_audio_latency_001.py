#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
TEXT_SANDBOX_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001" / "result.json"
TUNNEL_DIAGNOSTICS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-DIAGNOSTICS-001" / "result.json"
RESULT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LATENCY-AUDIT-001"
RESULT_PATH = RESULT_DIR / "result.json"
REPORT_PATH = RESULT_DIR / "report.md"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return load_json(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def maybe_number(value: Any) -> int | float | None:
    return value if isinstance(value, (int, float)) else None


def build_result(sandbox: dict[str, Any], text_sandbox: dict[str, Any], tunnel_diagnostics: dict[str, Any]) -> dict[str, Any]:
    latency = sandbox.get("latency_metrics", {}) if isinstance(sandbox.get("latency_metrics"), dict) else {}
    tool_latency = latency.get("client_tool_local_call_latency_ms")
    tool_latency_available = isinstance(tool_latency, list) and bool(tool_latency)
    current_observed = maybe_number(sandbox.get("first_agent_audio_latency_seconds"))
    live_ready = current_observed is not None and current_observed <= 3
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-LATENCY-AUDIT-001",
        "phase": "4J6",
        "source_sandbox_evaluation_id": sandbox.get("evaluation_id"),
        "first_agent_audio_latency_seconds": current_observed,
        "current_observed_latency_seconds": current_observed,
        "per_turn_latency_available": False,
        "per_turn_latency_seconds": [],
        "session_creation_time_ms": maybe_number((sandbox.get("create_call") or {}).get("latency_ms")) if isinstance(sandbox.get("create_call"), dict) else maybe_number(latency.get("create_call_latency_ms")),
        "tunnel_setup_time_ms": maybe_number(latency.get("tunnel_start_latency_ms")),
        "public_endpoint_preflight_time_ms": maybe_number(latency.get("public_endpoint_valid_request_latency_ms")),
        "websocket_connect_latency_ms": maybe_number(latency.get("websocket_connect_latency_ms")),
        "ping_round_trip_ms": maybe_number(latency.get("ping_round_trip_ms")),
        "first_transcript_latency_seconds": maybe_number(sandbox.get("first_transcript_latency_seconds")),
        "first_user_transcript_latency_seconds": None,
        "first_user_transcript_latency_available": False,
        "tool_request_latency_ms": tool_latency if tool_latency_available else None,
        "tool_request_latency_available": tool_latency_available,
        "time_from_tool_response_to_agent_audio_seconds": None,
        "time_from_tool_response_to_agent_audio_available": False,
        "first_agent_audio_latency_likely_includes_session_setup_startup": False,
        "first_agent_audio_latency_likely_includes_first_turn_startup": True,
        "latency_measurement_note": "The runner starts first_agent_audio_latency_seconds immediately before sending the first audio turn, after tunnel setup, session creation, and WebSocket connection. It likely includes first-turn audio upload, transcription, tool, model, and voice startup, but not tunnel/session setup.",
        "another_provider_run_should_separate_cold_start_vs_warm_turn": True,
        "live_target_seconds": {"min": 2, "max": 3},
        "live_ready_latency": live_ready,
        "promising_with_warm_session": "unknown",
        "needs_warm_turn_benchmark": True,
        "text_sandbox_first_agent_audio_latency_seconds": text_sandbox.get("first_agent_audio_latency_seconds"),
        "tunnel_diagnostics_available": bool(tunnel_diagnostics),
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def render_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-AUDIO-LATENCY-AUDIT-001",
            "",
            f"First agent audio latency seconds: `{result['first_agent_audio_latency_seconds']}`",
            f"Current observed latency seconds: `{result['current_observed_latency_seconds']}`",
            "Live target seconds: `2-3`",
            f"Live-ready latency: `{str(result['live_ready_latency']).lower()}`",
            f"Promising with warm session: `{result['promising_with_warm_session']}`",
            f"Needs warm-turn benchmark: `{str(result['needs_warm_turn_benchmark']).lower()}`",
            f"Another provider run should separate cold-start vs warm-turn latency: `{str(result['another_provider_run_should_separate_cold_start_vs_warm_turn']).lower()}`",
            "",
            "## Breakdown",
            f"Session creation time ms: `{result['session_creation_time_ms']}`",
            f"Tunnel setup time ms: `{result['tunnel_setup_time_ms']}`",
            f"Public endpoint preflight time ms: `{result['public_endpoint_preflight_time_ms']}`",
            f"WebSocket connect latency ms: `{result['websocket_connect_latency_ms']}`",
            f"Ping round trip ms: `{result['ping_round_trip_ms']}`",
            f"First transcript latency seconds: `{result['first_transcript_latency_seconds']}`",
            f"First user transcript latency seconds: `{result['first_user_transcript_latency_seconds']}`",
            f"Tool request latency ms: `{result['tool_request_latency_ms']}`",
            f"Time from tool response to agent audio seconds: `{result['time_from_tool_response_to_agent_audio_seconds']}`",
            "",
            "## Interpretation",
            f"First agent audio latency likely includes session setup/startup: `{str(result['first_agent_audio_latency_likely_includes_session_setup_startup']).lower()}`",
            f"First agent audio latency likely includes first-turn startup: `{str(result['first_agent_audio_latency_likely_includes_first_turn_startup']).lower()}`",
            result["latency_measurement_note"],
            "",
            "## Boundaries",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )


def main() -> None:
    sandbox = load_json(SANDBOX_RESULT_PATH)
    text_sandbox = load_optional_json(TEXT_SANDBOX_RESULT_PATH)
    tunnel_diagnostics = load_optional_json(TUNNEL_DIAGNOSTICS_RESULT_PATH)
    result = build_result(sandbox, text_sandbox, tunnel_diagnostics)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps({"current_observed_latency_seconds": result["current_observed_latency_seconds"], "needs_warm_turn_benchmark": result["needs_warm_turn_benchmark"]}, indent=2))


if __name__ == "__main__":
    main()
