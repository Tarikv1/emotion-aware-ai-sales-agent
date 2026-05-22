#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter as adapter  # noqa: E402
from runtime.core import dialogue_manager  # noqa: E402
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet  # noqa: E402
from runtime.speech.asr_quality_gate import evaluate_asr_quality  # noqa: E402
from runtime.voice.runtime_tts_delivery import attach_runtime_tts_delivery  # noqa: E402
from runtime.voice.runtime_voice_delivery import attach_runtime_voice_delivery  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-RUNTIME-SMOKE-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
FORBIDDEN_BRAND_TERMS = ["RouteSignal", "Northstar", "Starter", "Growth", "$29", "$59"]
FORBIDDEN_ROUTE_PHRASES = ["inbound demo", "demo follow-up", "missed callbacks", "manual tracking", "messy handoffs"]
ROUTESIGNAL_GAP_IDS = {"callbacks", "manual_tracking", "handoffs"}
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def gap(
    gap_id: str,
    label: str,
    *,
    review_focus: str,
    customer_language: list[str],
    positive: list[str],
    negative: list[str],
    next_gap_candidates: list[str],
    universal: list[str] | None = None,
    qualifications: list[str] | None = None,
    value_bridge: str | None = None,
) -> dict[str, Any]:
    return {
        "campaign_gap_id": gap_id,
        "label": label,
        "universal_pain_dimensions": universal or ["unclear_next_step"],
        "qualification_dimensions": qualifications or ["need_or_pain", "fit"],
        "definition": f"Determine whether {label} is a real current constraint.",
        "causal_story": f"If {label} is unresolved, a qualified human should review it before a next step is promised.",
        "customer_language": customer_language,
        "evidence_positive": positive,
        "evidence_negative": negative,
        "diagnostic_questions": [f"Is {label} creating issues today?"],
        "value_bridge": value_bridge or f"A human review should verify {review_focus} before promising fit.",
        "review_focus": review_focus,
        "next_gap_candidates": next_gap_candidates,
    }


def campaign(
    *,
    campaign_id: str,
    client_name: str,
    offer: str,
    vertical_id: str,
    human_owner: str,
    appointment_target: str,
    diagnostic_gaps: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    order = list(diagnostic_gaps)
    return {
        "campaign_id": campaign_id,
        "client_name": client_name,
        "product_name": offer,
        "product_or_offer_name": offer,
        "vertical_id": vertical_id,
        "language": "en",
        "objective": "appointment_setting",
        "human_followup_owner": human_owner,
        "human_handoff_role": human_owner,
        "appointment_target": appointment_target,
        "specialist_handoff_route": human_owner,
        "target_account_context": {"buyer_role": "the right person for this review"},
        "caller_identity": {
            "representative_name": "Maya",
            "product_relationship": f"calling about {offer}",
        },
        "diagnostic_gaps": diagnostic_gaps,
        "core_diagnostic_gaps": order[:3],
        "gap_order": order,
        "campaign_playbook_id": f"{campaign_id}-playbook",
        "allowed_claims": ["general information and scheduling only"],
        "forbidden_claims": ["unsupported guarantee", "unverified outcome promise"],
        "regulated_advice_boundary_text": "Specific guarantees require human review of verified details.",
    }


def synthetic_campaigns() -> dict[str, dict[str, Any]]:
    return {
        "insurance": campaign(
            campaign_id="synthetic-insurance-runtime-001",
            client_name="Synthetic Insurance Agency",
            offer="Policy Review Call",
            vertical_id="insurance",
            human_owner="licensed insurance specialist",
            appointment_target="licensed coverage review",
            diagnostic_gaps={
                "coverage_fit": gap(
                    "coverage_fit",
                    "coverage fit",
                    review_focus="coverage fit against policy details",
                    customer_language=["coverage fit", "coverage", "covered"],
                    positive=["coverage fit is a problem", "coverage is the issue"],
                    negative=["coverage fit is handled", "coverage is fine"],
                    next_gap_candidates=["premium_or_budget", "renewal_or_timing"],
                    universal=["fit", "risk_or_compliance"],
                    qualifications=["fit", "compliance_or_risk_constraints"],
                ),
                "premium_or_budget": gap(
                    "premium_or_budget",
                    "premium or budget",
                    review_focus="premium and budget pressure",
                    customer_language=["premium", "budget"],
                    positive=["premium is a problem", "premium is the problem", "budget is a problem"],
                    negative=["premium is handled", "premium is fine", "budget is fine"],
                    next_gap_candidates=["coverage_fit", "renewal_or_timing"],
                    universal=["budget_pressure"],
                    qualifications=["budget_or_price_sensitivity"],
                ),
                "renewal_or_timing": gap(
                    "renewal_or_timing",
                    "renewal or timing",
                    review_focus="renewal timing and next-step urgency",
                    customer_language=["renewal", "timing"],
                    positive=["renewal timing is an issue", "timing is a problem"],
                    negative=["renewal timing is handled", "timing is fine"],
                    next_gap_candidates=["coverage_fit", "premium_or_budget"],
                    universal=["timing"],
                    qualifications=["timing"],
                ),
            },
        ),
        "telecom": campaign(
            campaign_id="synthetic-telecom-runtime-001",
            client_name="Synthetic Telecom Provider",
            offer="Plan Review Call",
            vertical_id="telecom",
            human_owner="telecom plan specialist",
            appointment_target="plan and coverage review",
            diagnostic_gaps={
                "coverage_or_availability": gap(
                    "coverage_or_availability",
                    "coverage or availability",
                    review_focus="coverage and availability constraints",
                    customer_language=["coverage", "availability"],
                    positive=["coverage is the issue", "coverage is a problem", "availability is the issue"],
                    negative=["coverage is fine", "availability is fine"],
                    next_gap_candidates=["plan_fit", "contract_or_switching"],
                    universal=["fit", "risk_or_compliance"],
                    qualifications=["fit", "compliance_or_risk_constraints"],
                ),
                "plan_fit": gap(
                    "plan_fit",
                    "plan fit",
                    review_focus="plan fit against actual usage",
                    customer_language=["plan fit", "plan"],
                    positive=["plan fit is a problem", "plan is the issue"],
                    negative=["plan fit is fine", "plan is fine"],
                    next_gap_candidates=["coverage_or_availability", "contract_or_switching"],
                    universal=["fit"],
                    qualifications=["fit"],
                ),
                "contract_or_switching": gap(
                    "contract_or_switching",
                    "contract or switching",
                    review_focus="contract timing and switching friction",
                    customer_language=["contract", "switching"],
                    positive=["contract switching is an issue", "switching is a problem"],
                    negative=["contract switching is handled", "switching is fine"],
                    next_gap_candidates=["coverage_or_availability", "plan_fit"],
                    universal=["timing"],
                    qualifications=["timing", "current_solution_or_status_quo"],
                ),
            },
        ),
        "home_services": campaign(
            campaign_id="synthetic-home-services-runtime-001",
            client_name="Synthetic Home Services",
            offer="Service Estimate Call",
            vertical_id="home_services",
            human_owner="service advisor",
            appointment_target="service estimate review",
            diagnostic_gaps={
                "service_need": gap(
                    "service_need",
                    "service need",
                    review_focus="service need and fit",
                    customer_language=["service need", "service"],
                    positive=["service need is a problem", "service is needed"],
                    negative=["service need is handled", "service need is fine"],
                    next_gap_candidates=["scheduling_urgency", "estimate_or_property_details"],
                    universal=["need"],
                    qualifications=["need_or_pain", "fit"],
                ),
                "scheduling_urgency": gap(
                    "scheduling_urgency",
                    "scheduling urgency",
                    review_focus="scheduling urgency and access timing",
                    customer_language=["scheduling", "schedule", "urgency"],
                    positive=["scheduling is a problem", "urgency is the issue"],
                    negative=["scheduling is fine", "scheduling is handled"],
                    next_gap_candidates=["service_need", "estimate_or_property_details"],
                    universal=["timing"],
                    qualifications=["timing"],
                ),
                "estimate_or_property_details": gap(
                    "estimate_or_property_details",
                    "estimate or property details",
                    review_focus="estimate assumptions and property details",
                    customer_language=["estimate", "property details", "price"],
                    positive=["estimate is unclear", "the estimate is unclear", "property details are unclear"],
                    negative=["estimate is handled", "estimate is fine"],
                    next_gap_candidates=["service_need", "scheduling_urgency"],
                    universal=["risk_or_compliance"],
                    qualifications=["fit", "compliance_or_risk_constraints"],
                ),
            },
        ),
        "b2b_saas": campaign(
            campaign_id="synthetic-b2b-saas-runtime-001",
            client_name="Synthetic SaaS Operations",
            offer="Operations Workflow Review",
            vertical_id="b2b_saas",
            human_owner="implementation specialist",
            appointment_target="operations fit review",
            diagnostic_gaps={
                "manual_work": gap(
                    "manual_work",
                    "manual work",
                    review_focus="manual work in the current workflow",
                    customer_language=["manual work", "manual"],
                    positive=["manual work is a problem", "manual work is the issue"],
                    negative=["manual work is handled", "manual work is fine"],
                    next_gap_candidates=["integration_risk", "visibility_gap"],
                    universal=["manual_work"],
                    qualifications=["current_solution_or_status_quo", "need_or_pain"],
                ),
                "integration_risk": gap(
                    "integration_risk",
                    "integration risk",
                    review_focus="integration and security review needs",
                    customer_language=["integration", "integrate", "security"],
                    positive=["integration is a problem", "security is the issue"],
                    negative=["integration is handled", "security is fine"],
                    next_gap_candidates=["manual_work", "visibility_gap"],
                    universal=["risk_or_compliance"],
                    qualifications=["compliance_or_risk_constraints", "fit"],
                ),
                "visibility_gap": gap(
                    "visibility_gap",
                    "visibility gap",
                    review_focus="visibility into workflow status",
                    customer_language=["visibility", "status visibility"],
                    positive=["visibility is the problem", "visibility is a problem"],
                    negative=["visibility is handled", "visibility is fine"],
                    next_gap_candidates=["manual_work", "integration_risk"],
                    universal=["visibility_gap"],
                    qualifications=["need_or_pain"],
                ),
            },
        ),
    }


def elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def build_synthetic_turn_packet(
    *,
    transcript: str,
    campaign_config: dict[str, Any],
    session_state: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    start = time.perf_counter()
    input_type = "agent-open" if transcript == "__agent_open__" else "speech-final"
    quality_gate = evaluate_asr_quality(transcript, 0.94)
    dialogue_action = dialogue_manager.plan_dialogue_action(
        transcript=transcript,
        session_state=session_state,
        campaign=campaign_config,
        quality_gate=quality_gate,
        dialogue_reasoning={"validator": CHECKPOINT_ID, "provider_calls_made": False, "local_llm_calls_made": False},
    )

    def guarded_packet_for_action(action: dict[str, Any]) -> dict[str, Any]:
        return build_guarded_response_packet(
            campaign=campaign_config,
            stage="relevance-check",
            input_type=input_type,
            transcript=transcript,
            silence_count=0,
            candidate_response_override=dialogue_manager.candidate_response(action),
            retrieval_enabled=False,
            composer_hooks_enabled=False,
            align_decision_trace=True,
        )

    guarded = guarded_packet_for_action(dialogue_action)
    updated_action = dialogue_manager.apply_anti_loop_if_needed(
        action=dialogue_action,
        transcript=transcript,
        session_state=session_state,
        campaign=campaign_config,
        generated_response=str(guarded.get("final_response") or ""),
    )
    if updated_action is not dialogue_action:
        dialogue_action = updated_action
        guarded = guarded_packet_for_action(dialogue_action)
    updated_action = dialogue_manager.apply_duplicate_repair_if_needed(
        action=dialogue_action,
        transcript=transcript,
        session_state=session_state,
        campaign=campaign_config,
        generated_response=str(guarded.get("final_response") or ""),
    )
    if updated_action is not dialogue_action:
        dialogue_action = updated_action
        guarded = guarded_packet_for_action(dialogue_action)

    continuity = dialogue_manager.continuity(dialogue_action)
    conversation_memory = dialogue_manager.build_conversation_memory(
        action=dialogue_action,
        session_state=session_state,
        transcript=transcript,
        final_response=str(guarded.get("final_response") or ""),
        campaign=campaign_config,
    )
    updated_action, stability_guard = dialogue_manager.apply_stability_guard_if_needed(
        action=dialogue_action,
        transcript=transcript,
        session_state=session_state,
        campaign=campaign_config,
        generated_response=str(guarded.get("final_response") or ""),
        conversation_memory=conversation_memory,
    )
    if updated_action is not dialogue_action:
        dialogue_action = updated_action
        guarded = guarded_packet_for_action(dialogue_action)
        continuity = dialogue_manager.continuity(dialogue_action)
        conversation_memory = dialogue_manager.build_conversation_memory(
            action=dialogue_action,
            session_state=session_state,
            transcript=transcript,
            final_response=str(guarded.get("final_response") or ""),
            campaign=campaign_config,
        )

    guarded = dialogue_manager.apply_decision_override(guarded, dialogue_action)
    voice_packet = attach_runtime_voice_delivery(guarded, campaign_config, provider_key="elevenlabs")
    tts_packet = attach_runtime_tts_delivery(
        voice_packet,
        provider_key="elevenlabs",
        live=False,
        force_key_missing=True,
        audio_dir=TMP_DIR / "audio",
        timeout_seconds=8.0,
        command_name="scripts/validate_generic_campaign_runtime_smoke_001.py",
        voice_consistency_mode="live-demo-stable",
    )
    dialogue_manager_trace = dialogue_manager.finalize_trace(
        action=dialogue_action,
        packet=tts_packet,
        conversation_memory=conversation_memory,
        stability_guard=stability_guard,
    )
    decision = tts_packet.get("decision_snapshot") or {}
    summary = {
        "final_response": tts_packet.get("final_response"),
        "candidate_response": tts_packet.get("candidate_response"),
        "call_control": decision.get("call_control"),
        "sales_difficulty": decision.get("sales_difficulty"),
        "next_action": decision.get("next_action"),
        "tts_input_text": (tts_packet.get("tts_delivery") or {}).get("tts_input_text"),
        "tts_provider_calls_made": bool((tts_packet.get("tts_delivery") or {}).get("provider_calls_made")),
    }
    playbook = adapter.resolve_campaign_playbook(campaign_config)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "mode": "synthetic-dry-run",
        "session_id": session_id,
        "session_turn_index": len(session_state.get("turns") or []) + 1,
        "campaign_id": campaign_config.get("campaign_id"),
        "campaign_playbook_id": playbook.get("campaign_playbook_id"),
        "stage": "relevance-check",
        "input_type": input_type,
        "transcript": transcript,
        "asr": {"quality_gate": quality_gate},
        "provider_agent_used": False,
        "durable_provider_agent_created": False,
        "voice_cloning_used": False,
        "runtime_behavior_changed": False,
        "opens_prod_102": False,
        "demo_session_continuity": continuity,
        "demo_conversation_memory": conversation_memory,
        "dialogue_manager": dialogue_manager_trace,
        "dialogue_pragmatics": dialogue_manager_trace.get("pragmatic_move") or {},
        "packet": tts_packet,
        "summary": summary,
        "latency": {"server_total_ms": elapsed_ms(start)},
    }


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity", {}),
            "conversation_memory": packet.get("demo_conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
        }
    )


def run_sequence(campaign_config: dict[str, Any], transcripts: list[str], label: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_synthetic_turn_packet(
            transcript=transcript,
            campaign_config=campaign_config,
            session_state=state,
            session_id=label,
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets, state


def packet_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return dict(manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {})


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or (packet.get("packet") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    return str(((packet.get("packet") or {}).get("tts_delivery") or {}).get("tts_input_text") or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = packet_frame(packet)
    tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
    voice = ((packet.get("packet") or {}).get("voice_delivery") or {})
    manager = packet.get("dialogue_manager") or {}
    return {
        "turn": packet.get("session_turn_index"),
        "transcript": packet.get("transcript"),
        "campaign_id": packet.get("campaign_id"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "playbook_id": frame.get("playbook_id"),
        "playbook_review_focus": frame.get("playbook_review_focus"),
        "outgoing_candidate_gaps": frame.get("outgoing_candidate_gaps"),
        "call_control": (packet.get("summary") or {}).get("call_control"),
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "send_info_state": (packet.get("demo_conversation_memory") or {}).get("send_info_state"),
        "handoff_target_state": (packet.get("demo_conversation_memory") or {}).get("handoff_target_state"),
        "regulated_cautions": (frame.get("playbook") or {}).get("regulated_cautions"),
        "provider_calls_made": bool(tts.get("provider_calls_made") or voice.get("provider_calls_made") or (packet.get("packet") or {}).get("api_calls_made")),
        "local_llm_calls_made": bool(manager.get("local_llm_calls_made") or (packet.get("packet") or {}).get("llm_used")),
        "sends_email": bool(((packet.get("demo_conversation_memory") or {}).get("lead_followup_state") or {}).get("safety", {}).get("sends_email")),
        "creates_calendar_event": bool(((packet.get("demo_conversation_memory") or {}).get("lead_followup_state") or {}).get("safety", {}).get("creates_calendar_event")),
        "writes_crm": bool(((packet.get("demo_conversation_memory") or {}).get("lead_followup_state") or {}).get("safety", {}).get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
    }


def assert_no_forbidden_text(failures: list[str], packet: dict[str, Any], label: str, *, route_phrases: bool = True) -> None:
    texts = {
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
    }
    terms = list(FORBIDDEN_BRAND_TERMS)
    if route_phrases:
        terms.extend(FORBIDDEN_ROUTE_PHRASES)
    for text_name, text in texts.items():
        lowered = text.lower()
        found = [term for term in terms if term.lower() in lowered]
        assert_condition(failures, not found, f"{label}: {text_name} leaked forbidden wording {found}: {text}")


def assert_packet_safety(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
    voice = ((packet.get("packet") or {}).get("voice_delivery") or {})
    assert_condition(failures, tts.get("generated_text_sent_to_provider") is False, f"{label}: TTS text must not be sent to provider: {tts}")
    assert_condition(failures, tts.get("audio_file_created") is False, f"{label}: dry-run TTS must not create audio: {tts}")
    assert_condition(failures, voice.get("customer_audio_uploaded") is False, f"{label}: voice path must not upload customer audio: {voice}")
    assert_condition(failures, voice.get("voice_cloning_used") is False, f"{label}: voice path must not clone voice: {voice}")


def assert_synthetic_playbook(failures: list[str], packet: dict[str, Any], campaign_config: dict[str, Any], label: str) -> None:
    playbook = adapter.resolve_campaign_playbook(campaign_config)
    frame = packet_frame(packet)
    expected_playbook_id = playbook.get("campaign_playbook_id")
    assert_condition(failures, expected_playbook_id != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: resolved playbook must be synthetic: {playbook}")
    assert_condition(failures, packet.get("campaign_playbook_id") == expected_playbook_id, f"{label}: packet playbook id mismatch: {snapshot(packet)}")
    assert_condition(failures, frame.get("playbook_id") == expected_playbook_id, f"{label}: semantic frame playbook id mismatch: {snapshot(packet)}")
    target_gap = frame.get("target_gap")
    campaign_gaps = set(playbook.get("diagnostic_gaps") or {})
    if target_gap:
        assert_condition(failures, target_gap in campaign_gaps, f"{label}: target_gap must be synthetic: {snapshot(packet)}")
        assert_condition(failures, target_gap not in ROUTESIGNAL_GAP_IDS, f"{label}: target_gap leaked RouteSignal gap: {snapshot(packet)}")
        expected_focus = (playbook.get("diagnostic_gaps") or {}).get(target_gap, {}).get("review_focus")
        assert_condition(failures, frame.get("playbook_review_focus") == expected_focus, f"{label}: review focus must come from campaign gap: {snapshot(packet)}")


def assert_common_packet(failures: list[str], packet: dict[str, Any], campaign_config: dict[str, Any], label: str, *, route_phrases: bool = True) -> None:
    assert_synthetic_playbook(failures, packet, campaign_config, label)
    assert_no_forbidden_text(failures, packet, label, route_phrases=route_phrases)
    assert_packet_safety(failures, packet, label)


def assert_semantic(failures: list[str], packet: dict[str, Any], expected_semantic: str, label: str, expected_gap: str | None = None) -> None:
    frame = packet_frame(packet)
    assert_condition(failures, frame.get("semantic") == expected_semantic, f"{label}: expected semantic {expected_semantic}, got {frame.get('semantic')}: {snapshot(packet)}")
    if expected_gap:
        assert_condition(failures, frame.get("target_gap") == expected_gap, f"{label}: expected target_gap {expected_gap}, got {frame.get('target_gap')}: {snapshot(packet)}")


def validate_agent_open(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any]) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__"], f"{label}-agent-open")
    packet = packets[-1]
    evidence["scenario_a_agent_open"] = snapshot(packet)
    assert_common_packet(failures, packet, campaign_config, f"{label}:agent_open")
    response = normalize(final_response(packet))
    assert_condition(failures, normalize(campaign_config["client_name"]) in response, f"{label}: opening must use client name: {snapshot(packet)}")
    assert_condition(failures, normalize(campaign_config["product_or_offer_name"]) in response, f"{label}: opening must use product/offer: {snapshot(packet)}")
    assert_condition(failures, (packet.get("summary") or {}).get("call_control") == "continue-call", f"{label}: opening call_control must continue-call: {snapshot(packet)}")


def validate_permission_ack(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any]) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__", "yeah sure"], f"{label}-permission")
    packet = packets[-1]
    playbook = adapter.resolve_campaign_playbook(campaign_config)
    core = list(playbook.get("core_diagnostic_gaps") or [])
    evidence["scenario_b_permission_acknowledgement"] = snapshot(packet)
    assert_common_packet(failures, packet, campaign_config, f"{label}:permission_ack")
    assert_semantic(failures, packet, "permission_acknowledgement", f"{label}:permission_ack")
    frame = packet_frame(packet)
    memory = packet.get("demo_conversation_memory") or {}
    assert_condition(failures, frame.get("outgoing_candidate_gaps") == core, f"{label}: frame outgoing gaps must be campaign core gaps: {snapshot(packet)}")
    assert_condition(failures, memory.get("outgoing_candidate_gaps") == core, f"{label}: memory outgoing gaps must be campaign core gaps: {snapshot(packet)}")
    lowered = normalize(final_response(packet))
    assert_condition(failures, not any(term in lowered for term in ["callbacks", "manual tracking", "handoffs"]), f"{label}: permission response asked RouteSignal gaps: {snapshot(packet)}")
    assert_condition(failures, any(normalize((playbook.get("diagnostic_gaps") or {})[gap]["label"]) in lowered for gap in core), f"{label}: permission response must ask synthetic gaps: {snapshot(packet)}")


def validate_first_gap_clear(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any], utterance: str, expected_gap: str) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__", "yeah sure", utterance], f"{label}-first-clear")
    packet = packets[-1]
    evidence["scenario_c_first_gap_clear"] = snapshot(packet)
    assert_common_packet(failures, packet, campaign_config, f"{label}:first_gap_clear")
    assert_semantic(failures, packet, "current_gap_clear", f"{label}:first_gap_clear", expected_gap)
    response = normalize(final_response(packet))
    assert_condition(
        failures,
        "or stop here" in response or "create issues" in response,
        f"{label}: clear response should ask remaining synthetic gaps: {snapshot(packet)}",
    )


def validate_pain_confirmed(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any], utterance: str, expected_gap: str) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__", "yeah sure", utterance], f"{label}-pain")
    packet = packets[-1]
    evidence["scenario_d_pain_confirmed"] = snapshot(packet)
    assert_common_packet(failures, packet, campaign_config, f"{label}:pain_confirmed")
    assert_semantic(failures, packet, "pain_confirmed", f"{label}:pain_confirmed", expected_gap)
    response = normalize(final_response(packet))
    assert_condition(
        failures,
        normalize(campaign_config["human_followup_owner"]) in response
        or normalize(campaign_config["appointment_target"]) in response,
        f"{label}: pain response must move to campaign human follow-up: {snapshot(packet)}",
    )
    assert_condition(failures, normalize(campaign_config["appointment_target"]) in response, f"{label}: pain response must use campaign appointment target: {snapshot(packet)}")
    assert_condition(failures, "goodbye" not in response and "sale" not in response and "buy now" not in response, f"{label}: pain response must not full-close: {snapshot(packet)}")


def validate_send_info(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any]) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__", "yeah sure", "send me details", "yes send it"], f"{label}-send-info")
    packet = packets[-1]
    evidence["scenario_e_send_info"] = [snapshot(item) for item in packets]
    assert_common_packet(failures, packet, campaign_config, f"{label}:send_info", route_phrases=False)
    memory = packet.get("demo_conversation_memory") or {}
    send_info = memory.get("send_info_state") or {}
    response = normalize(final_response(packet))
    assert_condition(failures, send_info.get("requested") is True, f"{label}: send_info_state must open: {snapshot(packet)}")
    assert_condition(failures, str(send_info.get("capture_status") or "") == "needs_email_or_callback_time", f"{label}: send_info should ask for contact path: {snapshot(packet)}")
    assert_condition(failures, "email" in response or "callback" in response, f"{label}: send_info response must ask email or callback path: {snapshot(packet)}")
    assert_condition(failures, "confirmed" not in response and "appointment" not in response, f"{label}: send_info must not fake appointment confirmation: {snapshot(packet)}")
    assert_no_forbidden_text(failures, packet, f"{label}:send_info")


def validate_right_person(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any]) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__", "yeah sure", "I'm not the person"], f"{label}-right-person")
    packet = packets[-1]
    evidence["scenario_f_right_person"] = snapshot(packet)
    assert_common_packet(failures, packet, campaign_config, f"{label}:right_person")
    assert_semantic(failures, packet, "wrong_person_or_wrong_department", f"{label}:right_person")
    memory = packet.get("demo_conversation_memory") or {}
    handoff = memory.get("handoff_target_state") or {}
    response = normalize(final_response(packet))
    assert_condition(failures, handoff.get("requested") is True, f"{label}: handoff target state must open: {snapshot(packet)}")
    assert_condition(failures, any(term in response for term in ["right person", "contact", "team"]), f"{label}: right-person response should ask right person/contact/team: {snapshot(packet)}")
    assert_condition(failures, packet_frame(packet).get("target_gap") not in ROUTESIGNAL_GAP_IDS, f"{label}: wrong-person turn selected RouteSignal product gap: {snapshot(packet)}")


def validate_regulated_caution(failures: list[str], evidence: dict[str, Any], label: str, campaign_config: dict[str, Any], utterance: str, expected_caution: str) -> None:
    packets, _state = run_sequence(campaign_config, ["__agent_open__", utterance], f"{label}-regulated")
    packet = packets[-1]
    evidence["scenario_g_regulated_caution"] = snapshot(packet)
    assert_common_packet(failures, packet, campaign_config, f"{label}:regulated_caution")
    response = normalize(final_response(packet))
    assert_condition(failures, any(term in response for term in ["cannot", "can't", "not guarantee", "should not", "need", "needs"]), f"{label}: caution response must avoid guarantees: {snapshot(packet)}")
    assert_condition(failures, any(term in response for term in ["review", "specialist", "advisor", "inspection", "verified details"]), f"{label}: caution response must route to safe human review: {snapshot(packet)}")
    assert_condition(failures, "guarantee you" not in response and "you are covered" not in response and "exact price is" not in response, f"{label}: response made unsupported regulated claim: {snapshot(packet)}")
    cautions = set(snapshot(packet).get("regulated_cautions") or [])
    assert_condition(failures, expected_caution in cautions, f"{label}: regulated caution should be exposed in trace when available: {snapshot(packet)}")


def validate_campaign_runtime(failures: list[str], evidence: dict[str, Any]) -> None:
    clear_cases = {
        "insurance": ("coverage fit is handled", "coverage_fit"),
        "telecom": ("coverage is fine", "coverage_or_availability"),
        "home_services": ("scheduling is fine", "scheduling_urgency"),
        "b2b_saas": ("manual work is handled", "manual_work"),
    }
    pain_cases = {
        "insurance": ("premium is a problem", "premium_or_budget"),
        "telecom": ("coverage is the issue", "coverage_or_availability"),
        "home_services": ("estimate is unclear", "estimate_or_property_details"),
        "b2b_saas": ("visibility is the problem", "visibility_gap"),
    }
    regulated_cases = {
        "insurance": ("can you guarantee I'm covered?", "insurance"),
        "telecom": ("can you guarantee coverage here?", "telecom_contract_or_coverage"),
        "home_services": ("can you give exact price without looking?", "home_services_safety_or_estimate"),
    }
    for label, campaign_config in synthetic_campaigns().items():
        playbook = adapter.resolve_campaign_playbook(campaign_config)
        evidence[label] = {
            "campaign_id": campaign_config.get("campaign_id"),
            "campaign_playbook_id": playbook.get("campaign_playbook_id"),
            "vertical_id": playbook.get("vertical_id"),
            "core_diagnostic_gaps": playbook.get("core_diagnostic_gaps"),
            "regulated_cautions": playbook.get("regulated_cautions") or (playbook.get("campaign_context") or {}).get("regulated_cautions") or [],
        }
        assert_condition(failures, playbook.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: playbook must be synthetic")
        validate_agent_open(failures, evidence[label], label, campaign_config)
        validate_permission_ack(failures, evidence[label], label, campaign_config)
        validate_first_gap_clear(failures, evidence[label], label, campaign_config, *clear_cases[label])
        validate_pain_confirmed(failures, evidence[label], label, campaign_config, *pain_cases[label])
        validate_send_info(failures, evidence[label], label, campaign_config)
        validate_right_person(failures, evidence[label], label, campaign_config)
        if label in regulated_cases:
            validate_regulated_caution(failures, evidence[label], label, campaign_config, *regulated_cases[label])


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
        DEFAULT_CAMPAIGN_ID,
        DEFAULT_CASES_PATH,
        DEFAULT_STAGE,
        build_turn_packet,
    )

    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "callbacks are fine"]:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "routesignal",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id="generic-runtime-smoke-routesignal",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    snapshots = [snapshot(packet) for packet in packets]
    evidence["routesignal_preservation"] = snapshots
    final = snapshots[-1]
    assert_condition(failures, final.get("semantic") == "current_gap_clear", f"routesignal: callbacks clear semantic changed: {final}")
    assert_condition(failures, final.get("target_gap") == "callbacks", f"routesignal: callbacks target gap changed: {final}")
    assert_condition(failures, final.get("playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, f"routesignal: playbook id changed: {final}")
    assert_condition(failures, "manual tracking" in normalize(final.get("final_response")), f"routesignal: remaining manual_tracking behavior changed: {final}")
    assert_condition(failures, "handoffs" in normalize(final.get("final_response")), f"routesignal: remaining handoffs behavior changed: {final}")
    assert_condition(failures, final.get("provider_calls_made") is False, f"routesignal: provider calls must be false: {final}")
    assert_condition(failures, final.get("local_llm_calls_made") is False, f"routesignal: local LLM calls must be false: {final}")
    assert_condition(failures, final.get("opens_prod_102") is False, f"routesignal: PROD-102 must remain closed: {final}")


def build_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-RUNTIME-SMOKE-001",
        "",
        f"Status: {result['status']}",
        "",
        "## Synthetic Campaigns",
        "",
    ]
    for label, item in sorted((result.get("synthetic_campaigns") or {}).items()):
        lines.append(
            f"- {label}: campaign={item.get('campaign_id')}, playbook={item.get('campaign_playbook_id')}, "
            f"vertical={item.get('vertical_id')}, core_gaps={item.get('core_diagnostic_gaps')}"
        )
    lines.extend(
        [
            "",
            "## Smoke Coverage",
            "",
            "- Scenario A: agent open",
            "- Scenario B: permission acknowledgement",
            "- Scenario C: first gap clear",
            "- Scenario D: pain confirmed",
            "- Scenario E: send info",
            "- Scenario F: right person",
            "- Scenario G: regulated caution for insurance, telecom, and home_services",
            "",
            "Note: home_services Scenario C follows the supplied utterance `scheduling is fine`, so the expected target is `scheduling_urgency` rather than the first listed gap.",
            "",
            "## RouteSignal Preservation",
            "",
        ]
    )
    route = (result.get("routesignal_preservation") or [{}])[-1]
    lines.append(
        f"- callbacks clear: semantic={route.get('semantic')}, target_gap={route.get('target_gap')}, playbook_id={route.get('playbook_id')}"
    )
    if result.get("failures"):
        lines.extend(["", "## Failures", ""])
        for failure in result["failures"]:
            lines.append(f"- {failure}")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {"synthetic_campaigns": {}}
    validate_campaign_runtime(failures, evidence["synthetic_campaigns"])
    validate_routesignal_preservation(failures, evidence)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        **evidence,
        "leakage_findings": failures,
        "forbidden_terms_checked": FORBIDDEN_BRAND_TERMS + FORBIDDEN_ROUTE_PHRASES,
        "phase_1_2_3_backpatch_required": False,
        "safety_assertions": {key: False for key in SAFETY_KEYS},
        "uses_provider_calls": False,
        "uses_live_tts": False,
        "uses_real_customer_data": False,
    }
    write_evidence(result, build_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
