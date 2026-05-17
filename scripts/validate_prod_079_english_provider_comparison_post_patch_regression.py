#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402


CHECKPOINT_ID = "PROD-079-english-provider-comparison-post-patch-regression"
SOURCE_CHECKPOINT_ID = "PROD-078-english-provider-comparison-runtime-patch"
NEXT_CHECKPOINT_ID = "PROD-080-english-customer-move-remaining-slice-selection"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-079-english-provider-comparison-post-patch-regression.json"
EXPECTED_RESPONSE = "Fair. We can compare fit against what you use now before you decide."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_079_english_provider_comparison_post_patch_regression.py",
    "runner": ROOT / "scripts" / "run_prod_079_english_provider_comparison_post_patch_regression.py",
    "validator": ROOT / "scripts" / "validate_prod_079_english_provider_comparison_post_patch_regression.py",
    "source_validator": ROOT / "scripts" / "validate_prod_078_english_provider_comparison_runtime_patch.py",
    "stable_guard_validator": ROOT / "scripts" / "validate_prod_056_english_post_patch_multi_turn_regression.py",
    "doc": ROOT / "docs" / "product" / "PROD_079_ENGLISH_PROVIDER_COMPARISON_POST_PATCH_REGRESSION.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_reviews": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "runtime_patch_reviews.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "patch_decision.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "post_patch_regression_reviews": OUT_DIR / "post_patch_regression_reviews.json",
    "stable_guard_summary": OUT_DIR / "stable_guard_summary.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

BOUNDARY_FALSE_FIELDS = [
    "runtime_behavior_changed",
    "response_text_behavior_changed",
    "classifier_behavior_changed",
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


def validate_sources() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    decision = read_json(SOURCE_FILES["source_decision"])
    reviews = read_json(SOURCE_FILES["source_reviews"])["items"]
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["patched_response"] == EXPECTED_RESPONSE, result["summary"])
    assert_condition(decision["decision"] == "english_provider_comparison_runtime_patch_applied", decision)
    assert_condition(all(item["passed"] for item in reviews), reviews)


def runtime_decision(transcript: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": "prod-079-runtime-check",
            "customer_input": {
                "input_type": "speech",
                "transcript": transcript,
                "stage": "objection-handling",
            },
        },
        campaign={"language": "en"},
    )


def validate_runtime_regression() -> None:
    assert_condition(localized_response("en", "provider-comparison", None) == EXPECTED_RESPONSE, localized_response("en", "provider-comparison", None))
    for transcript in [
        "How is this different from our current provider?",
        "Can you compare this with what we already use?",
        "What would be different versus our current setup?",
        "How does this compare with our current terms?",
        "Can you compare your terms with what we already have?",
    ]:
        decision = runtime_decision(transcript)
        assert_condition(decision["sales_difficulty"] == "provider-comparison", decision)
        assert_condition(decision["agent_response"] == EXPECTED_RESPONSE, decision)
    for transcript in [
        "We already have a provider and I do not want to switch.",
        "We have another provider.",
        "We already use another provider.",
    ]:
        assert_condition(runtime_decision(transcript)["sales_difficulty"] == "existing-provider-gap", transcript)
    assert_condition(runtime_decision("What does this cost?")["sales_difficulty"] == "price-first-direct", "price route")
    assert_condition(runtime_decision("What do you offer?")["sales_difficulty"] == "unknown-runtime-signal", "generic offer route")
    assert_condition(runtime_decision("Can you take payment or card details if it is better?")["sales_difficulty"] == "payment-safety-boundary", "payment route")
    assert_condition(runtime_decision("Can you sign me up if this is better?")["sales_difficulty"] != "provider-comparison", "signup route")


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
    assert_condition(not (OUT_DIR / "prod_079_review.html").exists(), "PROD-079 must not create review HTML")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_provider_comparison_post_patch_regression", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    reviews = read_json(GENERATED_FILES["post_patch_regression_reviews"])["items"]
    stable = read_json(GENERATED_FILES["stable_guard_summary"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["post_patch_regression_only"] is True, summary)
    assert_condition(summary["failed_regression_case_count"] == 0, summary)
    assert_condition(summary["provider_comparison_positive_case_count"] >= 5, summary)
    assert_condition(summary["existing_provider_control_count"] >= 3, summary)
    assert_condition(summary["stable_english_guard_passed"] is True, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(all(item["passed"] for item in reviews), reviews)
    assert_condition(stable["passed"] is True, stable)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)
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
        "prod-079",
        "english provider-comparison post-patch regression",
        "stable english guard passed",
        "provider-comparison positive",
        "existing-provider-gap",
        "failed regression case count: `0`",
        "review html created: `false`",
        "prod-080-english-customer-move-remaining-slice-selection",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "classifier behavior changed: `false`",
        "retrieval enabled: `false`",
        "production runtime promotion allowed: `false`",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_sources()
    validate_runtime_regression()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
