#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
QUALITY_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001" / "result.json"
QUALITY_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001" / "report.md"
AUDIT_PATH = ROOT / "scripts" / "audit_ultravox_websocket_audio_sandbox_001.py"
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


def main() -> None:
    sandbox = load_json(SANDBOX_RESULT)
    quality = load_json(QUALITY_RESULT)
    report = QUALITY_REPORT.read_text(encoding="utf-8") if QUALITY_REPORT.is_file() else ""
    if not report:
        fail(f"missing file: {rel(QUALITY_REPORT)}")
    if not AUDIT_PATH.is_file():
        fail(f"missing file: {rel(AUDIT_PATH)}")
    assert_no_secret("audio sandbox quality evidence/audit", json.dumps(sandbox) + json.dumps(quality) + report + AUDIT_PATH.read_text(encoding="utf-8"))

    if quality.get("evaluation_id") != "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001":
        fail("unexpected audio quality evaluation_id")
    if quality.get("phase") != "4J5B":
        fail("audio quality must record phase 4J5B")

    for key in (
        "audio_input_generation_succeeded",
        "manual_audio_inputs_found",
        "manual_audio_conversion_succeeded",
        "user_transcript_observed",
        "agent_audio_observed",
        "agent_transcript_observed",
        "project_tool_called",
        "tool_boundary_enforced",
        "ultravox_invented_product_facts",
        "ultravox_claimed_side_effects",
        "no_openai_affiliation_claim",
        "response_follows_project_tool",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if key not in quality or not isinstance(quality[key], bool):
            fail(f"quality missing boolean field: {key}")

    if quality.get("project_tool_called") != (sandbox.get("local_http_tool_request_count", 0) > 0 or sandbox.get("tool_result_sent_count", 0) > 0):
        fail("project_tool_called must match sandbox tool evidence")
    if quality.get("manual_audio_inputs_found") != (sandbox.get("manual_audio_inputs_found") is True):
        fail("manual_audio_inputs_found must match sandbox evidence")
    if quality.get("manual_audio_conversion_succeeded") != (sandbox.get("manual_audio_conversion_succeeded") is True):
        fail("manual_audio_conversion_succeeded must match sandbox evidence")
    if quality.get("agent_audio_observed") != (sandbox.get("agent_audio_chunks_received", 0) > 0):
        fail("agent_audio_observed must match audio chunk evidence")
    if quality.get("user_transcript_observed") != (sandbox.get("user_transcript_count", 0) > 0):
        fail("user_transcript_observed must match sandbox transcript evidence")
    if quality.get("tool_boundary_enforced") and not quality.get("project_tool_called"):
        fail("tool boundary cannot be enforced without project tool evidence")

    if sandbox.get("synthetic_audio_turns_attempted", 0) == 0:
        allowed_zero_turn_blockers = {"no_automated_audio_interaction", "manual_audio_inputs_missing", "manual_audio_conversion_failed"}
        if quality.get("blocker_classification") not in allowed_zero_turn_blockers:
            fail("no automated audio interaction must be classified honestly")
        if quality.get("tool_boundary_enforced") is not False:
            fail("no automated audio interaction cannot claim tool-boundary success")
    if quality.get("ultravox_claimed_side_effects") is True and int(quality.get("crm_email_calendar_claim_count", 0)) <= 0:
        fail("side effect claims must include CRM/email/calendar claim count evidence")
    if quality.get("ultravox_invented_product_facts") is True and quality.get("response_follows_project_tool") is True:
        fail("invented product facts cannot be marked as following the project tool")

    for key in ("live_wiring_allowed", "production_call_allowed", "real_customer_data_allowed", "runtime_behavior_changed", "response_text_changed"):
        if quality.get(key) is not False:
            fail(f"{key} must remain false")

    required_report_lines = [
        "Audio input generation succeeded:",
        "Manual audio inputs found:",
        "Manual audio conversion succeeded:",
        "Prepared audio input count:",
        "Manual audio converter used:",
        "User transcript observed:",
        "Agent audio observed:",
        "Agent transcript observed:",
        "Project tool called:",
        "Tool boundary enforced:",
        "Response follows project tool:",
        "Blocker classification:",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"audio quality report missing line: {line}")

    print("ULTRAVOX websocket audio sandbox quality validation passed.")


if __name__ == "__main__":
    main()
