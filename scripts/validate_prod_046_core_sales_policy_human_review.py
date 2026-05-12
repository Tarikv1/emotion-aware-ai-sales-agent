#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_046_core_sales_policy_human_review.py",
    "runner": ROOT / "scripts" / "run_prod_046_core_sales_policy_human_review.py",
    "validator": ROOT / "scripts" / "validate_prod_046_core_sales_policy_human_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_046_CORE_SALES_POLICY_HUMAN_REVIEW.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "human_review_packet": OUT_DIR / "human_review_packet.json",
    "english_findings": OUT_DIR / "english_response_quality_findings.json",
    "german_findings": OUT_DIR / "german_response_quality_findings.json",
    "call_control_findings": OUT_DIR / "call_control_findings.json",
    "campaign_field_findings": OUT_DIR / "campaign_field_findings.json",
    "recommended_next_actions": OUT_DIR / "recommended_next_actions.json",
    "review_html": OUT_DIR / "prod_046_review.html",
    "prod_045_result": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
    "prod_046a_result": ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json",
    "prod_046b_result": ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json",
    "prod_046c_result": ROOT / "research" / "experiments" / "generated" / "PROD-046C-german-campaign-field-interpolation-guard" / "result.json",
    "prod_046d_result": ROOT / "research" / "experiments" / "generated" / "PROD-046D-german-source-informed-wording-quality-guard" / "result.json",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
    "uses_exact_transcript_text",
    "uses_source_transcript_sequence",
    "uses_dataset_specific_phrasing",
    "generated_synthetic_conversations",
    "final_native_german_approval_claimed",
]

REQUIRED_CLASSIFICATION_KEYS = {
    "accepted_for_regression",
    "accepted_with_human_review_needed",
    "revise_wording_later",
    "revise_call_control_later",
    "needs_campaign_field_validator",
    "blocked_for_voice",
    "blocked_for_public_demo",
    "blocked_for_real_customer_use",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_source_results() -> None:
    for key in ("prod_045_result", "prod_046a_result", "prod_046b_result", "prod_046c_result", "prod_046d_result"):
        payload = read_json(REQUIRED_FILES[key])
        assert_condition(payload.get("validation", {}).get("passed") is True, f"{key} must have validation.passed=true")


def validate_result_summary() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["next_checkpoint_recommended"] == "PROD-047-campaign-profile-contract-validator", result)
    for field in (
        "prod_045_result_validation_passed",
        "prod_046a_result_validation_passed",
        "prod_046b_result_validation_passed",
        "prod_046c_result_validation_passed",
        "prod_046d_result_validation_passed",
        "policy_surface_accepted_for_offline_regression_evidence",
        "policy_surface_accepted_for_internal_product_review",
        "policy_surface_blocked_from_voice_demo_customer_use",
        "ready_for_campaign_profile_validator_next",
        "review_only_checkpoint",
    ):
        assert_condition(summary[field] is True, f"{field} must be true")
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    assert_condition(summary["english_reviewed_response_count"] > 0, summary)
    assert_condition(summary["german_reviewed_response_count"] > 0, summary)
    assert_condition(summary["accepted_with_human_review_needed_count"] > 0, summary)
    assert_condition(summary["revise_wording_later_count"] > 0, summary)
    assert_condition(summary["revise_call_control_later_count"] > 0, summary)
    assert_condition(summary["needs_campaign_field_validator_count"] > 0, summary)
    assert_condition(summary["call_control_finding_count"] > 0, summary)
    assert_condition(summary["campaign_field_finding_count"] > 0, summary)
    return summary


def validate_findings() -> None:
    for key in ("english_findings", "german_findings"):
        items = read_json(REQUIRED_FILES[key])["items"]
        assert_condition(items, f"{key} must not be empty")
        for item in items:
            classifications = item["classifications"]
            assert_condition(REQUIRED_CLASSIFICATION_KEYS <= set(classifications), item)
            assert_condition(classifications["accepted_for_regression"] is True, item)
            assert_condition(classifications["blocked_for_voice"] is True, item)
            assert_condition(classifications["blocked_for_public_demo"] is True, item)
            assert_condition(classifications["blocked_for_real_customer_use"] is True, item)
            assert_condition(isinstance(item.get("review_notes"), list) and item["review_notes"], item)
    german = read_json(REQUIRED_FILES["german_findings"])["items"]
    assert_condition(all(item["classifications"]["accepted_with_human_review_needed"] for item in german), "all German findings need human review")
    assert_condition(any("verkaufsteil" in item["agent_response"].lower() for item in german), "support/cancellation Verkaufsteil risk must be visible")


def validate_review_packets() -> None:
    packet = read_json(REQUIRED_FILES["human_review_packet"])
    assert_condition(packet["review_boundary"]["runtime_behavior_changed"] is False, packet)
    assert_condition(packet["review_boundary"]["final_native_german_approval_claimed"] is False, packet)
    assert_condition(packet["summary"]["policy_surface_blocked_from_voice_demo_customer_use"] is True, packet)
    call_control = read_json(REQUIRED_FILES["call_control_findings"])["items"]
    campaign = read_json(REQUIRED_FILES["campaign_field_findings"])["items"]
    actions = read_json(REQUIRED_FILES["recommended_next_actions"])["items"]
    assert_condition(call_control, "call-control findings required")
    assert_condition(campaign, "campaign-field findings required")
    assert_condition(actions and actions[0]["recommended_checkpoint"] == "PROD-047-campaign-profile-contract-validator", actions)
    assert_condition(any("bridge-then-continue" in item["recommended_future_change"] for item in call_control), call_control)
    assert_condition(any("contract validator" in item["required_future_guard"].lower() for item in campaign), campaign)


def validate_docs() -> None:
    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8").lower()
    html = REQUIRED_FILES["review_html"].read_text(encoding="utf-8").lower()
    roadmap = (ROOT / "docs" / "thesis" / "ROADMAP.md").read_text(encoding="utf-8").lower()
    commands = (ROOT / "docs" / "product" / "COMMANDS.md").read_text(encoding="utf-8").lower()
    index = (ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md").read_text(encoding="utf-8").lower()
    methodology = (ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md").read_text(encoding="utf-8").lower()
    decision = (ROOT / "docs" / "thesis" / "DECISION_LOG.md").read_text(encoding="utf-8").lower()
    for text in (doc, report, html):
        assert_condition("accepted for offline regression evidence" in text, "missing offline regression status")
        assert_condition("blocked" in text and "voice" in text and "public demo" in text, "missing blocked status")
        assert_condition("native german" in text or "native-speaker" in text, "missing native German review caveat")
    assert_condition("prod-046-core-sales-policy-human-review" in roadmap, "roadmap missing PROD-046")
    assert_condition("run_prod_046_core_sales_policy_human_review" in commands, "commands missing runner")
    assert_condition("prod_046_core_sales_policy_human_review" in index, "checkpoint index missing doc")
    assert_condition("prod-046" in methodology and "human/product review" in methodology, "methodology log missing review entry")
    assert_condition("core sales-policy surface" in decision and "offline regression" in decision, "decision log missing PROD-046 decision")


def main() -> None:
    validate_required_files()
    validate_source_results()
    summary = validate_result_summary()
    validate_findings()
    validate_review_packets()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
