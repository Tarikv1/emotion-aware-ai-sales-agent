#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-070-english-coverage-knowledge-policy-probe"
SOURCE_CHECKPOINT_ID = "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail"
NEXT_CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-070-english-coverage-knowledge-policy-probe.json"

EXPECTED_RUNTIME_GAP_CASES = {
    "prod-070-eligible-reimbursement",
    "prod-070-plan-covers-this",
    "prod-070-policy-reimbursed",
}

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_070_english_coverage_knowledge_policy_probe.py",
    "runner": ROOT / "scripts" / "run_prod_070_english_coverage_knowledge_policy_probe.py",
    "validator": ROOT / "scripts" / "validate_prod_070_english_coverage_knowledge_policy_probe.py",
    "source_validator": ROOT / "scripts" / "validate_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py",
    "doc": ROOT / "docs" / "product" / "PROD_070_ENGLISH_COVERAGE_KNOWLEDGE_POLICY_PROBE.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_selection": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "remaining_gate_selection.json",
    "source_options": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "remaining_gate_options.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "policy_decision": OUT_DIR / "policy_decision.json",
    "policy_probe_reviews": OUT_DIR / "policy_probe_reviews.json",
    "runtime_probe_reviews": OUT_DIR / "runtime_probe_reviews.json",
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


def validate_source_files() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    source = read_json(SOURCE_FILES["source_result"])
    selection = read_json(SOURCE_FILES["source_selection"])
    options = read_json(SOURCE_FILES["source_options"])
    summary = source["summary"]

    assert_condition(source["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source)
    assert_condition(source["validation"]["passed"] is True, source)
    assert_condition(summary["selected_gate_id"] == "coverage_knowledge_policy_behavior", summary)
    assert_condition(summary["recommended_next_checkpoint"] == CHECKPOINT_ID, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(selection["selected_gate"]["gate_id"] == "coverage_knowledge_policy_behavior", selection)
    assert_condition(selection["selected_gate"]["coverage_advice_allowed"] is False, selection)
    assert_condition(selection["selected_gate"]["knowledge_fact_claims_allowed"] is False, selection)
    assert_condition(options["selected_next_gate_id"] == "coverage_knowledge_policy_behavior", options)


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
    review_html = OUT_DIR / "prod_070_review.html"
    assert_condition(not review_html.exists(), "PROD-070 must not create review HTML unless human review is required")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "synthetic_english_coverage_knowledge_policy_probe_only", payload)
    assert_condition(payload["selected_gate_id"] == "coverage_knowledge_policy_behavior", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["not_a_runtime_patch"] is True, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(len(payload["policy_probe_cases"]) == 6, payload)
    assert_condition(len(payload["runtime_probe_cases"]) == 7, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    decision = read_json(GENERATED_FILES["policy_decision"])
    policy_reviews = read_json(GENERATED_FILES["policy_probe_reviews"])
    runtime_reviews = read_json(GENERATED_FILES["runtime_probe_reviews"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["policy_probe_passed"] is True, result)
    assert_condition(result["validation"]["runtime_gap_detection_passed"] is True, result)

    assert_condition(summary["policy_probe_only"] is True, summary)
    assert_condition(summary["selected_gate_id"] == "coverage_knowledge_policy_behavior", summary)
    assert_condition(summary["coverage_advice_allowed"] is False, summary)
    assert_condition(summary["coverage_fact_claims_allowed"] is False, summary)
    assert_condition(summary["eligibility_claims_allowed"] is False, summary)
    assert_condition(summary["reimbursement_claims_allowed"] is False, summary)
    assert_condition(summary["escalation_required_for_specific_coverage_questions"] is True, summary)
    assert_condition(summary["policy_probe_case_count"] == 6, summary)
    assert_condition(summary["passed_policy_probe_count"] == 6, summary)
    assert_condition(summary["failed_policy_probe_count"] == 0, summary)
    assert_condition(summary["runtime_probe_case_count"] == 7, summary)
    assert_condition(summary["runtime_gap_count"] == len(EXPECTED_RUNTIME_GAP_CASES), summary)
    assert_condition(set(summary["runtime_gap_case_ids"]) == EXPECTED_RUNTIME_GAP_CASES, summary)
    assert_condition(summary["current_runtime_gap_detected"] is True, summary)
    assert_condition(summary["runtime_patch_allowed"] is False, summary)
    assert_condition(summary["runtime_patch_recommended_next"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(decision["decision"] == "coverage_policy_probe_passed_recommend_narrow_runtime_patch", decision)
    assert_condition(decision["runtime_patch_allowed_in_prod_070"] is False, decision)
    assert_condition(decision["runtime_patch_recommended_next"] is True, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(decision["requires_human_review_before_next_checkpoint"] is False, decision)

    for item in policy_reviews["items"]:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["issue_codes"] == [], item)
        gates = item["gates"]
        for key in [
            "refuses_coverage_advice",
            "routes_to_qualified_reviewer",
            "no_coverage_fact_claim",
            "no_eligibility_claim",
            "no_reimbursement_claim",
            "no_price_payment_or_contract",
            "english_only",
        ]:
            assert_condition(gates[key] is True, item)

    gap_items = [item for item in runtime_reviews["items"] if item["runtime_gap"]]
    assert_condition({item["case_id"] for item in gap_items} == EXPECTED_RUNTIME_GAP_CASES, runtime_reviews)
    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
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
        "prod-070",
        "english coverage knowledge-policy probe",
        "synthetic english coverage knowledge-policy probe only",
        "coverage_knowledge_policy_behavior",
        "i should not give coverage advice",
        "approved qualified reviewer path",
        "eligible",
        "reimbursement",
        "plan covers",
        "current runtime gap detected",
        "not a runtime patch",
        "no human review required",
        "review html created: `false`",
        "prod-071-english-coverage-knowledge-runtime-patch",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "classifier behavior changed: `false`",
        "retrieval enabled: `false`",
        "production runtime promotion allowed: `false`",
        "provider",
        "private data",
        "voice playback",
        "german",
        "payment",
        "contract",
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
