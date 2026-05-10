#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-041A-conditional-scenario-diversity-expansion"
SOURCE_CHECKPOINT_ID = "PROD-040-callcenteren-conditional-customer-simulation"
SCENARIO_SOURCE_CHECKPOINT_ID = "PROD-014-callcenteren-scenario-bank"
PATTERN_SOURCE_CHECKPOINT_ID = "PROD-013-callcenteren-pattern-extraction"
NEXT_CHECKPOINT_ID = "PROD-041-conditional-simulation-review"

MODULE = ROOT / "scripts" / "prod_041a_conditional_scenario_diversity_expansion.py"
RUNNER = ROOT / "scripts" / "run_prod_041a_conditional_scenario_diversity_expansion.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TRACE_PATH = OUT_DIR / "scenario_diversity_traces.json"
SURFACE_PATH = OUT_DIR / "scenario_diversity_review.html"
SURFACE_DATA_PATH = OUT_DIR / "scenario_diversity_review_data.json"
SCENARIO_BANK_PATH = ROOT / "research" / "experiments" / "generated" / SCENARIO_SOURCE_CHECKPOINT_ID / "scenario-bank.json"
PATTERN_BANK_PATH = ROOT / "research" / "experiments" / "generated" / PATTERN_SOURCE_CHECKPOINT_ID / "pattern-bank.json"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_LABELS = [
    "price_sensitive",
    "manager_review",
    "existing_provider",
    "confused_fit",
    "skeptical_proof",
    "busy_now",
    "send_info",
    "contract_fear",
    "payment_fear",
    "security_review",
    "bad_experience",
    "needs_approval",
    "hidden_objection",
    "competitor_comparison",
    "not_interested",
    "hostile_rejection",
    "callback_request",
    "support_boundary",
    "technical_integration",
    "setup_timeline",
    "multi_location_routing",
    "low_fit",
    "sale_ready",
    "discovery_needed",
    "insurance_price_fear",
    "spouse_input",
    "scam_card_fear",
    "consumer_not_interested",
    "consumer_callback",
    "coverage_confusion",
    "already_covered",
    "consumer_bad_experience",
    "written_info",
    "consumer_hostile",
    "cancellation_boundary",
    "appointment_interest",
    "sensitive_healthcare",
    "home_service_comparison",
    "reminder_plan",
    "no_pressure_consumer",
]
OPENING_STYLES = {
    "b2b_permission_first",
    "b2b_reason_first",
    "b2b_time_respectful",
    "b2b_manager_relevance",
    "b2c_no_payment_disclosure",
    "b2c_simple_consumer_reason",
    "b2c_safety_first",
}
EMOTIONS = {"calm", "skeptical", "confused", "rushed", "irritated", "anxious", "distrustful", "curious"}
STATE_SHIFTS = {"more_trusting", "unchanged", "more_resistant", "escalated", "reassured"}
STRATEGIES = {
    "permission_first",
    "problem_framing",
    "social_proof_safe",
    "risk_reversal",
    "simple_explanation",
    "objection_isolation",
    "next_step_close",
    "consultative_discovery",
    "trust_repair",
}
SAFE_CLOSE = {"accepted", "callback_scheduled", "written_info_requested", "manager_review_needed", "handoff_required"}
NON_SALE = {"rejected", "support_boundary_ended", "not_qualified", "do_not_contact"}
TERMINAL_OUTCOMES = SAFE_CLOSE | NON_SALE
FAILURE_FLAGS = {
    "dodged_question",
    "question_storming",
    "premature_price_discussion",
    "unsupported_claim",
    "pressure_after_refusal",
    "unsafe_payment_request",
    "missed_handoff",
    "ignored_emotion",
    "repeated_answer",
    "unclear_next_step",
    "product_misfit",
}
REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    TRACE_PATH,
    SURFACE_PATH,
    SURFACE_DATA_PATH,
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
    "source_prod_040_overwritten",
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


def validate_payload(payload: dict[str, Any], trace: dict[str, Any], surface_data: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("scenario_source_checkpoint_id") == SCENARIO_SOURCE_CHECKPOINT_ID, payload.get("scenario_source_checkpoint_id"))
    assert_condition(payload.get("pattern_source_checkpoint_id") == PATTERN_SOURCE_CHECKPOINT_ID, payload.get("pattern_source_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))
    assert_condition(trace.get("checkpoint_id") == CHECKPOINT_ID, trace.get("checkpoint_id"))
    assert_condition(surface_data.get("checkpoint_id") == CHECKPOINT_ID, surface_data.get("checkpoint_id"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("trace_path") == normalized(TRACE_PATH), outputs)
    assert_condition(outputs.get("surface_path") == normalized(SURFACE_PATH), outputs)
    assert_condition(outputs.get("surface_data_path") == normalized(SURFACE_DATA_PATH), outputs)

    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(payload.get("boundaries", {}).get(key) is False, f"boundary {key} must be false")

    calls = trace.get("calls", [])
    profiles = trace.get("scenario_profiles", [])
    summary = payload.get("summary", {})
    assert_condition(summary.get("call_count") == 40, summary)
    assert_condition(len(calls) == 40, len(calls))
    assert_condition(len(profiles) == 40, len(profiles))
    assert_condition(summary.get("b2b_call_count") == 24, summary)
    assert_condition(summary.get("b2c_call_count") == 16, summary)
    assert_condition(Counter(call["scenario_label"] for call in calls) == Counter(REQUIRED_LABELS), "scenario labels must appear exactly once")
    assert_condition(summary.get("domain_count", 0) >= 8, summary)
    assert_condition(summary.get("b2b_domain_count", 0) >= 3, summary)
    assert_condition(summary.get("b2c_domain_count", 0) >= 3, summary)
    assert_condition(summary.get("emotional_start_state_count", 0) >= 6, summary)
    assert_condition(summary.get("objection_type_count", 0) >= 8, summary)
    assert_condition({call["opening"]["selected_opening_style"] for call in calls} == OPENING_STYLES, "all opening styles must be used")
    assert_condition(summary.get("terminal_outcome_type_count", 0) >= 6, summary)
    for key in [
        "support_boundary_ended_count",
        "not_qualified_count",
        "handoff_required_count",
        "callback_scheduled_count",
        "written_info_requested_count",
        "rejected_count",
    ]:
        assert_condition(summary.get(key, 0) >= 1, f"{key} missing")
    assert_condition(summary.get("fixed_turn_limit_used") is False, summary)
    assert_condition(summary.get("loop_guard_triggered") is False, summary)
    assert_condition(summary.get("payment_card_safety_scenario_count", 0) >= 2, summary)
    assert_condition(summary.get("sensitive_healthcare_or_insurance_count", 0) >= 1, summary)
    assert_condition(summary.get("cancellation_support_boundary_count", 0) >= 1, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("strategy_match_rate") == 1.0, summary)
    assert_condition(summary.get("emotion_handling_rate") == 1.0, summary)
    assert_condition(summary.get("no_repeated_selected_opening_text") is True, summary)
    assert_condition(summary.get("no_repeated_full_agent_response_sequence") is True, summary)
    assert_condition(summary.get("no_repeated_closing_answer_for_same_objection") is True, summary)
    assert_condition(summary.get("all_customer_turns_react_to_previous_agent_answer") is True, summary)
    assert_condition(summary.get("all_strategy_bearing_turns_have_detected_strategy") is True, summary)
    assert_condition(summary.get("abstract_pattern_only") is True, summary)
    assert_condition(summary.get("exact_transcript_text_used") is False, summary)
    assert_condition(summary.get("calls_end_with_valid_terminal_outcome") is True, summary)

    selected_openings: set[str] = set()
    full_sequences: set[str] = set()
    closing_by_objection: dict[str, set[str]] = defaultdict(set)
    for call, profile in zip(calls, profiles):
        assert_condition(call["scenario_id"] == profile["scenario_id"], call["scenario_id"])
        assert_condition(call["scenario_label"] == profile["scenario_label"], call["scenario_label"])
        assert_condition(call["b2b_or_b2c"] in {"B2B", "B2C"}, call)
        assert_condition(call["customer_emotional_state_start"] in EMOTIONS, call)
        assert_condition(call["customer_state_shift"] in STATE_SHIFTS, call)
        assert_condition(call["required_strategy"] in STRATEGIES, call)
        assert_condition(call["terminal_outcome"] in TERMINAL_OUTCOMES, call)
        assert_condition(call["terminal_outcome_valid"] is True, call)
        assert_condition(call["terminal_outcome"] in call["valid_terminal_outcomes"], call)
        assert_condition(call["scenario_strategy_match"] is True, call)
        assert_condition(call["emotion_handled"] is True, call)
        assert_condition(call["hard_failure_count"] == 0, call)
        assert_condition(call["failure_flags"] == [], call)
        assert_condition(set(call["failure_taxonomy_hits"]) == FAILURE_FLAGS, call["failure_taxonomy_hits"])
        assert_condition(all(value == 0 for value in call["failure_taxonomy_hits"].values()), call["failure_taxonomy_hits"])

        variants = profile["opening_variants"]
        assert_condition(3 <= len(variants) <= 5, variants)
        assert_condition(call["opening"]["selected_opening"] in variants, call["opening"])
        assert_condition(call["opening"]["selected_opening"] not in selected_openings, call["opening"]["selected_opening"])
        selected_openings.add(call["opening"]["selected_opening"])
        assert_condition(call["opening"]["unused_opening_variants"], call["opening"])

        sequence = call["conversation_sequence"]
        assert_condition(sequence[0]["speaker"] == "agent", sequence[:2])
        assert_condition(sequence[1]["speaker"] == "customer", sequence[:2])
        assert_condition(sequence[0]["text"] == call["opening"]["selected_opening"], sequence[:2])
        assert_condition(sequence[1]["text"] == call["opening"]["customer_opening_response"], sequence[:2])
        assert_condition(len(call["turns"]) in {2, 3}, call["turns"])
        full_sequence = " || ".join(turn["agent_answer"] for turn in call["turns"])
        assert_condition(full_sequence not in full_sequences, full_sequence)
        full_sequences.add(full_sequence)
        closing_answer = call["turns"][-1]["agent_answer"]
        assert_condition(closing_answer not in closing_by_objection[call["primary_objection"]], closing_answer)
        closing_by_objection[call["primary_objection"]].add(closing_answer)

        for turn in call["turns"]:
            assert_condition(turn["customer_context"], turn)
            assert_condition(turn["agent_answer"], turn)
            assert_condition(turn["customer_response"], turn)
            assert_condition(turn["reacts_to_previous_agent_answer"] is True, turn)
            assert_condition(turn["detected_strategy"] in STRATEGIES, turn)
            assert_condition(call["required_strategy"] in call["detected_strategies_used"], call["detected_strategies_used"])
            assert_condition(turn["question_count"] <= 1, turn)
            assert_condition(turn["safety_flags"]["hard_failure"] is False, turn)
            lowered = turn["agent_answer"].lower()
            assert_condition("give me your card" not in lowered, turn)
            assert_condition("guaranteed" not in lowered, turn)
            assert_condition("medical advice" not in lowered, turn)
            assert_condition("coverage is guaranteed" not in lowered, turn)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_041a_conditional_scenario_diversity_expansion.py" in commands, "PROD-041A runner missing from COMMANDS.md")
    assert_condition("validate_prod_041a_conditional_scenario_diversity_expansion.py" in commands, "PROD-041A validator missing from COMMANDS.md")
    assert_condition("PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-041A missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-041A missing from roadmap")
    assert_condition("PROD-041A conditional scenario diversity expansion" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-041A missing from methodology log")
    assert_condition("Add PROD-041A before the PROD-041 human review" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-041A decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, SURFACE_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-041A",
            "Conditional Scenario Diversity Expansion",
            "call count",
            "B2B call count",
            "B2C call count",
            "safe close rate",
            "non sale correctness rate",
            "strategy match rate",
            "emotion handling rate",
            "hard failure count",
            "failure taxonomy",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-041A files: {missing}")
    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")
    validate_payload(read_json(RESULT_PATH), read_json(TRACE_PATH), read_json(SURFACE_DATA_PATH))
    validate_docs()
    print("PROD-041A conditional scenario diversity expansion validation passed.")


if __name__ == "__main__":
    main()
