#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053B-compact-english-psychology-layer-review"
SOURCE_CHECKPOINT_ID = "PROD-053A-english-sales-psychology-deep-dive"
LANGUAGE_LANE_CHECKPOINT_ID = "PROD-052-language-lane-review-separation"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
LANGUAGE_LANE_DIR = ROOT / "research" / "experiments" / "generated" / LANGUAGE_LANE_CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_053b_compact_english_psychology_layer_review.py",
    "runner": ROOT / "scripts" / "run_prod_053b_compact_english_psychology_layer_review.py",
    "validator": ROOT / "scripts" / "validate_prod_053b_compact_english_psychology_layer_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_053B_COMPACT_ENGLISH_PSYCHOLOGY_LAYER_REVIEW.md",
}

SOURCE_FILES = {
    "prod_053a_result": SOURCE_DIR / "result.json",
    "prod_053a_candidates": SOURCE_DIR / "compact_candidate_rules.json",
    "prod_053a_deferred": SOURCE_DIR / "rejected_or_deferred_tactics.json",
    "prod_052_english_items": LANGUAGE_LANE_DIR / "english_spoken_review_items.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "compact_policy": OUT_DIR / "compact_english_policy_rules.json",
    "candidate_review": OUT_DIR / "candidate_rule_review.json",
    "current_case_audit": OUT_DIR / "current_english_case_policy_audit.json",
    "rejected_or_deferred_review": OUT_DIR / "rejected_or_deferred_tactics_review.json",
    "review_html": OUT_DIR / "prod_053b_compact_english_policy_review.html",
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

REQUIRED_POLICY_RULE_IDS = {
    "en_response_001_answer_then_continue",
    "en_response_002_plain_relief",
    "en_response_003_mirror_only_for_repair",
    "en_response_004_one_small_decision",
    "en_response_005_friction_not_personality",
    "en_response_006_autonomy_visible",
    "en_response_007_trust_gap_specific",
    "en_response_008_stop_after_question",
}

FORBIDDEN_SUBSTRINGS = [
    "data/private",
    "runtime_promoted\": true",
    "provider_calls_made\": true",
    "llm_used\": true",
    "german_exact_phrase_promotion_allowed\": true",
    "false scarcity allowed",
    "hidden emotion diagnosis allowed",
    "commitment trap allowed",
]


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


def validate_source_files() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    source_result = read_json(SOURCE_FILES["prod_053a_result"])
    assert_condition(source_result.get("validation", {}).get("passed") is True, "PROD-053A must be valid before PROD-053B")


def run_runner() -> None:
    completed = subprocess.run(
        [sys.executable, str(REQUIRED_FILES["runner"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")


def validate_result() -> dict[str, Any]:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["language_lane_checkpoint_id"] == LANGUAGE_LANE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["source_candidate_rule_count"] == 8, summary)
    assert_condition(summary["accepted_rule_count"] == 8, summary)
    assert_condition(summary["compact_policy_rule_count"] == 8, summary)
    assert_condition(summary["current_english_case_count"] == 4, summary)
    assert_condition(summary["current_english_cases_requiring_prod_053c_rewrite"] >= 2, summary)
    assert_condition(summary["english_only_review"] is True, summary)
    assert_condition(summary["prod_053c_ready"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_compact_policy(result: dict[str, Any]) -> None:
    policy_items = read_json(GENERATED_FILES["compact_policy"])["items"]
    candidate_ids = {
        item["rule_id"]
        for item in read_json(SOURCE_FILES["prod_053a_candidates"])["items"]
    }
    policy_ids = {item["policy_rule_id"] for item in policy_items}
    assert_condition(REQUIRED_POLICY_RULE_IDS == policy_ids, sorted(REQUIRED_POLICY_RULE_IDS - policy_ids))
    assert_condition(len(policy_items) == result["summary"]["compact_policy_rule_count"], policy_items)
    for item in policy_items:
        assert_condition(item["language"] == "en", item)
        assert_condition(item["deterministic"] is True, item)
        assert_condition(item["runtime_cost"] == "low", item)
        assert_condition(item["runtime_promoted"] is False, item)
        assert_condition(item["review_status"] in {"accepted_for_prod_053c", "accepted_with_constraint_for_prod_053c"}, item)
        assert_condition(item["source_candidate_rule_ids"], item)
        assert_condition(set(item["source_candidate_rule_ids"]).issubset(candidate_ids), item)
        assert_condition(item["runtime_instruction"].strip(), item)
        assert_condition(item["blocked_shape"].strip(), item)


def validate_candidate_review() -> None:
    review_items = read_json(GENERATED_FILES["candidate_review"])["items"]
    assert_condition(len(review_items) == 8, review_items)
    for item in review_items:
        assert_condition(item["decision"] in {"accept", "accept_with_constraint"}, item)
        assert_condition(item["runtime_promoted"] is False, item)
        assert_condition(item["exact_phrase_change_allowed"] is False, item)
        assert_condition(item["prod_053c_use"].strip(), item)
    constrained = [item for item in review_items if item["decision"] == "accept_with_constraint"]
    assert_condition(constrained, "at least one candidate rule should be constrained rather than blindly accepted")


def validate_current_case_audit() -> None:
    audit = read_json(GENERATED_FILES["current_case_audit"])
    items = audit["items"]
    assert_condition(audit["language"] == "en", audit)
    assert_condition(len(items) == 4, items)
    issue_ids = {issue for item in items for issue in item["policy_issues"]}
    assert_condition("live_turn_too_long" in issue_ids, issue_ids)
    for item in items:
        assert_condition(item["language"] == "en", item)
        assert_condition(item["runtime_response_changed"] is False, item)
        assert_condition(item["prod_053c_rewrite_decision"] in {"carry_forward", "rewrite_candidate"}, item)
        assert_condition("manager or spouse" not in item["policy_shape_suggestion"].lower(), item)
        if item["sales_difficulty"] in {"stakeholder-review", "partner-review"}:
            response_lower = item["current_agent_response"].lower()
            has_category_echo = any(token in response_lower for token in ["manager", "spouse", "boss", "partner"])
            assert_condition(("customer_category_echo" in item["policy_issues"]) == has_category_echo, item)
            assert_condition(("relief_needs_commitment_wording" in item["policy_issues"]) == ("commitment" not in response_lower), item)


def validate_deferred_tactics_review() -> None:
    items = read_json(GENERATED_FILES["rejected_or_deferred_review"])["items"]
    assert_condition(len(items) >= 6, items)
    for item in items:
        assert_condition(item["prod_053b_decision"] in {"keep_rejected", "keep_deferred"}, item)
        assert_condition(item["allowed_in_compact_policy"] is False, item)


def validate_docs_and_payload_text() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    html_text = GENERATED_FILES["review_html"].read_text(encoding="utf-8")
    combined = "\n".join([doc_text, report_text, html_text, json.dumps(read_json(GENERATED_FILES["result"]), sort_keys=True)])
    lowered = combined.lower().replace("\\", "/")
    for marker in [
        "prod-053b",
        "prod-053a",
        "prod-053c",
        "english-only",
        "no runtime behavior",
        "no german exact phrase",
        "no llm",
        "no provider",
    ]:
        assert_condition(marker in lowered, f"missing marker: {marker}")
    for forbidden in FORBIDDEN_SUBSTRINGS:
        assert_condition(forbidden not in lowered, forbidden)


def main() -> None:
    validate_required_files()
    validate_source_files()
    run_runner()
    validate_required_files()
    validate_generated_files()
    result = validate_result()
    validate_compact_policy(result)
    validate_candidate_review()
    validate_current_case_audit()
    validate_deferred_tactics_review()
    validate_docs_and_payload_text()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
