#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-060-runtime-promotion-path-decision"
SOURCE_CHECKPOINT_ID = "PROD-059-final-english-only-runtime-readiness-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-060-runtime-promotion-path-decision.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_060_runtime_promotion_path_decision.py",
    "runner": ROOT / "scripts" / "run_prod_060_runtime_promotion_path_decision.py",
    "validator": ROOT / "scripts" / "validate_prod_060_runtime_promotion_path_decision.py",
    "doc": ROOT / "docs" / "product" / "PROD_060_RUNTIME_PROMOTION_PATH_DECISION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "readiness_decision.json",
    "source_exclusions": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "scope_exclusions.json",
    "source_evidence": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "evidence_summary.json",
    "source_review_html": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "prod_059_review.html",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "path_decision": OUT_DIR / "path_decision.json",
    "path_options": OUT_DIR / "path_options.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
    "review_html": OUT_DIR / "prod_060_review.html",
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

REQUIRED_BLOCKED_PATHS = {
    "public_demo_path",
    "real_customer_path",
    "provider_or_private_data_path",
    "retrieval_default_path",
    "voice_playback_path",
    "german_language_path",
    "payment_or_contract_path",
    "production_runtime_path",
}

REQUIRED_STILL_BLOCKED = {
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

    result = read_json(SOURCE_FILES["source_result"])
    decision = read_json(SOURCE_FILES["source_decision"])
    exclusions = read_json(SOURCE_FILES["source_exclusions"])
    evidence = read_json(SOURCE_FILES["source_evidence"])

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["human_review_acceptance_recorded"] is True, result)
    assert_condition(result["summary"]["english_only_runtime_readiness_status"] == "ready_with_exclusions", result)
    assert_condition(result["summary"]["bounded_english_surface_ready"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result)
    assert_condition(decision["decision"] == "english_only_runtime_ready_with_exclusions", decision)
    assert_condition(decision["not_production_ready"] is True, decision)
    assert_condition(decision["requires_human_decision_before_runtime_promotion_path"] is True, decision)
    assert_condition(set(exclusions["excluded_blockers"]) == REQUIRED_STILL_BLOCKED, exclusions)
    assert_condition(evidence["stable_guard_run"]["passed"] is True, evidence)


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
    assert_condition(payload["scope"] == "path_decision_only", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["not_a_production_promotion"] is True, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is True, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    path_decision = read_json(GENERATED_FILES["path_decision"])
    path_options = read_json(GENERATED_FILES["path_options"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["path_decision_gate_passed"] is True, result)

    assert_condition(summary["path_decision_only"] is True, summary)
    assert_condition(summary["source_readiness_status"] == "ready_with_exclusions", summary)
    assert_condition(summary["selected_path"] == "internal_guarded_english_baseline_only", summary)
    assert_condition(summary["selected_path_allowed"] is True, summary)
    assert_condition(summary["blocked_path_count"] >= len(REQUIRED_BLOCKED_PATHS), summary)
    assert_condition(summary["still_blocked_count"] == len(REQUIRED_STILL_BLOCKED), summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is True, summary)
    assert_condition(summary["recommended_next_checkpoint"] == "PROD-061-english-product-policy-gate-prioritization", summary)
    assert_condition(summary["review_html_path"] == "research/experiments/generated/PROD-060-runtime-promotion-path-decision/prod_060_review.html", summary)

    assert_condition(path_decision["decision"] == "select_internal_guarded_english_baseline_only", path_decision)
    assert_condition(path_decision["selected_path"]["path_id"] == "internal_guarded_english_baseline_only", path_decision)
    assert_condition(path_decision["selected_path"]["runtime_change"] is False, path_decision)
    assert_condition(path_decision["selected_path"]["production_promotion"] is False, path_decision)
    assert_condition(path_decision["requires_human_review_before_next_checkpoint"] is True, path_decision)
    assert_condition(set(path_decision["still_blocked"]) == REQUIRED_STILL_BLOCKED, path_decision)

    options = path_options["path_options"]
    selected = [item for item in options if item["selected"]]
    blocked = [item for item in options if item["status"] == "blocked"]
    assert_condition(len(selected) == 1, options)
    assert_condition(selected[0]["path_id"] == "internal_guarded_english_baseline_only", selected)
    assert_condition(selected[0]["status"] == "selected", selected)
    assert_condition(selected[0]["allowed_scope"] == "local_offline_synthetic_internal_regression_reference", selected)
    assert_condition({item["path_id"] for item in blocked} >= REQUIRED_BLOCKED_PATHS, blocked)
    for option in options:
        assert_condition(isinstance(option["why"], str) and option["why"], option)
        assert_condition(isinstance(option["review_question"], str) and option["review_question"], option)

    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_readiness_decision"] == "english_only_runtime_ready_with_exclusions", evidence)
    assert_condition(evidence["source_stable_guard_passed"] is True, evidence)

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
        "prod-060",
        "runtime promotion path decision",
        "internal_guarded_english_baseline_only",
        "local offline synthetic internal regression reference",
        "ready_with_exclusions",
        "prod-059",
        "prod-061-english-product-policy-gate-prioritization",
        "requires human review",
        "not production",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "production runtime promotion allowed: `false`",
        "public demo",
        "real customer",
        "provider",
        "private data",
        "retrieval",
        "voice playback",
        "german",
        "payment",
        "contract",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def validate_review_html() -> None:
    text = GENERATED_FILES["review_html"].read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in [
        "<!doctype html>",
        "prod-060",
        "runtime promotion path decision",
        "review examples",
        "internal_guarded_english_baseline_only",
        "local offline synthetic internal regression reference",
        "public demo path",
        "real customer path",
        "production runtime path",
        "accept current decision",
        "request revision",
        "export json",
        "import json",
        "localstorage",
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
