#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MOCK_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TOOL-BOUNDARY-MOCK-001" / "result.json"
HOSTED_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001" / "result.json"
DECISION_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "result.json"
DECISION_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001" / "report.md"


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


def expected_recommendation(mock: dict[str, Any], hosted: dict[str, Any]) -> str:
    mock_passed = mock.get("summary", {}).get("tool_boundary_passed") is True
    provider_run = hosted.get("provider_call_made") is True and hosted.get("run_status") == "provider_run"
    provider_tool_calls_work = hosted.get("tool_calls_work") is True
    provider_failed_boundary = hosted.get("tool_boundary_supported") is False or hosted.get("run_status") == "failed"
    if not mock_passed:
        return "fix tool contract before any provider sandbox"
    if mock_passed and not provider_run:
        return "optional gated Ultravox hosted sandbox next"
    if provider_run and provider_tool_calls_work:
        return "limited synthetic voice call evaluation next"
    if provider_failed_boundary:
        return "keep Ultravox as research/reference only"
    return "keep Ultravox as research/reference only"


def main() -> None:
    mock = load_json(MOCK_RESULT)
    hosted = load_json(HOSTED_RESULT)
    decision = load_json(DECISION_RESULT)
    report_text = DECISION_REPORT.read_text(encoding="utf-8") if DECISION_REPORT.is_file() else ""
    if not report_text:
        fail(f"missing file: {rel(DECISION_REPORT)}")

    if decision.get("evaluation_id") != "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001":
        fail("unexpected feasibility decision evaluation_id")
    expected = expected_recommendation(mock, hosted)
    if decision.get("recommendation") != expected:
        fail(f"recommendation must be {expected!r}, got {decision.get('recommendation')!r}")

    for key in ("live_wiring_allowed", "production_call_allowed", "real_customer_data_allowed"):
        if decision.get(key) is not False:
            fail(f"{key} must always stay false")
    if decision.get("memory_ownership_decision") != "project_runtime_owns_canonical_memory":
        fail("canonical memory ownership must stay with project runtime")
    if decision.get("sales_brain_ownership_decision") != "project_runtime_owns_sales_brain_and_campaign_truth":
        fail("sales brain and campaign truth must stay project-owned")
    if decision.get("ultravox_product_truth_owner") is not False:
        fail("Ultravox must not own product truth")
    if decision.get("side_effects_allowed") is not False:
        fail("side effects must stay blocked")
    if decision.get("runtime_behavior_changed") is not False:
        fail("decision must record no runtime behavior change")
    if decision.get("response_text_changed") is not False:
        fail("decision must record no response text change")

    required_report_lines = [
        f"Recommendation: `{expected}`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Project runtime owns canonical memory.",
        "Project runtime owns the sales brain and campaign truth.",
    ]
    for line in required_report_lines:
        if line not in report_text:
            fail(f"decision report missing line: {line}")
    print("ULTRAVOX hosted feasibility decision validation passed.")


if __name__ == "__main__":
    main()
