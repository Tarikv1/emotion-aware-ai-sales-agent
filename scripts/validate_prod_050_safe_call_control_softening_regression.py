#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-050-safe-call-control-softening-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_050_safe_call_control_softening_regression.py",
    "runner": ROOT / "scripts" / "run_prod_050_safe_call_control_softening_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_050_safe_call_control_softening_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_050_SAFE_CALL_CONTROL_SOFTENING_REGRESSION.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "cases": OUT_DIR / "softening_regression_cases.json",
    "results": OUT_DIR / "softening_regression_results.json",
    "boundary_results": OUT_DIR / "protected_boundary_results.json",
    "change_summary": OUT_DIR / "proposed_runtime_change_summary.json",
    "review_html": OUT_DIR / "prod_050_review.html",
}

SOURCE_FILES = {
    "prod_049_result": ROOT / "research" / "experiments" / "generated" / "PROD-049-safe-end-call-bridge-continue-review" / "result.json",
    "prod_049_matrix": ROOT / "research" / "experiments" / "generated" / "PROD-049-safe-end-call-bridge-continue-review" / "bridge_continue_candidate_matrix.json",
    "prod_048c_result": ROOT / "research" / "experiments" / "generated" / "PROD-048C-german-wording-feedback-patch" / "result.json",
    "prod_047_result": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046_result": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
}

SELECTED_DIFFICULTIES = {
    "price-first-direct",
    "written-info-request",
    "stakeholder-review",
    "partner-review",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "call_control_behavior_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
]

PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\-\(\) ]{7,}\d)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


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


def validate_required_files() -> None:
    missing = [rel(path) for path in [*REQUIRED_FILES.values(), *SOURCE_FILES.values()] if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_sources() -> None:
    for key, path in SOURCE_FILES.items():
        payload = read_json(path)
        if key.endswith("_result"):
            assert_condition(payload.get("validation", {}).get("passed") is True, f"{key} must pass")
    matrix = read_json(SOURCE_FILES["prod_049_matrix"])["items"]
    candidates = [item for item in matrix if item["bridge_then_continue_candidate"] is True]
    assert_condition(len(candidates) == 22, f"expected 22 source candidates, got {len(candidates)}")
    candidate_keys = {(item["finding_id"], item["case_id"]) for item in candidates}
    assert_condition(len(candidate_keys) == len(candidates), "source candidates must be unique")
    assert_condition({item["sales_difficulty"] for item in candidates} == SELECTED_DIFFICULTIES, candidates)
    assert_condition(all(item["current_call_control"] == "end-call" for item in candidates), candidates)


def validate_result() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["source_checkpoint_id"] == "PROD-049-safe-end-call-bridge-continue-review", summary)
    assert_condition(summary["source_bridge_candidate_count"] == 22, summary)
    assert_condition(summary["softening_regression_case_count"] == 22, summary)
    assert_condition(summary["softening_regression_pass_count"] == 22, summary)
    assert_condition(summary["softening_regression_fail_count"] == 0, summary)
    assert_condition(summary["selected_sales_difficulty_count"] == 4, summary)
    assert_condition(summary["protected_boundary_probe_count"] >= 9, summary)
    assert_condition(summary["protected_boundary_pass_count"] == summary["protected_boundary_probe_count"], summary)
    assert_condition(summary["current_runtime_unchanged_count"] == 22, summary)
    assert_condition(summary["proposed_bridge_then_continue_count"] == 22, summary)
    assert_condition(summary["current_safe_answer_preserved_count"] == 22, summary)
    assert_condition(summary["proposed_response_text_changed_count"] == 22, summary)
    assert_condition(summary["low_pressure_continuation_prompt_count"] == 22, summary)
    assert_condition(summary["terminal_closing_phrase_in_proposed_count"] == 0, summary)
    assert_condition(summary["pressure_violation_count"] == 0, summary)
    assert_condition(summary["unsupported_claim_violation_count"] == 0, summary)
    assert_condition(summary["payment_collection_violation_count"] == 0, summary)
    assert_condition(summary["contract_signing_violation_count"] == 0, summary)
    assert_condition(summary["support_cancellation_do_not_call_softened"] is False, summary)
    assert_condition(summary["runtime_change_recommended"] is True, summary)
    assert_condition(summary["runtime_change_applied_by_this_checkpoint"] is False, summary)
    assert_condition(summary["response_text_change_recommended"] is True, summary)
    assert_condition(summary["call_control_definition_update_required"] is True, summary)
    assert_condition(summary["recommended_next_checkpoint"] == "PROD-051-safe-call-control-runtime-update", summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_softening_cases_and_results() -> None:
    cases = read_json(REQUIRED_FILES["cases"])["items"]
    results = read_json(REQUIRED_FILES["results"])["items"]
    assert_condition(len(cases) == 22, len(cases))
    assert_condition(len(results) == 22, len(results))
    case_ids = {item["case_id"] for item in cases}
    result_ids = {item["case_id"] for item in results}
    assert_condition(len(case_ids) == len(cases), "case ids must be unique")
    assert_condition(len(result_ids) == len(results), "result ids must be unique")
    assert_condition(case_ids == result_ids, "case/result ids must match")
    assert_condition({item["sales_difficulty"] for item in results}.issubset(SELECTED_DIFFICULTIES), results)
    for item in results:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["current_runtime_decision"]["call_control"] == "end-call", item)
        assert_condition(item["proposed_runtime_decision"]["call_control"] == "bridge-then-continue", item)
        assert_condition(item["proposed_runtime_decision"]["sales_difficulty"] == item["current_runtime_decision"]["sales_difficulty"], item)
        assert_condition(item["proposed_runtime_decision"]["agent_response"] != item["current_runtime_decision"]["agent_response"], item)
        assert_condition(item["proposed_runtime_decision"]["response_text_change_applied"] is True, item)
        assert_condition(item["current_answered_or_acknowledged"] is True, item)
        assert_condition(item["answered_or_acknowledged_before_continue"] is True, item)
        assert_condition(item["current_safe_answer_preserved"] is True, item)
        assert_condition(item["proposed_response_text_changed"] is True, item)
        assert_condition(item["low_pressure_continuation_prompt"] is True, item)
        assert_condition(item["terminal_closing_phrase_in_proposed"] is False, item)
        assert_condition(item["pressure_violation"] is False, item)
        assert_condition(item["payment_collection_violation"] is False, item)
        assert_condition(item["contract_signing_violation"] is False, item)
        assert_condition(item["unsupported_claim_violation"] is False, item)
        assert_condition(item["runtime_change_applied"] is False, item)


def validate_protected_boundaries() -> None:
    payload = read_json(REQUIRED_FILES["boundary_results"])
    items = payload["items"]
    assert_condition(len(items) >= 9, items)
    expected = {
        "prod-050-support-boundary": "transfer-or-escalate",
        "prod-050-cancellation-boundary": "transfer-or-escalate",
        "prod-050-do-not-call-boundary": "end-call",
        "prod-050-human-request-boundary": "transfer-or-escalate",
        "prod-050-email-only-boundary": "end-call",
        "prod-050-payment-safety-boundary": "end-call",
        "prod-050-scam-safety-boundary": "end-call",
        "prod-050-sale-ready-boundary": "close-and-log-sale-ready",
        "prod-050-callback-boundary": "end-call",
    }
    by_case = {item["case_id"]: item for item in items}
    for case_id, expected_call_control in expected.items():
        item = by_case[case_id]
        assert_condition(item["passed"] is True, item)
        assert_condition(item["current_runtime_decision"]["call_control"] == expected_call_control, item)
        assert_condition(item["proposed_runtime_decision"]["call_control"] == expected_call_control, item)
        assert_condition(item["proposed_runtime_decision"]["call_control"] != "bridge-then-continue", item)


def validate_change_summary_and_docs() -> None:
    change_summary = read_json(REQUIRED_FILES["change_summary"])
    assert_condition(change_summary["runtime_change_applied_by_this_checkpoint"] is False, change_summary)
    assert_condition(change_summary["response_text_change_recommended"] is True, change_summary)
    assert_condition(change_summary["call_control_definition_update_required"] is True, change_summary)
    assert_condition(change_summary["recommended_next_checkpoint"] == "PROD-051-safe-call-control-runtime-update", change_summary)
    assert_condition(sorted(change_summary["selected_sales_difficulties"]) == sorted(SELECTED_DIFFICULTIES), change_summary)
    assert_condition(change_summary["protected_boundaries_preserved"] is True, change_summary)

    for key in ("doc", "report", "review_html"):
        text = REQUIRED_FILES[key].read_text(encoding="utf-8")
        lowered = text.lower()
        assert_condition("prod-050" in lowered, f"{key} missing PROD-050")
        assert_condition("bridge-then-continue" in lowered, f"{key} missing bridge marker")
        assert_condition("runtime behavior changed" in lowered, f"{key} missing runtime boundary")
        assert_condition("provider calls made" in lowered, f"{key} missing provider boundary")
        assert_condition("production runtime promotion allowed" in lowered, f"{key} missing promotion boundary")
        assert_condition(not PHONE_PATTERN.search(text), f"phone-like string found in {key}")
        assert_condition(not EMAIL_PATTERN.search(text), f"email-like string found in {key}")


def main() -> None:
    validate_required_files()
    validate_sources()
    run_runner()
    validate_required_files()
    result = validate_result()
    validate_softening_cases_and_results()
    validate_protected_boundaries()
    validate_change_summary_and_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
