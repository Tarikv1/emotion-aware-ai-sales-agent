#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-058-english-runtime-promotion-blocker-inventory"
SOURCE_CHECKPOINT_ID = "PROD-057-english-multi-turn-regression-guard-decision"
SOURCE_REGRESSION_ID = "PROD-056-english-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-058-english-runtime-promotion-blocker-inventory.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_058_english_runtime_promotion_blocker_inventory.py",
    "runner": ROOT / "scripts" / "run_prod_058_english_runtime_promotion_blocker_inventory.py",
    "validator": ROOT / "scripts" / "validate_prod_058_english_runtime_promotion_blocker_inventory.py",
    "doc": ROOT / "docs" / "product" / "PROD_058_ENGLISH_RUNTIME_PROMOTION_BLOCKER_INVENTORY.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_guard_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_regression_result": ROOT / "research" / "experiments" / "generated" / SOURCE_REGRESSION_ID / "result.json",
    "stable_guard": ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "blocker_inventory": OUT_DIR / "blocker_inventory.json",
    "recommendation": OUT_DIR / "recommendation.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
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
]

REQUIRED_BLOCKER_CATEGORIES = {
    "english_evidence_gap",
    "product_policy_gate",
    "separate_language_gate",
    "separate_voice_gate",
    "separate_retrieval_gate",
    "provider_or_private_data_gate",
    "legal_or_deployment_gate",
}

REQUIRED_BLOCKER_IDS = {
    "final_english_only_readiness_review_not_run",
    "english_guard_scope_limited_to_promoted_multi_turn_surface",
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
    guard_result = read_json(SOURCE_FILES["source_guard_result"])
    regression_result = read_json(SOURCE_FILES["source_regression_result"])
    guard_summary = guard_result["summary"]
    regression_summary = regression_result["summary"]

    assert_condition(guard_result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, guard_result)
    assert_condition(guard_result["validation"]["passed"] is True, guard_result)
    assert_condition(guard_result["validation"]["guard_decision_passed"] is True, guard_result)
    assert_condition(guard_summary["guard_status"] == "adopted", guard_summary)
    assert_condition(guard_summary["english_multi_turn_guard_adopted"] is True, guard_summary)
    assert_condition(guard_summary["source_promoted_response_count"] == 26, guard_summary)
    assert_condition(guard_summary["source_blocking_finding_count"] == 0, guard_summary)

    assert_condition(regression_result["checkpoint_id"] == SOURCE_REGRESSION_ID, regression_result)
    assert_condition(regression_result["validation"]["regression_gate_passed"] is True, regression_result)
    assert_condition(regression_summary["blocking_finding_count"] == 0, regression_summary)
    assert_condition(regression_summary["permanent_regression_guard_recommended"] is True, regression_summary)


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
    assert_condition(payload["scope"] == "inventory_only", payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is True, payload)
    assert_condition("final_english_only_readiness_review" in payload["possible_next_decisions"], payload)
    assert_condition("return_to_native_german_review_import" in payload["possible_next_decisions"], payload)
    assert_condition("reopen_voice_or_retrieval_only_through_separate_gates" in payload["possible_next_decisions"], payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    inventory = read_json(GENERATED_FILES["blocker_inventory"])
    recommendation = read_json(GENERATED_FILES["recommendation"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]
    blockers = inventory["blockers"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["inventory_gate_passed"] is True, result)
    assert_condition(summary["inventory_only"] is True, summary)
    assert_condition(summary["blocker_count"] == len(blockers), summary)
    assert_condition(summary["english_evidence_gap_count"] >= 2, summary)
    assert_condition(summary["product_policy_gate_count"] >= 4, summary)
    assert_condition(summary["separate_gate_count"] >= 7, summary)
    assert_condition(summary["final_english_only_readiness_review_justified"] is True, summary)
    assert_condition(summary["production_runtime_promotion_allowed"] is False, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is True, summary)
    assert_condition(summary["recommended_next_checkpoint"] == "PROD-059-final-english-only-runtime-readiness-review", summary)

    blocker_ids = {item["blocker_id"] for item in blockers}
    categories = {item["category"] for item in blockers}
    assert_condition(REQUIRED_BLOCKER_IDS <= blocker_ids, blocker_ids)
    assert_condition(REQUIRED_BLOCKER_CATEGORIES <= categories, categories)
    for item in blockers:
        assert_condition(item["status"] == "blocked", item)
        assert_condition(item["category"] in REQUIRED_BLOCKER_CATEGORIES, item)
        assert_condition(isinstance(item["evidence"], str) and item["evidence"], item)
        assert_condition(isinstance(item["recommended_next_action"], str) and item["recommended_next_action"], item)

    assert_condition(recommendation["decision"] == "run_final_english_only_readiness_review_after_human_acceptance", recommendation)
    assert_condition(recommendation["not_a_production_promotion"] is True, recommendation)
    assert_condition(recommendation["requires_human_review_before_next_checkpoint"] is True, recommendation)
    assert_condition("PROD-058 inventory" in recommendation["human_review_request"], recommendation)

    assert_condition(evidence["source_guard"]["checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_guard"]["guard_status"] == "adopted", evidence)
    assert_condition(evidence["source_regression"]["checkpoint_id"] == SOURCE_REGRESSION_ID, evidence)
    assert_condition(evidence["source_regression"]["blocking_finding_count"] == 0, evidence)

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
        "prod-058",
        "english runtime promotion blocker inventory",
        "inventory-only",
        "prod-057",
        "prod-056",
        "english evidence gap",
        "product-policy gate",
        "separate language gate",
        "separate voice gate",
        "separate retrieval gate",
        "final english-only runtime readiness review",
        "requires human review",
        "no provider",
        "no llm",
        "no private data",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "production runtime promotion allowed: `false`",
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
