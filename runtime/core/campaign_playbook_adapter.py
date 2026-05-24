from __future__ import annotations

from copy import deepcopy
from typing import Any

from runtime.core import sales_diagnostic_playbook as routesignal_playbook
from runtime.core import universal_sales_knowledge
from runtime.core import vertical_sales_playbooks


CAMPAIGN_PLAYBOOK_ADAPTER_ID = "CAMPAIGN-PLAYBOOK-ADAPTER-001"
SCHEMA_VERSION = 1
DEFAULT_CAMPAIGN_ID = "live-demo-001-routesignal"
CURRENT_LIVE_DEMO_ROUTESIGNAL_CAMPAIGN_ID = "campaign-prod-005-b2b-software"
DEFAULT_VERTICAL_ID = "b2b_saas"
ROUTESIGNAL_CAMPAIGN_IDS = {
    DEFAULT_CAMPAIGN_ID,
    CURRENT_LIVE_DEMO_ROUTESIGNAL_CAMPAIGN_ID,
}

SAFETY_FLAGS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
}

ROUTESIGNAL_GAP_MAPPINGS: dict[str, dict[str, list[str]]] = {
    "callbacks": {
        "universal_pain_dimensions": ["missed_follow_up", "delay", "unclear_next_step"],
        "qualification_dimensions": ["need_or_pain", "urgency", "fit", "contact_path"],
    },
    "manual_tracking": {
        "universal_pain_dimensions": ["manual_work", "missed_follow_up", "unclear_next_step"],
        "qualification_dimensions": ["need_or_pain", "current_solution_or_status_quo", "fit"],
    },
    "handoffs": {
        "universal_pain_dimensions": ["ownership_confusion", "unclear_next_step", "customer_experience_friction"],
        "qualification_dimensions": ["need_or_pain", "authority_or_right_person", "fit"],
    },
    "routing": {
        "universal_pain_dimensions": ["ownership_confusion", "delay", "unclear_next_step"],
        "qualification_dimensions": ["need_or_pain", "authority_or_right_person", "fit"],
    },
    "reminders": {
        "universal_pain_dimensions": ["missed_follow_up", "unclear_next_step", "delay"],
        "qualification_dimensions": ["need_or_pain", "timing", "fit"],
    },
    "duplicates": {
        "universal_pain_dimensions": ["duplicate_work", "ownership_confusion", "unclear_next_step"],
        "qualification_dimensions": ["need_or_pain", "current_solution_or_status_quo", "fit"],
    },
    "visibility": {
        "universal_pain_dimensions": ["visibility_gap", "unclear_next_step"],
        "qualification_dimensions": ["need_or_pain", "authority_or_right_person", "fit"],
    },
    "right_person": {
        "universal_pain_dimensions": ["unclear_next_step"],
        "qualification_dimensions": ["authority_or_right_person", "contact_path"],
    },
}


def _campaign_context() -> dict[str, Any]:
    source_context = dict((routesignal_playbook.PLAYBOOK.get("campaign_context") or {}))
    return {
        "customer_facing_company_name": "Northstar Workflow Labs",
        "customer_facing_offer_name": "RouteSignal",
        "customer_facing_offer_summary": (
            "RouteSignal is a CRM workflow tool for inbound demo follow-up."
        ),
        "customer_facing_value_proposition": (
            "The high-level value is fewer missed replies, clearer ownership, and less manual follow-up drift."
        ),
        "customer_facing_call_objective": "check whether inbound demo follow-up is active enough for a workflow review",
        "customer_facing_human_review_scope": "who owns the lead, when follow-up happens, and where reminders or handoffs slip",
        "product_or_offer_name": str(source_context.get("product") or "RouteSignal"),
        "product_or_offer_summary": (
            "RouteSignal is a CRM workflow tool for inbound demo follow-up. "
            "It helps teams assign the next reply, track reminders, and avoid missed handoffs."
        ),
        "high_level_value_proposition": (
            "The high-level value is fewer missed replies, clearer ownership, and less manual follow-up drift."
        ),
        "allowed_high_level_capabilities": [
            "inbound demo follow-up ownership",
            "next-reply assignment",
            "reminder and handoff visibility",
        ],
        "client_name": "Northstar Workflow Labs",
        "objective": str(source_context.get("objective") or "appointment_setting"),
        "agent_call_objective": "check whether inbound demo follow-up is active enough for a workflow review",
        "human_followup_owner": str(source_context.get("human_followup_owner") or "Northstar workflow reviewer"),
        "appointment_target": "short workflow review",
        "human_review_scope": "who owns the lead, when follow-up happens, and where reminders or handoffs slip",
        "agent_can_say": [
            "RouteSignal is a CRM workflow tool for inbound demo follow-up",
            "the call can check follow-up ownership, reminders, and handoffs at a high level",
        ],
        "agent_must_not_claim": [
            "live CRM access",
            "calendar booking",
            "guaranteed implementation outcome",
        ],
        "primary_customer_issue_phrase": str(source_context.get("primary_customer_issue_phrase") or ""),
        "short_relevance_question": str(source_context.get("short_relevance_question") or ""),
        "campaign_purpose_phrase": str(source_context.get("campaign_purpose_phrase") or ""),
        "product_detail_answer": str(source_context.get("product_detail_answer") or ""),
        "allowed_claims": [],
        "blocked_claims": list(source_context.get("forbidden") or []),
    }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item or "")]
    return [str(value)] if str(value or "") else []


def _append_unique(target: list[str], values: Any) -> None:
    seen = set(target)
    for value in _string_list(values):
        if value not in seen:
            target.append(value)
            seen.add(value)


def _has_generic_campaign_playbook_config(campaign: dict[str, Any] | None) -> bool:
    if not isinstance(campaign, dict):
        return False
    campaign_id = str(campaign.get("campaign_id") or "")
    if campaign_id in ROUTESIGNAL_CAMPAIGN_IDS:
        return False
    return bool(
        campaign.get("vertical_id")
        and isinstance(campaign.get("diagnostic_gaps"), dict)
        and campaign.get("diagnostic_gaps")
    )


def _adapt_generic_gap(gap_id: str, source: dict[str, Any], vertical_record: dict[str, Any]) -> dict[str, Any]:
    universal_pain_dimensions = _string_list(source.get("universal_pain_dimensions"))
    vertical_pain_dimensions = [
        pain_id
        for pain_id in universal_pain_dimensions
        if pain_id in set(vertical_record.get("common_pain_dimensions") or [])
    ]
    diagnostic_questions = _string_list(source.get("diagnostic_questions"))
    return {
        "campaign_gap_id": str(source.get("campaign_gap_id") or gap_id),
        "label": str(source.get("label") or gap_id),
        "customer_facing_phrase": str(
            source.get("customer_facing_phrase")
            or source.get("customer_facing_gap_phrase")
            or source.get("label")
            or gap_id
        ),
        "universal_pain_dimensions": universal_pain_dimensions,
        "qualification_dimensions": _string_list(source.get("qualification_dimensions")),
        "vertical_pain_dimensions": vertical_pain_dimensions,
        "definition": str(source.get("definition") or ""),
        "causal_story": str(source.get("causal_story") or ""),
        "customer_language": _string_list(source.get("customer_language")),
        "evidence_positive": _string_list(source.get("evidence_positive")),
        "evidence_negative": _string_list(source.get("evidence_negative")),
        "diagnostic_questions": diagnostic_questions,
        "diagnostic_question_phrase": str(
            source.get("diagnostic_question_phrase")
            or (diagnostic_questions[0] if diagnostic_questions else "")
        ),
        "impact_question_phrase": str(source.get("impact_question_phrase") or ""),
        "pain_acknowledgement_phrase": str(source.get("pain_acknowledgement_phrase") or ""),
        "value_bridge": str(source.get("value_bridge") or ""),
        "value_bridge_phrase": str(source.get("value_bridge_phrase") or source.get("value_bridge") or ""),
        "review_focus": source.get("review_focus"),
        "next_gap_candidates": _string_list(source.get("next_gap_candidates")),
    }


def _adapt_gap(gap_id: str) -> dict[str, Any]:
    source = routesignal_playbook.gap_definition(gap_id)
    mapping = ROUTESIGNAL_GAP_MAPPINGS.get(gap_id) or {}
    universal_pain_dimensions = list(mapping.get("universal_pain_dimensions") or [])
    vertical_record = vertical_sales_playbooks.vertical_playbook(DEFAULT_VERTICAL_ID)
    vertical_pain_dimensions = [
        pain_id
        for pain_id in universal_pain_dimensions
        if pain_id in set(vertical_record.get("common_pain_dimensions") or [])
    ]
    return {
        "campaign_gap_id": gap_id,
        "label": str(source.get("label") or gap_id),
        "customer_facing_phrase": str(source.get("customer_facing_phrase") or source.get("label") or gap_id),
        "universal_pain_dimensions": universal_pain_dimensions,
        "qualification_dimensions": list(mapping.get("qualification_dimensions") or []),
        "vertical_pain_dimensions": vertical_pain_dimensions,
        "definition": str(source.get("definition") or ""),
        "causal_story": str(source.get("causal_story") or ""),
        "customer_language": list(source.get("customer_language") or []),
        "evidence_positive": list(source.get("evidence_positive") or []),
        "evidence_negative": list(source.get("evidence_negative") or []),
        "diagnostic_questions": list(source.get("diagnostic_questions") or []),
        "diagnostic_question_phrase": str(source.get("diagnostic_question_phrase") or routesignal_playbook.diagnostic_question(gap_id)),
        "impact_question_phrase": str(source.get("impact_question_phrase") or ""),
        "pain_acknowledgement_phrase": str(source.get("pain_acknowledgement_phrase") or ""),
        "value_bridge": str(source.get("value_bridge") or ""),
        "value_bridge_phrase": str(source.get("value_bridge_phrase") or source.get("value_bridge") or ""),
        "review_focus": source.get("review_focus"),
        "next_gap_candidates": list(source.get("next_gap_candidates") or []),
    }


def _resolve_routesignal_playbook(campaign: dict[str, Any] | None = None) -> dict[str, Any]:
    campaign_id = str((campaign or {}).get("campaign_id") or DEFAULT_CAMPAIGN_ID)
    diagnostic_gaps = {gap_id: _adapt_gap(gap_id) for gap_id in routesignal_playbook.gap_ids()}
    return {
        "adapter_id": CAMPAIGN_PLAYBOOK_ADAPTER_ID,
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "vertical_id": DEFAULT_VERTICAL_ID,
        "universal_knowledge_id": universal_sales_knowledge.universal_knowledge_id(),
        "vertical_playbook_id": DEFAULT_VERTICAL_ID,
        "campaign_playbook_id": routesignal_playbook.PLAYBOOK_ID,
        "campaign_context": _campaign_context(),
        "diagnostic_gaps": diagnostic_gaps,
        "core_diagnostic_gaps": routesignal_playbook.core_diagnostic_gaps(),
        "gap_order": routesignal_playbook.gap_ids(),
        "safety": dict(SAFETY_FLAGS),
    }


def _resolve_generic_campaign_playbook(campaign: dict[str, Any]) -> dict[str, Any]:
    campaign_id = str(campaign.get("campaign_id") or "generic-campaign")
    vertical_id = str(campaign.get("vertical_id") or "")
    vertical_record = vertical_sales_playbooks.vertical_playbook(vertical_id)
    regulated_cautions = vertical_sales_playbooks.vertical_regulated_cautions(vertical_id)
    vertical_blocked_claims = vertical_sales_playbooks.vertical_blocked_claim_types(vertical_id)

    blocked_claims: list[str] = []
    _append_unique(blocked_claims, campaign.get("blocked_claims"))
    _append_unique(blocked_claims, campaign.get("forbidden_claims"))
    _append_unique(blocked_claims, vertical_blocked_claims)
    for caution_id in regulated_cautions:
        caution = universal_sales_knowledge.regulated_caution(caution_id)
        _append_unique(blocked_claims, caution.get("blocked_claims"))

    allowed_claims: list[str] = []
    _append_unique(allowed_claims, campaign.get("allowed_claims"))

    diagnostic_gaps_source = dict(campaign.get("diagnostic_gaps") or {})
    gap_order = _string_list(campaign.get("gap_order")) or list(diagnostic_gaps_source)
    diagnostic_gaps = {
        gap_id: _adapt_generic_gap(gap_id, dict(diagnostic_gaps_source.get(gap_id) or {}), vertical_record)
        for gap_id in gap_order
        if gap_id in diagnostic_gaps_source
    }
    core_diagnostic_gaps = _string_list(campaign.get("core_diagnostic_gaps")) or gap_order[:3]

    campaign_context = {
        "product_or_offer_name": str(
            campaign.get("customer_facing_offer_name")
            or campaign.get("product_or_offer_name")
            or campaign.get("offer_name")
            or campaign.get("product_name")
            or "Generic Campaign Offer"
        ),
        "customer_facing_company_name": str(campaign.get("customer_facing_company_name") or ""),
        "customer_facing_offer_name": str(campaign.get("customer_facing_offer_name") or ""),
        "customer_facing_offer_summary": str(campaign.get("customer_facing_offer_summary") or ""),
        "customer_facing_value_proposition": str(campaign.get("customer_facing_value_proposition") or ""),
        "customer_facing_call_objective": str(campaign.get("customer_facing_call_objective") or ""),
        "customer_facing_human_review_scope": str(campaign.get("customer_facing_human_review_scope") or ""),
        "customer_facing_agent_limitations": str(campaign.get("customer_facing_agent_limitations") or ""),
        "internal_fixture_description": str(campaign.get("internal_fixture_description") or ""),
        "client_name": str(campaign.get("customer_facing_company_name") or campaign.get("client_name") or "Generic Campaign Client"),
        "objective": str(campaign.get("objective") or "appointment_setting"),
        "primary_customer_issue_phrase": str(campaign.get("primary_customer_issue_phrase") or ""),
        "short_relevance_question": str(campaign.get("short_relevance_question") or ""),
        "campaign_purpose_phrase": str(campaign.get("campaign_purpose_phrase") or ""),
        "product_detail_answer": str(campaign.get("product_detail_answer") or ""),
        "product_or_offer_summary": str(campaign.get("customer_facing_offer_summary") or campaign.get("product_or_offer_summary") or ""),
        "high_level_value_proposition": str(
            campaign.get("customer_facing_value_proposition") or campaign.get("high_level_value_proposition") or ""
        ),
        "allowed_high_level_capabilities": _string_list(campaign.get("allowed_high_level_capabilities")),
        "agent_call_objective": str(campaign.get("customer_facing_call_objective") or campaign.get("agent_call_objective") or ""),
        "human_followup_owner": str(
            campaign.get("human_followup_owner")
            or campaign.get("human_handoff_role")
            or "qualified human specialist"
        ),
        "appointment_target": str(
            campaign.get("appointment_target")
            or campaign.get("scheduling_goal")
            or "human review"
        ),
        "human_review_scope": str(campaign.get("customer_facing_human_review_scope") or campaign.get("human_review_scope") or ""),
        "agent_can_say": _string_list(campaign.get("agent_can_say")),
        "agent_must_not_claim": _string_list(campaign.get("agent_must_not_claim")),
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "regulated_cautions": regulated_cautions,
        "vertical_blocked_claim_types": vertical_blocked_claims,
    }

    return {
        "adapter_id": CAMPAIGN_PLAYBOOK_ADAPTER_ID,
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "vertical_id": vertical_id,
        "universal_knowledge_id": universal_sales_knowledge.universal_knowledge_id(),
        "vertical_playbook_id": vertical_id,
        "campaign_playbook_id": str(campaign.get("campaign_playbook_id") or f"{campaign_id}-playbook"),
        "campaign_context": campaign_context,
        "regulated_cautions": regulated_cautions,
        "diagnostic_gaps": diagnostic_gaps,
        "core_diagnostic_gaps": core_diagnostic_gaps,
        "gap_order": gap_order,
        "safety": dict(SAFETY_FLAGS),
    }


def resolve_campaign_playbook(campaign: dict[str, Any] | None = None) -> dict[str, Any]:
    if _has_generic_campaign_playbook_config(campaign):
        return _resolve_generic_campaign_playbook(dict(campaign or {}))
    return _resolve_routesignal_playbook(campaign)


def default_campaign_playbook() -> dict[str, Any]:
    return resolve_campaign_playbook(None)


def campaign_playbook_id(campaign: dict[str, Any] | None = None) -> str:
    return str(resolve_campaign_playbook(campaign).get("campaign_playbook_id") or "")


def campaign_vertical_id(campaign: dict[str, Any] | None = None) -> str:
    return str(resolve_campaign_playbook(campaign).get("vertical_id") or "")


def campaign_gap_labels(campaign: dict[str, Any] | None = None) -> dict[str, str]:
    playbook = resolve_campaign_playbook(campaign)
    return {
        gap_id: str(gap.get("label") or gap_id)
        for gap_id, gap in (playbook.get("diagnostic_gaps") or {}).items()
    }


def campaign_core_diagnostic_gaps(campaign: dict[str, Any] | None = None) -> list[str]:
    return list(resolve_campaign_playbook(campaign).get("core_diagnostic_gaps") or [])


def campaign_gap_order(campaign: dict[str, Any] | None = None) -> list[str]:
    return list(resolve_campaign_playbook(campaign).get("gap_order") or [])


def campaign_supported_gap_ids(campaign: dict[str, Any] | None = None) -> list[str]:
    return list(campaign_gap_order(campaign))


def campaign_gap_definition(gap_id: str | None, campaign: dict[str, Any] | None = None) -> dict[str, Any]:
    if not gap_id:
        return {}
    return deepcopy((resolve_campaign_playbook(campaign).get("diagnostic_gaps") or {}).get(gap_id) or {})


def campaign_review_focus(gap_id: str | None, campaign: dict[str, Any] | None = None) -> str | None:
    gap = campaign_gap_definition(gap_id, campaign)
    value = gap.get("review_focus")
    return str(value) if value else None


def campaign_next_gap_candidates(gap_id: str | None, campaign: dict[str, Any] | None = None) -> list[str]:
    return list(campaign_gap_definition(gap_id, campaign).get("next_gap_candidates") or [])


def validate_campaign_playbook(playbook: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    required_top_level = {
        "adapter_id",
        "schema_version",
        "campaign_id",
        "vertical_id",
        "universal_knowledge_id",
        "vertical_playbook_id",
        "campaign_playbook_id",
        "campaign_context",
        "diagnostic_gaps",
        "core_diagnostic_gaps",
        "gap_order",
        "safety",
    }
    missing = sorted(required_top_level - set(playbook))
    if missing:
        failures.append(f"missing top-level fields: {missing}")
    if playbook.get("adapter_id") != CAMPAIGN_PLAYBOOK_ADAPTER_ID:
        failures.append("adapter_id mismatch")
    if playbook.get("schema_version") != SCHEMA_VERSION:
        failures.append("schema_version mismatch")
    if playbook.get("vertical_id") not in vertical_sales_playbooks.all_vertical_ids():
        failures.append("vertical_id not found in vertical playbooks")
    if playbook.get("universal_knowledge_id") != universal_sales_knowledge.universal_knowledge_id():
        failures.append("universal_knowledge_id mismatch")

    diagnostic_gaps = playbook.get("diagnostic_gaps") or {}
    gap_order = list(playbook.get("gap_order") or [])
    core_diagnostic_gaps = list(playbook.get("core_diagnostic_gaps") or [])
    if not isinstance(diagnostic_gaps, dict) or not diagnostic_gaps:
        failures.append("diagnostic_gaps must be a populated dict")
        diagnostic_gaps = {}
    if not gap_order:
        failures.append("gap_order must be populated")
    if not core_diagnostic_gaps:
        failures.append("core_diagnostic_gaps must be populated")
    if set(gap_order) != set(diagnostic_gaps):
        failures.append("gap_order must match diagnostic gap ids")
    unknown_core = sorted(set(core_diagnostic_gaps) - set(gap_order))
    if unknown_core:
        failures.append(f"core_diagnostic_gaps not present in gap_order: {unknown_core}")

    is_routesignal_playbook = playbook.get("campaign_playbook_id") == routesignal_playbook.PLAYBOOK_ID
    if is_routesignal_playbook:
        if playbook.get("core_diagnostic_gaps") != routesignal_playbook.core_diagnostic_gaps():
            failures.append("core diagnostic gaps changed")
        if playbook.get("gap_order") != routesignal_playbook.gap_ids():
            failures.append("gap order changed")
    else:
        vertical_cautions = set(vertical_sales_playbooks.vertical_regulated_cautions(str(playbook.get("vertical_id") or "")))
        output_cautions = set(playbook.get("regulated_cautions") or (playbook.get("campaign_context") or {}).get("regulated_cautions") or [])
        missing_cautions = sorted(vertical_cautions - output_cautions)
        if missing_cautions:
            failures.append(f"regulated cautions missing from adapter output: {missing_cautions}")

    universal_pain_ids = set(universal_sales_knowledge.all_generic_pain_dimension_ids())
    qualification_ids = set(universal_sales_knowledge.all_qualification_dimension_ids())
    for gap_id in gap_order:
        gap = diagnostic_gaps.get(gap_id)
        if not isinstance(gap, dict):
            failures.append(f"{gap_id}: missing diagnostic gap")
            continue
        for field in [
            "campaign_gap_id",
            "label",
            "universal_pain_dimensions",
            "qualification_dimensions",
            "definition",
            "causal_story",
            "customer_language",
            "evidence_positive",
            "evidence_negative",
            "diagnostic_questions",
            "value_bridge",
            "review_focus",
        ]:
            if gap.get(field) in (None, "", []):
                failures.append(f"{gap_id}.{field}: missing")
        if "next_gap_candidates" not in gap or not isinstance(gap.get("next_gap_candidates"), list):
            failures.append(f"{gap_id}.next_gap_candidates: must be a list")
        unknown_pain = sorted(set(gap.get("universal_pain_dimensions") or []) - universal_pain_ids)
        unknown_qual = sorted(set(gap.get("qualification_dimensions") or []) - qualification_ids)
        if unknown_pain:
            failures.append(f"{gap_id}: unknown universal pain dimensions {unknown_pain}")
        if unknown_qual:
            failures.append(f"{gap_id}: unknown qualification dimensions {unknown_qual}")

    safety = playbook.get("safety") or {}
    for key, expected in SAFETY_FLAGS.items():
        if safety.get(key) is not expected:
            failures.append(f"safety.{key}: must be {expected}")

    return {
        "valid": not failures,
        "adapter_id": playbook.get("adapter_id"),
        "campaign_playbook_id": playbook.get("campaign_playbook_id"),
        "vertical_id": playbook.get("vertical_id"),
        "universal_knowledge_id": playbook.get("universal_knowledge_id"),
        "failures": failures,
    }


def validate_campaign_playbook_adapter() -> dict[str, Any]:
    playbook = default_campaign_playbook()
    validation = validate_campaign_playbook(playbook)
    return {
        "valid": validation.get("valid") is True,
        "adapter_id": CAMPAIGN_PLAYBOOK_ADAPTER_ID,
        "campaign_playbook_id": campaign_playbook_id(),
        "vertical_id": campaign_vertical_id(),
        "universal_knowledge_id": playbook.get("universal_knowledge_id"),
        "supported_gap_ids": campaign_supported_gap_ids(),
        "safety": dict(SAFETY_FLAGS),
        "failures": list(validation.get("failures") or []),
    }


# Legacy campaign-gap helper surface consumed by contextual_buyer_semantics.
def normalize_text(text: str) -> str:
    return routesignal_playbook.normalize_text(text)


def gap_ids() -> list[str]:
    return campaign_supported_gap_ids()


def core_diagnostic_gaps() -> list[str]:
    return campaign_core_diagnostic_gaps()


def gap_labels() -> dict[str, str]:
    return campaign_gap_labels()


def gap_definition(gap_id: str | None) -> dict[str, Any]:
    return campaign_gap_definition(gap_id)


def customer_label(gap_id: str | None) -> str:
    definition = campaign_gap_definition(gap_id)
    return str(definition.get("label") or gap_id or "that follow-up gap")


def review_focus(gap_id: str | None) -> str | None:
    return campaign_review_focus(gap_id)


def value_bridge(gap_id: str | None) -> str:
    definition = campaign_gap_definition(gap_id)
    return str(definition.get("value_bridge") or routesignal_playbook.value_bridge(gap_id))


def diagnostic_question(gap_id: str | None) -> str:
    definition = campaign_gap_definition(gap_id)
    questions = definition.get("diagnostic_questions") or []
    if questions:
        return str(questions[0])
    return routesignal_playbook.diagnostic_question(gap_id)


def ordered_gap_ids(gaps: list[str] | tuple[str, ...] | set[str]) -> list[str]:
    return routesignal_playbook.ordered_gap_ids(gaps)


def gaps_from_text(text: str) -> list[str]:
    return routesignal_playbook.gaps_from_text(text)


def first_gap_from_text(text: str) -> str | None:
    return routesignal_playbook.first_gap_from_text(text)


def cleared_gaps_from_text(text: str) -> list[str]:
    return routesignal_playbook.cleared_gaps_from_text(text)


def confirmed_gaps_from_text(text: str) -> list[str]:
    return routesignal_playbook.confirmed_gaps_from_text(text)


def remaining_gaps(
    *,
    cleared_gaps: list[str] | tuple[str, ...] | set[str],
    confirmed_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    candidate_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
) -> list[str]:
    return routesignal_playbook.remaining_gaps(
        cleared_gaps=cleared_gaps,
        confirmed_gaps=confirmed_gaps,
        candidate_gaps=candidate_gaps,
    )


def next_gap(
    *,
    cleared_gaps: list[str] | tuple[str, ...] | set[str],
    confirmed_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
    candidate_gaps: list[str] | tuple[str, ...] | set[str] | None = None,
) -> str | None:
    return routesignal_playbook.next_gap(
        cleared_gaps=cleared_gaps,
        confirmed_gaps=confirmed_gaps,
        candidate_gaps=candidate_gaps,
    )


def rank_confirmed_gaps(gaps: list[str], utterance: str = "") -> tuple[str | None, list[str]]:
    return routesignal_playbook.rank_confirmed_gaps(gaps, utterance)


def playbook_trace(
    *,
    gap_id: str | None,
    cleared_gaps: list[str] | None = None,
    confirmed_gaps: list[str] | None = None,
    candidate_gaps: list[str] | None = None,
) -> dict[str, Any]:
    trace = routesignal_playbook.playbook_trace(
        gap_id=gap_id,
        cleared_gaps=cleared_gaps,
        confirmed_gaps=confirmed_gaps,
        candidate_gaps=candidate_gaps,
    )
    adapted_gap = campaign_gap_definition(trace.get("playbook_gap"))
    trace.update(
        {
            "adapter_id": CAMPAIGN_PLAYBOOK_ADAPTER_ID,
            "vertical_id": DEFAULT_VERTICAL_ID,
            "universal_knowledge_id": universal_sales_knowledge.universal_knowledge_id(),
            "campaign_playbook_id": routesignal_playbook.PLAYBOOK_ID,
            "universal_pain_dimensions": list(adapted_gap.get("universal_pain_dimensions") or []),
            "qualification_dimensions": list(adapted_gap.get("qualification_dimensions") or []),
        }
    )
    return trace
