#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053D-english-review-import"
SOURCE_CHECKPOINT_ID = "PROD-053C-english-spoken-response-expansion-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
IMPORT_DIR = ROOT / "research" / "experiments" / "imports" / SOURCE_CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_053d_english_review_import.py",
    "runner": ROOT / "scripts" / "run_prod_053d_english_review_import.py",
    "validator": ROOT / "scripts" / "validate_prod_053d_english_review_import.py",
    "doc": ROOT / "docs" / "product" / "PROD_053D_ENGLISH_REVIEW_IMPORT.md",
}

SOURCE_FILES = {
    "source_result": SOURCE_DIR / "result.json",
    "source_items": SOURCE_DIR / "english_spoken_response_review_items.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "import_summary": OUT_DIR / "imported_review_summary.json",
    "accepted_as_written": OUT_DIR / "accepted_as_written_items.json",
    "approved_with_edit_note": OUT_DIR / "approved_with_edit_note_items.json",
    "needs_rework": OUT_DIR / "needs_rework_items.json",
    "owner_feedback_themes": OUT_DIR / "owner_feedback_themes.json",
    "runtime_patch_candidates": OUT_DIR / "runtime_patch_candidates.json",
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

EXPECTED_REWORK_IDS = {
    "prod-053c-voicemail",
    "prod-053c-identity-repair",
    "prod-053c-support-route",
    "prod-053c-cancellation-route",
    "prod-053c-security-review-route",
    "prod-053c-coverage-boundary-route",
    "prod-053c-healthcare-boundary-route",
    "prod-053c-claim-boundary",
    "prod-053c-scheduling-confirmation",
    "prod-053c-sale-ready-commitment",
    "prod-053c-procurement-review",
    "prod-053c-callback-request",
    "prod-053c-autonomy-check",
}

EXPECTED_APPROVED_WITH_EDIT_NOTE_IDS = {"prod-053c-existing-provider-gap"}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def find_import_path() -> Path:
    canonical = IMPORT_DIR / "prod_053c_review_export.json"
    if canonical.exists():
        return canonical
    candidates = sorted([path for path in IMPORT_DIR.glob("*.json*") if path.is_file()])
    assert_condition(len(candidates) == 1, f"expected exactly one import JSON in {rel(IMPORT_DIR)}, found {[path.name for path in candidates]}")
    return candidates[0]


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
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_sources() -> None:
    import_path = find_import_path()
    source_missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not source_missing, f"missing source files: {source_missing}")
    source_result = read_json(SOURCE_FILES["source_result"])
    import_payload = read_json(import_path)
    assert_condition(source_result["validation"]["passed"] is True, "PROD-053C source must pass")
    assert_condition(import_payload["checkpoint_id"] == SOURCE_CHECKPOINT_ID, import_payload.get("checkpoint_id"))
    assert_condition(len(import_payload["items"]) == source_result["summary"]["review_item_count"], import_payload)


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")


def validate_result() -> dict[str, Any]:
    result = read_json(GENERATED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["import_item_count"] == 29, summary)
    assert_condition(summary["approved_count"] == 16, summary)
    assert_condition(summary["needs_rework_count"] == 13, summary)
    assert_condition(summary["pending_count"] == 0, summary)
    assert_condition(summary["approved_as_written_count"] == 15, summary)
    assert_condition(summary["approved_with_edit_note_count"] == 1, summary)
    assert_condition(summary["runtime_patch_candidate_count"] >= 14, summary)
    assert_condition(summary["voicemail_requires_action_only_change"] is True, summary)
    assert_condition(summary["coverage_requires_policy_knowledge_decision"] is True, summary)
    assert_condition(summary["autonomy_requires_context_sensitive_response"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_item_files() -> None:
    accepted = read_json(GENERATED_FILES["accepted_as_written"])["items"]
    approved_with_note = read_json(GENERATED_FILES["approved_with_edit_note"])["items"]
    rework = read_json(GENERATED_FILES["needs_rework"])["items"]
    assert_condition(len(accepted) == 15, len(accepted))
    assert_condition({item["case_id"] for item in approved_with_note} == EXPECTED_APPROVED_WITH_EDIT_NOTE_IDS, approved_with_note)
    assert_condition({item["case_id"] for item in rework} == EXPECTED_REWORK_IDS, rework)
    for item in [*accepted, *approved_with_note, *rework]:
        assert_condition(item["language"] == "en", item)
        assert_condition(item["runtime_response_changed"] is False, item)
        assert_condition(item["response_text_behavior_changed"] is False, item)
    for item in rework:
        assert_condition(item["owner_notes"].strip(), item)
        assert_condition(item["rework_category"] in {"wording_only", "action_or_behavior_change", "policy_knowledge_decision", "context_sensitive_wording"}, item)


def validate_themes_and_candidates() -> None:
    themes = read_json(GENERATED_FILES["owner_feedback_themes"])["items"]
    candidates = read_json(GENERATED_FILES["runtime_patch_candidates"])["items"]
    theme_ids = {item["theme_id"] for item in themes}
    assert_condition("contractions_over_formal_expansions" in theme_ids, theme_ids)
    assert_condition("less_formal_acknowledgements" in theme_ids, theme_ids)
    assert_condition("voicemail_action_only" in theme_ids, theme_ids)
    assert_condition("policy_knowledge_is_not_advice" in theme_ids, theme_ids)

    candidate_by_id = {item["case_id"]: item for item in candidates}
    assert_condition(candidate_by_id["prod-053c-voicemail"]["candidate_type"] == "action_only_no_spoken_response", candidate_by_id["prod-053c-voicemail"])
    assert_condition(candidate_by_id["prod-053c-coverage-boundary-route"]["requires_design_decision"] is True, candidate_by_id["prod-053c-coverage-boundary-route"])
    assert_condition(candidate_by_id["prod-053c-autonomy-check"]["context_sensitive"] is True, candidate_by_id["prod-053c-autonomy-check"])
    assert_condition("I'll" in candidate_by_id["prod-053c-cancellation-route"]["candidate_response"], candidate_by_id["prod-053c-cancellation-route"])
    assert_condition("I can't" in candidate_by_id["prod-053c-healthcare-boundary-route"]["candidate_response"], candidate_by_id["prod-053c-healthcare-boundary-route"])
    assert_condition("I won't" in candidate_by_id["prod-053c-existing-provider-gap"]["candidate_response"], candidate_by_id["prod-053c-existing-provider-gap"])
    for item in candidates:
        assert_condition(item["runtime_response_changed"] is False, item)
        assert_condition(item["candidate_runtime_promoted"] is False, item)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}".lower()
    for marker in [
        "prod-053d",
        "prod-053c",
        "approved as-written",
        "needs rework",
        "voicemail",
        "coverage",
        "no runtime behavior",
        "no llm",
        "no provider",
        "german exact phrase",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_sources()
    run_runner()
    validate_required_files()
    validate_sources()
    validate_generated_files()
    validate_result()
    validate_item_files()
    validate_themes_and_candidates()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
