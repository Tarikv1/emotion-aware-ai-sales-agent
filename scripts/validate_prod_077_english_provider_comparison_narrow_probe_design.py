#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-077-english-provider-comparison-narrow-probe-design"
SOURCE_CHECKPOINT_ID = "PROD-076-english-provider-comparison-review-import"
NEXT_CHECKPOINT_ID = "PROD-078-english-provider-comparison-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-077-english-provider-comparison-narrow-probe-design.json"
EXPECTED_RESPONSE = "Fair. We can compare fit against what you use now before you decide."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_077_english_provider_comparison_narrow_probe_design.py",
    "runner": ROOT / "scripts" / "run_prod_077_english_provider_comparison_narrow_probe_design.py",
    "validator": ROOT / "scripts" / "validate_prod_077_english_provider_comparison_narrow_probe_design.py",
    "source_validator": ROOT / "scripts" / "validate_prod_076_english_provider_comparison_review_import.py",
    "doc": ROOT / "docs" / "product" / "PROD_077_ENGLISH_PROVIDER_COMPARISON_NARROW_PROBE_DESIGN.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "requirements": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "narrow_probe_requirements.json",
    "constraints": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "candidate_response_constraints.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "narrow_probe_design": OUT_DIR / "narrow_probe_design.json",
    "candidate_response_design": OUT_DIR / "candidate_response_design.json",
    "probe_case_matrix": OUT_DIR / "probe_case_matrix.json",
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
    requirements = read_json(SOURCE_FILES["requirements"])
    constraints = read_json(SOURCE_FILES["constraints"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["narrow_probe_approved"] is True, result["summary"])
    assert_condition(result["summary"]["exact_as_written_approval"] is False, result["summary"])
    assert_condition(requirements["requirements"]["comparison_target_required"] is True, requirements)
    assert_condition(requirements["requirements"]["generic_provider_or_terms_comparison_allowed"] is False, requirements)
    assert_condition(constraints["brevity_required"] is True, constraints)


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
    assert_condition(payload["scope"] == "english_provider_comparison_narrow_probe_design_only", payload)
    assert_condition(payload["probe_design_only"] is True, payload)
    assert_condition(payload["runtime_patch_allowed_inside_checkpoint"] is False, payload)
    assert_condition(payload["comparison_target_required"] is True, payload)
    assert_condition(payload["generic_provider_or_terms_comparison_allowed"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    design = read_json(GENERATED_FILES["narrow_probe_design"])
    response = read_json(GENERATED_FILES["candidate_response_design"])
    matrix = read_json(GENERATED_FILES["probe_case_matrix"])
    gaps = read_json(GENERATED_FILES["current_runtime_gap_analysis"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["probe_design_only"] is True, summary)
    assert_condition(summary["selected_review_item"] == "provider-comparison", summary)
    assert_condition(summary["comparison_target_required"] is True, summary)
    assert_condition(summary["generic_provider_or_terms_comparison_allowed"] is False, summary)
    assert_condition(summary["candidate_response"] == EXPECTED_RESPONSE, summary)
    assert_condition(summary["candidate_response_word_count"] < summary["source_response_word_count"], summary)
    assert_condition(summary["positive_probe_case_count"] >= 4, summary)
    assert_condition(summary["negative_control_case_count"] >= 5, summary)
    assert_condition(summary["protected_control_case_count"] >= 2, summary)
    assert_condition(summary["current_runtime_positive_gap_count"] >= 1, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(design["route_name"] == "provider-comparison", design)
    assert_condition("compare_or_difference_signal" in design["required_signal_groups"], design)
    assert_condition("known_comparison_target_signal" in design["required_signal_groups"], design)
    assert_condition(design["branch_order"]["insert_before"] == "existing-provider-gap", design)
    assert_condition(response["candidate_response"] == EXPECTED_RESPONSE, response)
    assert_condition(response["approved_as_exact_response_text"] is False, response)
    assert_condition(response["candidate_selected_for_probe"] is True, response)
    assert_condition(len(matrix["positive_probe_cases"]) >= 4, matrix)
    assert_condition(len(matrix["negative_control_cases"]) >= 5, matrix)
    assert_condition(len(matrix["protected_control_cases"]) >= 2, matrix)
    assert_condition(all(item["expected_sales_difficulty"] == "provider-comparison" for item in matrix["positive_probe_cases"]), matrix)
    assert_condition(all(item["expected_sales_difficulty"] != "provider-comparison" for item in matrix["negative_control_cases"]), matrix)
    assert_condition(all(item["expected_sales_difficulty"] != "provider-comparison" for item in matrix["protected_control_cases"]), matrix)
    assert_condition(gaps["current_runtime_positive_gap_count"] >= 1, gaps)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    commands_text = REQUIRED_FILES["commands"].read_text(encoding="utf-8")
    index_text = REQUIRED_FILES["checkpoint_index"].read_text(encoding="utf-8")
    roadmap_text = REQUIRED_FILES["roadmap"].read_text(encoding="utf-8")
    methodology_text = REQUIRED_FILES["methodology_log"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}\n{commands_text}\n{index_text}\n{roadmap_text}\n{methodology_text}".lower()
    for marker in [
        "prod-077",
        "english provider-comparison narrow probe design",
        "comparison target required",
        "compare_or_difference_signal",
        "known_comparison_target_signal",
        "fair. we can compare fit against what you use now before you decide.",
        "insert before `existing-provider-gap`",
        "review html created: `false`",
        "prod-078-english-provider-comparison-runtime-patch",
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
