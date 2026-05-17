#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity"
SOURCE_CHECKPOINT_ID = "PROD-096-english-next-step-process-clarity-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-098-english-recommendation-roleplay-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-097-english-customer-move-remaining-slice-selection-after-process-clarity.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py",
    "runner": ROOT / "scripts" / "run_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py",
    "validator": ROOT / "scripts" / "validate_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py",
    "source_validator": ROOT / "scripts" / "validate_prod_096_english_next_step_process_clarity_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_097_ENGLISH_CUSTOMER_MOVE_REMAINING_SLICE_SELECTION_AFTER_PROCESS_CLARITY.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_process_regression": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "process_clarity_regression_cases.json",
    "source_adjacent_controls": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "adjacent_control_cases.json",
    "source_stable_guard": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "stable_english_guard_summary.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "remaining_subtype_selection": OUT_DIR / "remaining_subtype_selection.json",
    "review_packet": OUT_DIR / "review_packet.json",
    "review_examples": OUT_DIR / "review_examples.json",
    "review_state_template": OUT_DIR / "review_state_template.json",
    "review_html": OUT_DIR / "review.html",
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
    process_regression = read_json(SOURCE_FILES["source_process_regression"])
    adjacent_controls = read_json(SOURCE_FILES["source_adjacent_controls"])
    stable_guard = read_json(SOURCE_FILES["source_stable_guard"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(process_regression["failure_count"] == 0, process_regression)
    assert_condition(adjacent_controls["failure_count"] == 0, adjacent_controls)
    assert_condition(stable_guard["passed"] is True, stable_guard)


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
    assert_condition(payload["scope"] == "english_customer_move_remaining_slice_selection_after_process_clarity", payload)
    assert_condition(payload["selection_only"] is True, payload)
    assert_condition(payload["selected_next_slice"] == "recommendation_roleplay_boundary", payload)
    assert_condition(payload["selected_remaining_case_id"] == "prod-081-recommendation-02", payload)
    assert_condition(payload["review_html_created"] is True, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is True, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    selection = read_json(GENERATED_FILES["remaining_subtype_selection"])
    packet = read_json(GENERATED_FILES["review_packet"])
    examples = read_json(GENERATED_FILES["review_examples"])
    state = read_json(GENERATED_FILES["review_state_template"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    html = GENERATED_FILES["review_html"].read_text(encoding="utf-8").lower()
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["review_packet_created"] is True, result)
    assert_condition(summary["selection_only"] is True, summary)
    assert_condition(summary["selected_next_slice"] == "recommendation_roleplay_boundary", summary)
    assert_condition(summary["selected_remaining_case_id"] == "prod-081-recommendation-02", summary)
    assert_condition(summary["review_html_created"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is True, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(selection["decision"] == "select_recommendation_roleplay_review_next", selection)
    assert_condition(selection["selected_requires_human_review_before_probe"] is True, selection)
    assert_condition(packet["review_required"] is True, packet)
    assert_condition(packet["review_type"] == "recommendation_roleplay_boundary", packet)
    assert_condition(examples["example_count"] >= 6, examples)
    assert_condition(state["checkpoint_id"] == CHECKPOINT_ID, state)
    assert_condition(all(item["decision"] == "pending" for item in state["items"]), state)
    for marker in ["what you are reviewing", "approve", "needs edit", "reject", "export review", "import review"]:
        assert_condition(marker in html, f"review HTML missing marker {marker!r}")
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
        "prod-097",
        "english customer-move remaining slice selection after process clarity",
        "recommendation_roleplay_boundary",
        "selected remaining case: `prod-081-recommendation-02`",
        "requires human review before next checkpoint: `true`",
        "review html created: `true`",
        "prod-098-english-recommendation-roleplay-review-import",
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
