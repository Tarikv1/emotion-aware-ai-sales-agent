#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-066-english-voicemail-action-only-policy-probe"
SOURCE_CHECKPOINT_ID = "PROD-065-english-remaining-product-policy-gate-selection"
NEXT_CHECKPOINT_ID = "PROD-067-english-voicemail-action-only-runtime-patch"
SUCCESSOR_CHECKPOINT_ID = "PROD-067-english-voicemail-action-only-runtime-patch"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-066-english-voicemail-action-only-policy-probe.json"
SUCCESSOR_RESULT = ROOT / "research" / "experiments" / "generated" / SUCCESSOR_CHECKPOINT_ID / "result.json"
SELECTED_GATE_ID = "voicemail_action_only_behavior"
CURRENT_RUNTIME_RESPONSE = "I reached voicemail, so I will log this for follow-up according to campaign rules."
EXPECTED_ACTION = "Do not speak to voicemail. Log follow-up and try again later according to campaign rules."

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision  # noqa: E402

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_066_english_voicemail_action_only_policy_probe.py",
    "runner": ROOT / "scripts" / "run_prod_066_english_voicemail_action_only_policy_probe.py",
    "validator": ROOT / "scripts" / "validate_prod_066_english_voicemail_action_only_policy_probe.py",
    "source_validator": ROOT / "scripts" / "validate_prod_065_english_remaining_product_policy_gate_selection.py",
    "doc": ROOT / "docs" / "product" / "PROD_066_ENGLISH_VOICEMAIL_ACTION_ONLY_POLICY_PROBE.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_selection": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "remaining_gate_selection.json",
    "voicemail_candidate": ROOT / "research" / "experiments" / "generated" / "PROD-053D-english-review-import" / "runtime_patch_candidates.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "policy_decision": OUT_DIR / "policy_decision.json",
    "policy_probe_reviews": OUT_DIR / "policy_probe_reviews.json",
    "current_runtime_gap.json": OUT_DIR / "current_runtime_gap.json",
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


def validate_source_files() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    selection = read_json(SOURCE_FILES["source_selection"])
    candidates = read_json(SOURCE_FILES["voicemail_candidate"])["items"]

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["selected_gate_id"] == SELECTED_GATE_ID, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result)
    assert_condition(selection["selected_gate"]["gate_id"] == SELECTED_GATE_ID, selection)
    assert_condition(selection["selected_gate"]["candidate_type"] == "action_only_no_spoken_response", selection)
    voicemail = next(item for item in candidates if item["case_id"] == "prod-053c-voicemail")
    assert_condition(voicemail["candidate_action"] == EXPECTED_ACTION, voicemail)
    assert_condition(voicemail["candidate_response"] == "", voicemail)


def successor_patch_applied() -> bool:
    if not SUCCESSOR_RESULT.exists():
        return False
    try:
        result = read_json(SUCCESSOR_RESULT)
    except (OSError, json.JSONDecodeError):
        return False
    return (
        result.get("checkpoint_id") == SUCCESSOR_CHECKPOINT_ID
        and result.get("validation", {}).get("passed") is True
        and result.get("summary", {}).get("patched_agent_response") == ""
    )


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
    review_html = OUT_DIR / "prod_066_review.html"
    assert_condition(not review_html.exists(), "PROD-066 must not create review HTML unless human review is required")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_voicemail_action_only_policy_probe_only", payload)
    assert_condition(payload["selected_gate_id"] == SELECTED_GATE_ID, payload)
    assert_condition(payload["candidate_action"] == EXPECTED_ACTION, payload)
    assert_condition(payload["candidate_response"] == "", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(len(payload["policy_probe_cases"]) == 6, payload)


def validate_current_runtime_gap() -> None:
    decision = build_runtime_decision(
        {
            "case_id": "prod-066-current-runtime-gap",
            "customer_input": {
                "input_type": "voicemail-detected",
                "transcript": "",
                "stage": "opening",
            },
        }
    )
    assert_condition(decision["sales_difficulty"] == "voicemail", decision)
    assert_condition(decision["next_action"] == "create-follow-up-task", decision)
    assert_condition(decision["call_control"] == "end-call", decision)
    if decision["agent_response"] == "" and successor_patch_applied():
        historical_gap = read_json(GENERATED_FILES["current_runtime_gap.json"])
        assert_condition(historical_gap["current_runtime_decision"]["agent_response"] == CURRENT_RUNTIME_RESPONSE, historical_gap)
        assert_condition(historical_gap["gap_detected"] is True, historical_gap)
        return
    assert_condition(decision["agent_response"] == CURRENT_RUNTIME_RESPONSE, decision)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    decision = read_json(GENERATED_FILES["policy_decision"])
    reviews = read_json(GENERATED_FILES["policy_probe_reviews"])["items"]
    runtime_gap = read_json(GENERATED_FILES["current_runtime_gap.json"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["policy_probe_passed"] is True, result)
    assert_condition(summary["policy_probe_only"] is True, summary)
    assert_condition(summary["selected_gate_id"] == SELECTED_GATE_ID, summary)
    assert_condition(summary["owner_feedback_imported"] is True, summary)
    assert_condition(summary["policy_probe_count"] == 6, summary)
    assert_condition(summary["failed_policy_probe_count"] == 0, summary)
    assert_condition(summary["current_runtime_gap_detected"] is True, summary)
    assert_condition(summary["current_runtime_has_spoken_voicemail_response"] is True, summary)
    assert_condition(summary["candidate_action"] == EXPECTED_ACTION, summary)
    assert_condition(summary["candidate_response"] == "", summary)
    assert_condition(summary["runtime_patch_allowed_in_prod_066"] is False, summary)
    assert_condition(summary["runtime_patch_recommended_next"] is True, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(decision["decision"] == "voicemail_action_only_policy_probe_passed_recommend_narrow_runtime_patch", decision)
    assert_condition(decision["runtime_patch_allowed_in_prod_066"] is False, decision)
    assert_condition(decision["runtime_patch_recommended_next"] is True, decision)
    assert_condition(decision["requires_human_review_before_next_checkpoint"] is False, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(runtime_gap["current_runtime_decision"]["agent_response"] == CURRENT_RUNTIME_RESPONSE, runtime_gap)
    assert_condition(runtime_gap["gap_detected"] is True, runtime_gap)
    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)
    assert_condition(len(reviews) == 6, reviews)
    assert_condition(all(item["passed"] for item in reviews), reviews)

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
        "prod-066",
        "english voicemail action-only policy probe",
        "voicemail_action_only_behavior",
        "do not speak to voicemail",
        "current runtime gap detected: `true`",
        "runtime patch allowed in prod-066: `false`",
        "runtime patch recommended next: `true`",
        "no human review required",
        "review html created: `false`",
        "prod-067-english-voicemail-action-only-runtime-patch",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
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
    validate_current_runtime_gap()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
