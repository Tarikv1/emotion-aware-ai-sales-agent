#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-073-english-customer-move-classification-gate-decision"
SOURCE_CHECKPOINT_ID = "PROD-072-english-coverage-knowledge-post-patch-regression"
PRIORITY_SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
NEXT_CHECKPOINT_ID = "PROD-074-english-customer-move-classification-slice-inventory"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-073-english-customer-move-classification-gate-decision.json"
GATE_ID = "customer_move_classification_outside_selected_non_refusal_groups"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_073_english_customer_move_classification_gate_decision.py",
    "runner": ROOT / "scripts" / "run_prod_073_english_customer_move_classification_gate_decision.py",
    "validator": ROOT / "scripts" / "validate_prod_073_english_customer_move_classification_gate_decision.py",
    "source_validator": ROOT / "scripts" / "validate_prod_072_english_coverage_knowledge_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_073_ENGLISH_CUSTOMER_MOVE_CLASSIFICATION_GATE_DECISION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "post_patch_regression_decision.json",
    "priority_gate_options": ROOT / "research" / "experiments" / "generated" / PRIORITY_SOURCE_CHECKPOINT_ID / "gate_options.json",
    "prod_069_selection": ROOT / "research" / "experiments" / "generated" / "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail" / "remaining_gate_selection.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "customer_move_gate_decision": OUT_DIR / "customer_move_gate_decision.json",
    "classifier_slice_plan": OUT_DIR / "classifier_slice_plan.json",
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
    source_decision = read_json(SOURCE_FILES["source_decision"])
    priority = read_json(SOURCE_FILES["priority_gate_options"])
    prod_069 = read_json(SOURCE_FILES["prod_069_selection"])
    summary = source["summary"]

    assert_condition(source["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source)
    assert_condition(source["validation"]["passed"] is True, source)
    assert_condition(summary["failed_case_count"] == 0, summary)
    assert_condition(summary["recommended_next_checkpoint"] == CHECKPOINT_ID, summary)
    assert_condition(source_decision["decision"] == "coverage_patch_post_regression_passed", source_decision)
    assert_condition(source_decision["recommended_next_checkpoint"] == CHECKPOINT_ID, source_decision)
    assert_condition(GATE_ID in {item["gate_id"] for item in priority["ranked_gates"]}, priority)
    assert_condition(prod_069["deferred_gates"] == [GATE_ID], prod_069)


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
    review_html = OUT_DIR / "prod_073_review.html"
    assert_condition(not review_html.exists(), "PROD-073 must not create review HTML unless human review is required")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["priority_source_checkpoint_id"] == PRIORITY_SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_customer_move_classification_gate_decision_only", payload)
    assert_condition(payload["remaining_gate_id"] == GATE_ID, payload)
    assert_condition(payload["decision_type"] == "split_before_probe", payload)
    assert_condition(payload["broad_classifier_patch_allowed"] is False, payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(len(payload["split_criteria"]) >= 4, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    decision = read_json(GENERATED_FILES["customer_move_gate_decision"])
    slice_plan = read_json(GENERATED_FILES["classifier_slice_plan"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["gate_decision_passed"] is True, result)
    assert_condition(summary["decision_only"] is True, summary)
    assert_condition(summary["remaining_gate_id"] == GATE_ID, summary)
    assert_condition(summary["decision"] == "split_broad_customer_move_gate_before_probe", summary)
    assert_condition(summary["broad_classifier_patch_allowed"] is False, summary)
    assert_condition(summary["narrow_slice_inventory_required_next"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(decision["decision"] == "split_broad_customer_move_gate_before_probe", decision)
    assert_condition(decision["broad_classifier_patch_allowed"] is False, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(slice_plan["selected_next_action"] == "inventory_classifier_slices", slice_plan)
    assert_condition(slice_plan["runtime_patch_allowed"] is False, slice_plan)
    assert_condition(slice_plan["requires_human_review_before_next_checkpoint"] is False, slice_plan)
    assert_condition(len(slice_plan["candidate_slices"]) >= 4, slice_plan)
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
        "prod-073",
        "english customer-move classification gate decision",
        "customer_move_classification_outside_selected_non_refusal_groups",
        "split broad customer-move gate before probe",
        "broad classifier patch allowed: `false`",
        "narrow slice inventory required next: `true`",
        "decision only",
        "no human review required",
        "review html created: `false`",
        "prod-074-english-customer-move-classification-slice-inventory",
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
