#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001" / "result.json"
QUALITY_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001" / "result.json"
QUALITY_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001" / "report.md"
AUDIT_PATH = ROOT / "scripts" / "audit_ultravox_websocket_text_sandbox_001.py"
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
    assert_no_secret("sandbox/quality/report/audit", json.dumps(sandbox) + json.dumps(quality) + report + AUDIT_PATH.read_text(encoding="utf-8"))

    if quality.get("evaluation_id") != "ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-QUALITY-001":
        fail("unexpected websocket quality evaluation_id")
    if quality.get("phase") != "4J4":
        fail("websocket quality must record phase 4J4")

    for key in (
        "tool_boundary_enforced",
        "project_tool_called",
        "ultravox_invented_product_facts",
        "ultravox_claimed_side_effects",
        "source_boundary_respected",
        "no_crm_email_calendar_claims",
        "no_openai_affiliation_claim",
        "response_follows_project_tool",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if key not in quality or not isinstance(quality[key], bool):
            fail(f"quality missing boolean field: {key}")

    if quality.get("project_tool_called") != (sandbox.get("http_tool_endpoint_request_count", 0) > 0 or sandbox.get("tool_result_sent_count", 0) > 0):
        fail("project_tool_called must match sandbox tool evidence")
    if quality.get("tool_boundary_enforced") and not quality.get("project_tool_called"):
        fail("tool boundary cannot be enforced without a project tool call")
    if sandbox.get("synthetic_turns_attempted", 0) == 0 and quality.get("blocker_classification") != "websocket_client_blocker":
        fail("no automated interaction must be classified as websocket_client_blocker")
    if sandbox.get("synthetic_turns_attempted", 0) == 0 and quality.get("tool_boundary_enforced") is not False:
        fail("no automated interaction cannot claim tool-boundary success")

    if quality.get("ultravox_claimed_side_effects") is True:
        if quality.get("no_crm_email_calendar_claims") is not False:
            fail("side effect claims must fail CRM/email/calendar quality")
    if quality.get("ultravox_invented_product_facts") is True and quality.get("source_boundary_respected") is True:
        fail("invented product facts must fail source boundary")
    if quality.get("live_wiring_allowed") is not False:
        fail("live wiring must remain false")
    if quality.get("production_call_allowed") is not False:
        fail("production call must remain false")
    if quality.get("runtime_behavior_changed") is not False:
        fail("runtime behavior changed must remain false")
    if quality.get("response_text_changed") is not False:
        fail("response text changed must remain false")

    required_report_lines = [
        "Tool boundary enforced:",
        "Project tool called:",
        "Source boundary respected:",
        "Response follows project tool:",
        "Blocker classification:",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"quality report missing line: {line}")

    print("ULTRAVOX websocket text sandbox quality validation passed.")


if __name__ == "__main__":
    main()
