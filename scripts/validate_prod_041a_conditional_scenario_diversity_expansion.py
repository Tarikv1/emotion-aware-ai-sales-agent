#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-041A-conditional-scenario-diversity-expansion"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
RECIPES_PATH = OUT_DIR / "scenario_recipes.json"
POLICY_BANK_PATH = OUT_DIR / "customer_reaction_policy_bank.json"
FRAMES_PATH = OUT_DIR / "concrete_scenario_frames.json"
PROFILES_PATH = OUT_DIR / "interactive_scenario_profiles.json"
TRACE_PATH = OUT_DIR / "interaction_traces.json"
LEGACY_TRACE_PATH = OUT_DIR / "scenario_diversity_traces.json"
SURFACE_PATH = OUT_DIR / "scenario_diversity_review.html"
SURFACE_DATA_PATH = OUT_DIR / "scenario_diversity_review_data.json"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
DOC_PATH = ROOT / "docs" / "product" / "PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md"
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

FORBIDDEN_SOURCE_USE = {
    "raw transcript text",
    "transcript-specific situations",
    "customer phrasing",
    "company names",
    "customer names",
    "phone numbers",
    "addresses",
    "provider names",
    "unique event sequences",
    "dataset-specific phrasing",
}

BANNED_VISIBLE_DIALOGUE = [
    "first_customer_objection",
    "realistic_next_step",
    "This is about one concrete issue",
    "Quick version please -",
    "Okay, but keep it focused on",
    "This only matters if no immediate workflow trigger",
    "From here, I would keep",
    "The clean next step would be",
]

PROVIDER_OR_SOURCE_NAME_PATTERN = re.compile(r"\b(AIxBlock|CallCenterEN)\b", re.IGNORECASE)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def visible_dialogue(trace: dict[str, Any]) -> str:
    return "\n".join(item.get("text", "") for item in trace.get("conversation_sequence", []))


def full_sequence(trace: dict[str, Any], speaker: str) -> str:
    return " || ".join(item["text"] for item in trace["conversation_sequence"] if item["speaker"] == speaker)


def validate_files() -> None:
    required = [
        RESULT_PATH,
        REPORT_PATH,
        RECIPES_PATH,
        POLICY_BANK_PATH,
        FRAMES_PATH,
        PROFILES_PATH,
        TRACE_PATH,
        LEGACY_TRACE_PATH,
        SURFACE_PATH,
        SURFACE_DATA_PATH,
        DOC_PATH,
        COMMANDS,
        CHECKPOINT_INDEX,
        ROADMAP,
        METHODOLOGY_LOG,
        DECISION_LOG,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    assert_condition(not missing, f"missing required PROD-041A files: {missing}")


def validate_policy_bank(policy_bank: dict[str, Any]) -> None:
    rules = policy_bank.get("reaction_rules", [])
    assert_condition(len(rules) >= 20, len(rules))
    required_fields = {
        "reaction_rule_id",
        "source_pattern_ids",
        "stage",
        "agent_action_trigger",
        "customer_state_preconditions",
        "customer_state_delta",
        "next_customer_behavior",
        "utterance_variants",
        "possible_next_paths",
        "terminal_risk",
        "safety_notes",
    }
    covered = set()
    for rule in rules:
        assert_condition(set(rule) >= required_fields, rule)
        assert_condition(len(rule["source_pattern_ids"]) >= 2, rule)
        assert_condition(rule.get("abstract_pattern_only") is True, rule)
        assert_condition(set(rule.get("forbidden_source_use", [])) >= FORBIDDEN_SOURCE_USE, rule)
        assert_condition(len(rule["utterance_variants"]) >= 3, rule)
        covered.update(rule["agent_action_trigger"])
        serialized = json.dumps(rule, ensure_ascii=False)
        assert_condition(not PROVIDER_OR_SOURCE_NAME_PATTERN.search(serialized), rule["reaction_rule_id"])
    for trigger in [
        "answered_price_directly",
        "dodged_price",
        "respected_refusal",
        "offered_callback",
        "offered_written_info",
        "handled_payment_safety",
        "offered_handoff",
        "pressured_after_refusal",
        "made_unsupported_claim",
        "handled_support_boundary",
    ]:
        assert_condition(trigger in covered, f"missing reaction coverage for {trigger}")


def validate_profiles(profiles_payload: dict[str, Any]) -> None:
    profiles = profiles_payload.get("profiles", [])
    assert_condition(len(profiles) == 40, len(profiles))
    assert_condition(Counter(profile["scenario_label"] for profile in profiles) == Counter(REQUIRED_LABELS), "profile labels")
    assert_condition(sum(1 for profile in profiles if profile["b2b_or_b2c"] == "B2B") == 24, "B2B profiles")
    assert_condition(sum(1 for profile in profiles if profile["b2b_or_b2c"] == "B2C") == 16, "B2C profiles")
    for profile in profiles:
        assert_condition(profile.get("scenario_id"), profile)
        assert_condition(profile.get("scenario_label") in REQUIRED_LABELS, profile)
        assert_condition(profile.get("scenario_frame_id"), profile)
        assert_condition(profile.get("recipe_id"), profile)
        assert_condition(profile.get("customer_role"), profile)
        assert_condition(profile.get("real_world_context"), profile)
        assert_condition(profile.get("agent_visible_context"), profile)
        assert_condition(profile["agent_visible_context"].get("do_not_show_hidden_objection") is True, profile)
        assert_condition(profile.get("initial_customer_state"), profile)
        assert_condition(profile.get("hidden_customer_state"), profile)
        assert_condition(profile.get("customer_goal"), profile)
        assert_condition(profile.get("agent_success_conditions"), profile)
        assert_condition(profile.get("agent_failure_conditions"), profile)
        assert_condition(len(profile.get("available_paths", [])) >= 3, profile)
        assert_condition(len(profile.get("seed_variants", [])) >= 3, profile)
        assert_condition(profile["profile_script_policy"]["full_agent_answers_in_profile"] is False, profile)
        assert_condition(profile["profile_script_policy"]["fixed_customer_script_in_profile"] is False, profile)
        serialized = json.dumps(profile, ensure_ascii=False).lower()
        for banned in ['"agent_answers"', '"customer_responses"', '"opening_customer"', '"spoken_trace_authoring"']:
            assert_condition(banned not in serialized, f"profile contains static script marker {banned}: {profile['scenario_id']}")


def validate_traces(payload: dict[str, Any], trace_payload: dict[str, Any], surface_data: dict[str, Any]) -> None:
    traces = trace_payload.get("interaction_traces", [])
    profiles = trace_payload.get("scenario_profiles", [])
    summary = payload.get("summary", {})
    assert_condition(trace_payload.get("generation_model") == "interactive_conditional_customer_simulation", trace_payload.get("generation_model"))
    assert_condition(summary.get("scenario_profile_count") == 40, summary)
    assert_condition(summary.get("seed_count_per_scenario_min", 0) >= 3, summary)
    assert_condition(summary.get("generated_trace_count", 0) >= 120, summary)
    assert_condition(len(traces) >= 120, len(traces))
    assert_condition(len(profiles) == 40, len(profiles))
    assert_condition(Counter(profile["scenario_label"] for profile in profiles) == Counter(REQUIRED_LABELS), "trace labels")
    assert_condition(summary.get("actual_agent_logic_used") is True or summary.get("actual_agent_logic_unavailable") is True, summary)
    if summary.get("actual_agent_logic_used") is not True:
        assert_condition(summary.get("actual_agent_logic_unavailable") is True, summary)

    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        by_scenario.setdefault(trace["scenario_id"], []).append(trace)
    assert_condition(all(len(items) >= 3 for items in by_scenario.values()), "each scenario needs >=3 seeds")

    exchange_counts = Counter(trace["exchange_count"] for trace in traces)
    assert_condition(not summary.get("same_exchange_count_for_all_traces"), summary)
    assert_condition(not summary.get("all_traces_three_exchanges"), summary)
    assert_condition(summary.get("traces_with_5_plus_exchanges", 0) >= 70, summary)
    assert_condition(summary.get("traces_with_8_plus_exchanges", 0) >= 40, summary)
    assert_condition(summary.get("traces_with_12_plus_exchanges", 0) >= 15, summary)
    assert_condition(summary.get("traces_with_18_plus_exchanges", 0) >= 4, summary)
    assert_condition(max(exchange_counts.values()) <= len(traces) * 0.25, exchange_counts)
    assert_condition(summary.get("scenario_same_count_across_seeds_count") == 0, summary)

    assert_condition(summary.get("neutral_state_two_exchange_trace_count", 0) >= 20, summary)
    assert_condition(summary.get("agent_caused_state_change_trace_count", 0) >= 20, summary)
    assert_condition(summary.get("challenge_pushback_trace_count", 0) >= 20, summary)
    assert_condition(summary.get("recovery_from_weak_answer_trace_count", 0) >= 10, summary)
    assert_condition(summary.get("rejection_or_near_rejection_trace_count", 0) >= 10, summary)
    assert_condition(summary.get("boundary_handling_trace_count", 0) >= 5, summary)
    assert_condition(summary.get("repeated_full_agent_response_sequence_count") == 0, summary)
    assert_condition(summary.get("repeated_full_customer_response_sequence_count") == 0, summary)
    assert_condition(summary.get("static_script_trace_count") == 0, summary)
    assert_condition(summary.get("loop_guard_triggered_count") == 0, summary)

    for key in [
        "hard_failure_count",
        "payment_collection_count",
        "unsupported_claim_count",
        "leakage_finding_count",
    ]:
        assert_condition(summary.get(key) == 0, summary)
    for key in [
        "provider_calls_made",
        "llm_used",
        "exact_transcript_text_used",
        "uses_source_transcript_sequence",
        "runtime_behavior_changed_by_this_checkpoint",
        "production_runtime_promotion_allowed",
    ]:
        assert_condition(summary.get(key) is False, f"{key}: {summary.get(key)}")

    for trace in traces:
        assert_condition(trace.get("scenario_id"), trace)
        assert_condition(trace.get("seed") in {1, 2, 3}, trace)
        assert_condition(trace.get("actual_agent_logic_used") is True, trace)
        assert_condition(trace.get("static_script_used") is False, trace)
        assert_condition(trace.get("terminal_outcome_valid") is True, trace)
        assert_condition(trace.get("hard_failure_count") == 0, trace)
        assert_condition(trace.get("failure_flags") == [], trace)
        assert_condition(trace.get("loop_guard", {}).get("triggered") is False, trace)
        assert_condition(trace.get("exchange_count") == len(trace.get("exchanges", [])), trace)
        assert_condition(trace.get("exchange_count") != 3 or trace["terminal_outcome"] in {"do_not_contact", "support_boundary_ended"}, trace)
        assert_condition(trace.get("selected_reaction_rule_ids"), trace)
        assert_condition(trace.get("scenario_level_scores", {}).get("interactive_generation") is True, trace)
        assert_condition(trace.get("dialogue_realism", {}).get("interactive_not_static") is True, trace)
        spoken = visible_dialogue(trace)
        assert_condition(not PROVIDER_OR_SOURCE_NAME_PATTERN.search(spoken), trace["trace_id"])
        for phrase in BANNED_VISIBLE_DIALOGUE:
            assert_condition(phrase.lower() not in spoken.lower(), {"trace": trace["trace_id"], "phrase": phrase})
        for exchange in trace["exchanges"]:
            assert_condition(exchange.get("agent_text"), exchange)
            assert_condition(exchange.get("customer_text"), exchange)
            assert_condition(exchange.get("agent_action_tags"), exchange)
            assert_condition(exchange.get("selected_reaction_rule_ids"), exchange)
            assert_condition(exchange.get("depends_on_previous_agent_action_tags") is True, exchange)
            assert_condition(exchange.get("customer_state_before") is not None, exchange)
            assert_condition(exchange.get("customer_state_after") is not None, exchange)
            assert_condition(exchange.get("agent_runtime_decision"), exchange)
            assert_condition(exchange.get("safety_flags", {}).get("hard_failure") is False, exchange)

    surface_calls = surface_data.get("calls", [])
    assert_condition(len(surface_calls) == len(traces), "surface data trace count")
    for call in surface_calls[:5]:
        for field in [
            "scenario_id",
            "seed",
            "path_taken",
            "exchange_count",
            "terminal_outcome",
            "counts_toward_safe_close_rate",
            "counts_toward_non_sale_correctness",
            "exchanges",
            "failure_taxonomy_hits",
            "safety_flags",
            "loop_guard",
            "actual_agent_logic_used",
        ]:
            assert_condition(field in call, f"surface missing {field}")


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    doc = DOC_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")
    surface = SURFACE_PATH.read_text(encoding="utf-8")
    assert_condition("run_prod_041a_conditional_scenario_diversity_expansion.py" in commands, "runner missing")
    assert_condition("validate_prod_041a_conditional_scenario_diversity_expansion.py" in commands, "validator missing")
    assert_condition("customer_reaction_policy_bank.json" in doc, "policy bank doc missing")
    assert_condition("interactive_scenario_profiles.json" in doc, "profiles doc missing")
    assert_condition("interaction_traces.json" in doc, "interaction traces doc missing")
    for text, name in [(doc, "doc"), (report, "report"), (surface, "surface")]:
        lowered = text.lower()
        assert_condition("interactive conditional customer simulation" in lowered, name)
        assert_condition("not fixed scripted dialogue" in lowered or "not fixed scripts" in lowered or "not full scripts" in lowered, name)
        assert_condition("agent_action_tags" in text or "agent action tags" in lowered, name)
        assert_condition("reaction_rule" in text or "reaction rule" in lowered, name)
    assert_condition("PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "roadmap")
    assert_condition("interactive conditional customer simulation" in METHODOLOGY_LOG.read_text(encoding="utf-8").lower(), "methodology log")
    assert_condition("interactive conditional customer simulation" in DECISION_LOG.read_text(encoding="utf-8").lower(), "decision log")


def main() -> None:
    validate_files()
    payload = read_json(RESULT_PATH)
    recipes_payload = read_json(RECIPES_PATH)
    policy_bank = read_json(POLICY_BANK_PATH)
    frames_payload = read_json(FRAMES_PATH)
    profiles_payload = read_json(PROFILES_PATH)
    trace_payload = read_json(TRACE_PATH)
    legacy_trace = read_json(LEGACY_TRACE_PATH)
    surface_data = read_json(SURFACE_DATA_PATH)

    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(recipes_payload.get("checkpoint_id") == CHECKPOINT_ID, "recipes checkpoint")
    assert_condition(frames_payload.get("checkpoint_id") == CHECKPOINT_ID, "frames checkpoint")
    assert_condition(policy_bank.get("checkpoint_id") == CHECKPOINT_ID, "policy checkpoint")
    assert_condition(profiles_payload.get("checkpoint_id") == CHECKPOINT_ID, "profiles checkpoint")
    assert_condition(trace_payload.get("checkpoint_id") == CHECKPOINT_ID, "trace checkpoint")
    assert_condition(legacy_trace.get("interaction_traces") == trace_payload.get("interaction_traces"), "legacy alias mismatch")
    assert_condition(surface_data.get("checkpoint_id") == CHECKPOINT_ID, "surface data checkpoint")

    validate_policy_bank(policy_bank)
    validate_profiles(profiles_payload)
    validate_traces(payload, trace_payload, surface_data)
    validate_docs()
    print("PROD-041A interactive conditional customer simulation validation passed.")


if __name__ == "__main__":
    main()
