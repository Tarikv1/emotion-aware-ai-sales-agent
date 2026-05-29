#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STRATEGY_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-ENDPOINT-STRATEGY-001" / "result.json"
STRATEGY_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-ENDPOINT-STRATEGY-001" / "report.md"
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_endpoint_config.json"
SERVER_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_server.py"
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
    result = load_json(STRATEGY_RESULT)
    config = load_json(CONFIG_PATH)
    report = STRATEGY_REPORT.read_text(encoding="utf-8") if STRATEGY_REPORT.is_file() else ""
    if not report:
        fail(f"missing file: {rel(STRATEGY_REPORT)}")
    if not SERVER_PATH.is_file():
        fail(f"missing file: {rel(SERVER_PATH)}")
    assert_no_secret(json.dumps(result) + json.dumps(config) + report + SERVER_PATH.read_text(encoding="utf-8"))

    if result.get("evaluation_id") != "ULTRAVOX-TOOL-ENDPOINT-STRATEGY-001":
        fail("unexpected strategy evaluation_id")
    if result.get("primary_next_path") != "local_http_endpoint_first_then_gated_temporary_https_tunnel":
        fail("strategy must recommend local HTTP endpoint first, then gated temporary HTTPS tunnel")
    if result.get("temporary_per_call_tool_preferred_for_testing") is not True:
        fail("temporary per-call tool must be preferred for testing")
    if result.get("dashboard_durable_tool_waits") is not True:
        fail("dashboard/durable setup must wait")
    if config.get("endpoint_id") != "project_sales_brain_next_move_local_http":
        fail("unexpected local endpoint config id")
    for key in ("public_exposure_allowed", "tunnel_allowed_by_default", "live_wiring_allowed", "production_call_allowed", "real_customer_data_allowed", "side_effects_allowed"):
        if config.get(key) is not False:
            fail(f"config {key} must be false")
    if config.get("auth_required") is not True:
        fail("local endpoint auth must be required")
    if "HTTP tool with temporary HTTPS tunnel" not in report:
        fail("strategy report must compare HTTP tunnel option")
    print("ULTRAVOX tool endpoint strategy validation passed.")


if __name__ == "__main__":
    main()
