#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "full_call_gauntlet.py"
RUNNER = ROOT / "scripts" / "run_prod_007_full_call_gauntlet.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-007-full-call-gauntlet.json"
DOC_PATH = ROOT / "docs" / "product" / "PROD_007_FULL_CALL_GAUNTLET.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-007-full-call-gauntlet" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-007-full-call-gauntlet" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"

EXPECTED_ID = "PROD-007-full-call-gauntlet"
EXPECTED_BASELINE = "old_core_pre_full_sale"
EXPECTED_CANDIDATE = "brain_002_full_sale_candidate"
REQUIRED_METRICS = {
    "safe_close_rate",
    "hard_failure_rate",
    "non_sale_correctness",
    "close_attempt_quality",
    "call_control_correctness",
    "retrieval_default_off",
    "latency_readiness",
}
REQUIRED_LABELS = {
    "sale_eligible",
    "non_sale_correct",
    "support_only",
    "complaint_recovery",
    "escalation_only",
    "unsafe_for_closing",
}
BLOCKED_STRINGS = [
    "credit card",
    "customer phone",
    "raw private audio",
    "raw private transcript",
    "api key",
    "provider call made",
    "download_performed\": true",
    "provider_calls_made\": true",
    "private_data_read\": true",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_007_id"] == EXPECTED_ID, payload)
    assert_condition(payload["baseline_id"] == EXPECTED_BASELINE, payload)
    assert_condition(payload["candidate_id"] == EXPECTED_CANDIDATE, payload)
    assert_condition(payload["experiment_protocol"]["fixed_cases"] is True, payload)
    assert_condition(payload["experiment_protocol"]["same_calls_for_baseline_and_candidate"] is True, payload)
    assert_condition(payload["experiment_protocol"]["editable_surface"] == "runtime_state_decision_packet", payload)

    boundaries = payload["boundaries"]
    assert_condition(boundaries["provider_calls_made"] is False, boundaries)
    assert_condition(boundaries["private_data_read"] is False, boundaries)
    assert_condition(boundaries["runtime_behavior_changed"] is False, boundaries)
    assert_condition(boundaries["retrieval_default"] == "disabled", boundaries)
    assert_condition(boundaries["dataset_download_performed"] is False, boundaries)

    metrics = payload["metrics"]
    assert_condition(REQUIRED_METRICS.issubset(set(metrics)), metrics)

    summary = payload["summary"]
    baseline = summary["baseline"]
    candidate = summary["candidate"]
    comparison = summary["comparison"]

    assert_condition(summary["call_count"] >= 6, summary)
    assert_condition(summary["turn_count"] >= 12, summary)
    assert_condition(summary["eligible_close_count"] >= 1, summary)
    assert_condition(summary["non_sale_call_count"] >= 5, summary)
    assert_condition(candidate["hard_failure_rate"] == 0.0, candidate)
    assert_condition(candidate["safe_close_rate"] == 1.0, candidate)
    assert_condition(candidate["non_sale_correctness"] == 1.0, candidate)
    assert_condition(candidate["call_control_correctness"] == 1.0, candidate)
    assert_condition(candidate["retrieval_enabled_count"] == 0, candidate)
    assert_condition(candidate["provider_calls_made"] is False, candidate)
    assert_condition(candidate["private_data_read"] is False, candidate)
    assert_condition(candidate["max_latency_ms"] <= metrics["latency_readiness"]["acceptable_ms"], candidate)
    assert_condition(comparison["candidate_safe_close_rate_delta"] > 0, comparison)
    assert_condition(comparison["candidate_non_sale_correctness_delta"] > 0, comparison)
    assert_condition(comparison["candidate_hard_failure_rate_delta"] < 0, comparison)
    assert_condition(comparison["candidate_call_control_correctness_delta"] > 0, comparison)
    assert_condition(comparison["decision"].startswith("keep_brain_002"), comparison)

    calls = payload["calls"]
    labels = {call["scenario_label"] for call in calls}
    assert_condition(REQUIRED_LABELS.issubset(labels), labels)
    for call in calls:
        assert_condition(call["baseline"]["case_id"] == call["candidate"]["case_id"], call)
        assert_condition(call["candidate"]["retrieval_enabled"] is False, call)
        assert_condition(call["candidate"]["provider_calls_made"] is False, call)
        assert_condition(call["candidate"]["private_data_read"] is False, call)
        assert_condition(call["candidate"]["hard_failure"] is False, call)
        assert_condition(call["candidate"]["state_packet"]["response"]["final_response"] == call["candidate"]["response"], call)
        if call["expected_outcome"] == "sale_ready":
            assert_condition(call["candidate"]["sale_ready"] is True, call)
            assert_condition(call["candidate"]["call_control"] == "close-and-log-sale-ready", call)
        else:
            assert_condition(call["candidate"]["non_sale_correct"] is True, call)
            assert_condition(call["candidate"]["sale_ready"] is False, call)

    combined_text = (json.dumps(payload, sort_keys=True) + "\n" + report).lower().replace("\\", "/")
    for blocked in BLOCKED_STRINGS:
        assert_condition(blocked not in combined_text, blocked)
    for marker in [
        "PROD-007",
        "full-call gauntlet",
        "old core",
        "BRAIN-002",
        "safe close rate",
        "hard failure rate",
        "non-sale correctness",
        "retrieval disabled by default",
    ]:
        assert_condition(marker.lower() in combined_text, marker)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-007 gauntlet module"),
        (RUNNER, "PROD-007 runner"),
        (CASE_PATH, "PROD-007 case file"),
        (DOC_PATH, "PROD-007 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_007_full_call_gauntlet.py" in commands, "PROD-007 runner missing from command map.")
    assert_condition("validate_prod_007_full_call_gauntlet.py" in commands, "PROD-007 validator missing from command map.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-007 full-call gauntlet validation passed.")


if __name__ == "__main__":
    main()
