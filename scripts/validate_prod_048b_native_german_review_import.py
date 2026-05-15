#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048B-native-german-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
IMPORT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "imports"
    / CHECKPOINT_ID
    / "deutsche-telefonantworten-bewertung-1.json"
)

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_048b_native_german_review_import.py",
    "runner": ROOT / "scripts" / "run_prod_048b_native_german_review_import.py",
    "validator": ROOT / "scripts" / "validate_prod_048b_native_german_review_import.py",
    "doc": ROOT / "docs" / "product" / "PROD_048B_NATIVE_GERMAN_REVIEW_IMPORT.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "summary": OUT_DIR / "imported_reviewer_feedback_summary.json",
    "reviewed_items": OUT_DIR / "reviewed_items.json",
    "unreviewed_items": OUT_DIR / "unreviewed_items.json",
    "revision_candidates": OUT_DIR / "revision_candidates.json",
    "followup_review_plan": OUT_DIR / "followup_review_plan.json",
    "html": OUT_DIR / "reviewer_feedback_import.html",
}

DEPENDENCY_RESULTS = {
    "prod_048a": ROOT / "research" / "experiments" / "generated" / "PROD-048A-german-review-html-and-brevity-packet" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
}

BOUNDARY_FALSE_FIELDS = [
    "full_native_german_approval_claimed",
    "legal_compliance_claimed",
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(filled(item) for item in value)
    if isinstance(value, dict):
        return any(filled(item) for item in value.values())
    return bool(value)


def recompute_reviewed(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reviewed = []
    unreviewed = []
    for item in items:
        marker = {
            "ratings": item.get("ratings", {}),
            "safety_flags": item.get("safety_flags", []),
            "rewrite_suggestion": item.get("rewrite_suggestion", ""),
            "comment": item.get("comment", ""),
        }
        if filled(marker):
            reviewed.append(item)
        else:
            unreviewed.append(item)
    return reviewed, unreviewed


def validate_required_files() -> None:
    assert_condition(IMPORT_PATH.exists(), f"missing reviewer import JSON: {rel(IMPORT_PATH)}")
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_dependency_results() -> None:
    for key, path in DEPENDENCY_RESULTS.items():
        payload = read_json(path)
        assert_condition(payload.get("validation", {}).get("passed") is True, f"{key} validation must still pass")


def validate_import_summary(import_payload: dict[str, Any]) -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    feedback_summary = read_json(REQUIRED_FILES["summary"])
    reviewed_items = read_json(REQUIRED_FILES["reviewed_items"])["items"]
    unreviewed_items = read_json(REQUIRED_FILES["unreviewed_items"])["items"]

    source_items = import_payload.get("items", [])
    recomputed_reviewed, recomputed_unreviewed = recompute_reviewed(source_items)

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["reviewer_name_or_initials"] == "Diro", summary)
    assert_condition(summary["reviewer_native_german"] == "Ja", summary)
    assert_condition(summary["reviewer_region"] == "Basel", summary)
    assert_condition(summary["reviewer_date"] == "2026-05-12", summary)
    assert_condition(summary["reviewed_item_count"] == len(recomputed_reviewed), summary)
    assert_condition(summary["unreviewed_item_count"] == len(recomputed_unreviewed), summary)
    assert_condition(len(reviewed_items) == summary["reviewed_item_count"], reviewed_items)
    assert_condition(len(unreviewed_items) == summary["unreviewed_item_count"], unreviewed_items)
    assert_condition(summary["reported_checked_count"] != summary["reviewed_item_count"], summary)
    assert_condition(summary["blank_rows_counted_as_unreviewed"] is True, summary)
    assert_condition(summary["accepted_count"] >= 1, summary)
    assert_condition(summary["small_change_count"] >= 1, summary)
    assert_condition(summary["safety_or_impact_count"] >= 1, summary)
    assert_condition(summary["rejected_count"] == 0, summary)
    assert_condition(feedback_summary["recomputed_counts"]["reviewed_item_count"] == summary["reviewed_item_count"], feedback_summary)
    assert_condition(feedback_summary["input_export_shape"]["item_count"] == len(source_items), feedback_summary)
    assert_condition(feedback_summary["input_export_shape"]["current_grouped_packet_group_count"] < len(source_items), feedback_summary)
    return summary


def validate_revision_candidates() -> None:
    payload = read_json(REQUIRED_FILES["revision_candidates"])
    candidates = payload["items"]
    assert_condition(candidates, "revision candidates required")
    price_candidates = [item for item in candidates if item["topic"] == "Preisfrage"]
    assert_condition(price_candidates, candidates)
    price = price_candidates[0]
    assert_condition(price["runtime_change_allowed_now"] is False, price)
    assert_condition(price["requires_later_patch_checkpoint"] is True, price)
    assert_condition("Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat" in price["proposed_project_owned_revision"], price)
    assert_condition("Zahlung" not in price["proposed_project_owned_revision"], price)
    assert_condition("Vertragsabschluss" not in price["proposed_project_owned_revision"], price)
    assert_condition(price["reviewer_safety_flags"] == ["verkaufsdruck"], price)
    assert_condition("lenkt zu sehr" in price["reviewer_issue"], price)


def validate_followup_plan() -> None:
    plan = read_json(REQUIRED_FILES["followup_review_plan"])
    assert_condition(plan["recommendation"] == "ask_reviewer_to_continue_with_grouped_html", plan)
    assert_condition(plan["groups_accepted_from_current_feedback"], plan)
    assert_condition(plan["groups_requiring_focused_followup"], plan)
    assert_condition(plan["groups_still_completely_unreviewed"], plan)
    assert_condition(
        any(item.get("topic") == "Preisfrage" for item in plan["groups_requiring_focused_followup"]),
        plan,
    )
    assert_condition(plan["review_coverage_gaps"]["full_native_german_approval_claimed"] is False, plan)


def validate_boundaries() -> None:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must be false")
    report_text = REQUIRED_FILES["report"].read_text(encoding="utf-8")
    html_text = REQUIRED_FILES["html"].read_text(encoding="utf-8")
    assert_condition("No full native German approval is claimed" in report_text, report_text[:500])
    assert_condition("No legal compliance is claimed" in report_text, report_text[:500])
    assert_condition("blank rows are treated as unreviewed" in report_text.lower(), report_text[:800])
    assert_condition("Full native German approval is not claimed" in html_text, "approval claim missing")
    assert_condition("Legal compliance is not claimed" in html_text, "legal claim missing")


def main() -> None:
    validate_required_files()
    import_payload = read_json(IMPORT_PATH)
    validate_dependency_results()
    validate_import_summary(import_payload)
    validate_revision_candidates()
    validate_followup_plan()
    validate_boundaries()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
