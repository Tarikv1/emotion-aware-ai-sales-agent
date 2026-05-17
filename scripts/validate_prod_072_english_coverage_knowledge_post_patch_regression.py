#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-072-english-coverage-knowledge-post-patch-regression"
SOURCE_CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
STABLE_GUARD_SOURCE_CHECKPOINT_ID = "PROD-056-english-post-patch-multi-turn-regression"
VOICEMAIL_GUARD_SOURCE_CHECKPOINT_ID = "PROD-068-english-voicemail-post-patch-regression"
NEXT_CHECKPOINT_ID = "PROD-073-english-customer-move-classification-gate-decision"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-072-english-coverage-knowledge-post-patch-regression.json"
BOUNDARY_ROUTE = "coverage-boundary-route"
BOUNDARY_RESPONSE = "I should not give coverage advice. I can route this to the approved qualified reviewer path."
HEALTHCARE_RESPONSE = "I can't give medical advice, but I can send you to someone qualified."
PRICE_RESPONSE = "I do not have an approved exact price in this campaign, so I should not invent one. I can send approved pricing information and stop there."
PRODUCT_DETAIL_RESPONSE = "One moment. I will check the product details before I answer."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_072_english_coverage_knowledge_post_patch_regression.py",
    "runner": ROOT / "scripts" / "run_prod_072_english_coverage_knowledge_post_patch_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_072_english_coverage_knowledge_post_patch_regression.py",
    "source_validator": ROOT / "scripts" / "validate_prod_071_english_coverage_knowledge_runtime_patch.py",
    "stable_guard_validator": ROOT / "scripts" / "validate_english_multi_turn_regression_guard.py",
    "voicemail_guard_validator": ROOT / "scripts" / "validate_prod_068_english_voicemail_post_patch_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_072_ENGLISH_COVERAGE_KNOWLEDGE_POST_PATCH_REGRESSION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "patch_decision.json",
    "source_reviews": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "runtime_patch_reviews.json",
    "source_evidence": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "evidence_summary.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "coverage_boundary_regression_reviews": OUT_DIR / "coverage_boundary_regression_reviews.json",
    "adjacent_control_reviews": OUT_DIR / "adjacent_control_reviews.json",
    "voicemail_control_reviews": OUT_DIR / "voicemail_control_reviews.json",
    "post_patch_regression_decision": OUT_DIR / "post_patch_regression_decision.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "response_text_behavior_changed",
    "classifier_behavior_changed",
    "call_control_behavior_changed",
    "next_action_behavior_changed",
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


def validate_source_files() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    decision = read_json(SOURCE_FILES["source_decision"])
    reviews = read_json(SOURCE_FILES["source_reviews"])["items"]
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["runtime_patch_passed"] is True, result)
    assert_condition(result["validation"]["controls_preserved"] is True, result)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["classifier_behavior_changed"] is True, summary)
    assert_condition(summary["call_control_behavior_changed"] is True, summary)
    assert_condition(summary["next_action_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is False, summary)
    assert_condition(summary["patched_sales_difficulty"] == BOUNDARY_ROUTE, summary)
    assert_condition(summary["failed_runtime_patch_case_count"] == 0, summary)
    assert_condition(summary["recommended_next_checkpoint"] == CHECKPOINT_ID, summary)
    assert_condition(decision["decision"] == "english_coverage_knowledge_runtime_patch_applied", decision)
    assert_condition(decision["recommended_next_checkpoint"] == CHECKPOINT_ID, decision)
    assert_condition(len(reviews) == 6, reviews)
    assert_condition(all(item["passed"] for item in reviews), reviews)


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")
    review_html = OUT_DIR / "prod_072_review.html"
    assert_condition(not review_html.exists(), "PROD-072 must not create review HTML unless human review is required")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["stable_guard_source_checkpoint_id"] == STABLE_GUARD_SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["voicemail_guard_source_checkpoint_id"] == VOICEMAIL_GUARD_SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_coverage_knowledge_post_patch_regression_only", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["coverage_advice_allowed"] is False, payload)
    assert_condition(payload["coverage_fact_claims_allowed"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(len(payload["coverage_boundary_regression_cases"]) == 5, payload)
    assert_condition(len(payload["adjacent_control_cases"]) == 6, payload)
    assert_condition(len(payload["voicemail_control_cases"]) == 2, payload)


def runtime_decision_for(case: dict[str, Any]) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": case["case_id"],
            "customer_input": {
                "input_type": case["input_type"],
                "transcript": case["customer_turn"],
                "stage": case["stage"],
            },
        }
    )


def validate_runtime_surface_from_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(localized_response("en", BOUNDARY_ROUTE, None) == BOUNDARY_RESPONSE, "coverage response changed")
    assert_condition(localized_response("en", "healthcare-boundary-route", None) == HEALTHCARE_RESPONSE, "healthcare response changed")
    assert_condition(localized_response("en", "voicemail", None) == "", "English voicemail response must remain empty")

    for case in payload["coverage_boundary_regression_cases"]:
        decision = runtime_decision_for(case)
        assert_condition(decision["response_language"] == "en", decision)
        assert_condition(decision["sales_difficulty"] == BOUNDARY_ROUTE, decision)
        assert_condition(decision["selected_strategy"] == "rapport", decision)
        assert_condition(decision["interest_state"] == "needs-human", decision)
        assert_condition(decision["next_action"] == "escalate", decision)
        assert_condition(decision["call_control"] == "transfer-or-escalate", decision)
        assert_condition(decision["agent_response"] == BOUNDARY_RESPONSE, decision)

    for case in payload["adjacent_control_cases"]:
        decision = runtime_decision_for(case)
        expected = case["expected_runtime"]
        assert_condition(decision["sales_difficulty"] == expected["sales_difficulty"], decision)
        assert_condition(decision["selected_strategy"] == expected["selected_strategy"], decision)
        assert_condition(decision["next_action"] == expected["next_action"], decision)
        assert_condition(decision["call_control"] == expected["call_control"], decision)
        assert_condition(decision["agent_response"] == expected["agent_response"], decision)
        assert_condition(decision["sales_difficulty"] != BOUNDARY_ROUTE, decision)

    for case in payload["voicemail_control_cases"]:
        decision = runtime_decision_for(case)
        assert_condition(decision["sales_difficulty"] == "voicemail", decision)
        assert_condition(decision["selected_strategy"] == "rapport", decision)
        assert_condition(decision["next_action"] == "create-follow-up-task", decision)
        assert_condition(decision["call_control"] == "end-call", decision)
        assert_condition(decision["agent_response"] == "", decision)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    coverage_reviews = read_json(GENERATED_FILES["coverage_boundary_regression_reviews"])["items"]
    adjacent_reviews = read_json(GENERATED_FILES["adjacent_control_reviews"])["items"]
    voicemail_reviews = read_json(GENERATED_FILES["voicemail_control_reviews"])["items"]
    decision = read_json(GENERATED_FILES["post_patch_regression_decision"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["post_patch_regression_passed"] is True, result)
    assert_condition(result["validation"]["coverage_boundary_regression_passed"] is True, result)
    assert_condition(result["validation"]["adjacent_controls_preserved"] is True, result)
    assert_condition(result["validation"]["voicemail_controls_preserved"] is True, result)

    assert_condition(summary["source_validator_passed"] is True, summary)
    assert_condition(summary["stable_english_guard_passed"] is True, summary)
    assert_condition(summary["voicemail_guard_passed"] is True, summary)
    assert_condition(summary["coverage_boundary_regression_case_count"] == 5, summary)
    assert_condition(summary["adjacent_control_case_count"] == 6, summary)
    assert_condition(summary["voicemail_control_case_count"] == 2, summary)
    assert_condition(summary["failed_case_count"] == 0, summary)
    assert_condition(summary["coverage_advice_allowed"] is False, summary)
    assert_condition(summary["coverage_fact_claims_allowed"] is False, summary)
    assert_condition(summary["eligibility_claims_allowed"] is False, summary)
    assert_condition(summary["reimbursement_claims_allowed"] is False, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(decision["decision"] == "coverage_patch_post_regression_passed", decision)
    assert_condition(decision["runtime_patch_from_source_kept"] is True, decision)
    assert_condition(decision["new_runtime_change_in_prod_072"] is False, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(decision["production_runtime_promotion_allowed"] is False, decision)
    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)
    assert_condition(evidence["stable_guard_run"]["passed"] is True, evidence)
    assert_condition(evidence["voicemail_guard_run"]["passed"] is True, evidence)

    assert_condition(len(coverage_reviews) == 5, coverage_reviews)
    assert_condition(len(adjacent_reviews) == 6, adjacent_reviews)
    assert_condition(len(voicemail_reviews) == 2, voicemail_reviews)
    for item in coverage_reviews + adjacent_reviews + voicemail_reviews:
        assert_condition(item["passed"] is True, item)
        assert_condition(item["issue_codes"] == [], item)

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
        "prod-072",
        "english coverage knowledge post-patch regression",
        "prod-071",
        "prod-068",
        "prod-056",
        "coverage boundary regression cases: `5`",
        "adjacent control cases: `6`",
        "voicemail control cases: `2`",
        "stable english guard passed: `true`",
        "voicemail guard passed: `true`",
        "failed case count: `0`",
        "runtime behavior changed: `false`",
        "classifier behavior changed: `false`",
        "response text behavior changed: `false`",
        "coverage advice allowed: `false`",
        "no human review required",
        "review html created: `false`",
        "prod-073-english-customer-move-classification-gate-decision",
        "guided_option_selection",
        "future persuasion-tactics checkpoint",
        "production runtime promotion allowed: `false`",
        "provider",
        "private data",
        "retrieval",
        "voice playback",
        "german",
        "payment",
        "contract",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_source_files()
    validate_runtime_surface_from_case_file()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
