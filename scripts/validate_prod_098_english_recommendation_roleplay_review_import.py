#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-098-english-recommendation-roleplay-review-import"
SOURCE_CHECKPOINT_ID = "PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity"
NEXT_CHECKPOINT_ID = "PROD-099-english-recommendation-roleplay-narrow-policy-probe"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
IMPORT_DIR = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID
IMPORT_FILE = IMPORT_DIR / "prod_097_recommendation_roleplay_review_from_chat.json"
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-098-english-recommendation-roleplay-review-import.json"

FINAL_EXAMPLE_3 = "Based on [customer pain], I would recommend $59. If budget is the main concern, start with $29 and upgrade later if you need to."
FINAL_EXAMPLE_5 = "I cannot decide for you, but I can show what each plan covers and why one may fit your needs better."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_098_english_recommendation_roleplay_review_import.py",
    "runner": ROOT / "scripts" / "run_prod_098_english_recommendation_roleplay_review_import.py",
    "validator": ROOT / "scripts" / "validate_prod_098_english_recommendation_roleplay_review_import.py",
    "source_validator": ROOT / "scripts" / "validate_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py",
    "doc": ROOT / "docs" / "product" / "PROD_098_ENGLISH_RECOMMENDATION_ROLEPLAY_REVIEW_IMPORT.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "import_file": IMPORT_FILE,
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_packet": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "review_packet.json",
    "source_examples": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "review_examples.json",
    "source_review_html": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "review.html",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "imported_review_summary": OUT_DIR / "imported_review_summary.json",
    "wording_edits": OUT_DIR / "wording_edits.json",
    "approved_candidate_packet": OUT_DIR / "approved_recommendation_roleplay_candidate_packet.json",
    "narrow_policy_probe_readiness": OUT_DIR / "narrow_policy_probe_readiness.json",
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
    examples = read_json(SOURCE_FILES["source_examples"])
    import_payload = read_json(IMPORT_FILE)
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["review_html_created"] is True, result["summary"])
    assert_condition(result["summary"]["requires_human_review_before_next_checkpoint"] is True, result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(packet["review_required"] is True, packet)
    assert_condition(packet["review_type"] == "recommendation_roleplay_boundary", packet)
    assert_condition(examples["review_type"] == "recommendation_roleplay_boundary", examples)
    assert_condition(examples["example_count"] >= 6, examples)
    assert_condition(import_payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, import_payload)
    assert_condition(import_payload["review_status"] == "completed_from_chat_review", import_payload)
    assert_condition(import_payload["overall_decision"] == "approve_for_policy_probe_with_two_wording_edits", import_payload)
    assert_condition(import_payload["narrow_policy_probe_approved_after_required_edits"] is True, import_payload)
    assert_condition(import_payload["required_wording_edits"]["prod-097-direct-recommendation"]["final_candidate_response"] == FINAL_EXAMPLE_3, import_payload)
    assert_condition(import_payload["required_wording_edits"]["prod-097-decide-for-me-control"]["final_candidate_response"] == FINAL_EXAMPLE_5, import_payload)


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
    assert_condition(payload["scope"] == "english_recommendation_roleplay_review_import_only", payload)
    assert_condition(payload["human_review_imported"] is True, payload)
    assert_condition(payload["imported_review_decision"] == "approve_for_policy_probe_with_two_wording_edits", payload)
    assert_condition(payload["narrow_policy_probe_approved_after_required_edits"] is True, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    imported = read_json(GENERATED_FILES["imported_review_summary"])
    edits = read_json(GENERATED_FILES["wording_edits"])
    candidates = read_json(GENERATED_FILES["approved_candidate_packet"])
    readiness = read_json(GENERATED_FILES["narrow_policy_probe_readiness"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["review_imported"] is True, result)
    assert_condition(summary["review_import_only"] is True, summary)
    assert_condition(summary["human_review_imported"] is True, summary)
    assert_condition(summary["selected_review_item"] == "recommendation_roleplay_boundary", summary)
    assert_condition(summary["imported_review_decision"] == "approve_for_policy_probe_with_two_wording_edits", summary)
    assert_condition(summary["approved_example_count"] == 7, summary)
    assert_condition(summary["required_edit_example_count"] == 2, summary)
    assert_condition(summary["narrow_policy_probe_approved_after_required_edits"] is True, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["runtime_candidate_promoted"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is False, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(imported["overall_decision"] == summary["imported_review_decision"], imported)
    assert_condition(imported["edited_example_ids"] == ["prod-097-direct-recommendation", "prod-097-decide-for-me-control"], imported)
    assert_condition(edits["edits"]["prod-097-direct-recommendation"]["final_candidate_response"] == FINAL_EXAMPLE_3, edits)
    assert_condition(edits["edits"]["prod-097-decide-for-me-control"]["final_candidate_response"] == FINAL_EXAMPLE_5, edits)
    assert_condition(candidates["checkpoint_id"] == CHECKPOINT_ID, candidates)
    assert_condition(candidates["review_item"] == "recommendation_roleplay_boundary", candidates)
    assert_condition(candidates["narrow_policy_probe_candidate"] is True, candidates)
    assert_condition(candidates["runtime_candidate_promoted"] is False, candidates)
    assert_condition(len(candidates["examples"]) == 7, candidates)
    example_map = {item["example_id"]: item for item in candidates["examples"]}
    assert_condition(example_map["prod-097-direct-recommendation"]["final_candidate_response"] == FINAL_EXAMPLE_3, example_map)
    assert_condition(example_map["prod-097-decide-for-me-control"]["final_candidate_response"] == FINAL_EXAMPLE_5, example_map)
    assert_condition("if you need to" in example_map["prod-097-direct-recommendation"]["final_candidate_response"], example_map)
    assert_condition(", but i can show" in example_map["prod-097-decide-for-me-control"]["final_candidate_response"].lower(), example_map)
    assert_condition(readiness["narrow_policy_probe_approved_after_required_edits"] is True, readiness)
    assert_condition(readiness["runtime_patch_allowed"] is False, readiness)
    assert_condition(readiness["requires_customer_facts_for_recommendation"] is True, readiness)
    assert_condition(readiness["requires_agency_preservation"] is True, readiness)
    assert_condition(readiness["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, readiness)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)
    assert_condition(evidence["source_review_html_preserved"] is True, evidence)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    commands_text = REQUIRED_FILES["commands"].read_text(encoding="utf-8")
    index_text = REQUIRED_FILES["checkpoint_index"].read_text(encoding="utf-8")
    roadmap_text = REQUIRED_FILES["roadmap"].read_text(encoding="utf-8")
    methodology_text = REQUIRED_FILES["methodology_log"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}\n{commands_text}\n{index_text}\n{roadmap_text}\n{methodology_text}".lower()
    for marker in [
        "prod-098",
        "english recommendation roleplay review import",
        "approve for policy probe with two wording edits",
        "if you need to",
        "but i can show",
        "review html created: `false`",
        "narrow policy probe approved after required edits: `true`",
        "runtime candidate promoted: `false`",
        "prod-099-english-recommendation-roleplay-narrow-policy-probe",
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
