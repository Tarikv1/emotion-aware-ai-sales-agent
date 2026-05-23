from __future__ import annotations

import re
from typing import Any

from runtime.core import campaign_playbook_adapter
from runtime.core import live_voice_session_policy as session_policy
from runtime.core import universal_sales_conversation_knowledge as knowledge
from runtime.speech.asr_quality_gate import normalize_transcript


POLICY_RUNTIME_ID = "UNIVERSAL-CONVERSATION-POLICY-RUNTIME-001"
SCHEMA_VERSION = 1
REPAIR_RESPONSE = "I may have misheard that. Could you repeat it briefly?"
REPEATED_REPAIR_RESPONSE = "I still may not have caught that. Could you repeat it in a few words?"

ROUTESIGNAL_CAMPAIGN_IDS = {
    "live-demo-001-routesignal",
    "campaign-prod-005-b2b-software",
}

KNOWN_NONSENSE_PHRASES = {
    "play a double be good",
    "yadav would be good",
}

UNIVERSAL_ASR_REPAIR_REASONS = {
    "asr_quality_rejected",
    "domain_near_miss",
    "empty_or_fragment",
    "high_risk_appointment_time_mismatch",
    "known_phonetic_nonsense",
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

PAIN_PROGRESSION_MOVES = {
    "permission_acknowledgement",
    "pain_confirmed",
    "tentative_gap_interest",
    "implication_confirmed",
    "implication_weak_or_denied",
    "implication_unclear",
}

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

SOCIAL_CONVERSATION_MANAGEMENT_MOVES = {
    "slow_down_or_speak_faster",
    "repeat_last_answer",
    "repeat_or_rephrase_request",
    "language_mismatch",
    "pronunciation_or_name_correction",
    "small_talk",
    "silence_or_backchannel",
    "emotional_frustration",
    "abusive_or_hostile_buyer",
}

RAPPORT_RELEVANCE_BRIDGE_MOVES = {
    "busy_or_distracted",
    "serious_hardship_bad_timing",
    "financial_stress_context",
    "prior_bad_experience_context",
    "stakeholder_or_right_person_context",
    "sarcasm_or_joking_context",
    "emotional_venting_context",
    "irrelevant_off_topic_context",
    "sensitive_personal_data_disclosure",
    "home_life_interruption",
    "workplace_interruption",
}

NEXT_STEP_DISCIPLINE_MOVES = {
    "send_info_request",
    "callback_request",
    "buyer_requests_available_times",
    "buyer_wants_email_before_booking",
    "buyer_defers_to_later",
    "appointment_interest",
    "callback_time_provided",
}

TERMINAL_RESPONSE_SHAPE_MOVES = {"permission_to_continue_denied", "stop_request"}
TERMINAL_RAPPORT_MOVES = {"serious_hardship_bad_timing", "sensitive_personal_data_disclosure"}


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


def _previous_response_asked_next_step_timing(session_state: dict | None) -> bool:
    previous = normalize_transcript(_previous_agent_response(session_state))
    return _contains_any(
        previous,
        {
            "callback window",
            "time window",
            "day or time",
            "what time",
            "which day",
            "preferred window",
            "later window",
        },
    )


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
    context = campaign.get("campaign_context")
    if isinstance(context, dict):
        for key in keys:
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    resolved = _resolved_campaign_playbook(campaign)
    context = resolved.get("campaign_context") if isinstance(resolved, dict) else None
    if isinstance(context, dict):
        for key in keys:
            value = context.get(key)
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


def _campaign_id(campaign: dict | None) -> str:
    return _campaign_text(campaign, "campaign_id")


def _campaign_vertical(campaign: dict | None) -> str:
    return _campaign_text(campaign, "vertical_id")


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


def _resolved_campaign_playbook(campaign: dict | None) -> dict[str, Any]:
    if not isinstance(campaign, dict):
        return {}
    try:
        playbook = campaign_playbook_adapter.resolve_campaign_playbook(campaign)
    except Exception:
        return {}
    return playbook if isinstance(playbook, dict) else {}


def _string_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item or "").strip()]
    return [str(value).strip()] if str(value or "").strip() else []


def _gap_record_items(campaign: dict | None) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(campaign, dict) or not isinstance(campaign.get("diagnostic_gaps"), dict):
        resolved = _resolved_campaign_playbook(campaign)
        gaps = resolved.get("diagnostic_gaps") if isinstance(resolved, dict) else {}
        ordered_ids = _string_items(resolved.get("gap_order") or resolved.get("core_diagnostic_gaps")) if isinstance(resolved, dict) else []
    else:
        gaps = campaign.get("diagnostic_gaps") or {}
        ordered_ids = _string_items(campaign.get("gap_order") or campaign.get("core_diagnostic_gaps"))
    if not isinstance(gaps, dict):
        return []
    records: list[tuple[str, dict[str, Any]]] = []
    for gap_id in ordered_ids:
        value = gaps.get(gap_id)
        if isinstance(value, dict):
            records.append((str(gap_id), value))
    if not records:
        records = [(str(gap_id), value) for gap_id, value in gaps.items() if isinstance(value, dict)]
    return records


def _gap_records(campaign: dict | None) -> list[dict[str, Any]]:
    return [record for _, record in _gap_record_items(campaign)]


def _gap_text(record: dict[str, Any] | None, *keys: str) -> str:
    if not isinstance(record, dict):
        return ""
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _gap_record_by_id(campaign: dict | None, gap_id: str) -> dict[str, Any]:
    for candidate_id, record in _gap_record_items(campaign):
        if candidate_id == gap_id or str(record.get("campaign_gap_id") or "") == gap_id:
            return record
    return {}


def _gap_customer_phrase(record: dict[str, Any] | None, gap_id: str = "") -> str:
    phrase = _gap_text(record, "customer_facing_phrase", "customer_facing_gap_phrase")
    if phrase:
        return _plain_phrase(phrase).lower()
    label = _gap_text(record, "label", "campaign_gap_id") or gap_id
    return _human_gap_phrase(label)


def _first_gap_customer_phrase(campaign: dict | None) -> str:
    records = _gap_record_items(campaign)
    if records:
        gap_id, record = records[0]
        return _gap_customer_phrase(record, gap_id)
    return "the relevant issue"


def _campaign_primary_customer_issue_phrase(campaign: dict | None) -> str:
    phrase = _campaign_text(campaign, "primary_customer_issue_phrase", "primary_issue_phrase")
    if phrase:
        return _plain_phrase(phrase).lower()
    return _first_gap_customer_phrase(campaign)


def _campaign_short_relevance_question(campaign: dict | None) -> str:
    return _campaign_text(campaign, "short_relevance_question", "rapport_bridge_question", "diagnostic_question_phrase")


def _question_sentence(question: str) -> str:
    cleaned = " ".join(str(question or "").split()).strip()
    if not cleaned:
        return ""
    if cleaned[-1] not in ".?!":
        cleaned = f"{cleaned}?"
    return cleaned


def _lower_initial(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return cleaned
    return cleaned[:1].lower() + cleaned[1:]


def _gap_match_phrases(record: dict[str, Any]) -> list[str]:
    phrases: list[str] = []
    for key in (
        "customer_facing_phrase",
        "customer_facing_gap_phrase",
        "label",
        "campaign_gap_id",
        "evidence_positive",
        "evidence_negative",
    ):
        phrases.extend(_string_items(record.get(key)))
    for phrase in _string_items(record.get("customer_language")):
        if len(normalize_transcript(phrase).split()) > 1:
            phrases.append(phrase)
    return phrases


def _normalized_phrase_in(normalized: str, phrase: str) -> bool:
    cleaned = normalize_transcript(phrase)
    if not cleaned:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(cleaned)}(?![a-z0-9])", normalized) is not None


def _transcript_matches_gap_record(normalized: str, record: dict[str, Any]) -> bool:
    return any(_normalized_phrase_in(normalized, phrase) for phrase in _gap_match_phrases(record))


def _pain_like_unsupported_phrase(normalized: str) -> bool:
    return _contains_any(
        normalized,
        {"is a problem", "is the problem", "usually pretty long", "we need", "is unclear", "is the issue"},
    )


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
    if phrase.endswith(" gap"):
        return f"{phrase[:-4]} issue"
    return phrase


def _primary_gap_phrase(campaign: dict | None) -> str:
    return _campaign_primary_customer_issue_phrase(campaign)


def _secondary_gap_phrase(campaign: dict | None) -> str:
    records = _gap_records(campaign)
    if len(records) < 2:
        return ""
    phrase = _gap_customer_phrase(records[1])
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


def _agreement_verb(phrase: str) -> str:
    cleaned = _plain_phrase(phrase).lower()
    if cleaned.endswith("s") and not cleaned.endswith("ss"):
        return "are"
    return "is"


def _prior_appointment_readiness(session_state: dict | None) -> str:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    best = "none"
    for turn in _turns(session_state):
        frame = turn.get("universal_policy_frame") or ((turn.get("dialogue_manager") or {}).get("universal_policy_frame") or {})
        readiness = str((frame or {}).get("appointment_readiness") or "none")
        if order.get(readiness, 0) > order.get(best, 0):
            best = readiness
    return best


def _short_gap_pair(campaign: dict | None) -> str:
    labels: list[str] = []
    for gap_id, record in _gap_record_items(campaign)[:2]:
        labels.append(_gap_customer_phrase(record, gap_id))
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
        return f"Fair question. The useful difference here is narrow: {gerund}. More detail should come from a human follow-up."
    return f"Fair question. The useful difference here is narrow: {claim}. More detail should come from a human follow-up."


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
    configured_question = _campaign_short_relevance_question(campaign)
    if configured_question:
        question = _lower_initial(_question_sentence(configured_question))
        return f"Sure, one quick check: {question}"
    primary_gap = _sharp_diagnostic_gap_phrase(campaign)
    if primary_gap.endswith("issue"):
        question = f"is {_area_phrase(primary_gap)} causing trouble right now?"
    elif primary_gap.endswith("need"):
        question = f"is {_area_phrase(primary_gap)} active right now?"
    else:
        question = f"is {primary_gap} causing any issue right now?"
    return f"Sure, one quick check: {question}"


def _permission_response(campaign: dict | None) -> str:
    configured_question = _campaign_short_relevance_question(campaign)
    if configured_question:
        return f"Thanks. {_question_sentence(configured_question)}"
    primary_gap = _sharp_diagnostic_gap_phrase(campaign)
    if primary_gap.endswith("need"):
        return f"Thanks. Is {_area_phrase(primary_gap)} active right now?"
    return f"Thanks. Is {primary_gap} causing any issue right now?"


def _scope_relevance_clarification_response(campaign: dict | None) -> str:
    primary_gap = _sharp_diagnostic_gap_phrase(campaign)
    if primary_gap.endswith("need"):
        return f"That may be outside this call's scope. The quick check here is whether {_area_phrase(primary_gap)} is active now."
    return f"That may be outside this call's scope. The quick check here is whether {primary_gap} is causing any issue now."


def _issue_check_question_for_phrase(phrase: str) -> str:
    cleaned = _plain_phrase(phrase)
    if cleaned.endswith("slipping"):
        return f"is {cleaned} now?"
    if cleaned.endswith("need"):
        return f"is {_area_phrase(cleaned)} active now?"
    return f"is {cleaned} causing an issue now?"


def _primary_issue_check_question(campaign: dict | None) -> str:
    configured_question = _campaign_short_relevance_question(campaign)
    if configured_question:
        return _lower_initial(_question_sentence(configured_question))
    return _issue_check_question_for_phrase(_sharp_diagnostic_gap_phrase(campaign))


def _primary_issue_subject_phrase(campaign: dict | None) -> str:
    phrase = _plain_phrase(_sharp_diagnostic_gap_phrase(campaign))
    if phrase.endswith(" slipping"):
        phrase = phrase[: -len(" slipping")]
    return _area_phrase(phrase)


def _primary_issue_problem_clause(campaign: dict | None) -> str:
    phrase = _plain_phrase(_sharp_diagnostic_gap_phrase(campaign))
    if phrase.endswith(" slipping"):
        return f"{phrase[: -len(' slipping')]} is slipping now"
    if phrase.endswith("need"):
        return f"{_area_phrase(phrase)} is active now"
    return f"{_area_phrase(phrase)} is still a problem"


def _has_confirmed_gap(session_state: dict | None) -> bool:
    return bool(_string_items(_memory_from_session(session_state).get("confirmed_gaps")))


def _impact_followup_question() -> str:
    return "Is it causing delays or extra work?"


def _sharp_diagnostic_gap_phrase(campaign: dict | None) -> str:
    return _campaign_primary_customer_issue_phrase(campaign)


def _campaign_purpose_phrase(campaign: dict | None) -> str:
    phrase = _campaign_text(campaign, "campaign_purpose_phrase")
    if phrase:
        return phrase
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
    value = _gap_record_by_id(campaign, gap_id)
    if value:
        return _gap_customer_phrase(value, gap_id)
    return _human_gap_phrase(gap_id)


def _active_gap_phrase(campaign: dict | None, session_state: dict | None) -> str:
    memory = _memory_from_session(session_state)
    confirmed = _string_items(memory.get("confirmed_gaps"))
    if confirmed:
        return _gap_phrase_for_id(campaign, confirmed[0])
    return _primary_gap_phrase(campaign)


def _confirmed_gap_id(session_state: dict | None) -> str:
    memory = _memory_from_session(session_state)
    confirmed = _string_items(memory.get("confirmed_gaps"))
    if confirmed:
        return confirmed[0]
    return ""


def _prior_universal_gap_id(session_state: dict | None) -> str:
    for turn in reversed(_turns(session_state)):
        frame = turn.get("universal_policy_frame") if isinstance(turn, dict) else None
        if not isinstance(frame, dict):
            frame = ((turn.get("dialogue_manager") or {}).get("universal_policy_frame") if isinstance(turn, dict) else None)
        if not isinstance(frame, dict):
            continue
        gap = str(frame.get("confirmed_gap_id") or frame.get("selected_gap") or "").strip()
        if gap and frame.get("buyer_move_id") in {"pain_confirmed", "tentative_gap_interest", "implication_confirmed"}:
            return gap
    return ""


def _pending_tentative_gap_id(session_state: dict | None) -> str:
    memory = _memory_from_session(session_state)
    pending = str(memory.get("tentative_gap") or memory.get("pending_tentative_gap") or "").strip()
    if pending:
        return pending
    for turn in reversed(_turns(session_state)):
        frame = turn.get("universal_policy_frame") if isinstance(turn, dict) else None
        if not isinstance(frame, dict):
            frame = ((turn.get("dialogue_manager") or {}).get("universal_policy_frame") if isinstance(turn, dict) else None)
        if isinstance(frame, dict) and frame.get("buyer_move_id") == "tentative_gap_interest":
            gap = str(frame.get("confirmed_gap_id") or frame.get("selected_gap") or "").strip()
            if gap:
                return gap
    return ""


def _prior_asr_repair_count(session_state: dict | None) -> int:
    count = 0
    for turn in _turns(session_state):
        frame = turn.get("universal_policy_frame") if isinstance(turn, dict) else None
        if not isinstance(frame, dict):
            frame = ((turn.get("dialogue_manager") or {}).get("universal_policy_frame") if isinstance(turn, dict) else None)
        if isinstance(frame, dict) and frame.get("asr_repair_required"):
            count += 1
    return count


def _gap_id_from_transcript(normalized: str, campaign: dict | None) -> str:
    for gap_id, record in _gap_record_items(campaign):
        if _transcript_matches_gap_record(normalized, record):
            return gap_id
    return ""


def _campaign_supported_gap_ids(campaign: dict | None) -> set[str]:
    return {gap_id for gap_id, _ in _gap_record_items(campaign)}


def _unsupported_pain_phrase_gap_id(normalized: str, campaign: dict | None) -> str:
    if not _pain_like_unsupported_phrase(normalized):
        return ""
    gap_id = _gap_id_from_transcript(normalized, campaign)
    if gap_id in _campaign_supported_gap_ids(campaign):
        return ""
    return "unsupported_pain_phrase"


def contextual_pain_supported_by_campaign(
    *,
    transcript: str,
    campaign: dict | None,
    contextual_semantics: dict | None,
) -> bool:
    semantic = str((contextual_semantics or {}).get("semantic") or "")
    if semantic != "pain_confirmed":
        return True
    target_gap = str((contextual_semantics or {}).get("target_gap") or "")
    if not target_gap:
        return False
    supported_gap_ids = _campaign_supported_gap_ids(campaign)
    if supported_gap_ids and target_gap not in supported_gap_ids:
        return False
    normalized = normalize_transcript(transcript)
    matched_gap = _gap_id_from_transcript(normalized, campaign)
    if matched_gap:
        return target_gap == matched_gap
    if _pain_like_unsupported_phrase(normalized) and not _contains_any(
        normalized,
        {"it is a problem", "it is the problem", "that is a problem", "that is the problem", "this is a problem", "this is the problem"},
    ):
        return False
    return True


def sanitize_contextual_semantics_for_universal_policy(
    *,
    transcript: str,
    campaign: dict | None,
    contextual_semantics: dict | None,
) -> dict[str, Any]:
    frame = dict(contextual_semantics or {})
    if contextual_pain_supported_by_campaign(
        transcript=transcript,
        campaign=campaign,
        contextual_semantics=frame,
    ):
        return frame
    frame.update(
        {
            "applied": False,
            "semantic": "no_contextual_semantic",
            "target_gap": None,
            "universal_policy_sanitized": True,
            "sanitization_reason": "pain_transcript_does_not_match_campaign_gap",
        }
    )
    return frame


def _gap_phrase_from_frame_or_text(frame: dict[str, Any], campaign: dict | None, session_state: dict | None) -> str:
    frame_phrase = str((frame or {}).get("confirmed_gap_phrase") or "").strip()
    if frame_phrase:
        return frame_phrase
    return _active_gap_phrase(campaign, session_state)


def _impact_signal_from_transcript(normalized: str) -> dict[str, Any]:
    if _contains_any(
        normalized,
        {
            "not really",
            "not much",
            "not a big deal",
            "just annoying",
            "minor",
            "not urgent",
        },
    ):
        return {"detected": True, "strength": "weak_or_denied", "type": "weak_or_denied"}
    if _contains_any(normalized, {"kind of", "sort of", "i guess", "maybe"}):
        return {"detected": True, "strength": "unclear", "type": "unclear"}
    if normalized in {"yes", "yeah", "yep", "correct", "right"}:
        return {"detected": True, "strength": "confirmed", "type": "quality"}
    impact_patterns: list[tuple[str, tuple[str, ...]]] = [
        ("delay", ("causes delays", "cause delays", "delay", "delays", "customers wait", "wait longer")),
        ("time", ("wastes time", "waste time", "slows us down", "slowing us down", "takes time")),
        ("follow_up", ("miss follow", "missed follow", "miss follow-ups", "missed follow-ups")),
        ("cost", ("costs money", "cost money", "expensive", "budget concern")),
        ("risk", ("creates risk", "risk", "liability")),
        ("quality", ("becoming a problem", "real problem", "causing issues", "hurts quality")),
    ]
    for signal_type, phrases in impact_patterns:
        if _contains_any(normalized, phrases):
            return {"detected": True, "strength": "confirmed", "type": signal_type}
    return {"detected": False, "strength": "none", "type": "none"}


def _is_tentative_gap_active_confirmation(normalized: str) -> bool:
    if _contains_any(
        normalized,
        {
            "not active",
            "not happening",
            "not a real issue",
            "not a real problem",
            "is not active",
            "isn t active",
        },
    ):
        return False
    return normalized in {
        "it is active now",
        "yes it is active",
        "that is active",
        "it is happening",
        "yes that is happening",
        "it is a real issue",
    } or _contains_any(
        normalized,
        {
            "active now",
            "is active",
            "is happening",
            "real issue",
            "real problem",
        },
    )


def _pain_progression_metadata(
    *,
    buyer_move_id: str,
    normalized: str,
    campaign: dict | None,
    session_state: dict | None,
    contextual_semantics: dict | None,
) -> dict[str, Any]:
    if buyer_move_id in NEXT_STEP_DISCIPLINE_MOVES:
        target_gap = _prior_universal_gap_id(session_state) or _confirmed_gap_id(session_state)
    else:
        target_gap = str((contextual_semantics or {}).get("target_gap") or "") or _confirmed_gap_id(session_state)
    if not target_gap and buyer_move_id in {"pain_confirmed", "implication_confirmed", "implication_weak_or_denied", "implication_unclear"}:
        target_gap = _pending_tentative_gap_id(session_state)
    if not target_gap:
        target_gap = _gap_id_from_transcript(normalized, campaign)
    if buyer_move_id == "confusion_not_clear" and _unsupported_pain_phrase_gap_id(normalized, campaign):
        target_gap = ""
    gap_phrase = _gap_phrase_for_id(campaign, target_gap) if target_gap else _sharp_diagnostic_gap_phrase(campaign)
    impact = _impact_signal_from_transcript(normalized)
    base = {
        "sales_progression_stage": "none",
        "appointment_readiness": "none",
        "pain_development_required": False,
        "implication_check_required": False,
        "next_best_sales_action": "none",
        "confirmed_gap_id": target_gap,
        "selected_gap": target_gap,
        "confirmed_gap_phrase": "" if not target_gap and buyer_move_id == "confusion_not_clear" else gap_phrase,
        "impact_signal_detected": bool(impact.get("detected")),
        "impact_signal_type": str(impact.get("type") or "none"),
    }
    if buyer_move_id == "permission_acknowledgement":
        base.update(
            sales_progression_stage="permission_diagnostic",
            appointment_readiness="none",
            pain_development_required=True,
            next_best_sales_action="ask_one_sharp_diagnostic",
            confirmed_gap_phrase=_sharp_diagnostic_gap_phrase(campaign),
        )
    elif buyer_move_id == "pain_confirmed":
        base.update(
            sales_progression_stage="pain_confirmed_needs_implication",
            appointment_readiness="medium",
            pain_development_required=True,
            implication_check_required=True,
            next_best_sales_action="ask_implication_question",
        )
    elif buyer_move_id == "tentative_gap_interest":
        base.update(
            sales_progression_stage="tentative_pain_needs_clarification",
            appointment_readiness="low",
            pain_development_required=True,
            implication_check_required=True,
            next_best_sales_action="clarify_active_or_possible",
        )
    elif buyer_move_id == "implication_confirmed":
        base.update(
            sales_progression_stage="implication_confirmed",
            appointment_readiness="high",
            next_best_sales_action="ask_callback_window",
        )
    elif buyer_move_id == "implication_weak_or_denied":
        base.update(
            sales_progression_stage="implication_weak_or_denied",
            appointment_readiness="low",
            next_best_sales_action="reduce_pressure_or_close",
        )
    elif buyer_move_id == "implication_unclear":
        base.update(
            sales_progression_stage="implication_unclear",
            appointment_readiness="medium",
            implication_check_required=True,
            next_best_sales_action="clarify_implication",
        )
    elif buyer_move_id in NEXT_STEP_DISCIPLINE_MOVES:
        prior_readiness = _prior_appointment_readiness(session_state)
        readiness = prior_readiness if prior_readiness in {"medium", "high"} else "none"
        next_action_by_move = {
            "send_info_request": "capture_send_info_contact",
            "callback_request": "clarify_callback_window",
            "buyer_requests_available_times": "offer_window_without_calendar_claim",
            "buyer_wants_email_before_booking": "capture_email_before_booking",
            "buyer_defers_to_later": "clarify_later_window" if readiness in {"medium", "high"} else "reduce_pressure",
            "appointment_interest": "clarify_callback_window",
            "callback_time_provided": "confirm_callback_time",
        }
        if buyer_move_id == "callback_time_provided" and target_gap and readiness == "none":
            readiness = "high"
        base.update(
            sales_progression_stage="next_step_capture",
            appointment_readiness=readiness,
            next_best_sales_action=next_action_by_move.get(buyer_move_id, "capture_next_step"),
        )
    return base


def _pain_implication_response(gap_phrase: str, campaign: dict | None = None, gap_id: str = "") -> str:
    normalized_gap = _plain_phrase(gap_phrase).lower()
    record = _gap_record_by_id(campaign, gap_id) if gap_id else {}
    if not record:
        for _, candidate in _gap_record_items(campaign):
            if _gap_customer_phrase(candidate) == normalized_gap:
                record = candidate
                break
    acknowledgement = _gap_text(record, "pain_acknowledgement_phrase")
    impact_question = _gap_text(record, "impact_question_phrase")
    if acknowledgement and impact_question:
        return f"{acknowledgement.rstrip('.')} . {_question_sentence(impact_question)}".replace(" . ", ". ")
    if impact_question:
        return f"Got it, {_area_phrase(normalized_gap)} is the issue. {_question_sentence(impact_question)}"
    return f"Got it, {_area_phrase(normalized_gap)} is the issue. Is it causing a real impact now, or mostly a general concern?"


def _tentative_gap_response(gap_phrase: str) -> str:
    normalized_gap = _plain_phrase(gap_phrase).lower()
    return f"Maybe {normalized_gap}, understood. Is that an active concern now, or just something you might want checked later?"


def _impact_confirmed_response(frame: dict[str, Any], campaign: dict | None) -> str:
    signal_type = str((frame or {}).get("impact_signal_type") or "quality")
    owner_role = _role_phrase(_campaign_owner(campaign))
    signal_phrase = {
        "delay": "causing delays",
        "time": "costing time",
        "follow_up": "affecting follow-up",
        "cost": "creating cost pressure",
        "risk": "creating risk",
        "quality": "already becoming a real issue",
    }.get(signal_type, "already creating impact")
    return f"Got it. If it is already {signal_phrase}, the next useful step is a short review with {owner_role}. What callback window works?"


def _response_shape_category(buyer_move_id: str) -> str | None:
    if buyer_move_id in RAPPORT_RELEVANCE_BRIDGE_MOVES:
        return "rapport_relevance_bridge"
    if buyer_move_id in SOCIAL_CONVERSATION_MANAGEMENT_MOVES:
        return "social_conversation_management"
    if buyer_move_id in NEXT_STEP_DISCIPLINE_MOVES:
        return "appointment_callback_send_info"
    if buyer_move_id in DIRECT_PRODUCT_VALUE_MOVES:
        return "direct_product_value_questions"
    if buyer_move_id in OBJECTION_MOVES:
        return "objections"
    if buyer_move_id in TIME_PRESSURE_MOVES:
        return "permission_time_pressure"
    if buyer_move_id in PAIN_PROGRESSION_MOVES:
        return "pain_progression"
    if buyer_move_id in TRUST_IDENTITY_PRIVACY_MOVES:
        return "trust_identity_privacy_consent"
    if buyer_move_id in CHALLENGE_REPAIR_MOVES:
        return "confusion_challenge_repair"
    if buyer_move_id in REGULATED_SCOPE_BOUNDARY_MOVES:
        return "scope_regulated_claim_boundaries"
    return None


def _social_repair_metadata(buyer_move_id: str) -> dict[str, Any]:
    social = buyer_move_id in SOCIAL_CONVERSATION_MANAGEMENT_MOVES
    if buyer_move_id == "slow_down_or_speak_faster":
        repair_type = "speech_rate"
        friction_level = "mild"
    elif buyer_move_id == "language_mismatch":
        repair_type = "language_simplification"
        friction_level = "mild"
    elif buyer_move_id in {"emotional_frustration", "abusive_or_hostile_buyer"}:
        repair_type = "friction_deescalation"
        friction_level = "high"
    elif buyer_move_id in {"repeat_last_answer", "repeat_or_rephrase_request"}:
        repair_type = "repeat_or_rephrase"
        friction_level = "mild"
    elif buyer_move_id == "pronunciation_or_name_correction":
        repair_type = "pronunciation_correction"
        friction_level = "mild"
    elif buyer_move_id in {"small_talk", "silence_or_backchannel"}:
        repair_type = "light_bridge"
        friction_level = "none"
    else:
        repair_type = "none"
        friction_level = "none"
    return {
        "social_repair_required": social,
        "speech_adjustment_requested": buyer_move_id == "slow_down_or_speak_faster",
        "simplified_language_required": buyer_move_id == "language_mismatch",
        "friction_level": friction_level if social else "none",
        "should_preserve_previous_question": social,
        "social_repair_type": repair_type,
    }


def _rapport_repair_metadata(buyer_move_id: str, normalized: str) -> dict[str, Any]:
    rapport = buyer_move_id in RAPPORT_RELEVANCE_BRIDGE_MOVES
    human_context_type = "none"
    emotional_temperature = "none"
    sensitive_context_detected = False
    serious_bad_timing_detected = False
    safe_to_continue = True
    should_stop_for_hardship = False
    should_offer_later_or_stop = False
    relevance_bridge_allowed = rapport
    stakeholder_routing_required = False
    response_shape_id = "none"

    if buyer_move_id == "serious_hardship_bad_timing":
        human_context_type = "serious_hardship"
        emotional_temperature = "serious"
        serious_bad_timing_detected = True
        safe_to_continue = False
        should_stop_for_hardship = True
        relevance_bridge_allowed = False
        response_shape_id = "serious_hardship_close"
    elif buyer_move_id == "sensitive_personal_data_disclosure":
        human_context_type = "sensitive_personal_data"
        emotional_temperature = "serious"
        sensitive_context_detected = True
        safe_to_continue = False
        relevance_bridge_allowed = False
        response_shape_id = "sensitive_data_boundary_close"
    elif buyer_move_id == "busy_or_distracted":
        human_context_type = "busy_or_distracted"
        emotional_temperature = "mild"
        should_offer_later_or_stop = True
        if _contains_any(normalized, {"driving", "in a meeting"}):
            safe_to_continue = False
        response_shape_id = "busy_context_one_question_or_stop"
    elif buyer_move_id == "home_life_interruption":
        human_context_type = "home_life_interruption"
        emotional_temperature = "mild"
        should_offer_later_or_stop = True
        safe_to_continue = False
        response_shape_id = "home_interruption_one_question_or_stop"
    elif buyer_move_id == "workplace_interruption":
        human_context_type = "workplace_interruption"
        emotional_temperature = "mild"
        should_offer_later_or_stop = True
        if _contains_any(normalized, {"incident response", "another call", "boss just walked in"}):
            safe_to_continue = False
        response_shape_id = "workplace_interruption_control"
    elif buyer_move_id == "financial_stress_context":
        human_context_type = "financial_stress"
        emotional_temperature = "mild"
        response_shape_id = "financial_stress_relevance_bridge"
    elif buyer_move_id == "prior_bad_experience_context":
        human_context_type = "prior_bad_experience"
        emotional_temperature = "mild"
        response_shape_id = "skepticism_relevance_bridge"
    elif buyer_move_id == "stakeholder_or_right_person_context":
        human_context_type = "stakeholder_or_right_person"
        emotional_temperature = "none"
        stakeholder_routing_required = True
        relevance_bridge_allowed = False
        response_shape_id = "stakeholder_routing"
    elif buyer_move_id == "sarcasm_or_joking_context":
        human_context_type = "sarcasm_or_joking"
        emotional_temperature = "mild"
        response_shape_id = "sarcasm_relevance_bridge"
    elif buyer_move_id == "emotional_venting_context":
        human_context_type = "emotional_venting"
        emotional_temperature = "high"
        response_shape_id = "venting_relevance_bridge"
    elif buyer_move_id == "irrelevant_off_topic_context":
        human_context_type = "irrelevant_off_topic"
        emotional_temperature = "none"
        should_offer_later_or_stop = True
        response_shape_id = "off_topic_relevance_bridge"

    return {
        "rapport_repair_required": rapport,
        "human_context_type": human_context_type,
        "emotional_temperature": emotional_temperature,
        "sensitive_context_detected": sensitive_context_detected,
        "serious_bad_timing_detected": serious_bad_timing_detected,
        "safe_to_continue": safe_to_continue,
        "should_stop_for_hardship": should_stop_for_hardship,
        "should_offer_later_or_stop": should_offer_later_or_stop,
        "relevance_bridge_allowed": relevance_bridge_allowed,
        "stakeholder_routing_required": stakeholder_routing_required,
        "max_rapport_turns": 1 if rapport else 0,
        "rapport_response_shape_id": response_shape_id,
    }


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
    if semantic == "purpose_explanation_accepted":
        return "why_are_you_asking"
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

    if _contains_any(normalized, {"got out of the hospital", "dealing with a funeral", "family emergency", "really bad time"}):
        return _recognition(
            "serious_hardship_bad_timing",
            reason="serious_hardship_or_bad_timing_phrase",
            confidence="high",
            category="rapport_relevance_bridge",
        )
    if _contains_any(
        normalized,
        {
            "redacted_medical_detail",
            "redacted_account_number",
            "redacted_personal_id",
            "redacted_family_detail",
            "my condition is",
            "my account number is",
            "my personal id is",
            "private family stuff",
        },
    ):
        return _recognition(
            "sensitive_personal_data_disclosure",
            reason="sensitive_personal_data_phrase",
            confidence="high",
            category="rapport_relevance_bridge",
        )
    if _contains_any(normalized, {"i m driving", "i am driving", "cooking dinner", "in a meeting", "only have ten seconds"}):
        return _recognition("busy_or_distracted", reason="busy_or_distracted_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(normalized, {"kids are screaming", "baby crying", "doorbell", "someone is at the door", "groceries in my hands"}):
        return _recognition("home_life_interruption", reason="home_life_interruption_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(normalized, {"between meetings", "boss just walked in", "incident response", "on another call"}):
        return _recognition("workplace_interruption", reason="workplace_interruption_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(normalized, {"everything is expensive", "worried about money", "cutting costs", "cannot afford", "can t afford", "cant afford"}):
        return _recognition("financial_stress_context", reason="financial_stress_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(normalized, {"wasted my time", "got burned", "salespeople always say", "do not trust these calls", "don t trust these calls", "dont trust these calls"}):
        return _recognition("prior_bad_experience_context", reason="prior_bad_experience_or_distrust_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(
        normalized,
        {
            "husband handles",
            "wife decides",
            "manager handles",
            "legal needs to approve",
            "son usually deals",
            "son deals",
            "wife handles",
            "husband decides",
        },
    ):
        return _recognition("stakeholder_or_right_person_context", reason="stakeholder_or_right_person_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(normalized, {"make me rich", "magic solution", "fix my whole life", "too good to be true"}):
        return _recognition("sarcasm_or_joking_context", reason="sarcasm_or_joking_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(
        normalized,
        {
            "tired of dealing with this",
            "annoying for months",
            "nobody ever follows up",
            "sick of this process",
        },
    ):
        return _recognition("emotional_venting_context", reason="emotional_venting_phrase", confidence="high", category="rapport_relevance_bridge")
    if _contains_any(
        normalized,
        {
            "weekend fixing my fence",
            "office printer",
            "unrelated software",
            "long list of errands",
            "forgot my phone",
        },
    ):
        return _recognition("irrelevant_off_topic_context", reason="irrelevant_off_topic_phrase", confidence="high", category="rapport_relevance_bridge")

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
    if "that would be good" in normalized and _previous_response_asked_next_step_timing(session_state):
        return _recognition("appointment_interest", reason="clean_positive_after_progression", confidence="medium", category="appointment_callback_send_info")

    pending_tentative_gap = _pending_tentative_gap_id(session_state)
    if pending_tentative_gap and _is_tentative_gap_active_confirmation(normalized):
        return _recognition(
            "pain_confirmed",
            reason="tentative_gap_confirmed_active",
            confidence="high",
            category="pain_tentative_pain",
        )

    if _confirmed_gap_id(session_state) and _looks_like_time(normalized):
        return _recognition(
            "callback_time_provided",
            reason="time_provided_after_confirmed_gap",
            confidence="high",
            category="appointment_callback_send_info",
        )

    if _confirmed_gap_id(session_state):
        impact = _impact_signal_from_transcript(normalized)
        if impact.get("strength") == "confirmed":
            return _recognition(
                "implication_confirmed",
                reason=f"impact_signal_{impact.get('type')}",
                confidence="high",
                category="pain_progression",
            )
        if impact.get("strength") == "weak_or_denied":
            return _recognition(
                "implication_weak_or_denied",
                reason="weak_or_denied_impact_signal",
                confidence="high",
                category="pain_progression",
            )
        if impact.get("strength") == "unclear":
            return _recognition(
                "implication_unclear",
                reason="unclear_impact_signal",
                confidence="medium",
                category="pain_progression",
            )

    if _contains_any(normalized, {"slow down", "too fast", "speak faster", "speak slower"}):
        return _recognition("slow_down_or_speak_faster", reason="speech_rate_request_phrase", confidence="high", category="social_conversation_management")
    if _contains_any(normalized, {"say that again", "repeat that", "say again", "can you repeat"}):
        return _recognition("repeat_last_answer", reason="repeat_last_answer_phrase", confidence="high", category="social_conversation_management")
    if _contains_any(normalized, {"don t speak english", "dont speak english", "do not speak english", "english well", "different language"}):
        return _recognition("language_mismatch", reason="language_mismatch_phrase", confidence="high", category="social_conversation_management")
    if _contains_any(normalized, {"not how you say my name", "that s not how you say my name", "you said my name wrong"}) or (
        "call me" in normalized and not _looks_like_time(normalized)
    ):
        return _recognition(
            "pronunciation_or_name_correction",
            reason="name_or_pronunciation_correction_phrase",
            confidence="high",
            category="social_conversation_management",
        )
    if _contains_any(normalized, {"haha", "ha ha", "lol", "how are you", "nice weather", "busy day"}):
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
    if _contains_any(normalized, {"already told you", "i told you", "already asked that", "keep asking the same"}):
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

    if normalized.startswith("maybe ") or _contains_any(normalized, {"maybe coverage", "maybe integration", "maybe repair", "maybe scheduling", "maybe handoff"}):
        return _recognition("tentative_gap_interest", reason="tentative_gap_phrase", confidence="high", category="pain_tentative_pain")
    if "price" not in normalized and _contains_any(normalized, {"is a problem", "is the problem", "usually pretty long", "we need service", "is unclear", "is the issue"}):
        if _unsupported_pain_phrase_gap_id(normalized, campaign):
            return _recognition(
                "confusion_not_clear",
                reason="out_of_campaign_pain_phrase",
                confidence="medium",
                category="confusion_challenge_repair",
            )
        return _recognition("pain_confirmed", reason="clean_pain_phrase", confidence="high", category="pain_tentative_pain")

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
        active_detection = dict(frame.get("detection") or {})
        active_detection["applied"] = bool(frame.get("asr_repair_required"))
    if not active_detection.get("applied"):
        return False
    if _is_generic_campaign(campaign):
        return True
    return str(active_detection.get("reason") or "") in UNIVERSAL_ASR_REPAIR_REASONS


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
    normalized = str(detection.get("normalized_transcript") or "")
    progression = _pain_progression_metadata(
        buyer_move_id=buyer_move_id,
        normalized=normalized,
        campaign=campaign,
        session_state=session_state,
        contextual_semantics=contextual_semantics,
    )

    frame = {
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
        "asr_repair_turn_count": _prior_asr_repair_count(session_state) + 1 if detection.get("applied") else 0,
        "detection": detection,
        "pragmatic_move_id": (pragmatic_move or {}).get("move_id"),
    }
    frame.update(progression)
    frame.update(_social_repair_metadata(buyer_move_id))
    frame.update(_rapport_repair_metadata(buyer_move_id, normalized))
    if buyer_move_id in NEXT_STEP_DISCIPLINE_MOVES and frame.get("confirmed_gap_id"):
        frame["should_preserve_confirmed_gaps"] = True
        frame["should_preserve_cleared_gaps"] = True
    if buyer_move_id in NEXT_STEP_DISCIPLINE_MOVES:
        frame.update(
            {
                "next_step_discipline_required": True,
                "callback_capture_required": buyer_move_id in {"callback_request", "appointment_interest"},
                "contact_capture_required": buyer_move_id in {"send_info_request", "buyer_wants_email_before_booking"},
                "should_preserve_appointment_readiness": frame.get("appointment_readiness") in {"medium", "high"},
                "timing_specificity": "concrete" if buyer_move_id == "callback_time_provided" else "vague_or_missing",
            }
        )
    else:
        frame.update(
            {
                "next_step_discipline_required": False,
                "callback_capture_required": False,
                "contact_capture_required": False,
                "should_preserve_appointment_readiness": False,
                "timing_specificity": "none",
            }
        )
    return frame


def _enforcement_reason(enforcement_enabled: bool, detection: dict, campaign: dict | None) -> str:
    if enforcement_enabled:
        return str(detection.get("reason") or "generic_asr_repair")
    if not detection.get("applied"):
        return "no_asr_repair_required"
    if not _is_generic_campaign(campaign):
        return "routesignal_or_non_generic_enforcement_disabled"
    return "enforcement_disabled"


def universal_asr_repair_continuity(frame: dict[str, Any]) -> dict[str, Any]:
    response = REPEATED_REPAIR_RESPONSE if int((frame or {}).get("asr_repair_turn_count") or 0) > 1 else REPAIR_RESPONSE
    return {
        "applied": True,
        "reason": "asr_fragment_repair",
        "action_id": "repair_asr_fragment",
        "dialogue_focus": "repair",
        "candidate_response": response,
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
    confidence = str((frame or {}).get("recognition_confidence") or "")
    out_of_campaign_pain = (
        buyer_move_id == "confusion_not_clear"
        and str((frame or {}).get("recognition_reason") or "") == "out_of_campaign_pain_phrase"
    )
    if (
        confidence != "high"
        and not out_of_campaign_pain
        and buyer_move_id
        not in PAIN_PROGRESSION_MOVES | SOCIAL_CONVERSATION_MANAGEMENT_MOVES | NEXT_STEP_DISCIPLINE_MOVES | RAPPORT_RELEVANCE_BRIDGE_MOVES
    ):
        return False
    if buyer_move_id in PAIN_PROGRESSION_MOVES and confidence not in {"high", "medium"}:
        return False
    if buyer_move_id in SOCIAL_CONVERSATION_MANAGEMENT_MOVES and confidence not in {"high", "medium"}:
        return False
    if buyer_move_id in NEXT_STEP_DISCIPLINE_MOVES and confidence not in {"high", "medium"}:
        return False
    if buyer_move_id in RAPPORT_RELEVANCE_BRIDGE_MOVES and confidence not in {"high", "medium"}:
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
    has_confirmed_gap = _has_confirmed_gap(session_state)
    active_area = _area_phrase(active_gap)
    primary_issue_subject = _primary_issue_subject_phrase(campaign)
    primary_issue_clause = _primary_issue_problem_clause(campaign)
    primary_issue_question = _primary_issue_check_question(campaign)

    if buyer_move_id == "serious_hardship_bad_timing":
        return "I'm sorry to hear that. This is not the right time for this call. I'll stop here."
    if buyer_move_id == "sensitive_personal_data_disclosure":
        return "Understood. Please don't share sensitive details on this call. This is not the right place for that information, so I'll stop here."
    if buyer_move_id == "busy_or_distracted":
        if "driving" in normalized:
            return "No problem. I do not want to distract you while driving. I'll stop here."
        if "in a meeting" in normalized:
            return "Understood, bad time. I will not pull you out of the meeting. I'll stop here."
        if "ten seconds" in normalized:
            return f"Understood. I'll keep it to one question: {primary_issue_question}"
        if "cooking" in normalized:
            return f"Understood. I'll keep it to one yes-or-no: {primary_issue_question}"
        return f"Understood, bad time. I can keep it to one yes-or-no: {primary_issue_question}"
    if buyer_move_id == "home_life_interruption":
        if "kids are screaming" in normalized:
            return "No problem. Sounds like a bad moment with the kids. I'll stop here."
        if "baby crying" in normalized:
            return "No problem. The baby needs you. I'll stop here."
        if _contains_any(normalized, {"doorbell", "someone is at the door"}):
            return "No problem. Handle the door; I'll stop here."
        if "groceries" in normalized:
            return "No problem. I will not keep you while your hands are full. I'll stop here."
        return "No problem. Sounds like a bad moment. I'll stop here."
    if buyer_move_id == "workplace_interruption":
        if _contains_any(normalized, {"incident response", "another call", "boss just walked in"}):
            return "Understood, bad timing. I will not pull you away from that. I'll stop here."
        return f"Understood, I will keep it tight: {primary_issue_question}"
    if buyer_move_id == "financial_stress_context":
        if "everything is expensive" in normalized:
            return (
                "I hear you. Costs are tight for a lot of people. I'm not here to add pressure; "
                f"the useful check is whether {primary_issue_subject} is already costing time or money."
            )
        if "worried about money" in normalized:
            return (
                "Understood. Budget pressure matters. I won't push a review unless "
                f"{primary_issue_subject} is already costing time or creating risk."
            )
        if "cutting costs" in normalized:
            return (
                "Makes sense. If cutting costs is the priority, the only reason to continue is if "
                f"{primary_issue_subject} is already wasting time."
            )
        return (
            "I hear you. Then I should not push anything. The only useful question is whether "
            f"{primary_issue_subject} is already costing more than it should."
        )
    if buyer_move_id == "prior_bad_experience_context":
        if "wasted my time" in normalized:
            return f"Fair. If someone wasted your time before, I would be cautious too. I'll keep this to one concrete check: {primary_issue_question}"
        if "got burned" in normalized:
            return f"That makes sense. I'm not asking for trust upfront; only whether {primary_issue_clause}."
        if "salespeople always say" in normalized:
            return f"Fair. Then I should be specific, not pitchy: {primary_issue_question}"
        return (
            "I understand. You do not need to share sensitive details or commit to anything here. "
            f"The useful check is whether {primary_issue_clause}."
        )
    if buyer_move_id == "stakeholder_or_right_person_context":
        if _contains_any(normalized, {"manager", "legal"}):
            return (
                "Understood. Then the useful next step is not to sell you. "
                "Should I note the decision-maker as the right contact, or leave it here?"
            )
        return "Got it, sounds like they may be the better person. Should I note them as the right contact, or leave it here?"
    if buyer_move_id == "sarcasm_or_joking_context":
        if "make me rich" in normalized:
            return f"No big promises from me. I'm only checking whether {primary_issue_subject} is costing time."
        if "magic solution" in normalized:
            return f"No magic claims. Just a quick check on whether {primary_issue_clause}."
        if "fix my whole life" in normalized:
            return f"No, nothing that dramatic. Just checking whether {primary_issue_subject} is worth a review."
        return f"Fair concern. I won't overstate it; the only question is whether {primary_issue_clause}."
    if buyer_move_id == "emotional_venting_context":
        if "nobody ever follows up" in normalized:
            return "That sounds frustrating. If nobody follows up, that may be exactly the issue. Is it causing missed replies or delays?"
        return "That sounds frustrating. Is it causing delays or extra work now?"
    if buyer_move_id == "irrelevant_off_topic_context":
        if "weekend fixing my fence" in normalized:
            return f"Got it. I won't chase the story; the relevant check is whether {primary_issue_clause}."
        if "office printer" in normalized:
            return f"Understood. I won't pull this into the printer issue; the quick check here: {primary_issue_question}"
        if "unrelated software" in normalized:
            return f"Got it. That sounds separate from this call. The relevant check here: {primary_issue_question}"
        if "errands" in normalized:
            return f"No problem. I won't make this a long call. The only relevant check: {primary_issue_question}"
        return f"Got it. I won't pull this into a long call; the relevant check: {primary_issue_question}"

    if buyer_move_id == "slow_down_or_speak_faster":
        if has_confirmed_gap:
            if _contains_any(normalized, {"speak faster", "too slow"}):
                return f"Sure, I can move faster. You named {active_area}; I'm checking whether it is causing real impact."
            return f"Sure, I'll slow down. You named {active_area}; I'm checking whether it is causing real impact."
        if _contains_any(normalized, {"speak faster", "too slow"}):
            return f"Sure, I can move faster. I'm checking one thing: {_primary_issue_check_question(campaign)}"
        return f"Sure, I'll slow down. I'm checking one thing: {_primary_issue_check_question(campaign)}"
    if buyer_move_id in {"repeat_or_rephrase_request", "repeat_last_answer"}:
        if has_confirmed_gap:
            return f"Sure. Short version: you named {active_area}; I'm checking whether it is causing enough impact for a quick human review."
        return f"Sure. Short version: I'm checking one thing: {_primary_issue_check_question(campaign)}"
    if buyer_move_id == "language_mismatch":
        if has_confirmed_gap:
            return f"Understood. I'll use simple English. You named {active_area}; is it causing a real problem now?"
        return f"Understood. I'll use simple English. One question: {_primary_issue_check_question(campaign)}"
    if buyer_move_id == "pronunciation_or_name_correction":
        return "Sorry about that. I'll use the correction. Should I continue with the quick check?"
    if buyer_move_id in {"small_talk", "silence_or_backchannel"}:
        if "how are you" in normalized:
            return f"I'm good, thanks. I'll keep this quick: {_primary_issue_check_question(campaign)}"
        return f"Okay, thanks. I'll keep this quick: {_primary_issue_check_question(campaign)}"
    if buyer_move_id in {"emotional_frustration", "abusive_or_hostile_buyer"}:
        return "Fair. I do not want to waste your time. I can end the call, or keep it to one simple check."

    if buyer_move_id == "permission_acknowledgement":
        return _permission_response(campaign)
    if buyer_move_id == "time_constrained_permission":
        return _time_pressure_response(campaign)
    if buyer_move_id == "pain_confirmed":
        gap_phrase = _gap_phrase_from_frame_or_text(frame, campaign, session_state)
        gap_id = str((frame or {}).get("confirmed_gap_id") or (frame or {}).get("selected_gap") or "")
        if gap_id and gap_id in _string_items(_memory_from_session(session_state).get("confirmed_gaps")):
            return f"Right, {_area_phrase(gap_phrase)} is already noted. Is it creating a real impact now?"
        return _pain_implication_response(gap_phrase, campaign=campaign, gap_id=gap_id)
    if buyer_move_id == "tentative_gap_interest":
        return _tentative_gap_response(_gap_phrase_from_frame_or_text(frame, campaign, session_state))
    if buyer_move_id == "implication_confirmed":
        return _impact_confirmed_response(frame, campaign)
    if buyer_move_id == "implication_weak_or_denied":
        return "Understood. If it is only minor, there is no reason to force a review. Keep it in mind if it starts costing time."
    if buyer_move_id == "implication_unclear":
        return "Understood. Is it creating a real impact now, or more of a possible concern?"
    if buyer_move_id == "send_info_request":
        if str((frame or {}).get("appointment_readiness") or "") in {"medium", "high"}:
            return f"Sure. Since this sounds worth a review, I can note it for {owner_role}. What email or callback window should they use?"
        return f"Sure. I can note a request for details. What email should {owner_role} use?"
    if buyer_move_id == "callback_request":
        if "next week" in normalized:
            return "Sure. Next week works as a direction. Which day or time window should I note?"
        return "Sure. What day or time window should I note?"
    if buyer_move_id == "buyer_requests_available_times":
        return f"I cannot send a live calendar from this call. I can note a preferred window for {owner_role}. What works?"
    if buyer_move_id == "buyer_wants_email_before_booking":
        return f"Sure. I can note that you want email first. What email should {owner_role} use?"
    if buyer_move_id == "buyer_defers_to_later":
        if str((frame or {}).get("appointment_readiness") or "") in {"medium", "high"}:
            return "Understood. Timing is not right now. What later window should I note?"
        return "Understood. I will not push it now."
    if buyer_move_id == "appointment_interest":
        return "Good. What day or time window should I note?"
    if buyer_move_id == "callback_time_provided":
        return f"Got it. I'll note that time for {owner_role} to follow up."

    if buyer_move_id == "product_detail_question":
        configured_answer = _campaign_text(campaign, "product_detail_answer", "product_summary_phrase")
        if configured_answer:
            return f"Sure. {configured_answer}"
        return (
            f"Sure. This call is only to check whether a short human review is useful around {_area_phrase(primary_gap)}. "
            "The quick question is whether that area is causing friction now."
        )
    if buyer_move_id == "what_problem_do_you_solve":
        return (
            f"Fair question. Mainly {primary_gap}: when it is costing time, creating delays, or hurting quality. "
            "The useful check is whether it is showing up now."
        )
    if buyer_move_id == "why_should_i_care":
        return (
            f"Fair question. Only if {primary_gap} is costing time, creating delays, or hurting follow-up quality. "
            "If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?"
        )
    if buyer_move_id == "what_makes_you_different":
        return _approved_scope_response(campaign)
    if buyer_move_id == "who_is_this_for":
        return f"Fair question. It is for {buyer_role}. If that is not you, I can note the right person or keep this brief."
    if buyer_move_id == "is_this_worth_my_time":
        return f"Fair question. It is worth time only if {primary_gap} is real enough to justify a short review. The useful check is whether it is showing up now."

    if buyer_move_id == "who_are_you":
        return f"Sure, I'm {caller} calling on behalf of {client} about {_campaign_purpose_phrase(campaign)}."
    if buyer_move_id == "are_you_ai_or_robot":
        return f"Yes, I'm an AI voice agent calling for {client}. I'll keep it brief: {_primary_issue_check_question(campaign)}"
    if buyer_move_id == "how_did_you_get_my_number":
        return "I do not have a reliable source note for that in this call, so I will not guess. I can stop here."
    if buyer_move_id == "is_this_recorded":
        return "I do not have a verified recording notice to give here. I can continue only with the call purpose, or stop."
    if buyer_move_id == "privacy_data_use_question":
        return "I can only use what you say here to handle this call flow. I will not ask for sensitive personal details."
    if buyer_move_id in TERMINAL_RESPONSE_SHAPE_MOVES:
        return "Understood. I'll stop here. Goodbye."

    if buyer_move_id == "confusion_not_clear":
        if str((frame or {}).get("recognition_reason") or "") == "out_of_campaign_pain_phrase":
            return _scope_relevance_clarification_response(campaign)
        if has_confirmed_gap:
            return (
                f"I mean whether that issue is causing real impact, like delays, extra work, or missed follow-up. "
                f"You already named {active_area}, so I'm checking whether it is worth a short review. {_impact_followup_question()}"
            )
        return f"I mean whether {_sharp_diagnostic_gap_phrase(campaign)} is happening and causing enough impact to review. Is it showing up now?"
    if buyer_move_id == "why_are_you_asking":
        return (
            f"Fair question. Because {owner_role} only needs to review this when there is real impact from {active_area}, "
            "I'm asking about impact now, not collecting extra details."
        )
    if buyer_move_id == "already_answered_challenge":
        if str((frame or {}).get("recognition_reason") or "") == "did_not_answer_challenge_phrase":
            return (
                "You're right. The direct answer is: I'm checking whether this problem has enough impact to justify "
                f"a short human review. Since you already named {active_area}, the only useful follow-up is impact. "
                f"{_impact_followup_question()}"
            )
        return (
            f"You're right, you already gave me that. I have {active_area} noted; the useful follow-up is whether it is "
            f"causing real impact. {_impact_followup_question()}"
        )
    if buyer_move_id == "contradiction_challenge":
        return f"Fair point. I can ask basic fit questions, but detailed advice belongs with {owner_role}."
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
    if buyer_move_id in TERMINAL_RESPONSE_SHAPE_MOVES or buyer_move_id in TERMINAL_RAPPORT_MOVES or (frame or {}).get("safe_to_continue") is False:
        action_id = "end_call_stop_request"
    elif buyer_move_id == "callback_time_provided":
        action_id = "confirm_callback_and_end"
    elif buyer_move_id in {"send_info_request", "buyer_wants_email_before_booking"}:
        action_id = "request_send_info_contact"
    elif buyer_move_id in {"callback_request", "buyer_requests_available_times", "buyer_defers_to_later", "appointment_interest"}:
        action_id = "request_callback_time"
    else:
        action_id = "continue_with_session_policy"
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
