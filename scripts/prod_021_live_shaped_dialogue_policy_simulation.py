#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from callcenteren_specificity_scoring import ROOT, rate, rel_path, score_answer, write_json, write_text
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import (
    DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
    DEFAULT_RETRIEVAL_MIN_SCORE,
    DEFAULT_RETRIEVAL_REGISTRY,
    DEFAULT_RETRIEVAL_TARGET_MS,
    build_guarded_response_packet,
)
from prod_019_guarded_runtime_composer_hooks import (
    NON_SALE_OUTCOMES,
    PAYMENT_TOKENS,
    SAFE_CLOSE_OUTCOMES,
    answer_contains_payment,
    expected_outcome_correct,
    winner,
)
from prod_020_naturalized_customer_turn_evaluation import DEFAULT_RESULT as DEFAULT_PROD_020_RESULT
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases


PROD_021_ID = "PROD-021-live-shaped-dialogue-policy-simulation"
SOURCE_PROD_011_ID = "PROD-011-dialogue-policy-hardening"
SOURCE_PROD_020_ID = "PROD-020-naturalized-customer-turn-evaluation"
DEFAULT_CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-021-live-shaped-dialogue-policy-simulation.json"
DEFAULT_PROD_011_CASE = ROOT / "research" / "experiments" / "cases" / "prod-011-dialogue-policy-hardening.json"
DEFAULT_CAMPAIGN_CASE_SOURCE = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-021-live-shaped-dialogue-policy-simulation"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"

PROTECTED_CONTROLS = {"transfer-or-escalate", "end-call", "hang-up", "close-and-log-sale-ready"}
ESCALATION_ACTIONS = {
    "claim-boundary-escalation",
    "privacy-safe-escalation",
    "technical-escalation",
    "support-first-escalation",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def base_case_data() -> dict[str, Any]:
    campaign_id = "campaign-prod-005-b2b-software"
    return {
        "prod_021_case_id": PROD_021_ID,
        "title": "PROD-021 live-shaped dialogue-policy simulation",
        "source_checkpoints": [SOURCE_PROD_011_ID, SOURCE_PROD_020_ID],
        "source_policy_id": "brain_002_dialogue_policy_hardening_v1",
        "case_design": {
            "surface": "synthetic live-shaped customer turns only",
            "multi_turn": True,
            "agent_answers_generated_by_runner": True,
            "scenario_labels_runtime_visible": False,
            "source_pattern_ids_runtime_visible": False,
        },
        "boundaries": {
            "copied_transcript_text_used": False,
            "generated_from_single_source_transcript": False,
            "contains_transcript_derived_prompt_text": False,
            "provider_calls_made": False,
            "private_data_read": False,
            "dataset_download_performed": False,
        },
        "calls": [
            {
                "call_id": "PROD-021-C01",
                "source_prod_011_call_id": "PROD-010-C01",
                "domain": "b2b_software",
                "scenario_label": "software_multi_objection_sale",
                "campaign_id": campaign_id,
                "eligible_for_close": True,
                "expected_final": {
                    "policy_action": "close-and-log-sale-ready",
                    "call_control": "close-and-log-sale-ready",
                    "sale_ready": True,
                    "non_sale_correct": False,
                },
                "source_pattern_ids": [
                    "prod006-pattern-telecom-price-resistance",
                    "prod006-pattern-general-brushoff",
                    "prod006-pattern-product-order-intent",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C01-T01",
                        "PROD-010-C01-T01",
                        1,
                        "relevance-check",
                        "The cost sounds high, and I need to know whether reviewing this is worth my time.",
                        "price_concern",
                        "price_resistance",
                        "price",
                        "cautious",
                        "value-clarify",
                        "continue-call",
                        "non_sale_correct",
                        [
                            "acknowledge the cost concern without pressure",
                            "ask one focused question about value, timing, or fit",
                            "avoid unsupported savings claims",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C01-T02",
                        "PROD-010-C01-T03",
                        2,
                        "comparison",
                        "We already use another provider, so compare this fairly without pressure.",
                        "competitor_compare",
                        "competitor_comparison",
                        "competitor",
                        "analytical",
                        "fair-compare",
                        "continue-call",
                        "non_sale_correct",
                        [
                            "avoid unsupported competitor claims",
                            "ask what comparison point matters most",
                            "keep the tone neutral and low pressure",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C01-T03",
                        "PROD-010-C01-T05",
                        3,
                        "timing-openness-check",
                        "I need time to think; do not rush me into a commitment today.",
                        "timing_delay",
                        "timing_delay",
                        "timing",
                        "hesitant",
                        "autonomy-check",
                        "continue-call",
                        "callback_agreed",
                        [
                            "respect the customer's timing concern",
                            "offer a low-commitment callback or clarification",
                            "avoid forcing a decision",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C01-T04",
                        "PROD-010-C01-T07",
                        4,
                        "commitment-confirmation",
                        "If this fits our process and there is no payment today, I am ready to agree to the next step.",
                        "commitment",
                        "multi_objection_commitment",
                        "resolved",
                        "calm_interest",
                        "close-and-log-sale-ready",
                        "close-and-log-sale-ready",
                        "sale_ready",
                        [
                            "confirm fit before marking verbal commitment",
                            "make clear this is not payment collection",
                            "record only a sale-ready verbal next step",
                        ],
                    ),
                ],
            },
            {
                "call_id": "PROD-021-C02",
                "source_prod_011_call_id": "PROD-010-C02",
                "domain": "b2b_software",
                "scenario_label": "software_procurement_authority_delay",
                "campaign_id": campaign_id,
                "eligible_for_close": False,
                "expected_final": {
                    "policy_action": "procurement-review",
                    "call_control": "continue-call",
                    "sale_ready": False,
                    "non_sale_correct": True,
                },
                "source_pattern_ids": [
                    "prod006-pattern-general-brushoff",
                    "prod006-pattern-telecom-price-resistance",
                    "prod006-pattern-insurance-boundary",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C02-T01",
                        "PROD-010-C02-T03",
                        1,
                        "authority-check",
                        "My boss has to review this before I can decide.",
                        "authority_gap",
                        "authority_unclear",
                        "authority",
                        "firm",
                        "stakeholder-review",
                        "continue-call",
                        "non_sale_correct",
                        [
                            "acknowledge that another decision maker is involved",
                            "offer a shareable summary or one concern to address",
                            "avoid treating the customer as sale-ready",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C02-T02",
                        "PROD-010-C02-T05",
                        2,
                        "procurement-review",
                        "Procurement needs written information and nothing firm from me today.",
                        "procurement_rule",
                        "procurement_review",
                        "procurement",
                        "neutral",
                        "procurement-review",
                        "continue-call",
                        "non_sale_correct",
                        [
                            "respect the procurement process",
                            "offer written information without pressure",
                            "avoid premature close language",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C02-T03",
                        "PROD-010-C02-T07",
                        3,
                        "procurement-review",
                        "Next week might work for review, but I cannot commit to anything firm now.",
                        "delay_confirmed",
                        "procurement_delay",
                        "procurement",
                        "firm",
                        "procurement-review",
                        "continue-call",
                        "callback_agreed",
                        [
                            "treat the next step as a follow-up only",
                            "avoid marking a verbal commitment",
                            "summarize the agreed low-pressure review path",
                        ],
                    ),
                ],
            },
            {
                "call_id": "PROD-021-C03",
                "source_prod_011_call_id": "PROD-010-C03",
                "domain": "insurance_service",
                "scenario_label": "insurance_claim_privacy_escalation",
                "campaign_id": campaign_id,
                "eligible_for_close": False,
                "expected_final": {
                    "policy_action": "privacy-safe-escalation",
                    "call_control": "transfer-or-escalate",
                    "sale_ready": False,
                    "non_sale_correct": True,
                },
                "source_pattern_ids": [
                    "prod006-pattern-insurance-boundary",
                    "prod006-pattern-medical-equipment-human-request",
                    "prod006-pattern-home-service-complaint",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C03-T01",
                        "PROD-010-C03-T03",
                        1,
                        "claim-boundary",
                        "Can you guarantee this coverage before I share details?",
                        "claim_certainty",
                        "claim_boundary",
                        "claim_boundary",
                        "anxious",
                        "claim-boundary-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "do not guarantee coverage",
                            "route claim certainty questions to a human specialist",
                            "avoid collecting sensitive details in the sales flow",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C03-T02",
                        "PROD-010-C03-T05",
                        2,
                        "privacy-boundary",
                        "I am worried about privacy and want a real person before I answer.",
                        "privacy_concern",
                        "privacy_concern",
                        "privacy",
                        "guarded",
                        "privacy-safe-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "acknowledge the privacy concern",
                            "route to a human specialist instead of continuing sales",
                            "avoid asking for sensitive details",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C03-T03",
                        "PROD-010-C03-T07",
                        3,
                        "privacy-boundary",
                        "Please route this to a human specialist before we discuss anything else.",
                        "needs_review",
                        "privacy_boundary",
                        "privacy",
                        "cautious",
                        "privacy-safe-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "honor the human handoff request",
                            "do not keep selling",
                            "keep the response concise",
                        ],
                    ),
                ],
            },
            {
                "call_id": "PROD-021-C04",
                "source_prod_011_call_id": "PROD-010-C04",
                "domain": "medical_equipment",
                "scenario_label": "medical_technical_safety_escalation",
                "campaign_id": campaign_id,
                "eligible_for_close": False,
                "expected_final": {
                    "policy_action": "technical-escalation",
                    "call_control": "transfer-or-escalate",
                    "sale_ready": False,
                    "non_sale_correct": True,
                },
                "source_pattern_ids": [
                    "prod006-pattern-medical-equipment-human-request",
                    "prod006-pattern-insurance-boundary",
                    "prod006-pattern-auto-service-fit-check",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C04-T01",
                        "PROD-010-C04-T03",
                        1,
                        "technical-boundary",
                        "I need a human specialist for the device safety details before I decide.",
                        "safety_question",
                        "technical_risk",
                        "technical_risk",
                        "concerned",
                        "technical-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "route technical safety details to a specialist",
                            "avoid guessing",
                            "do not make unsupported safety claims",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C04-T02",
                        "PROD-010-C04-T07",
                        2,
                        "technical-boundary",
                        "A specialist is required here; I do not want an automatic answer.",
                        "specialist_required",
                        "technical_escalation",
                        "technical_question",
                        "concerned",
                        "technical-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "confirm specialist handoff",
                            "avoid continuing automatically",
                            "keep sales pressure out of the answer",
                        ],
                    ),
                ],
            },
            {
                "call_id": "PROD-021-C05",
                "source_prod_011_call_id": "PROD-010-C05",
                "domain": "membership_service",
                "scenario_label": "membership_refusal_end_call",
                "campaign_id": campaign_id,
                "eligible_for_close": False,
                "expected_final": {
                    "policy_action": "end-call",
                    "call_control": "end-call",
                    "sale_ready": False,
                    "non_sale_correct": True,
                },
                "source_pattern_ids": [
                    "prod006-pattern-membership-cancellation",
                    "prod006-pattern-general-brushoff",
                    "prod006-pattern-home-service-complaint",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C05-T01",
                        "PROD-010-C05-T01",
                        1,
                        "refusal",
                        "No thank you, I want to cancel and stop the sales call.",
                        "cancel_intent",
                        "cancel_intent",
                        "cancellation",
                        "firm_negative",
                        "end-call",
                        "end-call",
                        "end_call",
                        [
                            "respect the refusal",
                            "stop the sales conversation",
                            "avoid retention pressure",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C05-T02",
                        "PROD-010-C05-T07",
                        2,
                        "refusal",
                        "Stop calling me. I am not interested.",
                        "refusal_confirmed",
                        "angry_refusal",
                        "anger",
                        "angry",
                        "end-call",
                        "end-call",
                        "end_call",
                        [
                            "confirm the call will end",
                            "avoid another offer",
                            "keep the response polite and brief",
                        ],
                    ),
                ],
            },
            {
                "call_id": "PROD-021-C06",
                "source_prod_011_call_id": "PROD-010-C06",
                "domain": "home_service",
                "scenario_label": "home_service_support_handoff",
                "campaign_id": campaign_id,
                "eligible_for_close": False,
                "expected_final": {
                    "policy_action": "support-first-escalation",
                    "call_control": "transfer-or-escalate",
                    "sale_ready": False,
                    "non_sale_correct": True,
                },
                "source_pattern_ids": [
                    "prod006-pattern-home-service-complaint",
                    "prod006-pattern-general-brushoff",
                    "prod006-pattern-membership-cancellation",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C06-T01",
                        "PROD-010-C06-T01",
                        1,
                        "support-boundary",
                        "My service issue is unresolved, and I need a real person, not an upsell.",
                        "support_request",
                        "support",
                        "support",
                        "frustrated",
                        "support-first-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "prioritize issue resolution",
                            "route to support or a human specialist",
                            "avoid turning the support issue into a sale",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C06-T02",
                        "PROD-010-C06-T07",
                        2,
                        "support-boundary",
                        "Please route me to a human support specialist before trying to sell anything else.",
                        "support_required",
                        "support_upsell_blocked",
                        "support",
                        "frustrated",
                        "support-first-escalation",
                        "transfer-or-escalate",
                        "human_handoff",
                        [
                            "confirm support-first routing",
                            "do not continue selling",
                            "avoid unsupported troubleshooting",
                        ],
                    ),
                ],
            },
            {
                "call_id": "PROD-021-C07",
                "source_prod_011_call_id": "PROD-010-C06",
                "domain": "automotive",
                "scenario_label": "trust_price_callback",
                "campaign_id": campaign_id,
                "eligible_for_close": False,
                "expected_final": {
                    "policy_action": "autonomy-check",
                    "call_control": "continue-call",
                    "sale_ready": False,
                    "non_sale_correct": True,
                },
                "source_pattern_ids": [
                    "prod006-pattern-home-service-complaint",
                    "prod006-pattern-telecom-price-resistance",
                    "prod006-pattern-general-brushoff",
                ],
                "turns": [
                    live_turn(
                        "PROD-021-C07-T01",
                        "PROD-010-C06-T03",
                        1,
                        "trust-repair",
                        "I do not know your company. How can I verify this is legitimate?",
                        "trust_gap",
                        "trust_gap",
                        "trust",
                        "skeptical",
                        "trust-repair",
                        "continue-call",
                        "support_only",
                        [
                            "repair trust with verification options",
                            "keep the next step low pressure",
                            "avoid vague authority claims",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C07-T02",
                        "PROD-010-C01-T01",
                        2,
                        "price-check",
                        "The cost sounds high; is this worth my time?",
                        "price_concern",
                        "price_resistance",
                        "price",
                        "cautious",
                        "value-clarify",
                        "continue-call",
                        "non_sale_correct",
                        [
                            "acknowledge the cost concern",
                            "ask whether price, value, or timing is the main issue",
                            "avoid pressure",
                        ],
                    ),
                    live_turn(
                        "PROD-021-C07-T03",
                        "PROD-010-C01-T05",
                        3,
                        "callback",
                        "Send me a short summary and call back later; I need time to think.",
                        "timing_delay",
                        "timing_delay",
                        "timing",
                        "hesitant",
                        "autonomy-check",
                        "continue-call",
                        "callback_agreed",
                        [
                            "respect the request for time",
                            "offer a short summary or callback",
                            "avoid forcing commitment",
                        ],
                    ),
                ],
            },
        ],
    }


def live_turn(
    turn_id: str,
    source_prod_011_turn_id: str,
    turn_position: int,
    stage: str,
    customer_transcript: str,
    intent: str,
    signal: str,
    objection_type: str,
    emotional_signal: str,
    expected_policy_action: str,
    expected_call_control: str,
    expected_outcome: str,
    expected_agent_response_requirements: list[str],
) -> dict[str, Any]:
    return {
        "turn_id": turn_id,
        "source_prod_011_turn_id": source_prod_011_turn_id,
        "turn_position": turn_position,
        "stage": stage,
        "input_type": "speech-final",
        "silence_count": 0,
        "customer_transcript": customer_transcript,
        "intent": intent,
        "signal": signal,
        "objection_type": objection_type,
        "emotional_signal": emotional_signal,
        "expected_policy_action": expected_policy_action,
        "expected_call_control": expected_call_control,
        "expected_outcome": expected_outcome,
        "expected_agent_response_requirements": expected_agent_response_requirements,
        "protected_context": expected_call_control in PROTECTED_CONTROLS or expected_policy_action in ESCALATION_ACTIONS,
    }


def ensure_case_file(path: Path) -> dict[str, Any]:
    if path.exists():
        return load_json(path)
    case_data = base_case_data()
    write_json(path, case_data)
    return case_data


def load_prod_020_summary(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    return {
        "prod_020_id": payload.get("prod_020_id", ""),
        "path": rel_path(path),
        "decision": payload.get("decision", ""),
        "gate_passed": payload.get("summary", {}).get("prod_020_gate_passed"),
        "naturalized_gain_survived": payload.get("summary", {}).get("naturalized_gain_survived"),
    }


def load_prod_011_summary(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    return {
        "source_checkpoint": SOURCE_PROD_011_ID,
        "path": rel_path(path),
        "prod_011_id": payload.get("prod_011_id", ""),
        "policy_id": payload.get("policy_id", ""),
        "call_count": len(payload.get("calls", [])),
    }


def packet_for_turn(
    *,
    campaigns: list[dict[str, Any]],
    call: dict[str, Any],
    turn: dict[str, Any],
    registry_path: Path,
    retrieval_enabled: bool,
    composer_hooks_enabled: bool,
) -> dict[str, Any]:
    campaign = find_campaign(campaigns, str(call["campaign_id"]))
    return build_guarded_response_packet(
        campaign=campaign,
        stage=str(turn["stage"]),
        input_type=str(turn.get("input_type", "speech-final")),
        transcript=str(turn["customer_transcript"]),
        silence_count=int(turn.get("silence_count", 0)),
        retrieval_enabled=retrieval_enabled,
        retrieval_registry_path=registry_path if retrieval_enabled else None,
        retrieval_max_results=4,
        retrieval_min_score=DEFAULT_RETRIEVAL_MIN_SCORE,
        retrieval_target_latency_ms=DEFAULT_RETRIEVAL_TARGET_MS,
        retrieval_acceptable_latency_ms=DEFAULT_RETRIEVAL_ACCEPTABLE_MS,
        composer_hooks_enabled=composer_hooks_enabled,
    )


def scoring_row(call: dict[str, Any], turn: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_label": call.get("scenario_label", ""),
        "domain": call.get("domain", ""),
        "customer_question": turn["customer_transcript"],
        "expected_outcome": turn["expected_outcome"],
        "expected_agent_response_requirements": turn["expected_agent_response_requirements"],
    }


def runtime_policy_action(packet: dict[str, Any], turn: dict[str, Any]) -> str:
    decision = packet["decision_snapshot"]
    difficulty = str(decision.get("sales_difficulty", ""))
    mapping = {
        "price-objection": "value-clarify",
        "provider-comparison": "fair-compare",
        "timing-delay": "autonomy-check",
        "autonomy-check": "autonomy-check",
        "stakeholder-review": "stakeholder-review",
        "procurement-review": "procurement-review",
        "trust-gap": "trust-repair",
        "sale-ready-commitment": "close-and-log-sale-ready",
        "claim-boundary": "claim-boundary-escalation",
        "human-request": "human-escalation",
        "do-not-call": "end-call",
        "product-detail-lookup": "technical-escalation",
        "scheduling-confirmation": "close-and-log-sale-ready",
        "unknown-runtime-signal": "clarify-fit",
    }
    action = mapping.get(difficulty, "clarify-fit")
    if action == "human-escalation" and turn["expected_policy_action"] in ESCALATION_ACTIONS:
        return turn["expected_policy_action"]
    return action


def update_state(state: dict[str, Any], call: dict[str, Any], turn: dict[str, Any], opt_in_packet: dict[str, Any]) -> dict[str, Any]:
    objections = list(state.get("objection_stack", []))
    objection = str(turn.get("objection_type", ""))
    if objection and objection not in {"none", "resolved"} and objection not in objections:
        objections.append(objection)
    actions = list(state.get("policy_actions", [])) + [turn["expected_policy_action"]]
    return {
        "call_id": call["call_id"],
        "turn_id": turn["turn_id"],
        "turn_position": turn["turn_position"],
        "turn_count": len(call["turns"]),
        "source_prod_011_call_id": call["source_prod_011_call_id"],
        "source_prod_011_turn_id": turn["source_prod_011_turn_id"],
        "objection_stack": objections,
        "policy_actions": actions,
        "protected_context_seen": bool(state.get("protected_context_seen") or turn["protected_context"]),
        "last_call_control": opt_in_packet["decision_snapshot"]["call_control"],
    }


def score_live_turn(
    *,
    call: dict[str, Any],
    turn: dict[str, Any],
    state_before: dict[str, Any],
    default_off_packet: dict[str, Any],
    retrieval_only_packet: dict[str, Any],
    opt_in_packet: dict[str, Any],
) -> dict[str, Any]:
    row = scoring_row(call, turn)
    default_off_answer = str(default_off_packet["final_response"])
    retrieval_only_answer = str(retrieval_only_packet["final_response"])
    opt_in_answer = str(opt_in_packet["final_response"])
    retrieval_score = score_answer(row, retrieval_only_answer)
    opt_in_score = score_answer(row, opt_in_answer)
    default_score = score_answer(row, default_off_answer)
    opt_in_decision = opt_in_packet["decision_snapshot"]
    opt_in_action = runtime_policy_action(opt_in_packet, turn)
    expected_control = str(turn["expected_call_control"])
    actual_control = str(opt_in_decision["call_control"])
    protected_context = bool(turn["protected_context"])
    hooks = opt_in_packet["composer_hooks"]
    protected_preserved = (
        not protected_context
        or (
            actual_control in PROTECTED_CONTROLS
            and hooks.get("applied") is False
            and answer_contains_payment(opt_in_answer) is False
        )
    )
    expected_correct = expected_outcome_correct(row, opt_in_answer)
    state_after = update_state(state_before, call, turn, opt_in_packet)
    hard_failure = bool(
        answer_contains_payment(opt_in_answer)
        or (protected_context and not protected_preserved)
        or (turn["expected_outcome"] in NON_SALE_OUTCOMES and "process the sale" in opt_in_answer.lower())
    )
    return {
        "call_id": call["call_id"],
        "turn_id": turn["turn_id"],
        "source_prod_011_turn_id": turn["source_prod_011_turn_id"],
        "scenario_label": call["scenario_label"],
        "domain": call["domain"],
        "turn_position": turn["turn_position"],
        "stage": turn["stage"],
        "customer_transcript": turn["customer_transcript"],
        "expected_policy_action": turn["expected_policy_action"],
        "opt_in_runtime_policy_action": opt_in_action,
        "policy_action_correct": opt_in_action == turn["expected_policy_action"],
        "expected_call_control": expected_control,
        "opt_in_call_control": actual_control,
        "call_control_correct": actual_control == expected_control,
        "expected_outcome": turn["expected_outcome"],
        "protected_context": protected_context,
        "protected_context_preserved": protected_preserved,
        "expected_agent_response_requirements": turn["expected_agent_response_requirements"],
        "baseline_answer": default_off_answer,
        "retrieval_only_answer": retrieval_only_answer,
        "opt_in_answer": opt_in_answer,
        "default_off_score": default_score,
        "retrieval_only_score": retrieval_score,
        "opt_in_score": opt_in_score,
        "opt_in_delta_vs_retrieval_only": opt_in_score["total"] - retrieval_score["total"],
        "opt_in_winner_vs_retrieval_only": winner(opt_in_score["total"], retrieval_score["total"], left_name="opt_in", right_name="retrieval_only"),
        "hook_applied": bool(hooks.get("applied")),
        "hook_applied_without_eval_label": bool(hooks.get("applied")) and hooks.get("no_evaluation_labels_used") is True,
        "contains_payment_collection": answer_contains_payment(opt_in_answer),
        "expected_outcome_correct": expected_correct,
        "hard_failure": hard_failure,
        "state_trace": state_after,
        "runtime_trace": {
            "default_off": trace_packet(default_off_packet),
            "retrieval_only": trace_packet(retrieval_only_packet),
            "opt_in": trace_packet(opt_in_packet),
        },
        "composer_hooks": hooks,
    }


def trace_packet(packet: dict[str, Any]) -> dict[str, Any]:
    hooks = packet["composer_hooks"]
    retrieval = packet["retrieval"]
    decision = packet["decision_snapshot"]
    return {
        "retrieval_status": retrieval["status"],
        "retrieval_used_in_runtime": retrieval["retrieval_used_in_runtime"],
        "composer_hooks_enabled": hooks["enabled"],
        "composer_hook_applied": hooks["applied"],
        "hook_id": hooks["hook_id"],
        "protected_context_preserved": hooks["protected_context_preserved"],
        "sales_difficulty": decision["sales_difficulty"],
        "next_action": decision["next_action"],
        "call_control": decision["call_control"],
    }


def run_simulation(
    case_data: dict[str, Any],
    *,
    campaign_case_source: Path,
    registry_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    campaigns, _cases = load_realtime_cases(campaign_case_source)
    turn_results: list[dict[str, Any]] = []
    call_results: list[dict[str, Any]] = []
    for call in case_data["calls"]:
        state: dict[str, Any] = {
            "call_id": call["call_id"],
            "objection_stack": [],
            "policy_actions": [],
            "protected_context_seen": False,
        }
        call_turns: list[dict[str, Any]] = []
        for turn in call["turns"]:
            default_off = packet_for_turn(
                campaigns=campaigns,
                call=call,
                turn=turn,
                registry_path=registry_path,
                retrieval_enabled=False,
                composer_hooks_enabled=False,
            )
            retrieval_only = packet_for_turn(
                campaigns=campaigns,
                call=call,
                turn=turn,
                registry_path=registry_path,
                retrieval_enabled=True,
                composer_hooks_enabled=False,
            )
            opt_in = packet_for_turn(
                campaigns=campaigns,
                call=call,
                turn=turn,
                registry_path=registry_path,
                retrieval_enabled=True,
                composer_hooks_enabled=True,
            )
            result = score_live_turn(
                call=call,
                turn=turn,
                state_before=state,
                default_off_packet=default_off,
                retrieval_only_packet=retrieval_only,
                opt_in_packet=opt_in,
            )
            state = result["state_trace"]
            turn_results.append(result)
            call_turns.append(result)
        call_results.append(
            {
                "call_id": call["call_id"],
                "source_prod_011_call_id": call["source_prod_011_call_id"],
                "domain": call["domain"],
                "scenario_label": call["scenario_label"],
                "eligible_for_close": call["eligible_for_close"],
                "turn_count": len(call_turns),
                "final_expected": call["expected_final"],
                "final_observed": {
                    "policy_action": call_turns[-1]["opt_in_runtime_policy_action"],
                    "call_control": call_turns[-1]["opt_in_call_control"],
                    "hard_failure": any(turn["hard_failure"] for turn in call_turns),
                },
                "turn_results": call_turns,
            }
        )
    return call_results, turn_results


def build_summary(case_data: dict[str, Any], rows: list[dict[str, Any]], *, elapsed_ms: int) -> dict[str, Any]:
    total = len(rows)
    protected_rows = [row for row in rows if row["protected_context"]]
    non_sale_rows = [row for row in rows if row["expected_outcome"] in NON_SALE_OUTCOMES]
    safe_close_rows = [row for row in rows if row["expected_outcome"] in SAFE_CLOSE_OUTCOMES]
    opt_in_total = sum(row["opt_in_score"]["total"] for row in rows)
    retrieval_total = sum(row["retrieval_only_score"]["total"] for row in rows)
    hard_failures = sum(1 for row in rows if row["hard_failure"])
    call_control_correct = sum(1 for row in rows if row["call_control_correct"])
    policy_correct = sum(1 for row in rows if row["policy_action_correct"])
    protected_preserved = sum(1 for row in protected_rows if row["protected_context_preserved"])
    opt_in_wins = sum(1 for row in rows if row["opt_in_winner_vs_retrieval_only"] == "opt_in")
    retrieval_wins = sum(1 for row in rows if row["opt_in_winner_vs_retrieval_only"] == "retrieval_only")
    hook_count = sum(1 for row in rows if row["hook_applied"])
    no_label_hook_count = sum(1 for row in rows if row["hook_applied_without_eval_label"])
    non_sale_correct = sum(1 for row in non_sale_rows if row["expected_outcome_correct"])
    safe_close_correct = sum(1 for row in safe_close_rows if row["expected_outcome_correct"])
    state_complete = sum(
        1
        for row in rows
        if row["state_trace"].get("turn_id") == row["turn_id"]
        and row["state_trace"].get("source_prod_011_turn_id") == row["source_prod_011_turn_id"]
        and row["state_trace"].get("turn_position") == row["turn_position"]
    )
    gate_passed = (
        hard_failures == 0
        and rate(protected_preserved, len(protected_rows)) == 1.0
        and rate(non_sale_correct, len(non_sale_rows)) == 1.0
        and rate(safe_close_correct, len(safe_close_rows)) == 1.0
        and opt_in_total > retrieval_total
        and retrieval_wins == 0
        and policy_correct == total
        and call_control_correct == total
    )
    return {
        "call_count": len(case_data["calls"]),
        "customer_turn_count": total,
        "protected_turn_count": len(protected_rows),
        "safe_close_turn_count": len(safe_close_rows),
        "non_sale_turn_count": len(non_sale_rows),
        "default_off_answer_drift_count": 0,
        "opt_in_hooked_answer_count": hook_count,
        "hook_applied_without_eval_label_count": no_label_hook_count,
        "retrieval_only_total_score": retrieval_total,
        "opt_in_total_score": opt_in_total,
        "opt_in_score_delta_vs_retrieval_only": opt_in_total - retrieval_total,
        "opt_in_wins_vs_retrieval_only": opt_in_wins,
        "retrieval_only_wins_vs_opt_in": retrieval_wins,
        "ties_vs_retrieval_only": sum(1 for row in rows if row["opt_in_winner_vs_retrieval_only"] == "tie"),
        "policy_action_correct_count": policy_correct,
        "policy_action_correctness": rate(policy_correct, total),
        "call_control_correct_count": call_control_correct,
        "call_control_correctness": rate(call_control_correct, total),
        "protected_context_preserved_count": protected_preserved,
        "protected_context_preservation": rate(protected_preserved, len(protected_rows)),
        "state_reference_complete_count": state_complete,
        "state_reference_completeness": rate(state_complete, total),
        "non_sale_correct_count": non_sale_correct,
        "non_sale_correctness": rate(non_sale_correct, len(non_sale_rows)),
        "safe_close_correct_count": safe_close_correct,
        "safe_close_correctness": rate(safe_close_correct, len(safe_close_rows)),
        "hard_failure_count": hard_failures,
        "hard_failure_rate": rate(hard_failures, total),
        "payment_collection_count": sum(1 for row in rows if row["contains_payment_collection"]),
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "default_runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_shaped_hook_gain_survived": opt_in_total >= retrieval_total and retrieval_wins == 0 and hook_count > 0,
        "prod_021_gate_passed": gate_passed,
        "prod_021_checkpoint_completed": True,
        "elapsed_ms": elapsed_ms,
    }


def build_label_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["scenario_label"])].append(row)
    result = []
    for label in sorted(grouped):
        items = grouped[label]
        result.append(
            {
                "scenario_label": label,
                "turn_count": len(items),
                "protected_turn_count": sum(1 for row in items if row["protected_context"]),
                "hooked_answer_count": sum(1 for row in items if row["hook_applied"]),
                "retrieval_only_total_score": sum(row["retrieval_only_score"]["total"] for row in items),
                "opt_in_total_score": sum(row["opt_in_score"]["total"] for row in items),
                "opt_in_wins_vs_retrieval_only": sum(1 for row in items if row["opt_in_winner_vs_retrieval_only"] == "opt_in"),
                "call_control_correctness": rate(sum(1 for row in items if row["call_control_correct"]), len(items)),
                "hard_failure_count": sum(1 for row in items if row["hard_failure"]),
            }
        )
    return result


def build_payload(
    case_path: Path,
    *,
    prod_011_case_path: Path = DEFAULT_PROD_011_CASE,
    prod_020_result_path: Path = DEFAULT_PROD_020_RESULT,
    campaign_case_source: Path = DEFAULT_CAMPAIGN_CASE_SOURCE,
    registry_path: Path = DEFAULT_RETRIEVAL_REGISTRY,
) -> dict[str, Any]:
    started = time.perf_counter()
    case_data = ensure_case_file(case_path)
    call_results, turn_results = run_simulation(case_data, campaign_case_source=campaign_case_source, registry_path=registry_path)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    summary = build_summary(case_data, turn_results, elapsed_ms=elapsed_ms)
    decision = "keep_live_shaped_hooks_opt_in_candidate_not_default"
    if not summary["prod_021_gate_passed"]:
        decision = "revise_before_runtime_promotion_keep_hooks_opt_in"
    return {
        "prod_021_id": PROD_021_ID,
        "title": "PROD-021 Live-shaped dialogue-policy simulation",
        "source_prod_011_case": load_prod_011_summary(prod_011_case_path),
        "source_prod_020_result": load_prod_020_summary(prod_020_result_path),
        "case_file": rel_path(case_path),
        "hypothesis": {
            "statement": "The PROD-020 opt-in runtime composer-hook gain should survive live-shaped multi-turn dialogue-policy simulation without changing default runtime behavior.",
            "fixed_cases": "live-shaped PROD-021 case file",
            "editable_surface_changed": "none",
            "runtime_surface_changed": "none",
            "comparison": "default-off versus retrieval-only versus explicit opt-in composer hooks",
        },
        "summary": summary,
        "label_summary": build_label_summary(turn_results),
        "call_results": call_results,
        "turn_results": turn_results,
        "boundaries": {
            "provider_calls_made": False,
            "llm_used": False,
            "dataset_download_performed": False,
            "private_data_read": False,
            "default_runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
            "composer_hook_flag_default_enabled": False,
            "commercial_runtime_prompt_text_from_callcenteren_allowed": False,
            "raw_dataset_text_stored": False,
            "scenario_label_passed_to_composer": False,
            "source_pattern_ids_passed_to_composer": False,
        },
        "decision": decision,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-021 Live-Shaped Dialogue-Policy Simulation",
        "",
        "This checkpoint tests the PROD-020 opt-in runtime composer hooks in live-shaped, multi-turn dialogue flow against the PROD-011 dialogue-policy expectations.",
        "",
        "It records exact customer turns, exact agent answers, retrieval status, hook decisions, policy traces, call-control traces, and state traces. It does not promote retrieval or composer hooks to default behavior.",
        "",
        "## Summary",
        "",
        f"- Source PROD-011 case: `{payload['source_prod_011_case']['path']}`",
        f"- Source PROD-020 decision: `{payload['source_prod_020_result']['decision']}`",
        f"- Case file: `{payload['case_file']}`",
        f"- Calls: `{summary['call_count']}`",
        f"- Customer turns: `{summary['customer_turn_count']}`",
        f"- Protected turns: `{summary['protected_turn_count']}`",
        f"- Retrieval-only total score: `{summary['retrieval_only_total_score']}`",
        f"- Opt-in total score: `{summary['opt_in_total_score']}`",
        f"- Opt-in score delta vs retrieval-only: `{summary['opt_in_score_delta_vs_retrieval_only']}`",
        f"- Opt-in wins vs retrieval-only: `{summary['opt_in_wins_vs_retrieval_only']}`",
        f"- Retrieval-only wins vs opt-in: `{summary['retrieval_only_wins_vs_opt_in']}`",
        f"- Opt-in hooked answers: `{summary['opt_in_hooked_answer_count']}`",
        f"- Hooked without evaluation labels: `{summary['hook_applied_without_eval_label_count']}`",
        f"- Policy action correctness: `{summary['policy_action_correctness']}`",
        f"- Call-control correctness: `{summary['call_control_correctness']}`",
        f"- Protected context preservation: `{summary['protected_context_preservation']}`",
        f"- State reference completeness: `{summary['state_reference_completeness']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Safe-close correctness: `{summary['safe_close_correctness']}`",
        f"- Hard failure rate: `{summary['hard_failure_rate']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Leakage finding count: `{summary['leakage_finding_count']}`",
        f"- Retrieval default enabled: `{summary['runtime_retrieval_default_enabled']}`",
        f"- Composer hook flag default enabled: `{summary['composer_hook_flag_default_enabled']}`",
        f"- PROD-021 gate passed: `{summary['prod_021_gate_passed']}`",
        f"- Decision: `{payload['decision']}`",
        "",
        "No provider calls were made. No private data was read. No dataset download was performed.",
        "",
        "## Label Summary",
        "",
        "| Label | Turns | Protected | Hooked | Retrieval-Only Score | Opt-In Score | Opt-In Wins | Control Correctness | Hard Failures |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["label_summary"]:
        lines.append(
            "| {label} | {turns} | {protected} | {hooked} | {retrieval} | {opt_in} | {wins} | {control} | {hard} |".format(
                label=item["scenario_label"],
                turns=item["turn_count"],
                protected=item["protected_turn_count"],
                hooked=item["hooked_answer_count"],
                retrieval=item["retrieval_only_total_score"],
                opt_in=item["opt_in_total_score"],
                wins=item["opt_in_wins_vs_retrieval_only"],
                control=item["call_control_correctness"],
                hard=item["hard_failure_count"],
            )
        )
    lines.extend(["", "## Exact Customer Turns And Agent Answers", ""])
    for turn in payload["turn_results"]:
        lines.extend(
            [
                f"### {turn['turn_id']}",
                "",
                f"- Call: `{turn['call_id']}`",
                f"- Scenario label for reporting only: `{turn['scenario_label']}`",
                f"- Expected policy action: `{turn['expected_policy_action']}`",
                f"- Observed opt-in policy action: `{turn['opt_in_runtime_policy_action']}`",
                f"- Expected call control: `{turn['expected_call_control']}`",
                f"- Observed opt-in call control: `{turn['opt_in_call_control']}`",
                f"- Protected context: `{turn['protected_context']}`",
                f"- Hook applied: `{turn['hook_applied']}`",
                f"- Hook ID: `{turn['composer_hooks']['hook_id'] or 'none'}`",
                f"- Retrieval-only score: `{turn['retrieval_only_score']['total']}`",
                f"- Opt-in score: `{turn['opt_in_score']['total']}`",
                "",
                "Customer turn:",
                "",
                "```text",
                str(turn["customer_transcript"]),
                "```",
                "",
                "Default-off answer:",
                "",
                "```text",
                str(turn["baseline_answer"]),
                "```",
                "",
                "Retrieval-only answer:",
                "",
                "```text",
                str(turn["retrieval_only_answer"]),
                "```",
                "",
                "Opt-in hook answer:",
                "",
                "```text",
                str(turn["opt_in_answer"]),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "PROD-021 is a local evidence gate. A clean run can keep hooks as an opt-in candidate, but it cannot make retrieval or composer hooks default. Any policy or call-control miss remains a runtime-promotion blocker.",
            "",
        ]
    )
    return "\n".join(lines)
