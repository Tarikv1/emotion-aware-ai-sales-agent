#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046A-german-naturalized-policy-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_046a_german_naturalized_policy_regression.py",
    "runner": ROOT / "scripts" / "run_prod_046a_german_naturalized_policy_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_046a_german_naturalized_policy_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_046A_GERMAN_NATURALIZED_POLICY_REGRESSION.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "cases": OUT_DIR / "german_regression_cases.json",
    "results": OUT_DIR / "german_regression_results.json",
    "false_cases": OUT_DIR / "german_false_positive_cases.json",
    "false_results": OUT_DIR / "german_false_positive_results.json",
    "review_data": OUT_DIR / "german_policy_review_data.json",
    "review_html": OUT_DIR / "german_policy_review.html",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
}

REQUIRED_MOVES = {
    "price_first",
    "who_are_you",
    "send_info",
    "email_only",
    "scam_or_card_fear",
    "payment_safety_fear",
    "support_issue",
    "cancellation_request",
    "technical_question",
    "security_review",
    "coverage_confusion",
    "sensitive_healthcare_concern",
    "existing_provider",
    "needs_manager_approval",
    "needs_spouse_or_partner_input",
    "sale_ready_interest",
    "not_interested",
    "hostile_rejection",
    "callback_request",
    "skeptical_proof_request",
    "product_detail_lookup",
    "scheduling_confirmation",
}

BOUNDARY_FALSE_FIELDS = [
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "uses_exact_transcript_text",
    "uses_source_transcript_sequence",
    "uses_dataset_specific_phrasing",
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


def validate_existence() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_cases() -> None:
    cases = read_json(REQUIRED_FILES["cases"])
    assert_condition(len(cases) >= len(REQUIRED_MOVES) * 3, f"not enough German positive cases: {len(cases)}")
    by_move: dict[str, list[dict[str, Any]]] = {}
    utf8_german_case_count = 0
    for case in cases:
        by_move.setdefault(case["customer_move_id"], []).append(case)
        assert_condition(case["example_type"] == "synthetic_naturalized_de_regression_case", case)
        assert_condition(case["source_quote"] is False, case)
        assert_condition(case["from_single_transcript"] is False, case)
        assert_condition(case["translation_mode"] == "intent_equivalent_not_literal", case)
        assert_condition(case["campaign"]["language"] == "de", case)
        utf8_german_case_count += int(any(ch in case["customer_input"]["transcript"] for ch in "äöüÄÖÜß"))
    missing = REQUIRED_MOVES - set(by_move)
    assert_condition(not missing, f"missing German move cases: {missing}")
    for move_id in REQUIRED_MOVES:
        assert_condition(len(by_move[move_id]) >= 3, f"{move_id} has fewer than 3 variants")
    assert_condition(utf8_german_case_count >= 30, f"not enough UTF-8 German naturalized cases: {utf8_german_case_count}")


def validate_result_and_outputs() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["german_positive_case_count"] >= 66, summary)
    assert_condition(summary["german_positive_fail_count"] == 0, summary)
    assert_condition(summary["german_false_positive_case_count"] >= 6, summary)
    assert_condition(summary["german_false_positive_fail_count"] == 0, summary)
    assert_condition(summary["english_prod_045_regression_still_passed"] is True, summary)
    assert_condition(summary["german_unknown_runtime_signal_count"] == 0, summary)
    assert_condition(summary["german_generic_clarification_count"] == 0, summary)
    assert_condition(summary["german_response_language_mismatch_count"] == 0, summary)
    assert_condition(summary["german_phrase_triggers_added"] is True, summary)
    assert_condition(summary["german_localized_responses_changed"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_results() -> None:
    results = read_json(REQUIRED_FILES["results"])["results"]
    false_results = read_json(REQUIRED_FILES["false_results"])["results"]
    for item in results:
        decision = item["runtime_decision"]
        assert_condition(item["passed"] is True, item)
        assert_condition(decision["response_language"] == "de", item)
        assert_condition(decision["sales_difficulty"] != "unknown-runtime-signal", item)
        assert_condition(item["generic_german_clarification"] is False, item)
        assert_condition(not item["response_language_mismatch"], item)
        assert_condition("Darf ich kurz" not in decision["agent_response"], item)
    for item in false_results:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["runtime_decision"]["response_language"] == "de", item)
    priorities = {item["case_id"]: item["runtime_decision"]["sales_difficulty"] for item in false_results}
    assert_condition(priorities["de-false-no-cancel"] != "cancellation-route", priorities)
    assert_condition(priorities["de-false-identity-over-scam"] == "identity-repair", priorities)
    assert_condition(priorities["de-false-price-over-support"] == "price-first-direct", priorities)
    assert_condition(priorities["de-false-security-negated"] != "security-review-route", priorities)
    assert_condition(priorities["de-false-payment-safe-boundary"] == "payment-safety-boundary", priorities)
    assert_condition(priorities["de-false-price-over-provider"] == "price-first-direct", priorities)


def validate_docs_and_leakage() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    for marker in ("prod-046a", "intent-equivalent", "german", "retrieval enabled: `false`"):
        assert_condition(marker in doc_text, f"doc missing {marker}")
    html_text = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    for marker in ("german positive regression cases", "german false-positive cases", "review limitations"):
        assert_condition(marker in html_text, f"review HTML missing {marker}")
    for key in ("report", "review_html", "review_data", "cases", "results", "false_cases", "false_results"):
        path = REQUIRED_FILES[key]
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert_condition("raw transcript" not in lowered, f"raw transcript claim found in {key}")
        assert_condition("source_quote\": true" not in lowered, f"source quote true in {key}")
        assert_condition(not PHONE_PATTERN.search(text), f"phone-like string found in {key}")
        assert_condition(not EMAIL_PATTERN.search(text), f"email-like string found in {key}")


def main() -> None:
    validate_existence()
    prod_045_result = read_json(REQUIRED_FILES["prod_045_result"])
    assert_condition(prod_045_result["validation"]["passed"] is True, "PROD-045 must be passing before PROD-046A")
    run_runner()
    validate_existence()
    result = validate_result_and_outputs()
    validate_cases()
    validate_results()
    validate_docs_and_leakage()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
