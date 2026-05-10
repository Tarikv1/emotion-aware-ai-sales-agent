#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-040-callcenteren-conditional-customer-simulation"
SOURCE_CHECKPOINT_ID = "PROD-039-customer-realism-simulator-hardening"
SCENARIO_SOURCE_CHECKPOINT_ID = "PROD-014-callcenteren-scenario-bank"
PATTERN_SOURCE_CHECKPOINT_ID = "PROD-013-callcenteren-pattern-extraction"
NEXT_CHECKPOINT_ID = "PROD-041-conditional-simulation-review"

MODULE = ROOT / "scripts" / "prod_040_callcenteren_conditional_customer_simulation.py"
RUNNER = ROOT / "scripts" / "run_prod_040_callcenteren_conditional_customer_simulation.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_040_CALLCENTEREN_CONDITIONAL_CUSTOMER_SIMULATION.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TRACE_PATH = OUT_DIR / "conditional_customer_traces.json"
SURFACE_PATH = OUT_DIR / "conditional_customer_trace_demo.html"
SURFACE_DATA_PATH = OUT_DIR / "conditional_customer_trace_demo_data.json"
SOURCE_TRACE_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "customer_realism_hardened_traces.json"
SCENARIO_BANK_PATH = ROOT / "research" / "experiments" / "generated" / SCENARIO_SOURCE_CHECKPOINT_ID / "scenario-bank.json"
PATTERN_BANK_PATH = ROOT / "research" / "experiments" / "generated" / PATTERN_SOURCE_CHECKPOINT_ID / "pattern-bank.json"

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
    TRACE_PATH,
    SURFACE_PATH,
    SURFACE_DATA_PATH,
    SOURCE_TRACE_PATH,
    SCENARIO_BANK_PATH,
    PATTERN_BANK_PATH,
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
    "source_prod_039_overwritten",
    "source_prod_014_overwritten",
    "source_prod_013_overwritten",
    "production_runtime_promotion_allowed",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private transcript",
    "api key",
    '"provider_calls_made": true',
    '"llm_used": true',
    '"raw_transcript_text_stored": true',
    '"copied_transcript_text_used": true',
    '"runtime_behavior_changed_by_this_checkpoint": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
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


def all_turns(trace: dict[str, Any]) -> list[dict[str, Any]]:
    return [turn for call in trace.get("calls", []) for turn in call.get("turns", [])]


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("scenario_source_checkpoint_id") == SCENARIO_SOURCE_CHECKPOINT_ID, payload.get("scenario_source_checkpoint_id"))
    assert_condition(payload.get("pattern_source_checkpoint_id") == PATTERN_SOURCE_CHECKPOINT_ID, payload.get("pattern_source_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("trace_path") == normalized(TRACE_PATH), outputs)
    assert_condition(outputs.get("surface_path") == normalized(SURFACE_PATH), outputs)
    assert_condition(outputs.get("surface_data_path") == normalized(SURFACE_DATA_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("call_count") == 8, summary)
    assert_condition(summary.get("total_turn_count", 0) >= 18, summary)
    assert_condition(summary.get("conditional_customer_turn_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("agent_conditioned_customer_reply_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("unique_customer_response_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("repeated_customer_response_count") == 0, summary)
    assert_condition(summary.get("unique_agent_answer_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("repeated_agent_answer_count") == 0, summary)
    assert_condition(summary.get("profile_customized_agent_answer_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("b2b_call_count", 0) >= 4, summary)
    assert_condition(summary.get("b2c_call_count", 0) >= 2, summary)
    assert_condition(summary.get("internal_reason_answer_count", 0) >= 3, summary)
    assert_condition(summary.get("internal_reason_price_first_violation_count") == 0, summary)
    assert_condition(summary.get("callcenteren_pattern_source_count", 0) >= 20, summary)
    assert_condition(summary.get("scenario_bank_source_count") == 8, summary)
    assert_condition(summary.get("abstract_pattern_only") is True, summary)
    assert_condition(summary.get("exact_transcript_text_used") is False, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("all_calls_start_with_cold_opening") is True, summary)
    assert_condition(summary.get("agent_opening_line_visible_count") == 8, summary)
    assert_condition(summary.get("conversation_sequence_starts_with_agent_count") == 8, summary)
    assert_condition(summary.get("all_calls_end_by_customer_decision") is True, summary)
    assert_condition(summary.get("fixed_turn_limit_used") is False, summary)
    assert_condition(summary.get("loop_guard_triggered") is False, summary)
    assert_condition(summary.get("accepted_deal_count", 0) >= 2, summary)
    assert_condition(summary.get("rejected_deal_count", 0) >= 2, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("runtime_behavior_changed") is False, summary)

    trace = read_json(TRACE_PATH)
    surface_data = read_json(SURFACE_DATA_PATH)
    assert_condition(trace.get("checkpoint_id") == CHECKPOINT_ID, trace.get("checkpoint_id"))
    assert_condition(surface_data.get("checkpoint_id") == CHECKPOINT_ID, surface_data.get("checkpoint_id"))
    assert_condition(len(trace.get("calls", [])) == 8, "trace call count")
    turns = all_turns(trace)
    assert_condition(len(turns) == summary.get("total_turn_count"), "turn count mismatch")
    seen_customer_responses: set[str] = set()
    for call in trace["calls"]:
        assert_condition(call.get("market_scope") in {"B2B", "B2C"}, call)
        assert_condition(call.get("opening", {}).get("agent_opening"), call)
        assert_condition(call.get("opening", {}).get("customer_opening_response"), call)
        sequence = call.get("conversation_sequence", [])
        assert_condition(sequence, call)
        assert_condition(sequence[0].get("speaker") == "agent", sequence[:2])
        assert_condition(sequence[0].get("kind") == "opening_line", sequence[:2])
        assert_condition(sequence[0].get("text") == call["opening"]["agent_opening"], sequence[:2])
        assert_condition(sequence[1].get("speaker") == "customer", sequence[:2])
        assert_condition(sequence[1].get("kind") == "opening_response", sequence[:2])
        assert_condition(sequence[1].get("text") == call["opening"]["customer_opening_response"], sequence[:2])
        assert_condition(call.get("terminal_decision_source") == "customer", call)
        assert_condition(call.get("terminal_outcome") in {"accepted-deal", "rejected-deal"}, call)
        assert_condition(call.get("source_recipe", {}).get("source_pattern_ids"), call)
        assert_condition(call.get("source_recipe", {}).get("uses_exact_transcript_text") is False, call)
        for turn in call.get("turns", []):
            assert_condition(turn.get("customer_context"), turn)
            assert_condition(turn.get("agent_answer"), turn)
            assert_condition(turn.get("agent_answer_customization"), turn)
            assert_condition(turn["agent_answer_customization"].get("market_scope") in {"B2B", "B2C"}, turn)
            assert_condition(turn.get("customer_response"), turn)
            assert_condition(turn.get("agent_answer_signals"), turn)
            assert_condition(turn.get("customer_response_condition"), turn)
            assert_condition(turn.get("callcenteren_pattern_basis"), turn)
            assert_condition(turn.get("customer_response") not in seen_customer_responses, turn)
            seen_customer_responses.add(turn["customer_response"])
            assert_condition(turn.get("reacts_to_agent_answer") is True, turn)
            assert_condition(turn.get("copied_transcript_text_used") is False, turn)
            assert_condition(turn.get("contains_transcript_derived_prompt_text") is False, turn)
            assert_condition(turn.get("safety_flags", {}).get("hard_failure") is False, turn)
            if turn.get("state_before", {}).get("active_objection") == "authority":
                lowered_context = turn.get("customer_context", "").lower()
                asks_internal_reason = any(
                    marker in lowered_context
                    for marker in [
                        "internal reason",
                        "what problem",
                        "what would i tell",
                        "version i can repeat",
                        "plain reason",
                        "simple reason",
                    ]
                )
                if asks_internal_reason:
                    answer = turn["agent_answer"].lower()
                    assert_condition(
                        "inbound" in answer
                        or "routing" in answer
                        or "callback" in answer
                        or "response" in answer
                        or "appointment" in answer
                        or "reminder" in answer
                        or "service follow-up" in answer,
                        turn,
                    )
                    assert_condition("$" not in turn["agent_answer"], turn)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_040_callcenteren_conditional_customer_simulation.py" in commands, "PROD-040 runner missing from COMMANDS.md")
    assert_condition("validate_prod_040_callcenteren_conditional_customer_simulation.py" in commands, "PROD-040 validator missing from COMMANDS.md")
    assert_condition("PROD_040_CALLCENTEREN_CONDITIONAL_CUSTOMER_SIMULATION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-040 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-040 missing from roadmap")
    assert_condition("PROD-040 CallCenterEN conditional customer simulation" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-040 missing from methodology log")
    assert_condition("Keep PROD-040 as the CallCenterEN-conditioned customer simulator" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-040 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, SURFACE_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-040",
            "CallCenterEN conditional customer simulation",
            "conditional customer turn count",
            "agent-conditioned customer reply count",
            "unique customer response count",
            "repeated customer response count: `0`",
            "unique agent answer count",
            "repeated agent answer count: `0`",
            "profile customized agent answer count",
            "B2B call count",
            "B2C call count",
            "internal reason answer count",
            "internal reason price-first violation count: `0`",
            "agent opening line visible count",
            "conversation sequence starts with agent count",
            "fixed turn limit used: `false`",
            "loop guard triggered: `false`",
            "leakage findings: `0`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-040 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-040 CallCenterEN conditional customer simulation validation passed.")


if __name__ == "__main__":
    main()
