#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-062-english-context-sensitive-autonomy-policy-probe"
SOURCE_CHECKPOINT_ID = "PROD-061-english-product-policy-gate-prioritization"
NEXT_CHECKPOINT_ID = "PROD-063-english-autonomy-check-runtime-wording-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-062-english-context-sensitive-autonomy-policy-probe.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_062_english_context_sensitive_autonomy_policy_probe.py",
    "runner": ROOT / "scripts" / "run_prod_062_english_context_sensitive_autonomy_policy_probe.py",
    "validator": ROOT / "scripts" / "validate_prod_062_english_context_sensitive_autonomy_policy_probe.py",
    "doc": ROOT / "docs" / "product" / "PROD_062_ENGLISH_CONTEXT_SENSITIVE_AUTONOMY_POLICY_PROBE.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_priority": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "gate_priority.json",
    "source_options": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "gate_options.json",
    "source_evidence": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "evidence_summary.json",
    "source_candidate": ROOT / "research" / "experiments" / "generated" / "PROD-053D-english-review-import" / "runtime_patch_candidates.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "policy_decision": OUT_DIR / "policy_decision.json",
    "probe_reviews": OUT_DIR / "probe_reviews.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

EXPECTED_CANDIDATE = "Okay, no rush. We can keep this low-pressure and only clarify what you need."

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
    priority = read_json(SOURCE_FILES["source_priority"])
    options = read_json(SOURCE_FILES["source_options"])

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["selected_first_gate"] == "context_sensitive_autonomy_behavior", result)
    assert_condition(result["summary"]["requires_human_review_before_next_checkpoint"] is False, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result)
    assert_condition(priority["selected_first_gate"]["gate_id"] == "context_sensitive_autonomy_behavior", priority)
    assert_condition(priority["selected_first_gate"]["runtime_patch_allowed"] is False, priority)
    assert_condition(priority["recommended_next_checkpoint"] == CHECKPOINT_ID, priority)
    assert_condition(options["selected_first_gate_id"] == "context_sensitive_autonomy_behavior", options)


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
    assert_condition(payload["scope"] == "synthetic_english_autonomy_policy_probe_only", payload)
    assert_condition(payload["candidate_response"] == EXPECTED_CANDIDATE, payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["not_a_runtime_patch"] is True, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(len(payload["probe_cases"]) == 5, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    decision = read_json(GENERATED_FILES["policy_decision"])
    reviews = read_json(GENERATED_FILES["probe_reviews"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["policy_probe_passed"] is True, result)

    assert_condition(summary["policy_probe_only"] is True, summary)
    assert_condition(summary["candidate_response"] == EXPECTED_CANDIDATE, summary)
    assert_condition(summary["probe_case_count"] == 5, summary)
    assert_condition(summary["passed_probe_count"] == 5, summary)
    assert_condition(summary["failed_probe_count"] == 0, summary)
    assert_condition(summary["runtime_patch_allowed"] is False, summary)
    assert_condition(summary["runtime_patch_recommended_next"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(decision["decision"] == "autonomy_policy_probe_passed_recommend_narrow_runtime_patch", decision)
    assert_condition(decision["candidate_response"] == EXPECTED_CANDIDATE, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(decision["runtime_patch_allowed_in_prod_062"] is False, decision)
    assert_condition(decision["requires_human_review_before_next_checkpoint"] is False, decision)

    items = reviews["items"]
    assert_condition(len(items) == 5, items)
    for item in items:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["issue_codes"] == [], item)
        gates = item["gates"]
        for key in [
            "acknowledges_no_rush",
            "preserves_customer_choice",
            "offers_clarification_only",
            "no_commitment_or_payment",
            "no_urgency_or_pressure",
            "no_fake_personalization",
            "single_low_pressure_next_step",
            "english_only",
        ]:
            assert_condition(gates[key] is True, item)

    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_selected_gate"] == "context_sensitive_autonomy_behavior", evidence)
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
        "prod-062",
        "english context-sensitive autonomy policy probe",
        "synthetic english autonomy policy probe only",
        "okay, no rush",
        "not a runtime patch",
        "no human review required",
        "prod-063-english-autonomy-check-runtime-wording-patch",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "production runtime promotion allowed: `false`",
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
