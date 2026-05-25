from __future__ import annotations

from typing import Any


CAMPAIGN_ID = "public-openai-chatgpt-plans"


def applies(campaign: dict | None) -> bool:
    return isinstance(campaign, dict) and str(campaign.get("campaign_id") or "") == CAMPAIGN_ID


def _contains(normalized: str, phrases: set[str]) -> bool:
    return any(phrase in normalized for phrase in phrases)


def _prior_customer_text(turns: list[dict[str, Any]]) -> str:
    texts: list[str] = []
    for turn in turns[-8:]:
        texts.append(str(turn.get("transcript") or ""))
        summary = turn.get("summary") if isinstance(turn.get("summary"), dict) else {}
        texts.append(str(summary.get("transcript") or summary.get("buyer_transcript") or ""))
        continuity = turn.get("continuity") if isinstance(turn.get("continuity"), dict) else {}
        semantics = continuity.get("contextual_buyer_semantics") if isinstance(continuity.get("contextual_buyer_semantics"), dict) else {}
        evidence = semantics.get("evidence") if isinstance(semantics.get("evidence"), dict) else {}
        texts.append(str(evidence.get("buyer_utterance") or evidence.get("normalized_buyer_utterance") or ""))
    return " ".join(text.lower() for text in texts if text)


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
        "tell me",
        "yeah tell me",
        "sounds fine",
        "i have a minute",
    }


def _adoption_state_discovery_response() -> str:
    return (
        "Just so I don't assume - are you using ChatGPT today, using another AI tool, "
        "or mostly not using AI yet?"
    )


def _adoption_state_followup_response() -> str:
    return (
        "I can keep it high level. If you already use ChatGPT, the next useful question is what you use it for. "
        "If you use another AI tool or no AI yet, we can start with whether ChatGPT is relevant at all. "
        "Only after that would Plus, Pro, Business, or Enterprise matter. Which is closest?"
    )


def _assumption_challenge(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "why did you assume",
            "why are you assuming",
            "you assumed",
            "you assume",
            "i never said i was comparing",
            "i did not say i was comparing",
            "i didn't say i was comparing",
            "just said yes",
            "asking about plans already",
            "do not assume i want to buy",
            "don't assume i want to buy",
            "comparing plants",
        },
    )


def _low_or_unclear_intent(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "not comparing anything",
            "just curious",
            "just doing the work myself",
            "not buying anything yet",
            "not buying",
            "do not want to buy",
            "don't want to buy",
            "not deciding today",
            "only wanted to know what this is",
        },
    )


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
            "what plans are available",
            "which plans are available",
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
        "tell me",
        "yeah tell me",
        "go on",
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
    return _contains(
        normalized,
        {
            "coding and writing",
            "coding",
            "code",
            "writing",
            "files",
            "research",
            "work documents",
            "personal coding",
        },
    ) or (
        ("coding" in prior or "code" in prior) and "writing" in prior
    )


def _known_heavy_use(normalized: str, turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    return _contains(
        f"{prior} {normalized}",
        {
            "heavily every day",
            "very heavily",
            "heavy daily",
            "heavily for coding every day",
            "advanced tools all week",
            "every day",
        },
    )


def _team_context(normalized: str, turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    return _contains(
        f"{prior} {normalized}",
        {
            "we have a team",
            "small team",
            "team admin",
            "team workspace",
            "workspace controls",
            "business sounds right",
            "business",
            "enterprise controls",
            "sso",
            "scim",
        },
    )


def _light_or_basic_use(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "once in a while",
            "only need basic",
            "basic use",
            "studying",
            "study",
            "school",
            "personal tasks",
            "free is enough",
            "only use it sometimes",
        },
    )


def _current_chatgpt_user(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "already use chatgpt",
            "use chatgpt today",
            "using chatgpt today",
            "current chatgpt user",
            "i use chatgpt",
            "i'm using chatgpt",
            "i m using chatgpt",
        },
    )


def _another_ai_user(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "another llm",
            "different ai tool",
            "another ai tool",
            "use claude",
            "use gemini",
            "use copilot",
            "current tool",
        },
    )


def _no_ai_user(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "don't use ai tools",
            "don t use ai tools",
            "do not use ai tools",
            "not using ai yet",
            "no ai tools",
            "not using one yet",
            "new to ai",
        },
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


def _continue_request(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "keep checking it",
            "keep checking",
            "tell me",
            "yeah tell me",
            "go on",
            "continue",
            "what next",
        },
    )


def _trust_or_affiliation(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "where are you getting",
            "getting this information",
            "where did you get this information",
            "source for this",
            "what is your source",
            "are you calling from openai",
            "are you calling from open ai",
            "are you authorized by openai",
            "are you authorised by openai",
            "are you authorised by opening eyes",
            "are you from openai",
            "are you from open ai",
            "say you are from openai",
            "who are you with",
            "is this official",
            "do you work for openai",
            "are you actually openai",
            "is openai behind this",
            "why should i trust this",
        },
    )


def _context_progress_response(normalized: str, turns: list[dict[str, Any]]) -> tuple[str, str, str]:
    prior = _prior_customer_text(turns)
    combined = f"{prior} {normalized}"
    if _team_context(normalized, turns):
        return (
            "public_plan_team_context_progress",
            (
                "Right - team use. Business is the self-serve workspace route; Enterprise is for organization-level controls. "
                "Are you looking for basic team workspace controls, or Enterprise requirements like SSO, SCIM, procurement, or security review?"
            ),
            "team_plan_fit",
        )
    if _known_use_case(normalized, turns) and _known_heavy_use(normalized, turns):
        return (
            "public_plan_known_use_and_heavy_progress",
            (
                "Right - coding and writing with heavy daily use. Plus is the first paid plan to compare, and Pro is the heavier individual tier. "
                "Do you want the Plus-versus-Pro tradeoff, or should I stop there?"
            ),
            "plan_fit",
        )
    if _known_use_case(normalized, turns):
        return (
            "public_plan_known_use_case_progress",
            (
                "Right - coding and writing. Plus is usually the first paid plan to compare; Pro is for heavier use. "
                "Are you using it occasionally or heavily every day?"
            ),
            "usage_intensity",
        )
    if _known_heavy_use(normalized, turns):
        return (
            "public_plan_heavy_use_needs_context",
            (
                "Heavy daily use can make Plus or Pro relevant, but I should first check the actual work. "
                "What would you mainly use ChatGPT for - coding, writing, study, files, or a team?"
            ),
            "use_case_discovery",
        )
    if "myself" in combined or "personal use" in combined or "just me" in combined:
        return (
            "public_plan_personal_context_needs_use_case",
            (
                "For personal use, I would not jump to a paid plan yet. "
                "What would you mainly use ChatGPT for - coding, writing, study, files, or personal tasks?"
            ),
            "use_case_discovery",
        )
    return (
        "public_plan_adoption_state_discovery",
        _adoption_state_followup_response(),
        "adoption_state_discovery",
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
            "free sounds enough",
            "business sounds right",
            "how do we sign up",
        },
    )


def _plan_fit_established(turns: list[dict[str, Any]]) -> bool:
    prior_customer = _prior_customer_text(turns)
    if _known_use_case("", turns) or _team_context("", turns) or _light_or_basic_use(prior_customer):
        return True
    prior_responses = " ".join(
        str((turn.get("summary") or {}).get("final_response") or "").lower() for turn in turns[-4:]
    )
    return _contains(
        prior_responses,
        {
            "plus is usually",
            "free may be enough",
            "business is the self-serve",
            "enterprise is for",
            "pro is for heavier",
        },
    )


def _followup_route_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "who follows up after this",
            "who contacts me after this",
            "who contact me after this",
            "who will contact me",
            "who follows up",
            "who handles the follow up",
            "who handles follow up",
            "who owns the follow up",
            "who owns follow up",
            "who would contact me",
            "who will follow up",
            "what happens after i say yes",
            "what happens if i say yes",
            "what happens after yes",
            "what happens next if i say yes",
        },
    )


def _demo_operator_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "who is the demo operator",
            "who runs this demo",
            "who is running this demo",
            "who operates this demo",
            "who is behind this demo",
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
                "I'm not calling from OpenAI. This is a public-data simulation using OpenAI's public pricing and help pages. "
                "I can summarize official public OpenAI sources, but those pages are the authority. What are you trying to decide about ChatGPT?"
            ),
            dialogue_focus="trust",
            polarity="boundary",
        )

    if _demo_operator_question(normalized):
        return _frame(
            **base,
            semantic="public_plan_demo_operator_boundary",
            response=(
                "This is an internal public-data simulation. I can explain the public plan information, "
                "but I'm not representing OpenAI and not booking follow-up."
            ),
            dialogue_focus="operator_boundary",
            polarity="boundary",
        )

    if _followup_route_question(normalized):
        if _contains(normalized, {"what happens after i say yes", "what happens if i say yes", "what happens after yes", "what happens next if i say yes"}):
            response = (
                "After interest, individual plans stay self-serve: use the official ChatGPT plans page or profile upgrade flow. "
                "For Enterprise, the official next step is contact sales. I cannot send email, book a meeting, or create a CRM record here."
            )
        elif _contains(normalized, {"who contacts me", "who contact me", "who will contact me", "who would contact me"}):
            response = (
                "No one contacts you from this demo. For individual plans, the next step is self-serve through the official ChatGPT plans page. "
                "For Enterprise, the official next step is contact sales; I still cannot email, book, or create a CRM record."
            )
        else:
            response = (
                "For individual plans, there is no follow-up needed from this demo; I can point you to the official ChatGPT plans page. "
                "For Enterprise, the official next step is contact sales."
            )
        return _frame(
            **base,
            semantic="public_plan_followup_route_boundary",
            response=response,
            dialogue_focus="next_step_route",
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

    if _contains(normalized, {"read me the raw url", "raw url", "read the url"}):
        return _frame(
            **base,
            semantic="public_plan_raw_url_boundary",
            response="I should not read a raw URL aloud. The voice-safe next step is the official ChatGPT plans page.",
            dialogue_focus="side_effect_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"create a crm record", "crm record", "write crm"}):
        return _frame(
            **base,
            semantic="public_plan_crm_side_effect_boundary",
            response="I cannot create a CRM record from this fixture. I can only explain the public ChatGPT plan information.",
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

    if _contains(normalized, {"route signal", "routesignal", "insurance coverage", "telecom", "home service"}):
        return _frame(
            **base,
            semantic="public_plan_cross_campaign_boundary",
            response="That is outside this ChatGPT plan-fit simulation. I can only discuss ChatGPT plan information from official public OpenAI sources.",
            dialogue_focus="scope_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"hardship", "cannot afford", "worried about money"}):
        return _frame(
            **base,
            semantic="public_plan_hardship_no_fit",
            response="No pressure. If budget is the issue or basic use is enough, Free may be enough; I would not push a paid plan.",
            dialogue_focus="low_intent",
            polarity="low_pressure",
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

    if _contains(normalized, {"building an app", "developer app", "is this api", "platform api"}):
        return _frame(
            **base,
            semantic="public_plan_api_boundary",
            response="API usage is separate from ChatGPT subscriptions where the official sources state that boundary. Are you asking about the ChatGPT app, API usage, or both?",
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

    if _contains(normalized, {"legally compliant", "company legally compliant", "legal compliant"}):
        return _frame(
            **base,
            semantic="public_plan_legal_claim_boundary",
            response="I cannot give a legal compliance answer. For legal, security, or procurement review, use official OpenAI terms or the official contact-sales route.",
            dialogue_focus="claim_boundary",
            polarity="boundary",
        )

    if _contains(normalized, {"human_followup_owner", "human followup owner", "appointment target", "legacy compatibility field", "primary close"}):
        return _frame(
            **base,
            semantic="public_plan_internal_field_boundary",
            response="Those are internal fixture fields, not buyer-facing OpenAI plan guidance. I can discuss ChatGPT plan fit, official public sources, or stop here.",
            dialogue_focus="internal_field_boundary",
            polarity="boundary",
        )

    if previous_question_type == "permission_check" and _permission_ack(normalized):
        return _frame(
            **base,
            semantic="public_plan_adoption_state_discovery",
            response=_adoption_state_discovery_response(),
            target_gap="openai_adoption_state",
            dialogue_focus="adoption_state_discovery",
            polarity="progress",
        )

    if _assumption_challenge(normalized):
        return _frame(
            **base,
            semantic="public_plan_assumption_repair",
            response=(
                "Fair point - I shouldn't assume you're comparing plans. "
                "Are you using ChatGPT today, using another AI tool, or mostly not using AI yet?"
            ),
            target_gap="openai_adoption_state",
            dialogue_focus="assumption_repair",
            polarity="repair",
        )

    if _low_or_unclear_intent(normalized):
        return _frame(
            **base,
            semantic="public_plan_low_unclear_intent",
            response=(
                "No problem. Then I would keep it simple: Free may be enough for light use; paid plans are mainly worth comparing "
                "if limits, tools, or team needs matter. I can explain Free versus paid only if that would be useful, or I can stop here."
            ),
            target_gap="openai_adoption_state",
            dialogue_focus="low_intent",
            polarity="low_pressure",
        )

    if _current_chatgpt_user(normalized):
        return _frame(
            **base,
            semantic="public_plan_current_chatgpt_user",
            response=(
                "Got it - since you already use ChatGPT, the next question is use case and intensity. "
                "Do you mostly use it for coding, writing, study, files, research, work, or something else?"
            ),
            target_gap="openai_use_case",
            dialogue_focus="use_case_discovery",
            polarity="progress",
        )

    if _another_ai_user(normalized):
        return _frame(
            **base,
            semantic="public_plan_another_ai_user",
            response=(
                "You may not need to switch. The useful comparison is what your current tool does not cover. "
                "What matters most: coding, files, research, writing, privacy controls, or team admin?"
            ),
            target_gap="alternative_tool_gap",
            dialogue_focus="competitive_objection",
            polarity="low_pressure",
        )

    if _no_ai_user(normalized):
        return _frame(
            **base,
            semantic="public_plan_no_ai_user",
            response=(
                "No pressure. If you are not using AI yet, I would not start with a paid plan. "
                "ChatGPT can help with writing, studying, planning, coding, research, and files; does any of that sound relevant?"
            ),
            target_gap="openai_use_case",
            dialogue_focus="education_relevance",
            polarity="low_pressure",
        )

    if _self_serve_close(normalized) and not _plan_fit_established(turns):
        return _frame(
            **base,
            semantic="public_plan_close_needs_fit",
            response=(
                "I can help with the next step, but I should not point you to a plan before fit is clear. "
                "Are you using ChatGPT today, using another AI tool, or mostly not using AI yet?"
            ),
            target_gap="openai_adoption_state",
            dialogue_focus="adoption_state_discovery",
            polarity="low_pressure",
        )

    if _self_serve_close(normalized):
        prior_response = " ".join(str((turn.get("summary") or {}).get("final_response") or "") for turn in turns[-3:])
        if "free" in normalized:
            response = (
                "If Free is enough, no paid close is needed. The official ChatGPT plans page is the reference if you later compare paid plans. "
                "I cannot send a link, book anything, or take payment here."
            )
        elif "business" in normalized or "team" in _prior_customer_text(turns):
            response = (
                "For Business, use the official ChatGPT plans page for the self-serve workspace route. "
                "For Enterprise requirements, use contact sales. I cannot send a link, book anything, or take payment here."
            )
        else:
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
        if _known_heavy_use(normalized, turns) and not _known_use_case(normalized, turns):
            semantic = "public_plan_heavy_use_still_needs_use_case"
            response = (
                "You told me heavy daily use. I still need the actual work before plan fit; once I know that, Plus or Pro may be the comparison. "
                "Is it coding, writing, study, files, research, or team work?"
            )
            focus = "use_case_discovery"
        else:
            semantic, response, focus = _context_progress_response(normalized, turns)
        return _frame(
            **base,
            semantic=f"{semantic}_already_answered",
            response=response,
            target_gap="openai_use_case",
            dialogue_focus=focus,
            polarity="progress",
        )

    if _continue_request(normalized):
        semantic, response, focus = _context_progress_response(normalized, turns)
        return _frame(
            **base,
            semantic=f"{semantic}_continue",
            response=response,
            target_gap="openai_use_case",
            dialogue_focus=focus,
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

    if _known_use_case(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_use_case_confirmed",
            response=(
                "That use case makes plan fit relevant. Plus is usually the first paid plan to compare; Pro is for heavier individual use. "
                "Are you using it occasionally or heavily every day?"
            ),
            target_gap="individual_use_case",
            dialogue_focus="usage_intensity",
            polarity="progress",
        )

    if _known_heavy_use(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_heavy_use_needs_relevance",
            response=(
                "Heavy daily use can make Plus or Pro relevant, but I should first check the actual work. "
                "What would you mainly use ChatGPT for - coding, writing, study, files, or a team?"
            ),
            target_gap="openai_use_case",
            dialogue_focus="use_case_discovery",
            polarity="progress",
        )

    if _team_context(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_team_context",
            response=(
                "For team use, Business is the self-serve workspace route and Enterprise is for organization-level controls. "
                "Are you looking for basic team workspace controls, or Enterprise requirements like SSO, SCIM, procurement, or security review?"
            ),
            target_gap="team_use_case",
            dialogue_focus="team_plan_fit",
            polarity="progress",
        )

    if _light_or_basic_use(normalized):
        return _frame(
            **base,
            semantic="public_plan_light_basic_use",
            response=(
                "If your use is light or basic, Free may be enough. I would only compare paid plans if limits, tools, or team needs matter. "
                "What would you mainly use ChatGPT for?"
            ),
            target_gap="openai_use_case",
            dialogue_focus="no_fit_or_light_use",
            polarity="low_pressure",
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
                "This is a public-data ChatGPT plan-fit simulation. I should first learn the adoption state before comparing plans. "
                "Are you using ChatGPT today, using another AI tool, or mostly not using AI yet?"
            ),
            target_gap="openai_adoption_state",
            dialogue_focus="adoption_state_discovery",
            polarity="clarification",
        )

    if _self_use(normalized):
        return _frame(
            **base,
            semantic="public_plan_individual_use_case",
            response=(
                "If it is just for yourself, I would not jump to a paid plan yet. "
                "What would you mainly use ChatGPT for - coding, writing, study, files, or personal tasks?"
            ),
            target_gap="individual_use_case",
            dialogue_focus="use_case_discovery",
            polarity="progress",
        )

    return None
