#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUNNER = ROOT / "scripts" / "run_live_demo_002_runtime_extraction_baseline.py"
BASELINE_PATH = ROOT / "research" / "experiments" / "generated" / "LIVE-DEMO-002" / "runtime_extraction_baseline.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIVE-DEMO-002" / "runtime_extraction_baseline.md"
DOC_PATH = ROOT / "docs" / "product" / "LIVE_DEMO_002_RUNTIME_EXTRACTION_BASELINE.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
RUNTIME_MANIFEST = ROOT / "runtime" / "runtime_manifest.json"

EXPECTED_RUNTIME_MODULES = [
    "runtime.contracts.voice_turn_state_contract",
    "runtime.speech.asr_quality_gate",
    "runtime.core.live_voice_session_policy",
]

EXPECTED_BASELINE_CATEGORIES = {
    "direct_price_answer_routing",
    "product_answer_routing",
    "followup_continuity",
    "anti_loop",
    "voice_delivery_propagation",
    "asr_quality_handling",
}

EXPECTED_PACKET_SHAPE_KEYS = {
    "live_demo_id",
    "mode",
    "campaign_id",
    "session_id",
    "session_turn_index",
    "stage",
    "input_type",
    "transcript",
    "asr",
    "turn_taking",
    "provider_agent_used",
    "durable_provider_agent_created",
    "voice_cloning_used",
    "runtime_behavior_changed",
    "opens_prod_102",
    "demo_session_continuity",
    "dialogue_reasoner_async_enrichment",
    "packet",
    "summary",
    "audio_url",
    "latency",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_leading_voice_filler(text: str) -> str:
    lowered = text.strip().lower()
    return lowered.removeprefix("um, ").removeprefix("uh, ").removeprefix("well, ").removeprefix("so, ")


def has_seller_led_next_move(text: str) -> bool:
    lowered = text.lower()
    return "?" in text and any(
        fragment in lowered
        for fragment in {
            "where does",
            "where is",
            "which part",
            "which gap",
            "which one",
            "main gap",
            "are missed",
            "frequent enough",
            "should i keep",
            "would a short",
        }
    )


def has_sales_context_depth(text: str) -> bool:
    lowered = text.lower()
    if any(fragment in lowered for fragment in {"the narrow check", "the sales case is simple", "feature-wise"}):
        return False
    concepts = {
        "inbound",
        "demo",
        "owner",
        "routing",
        "callback",
        "handoff",
        "reminder",
        "visibility",
        "manager",
        "follow-up",
        "spreadsheet",
        "slack",
    }
    return len({fragment for fragment in concepts if fragment in lowered}) >= 3


def callback_workflow_not_scheduling(text: str) -> bool:
    lowered = text.lower()
    return (
        "what time" not in lowered
        and "call you back" not in lowered
        and "note for the callback" not in lowered
        and "when should" not in lowered
        and any(
            fragment in lowered
            for fragment in {
                "callback reminder",
                "missed follow-up",
                "inbound demo",
                "next step",
                "without a next step",
                "owner",
                "reminder",
            }
        )
        and "?" in text
    )


def has_sales_emphasis_priority(case: dict[str, Any]) -> bool:
    targets = [str(target).strip().lower() for target in case.get("voice_prosody_cue_targets", [])]
    blocked_prefixes = {
        "hi",
        "hello",
        "do you have a minute",
        "this is northstar",
        "calling from northstar",
        "hi, this is",
    }
    important = {
        "missed callback",
        "callback",
        "handoff",
        "routing",
        "owner",
        "workflow review",
        "inbound demo",
        "reminder",
        "visibility",
    }
    return (
        case.get("voice_allowed_emphasis_count", 0) >= 1
        and all(not any(target.startswith(prefix) for prefix in blocked_prefixes) for target in targets if target)
        and any(any(fragment in target for fragment in important) for target in targets)
    )


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def validate_runtime_modules() -> None:
    for module_name in EXPECTED_RUNTIME_MODULES:
        module = importlib.import_module(module_name)
        assert_condition(module is not None, f"missing module {module_name}")

    voice_contract = importlib.import_module("runtime.contracts.voice_turn_state_contract")
    assert_condition(voice_contract.TURN_TAKING_CONTROLLER == "voice-turn-state-machine", "wrong voice turn controller")
    assert_condition(
        set(voice_contract.VOICE_TURN_STATE_VALUES) == {"idle", "listening", "agent_thinking", "agent_speaking", "paused"},
        "voice turn states mismatch",
    )

    asr_gate = importlib.import_module("runtime.speech.asr_quality_gate")
    assert_condition(asr_gate.ASR_LOW_CONFIDENCE_THRESHOLD == 0.45, "wrong ASR low-confidence threshold")
    assert_condition(
        asr_gate.evaluate_asr_quality("what does your product do", 0.2)["reason"] == "low_confidence",
        "low-confidence ASR should reject before sales logic",
    )

    session_policy = importlib.import_module("runtime.core.live_voice_session_policy")
    for name in ["continuity_response", "anti_loop_response", "duplicate_response_repair"]:
        assert_condition(hasattr(session_policy, name), f"session policy missing {name}")


def validate_manifest() -> None:
    manifest = read_json(RUNTIME_MANIFEST)
    paths = {entry.get("path") for entry in manifest.get("runtime_entries", [])}
    for path in [
        "runtime/contracts/voice_turn_state_contract.py",
        "runtime/speech/asr_quality_gate.py",
        "runtime/core/live_voice_session_policy.py",
    ]:
        assert_condition(path in paths, f"runtime manifest missing {path}")


def validate_baseline(payload: dict[str, Any]) -> None:
    assert_condition(payload["live_demo_id"] == "LIVE-DEMO-002", "unexpected baseline id")
    assert_condition(payload["baseline_source"] == "LIVE-DEMO-001", "baseline should preserve LIVE-DEMO-001")
    assert_condition(payload["behavior_change_policy"] == "behavior_preserved", "baseline should preserve behavior")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")
    assert_condition(payload["provider_calls_made"] is False, "baseline must not call providers")
    assert_condition(payload["runtime_behavior_changed"] is False, "baseline capture must not change runtime behavior")
    assert_condition(payload["validator_pass_status"]["live_demo_001"] == "pass", "LIVE-DEMO-001 baseline validator must pass")

    categories = {case["category"] for case in payload["baseline_cases"]}
    assert_condition(EXPECTED_BASELINE_CATEGORIES.issubset(categories), categories)
    assert_condition(len(payload["baseline_cases"]) >= 12, "baseline should be compact but cover fixed behavior families")

    for case in payload["baseline_cases"]:
        assert_condition(case["pass"] is True, case)
        assert_condition(case["behavior_change_policy"] == "behavior_preserved", case)
        assert_condition(case["provider_agent_used"] is False, case)
        assert_condition(case["voice_cloning_used"] is False, case)
        assert_condition(case["runtime_behavior_changed"] is False, case)
        assert_condition(case["opens_prod_102"] is False, case)
        assert_condition(case["final_response"], case)

    packet_shape = set(payload["private_evidence_packet_shape"]["top_level_keys"])
    assert_condition(EXPECTED_PACKET_SHAPE_KEYS.issubset(packet_shape), packet_shape)
    assert_condition("quality_gate" in payload["private_evidence_packet_shape"]["asr_keys"], "ASR quality shape missing")
    assert_condition("voice_turn_state_received" in payload["private_evidence_packet_shape"]["turn_taking_keys"], "voice turn state shape missing")
    assert_condition("tts_delivery" in payload["private_evidence_packet_shape"]["packet_keys"], "TTS delivery shape missing")
    assert_condition(
        "customer_response_snapshot" in payload["private_evidence_packet_shape"]["dialogue_reasoner_async_enrichment_keys"],
        "async enrichment packet shape missing customer response snapshot",
    )
    assert_condition(
        "text_fingerprint" in payload["private_evidence_packet_shape"]["async_customer_response_snapshot_keys"],
        "async enrichment response snapshot must use fingerprint evidence",
    )

    compact_regressions = payload["compact_regression_coverage"]
    for key in [
        "repetition_prevention",
        "followup_continuity",
        "voice_delivery_propagation",
        "product_answer_routing",
        "asr_quality_handling",
        "callback_scheduling_boundary",
        "callback_workflow_disambiguation",
        "customer_echo_prevention",
        "seller_led_next_move",
        "seller_led_close_progression",
        "terminal_call_control_stop",
        "live_tts_fallback_voice_guard",
        "stale_session_greeting_relevance",
        "voice_consistency_across_turns",
        "agent_led_sales_opening",
        "qualification_steering",
        "sales_context_variety",
        "sales_emphasis_priority",
        "previous_question_clarification",
        "ambiguous_negative_clarification",
        "caller_identity_recall",
        "internal_repair_speech_blocked",
        "async_reasoning_enrichment_evidence",
    ]:
        assert_condition(compact_regressions.get(key) is True, f"missing compact regression {key}")

    echo_blocks = {
        "manual-tracking": ("manual tracking", "tracking leads manually"),
        "growth-plan": ("growth", "$59", "59 dollars", "fifty nine"),
        "small-team": ("for a small team", "small team"),
        "salesforce-boundary": ("salesforce", "it integrates", "yes"),
        "security-boundary": ("soc 2", "yes", "security"),
        "workflow-included": ("the workflow", "workflow"),
    }
    baseline_by_id = {case["case_id"]: case for case in payload["baseline_cases"]}
    for case_id, blocked_prefixes in echo_blocks.items():
        assert_condition(case_id in baseline_by_id, f"missing echo-prevention baseline case {case_id}")
        response = strip_leading_voice_filler(baseline_by_id[case_id]["final_response"])
        assert_condition(
            not response.startswith(blocked_prefixes),
            f"{case_id} still leads by echoing the buyer's stated topic: {baseline_by_id[case_id]['final_response']}",
        )
    growth_response = strip_leading_voice_filler(baseline_by_id["growth-plan"]["final_response"])
    assert_condition(
        not any(fragment in growth_response for fragment in ("$59", "59/month", "59 dollars", "fifty nine")),
        baseline_by_id["growth-plan"],
    )
    for case_id in {"product-explanation", "manual-tracking", "growth-plan", "small-team", "workflow-included"}:
        assert_condition(case_id in baseline_by_id, f"missing seller-led baseline case {case_id}")
        assert_condition(has_seller_led_next_move(baseline_by_id[case_id]["final_response"]), baseline_by_id[case_id])
    assert_condition("direct-price-seller-led" in baseline_by_id, "missing direct price seller-led baseline case")
    direct_price = baseline_by_id["direct-price-seller-led"]
    assert_condition(direct_price["sales_difficulty"] == "price-first-direct", direct_price)
    assert_condition("$29/month" in direct_price["final_response"] and "$59/month" in direct_price["final_response"], direct_price)
    assert_condition(has_seller_led_next_move(direct_price["final_response"]), direct_price)

    improvements = payload.get("intentional_improvements") or []
    assert_condition(improvements, "intentional improvement coverage missing")
    agent_open_cases = [case for case in improvements if case["category"] == "agent_led_sales_opening"]
    assert_condition(
        {case["case_id"] for case in agent_open_cases}
        >= {
            "agent-open-speaks-first",
            "agent-open-ack-steers-qualification",
            "agent-open-gap-to-workflow-review",
        },
        "agent-led sales opening improvement should cover opening, acknowledgement, and gap-to-value routing",
    )
    agent_open = next(case for case in agent_open_cases if case["case_id"] == "agent-open-speaks-first")
    assert_condition(agent_open["pass"] is True, agent_open)
    assert_condition(agent_open["continuity_reason"] == "agent_opening_started", agent_open)
    assert_condition(agent_open["dialogue_focus"] == "qualification", agent_open)
    assert_condition("Maya" in agent_open["final_response"], agent_open)
    assert_condition("Northstar Workflow Labs" in agent_open["final_response"], agent_open)
    assert_condition("RouteSignal" in agent_open["final_response"], agent_open)
    assert_condition("calling from" in agent_open["final_response"].lower(), agent_open)
    assert_condition("team behind" in agent_open["final_response"].lower(), agent_open)
    assert_condition("inbound demo follow-up" in agent_open["final_response"].lower(), agent_open)
    assert_condition("do you have a minute" in agent_open["final_response"].lower(), agent_open)
    assert_condition("price, fit" not in agent_open["final_response"].lower(), agent_open)
    assert_condition(has_sales_context_depth(agent_open["final_response"]), agent_open)
    assert_condition(has_sales_emphasis_priority(agent_open), agent_open)
    agent_ack = next(case for case in agent_open_cases if case["case_id"] == "agent-open-ack-steers-qualification")
    assert_condition(agent_ack["pass"] is True, agent_ack)
    assert_condition(agent_ack["continuity_reason"] == "proactive_qualification_guidance_after_acknowledgement", agent_ack)
    assert_condition(has_seller_led_next_move(agent_ack["final_response"]), agent_ack)
    assert_condition(has_sales_context_depth(agent_ack["final_response"]), agent_ack)
    assert_condition(has_sales_emphasis_priority(agent_ack), agent_ack)
    agent_gap = next(case for case in agent_open_cases if case["case_id"] == "agent-open-gap-to-workflow-review")
    assert_condition(agent_gap["pass"] is True, agent_gap)
    assert_condition(agent_gap["continuity_reason"] == "seller_gap_selected_for_qualification", agent_gap)
    assert_condition("short workflow review" in agent_gap["final_response"].lower(), agent_gap)
    assert_condition(has_seller_led_next_move(agent_gap["final_response"]), agent_gap)
    assert_condition(has_sales_context_depth(agent_gap["final_response"]), agent_gap)
    assert_condition(has_sales_emphasis_priority(agent_gap), agent_gap)

    callback_workflow_cases = [case for case in improvements if case["category"] == "callback_workflow_disambiguation"]
    assert_condition(
        {case["case_id"] for case in callback_workflow_cases}
        >= {"callback-gap-maps-to-value-not-scheduling", "callback-term-clarified-as-workflow"},
        "callback workflow disambiguation should cover gap selection and clarification",
    )
    callback_gap = next(case for case in callback_workflow_cases if case["case_id"] == "callback-gap-maps-to-value-not-scheduling")
    assert_condition(callback_gap["pass"] is True, callback_gap)
    assert_condition(callback_gap["continuity_reason"] == "seller_gap_selected_for_qualification", callback_gap)
    assert_condition(callback_gap["sales_difficulty"] != "callback-request", callback_gap)
    assert_condition(callback_workflow_not_scheduling(callback_gap["final_response"]), callback_gap)
    assert_condition(has_seller_led_next_move(callback_gap["final_response"]), callback_gap)
    assert_condition(has_sales_context_depth(callback_gap["final_response"]), callback_gap)
    assert_condition(has_sales_emphasis_priority(callback_gap), callback_gap)
    callback_clarification = next(case for case in callback_workflow_cases if case["case_id"] == "callback-term-clarified-as-workflow")
    assert_condition(callback_clarification["pass"] is True, callback_clarification)
    assert_condition(callback_clarification["continuity_reason"] == "callback_workflow_clarified", callback_clarification)
    assert_condition(callback_clarification["sales_difficulty"] != "callback-request", callback_clarification)
    assert_condition(callback_workflow_not_scheduling(callback_clarification["final_response"]), callback_clarification)
    assert_condition(has_seller_led_next_move(callback_clarification["final_response"]), callback_clarification)
    assert_condition(has_sales_context_depth(callback_clarification["final_response"]), callback_clarification)

    clarification_cases = [case for case in improvements if case["category"] == "previous_question_clarification"]
    assert_condition(clarification_cases, "previous-question clarification improvement missing")
    clarification = clarification_cases[0]
    lowered_clarification = clarification["final_response"].lower()
    assert_condition(clarification["pass"] is True, clarification)
    assert_condition(clarification["behavior_change_policy"] == "intentional_improvement", clarification)
    assert_condition(clarification["continuity_reason"] == "previous_question_clarified", clarification)
    assert_condition(any(fragment in lowered_clarification for fragment in {"i was asking", "i meant", "in plain terms"}), clarification)
    assert_condition(any(fragment in lowered_clarification for fragment in {"missed callbacks", "handoffs", "owner", "inbound demo"}), clarification)
    assert_condition("growth only matters" not in lowered_clarification, clarification)
    assert_condition("which part slips most" not in lowered_clarification, clarification)
    assert_condition("where does that break" not in lowered_clarification, clarification)
    assert_condition(has_seller_led_next_move(clarification["final_response"]), clarification)
    assert_condition(has_sales_context_depth(clarification["final_response"]), clarification)
    assert_condition(has_sales_emphasis_priority(clarification), clarification)

    negative_cases = [case for case in improvements if case["category"] == "ambiguous_negative_clarification"]
    assert_condition(
        {case["case_id"] for case in negative_cases} >= {"agent-open-negative-clarified", "qualification-negative-clarified"},
        "ambiguous negative clarification improvement missing",
    )
    for case in negative_cases:
        lowered = case["final_response"].lower()
        assert_condition(case["pass"] is True, case)
        assert_condition(case["behavior_change_policy"] == "intentional_improvement", case)
        assert_condition(case["continuity_reason"] == "ambiguous_negative_clarified", case)
        assert_condition(any(fragment in lowered for fragment in {"do you mean", "are you saying"}), case)
        assert_condition(any(fragment in lowered for fragment in {"not a good time", "none of those gaps", "not an issue"}), case)
        assert_condition(any(fragment in lowered for fragment in {"missed callbacks", "handoffs", "gaps"}), case)
        assert_condition("price, fit, timing" not in lowered, case)
        assert_condition("shared inbox leads" not in lowered, case)
        assert_condition("owner routing, callback reminders" not in lowered, case)

    identity_cases = [case for case in improvements if case["category"] == "caller_identity_recall"]
    assert_condition(identity_cases, "caller identity recall improvement missing")
    identity = identity_cases[0]
    lowered_identity = identity["final_response"].lower()
    assert_condition(identity["pass"] is True, identity)
    assert_condition(identity["continuity_reason"] == "caller_identity_recalled", identity)
    assert_condition("northstar workflow labs" in lowered_identity, identity)
    assert_condition("routesignal crm" in lowered_identity, identity)
    assert_condition("calling from" in lowered_identity, identity)
    assert_condition("price, fit, timing" not in lowered_identity, identity)
    assert_condition("main question" not in lowered_identity, identity)

    repair_block_cases = [case for case in improvements if case["category"] == "internal_repair_speech_blocked"]
    assert_condition(repair_block_cases, "internal repair speech block improvement missing")
    for case in repair_block_cases:
        lowered = case["final_response"].lower()
        assert_condition(case["pass"] is True, case)
        assert_condition(case["behavior_change_policy"] == "intentional_improvement", case)
        assert_condition("avoid repeating" not in lowered, case)
        assert_condition("same question" not in lowered, case)
        assert_condition("keep the next step narrow" not in lowered, case)
        assert_condition("candidate_response" not in lowered, case)
        assert_condition("internal" not in lowered, case)
        assert_condition("runtime" not in lowered, case)

    variety_cases = [case for case in improvements if case["category"] == "sales_context_variety_and_emphasis"]
    assert_condition(
        {case["case_id"] for case in variety_cases} >= {"agent-open-followup-variety"},
        "sales context variety and emphasis improvement missing",
    )
    variety = next(case for case in variety_cases if case["case_id"] == "agent-open-followup-variety")
    assert_condition(variety["pass"] is True, variety)
    assert_condition(variety["behavior_change_policy"] == "intentional_improvement", variety)
    assert_condition(variety.get("response_count", 0) >= 5, variety)
    assert_condition(variety.get("unique_response_count") == variety.get("response_count"), variety)
    assert_condition(len(variety.get("observed_sales_concepts") or []) >= 7, variety)
    assert_condition(variety.get("all_responses_context_depth") is True, variety)
    assert_condition(variety.get("all_responses_seller_led_next_move") is True, variety)
    assert_condition(variety.get("all_responses_sales_emphasis_priority") is True, variety)
    assert_condition(has_sales_context_depth(variety["final_response"]), variety)
    assert_condition(has_sales_emphasis_priority(variety), variety)

    opening_cases = [case for case in improvements if case["category"] == "sales_opening_permission_check"]
    assert_condition(opening_cases, "sales opening permission-check improvement missing")
    for case in opening_cases:
        assert_condition(case["pass"] is True, case)
        assert_condition(case["behavior_change_policy"] == "intentional_improvement", case)
        assert_condition("Northstar Workflow Labs" in case["final_response"], case)
        assert_condition("RouteSignal" in case["final_response"], case)
        assert_condition("do you have a minute" in case["final_response"].lower(), case)
        assert_condition("price, fit" not in case["final_response"].lower(), case)
        assert_condition("calling from" in case["final_response"].lower(), case)
        assert_condition("team behind" in case["final_response"].lower(), case)
        assert_condition(has_sales_context_depth(case["final_response"]), case)
        assert_condition(has_sales_emphasis_priority(case), case)

    stale_greeting_cases = [case for case in improvements if case["category"] == "stale_session_greeting_relevance"]
    assert_condition(stale_greeting_cases, "stale-session greeting relevance improvement missing")
    stale_greeting = stale_greeting_cases[0]
    assert_condition(stale_greeting["pass"] is True, stale_greeting)
    assert_condition(stale_greeting["continuity_reason"] == "opening_greeting_answered", stale_greeting)
    assert_condition("do you have a minute" in stale_greeting["final_response"].lower(), stale_greeting)
    assert_condition("main question about price, fit, timing" not in stale_greeting["final_response"].lower(), stale_greeting)

    voice_consistency_cases = [case for case in improvements if case["category"] == "voice_consistency_across_turns"]
    assert_condition(voice_consistency_cases, "voice consistency improvement missing")
    voice_consistency = voice_consistency_cases[0]
    assert_condition(voice_consistency["pass"] is True, voice_consistency)
    assert_condition(voice_consistency["tts_voice_consistency_mode"] == "live-demo-stable", voice_consistency)
    assert_condition(voice_consistency["tts_voice_settings_source"] == "live_demo_stable_profile", voice_consistency)

    proactive_cases = [case for case in improvements if case["category"] == "proactive_guidance_after_acknowledgement"]
    assert_condition(len(proactive_cases) >= 2, "proactive guidance improvement should cover repeated acknowledgements")
    seen_responses = set()
    for case in proactive_cases:
        assert_condition(case["pass"] is True, case)
        assert_condition(case["behavior_change_policy"] == "intentional_improvement", case)
        assert_condition(case["continuity_reason"] == "proactive_price_guidance_after_acknowledgement", case)
        assert_condition("Starter is $29/month for basic routing" not in case["final_response"], case)
        assert_condition(has_seller_led_next_move(case["final_response"]), case)
        assert_condition(case["final_response"] not in seen_responses, case)
        seen_responses.add(case["final_response"])

    close_cases = [case for case in improvements if case["category"] == "seller_led_close_progression"]
    assert_condition(close_cases, "seller-led close progression improvement missing")
    close_case = close_cases[0]
    assert_condition(close_case["pass"] is True, close_case)
    assert_condition(close_case["behavior_change_policy"] == "intentional_improvement", close_case)
    assert_condition(close_case["continuity_reason"] == "seller_gap_selected_for_price", close_case)
    assert_condition("short workflow review" in close_case["final_response"].lower(), close_case)
    assert_condition(has_seller_led_next_move(close_case["final_response"]), close_case)
    assert_condition("book a demo" not in close_case["final_response"].lower(), close_case)

    progression_cases = [case for case in improvements if case["category"] == "multi_topic_non_repeating_progression"]
    assert_condition(
        {case["case_id"] for case in progression_cases}
        >= {"guided-price-progression", "guided-fit-progression", "guided-timing-progression", "guided-features-progression"},
        "multi-topic progression improvement should cover price, fit, timing, and features",
    )
    for case in progression_cases:
        assert_condition(case["pass"] is True, case)
        assert_condition(case["behavior_change_policy"] == "intentional_improvement", case)
        assert_condition("main question about price, fit, timing" not in case["final_response"].lower(), case)

    callback_cases = [case for case in improvements if case["category"] == "callback_scheduling_boundary"]
    assert_condition(
        {case["case_id"] for case in callback_cases}
        >= {"no-time-asks-for-callback-time", "callback-time-confirms-and-ends"},
        "callback scheduling improvement should cover no-time and supplied-time turns",
    )
    no_time = next(case for case in callback_cases if case["case_id"] == "no-time-asks-for-callback-time")
    assert_condition(no_time["pass"] is True, no_time)
    assert_condition(no_time["continuity_reason"] == "callback_request_time_needed", no_time)
    assert_condition(no_time["behavior_change_policy"] == "intentional_improvement", no_time)
    assert_condition("main question about price, fit, timing" not in no_time["final_response"].lower(), no_time)
    callback_time = next(case for case in callback_cases if case["case_id"] == "callback-time-confirms-and-ends")
    assert_condition(callback_time["pass"] is True, callback_time)
    assert_condition(callback_time["continuity_reason"] == "callback_time_confirmed", callback_time)
    assert_condition(callback_time["behavior_change_policy"] == "intentional_improvement", callback_time)
    assert_condition(callback_time["final_response"].lower().count("callback") >= 1, callback_time)
    assert_condition("goodbye" in callback_time["final_response"].lower(), callback_time)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    methodology = METHODOLOGY_LOG.read_text(encoding="utf-8")
    doc = DOC_PATH.read_text(encoding="utf-8")
    for marker in [
        "LIVE-DEMO-002",
        "runtime extraction baseline",
        "behavior_preserved",
        "intentional_improvement",
        "proactive_price_guidance_after_acknowledgement",
        "sales_opening_permission_check",
        "multi_topic_non_repeating_progression",
        "callback_scheduling_boundary",
        "callback_workflow_disambiguation",
        "callback_workflow_clarified",
        "callback_request_time_needed",
        "callback_time_confirmed",
        "customer_echo_prevention",
        "seller_led_next_move",
        "seller_led_close_progression",
        "terminal_call_control_stop",
        "live_tts_fallback_voice_guard",
        "stale_session_greeting_relevance",
        "voice_consistency_across_turns",
        "agent_led_sales_opening",
        "qualification_steering",
        "caller_identity",
        "target_account_context",
        "sales_context_variety",
        "sales_emphasis_priority",
        "sales_context_variety_and_emphasis",
        "previous_question_clarification",
        "ambiguous_negative_clarification",
        "caller_identity_recall",
        "internal_repair_speech_blocked",
        "Maya",
        "calling from Northstar Workflow Labs, the team behind RouteSignal CRM",
        "LIVE-DEMO-001",
        "voice_turn_state",
        "ASR quality",
    ]:
        assert_condition(marker in doc, f"doc missing {marker}")
    assert_condition("validate_live_demo_002_runtime_extraction_baseline.py" in commands, "COMMANDS missing LIVE-DEMO-002 validator")
    assert_condition("LIVE_DEMO_002_RUNTIME_EXTRACTION_BASELINE.md" in index, "checkpoint index missing LIVE-DEMO-002 doc")
    assert_condition("LIVE-DEMO-002 runtime extraction baseline" in methodology, "methodology missing LIVE-DEMO-002 entry")


def main() -> None:
    assert_condition(RUNNER.exists(), "LIVE-DEMO-002 runner missing")
    assert_condition(DOC_PATH.exists(), "LIVE-DEMO-002 doc missing")
    validate_runtime_modules()
    validate_manifest()

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(BASELINE_PATH.exists(), "baseline JSON missing")
    assert_condition(REPORT_PATH.exists(), "baseline report missing")

    payload = read_json(BASELINE_PATH)
    validate_baseline(payload)
    validate_docs()

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("LIVE-DEMO-002 runtime extraction baseline" in report_text, "report title missing")
    assert_condition("behavior_preserved" in report_text, "report behavior policy missing")

    print("LIVE-DEMO-002 runtime extraction baseline validation passed.")


if __name__ == "__main__":
    main()
