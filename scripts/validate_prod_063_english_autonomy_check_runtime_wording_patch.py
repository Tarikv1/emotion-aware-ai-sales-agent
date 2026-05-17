#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-063-english-autonomy-check-runtime-wording-patch"
SOURCE_CHECKPOINT_ID = "PROD-062-english-context-sensitive-autonomy-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-064-english-autonomy-post-patch-multi-turn-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-063-english-autonomy-check-runtime-wording-patch.json"
EXPECTED_RESPONSE = "Okay, no rush. We can keep this low-pressure and only clarify what you need."
OLD_RESPONSE = "That makes sense. We can keep this low pressure and clarify only what you need before any next step."
GERMAN_RESPONSE = "Das verstehe ich. Wir können das ohne Druck klären, bevor es irgendeinen nächsten Schritt gibt."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_063_english_autonomy_check_runtime_wording_patch.py",
    "runner": ROOT / "scripts" / "run_prod_063_english_autonomy_check_runtime_wording_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_063_english_autonomy_check_runtime_wording_patch.py",
    "doc": ROOT / "docs" / "product" / "PROD_063_ENGLISH_AUTONOMY_CHECK_RUNTIME_WORDING_PATCH.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "runtime": ROOT / "runtime" / "core" / "realtime_turns.py",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "policy_decision.json",
    "source_reviews": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "probe_reviews.json",
    "source_evidence": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "evidence_summary.json",
    "source_validator": ROOT / "scripts" / "validate_prod_062_english_context_sensitive_autonomy_policy_probe.py",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "runtime_patch_reviews": OUT_DIR / "runtime_patch_reviews.json",
    "patch_decision": OUT_DIR / "patch_decision.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

BOUNDARY_FALSE_FIELDS = [
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
    reviews = read_json(SOURCE_FILES["source_reviews"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["candidate_response"] == EXPECTED_RESPONSE, result)
    assert_condition(result["summary"]["runtime_patch_recommended_next"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result)
    assert_condition(decision["candidate_response"] == EXPECTED_RESPONSE, decision)
    assert_condition(decision["runtime_patch_allowed_in_prod_062"] is False, decision)
    assert_condition(decision["runtime_patch_recommended_next"] is True, decision)
    assert_condition(len(reviews["items"]) == 5, reviews)
    assert_condition(all(item["passed"] for item in reviews["items"]), reviews)


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


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_autonomy_check_response_text_patch_only", payload)
    assert_condition(payload["expected_response"] == EXPECTED_RESPONSE, payload)
    assert_condition(payload["old_response"] == OLD_RESPONSE, payload)
    assert_condition(payload["runtime_change_requested"] is True, payload)
    assert_condition(payload["response_text_change_requested"] is True, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(len(payload["runtime_probe_cases"]) == 3, payload)


def runtime_decision(transcript: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": "prod-063-runtime-probe",
            "customer_input": {
                "input_type": "speech",
                "transcript": transcript,
                "stage": "objection",
            },
        }
    )


def validate_runtime_patch() -> None:
    assert_condition(localized_response("en", "autonomy-check", None) == EXPECTED_RESPONSE, localized_response("en", "autonomy-check", None))
    assert_condition(OLD_RESPONSE not in REQUIRED_FILES["runtime"].read_text(encoding="utf-8"), "old English autonomy response still present")
    assert_condition(localized_response("de", "autonomy-check", None) == GERMAN_RESPONSE, localized_response("de", "autonomy-check", None))
    for transcript in ["I need time to think. Do not rush.", "Please do not rush me.", "I need time to think before anything else."]:
        decision = runtime_decision(transcript)
        assert_condition(decision["response_language"] == "en", decision)
        assert_condition(decision["sales_difficulty"] == "autonomy-check", decision)
        assert_condition(decision["selected_strategy"] == "inquiry", decision)
        assert_condition(decision["next_action"] == "ask-follow-up", decision)
        assert_condition(decision["call_control"] == "continue-call", decision)
        assert_condition(decision["agent_response"] == EXPECTED_RESPONSE, decision)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    reviews = read_json(GENERATED_FILES["runtime_patch_reviews"])["items"]
    decision = read_json(GENERATED_FILES["patch_decision"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["runtime_patch_passed"] is True, result)
    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    assert_condition(summary["classifier_behavior_changed"] is False, summary)
    assert_condition(summary["english_only_runtime_patch"] is True, summary)
    assert_condition(summary["patched_sales_difficulty"] == "autonomy-check", summary)
    assert_condition(summary["patched_response"] == EXPECTED_RESPONSE, summary)
    assert_condition(summary["runtime_probe_count"] == 3, summary)
    assert_condition(summary["failed_runtime_probe_count"] == 0, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(decision["decision"] == "english_autonomy_check_runtime_wording_patch_applied", decision)
    assert_condition(decision["runtime_path"] == "runtime/core/realtime_turns.py", decision)
    assert_condition(decision["patched_response"] == EXPECTED_RESPONSE, decision)
    assert_condition(decision["classifier_change"] is False, decision)
    assert_condition(decision["call_control_change"] is False, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(decision["production_runtime_promotion_allowed"] is False, decision)

    assert_condition(len(reviews) == 3, reviews)
    assert_condition(all(item["passed"] for item in reviews), reviews)
    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
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
        "prod-063",
        "english autonomy-check runtime wording patch",
        "okay, no rush",
        "runtime behavior changed: `true`",
        "response text behavior changed: `true`",
        "classifier behavior changed: `false`",
        "no human review required",
        "prod-064-english-autonomy-post-patch-multi-turn-regression",
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
    validate_runtime_patch()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
