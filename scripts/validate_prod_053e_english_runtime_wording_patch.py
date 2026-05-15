#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053E-english-runtime-wording-patch"
SOURCE_CHECKPOINT_ID = "PROD-053D-english-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
SOURCE_REVIEW_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-053C-english-spoken-response-expansion-review"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402
from prod_053c_english_spoken_response_expansion_review import BASE_CAMPAIGN, RUNTIME_PROBES  # noqa: E402


REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_053e_english_runtime_wording_patch.py",
    "runner": ROOT / "scripts" / "run_prod_053e_english_runtime_wording_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_053e_english_runtime_wording_patch.py",
    "doc": ROOT / "docs" / "product" / "PROD_053E_ENGLISH_RUNTIME_WORDING_PATCH.md",
}

SOURCE_FILES = {
    "source_result": SOURCE_DIR / "result.json",
    "accepted_as_written": SOURCE_DIR / "accepted_as_written_items.json",
    "runtime_patch_candidates": SOURCE_DIR / "runtime_patch_candidates.json",
    "source_review_items": SOURCE_REVIEW_DIR / "english_spoken_response_review_items.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "promoted_runtime_responses": OUT_DIR / "promoted_runtime_responses.json",
    "skipped_runtime_candidates": OUT_DIR / "skipped_runtime_candidates.json",
}

SAFE_CANDIDATE_TYPES = {"wording", "approved_with_edit_note"}
EXPECTED_EXCLUDED_IDS = {
    "prod-053c-voicemail",
    "prod-053c-coverage-boundary-route",
    "prod-053c-autonomy-check",
}
BOUNDARY_FALSE_FIELDS = [
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
    source_result = read_json(SOURCE_FILES["source_result"])
    summary = source_result["summary"]
    assert_condition(source_result["validation"]["passed"] is True, source_result)
    assert_condition(summary["approved_as_written_count"] == 15, summary)
    assert_condition(summary["approved_with_edit_note_count"] == 1, summary)
    assert_condition(summary["runtime_patch_candidate_count"] >= 14, summary)
    assert_condition(summary["response_text_behavior_changed"] is False, summary)


def expected_promotions() -> dict[str, dict[str, Any]]:
    accepted = read_json(SOURCE_FILES["accepted_as_written"])["items"]
    candidates = read_json(SOURCE_FILES["runtime_patch_candidates"])["items"]
    expected: dict[str, dict[str, Any]] = {}
    for item in accepted:
        expected[item["case_id"]] = {
            "case_id": item["case_id"],
            "sales_difficulty": item["sales_difficulty"],
            "source_bucket": "approved_as_written",
            "previous_response": item["current_agent_response"],
            "promoted_response": item["proposed_review_response"],
        }
    for item in candidates:
        if (
            item["candidate_type"] in SAFE_CANDIDATE_TYPES
            and item["requires_design_decision"] is False
            and item["context_sensitive"] is False
        ):
            expected[item["case_id"]] = {
                "case_id": item["case_id"],
                "sales_difficulty": item["sales_difficulty"],
                "source_bucket": item["candidate_type"],
                "previous_response": item["source_current_response"],
                "promoted_response": item["candidate_response"],
            }
    return expected


def expected_skips() -> dict[str, dict[str, Any]]:
    candidates = read_json(SOURCE_FILES["runtime_patch_candidates"])["items"]
    skipped = {
        item["case_id"]: item
        for item in candidates
        if (
            item["candidate_type"] not in SAFE_CANDIDATE_TYPES
            or item["requires_design_decision"] is True
            or item["context_sensitive"] is True
        )
    }
    return skipped


def runtime_probe_by_id() -> dict[str, dict[str, Any]]:
    probes = {item["case_id"]: item for item in RUNTIME_PROBES}
    source_items = read_json(SOURCE_FILES["source_review_items"])["items"]
    for item in source_items:
        if item["case_id"] not in probes:
            probes[item["case_id"]] = {
                "case_id": item["case_id"],
                "case_title": item["case_title"],
                "sales_difficulty": item["sales_difficulty"],
                "customer_utterance": item["customer_utterance"],
                "customer_input": {
                    "input_type": "speech",
                    "transcript": item["customer_utterance"],
                    "stage": "opening",
                },
            }
    return probes


def runtime_response_for(case_id: str) -> str:
    probe = runtime_probe_by_id()[case_id]
    campaign = probe.get("campaign", BASE_CAMPAIGN)
    decision = build_runtime_decision(probe, campaign=campaign)
    assert_condition(decision["response_language"] == "en", decision)
    return decision["agent_response"]


def validate_runtime_promotions() -> None:
    expected = expected_promotions()
    assert_condition(len(expected) == 26, sorted(expected))
    for case_id, item in expected.items():
        assert_condition(item["sales_difficulty"], item)
        actual = runtime_response_for(case_id)
        assert_condition(
            actual == item["promoted_response"],
            {
                "case_id": case_id,
                "expected": item["promoted_response"],
                "actual": actual,
            },
        )


def validate_runtime_exclusions() -> None:
    skipped = expected_skips()
    assert_condition(set(skipped) == EXPECTED_EXCLUDED_IDS, sorted(skipped))
    for case_id, item in skipped.items():
        actual = runtime_response_for(case_id)
        assert_condition(actual != item["candidate_response"], {"case_id": case_id, "unexpected": actual})


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


def validate_generated_payloads() -> None:
    expected = expected_promotions()
    skipped = expected_skips()
    result = read_json(GENERATED_FILES["result"])
    promoted = read_json(GENERATED_FILES["promoted_runtime_responses"])["items"]
    skipped_payload = read_json(GENERATED_FILES["skipped_runtime_candidates"])["items"]
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["promoted_response_count"] == len(expected), summary)
    assert_condition(summary["accepted_as_written_promoted_count"] == 15, summary)
    assert_condition(summary["safe_rework_promoted_count"] == 10, summary)
    assert_condition(summary["approved_with_edit_note_promoted_count"] == 1, summary)
    assert_condition(summary["skipped_runtime_candidate_count"] == len(skipped), summary)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    assert_condition({item["case_id"] for item in promoted} == set(expected), promoted)
    assert_condition({item["case_id"] for item in skipped_payload} == EXPECTED_EXCLUDED_IDS, skipped_payload)
    for item in promoted:
        assert_condition(item["language"] == "en", item)
        assert_condition(item["runtime_response"] == item["promoted_response"], item)
        assert_condition(item["runtime_promoted"] is True, item)
    for item in skipped_payload:
        assert_condition(item["runtime_promoted"] is False, item)


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}".lower()
    for marker in [
        "prod-053e",
        "prod-053d",
        "26",
        "voicemail",
        "coverage",
        "autonomy",
        "runtime behavior changed",
        "response text behavior changed",
        "no provider",
        "no llm",
        "no private data",
        "prod-054",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_source_files()
    validate_runtime_promotions()
    validate_runtime_exclusions()
    run_runner()
    validate_generated_files()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
