#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms"
SOURCE_CHECKPOINT_ID = "PROD-092-english-guided-option-synonym-coverage-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-094-english-next-step-process-clarity-narrow-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-093-english-customer-move-remaining-slice-selection-after-guided-option-synonyms.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_093_english_customer_move_remaining_slice_selection_after_guided_option_synonyms.py",
    "runner": ROOT / "scripts" / "run_prod_093_english_customer_move_remaining_slice_selection_after_guided_option_synonyms.py",
    "validator": ROOT / "scripts" / "validate_prod_093_english_customer_move_remaining_slice_selection_after_guided_option_synonyms.py",
    "source_validator": ROOT / "scripts" / "validate_prod_092_english_guided_option_synonym_coverage_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_093_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION_AFTER_GUIDED_OPTION_SYNONYMS.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_synonym_cases": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "synonym_regression_cases.json",
    "source_adjacent_controls": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "adjacent_control_cases.json",
    "source_stable_guard": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "stable_english_guard_summary.json",
    "prod_089_probe_results": ROOT / "research" / "experiments" / "generated" / "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option" / "post_guided_option_probe_results.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "remaining_subtype_inventory": OUT_DIR / "remaining_subtype_inventory.json",
    "remaining_subtype_selection": OUT_DIR / "remaining_subtype_selection.json",
    "protected_boundary_control_results": OUT_DIR / "protected_boundary_control_results.json",
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
    synonym_cases = read_json(SOURCE_FILES["source_synonym_cases"])
    adjacent_controls = read_json(SOURCE_FILES["source_adjacent_controls"])
    stable_guard = read_json(SOURCE_FILES["source_stable_guard"])
    prod_089_probe_results = read_json(SOURCE_FILES["prod_089_probe_results"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(synonym_cases["failure_count"] == 0, synonym_cases)
    assert_condition(adjacent_controls["failure_count"] == 0, adjacent_controls)
    assert_condition(stable_guard["passed"] is True, stable_guard)
    deferred_ids = {item["case_id"] for item in prod_089_probe_results["items"]}
    assert_condition(
        {"prod-081-recommendation-02", "prod-081-next-step-01", "prod-081-unclear-interest-01"} <= deferred_ids,
        deferred_ids,
    )


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
    assert_condition(payload["scope"] == "english_customer_move_remaining_slice_selection_after_guided_option_synonyms", payload)
    assert_condition(payload["selection_only"] is True, payload)
    assert_condition(payload["selected_next_slice"] == "next_step_process_clarity", payload)
    assert_condition(payload["selected_remaining_case_id"] == "prod-081-next-step-01", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(payload["recommended_next_checkpoint_requires_human_review"] is False, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    inventory = read_json(GENERATED_FILES["remaining_subtype_inventory"])
    selection = read_json(GENERATED_FILES["remaining_subtype_selection"])
    controls = read_json(GENERATED_FILES["protected_boundary_control_results"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["selection_passed"] is True, result)
    assert_condition(summary["selection_only"] is True, summary)
    assert_condition(summary["source_validator_passed"] is True, summary)
    assert_condition(summary["source_synonym_regression_passed"] is True, summary)
    assert_condition(summary["source_adjacent_controls_passed"] is True, summary)
    assert_condition(summary["stable_english_guard_passed"] is True, summary)
    assert_condition(summary["remaining_subtype_count"] >= 3, summary)
    assert_condition(summary["selected_next_slice"] == "next_step_process_clarity", summary)
    assert_condition(summary["selected_remaining_case_id"] == "prod-081-next-step-01", summary)
    assert_condition(summary["selected_requires_human_review_before_probe"] is False, summary)
    assert_condition(summary["advice_roleplay_deferred_for_review"] is True, summary)
    assert_condition(summary["generic_confusion_kept_unknown"] is True, summary)
    assert_condition(summary["failed_protected_boundary_control_count"] == 0, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(inventory["remaining_subtype_count"] >= 3, inventory)
    subtype_ids = {item["subtype_id"] for item in inventory["remaining_subtypes"]}
    assert_condition(
        {"recommendation_roleplay_boundary", "next_step_process_clarity", "generic_decision_confusion"} <= subtype_ids,
        subtype_ids,
    )
    assert_condition(inventory["selected_subtype_id"] == "next_step_process_clarity", inventory)

    assert_condition(selection["decision"] == "select_next_step_process_clarity_probe_next", selection)
    assert_condition(selection["selected_next_slice"] == "next_step_process_clarity", selection)
    assert_condition(selection["selected_remaining_case_id"] == "prod-081-next-step-01", selection)
    assert_condition(selection["selected_requires_human_review_before_probe"] is False, selection)
    assert_condition(selection["advice_roleplay_deferred_for_review"] is True, selection)
    assert_condition(selection["generic_confusion_kept_unknown"] is True, selection)
    assert_condition(selection["runtime_patch_allowed"] is False, selection)
    assert_condition(selection["response_text_change_allowed"] is False, selection)
    assert_condition(selection["classifier_change_allowed"] is False, selection)
    assert_condition(selection["review_html_created"] is False, selection)
    assert_condition(selection["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, selection)
    assert_condition(selection["recommended_next_checkpoint_requires_human_review"] is False, selection)

    assert_condition(controls["failed_control_count"] == 0, controls)
    assert_condition(controls["control_count"] >= 6, controls)
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
        "prod-093",
        "english customer-move remaining slice selection after guided option synonyms",
        "next_step_process_clarity",
        "selected remaining case: `prod-081-next-step-01`",
        "advice roleplay deferred for review: `true`",
        "generic confusion kept unknown: `true`",
        "requires human review before next checkpoint: `false`",
        "recommended next checkpoint requires human review: `false`",
        "review html created: `false`",
        "prod-094-english-next-step-process-clarity-narrow-probe",
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
