from __future__ import annotations

from typing import Any


CAMPAIGN_ID = "public-openai-chatgpt-plans"


def applies(campaign: dict | None) -> bool:
    return isinstance(campaign, dict) and str(campaign.get("campaign_id") or "") == CAMPAIGN_ID


def _contains(normalized: str, phrases: set[str]) -> bool:
    return any(phrase in normalized for phrase in phrases)


def _prior_customer_text(turns: list[dict[str, Any]]) -> str:
    return " ".join(str(turn.get("transcript") or "").lower() for turn in turns[-8:])


def _frame(
    *,
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
    candidate_gaps: list[str],
    response: str,
    action_id: str = "continue_with_session_policy",
    dialogue_focus: str = "qualification",
    target_gap: str | None = None,
    polarity: str = "neutral",
    confidence: float = 0.94,
) -> dict[str, Any]:
    return {
        "semantic": semantic,
        "transcript": transcript,
        "normalized": normalized,
        "previous_question_type": previous_question_type,
        "previous_question_text": previous_question_text,
        "conversation_stage": conversation_stage,
        "active_gap": active_gap,
        "confirmed_gaps": confirmed_gaps,
        "cleared_gaps": cleared_gaps,
        "pending_callback": pending_callback,
        "pending_appointment": pending_appointment,
        "candidate_gaps": candidate_gaps,
        "target_gap": target_gap,
        "polarity": polarity,
        "confidence": confidence,
        "next_action_hint": "use_campaign_specific_public_plan_response",
        "must_not_do": [
            "claim affiliation",
            "leak internal fields",
            "claim side effects",
            "read raw URL aloud",
        ],
        "candidate_response": response,
        "action_id": action_id,
        "dialogue_focus": dialogue_focus,
        "campaign_response_priority": True,
        "applied": True,
    }


def _permission_ack(normalized: str) -> bool:
    return normalized in {
        "yes",
        "yes i do",
        "yes sure",
        "yeah",
        "yeah i do",
        "yeah sure",
        "okay",
        "ok",
        "go ahead",
        "sure",
        "sure quick",
        "sounds fine",
        "i have a minute",
    }


def _plain_plan_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "what do you mean by plans",
            "what are plans",
            "what does plans mean",
            "what do you mean by plan categories",
            "i don t know what plans means",
            "i don't know what plans means",
            "which plans are you talking about",
            "explain the plans",
            "say the plans plainly",
            "what is a chatgpt plan",
            "plans",
            "can you explain plans first",
        },
    )


def _explain_request(normalized: str) -> bool:
    return normalized in {
        "explain",
        "explain plainly",
        "say that simply",
        "what is this about",
        "plain english please",
        "can you explain",
        "make it simple",
        "summarize",
    }


def _self_use(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "just me",
            "personal use",
            "work alone",
            "using it myself",
            "not for a team",
            "just my own writing",
            "solo coding",
            "personal research",
            "not comparing anything",
            "do the work myself",
            "myself",
        },
    )


def _competitor_objection(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "another llm",
            "why would i switch",
            "why switch",
            "use claude",
            "use gemini",
            "another ai tool",
            "current model",
            "different llm",
            "current assistant",
            "use copilot",
            "reason to switch",
            "instead of what i have",
        },
    )


def _known_use_case(normalized: str, turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    return _contains(normalized, {"coding and writing", "coding", "writing"}) or (
        "coding" in prior and "writing" in prior
    )


def _already_told(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "already told you",
            "i told you",
            "i said",
            "already said",
            "you asked that already",
            "like i said",
        },
    )


def _trust_or_affiliation(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "are you calling from openai",
            "are you authorized by openai",
            "who are you with",
            "is this official",
            "do you work for openai",
            "are you actually openai",
            "is openai behind this",
            "why should i trust this",
        },
    )


def _self_serve_close(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "i want plus",
            "plus sounds right",
            "how do i sign up",
            "where do i upgrade",
            "show me the official page",
            "i want pro",
            "i want go",
            "where is the plan page",
            "ready to start",
            "what is the next step",
            "sounds good how do i sign up",
        },
    )


def classify_turn(
    *,
    campaign: dict | None,
    transcript: str,
    normalized: str,
    turns: list[dict[str, Any]],
    previous_question: str | None,
    previous_question_type: str,
    conversation_stage: str,
    active_gap: str | None,
    confirmed_gaps: list[str],
    cleared_gaps: list[str],
    pending_callback: bool,
    pending_appointment: bool,
    candidate_gaps: list[str],
) -> dict[str, Any] | None:
    if not applies(campaign):
        return None

    base = {
        "transcript": transcript,
        "normalized": normalized,
        "previous_question_type": previous_question_type,
        "previous_question_text": previous_question,
        "conversation_stage": conversation_stage,
        "active_gap": active_gap,
        "confirmed_gaps": confirmed_gaps,
        "cleared_gaps": cleared_gaps,
        "pending_callback": pending_callback,
        "pending_appointment": pending_appointment,
        "candidate_gaps": candidate_gaps,
    }

    if _trust_or_affiliation(normalized):
        return _frame(
            **base,
            semantic="public_plan_affiliation_boundary",
            response=(
                "No. This is a public-data simulation, not an official OpenAI call. "
                "I can only use official public OpenAI plan information here. Do you want the high-level plan comparison, or should I stop?"
            ),
            dialogue_focus="trust",
            polarity="boundary",
        )

    if _contains(normalized, {"i m driving", "i am driving", "driving"}):
        return _frame(
            **base,
            semantic="public_plan_bad_timing_driving",
            response="Please focus on driving. I will stop here.",
            action_id="end_call_stop_request",
            dialogue_focus="safety",
            polarity="stop",
            confidence=0.98,
        )

    if _contains(normalized, {"send me the link by email", "email me", "send it to my email"}):
        return _frame(
            **base,
            semantic="public_plan_email_side_effect_boundary",
            response="I cannot send email from this fixture. I can only point you to the official ChatGPT plans page.",
            dialogue_focus="side_effect_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"book a meeting", "book sales", "calendar"}):
        return _frame(
            **base,
            semantic="public_plan_calendar_side_effect_boundary",
            response="I cannot book meetings or create calendar events here. For Enterprise, use the official contact-sales route.",
            dialogue_focus="side_effect_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"take my payment", "charge my card", "payment"}):
        return _frame(
            **base,
            semantic="public_plan_payment_boundary",
            response="I cannot take payment here. For self-serve plans, use the official ChatGPT plans page or the profile upgrade flow.",
            dialogue_focus="side_effect_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"discount", "coupon", "special deal"}):
        return _frame(
            **base,
            semantic="public_plan_discount_boundary",
            response="I cannot invent discounts. The safe reference is the official ChatGPT plans page; if Free covers your use, Free may be enough.",
            dialogue_focus="claim_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"guarantee gpt 5 5 pro", "guarantee", "gpt 5 5"}):
        return _frame(
            **base,
            semantic="public_plan_future_model_boundary",
            response="I cannot guarantee a future model, exact availability, or unrestricted usage. Official limits vary by plan and model and can change.",
            dialogue_focus="claim_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"api included", "is api included", "api usage", "tokens"}):
        return _frame(
            **base,
            semantic="public_plan_api_boundary",
            response="API usage is separate from ChatGPT subscriptions where the official sources state that boundary. Are you asking about ChatGPT itself, the API, or both?",
            dialogue_focus="api_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"exact enterprise pricing", "enterprise pricing", "enterprise price"}):
        return _frame(
            **base,
            semantic="public_plan_enterprise_price_boundary",
            response="I cannot quote exact Enterprise pricing here. The official path for Enterprise pricing is contact sales.",
            dialogue_focus="claim_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"promise my data is never used", "never used", "privacy guarantee"}):
        return _frame(
            **base,
            semantic="public_plan_privacy_claim_boundary",
            response="I cannot promise that in every circumstance. Privacy and training settings should be checked in the official OpenAI terms and plan information.",
            dialogue_focus="claim_boundary",
            polarity="boundary",
        )

    if _self_serve_close(normalized):
        prior_response = " ".join(str((turn.get("summary") or {}).get("final_response") or "") for turn in turns[-3:])
        response = (
            "Same next step: use the official ChatGPT plans page or the profile upgrade flow. "
            "I still cannot send a link, book anything, or take payment here."
            if "official ChatGPT plans page" in prior_response
            else (
                "For Plus, use the official ChatGPT plans page or the profile upgrade flow. "
                "I cannot send a link, book anything, or take payment here."
            )
        )
        return _frame(
            **base,
            semantic="public_plan_self_serve_close",
            response=response,
            dialogue_focus="self_serve_close",
            polarity="close",
        )

    if _competitor_objection(normalized):
        return _frame(
            **base,
            semantic="public_plan_competitor_objection",
            response=(
                "You may not need to switch. The question is whether ChatGPT's plan features, tools, or business controls fit something your current tool does not cover. "
                "What matters most: coding, files, research, voice/images, team admin, or privacy controls?"
            ),
            dialogue_focus="competitive_objection",
            polarity="objection",
        )

    if _already_told(normalized):
        known = "coding and writing" if _known_use_case(normalized, turns) else "your use case"
        response = (
            "Right - coding and writing. For that, Plus is usually the first paid plan to compare; Pro is for heavier use. "
            "Are you using it occasionally or heavily every day?"
            if known == "coding and writing"
            else "Right - you already gave me the use case. Are you using it lightly, or heavily every day?"
        )
        return _frame(
            **base,
            semantic="public_plan_already_answered",
            response=response,
            target_gap="individual_use_case",
            dialogue_focus="usage_intensity",
            polarity="progress",
        )

    if _known_use_case(normalized, turns) and _contains(normalized, {"coding", "writing"}):
        return _frame(
            **base,
            semantic="public_plan_use_case_confirmed",
            response=(
                "Right - coding and writing. Plus is usually the first paid plan to compare; Pro is for heavier use. "
                "Are you using it occasionally or heavily every day?"
            ),
            target_gap="individual_use_case",
            dialogue_focus="usage_intensity",
            polarity="progress",
        )

    if _plain_plan_question(normalized):
        return _frame(
            **base,
            semantic="public_plan_categories_explained",
            response="By plans, I mean Free, Go, Plus, Pro, Business, and Enterprise. Are you looking for personal use, team use, or enterprise controls?",
            dialogue_focus="plan_categories",
            polarity="clarification",
        )

    if _explain_request(normalized):
        return _frame(
            **base,
            semantic="public_plan_plain_explanation",
            response=(
                "By plans, I mean Free, Go, Plus, Pro, Business, and Enterprise. "
                "Free is for basic use, Plus is the first paid plan to compare, Pro is for heavier individual use, Business is for team workspaces, and Enterprise is for organization controls. "
                "Are you looking for personal use, team use, or enterprise controls?"
            ),
            dialogue_focus="plan_categories",
            polarity="clarification",
        )

    if _self_use(normalized):
        return _frame(
            **base,
            semantic="public_plan_individual_use_case",
            response=(
                "If it is just for yourself and basic use is enough, Free may be enough. "
                "If limits or tools get in the way, Plus or Pro are the comparison points. Are you using it lightly, or heavily every day?"
            ),
            target_gap="individual_use_case",
            dialogue_focus="usage_intensity",
            polarity="progress",
        )

    if previous_question_type == "permission_check" and _permission_ack(normalized):
        return _frame(
            **base,
            semantic="public_plan_permission_acknowledgement",
            response="Are you comparing plans for yourself, a small team, or a larger organization?",
            dialogue_focus="plan_fit",
            polarity="progress",
        )

    return None
