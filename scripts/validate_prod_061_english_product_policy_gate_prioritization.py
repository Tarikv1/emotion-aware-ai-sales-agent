#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
SOURCE_CHECKPOINT_ID = "PROD-060-runtime-promotion-path-decision"
NEXT_CHECKPOINT_ID = "PROD-062-english-context-sensitive-autonomy-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-061-english-product-policy-gate-prioritization.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_061_english_product_policy_gate_prioritization.py",
    "runner": ROOT / "scripts" / "run_prod_061_english_product_policy_gate_prioritization.py",
    "validator": ROOT / "scripts" / "validate_prod_061_english_product_policy_gate_prioritization.py",
    "doc": ROOT / "docs" / "product" / "PROD_061_ENGLISH_PRODUCT_POLICY_GATE_PRIORITIZATION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "path_decision.json",
    "source_options": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "path_options.json",
    "source_evidence": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "evidence_summary.json",
    "source_review_html": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "prod_060_review.html",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "gate_priority": OUT_DIR / "gate_priority.json",
    "gate_options": OUT_DIR / "gate_options.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

UNNEEDED_REVIEW_HTML = OUT_DIR / "prod_061_review.html"

PRODUCT_POLICY_GATES = {
    "context_sensitive_autonomy_behavior",
    "voicemail_action_only_behavior",
    "coverage_knowledge_policy_behavior",
    "customer_move_classification_outside_selected_non_refusal_groups",
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
    options = read_json(SOURCE_FILES["source_options"])
    evidence = read_json(SOURCE_FILES["source_evidence"])

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["selected_path"] == "internal_guarded_english_baseline_only", result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result)
    assert_condition(set(result["summary"]["still_blocked"]) == REQUIRED_STILL_BLOCKED, result)
    assert_condition(decision["decision"] == "select_internal_guarded_english_baseline_only", decision)
    assert_condition(decision["selected_path"]["production_promotion"] is False, decision)
    assert_condition(decision["requires_human_review_before_next_checkpoint"] is True, decision)
    assert_condition(options["selected_path_id"] == "internal_guarded_english_baseline_only", options)
    assert_condition(evidence["source_stable_guard_passed"] is True, evidence)


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
    assert_condition(not UNNEEDED_REVIEW_HTML.exists(), f"review HTML is not required for {CHECKPOINT_ID}: {rel(UNNEEDED_REVIEW_HTML)}")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_product_policy_prioritization_only", payload)
    assert_condition(payload["human_review_decision"] == "accepted_to_proceed", payload)
    assert_condition(payload["selected_first_gate"] == "context_sensitive_autonomy_behavior", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["not_a_runtime_patch"] is True, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    priority = read_json(GENERATED_FILES["gate_priority"])
    options = read_json(GENERATED_FILES["gate_options"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["priority_gate_passed"] is True, result)

    assert_condition(summary["prioritization_only"] is True, summary)
    assert_condition(summary["selected_first_gate"] == "context_sensitive_autonomy_behavior", summary)
    assert_condition(summary["selected_first_gate_status"] == "selected_for_next_probe_still_blocked", summary)
    assert_condition(summary["product_policy_gate_count"] == 4, summary)
    assert_condition(summary["still_blocked_count"] == len(REQUIRED_STILL_BLOCKED), summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition("review_html_path" not in summary, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)

    assert_condition(priority["decision"] == "prioritize_context_sensitive_autonomy_first", priority)
    assert_condition(priority["selected_first_gate"]["gate_id"] == "context_sensitive_autonomy_behavior", priority)
    assert_condition(priority["selected_first_gate"]["next_action"] == "open_targeted_policy_probe", priority)
    assert_condition(priority["selected_first_gate"]["runtime_patch_allowed"] is False, priority)
    assert_condition(priority["selected_first_gate"]["still_blocked_until_probe_passes"] is True, priority)
    assert_condition(priority["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, priority)
    assert_condition(priority["requires_human_review_before_next_checkpoint"] is False, priority)
    assert_condition(set(priority["still_blocked"]) == REQUIRED_STILL_BLOCKED, priority)

    ranked = options["ranked_gates"]
    assert_condition(len(ranked) == 4, ranked)
    assert_condition({item["gate_id"] for item in ranked} == PRODUCT_POLICY_GATES, ranked)
    assert_condition(ranked[0]["gate_id"] == "context_sensitive_autonomy_behavior", ranked)
    assert_condition(ranked[0]["rank"] == 1, ranked)
    assert_condition(ranked[0]["selected_for_next_probe"] is True, ranked)
    for index, item in enumerate(ranked, start=1):
        assert_condition(item["rank"] == index, ranked)
        assert_condition(item["status"] in {"selected_for_next_probe_still_blocked", "deferred_still_blocked"}, item)
        assert_condition(isinstance(item["why"], str) and item["why"], item)
        assert_condition(isinstance(item["risk"], str) and item["risk"], item)
        assert_condition(isinstance(item["review_question"], str) and item["review_question"], item)
        assert_condition(item["runtime_patch_allowed"] is False, item)

    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_selected_path"] == "internal_guarded_english_baseline_only", evidence)
    assert_condition(evidence["english_direction_accepted"] is True, evidence)
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
        "prod-061",
        "english product-policy gate prioritization",
        "context_sensitive_autonomy_behavior",
        "selected_for_next_probe_still_blocked",
        "prod-062-english-context-sensitive-autonomy-policy-probe",
        "voicemail_action_only_behavior",
        "coverage_knowledge_policy_behavior",
        "customer_move_classification_outside_selected_non_refusal_groups",
        "no human review required",
        "not a runtime patch",
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
