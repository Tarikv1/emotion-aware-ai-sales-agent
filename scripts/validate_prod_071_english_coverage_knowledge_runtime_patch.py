#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-071-english-coverage-knowledge-runtime-patch"
SOURCE_CHECKPOINT_ID = "PROD-070-english-coverage-knowledge-policy-probe"
NEXT_CHECKPOINT_ID = "PROD-072-english-coverage-knowledge-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-071-english-coverage-knowledge-runtime-patch.json"
BOUNDARY_ROUTE = "coverage-boundary-route"
BOUNDARY_RESPONSE = "I should not give coverage advice. I can route this to the approved qualified reviewer path."
EXPECTED_PATCHED_CASE_IDS = {
    "prod-071-eligible-reimbursement",
    "prod-071-plan-covers-this",
    "prod-071-policy-reimbursed",
}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, localized_response  # noqa: E402


REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_071_english_coverage_knowledge_runtime_patch.py",
    "runner": ROOT / "scripts" / "run_prod_071_english_coverage_knowledge_runtime_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_071_english_coverage_knowledge_runtime_patch.py",
    "source_validator": ROOT / "scripts" / "validate_prod_070_english_coverage_knowledge_policy_probe.py",
    "doc": ROOT / "docs" / "product" / "PROD_071_ENGLISH_COVERAGE_KNOWLEDGE_RUNTIME_PATCH.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "runtime": ROOT / "runtime" / "core" / "realtime_turns.py",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_policy_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "policy_decision.json",
    "source_runtime_reviews": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "runtime_probe_reviews.json",
    "source_evidence": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "evidence_summary.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "runtime_patch_reviews": OUT_DIR / "runtime_patch_reviews.json",
    "patch_decision": OUT_DIR / "patch_decision.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
}

BOUNDARY_FALSE_FIELDS = [
    "response_text_behavior_changed",
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
    decision = read_json(SOURCE_FILES["source_policy_decision"])
    runtime_reviews = read_json(SOURCE_FILES["source_runtime_reviews"])["items"]
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["policy_probe_passed"] is True, result)
    assert_condition(summary["runtime_gap_count"] == 3, summary)
    assert_condition(set(summary["runtime_gap_case_ids"]) == {
        "prod-070-eligible-reimbursement",
        "prod-070-plan-covers-this",
        "prod-070-policy-reimbursed",
    }, summary)
    assert_condition(summary["runtime_patch_recommended_next"] is True, summary)
    assert_condition(summary["recommended_next_checkpoint"] == CHECKPOINT_ID, summary)
    assert_condition(decision["runtime_patch_allowed_in_prod_070"] is False, decision)
    assert_condition(decision["runtime_patch_recommended_next"] is True, decision)
    assert_condition(sum(1 for item in runtime_reviews if item["runtime_gap"]) == 3, runtime_reviews)


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


def runtime_decision(transcript: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": "prod-071-runtime-probe",
            "customer_input": {
                "input_type": "speech",
                "transcript": transcript,
                "stage": "objection",
            },
        }
    )


def validate_runtime_patch() -> None:
    assert_condition(localized_response("en", BOUNDARY_ROUTE, None) == BOUNDARY_RESPONSE, localized_response("en", BOUNDARY_ROUTE, None))
    patched_inputs = [
        "Am I eligible for reimbursement?",
        "Can you tell me if my plan covers this?",
        "Will this be reimbursed by my policy?",
    ]
    for transcript in patched_inputs:
        decision = runtime_decision(transcript)
        assert_condition(decision["response_language"] == "en", decision)
        assert_condition(decision["sales_difficulty"] == BOUNDARY_ROUTE, decision)
        assert_condition(decision["selected_strategy"] == "rapport", decision)
        assert_condition(decision["interest_state"] == "needs-human", decision)
        assert_condition(decision["next_action"] == "escalate", decision)
        assert_condition(decision["call_control"] == "transfer-or-escalate", decision)
        assert_condition(decision["agent_response"] == BOUNDARY_RESPONSE, decision)
    controls = {
        "Which plan is included?": ("product-detail-lookup", "continue", "bridge-then-continue"),
        "What is the price?": ("price-first-direct", "answer-and-continue", "bridge-then-continue"),
        "I need a doctor to diagnose this.": ("healthcare-boundary-route", "escalate", "transfer-or-escalate"),
    }
    for transcript, expected in controls.items():
        decision = runtime_decision(transcript)
        assert_condition((decision["sales_difficulty"], decision["next_action"], decision["call_control"]) == expected, decision)


def validate_generated_files() -> None:
    missing = [rel(path) for path in GENERATED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing generated files: {missing}")
    review_html = OUT_DIR / "prod_071_review.html"
    assert_condition(not review_html.exists(), "PROD-071 must not create review HTML unless human review is required")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_coverage_knowledge_classifier_reachability_patch_only", payload)
    assert_condition(payload["runtime_change_requested"] is True, payload)
    assert_condition(payload["classifier_change_requested"] is True, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["coverage_advice_allowed"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)
    assert_condition(len(payload["runtime_patch_cases"]) == 6, payload)
    assert_condition(payload["future_persuasion_tactic_candidate"]["tactic_id"] == "guided_option_selection", payload)


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
    assert_condition(result["validation"]["controls_preserved"] is True, result)

    assert_condition(summary["runtime_behavior_changed"] is True, summary)
    assert_condition(summary["classifier_behavior_changed"] is True, summary)
    assert_condition(summary["response_text_behavior_changed"] is False, summary)
    assert_condition(summary["english_only_runtime_patch"] is True, summary)
    assert_condition(summary["patched_sales_difficulty"] == BOUNDARY_ROUTE, summary)
    assert_condition(summary["runtime_patch_case_count"] == 6, summary)
    assert_condition(summary["patched_case_count"] == 3, summary)
    assert_condition(summary["control_case_count"] == 3, summary)
    assert_condition(summary["failed_runtime_patch_case_count"] == 0, summary)
    assert_condition(set(summary["patched_case_ids"]) == EXPECTED_PATCHED_CASE_IDS, summary)
    assert_condition(summary["coverage_advice_allowed"] is False, summary)
    assert_condition(summary["coverage_fact_claims_allowed"] is False, summary)
    assert_condition(summary["eligibility_claims_allowed"] is False, summary)
    assert_condition(summary["reimbursement_claims_allowed"] is False, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is False, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["future_persuasion_tactic_candidate_recorded"] is True, summary)
    assert_condition(summary["guided_option_selection_recorded"] is True, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(decision["decision"] == "english_coverage_knowledge_runtime_patch_applied", decision)
    assert_condition(decision["runtime_path"] == "runtime/core/realtime_turns.py", decision)
    assert_condition(decision["response_text_change"] is False, decision)
    assert_condition(decision["classifier_change"] is True, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(decision["production_runtime_promotion_allowed"] is False, decision)

    assert_condition(len(reviews) == 6, reviews)
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
        "prod-071",
        "english coverage knowledge runtime patch",
        "english coverage knowledge classifier reachability patch only",
        "eligible",
        "reimbursement",
        "plan covers",
        "runtime behavior changed: `true`",
        "classifier behavior changed: `true`",
        "response text behavior changed: `false`",
        "retrieval enabled: `false`",
        "coverage advice allowed: `false`",
        "no human review required",
        "review html created: `false`",
        "guided_option_selection",
        "future persuasion-tactics checkpoint",
        "prod-072-english-coverage-knowledge-post-patch-regression",
        "production runtime promotion allowed: `false`",
        "provider",
        "private data",
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
