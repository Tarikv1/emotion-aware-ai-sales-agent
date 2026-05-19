from __future__ import annotations

import json
from typing import Any

from runtime.core.dialogue_reasoner import parse_json_object


HYBRID_REASONER_ID = "DIALOGUE-REASONER-003"

HYBRID_REASONING_SCHEMA_FIELDS = [
    "reasoning_summary",
    "implied_buyer_concern",
    "selling_angle",
    "evidence_to_use",
    "next_diagnostic_question",
    "avoid",
    "confidence",
]

PROTECTED_ROUTE_FIELDS = {
    "dialogue_act",
    "buyer_intent",
    "resolved_topic",
    "sales_stage",
    "response_strategy",
    "safety_boundary",
}

LLM_BLOCKED_DIALOGUE_ACTS = {
    "agent_open",
    "opening_greeting",
    "caller_identity_question",
    "previous_question_clarification",
    "ambiguous_negative",
    "callback_request",
    "callback_time",
    "price_question",
    "plan_question",
    "timing_objection",
    "integration_question",
    "security_question",
    "specialist_request",
    "low_information_acknowledgement",
    "asr_fragment",
    "unknown",
    "recommendation_request",
}

LLM_ALLOWED_DIALOGUE_ACTS = {
    "product_question",
    "workflow_question",
    "manual_tracking_objection",
    "selected_gap",
    "fit_question",
    "effort_objection",
    "topic_shift",
}

DEFAULT_FORBIDDEN_TERMS = {
    "guaranteed roi",
    "guarantee roi",
    "guaranteed revenue",
    "soc 2 certified",
    "soc2 certified",
    "fully compliant",
    "exactly integrates",
    "will definitely",
    "discount",
    "free trial",
    "sign today",
    "contract",
    "payment",
}


def _text(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(_text(item) for item in value)
    return str(value or "")


def _normalized(value: Any) -> str:
    return " ".join(_text(value).lower().replace("_", " ").split())


def should_call_llm_reasoning(reasoning_packet: dict[str, Any]) -> bool:
    if reasoning_packet.get("safety_boundary") != "none":
        return False
    dialogue_act = str(reasoning_packet.get("dialogue_act") or "")
    if dialogue_act in LLM_BLOCKED_DIALOGUE_ACTS:
        return False
    return dialogue_act in LLM_ALLOWED_DIALOGUE_ACTS


def render_hybrid_reasoning_prompt(
    *,
    transcript: str,
    context: dict[str, Any],
    deterministic_reasoning: dict[str, Any],
    case_goal: str,
) -> str:
    schema = {
        "reasoning_summary": "one concise sentence explaining the buyer's likely meaning",
        "implied_buyer_concern": "the likely concern behind the buyer's words",
        "selling_angle": "the safest useful sales angle to help the response composer",
        "evidence_to_use": ["2 to 4 campaign-grounded points to use"],
        "next_diagnostic_question": "one short question the agent can ask next",
        "avoid": ["behaviors, claims, or wording to avoid"],
        "confidence": "float from 0.0 to 1.0",
    }
    return "\n".join(
        [
            "You are a reasoning assistant behind a deterministic sales-call runtime.",
            "Return only strict JSON. Do not include markdown.",
            "Do not write the final customer-facing response.",
            "Do not classify the turn. The deterministic runtime already owns classification.",
            "Do not override, repeat, reinterpret, or emit any protected route fields.",
            "Protected route fields:",
            json.dumps(sorted(PROTECTED_ROUTE_FIELDS), ensure_ascii=False),
            "",
            "Your job:",
            "- infer the buyer's concern",
            "- choose a safe selling angle",
            "- choose campaign-grounded evidence the composer may use",
            "- propose one next diagnostic question",
            "- name what to avoid",
            "",
            "Hard boundaries:",
            "- Do not invent pricing, security, integration, ROI, discounts, legal, payment, or contract claims.",
            "- Do not decide for the buyer.",
            "- Do not suggest call-control actions such as transfer, hang up, schedule, or close.",
            "- Keep the next question short and low pressure.",
            "",
            "Schema:",
            json.dumps(schema, indent=2, ensure_ascii=False),
            "",
            "Case goal:",
            case_goal,
            "",
            "Transcript:",
            transcript,
            "",
            "Runtime context:",
            json.dumps(context, indent=2, ensure_ascii=False),
            "",
            "Deterministic reasoning packet locked by runtime:",
            json.dumps(deterministic_reasoning, indent=2, ensure_ascii=False),
            "",
            "Return only JSON with exactly these fields:",
            json.dumps(HYBRID_REASONING_SCHEMA_FIELDS, ensure_ascii=False),
        ]
    )


def validate_hybrid_reasoning_packet(packet: dict[str, Any]) -> dict[str, Any]:
    fields = set(packet.keys())
    expected = set(HYBRID_REASONING_SCHEMA_FIELDS)
    if fields != expected:
        raise ValueError(f"Hybrid reasoning packet fields mismatch: expected {sorted(expected)}, got {sorted(fields)}")
    for field in ["reasoning_summary", "implied_buyer_concern", "selling_angle", "next_diagnostic_question"]:
        if not isinstance(packet[field], str) or not packet[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    for field in ["evidence_to_use", "avoid"]:
        if not isinstance(packet[field], list) or not 1 <= len(packet[field]) <= 5:
            raise ValueError(f"{field} must be a short list")
        if not all(isinstance(item, str) and item.strip() for item in packet[field]):
            raise ValueError(f"{field} must contain non-empty strings")
    confidence = float(packet["confidence"])
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError(f"confidence out of range: {confidence}")
    packet["confidence"] = confidence
    return packet


def parse_hybrid_reasoning_packet(text: str) -> dict[str, Any]:
    return validate_hybrid_reasoning_packet(parse_json_object(text))


def score_hybrid_reasoning_case(packet: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    combined = _normalized({key: value for key, value in packet.items() if key != "avoid"})
    mismatches: dict[str, Any] = {}
    if any(field in packet for field in PROTECTED_ROUTE_FIELDS):
        mismatches["protected_route_field_present"] = sorted(set(packet).intersection(PROTECTED_ROUTE_FIELDS))
    if not packet["next_diagnostic_question"].strip().endswith("?"):
        mismatches["next_diagnostic_question"] = "must end with a question mark"
    if len(packet["evidence_to_use"]) < 2:
        mismatches["evidence_to_use"] = "must include at least two evidence points"
    forbidden_terms = set(DEFAULT_FORBIDDEN_TERMS)
    forbidden_terms.update(str(term).lower() for term in case.get("forbidden_terms") or [])
    found_forbidden = sorted(term for term in forbidden_terms if term and term in combined)
    if found_forbidden:
        mismatches["forbidden_terms"] = found_forbidden
    missing_signal_groups = []
    for group in case.get("quality_signal_groups") or []:
        terms = [str(term).lower() for term in group if str(term).strip()]
        if terms and not any(term in combined for term in terms):
            missing_signal_groups.append(terms)
    if missing_signal_groups:
        mismatches["quality_signal_groups"] = missing_signal_groups
    return {
        "case_id": case["case_id"],
        "pass": not mismatches,
        "mismatches": mismatches,
    }
