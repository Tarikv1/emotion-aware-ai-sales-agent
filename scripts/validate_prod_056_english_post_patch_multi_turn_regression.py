#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
SOURCE_CHECKPOINT_ID = "PROD-055-english-multi-turn-runtime-patch"
PREVIOUS_STRESS_CHECKPOINT_ID = "PROD-054-english-multi-turn-naturalness-stress-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-056-english-post-patch-multi-turn-regression.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_056_english_post_patch_multi_turn_regression.py",
    "runner": ROOT / "scripts" / "run_prod_056_english_post_patch_multi_turn_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_056_english_post_patch_multi_turn_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_056_ENGLISH_POST_PATCH_MULTI_TURN_REGRESSION.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "previous_stress_result": ROOT
    / "research"
    / "experiments"
    / "generated"
    / PREVIOUS_STRESS_CHECKPOINT_ID
    / "result.json",
    "previous_stress_cases": ROOT
    / "research"
    / "experiments"
    / "cases"
    / "prod-054-english-multi-turn-naturalness-stress-review.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "runtime_regression_reviews": OUT_DIR / "runtime_regression_reviews.json",
    "callback_scheduling_reviews": OUT_DIR / "callback_scheduling_reviews.json",
    "terminal_boundary_reviews": OUT_DIR / "terminal_boundary_reviews.json",
}

EXPECTED_PATCH_SOURCE_IDS = {
    "prod-053c-callback-request",
    "prod-053c-existing-provider-gap",
    "prod-053c-price-objection",
    "prod-053c-procurement-review",
    "prod-053c-product-detail-lookup",
    "prod-053c-unknown-runtime-signal",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "response_text_behavior_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "llm_judging_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "german_exact_phrase_promotion_allowed",
    "german_naturalness_claimed",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_source_files() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")

    source = read_json(SOURCE_FILES["source_result"])
    source_summary = source["summary"]
    assert_condition(source["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source)
    assert_condition(source["validation"]["passed"] is True, source)
    assert_condition(source_summary["source_blocking_finding_count"] == 6, source_summary)
    assert_condition(source_summary["post_patch_blocking_finding_count"] == 0, source_summary)
    assert_condition(source_summary["all_patch_cases_passed"] is True, source_summary)
    assert_condition(set(source_summary["source_blocking_case_ids"]) == EXPECTED_PATCH_SOURCE_IDS, source_summary)

    previous = read_json(SOURCE_FILES["previous_stress_result"])
    previous_summary = previous["summary"]
    assert_condition(previous["checkpoint_id"] == PREVIOUS_STRESS_CHECKPOINT_ID, previous)
    assert_condition(previous["validation"]["passed"] is True, previous)
    assert_condition(previous["validation"]["stress_gate_passed"] is False, previous)
    assert_condition(previous_summary["source_promoted_response_count"] == 26, previous_summary)
    assert_condition(previous_summary["blocking_finding_count"] == 6, previous_summary)


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    cases = payload["cases"]
    previous_cases = read_json(SOURCE_FILES["previous_stress_cases"])["cases"]
    expected_source_ids = {case["source_case_id"] for case in previous_cases}
    source_ids = {case["source_case_id"] for case in cases}

    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["previous_stress_checkpoint_id"] == PREVIOUS_STRESS_CHECKPOINT_ID, payload)
    assert_condition(len(cases) == 26, cases)
    assert_condition(source_ids == expected_source_ids, {"missing": sorted(expected_source_ids - source_ids)})
    assert_condition(sum(1 for case in cases if case["next_turn_mode"] == "runtime_second_turn") == 10, cases)
    assert_condition(sum(1 for case in cases if case["next_turn_mode"] == "callback_scheduling_flow") == 1, cases)
    assert_condition(sum(1 for case in cases if case["next_turn_mode"] == "terminal_boundary") == 15, cases)

    callback = next(case for case in cases if case["source_case_id"] == "prod-053c-callback-request")
    assert_condition(callback["next_turn_mode"] == "callback_scheduling_flow", callback)
    assert_condition(callback["initial_customer_input"]["input_type"] == "speech", callback)
    assert_condition(callback["follow_up_customer_input"]["stage"] == "scheduling", callback)

    for case in cases:
        assert_condition(case["language"] == "en", case)
        if case["next_turn_mode"] == "runtime_second_turn":
            assert_condition(case["follow_up_customer_input"]["input_type"] == "speech", case)
            assert_condition(case["expected_second_turn"]["sales_difficulty"], case)
            assert_condition(case["expected_second_turn"]["next_action"], case)
            assert_condition(case["expected_second_turn"]["call_control"], case)
        if case["next_turn_mode"] == "terminal_boundary":
            assert_condition(case["terminal_boundary"]["no_second_agent_turn_expected"] is True, case)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    runtime_reviews = read_json(GENERATED_FILES["runtime_regression_reviews"])["items"]
    callback_reviews = read_json(GENERATED_FILES["callback_scheduling_reviews"])["items"]
    terminal_reviews = read_json(GENERATED_FILES["terminal_boundary_reviews"])["items"]
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["previous_stress_checkpoint_id"] == PREVIOUS_STRESS_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["regression_gate_passed"] is True, result)
    assert_condition(summary["source_promoted_response_count"] == 26, summary)
    assert_condition(summary["runtime_second_turn_case_count"] == 10, summary)
    assert_condition(summary["callback_scheduling_case_count"] == 1, summary)
    assert_condition(summary["terminal_boundary_case_count"] == 15, summary)
    assert_condition(summary["runtime_second_turn_failure_count"] == 0, summary)
    assert_condition(summary["callback_scheduling_failure_count"] == 0, summary)
    assert_condition(summary["terminal_boundary_failure_count"] == 0, summary)
    assert_condition(summary["blocking_finding_count"] == 0, summary)
    assert_condition(summary["blocking_case_ids"] == [], summary)
    assert_condition(summary["regression_gate_passed"] is True, summary)
    assert_condition(summary["runtime_promotion_allowed"] is False, summary)
    assert_condition(summary["permanent_regression_guard_recommended"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(len(runtime_reviews) == 10, runtime_reviews)
    assert_condition(len(callback_reviews) == 1, callback_reviews)
    assert_condition(len(terminal_reviews) == 15, terminal_reviews)
    for item in runtime_reviews:
        assert_condition(item["regression_gates_passed"] is True, item)
        assert_condition(item["issue_codes"] == [], item)
    for item in terminal_reviews:
        assert_condition(item["terminal_boundary_passed"] is True, item)
        assert_condition(item["issue_codes"] == [], item)
    callback = callback_reviews[0]
    assert_condition(callback["source_case_id"] == "prod-053c-callback-request", callback)
    assert_condition(callback["first_turn"]["call_control"] == "continue-call", callback)
    assert_condition(callback["first_turn"]["next_action"] == "offer-scheduling", callback)
    assert_condition(callback["follow_up_turn"]["sales_difficulty"] == "scheduling-confirmation", callback)
    assert_condition(callback["follow_up_turn"]["call_control"] == "schedule-and-end", callback)
    assert_condition(callback["callback_flow_passed"] is True, callback)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}".lower()
    for marker in [
        "prod-056",
        "prod-055",
        "prod-054",
        "source promoted responses: `26`",
        "runtime second-turn cases: `10`",
        "callback scheduling cases: `1`",
        "terminal boundary cases: `15`",
        "blocking finding count: `0`",
        "regression gate passed: `true`",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "production runtime promotion allowed: `false`",
        "no provider",
        "no llm",
        "no private data",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_source_files()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
