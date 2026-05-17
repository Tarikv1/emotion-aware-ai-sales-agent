#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-075-english-provider-comparison-reachability-review"
SOURCE_CHECKPOINT_ID = "PROD-074-english-customer-move-classification-slice-inventory"
NEXT_CHECKPOINT_ID = "PROD-076-english-provider-comparison-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-075-english-provider-comparison-reachability-review.json"
REVIEW_HTML = OUT_DIR / "prod_075_review.html"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_075_english_provider_comparison_reachability_review.py",
    "runner": ROOT / "scripts" / "run_prod_075_english_provider_comparison_reachability_review.py",
    "validator": ROOT / "scripts" / "validate_prod_075_english_provider_comparison_reachability_review.py",
    "source_validator": ROOT / "scripts" / "validate_prod_074_english_customer_move_classification_slice_inventory.py",
    "doc": ROOT / "docs" / "product" / "PROD_075_ENGLISH_PROVIDER_COMPARISON_REACHABILITY_REVIEW.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "cases": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "source_decision": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "slice_inventory_decision.json",
    "source_unreachable": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "unreachable_response_inventory.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "provider_comparison_review_packet": OUT_DIR / "provider_comparison_review_packet.json",
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


def validate_source_files() -> None:
    missing = [rel(path) for path in SOURCE_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing source files: {missing}")
    result = read_json(SOURCE_FILES["source_result"])
    decision = read_json(SOURCE_FILES["source_decision"])
    unreachable = read_json(SOURCE_FILES["source_unreachable"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["selected_next_review_item"] == "provider-comparison", summary)
    assert_condition(summary["recommended_next_checkpoint"] == CHECKPOINT_ID, summary)
    assert_condition(summary["recommended_next_checkpoint_requires_human_review"] is True, summary)
    assert_condition(decision["decision"] == "select_provider_comparison_reachability_review_next", decision)
    assert_condition(decision["recommended_next_checkpoint"] == CHECKPOINT_ID, decision)
    assert_condition(unreachable["items"][0]["sales_difficulty"] == "provider-comparison", unreachable)


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
    assert_condition(payload["scope"] == "english_provider_comparison_reachability_review_only", payload)
    assert_condition(payload["review_item"] == "provider-comparison", payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is True, payload)
    assert_condition(payload["review_html_created"] is True, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    packet = read_json(GENERATED_FILES["provider_comparison_review_packet"])
    template = read_json(GENERATED_FILES["review_state_template"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["review_packet_created"] is True, result)
    assert_condition(summary["review_packet_only"] is True, summary)
    assert_condition(summary["selected_review_item"] == "provider-comparison", summary)
    assert_condition(summary["review_example_count"] >= 4, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is True, summary)
    assert_condition(summary["review_html_created"] is True, summary)
    assert_condition(summary["review_html_path"].endswith("prod_075_review.html"), summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(packet["review_item"] == "provider-comparison", packet)
    assert_condition(packet["current_response"] == "That is fair. We can compare fit and terms without pressure before you decide whether this is worth reviewing.", packet)
    assert_condition({"keep_blocked", "approve_for_narrow_probe_as_written", "needs_rewrite_before_probe"} <= set(packet["review_options"]), packet)
    assert_condition(len(packet["examples"]) >= 4, packet)
    assert_condition(template["checkpoint_id"] == CHECKPOINT_ID, template)
    assert_condition(template["review_status"] == "pending_tarik_review", template)
    assert_condition(evidence["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, evidence)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)

    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")


def validate_html() -> None:
    html = REVIEW_HTML.read_text(encoding="utf-8")
    lowered = html.lower()
    for marker in [
        "prod-075",
        "provider-comparison",
        "how is this different from our current provider",
        "that is fair. we can compare fit and terms without pressure",
        "keep blocked",
        "approve for narrow probe",
        "needs rewrite",
        "export json",
        "import json",
        "save in browser",
        "reviewpayload",
        "no payment",
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
        "prod-075",
        "english provider-comparison reachability review",
        "provider-comparison",
        "requires human review before next checkpoint: `true`",
        "review html created: `true`",
        "prod_075_review.html",
        "prod-076-english-provider-comparison-review-import",
        "runtime behavior changed: `false`",
        "response text behavior changed: `false`",
        "classifier behavior changed: `false`",
        "retrieval enabled: `false`",
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
    run_runner()
    validate_generated_files()
    validate_case_file()
    validate_generated_payloads()
    validate_html()
    validate_docs()
    print(f"{CHECKPOINT_ID} validation passed")


if __name__ == "__main__":
    main()
