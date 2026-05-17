#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option"
SOURCE_CHECKPOINT_ID = "PROD-088-english-guided-option-selection-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-090-english-guided-option-synonym-coverage-narrow-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-089-english-customer-move-remaining-slice-selection-after-guided-option.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py",
    "runner": ROOT / "scripts" / "run_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py",
    "validator": ROOT / "scripts" / "validate_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py",
    "source_validator": ROOT / "scripts" / "validate_prod_088_english_guided_option_selection_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_089_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION_AFTER_GUIDED_OPTION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_guided_cases": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "guided_option_regression_cases.json",
    "source_adjacent_controls": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "adjacent_control_cases.json",
    "prod_081_inventory": ROOT / "research" / "experiments" / "generated" / "PROD-081-english-unknown-runtime-signal-subtype-inventory" / "unknown_runtime_signal_subtype_inventory.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "post_guided_option_probe_results": OUT_DIR / "post_guided_option_probe_results.json",
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
    guided = read_json(SOURCE_FILES["source_guided_cases"])
    adjacent = read_json(SOURCE_FILES["source_adjacent_controls"])
    inventory = read_json(SOURCE_FILES["prod_081_inventory"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(guided["failure_count"] == 0, guided)
    assert_condition(adjacent["failure_count"] == 0, adjacent)
    subtype_ids = {item["subtype_id"] for item in inventory["subtypes"]}
    assert_condition({"guided_option_selection_candidate", "plan_option_difference", "recommendation_request"} <= subtype_ids, subtype_ids)


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
    assert_condition(payload["scope"] == "english_customer_move_remaining_slice_selection_after_guided_option", payload)
    assert_condition(payload["selection_only"] is True, payload)
    assert_condition(payload["post_guided_option_reinventory"] is True, payload)
    assert_condition(payload["selected_next_slice"] == "guided_option_synonym_coverage", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(payload["recommended_next_checkpoint_requires_human_review"] is False, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    probes = read_json(GENERATED_FILES["post_guided_option_probe_results"])
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
    assert_condition(summary["post_guided_option_reinventory"] is True, summary)
    assert_condition(summary["guided_option_patch_closed_for_approved_cases"] is True, summary)
    assert_condition(summary["old_unknown_case_count"] >= 10, summary)
    assert_condition(summary["old_unknown_cases_now_guided_option_count"] >= 5, summary)
    assert_condition(summary["remaining_unknown_case_count"] >= 4, summary)
    assert_condition(summary["selected_next_slice"] == "guided_option_synonym_coverage", summary)
    assert_condition(summary["selected_gap_count"] == 2, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(summary["recommendation_roleplay_boundary_deferred"] is True, summary)
    assert_condition(summary["process_clarity_deferred"] is True, summary)
    assert_condition(summary["generic_confusion_kept_unknown"] is True, summary)

    assert_condition(probes["case_count"] >= 10, probes)
    assert_condition(probes["currently_guided_option_count"] >= 5, probes)
    assert_condition(probes["remaining_unknown_count"] >= 4, probes)
    selected_ids = {item["case_id"] for item in probes["selected_gaps"]}
    assert_condition(selected_ids == {"prod-081-guided-option-02", "prod-081-plan-difference-02"}, selected_ids)
    assert_condition(all(item["observed_sales_difficulty"] == "unknown-runtime-signal" for item in probes["selected_gaps"]), probes)

    assert_condition(selection["decision"] == "select_guided_option_synonym_coverage_probe_next", selection)
    assert_condition(selection["selected_next_slice"] == "guided_option_synonym_coverage", selection)
    assert_condition(selection["uses_existing_review_guardrails"] is True, selection)
    assert_condition(selection["requires_human_review_before_probe"] is False, selection)
    assert_condition(selection["runtime_patch_allowed"] is False, selection)
    assert_condition(selection["classifier_change_allowed"] is False, selection)
    assert_condition(selection["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, selection)
    assert_condition(selection["recommended_next_checkpoint_requires_human_review"] is False, selection)

    assert_condition(controls["failed_control_count"] == 0, controls)
    assert_condition(controls["control_count"] >= 8, controls)
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
        "prod-089",
        "english customer-move remaining slice selection after guided option",
        "guided_option_synonym_coverage",
        "old unknown cases now guided option: `5`",
        "selected gap count: `2`",
        "requires human review before next checkpoint: `false`",
        "recommended next checkpoint requires human review: `false`",
        "review html created: `false`",
        "prod-090-english-guided-option-synonym-coverage-narrow-probe",
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
