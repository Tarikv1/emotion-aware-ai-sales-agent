#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-076-english-provider-comparison-review-import"
SOURCE_CHECKPOINT_ID = "PROD-075-english-provider-comparison-reachability-review"
NEXT_CHECKPOINT_ID = "PROD-077-english-provider-comparison-narrow-probe-design"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
IMPORT_DIR = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID
IMPORT_FILE = IMPORT_DIR / "prod_075_provider_comparison_review_export_from_chat.json"
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-076-english-provider-comparison-review-import.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_076_english_provider_comparison_review_import.py",
    "runner": ROOT / "scripts" / "run_prod_076_english_provider_comparison_review_import.py",
    "validator": ROOT / "scripts" / "validate_prod_076_english_provider_comparison_review_import.py",
    "source_validator": ROOT / "scripts" / "validate_prod_075_english_provider_comparison_reachability_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_076_ENGLISH_PROVIDER_COMPARISON_REVIEW_IMPORT.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "import_file": IMPORT_FILE,
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_packet": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "provider_comparison_review_packet.json",
    "source_template": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "review_state_template.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "imported_review_summary": OUT_DIR / "imported_review_summary.json",
    "approved_with_constraints": OUT_DIR / "approved_with_constraints.json",
    "narrow_probe_requirements": OUT_DIR / "narrow_probe_requirements.json",
    "candidate_response_constraints": OUT_DIR / "candidate_response_constraints.json",
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


def validate_sources() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    packet = read_json(SOURCE_FILES["source_packet"])
    import_payload = read_json(IMPORT_FILE)
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["requires_human_review_before_next_checkpoint"] is True, result["summary"])
    assert_condition(packet["review_item"] == "provider-comparison", packet)
    assert_condition(import_payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, import_payload)
    assert_condition(import_payload["review_status"] == "completed_from_chat_review", import_payload)
    assert_condition(import_payload["overall_decision"] == "approve_for_narrow_probe_with_brevity_constraint", import_payload)


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
    assert_condition(payload["scope"] == "english_provider_comparison_review_import_only", payload)
    assert_condition(payload["human_review_imported"] is True, payload)
    assert_condition(payload["narrow_probe_approved"] is True, payload)
    assert_condition(payload["exact_as_written_approval"] is False, payload)
    assert_condition(payload["brevity_constraint_required"] is True, payload)
    assert_condition(payload["comparison_grounding_required"] is True, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    imported = read_json(GENERATED_FILES["imported_review_summary"])
    approved = read_json(GENERATED_FILES["approved_with_constraints"])
    requirements = read_json(GENERATED_FILES["narrow_probe_requirements"])
    constraints = read_json(GENERATED_FILES["candidate_response_constraints"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["review_import_only"] is True, summary)
    assert_condition(summary["human_review_imported"] is True, summary)
    assert_condition(summary["selected_review_item"] == "provider-comparison", summary)
    assert_condition(summary["imported_review_decision"] == "approve_for_narrow_probe_with_brevity_constraint", summary)
    assert_condition(summary["narrow_probe_approved"] is True, summary)
    assert_condition(summary["exact_as_written_approval"] is False, summary)
    assert_condition(summary["brevity_constraint_required"] is True, summary)
    assert_condition(summary["comparison_grounding_required"] is True, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is False, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(imported["overall_decision"] == "approve_for_narrow_probe_with_brevity_constraint", imported)
    assert_condition("not approved as exact wording" in imported["decision_interpretation"].lower(), imported)
    assert_condition(approved["review_item"] == "provider-comparison", approved)
    assert_condition(approved["approved_for_narrow_probe"] is True, approved)
    assert_condition(approved["approved_as_exact_response_text"] is False, approved)
    assert_condition(requirements["requirements"]["comparison_target_required"] is True, requirements)
    assert_condition(requirements["requirements"]["generic_provider_or_terms_comparison_allowed"] is False, requirements)
    assert_condition(requirements["requirements"]["payment_details_request_allowed"] is False, requirements)
    assert_condition("no payment details needed." in constraints["example_brevity_edit"].lower(), constraints)
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
        "prod-076",
        "english provider-comparison review import",
        "approve for narrow probe with brevity constraint",
        "not approved as exact wording",
        "comparison target required",
        "no payment details needed",
        "review html created: `false`",
        "prod-077-english-provider-comparison-narrow-probe-design",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "classifier behavior changed: `false`",
        "retrieval enabled: `false`",
        "production runtime promotion allowed: `false`",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_sources()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
