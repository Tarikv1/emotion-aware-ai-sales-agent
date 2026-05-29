#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_latency_optimization_config.json"
RUNNER_PATH = ROOT / "scripts" / "run_ultravox_latency_optimization_benchmark_001.py"
SETTINGS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001" / "result.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001" / "report.md"
ENV_PATH = ROOT / "runtime" / "config" / "local" / "ultravox.env"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9]|wss://[^\"'\s]+|https://voice\.ultravox\.ai/[^\"'\s]+)"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def git_ignored(path: Path) -> bool:
    completed = subprocess.run(["git", "check-ignore", "-v", rel(path)], cwd=ROOT, text=True, capture_output=True, check=False)
    return completed.returncode == 0


def git_tracked(relative_path: str) -> bool:
    completed = subprocess.run(["git", "ls-files", "--error-unmatch", relative_path], cwd=ROOT, text=True, capture_output=True, check=False)
    return completed.returncode == 0


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def assert_required_config(config: dict[str, Any]) -> None:
    expected = {
        "benchmark_id": "ultravox_latency_optimization_001",
        "provider_calls_allowed_by_default": False,
        "use_ngrok_tunnel": True,
        "local_endpoint_host": "127.0.0.1",
        "local_endpoint_port": 8765,
        "local_endpoint_path": "/ultravox/project-sales-brain-next-move",
        "websocket_mode": "serverWebSocket",
        "input_sample_rate": 48000,
        "output_sample_rate": 48000,
        "existing_audio_only": True,
        "no_new_audio_generation": True,
        "no_microphone": True,
        "no_outbound_phone": True,
        "real_customer_data_allowed": False,
        "raw_audio_commit_allowed": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "max_provider_runs": 1,
        "max_audio_turns": 4,
        "warmup_turn_count": 1,
        "measured_turn_count": 3,
    }
    for key, value in expected.items():
        if config.get(key) != value:
            fail(f"config {key} must be {value!r}")
    gates = set(config.get("required_env_gates", []))
    for gate in (
        "ENABLE_ULTRAVOX_SANDBOX=1",
        "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1",
        "ULTRAVOX_API_KEY present",
        "LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1",
        "PROJECT_ULTRAVOX_TOOL_TOKEN present",
    ):
        if gate not in gates:
            fail(f"config missing required gate: {gate}")


def main() -> None:
    config = load_json(CONFIG_PATH)
    settings = load_json(SETTINGS_RESULT_PATH)
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    runner_text = RUNNER_PATH.read_text(encoding="utf-8") if RUNNER_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret("latency optimization benchmark", json.dumps(config) + json.dumps(settings) + json.dumps(result) + report + runner_text)
    assert_required_config(config)

    if ENV_PATH.exists() and not git_ignored(ENV_PATH):
        fail("runtime/config/local/ultravox.env exists but is not ignored by Git")
    if result.get("evaluation_id") != "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001":
        fail("unexpected latency optimization benchmark evaluation_id")
    if result.get("phase") != "4J8":
        fail("latency optimization benchmark must record phase 4J8")
    if result.get("benchmark_id") != config["benchmark_id"]:
        fail("result benchmark_id must match config")
    if result.get("unsupported_parameters_sent_as_confirmed") is not False:
        fail("unsupported parameters must not be sent as confirmed")

    confirmed = set(result.get("confirmed_supported_payload_keys_sent", []))
    sent = set(result.get("optimized_payload_keys_sent", []))
    unknown = sorted(sent - confirmed)
    if unknown:
        fail(f"optimized payload sent unconfirmed keys: {unknown}")
    for forbidden in ("lowLatency", "latencyMode", "optimizeStreamingLatency"):
        if forbidden in sent:
            fail(f"forbidden unsupported payload key sent: {forbidden}")

    for key in ("no_new_audio_generation", "existing_audio_only", "no_microphone", "no_outbound_phone"):
        if result.get(key) is not True:
            fail(f"{key} must be true")
    for key in (
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "raw_audio_stored_public",
        "audio_committed",
        "secrets_logged",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "local_model_generation_made",
        "model_weights_downloaded",
        "training_performed",
        "crm_email_calendar_actions_made",
        "side_effects_allowed",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
        "final_elevenlabs_replacement_claimed",
    ):
        assert_false(result, key)

    turns = result.get("turns")
    if not isinstance(turns, list):
        fail("turns must be a list")
    if len(turns) > int(config["max_audio_turns"]):
        fail("turn count exceeds configured max_audio_turns")
    measured = [turn for turn in turns if isinstance(turn, dict) and turn.get("measured_turn") is True and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))]
    if result.get("measured_warm_turn_count") != len(measured):
        fail("measured_warm_turn_count must equal measured turns with first-agent-audio latency")
    if result.get("optimized_warm_measured_turn_count") != len(measured):
        fail("optimized_warm_measured_turn_count must equal measured turn count")
    if result.get("provider_call_made") is True:
        gates = result.get("env_gates", {})
        for gate in config["required_env_gates"]:
            if gates.get(gate) is not True:
                fail(f"provider call was made without enabled gate: {gate}")
    for turn in turns:
        if not isinstance(turn, dict):
            fail("each turn must be an object")
        for key in (
            "first_user_transcript_time",
            "first_tool_request_time",
            "tool_response_time",
            "first_agent_transcript_time",
            "first_agent_audio_time",
            "final_agent_audio_time",
            "agent_audio_chunks",
            "agent_audio_bytes",
            "local_http_tool_request_count",
            "tool_response_followed",
            "fake_side_effect_detected",
            "product_truth_drift_detected",
            "boundary_respected",
        ):
            if key not in turn:
                fail(f"turn missing field: {key}")
    for path_text in result.get("input_audio_files", []):
        if git_tracked(str(path_text).replace("\\", "/")):
            fail(f"input audio artifact must not be tracked by Git: {path_text}")
    if settings.get("provider_call_made") is not False:
        fail("settings audit must remain provider-call-free")
    for line in (
        "Provider call made:",
        "Session created:",
        "WebSocket connected:",
        "Warm measured turn count:",
        "Optimized p50 first-agent-audio latency seconds:",
        "Optimized p90 first-agent-audio latency seconds:",
        "No new audio generated: `true`",
        "Audio committed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ):
        if line not in report:
            fail(f"benchmark report missing line: {line}")
    print("ULTRAVOX latency optimization benchmark validation passed.")


if __name__ == "__main__":
    main()
