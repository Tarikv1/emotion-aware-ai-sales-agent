#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-054-english-multi-turn-naturalness-stress-review"
SOURCE_CHECKPOINT_ID = "PROD-053E-english-runtime-wording-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-054-english-multi-turn-naturalness-stress-review.json"


REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_054_english_multi_turn_naturalness_stress_review.py",
    "runner": ROOT / "scripts" / "run_prod_054_english_multi_turn_naturalness_stress_review.py",
    "validator": ROOT / "scripts" / "validate_prod_054_english_multi_turn_naturalness_stress_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_054_ENGLISH_MULTI_TURN_NATURALNESS_STRESS_REVIEW.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": SOURCE_DIR / "result.json",
    "promoted_runtime_responses": SOURCE_DIR / "promoted_runtime_responses.json",
    "skipped_runtime_candidates": SOURCE_DIR / "skipped_runtime_candidates.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "runtime_second_turn_reviews": OUT_DIR / "runtime_second_turn_reviews.json",
    "terminal_boundary_reviews": OUT_DIR / "terminal_boundary_reviews.json",
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
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "german_exact_phrase_promotion_allowed",
    "german_naturalness_claimed",
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
    source_result = read_json(SOURCE_FILES["source_result"])
    summary = source_result["summary"]
    assert_condition(source_result["validation"]["passed"] is True, source_result)
    assert_condition(summary["promoted_response_count"] == 26, summary)
    assert_condition(summary["skipped_runtime_candidate_count"] == 3, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)


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
    source_items = read_json(SOURCE_FILES["promoted_runtime_responses"])["items"]
    source_ids = {item["case_id"] for item in source_items}
    cases = payload["cases"]
    case_source_ids = {case["source_case_id"] for case in cases}
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(len(cases) == 26, len(cases))
    assert_condition(case_source_ids == source_ids, sorted(source_ids ^ case_source_ids))
    assert_condition(sum(1 for case in cases if case["next_turn_mode"] == "runtime_second_turn") == 10, cases)
    assert_condition(sum(1 for case in cases if case["next_turn_mode"] == "terminal_boundary") == 16, cases)
    for case in cases:
        assert_condition(case["language"] == "en", case)
        assert_condition(case["source_agent_response"], case)
        if case["next_turn_mode"] == "runtime_second_turn":
            expected = case["expected_second_turn"]
            assert_condition(case["follow_up_customer_utterance"], case)
            assert_condition(expected["sales_difficulty"], case)
            assert_condition(expected["next_action"], case)
            assert_condition(expected["call_control"], case)
            assert_condition(expected["response_must_include_any"], case)
        else:
            assert_condition(case["follow_up_customer_utterance"] is None, case)
            assert_condition(case["expected_second_turn"] is None, case)
            assert_condition(case["terminal_boundary"]["no_second_agent_turn_expected"] is True, case)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    second_turns = read_json(GENERATED_FILES["runtime_second_turn_reviews"])["items"]
    terminal = read_json(GENERATED_FILES["terminal_boundary_reviews"])["items"]
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["source_promoted_response_count"] == 26, summary)
    assert_condition(summary["runtime_second_turn_case_count"] == 10, summary)
    assert_condition(summary["terminal_boundary_case_count"] == 16, summary)
    assert_condition(summary["stress_gate_passed"] is False, summary)
    assert_condition(summary["blocking_finding_count"] >= 4, summary)
    assert_condition(summary["runtime_promotion_allowed"] is False, summary)
    assert_condition(summary["needs_followup_checkpoint"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    assert_condition(len(second_turns) == summary["runtime_second_turn_case_count"], second_turns)
    assert_condition(len(terminal) == summary["terminal_boundary_case_count"], terminal)
    assert_condition(any(not item["stress_gates_passed"] for item in second_turns), second_turns)
    assert_condition(any(not item["terminal_boundary_passed"] for item in terminal), terminal)
    assert_condition(
        {"prod-053c-product-detail-lookup", "prod-053c-price-objection", "prod-053c-unknown-runtime-signal"}.issubset(
            set(summary["blocking_case_ids"])
        ),
        summary,
    )


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}".lower()
    for marker in [
        "prod-054",
        "prod-053e",
        "multi-turn",
        "26",
        "10",
        "terminal",
        "blocking finding",
        "no provider",
        "no llm",
        "no private data",
        "runtime promotion allowed: `false`",
        "prod-055",
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
