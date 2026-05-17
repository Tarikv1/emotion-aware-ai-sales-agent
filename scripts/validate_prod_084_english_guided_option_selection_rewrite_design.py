#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-084-english-guided-option-selection-rewrite-design"
SOURCE_CHECKPOINT_ID = "PROD-083-english-guided-option-selection-review-import"
NEXT_CHECKPOINT_ID = "PROD-085-english-guided-option-selection-rewrite-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CASE_FILE = ROOT / "research" / "experiments" / "cases" / "prod-084-english-guided-option-selection-rewrite-design.json"
REVIEW_HTML = OUT_DIR / "prod_084_review.html"

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_084_english_guided_option_selection_rewrite_design.py",
    "runner": ROOT / "scripts" / "run_prod_084_english_guided_option_selection_rewrite_design.py",
    "validator": ROOT / "scripts" / "validate_prod_084_english_guided_option_selection_rewrite_design.py",
    "source_validator": ROOT / "scripts" / "validate_prod_083_english_guided_option_selection_review_import.py",
    "doc": ROOT / "docs" / "product" / "PROD_084_ENGLISH_GUIDED_OPTION_SELECTION_REWRITE_DESIGN.md",
    "commands": ROOT / "docs" / "product" / "COMMANDS.md",
    "checkpoint_index": ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
    "roadmap": ROOT / "docs" / "thesis" / "ROADMAP.md",
    "methodology_log": ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
    "case_file": CASE_FILE,
}

SOURCE_FILES = {
    "source_result": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "rewrite_requirements": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "rewrite_requirements.json",
    "plan_fact_requirements": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "plan_fact_requirements.json",
    "payment_workflow_requirements": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "payment_workflow_requirements.json",
    "spoken_naturalness_constraints": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "spoken_naturalness_constraints.json",
}

GENERATED_FILES = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "rewritten_review_packet": OUT_DIR / "rewritten_guided_option_review_packet.json",
    "review_state_template": OUT_DIR / "review_state_template.json",
    "review_only_plan_feature_fixture": OUT_DIR / "review_only_plan_feature_fixture.json",
    "spoken_naturalness_audit": OUT_DIR / "spoken_naturalness_audit.json",
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

BANNED_RESPONSE_PHRASES = [
    "there are two fair paths",
    "neither is fine too",
    "not now is a valid answer",
    "$29 is the lower starting point",
    "$59 includes more.",
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
    source_result = read_json(SOURCE_FILES["source_result"])
    rewrite = read_json(SOURCE_FILES["rewrite_requirements"])
    plan_facts = read_json(SOURCE_FILES["plan_fact_requirements"])
    payment = read_json(SOURCE_FILES["payment_workflow_requirements"])
    naturalness = read_json(SOURCE_FILES["spoken_naturalness_constraints"])
    assert_condition(source_result["checkpoint_id"] == SOURCE_CHECKPOINT_ID, source_result)
    assert_condition(source_result["validation"]["passed"] is True, source_result)
    assert_condition(source_result["summary"]["recommended_next_checkpoint"] == CHECKPOINT_ID, source_result["summary"])
    assert_condition(rewrite["rewrite_required"] is True, rewrite)
    assert_condition(rewrite["narrow_policy_probe_allowed_now"] is False, rewrite)
    assert_condition(plan_facts["plan_feature_matrix_required"] is True, plan_facts)
    assert_condition(plan_facts["invent_plan_features_allowed"] is False, plan_facts)
    assert_condition(payment["no_payment_on_call_default"] is True, payment)
    assert_condition(payment["approved_campaign_payment_path_can_be_explained"] is True, payment)
    assert_condition(naturalness["sparse_contextual_discourse_markers_candidate"] is True, naturalness)
    assert_condition(naturalness["random_fillers_allowed"] is False, naturalness)


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
    assert_condition(payload["scope"] == "english_guided_option_selection_rewrite_review_only", payload)
    assert_condition(payload["review_item"] == "guided_option_selection_rewritten_examples", payload)
    assert_condition(payload["requires_human_review_before_next_checkpoint"] is True, payload)
    assert_condition(payload["review_html_created"] is True, payload)
    assert_condition(payload["review_html_path"].endswith("prod_084_review.html"), payload)
    assert_condition(payload["runtime_change_requested"] is False, payload)
    assert_condition(payload["response_text_change_requested"] is False, payload)
    assert_condition(payload["classifier_change_requested"] is False, payload)
    assert_condition(payload["retrieval_change_requested"] is False, payload)
    assert_condition(payload["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, payload)


def validate_generated_payloads() -> None:
    result = read_json(GENERATED_FILES["result"])
    packet = read_json(GENERATED_FILES["rewritten_review_packet"])
    template = read_json(GENERATED_FILES["review_state_template"])
    plan_fixture = read_json(GENERATED_FILES["review_only_plan_feature_fixture"])
    naturalness = read_json(GENERATED_FILES["spoken_naturalness_audit"])
    evidence = read_json(GENERATED_FILES["evidence_summary"])
    summary = result["summary"]

    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["source_checkpoint_id"] == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["validation"]["review_packet_created"] is True, result)
    assert_condition(summary["review_packet_only"] is True, summary)
    assert_condition(summary["source_validator_passed"] is True, summary)
    assert_condition(summary["selected_review_item"] == "guided_option_selection_rewritten_examples", summary)
    assert_condition(summary["review_example_count"] >= 8, summary)
    assert_condition(summary["requires_human_review_before_next_checkpoint"] is True, summary)
    assert_condition(summary["review_html_created"] is True, summary)
    assert_condition(summary["review_html_path"].endswith("prod_084_review.html"), summary)
    assert_condition(summary["recommended_next_checkpoint"] == NEXT_CHECKPOINT_ID, summary)
    assert_condition(summary["narrow_policy_probe_approved"] is False, summary)
    assert_condition(summary["runtime_candidate_promoted"] is False, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")

    assert_condition(packet["review_item"] == "guided_option_selection_rewritten_examples", packet)
    assert_condition({"approve_rewrite_for_policy_probe", "needs_rewrite", "keep_deferred"} <= set(packet["review_options"]), packet)
    assert_condition(packet["runtime_candidate_promoted"] is False, packet)
    assert_condition(packet["examples_are_review_only"] is True, packet)
    assert_condition(len(packet["examples"]) >= 8, packet)
    all_responses = "\n".join(item["proposed_response"] for item in packet["examples"])
    lowered = all_responses.lower()
    for banned in BANNED_RESPONSE_PHRASES:
        assert_condition(banned not in lowered, f"banned phrase still present: {banned}")
    for marker in ["[feature x]", "[feature y]", "[feature a]", "[feature b]", "$29", "$59"]:
        assert_condition(marker.lower() in lowered, f"missing rewritten marker: {marker}")
    assert_condition("companyname.com" in lowered, all_responses)
    assert_condition("no payment on this call" in lowered, all_responses)
    assert_condition("upgrade" in lowered, all_responses)
    assert_condition(any("I mean" in item["proposed_response"] for item in packet["examples"]), packet)
    assert_condition(any("you know" in item["proposed_response"] for item in packet["examples"]), packet)
    assert_condition(any("like" in item["proposed_response"] for item in packet["examples"]), packet)
    assert_condition(all(item["word_count"] <= 38 for item in packet["examples"]), packet)
    payment_examples = [item for item in packet["examples"] if item["example_id"] == "rewrite-payment-path"]
    assert_condition(payment_examples and not payment_examples[0]["uses_discourse_marker"], payment_examples)

    assert_condition(plan_fixture["review_only_fixture"] is True, plan_fixture)
    assert_condition(plan_fixture["invent_plan_features_allowed_in_runtime"] is False, plan_fixture)
    assert_condition({"29", "59"} <= set(plan_fixture["plans"].keys()), plan_fixture)
    assert_condition(naturalness["random_fillers_allowed"] is False, naturalness)
    assert_condition(3 <= naturalness["examples_with_discourse_markers"] <= 5, naturalness)
    assert_condition(naturalness["sensitive_boundary_marker_violations"] == [], naturalness)
    assert_condition(template["checkpoint_id"] == CHECKPOINT_ID, template)
    assert_condition(template["review_status"] == "pending_tarik_review", template)
    assert_condition(evidence["source_validator_run"]["passed"] is True, evidence)


def validate_html() -> None:
    html = REVIEW_HTML.read_text(encoding="utf-8")
    lowered = html.lower()
    for marker in [
        "prod-084",
        "guided option selection rewrite",
        "approve rewrite for policy probe",
        "needs rewrite",
        "keep deferred",
        "[feature x]",
        "[feature y]",
        "[feature a]",
        "[feature b]",
        "i mean",
        "you know",
        "like",
        "companyname.com",
        "no payment on this call",
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
        "prod-084",
        "english guided option selection rewrite design",
        "guided_option_selection_rewritten_examples",
        "requires human review before next checkpoint: `true`",
        "review html created: `true`",
        "prod_084_review.html",
        "prod-085-english-guided-option-selection-rewrite-review-import",
        "leave obvious facts out",
        "plan feature matrix",
        "sparse discourse markers",
        "random fillers allowed: `false`",
        "no payment on this call",
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
