#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MOCK_SCRIPT = ROOT / "scripts" / "run_ultravox_tool_boundary_mock_001.py"
MOCK_TOOL = ROOT / "runtime" / "audio_backends" / "ultravox_sales_brain_mock.py"
PROMPT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_agent_prompt.md"
STAGE_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_call_stage_plan.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001" / "report.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
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


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def load_mock_module() -> Any:
    if not MOCK_TOOL.is_file():
        fail(f"missing file: {rel(MOCK_TOOL)}")
    spec = importlib.util.spec_from_file_location("ultravox_sales_brain_mock_under_test", MOCK_TOOL)
    if spec is None or spec.loader is None:
        fail("could not import mock tool")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ultravox_sales_brain_mock_under_test"] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    for path in (MOCK_SCRIPT, MOCK_TOOL, PROMPT_PATH, STAGE_PATH, RESULT_PATH, REPORT_PATH):
        if not path.is_file():
            fail(f"required mock boundary artifact missing: {rel(path)}")

    result = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_no_secret_patterns(json.dumps(result) + report_text)

    if result.get("evaluation_id") != "ULTRAVOX-TOOL-BOUNDARY-MOCK-001":
        fail("unexpected mock evaluation_id")
    if result.get("provider_calls_made") is not False:
        fail("mock simulation must not make provider calls")
    if result.get("runtime_behavior_changed") is not False:
        fail("mock simulation must not change runtime behavior")
    if result.get("response_text_changed") is not False:
        fail("mock simulation must not change canonical response text")

    metrics = result.get("metrics", {})
    expected_metrics = {
        "case_count": 8,
        "passed_count": 8,
        "failed_count": 0,
        "tool_called_required": True,
        "fake_side_effect_count": 0,
        "unsupported_claim_count": 0,
        "internal_language_count": 0,
    }
    for key, expected in expected_metrics.items():
        if metrics.get(key) != expected:
            fail(f"metrics.{key} must be {expected!r}, got {metrics.get(key)!r}")
    if metrics.get("boundary_respected_count") != 8:
        fail("all cases must respect boundaries")
    if metrics.get("response_short_enough_count") != 8:
        fail("all responses must be short enough")

    mock_module = load_mock_module()
    for function_name in ("build_mock_project_memory", "handle_project_sales_brain_next_move", "validate_ultravox_tool_response"):
        if not callable(getattr(mock_module, function_name, None)):
            fail(f"mock tool missing callable: {function_name}")

    case_results = result.get("case_results", [])
    if len(case_results) != 8:
        fail("expected exactly 8 mock cases")
    for case in case_results:
        if case.get("passed") is not True:
            fail(f"{case.get('case_id')} did not pass")
        if case.get("tool_called_required") is not True:
            fail(f"{case.get('case_id')} did not require tool call")
        response = case.get("tool_response")
        if not isinstance(response, dict):
            fail(f"{case.get('case_id')} missing tool_response")
        validation_errors = mock_module.validate_ultravox_tool_response(response)
        if validation_errors:
            fail(f"{case.get('case_id')} response failed mock validator: {validation_errors}")
        if response.get("side_effects_allowed") is not False:
            fail(f"{case.get('case_id')} allowed side effects")

    if "Hosted sandbox next step" not in report_text:
        fail("mock report must include hosted sandbox next-step statement")
    print("ULTRAVOX tool boundary mock validation passed.")


if __name__ == "__main__":
    main()
