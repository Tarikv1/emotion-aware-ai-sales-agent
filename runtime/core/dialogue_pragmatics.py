from __future__ import annotations

from typing import Any

from runtime.core import live_voice_session_policy as session_policy


DIALOGUE_PRAGMATICS_ID = "DIALOGUE-PRAGMATICS-001"
SCHEMA_VERSION = 1
LEGACY_REASON_BY_MOVE = {
    "call_purpose_question": "call_purpose_explained",
    "previous_question_clarification": "previous_question_clarified",
    "term_or_context_unfamiliarity": "uncertain_gap_simplified",
    "term_meaning_question": "plain_qualification_term_clarified",
    "relevance_challenge": "value_relevance_explained",
    "agent_should_lead": "seller_agenda_recovered",
    "crm_replacement_question": "structured_reasoner_crm_replacement_answered",
    "pain_statement": "appointment_time_requested",
    "appointment_think_about_it": "callback_request_time_needed",
    "callback_later_affirmed": "callback_request_time_needed",
}


def _turns(session_state: dict | None) -> list[dict[str, Any]]:
    return list((session_state or {}).get("turns") or [])


def _previous_response(turns: list[dict[str, Any]]) -> str:
    if not turns:
        return ""
    return str((turns[-1].get("summary") or {}).get("final_response") or "")


def _contains(normalized: str, phrases: set[str]) -> bool:
    return session_policy.normalized_contains_any(normalized, phrases)


def _packet(
    *,
    move_id: str,
    action_id: str | None,
    reason: str | None,
    confidence: float,
    transcript: str,
    normalized: str,
    session_state: dict | None,
    campaign: dict,
    dialogue_reasoning: dict | None,
    selected_gap: str | None = None,
    candidate_response: str | None = None,
    target_focus: str | None = None,
    legacy_reason: str | None = None,
) -> dict[str, Any]:
    turns = _turns(session_state)
    previous_response = _previous_response(turns)
    resolved_focus = target_focus or session_policy.dialogue_focus_from_turns(turns) or "qualification"
    return {
        "pragmatics_id": DIALOGUE_PRAGMATICS_ID,
        "schema_version": SCHEMA_VERSION,
        "move_id": move_id,
        "applied": bool(action_id and reason and candidate_response),
        "target_action": action_id,
        "continuity_reason": reason,
        "legacy_reason": legacy_reason,
        "confidence": round(float(confidence), 2),
        "normalized_transcript": normalized,
        "dialogue_focus": resolved_focus,
        "selected_gap": selected_gap,
        "previous_question": session_policy.previous_agent_question(turns),
        "previous_question_type": session_policy.question_type_from_response(previous_response),
        "dialogue_reasoning_act": str((dialogue_reasoning or {}).get("dialogue_act") or ""),
        "response_strategy": str((dialogue_reasoning or {}).get("response_strategy") or ""),
        "campaign_id": campaign.get("campaign_id"),
        "candidate_response": candidate_response,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "opens_prod_102": False,
    }


def _no_match(
    *,
    transcript: str,
    normalized: str,
    session_state: dict | None,
    campaign: dict,
    dialogue_reasoning: dict | None,
) -> dict[str, Any]:
    return _packet(
        move_id="no_pragmatic_repair",
        action_id=None,
        reason=None,
        confidence=0.0,
        transcript=transcript,
        normalized=normalized,
        session_state=session_state,
        campaign=campaign,
        dialogue_reasoning=dialogue_reasoning,
    )


def _term_explanation(language: str, normalized: str) -> str | None:
    if language.startswith("de"):
        return session_policy.plain_qualification_term_clarification_text(language, normalized)
    if _contains(normalized, {"growth"}):
        return (
            "Sorry, I should have explained that. Growth is the RouteSignal setup for teams that need "
            "follow-up reminders and handoff review around inbound demo requests. The practical question "
            "is whether missed callbacks are worth a short workflow review."
        )
    if _contains(normalized, {"handoff", "handoffs"}):
        return (
            "I meant: a handoff is the owner or next person getting the demo request "
            "with the next callback visible. The gap is when that next reply gets lost."
        )
    return session_policy.plain_qualification_term_clarification_text(language, normalized)


def _is_term_meaning_question(normalized: str) -> bool:
    if not _contains(normalized, {"what do you mean", "what does that mean", "mean by", "meaning of", "what is", "what are"}):
        return False
    return _contains(
        normalized,
        {
            "handoff",
            "handoffs",
            "owner",
            "ownership",
            "callback",
            "callbacks",
            "shared inbox",
            "routing",
            "route",
            "growth",
        },
    )


def _is_unfamiliarity_reply(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "not familiar",
            "not really familiar",
            "unfamiliar",
            "do not know these",
            "dont know these",
            "don t know these",
            "do not know that",
            "dont know that",
            "not sure what that means",
            "no idea what that means",
            "not following",
        },
    )


def classify_pragmatic_move(
    transcript: str,
    session_state: dict | None,
    campaign: dict,
    *,
    dialogue_reasoning: dict | None = None,
) -> dict[str, Any]:
    language = str(campaign.get("language") or "en")
    normalized = session_policy.normalize_text(transcript)
    turns = _turns(session_state)
    previous_question = session_policy.previous_agent_question(turns)

    if not normalized or session_policy.is_agent_open_turn(normalized):
        return _no_match(
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
        )

    if session_policy.is_crm_replacement_question(normalized):
        return _packet(
            move_id="crm_replacement_question",
            action_id="answer_crm_boundary_continue",
            reason="pragmatic_crm_boundary_answered",
            confidence=0.95,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus="qualification",
            candidate_response=session_policy.public_crm_boundary_response(normalized, campaign),
        )

    if session_policy.is_call_purpose_question(normalized):
        return _packet(
            move_id="call_purpose_question",
            action_id="recover_call_purpose",
            reason="pragmatic_call_purpose_explained",
            confidence=0.95,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus="qualification",
            candidate_response=session_policy.call_purpose_response(language, campaign),
        )

    if session_policy.is_buyer_no_question_repair(normalized) and not _contains(normalized, {"you called me", "you should ask"}):
        return _packet(
            move_id="buyer_no_question_repair",
            action_id="recover_seller_agenda",
            reason="pragmatic_buyer_no_question_recovered",
            confidence=0.9,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus="qualification",
            candidate_response=session_policy.buyer_no_question_response(language),
            legacy_reason="buyer_no_question_recovered",
        )

    if session_policy.is_buyer_expects_agent_to_lead(normalized):
        return _packet(
            move_id="agent_should_lead",
            action_id="recover_seller_agenda",
            reason="pragmatic_seller_agenda_recovered",
            confidence=0.94,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus="qualification",
            candidate_response=session_policy.seller_agenda_recovered_response(language),
            legacy_reason="buyer_no_question_recovered",
        )

    if _is_term_meaning_question(normalized):
        explanation = _term_explanation(language, normalized)
        if explanation:
            legacy_reason = "callback_workflow_clarified" if _contains(normalized, {"callback", "callbacks"}) else None
            return _packet(
                move_id="term_meaning_question",
                action_id="explain_term",
                reason="pragmatic_term_explained",
                confidence=0.93,
                transcript=transcript,
                normalized=normalized,
                session_state=session_state,
                campaign=campaign,
                dialogue_reasoning=dialogue_reasoning,
                target_focus="qualification",
                candidate_response=explanation,
                legacy_reason=legacy_reason,
            )

    pending_appointment_gap = session_policy.pending_appointment_gap_from_turns(turns)
    pending_review_gap = pending_appointment_gap or (
        session_policy.last_selected_gap_from_turns(turns) if session_policy.has_recent_review_next_step_question(turns) else None
    )
    if pending_review_gap and session_policy.is_think_about_it_reply(normalized):
        return _packet(
            move_id="appointment_think_about_it",
            action_id="request_callback_time",
            reason="pragmatic_callback_time_after_think",
            confidence=0.94,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            selected_gap=pending_review_gap,
            target_focus="timing",
            candidate_response=session_policy.appointment_think_about_it_response(language, pending_review_gap),
        )

    if session_policy.previous_response_offered_callback_later(turns) and session_policy.is_affirmative_next_step_reply(normalized):
        return _packet(
            move_id="callback_later_affirmed",
            action_id="request_callback_time",
            reason="pragmatic_callback_later_time_needed",
            confidence=0.94,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            selected_gap=session_policy.last_selected_gap_from_turns(turns),
            target_focus="timing",
            candidate_response=session_policy.callback_later_time_request_response(language),
        )

    if pending_appointment_gap and session_policy.is_value_relevance_question(normalized):
        return _packet(
            move_id="appointment_value_question",
            action_id="clarify_appointment_value",
            reason="pragmatic_appointment_value_clarified",
            confidence=0.92,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            selected_gap=pending_appointment_gap,
            target_focus="timing",
            candidate_response=session_policy.appointment_value_clarification_response(language, pending_appointment_gap),
            legacy_reason="appointment_value_clarified",
        )

    if pending_appointment_gap and (
        session_policy.is_affirmative_next_step_reply(normalized) or session_policy.is_pain_confirmation_reply(normalized)
    ):
        return _packet(
            move_id="pain_statement",
            action_id="request_appointment_time",
            reason="pragmatic_pain_to_appointment",
            confidence=0.94,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            selected_gap=pending_appointment_gap,
            target_focus="timing",
            candidate_response=session_policy.appointment_time_followup_response(
                language,
                pending_appointment_gap,
                session_policy.appointment_time_request_count(turns),
            ),
        )

    if session_policy.is_value_relevance_question(normalized):
        return _packet(
            move_id="relevance_challenge",
            action_id="explain_relevance",
            reason="pragmatic_relevance_explained",
            confidence=0.92,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus="qualification",
            candidate_response=session_policy.value_relevance_response(language),
        )

    if session_policy.is_new_trial_request_clarification(normalized):
        return _no_match(
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
        )

    if previous_question and session_policy.is_previous_question_clarification_request(normalized):
        focus = session_policy.dialogue_focus_from_turns(turns) or "qualification"
        return _packet(
            move_id="previous_question_clarification",
            action_id="clarify_previous_question",
            reason="pragmatic_previous_question_clarified",
            confidence=0.93,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus=focus,
            candidate_response=session_policy.clarify_previous_question_text(language, focus, previous_question),
        )

    if _is_unfamiliarity_reply(normalized):
        return _packet(
            move_id="term_or_context_unfamiliarity",
            action_id="simplify_previous_question",
            reason="pragmatic_question_simplified",
            confidence=0.89,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            target_focus="qualification",
            candidate_response=session_policy.uncertain_gap_response(language),
        )

    should_close, appointment_gap = session_policy.should_offer_appointment_close(normalized, turns)
    if should_close:
        return _packet(
            move_id="pain_statement",
            action_id="request_appointment_time",
            reason="pragmatic_pain_to_appointment",
            confidence=0.94,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            selected_gap=appointment_gap,
            target_focus="timing",
            candidate_response=session_policy.appointment_lead_close_response(language, appointment_gap, campaign),
        )

    selected_gap = session_policy.selected_sales_gap_from_transcript(normalized)
    if selected_gap and session_policy.is_pain_confirmation_reply(normalized):
        previous_question_type = session_policy.question_type_from_response(previous_question or "")
        direct_time_ask_allowed = (
            selected_gap != "callbacks"
            or session_policy.has_recent_review_next_step_question(turns)
            or previous_question_type in {"workflow_review_next_step", "value_review_check", "summary_next_step"}
            or session_policy.dialogue_focus_from_turns(turns) == "fit"
        )
        if not direct_time_ask_allowed:
            return _packet(
                move_id="pain_review_offered",
                action_id="continue_with_session_policy",
                reason="pragmatic_pain_review_offered",
                confidence=0.88,
                transcript=transcript,
                normalized=normalized,
                session_state=session_state,
                campaign=campaign,
                dialogue_reasoning=dialogue_reasoning,
                selected_gap=selected_gap,
                target_focus="qualification",
                candidate_response=session_policy.pain_review_usefulness_response(language, selected_gap),
            )
        return _packet(
            move_id="pain_statement",
            action_id="request_appointment_time",
            reason="pragmatic_pain_to_appointment",
            confidence=0.9,
            transcript=transcript,
            normalized=normalized,
            session_state=session_state,
            campaign=campaign,
            dialogue_reasoning=dialogue_reasoning,
            selected_gap=selected_gap,
            target_focus="timing",
            candidate_response=session_policy.appointment_lead_close_response(language, selected_gap, campaign),
        )

    return _no_match(
        transcript=transcript,
        normalized=normalized,
        session_state=session_state,
        campaign=campaign,
        dialogue_reasoning=dialogue_reasoning,
    )


def continuity_from_pragmatic_move(move: dict[str, Any]) -> dict[str, Any] | None:
    if not move.get("applied"):
        return None
    move_id = str(move.get("move_id") or "")
    return {
        "applied": True,
        "reason": str(move.get("legacy_reason") or LEGACY_REASON_BY_MOVE.get(move_id, str(move.get("continuity_reason") or ""))),
        "action_id": str(move.get("target_action") or ""),
        "pragmatic_continuity_reason": str(move.get("continuity_reason") or ""),
        "dialogue_focus": move.get("dialogue_focus"),
        "selected_gap": move.get("selected_gap"),
        "candidate_response": str(move.get("candidate_response") or ""),
        "pragmatic_move": {
            key: value
            for key, value in move.items()
            if key not in {"candidate_response", "normalized_transcript"}
        },
    }
