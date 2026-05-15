#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-055-english-multi-turn-runtime-patch"
SOURCE_CHECKPOINT_ID = "PROD-054-english-multi-turn-naturalness-stress-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-055-english-multi-turn-runtime-patch.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_055_english_multi_turn_runtime_patch.py",
    "runner": ROOT / "scripts" / "run_prod_055_english_multi_turn_runtime_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_055_english_multi_turn_runtime_patch.py",
    "doc": ROOT / "docs" / "product" / "PROD_055_ENGLISH_MULTI_TURN_RUNTIME_PATCH.md",
    "runtime": ROOT / "runtime" / "core" / "realtime_turns.py",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT
    / "research"
    / "experiments"
    / "generated"
    / SOURCE_CHECKPOINT_ID
    / "result.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "source_blocking_findings": OUT_DIR / "source_blocking_findings.json",
    "patched_runtime_reviews": OUT_DIR / "patched_runtime_reviews.json",
}

EXPECTED_SOURCE_BLOCKING_IDS = {
    "prod-053c-callback-request",
    "prod-053c-existing-provider-gap",
    "prod-053c-price-objection",
    "prod-053c-procurement-review",
    "prod-053c-product-detail-lookup",
    "prod-053c-unknown-runtime-signal",
}

BOUNDARY_FALSE_FIELDS = [
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
    summary = source["summary"]
    assert_condition(source["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source)
    assert_condition(source["validation"]["passed"] is True, source)
    assert_condition(source["validation"]["stress_gate_passed"] is False, source)
    assert_condition(set(summary["blocking_case_ids"]) == EXPECTED_SOURCE_BLOCKING_IDS, summary)


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
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(len(cases) == 6, cases)
    assert_condition({case["source_case_id"] for case in cases} == EXPECTED_SOURCE_BLOCKING_IDS, cases)
    assert_condition(sum(1 for case in cases if case["patch_mode"] == "current_first_turn") == 1, cases)
    assert_condition(sum(1 for case in cases if case["patch_mode"] == "runtime_second_turn") == 5, cases)
    for case in cases:
        assert_condition(case["language"] == "en", case)
        assert_condition(case["customer_input"]["input_type"] == "speech", case)
        expected = case["expected_runtime_after_patch"]
        assert_condition(expected["sales_difficulty"], case)
        assert_condition(expected["next_action"], case)
        assert_condition(expected["call_control"], case)
        assert_condition(expected["response_must_include_any"], case)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    source_findings = read_json(GENERATED_FILES["source_blocking_findings"])["items"]
    reviews = read_json(GENERATED_FILES["patched_runtime_reviews"])["items"]
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["source_blocking_finding_count"] == 6, summary)
    assert_condition(summary["patched_runtime_review_count"] == 6, summary)
    assert_condition(summary["post_patch_blocking_finding_count"] == 0, summary)
    assert_condition(summary["all_patch_cases_passed"] is True, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    assert_condition(summary["runtime_promotion_allowed"] is False, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    assert_condition({item["source_case_id"] for item in source_findings} == EXPECTED_SOURCE_BLOCKING_IDS, source_findings)
    assert_condition({item["source_case_id"] for item in reviews} == EXPECTED_SOURCE_BLOCKING_IDS, reviews)
    for item in reviews:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["issue_codes"] == [], item)
    callback = next(item for item in reviews if item["source_case_id"] == "prod-053c-callback-request")
    assert_condition(callback["runtime_decision"]["call_control"] == "continue-call", callback)
    assert_condition(callback["runtime_decision"]["next_action"] == "offer-scheduling", callback)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}".lower()
    for marker in [
        "prod-055",
        "prod-054",
        "six",
        "runtime behavior changed: `true`",
        "response text behavior changed: `true`",
        "post-patch blocking findings: `0`",
        "no provider",
        "no llm",
        "no private data",
        "production runtime promotion allowed: `false`",
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
