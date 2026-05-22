from __future__ import annotations

from typing import Any

from runtime.core import live_voice_session_policy as session_policy
from runtime.core import universal_sales_conversation_knowledge as knowledge
from runtime.speech.asr_quality_gate import normalize_transcript


POLICY_RUNTIME_ID = "UNIVERSAL-CONVERSATION-POLICY-RUNTIME-001"
SCHEMA_VERSION = 1
REPAIR_RESPONSE = "I may have misheard that. Could you repeat it briefly?"

ROUTESIGNAL_CAMPAIGN_IDS = {
    "live-demo-001-routesignal",
    "campaign-prod-005-b2b-software",
}

KNOWN_NONSENSE_PHRASES = {
    "play a double be good",
    "yadav would be good",
}

NEAR_MISS_PHRASES = {
    "repeal timing",
    "repeal timings",
}

CLEAN_ACKNOWLEDGEMENTS = {
    "yeah",
    "yes",
    "sure",
    "yeah sure",
    "yes sure",
    "that would be good",
    "yeah that would be good",
    "ok",
    "okay",
}

TIME_WORDS = {
    "today",
    "tomorrow",
    "morning",
    "afternoon",
    "evening",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "am",
    "pm",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
}

FRAGMENT_WORDS = {"a", "an", "the", "about", "of", "to", "for", "with", "and", "or", "but"}


def _turns(session_state: dict | None) -> list[dict[str, Any]]:
    return list((session_state or {}).get("turns") or [])


def _previous_agent_response(session_state: dict | None) -> str:
    turns = _turns(session_state)
    if not turns:
        return ""
    return str((turns[-1].get("summary") or {}).get("final_response") or turns[-1].get("agent_response") or "")


def _previous_question_type(session_state: dict | None) -> str:
    return session_policy.question_type_from_response(_previous_agent_response(session_state))


def _is_generic_campaign(campaign: dict | None) -> bool:
    if not isinstance(campaign, dict):
        return False
    campaign_id = str(campaign.get("campaign_id") or "")
    if campaign_id in ROUTESIGNAL_CAMPAIGN_IDS:
        return False
    return bool(campaign.get("vertical_id") and isinstance(campaign.get("diagnostic_gaps"), dict))


def _looks_like_time(normalized: str) -> bool:
    words = set(normalized.split())
    if words & TIME_WORDS:
        return True
    return any(char.isdigit() for char in normalized)


def detect_universal_asr_garble(
    *,
    transcript: str,
    quality_gate: dict | None = None,
    session_state: dict | None = None,
    campaign: dict | None = None,
) -> dict[str, Any]:
    normalized = normalize_transcript(transcript)
    previous_question_type = _previous_question_type(session_state)
    quality_gate = quality_gate or {}

    if transcript == "__agent_open__":
        return _detection(False, "agent_open", normalized, previous_question_type)

    if quality_gate.get("accepted") is False:
        return _detection(True, str(quality_gate.get("reason") or "asr_quality_rejected"), normalized, previous_question_type)

    if not normalized:
        return _detection(True, "empty_or_fragment", normalized, previous_question_type)

    if normalized in CLEAN_ACKNOWLEDGEMENTS:
        return _detection(False, "clean_acknowledgement", normalized, previous_question_type)

    for phrase in KNOWN_NONSENSE_PHRASES:
        if phrase in normalized:
            return _detection(True, "known_phonetic_nonsense", normalized, previous_question_type)

    for phrase in NEAR_MISS_PHRASES:
        if phrase in normalized:
            return _detection(True, "domain_near_miss", normalized, previous_question_type)

    words = normalized.split()
    if len(words) <= 2 and words[-1] in FRAGMENT_WORDS:
        return _detection(True, "empty_or_fragment", normalized, previous_question_type)

    if previous_question_type in {"callback_time", "appointment_time"}:
        if not _looks_like_time(normalized) and normalized not in CLEAN_ACKNOWLEDGEMENTS:
            if any(token in normalized for token in {"yadav", "double", "play"}):
                return _detection(True, "high_risk_appointment_time_mismatch", normalized, previous_question_type)

    return _detection(False, "not_garbled", normalized, previous_question_type)


def _detection(applied: bool, reason: str, normalized: str, previous_question_type: str) -> dict[str, Any]:
    return {
        "applied": bool(applied),
        "reason": reason,
        "normalized_transcript": normalized,
        "previous_question_type": previous_question_type,
    }


def _buyer_move_from_context(contextual_semantics: dict | None, transcript: str) -> str:
    semantic = str((contextual_semantics or {}).get("semantic") or "")
    normalized = normalize_transcript(transcript)
    if semantic == "pain_confirmed":
        return "pain_confirmed"
    if semantic in {"current_gap_clear", "no_pain_for_specific_gap"}:
        return "no_pain_clear"
    if semantic in {"callback_time_confirmed", "appointment_time_confirmed"}:
        return "callback_time_provided"
    if normalized in CLEAN_ACKNOWLEDGEMENTS:
        return "permission_acknowledgement"
    if "why" in normalized and "asking" in normalized:
        return "why_are_you_asking"
    if "product" in normalized or "details" in normalized:
        return "product_detail_question"
    return "confusion_not_clear"


def _conversation_stage(
    *,
    transcript: str,
    session_state: dict | None,
    contextual_semantics: dict | None,
    detection: dict,
) -> str:
    if detection.get("applied"):
        previous_type = str(detection.get("previous_question_type") or "")
        if previous_type == "appointment_time":
            return "appointment_progression"
        if previous_type == "callback_time":
            return "callback_capture"
        return "diagnostic"
    semantic = str((contextual_semantics or {}).get("semantic") or "")
    if transcript == "__agent_open__":
        return "opening"
    if not _turns(session_state):
        return "permission"
    if semantic in {"callback_time_confirmed", "appointment_time_confirmed"}:
        return "callback_capture"
    return "diagnostic"


def should_enforce_universal_asr_repair(
    *,
    detection: dict | None = None,
    campaign: dict | None = None,
    frame: dict | None = None,
) -> bool:
    active_detection = detection or {}
    if frame:
        active_detection = {"applied": bool(frame.get("asr_repair_required"))}
    return bool(active_detection.get("applied") and _is_generic_campaign(campaign))


def build_universal_conversation_policy_frame(
    *,
    transcript: str,
    session_state: dict | None = None,
    campaign: dict | None = None,
    quality_gate: dict | None = None,
    contextual_semantics: dict | None = None,
    pragmatic_move: dict | None = None,
) -> dict[str, Any]:
    detection = detect_universal_asr_garble(
        transcript=transcript,
        quality_gate=quality_gate,
        session_state=session_state,
        campaign=campaign,
    )
    if detection.get("applied"):
        buyer_move_id = "asr_garbled_or_low_confidence"
        response_shape_id = "ask_repeat_for_asr_garble"
    else:
        buyer_move_id = _buyer_move_from_context(contextual_semantics, transcript)
        response_shape_id = (
            knowledge.buyer_move(buyer_move_id).get("expected_response_shape_id")
            or "confusion_explain_plainly"
        )

    move = knowledge.buyer_move(buyer_move_id)
    shape = knowledge.response_shape(response_shape_id)
    enforcement_enabled = should_enforce_universal_asr_repair(detection=detection, campaign=campaign)
    enforcement_reason = _enforcement_reason(enforcement_enabled, detection, campaign)
    allowed_call_controls = list(shape.get("allowed_call_control") or move.get("default_call_control_allowed") or ["continue-call"])
    memory_policy = str(move.get("memory_policy") or "preserve_confirmed_and_cleared_gaps")

    return {
        "schema_version": SCHEMA_VERSION,
        "knowledge_id": knowledge.KNOWLEDGE_ID,
        "buyer_move_id": buyer_move_id,
        "response_shape_id": response_shape_id,
        "conversation_stage": _conversation_stage(
            transcript=transcript,
            session_state=session_state,
            contextual_semantics=contextual_semantics,
            detection=detection,
        ),
        "allowed_fact_slots": list(shape.get("allowed_fact_slots") or []),
        "forbidden_patterns": list(shape.get("forbidden_patterns") or move.get("must_not_do") or []),
        "allowed_call_controls": allowed_call_controls,
        "memory_policy": memory_policy,
        "appointment_pressure_level": str(shape.get("appointment_pressure_level") or "none"),
        "direct_question_required": bool(move.get("must_answer_direct_question")),
        "asr_repair_required": bool(detection.get("applied")),
        "should_preserve_confirmed_gaps": "preserve" in memory_policy or bool(detection.get("applied")),
        "should_preserve_cleared_gaps": "preserve" in memory_policy or bool(detection.get("applied")),
        "one_next_action_only": True,
        "enforcement_enabled": enforcement_enabled,
        "enforcement_reason": enforcement_reason,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "opens_prod_102": False,
        "detection": detection,
        "pragmatic_move_id": (pragmatic_move or {}).get("move_id"),
    }


def _enforcement_reason(enforcement_enabled: bool, detection: dict, campaign: dict | None) -> str:
    if enforcement_enabled:
        return str(detection.get("reason") or "generic_asr_repair")
    if not detection.get("applied"):
        return "no_asr_repair_required"
    if not _is_generic_campaign(campaign):
        return "routesignal_or_non_generic_enforcement_disabled"
    return "enforcement_disabled"


def universal_asr_repair_continuity(frame: dict[str, Any]) -> dict[str, Any]:
    return {
        "applied": True,
        "reason": "asr_fragment_repair",
        "action_id": "repair_asr_fragment",
        "dialogue_focus": "repair",
        "candidate_response": REPAIR_RESPONSE,
        "universal_policy_frame": dict(frame),
    }
