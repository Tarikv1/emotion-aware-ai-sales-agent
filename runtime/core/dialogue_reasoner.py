from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from runtime.core import live_voice_session_policy as session_policy


DIALOGUE_REASONER_ID = "DIALOGUE-REASONER-001"
REASONER_SCHEMA_VERSION = 1

REASONER_SCHEMA_FIELDS = [
    "dialogue_act",
    "buyer_intent",
    "resolved_topic",
    "sales_stage",
    "response_strategy",
    "must_include",
    "must_avoid",
    "safety_boundary",
    "confidence",
]

ALLOWED_DIALOGUE_ACTS = {
    "agent_open",
    "opening_greeting",
    "caller_identity_question",
    "previous_question_clarification",
    "ambiguous_negative",
    "callback_request",
    "callback_time",
    "price_question",
    "plan_question",
    "product_question",
    "workflow_question",
    "manual_tracking_objection",
    "selected_gap",
    "fit_question",
    "timing_objection",
    "effort_objection",
    "integration_question",
    "security_question",
    "specialist_request",
    "topic_shift",
    "low_information_acknowledgement",
    "asr_fragment",
    "unknown",
    "recommendation_request",
}

ALLOWED_BUYER_INTENTS = {
    "start_call",
    "small_talk_start",
    "identify_caller",
    "clarify_prior_question",
    "reject_or_decline_unclear",
    "schedule_callback",
    "confirm_callback_time",
    "understand_price",
    "understand_plan_value",
    "understand_product",
    "understand_workflow",
    "compare_manual_process",
    "name_workflow_gap",
    "evaluate_fit",
    "defer_timing",
    "evaluate_effort",
    "verify_integration",
    "verify_security",
    "request_human",
    "change_topic",
    "acknowledge_continue",
    "repair_asr",
    "off_topic_or_unclear",
    "ask_for_recommendation",
}

ALLOWED_SALES_STAGES = {
    "opening",
    "qualification",
    "discovery",
    "value_mapping",
    "objection_handling",
    "scheduling",
    "boundary",
    "repair",
}

ALLOWED_RESPONSE_STRATEGIES = {
    "open_with_permission",
    "answer_identity_then_offer_reason",
    "clarify_prior_question",
    "clarify_rejection_target",
    "ask_for_callback_time",
    "confirm_schedule_and_end",
    "answer_then_diagnose",
    "proactive_guided_selling",
    "map_gap_to_value",
    "guarded_boundary",
    "avoid_unnecessary_handoff",
    "repeat_request",
    "refocus_to_sales_call",
    "diagnose_before_recommendation",
}

ALLOWED_SAFETY_BOUNDARIES = {
    "none",
    "integration_claim_boundary",
    "security_claim_boundary",
    "human_handoff_boundary",
    "agency_preservation_boundary",
    "asr_quality_boundary",
}

GENERIC_FOLLOWUP_SIGNALS = {
    "tell me more",
    "what else",
    "what else should i know",
    "anything else",
    "why does that matter",
    "why would that matter",
    "how would it help",
    "how does that help",
}


def _contains_any(normalized: str, phrases: set[str]) -> bool:
    return session_policy.normalized_contains_any(normalized, phrases)


def _normalized(text: str) -> str:
    return session_policy.normalize_text(text)


def _turns(session_state: dict | None) -> list[dict[str, Any]]:
    return list((session_state or {}).get("turns") or [])


def _previous_call_control(turns: list[dict[str, Any]]) -> str:
    if not turns:
        return ""
    summary = turns[-1].get("summary") or {}
    return str(summary.get("call_control") or "")


def _resolved_focus(turns: list[dict[str, Any]]) -> str | None:
    return session_policy.dialogue_focus_from_turns(turns)


def _campaign_identity_terms(campaign: dict | None) -> list[str]:
    context = session_policy.generic_campaign_context(campaign)
    return [context["client"], context["offer"]]


def _packet(
    *,
    dialogue_act: str,
    buyer_intent: str,
    resolved_topic: str,
    sales_stage: str,
    response_strategy: str,
    safety_boundary: str = "none",
    must_include: list[str] | None = None,
    must_avoid: list[str] | None = None,
    confidence: float = 0.82,
) -> dict[str, Any]:
    packet = {
        "dialogue_act": dialogue_act,
        "buyer_intent": buyer_intent,
        "resolved_topic": resolved_topic,
        "sales_stage": sales_stage,
        "response_strategy": response_strategy,
        "must_include": list(must_include or []),
        "must_avoid": list(must_avoid or []),
        "safety_boundary": safety_boundary,
        "confidence": round(float(confidence), 2),
    }
    validate_reasoning_packet(packet)
    return packet


def _topic_shift_or_direct(
    *,
    direct_act: str,
    direct_intent: str,
    topic: str,
    resolved_focus: str | None,
    sales_stage: str = "discovery",
    response_strategy: str = "answer_then_diagnose",
    must_include: list[str] | None = None,
) -> dict[str, Any]:
    if resolved_focus and resolved_focus != topic:
        return _packet(
            dialogue_act="topic_shift",
            buyer_intent="change_topic",
            resolved_topic=topic,
            sales_stage=sales_stage,
            response_strategy=response_strategy,
            must_include=must_include,
            confidence=0.86,
        )
    return _packet(
        dialogue_act=direct_act,
        buyer_intent=direct_intent,
        resolved_topic=topic,
        sales_stage=sales_stage,
        response_strategy=response_strategy,
        must_include=must_include,
        confidence=0.86,
    )


def build_reasoning_context(transcript: str, session_state: dict | None, campaign: dict | None) -> dict[str, Any]:
    turns = _turns(session_state)
    normalized = _normalized(transcript)
    return {
        "reasoner_id": DIALOGUE_REASONER_ID,
        "transcript": transcript,
        "normalized_transcript": normalized,
        "language": str((campaign or {}).get("language") or "en"),
        "campaign_id": (campaign or {}).get("campaign_id"),
        "client_name": (campaign or {}).get("client_name"),
        "product_name": (campaign or {}).get("product_name"),
        "resolved_focus": _resolved_focus(turns),
        "selected_focus": session_policy.focus_from_transcript(normalized),
        "previous_agent_question": session_policy.previous_agent_question(turns),
        "turn_count": len(turns),
    }


def reason_about_turn(
    transcript: str,
    session_state: dict | None,
    campaign: dict | None,
    *,
    mode: str = "baseline",
    provider: Callable[[str], str | dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if mode == "baseline":
        return deterministic_reason_about_turn(transcript, session_state, campaign)
    if mode != "llm":
        raise ValueError(f"Unsupported dialogue reasoner mode: {mode}")
    if provider is None:
        raise ValueError("LLM dialogue reasoner mode requires an explicit provider callable")
    prompt = render_strict_json_reasoner_prompt(build_reasoning_context(transcript, session_state, campaign))
    raw = provider(prompt)
    if isinstance(raw, str):
        raw = parse_json_object(raw)
    return validate_reasoning_packet(raw)


def deterministic_reason_about_turn(
    transcript: str,
    session_state: dict | None,
    campaign: dict | None,
) -> dict[str, Any]:
    normalized = _normalized(transcript)
    turns = _turns(session_state)
    resolved_focus = _resolved_focus(turns)
    selected_focus = session_policy.focus_from_transcript(normalized)
    previous_question = session_policy.previous_agent_question(turns)

    if session_policy.is_agent_open_turn(normalized):
        return _packet(
            dialogue_act="agent_open",
            buyer_intent="start_call",
            resolved_topic="qualification",
            sales_stage="opening",
            response_strategy="open_with_permission",
            must_include=["caller identity", "permission check", "missed callbacks or handoffs"],
            confidence=0.99,
        )

    if session_policy.looks_like_asr_fragment(normalized, selected_focus):
        return _packet(
            dialogue_act="asr_fragment",
            buyer_intent="repair_asr",
            resolved_topic="asr_quality",
            sales_stage="repair",
            response_strategy="repeat_request",
            safety_boundary="asr_quality_boundary",
            must_avoid=["guessing buyer intent from a fragment"],
            confidence=0.94,
        )

    if session_policy.is_opening_greeting(normalized) and (
        not turns or not resolved_focus or _previous_call_control(turns) in {"end-call", "hang-up", "schedule-and-end"}
    ):
        return _packet(
            dialogue_act="opening_greeting",
            buyer_intent="small_talk_start",
            resolved_topic="qualification",
            sales_stage="opening",
            response_strategy="open_with_permission",
            must_include=["caller identity", "permission check"],
            confidence=0.92,
        )

    if session_policy.has_callback_time_signal(normalized):
        return _packet(
            dialogue_act="callback_time",
            buyer_intent="confirm_callback_time",
            resolved_topic="timing",
            sales_stage="scheduling",
            response_strategy="confirm_schedule_and_end",
            must_include=["callback", "goodbye"],
            confidence=0.94,
        )

    selected_gap = session_policy.selected_sales_gap_from_transcript(normalized)
    if selected_gap and (
        resolved_focus in {"price", "fit", "details", "effort", "qualification"}
        or _contains_any(normalized, {"missed callback", "missed callbacks", "happen more often", "bigger problem"})
    ):
        return _packet(
            dialogue_act="selected_gap",
            buyer_intent="name_workflow_gap",
            resolved_topic=selected_gap,
            sales_stage="value_mapping",
            response_strategy="map_gap_to_value",
            must_include=[selected_gap],
            confidence=0.9,
        )

    if _contains_any(normalized, {"do not have time", "dont have time", "don t have time", "no time", "not right now"}):
        return _packet(
            dialogue_act="callback_request",
            buyer_intent="schedule_callback",
            resolved_topic="timing",
            sales_stage="scheduling",
            response_strategy="ask_for_callback_time",
            must_include=["callback time"],
            confidence=0.9,
        )

    if session_policy.has_callback_request_signal(normalized):
        return _packet(
            dialogue_act="callback_request",
            buyer_intent="schedule_callback",
            resolved_topic="timing",
            sales_stage="scheduling",
            response_strategy="ask_for_callback_time",
            must_include=["callback time"],
            confidence=0.9,
        )

    if session_policy.has_caller_identity_question(normalized):
        return _packet(
            dialogue_act="caller_identity_question",
            buyer_intent="identify_caller",
            resolved_topic="caller_identity",
            sales_stage="repair",
            response_strategy="answer_identity_then_offer_reason",
            must_include=_campaign_identity_terms(campaign),
            confidence=0.95,
        )

    if previous_question and session_policy.is_previous_question_clarification_request(normalized):
        return _packet(
            dialogue_act="previous_question_clarification",
            buyer_intent="clarify_prior_question",
            resolved_topic=resolved_focus or "qualification",
            sales_stage="repair",
            response_strategy="clarify_prior_question",
            must_include=["plain terms"],
            confidence=0.93,
        )

    if previous_question and session_policy.is_ambiguous_negative_reply(normalized):
        return _packet(
            dialogue_act="ambiguous_negative",
            buyer_intent="reject_or_decline_unclear",
            resolved_topic=resolved_focus or "qualification",
            sales_stage="repair",
            response_strategy="clarify_rejection_target",
            must_include=["not a good time", "not an issue"],
            confidence=0.91,
        )

    if _contains_any(normalized, {"soc 2", "soc2", "security", "secure", "compliance"}):
        return _packet(
            dialogue_act="security_question",
            buyer_intent="verify_security",
            resolved_topic="security",
            sales_stage="boundary",
            response_strategy="guarded_boundary",
            safety_boundary="security_claim_boundary",
            must_avoid=["SOC 2 certified", "guaranteed compliance"],
            confidence=0.94,
        )

    if _contains_any(normalized, {"salesforce", "hubspot", "integrate", "integration", "connect with", "crm"}):
        return _packet(
            dialogue_act="integration_question",
            buyer_intent="verify_integration",
            resolved_topic="integration",
            sales_stage="boundary",
            response_strategy="guarded_boundary",
            safety_boundary="integration_claim_boundary",
            must_avoid=["exact compatibility claim", "permissions claim"],
            confidence=0.9,
        )

    if _contains_any(normalized, {"do i need to talk to a specialist", "need a specialist", "talk to a specialist"}):
        return _packet(
            dialogue_act="specialist_request",
            buyer_intent="request_human",
            resolved_topic="handoff_boundary",
            sales_stage="boundary",
            response_strategy="avoid_unnecessary_handoff",
            safety_boundary="human_handoff_boundary",
            must_include=["cover basics"],
            confidence=0.88,
        )

    product_question = _contains_any(
        normalized,
        {
            "what does your product",
            "what does the product",
            "what do you do",
            "what does it do",
            "what is your product",
            "product actually do",
        },
    )
    if product_question:
        return _topic_shift_or_direct(
            direct_act="product_question",
            direct_intent="understand_product",
            topic="product_details",
            resolved_focus=resolved_focus,
            must_include=["lead routing", "follow-up", "handoff"],
        )

    workflow_question = _contains_any(
        normalized,
        {"workflow include", "workflow includes", "what is included", "included in the workflow"},
    )
    if workflow_question:
        return _topic_shift_or_direct(
            direct_act="workflow_question",
            direct_intent="understand_workflow",
            topic="workflow_scope",
            resolved_focus=resolved_focus,
            must_include=["lead capture", "routing", "handoff review"],
        )

    if _contains_any(normalized, {"manual", "spreadsheet", "tracking leads manually", "track leads manually"}):
        return _packet(
            dialogue_act="manual_tracking_objection",
            buyer_intent="compare_manual_process",
            resolved_topic="manual_tracking",
            sales_stage="objection_handling",
            response_strategy="answer_then_diagnose",
            must_include=["ownership", "callback", "handoff"],
            confidence=0.88,
        )

    if _contains_any(normalized, {"fifty nine", "59 dollars", "$59", "growth plan", "growth"}):
        return _packet(
            dialogue_act="plan_question",
            buyer_intent="understand_plan_value",
            resolved_topic="growth_plan",
            sales_stage="discovery",
            response_strategy="answer_then_diagnose",
            must_include=["priority routing", "reminders", "handoff review"],
            confidence=0.88,
        )

    if _contains_any(normalized, {"small team", "small teams", "starter"}):
        return _packet(
            dialogue_act="fit_question",
            buyer_intent="evaluate_fit",
            resolved_topic="starter_plan",
            sales_stage="discovery",
            response_strategy="answer_then_diagnose",
            must_include=["Starter", "Growth"],
            confidence=0.85,
        )

    if selected_gap:
        return _packet(
            dialogue_act="selected_gap",
            buyer_intent="name_workflow_gap",
            resolved_topic=selected_gap,
            sales_stage="value_mapping",
            response_strategy="map_gap_to_value",
            must_include=[selected_gap],
            confidence=0.9,
        )

    if _contains_any(normalized, {"recommend", "what should i choose", "what do you recommend"}):
        return _packet(
            dialogue_act="recommendation_request",
            buyer_intent="ask_for_recommendation",
            resolved_topic=resolved_focus or selected_focus or "qualification",
            sales_stage="value_mapping",
            response_strategy="diagnose_before_recommendation",
            safety_boundary="agency_preservation_boundary",
            must_avoid=["decide for the buyer", "guaranteed ROI"],
            confidence=0.87,
        )

    if session_policy.is_low_information_acknowledgement(normalized) or (
        resolved_focus and not selected_focus and _contains_any(normalized, GENERIC_FOLLOWUP_SIGNALS)
    ):
        return _packet(
            dialogue_act="low_information_acknowledgement",
            buyer_intent="acknowledge_continue",
            resolved_topic=resolved_focus or "qualification",
            sales_stage="value_mapping" if resolved_focus == "price" else "qualification",
            response_strategy="proactive_guided_selling",
            must_include=["next diagnostic question"],
            confidence=0.82,
        )

    if selected_focus == "price" or _contains_any(normalized, {"price", "cost", "monthly price", "budget", "money"}):
        return _packet(
            dialogue_act="price_question",
            buyer_intent="understand_price",
            resolved_topic="price",
            sales_stage="value_mapping" if resolved_focus == "price" else "discovery",
            response_strategy="proactive_guided_selling" if resolved_focus == "price" else "answer_then_diagnose",
            must_include=["Starter", "Growth"],
            confidence=0.86,
        )

    if selected_focus == "fit" or _contains_any(normalized, {"fit", "relevant", "situation", "problem"}):
        return _packet(
            dialogue_act="fit_question",
            buyer_intent="evaluate_fit",
            resolved_topic="fit",
            sales_stage="discovery",
            response_strategy="answer_then_diagnose",
            must_include=["workflow gap"],
            confidence=0.82,
        )

    if selected_focus == "timing" or _contains_any(normalized, {"timing", "not good right now", "later", "not now"}):
        return _packet(
            dialogue_act="timing_objection",
            buyer_intent="defer_timing",
            resolved_topic="timing",
            sales_stage="objection_handling",
            response_strategy="answer_then_diagnose",
            must_include=["callback", "no pressure"],
            confidence=0.82,
        )

    if selected_focus == "effort" or _contains_any(normalized, {"worth my time", "worth the effort", "reviewing options", "viewing options", "effort"}):
        return _packet(
            dialogue_act="effort_objection",
            buyer_intent="evaluate_effort",
            resolved_topic="effort",
            sales_stage="objection_handling",
            response_strategy="answer_then_diagnose",
            must_include=["missed follow-up", "time"],
            confidence=0.82,
        )

    return _packet(
        dialogue_act="unknown",
        buyer_intent="off_topic_or_unclear",
        resolved_topic="unknown",
        sales_stage="repair",
        response_strategy="refocus_to_sales_call",
        confidence=0.48,
    )


def provider_boundary_packet(mode: str) -> dict[str, Any]:
    return {
        "reasoner_id": DIALOGUE_REASONER_ID,
        "mode": mode,
        "llm_default_enabled": False,
        "provider_calls_made": False,
        "text_sent_to_provider": False,
        "requires_explicit_provider_callable": mode == "llm",
        "stores_provider_response": False,
        "opens_prod_102": False,
    }


def render_strict_json_reasoner_prompt(context: dict[str, Any]) -> str:
    schema = {field: field_type for field, field_type in {
        "dialogue_act": "one allowed dialogue act",
        "buyer_intent": "one allowed buyer intent",
        "resolved_topic": "short snake_case topic",
        "sales_stage": "one allowed sales stage",
        "response_strategy": "one allowed response strategy",
        "must_include": ["strings the response composer should include if safe"],
        "must_avoid": ["strings or behaviors the response composer must avoid"],
        "safety_boundary": "one allowed safety boundary",
        "confidence": "float from 0.0 to 1.0",
    }.items()}
    return "\n".join(
        [
            "You are a bounded dialogue reasoner for a sales-agent runtime.",
            "Classify the current runtime turn and return only strict JSON.",
            "Do not write customer-facing copy.",
            "Do not invent campaign facts.",
            "Do not decide for the buyer.",
            "Use exact labels from the allowed lists; do not substitute near-synonyms.",
            "",
            "Special runtime sentinels:",
            (
                "- __agent_open__ is an internal agent-open sentinel, not buyer speech. "
                "For that transcript return dialogue_act=agent_open, buyer_intent=start_call, "
                "resolved_topic=qualification, sales_stage=opening, "
                "response_strategy=open_with_permission, safety_boundary=none."
            ),
            "",
            "Runtime label policy:",
            "- Opening greetings resolve to resolved_topic=qualification; do not use greeting.",
            (
                "- Clarification, caller identity, ambiguous negatives, and ASR repairs use sales_stage=repair; "
                "do not classify them as opening or qualification."
            ),
            (
                "- Boundary questions use sales_stage=boundary and guarded boundary labels: "
                "integration uses response_strategy=guarded_boundary and safety_boundary=integration_claim_boundary; "
                "security uses response_strategy=guarded_boundary and safety_boundary=security_claim_boundary; "
                "human handoff questions use safety_boundary=human_handoff_boundary."
            ),
            (
                "- Use context.resolved_focus to preserve continuity. If it is price and the buyer asks for more price detail, "
                "use sales_stage=value_mapping and response_strategy=proactive_guided_selling."
            ),
            (
                "- Topic shifts from an existing focus use dialogue_act=topic_shift and buyer_intent=change_topic "
                "while resolving the new topic exactly."
            ),
            "- Low-information acknowledgements use response_strategy=proactive_guided_selling.",
            "- ASR fragments use resolved_topic=asr_quality and safety_boundary=asr_quality_boundary.",
            (
                "- Use resolved_topic labels exactly when applicable: qualification, caller_identity, timing, price, "
                "growth_plan, starter_plan, product_details, workflow_scope, manual_tracking, handoffs, callbacks, "
                "fit, effort, integration, security, handoff_boundary, asr_quality, unknown."
            ),
            (
                "- Do not emit synonym topics such as greeting, product, workflow, pricing, recommendation, "
                "starter_plan_fit, asr_issue, or clarification."
            ),
            (
                "- A no-time or not-right-now statement is a callback_request with buyer_intent=schedule_callback, "
                "sales_stage=scheduling, and response_strategy=ask_for_callback_time unless the buyer already gave a callback time."
            ),
            (
                "- Recommendation requests preserve buyer agency: use response_strategy=diagnose_before_recommendation, "
                "safety_boundary=agency_preservation_boundary, and keep resolved_topic on context.resolved_focus when available."
            ),
            "",
            "Allowed dialogue acts:",
            json.dumps(sorted(ALLOWED_DIALOGUE_ACTS), ensure_ascii=False),
            "Allowed buyer intents:",
            json.dumps(sorted(ALLOWED_BUYER_INTENTS), ensure_ascii=False),
            "Allowed sales stages:",
            json.dumps(sorted(ALLOWED_SALES_STAGES), ensure_ascii=False),
            "Allowed response strategies:",
            json.dumps(sorted(ALLOWED_RESPONSE_STRATEGIES), ensure_ascii=False),
            "Allowed safety boundaries:",
            json.dumps(sorted(ALLOWED_SAFETY_BOUNDARIES), ensure_ascii=False),
            "",
            "Schema:",
            json.dumps(schema, indent=2, ensure_ascii=False),
            "",
            "Context:",
            json.dumps(context, indent=2, ensure_ascii=False),
            "",
            "Return only JSON with exactly these fields:",
            json.dumps(REASONER_SCHEMA_FIELDS, ensure_ascii=False),
        ]
    )


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1)
    else:
        first = stripped.find("{")
        last = stripped.rfind("}")
        if first != -1 and last != -1 and first < last:
            stripped = stripped[first : last + 1]
    return json.loads(stripped)


def validate_reasoning_packet(packet: dict[str, Any]) -> dict[str, Any]:
    fields = set(packet.keys())
    expected = set(REASONER_SCHEMA_FIELDS)
    if fields != expected:
        raise ValueError(f"Reasoning packet fields mismatch: expected {sorted(expected)}, got {sorted(fields)}")
    if packet["dialogue_act"] not in ALLOWED_DIALOGUE_ACTS:
        raise ValueError(f"Unsupported dialogue_act: {packet['dialogue_act']}")
    if packet["buyer_intent"] not in ALLOWED_BUYER_INTENTS:
        raise ValueError(f"Unsupported buyer_intent: {packet['buyer_intent']}")
    if packet["sales_stage"] not in ALLOWED_SALES_STAGES:
        raise ValueError(f"Unsupported sales_stage: {packet['sales_stage']}")
    if packet["response_strategy"] not in ALLOWED_RESPONSE_STRATEGIES:
        raise ValueError(f"Unsupported response_strategy: {packet['response_strategy']}")
    if packet["safety_boundary"] not in ALLOWED_SAFETY_BOUNDARIES:
        raise ValueError(f"Unsupported safety_boundary: {packet['safety_boundary']}")
    if not isinstance(packet["must_include"], list) or not all(isinstance(item, str) for item in packet["must_include"]):
        raise ValueError("must_include must be a list of strings")
    if not isinstance(packet["must_avoid"], list) or not all(isinstance(item, str) for item in packet["must_avoid"]):
        raise ValueError("must_avoid must be a list of strings")
    confidence = float(packet["confidence"])
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(f"confidence out of range: {confidence}")
    packet["confidence"] = confidence
    return packet
