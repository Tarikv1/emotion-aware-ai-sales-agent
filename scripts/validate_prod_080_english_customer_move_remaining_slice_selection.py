#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-080-english-customer-move-remaining-slice-selection"
SOURCE_CHECKPOINT_ID = "PROD-079-english-provider-comparison-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-081-english-unknown-runtime-signal-subtype-inventory"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-080-english-customer-move-remaining-slice-selection.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_080_english_customer_move_remaining_slice_selection.py",
    "runner": ROOT / "scripts" / "run_prod_080_english_customer_move_remaining_slice_selection.py",
    "validator": ROOT / "scripts" / "validate_prod_080_english_customer_move_remaining_slice_selection.py",
    "source_validator": ROOT / "scripts" / "validate_prod_079_english_provider_comparison_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_080_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_reviews": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "post_patch_regression_reviews.json",
    "prod_073_slice_plan": ROOT / "research" / "experiments" / "generated" / "PROD-073-english-customer-move-classification-gate-decision" / "classifier_slice_plan.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "remaining_slice_selection": OUT_DIR / "remaining_slice_selection.json",
    "current_classifier_reachability_snapshot": OUT_DIR / "current_classifier_reachability_snapshot.json",
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
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])


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
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_customer_move_remaining_slice_selection_only", payload)
    assert_condition(payload["selection_only"] is True, payload)
    assert_condition(payload["selected_next_slice"] == "unknown_runtime_signal_subtypes", payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    selection = read_json(GENERATED_FILES["remaining_slice_selection"])
    snapshot = read_json(GENERATED_FILES["current_classifier_reachability_snapshot"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["selection_only"] is True, summary)
    assert_condition(summary["provider_comparison_slice_closed"] is True, summary)
    assert_condition(summary["unreachable_existing_response_types_remaining"] is False, summary)
    assert_condition(summary["selected_next_slice"] == "unknown_runtime_signal_subtypes", summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(selection["decision"] == "select_unknown_runtime_signal_subtypes_inventory_next", selection)
    assert_condition(selection["runtime_patch_allowed"] is False, selection)
    assert_condition(selection["protected_boundary_controls_required"] is True, selection)
    assert_condition(snapshot["unreachable_localized_response_types"] == [], snapshot)
    assert_condition("provider-comparison" in snapshot["reachable_sales_difficulties"], snapshot)
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
        "prod-080",
        "english customer-move remaining slice selection",
        "unknown_runtime_signal_subtypes",
        "unreachable existing response types remaining: `false`",
        "provider-comparison slice closed",
        "protected boundary controls required",
        "review html created: `false`",
        "prod-081-english-unknown-runtime-signal-subtype-inventory",
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
