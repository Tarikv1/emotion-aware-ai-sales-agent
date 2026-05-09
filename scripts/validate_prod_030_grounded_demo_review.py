#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-030-grounded-demo-review"
SOURCE_CHECKPOINT_ID = "PROD-029-grounded-full-scenario-rerun"
NEXT_CHECKPOINT_ID = "PROD-031-grounded-route-gap-fix"

MODULE = ROOT / "scripts" / "prod_030_grounded_demo_review.py"
RUNNER = ROOT / "scripts" / "run_prod_030_grounded_demo_review.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_030_GROUNDED_DEMO_REVIEW.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PACKET_PATH = OUT_DIR / "demo_review_packet.json"
TRACE_HTML_PATH = OUT_DIR / "demo_review_trace.html"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    PACKET_PATH,
    TRACE_HTML_PATH,
    SOURCE_RESULT_PATH,
]

REQUIRED_FALSE_BOUNDARIES = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "raw_transcript_text_stored",
    "copied_transcript_text_used",
    "commercial_runtime_prompt_text_from_transcripts_allowed",
    "customer_data_allowed",
    "payment_collection_enabled",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "source_prod_029_overwritten",
    "runtime_campaign_profile_promotion_allowed",
    "production_runtime_promotion_allowed",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "take your payment",
    "card number",
    "credit card number",
    '"provider_calls_made": true',
    '"runtime_behavior_changed_by_this_checkpoint": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"runtime_campaign_profile_promotion_allowed": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("packet_path") == normalized(PACKET_PATH), outputs)
    assert_condition(outputs.get("trace_html_path") == normalized(TRACE_HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("source_scenario_count") == 20, summary)
    assert_condition(summary.get("source_turn_count") == 120, summary)
    assert_condition(summary.get("reviewed_turn_count") == 120, summary)
    assert_condition(summary.get("reviewed_scenario_count") == 20, summary)
    assert_condition(summary.get("accepted_grounded_answer_count") == 120, summary)
    assert_condition(summary.get("revise_grounded_answer_count") == 0, summary)
    assert_condition(summary.get("rejected_grounded_answer_count") == 0, summary)
    assert_condition(summary.get("route_accepted_turn_count") == 110, summary)
    assert_condition(summary.get("route_gap_turn_count") == 10, summary)
    assert_condition(summary.get("route_gap_scenario_count") == 7, summary)
    assert_condition(summary.get("demo_ready_turn_count") == 110, summary)
    assert_condition(summary.get("demo_ready_scenario_count") == 13, summary)
    assert_condition(summary.get("local_demo_subset_allowed") is True, summary)
    assert_condition(summary.get("full_demo_set_allowed") is False, summary)
    assert_condition(summary.get("grounded_answer_layer_candidate_accepted") is True, summary)
    assert_condition(summary.get("runtime_profile_promotion_blocked") is True, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("runtime_behavior_changed") is False, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)

    expected_route_gap_types = {
        "unknown-runtime-signal_policy_mismatch",
        "autonomy-check_policy_mismatch",
        "scheduling-confirmation_call-control-mismatch",
    }
    assert_condition(set(summary.get("route_gap_types", [])) == expected_route_gap_types, summary.get("route_gap_types"))
    assert_condition(summary.get("scenario_labels_demo_ready") == ["cancellation_boundary", "sale_eligible", "support_handoff", "trust_repair"], summary)
    assert_condition(summary.get("scenario_labels_route_gap") == ["callback_request", "price_objection"], summary)

    packet = read_json(PACKET_PATH)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, packet.get("source_checkpoint_id"))
    assert_condition(len(packet.get("scenario_reviews", [])) == 20, "scenario review count")
    assert_condition(len(packet.get("demo_ready_scenarios", [])) == 13, "demo-ready scenario count")
    assert_condition(len(packet.get("route_gap_scenarios", [])) == 7, "route-gap scenario count")
    assert_condition(len(packet.get("recommended_demo_scenarios", [])) == 4, "recommended demo scenario count")

    all_turn_reviews = [turn for scenario in packet["scenario_reviews"] for turn in scenario.get("turn_reviews", [])]
    assert_condition(len(all_turn_reviews) == 120, "turn review count")
    assert_condition(sum(1 for turn in all_turn_reviews if turn["grounded_answer_review_status"] == "accepted") == 120, "accepted answers")
    assert_condition(sum(1 for turn in all_turn_reviews if turn["route_review_status"] == "route-gap-needs-policy-review") == 10, "route gaps")
    assert_condition(sum(1 for turn in all_turn_reviews if turn["demo_review_status"] == "demo-ready") == 110, "demo-ready turns")
    for turn in all_turn_reviews:
        for key in [
            "customer_message",
            "prod_027_agent_answer",
            "grounded_agent_answer",
            "grounded_answer_review_status",
            "route_review_status",
            "demo_review_status",
            "review_reason",
            "expected_policy_action",
            "observed_policy_action",
            "expected_call_control",
            "observed_call_control",
        ]:
            assert_condition(key in turn, f"missing {key}")
        assert_condition(turn["contains_payment_collection"] is False, turn)
        assert_condition(turn["unsupported_claim"] is False, turn)
        assert_condition(turn["hard_failure"] is False, turn)

    decision = payload.get("decision", {})
    assert_condition(decision.get("grounded_answers_for_demo") == "accept", decision)
    assert_condition(decision.get("route_gaps") == "revise-before-full-demo-or-runtime-profile", decision)
    assert_condition(decision.get("runtime_campaign_profile") == "candidate-only-not-promoted", decision)
    assert_condition(decision.get("next_step") == NEXT_CHECKPOINT_ID, decision)

    html = TRACE_HTML_PATH.read_text(encoding="utf-8")
    for marker in [
        "PROD-030 Grounded Demo Review",
        "accepted/rejected/revise status per grounded answer and route gap",
        "demo-ready scenarios: 13",
        "route-gap scenarios: 7",
    ]:
        assert_condition(marker in html, marker)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_030_grounded_demo_review.py" in commands, "PROD-030 runner missing from COMMANDS.md")
    assert_condition("validate_prod_030_grounded_demo_review.py" in commands, "PROD-030 validator missing from COMMANDS.md")
    assert_condition("PROD_030_GROUNDED_DEMO_REVIEW.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-030 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-030 missing from roadmap")
    assert_condition("PROD-030 grounded demo review" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-030 missing from methodology log")
    assert_condition("Keep PROD-030 as a demo review gate" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-030 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-030",
            "grounded demo review",
            "accepted/rejected/revise status per grounded answer and route gap",
            "accepted grounded answers: `120`",
            "route gap turns: `10`",
            "demo-ready scenarios: `13`",
            "full demo set allowed: `false`",
            "runtime campaign profile promotion allowed: `false`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-030 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-030 grounded demo review validation passed.")


if __name__ == "__main__":
    main()
