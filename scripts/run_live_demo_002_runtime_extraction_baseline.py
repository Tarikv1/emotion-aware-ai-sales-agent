#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CASES_PATH,
    build_turn_packet,
)


LIVE_DEMO_ID = "LIVE-DEMO-002"
BASELINE_SOURCE = "LIVE-DEMO-001"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / LIVE_DEMO_ID
BASELINE_PATH = OUTPUT_DIR / "runtime_extraction_baseline.json"
REPORT_PATH = OUTPUT_DIR / "runtime_extraction_baseline.md"
PRIVATE_OUT = ROOT / ".tmp" / LIVE_DEMO_ID / "private"
VALIDATOR = ROOT / "scripts" / "validate_live_demo_001_agent_voice_call.py"


def safe_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ELEVENLABS_API_KEY", None)
    env.pop("ELEVENLABS_VOICE_ID", None)
    env.pop("ELEVENLABS_VOICE_ID_EN", None)
    return env


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_live_demo_001() -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        env=safe_env(),
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    return {
        "live_demo_001": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip().splitlines()[-3:],
        "stderr_tail": completed.stderr.strip().splitlines()[-3:],
    }


def append_session_turn(session_state: dict[str, Any], packet: dict[str, Any]) -> None:
    session_state["turns"].append(
        {
            "transcript": packet["transcript"],
            "summary": packet["summary"],
            "continuity": packet["demo_session_continuity"],
        }
    )


def make_packet(
    transcript: str,
    *,
    session_id: str,
    session_state: dict[str, Any] | None = None,
    live_tts: bool = False,
    force_key_missing: bool = False,
    input_type: str = "speech-final",
    asr_confidence: float | None = None,
    voice_turn_state: str | None = "listening",
) -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type=input_type,
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=PRIVATE_OUT,
        live_tts=live_tts,
        force_key_missing=force_key_missing,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=session_state or {"turns": []},
        asr_confidence=asr_confidence,
        voice_turn_state=voice_turn_state,
    )


def common_case_fields(packet: dict[str, Any]) -> dict[str, Any]:
    tts = packet["packet"]["tts_delivery"]
    voice = packet["packet"]["voice_delivery"]
    continuity = packet["demo_session_continuity"]
    return {
        "transcript": packet["transcript"],
        "final_response": packet["summary"]["final_response"],
        "sales_difficulty": packet["summary"]["sales_difficulty"],
        "continuity_reason": continuity.get("reason"),
        "dialogue_focus": continuity.get("dialogue_focus"),
        "asr_quality_gate": packet["asr"]["quality_gate"],
        "voice_turn_state_received": packet["turn_taking"]["voice_turn_state_received"],
        "tts_provider_calls_made": tts["provider_calls_made"],
        "tts_generated_text_sent_to_provider": tts["generated_text_sent_to_provider"],
        "tts_audio_file_created": tts["audio_file_created"],
        "tts_fallback_reason": tts["fallback_reason"],
        "tts_input_source": tts["tts_input_source"],
        "tts_voice_settings": tts["voice_settings"],
        "tts_voice_settings_source": tts.get("voice_settings_source"),
        "tts_voice_consistency_mode": tts.get("voice_consistency_mode"),
        "voice_prosody_cue_targets": [
            str(cue.get("target") or cue.get("after") or "")
            for cue in voice["prosody"]["prosody_plan"]
        ],
        "voice_allowed_emphasis_count": voice["voice_listening_calibration"]["emphasis_guard"][
            "allowed_emphasis_count"
        ],
        "voice_final_response_unchanged": voice["final_response_unchanged"],
        "voice_validation_passed": voice["validation"]["passed"],
        "provider_agent_used": packet["provider_agent_used"],
        "voice_cloning_used": packet["voice_cloning_used"],
        "runtime_behavior_changed": packet["runtime_behavior_changed"],
        "opens_prod_102": packet["opens_prod_102"],
    }


def record_case(
    cases: list[dict[str, Any]],
    *,
    category: str,
    case_id: str,
    packet: dict[str, Any],
    passed: bool,
    expectation: str,
    behavior_change_policy: str = "behavior_preserved",
    extra: dict[str, Any] | None = None,
) -> None:
    case = {
        "case_id": case_id,
        "category": category,
        "expectation": expectation,
        "pass": bool(passed),
        "behavior_change_policy": behavior_change_policy,
        **common_case_fields(packet),
    }
    if extra:
        case.update(extra)
    cases.append(case)


def contains_any(text: str, fragments: set[str]) -> bool:
    lowered = text.lower()
    return any(fragment.lower() in lowered for fragment in fragments)


def strip_leading_voice_filler(text: str) -> str:
    lowered = text.strip().lower()
    return lowered.removeprefix("um, ").removeprefix("uh, ").removeprefix("well, ").removeprefix("so, ")


def avoids_leading_echo(text: str, blocked_prefixes: tuple[str, ...]) -> bool:
    if not blocked_prefixes:
        return True
    lowered = strip_leading_voice_filler(text)
    return not lowered.startswith(tuple(prefix.lower() for prefix in blocked_prefixes))


def avoids_customer_price_fact_echo(text: str) -> bool:
    lowered = strip_leading_voice_filler(text)
    return not any(fragment in lowered for fragment in ("$59", "59/month", "59 dollars", "fifty nine"))


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


def clarifies_previous_question(text: str) -> bool:
    lowered = text.lower()
    return (
        any(fragment in lowered for fragment in {"i was asking", "i meant", "in plain terms"})
        and any(fragment in lowered for fragment in {"missed callbacks", "handoffs", "owner", "inbound demo"})
        and "growth only matters" not in lowered
        and "which part slips most" not in lowered
        and "where does that break" not in lowered
        and "?" in text
    )


def clarifies_negative_reply(text: str) -> bool:
    lowered = text.lower()
    return (
        any(fragment in lowered for fragment in {"do you mean", "are you saying"})
        and any(fragment in lowered for fragment in {"not a good time", "none of those gaps", "not an issue"})
        and any(fragment in lowered for fragment in {"missed callbacks", "handoffs", "gaps"})
        and "price, fit, timing" not in lowered
        and "shared inbox leads" not in lowered
        and "owner routing, callback reminders" not in lowered
        and "?" in text
    )


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


def recalls_caller_identity(text: str) -> bool:
    lowered = text.lower()
    return (
        "northstar workflow labs" in lowered
        and "routesignal crm" in lowered
        and "calling from" in lowered
        and "price, fit, timing" not in lowered
        and "main question" not in lowered
    )


def blocks_internal_repair_wording(text: str) -> bool:
    lowered = text.lower()
    return not any(
        fragment in lowered
        for fragment in {
            "avoid repeating",
            "same question",
            "keep the next step narrow",
            "candidate_response",
            "decision log",
            "guardrail",
            "internal",
            "runtime",
        }
    )


def call_context_recovered(text: str) -> bool:
    lowered = text.lower()
    return (
        "?" in text
        and "main question about price, fit, timing" not in lowered
        and "price, fit, timing, or exact product details" not in lowered
        and "to make this useful" not in lowered
        and blocks_internal_repair_wording(text)
        and contains_any(text, {"one question", "i called to check", "quick check", "short means", "not being clear"})
        and contains_any(text, {"inbound demo", "demo follow-up", "callback reminder", "handoff", "owner"})
    )


def response_reopens_focus_menu(response: str) -> bool:
    lowered = response.lower()
    return (
        "main question about price, fit, timing" in lowered
        or "bigger concern" in lowered
        or "main concern whether this is relevant for your situation" in lowered
    )


def is_sales_opening_response(response: str) -> bool:
    lowered = response.lower()
    return (
        any(fragment in lowered for fragment in {"do you have a minute", "is now a bad time", "quick question"})
        and "calling from" in lowered
        and "team behind" in lowered
        and any(fragment in response for fragment in {"Northstar Workflow Labs", "RouteSignal"})
        and any(fragment in lowered for fragment in {"missed callback", "missed follow-up", "handoff", "routing"})
        and "?" in response
        and "price, fit" not in lowered
        and "what do you want to check first" not in lowered
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


def has_sales_emphasis_priority(packet: dict[str, Any]) -> bool:
    voice = packet["packet"]["voice_delivery"]
    targets = [
        str(cue.get("target") or cue.get("after") or "").lower()
        for cue in voice["prosody"]["prosody_plan"]
    ]
    blocked = {"hi", "hello", "do you have a minute", "this is northstar", "calling from northstar"}
    important = {"missed callback", "callback", "handoff", "routing", "owner", "workflow review", "inbound demo"}
    return (
        voice["voice_listening_calibration"]["emphasis_guard"]["allowed_emphasis_count"] >= 1
        and all(not any(target.startswith(item) for item in blocked) for target in targets)
        and any(any(fragment in target for fragment in important) for target in targets)
    )


def build_baseline_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    direct_price = make_packet("How much does it cost?", session_id=f"{LIVE_DEMO_ID}-direct-price")
    direct_price_response = direct_price["summary"]["final_response"]
    record_case(
        cases,
        category="direct_price_answer_routing",
        case_id="direct-price-seller-led",
        packet=direct_price,
        passed=direct_price["summary"]["sales_difficulty"] == "price-first-direct"
        and contains_any(direct_price_response, {"$29/month", "$59/month"})
        and has_seller_led_next_move(direct_price_response)
        and not response_reopens_focus_menu(direct_price_response),
        expectation="direct price question should answer approved prices and ask one diagnostic buyer-led next move",
    )

    product_questions = [
        (
            "product-explanation",
            "What does your product actually do?",
            "campaign_depth_product_explanation_answered",
            {"routes leads", "lead capture", "handoff", "follow-up"},
            (),
        ),
        (
            "manual-tracking",
            "Why would I use this instead of tracking leads manually?",
            "campaign_depth_manual_tracking_answered",
            {"manual", "handoff", "follow-up"},
            ("manual tracking", "tracking leads manually"),
        ),
        (
            "growth-plan",
            "What do I get for fifty nine dollars?",
            "campaign_depth_growth_plan_answered",
            {"priority routing", "reminders", "handoff review"},
            ("growth", "$59", "59 dollars", "fifty nine"),
        ),
        (
            "small-team",
            "Is this worth it for a small team?",
            "campaign_depth_small_team_fit_answered",
            {"small team", "starter", "missed"},
            ("for a small team", "small team"),
        ),
        (
            "unnecessary-specialist",
            "Do I need to talk to a specialist?",
            "campaign_depth_unnecessary_handoff_answered",
            {"not for basics", "price", "fit", "workflow"},
            (),
        ),
        (
            "salesforce-boundary",
            "Does it integrate with Salesforce?",
            "campaign_depth_integration_boundary_answered",
            {"salesforce", "exact setup", "verify"},
            ("salesforce", "it integrates", "yes"),
        ),
        (
            "security-boundary",
            "Are you SOC 2 certified?",
            "campaign_depth_security_boundary_answered",
            {"cannot claim", "security", "verified"},
            ("soc 2", "yes", "security"),
        ),
        (
            "workflow-included",
            "What is included in the workflow?",
            "campaign_depth_workflow_scope_answered",
            {"lead capture", "routing", "reminders", "handoff review"},
            ("the workflow", "workflow"),
        ),
    ]
    for case_id, transcript, expected_reason, expected_fragments, blocked_prefixes in product_questions:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-{case_id}")
        response = packet["summary"]["final_response"]
        no_echo_passed = avoids_leading_echo(response, blocked_prefixes)
        if case_id == "growth-plan":
            no_echo_passed = no_echo_passed and avoids_customer_price_fact_echo(response)
        seller_led_passed = True
        if case_id in {"product-explanation", "manual-tracking", "growth-plan", "small-team", "workflow-included"}:
            seller_led_passed = has_seller_led_next_move(response)
        record_case(
            cases,
            category="product_answer_routing",
            case_id=case_id,
            packet=packet,
            passed=packet["demo_session_continuity"]["reason"] == expected_reason
            and contains_any(response, expected_fragments)
            and no_echo_passed
            and seller_led_passed,
            expectation=f"route to {expected_reason} without generic handoff",
        )

    observed_state: dict[str, Any] = {"turns": []}
    observed_sequence = [
        ("observed-greeting", "hey how's it going", None),
        ("observed-price", "first of all let's start with the price", "focus_shift_to_price_from_qualification"),
        (
            "observed-effort-shift",
            "my main concern is whether reviewing options is worth my time or not",
            "focus_shift_to_effort_from_price",
        ),
        (
            "observed-effort-persisted",
            "it's about whether a viewing options is worth my time",
            {"resolved_effort_focus_persisted", "duplicate_response_prevented_with_effort_progression"},
        ),
    ]
    prior_response: str | None = None
    for case_id, transcript, expected_reason in observed_sequence:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-observed", session_state=observed_state)
        reason = packet["demo_session_continuity"]["reason"]
        response = packet["summary"]["final_response"]
        if expected_reason is None:
            passed = True
        elif isinstance(expected_reason, set):
            passed = reason in expected_reason
        else:
            passed = reason == expected_reason
        passed = passed and "bigger concern" not in response.lower()
        if prior_response is not None and case_id == "observed-effort-persisted":
            passed = passed and response != prior_response
        record_case(
            cases,
            category="followup_continuity",
            case_id=case_id,
            packet=packet,
            passed=passed,
            expectation="preserve observed live follow-up focus without reopening old loops",
        )
        append_session_turn(observed_state, packet)
        prior_response = response

    fit_state: dict[str, Any] = {"turns": []}
    fit_responses: set[str] = set()
    fit_sequence = [
        ("fit-greeting", "hey how's it going"),
        ("fit-selected", "let's talk about the fit"),
        ("fit-price-deferred", "so it's mostly about the situation we can talk about the price later on"),
        ("fit-repeat", "talk about fit if the fit is good"),
        ("fit-relevance", "I want to talk about whether this is relevant for my situation or not"),
    ]
    for case_id, transcript in fit_sequence:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-fit", session_state=fit_state)
        response = packet["summary"]["final_response"]
        current_menu_count = sum(
            1
            for turn in [*fit_state["turns"], {"summary": packet["summary"]}]
            if response_reopens_focus_menu(str((turn.get("summary") or {}).get("final_response") or ""))
        )
        passed = current_menu_count <= 1 and response not in fit_responses
        if case_id != "fit-greeting":
            passed = passed and packet["demo_session_continuity"].get("dialogue_focus") == "fit"
        record_case(
            cases,
            category="anti_loop",
            case_id=case_id,
            packet=packet,
            passed=passed,
            expectation="keep fit sequence to one focus menu and no repeated final responses",
        )
        fit_responses.add(response)
        append_session_turn(fit_state, packet)

    dry_voice = make_packet(
        "What does your product actually do?",
        session_id=f"{LIVE_DEMO_ID}-voice-dry",
        live_tts=False,
        force_key_missing=False,
    )
    record_case(
        cases,
        category="voice_delivery_propagation",
        case_id="voice-dry-run",
        packet=dry_voice,
        passed=dry_voice["packet"]["tts_delivery"]["provider_calls_made"] is False
        and dry_voice["packet"]["voice_delivery"]["final_response_unchanged"] is True,
        expectation="dry-run voice packet preserves final response and makes no provider call",
    )
    forced_voice = make_packet(
        "What does your product actually do?",
        session_id=f"{LIVE_DEMO_ID}-voice-forced-missing-key",
        live_tts=True,
        force_key_missing=True,
    )
    record_case(
        cases,
        category="voice_delivery_propagation",
        case_id="voice-forced-missing-key",
        packet=forced_voice,
        passed=forced_voice["packet"]["tts_delivery"]["provider_calls_made"] is False
        and forced_voice["packet"]["tts_delivery"]["fallback_reason"] == "forced-key-missing"
        and forced_voice["packet"]["voice_delivery"]["final_response_unchanged"] is True,
        expectation="forced missing key path preserves voice delivery propagation without provider call",
    )

    low_confidence = make_packet(
        "what does your product actually do",
        session_id=f"{LIVE_DEMO_ID}-asr-low-confidence",
        asr_confidence=0.2,
    )
    record_case(
        cases,
        category="asr_quality_handling",
        case_id="asr-low-confidence",
        packet=low_confidence,
        passed=low_confidence["asr"]["quality_gate"]["accepted"] is False
        and low_confidence["asr"]["quality_gate"]["reason"] == "low_confidence"
        and low_confidence["demo_session_continuity"]["reason"] == "asr_low_confidence_repair",
        expectation="low-confidence transcript stops before sales logic",
    )
    clear_confidence = make_packet(
        "what does your product actually do",
        session_id=f"{LIVE_DEMO_ID}-asr-clear-confidence",
        asr_confidence=0.82,
    )
    record_case(
        cases,
        category="asr_quality_handling",
        case_id="asr-clear-confidence",
        packet=clear_confidence,
        passed=clear_confidence["asr"]["quality_gate"]["accepted"] is True
        and clear_confidence["demo_session_continuity"]["reason"] == "campaign_depth_product_explanation_answered",
        expectation="clear-confidence transcript enters product-answer routing",
    )
    fragment = make_packet(
        "it's about the",
        session_id=f"{LIVE_DEMO_ID}-asr-fragment",
        session_state={"turns": []},
    )
    record_case(
        cases,
        category="asr_quality_handling",
        case_id="asr-fragment",
        packet=fragment,
        passed=fragment["demo_session_continuity"]["reason"] == "asr_fragment_repair",
        expectation="obvious STT fragment asks for clean repeat instead of entering sales logic",
    )

    return cases


def build_intentional_improvement_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    agent_open = make_packet(
        "__agent_open__",
        session_id=f"{LIVE_DEMO_ID}-agent-led-opening",
        input_type="agent-open",
        voice_turn_state="idle",
    )
    record_case(
        cases,
        category="agent_led_sales_opening",
        case_id="agent-open-speaks-first",
        packet=agent_open,
        passed=agent_open["demo_session_continuity"]["reason"] == "agent_opening_started"
        and agent_open["demo_session_continuity"].get("dialogue_focus") == "qualification"
        and is_sales_opening_response(agent_open["summary"]["final_response"])
        and has_sales_context_depth(agent_open["summary"]["final_response"])
        and has_sales_emphasis_priority(agent_open),
        expectation="Start Conversation should route an agent-open turn that speaks before browser ASR starts",
        behavior_change_policy="intentional_improvement",
    )
    qualification_state: dict[str, Any] = {"turns": []}
    append_session_turn(qualification_state, agent_open)
    clarification_state: dict[str, Any] = {"turns": []}
    append_session_turn(clarification_state, agent_open)
    qualification_clarification = make_packet(
        "No, I did not really understand what you asked before that.",
        session_id=f"{LIVE_DEMO_ID}-agent-led-clarification",
        session_state=clarification_state,
    )
    record_case(
        cases,
        category="previous_question_clarification",
        case_id="agent-open-question-clarified",
        packet=qualification_clarification,
        passed=qualification_clarification["demo_session_continuity"]["reason"] == "previous_question_clarified"
        and clarifies_previous_question(qualification_clarification["summary"]["final_response"])
        and has_sales_context_depth(qualification_clarification["summary"]["final_response"])
        and has_seller_led_next_move(qualification_clarification["summary"]["final_response"])
        and has_sales_emphasis_priority(qualification_clarification),
        expectation="buyer clarification request should explain the previous sales question instead of advancing canned qualification copy",
        behavior_change_policy="intentional_improvement",
    )
    identity_recall = make_packet(
        "where were you calling from again?",
        session_id=f"{LIVE_DEMO_ID}-caller-identity-recall",
        session_state={"turns": list(clarification_state["turns"])},
    )
    record_case(
        cases,
        category="caller_identity_recall",
        case_id="caller-identity-recalled",
        packet=identity_recall,
        passed=identity_recall["demo_session_continuity"]["reason"] == "caller_identity_recalled"
        and recalls_caller_identity(identity_recall["summary"]["final_response"])
        and blocks_internal_repair_wording(identity_recall["summary"]["final_response"]),
        expectation="buyer identity recall should answer where the agent is calling from instead of reopening menus",
        behavior_change_policy="intentional_improvement",
    )
    opening_negative = make_packet(
        "no",
        session_id=f"{LIVE_DEMO_ID}-agent-led-negative",
        session_state={"turns": list(clarification_state["turns"])},
    )
    record_case(
        cases,
        category="ambiguous_negative_clarification",
        case_id="agent-open-negative-clarified",
        packet=opening_negative,
        passed=opening_negative["demo_session_continuity"]["reason"] == "ambiguous_negative_clarified"
        and clarifies_negative_reply(opening_negative["summary"]["final_response"]),
        expectation="bare no after the opener should clarify what was rejected instead of reopening menus or advancing qualification copy",
        behavior_change_policy="intentional_improvement",
    )
    qualification_ack = make_packet(
        "okay",
        session_id=f"{LIVE_DEMO_ID}-agent-led-opening",
        session_state=qualification_state,
    )
    record_case(
        cases,
        category="agent_led_sales_opening",
        case_id="agent-open-ack-steers-qualification",
        packet=qualification_ack,
        passed=qualification_ack["demo_session_continuity"]["reason"]
        == "proactive_qualification_guidance_after_acknowledgement"
        and has_seller_led_next_move(qualification_ack["summary"]["final_response"])
        and contains_any(
            qualification_ack["summary"]["final_response"],
            {"callback", "callbacks", "handoff", "handoffs", "routing", "missed follow-up"},
        )
        and has_sales_context_depth(qualification_ack["summary"]["final_response"])
        and has_sales_emphasis_priority(qualification_ack),
        expectation="weak acknowledgement after the agent-led opener should continue qualification instead of waiting for buyer questions",
        behavior_change_policy="intentional_improvement",
    )
    qualification_negative = make_packet(
        "no",
        session_id=f"{LIVE_DEMO_ID}-qualification-negative",
        session_state={
            "turns": [
                *qualification_state["turns"],
                {
                    "transcript": qualification_ack["transcript"],
                    "summary": qualification_ack["summary"],
                    "continuity": qualification_ack["demo_session_continuity"],
                },
            ]
        },
    )
    record_case(
        cases,
        category="ambiguous_negative_clarification",
        case_id="qualification-negative-clarified",
        packet=qualification_negative,
        passed=qualification_negative["demo_session_continuity"]["reason"] == "ambiguous_negative_clarified"
        and clarifies_negative_reply(qualification_negative["summary"]["final_response"]),
        expectation="bare no after qualification should clarify timing-vs-problem rejection instead of pushing another sales line",
        behavior_change_policy="intentional_improvement",
    )
    security_state: dict[str, Any] = {"turns": []}
    security_boundary = make_packet(
        "Does it have SOC 2?",
        session_id=f"{LIVE_DEMO_ID}-security-followup",
        session_state=security_state,
    )
    append_session_turn(security_state, security_boundary)
    security_followup = make_packet(
        "what else should I know?",
        session_id=f"{LIVE_DEMO_ID}-security-followup",
        session_state=security_state,
    )
    record_case(
        cases,
        category="internal_repair_speech_blocked",
        case_id="security-followup-no-internal-repair-speech",
        packet=security_followup,
        passed=security_followup["demo_session_continuity"]["reason"] == "resolved_security_focus_progressed"
        and blocks_internal_repair_wording(security_followup["summary"]["final_response"])
        and "security" in security_followup["summary"]["final_response"].lower(),
        expectation="non-core focus follow-ups should never speak anti-loop or internal repair wording",
        behavior_change_policy="intentional_improvement",
    )
    append_session_turn(qualification_state, qualification_ack)
    qualification_gap = make_packet(
        "handoffs are the problem",
        session_id=f"{LIVE_DEMO_ID}-agent-led-opening",
        session_state=qualification_state,
    )
    record_case(
        cases,
        category="agent_led_sales_opening",
        case_id="agent-open-gap-to-workflow-review",
        packet=qualification_gap,
        passed=qualification_gap["demo_session_continuity"]["reason"] == "seller_gap_selected_for_qualification"
        and contains_any(qualification_gap["summary"]["final_response"], {"handoff review", "short workflow review", "next step"})
        and has_seller_led_next_move(qualification_gap["summary"]["final_response"])
        and has_sales_context_depth(qualification_gap["summary"]["final_response"])
        and has_sales_emphasis_priority(qualification_gap),
        expectation="named gap after agent-led qualification should map to value and a consented workflow review",
        behavior_change_policy="intentional_improvement",
    )

    qualification_callback_gap = make_packet(
        "I have to say it's probably the callbacks",
        session_id=f"{LIVE_DEMO_ID}-callback-workflow-disambiguation",
        session_state=qualification_state,
    )
    record_case(
        cases,
        category="callback_workflow_disambiguation",
        case_id="callback-gap-maps-to-value-not-scheduling",
        packet=qualification_callback_gap,
        passed=qualification_callback_gap["demo_session_continuity"]["reason"] == "seller_gap_selected_for_qualification"
        and qualification_callback_gap["summary"]["sales_difficulty"] != "callback-request"
        and callback_workflow_not_scheduling(qualification_callback_gap["summary"]["final_response"])
        and has_seller_led_next_move(qualification_callback_gap["summary"]["final_response"])
        and has_sales_context_depth(qualification_callback_gap["summary"]["final_response"])
        and has_sales_emphasis_priority(qualification_callback_gap),
        expectation="callback gap mentions should map to product workflow value instead of callback scheduling",
        behavior_change_policy="intentional_improvement",
    )
    callback_clarification_state = {
        "turns": [
            *qualification_state["turns"],
            {
                "transcript": qualification_callback_gap["transcript"],
                "summary": qualification_callback_gap["summary"],
                "continuity": qualification_callback_gap["demo_session_continuity"],
            },
        ]
    }
    callback_clarification = make_packet(
        "what do you mean by callbacks",
        session_id=f"{LIVE_DEMO_ID}-callback-workflow-disambiguation",
        session_state=callback_clarification_state,
    )
    record_case(
        cases,
        category="callback_workflow_disambiguation",
        case_id="callback-term-clarified-as-workflow",
        packet=callback_clarification,
        passed=callback_clarification["demo_session_continuity"]["reason"] == "callback_workflow_clarified"
        and callback_clarification["summary"]["sales_difficulty"] != "callback-request"
        and callback_workflow_not_scheduling(callback_clarification["summary"]["final_response"])
        and has_seller_led_next_move(callback_clarification["summary"]["final_response"])
        and has_sales_context_depth(callback_clarification["summary"]["final_response"]),
        expectation="callback clarification should explain the workflow term instead of asking for a callback time",
        behavior_change_policy="intentional_improvement",
    )

    call_context_state = {"turns": list(qualification_state["turns"])}
    call_context_inputs = [
        (
            "time-constrained-agenda",
            "I don't have a lot of time right now what do you want exactly",
            "time_constrained_agenda_answered",
        ),
        (
            "buyer-expects-agent-lead",
            "I don't have a question you called me so you should ask whatever you want to ask",
            "seller_agenda_recovered",
        ),
        ("workflow-review-next-step", "what is the next step", "workflow_review_next_step_explained"),
        ("topic-confusion-repaired", "right I don't know what you're talking about", "topic_confusion_repaired"),
    ]
    for case_id, transcript, expected_reason in call_context_inputs:
        packet = make_packet(
            transcript,
            session_id=f"{LIVE_DEMO_ID}-call-context-recovery",
            session_state=call_context_state,
        )
        response = packet["summary"]["final_response"]
        record_case(
            cases,
            category="call_context_recovery",
            case_id=case_id,
            packet=packet,
            passed=packet["demo_session_continuity"]["reason"] == expected_reason
            and call_context_recovered(response)
            and not response_reopens_focus_menu(response),
            expectation="call-context, agenda, and confusion turns should recover directly instead of reopening generic menus",
            behavior_change_policy="intentional_improvement",
        )
        append_session_turn(call_context_state, packet)

    variety_state: dict[str, Any] = {"turns": []}
    append_session_turn(variety_state, agent_open)
    variety_packets = []
    for transcript in ["okay", "tell me more", "what else should I know", "why does that matter", "how would it help"]:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-agent-led-variety", session_state=variety_state)
        variety_packets.append(packet)
        append_session_turn(variety_state, packet)
    variety_responses = [packet["summary"]["final_response"] for packet in variety_packets]
    concept_fragments = {
        "inbound",
        "demo",
        "owner",
        "routing",
        "callback",
        "handoff",
        "reminder",
        "visibility",
        "manager",
        "spreadsheet",
        "slack",
    }
    observed_concepts = {
        fragment
        for response in variety_responses
        for fragment in concept_fragments
        if fragment in response.lower()
    }
    record_case(
        cases,
        category="sales_context_variety_and_emphasis",
        case_id="agent-open-followup-variety",
        packet=variety_packets[-1],
        passed=len(variety_responses) == len(set(variety_responses))
        and len(observed_concepts) >= 7
        and all(has_sales_context_depth(response) for response in variety_responses)
        and all(has_seller_led_next_move(response) for response in variety_responses)
        and all(has_sales_emphasis_priority(packet) for packet in variety_packets),
        expectation="agent-led qualification follow-ups should have enough sales context variety and emphasize problem/value targets",
        behavior_change_policy="intentional_improvement",
        extra={
            "response_count": len(variety_responses),
            "unique_response_count": len(set(variety_responses)),
            "observed_sales_concepts": sorted(observed_concepts),
            "all_responses_context_depth": all(has_sales_context_depth(response) for response in variety_responses),
            "all_responses_seller_led_next_move": all(has_seller_led_next_move(response) for response in variety_responses),
            "all_responses_sales_emphasis_priority": all(
                has_sales_emphasis_priority(packet) for packet in variety_packets
            ),
        },
    )

    opening = make_packet("hey what's up", session_id=f"{LIVE_DEMO_ID}-sales-opening")
    record_case(
        cases,
        category="sales_opening_permission_check",
        case_id="sales-opening-greeting",
        packet=opening,
        passed=opening["demo_session_continuity"]["reason"] == "opening_greeting_answered"
        and is_sales_opening_response(opening["summary"]["final_response"]),
        expectation="first greeting should open like a sales call with permission/time check instead of topic menu",
        behavior_change_policy="intentional_improvement",
    )

    stale_opening = make_packet(
        "hey what's up",
        session_id=f"{LIVE_DEMO_ID}-stale-sales-opening",
        session_state={
            "turns": [
                {
                    "transcript": "older unclear turn",
                    "summary": {
                        "final_response": "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
                    },
                    "continuity": {"applied": False, "reason": "no_session_continuity_match"},
                }
            ]
        },
    )
    record_case(
        cases,
        category="stale_session_greeting_relevance",
        case_id="stale-session-greeting-opens-cleanly",
        packet=stale_opening,
        passed=stale_opening["demo_session_continuity"]["reason"] == "opening_greeting_answered"
        and is_sales_opening_response(stale_opening["summary"]["final_response"])
        and not response_reopens_focus_menu(stale_opening["summary"]["final_response"]),
        expectation="greeting in a stale browser session should not fall through to the generic focus menu",
        behavior_change_policy="intentional_improvement",
    )

    voice_state: dict[str, Any] = {"turns": []}
    voice_packets = []
    for transcript in ["hey what's up", "I want to talk about the price", "handoffs", "you should call me 10 a.m. tomorrow"]:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-voice-consistency", session_state=voice_state)
        voice_packets.append(packet)
        append_session_turn(voice_state, packet)
    voice_settings = [packet["packet"]["tts_delivery"]["voice_settings"] for packet in voice_packets]
    record_case(
        cases,
        category="voice_consistency_across_turns",
        case_id="stable-elevenlabs-settings-across-mixed-turns",
        packet=voice_packets[-1],
        passed=len({json.dumps(settings, sort_keys=True) for settings in voice_settings}) == 1
        and all(
            packet["packet"]["tts_delivery"].get("voice_consistency_mode") == "live-demo-stable"
            for packet in voice_packets
        )
        and all(
            packet["packet"]["tts_delivery"].get("voice_settings_source") == "live_demo_stable_profile"
            for packet in voice_packets
        ),
        expectation="live demo should keep one stable voice-settings profile across freeform and protected turns",
        behavior_change_policy="intentional_improvement",
    )

    state: dict[str, Any] = {"turns": []}
    packets = []
    for transcript in [
        "I want to talk about the price",
        "hmm okay that is interesting",
        "okay that is interesting",
    ]:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-proactive-price", session_state=state)
        packets.append(packet)
        append_session_turn(state, packet)

    first_response = packets[0]["summary"]["final_response"]
    guidance_responses = [packet["summary"]["final_response"] for packet in packets[1:]]
    for index, packet in enumerate(packets[1:], start=1):
        response = packet["summary"]["final_response"]
        record_case(
            cases,
            category="proactive_guidance_after_acknowledgement",
            case_id=f"price-ack-proactive-guidance-{index}",
            packet=packet,
            passed=packet["demo_session_continuity"]["reason"] == "proactive_price_guidance_after_acknowledgement"
            and response != first_response
            and guidance_responses.count(response) == 1
            and contains_any(response, {"missed callbacks", "handoff review", "manual chasing", "sales case"})
            and has_seller_led_next_move(response)
            and has_seller_led_next_move(packet["summary"].get("browser_fallback_speech_text", "")),
            expectation="weak acknowledgement after price should advance guided selling instead of replaying the price sentence",
            behavior_change_policy="intentional_improvement",
        )

    close_state: dict[str, Any] = {"turns": []}
    close_packets = []
    for transcript in ["I want to talk about the price", "handoffs"]:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-seller-close", session_state=close_state)
        close_packets.append(packet)
        append_session_turn(close_state, packet)
    close_response = close_packets[1]["summary"]["final_response"]
    record_case(
        cases,
        category="seller_led_close_progression",
        case_id="price-gap-to-workflow-review",
        packet=close_packets[1],
        passed=close_packets[1]["demo_session_continuity"]["reason"] == "seller_gap_selected_for_price"
        and contains_any(close_response, {"handoff review", "short workflow review", "next step"})
        and has_seller_led_next_move(close_response)
        and "book a demo" not in close_response.lower(),
        expectation="when the buyer names a gap after price, guide toward a consented workflow review instead of waiting for another question",
        behavior_change_policy="intentional_improvement",
    )

    topic_sequences = {
        "price": [
            "hey what's up",
            "I want to talk about the price",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
        "fit": [
            "hey what's up",
            "let us talk about fit",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
        "timing": [
            "hey what's up",
            "timing is my concern",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
        "features": [
            "hey what's up",
            "I want to talk about the features",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
    }
    for topic, transcripts in topic_sequences.items():
        topic_state: dict[str, Any] = {"turns": []}
        topic_packets = []
        for transcript in transcripts:
            packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-guided-{topic}", session_state=topic_state)
            topic_packets.append(packet)
            append_session_turn(topic_state, packet)
        responses = [packet["summary"]["final_response"] for packet in topic_packets]
        topic_focus = "details" if topic == "features" else topic
        record_case(
            cases,
            category="multi_topic_non_repeating_progression",
            case_id=f"guided-{topic}-progression",
            packet=topic_packets[-1],
            passed=is_sales_opening_response(responses[0])
            and len(responses) == len(set(responses))
            and all(not response_reopens_focus_menu(response) for response in responses[1:])
            and topic_packets[1]["demo_session_continuity"].get("dialogue_focus") == topic_focus,
            expectation="topic sequence should start with sales opening and progress without replaying or reopening focus menus",
            behavior_change_policy="intentional_improvement",
        )

    callback_state: dict[str, Any] = {"turns": []}
    callback_packets = []
    for transcript in [
        "hey what's up",
        "I do not have time",
        "you should call me 10 a.m. tomorrow",
    ]:
        packet = make_packet(transcript, session_id=f"{LIVE_DEMO_ID}-callback-scheduling", session_state=callback_state)
        callback_packets.append(packet)
        append_session_turn(callback_state, packet)
    no_time = callback_packets[1]
    no_time_response = no_time["summary"]["final_response"]
    record_case(
        cases,
        category="callback_scheduling_boundary",
        case_id="no-time-asks-for-callback-time",
        packet=no_time,
        passed=no_time["demo_session_continuity"]["reason"] == "callback_request_time_needed"
        and no_time["summary"]["sales_difficulty"] == "callback-request"
        and no_time["summary"]["next_action"] == "offer-scheduling"
        and contains_any(no_time_response, {"time", "callback"})
        and not response_reopens_focus_menu(no_time_response),
        expectation="no-time boundary should ask for a callback time instead of reopening product topic menus",
        behavior_change_policy="intentional_improvement",
    )
    callback_time = callback_packets[2]
    callback_time_response = callback_time["summary"]["final_response"]
    record_case(
        cases,
        category="callback_scheduling_boundary",
        case_id="callback-time-confirms-and-ends",
        packet=callback_time,
        passed=callback_time["demo_session_continuity"]["reason"] == "callback_time_confirmed"
        and callback_time["summary"]["sales_difficulty"] == "scheduling-confirmation"
        and callback_time["summary"]["next_action"] == "confirm-scheduling"
        and callback_time["summary"]["call_control"] == "schedule-and-end"
        and contains_any(callback_time_response, {"confirmed", "callback", "goodbye"})
        and not response_reopens_focus_menu(callback_time_response),
        expectation="supplied callback time should be confirmed with schedule-and-end call control",
        behavior_change_policy="intentional_improvement",
    )
    return cases


def packet_shape(packet: dict[str, Any]) -> dict[str, list[str]]:
    async_enrichment = packet["dialogue_reasoner_async_enrichment"]
    return {
        "top_level_keys": sorted(packet.keys()),
        "asr_keys": sorted(packet["asr"].keys()),
        "turn_taking_keys": sorted(packet["turn_taking"].keys()),
        "packet_keys": sorted(packet["packet"].keys()),
        "summary_keys": sorted(packet["summary"].keys()),
        "continuity_keys": sorted(packet["demo_session_continuity"].keys()),
        "tts_delivery_keys": sorted(packet["packet"]["tts_delivery"].keys()),
        "voice_delivery_keys": sorted(packet["packet"]["voice_delivery"].keys()),
        "dialogue_reasoner_async_enrichment_keys": sorted(async_enrichment.keys()),
        "async_customer_response_snapshot_keys": sorted(async_enrichment["customer_response_snapshot"].keys()),
    }


def markdown_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-002 runtime extraction baseline",
        "",
        f"- Baseline source: `{payload['baseline_source']}`",
        f"- Behavior policy: `{payload['behavior_change_policy']}`",
        f"- LIVE-DEMO-001 validator: `{payload['validator_pass_status']['live_demo_001']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Opens PROD-102: `{str(payload['opens_prod_102']).lower()}`",
        "",
        "## Compact Regression Coverage",
    ]
    for key, value in payload["compact_regression_coverage"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(["", "## Baseline Cases"])
    for case in payload["baseline_cases"]:
        lines.append(
            f"- `{case['case_id']}` / `{case['category']}`: pass=`{str(case['pass']).lower()}`, "
            f"reason=`{case['continuity_reason']}`"
        )
    lines.extend(["", "## Intentional Improvements"])
    for case in payload.get("intentional_improvements", []):
        lines.append(
            f"- `{case['case_id']}` / `{case['category']}`: pass=`{str(case['pass']).lower()}`, "
            f"policy=`{case['behavior_change_policy']}`, reason=`{case['continuity_reason']}`"
        )
    lines.extend(
        [
            "",
            "## Private Evidence Packet Shape",
            "",
            "The baseline records packet keys only, not private turn audio or secret values.",
            "",
            f"- Top-level keys: `{', '.join(payload['private_evidence_packet_shape']['top_level_keys'])}`",
            f"- ASR keys include: `{', '.join(payload['private_evidence_packet_shape']['asr_keys'])}`",
            f"- Turn-taking keys include: `{', '.join(payload['private_evidence_packet_shape']['turn_taking_keys'])}`",
            f"- Packet keys include: `{', '.join(payload['private_evidence_packet_shape']['packet_keys'])}`",
            f"- Async enrichment keys include: `{', '.join(payload['private_evidence_packet_shape']['dialogue_reasoner_async_enrichment_keys'])}`",
            f"- Async response snapshot keys include: `{', '.join(payload['private_evidence_packet_shape']['async_customer_response_snapshot_keys'])}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    validator_status = validate_live_demo_001()
    if validator_status["live_demo_001"] != "pass":
        raise SystemExit(f"LIVE-DEMO-001 baseline validator failed: {validator_status}")

    baseline_cases = build_baseline_cases()
    if not all(case["pass"] for case in baseline_cases):
        failed = [case for case in baseline_cases if not case["pass"]]
        raise SystemExit(f"LIVE-DEMO-002 baseline cases failed: {failed}")
    intentional_improvements = build_intentional_improvement_cases()
    if not all(case["pass"] for case in intentional_improvements):
        failed = [case for case in intentional_improvements if not case["pass"]]
        raise SystemExit(f"LIVE-DEMO-002 intentional improvement cases failed: {failed}")

    sample_packet = make_packet("What does your product actually do?", session_id=f"{LIVE_DEMO_ID}-packet-shape")
    payload: dict[str, Any] = {
        "live_demo_id": LIVE_DEMO_ID,
        "baseline_source": BASELINE_SOURCE,
        "behavior_change_policy": "behavior_preserved",
        "opens_prod_102": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "provider_agent_used": False,
        "voice_cloning_used": False,
        "validator_pass_status": validator_status,
        "supported_campaign_questions": [
            case["transcript"]
            for case in baseline_cases
            if case["category"] in {"product_answer_routing", "direct_price_answer_routing"}
        ],
        "supported_continuity_behavior": [
            "short topic answer resolves the previous focus prompt",
            "agent-open turns speak first and put the session into qualification focus",
            "weak acknowledgements after the agent-led opener keep discovery moving",
            "buyer requests to clarify the previous agent question explain that question plainly before continuing qualification",
            "caller identity recall answers where the agent is calling from instead of reopening menus",
            "short negative replies clarify what was rejected before continuing sales guidance",
            "call-context turns such as why you called, what the next step is, and what you mean recover the seller agenda",
            "non-core follow-ups block internal anti-loop repair wording",
            "agent-led qualification follow-ups preserve sales context variety and problem/value emphasis",
            "price-to-effort shift is accepted when the buyer changes concern",
            "resolved effort focus advances instead of replaying the previous answer",
            "busy/no-time buyer turns ask for a callback time, then confirm the supplied time and end",
        ],
        "supported_anti_loop_behavior": [
            "at most one focus menu per fit/relevance session",
            "repeated fit follow-ups progress instead of replaying identical final responses",
            "campaign-depth answers move to value or boundary instead of leading with the buyer's stated topic",
        ],
        "supported_voice_delivery_behavior": [
            "dry-run TTS keeps provider calls blocked",
            "forced missing key live path keeps final response unchanged and uses fallback",
        ],
        "intentional_improvement_summary": [
            "Greeting turns now use a sales opener with a permission/time check instead of immediately offering a topic menu.",
            "Start Conversation now routes an agent-open turn through runtime-owned qualification before browser ASR starts.",
            "Weak acknowledgement after the agent-led opening now triggers qualification guidance, and named gaps map to workflow-review value.",
            "Qualification follow-ups now use a wider sales context set and voice emphasis targets the problem/value phrase instead of greeting text.",
            "Direct price-first turns now give the approved price and ask a diagnostic buyer-led next move instead of ending as a spoken FAQ answer.",
            "Greetings in stale browser sessions now route back to the sales opener instead of falling through to a generic topic menu.",
            "ElevenLabs request voice settings are pinned to one live-demo profile across mixed turn types to avoid delivery drift.",
            "Low-information acknowledgements after a price answer now trigger proactive guided selling instead of replaying the pricing sentence.",
            "When the buyer names the gap after a seller-led question, the agent maps it to value and asks for a consented short workflow review.",
            "Generic follow-ups such as tell me more and what else should I know now progress price, fit, timing, and feature/detail topics without replaying responses.",
            "No-time buyer turns now stay inside callback scheduling: ask for a time, then confirm the supplied callback time with schedule-and-end.",
            "Terminal call controls now stop browser auto-listening after goodbye, and live ElevenLabs failures no longer auto-switch to browser fallback voice.",
            "Buyer requests such as 'I did not understand what you asked before' now clarify the prior sales question instead of advancing canned qualification copy.",
            "Caller identity questions such as 'where were you calling from again' now answer with Maya, Northstar Workflow Labs, and RouteSignal CRM instead of falling through to a focus menu.",
            "Bare negative replies such as 'no' now ask what was rejected instead of falling through to a topic menu or another qualification line.",
            "Call-context and confusion turns now recover the seller agenda instead of falling through to generic topic menus or duplicate qualification copy.",
            "Internal anti-loop repair phrases such as 'avoid repeating the same question' are blocked from customer-facing follow-up responses.",
            "DIALOGUE-REASONER-004 async enrichment is attached as evidence only; deterministic response availability is fingerprinted before provider work and provider calls remain blocked.",
        ],
        "private_evidence_packet_shape": packet_shape(sample_packet),
        "compact_regression_coverage": {
            "repetition_prevention": True,
            "followup_continuity": True,
            "voice_delivery_propagation": True,
            "product_answer_routing": True,
            "asr_quality_handling": True,
            "callback_scheduling_boundary": True,
            "callback_workflow_disambiguation": True,
            "call_context_recovery": True,
            "customer_echo_prevention": True,
            "seller_led_next_move": True,
            "seller_led_close_progression": True,
            "terminal_call_control_stop": True,
            "live_tts_fallback_voice_guard": True,
            "stale_session_greeting_relevance": True,
            "voice_consistency_across_turns": True,
            "agent_led_sales_opening": True,
            "qualification_steering": True,
            "sales_context_variety": True,
            "sales_emphasis_priority": True,
            "previous_question_clarification": True,
            "ambiguous_negative_clarification": True,
            "caller_identity_recall": True,
            "internal_repair_speech_blocked": True,
            "async_reasoning_enrichment_evidence": True,
        },
        "baseline_cases": baseline_cases,
        "intentional_improvements": intentional_improvements,
    }

    write_json(BASELINE_PATH, payload)
    write_text(REPORT_PATH, markdown_report(payload))
    print(json.dumps({"baseline_json": str(BASELINE_PATH), "baseline_report": str(REPORT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
