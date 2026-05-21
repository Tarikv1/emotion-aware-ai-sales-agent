from __future__ import annotations

from typing import Any

from runtime.core import live_voice_session_policy as session_policy
from runtime.core import dialogue_pragmatics
from runtime.core.dialogue_reasoner import reason_about_turn, validate_reasoning_packet
from runtime.speech.asr_quality_gate import repair_response_for_quality_gate


DIALOGUE_MANAGER_ID = "DIALOGUE-MANAGER-001"
SCHEMA_VERSION = 1

TERMINAL_CALL_CONTROLS = {"end-call", "hang-up", "schedule-and-end"}

ACTION_BY_REASON = {
    "agent_opening_started": "open_with_permission",
    "opening_greeting_answered": "answer_greeting_continue",
    "callback_request_time_needed": "request_callback_time",
    "callback_time_confirmed": "confirm_callback_and_end",
    "appointment_time_requested": "request_appointment_time",
    "appointment_time_clarification_needed": "request_appointment_time",
    "appointment_time_confirmed": "confirm_appointment_and_end",
    "appointment_value_clarified": "clarify_appointment_value",
    "buyer_requested_stop": "end_call_stop_request",
    "call_purpose_explained": "recover_call_purpose",
    "seller_agenda_recovered": "recover_seller_agenda",
    "pragmatic_call_purpose_explained": "recover_call_purpose",
    "pragmatic_seller_agenda_recovered": "recover_seller_agenda",
    "pragmatic_previous_question_clarified": "clarify_previous_question",
    "pragmatic_question_simplified": "simplify_previous_question",
    "pragmatic_term_explained": "explain_term",
    "pragmatic_relevance_explained": "explain_relevance",
    "pragmatic_crm_boundary_answered": "answer_crm_boundary_continue",
    "pragmatic_pain_to_appointment": "request_appointment_time",
    "structured_reasoner_crm_replacement_answered": "answer_crm_boundary_continue",
    "structured_reasoner_integration_boundary_answered": "answer_crm_boundary_continue",
    "campaign_depth_crm_replacement_answered": "answer_crm_boundary_continue",
    "campaign_depth_integration_boundary_answered": "answer_crm_boundary_continue",
    "previous_question_clarified": "clarify_previous_question",
    "conversation_stability_repaired": "repair_conversation_stability",
    "asr_fragment_repair": "repair_asr_fragment",
}

TEMPLATE_BY_ACTION = {
    "open_with_permission": "sales_opening_permission",
    "answer_greeting_continue": "opening_greeting_answer",
    "request_callback_time": "callback_time_request",
    "confirm_callback_and_end": "callback_time_confirmation",
    "request_appointment_time": "appointment_time_request",
    "confirm_appointment_and_end": "appointment_time_confirmation",
    "clarify_appointment_value": "appointment_value_clarification",
    "end_call_stop_request": "buyer_stop_short",
    "keep_call_closed": "terminal_call_closed",
    "recover_call_purpose": "call_purpose_recovery",
    "recover_seller_agenda": "seller_agenda_recovery",
    "answer_crm_boundary_continue": "public_crm_boundary",
    "clarify_previous_question": "previous_question_clarification",
    "simplify_previous_question": "previous_question_simplification",
    "explain_term": "plain_term_explanation",
    "explain_relevance": "value_relevance_explanation",
    "repair_conversation_stability": "conversation_stability_repair",
    "repair_asr_fragment": "asr_fragment_repair",
    "continue_with_session_policy": "session_policy_response",
    "guarded_composer_passthrough": "guarded_response_composer",
}

CALL_CONTROL_BY_ACTION = {
    "end_call_stop_request": "end-call",
    "keep_call_closed": "end-call",
    "confirm_callback_and_end": "schedule-and-end",
    "confirm_appointment_and_end": "schedule-and-end",
    "request_callback_time": "continue-call",
    "request_appointment_time": "continue-call",
    "answer_crm_boundary_continue": "continue-call",
    "recover_call_purpose": "continue-call",
    "recover_seller_agenda": "continue-call",
    "clarify_previous_question": "continue-call",
    "simplify_previous_question": "continue-call",
    "explain_term": "continue-call",
    "explain_relevance": "continue-call",
}

DECISION_OVERRIDE_BY_ACTION = {
    "end_call_stop_request": {
        "sales_difficulty": "do-not-call",
        "detected_emotion": "skeptical-or-negative",
        "interest_state": "do-not-call",
        "selected_strategy": "rapport",
        "next_action": "suppress-contact",
        "call_control": "end-call",
    },
    "keep_call_closed": {
        "sales_difficulty": "do-not-call",
        "detected_emotion": "skeptical-or-negative",
        "interest_state": "do-not-call",
        "selected_strategy": "rapport",
        "next_action": "suppress-contact",
        "call_control": "end-call",
    },
    "confirm_callback_and_end": {
        "sales_difficulty": "scheduling-confirmation",
        "detected_emotion": "positive",
        "interest_state": "interested",
        "selected_strategy": "direct-ask-or-commitment",
        "next_action": "confirm-scheduling",
        "call_control": "schedule-and-end",
    },
    "confirm_appointment_and_end": {
        "sales_difficulty": "appointment-scheduling-confirmation",
        "detected_emotion": "positive",
        "interest_state": "interested",
        "selected_strategy": "direct-ask-or-commitment",
        "next_action": "confirm-appointment",
        "call_control": "schedule-and-end",
    },
    "request_appointment_time": {
        "sales_difficulty": "appointment-setting",
        "detected_emotion": "positive",
        "interest_state": "interested",
        "selected_strategy": "direct-ask-or-commitment",
        "next_action": "request-appointment-time",
        "call_control": "continue-call",
    },
    "answer_crm_boundary_continue": {
        "sales_difficulty": "product-detail-lookup",
        "detected_emotion": "neutral",
        "interest_state": "maybe-interested",
        "selected_strategy": "consultative-question",
        "next_action": "answer-and-continue",
        "call_control": "continue-call",
    },
    "recover_call_purpose": {
        "sales_difficulty": "call-purpose-repair",
        "detected_emotion": "neutral",
        "interest_state": "unclear",
        "selected_strategy": "consultative-question",
        "next_action": "answer-and-continue",
        "call_control": "continue-call",
    },
    "recover_seller_agenda": {
        "sales_difficulty": "seller-agenda-repair",
        "detected_emotion": "neutral",
        "interest_state": "unclear",
        "selected_strategy": "consultative-question",
        "next_action": "ask-diagnostic-question",
        "call_control": "continue-call",
    },
    "clarify_previous_question": {
        "sales_difficulty": "dialogue-repair",
        "detected_emotion": "neutral",
        "interest_state": "unclear",
        "selected_strategy": "consultative-question",
        "next_action": "clarify-question",
        "call_control": "continue-call",
    },
    "simplify_previous_question": {
        "sales_difficulty": "dialogue-repair",
        "detected_emotion": "neutral",
        "interest_state": "unclear",
        "selected_strategy": "consultative-question",
        "next_action": "simplify-question",
        "call_control": "continue-call",
    },
    "explain_term": {
        "sales_difficulty": "dialogue-repair",
        "detected_emotion": "neutral",
        "interest_state": "unclear",
        "selected_strategy": "consultative-question",
        "next_action": "explain-term",
        "call_control": "continue-call",
    },
    "explain_relevance": {
        "sales_difficulty": "dialogue-repair",
        "detected_emotion": "neutral",
        "interest_state": "unclear",
        "selected_strategy": "consultative-question",
        "next_action": "explain-relevance",
        "call_control": "continue-call",
    },
}


def _turns(session_state: dict | None) -> list[dict[str, Any]]:
    return list((session_state or {}).get("turns") or [])


def _previous_call_control(turns: list[dict[str, Any]]) -> str:
    if not turns:
        return ""
    return str((turns[-1].get("summary") or {}).get("call_control") or "")


def _previous_response(turns: list[dict[str, Any]]) -> str:
    if not turns:
        return ""
    return str((turns[-1].get("summary") or {}).get("final_response") or "")


def _state_from_inputs(
    *,
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    quality_gate: dict,
    dialogue_reasoning: dict | None,
    pragmatic_move: dict | None,
) -> dict[str, Any]:
    turns = _turns(session_state)
    normalized = session_policy.normalize_text(transcript)
    return {
        "normalized_transcript": normalized,
        "turn_count": len(turns),
        "language": str(campaign.get("language") or "en"),
        "campaign_id": campaign.get("campaign_id"),
        "resolved_focus": session_policy.dialogue_focus_from_turns(turns),
        "selected_focus": session_policy.focus_from_transcript(normalized),
        "selected_gap": session_policy.last_selected_gap_from_turns(turns),
        "callback_semantic": session_policy.callback_semantic_from_transcript(normalized, session_state),
        "previous_call_control": _previous_call_control(turns),
        "previous_question_type": session_policy.question_type_from_response(_previous_response(turns)),
        "quality_gate_accepted": bool(quality_gate.get("accepted")),
        "quality_gate_reason": quality_gate.get("reason"),
        "dialogue_reasoning": dialogue_reasoning or {},
        "pragmatic_move": pragmatic_move or {},
    }


def _fallback_reasoning(quality_gate: dict) -> dict[str, Any]:
    return validate_reasoning_packet(
        {
            "dialogue_act": "asr_fragment",
            "buyer_intent": "repair_asr",
            "resolved_topic": "asr_quality",
            "sales_stage": "repair",
            "response_strategy": "repeat_request",
            "must_include": ["repeat request"],
            "must_avoid": ["guessing buyer intent from low-confidence ASR"],
            "safety_boundary": "asr_quality_boundary",
            "confidence": float(quality_gate.get("confidence") or 0.0),
        }
    )


def _action_id_for_continuity(continuity: dict[str, Any]) -> str:
    explicit_action = str(continuity.get("action_id") or "")
    if explicit_action:
        return explicit_action
    reason = str(continuity.get("reason") or "")
    if reason in ACTION_BY_REASON:
        return ACTION_BY_REASON[reason]
    if reason.startswith("seller_gap_selected_for_") and continuity.get("selected_gap"):
        return "continue_with_session_policy"
    if reason.startswith("selected_") and reason.endswith("_next_step_explained"):
        return "continue_with_session_policy"
    if reason.startswith("focus_shift_to_"):
        return "continue_with_session_policy"
    if reason.startswith("resolved_"):
        return "continue_with_session_policy"
    if continuity.get("applied"):
        return "continue_with_session_policy"
    return "guarded_composer_passthrough"


def _template_id_for_action(action_id: str, continuity: dict[str, Any]) -> str:
    if action_id == "continue_with_session_policy":
        reason = str(continuity.get("reason") or "session_policy_response")
        return f"session_policy_{reason}"
    return TEMPLATE_BY_ACTION.get(action_id, "session_policy_response")


def _call_control_for_action(action_id: str, continuity: dict[str, Any]) -> str:
    if action_id in CALL_CONTROL_BY_ACTION:
        return CALL_CONTROL_BY_ACTION[action_id]
    if continuity.get("applied"):
        return "continue-call"
    return ""


def _action_from_continuity(
    *,
    state_before: dict[str, Any],
    continuity: dict[str, Any],
    source: str,
    dialogue_reasoning: dict[str, Any],
    rewrite_count: int = 0,
    repair_chain: list[str] | None = None,
) -> dict[str, Any]:
    action_id = _action_id_for_continuity(continuity)
    selected_action = {
        "action_id": action_id,
        "template_id": _template_id_for_action(action_id, continuity),
        "source": source,
        "continuity_reason": str(continuity.get("reason") or ""),
        "dialogue_focus": continuity.get("dialogue_focus"),
        "selected_gap": continuity.get("selected_gap"),
        "pragmatic_move": (continuity.get("pragmatic_move") or state_before.get("pragmatic_move") or {}),
        "candidate_response_available": bool(continuity.get("candidate_response")),
        "call_control": _call_control_for_action(action_id, continuity),
    }
    return {
        "manager_id": DIALOGUE_MANAGER_ID,
        "schema_version": SCHEMA_VERSION,
        "state_before": state_before,
        "selected_action": selected_action,
        "continuity": continuity,
        "candidate_response": continuity.get("candidate_response") if continuity.get("applied") else None,
        "decision_override": DECISION_OVERRIDE_BY_ACTION.get(action_id),
        "dialogue_reasoning": dialogue_reasoning,
        "candidate_response_rewrite_count": rewrite_count,
        "repair_chain": list(repair_chain or []),
    }


def _terminal_continuity(language: str) -> dict[str, Any]:
    return {
        "applied": True,
        "reason": "buyer_requested_stop",
        "dialogue_focus": "timing",
        "candidate_response": session_policy.buyer_stop_response(language),
    }


def plan_dialogue_action(
    *,
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    quality_gate: dict,
    dialogue_reasoning: dict | None = None,
) -> dict[str, Any]:
    language = str(campaign.get("language") or "en")
    turns = _turns(session_state)
    if quality_gate.get("accepted") and dialogue_reasoning is None:
        dialogue_reasoning = reason_about_turn(transcript, session_state, campaign, mode="baseline")
    elif not quality_gate.get("accepted"):
        dialogue_reasoning = _fallback_reasoning(quality_gate)

    pragmatic_move = dialogue_pragmatics.classify_pragmatic_move(
        transcript,
        session_state,
        campaign,
        dialogue_reasoning=dialogue_reasoning,
    )

    state_before = _state_from_inputs(
        transcript=transcript,
        session_state=session_state,
        campaign=campaign,
        quality_gate=quality_gate,
        dialogue_reasoning=dialogue_reasoning,
        pragmatic_move=pragmatic_move,
    )

    if _previous_call_control(turns) in TERMINAL_CALL_CONTROLS:
        continuity = _terminal_continuity(language)
        action = _action_from_continuity(
            state_before=state_before,
            continuity=continuity,
            source="terminal_call_control",
            dialogue_reasoning=dialogue_reasoning or {},
        )
        action["selected_action"]["action_id"] = "keep_call_closed"
        action["selected_action"]["template_id"] = TEMPLATE_BY_ACTION["keep_call_closed"]
        action["selected_action"]["call_control"] = "end-call"
        action["decision_override"] = DECISION_OVERRIDE_BY_ACTION["keep_call_closed"]
        return action

    if not quality_gate.get("accepted"):
        continuity = repair_response_for_quality_gate(language, quality_gate)
        return _action_from_continuity(
            state_before=state_before,
            continuity=continuity,
            source="asr_quality_gate",
            dialogue_reasoning=dialogue_reasoning or {},
        )

    pragmatic_continuity = dialogue_pragmatics.continuity_from_pragmatic_move(pragmatic_move)
    if pragmatic_continuity:
        return _action_from_continuity(
            state_before=state_before,
            continuity=pragmatic_continuity,
            source="dialogue_pragmatics",
            dialogue_reasoning=dialogue_reasoning or {},
        )

    continuity = session_policy.continuity_response(
        transcript,
        session_state,
        campaign,
        dialogue_reasoning=dialogue_reasoning,
    )
    return _action_from_continuity(
        state_before=state_before,
        continuity=continuity,
        source="live_voice_session_policy",
        dialogue_reasoning=dialogue_reasoning or {},
    )


def candidate_response(action: dict[str, Any]) -> str | None:
    value = action.get("candidate_response")
    return str(value) if value else None


def _is_terminal_action(action: dict[str, Any]) -> bool:
    selected = action.get("selected_action") or {}
    return str(selected.get("call_control") or "") in TERMINAL_CALL_CONTROLS


def continuity(action: dict[str, Any]) -> dict[str, Any]:
    return dict(action.get("continuity") or {})


def apply_anti_loop_if_needed(
    *,
    action: dict[str, Any],
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    generated_response: str,
) -> dict[str, Any]:
    if _is_terminal_action(action):
        return action
    if candidate_response(action):
        return action
    repair = session_policy.anti_loop_response(
        transcript,
        session_state,
        str(campaign.get("language") or "en"),
        generated_response,
    )
    if not repair.get("applied"):
        return action
    chain = list(action.get("repair_chain") or []) + ["anti_loop_response"]
    return _action_from_continuity(
        state_before=dict(action.get("state_before") or {}),
        continuity=repair,
        source="anti_loop_response",
        dialogue_reasoning=dict(action.get("dialogue_reasoning") or {}),
        rewrite_count=int(action.get("candidate_response_rewrite_count") or 0) + 1,
        repair_chain=chain,
    )


def apply_duplicate_repair_if_needed(
    *,
    action: dict[str, Any],
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    generated_response: str,
) -> dict[str, Any]:
    if _is_terminal_action(action):
        return action
    repair = session_policy.duplicate_response_repair(
        transcript,
        session_state,
        str(campaign.get("language") or "en"),
        generated_response,
    )
    if not repair.get("applied"):
        return action
    chain = list(action.get("repair_chain") or []) + ["duplicate_response_repair"]
    return _action_from_continuity(
        state_before=dict(action.get("state_before") or {}),
        continuity=repair,
        source="duplicate_response_repair",
        dialogue_reasoning=dict(action.get("dialogue_reasoning") or {}),
        rewrite_count=int(action.get("candidate_response_rewrite_count") or 0) + 1,
        repair_chain=chain,
    )


def build_conversation_memory(
    *,
    action: dict[str, Any],
    session_state: dict | None,
    transcript: str,
    final_response: str,
) -> dict[str, Any]:
    return session_policy.build_conversation_memory(
        session_state,
        transcript,
        final_response,
        continuity(action),
    )


def apply_stability_guard_if_needed(
    *,
    action: dict[str, Any],
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    generated_response: str,
    conversation_memory: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if _is_terminal_action(action):
        return action, {
            "applied": False,
            "reason": "terminal_action_stability_skipped",
            "violations": [],
            "dialogue_focus": continuity(action).get("dialogue_focus"),
            "selected_gap": continuity(action).get("selected_gap"),
        }
    repair = session_policy.pre_speech_conversation_stability_guard(
        transcript,
        session_state,
        str(campaign.get("language") or "en"),
        generated_response,
        conversation_memory,
    )
    if not repair.get("applied"):
        return action, repair
    chain = list(action.get("repair_chain") or []) + ["pre_speech_conversation_stability_guard"]
    repaired_action = _action_from_continuity(
        state_before=dict(action.get("state_before") or {}),
        continuity=repair,
        source="pre_speech_conversation_stability_guard",
        dialogue_reasoning=dict(action.get("dialogue_reasoning") or {}),
        rewrite_count=int(action.get("candidate_response_rewrite_count") or 0) + 1,
        repair_chain=chain,
    )
    return repaired_action, repair


def apply_decision_override(packet: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    override = action.get("decision_override")
    if not override:
        return packet
    decision = packet.get("decision_snapshot", {})
    decision.update(dict(override))
    packet["decision_snapshot"] = decision
    return packet


def finalize_trace(
    *,
    action: dict[str, Any],
    packet: dict[str, Any],
    conversation_memory: dict[str, Any],
    stability_guard: dict[str, Any],
) -> dict[str, Any]:
    decision = packet.get("decision_snapshot") or {}
    final_response = str(packet.get("final_response") or "")
    call_control = str(decision.get("call_control") or "")
    state_after = {
        "active_topic": conversation_memory.get("active_topic"),
        "selected_gap": conversation_memory.get("selected_gap"),
        "last_agent_question_type": conversation_memory.get("last_agent_question_type"),
        "last_customer_intent": conversation_memory.get("last_customer_intent"),
        "appointment_close_ready": conversation_memory.get("appointment_close_ready"),
        "call_control": call_control,
    }
    trace = {
        "manager_id": DIALOGUE_MANAGER_ID,
        "schema_version": SCHEMA_VERSION,
        "state_before": dict(action.get("state_before") or {}),
        "selected_action": dict(action.get("selected_action") or {}),
        "pragmatic_move": dict((action.get("state_before") or {}).get("pragmatic_move") or {}),
        "state_after": state_after,
        "final_response": final_response,
        "call_control": call_control,
        "authoritative_final_action": True,
        "final_response_source": str((action.get("selected_action") or {}).get("source") or ""),
        "candidate_response_rewrite_count": int(action.get("candidate_response_rewrite_count") or 0),
        "repair_chain": list(action.get("repair_chain") or []),
        "stability_guard_reason": stability_guard.get("reason"),
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "opens_prod_102": False,
    }
    if not trace["selected_action"].get("call_control"):
        trace["selected_action"]["call_control"] = call_control
    return trace
