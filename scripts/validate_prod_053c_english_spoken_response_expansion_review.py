#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053C-english-spoken-response-expansion-review"
SOURCE_CHECKPOINT_ID = "PROD-053B-compact-english-psychology-layer-review"
LANGUAGE_LANE_CHECKPOINT_ID = "PROD-052-language-lane-review-separation"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_053c_english_spoken_response_expansion_review.py",
    "runner": ROOT / "scripts" / "run_prod_053c_english_spoken_response_expansion_review.py",
    "validator": ROOT / "scripts" / "validate_prod_053c_english_spoken_response_expansion_review.py",
    "doc": ROOT / "docs" / "product" / "PROD_053C_ENGLISH_SPOKEN_RESPONSE_EXPANSION_REVIEW.md",
}

SOURCE_FILES = {
    "prod_053b_result": SOURCE_DIR / "result.json",
    "prod_053b_compact_policy": SOURCE_DIR / "compact_english_policy_rules.json",
    "prod_053b_case_audit": SOURCE_DIR / "current_english_case_policy_audit.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "review_items": OUT_DIR / "english_spoken_response_review_items.json",
    "scope_decisions": OUT_DIR / "review_scope_decisions.json",
    "policy_audit": OUT_DIR / "policy_application_audit.json",
    "review_html": OUT_DIR / "prod_053c_english_spoken_response_review.html",
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

EXPECTED_POLICY_RULE_IDS = {
    "en_response_001_answer_then_continue",
    "en_response_002_plain_relief",
    "en_response_003_mirror_only_for_repair",
    "en_response_004_one_small_decision",
    "en_response_005_friction_not_personality",
    "en_response_006_autonomy_visible",
    "en_response_007_trust_gap_specific",
    "en_response_008_stop_after_question",
}

EXPECTED_CARRY_FORWARD_EXCLUSIONS = {
    "prod-045-price-first",
    "prod-045-send-info",
}

EXPECTED_FLAGGED_INCLUSIONS = {
    "prod-045-manager",
    "prod-045-spouse",
}

FORBIDDEN_REVIEW_ITEM_SUBSTRINGS = [
    "lang\": \"de\"",
    "language\": \"de\"",
    "runtime_response_changed\": true",
    "provider_calls_made\": true",
    "llm_used\": true",
    "german_exact_phrase_promotion_allowed\": true",
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
    source_result = read_json(SOURCE_FILES["prod_053b_result"])
    source_summary = source_result["summary"]
    assert_condition(source_result["validation"]["passed"] is True, "PROD-053B must pass before PROD-053C")
    assert_condition(source_summary["prod_053c_ready"] is True, source_summary)
    assert_condition(source_summary["compact_policy_rule_count"] == 8, source_summary)
    assert_condition(source_summary["current_english_cases_requiring_prod_053c_rewrite"] == 2, source_summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(source_summary[field] is False, f"source {field} must remain false")


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


def validate_result() -> dict[str, Any]:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["language_lane_checkpoint_id"] == LANGUAGE_LANE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["english_only_review"] is True, summary)
    assert_condition(summary["source_compact_policy_rule_count"] == 8, summary)
    assert_condition(summary["carry_forward_excluded_count"] == 2, summary)
    assert_condition(summary["flagged_rewrite_included_count"] == 2, summary)
    assert_condition(summary["unreviewed_runtime_response_count"] >= 24, summary)
    assert_condition(summary["review_item_count"] >= 26, summary)
    assert_condition(summary["all_review_items_ready_for_tarik"] is True, summary)
    assert_condition(set(summary["approved_carry_forward_case_ids"]) == EXPECTED_CARRY_FORWARD_EXCLUSIONS, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_scope_decisions() -> None:
    scope = read_json(GENERATED_FILES["scope_decisions"])
    excluded_ids = {item["case_id"] for item in scope["excluded_already_approved_items"]}
    included_ids = {item["case_id"] for item in scope["included_flagged_rewrite_items"]}
    assert_condition(excluded_ids == EXPECTED_CARRY_FORWARD_EXCLUSIONS, scope)
    assert_condition(included_ids == EXPECTED_FLAGGED_INCLUSIONS, scope)
    assert_condition(scope["english_only_review"] is True, scope)
    assert_condition(scope["german_exact_phrase_review_allowed"] is False, scope)
    assert_condition(scope["runtime_behavior_changed"] is False, scope)
    assert_condition(scope["response_text_behavior_changed"] is False, scope)


def validate_review_items(result: dict[str, Any]) -> None:
    payload = read_json(GENERATED_FILES["review_items"])
    items = payload["items"]
    policy_rule_ids = {item["policy_rule_id"] for item in read_json(SOURCE_FILES["prod_053b_compact_policy"])["items"]}
    assert_condition(policy_rule_ids == EXPECTED_POLICY_RULE_IDS, policy_rule_ids)
    assert_condition(len(items) == result["summary"]["review_item_count"], len(items))
    item_ids = {item["case_id"] for item in items}
    assert_condition(EXPECTED_FLAGGED_INCLUSIONS.issubset(item_ids), item_ids)
    assert_condition(item_ids.isdisjoint(EXPECTED_CARRY_FORWARD_EXCLUSIONS), item_ids)

    source_scopes = {item["source_scope"] for item in items}
    assert_condition(
        source_scopes == {"flagged_prod_053b_rewrite", "unreviewed_runtime_response_surface"},
        source_scopes,
    )

    for item in items:
        assert_condition(item["language"] == "en", item)
        assert_condition(item["review_status"] == "ready_for_tarik_english_review", item)
        assert_condition(item["requires_tarik_review"] is True, item)
        assert_condition(item["exact_phrase_review_allowed"] is True, item)
        assert_condition(item["german_exact_phrase_review_allowed"] is False, item)
        assert_condition(item["runtime_response_changed"] is False, item)
        assert_condition(item["current_agent_response"].strip(), item)
        assert_condition(item["proposed_review_response"].strip(), item)
        assert_condition(set(item["applied_policy_rule_ids"]).issubset(policy_rule_ids), item)
        assert_condition(item["applied_policy_rule_ids"], item)
        if "?" in item["proposed_review_response"]:
            assert_condition(item["proposed_review_response"].rstrip().endswith("?"), item)

    for flagged_id in EXPECTED_FLAGGED_INCLUSIONS:
        item = next(candidate for candidate in items if candidate["case_id"] == flagged_id)
        proposed = item["proposed_review_response"].lower()
        assert_condition("no commitment today" in proposed, item)
        assert_condition("take a look" in proposed, item)
        assert_condition(not any(token in proposed for token in ["manager", "boss", "spouse", "partner"]), item)

    combined = json.dumps(payload, sort_keys=True)
    lowered = combined.lower()
    for forbidden in FORBIDDEN_REVIEW_ITEM_SUBSTRINGS:
        assert_condition(forbidden not in lowered, forbidden)


def validate_policy_audit(result: dict[str, Any]) -> None:
    audit = read_json(GENERATED_FILES["policy_audit"])
    items = audit["items"]
    assert_condition(audit["checkpoint_id"] == CHECKPOINT_ID, audit)
    assert_condition(len(items) == result["summary"]["review_item_count"], len(items))
    issue_ids = {issue for item in items for issue in item["policy_issues"]}
    assert_condition("live_turn_too_long" in issue_ids, issue_ids)
    assert_condition("internal_runtime_jargon" in issue_ids, issue_ids)
    for item in items:
        assert_condition(item["language"] == "en", item)
        assert_condition(item["runtime_response_changed"] is False, item)
        assert_condition(item["policy_rule_results"], item)


def validate_docs_and_html() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    html_text = GENERATED_FILES["review_html"].read_text(encoding="utf-8")
    combined = "\n".join([doc_text, report_text, html_text]).lower()
    for marker in [
        "prod-053c",
        "prod-053b",
        "english-only",
        "already-approved",
        "no runtime behavior",
        "no german exact phrase",
        "no llm",
        "no provider",
        "localstorage",
        "export json",
        "import json",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_source_files()
    run_runner()
    validate_required_files()
    validate_generated_files()
    result = validate_result()
    validate_scope_decisions()
    validate_review_items(result)
    validate_policy_audit(result)
    validate_docs_and_html()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
