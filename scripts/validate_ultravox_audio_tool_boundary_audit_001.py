#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001" / "report.md"
AUDIT_SCRIPT = ROOT / "scripts" / "audit_ultravox_audio_tool_boundary_001.py"
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


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not AUDIT_SCRIPT.is_file():
        fail(f"missing file: {rel(AUDIT_SCRIPT)}")
    assert_no_secret("tool boundary audit evidence", json.dumps(result) + report)

    if result.get("evaluation_id") != "ULTRAVOX-AUDIO-TOOL-BOUNDARY-AUDIT-001":
        fail("unexpected tool-boundary audit evaluation_id")
    if result.get("phase") != "4J6":
        fail("tool-boundary audit must record phase 4J6")
    if result.get("local_http_tool_request_count") != 2:
        fail("4J5B audio evidence should have two local HTTP tool requests")
    if result.get("tool_call_attempted") is not True or result.get("tool_call_succeeded") is not True:
        fail("tool call must be attempted and succeeded")
    if result.get("tool_called_for_each_relevant_turn") is not True:
        fail("tool must be called for each relevant turn")
    for key in (
        "side_effects_allowed",
        "new_provider_call_made",
        "new_audio_generated",
        "audio_files_copied",
        "audio_files_committed",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        assert_false(result, key)
    for key in (
        "fake_side_effect_count",
        "unsupported_claim_count",
        "product_truth_drift_count",
        "crm_email_calendar_claim_count",
    ):
        if result.get(key) != 0:
            fail(f"{key} must be zero")
    if result.get("canonical_memory_owner") != "project_runtime":
        fail("canonical memory owner must stay project_runtime")
    if result.get("sales_brain_owner") != "project_runtime":
        fail("sales brain owner must stay project_runtime")
    if result.get("ultravox_session_memory_limited_to_session_context") is not True:
        fail("Ultravox session memory must be limited to session context")

    required_report_lines = [
        "Local HTTP tool request count: `2`",
        "Tool call attempted: `true`",
        "Tool call succeeded: `true`",
        "Tool called for each relevant turn: `true`",
        "Side effects allowed: `false`",
        "Fake side effect count: `0`",
        "Unsupported claim count: `0`",
        "Product truth drift count: `0`",
        "CRM/email/calendar claim count: `0`",
        "Canonical memory owner: `project_runtime`",
        "Sales brain owner: `project_runtime`",
        "New provider call made: `false`",
        "New audio generated: `false`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"tool-boundary audit report missing line: {line}")

    print("ULTRAVOX audio tool-boundary audit validation passed.")


if __name__ == "__main__":
    main()
