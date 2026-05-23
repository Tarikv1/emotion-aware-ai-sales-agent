#!/usr/bin/env python3
"""Generate a live-inspired adversarial dialogue matrix.

This is a dry-run evidence harness. It does not call providers, live TTS,
email, calendar, CRM, local LLMs, or PROD-102.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]

FULL_MENU_PATTERNS = [
    "which part is least clear",
    "which part is more familiar",
    "name the point",
    "which part should i check first",
    "manual tracking or missed callbacks",
    "plan fit, coverage or availability, or contract or switching",
    "premium or budget, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
]

INTERNAL_PATTERNS = [
    "approved qualified reviewer path",
    "internal policy",
    "i should not",
    "transfer-or-escalate",
    "approved details",
]

CAMPAIGN_LEAKS = {
    "routesignal_live_demo": ["premium pressure", "licensed coverage review", "policy review call", "telecom account", "repair timing"],
    "synthetic-insurance-review": ["routesignal", "inbound demo", "callback reminders for demo", "telecom account", "repair timing"],
    "synthetic-telecom-plan-review": ["routesignal", "inbound demo", "premium pressure", "licensed coverage review", "repair timing"],
    "synthetic-automotive-service-review": ["routesignal", "inbound demo", "premium pressure", "telecom account", "licensed coverage review"],
    "synthetic-membership-plan-review": ["routesignal", "inbound demo", "premium pressure", "telecom account", "repair timing"],
    "synthetic-b2b-saas-operations": ["routesignal", "inbound demo", "premium pressure", "telecom account", "repair timing"],
}

ALL_FLAGS = [
    "did_not_answer_direct_question",
    "repeated_full_menu",
    "stability_guard_overrode_high_confidence_move",
    "false_assumption_not_repaired",
    "repeated_false_assumption",
    "internal_wording_leak",
    "out_of_scope_reset_after_relevant_context",
    "failed_to_preserve_context",
    "appointment_too_early",
    "failed_to_capture_callback_time",
    "over_deferential",
    "hostile_response_not_deescalated",
    "explicit_stop_not_respected",
    "asr_near_miss_not_clarified",
    "campaign_contamination",
    "too_many_questions",
    "too_long_for_live_voice",
    "repeated_response",
]

CORE_BLOCKING_FLAGS = [
    "did_not_answer_direct_question",
    "repeated_full_menu",
    "stability_guard_overrode_high_confidence_move",
    "false_assumption_not_repaired",
    "repeated_false_assumption",
    "internal_wording_leak",
    "out_of_scope_reset_after_relevant_context",
    "failed_to_preserve_context",
    "appointment_too_early",
    "failed_to_capture_callback_time",
    "hostile_response_not_deescalated",
    "explicit_stop_not_respected",
    "asr_near_miss_not_clarified",
    "campaign_contamination",
    "too_many_questions",
]

SCENARIO_FAMILIES = [
    "permission_weak_acknowledgement_variants",
    "direct_product_value_challenge_loops",
    "false_assumption_correction",
    "repeated_product_detail_scope_questions",
    "asr_near_miss_gap_phrases",
    "vague_affirmative_after_context",
    "agent_looping_complaints",
    "impact_before_clean_pain",
    "callback_time_too_early_or_ambiguous",
    "hostile_challenging_buyer",
    "human_context_interruption_pressure",
    "campaign_selector_wrong_campaign_contamination",
    "stop_refusal_pressure_test",
    "commercial_quality_stress",
    "mixed_intent_buyer_turns",
    "buyer_correction_contradiction_stress",
    "repeated_challenge_escalation",
    "buyer_says_agent_is_wrong",
    "early_callback_premature_scheduling",
    "price_budget_affordability_stress",
    "scope_boundary_regulated_detail_stress",
    "long_conversation_state_drift",
    "multi_campaign_contamination_stress",
    "human_context_sales_intent_hybrids",
    "asr_near_miss_invented_transcript_stress",
    "disallowed_persistence_after_stop",
    "commercial_pressure_close_strength_stress",
    "why_human_review_challenge",
    "repeated_answer_variation_anti_loop",
    "sales_realism_score_heuristics",
]


@dataclass(frozen=True)
class Campaign:
    id: str
    config_path: Path | None
    primary_issue: str
    false_issue: str
    pain: str
    impact: str
    near_misses: tuple[str, ...]
    other_campaign_phrase: str


CAMPAIGNS = [
    Campaign(
        "routesignal_live_demo",
        None,
        "inbound demo follow-up",
        "callbacks",
        "callbacks are a problem",
        "it causes delays",
        ("call bags are a problem", "call backs are the problem", "callback bag is the issue", "hand offs are messy"),
        "premium pressure is the issue",
    ),
    Campaign(
        "synthetic-insurance-review",
        EXAMPLES / "synthetic-insurance-review.json",
        "premium pressure",
        "premium",
        "premium is a problem",
        "it wastes time",
        ("premon pressure is a problem", "payment pressure is a problem", "cover fit is the issue", "coverage thing is confusing"),
        "callbacks are a problem",
    ),
    Campaign(
        "synthetic-telecom-plan-review",
        EXAMPLES / "synthetic-telecom-plan-review.json",
        "plan fit",
        "plan fit",
        "plan fit is a problem",
        "customers wait",
        ("plane fit is a problem", "cover availability is the issue", "contact switching is confusing", "plan thing is wrong"),
        "repair timings are usually pretty long",
    ),
    Campaign(
        "synthetic-automotive-service-review",
        EXAMPLES / "synthetic-automotive-service-review.json",
        "repair timing",
        "repair timing",
        "repair timings are usually pretty long",
        "it slows us down",
        ("repair timings are a problem", "warranty estimate thing is confusing", "repair time is the issue", "service timing is long"),
        "coverage availability is the issue",
    ),
    Campaign(
        "synthetic-membership-plan-review",
        EXAMPLES / "synthetic-membership-plan-review.json",
        "plan fit",
        "plan fit",
        "plan fit is a problem",
        "it costs money",
        ("membership level is wrong", "cancel timing is confusing", "usage thing is unclear", "plan thing is a problem"),
        "inbound demo follow-up is slipping",
    ),
    Campaign(
        "synthetic-b2b-saas-operations",
        EXAMPLES / "synthetic-b2b-saas-operations.json",
        "manual work",
        "manual work",
        "manual work is a problem",
        "it wastes time",
        ("manual trucking is a problem", "manual tracking is a problem", "integration thing is confusing", "visibility thing is unclear"),
        "premium pressure is the issue",
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    return " ".join(str(text or "").lower().replace("'", " ").split())


def safe_id(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", normalize(text)).strip("-")
    return cleaned[:80] or "scenario"


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "live_tts_used": bool(packet.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or tts.get("provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def selected_action(packet: dict[str, Any]) -> dict[str, Any]:
    action = ((packet.get("dialogue_manager") or {}).get("selected_action") or {})
    return action if isinstance(action, dict) else {}


def universal_frame(packet: dict[str, Any]) -> dict[str, Any]:
    frame = packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}
    return frame if isinstance(frame, dict) else {}


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or selected_action(packet).get("call_control") or "")


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "conversation_continuity": packet.get("conversation_continuity") or packet.get("demo_session_continuity") or {},
            "conversation_memory": packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
            "universal_policy_frame": universal_frame(packet),
        }
    )


def build_turn(transcript: str, state: dict[str, Any], campaign: Campaign, session_id: str) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=campaign.config_path,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def turn_record(packet: dict[str, Any], transcript: str, index: int) -> dict[str, Any]:
    action = selected_action(packet)
    frame = universal_frame(packet)
    source = str(action.get("source") or "")
    response = final_response(packet)
    return {
        "turn_index": index,
        "buyer_utterance": transcript,
        "final_response": response,
        "response_word_count": len(response.split()),
        "question_count": response.count("?"),
        "call_control": call_control(packet),
        "selected_action": {
            "source": source,
            "semantic": action.get("semantic"),
            "target_gap": action.get("target_gap"),
            "call_control": action.get("call_control"),
        },
        "semantic": action.get("semantic"),
        "target_gap": action.get("target_gap"),
        "confirmed_gaps": packet.get("confirmed_gaps"),
        "universal_policy_frame": frame,
        "buyer_move_id": frame.get("buyer_move_id"),
        "buyer_move_category": frame.get("buyer_move_category"),
        "stability_guard_applied": source == "pre_speech_conversation_stability_guard",
        "side_effect_flags": side_effect_flags(packet),
    }


def family_scripts(family: str, campaign: Campaign) -> list[list[str]]:
    issue = campaign.primary_issue
    false_issue = campaign.false_issue
    pain = campaign.pain
    impact = campaign.impact
    near = list(campaign.near_misses)
    other = campaign.other_campaign_phrase
    scripts: dict[str, list[list[str]]] = {
        "permission_weak_acknowledgement_variants": [
            ["__agent_open__", "sure sure"],
            ["__agent_open__", "okay fine"],
            ["__agent_open__", "go ahead"],
            ["__agent_open__", "fine but be fast"],
        ],
        "direct_product_value_challenge_loops": [
            ["__agent_open__", "what does your product do", "why should I care", "you still did not answer me"],
            ["__agent_open__", "what are you selling", "explain it plainly", "say it in one sentence"],
            ["__agent_open__", "what is this for", "why should I care"],
            ["__agent_open__", "what does your product do", "what should I care"],
        ],
        "false_assumption_correction": [
            ["__agent_open__", "yeah", "what does your product do", f"I did not mention {false_issue}"],
            ["__agent_open__", "yeah", pain, "that is not what I said"],
            ["__agent_open__", "yeah", pain, "stop assuming that"],
            ["__agent_open__", "yeah", f"I said {issue}, not something else"],
        ],
        "repeated_product_detail_scope_questions": [
            ["__agent_open__", "what does your product do", "can you give me details", "so you cannot give me details"],
            ["__agent_open__", "what exactly can you tell me", "why are you calling if you cannot explain it"],
            ["__agent_open__", "can you give me any information", "what can you say in plain English"],
            ["__agent_open__", "what does this do", "can you explain the scope"],
        ],
        "asr_near_miss_gap_phrases": [
            ["__agent_open__", "yeah", near[0]],
            ["__agent_open__", "yeah", near[1], impact],
            ["__agent_open__", "yeah", near[2]],
            ["__agent_open__", "yeah", near[3], "it wastes time"],
        ],
        "vague_affirmative_after_context": [
            ["__agent_open__", "I'm asking because the last company wasted my time", "yeah that would be good"],
            ["__agent_open__", "I don't trust these calls", "okay that sounds good"],
            ["__agent_open__", "salespeople always say that", "sure"],
            ["__agent_open__", "last company like this wasted my time", "I guess"],
        ],
        "agent_looping_complaints": [
            ["__agent_open__", "yeah", pain, "you already asked that"],
            ["__agent_open__", "yeah", pain, "you keep repeating yourself"],
            ["__agent_open__", "what does your product do", "you didn't answer my question"],
            ["__agent_open__", "yeah", pain, "I already told you"],
        ],
        "impact_before_clean_pain": [
            ["__agent_open__", "yeah", "it causes delays"],
            ["__agent_open__", "yeah", "it wastes time"],
            ["__agent_open__", "yeah", "customers wait"],
            ["__agent_open__", "yeah", "nobody follows up"],
        ],
        "callback_time_too_early_or_ambiguous": [
            ["__agent_open__", "call me tomorrow at 3"],
            ["__agent_open__", "tomorrow works"],
            ["__agent_open__", "yeah that time is fine"],
            ["__agent_open__", "Friday morning maybe"],
        ],
        "hostile_challenging_buyer": [
            ["__agent_open__", "this sounds like a scam"],
            ["__agent_open__", "are you wasting my time"],
            ["__agent_open__", "this is pointless"],
            ["__agent_open__", "prove this is useful"],
        ],
        "human_context_interruption_pressure": [
            ["__agent_open__", "I'm driving"],
            ["__agent_open__", "my kid is crying"],
            ["__agent_open__", "I just got out of the hospital"],
            ["__agent_open__", "last company wasted my time"],
        ],
        "campaign_selector_wrong_campaign_contamination": [
            ["__agent_open__", other],
            ["__agent_open__", "why are you talking about insurance"],
            ["__agent_open__", "why are you talking about callbacks"],
            ["__agent_open__", f"that is not about {issue}"],
        ],
        "stop_refusal_pressure_test": [
            ["__agent_open__", "not interested"],
            ["__agent_open__", "stop calling"],
            ["__agent_open__", "I don't want to continue"],
            ["__agent_open__", "I said no", "why are you still talking"],
        ],
        "commercial_quality_stress": [
            ["__agent_open__", "what does your product do", pain, impact, "call me next week", "why do I need a human review"],
            ["__agent_open__", "yeah", "maybe", impact, "send me details"],
            ["__agent_open__", "yeah", pain, "why should I care", impact, "tomorrow at 3 works"],
            ["__agent_open__", "yeah", pain, "that would be useful", "okay what now"],
        ],
        "mixed_intent_buyer_turns": [
            ["__agent_open__", "yeah but what does it cost"],
            ["__agent_open__", "sure but what are you selling"],
            ["__agent_open__", "maybe but I don't trust calls like this"],
            ["__agent_open__", "that sounds good but send me details first"],
        ],
        "buyer_correction_contradiction_stress": [
            ["__agent_open__", "yeah", pain, "no that's not what I said"],
            ["__agent_open__", "yeah", pain, f"I said {issue}, not {false_issue}"],
            ["__agent_open__", "yeah", "you misunderstood me"],
            ["__agent_open__", "yeah", "that's not my issue"],
        ],
        "repeated_challenge_escalation": [
            ["__agent_open__", "what does your product do", "no explain it plainly", "you still didn't answer"],
            ["__agent_open__", "what is this", "why should I care", "say it in one sentence"],
            ["__agent_open__", "what are you selling", "no, what exactly is it"],
            ["__agent_open__", "why are you calling", "that still doesn't explain it"],
        ],
        "buyer_says_agent_is_wrong": [
            ["__agent_open__", "that's wrong"],
            ["__agent_open__", "that doesn't make sense"],
            ["__agent_open__", "you're making assumptions"],
            ["__agent_open__", "this sounds automated"],
        ],
        "early_callback_premature_scheduling": [
            ["__agent_open__", "call me tomorrow"],
            ["__agent_open__", "can someone call me later"],
            ["__agent_open__", "send someone next week"],
            ["__agent_open__", "email me first"],
        ],
        "price_budget_affordability_stress": [
            ["__agent_open__", "how much is it"],
            ["__agent_open__", "is this free"],
            ["__agent_open__", "everything is expensive right now"],
            ["__agent_open__", "what's the exact price"],
        ],
        "scope_boundary_regulated_detail_stress": [
            ["__agent_open__", "can you tell me exactly what coverage I need"],
            ["__agent_open__", "can you guarantee cancellation"],
            ["__agent_open__", "is coverage available at my address"],
            ["__agent_open__", "can you diagnose the problem"],
        ],
        "long_conversation_state_drift": [
            ["__agent_open__", "yeah", "what does your product do", pain, "you already asked that", impact, "send me details", "call me tomorrow", "tomorrow at 3 works"],
            ["__agent_open__", "yeah", pain, f"I did not mention {false_issue}", impact, "why do I need a human review"],
            ["__agent_open__", "yeah", "what are you selling", pain, "you didn't answer my question", impact, "okay what now"],
            ["__agent_open__", "yeah", pain, "that is not what I said", "I mean it wastes time", "call me Friday morning"],
        ],
        "multi_campaign_contamination_stress": [
            ["__agent_open__", other, "why is that relevant"],
            ["__agent_open__", "I need insurance coverage", "why are you talking about something else"],
            ["__agent_open__", "callbacks are the issue", "is this about callbacks or something else"],
            ["__agent_open__", "repair timings are long", "wrong campaign maybe"],
        ],
        "human_context_sales_intent_hybrids": [
            ["__agent_open__", "I'm driving but what does it cost"],
            ["__agent_open__", "my kids are screaming, just tell me what this is"],
            ["__agent_open__", "I just got out of the hospital, can you call later"],
            ["__agent_open__", "I don't trust these calls but what do you do"],
        ],
        "asr_near_miss_invented_transcript_stress": [
            ["__agent_open__", "what should I care"],
            ["__agent_open__", near[0]],
            ["__agent_open__", "yadav would be good"],
            ["__agent_open__", "play a double be good"],
        ],
        "disallowed_persistence_after_stop": [
            ["__agent_open__", "not interested", "why are you still talking"],
            ["__agent_open__", "stop calling", "I said no"],
            ["__agent_open__", "take me off", "goodbye"],
            ["__agent_open__", "I don't want to continue", "one quick question?"],
        ],
        "commercial_pressure_close_strength_stress": [
            ["__agent_open__", "yeah", "maybe"],
            ["__agent_open__", "yeah", "not really", "it is annoying"],
            ["__agent_open__", "yeah", pain, "it wastes time", "that would be useful"],
            ["__agent_open__", "yeah", pain, impact, "okay what now"],
        ],
        "why_human_review_challenge": [
            ["__agent_open__", "why do I need a human review"],
            ["__agent_open__", "why can't you just tell me"],
            ["__agent_open__", "why can't you book it now"],
            ["__agent_open__", "what will they do that you can't"],
        ],
        "repeated_answer_variation_anti_loop": [
            ["__agent_open__", "what does your product do", "what does your product do"],
            ["__agent_open__", "yeah", pain, pain, "you keep repeating yourself"],
            ["__agent_open__", "so you cannot give details", "so you cannot give details"],
            ["__agent_open__", "you didn't answer", "you didn't answer"],
        ],
        "sales_realism_score_heuristics": [
            ["__agent_open__", "okay but why should I care", pain, impact],
            ["__agent_open__", "maybe quickly", pain, "customers wait"],
            ["__agent_open__", "I can talk but make it quick", "what exactly is this", pain],
            ["__agent_open__", "this sounds pointless", "what does your product do", impact],
        ],
    }
    return scripts[family]


def core_specs() -> list[dict[str, Any]]:
    route = CAMPAIGNS[0]
    insurance = CAMPAIGNS[1]
    telecom = CAMPAIGNS[2]
    return [
        {"scenario_id": "core-routesignal-permission-repeated-ack", "campaign": route, "scenario_family": "permission_weak_acknowledgement_variants", "buyer_script": ["__agent_open__", "sure sure"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-routesignal-asr-near-miss-callbacks", "campaign": route, "scenario_family": "asr_near_miss_gap_phrases", "buyer_script": ["__agent_open__", "sure sure", "call bags are a problem"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-routesignal-near-miss-impact", "campaign": route, "scenario_family": "asr_near_miss_gap_phrases", "buyer_script": ["__agent_open__", "sure sure", "call bags are a problem", "I mean it causes delays so that is a problem for us"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-routesignal-vague-followup", "campaign": route, "scenario_family": "commercial_pressure_close_strength_stress", "buyer_script": ["__agent_open__", "sure sure", "call bags are a problem", "I guess a little bit"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-routesignal-why-care", "campaign": route, "scenario_family": "direct_product_value_challenge_loops", "buyer_script": ["__agent_open__", "I do but what does your product do", "what should I care"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-insurance-false-assumption", "campaign": insurance, "scenario_family": "false_assumption_correction", "buyer_script": ["__agent_open__", "yeah", "what does your product do can you give me any details", "I did not mention premium"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-insurance-product-detail-repeat", "campaign": insurance, "scenario_family": "repeated_product_detail_scope_questions", "buyer_script": ["__agent_open__", "yeah", "what does your product do can you give me any details", "I did not mention premium", "so can you not give me any details"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-telecom-vague-positive-after-bad-experience", "campaign": telecom, "scenario_family": "vague_affirmative_after_context", "buyer_script": ["__agent_open__", "yeah start with how much is your product", "I'm asking because the last company wasted my time", "yeah that'd be good"], "reproduced_failure_before_patch": True},
        {"scenario_id": "core-telecom-plan-fit-boundary", "campaign": telecom, "scenario_family": "scope_boundary_regulated_detail_stress", "buyer_script": ["__agent_open__", "yeah start with how much is your product", "I'm asking because the last company wasted my time", "yeah that'd be good", "how about the plane fit and coverage"], "reproduced_failure_before_patch": True},
    ]


def exploratory_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for family in SCENARIO_FAMILIES:
        for campaign in CAMPAIGNS:
            for index, buyer_script in enumerate(family_scripts(family, campaign), start=1):
                specs.append(
                    {
                        "scenario_id": f"adv-{safe_id(family)}-{campaign.id}-{index:02d}",
                        "campaign": campaign,
                        "scenario_family": family,
                        "buyer_script": buyer_script,
                        "reproduced_failure_before_patch": False,
                    }
                )
    return specs


def run_scenario(spec: dict[str, Any], tier: str) -> dict[str, Any]:
    campaign: Campaign = spec["campaign"]
    scenario_id = str(spec["scenario_id"])
    state: dict[str, Any] = {}
    turns: list[dict[str, Any]] = []
    turn_failed = False
    for index, transcript in enumerate(spec["buyer_script"], start=1):
        try:
            packet = build_turn(transcript, state, campaign, scenario_id)
            turns.append(turn_record(packet, transcript, index))
        except Exception as exc:  # noqa: BLE001 - matrix should preserve evidence instead of crashing.
            turn_failed = True
            turns.append(
                {
                    "turn_index": index,
                    "buyer_utterance": transcript,
                    "final_response": "",
                    "response_word_count": 0,
                    "question_count": 0,
                    "call_control": "error",
                    "selected_action": {"source": "turn_failed", "semantic": None, "target_gap": None, "call_control": "error"},
                    "semantic": None,
                    "target_gap": None,
                    "confirmed_gaps": [],
                    "universal_policy_frame": {"error_type": type(exc).__name__, "error": str(exc)},
                    "buyer_move_id": None,
                    "buyer_move_category": None,
                    "stability_guard_applied": False,
                    "side_effect_flags": {key: False for key in SIDE_EFFECT_KEYS},
                }
            )
            break
    return evaluate_scenario(spec, tier, turns, turn_failed)


def evaluate_scenario(spec: dict[str, Any], tier: str, turns: list[dict[str, Any]], turn_failed: bool) -> dict[str, Any]:
    campaign: Campaign = spec["campaign"]
    family = str(spec["scenario_family"])
    script = list(spec["buyer_script"])
    final = turns[-1] if turns else {}
    response_texts = [str(turn.get("final_response") or "") for turn in turns]
    final_lower = normalize(str(final.get("final_response") or ""))
    all_response_lower = "\n".join(normalize(text) for text in response_texts)
    last_buyer = normalize(script[-1] if script else "")
    flags = set()

    if turn_failed:
        flags.add("turn_failed")
    if any(pattern in all_response_lower for pattern in FULL_MENU_PATTERNS):
        flags.add("repeated_full_menu")
    if any(pattern in all_response_lower for pattern in INTERNAL_PATTERNS):
        flags.add("internal_wording_leak")
    if any(int(turn.get("question_count") or 0) > 1 for turn in turns):
        flags.add("too_many_questions")
    if any(int(turn.get("response_word_count") or 0) > 55 for turn in turns):
        flags.add("too_long_for_live_voice")
    if "outside this call" in all_response_lower or "outside scope" in all_response_lower:
        flags.add("out_of_scope_reset_after_relevant_context")
    if "probably the right" in all_response_lower or "we can leave it there" in all_response_lower:
        flags.add("over_deferential")
    if any(
        turn.get("stability_guard_applied")
        and str((turn.get("universal_policy_frame") or {}).get("recognition_confidence") or "") == "high"
        for turn in turns
    ):
        flags.add("stability_guard_overrode_high_confidence_move")
    repeated_responses = [text for text, count in Counter(response_texts).items() if text and count > 1 and "stop here" not in normalize(text)]
    if repeated_responses:
        flags.add("repeated_response")

    explicit_stop_phrases = (
        "not interested",
        "stop calling",
        "i don t want to continue",
        "take me off",
        "i said no",
        "why are you still talking",
        "goodbye",
    )
    explicit_stop_seen = any(
        any(phrase in normalize(item) for phrase in explicit_stop_phrases)
        for item in script[1:]
    )
    if explicit_stop_seen:
        if str(final.get("call_control") or "") != "end-call":
            flags.add("explicit_stop_not_respected")
    if "schedule-and-end" == str(final.get("call_control") or "") and not any(
        token in normalize(" ".join(script)) for token in ["problem", "wastes", "delays", "wait", "slows", "costs", "follow"]
    ):
        flags.add("appointment_too_early")
    if any("tomorrow at 3" in normalize(item) for item in script) and any(token in normalize(" ".join(script)) for token in ["problem", "delays", "wastes"]):
        if str((final.get("universal_policy_frame") or {}).get("buyer_move_id") or "") != "callback_time_provided":
            flags.add("failed_to_capture_callback_time")

    if family in {"direct_product_value_challenge_loops", "repeated_challenge_escalation", "why_human_review_challenge"}:
        if any(token in last_buyer for token in ["what", "why", "explain", "sentence", "answer"]) and not any(
            token in final_lower for token in ["fair", "sure", "direct", "because", "helps", "checks", "review", "scope", "human"]
        ):
            flags.add("did_not_answer_direct_question")
    if family in {"false_assumption_correction", "buyer_correction_contradiction_stress"}:
        if any(token in last_buyer for token in ["did not mention", "not what", "stop assuming", "misunderstood", "not my issue"]):
            if not any(token in final_lower for token in ["right", "won t assume", "understood", "fair", "got it"]):
                flags.add("false_assumption_not_repaired")
            if "since you mentioned" in final_lower:
                flags.add("repeated_false_assumption")
    if family in {"asr_near_miss_gap_phrases", "asr_near_miss_invented_transcript_stress"}:
        if any(item in last_buyer for item in ["yadav", "play a double"]):
            if "repeat" not in final_lower and "misheard" not in final_lower:
                flags.add("asr_near_miss_not_clarified")
        elif not any(token in final_lower for token in ["issue", "misheard", "repeat", "mean", "clarify", "got it"]):
            flags.add("asr_near_miss_not_clarified")
    if family in {"hostile_challenging_buyer", "buyer_says_agent_is_wrong"}:
        if not any(token in final_lower for token in ["fair", "understand", "right", "sorry", "brief", "direct", "stop"]):
            flags.add("hostile_response_not_deescalated")
    if family in {"long_conversation_state_drift", "commercial_quality_stress"}:
        if any(cue in normalize(" ".join(script)) for cue in ["problem", "delays", "wastes", "wait"]) and not any(
            token in all_response_lower for token in ["issue", "impact", "review", "callback", "details"]
        ):
            flags.add("failed_to_preserve_context")

    leak_terms = CAMPAIGN_LEAKS.get(campaign.id, [])
    if any(term in all_response_lower for term in leak_terms):
        flags.add("campaign_contamination")

    side_effects = {key: any(bool((turn.get("side_effect_flags") or {}).get(key)) for turn in turns) for key in SIDE_EFFECT_KEYS}
    if any(side_effects.values()):
        flags.add("side_effect_boundary_failed")

    mechanical_flags = sorted(flag for flag in flags if flag in ALL_FLAGS or flag in {"turn_failed", "side_effect_boundary_failed"})
    core_blocking = sorted(flag for flag in mechanical_flags if flag in CORE_BLOCKING_FLAGS or flag in {"turn_failed", "side_effect_boundary_failed"})
    passed = not core_blocking if tier == "core_gate" else not mechanical_flags
    sales_quality = {
        "answered_current_buyer_move": "did_not_answer_direct_question" not in flags,
        "advanced_or_preserved_sales_state": "failed_to_preserve_context" not in flags,
        "avoided_menu_reset": "repeated_full_menu" not in flags,
        "preserved_corrected_fact": "false_assumption_not_repaired" not in flags and "repeated_false_assumption" not in flags,
        "avoided_false_assumption": "repeated_false_assumption" not in flags,
        "next_action_is_earned": "appointment_too_early" not in flags,
        "needs_human_sales_review": True,
    }
    priority = "low"
    if any(flag in flags for flag in ["explicit_stop_not_respected", "internal_wording_leak", "side_effect_boundary_failed"]):
        priority = "critical"
    elif len(flags) >= 3 or any(flag in flags for flag in ["did_not_answer_direct_question", "stability_guard_overrode_high_confidence_move"]):
        priority = "high"
    elif flags:
        priority = "medium"

    return {
        "scenario_id": str(spec["scenario_id"]),
        "scenario_family": family,
        "tier": tier,
        "campaign_id": campaign.id,
        "campaign_config_path": str(campaign.config_path.relative_to(ROOT)).replace("\\", "/") if campaign.config_path else None,
        "buyer_script": script,
        "full_turn_list": turns,
        "turns": turns,
        "selected_action_source": str(final.get("selected_action", {}).get("source") or ""),
        "call_control": str(final.get("call_control") or ""),
        "semantic": final.get("semantic"),
        "target_gap": final.get("target_gap"),
        "confirmed_gaps": final.get("confirmed_gaps"),
        "universal_policy_frame": final.get("universal_policy_frame") or {},
        "stability_guard_applied": any(bool(turn.get("stability_guard_applied")) for turn in turns),
        "repair_chain": [str(turn.get("selected_action", {}).get("source") or "") for turn in turns],
        "mechanical_failure_flags": mechanical_flags,
        "sales_quality_heuristic_flags": sales_quality,
        "human_reviewer_priority": priority,
        "side_effect_flags": side_effects,
        "reproduced_failure_before_patch": bool(spec.get("reproduced_failure_before_patch")),
        "requires_human_sales_review": True,
        "codex_assigned_final_sales_quality": False,
        "passed": passed,
        "core_blocking_flags": core_blocking,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def top_examples(scenarios: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    bad = [scenario for scenario in scenarios if scenario.get("mechanical_failure_flags")]
    bad.sort(key=lambda item: ({"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(item.get("human_reviewer_priority")), 4), -len(item.get("mechanical_failure_flags") or []), str(item.get("scenario_id"))))
    return [
        {
            "scenario_id": item["scenario_id"],
            "scenario_family": item["scenario_family"],
            "campaign_id": item["campaign_id"],
            "tier": item["tier"],
            "priority": item["human_reviewer_priority"],
            "mechanical_failure_flags": item["mechanical_failure_flags"],
            "buyer_script": item["buyer_script"],
            "final_response": (item.get("turns") or [{}])[-1].get("final_response"),
            "selected_action_source": item.get("selected_action_source"),
        }
        for item in bad[:limit]
    ]


def generate() -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    for spec in core_specs():
        scenarios.append(run_scenario(spec, "core_gate"))
    for spec in exploratory_specs():
        scenarios.append(run_scenario(spec, "exploratory_red_findings"))

    core_failures = [item for item in scenarios if item["tier"] == "core_gate" and not item["passed"]]
    red_findings = [item for item in scenarios if item["tier"] == "exploratory_red_findings" and item["mechanical_failure_flags"]]
    status = "fail" if core_failures else ("red_findings" if red_findings else "pass")
    family_counts = Counter(str(item["scenario_family"]) for item in scenarios)
    campaign_counts = Counter(str(item["campaign_id"]) for item in scenarios)
    failure_by_family = Counter(str(item["scenario_family"]) for item in red_findings + core_failures)
    failure_by_campaign = Counter(str(item["campaign_id"]) for item in red_findings + core_failures)
    failure_by_source = Counter(str(item.get("selected_action_source") or "") for item in red_findings + core_failures)
    failure_flags = Counter(flag for item in red_findings + core_failures for flag in item.get("mechanical_failure_flags") or [])
    repeated_clusters = Counter()
    for item in scenarios:
        responses = [str(turn.get("final_response") or "") for turn in item.get("turns") or []]
        for response, count in Counter(responses).items():
            if response and count > 1:
                repeated_clusters[response] += 1

    summary = {
        "scenario_count": len(scenarios),
        "core_gate_count": sum(1 for item in scenarios if item["tier"] == "core_gate"),
        "exploratory_count": sum(1 for item in scenarios if item["tier"] == "exploratory_red_findings"),
        "multi_turn_conversation_count": sum(1 for item in scenarios if len(item.get("buyer_script") or []) >= 3),
        "campaign_coverage": sorted(campaign_counts),
        "scenario_family_coverage": sorted(family_counts),
        "core_gate_failure_count": len(core_failures),
        "red_finding_count": len(red_findings),
        "pass_count": sum(1 for item in scenarios if item.get("passed")),
        "failure_count": sum(1 for item in scenarios if not item.get("passed")),
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": status,
        "summary": summary,
        "core_gate_failure_count": len(core_failures),
        "red_finding_count": len(red_findings),
        "family_counts": dict(sorted(family_counts.items())),
        "campaign_counts": dict(sorted(campaign_counts.items())),
        "pass_fail_counts": {
            "passed": summary["pass_count"],
            "failed_or_red": summary["failure_count"],
            "core_gate_failures": len(core_failures),
            "exploratory_red_findings": len(red_findings),
        },
        "top_failure_clusters": [
            {"flag": flag, "count": count} for flag, count in failure_flags.most_common(20)
        ],
        "failure_counts_by_family": dict(sorted(failure_by_family.items())),
        "failure_counts_by_campaign": dict(sorted(failure_by_campaign.items())),
        "failure_counts_by_selected_action_source": dict(sorted(failure_by_source.items())),
        "explicit_stop_red_findings": [
            item["scenario_id"] for item in scenarios if "explicit_stop_not_respected" in item.get("mechanical_failure_flags", [])
        ][:50],
        "stability_guard_override_findings": [
            item["scenario_id"] for item in scenarios if "stability_guard_overrode_high_confidence_move" in item.get("mechanical_failure_flags", [])
        ][:50],
        "direct_question_challenge_findings": [
            item["scenario_id"] for item in scenarios if "did_not_answer_direct_question" in item.get("mechanical_failure_flags", [])
        ][:50],
        "asr_near_miss_findings": [
            item["scenario_id"] for item in scenarios if "asr_near_miss_not_clarified" in item.get("mechanical_failure_flags", [])
        ][:50],
        "repeated_response_clusters": [
            {"response": response, "scenario_count": count} for response, count in repeated_clusters.most_common(12)
        ],
        "false_assumption_clusters": [
            item["scenario_id"] for item in scenarios if any(flag in item.get("mechanical_failure_flags", []) for flag in ["false_assumption_not_repaired", "repeated_false_assumption"])
        ][:50],
        "internal_wording_leaks": [
            item["scenario_id"] for item in scenarios if "internal_wording_leak" in item.get("mechanical_failure_flags", [])
        ][:50],
        "out_of_campaign_relevance_failures": [
            item["scenario_id"] for item in scenarios if "campaign_contamination" in item.get("mechanical_failure_flags", [])
        ][:50],
        "needs_human_review_examples": [item["scenario_id"] for item in scenarios if item.get("requires_human_sales_review")][:20],
        "worst_conversations": top_examples(scenarios),
        "side_effect_boundary": {key: any(bool((item.get("side_effect_flags") or {}).get(key)) for item in scenarios) for key in SIDE_EFFECT_KEYS},
        "recommendation": "patch core gate before live rehearsal" if core_failures else ("needs human review and ranked follow-up patches" if red_findings else "no patch"),
        "runtime_behavior_changed": False,
    }
    packet = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": result["generated_at"],
        "status": status,
        "requires_human_sales_review": True,
        "codex_assigned_final_sales_quality": False,
        "scenarios": scenarios,
    }
    return {"result": result, "packet": packet, "scenarios": scenarios}


def write_outputs(bundle: dict[str, Any]) -> dict[str, Any]:
    result = bundle["result"]
    packet = bundle["packet"]
    scenarios = bundle["scenarios"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_DIR / "result.json", result)
    write_json(OUT_DIR / "review_packet.json", packet)
    jsonl = "\n".join(json.dumps(item, sort_keys=True) for item in scenarios) + "\n"
    write_text(OUT_DIR / "review_packet.jsonl", jsonl)

    report_lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Scenario count: `{result['summary']['scenario_count']}`",
        f"- Multi-turn conversations: `{result['summary']['multi_turn_conversation_count']}`",
        f"- Core gate failures: `{result['summary']['core_gate_failure_count']}`",
        f"- Exploratory red findings: `{result['summary']['red_finding_count']}`",
        "",
        "## Scenario Count",
        f"- Total scenario runs: `{result['summary']['scenario_count']}`",
        f"- Core gate: `{result['summary']['core_gate_count']}`",
        f"- Exploratory: `{result['summary']['exploratory_count']}`",
        "",
        "## Campaign Coverage",
        *(f"- `{campaign}`: `{count}`" for campaign, count in result["campaign_counts"].items()),
        "",
        "## Scenario Family Coverage",
        *(f"- `{family}`: `{count}`" for family, count in result["family_counts"].items()),
        "",
        "## Pass/Fail Counts",
        *(f"- `{key}`: `{value}`" for key, value in result["pass_fail_counts"].items()),
        "",
        "## Top Failure Clusters",
        *(f"- `{item['flag']}`: `{item['count']}`" for item in result["top_failure_clusters"]),
        "",
        "## Failures By Scenario Family",
        *(f"- `{family}`: `{count}`" for family, count in result["failure_counts_by_family"].items()),
        "",
        "## Failures By Campaign",
        *(f"- `{campaign}`: `{count}`" for campaign, count in result["failure_counts_by_campaign"].items()),
        "",
        "## Failures By Selected Action Source",
        *(f"- `{source}`: `{count}`" for source, count in result["failure_counts_by_selected_action_source"].items()),
        "",
        "## Examples Of Worst Conversations",
    ]
    for item in result["worst_conversations"]:
        report_lines.extend(
            [
                f"### {item['scenario_id']}",
                f"- Family: `{item['scenario_family']}`",
                f"- Campaign: `{item['campaign_id']}`",
                f"- Priority: `{item['priority']}`",
                f"- Flags: `{', '.join(item['mechanical_failure_flags'])}`",
                f"- Buyer script: `{item['buyer_script']}`",
                f"- Final response: {item['final_response']}",
                "",
            ]
        )
    report_lines.extend(
        [
            "## Stability Guard Override Findings",
            *(f"- `{item}`" for item in result["stability_guard_override_findings"][:25]),
            "",
            "## Direct Question/Challenge Findings",
            *(f"- `{item}`" for item in result["direct_question_challenge_findings"][:25]),
            "",
            "## ASR Near-Miss Findings",
            *(f"- `{item}`" for item in result["asr_near_miss_findings"][:25]),
            "",
            "## Stop/Refusal Preservation",
            f"- Explicit-stop red findings: `{len(result['explicit_stop_red_findings'])}`",
            *(f"- `{item}`" for item in result["explicit_stop_red_findings"][:25]),
            "",
            "## Side-Effect Boundary Summary",
            *(f"- `{key}`: `{str(value).lower()}`" for key, value in result["side_effect_boundary"].items()),
            "",
            "## Recommendation",
            f"- `{result['recommendation']}`",
        ]
    )
    write_text(OUT_DIR / "report.md", "\n".join(report_lines) + "\n")

    packet_lines = [
        f"# {CHECKPOINT_ID} Review Packet",
        "",
        "This packet is mechanical triage evidence only. Codex did not assign final sales-quality labels.",
        "",
        f"- Scenario count: `{result['summary']['scenario_count']}`",
        f"- Core gate failures: `{result['summary']['core_gate_failure_count']}`",
        f"- Exploratory red findings: `{result['summary']['red_finding_count']}`",
        "",
        "## Review Priorities",
    ]
    for item in result["worst_conversations"][:20]:
        packet_lines.extend(
            [
                f"### {item['scenario_id']}",
                f"- Campaign: `{item['campaign_id']}`",
                f"- Family: `{item['scenario_family']}`",
                f"- Mechanical flags: `{', '.join(item['mechanical_failure_flags'])}`",
                f"- Buyer script: `{item['buyer_script']}`",
                f"- Final response: {item['final_response']}",
                "",
            ]
        )
    write_text(OUT_DIR / "review_packet.md", "\n".join(packet_lines) + "\n")
    return result


def main() -> None:
    result = write_outputs(generate())
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": result["status"],
                "scenario_count": result["summary"]["scenario_count"],
                "multi_turn_conversation_count": result["summary"]["multi_turn_conversation_count"],
                "campaign_count": len(result["campaign_counts"]),
                "family_count": len(result["family_counts"]),
                "core_gate_failure_count": result["summary"]["core_gate_failure_count"],
                "red_finding_count": result["summary"]["red_finding_count"],
                "side_effect_boundary": result["side_effect_boundary"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
