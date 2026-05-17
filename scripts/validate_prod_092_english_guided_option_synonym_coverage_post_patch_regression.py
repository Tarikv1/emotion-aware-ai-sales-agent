#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-092-english-guided-option-synonym-coverage-post-patch-regression"
SOURCE_CHECKPOINT_ID = "PROD-091-english-guided-option-synonym-coverage-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-092-english-guided-option-synonym-coverage-post-patch-regression.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_092_english_guided_option_synonym_coverage_post_patch_regression.py",
    "runner": ROOT / "scripts" / "run_prod_092_english_guided_option_synonym_coverage_post_patch_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_092_english_guided_option_synonym_coverage_post_patch_regression.py",
    "source_validator": ROOT / "scripts" / "validate_prod_091_english_guided_option_synonym_coverage_runtime_patch.py",
    "english_guard": ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py",
    "doc": ROOT / "docs" / "product" / "PROD_092_ENGLISH_GUIDED_OPTION_SYNONYM_COVERAGE_POST_PATCH_REGRESSION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_positive_cases": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "positive_runtime_cases.json",
    "source_control_cases": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "control_runtime_cases.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "synonym_regression_cases": OUT_DIR / "synonym_regression_cases.json",
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
    positives = read_json(SOURCE_FILES["source_positive_cases"])
    controls = read_json(SOURCE_FILES["source_control_cases"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["runtime_patch_applied"] is True, result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(positives["failure_count"] == 0, positives)
    assert_condition(controls["failure_count"] == 0, controls)


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
    assert_condition(payload["scope"] == "english_guided_option_synonym_coverage_post_patch_regression", payload)
    assert_condition(payload["post_patch_regression_only"] is True, payload)
    assert_condition(payload["runtime_patch_allowed_inside_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    synonym = read_json(GENERATED_FILES["synonym_regression_cases"])
    adjacent = read_json(GENERATED_FILES["adjacent_control_cases"])
    guard = read_json(GENERATED_FILES["stable_english_guard_summary"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["post_patch_regression_only"] is True, summary)
    assert_condition(summary["synonym_positive_failures"] == 0, summary)
    assert_condition(summary["adjacent_control_failures"] == 0, summary)
    assert_condition(summary["stable_english_guard_passed"] is True, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(synonym["failure_count"] == 0, synonym)
    assert_condition(synonym["case_count"] >= 4, synonym)
    assert_condition(adjacent["failure_count"] == 0, adjacent)
    assert_condition(adjacent["case_count"] >= 12, adjacent)
    assert_condition(guard["passed"] is True, guard)
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
        "prod-092",
        "english guided option synonym coverage post-patch regression",
        "synonym positive failures: `0`",
        "adjacent control failures: `0`",
        "stable english guard passed: `true`",
        "review html created: `false`",
        "prod-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms",
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
