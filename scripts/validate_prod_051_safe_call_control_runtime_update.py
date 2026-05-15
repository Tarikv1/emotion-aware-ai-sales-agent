#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-051-safe-call-control-runtime-update"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_051_safe_call_control_runtime_update.py",
    "runner": ROOT / "scripts" / "run_prod_051_safe_call_control_runtime_update.py",
    "validator": ROOT / "scripts" / "validate_prod_051_safe_call_control_runtime_update.py",
    "doc": ROOT / "docs" / "product" / "PROD_051_SAFE_CALL_CONTROL_RUNTIME_UPDATE.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "runtime_results": OUT_DIR / "runtime_update_results.json",
    "naturalness_audit": OUT_DIR / "naturalness_audit_results.json",
    "protected_boundaries": OUT_DIR / "protected_boundary_results.json",
    "before_after": OUT_DIR / "before_after_naturalness.json",
    "review_html": OUT_DIR / "prod_051_review.html",
}

SOURCE_FILES = {
    "prod_050_result": ROOT / "research" / "experiments" / "generated" / "PROD-050-safe-call-control-softening-regression" / "result.json",
    "prod_050_cases": ROOT / "research" / "experiments" / "generated" / "PROD-050-safe-call-control-softening-regression" / "softening_regression_cases.json",
    "prod_050_results": ROOT / "research" / "experiments" / "generated" / "PROD-050-safe-call-control-softening-regression" / "softening_regression_results.json",
    "prod_049_result": ROOT / "research" / "experiments" / "generated" / "PROD-049-safe-end-call-bridge-continue-review" / "result.json",
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
        if key.endswith("_result"):
            payload = read_json(path)
            assert_condition(payload.get("validation", {}).get("passed") is True, f"{key} must pass")
    source_cases = read_json(SOURCE_FILES["prod_050_cases"])["items"]
    source_results = read_json(SOURCE_FILES["prod_050_results"])["items"]
    assert_condition(len(source_cases) == 22, len(source_cases))
    assert_condition(len(source_results) == 22, len(source_results))
    assert_condition({item["sales_difficulty"] for item in source_results} == SELECTED_DIFFICULTIES, source_results)
    for item in source_results:
        assert_condition(item["proposed_runtime_decision"]["call_control"] == "bridge-then-continue", item)
        assert_condition(item["proposed_response_text_changed"] is True, item)
        assert_condition(item["low_pressure_continuation_prompt"] is True, item)
        assert_condition(item["terminal_closing_phrase_in_proposed"] is False, item)


def validate_result() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["source_checkpoint_id"] == "PROD-050-safe-call-control-softening-regression", summary)
    assert_condition(summary["runtime_update_case_count"] == 22, summary)
    assert_condition(summary["runtime_update_pass_count"] == 22, summary)
    assert_condition(summary["runtime_update_fail_count"] == 0, summary)
    assert_condition(summary["live_bridge_then_continue_count"] == 22, summary)
    assert_condition(summary["live_answer_and_continue_action_count"] == 22, summary)
    assert_condition(summary["response_matches_prod_050_proposal_count"] >= 20, summary)
    assert_condition(summary["response_matches_later_reviewed_runtime_text_count"] == 2, summary)
    assert_condition(summary["response_matches_prod_050_or_later_reviewed_count"] == 22, summary)
    assert_condition(summary["naturalness_case_count"] == 22, summary)
    assert_condition(summary["naturalness_pass_count"] == 22, summary)
    assert_condition(summary["naturalness_fail_count"] == 0, summary)
    assert_condition(summary["naturalness_improvement_count"] == 22, summary)
    assert_condition(summary["naturalness_average_score"] >= 0.9, summary)
    assert_condition(summary["protected_boundary_probe_count"] >= 9, summary)
    assert_condition(summary["protected_boundary_pass_count"] == summary["protected_boundary_probe_count"], summary)
    assert_condition(summary["protected_boundary_softened_count"] == 0, summary)
    assert_condition(summary["pressure_violation_count"] == 0, summary)
    assert_condition(summary["unsupported_claim_violation_count"] == 0, summary)
    assert_condition(summary["payment_collection_violation_count"] == 0, summary)
    assert_condition(summary["contract_signing_violation_count"] == 0, summary)
    assert_condition(summary["internal_jargon_violation_count"] == 0, summary)
    assert_condition(summary["terminal_closing_phrase_count"] == 0, summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["call_control_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_runtime_results() -> None:
    items = read_json(REQUIRED_FILES["runtime_results"])["items"]
    assert_condition(len(items) == 22, len(items))
    assert_condition(len({item["case_id"] for item in items}) == 22, "runtime cases must be unique")
    for item in items:
        decision = item["live_runtime_decision"]
        assert_condition(item["passed"] is True, item)
        assert_condition(decision["sales_difficulty"] in SELECTED_DIFFICULTIES, item)
        assert_condition(decision["call_control"] == "bridge-then-continue", item)
        assert_condition(decision["next_action"] == "answer-and-continue", item)
        assert_condition(decision["response_mode"] == "fast-response", item)
        assert_condition(decision["bridge_response"] is None, item)
        assert_condition("campaign-knowledge-lookup" not in decision["background_modules"], item)
        assert_condition(
            item["matches_prod_050_proposal"] is True or item["matches_later_reviewed_runtime_text"] is True,
            item,
        )
        if item["matches_later_reviewed_runtime_text"]:
            assert_condition(item["later_review_checkpoint_id"] == "PROD-053E-english-runtime-wording-patch", item)


def validate_naturalness() -> None:
    items = read_json(REQUIRED_FILES["naturalness_audit"])["items"]
    assert_condition(len(items) == 22, len(items))
    for item in items:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["score"] >= 0.9, item)
        checks = item["checks"]
        for check_name in (
            "direct_answer_or_acknowledgement",
            "optional_low_pressure_continuation",
            "no_terminal_closing_phrase",
            "no_internal_jargon",
            "spoken_sentence_shape",
            "customer_move_fit",
            "language_specific_naturalness",
            "no_pressure_payment_contract_or_unsupported_claim",
        ):
            assert_condition(checks[check_name]["passed"] is True, item)

    before_after = read_json(REQUIRED_FILES["before_after"])["items"]
    assert_condition(len(before_after) == 22, before_after)
    for item in before_after:
        assert_condition(item["score_delta"] > 0, item)
        assert_condition(item["changed_surface"] == "response_text_and_call_control", item)


def validate_protected_boundaries() -> None:
    items = read_json(REQUIRED_FILES["protected_boundaries"])["items"]
    assert_condition(len(items) >= 9, items)
    for item in items:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["live_runtime_decision"]["call_control"] == item["expected_call_control"], item)
        assert_condition(item["live_runtime_decision"]["call_control"] != "bridge-then-continue", item)


def validate_docs() -> None:
    for key in ("doc", "report", "review_html"):
        text = REQUIRED_FILES[key].read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in (
            "prod-051",
            "naturalness",
            "bridge-then-continue",
            "answer-and-continue",
            "runtime behavior changed",
            "provider calls made",
            "production runtime promotion allowed",
        ):
            assert_condition(marker in lowered, f"{key} missing {marker}")
        assert_condition(not PHONE_PATTERN.search(text), f"phone-like string found in {key}")
        assert_condition(not EMAIL_PATTERN.search(text), f"email-like string found in {key}")


def main() -> None:
    validate_required_files()
    validate_sources()
    run_runner()
    validate_required_files()
    result = validate_result()
    validate_runtime_results()
    validate_naturalness()
    validate_protected_boundaries()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
