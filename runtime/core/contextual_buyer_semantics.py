from __future__ import annotations

import hashlib
import re
from typing import Any

from runtime.core import campaign_playbook_adapter as diagnostic_playbook
from runtime.core import live_voice_session_policy as session_policy


SEMANTIC_ID = "CONTEXTUAL-BUYER-SEMANTICS-001"
SCHEMA_VERSION = 1

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
ROUTESIGNAL_PLAYBOOK_ID = diagnostic_playbook.campaign_playbook_id(None)
GENERIC_GAP_PHRASES = {
    "a problem",
    "an issue",
    "clear",
    "fine",
    "handled",
    "issue",
    "problem",
    "the issue",
    "the problem",
    "unclear",
}


def _turns(session_state: dict | None) -> list[dict[str, Any]]:
    return list((session_state or {}).get("turns") or [])


def _previous_response(turns: list[dict[str, Any]]) -> str:
    if not turns:
        return ""
    return str((turns[-1].get("summary") or {}).get("final_response") or "")


def _contains(normalized: str, phrases: set[str]) -> bool:
    return session_policy.normalized_contains_any(normalized, phrases)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item or "")]
    return [str(value)] if str(value or "") else []


def _resolved_playbook(campaign: dict | None) -> dict:
    return diagnostic_playbook.resolve_campaign_playbook(campaign)


def _is_routesignal_playbook(campaign: dict | None) -> bool:
    return str(_resolved_playbook(campaign).get("campaign_playbook_id") or "") == ROUTESIGNAL_PLAYBOOK_ID


def _gap_labels(campaign: dict | None) -> dict[str, str]:
    return diagnostic_playbook.campaign_gap_labels(campaign)


def _core_diagnostic_gaps(campaign: dict | None) -> list[str]:
    return diagnostic_playbook.campaign_core_diagnostic_gaps(campaign)


def _gap_order(campaign: dict | None) -> list[str]:
    return diagnostic_playbook.campaign_gap_order(campaign)


def _supported_gap_ids(campaign: dict | None) -> list[str]:
    return diagnostic_playbook.campaign_supported_gap_ids(campaign)


def _gap_definition(gap_id: str, campaign: dict | None) -> dict:
    return diagnostic_playbook.campaign_gap_definition(gap_id, campaign)


def _review_focus(gap_id: str, campaign: dict | None) -> str | None:
    return diagnostic_playbook.campaign_review_focus(gap_id, campaign)


def _next_gap_candidates(gap_id: str, campaign: dict | None) -> list[str]:
    return diagnostic_playbook.campaign_next_gap_candidates(gap_id, campaign)


def _campaign_context(campaign: dict | None) -> dict[str, Any]:
    return dict(_resolved_playbook(campaign).get("campaign_context") or {})


def _campaign_safety(campaign: dict | None) -> dict[str, Any]:
    return dict(_resolved_playbook(campaign).get("safety") or {})


def _customer_label(gap_id: str | None, campaign: dict | None) -> str:
    if not gap_id:
        return "that follow-up gap"
    definition = _gap_definition(str(gap_id), campaign)
    return str(definition.get("label") or gap_id)


def _value_bridge(gap_id: str | None, campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.value_bridge(gap_id)
    definition = _gap_definition(str(gap_id or ""), campaign)
    return str(definition.get("value_bridge") or "A qualified human should review that before any next step is promised.")


def _join_or(labels: list[str]) -> str:
    labels = [label for label in labels if label]
    if not labels:
        return "those areas"
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} or {labels[1]}"
    return f"{', '.join(labels[:-1])}, or {labels[-1]}"


def _normalized_gap_phrases(gap_id: str, campaign: dict | None, fields: list[str] | None = None) -> list[str]:
    definition = _gap_definition(gap_id, campaign)
    if fields is None:
        values: list[str] = [gap_id.replace("_", " "), str(definition.get("label") or "")]
        fields = [
            "customer_language",
            "evidence_positive",
            "evidence_negative",
            "diagnostic_questions",
            "review_focus",
        ]
    else:
        values = []
    for field in fields:
        if field == "label":
            values.append(str(definition.get("label") or ""))
        elif field in {"campaign_gap_id", "gap_id"}:
            values.extend([gap_id.replace("_", " "), str(definition.get("campaign_gap_id") or "")])
        else:
            values.extend(_string_list(definition.get(field)))
    phrases: list[str] = []
    for value in values:
        normalized = session_policy.normalize_text(value)
        if normalized and normalized not in GENERIC_GAP_PHRASES and normalized not in phrases:
            phrases.append(normalized)
    return phrases


def _matches_any_phrase(normalized: str, phrases: list[str]) -> bool:
    return any(phrase in normalized for phrase in phrases)


def _text_matches_gap(normalized: str, gap_id: str, campaign: dict | None) -> bool:
    return _matches_any_phrase(normalized, _normalized_gap_phrases(gap_id, campaign))


def _evidence_matches_gap(normalized: str, gap_id: str, campaign: dict | None, field: str) -> bool:
    return _matches_any_phrase(normalized, _normalized_gap_phrases(gap_id, campaign, [field]))


def _remaining_gaps(
    *,
    cleared_gaps: list[str] | tuple[str, ...] | set[str],
    confirmed_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    candidate_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    campaign: dict | None,
) -> list[str]:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.remaining_gaps(
            cleared_gaps=cleared_gaps,
            confirmed_gaps=confirmed_gaps,
            candidate_gaps=candidate_gaps,
        )
    excluded = set(str(gap) for gap in list(cleared_gaps or []) + list(confirmed_gaps or []))
    scope = list(candidate_gaps or []) or _core_diagnostic_gaps(campaign)
    ordered = _ordered_candidate_gaps(_unique([str(gap) for gap in scope]), campaign)
    return [gap for gap in ordered if gap not in excluded]


def _next_gap(
    *,
    gap_id: str | None = None,
    cleared_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    confirmed_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    candidate_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    campaign: dict | None,
) -> str | None:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.next_gap(
            cleared_gaps=cleared_gaps or [],
            confirmed_gaps=confirmed_gaps,
            candidate_gaps=candidate_gaps,
        )
    excluded = set(str(gap) for gap in list(cleared_gaps or []) + list(confirmed_gaps or []))
    scope = _ordered_candidate_gaps(list(candidate_gaps or []) or _core_diagnostic_gaps(campaign), campaign)
    if gap_id:
        for candidate in _next_gap_candidates(gap_id, campaign):
            if candidate in scope and candidate not in excluded:
                return candidate
    for candidate in scope:
        if candidate not in excluded:
            return candidate
    return None


def _playbook_trace(
    *,
    gap_id: str | None,
    cleared_gaps: list[str] | None,
    confirmed_gaps: list[str] | None,
    candidate_gaps: list[str] | None,
    campaign: dict | None,
) -> dict[str, Any]:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.playbook_trace(
            gap_id=gap_id,
            cleared_gaps=cleared_gaps,
            confirmed_gaps=confirmed_gaps,
            candidate_gaps=candidate_gaps,
        )
    playbook = _resolved_playbook(campaign)
    supported = _supported_gap_ids(campaign)
    scope = _ordered_candidate_gaps(candidate_gaps or _core_diagnostic_gaps(campaign), campaign)
    playbook_gap = gap_id if gap_id in supported else None
    if playbook_gap is None:
        for gap in list(confirmed_gaps or []) + list(cleared_gaps or []):
            if gap in supported:
                playbook_gap = gap
                break
    next_gap = _next_gap(
        gap_id=playbook_gap,
        cleared_gaps=cleared_gaps or [],
        confirmed_gaps=confirmed_gaps or [],
        candidate_gaps=scope,
        campaign=campaign,
    )
    definition = _gap_definition(str(playbook_gap or ""), campaign)
    regulated_cautions = list(playbook.get("regulated_cautions") or (_campaign_context(campaign).get("regulated_cautions") or []))
    return {
        "adapter_id": playbook.get("adapter_id"),
        "schema_version": playbook.get("schema_version"),
        "campaign_id": playbook.get("campaign_id"),
        "vertical_id": playbook.get("vertical_id"),
        "universal_knowledge_id": playbook.get("universal_knowledge_id"),
        "campaign_playbook_id": playbook.get("campaign_playbook_id"),
        "playbook_id": playbook.get("campaign_playbook_id"),
        "playbook_gap": playbook_gap,
        "playbook_next_gap": next_gap,
        "playbook_review_focus": definition.get("review_focus"),
        "playbook_supported_gap_ids": list(supported),
        "candidate_gaps": list(scope),
        "universal_pain_dimensions": list(definition.get("universal_pain_dimensions") or []),
        "qualification_dimensions": list(definition.get("qualification_dimensions") or []),
        "regulated_cautions": regulated_cautions,
        "safety": _campaign_safety(campaign),
    }


def _list_from_memory(turns: list[dict[str, Any]], key: str, campaign: dict | None = None) -> list[str]:
    values: list[str] = []
    supported = set(_supported_gap_ids(campaign))
    for turn in turns:
        memory = turn.get("conversation_memory") or {}
        if isinstance(memory.get(key), list):
            values.extend(str(item) for item in memory.get(key) or [])
        manager = turn.get("dialogue_manager") or {}
        frame = manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {}
        if key == "confirmed_gaps" and isinstance(frame.get("confirmed_gaps"), list):
            values.extend(str(item) for item in frame.get("confirmed_gaps") or [])
        if key == "cleared_gaps" and isinstance(frame.get("cleared_gaps"), list):
            values.extend(str(item) for item in frame.get("cleared_gaps") or [])
        if key == "confirmed_gaps" and frame.get("semantic") in {"pain_confirmed", "mixed_gap_response"} and frame.get("target_gap"):
            values.append(str(frame["target_gap"]))
        if key == "cleared_gaps" and frame.get("semantic") in {"current_gap_clear", "no_pain_for_specific_gap"} and frame.get("target_gap"):
            values.append(str(frame["target_gap"]))
    return _unique([value for value in values if not supported or value in supported])


def _previous_send_info_state(turns: list[dict[str, Any]]) -> dict[str, Any]:
    for turn in reversed(turns):
        memory = turn.get("conversation_memory") or {}
        state = memory.get("send_info_state")
        if isinstance(state, dict):
            return dict(state)
    return {}


def _previous_handoff_target_state(turns: list[dict[str, Any]]) -> dict[str, Any]:
    for turn in reversed(turns):
        memory = turn.get("conversation_memory") or {}
        state = memory.get("handoff_target_state")
        if isinstance(state, dict):
            return dict(state)
    return {}


def _send_info_capture_open(state: dict[str, Any]) -> bool:
    if not state.get("requested"):
        return False
    return str(state.get("lead_status") or "") not in {"closed_refused"} and str(state.get("capture_status") or "") in {
        "needs_email_or_callback_time",
        "email_captured",
        "none",
    }


def _handoff_capture_open(state: dict[str, Any]) -> bool:
    if not state.get("requested"):
        return False
    return str(state.get("lead_status") or "") not in {"closed_wrong_person"}


def _extract_email(text: str) -> str | None:
    match = EMAIL_RE.search(str(text or ""))
    return match.group(0).lower() if match else None


def _extract_contact_email(text: str) -> tuple[str | None, str]:
    explicit = _extract_email(text)
    if explicit:
        return explicit, "explicit_email"

    normalized = session_policy.normalize_text(text)
    match = re.search(
        r"\b([a-z](?:\s+[a-z]){1,}|[a-z0-9._%+-]+)\s+at\s+([a-z0-9-]+)(?:\s+dot\s+|\s+)([a-z]{2,})\b",
        normalized,
    )
    if not match:
        return None, "none"

    local_text = match.group(1).strip()
    domain_part = match.group(2)
    if local_text in {"today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}:
        return None, "none"
    if not re.search(r"[a-z]", domain_part):
        return None, "none"
    local = re.sub(r"\s+", "", local_text)
    domain = f"{domain_part}.{match.group(3)}"
    candidate = f"{local}@{domain}".lower()
    candidate_match = EMAIL_RE.search(candidate)
    if candidate_match and candidate_match.group(0) == candidate:
        return candidate, "asr_spelled_email"
    return None, "none"


def _redact_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    return f"{(local[:1] or '*')}***@{domain.lower()}"


def _email_hash(email: str | None) -> str | None:
    if not email:
        return None
    return hashlib.sha256(email.lower().encode("utf-8")).hexdigest()[:16]


def _callback_time_text(text: str) -> str:
    without_email = EMAIL_RE.sub("", str(text or ""))
    return session_policy.normalize_text(without_email)


def _empty_callback_normalized() -> dict[str, Any]:
    return {
        "date_text": None,
        "day_text": None,
        "time_text": None,
        "meridiem": None,
        "relative_date": None,
        "confidence": 0.0,
    }


def _normalize_callback_time(text: str) -> dict[str, Any]:
    raw_text = _callback_time_text(text)
    normalized = _empty_callback_normalized()
    if not raw_text:
        return {
            "raw_text_redacted": None,
            "normalized": normalized,
            "needs_clarification": True,
        }

    date_text: str | None = None
    day_text: str | None = None
    relative_date: str | None = None
    if _contains(raw_text, {"tomorrow"}):
        date_text = "tomorrow"
        relative_date = "tomorrow"
    elif _contains(raw_text, {"today"}):
        date_text = "today"
        relative_date = "today"
    elif _contains(raw_text, {"next week"}):
        date_text = "next week"
        relative_date = "next_week"

    weekday_match = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", raw_text)
    if weekday_match:
        day_text = weekday_match.group(1)
        if relative_date is None:
            relative_date = "weekday"

    time_text: str | None = None
    meridiem: str | None = None
    time_match = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm|a m|p m)?\b", raw_text)
    if time_match:
        hour = time_match.group(1)
        minute = time_match.group(2)
        suffix = (time_match.group(3) or "").replace(" ", "")
        time_text = f"{hour}:{minute}" if minute else hour
        meridiem = suffix if suffix in {"am", "pm"} else "unknown"
    elif _contains(raw_text, {"morning"}):
        time_text = "morning"
        meridiem = "am"
    elif _contains(raw_text, {"afternoon"}):
        time_text = "afternoon"
        meridiem = "pm"
    elif _contains(raw_text, {"evening"}):
        time_text = "evening"
        meridiem = "pm"

    has_date = bool(date_text or day_text or relative_date in {"today", "tomorrow", "weekday"})
    has_time = bool(time_text)
    needs_clarification = not (has_date and has_time)
    confidence = 0.9 if not needs_clarification and time_match else 0.78 if not needs_clarification else 0.45
    normalized.update(
        {
            "date_text": date_text,
            "day_text": day_text,
            "time_text": time_text,
            "meridiem": meridiem,
            "relative_date": relative_date or "unknown",
            "confidence": confidence,
        }
    )
    return {
        "raw_text_redacted": raw_text,
        "normalized": normalized,
        "needs_clarification": needs_clarification,
    }


def _has_callback_time_attempt(text: str, normalized: str) -> bool:
    callback = _normalize_callback_time(text)
    parts = callback.get("normalized") or {}
    return bool(
        session_policy.has_callback_time_signal(normalized)
        or parts.get("date_text")
        or parts.get("day_text")
        or parts.get("time_text")
        or parts.get("relative_date") in {"today", "tomorrow", "next_week", "weekday"}
    )


def _looks_like_unclear_email_attempt(normalized: str, raw_text: str) -> bool:
    if _extract_contact_email(raw_text)[0]:
        return False
    padded = f" {normalized} "
    return " at " in padded and _contains(normalized, {"send", "email", "mail"})


def _gap_from_text(text: str, campaign: dict | None = None) -> str | None:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.first_gap_from_text(text)
    gaps = _gaps_from_text(text, campaign)
    return gaps[0] if gaps else None


def _gaps_from_text(text: str, campaign: dict | None = None) -> list[str]:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.gaps_from_text(text)
    normalized = session_policy.normalize_text(text)
    if not normalized:
        return []
    return _ordered_candidate_gaps(
        [gap_id for gap_id in _gap_order(campaign) if _text_matches_gap(normalized, gap_id, campaign)],
        campaign,
    )


def _ordered_candidate_gaps(gaps: list[str], campaign: dict | None = None) -> list[str]:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.ordered_gap_ids(gaps)
    unique_gaps = _unique([str(gap) for gap in gaps])
    ordered: list[str] = []
    for gap_id in _gap_order(campaign):
        if gap_id in unique_gaps and gap_id not in ordered:
            ordered.append(gap_id)
    supported = set(_supported_gap_ids(campaign))
    for gap_id in unique_gaps:
        if gap_id not in ordered and (not supported or gap_id in supported):
            ordered.append(gap_id)
    return ordered


def _previous_outgoing_candidate_gaps(turns: list[dict[str, Any]], campaign: dict | None = None) -> list[str]:
    if not turns:
        return []
    memory = turns[-1].get("conversation_memory") or {}
    gaps = memory.get("outgoing_candidate_gaps")
    if not isinstance(gaps, list):
        return []
    return _ordered_candidate_gaps(_unique([str(gap) for gap in gaps]), campaign)


def _is_contextual_gap_reference(normalized: str) -> bool:
    return _contains(normalized, {"that", "that part", "there", "on that", "with that"})


def _active_gap(
    turns: list[dict[str, Any]],
    previous_question: str | None,
    normalized: str,
    *,
    previous_candidate_gaps: list[str] | None = None,
    campaign: dict | None = None,
) -> str | None:
    current_gap = _gap_from_text(normalized, campaign)
    contextual_reference = _is_contextual_gap_reference(normalized)
    if current_gap and not contextual_reference:
        return current_gap
    if len(previous_candidate_gaps or []) > 1:
        return None
    previous_question_gaps = _gaps_from_text(previous_question or "", campaign)
    if len(previous_question_gaps) > 1:
        return None
    supported = set(_supported_gap_ids(campaign))
    if len(previous_candidate_gaps or []) == 1:
        candidate = str((previous_candidate_gaps or [])[0])
        if not supported or candidate in supported:
            return candidate
    if len(previous_question_gaps) == 1:
        candidate = str(previous_question_gaps[0])
        if not supported or candidate in supported:
            return candidate
    for turn in reversed(turns):
        memory = turn.get("conversation_memory") or {}
        continuity = turn.get("continuity") or {}
        for value in [memory.get("selected_gap"), continuity.get("selected_gap")]:
            if value and str(value) != "timing" and (not supported or str(value) in supported):
                return str(value)
    if previous_question:
        gap = _gap_from_text(previous_question, campaign)
        if gap:
            return gap
    if current_gap:
        return current_gap
    selected = session_policy.last_selected_gap_from_turns(turns)
    if selected and (not supported or selected in supported):
        return selected
    return None


def _candidate_gaps(previous_question: str | None, campaign: dict | None = None) -> list[str]:
    gaps = _gaps_from_text(previous_question or "", campaign)
    return _ordered_candidate_gaps(gaps, campaign)


def outgoing_question_state_from_response(response: str, campaign: dict | None = None) -> dict[str, Any]:
    question_type = session_policy.question_type_from_response(response)
    candidate_gaps = _candidate_gaps(response, campaign)
    normalized = session_policy.normalize_text(response)
    diagnostic_types = {
        "qualification_gap_diagnostic",
        "call_purpose_gap_diagnostic",
        "focus_scope_question",
        "comparative_gap_diagnostic",
        "workflow_breakpoint_question",
        "gap_diagnostic",
    }
    diagnostic_markers = {
        "fit check",
        "creating issues",
        "create issues",
        "ever get missed",
        "ever get messy",
        "all clean",
        "clean today",
        "or handoffs",
        "or manual tracking",
    }
    is_diagnostic = question_type in diagnostic_types or (
        question_type == "sales_progression_question"
        and bool(candidate_gaps)
        and _contains(normalized, diagnostic_markers)
    )
    if not is_diagnostic or not candidate_gaps:
        return {
            "outgoing_question_type": question_type if question_type != "none" else None,
            "outgoing_candidate_gaps": [],
            "outgoing_active_gap_scope": "unknown",
        }
    if len(candidate_gaps) > 1:
        return {
            "outgoing_question_type": "multi_gap_diagnostic",
            "outgoing_candidate_gaps": candidate_gaps,
            "outgoing_active_gap_scope": "multi_gap",
        }
    return {
        "outgoing_question_type": "single_gap_diagnostic",
        "outgoing_candidate_gaps": candidate_gaps,
        "outgoing_active_gap_scope": "single_gap",
    }


def _active_gap_scope(
    *,
    previous_question_type: str,
    active_gap: str | None,
    candidate_gaps: list[str],
) -> str:
    if previous_question_type == "permission_check":
        return "campaign_relevance"
    if len(candidate_gaps) > 1:
        return "multi_gap"
    if active_gap:
        return "single_gap"
    return "unknown"


def _conversation_stage(
    *,
    turn_count: int,
    previous_question_type: str,
    pending_callback: bool,
    pending_appointment: bool,
    confirmed_gaps: list[str],
    cleared_gaps: list[str],
) -> str:
    if previous_question_type == "permission_check" or turn_count == 0:
        return "opening"
    if pending_callback:
        return "callback_scheduling"
    if pending_appointment:
        return "appointment_scheduling"
    if confirmed_gaps:
        return "post_pain"
    if cleared_gaps or turn_count > 2:
        return "mid_call"
    return "qualification"


def _is_permission_ack(normalized: str) -> bool:
    if normalized in {
        "yes",
        "yes sure",
        "yeah",
        "yeah sure",
        "yeah go ahead",
        "sure",
        "sure thing",
        "ok",
        "okay",
        "okay quick",
        "okay sure",
        "no problem",
        "go ahead",
        "i do",
        "i do yeah",
        "i have a minute",
        "i ve got a minute",
        "ive got a minute",
        "sure i guess",
    }:
        return True
    return _contains(normalized, {"go ahead"}) and _contains(normalized, {"yes", "yeah", "ok", "okay", "sure"})


def _is_low_information_ack(normalized: str) -> bool:
    return normalized in {
        "yes",
        "yes send it",
        "yeah",
        "yeah sure",
        "yeah let s do that",
        "yeah lets do that",
        "let s do that",
        "lets do that",
        "sure",
        "ok",
        "okay",
        "okay sure",
        "no problem",
        "got it",
        "sounds good",
    }


def _is_confusion(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "not clear",
            "not all clear",
            "i do not understand",
            "i dont understand",
            "i don t understand",
            "i am not following",
            "im not following",
            "what are you asking",
            "what did you ask",
            "what is the question",
        },
    )


def _is_meaning_question(normalized: str) -> bool:
    return _contains(normalized, {"what do you mean", "what does that mean", "mean by", "what are you saying"})


def _is_terminal_stop_request(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "take us off your list",
            "take me off your list",
            "remove us",
            "remove me",
            "do not call again",
            "don t call again",
            "dont call again",
            "do not contact me",
            "don t contact me",
            "dont contact me",
            "stop calling",
            "stop contacting",
            "i said no",
        },
    )


def _is_clear_or_no_pain(normalized: str) -> bool:
    if _is_confusion(normalized):
        return False
    if normalized in {
        "all clear",
        "it s all clear",
        "its all clear",
        "it is all clear",
        "everything is clear",
        "we re good",
        "were good",
        "we are good",
        "all good",
        "we are fine",
        "we re fine",
        "no issue",
        "no issues",
        "no pain point",
        "no pain points",
        "no problem",
        "no problems",
        "nothing is slipping",
        "we re covered",
        "were covered",
        "we are covered",
        "we have it covered",
        "that s handled",
        "thats handled",
            "we already handle that",
            "that does not happen here",
            "that is handled",
            "that part is fine",
            "we don t have that issue",
            "we dont have that issue",
            "we do not have that issue",
        "no need",
        "no need there",
        "no issue there",
        "nothing falls through",
        "nothing gets lost",
        "callbacks are handled",
        "handoffs are handled",
        "routing is fine",
        "reminders are fine",
        "tracking is fine",
        "just callbacks",
    }:
        return True
    return _contains(
        normalized,
        {
            "callbacks are fine",
            "callback is fine",
            "manual tracking is fine",
            "handoffs are fine",
            "everything is clear",
            "nothing is slipping",
            "nothing gets missed",
            "nothing gets lost",
            "nothing falls through",
            "no real issue",
            "no real problem",
            "we have it covered",
            "we are covered on that",
            "already handle that",
            "does not happen here",
            "that is handled",
            "that part is fine",
            "part is fine",
            "covered on that",
            "do not have that issue",
            "don t have that issue",
            "dont have that issue",
            "callbacks are handled",
            "handoffs are handled",
            "routing is fine",
            "reminders are fine",
            "tracking is fine",
        },
    )


def _is_broad_clear_or_no_pain(normalized: str) -> bool:
    if _is_confusion(normalized):
        return False
    if _contains(normalized, {"callback", "callbacks", "manual tracking", "tracking", "handoff", "handoffs", "routing", "reminders"}):
        return False
    return normalized in {
        "all clear",
        "it s all clear",
        "its all clear",
        "it is all clear",
        "everything is clear",
        "we re good",
        "were good",
        "we are good",
        "all good",
        "we are fine",
        "we re fine",
        "no issue",
        "no issues",
        "no pain point",
        "no pain points",
        "no problem",
        "no problems",
        "nothing is slipping",
        "we re covered",
        "were covered",
        "we are covered",
        "we have it covered",
        "that s handled",
        "thats handled",
        "we already handle that",
        "that does not happen here",
        "that is handled",
        "that part is fine",
        "we don t have that issue",
        "we dont have that issue",
        "we do not have that issue",
        "no need there",
        "no issue there",
        "nothing falls through",
        "nothing gets lost",
    }


def _clear_gaps_from_text(normalized: str, campaign: dict | None = None) -> list[str]:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.cleared_gaps_from_text(normalized)
    if _is_confusion(normalized):
        return []
    gaps = [
        gap_id
        for gap_id in _gap_order(campaign)
        if _evidence_matches_gap(normalized, gap_id, campaign, "evidence_negative")
        or (_is_clear_or_no_pain(normalized) and _text_matches_gap(normalized, gap_id, campaign))
    ]
    return _ordered_candidate_gaps(gaps, campaign)


def _confirmed_gaps_from_text(normalized: str, campaign: dict | None = None) -> list[str]:
    if _is_confusion(normalized):
        return []
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.confirmed_gaps_from_text(normalized)
    gaps = [
        gap_id
        for gap_id in _gap_order(campaign)
        if not _evidence_matches_gap(normalized, gap_id, campaign, "evidence_negative")
        and (
            _evidence_matches_gap(normalized, gap_id, campaign, "evidence_positive")
            or (_has_pain_signal(normalized) and _text_matches_gap(normalized, gap_id, campaign))
        )
    ]
    return _ordered_candidate_gaps(gaps, campaign)


def _rank_confirmed_gaps(gaps: list[str], utterance: str = "", campaign: dict | None = None) -> tuple[str | None, list[str]]:
    if _is_routesignal_playbook(campaign):
        return diagnostic_playbook.rank_confirmed_gaps(gaps, utterance)
    ordered = _ordered_candidate_gaps(gaps, campaign)
    if not ordered:
        return None, []
    normalized = session_policy.normalize_text(utterance)
    scored: list[tuple[int, str]] = []
    for gap_id in ordered:
        phrases = _normalized_gap_phrases(gap_id, campaign, ["evidence_positive", "customer_language", "label"])
        positions = [normalized.find(phrase) for phrase in phrases if phrase and phrase in normalized]
        scored.append((min(positions) if positions else 9999, gap_id))
    selected = sorted(scored, key=lambda item: (item[0], ordered.index(item[1])))[0][1]
    return selected, [gap for gap in ordered if gap != selected]


def _final_save_pending(turns: list[dict[str, Any]], previous_question: str | None) -> bool:
    previous = session_policy.normalize_text(previous_question or "")
    if _contains(previous, {"not an issue at all", "or just this part"}):
        return True
    for turn in reversed(turns[-2:]):
        memory = turn.get("conversation_memory") or {}
        if memory.get("final_save_pending"):
            return True
        manager = turn.get("dialogue_manager") or {}
        frame = manager.get("contextual_buyer_semantics") or (manager.get("state_before") or {}).get("contextual_buyer_semantics") or {}
        if frame.get("semantic") == "not_relevant_mid_call":
            return True
    return False


def _is_final_save_all_scope(normalized: str) -> bool:
    return normalized in {"all of it", "all of them", "everything", "all", "both", "none of it"}


def _is_not_relevant(normalized: str, *, stage: str, active_gap: str | None) -> bool:
    if _contains(
        normalized,
        {
            "not relevant",
            "not relevant for us",
            "not for us",
            "not our thing",
            "not useful for us",
            "does not apply",
            "doesn t apply",
            "doesnt apply",
            "not a fit",
            "we don t need this",
            "we dont need this",
            "we do not need this",
            "we already have a solution",
            "we already have a process",
            "we are all set",
            "all set",
        },
    ):
        return True
    if _contains(normalized, {"we re covered thanks", "were covered thanks", "we are covered thanks"}):
        return True
    if normalized in {"no need", "we re covered", "were covered", "we are covered"}:
        return stage == "opening"
    return False


def _is_not_interested(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "not interested",
            "no interest",
            "no thanks",
            "i m not interested",
            "im not interested",
            "we are not interested",
            "we re not interested",
            "were not interested",
        },
    )


def _is_send_info_request(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "send me something",
            "send over details",
            "send me details",
            "send details",
            "send me an email",
            "email me",
            "send info",
            "send information",
            "send the summary",
            "send a summary",
            "send me a summary",
            "can you send a summary",
            "can you send info first",
            "put it in writing",
        },
    )


def _is_send_info_contact_refusal(normalized: str) -> bool:
    return normalized in {"never mind", "nevermind", "forget it", "no email"} or _contains(
        normalized,
        {
            "don t send it",
            "dont send it",
            "do not send it",
            "don t send anything",
            "dont send anything",
            "do not send anything",
            "forget it",
            "no email",
        },
    )


def _is_wrong_person(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "wrong person",
            "i m not the person",
            "im not the person",
            "i am not the person",
            "not the right person",
            "not my department",
            "wrong department",
            "wrong team",
            "someone else handles",
            "i do not handle",
            "i dont handle",
            "i don t handle",
            "another team owns",
            "team owns that",
            "talk to operations",
            "talk to support",
            "sales handles that",
            "support handles that",
            "my manager handles that",
            "my manager handles it",
            "operations handles this",
            "operations handles that",
            "operations handles it",
            "operations handles lead routing",
        },
    )


def _department_from_text(normalized: str) -> str | None:
    if _contains(normalized, {"operations", "ops"}):
        return "operations"
    if _contains(normalized, {"sales handles", "sales team", "talk to sales"}):
        return "sales"
    if _contains(normalized, {"support handles", "support team", "talk to support"}):
        return "support"
    if _contains(normalized, {"my manager", "manager handles", "to my manager"}):
        return "manager"
    return None


def _person_name_from_text(text: str) -> str | None:
    match = re.search(r"\b(?:talk to|call|ask|send it to)?\s*(sarah)\b", str(text or ""), flags=re.IGNORECASE)
    if match:
        return "Sarah"
    return None


def _is_person_named(text: str, normalized: str) -> bool:
    return bool(_person_name_from_text(text)) and _contains(normalized, {"handles", "talk to", "call"})


def _is_send_info_to_right_person(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "send it to my manager",
            "send the summary to operations",
            "send it to operations",
            "send it to sales",
            "send it to support",
            "send the summary to my manager",
        },
    )


def _is_refused_right_person_contact(normalized: str) -> bool:
    return normalized in {"i don t know", "i dont know", "i do not know", "not sure"} or _contains(
        normalized,
        {
            "don t know who handles",
            "dont know who handles",
            "do not know who handles",
            "can t give that",
            "cant give that",
            "cannot give that",
            "no just stop",
        },
    )


def _is_timing_soft_deferral(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "maybe later",
            "not right now",
            "not today",
            "call another time",
            "call later",
            "try next week",
            "now is bad",
            "bad timing",
            "i m busy",
            "im busy",
            "i am busy",
            "i m in a meeting",
            "im in a meeting",
            "i am in a meeting",
        },
    )


def _is_appointment_hesitation(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "think about it",
            "have to think",
            "need to think",
            "not ready",
            "not sure yet",
            "didn t accept",
            "didnt accept",
            "did not accept",
            "not committing",
        },
    )


def _has_pain_signal(normalized: str) -> bool:
    if _is_clear_or_no_pain(normalized) or _is_confusion(normalized):
        return False
    return _contains(
        normalized,
        {
            "missed",
            "missing",
            "slipping",
            "slip",
            "problem",
            "issue",
            "hard",
            "messy",
            "manual",
            "breaks",
            "break",
            "struggle",
            "struggling",
            "costs time",
            "cost time",
            "causes delays",
            "cause delays",
            "delay",
            "occasional",
            "time to time",
            "sometimes",
        },
    )


def _is_unclear_possible_pain(normalized: str) -> bool:
    if _is_clear_or_no_pain(normalized) or _is_confusion(normalized):
        return False
    return normalized in {"sometimes maybe", "occasionally", "not always", "it depends"} or _contains(
        normalized,
        {
            "not sure",
            "not certain",
            "i am not sure",
            "i m not sure",
            "im not sure",
            "depends",
            "occasionally",
            "not always",
        },
    )


def _is_repeat_problem_reference(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "already told you",
            "i already told you",
            "i told you",
            "i said",
            "already said",
            "said manual",
            "said callbacks",
            "said handoffs",
            "said reminders",
            "that is what i said",
        },
    )


def _pending_callback(turns: list[dict[str, Any]], previous_question_type: str) -> bool:
    return previous_question_type == "callback_time" or session_policy.previous_response_offered_callback_later(turns)


def _pending_appointment(turns: list[dict[str, Any]], previous_question_type: str) -> bool:
    return bool(session_policy.pending_appointment_gap_from_turns(turns)) or previous_question_type in {
        "appointment_time",
        "workflow_review_next_step",
        "value_review_check",
        "summary_next_step",
    }


def _frame(
    *,
    campaign: dict | None = None,
    semantic: str,
    transcript: str,
    normalized: str,
    previous_question_type: str,
    previous_question_text: str | None,
    conversation_stage: str,
    active_gap: str | None,
    confirmed_gaps: list[str],
    cleared_gaps: list[str],
    pending_callback: bool,
    pending_appointment: bool,
    active_gap_scope: str = "unknown",
    candidate_gaps: list[str] | None = None,
    answered_gaps: list[str] | None = None,
    current_cleared_gaps: list[str] | None = None,
    current_confirmed_gaps: list[str] | None = None,
    primary_gap: str | None = None,
    secondary_confirmed_gaps: list[str] | None = None,
    target_gap: str | None = None,
    target_topic: str | None = None,
    polarity: str = "neutral",
    confidence: float = 0.85,
    next_action_hint: str = "continue",
    must_not_do: list[str] | None = None,
    candidate_response: str | None = None,
    action_id: str | None = None,
    dialogue_focus: str | None = None,
    send_info_state_update: dict[str, Any] | None = None,
    lead_followup_state_update: dict[str, Any] | None = None,
    handoff_target_state_update: dict[str, Any] | None = None,
    applied: bool = True,
) -> dict[str, Any]:
    candidate_gaps = list(candidate_gaps if candidate_gaps is not None else _candidate_gaps(previous_question_text, campaign))
    if active_gap_scope == "unknown":
        active_gap_scope = _active_gap_scope(
            previous_question_type=previous_question_type,
            active_gap=active_gap,
            candidate_gaps=candidate_gaps,
        )
    current_cleared_gaps = list(current_cleared_gaps or [])
    current_confirmed_gaps = list(current_confirmed_gaps or [])
    if answered_gaps is None:
        answered_gaps = _unique(current_cleared_gaps + current_confirmed_gaps + ([target_gap] if target_gap else []))
    outgoing_state = outgoing_question_state_from_response(candidate_response or "", campaign)
    all_cleared_gaps = _unique(list(cleared_gaps) + list(current_cleared_gaps or []))
    all_confirmed_gaps = _unique(list(confirmed_gaps) + list(current_confirmed_gaps or []))
    playbook_gap = primary_gap or target_gap
    playbook = _playbook_trace(
        gap_id=playbook_gap,
        cleared_gaps=all_cleared_gaps,
        confirmed_gaps=all_confirmed_gaps,
        candidate_gaps=candidate_gaps or _core_diagnostic_gaps(campaign),
        campaign=campaign,
    )
    return {
        "semantic_id": SEMANTIC_ID,
        "schema_version": SCHEMA_VERSION,
        "semantic": semantic,
        "target_gap": target_gap,
        "target_topic": target_topic or target_gap,
        "primary_gap": primary_gap or target_gap,
        "secondary_confirmed_gaps": list(secondary_confirmed_gaps or []),
        "active_gap_scope": active_gap_scope,
        "candidate_gaps": list(candidate_gaps or []),
        "answered_gaps": list(answered_gaps or []),
        "cleared_gaps": all_cleared_gaps,
        "confirmed_gaps": all_confirmed_gaps,
        "outgoing_question_type": outgoing_state.get("outgoing_question_type"),
        "outgoing_candidate_gaps": list(outgoing_state.get("outgoing_candidate_gaps") or []),
        "outgoing_active_gap_scope": outgoing_state.get("outgoing_active_gap_scope"),
        "playbook": playbook,
        "playbook_id": playbook.get("playbook_id"),
        "playbook_gap": playbook.get("playbook_gap"),
        "playbook_next_gap": playbook.get("playbook_next_gap"),
        "playbook_review_focus": playbook.get("playbook_review_focus"),
        "playbook_supported_gap_ids": list(playbook.get("playbook_supported_gap_ids") or []),
        "polarity": polarity,
        "confidence": round(float(confidence), 2),
        "evidence": {
            "buyer_utterance": transcript,
            "normalized_buyer_utterance": normalized,
            "previous_agent_question_type": previous_question_type,
            "previous_agent_question_text": previous_question_text,
            "conversation_stage": conversation_stage,
            "active_gap": active_gap,
            "active_gap_scope": active_gap_scope,
            "candidate_gaps": list(candidate_gaps or []),
            "answered_gaps": list(answered_gaps or []),
            "confirmed_gaps": list(confirmed_gaps),
            "cleared_gaps": list(cleared_gaps),
            "current_confirmed_gaps": list(current_confirmed_gaps or []),
            "current_cleared_gaps": list(current_cleared_gaps or []),
            "outgoing_question_type": outgoing_state.get("outgoing_question_type"),
            "outgoing_candidate_gaps": list(outgoing_state.get("outgoing_candidate_gaps") or []),
            "outgoing_active_gap_scope": outgoing_state.get("outgoing_active_gap_scope"),
            "playbook": playbook,
            "pending_callback": pending_callback,
            "pending_appointment": pending_appointment,
        },
        "next_action_hint": next_action_hint,
        "must_not_do": list(must_not_do or []),
        "candidate_response": candidate_response,
        "action_id": action_id,
        "dialogue_focus": dialogue_focus,
        "send_info_state_update": dict(send_info_state_update or {}),
        "lead_followup_state_update": dict(lead_followup_state_update or {}),
        "handoff_target_state_update": dict(handoff_target_state_update or {}),
        "applied": bool(applied and candidate_response and action_id),
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
    }


def _diagnostic_opening_response(language: str, campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return "Thanks. Quick fit check: are missed callbacks, manual tracking, or handoffs creating issues today?"
    labels = [_customer_label(gap, campaign) for gap in _core_diagnostic_gaps(campaign)]
    return f"Thanks, I am checking {_join_or(labels)}. Which one is causing trouble, if any?"


def _all_clear_response(campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return "Understood. If callbacks, manual tracking, and handoffs are all clean, I should not push a review. I will stop here. Goodbye."
    labels = [_customer_label(gap, campaign) for gap in _core_diagnostic_gaps(campaign)]
    return f"Understood. If {_join_or(labels)} are all clean, I should not push a review. I will stop here. Goodbye."


def _not_relevant_mid_call_response(campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return "Understood. Do you mean callbacks and handoffs are not an issue at all, or just this part?"
    labels = [_customer_label(gap, campaign) for gap in _core_diagnostic_gaps(campaign)]
    return f"Understood. Do you mean {_join_or(labels)} are not an issue at all, or just this part?"


def _next_diagnostic_response(language: str, cleared_gap: str | None, confirmed_gaps: list[str], campaign: dict | None) -> str:
    if confirmed_gaps:
        confirmed = _review_focus(confirmed_gaps[0], campaign) or _gap_labels(campaign).get(confirmed_gaps[0], confirmed_gaps[0])
        current = _customer_label(cleared_gap, campaign) if cleared_gap else "that part"
        if not _is_routesignal_playbook(campaign):
            context = _campaign_context(campaign)
            target = str(context.get("appointment_target") or "human review")
            return (
                f"Got it, {current} is clear and {confirmed} is still the part to review. "
                f"The next step would be a short {target}; what time works?"
            )
        return (
            f"Got it, {current} is clear. I still have {confirmed} as the real gap, "
            "so the useful next step is a short workflow review with someone from Northstar. What time works?"
        )
    if language.startswith("de"):
        return "Verstanden. Dann pruefe ich nur eine weitere Luecke: Gehen Rueckrufe, manuelle Nachverfolgung oder Uebergaben manchmal verloren?"
    return _remaining_gap_response(language, [cleared_gap] if cleared_gap else [], _core_diagnostic_gaps(campaign), campaign)


def _multi_gap_clear_response(language: str, candidate_gaps: list[str], campaign: dict | None) -> str:
    if language.startswith("de"):
        return "Verstanden. Wenn diese Follow-up-Luecken sauber sind, druecke ich das nicht weiter. Gibt es eine andere Follow-up-Luecke, oder soll ich hier stoppen?"
    gap_labels = [_gap_labels(campaign).get(gap, gap) for gap in candidate_gaps] or ["those gaps"]
    label = ", ".join(gap_labels[:-1]) + f", and {gap_labels[-1]}" if len(gap_labels) > 1 else gap_labels[0]
    return f"Understood. If {label} are clean, I should not push this further. Is there any other gap worth checking, or should I stop here?"


def _remaining_gap_response(language: str, cleared: list[str], candidate_gaps: list[str], campaign: dict | None) -> str:
    remaining = _remaining_gaps(
        cleared_gaps=cleared,
        candidate_gaps=candidate_gaps or _core_diagnostic_gaps(campaign),
        campaign=campaign,
    )
    if not remaining:
        return _multi_gap_clear_response(language, candidate_gaps, campaign)
    labels = [_customer_label(gap, campaign) for gap in remaining]
    label = " or ".join(labels)
    cleared_labels = [_customer_label(gap, campaign) for gap in cleared if gap]
    if len(cleared_labels) == 1:
        cleared_phrase = _clear_gap_acknowledgement(cleared[0], campaign)
        return f"Got it, {cleared_phrase}. Should I check {label}, or stop here?"
    return f"Got it, those parts are clear. Should I check {label}, or stop here?"


def _clear_gap_acknowledgement(gap: str | None, campaign: dict | None) -> str:
    label = _customer_label(gap, campaign)
    verb = "are" if gap in {"callbacks", "handoffs", "duplicates"} else "is"
    return f"{label} {verb} clear"


def _confusion_response(active_gap: str | None, campaign: dict | None) -> str:
    if not _is_routesignal_playbook(campaign):
        context = _campaign_context(campaign)
        target = str(context.get("appointment_target") or "human review")
        if active_gap:
            label = _customer_label(active_gap, campaign)
            return f"I am asking whether {label} is worth a human review. If it is not an issue, I can stop here."
        labels = [_customer_label(gap, campaign) for gap in _core_diagnostic_gaps(campaign)]
        return (
            f"I am asking whether anything is worth a {target}: {_join_or(labels)}. "
            "If none of those apply, I can stop here."
        )
    if active_gap == "callbacks":
        return "Sorry, I meant callbacks after an inbound demo request. Do those follow-up calls ever get missed?"
    if active_gap == "manual_tracking":
        return "Sorry, I meant the manual notes or spreadsheet steps after a demo request. Does that tracking ever slow follow-up down?"
    if active_gap == "handoffs":
        return "Sorry, I meant the step where the right person owns the next reply. Do those handoffs ever get missed?"
    return "Sorry, I meant the follow-up after an inbound demo request: callbacks, manual tracking, or handoffs. Which part causes trouble, if any?"


def _term_response(previous_question: str | None, normalized: str = "") -> str:
    previous = session_policy.normalize_text(previous_question or "")
    if _contains(previous, {"growth"}) or _contains(normalized, {"growth"}):
        return (
            "Sorry, I should have explained that. Growth is the RouteSignal setup for teams that need "
            "follow-up reminders and handoff review around inbound demo requests. Would that be worth a short workflow review?"
        )
    if _contains(previous, {"workflow review", "short workflow"}):
        return (
            "I mean a short call with someone from Northstar to look at where demo follow-up gets missed. "
            "It is not a contract or payment step. Is the callback or handoff gap worth reviewing?"
        )
    return "I mean the follow-up workflow after someone requests a demo: who owns the next reply, callback, and handoff."


def _callback_time_request_response(language: str, normalized: str) -> str:
    if language.startswith("de"):
        return "Kein Problem. Zu welcher Zeit soll ich zurueckrufen?"
    if _contains(normalized, {"try next week", "next week"}):
        return "No problem. Next week can work. What day and time should I call back?"
    return "No problem. What time should I call back?"


def _appointment_time_confirmed_response(language: str, campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return session_policy.appointment_time_confirmed_response(language)
    target = str(_campaign_context(campaign).get("appointment_target") or "human review")
    if language.startswith("de"):
        return f"Bestaetigt. Ich notiere diese Zeit fuer die {target}. Auf Wiederhoeren."
    return f"Confirmed. I will note that time for the {target}. Goodbye."


def _send_info_request_response(target_gap: str | None, campaign: dict | None) -> str:
    if target_gap:
        gap_label = _review_focus(target_gap, campaign) or _gap_labels(campaign).get(target_gap, target_gap)
        return f"No problem. I can send a short summary focused on {gap_label}. What email or callback time should I note?"
    return "No problem. I can keep it to a short written summary. What email or callback time should I note?"


def _wrong_person_response(campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return "Understood. Who is the right person or team for demo follow-up, or should I stop here?"
    context = _campaign_context(campaign)
    target = str(context.get("appointment_target") or "this review")
    return f"Understood. Who is the right person or team for {target}, or should I stop here?"


def _is_generic_claim_boundary_question(normalized: str, raw_text: str, campaign: dict | None) -> bool:
    if _is_routesignal_playbook(campaign):
        return False
    if "?" not in str(raw_text or "") and not normalized.startswith(("can ", "does ", "do ", "is ", "are ")):
        return False
    return _contains(
        normalized,
        {
            "integrate",
            "integration",
            "salesforce",
            "hubspot",
            "crm",
            "security",
            "secure",
            "compliance",
            "compliant",
            "guarantee",
            "guaranteed",
            "promise",
            "promised",
            "covered",
            "coverage",
            "exact price",
            "price without",
            "without looking",
            "exact quote",
            "exact estimate",
            "repair cost",
            "refund",
            "warranty",
            "cancellation terms",
            "hide cancellation",
            "hide terms",
            "equipment solves",
        },
    )


def _is_generic_product_detail_scope_question(normalized: str, campaign: dict | None) -> bool:
    if _is_routesignal_playbook(campaign) or not session_policy.is_generic_campaign_config(campaign):
        return False
    if session_policy.is_generic_product_detail_limitation_ack(normalized):
        return True
    return _contains(
        normalized,
        {
            "what does your product",
            "what does the product",
            "what do you do",
            "what does it do",
            "what is your product",
            "what your product do",
            "what your product does",
            "product actually do",
            "product details",
            "what is included",
            "what s included",
            "whats included",
            "can you give me information",
            "can you give me details",
            "give me information about the product",
            "give me details about the product",
        },
    )


def _generic_product_detail_scope_response(language: str, normalized: str, campaign: dict | None) -> str:
    if session_policy.is_generic_product_detail_limitation_ack(normalized):
        repeated = _contains(normalized, {"only a licensed", "only a license", "only licensed", "only license"})
        return session_policy.generic_campaign_product_detail_limitation_text(language, campaign, repeated=repeated)
    return session_policy.generic_campaign_product_detail_text(language, campaign)


def _is_account_support_boundary_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "password",
            "reset password",
            "account access",
            "log in",
            "login",
            "sign in",
            "support ticket",
            "help with my account",
            "help with my password",
            "handle my claim",
            "help with my claim",
            "claim status",
            "change my plan",
            "change the plan",
            "check my warranty",
            "warranty status",
            "help with my order",
            "order status",
            "cancel my account",
            "cancel account",
            "cancel my subscription",
            "cancel subscription",
        },
    )


def _account_support_boundary_response(normalized: str, campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        return "I cannot help with password or account support on this call. I can keep this to the RouteSignal workflow review topic, or stop here."
    vertical = str((campaign or {}).get("vertical_id") or "")
    owner = str(_campaign_context(campaign).get("human_followup_owner") or (campaign or {}).get("human_followup_owner") or "a human")
    owner_phrase = session_policy.generic_campaign_role_phrase(owner)
    if vertical == "insurance" or _contains(normalized, {"handle my claim", "help with my claim", "claim status"}):
        return "I cannot handle claim support on this call. Please use the authorized support path; I can keep this to the review topic, or stop here."
    if vertical == "telecom" or _contains(normalized, {"change my plan", "change the plan"}):
        return "I cannot change account plans on this call. Please use the authorized support path; I can keep this to the review topic, or stop here."
    if vertical == "automotive_service" or _contains(normalized, {"check my warranty", "warranty status"}):
        return "I cannot check warranty support on this call. Please use the authorized support path; I can keep this to the review topic, or stop here."
    if vertical == "membership_or_subscription" or _contains(normalized, {"cancel my account", "cancel account", "cancel my subscription", "cancel subscription"}):
        return "I cannot cancel or change an account on this call. Please use authorized account support; I can stop here."
    if vertical == "retail_or_ecommerce_support_sales" or _contains(normalized, {"help with my order", "order status"}):
        return "I cannot handle order support on this call. Please use the support team for order details; I can stop here."
    return f"I cannot help with account support on this call. If useful, {owner_phrase} can follow up separately, or I can stop here."


def _next_step_after_confirmed_pain_response(gap_id: str | None, campaign: dict | None) -> str:
    if _is_routesignal_playbook(campaign):
        if gap_id == "handoffs":
            focus = "handoffs getting messy"
        else:
            focus = _review_focus(gap_id or "", campaign) or _customer_label(gap_id, campaign)
        return (
            f"The next step is a short workflow review focused on {focus}. "
            "Someone from Northstar can review it; I can note a callback time, or leave it here."
        )
    context = _campaign_context(campaign)
    target = str(context.get("appointment_target") or "human review")
    owner = str(context.get("human_followup_owner") or "qualified specialist")
    owner_phrase = session_policy.generic_campaign_role_phrase(owner)
    focus = _review_focus(gap_id or "", campaign) or _customer_label(gap_id, campaign)
    return (
        f"The next step would be a short {target} focused on {focus}. "
        f"{session_policy.sentence_start(owner_phrase)} can review it. "
        "If you want, I can note a callback time, or leave it here."
    )


def _claim_boundary_gap(campaign: dict | None) -> str | None:
    for candidate in [
        "coverage_fit",
        "coverage_or_availability",
        "estimate_or_property_details",
        "specialist_review_needed",
        "equipment_or_service_fit",
        "warranty_or_estimate",
        "renewal_or_cancellation",
        "return_or_warranty",
        "integration_risk",
        "compliance_or_security",
        "security_review",
        "fit",
    ]:
        if candidate in set(_supported_gap_ids(campaign)):
            return candidate
    return None


def _generic_claim_boundary_response(campaign: dict | None, target_gap: str | None = None) -> str:
    context = _campaign_context(campaign)
    owner = str(context.get("human_followup_owner") or "qualified human specialist")
    owner_phrase = session_policy.generic_campaign_role_phrase(owner)
    owner_sentence = session_policy.sentence_start(owner_phrase)
    vertical = str(_resolved_playbook(campaign).get("vertical_id") or "")
    review = _review_focus(target_gap or "", campaign) or _customer_label(target_gap, campaign)
    if vertical == "insurance":
        return (
            f"I cannot promise coverage here. {owner_sentence} needs verified policy details before any coverage answer. "
            f"Is {review} what you want reviewed?"
        )
    if vertical == "telecom":
        return (
            f"I cannot promise service coverage here. {owner_sentence} needs verified address, plan, and account details before any coverage answer. "
            f"Is {review} what you want reviewed?"
        )
    if vertical == "home_services":
        return (
            f"I cannot give an exact price without property details or inspection. {owner_sentence} needs verified details before quoting. "
            f"Is {review} what you want reviewed?"
        )
    if vertical == "healthcare_admin_or_medical_equipment":
        return (
            f"I cannot promise an equipment or service outcome here. {owner_sentence} needs verified admin and specialist details first. "
            f"Is {review} what you want reviewed?"
        )
    if vertical == "automotive_service":
        return (
            f"I cannot promise repair cost or warranty outcome here. {owner_sentence} needs verified vehicle details or inspection first. "
            f"Is {review} what you want reviewed?"
        )
    if vertical == "membership_or_subscription":
        return (
            f"I cannot hide cancellation terms or make account-specific billing promises. {owner_sentence} should review the policy details transparently. "
            f"Is {review} what you want reviewed?"
        )
    if vertical == "retail_or_ecommerce_support_sales":
        return (
            f"I cannot promise a refund, warranty, stock, or delivery outcome here. {owner_sentence} needs verified policy and order details first. "
            f"Is {review} what you want reviewed?"
        )
    return (
        "I cannot verify that claim here. Exact integration, security, or setup fit needs verified material "
        f"and review by {owner_phrase} before I claim it. Is that the gap you want reviewed?"
    )


def _send_info_state_update(
    *,
    requested_at_turn: int,
    requested_summary_type: str,
    capture_status: str,
    captured_email_redacted: str | None = None,
    captured_callback_time: str | None = None,
    human_followup_needed: bool = True,
    lead_status: str = "open_send_info",
) -> dict[str, Any]:
    return {
        "requested": True,
        "requested_at_turn": requested_at_turn,
        "requested_summary_type": requested_summary_type,
        "capture_status": capture_status,
        "captured_email_redacted": captured_email_redacted,
        "captured_callback_time": captured_callback_time,
        "human_followup_needed": human_followup_needed,
        "lead_status": lead_status,
        "stores_private_contact_in_public_evidence": False,
    }


def _lead_followup_state_update(
    *,
    lead_status: str,
    capture_status: str,
    requested_summary_type: str,
    email: str | None = None,
    email_source: str = "none",
    callback: dict[str, Any] | None = None,
    appointment_type: str = "none",
    appointment_confirmed: bool = False,
    confirmation_text: str | None = None,
) -> dict[str, Any]:
    callback_state = callback or {
        "raw_text_redacted": None,
        "normalized": _empty_callback_normalized(),
        "needs_clarification": False,
    }
    return {
        "schema_version": 1,
        "lead_status": lead_status,
        "capture_status": capture_status,
        "requested_summary_type": requested_summary_type,
        "contact": {
            "email_redacted": _redact_email(email),
            "email_hash": _email_hash(email),
            "raw_email_stored_in_public_evidence": False,
            "email_source": email_source if email else "none",
            "email_valid": bool(email),
        },
        "callback": callback_state,
        "appointment": {
            "type": appointment_type,
            "confirmed": bool(appointment_confirmed),
            "confirmation_text": confirmation_text,
        },
        "safety": {
            "provider_calls_made": False,
            "local_llm_calls_made": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "stores_private_contact_in_public_evidence": False,
        },
    }


def _handoff_target_state_update(
    *,
    reason: str,
    capture_status: str,
    lead_status: str,
    person_name: str | None = None,
    role_or_department: str | None = None,
    email: str | None = None,
    phone_redacted: str | None = None,
    human_followup_needed: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "requested": True,
        "reason": reason,
        "capture_status": capture_status,
        "target": {
            "person_name_redacted": person_name,
            "role_or_department": role_or_department,
            "email_redacted": _redact_email(email),
            "email_hash": _email_hash(email),
            "phone_redacted": phone_redacted,
            "raw_contact_stored_in_public_evidence": False,
        },
        "lead_status": lead_status,
        "human_followup_needed": bool(human_followup_needed),
        "safety": {
            "provider_calls_made": False,
            "local_llm_calls_made": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "stores_private_contact_in_public_evidence": False,
        },
    }


def _pain_confirmed_response(
    language: str,
    gap: str | None,
    campaign: dict | None,
    *,
    acknowledge_repeat: bool = False,
) -> str:
    if language.startswith("de"):
        return session_policy.appointment_lead_close_response(language, gap)
    review_label = _review_focus(gap or "", campaign) or "that gap"
    gap_label = "missed callbacks" if gap == "callbacks" else review_label
    bridge = _value_bridge(gap, campaign)
    if not _is_routesignal_playbook(campaign):
        acknowledgement = (
            f"Got it, you already said {gap_label} is the issue. "
            if acknowledge_repeat
            else "Got it, that sounds like the part worth reviewing. "
        )
        context = _campaign_context(campaign)
        target = str(context.get("appointment_target") or "human review")
        return (
            f"{acknowledgement.rstrip()} "
            f"The next step would be a short {target}; what time works for that review?"
        )
    if acknowledge_repeat and gap == "handoffs":
        acknowledgement = "You're right, you already said handoffs get messy. "
    else:
        acknowledgement = (
            f"Got it, you already said that is the problem: {gap_label}. "
            if acknowledge_repeat
            else f"Got it, {gap_label} is the real gap. "
        )
    return (
        f"{acknowledgement}{bridge} "
        "The next step is a short workflow review with someone from Northstar. "
        f"They would check {review_label} against your actual follow-up flow. What time works for a quick call?"
    )


def classify_contextual_buyer_semantics(
    transcript: str,
    session_state: dict | None,
    campaign: dict | None,
    *,
    dialogue_reasoning: dict | None = None,
) -> dict[str, Any]:
    del dialogue_reasoning
    campaign = dict(campaign or {})
    build_frame = globals()["_frame"]

    def _frame(**kwargs: Any) -> dict[str, Any]:
        return build_frame(campaign=campaign, **kwargs)

    language = str(campaign.get("language") or "en")
    normalized = session_policy.normalize_text(transcript)
    turns = _turns(session_state)
    previous_response = _previous_response(turns)
    previous_question = session_policy.previous_agent_question(turns)
    previous_question_type = session_policy.question_type_from_response(previous_question or previous_response)
    confirmed_gaps = _list_from_memory(turns, "confirmed_gaps", campaign)
    cleared_gaps = _list_from_memory(turns, "cleared_gaps", campaign)
    prior_send_info_state = _previous_send_info_state(turns)
    send_info_open = _send_info_capture_open(prior_send_info_state)
    candidate_gaps = _previous_outgoing_candidate_gaps(turns, campaign) or _candidate_gaps(previous_question, campaign)
    active_gap = _active_gap(turns, previous_question, normalized, previous_candidate_gaps=candidate_gaps, campaign=campaign)
    active_gap_scope = _active_gap_scope(
        previous_question_type=previous_question_type,
        active_gap=active_gap,
        candidate_gaps=candidate_gaps,
    )
    current_clear_gaps = _clear_gaps_from_text(normalized, campaign)
    if active_gap and current_clear_gaps and _is_contextual_gap_reference(normalized):
        current_clear_gaps = [active_gap]
    current_confirmed_gaps = _confirmed_gaps_from_text(normalized, campaign)
    current_confirmed_gaps = [gap for gap in current_confirmed_gaps if gap not in set(current_clear_gaps)]
    final_save_pending = _final_save_pending(turns, previous_question)
    pending_callback = _pending_callback(turns, previous_question_type)
    pending_appointment = _pending_appointment(turns, previous_question_type)
    prior_handoff_state = _previous_handoff_target_state(turns)
    handoff_open = _handoff_capture_open(prior_handoff_state)
    stage = _conversation_stage(
        turn_count=len(turns),
        previous_question_type=previous_question_type,
        pending_callback=pending_callback,
        pending_appointment=pending_appointment,
        confirmed_gaps=confirmed_gaps,
        cleared_gaps=cleared_gaps,
    )

    if not normalized or session_policy.is_agent_open_turn(normalized):
        return _frame(
            semantic="no_contextual_semantic",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            confidence=0.0,
            applied=False,
        )

    if session_policy.is_buyer_stop_request(normalized) or _is_terminal_stop_request(normalized):
        return _frame(
            semantic="stop_request",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="refusal",
            confidence=0.96,
            next_action_hint="end_politely",
            must_not_do=["continue selling", "ask appointment"],
            candidate_response="Understood. I will stop here. Goodbye.",
            action_id="end_call_stop_request",
            dialogue_focus=active_gap or "qualification",
        )

    if not _is_routesignal_playbook(campaign) and _is_account_support_boundary_question(normalized):
        return _frame(
            semantic="account_support_boundary",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="account_support",
            polarity="out_of_scope",
            confidence=0.9,
            next_action_hint="safe_support_boundary",
            must_not_do=["provide account support", "invent support action", "push sales review"],
            candidate_response=_account_support_boundary_response(normalized, campaign),
            action_id="account_support_boundary",
            dialogue_focus="qualification",
        )

    if _is_confusion(normalized):
        return _frame(
            semantic="confusion_not_clear",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="confused",
            confidence=0.94,
            next_action_hint="clarify_previous_question",
            must_not_do=["classify as all clear", "push appointment"],
            candidate_response=_confusion_response(active_gap, campaign),
            action_id="clarify_previous_question",
            dialogue_focus=active_gap or "qualification",
        )

    if final_save_pending and _is_final_save_all_scope(normalized):
        return _frame(
            semantic="not_relevant_late",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="campaign_relevance",
            polarity="not_relevant",
            confidence=0.92,
            next_action_hint="end_politely",
            must_not_do=["repeat diagnostics", "push workflow review"],
            candidate_response="Understood. I will stop here. Goodbye.",
            action_id="end_call_stop_request",
            dialogue_focus="qualification",
        )

    if send_info_open:
        email, email_source = _extract_contact_email(transcript)
        redacted_email = _redact_email(email)
        callback_state = _normalize_callback_time(transcript)
        has_callback_attempt = _has_callback_time_attempt(transcript, normalized)
        has_usable_callback_time = has_callback_attempt and not bool(callback_state.get("needs_clarification"))
        callback_time = callback_state.get("raw_text_redacted") if has_usable_callback_time else None
        requested_at_turn = int(prior_send_info_state.get("requested_at_turn") or len(turns))
        summary_type = str(prior_send_info_state.get("requested_summary_type") or "unknown")
        if email and has_usable_callback_time:
            return _frame(
                semantic="contact_detail_provided",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="contact_captured",
                confidence=0.94,
                next_action_hint="confirm_callback_and_end",
                must_not_do=["repeat raw email", "confirm appointment"],
                candidate_response="Got it. I will note that email for the summary and that callback time. Goodbye.",
                action_id="capture_send_info_email_and_callback",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="email_and_callback_time_captured",
                    captured_email_redacted=redacted_email,
                    captured_callback_time=callback_time,
                    lead_status="open_callback",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_callback",
                    capture_status="email_and_callback_time_captured",
                    requested_summary_type=summary_type,
                    email=email,
                    email_source=email_source,
                    callback=callback_state,
                    appointment_type="send_info_followup",
                    appointment_confirmed=True,
                    confirmation_text="send-info callback time captured",
                ),
            )
        if email:
            return _frame(
                semantic="email_provided",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="contact_captured",
                confidence=0.94,
                next_action_hint="note_summary_contact",
                must_not_do=["repeat raw email", "confirm appointment", "schedule without time"],
                candidate_response="Got it. I will note that email for the short summary. Do you want a callback too, or should I leave it at the summary?",
                action_id="capture_send_info_email",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="email_captured",
                    captured_email_redacted=redacted_email,
                    lead_status="open_send_info",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_send_info",
                    capture_status="email_captured",
                    requested_summary_type=summary_type,
                    email=email,
                    email_source=email_source,
                    appointment_type="send_info_followup",
                    appointment_confirmed=False,
                ),
            )
        if has_usable_callback_time:
            return _frame(
                semantic="callback_time_provided",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="time_given",
                confidence=0.94,
                next_action_hint="confirm_callback_and_end",
                must_not_do=["invent email", "confirm appointment"],
                candidate_response=session_policy.callback_time_confirmed_response(language, campaign),
                action_id="capture_send_info_callback_time",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="callback_time_captured",
                    captured_callback_time=callback_time,
                    lead_status="open_callback",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_callback",
                    capture_status="callback_time_captured",
                    requested_summary_type=summary_type,
                    callback=callback_state,
                    appointment_type="send_info_followup",
                    appointment_confirmed=True,
                    confirmation_text="send-info callback time captured",
                ),
            )
        if _is_send_info_contact_refusal(normalized):
            return _frame(
                semantic="send_info_refused_contact",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="refused_contact",
                confidence=0.92,
                next_action_hint="end_politely",
                must_not_do=["repeat send-info pressure", "ask appointment"],
                candidate_response="Understood. I will not send anything. I will stop here. Goodbye.",
                action_id="close_send_info_refused",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="refused_contact",
                    human_followup_needed=False,
                    lead_status="closed_refused",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="closed_refused",
                    capture_status="refused_contact",
                    requested_summary_type=summary_type,
                    appointment_type="none",
                    appointment_confirmed=False,
                ),
            )
        if has_callback_attempt:
            return _frame(
                semantic="callback_time_unclear",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="unclear_time",
                confidence=0.86,
                next_action_hint="request_concrete_callback_time",
                must_not_do=["schedule without day and time", "invent callback time"],
                candidate_response="I can note that. What specific day and time should I use, or what email should I send the summary to?",
                action_id="clarify_send_info_contact",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="needs_email_or_callback_time",
                    lead_status="open_send_info",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_send_info",
                    capture_status="contact_unclear",
                    requested_summary_type=summary_type,
                    callback=callback_state,
                    appointment_type="send_info_followup",
                    appointment_confirmed=False,
                ),
            )
        if _looks_like_unclear_email_attempt(normalized, transcript):
            return _frame(
                semantic="contact_detail_unclear",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="unclear_contact",
                confidence=0.88,
                next_action_hint="request_contact_again",
                must_not_do=["capture invalid email", "confirm callback"],
                candidate_response="Sorry, I did not catch a valid email. Could you repeat the email, or give me a callback time instead?",
                action_id="clarify_send_info_contact",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="needs_email_or_callback_time",
                    lead_status="open_send_info",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_send_info",
                    capture_status="contact_unclear",
                    requested_summary_type=summary_type,
                    appointment_type="send_info_followup",
                    appointment_confirmed=False,
                ),
            )
        if _is_low_information_ack(normalized) or _is_send_info_request(normalized):
            return _frame(
                semantic="send_info_affirmed_without_contact",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="missing_contact",
                confidence=0.91,
                next_action_hint="request_contact_again",
                must_not_do=["confirm appointment", "confirm callback without time"],
                candidate_response="Sure. What email should I note for the summary, or what callback time should I use?",
                action_id="request_send_info_contact",
                dialogue_focus="timing",
                send_info_state_update=_send_info_state_update(
                    requested_at_turn=requested_at_turn,
                    requested_summary_type=summary_type,
                    capture_status="needs_email_or_callback_time",
                    lead_status="open_send_info",
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_send_info",
                    capture_status="needs_contact",
                    requested_summary_type=summary_type,
                    appointment_type="send_info_followup",
                    appointment_confirmed=False,
                ),
            )

    if handoff_open:
        email, _email_source = _extract_contact_email(transcript)
        callback_state = _normalize_callback_time(transcript)
        has_callback_attempt = _has_callback_time_attempt(transcript, normalized)
        has_usable_callback_time = has_callback_attempt and not bool(callback_state.get("needs_clarification"))
        prior_target = dict(prior_handoff_state.get("target") or {})
        person_name = _person_name_from_text(transcript) or prior_target.get("person_name_redacted")
        department = _department_from_text(normalized) or prior_target.get("role_or_department")
        requested_reason = str(prior_handoff_state.get("reason") or "wrong_person")
        if email:
            response_target = person_name or department or "the right person"
            return _frame(
                semantic="right_person_email_provided",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=None,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_topic="right_person_handoff",
                polarity="contact_captured",
                confidence=0.94,
                next_action_hint="note_right_person_contact",
                must_not_do=["send email", "write CRM", "confirm workflow review"],
                candidate_response=(
                    f"Got it. I will note that contact for {response_target} "
                    "so a human can follow up through the right path. I will not send anything from this call."
                ),
                action_id="capture_right_person_contact",
                dialogue_focus="handoff",
                handoff_target_state_update=_handoff_target_state_update(
                    reason=requested_reason,
                    capture_status="contact_detail_captured",
                    lead_status="open_send_info_to_right_person",
                    person_name=person_name,
                    role_or_department=department,
                    email=email,
                ),
            )
        if has_usable_callback_time:
            response_target = person_name or department or "the right person"
            return _frame(
                semantic="right_person_callback_time_provided",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=None,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_topic="right_person_handoff",
                polarity="time_given",
                confidence=0.93,
                next_action_hint="confirm_right_person_callback",
                must_not_do=["invent email", "write CRM"],
                candidate_response=f"Got it. I will note that {response_target} should be called at that time. Goodbye.",
                action_id="capture_right_person_callback_time",
                dialogue_focus="timing",
                handoff_target_state_update=_handoff_target_state_update(
                    reason=requested_reason,
                    capture_status="contact_detail_captured",
                    lead_status="open_callback_for_right_person",
                    person_name=person_name,
                    role_or_department=department,
                ),
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_callback",
                    capture_status="callback_time_captured",
                    requested_summary_type="right_person_handoff",
                    callback=callback_state,
                    appointment_type="right_person_callback",
                    appointment_confirmed=True,
                    confirmation_text="right-person callback time captured",
                ),
            )
        if _is_refused_right_person_contact(normalized):
            return _frame(
                semantic="refused_right_person_contact",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=None,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_topic="right_person_handoff",
                polarity="refused_contact",
                confidence=0.88,
                next_action_hint="close_wrong_person",
                must_not_do=["repeat pressure", "push workflow review"],
                candidate_response="No problem. I will stop here. Goodbye.",
                action_id="close_wrong_person",
                dialogue_focus="handoff",
                handoff_target_state_update=_handoff_target_state_update(
                    reason=requested_reason,
                    capture_status="refused_to_provide",
                    lead_status="closed_wrong_person",
                    person_name=person_name,
                    role_or_department=department,
                    human_followup_needed=False,
                ),
            )
        if has_callback_attempt:
            return _frame(
                semantic="right_person_contact_unclear",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=None,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_topic="right_person_handoff",
                polarity="unclear_contact",
                confidence=0.84,
                next_action_hint="request_right_person_contact_again",
                must_not_do=["schedule without usable time"],
                candidate_response="I need a clearer day and time, or an email for the right person. What should I note?",
                action_id="clarify_right_person_contact",
                dialogue_focus="handoff",
                handoff_target_state_update=_handoff_target_state_update(
                    reason=requested_reason,
                    capture_status="contact_unclear",
                    lead_status="open_right_person_handoff",
                    person_name=person_name,
                    role_or_department=department,
                ),
            )
        if _is_account_support_boundary_question(normalized):
            response_target = person_name or department or "the right contact"
            return _frame(
                semantic="handoff_support_boundary",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=None,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_topic="right_person_handoff",
                polarity="out_of_scope",
                confidence=0.88,
                next_action_hint="request_right_person_contact_again",
                must_not_do=["select product routing gap", "provide account support"],
                candidate_response=(
                    f"I cannot help with account support on this call. "
                    f"I can keep {response_target} noted as the right contact path, or stop here."
                ),
                action_id="request_right_person_contact",
                dialogue_focus="handoff",
                handoff_target_state_update=_handoff_target_state_update(
                    reason=requested_reason,
                    capture_status="needs_right_person",
                    lead_status="open_right_person_handoff",
                    person_name=person_name,
                    role_or_department=department,
                ),
            )

    if _is_account_support_boundary_question(normalized):
        return _frame(
            semantic="account_support_boundary" if _is_routesignal_playbook(campaign) else "vertical_support_boundary",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="account_support_boundary",
            polarity="out_of_scope",
            confidence=0.91,
            next_action_hint="answer_support_boundary_or_stop",
            must_not_do=["provide account support", "reopen diagnostic", "push appointment"],
            candidate_response=_account_support_boundary_response(normalized, campaign),
            action_id="continue_with_session_policy",
            dialogue_focus="support_boundary",
        )

    if confirmed_gaps and _is_repeat_problem_reference(normalized):
        selected_gap = confirmed_gaps[0]
        return _frame(
            semantic="already_stated_confirmed_pain",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=selected_gap,
            primary_gap=selected_gap,
            polarity="repeat_context",
            confidence=0.9,
            next_action_hint="acknowledge_confirmed_pain_and_offer_next_step",
            must_not_do=["ask buyer to repeat pain", "treat as stop request"],
            candidate_response=_pain_confirmed_response(language, selected_gap, campaign, acknowledge_repeat=True),
            action_id="request_appointment_time",
            dialogue_focus="timing",
        )

    if confirmed_gaps and session_policy.is_next_step_question(normalized):
        selected_gap = confirmed_gaps[0]
        return _frame(
            semantic="next_step_question_after_confirmed_pain",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=selected_gap,
            primary_gap=selected_gap,
            polarity="process_question",
            confidence=0.9,
            next_action_hint="explain_next_step_after_confirmed_pain",
            must_not_do=["request callback time as if already offered", "erase confirmed pain"],
            candidate_response=_next_step_after_confirmed_pain_response(selected_gap, campaign),
            action_id="continue_with_session_policy",
            dialogue_focus="timing",
        )

    if not confirmed_gaps and normalized in {"maybe", "maybe yes", "possibly", "perhaps", "not sure", "i am not sure", "i m not sure", "im not sure"}:
        response = (
            session_policy.uncertain_qualification_response(language, campaign)
            if "sure" in normalized
            else session_policy.tentative_qualification_response(language, campaign)
        )
        return _frame(
            semantic="uncertainty_after_diagnostic",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="uncertain",
            confidence=0.82,
            next_action_hint="clarify_or_stop_without_appointment_pressure",
            must_not_do=["confirm pain", "push appointment", "repeat full diagnostic loop"],
            candidate_response=response,
            action_id="clarify_previous_question",
            dialogue_focus="qualification",
        )

    if _is_not_interested(normalized):
        return _frame(
            semantic="not_interested",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="refusal",
            confidence=0.95,
            next_action_hint="end_politely",
            must_not_do=["continue selling"],
            candidate_response="Understood. I will stop here. Goodbye.",
            action_id="end_call_stop_request",
            dialogue_focus=active_gap or "qualification",
        )

    if _is_generic_product_detail_scope_question(normalized, campaign):
        selected_gap = (confirmed_gaps[0] if confirmed_gaps else None) or _gap_from_text(normalized, campaign) or active_gap
        semantic = (
            "cannot_provide_product_details_acknowledged"
            if session_policy.is_generic_product_detail_limitation_ack(normalized)
            else "product_detail_limit_question"
        )
        return _frame(
            semantic=semantic,
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=selected_gap,
            target_topic=selected_gap or "product_detail_scope",
            polarity="scope_limit",
            confidence=0.9,
            next_action_hint="answer_scope_limit_continue",
            must_not_do=["give regulated product advice", "invent product details", "escalate without buyer request"],
            candidate_response=_generic_product_detail_scope_response(language, normalized, campaign),
            action_id="answer_product_detail_scope_limit",
            dialogue_focus="details",
        )

    if _is_generic_claim_boundary_question(normalized, transcript, campaign):
        target_gap = _claim_boundary_gap(campaign)
        return _frame(
            semantic="campaign_claim_boundary_caution",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=target_gap,
            target_topic=target_gap or "campaign_claim_boundary",
            polarity="caution",
            confidence=0.88,
            next_action_hint="answer_cautiously_continue",
            must_not_do=["claim integration fit", "claim security proof", "invent setup details"],
            candidate_response=_generic_claim_boundary_response(campaign, target_gap),
            action_id="answer_campaign_claim_boundary",
            dialogue_focus="details",
        )

    if _is_not_relevant(normalized, stage=stage, active_gap=active_gap):
        if stage == "opening":
            semantic = "not_relevant_early"
            response = "Understood. If this is not relevant, I will stop here. Goodbye."
            action_id = "end_call_stop_request"
            hint = "end_politely"
            target_gap = None
            target_topic = "campaign_relevance"
        elif len(cleared_gaps) + len(confirmed_gaps) >= 2 or len(turns) >= 4:
            semantic = "not_relevant_late"
            response = "Understood. I will stop here. Goodbye."
            action_id = "end_call_stop_request"
            hint = "end_politely"
            target_gap = active_gap
            target_topic = active_gap
        else:
            semantic = "not_relevant_mid_call"
            response = _not_relevant_mid_call_response(campaign)
            action_id = "continue_with_session_policy"
            hint = "one_final_save_question"
            target_gap = active_gap
            target_topic = active_gap
        return _frame(
            semantic=semantic,
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=target_gap,
            target_topic=target_topic,
            polarity="not_relevant",
            confidence=0.94,
            next_action_hint=hint,
            must_not_do=["push workflow review", "repeat diagnostics"],
            candidate_response=response,
            action_id=action_id,
            dialogue_focus=active_gap or "qualification",
        )

    if _is_timing_soft_deferral(normalized):
        return _frame(
            semantic="callback_scheduling_request",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="defer_timing",
            confidence=0.9,
            next_action_hint="request_callback_time",
            must_not_do=["classify as no pain", "push appointment"],
            candidate_response=_callback_time_request_response(language, normalized),
            action_id="request_callback_time",
            dialogue_focus="timing",
        )

    if previous_question_type == "permission_check" and _is_permission_ack(normalized):
        return _frame(
            semantic="permission_acknowledgement",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="permission_granted",
            confidence=0.94,
            next_action_hint="start_diagnostic",
            must_not_do=["classify as no pain", "ask appointment"],
            candidate_response=_diagnostic_opening_response(language, campaign),
            action_id="continue_with_session_policy",
            dialogue_focus="qualification",
        )

    if pending_callback and _is_low_information_ack(normalized):
        return _frame(
            semantic="low_information_continue",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="acknowledgement",
            confidence=0.9,
            next_action_hint="request_callback_time_again",
            must_not_do=["classify as no pain", "end call without time"],
            candidate_response="No problem. What time should I call back?",
            action_id="request_callback_time",
            dialogue_focus="timing",
        )

    if pending_appointment and previous_question_type == "appointment_time" and _is_low_information_ack(normalized):
        return _frame(
            semantic="appointment_affirmed_without_time",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="appointment_interest_without_time",
            confidence=0.93,
            next_action_hint="request_appointment_time_again",
            must_not_do=["end call without appointment time"],
            candidate_response=session_policy.appointment_time_followup_response(
                language,
                active_gap,
                session_policy.appointment_time_request_count(turns),
            ),
            action_id="request_appointment_time",
            dialogue_focus="timing",
        )

    if pending_appointment and previous_question_type in {"workflow_review_next_step", "value_review_check", "summary_next_step"} and _is_low_information_ack(normalized):
        return _frame(
            semantic="appointment_review_interest",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="appointment_interest",
            confidence=0.94,
            next_action_hint="request_appointment_time",
            must_not_do=["repeat diagnostic"],
            candidate_response=session_policy.appointment_time_followup_response(language, active_gap, 0),
            action_id="request_appointment_time",
            dialogue_focus="timing",
        )

    if pending_appointment and _is_appointment_hesitation(normalized):
        return _frame(
            semantic="appointment_hesitation",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="hesitation",
            confidence=0.9,
            next_action_hint="offer_summary_and_callback_time",
            must_not_do=["treat as stop request", "end without callback option"],
            candidate_response=session_policy.appointment_think_about_it_response(language, active_gap),
            action_id="request_callback_time",
            dialogue_focus="timing",
        )

    if previous_question_type == "callback_time" and _has_callback_time_attempt(transcript, normalized):
        callback_state = _normalize_callback_time(transcript)
        if bool(callback_state.get("needs_clarification")):
            return _frame(
                semantic="callback_time_unclear",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                polarity="unclear_time",
                confidence=0.86,
                next_action_hint="request_concrete_callback_time",
                must_not_do=["schedule without day and time"],
                candidate_response=_callback_time_request_response(language, normalized),
                action_id="request_callback_time",
                dialogue_focus="timing",
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_callback",
                    capture_status="contact_unclear",
                    requested_summary_type="unknown",
                    callback=callback_state,
                    appointment_type="callback",
                    appointment_confirmed=False,
                ),
            )
        return _frame(
            semantic="callback_time_confirmation",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="time_given",
            confidence=0.94,
            next_action_hint="confirm_callback_and_end",
            candidate_response=session_policy.callback_time_confirmed_response(language, campaign),
            action_id="confirm_callback_and_end",
            dialogue_focus="timing",
            lead_followup_state_update=_lead_followup_state_update(
                lead_status="open_callback",
                capture_status="callback_time_captured",
                requested_summary_type="unknown",
                callback=callback_state,
                appointment_type="callback",
                appointment_confirmed=not bool(callback_state.get("needs_clarification")),
                confirmation_text="callback time captured",
            ),
        )

    if previous_question_type == "appointment_time" and (
        session_policy.has_appointment_time_confirmation_signal(normalized, session_state)
        or _has_callback_time_attempt(transcript, normalized)
    ):
        callback_state = _normalize_callback_time(transcript)
        if bool(callback_state.get("needs_clarification")):
            return _frame(
                semantic="appointment_time_unclear",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_gap=active_gap,
                polarity="unclear_time",
                confidence=0.86,
                next_action_hint="request_appointment_time_again",
                must_not_do=["schedule without day and time"],
                candidate_response="No problem. Next week can work, but I need a specific day and time for the workflow review. What day and time works?",
                action_id="request_appointment_time",
                dialogue_focus="timing",
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_workflow_review",
                    capture_status="contact_unclear",
                    requested_summary_type="workflow_review",
                    callback=callback_state,
                    appointment_type="workflow_review",
                    appointment_confirmed=False,
                ),
            )
        return _frame(
            semantic="appointment_time_given",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="time_given",
            confidence=0.94,
            next_action_hint="confirm_appointment_and_end",
            candidate_response=_appointment_time_confirmed_response(language, campaign),
            action_id="confirm_appointment_and_end",
            dialogue_focus="timing",
            lead_followup_state_update=_lead_followup_state_update(
                lead_status="open_workflow_review",
                capture_status="callback_time_captured",
                requested_summary_type="workflow_review",
                callback=callback_state,
                appointment_type="workflow_review",
                appointment_confirmed=not bool(callback_state.get("needs_clarification")),
                confirmation_text="workflow review time captured",
            ),
        )

    if confirmed_gaps and _has_callback_time_attempt(transcript, normalized):
        callback_state = _normalize_callback_time(transcript)
        target_gap = active_gap or confirmed_gaps[0]
        if bool(callback_state.get("needs_clarification")):
            return _frame(
                semantic="appointment_time_unclear",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_gap=target_gap,
                polarity="unclear_time",
                confidence=0.86,
                next_action_hint="request_appointment_time_again",
                must_not_do=["schedule without day and time"],
                candidate_response="I need a clearer day and time before I note the review. What day and time works?",
                action_id="request_appointment_time",
                dialogue_focus="timing",
                lead_followup_state_update=_lead_followup_state_update(
                    lead_status="open_workflow_review",
                    capture_status="contact_unclear",
                    requested_summary_type="workflow_review",
                    callback=callback_state,
                    appointment_type="workflow_review",
                    appointment_confirmed=False,
                ),
            )
        return _frame(
            semantic="appointment_time_given",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=target_gap,
            polarity="time_given",
            confidence=0.9,
            next_action_hint="confirm_appointment_and_end",
            candidate_response=_appointment_time_confirmed_response(language, campaign),
            action_id="confirm_appointment_and_end",
            dialogue_focus="timing",
            lead_followup_state_update=_lead_followup_state_update(
                lead_status="open_workflow_review",
                capture_status="callback_time_captured",
                requested_summary_type="workflow_review",
                callback=callback_state,
                appointment_type="workflow_review",
                appointment_confirmed=True,
                confirmation_text="workflow review time captured",
            ),
        )

    if _is_meaning_question(normalized) and previous_question:
        if _contains(normalized, {"handoff", "handoffs", "callback", "callbacks", "owner", "ownership", "routing", "route"}) and not _contains(
            normalized,
            {"growth", "starter", "workflow review", "routesignal"},
        ):
            return _frame(
                semantic="term_question",
                transcript=transcript,
                normalized=normalized,
                previous_question_type=previous_question_type,
                previous_question_text=previous_question,
                conversation_stage=stage,
                active_gap=active_gap,
                confirmed_gaps=confirmed_gaps,
                cleared_gaps=cleared_gaps,
                pending_callback=pending_callback,
                pending_appointment=pending_appointment,
                target_gap=None,
                polarity="clarification_request",
                confidence=0.86,
                next_action_hint="defer_to_pragmatics_explicit_term",
                applied=False,
            )
        previous_normalized = session_policy.normalize_text(previous_question)
        has_named_term = _contains(previous_normalized, {"growth", "starter", "workflow review", "routesignal"}) or _contains(
            normalized,
            {"growth", "starter", "workflow review", "routesignal"},
        )
        semantic = "term_question" if has_named_term else "previous_question_clarification"
        return _frame(
            semantic=semantic,
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="clarification_request",
            confidence=0.9,
            next_action_hint="explain_term" if semantic == "term_question" else "clarify_previous_question",
            must_not_do=["push appointment before clarifying"],
            candidate_response=_term_response(previous_question, normalized) if semantic == "term_question" else _confusion_response(active_gap, campaign),
            action_id="explain_term" if semantic == "term_question" else "clarify_previous_question",
            dialogue_focus=active_gap or "qualification",
        )

    right_person_email, _right_person_email_source = _extract_contact_email(transcript)
    right_person_department = _department_from_text(normalized)
    right_person_name = _person_name_from_text(transcript)
    right_person_callback_state = _normalize_callback_time(transcript)
    right_person_has_time = _has_callback_time_attempt(transcript, normalized) and not bool(right_person_callback_state.get("needs_clarification"))

    if right_person_email and right_person_department:
        return _frame(
            semantic="right_person_email_provided",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="right_person_handoff",
            polarity="contact_captured",
            confidence=0.94,
            next_action_hint="note_right_person_contact",
            must_not_do=["send email", "write CRM", "confirm appointment"],
            candidate_response=(
                f"Got it. I will note that contact for {right_person_department} "
                "so a human can follow up through the right path. I will not send anything from this call."
            ),
            action_id="capture_right_person_contact",
            dialogue_focus="handoff",
            handoff_target_state_update=_handoff_target_state_update(
                reason="buyer_named_team",
                capture_status="contact_detail_captured",
                lead_status="open_send_info_to_right_person",
                role_or_department=right_person_department,
                email=right_person_email,
            ),
        )

    if right_person_name and right_person_has_time:
        return _frame(
            semantic="right_person_callback_time_provided",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="right_person_handoff",
            polarity="time_given",
            confidence=0.93,
            next_action_hint="confirm_right_person_callback",
            must_not_do=["invent email", "write CRM"],
            candidate_response=f"Got it. I will note that {right_person_name} should be called at that time. Goodbye.",
            action_id="capture_right_person_callback_time",
            dialogue_focus="timing",
            handoff_target_state_update=_handoff_target_state_update(
                reason="buyer_named_person",
                capture_status="contact_detail_captured",
                lead_status="open_callback_for_right_person",
                person_name=right_person_name,
            ),
            lead_followup_state_update=_lead_followup_state_update(
                lead_status="open_callback",
                capture_status="callback_time_captured",
                requested_summary_type="right_person_handoff",
                callback=right_person_callback_state,
                appointment_type="right_person_callback",
                appointment_confirmed=True,
                confirmation_text="right-person callback time captured",
            ),
        )

    if _is_send_info_to_right_person(normalized):
        department = right_person_department or "manager"
        return _frame(
            semantic="send_info_to_right_person",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="right_person_handoff",
            polarity="defer_to_right_person",
            confidence=0.9,
            next_action_hint="request_right_person_contact",
            must_not_do=["send email", "confirm appointment"],
            candidate_response=f"No problem. What email or callback path should I use for your {department}? I will not send anything now.",
            action_id="send_info_to_right_person_contact",
            dialogue_focus="handoff",
            handoff_target_state_update=_handoff_target_state_update(
                reason="needs_manager" if department == "manager" else "buyer_named_team",
                capture_status="needs_right_person",
                lead_status="open_send_info_to_right_person",
                role_or_department=department,
            ),
        )

    if right_person_name and _is_person_named(transcript, normalized):
        return _frame(
            semantic="right_person_named",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="right_person_handoff",
            polarity="person_named",
            confidence=0.9,
            next_action_hint="request_right_person_contact",
            must_not_do=["push workflow review", "write CRM"],
            candidate_response=f"Understood, Sarah handles it. What email or callback path should I note for Sarah?",
            action_id="capture_right_person_name",
            dialogue_focus="handoff",
            handoff_target_state_update=_handoff_target_state_update(
                reason="buyer_named_person",
                capture_status="person_name_captured",
                lead_status="open_right_person_handoff",
                person_name=right_person_name,
            ),
        )

    if right_person_department and _is_wrong_person(normalized):
        return _frame(
            semantic="wrong_person_or_wrong_department",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=None,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_topic="right_person_handoff",
            polarity="department_named",
            confidence=0.9,
            next_action_hint="request_right_person_contact",
            must_not_do=["select product routing gap", "push workflow review"],
            candidate_response=f"Understood, {right_person_department} handles that. Who is the right person there, or what contact, email, or callback path should I note?",
            action_id="request_right_person_contact",
            dialogue_focus="handoff",
            handoff_target_state_update=_handoff_target_state_update(
                reason="buyer_named_team" if right_person_department != "manager" else "needs_manager",
                capture_status="department_captured",
                lead_status="open_right_person_handoff",
                role_or_department=right_person_department,
            ),
        )

    if _is_send_info_request(normalized):
        current_gap = _gap_from_text(normalized, campaign)
        target_gap = current_gap or (confirmed_gaps[0] if confirmed_gaps else None)
        semantic = "send_info_with_confirmed_pain" if confirmed_gaps else "send_info_request"
        summary_type = "workflow_review" if confirmed_gaps or pending_appointment else "product_details"
        return _frame(
            semantic=semantic,
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=target_gap,
            polarity="defer_to_info",
            confidence=0.86,
            next_action_hint="offer_summary_or_callback",
            must_not_do=["confirm appointment", "send email", "call provider"],
            candidate_response=_send_info_request_response(target_gap, campaign),
            action_id="request_send_info_contact",
            dialogue_focus="timing",
            send_info_state_update=_send_info_state_update(
                requested_at_turn=len(turns) + 1,
                requested_summary_type=summary_type,
                capture_status="needs_email_or_callback_time",
                lead_status="open_send_info",
            ),
            lead_followup_state_update=_lead_followup_state_update(
                lead_status="open_send_info",
                capture_status="needs_contact",
                requested_summary_type=summary_type,
                appointment_type="workflow_review" if pending_appointment else "send_info_followup",
                appointment_confirmed=False,
            ),
        )

    if _is_wrong_person(normalized):
        return _frame(
            semantic="wrong_person_or_wrong_department",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="wrong_contact",
            confidence=0.9,
            next_action_hint="ask_for_right_contact_or_end",
            must_not_do=["select product routing gap", "push workflow review"],
            candidate_response=_wrong_person_response(campaign),
            action_id="request_right_person_or_close",
            dialogue_focus="handoff",
            handoff_target_state_update=_handoff_target_state_update(
                reason="wrong_department" if _contains(normalized, {"department", "team"}) else "wrong_person",
                capture_status="needs_right_person",
                lead_status="open_right_person_handoff",
            ),
        )

    if current_confirmed_gaps:
        selected_gap, secondary_confirmed = _rank_confirmed_gaps(current_confirmed_gaps, normalized, campaign)
        selected_gap = selected_gap or current_confirmed_gaps[0]
        semantic = "mixed_gap_response" if current_clear_gaps else "pain_confirmed"
        return _frame(
            semantic=semantic,
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=selected_gap,
            primary_gap=selected_gap,
            secondary_confirmed_gaps=secondary_confirmed,
            current_cleared_gaps=current_clear_gaps,
            current_confirmed_gaps=current_confirmed_gaps,
            polarity="pain",
            confidence=0.9 if current_clear_gaps else 0.88,
            next_action_hint="move_toward_workflow_review",
            must_not_do=["treat as no pain", "erase cleared gaps"],
            candidate_response=_pain_confirmed_response(
                language,
                selected_gap,
                campaign,
                acknowledge_repeat=_is_repeat_problem_reference(normalized),
            ),
            action_id="request_appointment_time",
            dialogue_focus="timing",
        )

    if active_gap and _is_unclear_possible_pain(normalized):
        return _frame(
            semantic="pain_possible_but_unclear",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="unclear_pain",
            confidence=0.84,
            next_action_hint="clarify_current_gap",
            must_not_do=["confirm pain", "push appointment before clarifying"],
            candidate_response=f"Understood. Is {_customer_label(active_gap, campaign)} actually causing trouble, or is it mostly handled?",
            action_id="clarify_current_gap",
            dialogue_focus="qualification",
        )

    if active_gap and not current_clear_gaps and _has_pain_signal(normalized):
        return _frame(
            semantic="pain_confirmed",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=active_gap,
            polarity="pain",
            confidence=0.86,
            next_action_hint="move_toward_workflow_review",
            must_not_do=["treat as no pain"],
            candidate_response=_pain_confirmed_response(
                language,
                active_gap,
                campaign,
                acknowledge_repeat=_is_repeat_problem_reference(normalized),
            ),
            action_id="request_appointment_time",
            dialogue_focus="timing",
        )

    if active_gap_scope == "multi_gap" and _is_broad_clear_or_no_pain(normalized):
        current_cleared = list(candidate_gaps)
        return _frame(
            semantic="multi_gap_clear",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            active_gap_scope=active_gap_scope,
            candidate_gaps=candidate_gaps,
            answered_gaps=current_cleared,
            current_cleared_gaps=current_cleared,
            target_topic="campaign_relevance",
            polarity="no_pain",
            confidence=0.92,
            next_action_hint="one_final_save_question",
            must_not_do=["repeat same diagnostic", "push workflow review"],
            candidate_response=_multi_gap_clear_response(language, candidate_gaps, campaign),
            action_id="continue_with_session_policy",
            dialogue_focus="qualification",
        )

    if current_clear_gaps or _is_clear_or_no_pain(normalized):
        target_gap = (current_clear_gaps[0] if current_clear_gaps else active_gap)
        semantic = "current_gap_clear" if target_gap else "all_clear_no_pain"
        if semantic == "all_clear_no_pain":
            response = _all_clear_response(campaign)
            action_id = "end_call_stop_request"
            hint = "end_politely"
            polarity = "no_pain"
        elif confirmed_gaps:
            response = _next_diagnostic_response(language, target_gap, confirmed_gaps, campaign)
            action_id = "request_appointment_time"
            hint = "bridge_to_workflow_review"
            polarity = "clear_current_gap"
        elif not _remaining_gaps(
            cleared_gaps=_unique(cleared_gaps + [target_gap]),
            candidate_gaps=_core_diagnostic_gaps(campaign),
            campaign=campaign,
        ):
            response = _multi_gap_clear_response(language, _core_diagnostic_gaps(campaign), campaign)
            action_id = "continue_with_session_policy"
            hint = "one_final_save_question"
            polarity = "no_pain"
        elif final_save_pending or active_gap_scope == "multi_gap" or len(candidate_gaps or []) > 1:
            response = _remaining_gap_response(language, _unique(cleared_gaps + [target_gap]), candidate_gaps or _core_diagnostic_gaps(campaign), campaign)
            action_id = "continue_with_session_policy"
            hint = "ask_remaining_diagnostic"
            polarity = "clear_current_gap"
        else:
            response = _next_diagnostic_response(language, target_gap, confirmed_gaps, campaign)
            action_id = "request_appointment_time" if confirmed_gaps else "continue_with_session_policy"
            hint = "bridge_to_workflow_review" if confirmed_gaps else "ask_next_diagnostic"
            polarity = "clear_current_gap"
        return _frame(
            semantic=semantic,
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=target_gap,
            current_cleared_gaps=[target_gap] if target_gap else [],
            polarity=polarity,
            confidence=0.92,
            next_action_hint=hint,
            must_not_do=["classify as pain", "erase confirmed pain"],
            candidate_response=response,
            action_id=action_id,
            dialogue_focus="timing" if confirmed_gaps else "qualification",
        )

    callback_state = _normalize_callback_time(transcript)
    if (
        _contains(normalized, {"call me", "call back", "call us", "callback"})
        and _has_callback_time_attempt(transcript, normalized)
        and not bool(callback_state.get("needs_clarification"))
    ):
        return _frame(
            semantic="callback_time_confirmation",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="time_given",
            confidence=0.9,
            next_action_hint="confirm_callback_and_end",
            candidate_response=session_policy.callback_time_confirmed_response(language, campaign),
            action_id="confirm_callback_and_end",
            dialogue_focus="timing",
            lead_followup_state_update=_lead_followup_state_update(
                lead_status="open_callback",
                capture_status="callback_time_captured",
                requested_summary_type="unknown",
                callback=callback_state,
                appointment_type="callback",
                appointment_confirmed=True,
                confirmation_text="callback time captured",
            ),
        )

    if session_policy.has_callback_request_signal(normalized):
        return _frame(
            semantic="callback_scheduling_request",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="defer_timing",
            confidence=0.9,
            next_action_hint="request_callback_time",
            candidate_response=_callback_time_request_response(language, normalized),
            action_id="request_callback_time",
            dialogue_focus="timing",
        )

    selected_gap = _gap_from_text(normalized, campaign)
    if selected_gap and _has_pain_signal(normalized):
        return _frame(
            semantic="pain_confirmed",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            target_gap=selected_gap,
            polarity="pain",
            confidence=0.88,
            next_action_hint="move_toward_workflow_review",
            must_not_do=["treat as no pain"],
            candidate_response=_pain_confirmed_response(
                language,
                selected_gap,
                campaign,
                acknowledge_repeat=_is_repeat_problem_reference(normalized),
            ),
            action_id="request_appointment_time",
            dialogue_focus="timing",
        )

    if _is_low_information_ack(normalized):
        return _frame(
            semantic="social_acknowledgement",
            transcript=transcript,
            normalized=normalized,
            previous_question_type=previous_question_type,
            previous_question_text=previous_question,
            conversation_stage=stage,
            active_gap=active_gap,
            confirmed_gaps=confirmed_gaps,
            cleared_gaps=cleared_gaps,
            pending_callback=pending_callback,
            pending_appointment=pending_appointment,
            polarity="acknowledgement",
            confidence=0.74,
            next_action_hint="continue_without_inferring_pain",
            applied=False,
        )

    return _frame(
        semantic="no_contextual_semantic",
        transcript=transcript,
        normalized=normalized,
        previous_question_type=previous_question_type,
        previous_question_text=previous_question,
        conversation_stage=stage,
        active_gap=active_gap,
        confirmed_gaps=confirmed_gaps,
        cleared_gaps=cleared_gaps,
        pending_callback=pending_callback,
        pending_appointment=pending_appointment,
        confidence=0.0,
        applied=False,
    )


def continuity_from_semantic_frame(frame: dict[str, Any]) -> dict[str, Any] | None:
    if not frame.get("applied"):
        return None
    semantic = str(frame.get("semantic") or "")
    reason = "appointment_time_clarification_needed" if semantic == "appointment_time_unclear" else f"contextual_{semantic}"
    return {
        "applied": True,
        "reason": reason,
        "action_id": str(frame.get("action_id") or ""),
        "dialogue_focus": frame.get("dialogue_focus") or frame.get("target_topic") or "qualification",
        "selected_gap": frame.get("target_gap"),
        "candidate_response": str(frame.get("candidate_response") or ""),
        "contextual_buyer_semantics": {
            key: value
            for key, value in frame.items()
            if key not in {"candidate_response"}
        },
    }
