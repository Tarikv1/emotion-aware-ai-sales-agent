#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-095-english-next-step-process-clarity-runtime-patch"
SOURCE_CHECKPOINT_ID = "PROD-094-english-next-step-process-clarity-narrow-probe"
NEXT_CHECKPOINT_ID = "PROD-096-english-next-step-process-clarity-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-095-english-next-step-process-clarity-runtime-patch.json"
RUNTIME_FILE = ROOT / "runtime" / "core" / "realtime_turns.py"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_095_english_next_step_process_clarity_runtime_patch.py",
    "runner": ROOT / "scripts" / "run_prod_095_english_next_step_process_clarity_runtime_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_095_english_next_step_process_clarity_runtime_patch.py",
    "source_validator": ROOT / "scripts" / "validate_prod_094_english_next_step_process_clarity_narrow_probe.py",
    "doc": ROOT / "docs" / "product" / "PROD_095_ENGLISH_NEXT_STEP_PROCESS_CLARITY_RUNTIME_PATCH.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
    "runtime_file": RUNTIME_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_constraints": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "candidate_policy_constraints.json",
    "source_gaps": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "current_runtime_gap_analysis.json",
    "source_probe": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "policy_probe_result.json",
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
    constraints = read_json(SOURCE_FILES["source_constraints"])
    gaps = read_json(SOURCE_FILES["source_gaps"])
    probe = read_json(SOURCE_FILES["source_probe"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["process_clarity_probe_passed"] is True, result["summary"])
    assert_condition(result["summary"]["current_runtime_gap_count"] == 1, result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(constraints["runtime_patch_allowed_inside_checkpoint"] is False, constraints)
    assert_condition(constraints["no_payment_on_call_default"] is True, constraints)
    assert_condition(constraints["email_link_register_path_allowed"] is True, constraints)
    assert_condition(gaps["runtime_gap_count"] == 1, gaps)
    assert_condition(probe["failed_policy_case_count"] == 0, probe)


def validate_runtime_patch_text() -> None:
    text = RUNTIME_FILE.read_text(encoding="utf-8")
    for marker in [
        "english_next_step_process_clarity_response",
        "next-step-process-clarity",
        "No payment on this call",
        "guided_option_payment_email_link_allowed",
        "sign me up",
        "what happens after",
    ]:
        assert_condition(marker in text, f"runtime missing marker {marker!r}")


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=360,
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
    assert_condition(payload["scope"] == "english_next_step_process_clarity_runtime_patch", payload)
    assert_condition(payload["runtime_patch_allowed"] is True, payload)
    assert_condition(payload["selected_source_slice"] == "next_step_process_clarity", payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    patch = read_json(GENERATED_FILES["runtime_patch_summary"])
    positives = read_json(GENERATED_FILES["positive_runtime_cases"])
    controls = read_json(GENERATED_FILES["control_runtime_cases"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["runtime_patch_verified"] is True, result)
    assert_condition(summary["runtime_patch_applied"] is True, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    assert_condition(summary["classifier_behavior_changed"] is True, summary)
    assert_condition(summary["selected_gap_fixed_count"] == 1, summary)
    assert_condition(summary["positive_case_failures"] == 0, summary)
    assert_condition(summary["control_case_failures"] == 0, summary)
    assert_condition(summary["current_runtime_gap_count_before_patch"] == 1, summary)
    assert_condition(summary["no_payment_on_call_default"] is True, summary)
    assert_condition(summary["email_link_register_path_allowed"] is True, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(patch["runtime_patch_applied"] is True, patch)
    assert_condition(patch["selected_gap_case_ids"] == ["prod-081-next-step-01"], patch)
    assert_condition(patch["email_link_flag_required"] is True, patch)
    assert_condition(positives["failure_count"] == 0, positives)
    assert_condition(positives["case_count"] >= 5, positives)
    assert_condition(controls["failure_count"] == 0, controls)
    assert_condition(controls["case_count"] >= 10, controls)
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
        "prod-095",
        "english next-step process clarity runtime patch",
        "selected gap fixed count: `1`",
        "positive case failures: `0`",
        "control case failures: `0`",
        "no payment on this call default: `true`",
        "email link register path allowed: `true`",
        "review html created: `false`",
        "prod-096-english-next-step-process-clarity-post-patch-regression",
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
    validate_runtime_patch_text()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
