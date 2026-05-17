#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-069-english-remaining-product-policy-gate-selection-after-voicemail"
SOURCE_CHECKPOINT_ID = "PROD-068-english-voicemail-post-patch-regression"
PRIORITY_SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
PRIOR_SELECTION_CHECKPOINT_ID = "PROD-065-english-remaining-product-policy-gate-selection"
NEXT_CHECKPOINT_ID = "PROD-070-english-coverage-knowledge-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-069-english-remaining-product-policy-gate-selection-after-voicemail.json"
SELECTED_GATE_ID = "coverage_knowledge_policy_behavior"
REMAINING_GATES = {
    "coverage_knowledge_policy_behavior",
    "customer_move_classification_outside_selected_non_refusal_groups",
}

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py",
    "runner": ROOT / "scripts" / "run_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py",
    "validator": ROOT / "scripts" / "validate_prod_069_english_remaining_product_policy_gate_selection_after_voicemail.py",
    "source_validator": ROOT / "scripts" / "validate_prod_068_english_voicemail_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_069_ENGLISH_REMAINING_PRODUCT_POLICY_GATE_SELECTION_AFTER_VOICEMAIL.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "priority_gate_options": ROOT / "research" / "experiments" / "generated" / PRIORITY_SOURCE_CHECKPOINT_ID / "gate_options.json",
    "priority_gate_priority": ROOT / "research" / "experiments" / "generated" / PRIORITY_SOURCE_CHECKPOINT_ID / "gate_priority.json",
    "prior_remaining_options": ROOT / "research" / "experiments" / "generated" / PRIOR_SELECTION_CHECKPOINT_ID / "remaining_gate_options.json",
    "prior_remaining_selection": ROOT / "research" / "experiments" / "generated" / PRIOR_SELECTION_CHECKPOINT_ID / "remaining_gate_selection.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "remaining_gate_selection": OUT_DIR / "remaining_gate_selection.json",
    "remaining_gate_options": OUT_DIR / "remaining_gate_options.json",
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
    priority = read_json(SOURCE_FILES["priority_gate_options"])
    prior_options = read_json(SOURCE_FILES["prior_remaining_options"])
    prior_selection = read_json(SOURCE_FILES["prior_remaining_selection"])
    summary = source["summary"]

    assert_condition(source["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source)
    assert_condition(source["validation"]["passed"] is True, source)
    assert_condition(summary["stable_english_guard_passed"] is True, summary)
    assert_condition(summary["failed_case_count"] == 0, summary)
    assert_condition(summary["recommended_next_checkpoint"] == CHECKPOINT_ID, summary)
    assert_condition(priority["selected_first_gate_id"] == "context_sensitive_autonomy_behavior", priority)
    assert_condition(REMAINING_GATES <= {item["gate_id"] for item in priority["ranked_gates"]}, priority)
    assert_condition(prior_options["selected_next_gate_id"] == "voicemail_action_only_behavior", prior_options)
    assert_condition(prior_selection["selected_gate"]["gate_id"] == "voicemail_action_only_behavior", prior_selection)
    assert_condition(set(prior_selection["deferred_gates"]) == REMAINING_GATES, prior_selection)


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
    review_html = OUT_DIR / "prod_069_review.html"
    assert_condition(not review_html.exists(), "PROD-069 must not create review HTML unless human review is required")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "remaining_english_product_policy_gate_selection_after_voicemail_only", payload)
    assert_condition(payload["selected_gate_id"] == SELECTED_GATE_ID, payload)
    assert_condition(set(payload["remaining_gate_ids"]) == REMAINING_GATES, payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    selection = read_json(GENERATED_FILES["remaining_gate_selection"])
    options = read_json(GENERATED_FILES["remaining_gate_options"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["gate_selection_passed"] is True, result)
    assert_condition(summary["selection_only"] is True, summary)
    assert_condition(summary["selected_gate_id"] == SELECTED_GATE_ID, summary)
    assert_condition(summary["selected_gate_status"] == "selected_for_next_probe_still_blocked", summary)
    assert_condition(set(summary["remaining_gate_ids"]) == REMAINING_GATES, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(selection["decision"] == "select_coverage_knowledge_policy_behavior_next", selection)
    assert_condition(selection["selected_gate"]["gate_id"] == SELECTED_GATE_ID, selection)
    assert_condition(selection["selected_gate"]["runtime_patch_allowed"] is False, selection)
    assert_condition(selection["selected_gate"]["retrieval_allowed"] is False, selection)
    assert_condition(selection["selected_gate"]["recommended_probe_scope"] == "synthetic English coverage knowledge-policy boundary examples only", selection)
    assert_condition(selection["deferred_gates"] == ["customer_move_classification_outside_selected_non_refusal_groups"], selection)
    assert_condition(options["selected_next_gate_id"] == SELECTED_GATE_ID, options)
    assert_condition(len(options["ranked_remaining_gates"]) == 2, options)
    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)
    assert_condition(evidence["priority_source_checkpoint_id"] == PRIORITY_SOURCE_CHECKPOINT_ID, evidence)

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
        "prod-069",
        "english remaining product-policy gate selection after voicemail",
        "coverage_knowledge_policy_behavior",
        "customer_move_classification_outside_selected_non_refusal_groups",
        "selected for next probe",
        "selection only",
        "no human review required",
        "review html created: `false`",
        "prod-070-english-coverage-knowledge-policy-probe",
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
