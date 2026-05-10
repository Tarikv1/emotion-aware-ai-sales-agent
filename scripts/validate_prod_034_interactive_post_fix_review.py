#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-034-interactive-post-fix-review"
SOURCE_CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"
NEXT_CHECKPOINT_ID = "PROD-035-runtime-decision-trace-alignment"

MODULE = ROOT / "scripts" / "prod_034_interactive_post_fix_review.py"
RUNNER = ROOT / "scripts" / "run_prod_034_interactive_post_fix_review.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_034_INTERACTIVE_POST_FIX_REVIEW.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PACKET_PATH = OUT_DIR / "interactive_post_fix_review_packet.json"
TRACE_HTML_PATH = OUT_DIR / "interactive_post_fix_review_trace.html"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
SOURCE_TRACE_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "interactive_call_traces.json"

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
    SOURCE_TRACE_PATH,
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
    "source_prod_033_overwritten",
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
    '"production_runtime_promotion_allowed": true',
    '"loop_guard_triggered": true',
    '"fixed_turn_limit_used": true',
    '"terminal_outcome": "max-turns"',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def normalized(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    assert_condition(summary.get("source_call_count") == 8, summary)
    assert_condition(summary.get("source_turn_count") == 14, summary)
    assert_condition(summary.get("reviewed_call_count") == 8, summary)
    assert_condition(summary.get("reviewed_turn_count") == 14, summary)
    assert_condition(summary.get("cold_opening_fix_passed") is True, summary)
    assert_condition(summary.get("outcome_driven_termination_passed") is True, summary)
    assert_condition(summary.get("all_calls_start_with_agent_opening") is True, summary)
    assert_condition(summary.get("all_calls_end_by_customer_decision") is True, summary)
    assert_condition(summary.get("fixed_turn_limit_used") is False, summary)
    assert_condition(summary.get("loop_guard_triggered") is False, summary)
    assert_condition(summary.get("max_turn_terminal_count") == 0, summary)
    assert_condition(summary.get("accepted_deal_count") == 4, summary)
    assert_condition(summary.get("rejected_deal_count") == 4, summary)
    assert_condition(summary.get("callback_converted_to_sale_ready_count") == 0, summary)
    assert_condition(summary.get("repeated_agent_answer_count") == 0, summary)
    assert_condition(summary.get("repeated_customer_message_count") == 0, summary)
    assert_condition(summary.get("decision_snapshot_mismatch_count") == 13, summary)
    assert_condition(summary.get("unknown_objection_decision_count") == 6, summary)
    assert_condition(summary.get("terminal_call_control_mismatch_count") == 0, summary)
    assert_condition(summary.get("product_grounding_issue_count") == 0, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("runtime_behavior_changed") is False, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("first_fix_recommendation") == "runtime_decision_trace_alignment", summary)

    packet = read_json(PACKET_PATH)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, packet.get("source_checkpoint_id"))
    assert_condition(len(packet.get("call_reviews", [])) == 8, "call review count")
    assert_condition(len(packet.get("decision_trace_findings", [])) == 19, "decision trace finding count")
    assert_condition(len(packet.get("mechanics_regression_checks", [])) >= 8, "mechanics checks missing")
    assert_condition(packet.get("fix_recommendations", [{}])[0].get("fix_id") == "runtime_decision_trace_alignment", packet.get("fix_recommendations"))

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + json.dumps(packet, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_034_interactive_post_fix_review.py" in commands, "PROD-034 runner missing from COMMANDS.md")
    assert_condition("validate_prod_034_interactive_post_fix_review.py" in commands, "PROD-034 validator missing from COMMANDS.md")
    assert_condition("PROD_034_INTERACTIVE_POST_FIX_REVIEW.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-034 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-034 missing from roadmap")
    assert_condition("PROD-034 interactive post-fix review" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-034 missing from methodology log")
    assert_condition("Keep PROD-034 as the post-fix review gate" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-034 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-034",
            "interactive post-fix review",
            "cold opening fix passed: `true`",
            "outcome-driven termination passed: `true`",
            "fixed turn limit used: `false`",
            "loop guard triggered: `false`",
            "max-turn terminal count: `0`",
            "callback converted to sale-ready: `0`",
            "repeated agent answers: `0`",
            "repeated customer messages: `0`",
            "decision snapshot mismatches: `13`",
            "unknown-objection decisions: `6`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-034 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-034 interactive post-fix review validation passed.")


if __name__ == "__main__":
    main()
