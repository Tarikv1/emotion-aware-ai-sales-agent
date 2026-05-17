#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-101-english-recommendation-roleplay-post-patch-regression"
SOURCE_CHECKPOINT_ID = "PROD-100-english-recommendation-roleplay-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-102-english-customer-move-remaining-slice-selection-after-recommendation-roleplay"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-101-english-recommendation-roleplay-post-patch-regression.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_101_english_recommendation_roleplay_post_patch_regression.py",
    "runner": ROOT / "scripts" / "run_prod_101_english_recommendation_roleplay_post_patch_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_101_english_recommendation_roleplay_post_patch_regression.py",
    "source_validator": ROOT / "scripts" / "validate_prod_100_english_recommendation_roleplay_runtime_patch.py",
    "stable_english_guard": ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py",
    "doc": ROOT / "docs" / "product" / "PROD_101_ENGLISH_RECOMMENDATION_ROLEPLAY_POST_PATCH_REGRESSION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_patch_summary": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "runtime_patch_summary.json",
    "source_positive_runtime_cases": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "positive_runtime_cases.json",
    "source_control_runtime_cases": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "control_runtime_cases.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "recommendation_roleplay_regression_cases": OUT_DIR / "recommendation_roleplay_regression_cases.json",
    "adjacent_control_cases": OUT_DIR / "adjacent_control_cases.json",
    "stable_english_guard_summary": OUT_DIR / "stable_english_guard_summary.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "response_text_behavior_changed",
    "classifier_behavior_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "llm_judging_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "real_customer_use_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "german_exact_phrase_promotion_allowed",
    "german_naturalness_claimed",
    "legal_compliance_claimed",
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


def validate_sources() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    patch = read_json(SOURCE_FILES["source_patch_summary"])
    positives = read_json(SOURCE_FILES["source_positive_runtime_cases"])
    controls = read_json(SOURCE_FILES["source_control_runtime_cases"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(result["summary"]["selected_gap_fixed_count"] == 7, result["summary"])
    assert_condition(result["summary"]["positive_case_failures"] == 0, result["summary"])
    assert_condition(result["summary"]["control_case_failures"] == 0, result["summary"])
    assert_condition(result["summary"]["requires_customer_facts_for_recommendation"] is True, result["summary"])
    assert_condition(result["summary"]["requires_agency_preservation"] is True, result["summary"])
    assert_condition(result["summary"]["no_agent_decides_for_customer"] is True, result["summary"])
    assert_condition(result["summary"]["no_value_guarantee"] is True, result["summary"])
    assert_condition(patch["runtime_patch_applied"] is True, patch)
    assert_condition(len(patch["selected_gap_case_ids"]) == 7, patch)
    assert_condition(patch["new_sales_difficulty"] == "recommendation-roleplay-boundary", patch)
    assert_condition(patch["requires_customer_facts_for_recommendation"] is True, patch)
    assert_condition(patch["requires_agency_preservation"] is True, patch)
    assert_condition(patch["no_agent_decides_for_customer"] is True, patch)
    assert_condition(patch["no_value_guarantee"] is True, patch)
    assert_condition(positives["failure_count"] == 0, positives)
    assert_condition(positives["case_count"] == 7, positives)
    assert_condition(controls["failure_count"] == 0, controls)
    assert_condition(controls["case_count"] >= 10, controls)


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_recommendation_roleplay_post_patch_regression", payload)
    assert_condition(payload["post_patch_regression_only"] is True, payload)
    assert_condition(payload["runtime_patch_allowed_inside_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(payload["do_not_open_next_checkpoint_in_this_run"] is True, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    recommendation = read_json(GENERATED_FILES["recommendation_roleplay_regression_cases"])
    controls = read_json(GENERATED_FILES["adjacent_control_cases"])
    stable_guard = read_json(GENERATED_FILES["stable_english_guard_summary"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["post_patch_regression_completed"] is True, result)
    assert_condition(summary["post_patch_regression_only"] is True, summary)
    assert_condition(summary["source_validator_passed"] is True, summary)
    assert_condition(summary["recommendation_roleplay_positive_failures"] == 0, summary)
    assert_condition(summary["adjacent_control_failures"] == 0, summary)
    assert_condition(summary["stable_english_guard_passed"] is True, summary)
    assert_condition(summary["requires_customer_facts_for_recommendation"] is True, summary)
    assert_condition(summary["requires_agency_preservation"] is True, summary)
    assert_condition(summary["no_agent_decides_for_customer"] is True, summary)
    assert_condition(summary["no_value_guarantee"] is True, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(summary["do_not_open_next_checkpoint_in_this_run"] is True, summary)
    assert_condition(recommendation["failure_count"] == 0, recommendation)
    assert_condition(recommendation["case_count"] == 7, recommendation)
    assert_condition(controls["failure_count"] == 0, controls)
    assert_condition(controls["case_count"] >= 12, controls)
    assert_condition(stable_guard["passed"] is True, stable_guard)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    commands_text = REQUIRED_FILES["commands"].read_text(encoding="utf-8")
    index_text = REQUIRED_FILES["checkpoint_index"].read_text(encoding="utf-8")
    roadmap_text = REQUIRED_FILES["roadmap"].read_text(encoding="utf-8")
    methodology_text = REQUIRED_FILES["methodology_log"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}\n{commands_text}\n{index_text}\n{roadmap_text}\n{methodology_text}".lower()
    for marker in [
        "prod-101",
        "english recommendation roleplay post-patch regression",
        "recommendation roleplay positive failures: `0`",
        "adjacent control failures: `0`",
        "stable english guard passed: `true`",
        "requires customer facts for recommendation: `true`",
        "requires agency preservation: `true`",
        "no agent decides for customer: `true`",
        "no value guarantee: `true`",
        "review html created: `false`",
        "do not open the next checkpoint in this run: `true`",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "classifier behavior changed: `false`",
        "retrieval enabled: `false`",
        "production runtime promotion allowed: `false`",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_sources()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
