#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-087-english-guided-option-selection-runtime-patch"
SOURCE_CHECKPOINT_ID = "PROD-086-english-guided-option-selection-narrow-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-088-english-guided-option-selection-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-087-english-guided-option-selection-runtime-patch.json"
RUNTIME_FILE = ROOT / "runtime" / "core" / "realtime_turns.py"
PAYMENT_RESPONSE = "No payment on this call. I'll send you the link by email, and you can review the plan and register there."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_087_english_guided_option_selection_runtime_patch.py",
    "runner": ROOT / "scripts" / "run_prod_087_english_guided_option_selection_runtime_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_087_english_guided_option_selection_runtime_patch.py",
    "source_validator": ROOT / "scripts" / "validate_prod_086_english_guided_option_selection_narrow_policy_probe.py",
    "runtime": RUNTIME_FILE,
    "doc": ROOT / "docs" / "product" / "PROD_087_ENGLISH_GUIDED_OPTION_SELECTION_RUNTIME_PATCH.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "policy_probe": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "policy_probe_result.json",
    "constraints": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "candidate_policy_constraints.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "runtime_patch_summary": OUT_DIR / "runtime_patch_summary.json",
    "positive_runtime_cases": OUT_DIR / "positive_runtime_cases.json",
    "control_runtime_cases": OUT_DIR / "control_runtime_cases.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

BOUNDARY_FALSE_FIELDS = [
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
    probe = read_json(SOURCE_FILES["policy_probe"])
    constraints = read_json(SOURCE_FILES["constraints"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["policy_probe_passed"] is True, result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(probe["policy_probe_passed"] is True, probe)
    assert_condition(probe["failed_policy_case_count"] == 0, probe)
    assert_condition(constraints["requires_plan_feature_matrix"] is True, constraints)
    assert_condition(constraints["requires_customer_facts_for_steering"] is True, constraints)
    assert_condition(constraints["requires_no_payment_on_call_default"] is True, constraints)
    assert_condition(constraints["approved_payment_response"] == PAYMENT_RESPONSE, constraints)


def validate_runtime_text() -> None:
    text = RUNTIME_FILE.read_text(encoding="utf-8")
    for marker in [
        "guided-option-selection",
        "english_guided_option_plan_feature_matrix",
        "english_guided_option_selection_response",
        "is_english_guided_option_selection_turn",
        PAYMENT_RESPONSE,
    ]:
        assert_condition(marker in text, f"runtime missing marker: {marker}")


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
    assert_condition(payload["scope"] == "english_guided_option_selection_runtime_patch", payload)
    assert_condition(payload["runtime_patch_applied"] is True, payload)
    assert_condition(payload["requires_plan_feature_matrix"] is True, payload)
    assert_condition(payload["requires_customer_facts_for_steering"] is True, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    patch = read_json(GENERATED_FILES["runtime_patch_summary"])
    positives = read_json(GENERATED_FILES["positive_runtime_cases"])
    controls = read_json(GENERATED_FILES["control_runtime_cases"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["runtime_patch_applied"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    assert_condition(summary["classifier_behavior_changed"] is True, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["positive_case_count"] == 8, summary)
    assert_condition(summary["positive_case_failures"] == 0, summary)
    assert_condition(summary["control_case_failures"] == 0, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(patch["runtime_file"] == "runtime/core/realtime_turns.py", patch)
    assert_condition(patch["new_sales_difficulty"] == "guided-option-selection", patch)
    assert_condition(patch["requires_plan_feature_matrix"] is True, patch)
    assert_condition(patch["requires_customer_facts_for_steering"] is True, patch)
    assert_condition(patch["payment_response"] == PAYMENT_RESPONSE, patch)
    assert_condition(positives["case_count"] == 8, positives)
    assert_condition(all(item["passed"] for item in positives["cases"]), positives)
    assert_condition(all(item["sales_difficulty"] == "guided-option-selection" for item in positives["cases"]), positives)
    payment_cases = [item for item in positives["cases"] if item["case_id"] == "prod-087-rewrite-payment-path"]
    assert_condition(len(payment_cases) == 1, positives)
    assert_condition(payment_cases[0]["agent_response"] == PAYMENT_RESPONSE, payment_cases)
    assert_condition("companyname.com" not in json.dumps(positives).lower(), positives)
    assert_condition(controls["case_count"] >= 8, controls)
    assert_condition(all(item["passed"] for item in controls["cases"]), controls)
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
        "prod-087",
        "english guided option selection runtime patch",
        "guided-option-selection",
        "runtime patch applied: `true`",
        "requires plan feature matrix",
        "requires customer facts for steering",
        "no payment on this call",
        "i'll send you the link by email",
        "review html created: `false`",
        "prod-088-english-guided-option-selection-post-patch-regression",
        "runtime behavior changed: `true`",
        "response text behavior changed: `true`",
        "classifier behavior changed: `true`",
        "retrieval enabled: `false`",
        "production runtime promotion allowed: `false`",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_sources()
    validate_runtime_text()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
