from __future__ import annotations

import re
from typing import Any


PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
SCHEMA_VERSION = 1

CORE_DIAGNOSTIC_GAPS = ["callbacks", "manual_tracking", "handoffs"]
GAP_ORDER = [
    "callbacks",
    "manual_tracking",
    "handoffs",
    "routing",
    "reminders",
    "duplicates",
    "visibility",
    "right_person",
]

PLAYBOOK: dict[str, Any] = {
    "playbook_id": PLAYBOOK_ID,
    "schema_version": SCHEMA_VERSION,
    "campaign_context": {
        "product": "RouteSignal CRM",
        "human_followup_owner": "Northstar",
        "objective": "appointment_setting",
        "forbidden": ["full_sale_close", "payment", "contract", "provider_call"],
    },
    "gaps": {
        "callbacks": {
            "customer_language": ["missed callbacks", "callbacks slipping", "forgotten follow-up calls"],
            "label": "callbacks",
            "definition": "Inbound demo leads need a follow-up callback or reminder and may wait too long.",
            "causal_story": "If callbacks are not owned and reminded, warm demo leads wait and trust drops before a human can respond.",
            "evidence_positive": [
                "missed callback",
                "missed callbacks",
                "missing callback",
                "callbacks get missed",
                "callbacks are missed",
                "callbacks slip",
                "callbacks slipping",
                "forgot to call back",
                "people wait",
                "missed follow up call",
            ],
            "evidence_negative": [
                "callbacks are fine",
                "callback is fine",
                "callbacks are handled",
                "callbacks are clean",
                "not missed",
            ],
            "diagnostic_questions": ["Do missed callbacks ever create issues, or are those clean today?"],
            "value_bridge": "RouteSignal helps demo leads stay assigned, reminded, and followed up before callback gaps turn into lost opportunities.",
            "review_focus": "missed callback reminders",
            "next_gap_candidates": ["manual_tracking", "handoffs"],
        },
        "manual_tracking": {
            "customer_language": ["spreadsheet tracking", "manual lists", "copying notes", "manual reminders"],
            "label": "manual tracking",
            "definition": "The team tracks follow-up in spreadsheets, shared inboxes, manual notes, or manual reminders.",
            "causal_story": "Manual tracking makes the next step depend on memory and hand copying, so follow-up can slow down or disappear.",
            "evidence_positive": [
                "manual tracking",
                "tracking manually",
                "manual list",
                "spreadsheet",
                "manual notes",
                "copying notes",
                "manual reminders",
                "tracking gets messy",
                "manual tracking gets messy",
            ],
            "evidence_negative": [
                "manual tracking is fine",
                "tracking is fine",
                "manual tracking is handled",
                "tracking is handled",
            ],
            "diagnostic_questions": ["Does manual tracking or spreadsheet follow-up ever cause missed next steps?"],
            "value_bridge": "RouteSignal makes follow-up ownership and reminders visible without relying on scattered manual tracking.",
            "review_focus": "manual follow-up tracking",
            "next_gap_candidates": ["callbacks", "handoffs"],
        },
        "handoffs": {
            "customer_language": ["handoffs get messy", "owner unclear", "lost between teams"],
            "label": "handoffs",
            "definition": "A lead moves between people or teams and the next owner or next reply becomes unclear.",
            "causal_story": "When handoffs are unclear, a demo lead can sit between teams even though everyone thinks someone else owns it.",
            "evidence_positive": [
                "handoff gets messy",
                "handoffs get messy",
                "handoffs are messy",
                "handoff issue",
                "owner unclear",
                "ownership unclear",
                "lost between teams",
                "wrong owner",
            ],
            "evidence_negative": [
                "handoffs are fine",
                "handoff is fine",
                "handoffs are handled",
                "handoffs are clean",
            ],
            "diagnostic_questions": ["Do handoffs ever get messy, or is ownership clear today?"],
            "value_bridge": "RouteSignal helps each demo lead keep a clear owner and next reply.",
            "review_focus": "handoff ownership",
            "next_gap_candidates": ["callbacks", "manual_tracking"],
        },
        "routing": {
            "customer_language": ["lead routing unclear", "assignment delay", "wrong owner"],
            "label": "lead routing",
            "definition": "An inbound demo lead needs the right owner quickly.",
            "causal_story": "If assignment is delayed or unclear, follow-up starts late even when the lead is high intent.",
            "evidence_positive": [
                "lead routing is unclear",
                "routing is unclear",
                "assignment delay",
                "assigned late",
                "wrong owner",
                "owner unclear",
            ],
            "evidence_negative": ["routing is fine", "assignment is fine", "owners are clear"],
            "diagnostic_questions": ["Does lead routing ever delay who owns the next reply?"],
            "value_bridge": "RouteSignal helps each demo lead get a clear owner faster.",
            "review_focus": "lead assignment flow",
            "next_gap_candidates": ["callbacks", "handoffs"],
            "distinction": "Product lead routing is not the same as right-person or contact routing.",
        },
        "reminders": {
            "customer_language": ["missed reminders", "forgot to follow up", "manual reminders"],
            "label": "reminders",
            "definition": "Follow-up needs reminders so tasks do not sit.",
            "causal_story": "Without clear reminders, a lead can wait even when the team knows follow-up is needed.",
            "evidence_positive": ["missed reminders", "reminders get missed", "forgot to follow up", "manual reminders"],
            "evidence_negative": ["reminders are fine", "reminders are handled", "reminders are clean"],
            "diagnostic_questions": ["Do follow-up reminders ever get missed, or is that handled?"],
            "value_bridge": "RouteSignal keeps reminder ownership visible around demo follow-up.",
            "review_focus": "follow-up reminder flow",
            "next_gap_candidates": ["callbacks", "manual_tracking"],
        },
        "duplicates": {
            "customer_language": ["duplicate demo requests", "two people reply", "ownership split"],
            "label": "duplicate handling",
            "definition": "Duplicate demo leads split ownership or create confusion.",
            "causal_story": "Duplicate requests can make two people reply or make each person think the other owns the lead.",
            "evidence_positive": [
                "duplicate demo request",
                "duplicate demo requests",
                "duplicates confuse ownership",
                "duplicate leads",
                "two people reply",
                "ownership split",
            ],
            "evidence_negative": ["duplicates are fine", "duplicates are handled", "duplicate handling is fine"],
            "diagnostic_questions": ["Do duplicate demo requests ever confuse ownership?"],
            "value_bridge": "RouteSignal can review whether duplicate requests are creating ownership confusion.",
            "review_focus": "duplicate lead ownership",
            "next_gap_candidates": ["routing", "handoffs"],
        },
        "visibility": {
            "customer_language": ["manager cannot see status", "hard to see who followed up", "no visibility"],
            "label": "manager visibility",
            "definition": "A manager cannot quickly see which lead still needs follow-up.",
            "causal_story": "When status is not visible, managers ask around and issues surface only after follow-up is already late.",
            "evidence_positive": [
                "manager cannot see",
                "managers cannot see",
                "cannot see who followed up",
                "hard to see who followed up",
                "no visibility",
                "manager visibility",
                "no status",
                "asks around",
            ],
            "evidence_negative": ["visibility is fine", "manager visibility is fine", "status is visible"],
            "diagnostic_questions": ["Can managers see which demo leads still need follow-up?"],
            "value_bridge": "RouteSignal makes follow-up status and owner visibility easier to review.",
            "review_focus": "manager follow-up visibility",
            "next_gap_candidates": ["callbacks", "handoffs"],
        },
        "right_person": {
            "customer_language": ["wrong person", "operations handles that", "Sarah handles that"],
            "label": "right person",
            "definition": "The current speaker is not the right owner for the workflow decision.",
            "causal_story": "If the call is with the wrong person, the useful outcome is a safe handoff target, not a product review pressure step.",
            "evidence_positive": [
                "wrong person",
                "i am not the person",
                "i don't handle that",
                "operations handles that",
                "sales handles that",
                "support handles that",
                "manager handles that",
            ],
            "evidence_negative": ["i handle that", "i am the right person"],
            "diagnostic_questions": ["Who is the right person or team for demo follow-up?"],
            "value_bridge": "Northstar can follow up with the right person instead of pushing the wrong contact.",
            "review_focus": "right-person handoff",
            "next_gap_candidates": [],
        },
    },
    "conversation_policy": {
        "max_diagnostics_before_save": 2,
        "after_current_gap_clear": "ask_next_remaining_gap",
        "after_multi_gap_clear": "one_final_save_or_polite_close",
        "after_pain_confirmed": "workflow_review_or_send_info",
        "after_wrong_person": "right_person_handoff",
        "after_send_info": "collect_email_or_callback_time",
    },
}


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9@.]+", " ", str(text or "").lower()).strip()


def _contains(normalized: str, phrases: list[str] | tuple[str, ...] | set[str]) -> bool:
    return any(normalize_text(phrase) in normalized for phrase in phrases if phrase)


def gap_ids() -> list[str]:
    return list(GAP_ORDER)


def core_diagnostic_gaps() -> list[str]:
    return list(CORE_DIAGNOSTIC_GAPS)


def gap_labels() -> dict[str, str]:
    return {gap_id: str((PLAYBOOK["gaps"][gap_id]).get("label") or gap_id) for gap_id in GAP_ORDER if gap_id in PLAYBOOK["gaps"]}


def gap_definition(gap_id: str | None) -> dict[str, Any]:
    if not gap_id:
        return {}
    return dict((PLAYBOOK.get("gaps") or {}).get(gap_id) or {})


def customer_label(gap_id: str | None) -> str:
    definition = gap_definition(gap_id)
    return str(definition.get("label") or gap_id or "that follow-up gap")


def review_focus(gap_id: str | None) -> str | None:
    definition = gap_definition(gap_id)
    value = definition.get("review_focus")
    return str(value) if value else None


def value_bridge(gap_id: str | None) -> str:
    definition = gap_definition(gap_id)
    return str(definition.get("value_bridge") or "RouteSignal helps demo leads stay assigned, reminded, and followed up.")


def diagnostic_question(gap_id: str | None) -> str:
    definition = gap_definition(gap_id)
    questions = definition.get("diagnostic_questions") or []
    if questions:
        return str(questions[0])
    return "Do callbacks, manual tracking, or handoffs ever create issues?"


def ordered_gap_ids(gaps: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    unique = []
    for gap in gaps:
        text = str(gap or "")
        if text and text not in unique:
            unique.append(text)
    ordered = [gap for gap in GAP_ORDER if gap in unique]
    ordered.extend(gap for gap in unique if gap not in ordered)
    return ordered


def gaps_from_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    gaps: list[str] = []
    for gap_id in GAP_ORDER:
        definition = gap_definition(gap_id)
        phrases = []
        phrases.extend(definition.get("customer_language") or [])
        phrases.extend(definition.get("evidence_positive") or [])
        phrases.extend(definition.get("evidence_negative") or [])
        phrases.append(customer_label(gap_id))
        if _contains(normalized, phrases) and gap_id not in gaps:
            gaps.append(gap_id)
    return ordered_gap_ids(gaps)


def first_gap_from_text(text: str) -> str | None:
    gaps = gaps_from_text(text)
    return gaps[0] if gaps else None


def cleared_gaps_from_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    gaps = []
    for gap_id in GAP_ORDER:
        if _contains(normalized, list(gap_definition(gap_id).get("evidence_negative") or [])):
            gaps.append(gap_id)
    return ordered_gap_ids(gaps)


def confirmed_gaps_from_text(text: str) -> list[str]:
    normalized = normalize_text(text)
    clear_gaps = set(cleared_gaps_from_text(normalized))
    gaps = []
    for gap_id in GAP_ORDER:
        if gap_id == "right_person" or gap_id in clear_gaps:
            continue
        if _contains(normalized, list(gap_definition(gap_id).get("evidence_positive") or [])):
            gaps.append(gap_id)
    if "manual_tracking" not in gaps and "manual_tracking" not in clear_gaps:
        if _contains(normalized, {"manual tracking", "tracking"}) and _contains(normalized, {"messy", "issue", "problem", "occasional", "sometimes"}):
            gaps.append("manual_tracking")
    if "handoffs" not in gaps and "handoffs" not in clear_gaps:
        if _contains(normalized, {"handoff", "handoffs"}) and _contains(normalized, {"messy", "issue", "problem", "unclear", "lost"}):
            gaps.append("handoffs")
    if "callbacks" not in gaps and "callbacks" not in clear_gaps:
        if _contains(normalized, {"callback", "callbacks"}) and _contains(normalized, {"missed", "missing", "slip", "slipping", "issue", "problem", "occasional", "sometimes"}):
            gaps.append("callbacks")
    if "routing" not in gaps and "routing" not in clear_gaps:
        if _contains(normalized, {"routing", "assignment", "assigned", "owner"}) and _contains(normalized, {"unclear", "delay", "late", "wrong"}):
            gaps.append("routing")
    if "visibility" not in gaps and "visibility" not in clear_gaps:
        if _contains(normalized, {"manager", "managers", "status", "see who followed up"}) and _contains(normalized, {"cannot see", "can't see", "hard to see", "no visibility"}):
            gaps.append("visibility")
    return ordered_gap_ids(gaps)


def remaining_gaps(
    *,
    cleared_gaps: list[str] | tuple[str, ...] | set[str],
    confirmed_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    candidate_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
) -> list[str]:
    candidates = ordered_gap_ids(list(candidate_gaps or CORE_DIAGNOSTIC_GAPS))
    blocked = set(str(gap) for gap in cleared_gaps or []) | set(str(gap) for gap in confirmed_gaps or [])
    return [gap for gap in candidates if gap not in blocked]


def next_gap(
    *,
    cleared_gaps: list[str] | tuple[str, ...] | set[str],
    confirmed_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    candidate_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
) -> str | None:
    remaining = remaining_gaps(cleared_gaps=cleared_gaps, confirmed_gaps=confirmed_gaps, candidate_gaps=candidate_gaps)
    return remaining[0] if remaining else None


def rank_confirmed_gaps(gaps: list[str], utterance: str = "") -> tuple[str | None, list[str]]:
    ordered = ordered_gap_ids(gaps)
    normalized = normalize_text(utterance)
    if "mostly" in normalized:
        for gap in ordered:
            gap_position = normalized.find(customer_label(gap).split()[0])
            mostly_position = normalized.find("mostly")
            if gap_position >= 0 and mostly_position <= gap_position:
                secondary = [item for item in ordered if item != gap]
                return gap, secondary
    primary = ordered[0] if ordered else None
    secondary = [gap for gap in ordered if gap != primary]
    return primary, secondary


def playbook_trace(
    *,
    gap_id: str | None,
    cleared_gaps: list[str] | None = None,
    confirmed_gaps: list[str] | None = None,
    candidate_gaps: list[str] | None = None,
) -> dict[str, Any]:
    selected_gap = gap_id if gap_id in PLAYBOOK["gaps"] else None
    return {
        "playbook_id": PLAYBOOK_ID,
        "schema_version": SCHEMA_VERSION,
        "playbook_gap": selected_gap,
        "playbook_next_gap": next_gap(
            cleared_gaps=cleared_gaps or [],
            confirmed_gaps=confirmed_gaps or [],
            candidate_gaps=candidate_gaps or CORE_DIAGNOSTIC_GAPS,
        ),
        "playbook_review_focus": review_focus(selected_gap),
        "playbook_supported_gap_ids": gap_ids(),
    }
