#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-082-english-guided-option-selection-review"
SOURCE_CHECKPOINT_ID = "PROD-081-english-unknown-runtime-signal-subtype-inventory"
NEXT_CHECKPOINT_ID = "PROD-083-english-guided-option-selection-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-082-english-guided-option-selection-review.json"
REVIEW_HTML = OUT_DIR / "prod_082_review.html"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_082_english_guided_option_selection_review.py",
    "runner": ROOT / "scripts" / "run_prod_082_english_guided_option_selection_review.py",
    "validator": ROOT / "scripts" / "validate_prod_082_english_guided_option_selection_review.py",
    "source_validator": ROOT / "scripts" / "validate_prod_081_english_unknown_runtime_signal_subtype_inventory.py",
    "doc": ROOT / "docs" / "product" / "PROD_082_ENGLISH_GUIDED_OPTION_SELECTION_REVIEW.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "slice_decision.json",
    "source_inventory": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "unknown_runtime_signal_subtype_inventory.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "guided_option_selection_review_packet": OUT_DIR / "guided_option_selection_review_packet.json",
    "review_state_template": OUT_DIR / "review_state_template.json",
    "evidence_summary": OUT_DIR / "evidence_summary.json",
    "review_html": REVIEW_HTML,
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
    inventory = read_json(SOURCE_FILES["source_inventory"])
    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["summary"]["selected_next_subtype"] == "guided_option_selection_candidate", result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, result["summary"])
    assert_condition(result["summary"]["recommended_next_checkpoint_requires_human_review"] is True, result["summary"])
    assert_condition(decision["decision"] == "select_guided_option_selection_review_next", decision)
    assert_condition(decision["runtime_patch_allowed"] is False, decision)
    selected = [item for item in inventory["subtypes"] if item["subtype_id"] == "guided_option_selection_candidate"]
    assert_condition(selected and selected[0]["requires_human_review_before_probe"] is True, inventory)


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
    assert_condition(payload["scope"] == "english_guided_option_selection_review_only", payload)
    assert_condition(payload["review_item"] == "guided_option_selection_candidate", payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is True, payload)
    assert_condition(payload["review_html_created"] is True, payload)
    assert_condition(payload["review_html_path"].endswith("prod_082_review.html"), payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    packet = read_json(GENERATED_FILES["guided_option_selection_review_packet"])
    template = read_json(GENERATED_FILES["review_state_template"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["review_packet_created"] is True, result)
    assert_condition(summary["review_packet_only"] is True, summary)
    assert_condition(summary["source_validator_passed"] is True, summary)
    assert_condition(summary["selected_review_item"] == "guided_option_selection_candidate", summary)
    assert_condition(summary["review_example_count"] >= 6, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is True, summary)
    assert_condition(summary["review_html_created"] is True, summary)
    assert_condition(summary["review_html_path"].endswith("prod_082_review.html"), summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)

    assert_condition(packet["review_item"] == "guided_option_selection_candidate", packet)
    assert_condition({"keep_deferred", "approve_for_narrow_policy_probe_with_guardrails", "needs_rewrite_before_probe"} <= set(packet["review_options"]), packet)
    assert_condition(len(packet["examples"]) >= 6, packet)
    guardrails = set(packet["guardrails"])
    for marker in ["two real options", "neither", "not now", "explain the difference", "no fake urgency", "no pretend agreement", "no payment collection", "no contract signing"]:
        assert_condition(marker in guardrails, guardrails)
    joined_examples = json.dumps(packet["examples"], ensure_ascii=False).lower()
    for marker in ["$29", "$59", "neither", "not now", "explain the difference", "no payment details needed"]:
        assert_condition(marker in joined_examples, f"missing packet marker: {marker}")
    assert_condition(template["checkpoint_id"] == CHECKPOINT_ID, template)
    assert_condition(template["review_status"] == "pending_tarik_review", template)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)

    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")


def validate_html() -> None:
    html = REVIEW_HTML.read_text(encoding="utf-8")
    lowered = html.lower()
    for marker in [
        "prod-082",
        "guided option selection",
        "$29",
        "$59",
        "neither",
        "not now",
        "explain the difference",
        "no payment details needed",
        "keep deferred",
        "approve for narrow policy probe",
        "needs rewrite",
        "export json",
        "import json",
        "save in browser",
        "reviewpayload",
        "production runtime promotion allowed: false",
    ]:
        assert_condition(marker in lowered, f"missing html marker: {marker}")


def validate_docs() -> None:
    doc_text = REQUIRED_FILES["doc"].read_text(encoding="utf-8")
    report_text = GENERATED_FILES["report"].read_text(encoding="utf-8")
    commands_text = REQUIRED_FILES["commands"].read_text(encoding="utf-8")
    index_text = REQUIRED_FILES["checkpoint_index"].read_text(encoding="utf-8")
    roadmap_text = REQUIRED_FILES["roadmap"].read_text(encoding="utf-8")
    methodology_text = REQUIRED_FILES["methodology_log"].read_text(encoding="utf-8")
    combined = f"{doc_text}\n{report_text}\n{commands_text}\n{index_text}\n{roadmap_text}\n{methodology_text}".lower()
    for marker in [
        "prod-082",
        "english guided option selection review",
        "guided_option_selection_candidate",
        "requires human review before next checkpoint: `true`",
        "review html created: `true`",
        "prod_082_review.html",
        "prod-083-english-guided-option-selection-review-import",
        "two real options",
        "neither",
        "not now",
        "explain the difference",
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
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_html()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
