#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-052-language-lane-review-separation"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_052_language_lane_review_separation.py",
    "runner": ROOT / "scripts" / "run_prod_052_language_lane_review_separation.py",
    "validator": ROOT / "scripts" / "validate_prod_052_language_lane_review_separation.py",
    "doc": ROOT / "docs" / "product" / "PROD_052_LANGUAGE_LANE_REVIEW_SEPARATION.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "english_review": OUT_DIR / "english_spoken_review_items.json",
    "german_pending": OUT_DIR / "german_pending_review_items.json",
    "policy_rules": OUT_DIR / "multilingual_policy_rules.json",
    "legacy_surfaces": OUT_DIR / "legacy_mixed_review_surfaces.json",
    "review_html": OUT_DIR / "prod_052_language_lane_review.html",
}

SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-051-safe-call-control-runtime-update" / "result.json"
SOURCE_RUNTIME = ROOT / "research" / "experiments" / "generated" / "PROD-051-safe-call-control-runtime-update" / "runtime_update_results.json"
SOURCE_NATURALNESS = ROOT / "research" / "experiments" / "generated" / "PROD-051-safe-call-control-runtime-update" / "naturalness_audit_results.json"

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
    missing = [rel(path) for path in [*REQUIRED_FILES.values(), SOURCE_RESULT, SOURCE_RUNTIME, SOURCE_NATURALNESS] if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_sources() -> None:
    source_result = read_json(SOURCE_RESULT)
    assert_condition(source_result.get("validation", {}).get("passed") is True, "PROD-051 source result must pass")
    runtime_items = read_json(SOURCE_RUNTIME)["items"]
    naturalness_items = read_json(SOURCE_NATURALNESS)["items"]
    assert_condition(len(runtime_items) == 22, len(runtime_items))
    assert_condition(len(naturalness_items) == 22, len(naturalness_items))
    assert_condition(sum(1 for item in runtime_items if item["language"] == "en") == 4, "expected 4 English source cases")
    assert_condition(sum(1 for item in runtime_items if item["language"] == "de") == 18, "expected 18 German source cases")


def validate_result() -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == "PROD-051-safe-call-control-runtime-update", result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["response_text_behavior_changed"] is False, summary)
    assert_condition(summary["source_case_count"] == 22, summary)
    assert_condition(summary["english_spoken_review_case_count"] == 4, summary)
    assert_condition(summary["english_exact_phrase_review_allowed_count"] == 4, summary)
    assert_condition(summary["german_pending_review_case_count"] == 18, summary)
    assert_condition(summary["german_exact_phrase_acceptance_allowed_count"] == 0, summary)
    assert_condition(summary["german_pending_native_or_source_backed_review_count"] == 18, summary)
    assert_condition(summary["multilingual_policy_rule_count"] >= 8, summary)
    assert_condition(summary["multilingual_policy_rule_pass_count"] == summary["multilingual_policy_rule_count"], summary)
    assert_condition(summary["legacy_mixed_surface_count"] >= 4, summary)
    assert_condition(summary["legacy_mixed_surface_active_acceptance_count"] == 0, summary)
    assert_condition(summary["cross_language_policy_reuse_allowed"] is True, summary)
    assert_condition(summary["cross_language_exact_phrase_reuse_allowed"] is False, summary)
    assert_condition(summary["english_focus_next"] is True, summary)
    assert_condition(summary["native_german_approval_claimed"] is False, summary)
    assert_condition(summary["german_naturalness_claimed"] is False, summary)
    assert_condition(summary["llm_judging_used"] is False, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return result


def validate_english_review_items() -> None:
    items = read_json(REQUIRED_FILES["english_review"])["items"]
    source_items = {
        item["case_id"]: item for item in read_json(SOURCE_RUNTIME)["items"] if item["language"] == "en"
    }
    assert_condition(len(items) == 4, items)
    assert_condition(len(source_items) == 4, source_items)
    for item in items:
        source_item = source_items[item["case_id"]]
        assert_condition(item["language"] == "en", item)
        assert_condition(item["spoken_phrase_review_lane"] == "english_owner_review", item)
        assert_condition(item["exact_phrase_acceptance_allowed"] is True, item)
        assert_condition(item["requires_tarik_review"] is True, item)
        assert_condition(item["requires_native_german_review"] is False, item)
        assert_condition(item["agent_response"].strip(), item)
        assert_condition(item["call_control"] == "bridge-then-continue", item)
        assert_condition(item["next_action"] == "answer-and-continue", item)
        assert_condition(item["agent_response"] == source_item["live_runtime_decision"]["agent_response"], item)
        assert_condition(
            source_item["matches_prod_050_proposal"] is True
            or source_item["matches_later_reviewed_runtime_text"] is True,
            source_item,
        )
        if source_item["matches_later_reviewed_runtime_text"]:
            assert_condition(source_item["later_review_checkpoint_id"] == "PROD-053E-english-runtime-wording-patch", source_item)


def validate_german_pending_items() -> None:
    items = read_json(REQUIRED_FILES["german_pending"])["items"]
    assert_condition(len(items) == 18, items)
    for item in items:
        assert_condition(item["language"] == "de", item)
        assert_condition(item["spoken_phrase_review_lane"] == "german_pending_native_or_source_backed_review", item)
        assert_condition(item["exact_phrase_acceptance_allowed"] is False, item)
        assert_condition(item["requires_tarik_review"] is False, item)
        assert_condition(item["requires_native_german_review"] is True, item)
        assert_condition(item["agent_response"].strip(), item)
        assert_condition(item["policy_level_only"] is True, item)
        assert_condition("pending" in item["review_status"], item)


def validate_policy_rules() -> None:
    rules = read_json(REQUIRED_FILES["policy_rules"])["items"]
    assert_condition(len(rules) >= 8, rules)
    for rule in rules:
        assert_condition(rule["applies_to_languages"] == ["en", "de"], rule)
        assert_condition(rule["scope"] == "style_or_safety_policy", rule)
        assert_condition(rule["exact_phrase_acceptance_rule"] == "language_specific", rule)
        assert_condition(rule["passed"] is True, rule)


def validate_legacy_surfaces() -> None:
    items = read_json(REQUIRED_FILES["legacy_surfaces"])["items"]
    assert_condition(len(items) >= 4, items)
    for item in items:
        assert_condition(item["language_mix"] == "english_and_german", item)
        assert_condition(item["current_acceptance_surface"] is False, item)
        assert_condition(item["separation_action"] in {"superseded_by_prod_052", "historical_evidence_only"}, item)
        assert_condition(Path(ROOT / item["path"]).exists(), item)


def validate_docs() -> None:
    for key in ("doc", "report", "review_html"):
        text = REQUIRED_FILES[key].read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in (
            "prod-052",
            "english",
            "german",
            "native",
            "exact phrase",
            "policy",
            "provider calls made",
            "runtime behavior changed",
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
    validate_english_review_items()
    validate_german_pending_items()
    validate_policy_rules()
    validate_legacy_surfaces()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
