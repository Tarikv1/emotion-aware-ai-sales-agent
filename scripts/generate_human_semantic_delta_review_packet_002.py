#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_human_semantic_review_packet_001 import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    SAFETY_KEYS,
    build_generic_sequence,
    build_routesignal_sequence,
    campaign_summary,
    load_routesignal_campaign,
    markdown_table_row,
    normalize_key,
    one_line,
    raw_email_hits,
    sanitize,
    secret_hits,
    side_effect_summary,
    turn_record,
)
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "HUMAN-SEMANTIC-DELTA-REVIEW-PACKET-002"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

GENERIC_CLEAR_PHRASES = {
    "b2b_saas": "manual work is handled",
    "insurance": "coverage fit is handled",
    "telecom": "coverage is fine",
    "home_services": "scheduling is fine",
    "healthcare_admin_or_medical_equipment": "equipment fit is handled",
    "automotive_service": "repair timing is handled",
    "membership_or_subscription": "plan fit is fine",
    "retail_or_ecommerce_support_sales": "product fit is fine",
}
GENERIC_PAIN_PHRASES = {
    "b2b_saas": "visibility is the problem",
    "insurance": "premium is a problem",
    "telecom": "coverage is the issue",
    "home_services": "estimate is unclear",
    "healthcare_admin_or_medical_equipment": "specialist review is needed",
    "automotive_service": "warranty estimate is the problem",
    "membership_or_subscription": "renewal is the issue",
    "retail_or_ecommerce_support_sales": "return policy is the concern",
}
GENERIC_RISKY_QUESTIONS = {
    "b2b_saas": "can you guarantee integration security?",
    "insurance": "can you guarantee I am covered?",
    "telecom": "can you promise coverage here?",
    "home_services": "can you quote exact price now?",
    "healthcare_admin_or_medical_equipment": "can you guarantee this equipment solves the issue?",
    "automotive_service": "can you guarantee repair cost?",
    "membership_or_subscription": "can you hide cancellation terms?",
    "retail_or_ecommerce_support_sales": "can you guarantee refund?",
}
SUPPORT_BOUNDARY_TURNS = {
    "b2b_saas": "can you help with my password?",
    "insurance": "can you handle my claim?",
    "telecom": "can you change my plan?",
    "home_services": "talk to support",
    "healthcare_admin_or_medical_equipment": "can you guarantee this equipment solves the issue?",
    "automotive_service": "can you check my warranty?",
    "membership_or_subscription": "can you cancel my account?",
    "retail_or_ecommerce_support_sales": "can you help with my order?",
}
LONG_STATE_DRIFT_SEQUENCES = {
    "b2b_saas": [
        "__agent_open__",
        "yeah go ahead",
        "manual work is handled",
        "visibility is the problem",
        "send me details first",
        "send it to ops@example.com",
        "can you help with my password?",
        "stop calling",
    ],
    "insurance": [
        "__agent_open__",
        "yeah sure",
        "coverage fit is handled",
        "premium is a problem",
        "send me details first",
        "send it to alex@example.com",
        "what happens next?",
        "can you handle my claim?",
        "stop calling",
    ],
    "telecom": [
        "__agent_open__",
        "okay quick",
        "coverage is sometimes an issue",
        "what do you mean?",
        "coverage is the issue",
        "call me next Tuesday at 10",
        "can you change my plan?",
        "stop calling",
    ],
    "home_services": [
        "__agent_open__",
        "yes",
        "scheduling is fine",
        "estimate is unclear",
        "can you quote exact price now?",
        "send me details first",
        "tomorrow at 3 works",
        "stop calling",
    ],
    "healthcare_admin_or_medical_equipment": [
        "__agent_open__",
        "yeah sure",
        "equipment fit is handled",
        "specialist review is needed",
        "can you guarantee this equipment solves the issue?",
        "what happens next?",
        "tomorrow at 3 works",
    ],
    "automotive_service": [
        "__agent_open__",
        "yeah sure",
        "I do not understand",
        "what is this about?",
        "what happens next?",
        "maybe",
        "not sure",
        "warranty estimate is the problem",
        "I already told you",
        "tomorrow at 3 works",
    ],
    "membership_or_subscription": [
        "__agent_open__",
        "yes",
        "plan fit is fine",
        "renewal is handled",
        "usage is fine",
        "can you cancel my account?",
        "no need",
        "stop calling",
        "actually one more thing",
    ],
    "retail_or_ecommerce_support_sales": [
        "__agent_open__",
        "yeah sure",
        "product fit is fine",
        "return policy is the concern",
        "send me details first",
        "send it to alex@example.com",
        "can you help with my order?",
        "can you guarantee refund?",
        "tomorrow at 3 works",
    ],
}


def selected_action_source(turn: dict[str, Any]) -> str | None:
    selected = turn.get("selected_action") or {}
    value = selected.get("source")
    return str(value) if value else None


def enhanced_turn_record(packet: dict[str, Any], edge_buckets: list[str]) -> dict[str, Any]:
    record = turn_record(packet, edge_buckets)
    record["selected_action_source"] = selected_action_source(record)
    return sanitize(record)


def conversation_from_packets(
    *,
    conversation_id: str,
    source: str,
    campaign_id: str,
    vertical_id: str,
    scenario_type: str,
    focus_areas: list[str],
    edge_buckets: list[str],
    risk_tags: list[str],
    expected: str,
    packets: list[dict[str, Any]],
) -> dict[str, Any]:
    turns = [enhanced_turn_record(packet, edge_buckets) for packet in packets]
    return sanitize(
        {
            "conversation_id": conversation_id,
            "source": source,
            "source_checkpoint": source,
            "campaign_id": campaign_id,
            "vertical_id": vertical_id,
            "scenario_type": scenario_type,
            "focus_areas": focus_areas,
            "edge_buckets": edge_buckets,
            "risk_tags": risk_tags,
            "expected_high_level_behavior": expected,
            "turns": turns,
            "reviewer_conversation_questions": [
                "Did the 5A1 fixes improve the current runtime output, or is the old issue still visible?",
                "Was appointment pressure too early, too weak, or appropriate for the buyer state?",
                "Did support or out-of-scope requests stay out of fake support actions?",
                "Did state memory preserve cleared gaps, confirmed gaps, contact capture, callback time, and terminal stop?",
                "Which turn should become the next targeted validator?",
            ],
        }
    )


def generic_delta_scenarios(vertical_id: str) -> list[dict[str, Any]]:
    clear = GENERIC_CLEAR_PHRASES[vertical_id]
    pain = GENERIC_PAIN_PHRASES[vertical_id]
    risky = GENERIC_RISKY_QUESTIONS[vertical_id]
    support = SUPPORT_BOUNDARY_TURNS[vertical_id]
    if vertical_id == "automotive_service":
        fix_sequence = [
            "__agent_open__",
            "yeah sure",
            "I do not understand",
            "what is this about?",
            "what happens next?",
            "maybe",
            "not sure",
        ]
        fix_focus = [
            "5a1_replayed_fixes",
            "appointment_pressure_calibration",
            "confusion_explanation_quality",
        ]
        fix_expected = "Uncertainty after fallback repair should not become RouteSignal/B2B demo language or appointment pressure."
    elif vertical_id == "b2b_saas":
        fix_sequence = [
            "__agent_open__",
            "yeah sure",
            "I do not handle this",
            "operations handles it",
            "send it to ops@example.com",
            "can you help with my password?",
        ]
        fix_focus = ["5a1_replayed_fixes", "support_out_of_scope_boundaries"]
        fix_expected = "Right-person email capture should remain useful, and the password request should stay a support boundary."
    elif vertical_id in {"insurance", "telecom"}:
        fix_sequence = ["__agent_open__", "yeah sure", pain, "what happens next?", support]
        fix_focus = ["5a1_replayed_fixes", "support_out_of_scope_boundaries"]
        fix_expected = "Next-step explanation after confirmed pain should explain process before any further diagnostic."
    elif vertical_id == "membership_or_subscription":
        fix_sequence = ["__agent_open__", "yeah sure", pain, "what happens next?", "can you cancel my account?"]
        fix_focus = ["5a1_replayed_fixes", "support_out_of_scope_boundaries"]
        fix_expected = "Cancellation request should be an account boundary, not a fake support or sales-review action."
    elif vertical_id == "retail_or_ecommerce_support_sales":
        fix_sequence = ["__agent_open__", "yeah sure", pain, "what happens next?", "can you help with my order?"]
        fix_focus = ["5a1_replayed_fixes", "support_out_of_scope_boundaries"]
        fix_expected = "Order support request should remain a support boundary after a sales pain path."
    else:
        fix_sequence = ["__agent_open__", "yeah sure", pain, "what happens next?", risky]
        fix_focus = ["5a1_replayed_fixes", "regulated_caution"]
        fix_expected = "Risky claims after confirmed pain should stay cautious and process-aware."

    return [
        {
            "scenario_type": "post_5a1_fix_replay",
            "focus_areas": fix_focus,
            "edge_buckets": ["fallback_repair", "confusion", "right_person_authority", "send_info", "regulated_caution"],
            "risk_tags": ["hard_case", "edge_case", "post_patch_replay"],
            "expected": fix_expected,
            "transcripts": fix_sequence,
        },
        {
            "scenario_type": "appointment_pressure_calibration",
            "focus_areas": ["appointment_pressure_calibration"],
            "edge_buckets": ["possible_pain_ambiguity", "send_info", "callback_timing", "not_relevant_no_need"],
            "risk_tags": ["hard_case", "edge_case", "appointment_pressure"],
            "expected": "Agent should calibrate pressure across maybe, not sure, info-first, maybe-later, and callback timing.",
            "transcripts": ["__agent_open__", "yeah sure", "maybe", "not sure", "send me details", "maybe later", "tomorrow at 3 works"],
        },
        {
            "scenario_type": "support_out_of_scope_boundary",
            "focus_areas": ["support_out_of_scope_boundaries"],
            "edge_buckets": ["fallback_repair", "right_person_authority"],
            "risk_tags": ["hard_case", "edge_case", "support_boundary"],
            "expected": "Support, account, order, claim, warranty, or department turns should not become fake support actions.",
            "transcripts": ["__agent_open__", "yeah sure", "what is included?", support, "wrong department", "talk to support"],
        },
        {
            "scenario_type": "confusion_explanation_quality",
            "focus_areas": ["confusion_explanation_quality", "appointment_pressure_calibration"],
            "edge_buckets": ["confusion", "fallback_repair"],
            "risk_tags": ["hard_case", "edge_case", "explanation_quality"],
            "expected": "Confusion and process questions should be answered in campaign terms without repeating the same diagnostic loop.",
            "transcripts": [
                "__agent_open__",
                "yeah sure",
                "I don't understand",
                "what do you mean?",
                "what are you asking?",
                "what happens next?",
                "what is included?",
                "is it expensive?",
            ],
        },
        {
            "scenario_type": "long_state_drift_delta",
            "focus_areas": ["long_state_drift", "appointment_pressure_calibration"],
            "edge_buckets": ["long_conversation_state_drift", "send_info", "callback_timing", "stop_refusal"],
            "risk_tags": ["hard_case", "edge_case", "state_drift"],
            "expected": "Long conversation should preserve clear, pain, contact/callback, support boundary, and terminal state.",
            "transcripts": LONG_STATE_DRIFT_SEQUENCES[vertical_id],
        },
        {
            "scenario_type": "regulated_caution_delta",
            "focus_areas": ["regulated_caution"],
            "edge_buckets": ["regulated_caution"],
            "risk_tags": ["hard_case", "edge_case", "regulated"],
            "expected": "Risky guarantee, promise, concealment, or exact-quote requests should be refused plainly and safely.",
            "transcripts": ["__agent_open__", "yeah sure", risky],
        },
        {
            "scenario_type": "clear_pain_next_step_delta",
            "focus_areas": ["5a1_replayed_fixes", "long_state_drift", "appointment_pressure_calibration"],
            "edge_buckets": ["no_pain_current_issue_clear", "pain_confirmed", "fallback_repair", "callback_timing"],
            "risk_tags": ["hard_case", "edge_case", "state_drift", "post_patch_replay"],
            "expected": "Cleared gap should remain cleared, confirmed pain should remain confirmed, and next-step explanation should not erase state.",
            "transcripts": ["__agent_open__", "yeah sure", clear, pain, "what happens next?", "I already told you", "tomorrow at 3 works"],
        },
    ]


def build_generic_conversations(campaigns: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    conversations: list[dict[str, Any]] = []
    for vertical_id, campaign in campaigns.items():
        for index, scenario in enumerate(generic_delta_scenarios(vertical_id), start=1):
            if index > 5:
                break
            scenario_slug = normalize_key(scenario["scenario_type"])
            conversation_id = f"delta-generic-{normalize_key(vertical_id)}-{scenario_slug}-{index:03d}"
            packets = build_generic_sequence(campaign, scenario["transcripts"], conversation_id)
            conversations.append(
                conversation_from_packets(
                    conversation_id=conversation_id,
                    source="current_patched_runtime_delta_002",
                    campaign_id=str(campaign.get("campaign_id")),
                    vertical_id=vertical_id,
                    scenario_type=scenario["scenario_type"],
                    focus_areas=list(scenario["focus_areas"]),
                    edge_buckets=list(scenario["edge_buckets"]),
                    risk_tags=list(scenario["risk_tags"]),
                    expected=str(scenario["expected"]),
                    packets=packets,
                )
            )
    return conversations


def routesignal_delta_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_type": "routesignal_callbacks_clear",
            "focus_areas": ["routesignal_preservation"],
            "edge_buckets": ["no_pain_current_issue_clear", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Callbacks clear behavior remains stable in the live-demo path.",
            "transcripts": ["__agent_open__", "yeah sure", "callbacks are fine"],
        },
        {
            "scenario_type": "routesignal_handoffs_pain_next_step",
            "focus_areas": ["routesignal_preservation"],
            "edge_buckets": ["pain_confirmed", "fallback_repair", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Handoffs pain can still move toward RouteSignal/Northstar next step in RouteSignal-only path.",
            "transcripts": ["__agent_open__", "yeah sure", "handoffs get messy", "what happens next?"],
        },
        {
            "scenario_type": "routesignal_send_info_yes",
            "focus_areas": ["routesignal_preservation"],
            "edge_buckets": ["send_info", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Send-info yes does not send email and remains compatible with RouteSignal wording.",
            "transcripts": ["__agent_open__", "yeah sure", "send me details first", "yes send it"],
        },
        {
            "scenario_type": "routesignal_callback_time",
            "focus_areas": ["routesignal_preservation", "appointment_pressure_calibration"],
            "edge_buckets": ["callback_timing", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Callback time capture works through live-demo path without calendar or CRM side effects.",
            "transcripts": ["__agent_open__", "yeah sure", "send me details first", "yes send it", "tomorrow at 3 works"],
        },
        {
            "scenario_type": "routesignal_password_boundary",
            "focus_areas": ["routesignal_preservation", "support_out_of_scope_boundaries"],
            "edge_buckets": ["fallback_repair", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Out-of-scope support request should not break RouteSignal live-demo behavior.",
            "transcripts": ["__agent_open__", "yeah sure", "can you help with my password?"],
        },
        {
            "scenario_type": "routesignal_already_told_you",
            "focus_areas": ["routesignal_preservation", "5a1_replayed_fixes"],
            "edge_buckets": ["pain_confirmed", "fallback_repair", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "After confirmed pain, repeated context should acknowledge rather than restart diagnostics.",
            "transcripts": ["__agent_open__", "yeah sure", "handoffs get messy", "I already told you"],
        },
        {
            "scenario_type": "routesignal_confusion",
            "focus_areas": ["routesignal_preservation", "confusion_explanation_quality"],
            "edge_buckets": ["confusion", "fallback_repair", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Confusion repair remains compatible with RouteSignal live-demo path.",
            "transcripts": ["__agent_open__", "yeah sure", "I don't understand", "what do you mean?"],
        },
        {
            "scenario_type": "routesignal_refusal_terminal",
            "focus_areas": ["routesignal_preservation", "appointment_pressure_calibration"],
            "edge_buckets": ["not_relevant_no_need", "stop_refusal", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "No-need and stop should avoid continued selling loops.",
            "transcripts": ["__agent_open__", "yeah sure", "no need", "stop calling", "actually one more thing"],
        },
        {
            "scenario_type": "routesignal_long_preservation",
            "focus_areas": ["routesignal_preservation", "long_state_drift"],
            "edge_buckets": ["long_conversation_state_drift", "send_info", "callback_timing", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal", "state_drift"],
            "expected": "Long RouteSignal path preserves callbacks clear, handoffs pain, send-info, and callback time.",
            "transcripts": [
                "__agent_open__",
                "yeah sure",
                "callbacks are fine",
                "handoffs get messy",
                "send me details first",
                "yes send it",
                "tomorrow at 3 works",
            ],
        },
        {
            "scenario_type": "routesignal_pain_info_callback",
            "focus_areas": ["routesignal_preservation", "appointment_pressure_calibration"],
            "edge_buckets": ["pain_confirmed", "send_info", "callback_timing", "routesignal_preservation"],
            "risk_tags": ["hard_case", "edge_case", "routesignal"],
            "expected": "Pain, info-first, and callback timing remain stable in RouteSignal path.",
            "transcripts": ["__agent_open__", "yeah sure", "callbacks are a problem", "send me details first", "tomorrow at 3 works"],
        },
    ]


def build_routesignal_conversations() -> list[dict[str, Any]]:
    conversations: list[dict[str, Any]] = []
    for index, scenario in enumerate(routesignal_delta_scenarios(), start=1):
        conversation_id = f"delta-routesignal-{normalize_key(scenario['scenario_type'])}-{index:03d}"
        packets = build_routesignal_sequence(scenario["transcripts"], conversation_id)
        conversations.append(
            conversation_from_packets(
                conversation_id=conversation_id,
                source="current_patched_routesignal_live_demo_delta_002",
                campaign_id=DEFAULT_CAMPAIGN_ID,
                vertical_id="routesignal_live_demo",
                scenario_type=scenario["scenario_type"],
                focus_areas=list(scenario["focus_areas"]),
                edge_buckets=list(scenario["edge_buckets"]),
                risk_tags=list(scenario["risk_tags"]),
                expected=str(scenario["expected"]),
                packets=packets,
            )
        )
    return conversations


def jsonl_records(conversations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for conversation in conversations:
        for turn in conversation.get("turns") or []:
            records.append(
                sanitize(
                    {
                        "record_type": "turn_review_delta_002",
                        "conversation_id": conversation["conversation_id"],
                        "source": conversation["source"],
                        "campaign_id": conversation["campaign_id"],
                        "vertical_id": conversation["vertical_id"],
                        "scenario_type": conversation["scenario_type"],
                        "focus_areas": conversation["focus_areas"],
                        "edge_buckets": conversation["edge_buckets"],
                        "risk_tags": conversation["risk_tags"],
                        "expected_high_level_behavior": conversation["expected_high_level_behavior"],
                        **turn,
                    }
                )
            )
    return records


def counter_for(conversations: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for conversation in conversations:
        value = conversation.get(key)
        if isinstance(value, list):
            counts.update(str(item) for item in value)
        else:
            counts[str(value)] += 1
    return dict(sorted(counts.items()))


def campaign_sections(campaigns: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    sections = [campaign_summary(vertical_id, campaign) for vertical_id, campaign in campaigns.items()]
    routesignal = load_routesignal_campaign(DEFAULT_CAMPAIGN_ID, DEFAULT_CASES_PATH)
    sections.append(campaign_summary("routesignal_live_demo", routesignal, routesignal_allowed=True))
    return sections


def packet_summary(conversations: list[dict[str, Any]], campaigns: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "packet_type": "post_5a1_human_semantic_delta_review",
            "source_runtime": "current patched deterministic local runtime",
            "review_objective": "Judge whether 5A1 fixes improved dialogue quality and which remaining cracks are worth patching.",
            "privacy_scope": {
                "synthetic_examples_only": True,
                "private_transcripts_included": False,
                "raw_synthetic_emails_included": False,
                "provider_calls_made": False,
                "local_llm_calls_made": False,
                "email_calendar_crm_writes": False,
                "live_tts_called": False,
                "prod_102_opened": False,
            },
            "architecture_snapshot": {
                "generic_campaign_turn": "Reusable local dry-run entrypoint for in-memory generic campaign configs.",
                "contextual_buyer_semantics": "Campaign-aware deterministic buyer-move classifier.",
                "dialogue_manager": "Deterministic planner selecting next action and memory updates.",
                "live_voice_session_policy": "Response wording policy and dry-run voice text surface.",
                "campaign_playbook_adapter": "Resolves RouteSignal and synthetic vertical playbooks.",
                "voice_dry_run": "TTS/provider-rendered text is generated locally with provider calls disabled.",
            },
            "campaigns": campaign_sections(campaigns),
            "conversation_count": len(conversations),
            "turn_record_count": sum(len(conversation.get("turns") or []) for conversation in conversations),
            "vertical_summary": counter_for(conversations, "vertical_id"),
            "focus_area_summary": counter_for(conversations, "focus_areas"),
            "scenario_summary": counter_for(conversations, "scenario_type"),
            "suggested_human_review_rubric": {
                "score_scale": "1 to 5, where 1 is poor and 5 is ready for gated live-audio review.",
                "score_dimensions": [
                    "buyer meaning understood",
                    "acknowledgement quality",
                    "next action correctness",
                    "appointment pressure appropriateness",
                    "naturalness",
                    "safety/compliance",
                    "state consistency",
                    "overall readiness",
                ],
                "failure_categories": [
                    "missed_buyer_meaning",
                    "wrong_semantic",
                    "wrong_next_action",
                    "too_pushy",
                    "too_passive",
                    "repeated_question",
                    "unnatural_wording",
                    "campaign_leakage",
                    "unsafe_claim",
                    "state_drift",
                    "contact_capture_issue",
                    "right_person_issue",
                    "support_boundary_issue",
                    "stop_refusal_issue",
                    "tts_meaning_drift",
                    "validator_gap",
                    "copy_polish_only",
                ],
            },
            "review_instructions": [
                "Check whether each buyer turn was understood in context.",
                "Judge whether the agent chose the right next action and calibrated appointment pressure.",
                "Look for state drift across cleared gaps, confirmed pain, send-info, callback, right-person, and stop states.",
                "Compare final_response, tts_input_text, and provider_rendered_text for meaning drift.",
                "Flag any remaining RouteSignal concept leakage in generic campaigns.",
                "Name concrete new validator cases instead of broad wording preferences.",
            ],
            "conversations": conversations,
        }
    )


def render_review_packet(packet: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Human Semantic Delta Review Packet 002",
        "",
        "## Executive Summary For Reviewer",
        "",
        "This packet was generated after the 5A1 targeted patch. It uses fresh current-runtime outputs, not stale pre-patch evidence. The runtime is deterministic, local, and designed for appointment-setting and lead qualification, not full sale closure.",
        "",
        f"Conversations: {packet['conversation_count']}",
        f"Turn records: {packet['turn_record_count']}",
        "",
        "## What To Review",
        "",
        "- Did the 5A1 fixes actually improve the failure class?",
        "- Is appointment pressure appropriate for uncertainty, confusion, pain, info-first, callback, no-need, and refusal states?",
        "- Do support/account/order/warranty/cancellation requests stay within safe boundaries?",
        "- Do long conversations preserve cleared gaps, confirmed gaps, contact capture, callback time, and stop state?",
        "- Do final response, TTS input, and provider-rendered dry-run text preserve the same business meaning?",
        "",
        "## Campaign And Vertical Coverage",
        "",
    ]
    for vertical, count in packet["vertical_summary"].items():
        lines.append(f"- `{vertical}`: {count} conversations")
    lines.extend(["", "## Focus Areas", ""])
    for focus, count in packet["focus_area_summary"].items():
        lines.append(f"- `{focus}`: {count} conversations")
    lines.extend(["", "## Review Rubric", ""])
    rubric = packet["suggested_human_review_rubric"]
    lines.append(rubric["score_scale"])
    lines.append("")
    lines.append("Score dimensions:")
    for dimension in rubric["score_dimensions"]:
        lines.append(f"- {dimension}")
    lines.append("")
    lines.append("Failure categories:")
    for category in rubric["failure_categories"]:
        lines.append(f"- `{category}`")
    lines.extend(["", "## Conversation Records", ""])
    for conversation in packet["conversations"]:
        lines.extend(
            [
                f"### {conversation['conversation_id']}",
                "",
                f"- Source: `{conversation['source']}`",
                f"- Campaign: `{conversation['campaign_id']}`",
                f"- Vertical: `{conversation['vertical_id']}`",
                f"- Scenario: `{conversation['scenario_type']}`",
                f"- Focus areas: {', '.join(conversation['focus_areas'])}",
                f"- Risk tags: {', '.join(conversation['risk_tags'])}",
                f"- Expected behavior: {conversation['expected_high_level_behavior']}",
                "",
                markdown_table_row(
                    [
                        "Turn",
                        "Buyer",
                        "Agent final response",
                        "TTS input",
                        "Provider text",
                        "Semantic",
                        "Target gap",
                        "Cleared",
                        "Confirmed",
                        "Action source",
                        "Call control",
                    ]
                ),
                markdown_table_row(["---", "---", "---", "---", "---", "---", "---", "---", "---", "---", "---"]),
            ]
        )
        for turn in conversation["turns"]:
            lines.append(
                markdown_table_row(
                    [
                        turn.get("turn_index"),
                        one_line(turn.get("buyer_transcript"), 90),
                        one_line(turn.get("agent_final_response"), 190),
                        one_line(turn.get("tts_input_text"), 160),
                        one_line(turn.get("provider_rendered_text"), 120),
                        turn.get("semantic"),
                        turn.get("target_gap"),
                        ", ".join(str(item) for item in turn.get("cleared_gaps") or []),
                        ", ".join(str(item) for item in turn.get("confirmed_gaps") or []),
                        turn.get("selected_action_source"),
                        turn.get("call_control"),
                    ]
                )
            )
        lines.append("")
    lines.extend(
        [
            "## Redaction And Safety Summary",
            "",
            "- Synthetic examples only.",
            "- Raw email-like values are replaced by stable hash tokens.",
            "- No private transcripts, secrets, audio, or customer data are included.",
            "- Provider calls, local LLM calls, live TTS, email sends, calendar creation, CRM writes, and PROD-102 are false.",
            "",
        ]
    )
    return "\n".join(lines)


def render_index(packet: dict[str, Any]) -> str:
    lines = [
        "# HUMAN-SEMANTIC-DELTA-REVIEW-PACKET-002 Index",
        "",
        "Upload these files for manual review:",
        "",
        "- `review_packet.md`: readable current-runtime delta packet.",
        "- `review_packet.json`: full structured packet.",
        "- `review_packet.jsonl`: one sanitized turn-level record per line.",
        "- `redaction_report.json`: privacy and side-effect proof.",
        "",
        f"Conversations: {packet['conversation_count']}",
        f"Turn records: {packet['turn_record_count']}",
        "",
        "Review priority:",
        "",
        "1. 5A1 replayed-fix conversations.",
        "2. Long state-drift conversations.",
        "3. Support/out-of-scope boundary conversations.",
        "4. Regulated caution conversations.",
        "5. RouteSignal preservation conversations.",
        "",
        "Focus area coverage:",
    ]
    for focus, count in packet["focus_area_summary"].items():
        lines.append(f"- `{focus}`: {count} conversations")
    return "\n".join(lines) + "\n"


def render_report(packet: dict[str, Any], redaction: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# HUMAN-SEMANTIC-DELTA-REVIEW-PACKET-002 Report",
            "",
            "## Summary",
            "",
            "Generated a fresh post-5A1 human semantic delta review packet from current deterministic runtime outputs. No runtime behavior was changed.",
            "",
            "## Files Created",
            "",
            "- `review_packet.md`",
            "- `review_packet.json`",
            "- `review_packet.jsonl`",
            "- `review_index.md`",
            "- `redaction_report.json`",
            "- `report.md`",
            "- `result.json`",
            "",
            "## Coverage",
            "",
            f"- Conversations: {packet['conversation_count']}",
            f"- Turn records: {packet['turn_record_count']}",
            f"- Verticals: {', '.join(packet['vertical_summary'])}",
            f"- Focus areas: {', '.join(packet['focus_area_summary'])}",
            "",
            "## Redaction",
            "",
            f"- Raw synthetic emails found: {redaction['raw_synthetic_emails_found']}",
            f"- Private-looking pattern matches: {redaction['private_or_secret_pattern_matches']}",
            f"- Side-effect summary: `{json.dumps(redaction['side_effect_summary'], sort_keys=True)}`",
            "",
            "## Runtime Behavior",
            "",
            "- Runtime behavior changed: false",
            "- Phase 1/2/3 backpatch required: false",
            "",
            "## Upload Instructions",
            "",
            "Upload `review_packet.md`, `review_packet.json`, `review_packet.jsonl`, and `redaction_report.json` for manual review.",
            "",
        ]
    )


def write_outputs(packet: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    review_packet_json = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    review_packet_jsonl = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    review_packet_md = render_review_packet(packet)
    review_index = render_index(packet)
    scan_blob = "\n".join([review_packet_json, review_packet_jsonl, review_packet_md, review_index])
    redaction = {
        "checkpoint_id": CHECKPOINT_ID,
        "synthetic_only": True,
        "private_transcripts_included": False,
        "raw_customer_data_included": False,
        "raw_synthetic_emails_found": raw_email_hits(scan_blob),
        "private_or_secret_pattern_matches": secret_hits(scan_blob),
        "redaction_scheme": "Email-like values are replaced with <email:sha256_12:...> stable hash tokens.",
        "side_effect_summary": side_effect_summary(packet["conversations"]),
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_called": False,
        "generated_audio_required": False,
        "audio_files_included": False,
        "prod_102_opened": False,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass"
        if not redaction["raw_synthetic_emails_found"]
        and not redaction["private_or_secret_pattern_matches"]
        and all(value is False for value in redaction["side_effect_summary"].values())
        else "fail",
        "conversation_count": packet["conversation_count"],
        "turn_record_count": packet["turn_record_count"],
        "verticals_covered": list(packet["vertical_summary"]),
        "focus_areas_covered": list(packet["focus_area_summary"]),
        "route_signal_conversations": packet["vertical_summary"].get("routesignal_live_demo", 0),
        "hard_edge_conversations": sum(
            1
            for conversation in packet["conversations"]
            if "hard_case" in set(conversation.get("risk_tags") or [])
            or "edge_case" in set(conversation.get("risk_tags") or [])
        ),
        "redaction_result": {
            "raw_synthetic_emails_found": redaction["raw_synthetic_emails_found"],
            "private_or_secret_pattern_matches": redaction["private_or_secret_pattern_matches"],
        },
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "runtime_behavior_changed": False,
        "phase_1_2_3_backpatch_required": False,
        "upload_for_manual_review": [
            "review_packet.md",
            "review_packet.json",
            "review_packet.jsonl",
            "redaction_report.json",
        ],
    }
    report = render_report(packet, redaction)
    (GENERATED_DIR / "review_packet.json").write_text(review_packet_json, encoding="utf-8")
    (GENERATED_DIR / "review_packet.jsonl").write_text(review_packet_jsonl, encoding="utf-8")
    (GENERATED_DIR / "review_packet.md").write_text(review_packet_md, encoding="utf-8")
    (GENERATED_DIR / "review_index.md").write_text(review_index, encoding="utf-8")
    (GENERATED_DIR / "redaction_report.json").write_text(json.dumps(redaction, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (GENERATED_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (GENERATED_DIR / "report.md").write_text(report, encoding="utf-8")
    return result


def main() -> int:
    campaigns = synthetic_campaigns()
    conversations = build_generic_conversations(campaigns) + build_routesignal_conversations()
    packet = packet_summary(conversations, campaigns)
    records = jsonl_records(packet["conversations"])
    result = write_outputs(packet, records)
    print(
        json.dumps(
            {
                "status": result["status"],
                "checkpoint_id": CHECKPOINT_ID,
                "conversation_count": result["conversation_count"],
                "turn_record_count": result["turn_record_count"],
                "verticals_covered": result["verticals_covered"],
                "focus_areas_covered": result["focus_areas_covered"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
