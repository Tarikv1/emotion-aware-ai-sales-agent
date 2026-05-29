#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SERVER_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_server.py"
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_endpoint_config.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LOCAL-TOOL-ENDPOINT-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LOCAL-TOOL-ENDPOINT-001" / "report.md"
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


def load_server_module() -> Any:
    spec = importlib.util.spec_from_file_location("ultravox_local_tool_server_under_test", SERVER_PATH)
    if spec is None or spec.loader is None:
        fail("could not import local tool server")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ultravox_local_tool_server_under_test"] = module
    spec.loader.exec_module(module)
    return module


def assert_no_secret(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    config = load_json(CONFIG_PATH)
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    server = load_server_module()
    assert_no_secret(json.dumps(config) + json.dumps(result) + report + SERVER_PATH.read_text(encoding="utf-8"))

    for function_name in ("build_server", "handle_request", "run_local_server_once_for_tests", "validate_request_schema", "validate_response_schema"):
        if not callable(getattr(server, function_name, None)):
            fail(f"server missing callable: {function_name}")
    if result.get("evaluation_id") != "ULTRAVOX-LOCAL-TOOL-ENDPOINT-001":
        fail("unexpected endpoint evaluation_id")
    if result.get("case_count") != 8 or result.get("passed_count") != 8 or result.get("failed_count") != 0:
        fail("all 8 synthetic endpoint cases must pass")
    auth = result.get("auth_tests", {})
    if auth.get("missing_token_rejected") is not True or auth.get("invalid_token_rejected") is not True:
        fail("missing and invalid auth tokens must be rejected")
    for key in (
        "public_exposure_allowed",
        "public_tunnel_opened",
        "provider_calls_made",
        "ultravox_hosted_call_made",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "side_effects_allowed",
        "crm_email_calendar_actions_allowed",
        "live_wiring_allowed",
        "production_call_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if result.get(key) is not False:
            fail(f"{key} must be false")
    if result.get("project_sales_brain_owner") != "project_runtime":
        fail("project must remain sales brain owner")
    if result.get("canonical_memory_owner") != "project_runtime":
        fail("project must remain canonical memory owner")
    if result.get("fake_side_effect_count") != 0 or result.get("unsupported_claim_count") != 0 or result.get("internal_label_leak_count") != 0:
        fail("endpoint evidence contains unsafe response counts")
    for case in result.get("case_results", []):
        if case.get("http_status") != 200 or case.get("passed") is not True:
            fail(f"case failed: {case.get('case_id')}")
    print("ULTRAVOX local tool endpoint validation passed.")


if __name__ == "__main__":
    main()
