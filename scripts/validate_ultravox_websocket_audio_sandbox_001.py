#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_websocket_audio_sandbox_config.json"
RUNNER_PATH = ROOT / "scripts" / "run_ultravox_websocket_audio_sandbox_001.py"
INPUT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-MANUAL-AUDIO-INPUTS-001" / "result.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "report.md"
ENV_PATH = ROOT / "runtime" / "config" / "local" / "ultravox.env"
LOCAL_ARTIFACT_PREFIXES = (
    "local_artifacts/audio_outputs/ultravox/manual_inputs/",
    "local_artifacts/audio_outputs/ultravox/prepared_inputs/",
    "local_artifacts/audio_outputs/ultravox/synthetic_inputs/",
    "local_artifacts/audio_outputs/ultravox/agent_outputs/",
)
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


def git_ignored(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def git_tracked(relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def assert_false(result: dict[str, Any], key: str) -> None:
    if result.get(key) is not False:
        fail(f"{key} must be false")


def assert_local_artifact_path(value: str) -> None:
    normalized = value.replace("\\", "/")
    if not any(normalized.startswith(prefix) for prefix in LOCAL_ARTIFACT_PREFIXES):
        fail(f"audio artifact path outside local_artifacts audio boundary: {value}")
    if ".." in Path(normalized).parts:
        fail(f"audio artifact path must not contain parent traversal: {value}")
    if git_tracked(normalized):
        fail(f"audio artifact is tracked by Git: {value}")


def main() -> None:
    config = load_json(CONFIG_PATH)
    input_result = load_json(INPUT_RESULT_PATH)
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not RUNNER_PATH.is_file():
        fail(f"missing file: {rel(RUNNER_PATH)}")
    assert_no_secret("audio sandbox evidence/config/runner", json.dumps(config) + json.dumps(input_result) + json.dumps(result) + report + RUNNER_PATH.read_text(encoding="utf-8"))

    if config.get("sandbox_id") != "ultravox_websocket_synthetic_audio_sandbox":
        fail("unexpected audio sandbox id")
    if config.get("provider_calls_allowed_by_default") is not False:
        fail("provider calls must be disabled by default")
    if config.get("websocket_mode") != "serverWebSocket":
        fail("websocket mode must be serverWebSocket")
    if config.get("input_audio_format") != "s16le_pcm":
        fail("input_audio_format must be s16le_pcm")
    if config.get("max_hosted_sessions") != 1:
        fail("max hosted sessions must be 1")
    if config.get("max_audio_turns") != 2:
        fail("max audio turns must be 2")

    if result.get("evaluation_id") != "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001":
        fail("unexpected audio sandbox evaluation_id")
    if result.get("phase") != "4J5B":
        fail("audio sandbox must record phase 4J5B")
    if ENV_PATH.exists() and not git_ignored(ENV_PATH):
        fail("runtime/config/local/ultravox.env exists but is not ignored by Git")
    if result.get("env_file_exists") and result.get("env_file_ignored") is not True:
        fail("env file was used or present without ignored evidence")

    for key in (
        "manual_audio_inputs_found",
        "manual_audio_input_folder_exists",
        "manual_audio_conversion_attempted",
        "manual_audio_conversion_succeeded",
        "provider_call_made",
        "session_created",
        "websocket_connected",
        "tool_call_attempted",
        "tool_call_succeeded",
        "raw_audio_stored_public",
        "audio_committed",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if key not in result or not isinstance(result[key], bool):
            fail(f"result missing boolean field: {key}")

    for key in (
        "manual_audio_input_files_found",
        "manual_audio_expected_case_count",
        "prepared_audio_inputs_count",
        "synthetic_audio_turns_attempted",
        "synthetic_audio_turns_completed",
        "user_transcript_count",
        "agent_transcript_count",
        "agent_audio_chunks_received",
        "agent_audio_bytes_received",
        "local_http_tool_request_count",
        "product_truth_drift_count",
        "unsupported_claim_count",
        "fake_side_effect_count",
        "crm_email_calendar_claim_count",
        "internal_label_leak_count",
        "source_boundary_violation_count",
        "memory_conflict_count",
    ):
        if key not in result or not isinstance(result[key], int) or result[key] < 0:
            fail(f"result missing non-negative integer field: {key}")

    for key in (
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "raw_audio_stored_public",
        "audio_committed",
        "crm_email_calendar_actions_made",
        "side_effects_allowed",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        assert_false(result, key)

    if result.get("project_sales_brain_owner") != "project_runtime":
        fail("project must remain sales brain owner")
    if result.get("canonical_memory_owner") != "project_runtime":
        fail("project must remain canonical memory owner")

    env_gates = result.get("env_gates")
    if not isinstance(env_gates, dict):
        fail("env_gates must be recorded")
    if result.get("provider_call_made"):
        for gate in (
            "ENABLE_ULTRAVOX_SANDBOX=1",
            "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1",
            "ULTRAVOX_API_KEY present",
            "LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1",
            "PROJECT_ULTRAVOX_TOOL_TOKEN present",
        ):
            if env_gates.get(gate) is not True:
                fail(f"provider call made without enabled gate: {gate}")
        if input_result.get("conversion_succeeded") is not True or result.get("manual_audio_conversion_succeeded") is not True:
            fail("provider call made despite missing prepared manual audio conversion")
        if int(result.get("prepared_audio_inputs_count", 0)) < int(result.get("max_audio_turns", 2)):
            fail("provider call made without enough prepared manual audio inputs")

    for key in ("input_audio_files", "agent_audio_files_written_under_local_artifacts"):
        paths = result.get(key)
        if paths is None:
            continue
        if not isinstance(paths, list):
            fail(f"{key} must be a list")
        for path in paths:
            if not isinstance(path, str):
                fail(f"{key} entries must be strings")
            assert_local_artifact_path(path)

    if result.get("audio_sandbox_success_claimed") is True:
        if result.get("user_transcript_count", 0) <= 0 and result.get("agent_audio_chunks_received", 0) <= 0:
            fail("audio sandbox success claimed without user transcript or agent audio evidence")
    if result.get("manual_audio_inputs_found") != (input_result.get("input_files_found", 0) >= int(result.get("max_audio_turns", 2))):
        fail("manual_audio_inputs_found must match manual input evidence")
    if result.get("manual_audio_conversion_succeeded") != (input_result.get("conversion_succeeded") is True):
        fail("manual_audio_conversion_succeeded must match manual input evidence")
    if result.get("prepared_audio_inputs_count") != input_result.get("prepared_case_count"):
        fail("prepared_audio_inputs_count must match manual input evidence")

    required_report_lines = [
        "Provider call made:",
        "Ultravox session created:",
        "WebSocket connected:",
        "Manual audio inputs found:",
        "Prepared audio input count:",
        "Manual audio converter used:",
        "Audio turns attempted:",
        "User transcript count:",
        "Agent audio chunks received:",
        "Local HTTP tool request count:",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"audio sandbox report missing line: {line}")

    print("ULTRAVOX websocket audio sandbox validation passed.")


if __name__ == "__main__":
    main()
