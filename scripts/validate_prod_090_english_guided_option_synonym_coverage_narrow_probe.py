#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-090-english-guided-option-synonym-coverage-narrow-probe"
SOURCE_CHECKPOINT_ID = "PROD-089-english-customer-move-remaining-slice-selection-after-guided-option"
NEXT_CHECKPOINT_ID = "PROD-091-english-guided-option-synonym-coverage-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-090-english-guided-option-synonym-coverage-narrow-probe.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_090_english_guided_option_synonym_coverage_narrow_probe.py",
    "runner": ROOT / "scripts" / "run_prod_090_english_guided_option_synonym_coverage_narrow_probe.py",
    "validator": ROOT / "scripts" / "validate_prod_090_english_guided_option_synonym_coverage_narrow_probe.py",
    "source_validator": ROOT / "scripts" / "validate_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py",
    "doc": ROOT / "docs" / "product" / "PROD_090_ENGLISH_GUIDED_OPTION_SYNONYM_COVERAGE_NARROW_PROBE.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_selection": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "remaining_subtype_selection.json",
    "source_probe_results": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "post_guided_option_probe_results.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "candidate_policy_constraints": OUT_DIR / "candidate_policy_constraints.json",
    "synonym_probe_case_matrix": OUT_DIR / "synonym_probe_case_matrix.json",
    "policy_probe_result": OUT_DIR / "policy_probe_result.json",
    "current_runtime_gap_analysis": OUT_DIR / "current_runtime_gap_analysis.json",
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
    selection = read_json(SOURCE_FILES["source_selection"])
    probes = read_json(SOURCE_FILES["source_probe_results"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["selected_next_slice"] == "guided_option_synonym_coverage", result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(selection["decision"] == "select_guided_option_synonym_coverage_probe_next", selection)
    assert_condition(selection["recommended_next_checkpoint"] == CHECKPOINT_ID, selection)
    assert_condition({item["case_id"] for item in probes["selected_gaps"]} == {"prod-081-guided-option-02", "prod-081-plan-difference-02"}, probes)


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
    assert_condition(payload["scope"] == "english_guided_option_synonym_coverage_narrow_policy_probe", payload)
    assert_condition(payload["policy_probe_only"] is True, payload)
    assert_condition(payload["selected_source_slice"] == "guided_option_synonym_coverage", payload)
    assert_condition(payload["runtime_patch_allowed_inside_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(payload["recommended_next_checkpoint_requires_human_review"] is False, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    constraints = read_json(GENERATED_FILES["candidate_policy_constraints"])
    matrix = read_json(GENERATED_FILES["synonym_probe_case_matrix"])
    probe = read_json(GENERATED_FILES["policy_probe_result"])
    gaps = read_json(GENERATED_FILES["current_runtime_gap_analysis"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["policy_probe_passed"] is True, result)
    assert_condition(summary["policy_probe_only"] is True, summary)
    assert_condition(summary["policy_probe_passed"] is True, summary)
    assert_condition(summary["selected_gap_count"] == 2, summary)
    assert_condition(summary["positive_case_count"] >= 4, summary)
    assert_condition(summary["control_case_count"] >= 8, summary)
    assert_condition(summary["failed_policy_case_count"] == 0, summary)
    assert_condition(summary["current_runtime_gap_count"] == 2, summary)
    assert_condition(summary["uses_existing_review_guardrails"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(constraints["selected_source_slice"] == "guided_option_synonym_coverage", constraints)
    assert_condition(constraints["plan_feature_matrix_required"] is True, constraints)
    assert_condition(constraints["uses_existing_review_guardrails"] is True, constraints)
    assert_condition(constraints["advice_roleplay_boundary_deferred"] is True, constraints)
    assert_condition(constraints["process_clarity_deferred"] is True, constraints)
    assert_condition(constraints["no_new_payment_path"] is True, constraints)
    assert_condition(constraints["runtime_patch_allowed_inside_checkpoint"] is False, constraints)
    assert_condition(constraints["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, constraints)

    assert_condition(matrix["positive_case_count"] >= 4, matrix)
    assert_condition(matrix["control_case_count"] >= 8, matrix)
    assert_condition(probe["failed_policy_case_count"] == 0, probe)
    assert_condition(probe["positive_failure_count"] == 0, probe)
    assert_condition(probe["control_failure_count"] == 0, probe)
    assert_condition(gaps["runtime_gap_count"] == 2, gaps)
    assert_condition({item["case_id"] for item in gaps["runtime_gaps"]} == {"prod-081-guided-option-02", "prod-081-plan-difference-02"}, gaps)
    assert_condition(all(item["observed_sales_difficulty"] == "unknown-runtime-signal" for item in gaps["runtime_gaps"]), gaps)
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
        "prod-090",
        "english guided option synonym coverage narrow probe",
        "guided_option_synonym_coverage",
        "policy probe passed: `true`",
        "selected gap count: `2`",
        "current runtime gap count: `2`",
        "requires human review before next checkpoint: `false`",
        "recommended next checkpoint requires human review: `false`",
        "review html created: `false`",
        "prod-091-english-guided-option-synonym-coverage-runtime-patch",
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
