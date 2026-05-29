#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_websocket_text_sandbox_config.json"
RUNNER_PATH = ROOT / "scripts" / "run_ultravox_websocket_text_sandbox_001.py"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001" / "report.md"
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


def git_ignored(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_no_secret_text(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def assert_false(result: dict[str, Any], key: str) -> None:
    if result.get(key) is not False:
        fail(f"{key} must be false")


def assert_true(result: dict[str, Any], key: str) -> None:
    if result.get(key) is not True:
        fail(f"{key} must be true")


def main() -> None:
    config = load_json(CONFIG_PATH)
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not RUNNER_PATH.is_file():
        fail(f"missing file: {rel(RUNNER_PATH)}")

    assert_no_secret_text("config/result/report/runner", json.dumps(config) + json.dumps(result) + report + RUNNER_PATH.read_text(encoding="utf-8"))

    if config.get("sandbox_id") != "ultravox_websocket_text_turn_sandbox":
        fail("unexpected websocket sandbox id")
    if config.get("provider_calls_allowed_by_default") is not False:
        fail("provider calls must be disabled by default")
    if config.get("websocket_mode") != "serverWebSocket":
        fail("websocket mode must be serverWebSocket")
    if config.get("set_output_medium") != "text":
        fail("output medium must be text")
    if config.get("max_hosted_sessions") != 1:
        fail("max hosted sessions must be 1")
    if config.get("max_text_turns") != 3:
        fail("max text turns must be 3")
    if len(config.get("synthetic_turns", [])) != 3:
        fail("three synthetic turns are required")

    if result.get("evaluation_id") != "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001":
        fail("unexpected websocket sandbox evaluation_id")
    if result.get("phase") != "4J4":
        fail("websocket sandbox must record phase 4J4")
    if ENV_PATH.exists() and not git_ignored(ENV_PATH):
        fail("runtime/config/local/ultravox.env exists but is not ignored by Git")
    if result.get("env_file_exists") and result.get("env_file_ignored") is not True:
        fail("env file was used or present without ignored evidence")

    for key in (
        "env_file_ignored",
        "api_key_present",
        "tool_token_present",
        "public_endpoint_preflight_passed",
        "provider_call_attempted",
        "provider_call_made",
        "ultravox_session_created",
        "join_url_received",
        "websocket_connected",
        "set_output_medium_sent",
        "raw_audio_stored",
        "audio_committed",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if key not in result or not isinstance(result[key], bool):
            fail(f"result missing boolean field: {key}")

    for key in (
        "synthetic_turns_attempted",
        "synthetic_turns_completed",
        "client_tool_invocation_count",
        "data_connection_tool_invocation_count",
        "http_tool_endpoint_request_count",
        "tool_result_sent_count",
        "agent_transcript_count",
        "user_transcript_count",
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
        "raw_audio_stored",
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

    if result.get("websocket_connected") and result.get("join_url_received") is not True:
        fail("websocket_connected requires join_url_received")
    if result.get("websocket_connected") and result.get("join_url_full_recorded") is not False:
        fail("joinUrl must not be recorded in full")
    if result.get("tool_boundary_enforced") is True:
        evidence_count = result.get("client_tool_invocation_count", 0) + result.get("data_connection_tool_invocation_count", 0) + result.get("http_tool_endpoint_request_count", 0)
        if evidence_count <= 0:
            fail("tool boundary claimed without tool invocation or HTTP endpoint request evidence")

    if not isinstance(result.get("final_transcripts_sanitized"), list):
        fail("final_transcripts_sanitized must be a list")
    if result.get("provider_call_made") and result.get("provider_call_attempted") is not True:
        fail("provider_call_made requires provider_call_attempted")
    if result.get("ultravox_session_created") and result.get("join_url_received") is not True:
        fail("created session must record join_url_received true")

    required_report_lines = [
        "Provider call made:",
        "Ultravox session created:",
        "WebSocket connected:",
        "Synthetic turns attempted:",
        "Tool invocation count:",
        "Local HTTP tool request count:",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"websocket sandbox report missing line: {line}")

    print("ULTRAVOX websocket text sandbox validation passed.")


if __name__ == "__main__":
    main()
