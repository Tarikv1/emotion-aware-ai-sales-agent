from __future__ import annotations

import re
from typing import Any


CAMPAIGN_ID = "public-openai-chatgpt-plans"
OPENAI_STATE_KEY = "openai_chatgpt_plan_state"
CHATGPT_ASR_ALIASES = {
    "chachu pt",
    "chachu bt",
    "chachu p t",
    "chachu b t",
    "chachupt",
    "chat jpt",
    "chat gpt",
    "chat g p t",
    "chat gbt",
    "chat gb t",
    "chatgbt",
    "chat gpt plan",
    "chat jpt plan",
}


def applies(campaign: dict | None) -> bool:
    return isinstance(campaign, dict) and str(campaign.get("campaign_id") or "") == CAMPAIGN_ID


def _contains(normalized: str, phrases: set[str]) -> bool:
    return any(phrase in normalized for phrase in phrases)


def _normalize_openai_asr_aliases(normalized: str) -> str:
    semantic = f" {normalized} "
    for alias in sorted(CHATGPT_ASR_ALIASES, key=len, reverse=True):
        semantic = semantic.replace(f" {alias} ", " chatgpt ")
    return " ".join(semantic.split())


def _mentions_chatgpt_product(normalized: str) -> bool:
    return "chatgpt" in _normalize_openai_asr_aliases(normalized)


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
    return _normalize_openai_asr_aliases(" ".join(text.lower() for text in texts if text))


def _prior_openai_state(turns: list[dict[str, Any]], current_memory: dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(current_memory, dict):
        current = current_memory.get(OPENAI_STATE_KEY)
        if isinstance(current, dict):
            return dict(current)
    for turn in reversed(turns):
        memory = turn.get("conversation_memory") if isinstance(turn, dict) else {}
        if not isinstance(memory, dict):
            continue
        state = memory.get(OPENAI_STATE_KEY)
        if isinstance(state, dict):
            return dict(state)
    return {}


def _state_text_value(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")


def _state_has_use_case(state: dict[str, Any], value: str) -> bool:
    return value in _state_text_value(state, "openai_use_case").lower()


def _openai_use_case_tags(text: str) -> list[str]:
    normalized = _normalize_openai_asr_aliases(" ".join(str(text or "").lower().split()))
    tags: list[str] = []
    checks = [
        ("coding", {"coding", "code", "developer", "programming"}),
        ("writing", {"writing", "write", "drafting", "editing"}),
        ("research", {"research", "deep research"}),
        ("files", {"files", "file uploads", "documents", "work documents"}),
        ("study", {"study", "studying", "school"}),
        ("team", {"team", "workspace", "admin", "sso", "scim", "procurement"}),
        ("enterprise", {"enterprise", "security review", "legal", "compliance"}),
    ]
    for tag, phrases in checks:
        if _contains(normalized, phrases):
            tags.append(tag)
    return tags


def _usage_intensity_from_text(text: str) -> str:
    normalized = _normalize_openai_asr_aliases(" ".join(str(text or "").lower().split()))
    if _contains(
        normalized,
        {
            "heavily every day",
            "very heavily",
            "heavy daily",
            "a little bit on the heavy side",
            "heavy side",
            "a little heavy",
            "use heavily",
            "use it heavily",
            "heavy",
            "every day",
            "daily",
            "advanced tools all week",
            "hitting limits",
            "hit limits",
            "running out",
            "blocked by limits",
        },
    ):
        return "heavy"
    if _contains(normalized, {"middle", "medium", "moderate", "throughout the week", "regularly"}):
        return "medium"
    if _contains(normalized, {"occasionally", "light", "sometimes", "once in a while", "free is enough", "basic"}):
        return "light"
    return "unknown"


def _limit_pain_from_text(text: str) -> bool | None:
    normalized = _normalize_openai_asr_aliases(" ".join(str(text or "").lower().split()))
    if _contains(normalized, {"do not hit limits", "don't hit limits", "not hitting limits", "no limits problem"}):
        return False
    if _contains(
        normalized,
        {
            "mostly hitting limits",
            "hitting limits",
            "hit limits",
            "limits are frustrating",
            "limits frustrating",
            "running out of limits",
            "running out",
            "blocked by limits",
            "already hitting limits",
            "i run out of limits",
            "run out of limits",
            "limits are the problem",
            "hit the cap",
            "usage limits block",
            "need fewer limits",
            "want to avoid limits",
            "a bit frustrating",
            "frustrating",
        },
    ):
        return True
    return None


def _budget_sensitivity_from_text(text: str) -> str:
    normalized = " ".join(str(text or "").lower().split())
    if _contains(normalized, {"cannot afford", "too expensive", "worried about money", "budget is tight", "avoid paying"}):
        return "high"
    if _contains(normalized, {"price", "cost", "cheaper", "lower-cost", "twenty dollars", "20 dollars"}):
        return "medium"
    if _contains(normalized, {"budget is not a concern", "price is not a concern"}):
        return "low"
    return "unknown"


def _choosing_before_upgrade(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "just trying to choose before upgrading",
            "just choosing before upgrading",
            "trying to choose before upgrading",
            "before upgrading",
        },
    )


def _recommended_path_for_state(state: dict[str, Any]) -> str:
    use_text = _state_text_value(state, "openai_use_case").lower()
    intensity = str(state.get("openai_usage_intensity") or "unknown")
    limit_pain = state.get("openai_limit_pain")
    budget = str(state.get("openai_budget_sensitivity") or "unknown")
    if "enterprise" in use_text:
        return "enterprise"
    if "team" in use_text:
        return "business"
    if limit_pain is True or intensity == "heavy":
        return "pro"
    if intensity == "light" or budget == "high":
        return "free"
    if use_text and use_text != "unknown":
        return "plus"
    return "unknown"


def _prior_active_decision_frame(turns: list[dict[str, Any]]) -> str:
    state = _prior_openai_state(turns)
    return str(state.get("active_decision_frame") or state.get("last_decision_frame_given") or "")


def _prior_buyer_decision_stage(turns: list[dict[str, Any]]) -> str:
    state = _prior_openai_state(turns)
    return str(state.get("buyer_decision_stage") or "")


def _prior_pro_tier_context(turns: list[dict[str, Any]]) -> bool:
    prior_text = _prior_customer_text(turns)
    state = _prior_openai_state(turns)
    return (
        state.get("active_decision_frame") == "pro_100_vs_200"
        or state.get("buyer_decision_stage") == "pro_tier_selection"
        or _contains(prior_text, {"which pro", "pro tier", "100 dollar pro", "200 dollar pro", "version of pro"})
    )


def _next_best_action_for_state(state: dict[str, Any], normalized: str, final_response: str) -> str:
    if state.get("active_decision_frame") == "pro_100_vs_200" or _pro_tier_question(normalized):
        return "answer_pro_tier" if not _signup_question(normalized) else "self_serve_close"
    if _price_question(normalized):
        return "recommend_plan" if state.get("openai_price_answered") else "answer_price"
    if _contains(normalized, {"api included", "is api included", "api usage", "tokens", "developer app", "platform api"}):
        return "answer_api_boundary"
    if _signup_question(normalized):
        if _recommended_path_for_state(state) == "enterprise":
            return "contact_sales_close"
        return "self_serve_close"
    if not _state_text_value(state, "openai_adoption_state") or state.get("openai_adoption_state") == "unknown":
        return "ask_adoption_state"
    if not _state_text_value(state, "openai_use_case") or state.get("openai_use_case") == "unknown":
        return "ask_use_case"
    if state.get("openai_usage_intensity") in {None, "unknown"}:
        return "ask_usage_intensity"
    if _contains(final_response.lower(), {"official chatgpt plans page", "profile upgrade flow"}):
        return "self_serve_close"
    return "recommend_plan"


def _commercial_sales_state(
    *,
    state: dict[str, Any],
    normalized: str,
    final_response: str,
) -> dict[str, Any]:
    recommended = _recommended_path_for_state(state)
    use_text = _state_text_value(state, "openai_use_case").lower()
    intensity = str(state.get("openai_usage_intensity") or "unknown")
    limit_pain = state.get("openai_limit_pain")
    budget = str(state.get("openai_budget_sensitivity") or "unknown")
    response = " ".join(str(final_response or "").lower().split())
    active_frame = str(state.get("active_decision_frame") or "")
    prior_stage = str(state.get("buyer_decision_stage") or "")
    objection = _commercial_objection(normalized)

    if _signup_question(normalized):
        current_question_type = "signup"
    elif active_frame == "pro_100_vs_200" or _pro_tier_question(normalized):
        current_question_type = "which_pro_tier"
    elif _plus_sufficiency_question(normalized):
        current_question_type = "plus_enough"
    elif objection in {"price", "subscription", "why_pro"}:
        current_question_type = "worth_it" if _contains(normalized, {"why", "expensive", "worth", "pay"}) else "price"
    elif _price_question(normalized):
        current_question_type = "price"
    elif _competitor_objection(normalized) or _another_ai_user(normalized):
        current_question_type = "competitor_switch"
    elif _current_tool_enough(normalized) or budget == "high":
        current_question_type = "no_fit"
    elif _pro_agreement_signal(normalized):
        current_question_type = "pro_better"
    else:
        current_question_type = str(state.get("current_buyer_question_type") or "")

    if _signup_question(normalized) or "official chatgpt plans page" in response or "profile upgrade flow" in response:
        commercial_stage = "close"
    elif active_frame == "pro_100_vs_200" or _pro_tier_question(normalized):
        commercial_stage = "decision_frame"
    elif _price_question(normalized) or _plus_sufficiency_question(normalized) or _pro_agreement_signal(normalized):
        commercial_stage = "decision_frame"
    elif objection or _competitor_objection(normalized):
        commercial_stage = "objection_handling"
    elif recommended != "unknown":
        commercial_stage = "recommendation"
    elif use_text and use_text != "unknown":
        commercial_stage = "value_mapping"
    elif state.get("openai_adoption_state") not in {None, "unknown"}:
        commercial_stage = "use_case_discovery"
    else:
        commercial_stage = "adoption_discovery"

    if budget == "high" or _current_tool_enough(normalized):
        buyer_fit_level = "low"
    elif recommended in {"pro", "business", "enterprise"}:
        buyer_fit_level = "high"
    elif recommended in {"plus", "free"}:
        buyer_fit_level = "medium"
    else:
        buyer_fit_level = "unknown"

    if _pro_agreement_signal(normalized) or _signup_question(normalized) or _self_serve_close(normalized):
        buyer_momentum = "buying_signal"
    elif objection or _competitor_objection(normalized):
        buyer_momentum = "neutral"
    elif recommended != "unknown":
        buyer_momentum = "positive"
    else:
        buyer_momentum = "neutral"

    if recommended in {"pro", "business", "enterprise"} or _pro_agreement_signal(normalized):
        recommendation_confidence = "strong"
    elif recommended in {"plus", "free"}:
        recommendation_confidence = "moderate"
    elif use_text and use_text != "unknown":
        recommendation_confidence = "tentative"
    else:
        recommendation_confidence = "none"

    if recommended == "enterprise" or "privacy" in use_text:
        value_hypothesis = "privacy_controls"
    elif recommended == "business" or "team" in use_text:
        value_hypothesis = "team_controls"
    elif limit_pain is True or intensity == "heavy":
        value_hypothesis = "fewer_limits"
    elif budget == "high" or recommended == "free":
        value_hypothesis = "no_fit"
    elif recommended in {"plus", "pro"}:
        value_hypothesis = "lower_cost_entry"
    else:
        value_hypothesis = "better_tools" if use_text and use_text != "unknown" else "no_fit"

    if active_frame == "pro_100_vs_200" or _pro_tier_question(normalized):
        decision_frame = "pro_100_vs_200"
    elif recommended in {"plus", "pro"} or _plus_sufficiency_question(normalized) or _pro_agreement_signal(normalized):
        decision_frame = "plus_vs_pro"
    elif recommended == "free" or budget == "high":
        decision_frame = "free_vs_paid"
    elif recommended in {"business", "enterprise"}:
        decision_frame = "business_vs_enterprise"
    elif _competitor_objection(normalized) or _current_tool_enough(normalized) or _another_ai_user(normalized):
        decision_frame = "current_tool_vs_chatgpt"
    else:
        decision_frame = "no_fit"

    if _signup_question(normalized):
        buyer_decision_stage = "self_serve_close"
    elif decision_frame == "pro_100_vs_200":
        buyer_decision_stage = "pro_tier_selection"
    elif objection:
        buyer_decision_stage = "objection_handling"
    elif _price_question(normalized):
        buyer_decision_stage = "price_evaluation"
    elif decision_frame == "plus_vs_pro":
        buyer_decision_stage = "plus_vs_pro"
    elif decision_frame == "current_tool_vs_chatgpt":
        buyer_decision_stage = "use_case"
    elif decision_frame == "free_vs_paid":
        buyer_decision_stage = "no_fit" if budget == "high" else "price_evaluation"
    elif use_text and use_text != "unknown":
        buyer_decision_stage = "use_case"
    elif state.get("openai_adoption_state") not in {None, "unknown"}:
        buyer_decision_stage = "adoption_state"
    else:
        buyer_decision_stage = prior_stage or "adoption_state"

    if _signup_question(normalized) and recommended == "enterprise":
        close_readiness = "contact_sales"
    elif _signup_question(normalized) or _pro_agreement_signal(normalized):
        close_readiness = "self_serve"
    elif recommended != "unknown":
        close_readiness = "direct"
    elif use_text and use_text != "unknown":
        close_readiness = "soft"
    else:
        close_readiness = "none"

    if objection:
        last_objection_handled = objection
    elif _competitor_objection(normalized) or _current_tool_enough(normalized):
        last_objection_handled = "competitor"
    else:
        last_objection_handled = state.get("last_objection_handled") or ""

    return {
        "commercial_stage": commercial_stage,
        "buyer_fit_level": buyer_fit_level,
        "buyer_momentum": buyer_momentum,
        "recommendation_confidence": recommendation_confidence,
        "value_hypothesis": value_hypothesis,
        "decision_frame": decision_frame,
        "close_readiness": close_readiness,
        "last_recommendation_given": recommended if recommended != "unknown" else state.get("last_recommendation_given") or "",
        "last_decision_frame_given": decision_frame,
        "last_objection_handled": last_objection_handled,
        "next_commercial_action": _next_best_action_for_state(state, normalized, response),
        "buyer_decision_stage": buyer_decision_stage,
        "active_decision_frame": decision_frame,
        "last_decision_question_answered": current_question_type or state.get("last_decision_question_answered") or "",
        "current_buyer_question_type": current_question_type,
        "should_not_regress_to_prior_decision_stage": bool(
            decision_frame == "pro_100_vs_200"
            or active_frame == "pro_100_vs_200"
            or buyer_decision_stage in {"pro_tier_selection", "self_serve_close"}
        ),
    }


def memory_update_for_turn(
    *,
    transcript: str,
    turns: list[dict[str, Any]],
    final_response: str,
    campaign: dict | None,
    current_memory: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not applies(campaign):
        return None
    normalized = _normalize_openai_asr_aliases(" ".join(str(transcript or "").lower().split()))
    response = " ".join(str(final_response or "").lower().split())
    prior = _prior_openai_state(turns, current_memory)
    state: dict[str, Any] = {
        "openai_adoption_state": prior.get("openai_adoption_state") or "unknown",
        "openai_use_case": prior.get("openai_use_case") or [],
        "openai_usage_intensity": prior.get("openai_usage_intensity") or "unknown",
        "openai_limit_pain": prior.get("openai_limit_pain", "unknown"),
        "openai_budget_sensitivity": prior.get("openai_budget_sensitivity") or "unknown",
        "openai_price_answered": bool(prior.get("openai_price_answered")),
        "openai_api_boundary_answered": bool(prior.get("openai_api_boundary_answered")),
        "openai_recommended_path": prior.get("openai_recommended_path") or "unknown",
        "openai_next_best_action": prior.get("openai_next_best_action") or "unknown",
        "buyer_decision_stage": prior.get("buyer_decision_stage") or "adoption_state",
        "active_decision_frame": prior.get("active_decision_frame") or "",
        "last_decision_question_answered": prior.get("last_decision_question_answered") or "",
        "current_buyer_question_type": prior.get("current_buyer_question_type") or "",
        "should_not_regress_to_prior_decision_stage": bool(prior.get("should_not_regress_to_prior_decision_stage")),
    }

    if _current_chatgpt_user(normalized) or _openai_use_case_tags(normalized):
        state["openai_adoption_state"] = "current_chatgpt_user"
    elif _another_ai_user(normalized):
        state["openai_adoption_state"] = "other_ai_user"
    elif _no_ai_user(normalized):
        state["openai_adoption_state"] = "no_ai_user"

    prior_tags = state["openai_use_case"] if isinstance(state["openai_use_case"], list) else []
    tags = list(prior_tags)
    for tag in _openai_use_case_tags(normalized):
        if tag not in tags:
            tags.append(tag)
    state["openai_use_case"] = tags or "unknown"

    intensity = _usage_intensity_from_text(normalized)
    if intensity != "unknown":
        state["openai_usage_intensity"] = intensity

    limit_pain = _limit_pain_from_text(normalized)
    if limit_pain is not None:
        state["openai_limit_pain"] = limit_pain
        if limit_pain:
            state["openai_usage_intensity"] = "heavy"

    budget = _budget_sensitivity_from_text(normalized)
    if budget != "unknown":
        state["openai_budget_sensitivity"] = budget

    if _price_question(normalized) or re.search(r"\b(20|100|200)\b", response):
        state["openai_price_answered"] = bool(
            re.search(r"\b(20|100|200)\b|source of truth|free is the no-cost", response)
        ) or state["openai_price_answered"]
    if _contains(normalized, {"api included", "is api included", "api usage", "tokens", "developer app", "platform api"}) or "api usage is separate" in response:
        state["openai_api_boundary_answered"] = True

    if _signup_question(normalized):
        state["buyer_decision_stage"] = "self_serve_close"
        state["current_buyer_question_type"] = "signup"
        state["last_decision_question_answered"] = "signup"
        if state.get("active_decision_frame") == "pro_100_vs_200":
            state["should_not_regress_to_prior_decision_stage"] = True
    elif _pro_tier_question_for_context(normalized, turns) or (
        state.get("active_decision_frame") == "pro_100_vs_200" and not _contains(normalized, {"plus or pro", "plus enough"})
    ):
        state["buyer_decision_stage"] = "pro_tier_selection"
        state["active_decision_frame"] = "pro_100_vs_200"
        state["current_buyer_question_type"] = "which_pro_tier"
        state["last_decision_question_answered"] = "which_pro_tier"
        state["should_not_regress_to_prior_decision_stage"] = True

    recommended = _recommended_path_for_state(state)
    if recommended != "unknown":
        state["openai_recommended_path"] = recommended

    state["openai_next_best_action"] = _next_best_action_for_state(state, normalized, response)
    state["known_use_case"] = state["openai_use_case"]
    state["known_usage_intensity"] = state["openai_usage_intensity"]
    state["limit_pain"] = state["openai_limit_pain"]
    state["price_answered"] = state["openai_price_answered"]
    state["API_boundary_answered"] = state["openai_api_boundary_answered"]
    state["last_agent_question_type"] = "none"
    state["last_agent_question_text"] = final_response if "?" in final_response else ""
    state.update(_commercial_sales_state(state=state, normalized=normalized, final_response=final_response))
    return state


def _source_claim(campaign: dict | None, fact_id: str) -> dict[str, Any] | None:
    if not isinstance(campaign, dict):
        return None
    for item in campaign.get("source_grounded_claims") or []:
        if not isinstance(item, dict):
            continue
        if item.get("fact_id") == fact_id and item.get("allowed_in_speech") is True:
            return item
    return None


def _source_speech(campaign: dict | None, fact_id: str, fallback: str) -> str:
    claim = _source_claim(campaign, fact_id)
    if not claim:
        return fallback
    return str(claim.get("normalized_speech_version") or claim.get("claim") or fallback)


def _official_price_caveat() -> str:
    return "The official ChatGPT pricing page is the source of truth for exact current prices."


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
            "do not want to pay",
            "don't want to pay",
            "no paid plan",
            "no subscription",
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
            "why use chatgpt",
            "why compare chatgpt",
            "what gap would",
            "what would be different",
            "convince me",
            "use claude",
            "use gemini",
            "another ai tool",
            "current model",
            "different llm",
            "current assistant",
            "use copilot",
            "reason to switch",
            "reason to compare",
            "reason to compare chatgpt",
            "what is the reason to compare",
            "instead of what i have",
            "over what i have",
            "why would i add chatgpt",
            "why would i add this",
            "why add chatgpt",
            "why add this",
            "why not stay",
            "should i switch",
        },
    )


def _known_use_case(normalized: str, turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    state = _prior_openai_state(turns)
    if any(_state_has_use_case(state, tag) for tag in {"coding", "writing", "research", "files", "study"}):
        return True
    prior_has_use_case = _contains(
        prior,
        {
            "coding",
            "code",
            "writing",
            "coding/writing",
            "files",
            "research",
            "study",
            "work documents",
            "personal coding",
        },
    )
    return _contains(
        normalized,
        {
            "coding and writing",
            "coding/writing",
            "coding",
            "code",
            "writing",
            "files",
            "research",
            "work documents",
            "personal coding",
        },
    ) or prior_has_use_case


def _known_heavy_use(normalized: str, turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    state = _prior_openai_state(turns)
    if state.get("openai_usage_intensity") == "heavy" or state.get("openai_limit_pain") is True:
        return True
    return _contains(
        f"{prior} {normalized}",
        {
            "heavily every day",
            "very heavily",
            "heavy daily",
            "heavily for coding every day",
            "advanced tools all week",
            "every day",
            "heavy side",
            "a little bit on the heavy side",
            "a little heavy",
            "heavy",
            "use it heavily",
            "use heavily",
            "hit limits",
            "hitting limits",
            "mostly hitting limits",
            "limits are frustrating",
            "running out",
            "blocked by limits",
        },
    )


def _team_context(normalized: str, turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    state = _prior_openai_state(turns)
    if any(_state_has_use_case(state, tag) for tag in {"team", "enterprise"}):
        return True
    return _contains(
        f"{prior} {normalized}",
        {
            "we have a team",
            "team",
            "for a team",
            "this is for a team",
            "actually this is for a team",
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
            "occasionally",
            "light",
            "lightly",
            "light personal use",
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


def _known_limit_pain(normalized: str, turns: list[dict[str, Any]]) -> bool:
    state = _prior_openai_state(turns)
    return state.get("openai_limit_pain") is True or _limit_pain_from_text(normalized) is True


def _current_chatgpt_user(normalized: str) -> bool:
    normalized = _normalize_openai_asr_aliases(normalized)
    return _contains(
        normalized,
        {
            "already use chatgpt",
            "use chatgpt today",
            "using chatgpt today",
            "current chatgpt user",
            "i use chatgpt",
            "i used chatgpt",
            "used chatgpt",
            "i'm using chatgpt",
            "i m using chatgpt",
            "already use chatgpt",
            "chatgpt for coding",
            "chatgpt handles",
        },
    )


def _another_ai_user(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "another llm",
            "different ai tool",
            "another ai tool",
            "another ai tools",
            "other ai tools",
            "other ai tool",
            "other ai",
            "other tools",
            "ai tools already",
            "already use ai tools",
            "already using ai tools",
            "already have an ai tool",
            "use claude",
            "claude",
            "use gemini",
            "gemini",
            "use copilot",
            "copilot",
            "current tool",
            "current assistant",
            "other assistants",
            "another subscription",
            "already pay for another tool",
        },
    )


def _current_tool_enough(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "current tool works fine",
            "current tool is fine",
            "current setup is enough",
            "current setup works",
            "current tool covers everything",
            "my current tool covers everything",
            "happy with my current tool",
            "stay with what i have",
            "i can stay with what i have",
            "no paid plan",
            "no budget",
        },
    )


def _commercial_objection(normalized: str) -> str:
    if _contains(
        normalized,
        {
            "why pro over plus",
            "why pro",
            "why pay more than plus",
            "why would pro be safer",
            "plus is cheaper",
            "plus seems cheaper",
            "why not start lower",
            "is pro really necessary",
            "what if pro is too much",
            "why would pro be worth it",
            "why pay 100",
            "why pay 200",
            "why 100 or 200",
        },
    ):
        return "why_pro"
    if _contains(
        normalized,
        {
            "too expensive",
            "expensive",
            "price sensitive",
            "do not want to overpay",
            "don't want to overpay",
            "worth paying",
            "why would i pay",
            "why would i pay that much",
            "why pay that much",
            "why not just use free",
            "why pay",
            "is this worth paying",
            "paid is too much",
            "that is a lot monthly",
            "lot monthly",
            "overpay",
        },
    ):
        return "price"
    if _contains(
        normalized,
        {
            "another subscription",
            "do not want another subscription",
            "don't want another subscription",
            "subscription is annoying",
        },
    ):
        return "subscription"
    if _contains(normalized, {"already pay for another tool", "current tool is already paid"}):
        return "competitor"
    return ""


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


def _price_question(normalized: str) -> bool:
    if normalized in {"price", "cost", "costs", "money", "monthly price"}:
        return True
    return _contains(
        normalized,
        {
            "how much",
            "what are the prices",
            "what is the price",
            "what does plus cost",
            "what does pro cost",
            "what do i pay",
            "what do the paid tiers cost",
            "what are the paid tiers",
            "what does it cost monthly",
            "monthly",
            "monthly price",
            "paid plan price",
            "paid tiers",
            "tell me the cost",
            "tell me the pricing",
            "price please",
            "pricing",
            "current prices",
            "what should i budget",
            "how expensive",
            "difference in price",
            "what is the difference in price",
            "free versus paid",
            "free vs paid",
            "price before",
            "want to know the price",
            "want the price",
            "would like to know the price",
            "plan structure and price",
            "asked the price",
            "asked price",
            "answer the price",
            "not answering the price",
            "20 dollars",
            "twenty dollars",
            "100 dollars",
            "one hundred dollars",
            "expensive",
            "free option",
            "really free",
        },
    )


def _pro_tier_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "100 and 200 dollar pro",
            "100 or 200 pro",
            "100 or 200 dollar pro",
            "100 or 200 dollars",
            "$100 or $200 pro",
            "$100 version",
            "$200 version",
            "100 dollar pro",
            "200 dollar pro",
            "100 version",
            "200 version",
            "one hundred and two hundred dollar pro",
            "which pro should i use",
            "which pro",
            "which pro version",
            "pro version",
            "version of pro",
            "pro tier",
            "pro tiers",
            "pro should i use",
            "higher pro tier",
            "higher pro",
            "lower pro tier",
            "lower pro",
            "which paid pro level",
            "which pro plan tier",
            "choose between pro tiers",
            "difference between pro tiers",
            "between 100 and 200 pro",
            "100 and 200 pro",
            "200 dollar pro necessary",
        },
    )


def _pro_tier_question_for_context(normalized: str, turns: list[dict[str, Any]]) -> bool:
    if _pro_tier_question(normalized):
        return True
    if not (_known_heavy_use(normalized, turns) or _prior_pro_tier_context(turns)):
        return False
    return _contains(
        normalized,
        {
            "do not know how heavy",
            "don't know how heavy",
            "not sure how heavy",
            "which tier",
            "which version",
            "which level",
            "how do i choose",
        },
    )


def _price_followup_complaint(normalized: str, turns: list[dict[str, Any]]) -> bool:
    if not _contains(normalized, {"why not answer", "why are you not answering", "not answer"}):
        return False
    return "price" in _prior_customer_text(turns)


def _plus_sufficiency_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "is plus enough",
            "plus going to be enough",
            "plus enough",
            "plus or pro",
            "start with plus",
            "should i choose plus",
            "should i start with plus",
            "is pro worth it",
            "pro worth it",
            "why pro",
            "would plus cover that",
            "is plus the right plan",
            "right plan",
            "which plan",
            "what should i choose",
            "difference between plus and pro",
            "explain the paid plans",
            "what do the plans include",
            "what should i know before paying",
            "free versus plus versus pro",
            "free vs plus vs pro",
            "practical plan comparison",
            "which tier should i compare",
            "plus enough",
        },
    )


def _plain_ask_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "what do you want me to do",
            "what are you asking me",
            "what are you asking",
            "what is the next step",
            "what is your ask",
            "what do you need from me",
            "what are you trying to get me to do",
            "what decision are you asking for",
            "do you want me to buy now",
            "are you asking me to sign up",
            "plainly what do you want",
            "what action do you expect",
            "do not understand the ask",
            "do not understand what you want",
            "dont understand what you want",
            "don t understand what you want",
            "what is this call asking",
            "what is the point here",
            "what should i do next",
        },
    )


def _signup_question(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "how do i sign up",
            "where do i upgrade",
            "show me the official page",
            "where is the plan page",
            "ready to start",
            "what is the next step",
            "what should i do next",
            "sounds good how do i sign up",
            "how do we sign up",
            "can you send me a link",
            "send me a link",
            "how would i get pro",
            "where would i click",
            "how do i start",
            "how do i upgrade to pro",
            "how do i upgrade now",
            "how do i get it",
            "where do i choose the pro tier",
            "where do i choose pro",
            "where can i compare the plan",
            "what page should i use",
            "how do i move forward",
            "where do i buy it",
        },
    )


def _prior_plan_selection(turns: list[dict[str, Any]]) -> bool:
    prior = _prior_customer_text(turns)
    return _contains(
        prior,
        {
            "i want plus",
            "plus sounds right",
            "plus sounds good",
            "i want pro",
            "pro sounds right",
            "sounds like pro",
            "pro seems better",
            "pro is better",
            "pro is the better fit",
            "pro better fit",
            "pro is probably right",
            "pro makes more sense",
            "pro is safer",
            "pro first",
            "leaning pro",
            "free sounds enough",
            "business sounds right",
        },
    )


def _pro_agreement_signal(normalized: str) -> bool:
    return _contains(
        normalized,
        {
            "pro is better",
            "pro seems better",
            "pro probably",
            "pro is probably",
            "pro makes more sense",
            "pro is safer",
            "pro is the stronger",
            "pro sounds right",
            "sounds like pro",
            "then pro",
            "i guess pro",
            "pro fits",
            "pro probably works",
            "i should compare pro",
            "compare pro first",
            "pro for me",
            "that means pro",
            "i think pro",
            "not plus pro",
            "look at pro",
            "leaning pro",
            "pushes me to pro",
            "pro first",
            "i need pro",
        },
    )


def _limit_pain_recommendation_response(turns: list[dict[str, Any]]) -> str:
    if _known_use_case("", turns):
        return (
            "Got it - if limits are already frustrating, Pro is the plan to compare seriously. "
            "Plus is the lower-cost starting point, but Pro is the better fit if you are regularly hitting limits. "
            "Do you want the lower-cost starting point, or the plan least likely to hit limits?"
        )
    return (
        "Got it - hitting limits makes Pro relevant, but I should still tie that to the actual work. "
        "Is this mainly coding, writing, research, files, or team use?"
    )


def _choosing_before_upgrade_response(turns: list[dict[str, Any]]) -> str:
    if _known_use_case("", turns):
        return (
            "Got it - if you are choosing before upgrading and limits are not the problem yet, Plus is the lower-cost starting point. "
            "Pro is the comparison only if heavier use or limits are already blocking the work."
        )
    return (
        "Got it - if you are just choosing before upgrading, I would start with the use case before pushing a tier. "
        "Is this mainly coding, writing, research, files, or team use?"
    )


def _pro_agreement_response(turns: list[dict[str, Any]]) -> str:
    if _known_use_case("", turns) and (_known_heavy_use("", turns) or _known_limit_pain("", turns)):
        if _known_limit_pain("", turns):
            return (
                "Yes - based on coding and writing with explicit limit pain, Pro is the stronger fit to compare. "
                "Plus is cheaper, but Pro is safer if avoiding limits matters. The next step is the official ChatGPT plans page."
            )
        return (
            "Yes - based on heavy coding and writing, Pro is the stronger fit to compare. "
            "Plus is cheaper, but Pro is safer if usage limits matter. The next step is the official ChatGPT plans page."
        )
    if _known_use_case("", turns):
        return (
            "Yes - Pro is worth comparing if the coding and writing workload is heavy or limits matter. "
            "Plus is the lower-cost start; Pro is the safer higher-usage option. The next step is the official ChatGPT plans page."
        )
    return (
        "Pro can be the right comparison for heavier individual use, but I would tie that to the actual work before pushing it. "
        "If the workload is heavy, compare Pro; if it is moderate, Plus is the lower-cost start."
    )


def _commercial_objection_response(normalized: str, turns: list[dict[str, Any]]) -> str:
    objection = _commercial_objection(normalized)
    prior_text = _prior_customer_text(turns)
    if objection == "why_pro":
        if _prior_pro_tier_context(turns) or _pro_tier_question(normalized):
            return (
                "That price concern is fair. For heavy coding and writing, the 100 versus 200 dollar Pro choice is about usage pressure. "
                "If you are unsure, start with the lower Pro tier. Move to the higher Pro tier only if you are regularly maxing out usage or need the most headroom."
            )
        if _another_ai_user(prior_text) or _competitor_objection(f"{prior_text} {normalized}"):
            return (
                "No automatic switch: against your current tool, Pro only makes sense if ChatGPT fills a specific gap and you expect heavier usage. "
                "If the current tool covers the work, stay there; if coding, files, or usage headroom are the gap, compare Pro, with Plus as the lower-cost test."
            )
        if _known_limit_pain(normalized, turns):
            return (
                "The reason to compare Pro over Plus is limits. Plus is the lower-cost paid start; "
                "Pro is the safer choice if limits are already interrupting coding and writing."
            )
        return (
            "Pro over Plus is mainly a usage decision. Plus is cheaper and often enough for moderate coding and writing; "
            "Pro is safer for heavy use if avoiding limits matters. Choose Plus for lower cost, Pro for more usage headroom."
        )
    if objection == "subscription":
        return (
            "I understand the subscription concern. I would not add one unless ChatGPT removes real friction in your workflow. "
            "For heavy coding and writing, start with Plus if price matters most; choose Pro only if usage headroom or limits justify the extra cost."
        )
    if objection == "competitor":
        return (
            "If the paid tool you already have covers the job, I would not push a switch. "
            "Compare ChatGPT only where your current tool is weakest; for heavy coding and writing, that means Plus as a low-cost test or Pro for more usage headroom."
        )
    if objection == "price":
        if _prior_pro_tier_context(turns) or _pro_tier_question(normalized):
            return (
                "That price concern is fair. If you are already choosing between Pro tiers, start with the lower Pro tier unless you know you need maximum usage. "
                "Move to the higher Pro tier only if you are regularly maxing out usage or need the most headroom."
            )
        return (
            "That price concern is fair. If you are using it casually, I would not pay for Pro. "
            "For heavy coding and writing, the question is whether extra usage headroom saves enough friction to justify the price. "
            "If price matters most, start with Plus. If limits slow you down, Pro is the cleaner fit. "
            "The official ChatGPT pricing page is the source of truth for exact current prices."
        )
    return (
        "The clean decision is value versus cost: Plus is the lower-cost start; Pro is the higher-usage comparison. "
        "I would choose Pro only if the heavier workload makes limits matter."
    )


def _pro_tier_response(campaign: dict | None, normalized: str, turns: list[dict[str, Any]]) -> str:
    pro_price = _source_speech(
        campaign,
        "pro_tiers_100_200_001",
        "The Pro help article describes 100 dollar and 200 dollar Pro tiers.",
    )
    caveat = _official_price_caveat()
    return (
        f"{pro_price} Exact tier details should be checked against official OpenAI sources. "
        "If you are unsure, start with the lower Pro tier. "
        f"Move to the higher Pro tier only if you are regularly maxing out usage or need the most headroom. {caveat}"
    )


def _avoid_duplicate_response(
    candidate_response: str,
    proposed: str,
    fallback: str,
    turns: list[dict[str, Any]] | None = None,
) -> str:
    normalized_proposed = " ".join(proposed.split()).lower()
    prior_responses = {
        " ".join(str((turn.get("summary") or {}).get("final_response") or "").split()).lower()
        for turn in list(turns or [])
    }
    if " ".join(candidate_response.split()).lower() == normalized_proposed:
        return fallback
    if normalized_proposed and normalized_proposed in prior_responses:
        return fallback
    return proposed


def _price_response(campaign: dict | None, normalized: str, turns: list[dict[str, Any]]) -> str:
    plus_price = _source_speech(campaign, "plus_price_20_001", "Plus is an individual paid tier.")
    plus_features = _source_speech(
        campaign,
        "plus_features_001",
        "Plus gives more access than Free, with higher limits and expanded tools.",
    )
    pro_price = _source_speech(
        campaign,
        "pro_tiers_100_200_001",
        "Pro is the heavier-use individual tier.",
    )
    business_price = _source_speech(
        campaign,
        "business_standard_seat_price_001",
        "Business is for teams and pricing can vary by region.",
    )
    caveat = _official_price_caveat()
    known_context = _known_use_case(normalized, turns)
    heavy_context = _known_heavy_use(normalized, turns)
    limit_context = _known_limit_pain(normalized, turns)

    if _contains(normalized, {"what do i get for 20 dollars", "20 dollars", "twenty dollars"}):
        suffix = (
            " For coding and writing, Plus is the lower-cost starting point; if limits are already frustrating, compare Pro."
            if known_context
            else ""
        )
        return f"{plus_price} {plus_features} {caveat}{suffix}"
    if _contains(normalized, {"how much is plus", "plus cost", "pay for plus", "is plus twenty"}):
        if limit_context:
            suffix = (
                " Given you are hitting limits, compare Plus against Pro: "
                "Plus is the lower-cost start; Pro is safer if avoiding limits matters."
            )
        elif heavy_context:
            suffix = (
                " Given coding and heavy use, I would compare Pro first if usage headroom matters; "
                "Plus is the lower-cost start."
            )
        else:
            suffix = ""
        return f"{plus_price} {caveat}{suffix}"
    if _contains(normalized, {"how much is pro", "pro cost", "pay for pro", "pro one hundred"}):
        suffix = (
            " Given you are hitting limits, compare that against Plus at 20 dollars per month: Plus is cheaper; Pro is for higher usage."
            if known_context and limit_context
            else (
                " Given coding and heavy use, compare that against Plus at 20 dollars per month: Plus is cheaper; Pro is for higher usage."
                if known_context and heavy_context
                else (" That is the relevant comparison if limits are the main frustration." if limit_context else "")
            )
        )
        return f"{pro_price} {caveat}{suffix}"
    if "business" in normalized:
        return f"{business_price} {caveat}"
    if "enterprise" in normalized:
        return "Enterprise pricing is not a public fixed individual price in this fixture; the official route is contact sales. " + caveat
    if known_context and limit_context:
        return (
            f"Sure. Free is the no-cost option. {plus_price} {pro_price} "
            f"{caveat} Given you are hitting limits, the relevant comparison is Plus at 20 dollars per month versus the Pro tiers. "
            "I would compare Pro first if avoiding limits matters. Plus is cheaper; Pro is safer."
        )
    if known_context and heavy_context:
        return (
            f"Sure. Free is the no-cost option. {plus_price} {pro_price} "
            f"{caveat} Given coding and heavy use, I would compare Pro first. The real decision is Plus as the lower-cost start versus Pro as the higher-usage option."
        )
    if known_context:
        return (
            f"Sure. Free is the no-cost option. {plus_price} {pro_price} "
            f"{caveat} For coding and writing, Plus is the lower-cost paid starting point; Pro is for heavier usage."
        )
    return (
        f"Sure. Free is the no-cost option. {plus_price} {pro_price} "
        "Business is for teams, and Enterprise routes to contact sales. "
        f"{caveat} The decision frame is Free for no-cost use, Plus as the lower-cost individual start, "
        "Pro for heavier individual use, and Business or Enterprise when team controls matter."
    )


def _plus_sufficiency_response(normalized: str, turns: list[dict[str, Any]]) -> str:
    prior_state = _prior_openai_state(turns)
    if not _known_use_case(normalized, turns):
        if prior_state.get("openai_adoption_state") == "other_ai_user" or _another_ai_user(_prior_customer_text(turns)):
            return (
                "If your current tool covers everything, I would not push a paid ChatGPT plan. "
                "The reason to compare ChatGPT is a real gap in coding, files, research, writing, voice/images, or team controls."
            )
        return (
            "Plus is usually the first paid individual plan to compare when Free or Go feels limited. "
            "Pro is for heavier individual usage, especially if limits, files, or advanced tools are already frustrating. "
            "To choose cleanly, the deciding factor is whether your main use is coding, writing, research, files, or something lighter."
        )
    if _known_limit_pain(normalized, turns):
        return _limit_pain_recommendation_response(turns)
    if _choosing_before_upgrade(normalized):
        return _choosing_before_upgrade_response(turns)
    heavy = _known_heavy_use(normalized, turns)
    if heavy:
        proposed = (
            "For coding and writing, Plus is usually enough if use is moderate. "
            "Since your use is heavy, I would compare Pro seriously. Plus is the lower-cost starting point; "
            "Pro is safer if usage limits matter. The next step is the official ChatGPT plans page."
        )
        fallback = (
            "We've already narrowed it: for heavy coding and writing, Pro is the stronger plan to compare; "
            "Plus is the cheaper fallback if cost matters more than usage headroom. The next step is the official ChatGPT plans page."
        )
        return _avoid_duplicate_response("", proposed, fallback, turns)
    proposed = (
        "For coding and writing, Plus is usually enough if use is moderate. "
        "Plus is the lower-cost starting point; Pro is safer if usage limits matter. "
        "The next action is to compare Plus versus Pro on the official ChatGPT plans page."
    )
    fallback = (
        "We've already covered the plan frame: Plus is the lower-cost start for moderate individual use; "
        "Pro is the comparison if heavier usage or limits matter. The next action is to compare those two on the official ChatGPT plans page."
    )
    return _avoid_duplicate_response("", proposed, fallback, turns)


def _plain_ask_response(turns: list[dict[str, Any]]) -> str:
    if _known_use_case("", turns):
        return (
            "I'm not asking you to do anything yet. I'm helping you decide whether Free, Plus, Pro, Business, or Enterprise fits. "
            "Since you mentioned coding and writing, the next useful choice is usually Plus versus Pro."
        )
    return (
        "I'm not asking you to do anything yet. I'm helping you decide whether Free, Plus, Pro, Business, or Enterprise fits. "
        "The useful next detail is whether this is for personal work, team use, API usage, or enterprise controls."
    )


def _signup_response(normalized: str, turns: list[dict[str, Any]]) -> str:
    link_requested = _contains(normalized, {"send me a link", "can you send me a link"})
    if _team_context(normalized, turns):
        return (
            "For Business, use the official ChatGPT plans page for the self-serve workspace route. "
            "For Enterprise requirements, use contact sales."
        )
    if _prior_pro_tier_context(turns):
        suffix = " I cannot send a link from this fixture." if link_requested else ""
        return (
            "For individual plans, use the official ChatGPT plans page or profile upgrade flow. "
            "Since you are deciding between Pro tiers, start with the lower Pro tier unless you already know you need maximum usage. "
            "Move up only if you hit limits or need the most headroom."
            f"{suffix}"
        )
    if _known_use_case("", turns):
        suffix = " I cannot send a link from this fixture." if link_requested else ""
        if _known_limit_pain(normalized, turns) or _known_heavy_use(normalized, turns):
            basis = (
                "coding/writing and hitting limits"
                if _known_limit_pain(normalized, turns)
                else "heavy coding/writing"
            )
            value = "fewer limits" if _known_limit_pain(normalized, turns) else "more usage headroom"
            return (
                "Yes - for individual plans, use the official ChatGPT plans page or profile upgrade flow. "
                f"Based on what you said - {basis} - compare Pro first if you want {value}; "
                "choose Plus if you want the lower-cost starting point."
                f"{suffix}"
            )
        return (
            "If you decide to upgrade, individual plans use the official ChatGPT plans page or profile upgrade flow. "
            "For coding and writing, choose Plus first unless limits are already frustrating; then compare Pro."
            f"{suffix}"
        )
    suffix = " I cannot send a link from this fixture." if link_requested else ""
    return (
        "If you decide to upgrade, individual plans use the official ChatGPT plans page or profile upgrade flow, and Enterprise uses contact sales. "
        f"Choose the plan only after the use case is clear.{suffix}"
    )


def _known_context_repeat_response(normalized: str, turns: list[dict[str, Any]], *, mode: str = "repeat") -> tuple[str, str, str]:
    continuing = mode == "continue"
    if _team_context(normalized, turns):
        return (
            "public_plan_team_context_continue_progress" if continuing else "public_plan_team_context_repeat_progress",
            (
                "To move the team path forward: Business is the self-serve workspace route; Enterprise is for SSO, SCIM, procurement, or security review."
                if continuing
                else "You already gave the team context. The useful next choice is Business for a self-serve workspace, or Enterprise if you need SSO, SCIM, procurement, or security review."
            ),
            "team_plan_fit",
        )
    if _known_use_case(normalized, turns) and _known_heavy_use(normalized, turns):
        if _known_limit_pain(normalized, turns):
            return (
                "public_plan_known_use_limit_pain_continue_progress" if continuing else "public_plan_known_use_limit_pain_repeat_progress",
                _limit_pain_recommendation_response(turns),
                "plan_fit",
            )
        return (
            "public_plan_known_use_and_heavy_continue_progress" if continuing else "public_plan_known_use_and_heavy_repeat_progress",
            (
                "To move it forward: compare Pro first for heavy coding and writing; choose Plus only if lower cost matters more than usage headroom. The next step is the official ChatGPT plans page."
                if continuing
                else "You already gave both use case and intensity. For heavy coding and writing, Pro is the stronger fit to compare; Plus is the lower-cost starting point. The next step is the official ChatGPT plans page."
            ),
            "plan_fit",
        )
    if _known_use_case(normalized, turns):
        return (
            "public_plan_known_use_case_continue_progress" if continuing else "public_plan_known_use_case_repeat_progress",
            (
                "To move it forward: compare Plus as the safer first paid plan for that individual use; compare Pro only if limits, files, or heavier usage are already frustrating. The next action is the official ChatGPT plans page."
                if continuing
                else "You already gave the use case. For that kind of individual work, Plus is the safer first paid plan; Pro is the comparison if limits, files, or heavier usage are already frustrating. The next action is the official ChatGPT plans page."
            ),
            "plan_fit",
        )
    if _known_heavy_use(normalized, turns):
        return (
            "public_plan_heavy_use_continue_progress" if continuing else "public_plan_heavy_use_repeat_progress",
            (
                "To move it forward: heavy use can make Plus or Pro relevant; the remaining question is whether the work is coding, writing, research, files, or team use."
                if continuing
                else "You already gave the usage level. Heavy personal use can make Plus or Pro relevant; the missing piece is whether the work is coding, writing, research, files, or a team."
            ),
            "use_case_discovery",
        )
    return _context_progress_response(normalized, turns)


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
            "are you openai",
            "is openai behind this",
            "do you represent openai",
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
        if _known_limit_pain(normalized, turns):
            return (
                "public_plan_known_use_limit_pain_progress",
                _limit_pain_recommendation_response(turns),
                "plan_fit",
            )
        return (
            "public_plan_known_use_and_heavy_progress",
            (
                "Right - coding and writing with heavier use. I would compare Pro first because usage headroom matters more here. "
                "Plus is the lower-cost starting point; Pro is safer if usage limits matter."
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
            "plus sounds good",
            "how do i sign up",
            "where do i upgrade",
            "show me the official page",
            "i want pro",
            "i want go",
            "pro seems better",
            "pro is better",
            "pro makes more sense",
            "pro sounds right",
            "pro first",
            "then pro",
            "i guess pro",
            "pro fits",
            "pro probably works",
            "pro is the plan",
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


def duplicate_repair_response(
    *,
    transcript: str,
    memory: dict[str, Any] | None,
    turns: list[dict[str, Any]],
    candidate_response: str,
    campaign: dict | None,
) -> str | None:
    if not applies(campaign):
        return None
    normalized = _normalize_openai_asr_aliases(" ".join(str(transcript or "").lower().split()))
    state = _prior_openai_state(turns, memory)
    if not state:
        return None
    if _pro_tier_question_for_context(normalized, turns):
        return _pro_tier_response(campaign, normalized, turns)
    if _price_question(normalized) or _price_followup_complaint(normalized, turns):
        return _avoid_duplicate_response(
            candidate_response,
            _price_response(campaign, normalized, turns),
            (
                "Same price context: Plus is listed at 20 dollars per month, while Pro has 100 and 200 dollar tiers. "
                "Given the known usage context, Plus is cheaper; Pro is for higher usage. The official ChatGPT pricing page is the source of truth."
            ),
            turns,
        )
    if _contains(normalized, {"api included", "is api included", "api usage", "tokens"}):
        return "API usage is separate from ChatGPT subscriptions where the official sources state that boundary. Are you asking about ChatGPT itself, the API, or both?"
    if _signup_question(normalized):
        return _signup_response(normalized, turns)
    if _known_limit_pain(normalized, turns) or state.get("openai_limit_pain") is True:
        return _avoid_duplicate_response(
            candidate_response,
            _limit_pain_recommendation_response(turns),
            (
                "That new limits signal points more toward Pro than Plus. "
                "Plus is the lower-cost starting point; Pro is the path if avoiding limits matters most."
            ),
            turns,
        )
    if _known_use_case(normalized, turns) and (_known_heavy_use(normalized, turns) or state.get("openai_usage_intensity") == "heavy"):
        return _avoid_duplicate_response(
            candidate_response,
            _plus_sufficiency_response(normalized, turns),
            (
                "Since you already gave the use case and intensity, I would compare Pro first for heavy coding and writing. "
                "Plus is lower cost; Pro is safer if usage headroom matters. The next step is the official ChatGPT plans page."
            ),
            turns,
        )
    if _known_use_case(normalized, turns):
        return (
            "You already gave the use case. For coding and writing, Plus is the lower-cost paid starting point; "
            "Pro is the comparison if heavier usage or limits are already frustrating."
        )
    if state.get("openai_usage_intensity") == "heavy":
        return (
            "You already gave the usage level. Heavy personal use can make Plus or Pro relevant; "
            "the missing piece is whether the work is coding, writing, research, files, or team use."
        )
    return None


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

    normalized = _normalize_openai_asr_aliases(normalized)

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

    if _pro_agreement_signal(normalized):
        return _frame(
            **base,
            semantic="public_plan_pro_agreement_closed",
            response=_pro_agreement_response(turns),
            dialogue_focus="self_serve_close",
            polarity="close",
        )

    if _commercial_objection(normalized):
        prior_text = _prior_customer_text(turns)
        if _light_or_basic_use(prior_text) or _current_tool_enough(f"{prior_text} {normalized}"):
            return _frame(
                **base,
                semantic="public_plan_objection_no_fit_close",
                response=(
                    "Then I would not push a paid ChatGPT plan. Free or staying with your current tool may be enough "
                    "unless you hit limits, need a missing tool, or need team controls. The next action is no paid close."
                ),
                dialogue_focus="no_fit",
                polarity="low_pressure",
            )
        return _frame(
            **base,
            semantic="public_plan_commercial_objection_handled",
            response=_commercial_objection_response(normalized, turns),
            dialogue_focus="objection_handling",
            polarity="objection",
        )

    if _signup_question(normalized) and _prior_pro_tier_context(turns):
        return _frame(
            **base,
            semantic="public_plan_self_serve_next_step_answered",
            response=_signup_response(normalized, turns),
            dialogue_focus="self_serve_close",
            polarity="close",
        )

    if _pro_tier_question_for_context(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_pro_tier_comparison_answered",
            response=_pro_tier_response(campaign, normalized, turns),
            dialogue_focus="plan_fit",
            polarity="answer",
        )

    if _price_question(normalized) or _price_followup_complaint(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_direct_price_answer",
            response=_price_response(campaign, normalized, turns),
            dialogue_focus="price",
            polarity="answer",
        )

    if _plus_sufficiency_question(normalized):
        return _frame(
            **base,
            semantic="public_plan_plus_sufficiency_answered",
            response=_plus_sufficiency_response(normalized, turns),
            target_gap="usage_intensity",
            dialogue_focus="plan_fit",
            polarity="recommendation",
        )

    if _signup_question(normalized) and (
        _prior_plan_selection(turns)
        or _contains(
            normalized,
            {
                "how do i sign up",
                "where do i upgrade",
                "show me the official page",
                "where is the plan page",
                "sounds good how do i sign up",
                "how do we sign up",
                "can you send me a link",
                "send me a link",
            },
        )
    ):
        return _frame(
            **base,
            semantic="public_plan_self_serve_next_step_answered",
            response=_signup_response(normalized, turns),
            dialogue_focus="self_serve_close",
            polarity="close",
        )

    if _plain_ask_question(normalized):
        return _frame(
            **base,
            semantic="public_plan_plain_ask_explained",
            response=_plain_ask_response(turns),
            dialogue_focus="plain_ask",
            polarity="clarification",
        )

    if _signup_question(normalized):
        return _frame(
            **base,
            semantic="public_plan_self_serve_next_step_answered",
            response=_signup_response(normalized, turns),
            dialogue_focus="self_serve_close",
            polarity="close",
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
                "if limits, tools, or team needs matter. I would not push a paid plan; the next action is stay free or stop here."
            ),
            target_gap="openai_adoption_state",
            dialogue_focus="low_intent",
            polarity="low_pressure",
        )

    if _current_tool_enough(normalized):
        proposed = (
            "Then I would not push a paid ChatGPT plan. Free or staying with your current tool may be enough "
            "unless you hit limits, need tools your current setup lacks, or need team controls. The next action is stay free or stop here."
        )
        fallback = (
            "Same recommendation: if your current tool is enough and you do not want to pay, stay free or stay with the current tool. "
            "No paid ChatGPT close is needed unless a real gap appears."
        )
        return _frame(
            **base,
            semantic="public_plan_current_tool_no_fit",
            response=_avoid_duplicate_response("", proposed, fallback, turns),
            dialogue_focus="no_fit",
            polarity="low_pressure",
        )

    if _competitor_objection(normalized):
        if _known_use_case(normalized, turns):
            proposed = (
                "A switch only makes sense if ChatGPT improves a specific gap in your current tool: "
                "coding workflow, files, research, writing, voice/images, or team controls. For coding and writing, compare Plus as the lower-cost test and Pro if heavier usage matters."
            )
            fallback = (
                "We've already framed the switch: compare ChatGPT only against a current-tool gap. "
                "If the current tool covers the job, stay there; if coding, files, or usage headroom are the gap, compare Plus as the lower-cost test and Pro for heavier use."
            )
            response = _avoid_duplicate_response("", proposed, fallback, turns)
        else:
            proposed = (
                "A switch only makes sense if ChatGPT covers something your current tool does not: "
                "coding workflow, files, research, voice/images, team admin, or privacy controls. What is the one area where your current tool feels weakest?"
            )
            fallback = (
                "We've already covered the current-tool question. Do not switch if it covers the job; "
                "compare ChatGPT only against one concrete gap such as coding workflow, files, research, voice/images, team admin, or privacy controls."
            )
            response = _avoid_duplicate_response("", proposed, fallback, turns)
        return _frame(
            **base,
            semantic="public_plan_competitor_objection",
            response=response,
            dialogue_focus="competitive_objection",
            polarity="objection",
        )

    if _current_chatgpt_user(normalized):
        if _another_ai_user(normalized):
            return _frame(
                **base,
                semantic="public_plan_current_chatgpt_or_other_ai_user",
                response=(
                    "Got it - sounds like you're already using ChatGPT or another AI tool. "
                    "The useful comparison is whether ChatGPT covers something your current setup does not. "
                    "What is the one area where your current tool feels weakest: coding, files, research, writing, voice/images, or team controls?"
                ),
                target_gap="alternative_tool_gap",
                dialogue_focus="competitive_objection",
                polarity="progress",
            )
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
                "A switch only makes sense if ChatGPT gives you something your current setup does not: "
                "stronger coding workflow, file handling, research, voice/images, or team controls. What is the one area where your current tool feels weakest?"
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

    if _contains(
        normalized,
        {
            "we have a team",
            "team",
            "for a team",
            "this is for a team",
            "actually this is for a team",
            "small team",
            "team admin",
            "team workspace",
            "workspace controls",
            "enterprise controls",
            "sso",
            "scim",
            "procurement",
        },
    ):
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
        if _known_use_case(normalized, turns):
            return _frame(
                **base,
                semantic="public_plan_competitor_objection_with_use_case",
                response=(
                    "A switch only makes sense if ChatGPT improves a specific gap in your current tool: "
                    "coding workflow, files, research, writing, voice/images, or team controls. For coding and writing, compare Plus as the lower-cost test and Pro if heavier usage matters."
                ),
                dialogue_focus="competitive_objection",
                polarity="objection",
            )
        return _frame(
            **base,
            semantic="public_plan_competitor_objection",
            response=(
                "A switch only makes sense if ChatGPT covers something your current tool does not: "
                "coding workflow, files, research, voice/images, team admin, or privacy controls. What is the one area where your current tool feels weakest?"
            ),
            dialogue_focus="competitive_objection",
            polarity="objection",
        )

    if _known_limit_pain(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_limit_pain_answered",
            response=_limit_pain_recommendation_response(turns),
            target_gap="usage_intensity",
            dialogue_focus="plan_fit",
            polarity="recommendation",
        )

    if _choosing_before_upgrade(normalized):
        return _frame(
            **base,
            semantic="public_plan_choosing_before_upgrade_answered",
            response=_choosing_before_upgrade_response(turns),
            target_gap="usage_intensity",
            dialogue_focus="plan_fit",
            polarity="recommendation",
        )

    if _already_told(normalized):
        semantic, response, focus = _known_context_repeat_response(normalized, turns)
        return _frame(
            **base,
            semantic=f"{semantic}_already_answered",
            response=response,
            target_gap="openai_use_case",
            dialogue_focus=focus,
            polarity="progress",
        )

    if _continue_request(normalized):
        semantic, response, focus = _known_context_repeat_response(normalized, turns, mode="continue")
        return _frame(
            **base,
            semantic=f"{semantic}_continue",
            response=response,
            target_gap="openai_use_case",
            dialogue_focus=focus,
            polarity="progress",
        )

    if _known_use_case(normalized, turns) and _known_heavy_use(normalized, turns):
        proposed = (
            "Right - coding and writing with heavy use. I would compare Pro first because usage headroom matters here. "
            "Plus is the lower-cost starting point; Pro is safer if usage limits matter."
        )
        fallback = (
            "We already have the key context: heavy coding and writing. Compare Pro first for usage headroom; "
            "choose Plus only if the lower monthly cost matters more. The next decision is Pro versus Plus, not more discovery."
        )
        return _frame(
            **base,
            semantic="public_plan_known_use_and_heavy_answered",
            response=_avoid_duplicate_response("", proposed, fallback, turns),
            target_gap="usage_intensity",
            dialogue_focus="plan_fit",
            polarity="recommendation",
        )

    if _known_use_case(normalized, turns) and _contains(normalized, {"coding", "writing"}):
        return _frame(
            **base,
            semantic="public_plan_use_case_confirmed",
            response=(
                "Right - ChatGPT for coding and writing. Plus is usually the first paid plan to compare; Pro is for heavier use. "
                "Are you using it occasionally or heavily every day?"
            ),
            target_gap="individual_use_case",
            dialogue_focus="usage_intensity",
            polarity="progress",
        )

    if _known_use_case(normalized, turns):
        proposed = (
            "That ChatGPT use case is enough to frame the plan decision. Plus is the lower-cost first paid plan; "
            "Pro is for heavier individual use. The next action is compare Plus versus Pro rather than restart discovery."
        )
        fallback = (
            "We already have the use case. Compare Plus as the lower-cost first paid plan; compare Pro only if heavier usage or limits matter. "
            "The next action is the official ChatGPT plans page."
        )
        return _frame(
            **base,
            semantic="public_plan_use_case_confirmed",
            response=_avoid_duplicate_response("", proposed, fallback, turns),
            target_gap="individual_use_case",
            dialogue_focus="usage_intensity",
            polarity="progress",
        )

    if _known_heavy_use(normalized, turns):
        return _frame(
            **base,
            semantic="public_plan_heavy_use_needs_relevance",
            response=(
                "Heavy daily use makes Pro worth comparing, with Plus as the lower-cost fallback. "
                "The next action is to tie that to the work type only if the use case is still unknown."
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
