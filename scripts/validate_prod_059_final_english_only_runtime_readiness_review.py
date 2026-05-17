#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-059-final-english-only-runtime-readiness-review"
SOURCE_CHECKPOINT_ID = "PROD-058-english-runtime-promotion-blocker-inventory"
SOURCE_GUARD_ID = "PROD-057-english-multi-turn-regression-guard-decision"
SOURCE_REGRESSION_ID = "PROD-056-english-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-059-final-english-only-runtime-readiness-review.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_059_final_english_only_runtime_readiness_review.py",
    "runner": ROOT / "scripts" / "run_prod_059_final_english_only_runtime_readiness_review.py",
    "validator": ROOT / "scripts" / "validate_prod_059_final_english_only_runtime_readiness_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_059_FINAL_ENGLISH_ONLY_RUNTIME_READINESS_REVIEW.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_inventory_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_inventory_recommendation": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "recommendation.json",
    "source_inventory_blockers": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "blocker_inventory.json",
    "source_guard_result": ROOT / "research" / "experiments" / "generated" / SOURCE_GUARD_ID / "result.json",
    "source_regression_result": ROOT / "research" / "experiments" / "generated" / SOURCE_REGRESSION_ID / "result.json",
    "stable_guard": ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "readiness_decision": OUT_DIR / "readiness_decision.json",
    "scope_exclusions": OUT_DIR / "scope_exclusions.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
    "review_html": OUT_DIR / "prod_059_review.html",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "response_text_behavior_changed",
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

REQUIRED_RESOLVED_BLOCKERS = {
    "final_english_only_readiness_review_not_run",
    "english_guard_scope_limited_to_promoted_multi_turn_surface",
}

REQUIRED_EXCLUDED_BLOCKERS = {
    "customer_move_classification_outside_selected_non_refusal_groups",
    "voicemail_action_only_behavior",
    "coverage_knowledge_policy_behavior",
    "context_sensitive_autonomy_behavior",
    "native_german_review",
    "voice_playback_quality",
    "retrieval_default",
    "provider_or_private_data_use",
    "legal_compliance_review",
    "public_demo_use",
    "real_customer_use",
    "payment_collection",
    "contract_signing",
    "production_runtime_promotion",
}


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
    inventory = read_json(SOURCE_FILES["source_inventory_result"])
    recommendation = read_json(SOURCE_FILES["source_inventory_recommendation"])
    guard = read_json(SOURCE_FILES["source_guard_result"])
    regression = read_json(SOURCE_FILES["source_regression_result"])

    assert_condition(inventory["checkpoint_id"] == SOURCE_CHECKPOINT_ID, inventory)
    assert_condition(inventory["validation"]["inventory_gate_passed"] is True, inventory)
    assert_condition(inventory["summary"]["requires_human_review_before_next_checkpoint"] is True, inventory)
    assert_condition(inventory["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, inventory)
    assert_condition(recommendation["decision"] == "run_final_english_only_readiness_review_after_human_acceptance", recommendation)
    assert_condition(recommendation["requires_human_review_before_next_checkpoint"] is True, recommendation)
    assert_condition(recommendation["not_a_production_promotion"] is True, recommendation)

    assert_condition(guard["checkpoint_id"] == SOURCE_GUARD_ID, guard)
    assert_condition(guard["summary"]["guard_status"] == "adopted", guard)
    assert_condition(regression["checkpoint_id"] == SOURCE_REGRESSION_ID, regression)
    assert_condition(regression["summary"]["blocking_finding_count"] == 0, regression)


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
    assert_condition(payload["human_review_decision"] == "accepted_to_proceed", payload)
    assert_condition(payload["scope"] == "final_english_only_readiness_review", payload)
    assert_condition(payload["not_a_production_promotion"] is True, payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    decision = read_json(GENERATED_FILES["readiness_decision"])
    exclusions = read_json(GENERATED_FILES["scope_exclusions"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["readiness_review_passed"] is True, result)

    assert_condition(summary["human_review_acceptance_recorded"] is True, summary)
    assert_condition(summary["english_only_runtime_readiness_status"] == "ready_with_exclusions", summary)
    assert_condition(summary["bounded_english_surface_ready"] is True, summary)
    assert_condition(summary["production_runtime_promotion_allowed"] is False, summary)
    assert_condition(summary["resolved_blocker_count"] == len(REQUIRED_RESOLVED_BLOCKERS), summary)
    assert_condition(summary["excluded_blocker_count"] == len(REQUIRED_EXCLUDED_BLOCKERS), summary)
    assert_condition(set(summary["resolved_blockers"]) == REQUIRED_RESOLVED_BLOCKERS, summary)
    assert_condition(set(summary["excluded_blockers"]) == REQUIRED_EXCLUDED_BLOCKERS, summary)
    assert_condition(summary["recommended_next_checkpoint"] == "PROD-060-runtime-promotion-path-decision", summary)
    assert_condition(summary["review_html_path"] == "research/experiments/generated/PROD-059-final-english-only-runtime-readiness-review/prod_059_review.html", summary)

    assert_condition(decision["decision"] == "english_only_runtime_ready_with_exclusions", decision)
    assert_condition(decision["bounded_scope"]["language"] == "en", decision)
    assert_condition(decision["bounded_scope"]["surface"] == "PROD-053E promoted English deterministic runtime surface guarded by PROD-056/PROD-057", decision)
    assert_condition(decision["not_production_ready"] is True, decision)
    assert_condition(decision["requires_human_decision_before_runtime_promotion_path"] is True, decision)

    assert_condition(set(exclusions["resolved_blockers"]) == REQUIRED_RESOLVED_BLOCKERS, exclusions)
    assert_condition(set(exclusions["excluded_blockers"]) == REQUIRED_EXCLUDED_BLOCKERS, exclusions)
    assert_condition(exclusions["excluded_policy_gates_remain_blocked"] is True, exclusions)
    assert_condition(exclusions["separate_track_gates_remain_blocked"] is True, exclusions)

    assert_condition(evidence["source_inventory"]["checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_guard"]["checkpoint_id"] == SOURCE_GUARD_ID, evidence)
    assert_condition(evidence["source_regression"]["checkpoint_id"] == SOURCE_REGRESSION_ID, evidence)
    assert_condition(evidence["stable_guard_run"]["passed"] is True, evidence)

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
        "prod-059",
        "final english-only runtime readiness review",
        "ready_with_exclusions",
        "prod-058",
        "prod-057",
        "prod-056",
        "human review acceptance",
        "not production",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "production runtime promotion allowed: `false`",
        "no provider",
        "no llm",
        "no private data",
        "german exact-phrase promotion",
        "retrieval default",
        "voice playback",
        "prod-060",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def validate_review_html() -> None:
    text = GENERATED_FILES["review_html"].read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in [
        "<!doctype html>",
        "prod-059",
        "review examples",
        "ready_with_exclusions",
        "example-card",
        "accept current decision",
        "request revision",
        "export json",
        "import json",
        "localstorage",
        "filereader",
        "collectreview",
        "runtime behavior changed: false",
        "production runtime promotion allowed: false",
    ]:
        assert_condition(marker in lowered, f"review HTML missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_source_files()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    validate_review_html()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
