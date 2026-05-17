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


CHECKPOINT_ID = "PROD-078-english-provider-comparison-runtime-patch"
SOURCE_CHECKPOINT_ID = "PROD-077-english-provider-comparison-narrow-probe-design"
NEXT_CHECKPOINT_ID = "PROD-079-english-provider-comparison-post-patch-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-078-english-provider-comparison-runtime-patch.json"
EXPECTED_RESPONSE = "Fair. We can compare fit against what you use now before you decide."

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_078_english_provider_comparison_runtime_patch.py",
    "runner": ROOT / "scripts" / "run_prod_078_english_provider_comparison_runtime_patch.py",
    "validator": ROOT / "scripts" / "validate_prod_078_english_provider_comparison_runtime_patch.py",
    "source_validator": ROOT / "scripts" / "validate_prod_077_english_provider_comparison_narrow_probe_design.py",
    "doc": ROOT / "docs" / "product" / "PROD_078_ENGLISH_PROVIDER_COMPARISON_RUNTIME_PATCH.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "runtime": ROOT / "runtime" / "core" / "realtime_turns.py",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "design": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "narrow_probe_design.json",
    "response": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "candidate_response_design.json",
    "matrix": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "probe_case_matrix.json",
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


def validate_sources() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    design = read_json(SOURCE_FILES["design"])
    response = read_json(SOURCE_FILES["response"])
    matrix = read_json(SOURCE_FILES["matrix"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(design["branch_order"]["insert_before"] == "existing-provider-gap", design)
    assert_condition(response["candidate_response"] == EXPECTED_RESPONSE, response)
    assert_condition(response["candidate_selected_for_probe"] is True, response)
    assert_condition(len(matrix["positive_probe_cases"]) >= 4, matrix)
    assert_condition(len(matrix["negative_control_cases"]) >= 5, matrix)
    assert_condition(len(matrix["protected_control_cases"]) >= 2, matrix)


def runtime_decision(transcript: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": "prod-078-runtime-check",
            "customer_input": {
                "input_type": "speech",
                "transcript": transcript,
                "stage": "objection-handling",
            },
        },
        campaign={"language": "en"},
    )


def validate_runtime_patch() -> None:
    assert_condition(localized_response("en", "provider-comparison", None) == EXPECTED_RESPONSE, localized_response("en", "provider-comparison", None))
    positives = [
        "How is this different from our current provider?",
        "Can you compare this with what we already use?",
        "What would be different versus our current setup?",
        "How does this compare with our current terms?",
        "Can you compare your terms with what we already have?",
    ]
    for transcript in positives:
        decision = runtime_decision(transcript)
        assert_condition(decision["response_language"] == "en", decision)
        assert_condition(decision["sales_difficulty"] == "provider-comparison", decision)
        assert_condition(decision["selected_strategy"] == "inquiry", decision)
        assert_condition(decision["next_action"] == "ask-follow-up", decision)
        assert_condition(decision["call_control"] == "continue-call", decision)
        assert_condition(decision["agent_response"] == EXPECTED_RESPONSE, decision)

    existing = runtime_decision("We already have a provider and I do not want to switch.")
    assert_condition(existing["sales_difficulty"] == "existing-provider-gap", existing)
    assert_condition("replaces your provider" in existing["agent_response"], existing)
    assert_condition(runtime_decision("What does this cost?")["sales_difficulty"] == "price-first-direct", "price route must remain")
    assert_condition(runtime_decision("What do you offer?")["sales_difficulty"] == "unknown-runtime-signal", "generic offer must not route")
    assert_condition(runtime_decision("Is it better?")["sales_difficulty"] == "unknown-runtime-signal", "generic better must not route")
    assert_condition(runtime_decision("Can you take payment or card details if it is better?")["sales_difficulty"] == "payment-safety-boundary", "payment must remain protected")
    assert_condition(runtime_decision("Can you sign me up if this is better?")["sales_difficulty"] != "provider-comparison", "signup must not route to comparison")


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
    assert_condition(not (OUT_DIR / "prod_078_review.html").exists(), "PROD-078 must not create review HTML")


def validate_case_file() -> None:
    payload = read_json(CASE_FILE)
    assert_condition(payload["checkpoint_id"] == CHECKPOINT_ID, payload)
    assert_condition(payload["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, payload)
    assert_condition(payload["scope"] == "english_provider_comparison_narrow_runtime_patch", payload)
    assert_condition(payload["runtime_change_requested"] is True, payload)
    assert_condition(payload["response_text_change_requested"] is True, payload)
    assert_condition(payload["classifier_change_requested"] is True, payload)
    assert_condition(payload["comparison_target_required"] is True, payload)
    assert_condition(payload["generic_provider_or_terms_comparison_allowed"] is False, payload)
    assert_condition(payload["review_html_created"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_payloads() -> None:
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
    assert_condition(summary["response_text_behavior_changed"] is True, summary)
    assert_condition(summary["classifier_behavior_changed"] is True, summary)
    assert_condition(summary["english_only_runtime_patch"] is True, summary)
    assert_condition(summary["patched_sales_difficulty"] == "provider-comparison", summary)
    assert_condition(summary["patched_response"] == EXPECTED_RESPONSE, summary)
    assert_condition(summary["comparison_target_required"] is True, summary)
    assert_condition(summary["generic_provider_or_terms_comparison_allowed"] is False, summary)
    assert_condition(summary["failed_runtime_patch_case_count"] == 0, summary)
    assert_condition(summary["review_html_created"] is False, summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(decision["decision"] == "english_provider_comparison_runtime_patch_applied", decision)
    assert_condition(decision["inserted_before"] == "existing-provider-gap", decision)
    assert_condition(decision["response_text_change"] is True, decision)
    assert_condition(decision["classifier_change"] is True, decision)
    assert_condition(decision["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, decision)
    assert_condition(all(item["passed"] for item in reviews), reviews)
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
        "prod-078",
        "english provider-comparison runtime patch",
        "english provider-comparison narrow runtime patch",
        "fair. we can compare fit against what you use now before you decide.",
        "inserted before `existing-provider-gap`",
        "runtime behavior changed: `true`",
        "response text behavior changed: `true`",
        "classifier behavior changed: `true`",
        "comparison target required: `true`",
        "generic provider or terms comparison allowed: `false`",
        "review html created: `false`",
        "prod-079-english-provider-comparison-post-patch-regression",
        "retrieval enabled: `false`",
        "production runtime promotion allowed: `false`",
    ]:
        assert_condition(marker in combined, f"missing marker: {marker}")


def main() -> None:
    validate_required_files()
    validate_sources()
    validate_runtime_patch()
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_payloads()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
