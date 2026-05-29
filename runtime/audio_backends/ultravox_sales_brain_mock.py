#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any


REQUIRED_RESPONSE_FIELDS = {
    "allowed_to_speak",
    "buyer_facing_response",
    "next_action_id",
    "project_memory_updates",
    "prosody_hints",
    "must_not_say",
    "source_boundary",
    "side_effects_allowed",
    "call_should_end",
    "verifier_status",
    "safety_warnings",
}

INTERNAL_LANGUAGE = (
    "verifier",
    "schema",
    "tool",
    "internal",
    "project runtime",
    "canonical memory",
)

FAKE_SIDE_EFFECT_PATTERNS = (
    r"\bi (emailed|sent|scheduled|booked|added|updated)\b",
    r"\badded you to\b",
    r"\bput you in\b",
    r"\bcalendar invite\b",
)


def build_mock_project_memory() -> dict[str, Any]:
    return {
        "campaign_id": "synthetic_voice_sandbox",
        "campaign_truth_owner": "project_runtime",
        "canonical_memory_owner": "project_runtime",
        "approved_product_facts": [
            "This is a synthetic sandbox for an emotion-aware sales assistant.",
            "The project-owned sales brain must decide sales moves.",
            "No pricing or signup path is approved in this sandbox."
        ],
        "blocked_side_effects": [
            "CRM write",
            "email send",
            "calendar booking"
        ],
        "known_buyer_context": {
            "tools_mentioned": [],
            "needs_mentioned": [],
            "contact_boundary": "unknown"
        }
    }


def _base_response() -> dict[str, Any]:
    return {
        "allowed_to_speak": True,
        "buyer_facing_response": "",
        "next_action_id": "clarify",
        "project_memory_updates": [],
        "prosody_hints": {
            "tone": "calm",
            "pace": "steady",
            "emphasis": []
        },
        "must_not_say": [
            "I emailed you",
            "I booked your calendar",
            "I added you to the CRM",
            "guaranteed result",
            "approved price"
        ],
        "source_boundary": {
            "grounded_in_campaign_truth": True,
            "unsupported_claims_allowed": False,
            "raw_urls_allowed": False
        },
        "side_effects_allowed": False,
        "call_should_end": False,
        "verifier_status": "passed",
        "safety_warnings": []
    }


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def handle_project_sales_brain_next_move(request: dict) -> dict:
    utterance = str(request.get("buyer_utterance_text") or "").strip()
    lowered = utterance.lower()
    response = _base_response()

    if _contains_any(lowered, ("what is this", "who are you", "what are you")):
        response.update(
            {
                "buyer_facing_response": "This is a synthetic voice sandbox for an emotion-aware sales assistant. I can explain the fit without taking actions outside this call.",
                "next_action_id": "orient_buyer",
                "prosody_hints": {"tone": "clear", "pace": "measured", "emphasis": ["synthetic voice sandbox"]},
            }
        )
    elif "chatgpt" in lowered or "other tools" in lowered:
        response.update(
            {
                "buyer_facing_response": "That may cover general tasks. This sandbox tests whether sales calls can stay grounded in campaign facts and your buyer context.",
                "next_action_id": "differentiate_controlled_sales_guidance",
                "project_memory_updates": [{"field": "buyer_uses_general_tools", "value": True}],
                "prosody_hints": {"tone": "respectful", "pace": "steady", "emphasis": ["grounded"]},
            }
        )
    elif _contains_any(lowered, ("price", "cost", "how much")):
        response.update(
            {
                "buyer_facing_response": "I do not have an approved price in this sandbox. Tell me the use case, and I can keep the answer honest.",
                "next_action_id": "clarify_pricing_context",
                "safety_warnings": ["pricing_not_approved_for_sandbox"],
                "prosody_hints": {"tone": "plain", "pace": "slow", "emphasis": ["approved price"]},
            }
        )
    elif _contains_any(lowered, ("not a team", "by myself", "just me", "solo")):
        response.update(
            {
                "buyer_facing_response": "Then I will not frame this as a team rollout. For one person, the question is whether it saves repeated qualification work.",
                "next_action_id": "reframe_for_individual_user",
                "project_memory_updates": [{"field": "buyer_team_context", "value": "individual"}],
                "prosody_hints": {"tone": "adaptive", "pace": "steady", "emphasis": ["one person"]},
            }
        )
    elif _contains_any(lowered, ("already told you", "i told you")):
        response.update(
            {
                "buyer_facing_response": "You did: coding and voice. I will use that and focus on whether spoken sales turns can stay grounded.",
                "next_action_id": "repair_memory_acknowledgement",
                "project_memory_updates": [{"field": "buyer_needs_mentioned", "value": ["coding", "voice"]}],
                "prosody_hints": {"tone": "accountable", "pace": "slower", "emphasis": ["coding and voice"]},
            }
        )
    elif _contains_any(lowered, ("sign up", "signup", "get started", "start")):
        response.update(
            {
                "buyer_facing_response": "I cannot sign you up from this sandbox. The safe next step is a synthetic review path or a human follow-up outside this call.",
                "next_action_id": "safe_signup_boundary",
                "safety_warnings": ["signup_path_not_live"],
                "prosody_hints": {"tone": "firm", "pace": "steady", "emphasis": ["cannot sign you up"]},
            }
        )
    elif _contains_any(lowered, ("don't email", "do not email", "dont email", "crm")):
        response.update(
            {
                "buyer_facing_response": "Understood. I will not claim any email, CRM, or calendar action. We can keep this only in the current conversation.",
                "next_action_id": "respect_contact_boundary",
                "project_memory_updates": [{"field": "contact_boundary", "value": "no_email_or_crm"}],
                "prosody_hints": {"tone": "respectful", "pace": "steady", "emphasis": ["current conversation"]},
            }
        )
    elif _contains_any(lowered, ("thanks", "thank you", "ok thanks", "okay thanks")):
        response.update(
            {
                "buyer_facing_response": "Thanks. I will stop here.",
                "next_action_id": "end_call",
                "call_should_end": True,
                "prosody_hints": {"tone": "warm", "pace": "brief", "emphasis": []},
            }
        )
    else:
        response.update(
            {
                "buyer_facing_response": "I may be missing the point. What should I focus on: voice quality, sales guidance, or safe handoff?",
                "next_action_id": "natural_clarification",
                "prosody_hints": {"tone": "curious", "pace": "steady", "emphasis": ["focus"]},
            }
        )

    errors = validate_ultravox_tool_response(response)
    if errors:
        response["allowed_to_speak"] = False
        response["buyer_facing_response"] = "I need to clarify that before answering."
        response["next_action_id"] = "blocked_clarify"
        response["verifier_status"] = "blocked"
        response["safety_warnings"] = errors
    return response


def validate_ultravox_tool_response(response: dict) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_RESPONSE_FIELDS - set(response))
    if missing:
        errors.append(f"missing response fields: {missing}")
    if not isinstance(response.get("allowed_to_speak"), bool):
        errors.append("allowed_to_speak must be boolean")
    if not isinstance(response.get("buyer_facing_response"), str) or not response.get("buyer_facing_response", "").strip():
        errors.append("buyer_facing_response must be non-empty text")
    if response.get("side_effects_allowed") is not False:
        errors.append("side_effects_allowed must be false")
    if response.get("verifier_status") not in {"passed", "blocked"}:
        errors.append("verifier_status must be passed or blocked")
    if not isinstance(response.get("call_should_end"), bool):
        errors.append("call_should_end must be boolean")
    if not isinstance(response.get("project_memory_updates"), list):
        errors.append("project_memory_updates must be a list")
    if not isinstance(response.get("prosody_hints"), dict):
        errors.append("prosody_hints must be an object")

    buyer_text = str(response.get("buyer_facing_response") or "")
    lowered = buyer_text.lower()
    if _word_count(buyer_text) > 34:
        errors.append("buyer_facing_response is too long for the sandbox")
    for token in INTERNAL_LANGUAGE:
        if token in lowered:
            errors.append(f"buyer_facing_response contains internal language: {token}")
    if re.search(r"\[[^\]\n]{2,80}\]", buyer_text):
        errors.append("buyer_facing_response contains raw bracket tags")
    for pattern in FAKE_SIDE_EFFECT_PATTERNS:
        if re.search(pattern, lowered):
            errors.append("buyer_facing_response claims a side effect")
    if re.search(r"\$[0-9]|[0-9]+\s*(usd|eur|dollars|euros)", lowered):
        errors.append("buyer_facing_response contains unsupported pricing")
    if "guarantee" in lowered or "guaranteed" in lowered:
        errors.append("buyer_facing_response contains unsupported guarantee")
    if "http://" in lowered or "https://" in lowered:
        errors.append("buyer_facing_response contains raw URL")
    return errors
