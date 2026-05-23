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

DIRECT_PRODUCT_VALUE_MOVES = {
    "product_detail_question",
    "what_problem_do_you_solve",
    "why_should_i_care",
    "what_makes_you_different",
    "who_is_this_for",
    "is_this_worth_my_time",
}

OBJECTION_MOVES = {
    "price_or_budget_objection",
    "already_has_provider",
    "no_authority_or_needs_approval",
    "wants_proof_or_case_study",
    "timing_objection",
    "no_clear_need",
    "too_busy_now",
}

TIME_PRESSURE_MOVES = {"time_constrained_permission"}

TRUST_IDENTITY_PRIVACY_MOVES = {
    "who_are_you",
    "are_you_ai_or_robot",
    "how_did_you_get_my_number",
    "is_this_recorded",
    "privacy_data_use_question",
    "permission_to_continue_denied",
    "stop_request",
}

CHALLENGE_REPAIR_MOVES = {
    "confusion_not_clear",
    "why_are_you_asking",
    "already_answered_challenge",
    "contradiction_challenge",
    "repeat_or_rephrase_request",
    "repeat_last_answer",
}

REGULATED_SCOPE_BOUNDARY_MOVES = {
    "scope_limit_question",
    "regulated_claim_question",
}

TERMINAL_RESPONSE_SHAPE_MOVES = {"permission_to_continue_denied", "stop_request"}


def _contains_any(normalized: str, phrases: set[str] | list[str] | tuple[str, ...]) -> bool:
    return any(phrase in normalized for phrase in phrases)


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


def _campaign_text(campaign: dict | None, *keys: str, default: str = "") -> str:
    if not isinstance(campaign, dict):
        return default
    for key in keys:
        value = campaign.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _nested_campaign_text(campaign: dict | None, parent: str, key: str, default: str = "") -> str:
    value = (campaign or {}).get(parent) if isinstance(campaign, dict) else None
    if isinstance(value, dict) and isinstance(value.get(key), str) and value.get(key, "").strip():
        return str(value.get(key)).strip()
    return default


def _campaign_product_name(campaign: dict | None) -> str:
    return _campaign_text(campaign, "product_or_offer_name", "product_name", default="this review")


def _campaign_appointment_target(campaign: dict | None) -> str:
    return _campaign_text(campaign, "appointment_target", "scheduling_goal", default="short review")


def _campaign_owner(campaign: dict | None) -> str:
    return _campaign_text(campaign, "human_followup_owner", "human_handoff_role", default="a human specialist")


def _role_phrase(role: str) -> str:
    cleaned = _plain_phrase(role).strip()
    if not cleaned:
        return "the specialist"
    if cleaned.lower().startswith(("a ", "an ", "the ")):
        return cleaned
    return f"the {cleaned}"


def _campaign_buyer_role(campaign: dict | None) -> str:
    return _nested_campaign_text(campaign, "target_account_context", "buyer_role", "the person responsible for this area")


def _campaign_client_name(campaign: dict | None) -> str:
    return _campaign_text(campaign, "client_name", default=_campaign_product_name(campaign))


def _campaign_caller_name(campaign: dict | None) -> str:
    identity = (campaign or {}).get("caller_identity") if isinstance(campaign, dict) else None
    if isinstance(identity, dict):
        name = identity.get("representative_name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return "Maya"


def _is_routesignal_campaign(campaign: dict | None) -> bool:
    campaign_id = _campaign_text(campaign, "campaign_id")
    product = _campaign_product_name(campaign).lower()
    return campaign_id in ROUTESIGNAL_CAMPAIGN_IDS or product.startswith("routesignal")


def _string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    return [str(value).strip()] if str(value or "").strip() else []


def _gap_records(campaign: dict | None) -> list[dict[str, Any]]:
    if not isinstance(campaign, dict) or not isinstance(campaign.get("diagnostic_gaps"), dict):
        return []
    gaps = campaign.get("diagnostic_gaps") or {}
    ordered_ids = _string_items(campaign.get("gap_order") or campaign.get("core_diagnostic_gaps"))
    records: list[dict[str, Any]] = []
    for gap_id in ordered_ids:
        value = gaps.get(gap_id)
        if isinstance(value, dict):
            records.append(value)
    if not records:
        records = [value for value in gaps.values() if isinstance(value, dict)]
    return records


def _primary_gap_label(campaign: dict | None) -> str:
    records = _gap_records(campaign)
    if records:
        label = str(records[0].get("label") or records[0].get("campaign_gap_id") or "").strip()
        if label:
            return label
    if _is_routesignal_campaign(campaign):
        return "follow-up gap"
    return "the relevant issue"


def _plain_phrase(value: str) -> str:
    phrase = " ".join(str(value or "").replace("_", " ").split()).strip(" .")
    return phrase or "the relevant issue"


def _human_gap_phrase(label: str) -> str:
    phrase = _plain_phrase(label).lower()
    replacements = {
        "follow-up gap": "inbound demo follow-up slipping",
        "follow up gap": "inbound demo follow-up slipping",
        "premium or budget": "premium pressure",
        "visibility gap": "visibility issue",
    }
    if phrase in replacements:
        return replacements[phrase]
    if phrase.endswith(" gap"):
        return f"{phrase[:-4]} issue"
    return phrase


def _primary_gap_phrase(campaign: dict | None) -> str:
    return _human_gap_phrase(_primary_gap_label(campaign))


def _secondary_gap_phrase(campaign: dict | None) -> str:
    records = _gap_records(campaign)
    if len(records) < 2:
        return ""
    label = str(records[1].get("label") or records[1].get("campaign_gap_id") or "").strip()
    phrase = _human_gap_phrase(label)
    return "" if phrase == _primary_gap_phrase(campaign) else phrase


def _with_indefinite_article(phrase: str) -> str:
    cleaned = _plain_phrase(phrase)
    article = "an" if cleaned[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
    return f"{article} {cleaned}"


def _area_phrase(phrase: str) -> str:
    cleaned = _plain_phrase(phrase)
    if cleaned.startswith("the "):
        return cleaned
    if cleaned.endswith("issue") or cleaned.endswith("need"):
        return f"the {cleaned}"
    return cleaned


def _short_gap_pair(campaign: dict | None) -> str:
    labels: list[str] = []
    for record in _gap_records(campaign)[:2]:
        label = str(record.get("label") or record.get("campaign_gap_id") or "").strip()
        if label:
            labels.append(_human_gap_phrase(label))
    if len(labels) >= 2:
        return f"{labels[0]} or {labels[1]}"
    return _primary_gap_phrase(campaign)


def _primary_gap_review_focus(campaign: dict | None) -> str:
    records = _gap_records(campaign)
    if records:
        focus = str(records[0].get("review_focus") or records[0].get("definition") or "").strip()
        if focus:
            return _plain_phrase(focus)
    return _primary_gap_phrase(campaign)


def _allowed_claim_summary(campaign: dict | None) -> str:
    claims = _string_items((campaign or {}).get("allowed_claims") if isinstance(campaign, dict) else None)
    if claims:
        return claims[0].rstrip(".")
    return f"can check whether {_primary_gap_phrase(campaign)} is worth {_with_indefinite_article(_campaign_appointment_target(campaign))}"


def _approved_scope_response(campaign: dict | None) -> str:
    claim = _allowed_claim_summary(campaign)
    lowered = claim.lower()
    if lowered.startswith("can "):
        action = claim[4:].strip()
        gerund = _gerund_action(action)
        return f"I can speak only to this limited scope: {gerund}. Anything beyond that needs a human follow-up."
    return f"I can speak only to this limited scope: {claim}. Anything beyond that needs a human follow-up."


def _gerund_action(action: str) -> str:
    cleaned = _plain_phrase(action)
    for verb, gerund in (
        ("collect ", "collecting "),
        ("discuss ", "discussing "),
        ("arrange ", "arranging "),
        ("check ", "checking "),
        ("schedule ", "scheduling "),
        ("capture ", "capturing "),
    ):
        if cleaned.lower().startswith(verb):
            return gerund + cleaned[len(verb):]
    return cleaned


def _time_pressure_response(campaign: dict | None) -> str:
    primary_gap = _primary_gap_phrase(campaign)
    secondary_gap = _secondary_gap_phrase(campaign)
    if primary_gap == "inbound demo follow-up slipping":
        question = "is inbound demo follow-up slipping right now?"
    elif primary_gap.endswith("issue"):
        question = f"is {_area_phrase(primary_gap)} causing trouble right now?"
    elif primary_gap.endswith("need"):
        question = f"is {_area_phrase(primary_gap)} active right now?"
    else:
        question = f"is {primary_gap} causing any issue right now?"
    if secondary_gap:
        return (
            f"Sure, one quick check: {question} "
            f"If it is really {secondary_gap}, say that."
        )
    return f"Sure, one quick check: {question}"


def _campaign_purpose_phrase(campaign: dict | None) -> str:
    if _is_routesignal_campaign(campaign):
        return "inbound demo follow-up"
    return f"a short human review around {_area_phrase(_primary_gap_phrase(campaign))}"


def _memory_from_session(session_state: dict | None) -> dict[str, Any]:
    if not isinstance(session_state, dict):
        return {}
    memory = session_state.get("conversation_memory")
    if isinstance(memory, dict):
        return memory
    turns = _turns(session_state)
    for turn in reversed(turns):
        memory = turn.get("conversation_memory") if isinstance(turn, dict) else None
        if isinstance(memory, dict):
            return memory
    return {}


def _gap_phrase_for_id(campaign: dict | None, gap_id: str) -> str:
    gaps = (campaign or {}).get("diagnostic_gaps") if isinstance(campaign, dict) else None
    value = gaps.get(gap_id) if isinstance(gaps, dict) else None
    if isinstance(value, dict):
        label = str(value.get("label") or value.get("campaign_gap_id") or gap_id).strip()
        return _human_gap_phrase(label)
    return _human_gap_phrase(gap_id)


def _active_gap_phrase(campaign: dict | None, session_state: dict | None) -> str:
    memory = _memory_from_session(session_state)
    confirmed = _string_items(memory.get("confirmed_gaps"))
    if confirmed:
        return _gap_phrase_for_id(campaign, confirmed[0])
    return _primary_gap_phrase(campaign)


def _response_shape_category(buyer_move_id: str) -> str | None:
    if buyer_move_id in DIRECT_PRODUCT_VALUE_MOVES:
        return "direct_product_value_questions"
    if buyer_move_id in OBJECTION_MOVES:
        return "objections"
    if buyer_move_id in TIME_PRESSURE_MOVES:
        return "permission_time_pressure"
    if buyer_move_id in TRUST_IDENTITY_PRIVACY_MOVES:
        return "trust_identity_privacy_consent"
    if buyer_move_id in CHALLENGE_REPAIR_MOVES:
        return "confusion_challenge_repair"
    if buyer_move_id in REGULATED_SCOPE_BOUNDARY_MOVES:
        return "scope_regulated_claim_boundaries"
    return None


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


def _recognition(
    buyer_move_id: str,
    *,
    reason: str,
    confidence: str,
    category: str,
) -> dict[str, Any]:
    move = knowledge.buyer_move(buyer_move_id)
    return {
        "buyer_move_id": buyer_move_id,
        "recognition_reason": reason,
        "recognition_confidence": confidence,
        "buyer_move_category": category,
        "direct_question_required": bool(move.get("must_answer_direct_question")),
    }


def classify_universal_buyer_move_from_transcript(
    *,
    transcript: str,
    normalized_transcript: str | None = None,
    previous_question_type: str | None = None,
    contextual_semantics: dict | None = None,
    pragmatic_move: dict | None = None,
    campaign: dict | None = None,
    session_state: dict | None = None,
    asr_detection: dict | None = None,
) -> dict[str, Any]:
    normalized = normalized_transcript if normalized_transcript is not None else normalize_transcript(transcript)
    detection = asr_detection or detect_universal_asr_garble(
        transcript=transcript,
        session_state=session_state,
        campaign=campaign,
    )
    if detection.get("applied"):
        return _recognition(
            "asr_garbled_or_low_confidence",
            reason=str(detection.get("reason") or "asr_repair_required"),
            confidence="high",
            category="asr_repair",
        )

    if _contains_any(
        normalized,
        {
            "stop calling",
            "do not call",
            "don t call",
            "no thanks",
            "not interested",
            "leave me alone",
        },
    ):
        return _recognition(
            "stop_request",
            reason="explicit_stop_or_refusal_phrase",
            confidence="high",
            category="trust_identity_privacy_consent",
        )
    if _contains_any(
        normalized,
        {
            "do not want to continue",
            "don t want to continue",
            "dont want to continue",
            "do not continue",
        },
    ):
        return _recognition(
            "permission_to_continue_denied",
            reason="permission_to_continue_denied_phrase",
            confidence="high",
            category="trust_identity_privacy_consent",
        )

    if normalized in {"who are you", "who is calling", "who am i speaking with"} or normalized.startswith("who are you "):
        return _recognition("who_are_you", reason="identity_question_phrase", confidence="high", category="identity_trust_privacy")
    if _contains_any(normalized, {"are you a robot", "are you ai", "are you an ai", "is this automated"}):
        return _recognition("are_you_ai_or_robot", reason="ai_or_robot_question_phrase", confidence="high", category="identity_trust_privacy")
    if _contains_any(
        normalized,
        {
            "how did you get my number",
            "why do you have my number",
            "how did you get my contact",
            "why do you have my contact",
        },
    ):
        return _recognition(
            "how_did_you_get_my_number",
            reason="contact_source_question_phrase",
            confidence="high",
            category="identity_trust_privacy",
        )
    if _contains_any(normalized, {"is this recorded", "are you recording", "is this monitored"}):
        return _recognition("is_this_recorded", reason="recording_policy_question_phrase", confidence="high", category="identity_trust_privacy")
    if _contains_any(
        normalized,
        {
            "what do you do with my data",
            "what do you do with my information",
            "how is my data used",
            "how do you use my data",
            "privacy",
        },
    ):
        return _recognition("privacy_data_use_question", reason="privacy_data_question_phrase", confidence="high", category="identity_trust_privacy")

    if _contains_any(
        normalized,
        {
            "cannot give me details",
            "can t give me details",
            "cant give me details",
            "cannot give details",
            "only a licensed",
            "only licensed",
            "not give me details",
        },
    ):
        return _recognition("scope_limit_question", reason="scope_limit_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(
        normalized,
        {
            "guarantee",
            "promise the result",
            "promise result",
            "am i covered",
            "exact price",
            "exact quote",
            "refund",
            "roi guarantee",
            "security guarantee",
            "coverage guarantee",
        },
    ):
        return _recognition(
            "regulated_claim_question",
            reason="regulated_or_exact_claim_question_phrase",
            confidence="high",
            category="product_value_scope",
        )
    if _contains_any(normalized, {"what does your product do", "what is your product", "what your product do"}):
        return _recognition("product_detail_question", reason="product_detail_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"what problem do you solve", "what do you solve", "what do you help with", "what is this for"}):
        return _recognition("what_problem_do_you_solve", reason="problem_solved_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"why should i care", "why would i care", "why care"}):
        return _recognition("why_should_i_care", reason="why_should_i_care_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"what makes you different", "what is different", "why are you different"}):
        return _recognition("what_makes_you_different", reason="differentiation_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"who is this for", "who uses this", "is this for me"}):
        return _recognition("who_is_this_for", reason="target_buyer_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"is this worth my time", "worth my time", "why stay on the phone"}):
        return _recognition("is_this_worth_my_time", reason="time_value_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"what result can i expect", "what will this do for me", "what improvement"}):
        return _recognition("what_result_can_i_expect", reason="expected_result_question_phrase", confidence="high", category="product_value_scope")
    if _contains_any(normalized, {"does this apply to us", "is this relevant for us", "would this matter here"}):
        return _recognition("does_this_apply_to_us", reason="relevance_question_phrase", confidence="high", category="product_value_scope")

    if _contains_any(normalized, {"already have a provider", "already have provider", "use someone else", "we use someone else", "covered by another"}):
        return _recognition("already_has_provider", reason="existing_provider_objection_phrase", confidence="high", category="objections")
    if _contains_any(normalized, {"too expensive", "no budget", "not in budget", "cost too much", "how much does it cost", "what does it cost"}):
        return _recognition("price_or_budget_objection", reason="price_or_budget_objection_phrase", confidence="high", category="objections")
    if _contains_any(normalized, {"ask my manager", "ask manager", "need approval", "not my decision", "legal has to approve"}):
        return _recognition(
            "no_authority_or_needs_approval",
            reason="authority_or_approval_objection_phrase",
            confidence="high",
            category="objections",
        )
    if _contains_any(normalized, {"send me proof", "show me proof", "case study", "case studies", "send proof"}):
        return _recognition("wants_proof_or_case_study", reason="proof_request_phrase", confidence="high", category="objections")
    if _contains_any(normalized, {"not this week", "not this month", "not this quarter", "bad timing"}):
        return _recognition("timing_objection", reason="timing_objection_phrase", confidence="high", category="objections")
    if _contains_any(normalized, {"do not see the need", "don t see the need", "dont see the need", "no clear need", "not seeing the need"}):
        return _recognition("no_clear_need", reason="no_clear_need_objection_phrase", confidence="high", category="objections")
    if _contains_any(normalized, {"too busy", "we are busy", "in a meeting", "not a good time"}):
        return _recognition("too_busy_now", reason="too_busy_objection_phrase", confidence="high", category="objections")

    if _contains_any(normalized, {"send me details", "send details", "send me information", "send me info"}):
        return _recognition("send_info_request", reason="send_info_request_phrase", confidence="high", category="appointment_callback_send_info")
    if _contains_any(normalized, {"call me next week", "call me later", "call back", "callback request", "call me back"}):
        return _recognition("callback_request", reason="callback_request_phrase", confidence="high", category="appointment_callback_send_info")
    if _contains_any(normalized, {"available times", "send available times", "what times are available"}):
        return _recognition("buyer_requests_available_times", reason="available_times_request_phrase", confidence="high", category="appointment_callback_send_info")
    if _contains_any(normalized, {"email first", "need email first", "send email first"}):
        return _recognition("buyer_wants_email_before_booking", reason="email_before_booking_phrase", confidence="high", category="appointment_callback_send_info")
    if _contains_any(normalized, {"not now maybe later", "maybe later", "later maybe"}):
        return _recognition("buyer_defers_to_later", reason="defer_to_later_phrase", confidence="high", category="appointment_callback_send_info")
    if _looks_like_time(normalized) and _contains_any(normalized, {"works", "work", "is good", "would be good"}):
        return _recognition("callback_time_provided", reason="time_phrase_with_acceptance", confidence="high", category="appointment_callback_send_info")
    if "that would be good" in normalized:
        return _recognition("appointment_interest", reason="clean_positive_after_progression", confidence="medium", category="appointment_callback_send_info")

    if _contains_any(normalized, {"slow down", "too fast", "speak faster", "speak slower"}):
        return _recognition("slow_down_or_speak_faster", reason="speech_rate_request_phrase", confidence="high", category="social_conversation_management")
    if _contains_any(normalized, {"say that again", "repeat that", "say again", "can you repeat"}):
        return _recognition("repeat_last_answer", reason="repeat_last_answer_phrase", confidence="high", category="social_conversation_management")
    if _contains_any(normalized, {"don t speak english", "dont speak english", "do not speak english", "english well", "different language"}):
        return _recognition("language_mismatch", reason="language_mismatch_phrase", confidence="high", category="social_conversation_management")
    if _contains_any(normalized, {"not how you say my name", "that s not how you say my name", "you said my name wrong", "call me"}):
        return _recognition(
            "pronunciation_or_name_correction",
            reason="name_or_pronunciation_correction_phrase",
            confidence="high",
            category="social_conversation_management",
        )
    if _contains_any(normalized, {"haha", "ha ha", "lol", "how are you", "nice weather"}):
        return _recognition("small_talk", reason="small_talk_or_backchannel_phrase", confidence="medium", category="social_conversation_management")
    if _contains_any(normalized, {"annoying", "frustrated", "frustrating", "you re annoying", "you are annoying"}):
        return _recognition("emotional_frustration", reason="frustration_phrase", confidence="high", category="social_conversation_management")

    if _contains_any(normalized, {"what do you mean", "i do not understand", "i don t understand", "dont understand"}):
        return _recognition("confusion_not_clear", reason="confusion_or_clarification_phrase", confidence="high", category="confusion_challenge_repair")
    if "why" in normalized and "asking" in normalized:
        return _recognition("why_are_you_asking", reason="why_are_you_asking_phrase", confidence="high", category="confusion_challenge_repair")
    if _contains_any(normalized, {"didn t answer", "did not answer", "you didn t answer", "you did not answer"}):
        return _recognition(
            "already_answered_challenge",
            reason="did_not_answer_challenge_phrase",
            confidence="high",
            category="confusion_challenge_repair",
        )
    if _contains_any(normalized, {"already told you", "i told you", "keep asking the same"}):
        return _recognition(
            "already_answered_challenge",
            reason="already_answered_challenge_phrase",
            confidence="high",
            category="confusion_challenge_repair",
        )
    if _contains_any(normalized, {"not the right person why ask", "not the right contact why ask", "why ask"}):
        return _recognition(
            "contradiction_challenge",
            reason="role_contradiction_challenge_phrase",
            confidence="high",
            category="confusion_challenge_repair",
        )

    if normalized.startswith("maybe ") or _contains_any(normalized, {"maybe coverage", "maybe integration"}):
        return _recognition("tentative_gap_interest", reason="tentative_gap_phrase", confidence="high", category="pain_tentative_pain")
    if _contains_any(normalized, {"is a problem", "is the problem", "usually pretty long", "we need service", "is unclear", "is the issue"}):
        return _recognition("pain_confirmed", reason="clean_pain_phrase", confidence="medium", category="pain_tentative_pain")

    context_move = _buyer_move_from_context(contextual_semantics, transcript)
    if context_move != "confusion_not_clear":
        category = {
            "pain_confirmed": "pain_tentative_pain",
            "no_pain_clear": "pain_tentative_pain",
            "callback_time_provided": "appointment_callback_send_info",
            "permission_acknowledgement": "permission_time_pressure",
            "why_are_you_asking": "confusion_challenge_repair",
            "product_detail_question": "product_value_scope",
        }.get(context_move, "contextual_semantics")
        return _recognition(context_move, reason="contextual_semantics_mapping", confidence="medium", category=category)

    if normalized in CLEAN_ACKNOWLEDGEMENTS:
        return _recognition(
            "permission_acknowledgement",
            reason="clean_acknowledgement_phrase",
            confidence="high",
            category="permission_time_pressure",
        )
    if _contains_any(normalized, {"make it quick", "short minute", "quick minute", "keep it quick"}):
        return _recognition(
            "time_constrained_permission",
            reason="time_constrained_permission_phrase",
            confidence="high",
            category="permission_time_pressure",
        )

    return _recognition("confusion_not_clear", reason="fallback_no_universal_buyer_move_match", confidence="low", category="fallback")


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
    recognition = classify_universal_buyer_move_from_transcript(
        transcript=transcript,
        normalized_transcript=detection.get("normalized_transcript"),
        previous_question_type=detection.get("previous_question_type"),
        contextual_semantics=contextual_semantics,
        pragmatic_move=pragmatic_move,
        campaign=campaign,
        session_state=session_state,
        asr_detection=detection,
    )
    buyer_move_id = str(recognition.get("buyer_move_id") or "confusion_not_clear")
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
        "recognition_reason": recognition.get("recognition_reason"),
        "recognition_confidence": recognition.get("recognition_confidence"),
        "buyer_move_category": recognition.get("buyer_move_category"),
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
        "direct_question_required": bool(recognition.get("direct_question_required") or move.get("must_answer_direct_question")),
        "asr_repair_required": bool(detection.get("applied")),
        "should_preserve_confirmed_gaps": "preserve" in memory_policy or bool(detection.get("applied")),
        "should_preserve_cleared_gaps": "preserve" in memory_policy or bool(detection.get("applied")),
        "one_next_action_only": True,
        "enforcement_enabled": enforcement_enabled,
        "enforcement_reason": enforcement_reason,
        "response_shape_enforcement_enabled": False,
        "response_shape_enforcement_reason": "not_evaluated",
        "response_shape_enforced_category": None,
        "response_shape_candidate_source": None,
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


def should_enforce_response_shape(
    frame: dict[str, Any],
    candidate_response: str | None = None,
    campaign: dict | None = None,
    context: dict | None = None,
) -> bool:
    del candidate_response
    buyer_move_id = str((frame or {}).get("buyer_move_id") or "")
    if _response_shape_category(buyer_move_id) is None:
        return False
    if (frame or {}).get("asr_repair_required"):
        return False
    if (frame or {}).get("recognition_confidence") != "high":
        return False
    if buyer_move_id == "confusion_not_clear" and _is_routesignal_campaign(campaign):
        normalized = str(((frame or {}).get("detection") or {}).get("normalized_transcript") or "")
        if str((frame or {}).get("pragmatic_move_id") or "") == "term_meaning_question" or _contains_any(
            normalized,
            {
                "what do you mean by",
                "what this means for us",
                "i didn't ask a question",
                "i didn t ask a question",
                "i don't know what",
                "i don t know what",
            },
        ):
            return False
    if buyer_move_id == "price_or_budget_objection" and not _is_generic_campaign(campaign):
        normalized = str(((frame or {}).get("detection") or {}).get("normalized_transcript") or "")
        explicit_objection = _contains_any(normalized, {"too expensive", "no budget", "not in budget", "cost too much"})
        direct_price_question = _contains_any(normalized, {"how much", "what does it cost", "what is the price", "talk about the price"})
        if direct_price_question and not explicit_objection:
            return False
    if buyer_move_id == "is_this_worth_my_time" and not _is_generic_campaign(campaign):
        turns = _turns((context or {}).get("session_state") if isinstance(context, dict) else None)
        previous_focus = str(((turns[-1].get("continuity") or {}) if turns else {}).get("dialogue_focus") or "")
        if previous_focus in {"price", "effort"}:
            return False
    return True


def render_universal_response_outline(
    frame: dict[str, Any],
    campaign: dict | None,
    session_state: dict | None = None,
) -> str:
    buyer_move_id = str((frame or {}).get("buyer_move_id") or "")
    normalized = str(((frame or {}).get("detection") or {}).get("normalized_transcript") or "")
    owner = _campaign_owner(campaign)
    buyer_role = _campaign_buyer_role(campaign)
    primary_gap = _primary_gap_phrase(campaign)
    active_gap = _active_gap_phrase(campaign, session_state)
    client = _campaign_client_name(campaign)
    caller = _campaign_caller_name(campaign)
    owner_role = _role_phrase(owner)

    if buyer_move_id == "time_constrained_permission":
        return _time_pressure_response(campaign)

    if buyer_move_id == "product_detail_question":
        if _is_routesignal_campaign(campaign):
            return (
                "RouteSignal helps teams keep inbound demo follow-up from slipping through ownership, reminders, "
                "or handoffs. The quick check is whether that problem exists on your side."
            )
        return (
            f"This call is only to check whether a short human review is useful around {_area_phrase(primary_gap)}. "
            "The quick question is whether that area is causing friction now."
        )
    if buyer_move_id == "what_problem_do_you_solve":
        return f"Mainly {primary_gap}. If that is not happening, there is no reason to push a review."
    if buyer_move_id == "why_should_i_care":
        return f"Only if {primary_gap} is costing time, money, risk, or follow-up quality. If it is not, we can stop here."
    if buyer_move_id == "what_makes_you_different":
        return _approved_scope_response(campaign)
    if buyer_move_id == "who_is_this_for":
        return f"It is for {buyer_role}. If that is not you, I can stop or note the right person."
    if buyer_move_id == "is_this_worth_my_time":
        return f"Only if {primary_gap} is real enough to justify a short review. If not, no pressure."

    if buyer_move_id == "who_are_you":
        return f"I'm {caller} calling on behalf of {client} about {_campaign_purpose_phrase(campaign)}."
    if buyer_move_id == "are_you_ai_or_robot":
        return f"Yes, I'm an AI voice agent calling for {client}. I can keep this short or stop here."
    if buyer_move_id == "how_did_you_get_my_number":
        return "I do not have a reliable source note for that in this call, so I will not guess. I can stop here."
    if buyer_move_id == "is_this_recorded":
        return "I do not have a verified recording notice to give here. I can continue only with the call purpose, or stop."
    if buyer_move_id == "privacy_data_use_question":
        return "I can only use what you say here to handle this call flow. I will not ask for sensitive personal details."
    if buyer_move_id in TERMINAL_RESPONSE_SHAPE_MOVES:
        return "Understood. I'll stop here. Goodbye."

    if buyer_move_id == "confusion_not_clear":
        return f"I mean whether {_area_phrase(active_gap)} is actually happening. If not, there is no reason to continue."
    if buyer_move_id == "why_are_you_asking":
        return (
            f"Fair question. I'm asking because {owner_role} can review {_area_phrase(active_gap)} "
            "if it is worth your time, not to collect extra details."
        )
    if buyer_move_id == "already_answered_challenge":
        return f"You're right, you already answered that. I'll use {_area_phrase(active_gap)} and not ask it again."
    if buyer_move_id == "contradiction_challenge":
        return f"Fair point. I can ask basic fit questions, but detailed advice belongs with {owner_role}."
    if buyer_move_id in {"repeat_or_rephrase_request", "repeat_last_answer"}:
        return f"Sure. The short version: this call checks whether {_area_phrase(active_gap)} is worth a short human review."

    if buyer_move_id == "scope_limit_question":
        return (
            f"Correct. I can explain the purpose of the call, but detailed product or policy advice should come from {owner_role}. "
            f"Since you mentioned {_area_phrase(active_gap)}, that is the basic focus; I can keep it there or stop."
        )
    if buyer_move_id == "regulated_claim_question":
        if "guarantee" in normalized:
            return f"No, I cannot guarantee that on this call. That depends on details {owner_role} would need to review."
        if "exact price" in normalized or "exact quote" in normalized:
            return f"I cannot give an exact price on this call. That depends on details {owner_role} would need to review."
        if "covered" in normalized or "coverage" in normalized:
            return f"I cannot confirm coverage on this call. {owner_role} would need to review the details."
        if "promise" in normalized:
            return "No, I cannot promise a result. I can only check whether a review is worth setting up."
        return f"I cannot confirm that on this call. {owner} would need to review the details."

    if buyer_move_id == "already_has_provider":
        return (
            "Understood. If your current provider already handles this cleanly, there is no reason to change. "
            "The only useful check is whether anything still slips through."
        )
    if buyer_move_id == "price_or_budget_objection":
        return (
            "Fair. Budget matters. I cannot promise savings here; the only useful question is whether the problem "
            "costs enough to justify a short review."
        )
    if buyer_move_id == "no_authority_or_needs_approval":
        return (
            "Understood. Then the useful next step is not to sell you. It is either a short summary for the "
            "decision-maker or the right person's contact."
        )
    if buyer_move_id == "wants_proof_or_case_study":
        return (
            "Fair. Proof needs to come from approved material or a human follow-up. I can note that request."
        )
    if buyer_move_id == "timing_objection":
        return "Understood. Timing is not right this week. We can leave it here or note a later callback."
    if buyer_move_id == "no_clear_need":
        return "Understood. If there is no need, I will not push. We can stop here."
    if buyer_move_id == "too_busy_now":
        return "No problem. I will not drag this out. We can stop here or leave it for another time."

    return "I hear you. I can keep this to one relevance check or leave it there."


def universal_response_shape_continuity(
    frame: dict[str, Any],
    campaign: dict | None,
    session_state: dict | None = None,
) -> dict[str, Any] | None:
    if not should_enforce_response_shape(frame, campaign=campaign, context={"session_state": session_state}):
        return None
    buyer_move_id = str((frame or {}).get("buyer_move_id") or "")
    category = _response_shape_category(buyer_move_id) or "universal_response_shape"
    action_id = "end_call_stop_request" if buyer_move_id in TERMINAL_RESPONSE_SHAPE_MOVES else "continue_with_session_policy"
    enforced_frame = dict(frame)
    enforced_frame.update(
        {
            "response_shape_enforcement_enabled": True,
            "response_shape_enforcement_reason": f"{category}_high_confidence",
            "response_shape_enforced_category": category,
            "response_shape_candidate_source": "universal_response_shape",
        }
    )
    return {
        "applied": True,
        "reason": "universal_response_shape_enforced",
        "action_id": action_id,
        "dialogue_focus": category,
        "candidate_response": render_universal_response_outline(enforced_frame, campaign, session_state),
        "universal_policy_frame": enforced_frame,
    }
