#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-PLAN-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-PLAN-001" / "report.md"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9])"
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


def assert_no_secret(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret(json.dumps(result) + report)
    if result.get("evaluation_id") != "ULTRAVOX-TUNNEL-SANDBOX-PLAN-001":
        fail("unexpected tunnel plan evaluation_id")
    if result.get("public_tunnel_opened") is not False:
        fail("tunnel must not be opened in this phase")
    if result.get("provider_calls_made") is not False:
        fail("tunnel plan must not make provider calls")
    required_gates = {
        "ENABLE_ULTRAVOX_SANDBOX=1",
        "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1",
        "LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1",
        "PROJECT_ULTRAVOX_TOOL_TOKEN present",
        "ULTRAVOX_API_KEY present",
    }
    missing = sorted(required_gates - set(result.get("required_future_gates", [])))
    if missing:
        fail(f"missing future gate(s): {missing}")
    for control in ("random auth token", "synthetic prompts only", "no real customer data", "no outbound phone", "logs sanitized", "stop tunnel after run"):
        if control not in result.get("minimum_safety_controls", []):
            fail(f"missing safety control: {control}")
    if result.get("dashboard_durable_tool_waits") is not True:
        fail("dashboard/durable tool setup must wait")
    if "Do not open tunnel in this phase" not in report:
        fail("report must state no tunnel in this phase")
    print("ULTRAVOX tunnel sandbox plan validation passed.")


if __name__ == "__main__":
    main()
