#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any


CORE_PACK_ID = "CORE-sales-delivery-playbook"


def build_core_sales_delivery_pack() -> dict[str, Any]:
    return {
        "core_pack_id": CORE_PACK_ID,
        "runtime_default_enabled": True,
        "external_provider_calls_made": False,
        "private_customer_data_used": False,
        "campaign_facts_override_rag": True,
        "persuasion_boundary": {
            "ethical_persuasion_allowed": True,
            "strong_persuasion_allowed": True,
            "real_campaign_urgency_allowed": True,
            "real_scarcity_allowed": True,
            "fake_urgency_allowed": False,
            "invented_scarcity_allowed": False,
            "hidden_material_facts_allowed": False,
            "exploit_vulnerable_customer_allowed": False,
            "rule": (
                "Use ethical persuasion. Strong persuasion is allowed when it is truthful, "
                "campaign-supported, reversible, and respectful."
            ),
        },
        "emotion_boundary": {
            "observable_empathy_allowed": True,
            "hidden_state_certainty_allowed": False,
            "protected_trait_inference_allowed": False,
            "allowed_examples": [
                "I understand why that would be frustrating.",
                "That makes sense.",
                "I hear the hesitation.",
                "I get why you would want to be careful here.",
            ],
            "blocked_examples": [
                "You are angry.",
                "You are afraid.",
                "I know exactly how you feel.",
                "I can tell you feel anxious.",
            ],
        },
        "sales_playbook": {
            "opener_rules": [
                "Open with a short, concrete reason for the call.",
                "Use permission-based framing when interruption risk is high.",
                "Keep the first turn short enough for the customer to respond.",
                "Use a respectful pattern interrupt only when it reduces confusion.",
            ],
            "common_objection_rules": [
                {
                    "objection": "not_interested",
                    "rule": "Acknowledge, ask one low-friction relevance question, then respect refusal.",
                },
                {
                    "objection": "send_info",
                    "rule": "Offer to send information, then ask what they want the information to answer.",
                },
                {
                    "objection": "price",
                    "rule": "Diagnose whether the issue is price, terms, value, or effort before answering.",
                },
                {"objection": "timing", "rule": "Ask about real timing without inventing urgency."},
                {"objection": "trust", "rule": "Use truthful proof or process clarity; do not overclaim."},
                {
                    "objection": "competitor",
                    "rule": "Respect the existing provider and compare only approved differentiators.",
                },
                {
                    "objection": "already_have_someone",
                    "rule": "Ask whether they are open to a quick comparison without implying current choice is wrong.",
                },
                {
                    "objection": "think_about_it",
                    "rule": "Clarify what they need to think through and offer a concrete next step.",
                },
                {
                    "objection": "partner_or_boss",
                    "rule": "Ask what the stakeholder will care about and suggest a clean follow-up.",
                },
            ],
            "closing_rules": [
                "Use trial closes to check fit before asking for commitment.",
                "Use next-step closes more often than hard closes.",
                "When campaign urgency is real, state the deadline and the reversible next step.",
                "Do not turn hesitation into pressure.",
            ],
        },
        "delivery_pack": {
            "speech_delivery_rules": [
                "Use calm confidence rather than hype.",
                "Prefer short clauses over dense explanations.",
                "Pause before a clarifying question.",
                "Use light natural fillers only in eligible freeform speech.",
                "Match energy without overacting.",
                "Use observable empathy before objection diagnosis.",
                "Avoid phrase shapes that invite wrong emphasis.",
                "Keep protected text exact.",
                "Use provider-facing delivery metadata instead of changing final_response where possible.",
            ],
            "voice_layer_contract": "Feeds RESP-002 and VOICE layers; final_response remains policy-owned.",
        },
    }


def validate_core_sales_delivery_pack(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    serialized = json.dumps(payload, ensure_ascii=False).lower().replace("\\", "/")
    if payload.get("core_pack_id") != CORE_PACK_ID:
        errors.append("core_pack_id mismatch")
    if payload.get("campaign_facts_override_rag") is not True:
        errors.append("campaign facts must override RAG")
    if payload.get("persuasion_boundary", {}).get("fake_urgency_allowed") is not False:
        errors.append("fake urgency must be blocked")
    if payload.get("persuasion_boundary", {}).get("invented_scarcity_allowed") is not False:
        errors.append("invented scarcity must be blocked")
    if payload.get("emotion_boundary", {}).get("hidden_state_certainty_allowed") is not False:
        errors.append("hidden emotional certainty must be blocked")
    if "source_excerpt" in serialized:
        errors.append("source excerpts are not allowed")
    if "data/private" in serialized:
        errors.append("private data paths are not allowed")
    return errors


def render_core_sales_delivery_pack_report(payload: dict[str, Any]) -> str:
    validation_errors = validate_core_sales_delivery_pack(payload)
    lines = [
        "# Core Sales Delivery Playbook",
        "",
        "This report documents the always-on sales and delivery pack used before live RAG retrieval.",
        "",
        "## Boundaries",
        "",
        f"- Ethical persuasion allowed: `{payload['persuasion_boundary']['ethical_persuasion_allowed']}`",
        f"- Fake urgency allowed: `{payload['persuasion_boundary']['fake_urgency_allowed']}`",
        f"- Invented scarcity allowed: `{payload['persuasion_boundary']['invented_scarcity_allowed']}`",
        f"- Campaign facts override RAG: `{payload['campaign_facts_override_rag']}`",
        f"- Observable empathy allowed: `{payload['emotion_boundary']['observable_empathy_allowed']}`",
        f"- Hidden state certainty allowed: `{payload['emotion_boundary']['hidden_state_certainty_allowed']}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{not validation_errors}`",
        f"- Errors: `{', '.join(validation_errors) or 'none'}`",
    ]
    return "\n".join(lines) + "\n"
