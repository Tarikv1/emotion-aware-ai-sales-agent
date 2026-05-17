#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-081-english-unknown-runtime-signal-subtype-inventory"
SOURCE_CHECKPOINT_ID = "PROD-080-english-customer-move-remaining-slice-selection"
NEXT_CHECKPOINT_ID = "PROD-082-english-guided-option-selection-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-081-english-unknown-runtime-signal-subtype-inventory.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_081_english_unknown_runtime_signal_subtype_inventory.py",
    "runner": ROOT / "scripts" / "run_prod_081_english_unknown_runtime_signal_subtype_inventory.py",
    "validator": ROOT / "scripts" / "validate_prod_081_english_unknown_runtime_signal_subtype_inventory.py",
    "source_validator": ROOT / "scripts" / "validate_prod_080_english_customer_move_remaining_slice_selection.py",
    "doc": ROOT / "docs" / "product" / "PROD_081_ENGLISH_UNKNOWN_RUNTIME_SIGNAL_SUBTYPE_INVENTORY.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_selection": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "remaining_slice_selection.json",
    "source_snapshot": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "current_classifier_reachability_snapshot.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "unknown_signal_probe_results": OUT_DIR / "unknown_signal_probe_results.json",
    "unknown_runtime_signal_subtype_inventory": OUT_DIR / "unknown_runtime_signal_subtype_inventory.json",
    "protected_boundary_control_results": OUT_DIR / "protected_boundary_control_results.json",
    "slice_decision": OUT_DIR / "slice_decision.json",
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
    selection = read_json(SOURCE_FILES["source_selection"])
    snapshot = read_json(SOURCE_FILES["source_snapshot"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["selected_next_slice"] == "unknown_runtime_signal_subtypes", result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(selection["selected_next_slice"] == "unknown_runtime_signal_subtypes", selection)
    assert_condition(selection["protected_boundary_controls_required"] is True, selection)
    assert_condition("unknown-runtime-signal" in snapshot["reachable_sales_difficulties"], snapshot)
    assert_condition(snapshot["unreachable_localized_response_types"] == [], snapshot)


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
    assert_condition(payload["scope"] == "english_unknown_runtime_signal_subtype_inventory_only", payload)
    assert_condition(payload["inventory_only"] is True, payload)
    assert_condition(payload["selected_source_slice"] == "unknown_runtime_signal_subtypes", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(payload["recommended_next_checkpoint_requires_human_review"] is True, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    probes = read_json(GENERATED_FILES["unknown_signal_probe_results"])
    inventory = read_json(GENERATED_FILES["unknown_runtime_signal_subtype_inventory"])
    controls = read_json(GENERATED_FILES["protected_boundary_control_results"])
    decision = read_json(GENERATED_FILES["slice_decision"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["inventory_passed"] is True, result)
    assert_condition(summary["inventory_only"] is True, summary)
    assert_condition(summary["source_validator_passed"] is True, summary)
    assert_condition(summary["selected_source_slice"] == "unknown_runtime_signal_subtypes", summary)
    assert_condition(summary["unknown_subtype_count"] >= 5, summary)
    assert_condition(summary["unknown_runtime_signal_case_count"] >= 8, summary)
    assert_condition(summary["protected_boundary_control_count"] >= 8, summary)
    assert_condition(summary["failed_protected_boundary_control_count"] == 0, summary)
    assert_condition(summary["selected_next_subtype"] == "guided_option_selection_candidate", summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    subtype_ids = {item["subtype_id"] for item in inventory["subtypes"]}
    assert_condition("guided_option_selection_candidate" in subtype_ids, subtype_ids)
    assert_condition("next_step_clarity" in subtype_ids, subtype_ids)
    assert_condition("recommendation_request" in subtype_ids, subtype_ids)
    assert_condition("deferral_or_choose_later" in subtype_ids, subtype_ids)
    assert_condition("plan_option_difference" in subtype_ids, subtype_ids)
    selected = [item for item in inventory["subtypes"] if item["subtype_id"] == "guided_option_selection_candidate"][0]
    assert_condition(selected["requires_human_review_before_probe"] is True, selected)
    assert_condition(selected["runtime_patch_allowed"] is False, selected)
    assert_condition(selected["why_selected"].startswith("Tarik explicitly raised"), selected)

    assert_condition(probes["unknown_runtime_signal_case_count"] >= 8, probes)
    assert_condition(probes["unknown_runtime_signal_case_count"] == len(probes["unknown_cases"]), probes)
    assert_condition(all(item["observed_sales_difficulty"] == "unknown-runtime-signal" for item in probes["unknown_cases"]), probes)
    assert_condition(controls["failed_control_count"] == 0, controls)
    assert_condition({item["expected_sales_difficulty"] for item in controls["items"]} >= {"payment-safety-boundary", "coverage-boundary-route", "healthcare-boundary-route", "do-not-call", "support-route"}, controls)
    assert_condition(decision["decision"] == "select_guided_option_selection_review_next", decision)
    assert_condition(decision["selected_next_subtype"] == "guided_option_selection_candidate", decision)
    assert_condition(decision["runtime_patch_allowed"] is False, decision)
    assert_condition(decision["classifier_change_allowed"] is False, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
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
        "prod-081",
        "english unknown runtime signal subtype inventory",
        "unknown_runtime_signal_subtypes",
        "guided_option_selection_candidate",
        "two real options",
        "neither",
        "not now",
        "explain the difference",
        "protected boundary controls",
        "recommended next checkpoint requires human review: `true`",
        "review html created: `false`",
        "prod-082-english-guided-option-selection-review",
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
    validate_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
