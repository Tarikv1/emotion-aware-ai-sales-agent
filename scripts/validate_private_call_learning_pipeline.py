#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_private_call_learning_pipeline.py"
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "private-call-learning-001.json"
POLICY_DOC = ROOT / "docs" / "data" / "PRIVATE_CALL_LEARNING_PIPELINE.md"
VALIDATION_DIR = ROOT / ".tmp" / "private-call-learning-validation"
OUT_JSON = VALIDATION_DIR / "PRIVATE-CALL-LEARNING-001.json"
OUT_REPORT = VALIDATION_DIR / "PRIVATE-CALL-LEARNING-001-report.md"


REQUIRED_STAGE_IDS = [
    "ingest_raw_audio_local_only",
    "local_transcription",
    "speaker_segmentation",
    "pii_sensitive_redaction",
    "outcome_labeling",
    "pattern_mining",
    "human_review",
    "safe_learning_export",
    "retention_or_deletion",
]

REQUIRED_LEARNING_OUTPUTS = {
    "positive_sales_pattern",
    "negative_sales_pattern",
    "customer_objection_pattern",
    "human_agent_success_pattern",
    "human_agent_failure_pattern",
    "safety_or_compliance_constraint",
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_checker() -> dict[str, object]:
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--case",
            str(CASE_FILE),
            "--out",
            str(OUT_JSON),
            "--report-out",
            str(OUT_REPORT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    combined_output = completed.stdout + completed.stderr
    assert_condition("sk_" not in combined_output.lower(), "Checker output must not include secret-like API keys.")
    assert_condition(OUT_JSON.is_file(), "Checker did not write the JSON report.")
    assert_condition(OUT_REPORT.is_file(), "Checker did not write the Markdown report.")
    return json.loads(OUT_JSON.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, object]) -> None:
    assert_condition(payload["pipeline_id"] == "PRIVATE-CALL-LEARNING-001", "Unexpected pipeline id.")
    assert_condition(payload["status"] == "pass", "Private call learning pipeline check should pass.")
    assert_condition(payload["network_calls_made"] is False, "Checker must not make network calls.")
    assert_condition(payload["raw_private_content_read"] is False, "Checker must not read raw private call content.")
    assert_condition(payload["secret_values_logged"] is False, "Checker must not log secret values.")

    boundary = payload["boundary"]
    assert_condition(isinstance(boundary, dict), "Boundary summary must be an object.")
    assert_condition(boundary["raw_audio_provider_upload_allowed"] is False, "Raw private audio upload must be blocked.")
    assert_condition(boundary["raw_audio_git_tracking_allowed"] is False, "Raw private audio Git tracking must be blocked.")
    assert_condition(boundary["customer_identifier_learning_allowed"] is False, "Customer identifiers must not be learned.")
    assert_condition(boundary["fine_tuning_enabled_by_default"] is False, "Fine-tuning must not be enabled by default.")

    stage_ids = [stage["stage_id"] for stage in payload["stages"]]
    assert_condition(stage_ids == REQUIRED_STAGE_IDS, "Pipeline stages must preserve the reviewed local-only order.")

    learning_outputs = set(payload["learning_outputs"])
    missing_outputs = sorted(REQUIRED_LEARNING_OUTPUTS - learning_outputs)
    assert_condition(not missing_outputs, f"Missing required learning outputs: {missing_outputs}")

    checks = {check["id"]: check for check in payload["checks"]}
    for required_check in [
        "private_root.exists",
        "private_root.gitignored",
        "case_file.safe",
        "policy_doc.exists",
        "policy_doc.boundary",
        "pipeline.no_provider_upload",
        "pipeline.no_identifier_learning",
        "pipeline.redaction_before_export",
        "pipeline.human_review_before_export",
        "pipeline.retention_or_deletion",
    ]:
        assert_condition(required_check in checks, f"Missing check: {required_check}")
        assert_condition(checks[required_check]["status"] == "pass", f"Check failed: {required_check}")


def validate_docs() -> None:
    text = POLICY_DOC.read_text(encoding="utf-8")
    for phrase in [
        "Pattern-mining first, fine-tuning later",
        "Raw private audio never leaves `data/private/`",
        "Private identifiers are not training signal",
        "Bad calls are useful as negative constraints",
        "No safe export before redaction and human review",
    ]:
        assert_condition(phrase in text, f"Missing policy phrase: {phrase}")


def main() -> None:
    assert_condition(CHECKER.is_file(), "Private call learning checker is missing.")
    assert_condition(CASE_FILE.is_file(), "PRIVATE-CALL-LEARNING-001 case file is missing.")
    assert_condition(POLICY_DOC.is_file(), "Private call learning policy doc is missing.")
    validate_docs()
    validate_payload(run_checker())
    print("Private call learning pipeline validation passed.")


if __name__ == "__main__":
    main()
