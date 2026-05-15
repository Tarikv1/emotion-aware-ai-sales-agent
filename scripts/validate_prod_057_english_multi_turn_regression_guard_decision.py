#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-057-english-multi-turn-regression-guard-decision"
SOURCE_CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-057-english-multi-turn-regression-guard-decision.json"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_057_english_multi_turn_regression_guard_decision.py",
    "runner": ROOT / "scripts" / "run_prod_057_english_multi_turn_regression_guard_decision.py",
    "validator": ROOT / "scripts" / "validate_prod_057_english_multi_turn_regression_guard_decision.py",
    "stable_guard_validator": ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py",
    "doc": ROOT / "docs" / "product" / "PROD_057_ENGLISH_MULTI_TURN_REGRESSION_GUARD_DECISION.md",
    "stable_guard_doc": ROOT / "docs" / "product" / "ENGLISH_MULTI_TURN_REGRESSION_GUARD.md",
    "setup_checker": ROOT / "scripts" / "check_setup.py",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_validator": ROOT / "scripts" / "validate_prod_056_english_post_patch_multi_turn_regression.py",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "guard_decision": OUT_DIR / "guard_decision.json",
    "guard_readiness_checks": OUT_DIR / "guard_readiness_checks.json",
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

PROMOTION_BLOCKS = {
    "native_german_review",
    "voice_playback_quality",
    "retrieval_default",
    "public_demo_use",
    "real_customer_use",
    "payment_collection",
    "contract_signing",
    "legal_compliance_review",
    "private_data_or_provider_use",
}


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
    source = read_json(SOURCE_FILES["source_result"])
    summary = source["summary"]
    assert_condition(source["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source)
    assert_condition(source["validation"]["passed"] is True, source)
    assert_condition(source["validation"]["regression_gate_passed"] is True, source)
    assert_condition(summary["source_promoted_response_count"] == 26, summary)
    assert_condition(summary["runtime_second_turn_case_count"] == 10, summary)
    assert_condition(summary["callback_scheduling_case_count"] == 1, summary)
    assert_condition(summary["terminal_boundary_case_count"] == 15, summary)
    assert_condition(summary["blocking_finding_count"] == 0, summary)
    assert_condition(summary["permanent_regression_guard_recommended"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false in source")


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


def validate_stable_guard_command() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["stable_guard_validator"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"stable guard failed stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(SOURCE_CHECKPOINT_ID in completed.stdout, completed.stdout)


def validate_setup_checker_registration() -> None:
    text = REQUIRED_FILES["setup_checker"].read_text(encoding="utf-8")
    for marker in [
        "file.docs_product_english_multi_turn_regression_guard",
        "docs/product/ENGLISH_MULTI_TURN_REGRESSION_GUARD.md",
        "file.scripts_validate_english_multi_turn_regression_guard",
        "scripts/validate_english_multi_turn_regression_guard.py",
    ]:
        assert_condition(marker in text, f"setup checker missing marker: {marker}")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    criteria = payload["decision_criteria"]
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["candidate_guard_command"] == "python scripts\\validate_english_multi_turn_regression_guard.py", payload)
    assert_condition(len(criteria) >= 8, criteria)
    required_criteria = {
        "prod_056_regression_gate_passed",
        "full_promoted_english_surface_covered",
        "zero_blocking_findings",
        "stable_guard_command_exists",
        "stable_guard_command_passes",
        "setup_checker_requires_guard",
        "runtime_and_response_text_unchanged",
        "promotion_boundaries_remain_blocked",
    }
    assert_condition(required_criteria <= {item["criterion_id"] for item in criteria}, criteria)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    decision = read_json(GENERATED_FILES["guard_decision"])
    readiness = read_json(GENERATED_FILES["guard_readiness_checks"])["items"]
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["guard_decision_passed"] is True, result)
    assert_condition(summary["guard_status"] == "adopted", summary)
    assert_condition(summary["stable_guard_command"] == "python scripts\\validate_english_multi_turn_regression_guard.py", summary)
    assert_condition(summary["source_promoted_response_count"] == 26, summary)
    assert_condition(summary["source_blocking_finding_count"] == 0, summary)
    assert_condition(summary["readiness_check_count"] == len(readiness), summary)
    assert_condition(summary["readiness_failure_count"] == 0, summary)
    assert_condition(summary["runtime_promotion_allowed"] is False, summary)
    assert_condition(summary["english_multi_turn_guard_adopted"] is True, summary)
    assert_condition(set(summary["promotion_blocks_remaining"]) == PROMOTION_BLOCKS, summary)
    assert_condition(summary["next_checkpoint"] == "PROD-058-english-runtime-promotion-blocker-inventory", summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(decision["decision"] == "adopt_prod_056_as_permanent_english_multi_turn_guard", decision)
    assert_condition(decision["scope"]["language"] == "en", decision)
    assert_condition(decision["scope"]["runtime_path"] == "deterministic_realtime_turns", decision)
    assert_condition(decision["requires_before_runtime_changes"] is True, decision)
    assert_condition(set(decision["not_sufficient_for"]) == PROMOTION_BLOCKS, decision)
    for item in readiness:
        assert_condition(item["passed"] is True, item)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    guard_doc_text = REQUIRED_FILES["stable_guard_doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    commands_text = REQUIRED_FILES["commands"].read_text(encoding="utf-8")
    index_text = REQUIRED_FILES["checkpoint_index"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{guard_doc_text}\n{report_text}\n{commands_text}\n{index_text}".lower()
    for marker in [
        "prod-057",
        "prod-056",
        "english multi-turn regression guard",
        "python scripts\\validate_english_multi_turn_regression_guard.py",
        "guard status: `adopted`",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "production runtime promotion allowed: `false`",
        "no provider",
        "no llm",
        "no private data",
        "prod-058",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_source_files()
    run_runner()
    validate_generated_files()
    validate_stable_guard_command()
    validate_setup_checker_registration()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
