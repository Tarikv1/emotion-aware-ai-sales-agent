#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-086-english-guided-option-selection-narrow-policy-probe"
SOURCE_CHECKPOINT_ID = "PROD-085-english-guided-option-selection-rewrite-review-import"
NEXT_CHECKPOINT_ID = "PROD-087-english-guided-option-selection-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-086-english-guided-option-selection-narrow-policy-probe.json"
PAYMENT_RESPONSE = "No payment on this call. I'll send you the link by email, and you can review the plan and register there."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_086_english_guided_option_selection_narrow_policy_probe.py",
    "runner": ROOT / "scripts" / "run_prod_086_english_guided_option_selection_narrow_policy_probe.py",
    "validator": ROOT / "scripts" / "validate_prod_086_english_guided_option_selection_narrow_policy_probe.py",
    "source_validator": ROOT / "scripts" / "validate_prod_085_english_guided_option_selection_rewrite_review_import.py",
    "doc": ROOT / "docs" / "product" / "PROD_086_ENGLISH_GUIDED_OPTION_SELECTION_NARROW_POLICY_PROBE.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "candidate_packet": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "approved_rewrite_candidate_packet.json",
    "probe_readiness": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "narrow_policy_probe_readiness.json",
    "payment_edit": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "payment_wording_edit.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "candidate_policy_constraints": OUT_DIR / "candidate_policy_constraints.json",
    "probe_case_matrix": OUT_DIR / "probe_case_matrix.json",
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
    candidates = read_json(SOURCE_FILES["candidate_packet"])
    readiness = read_json(SOURCE_FILES["probe_readiness"])
    payment = read_json(SOURCE_FILES["payment_edit"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["narrow_policy_probe_approved_after_required_edit"] is True, result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(candidates["narrow_policy_probe_candidate"] is True, candidates)
    assert_condition(candidates["runtime_candidate_promoted"] is False, candidates)
    assert_condition(len(candidates["examples"]) == 8, candidates)
    assert_condition("companyname.com" not in json.dumps(candidates).lower(), candidates)
    assert_condition(readiness["requires_plan_feature_matrix"] is True, readiness)
    assert_condition(readiness["requires_customer_facts_for_steering"] is True, readiness)
    assert_condition(readiness["requires_no_payment_on_call_default"] is True, readiness)
    assert_condition(readiness["requires_no_company_domain_in_generic_payment_wording"] is True, readiness)
    assert_condition(payment["final_candidate_response"] == PAYMENT_RESPONSE, payment)


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
    assert_condition(payload["scope"] == "english_guided_option_selection_narrow_policy_probe_only", payload)
    assert_condition(payload["policy_probe_only"] is True, payload)
    assert_condition(payload["runtime_patch_allowed_inside_checkpoint"] is False, payload)
    assert_condition(payload["requires_plan_feature_matrix"] is True, payload)
    assert_condition(payload["requires_customer_facts_for_steering"] is True, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    constraints = read_json(GENERATED_FILES["candidate_policy_constraints"])
    matrix = read_json(GENERATED_FILES["probe_case_matrix"])
    probe = read_json(GENERATED_FILES["policy_probe_result"])
    gaps = read_json(GENERATED_FILES["current_runtime_gap_analysis"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["policy_probe_only"] is True, summary)
    assert_condition(summary["policy_probe_passed"] is True, summary)
    assert_condition(summary["selected_review_item"] == "guided_option_selection_rewritten_examples", summary)
    assert_condition(summary["approved_candidate_count"] == 8, summary)
    assert_condition(summary["positive_probe_case_count"] == 8, summary)
    assert_condition(summary["control_case_count"] >= 6, summary)
    assert_condition(summary["failed_policy_case_count"] == 0, summary)
    assert_condition(summary["current_runtime_positive_gap_count"] >= 1, summary)
    assert_condition(summary["runtime_patch_allowed_inside_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(constraints["requires_plan_feature_matrix"] is True, constraints)
    assert_condition(constraints["requires_customer_facts_for_steering"] is True, constraints)
    assert_condition(constraints["requires_no_payment_on_call_default"] is True, constraints)
    assert_condition(constraints["requires_no_company_domain_in_generic_payment_wording"] is True, constraints)
    assert_condition(constraints["random_fillers_allowed"] is False, constraints)
    assert_condition("companyname.com" in constraints["forbidden_text"], constraints)
    assert_condition(matrix["positive_probe_case_count"] == 8, matrix)
    assert_condition(len(matrix["control_cases"]) >= 6, matrix)
    assert_condition(all(item["passed"] for item in probe["positive_case_results"]), probe)
    assert_condition(all(item["passed"] for item in probe["control_case_results"]), probe)
    assert_condition(probe["policy_probe_passed"] is True, probe)
    assert_condition(probe["failed_policy_case_count"] == 0, probe)
    assert_condition(PAYMENT_RESPONSE in json.dumps(probe), probe)
    assert_condition("companyname.com" not in json.dumps(probe).lower(), probe)
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
        "prod-086",
        "english guided option selection narrow policy probe",
        "policy probe passed: `true`",
        "requires plan feature matrix",
        "requires customer facts for steering",
        "no payment on this call",
        "i'll send you the link by email",
        "companyname.com",
        "random fillers allowed: `false`",
        "runtime patch allowed inside checkpoint: `false`",
        "review html created: `false`",
        "prod-087-english-guided-option-selection-runtime-patch",
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
