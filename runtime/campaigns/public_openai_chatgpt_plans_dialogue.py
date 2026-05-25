from __future__ import annotations

from typing import Any


CAMPAIGN_ID = "public-openai-chatgpt-plans"
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
    prior_has_use_case = _contains(
        prior,
        {
            "coding",
            "code",
            "writing",
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
            "hit limits",
            "hitting limits",
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
    normalized = _normalize_openai_asr_aliases(normalized)
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
            "monthly price",
            "paid plan price",
            "tell me the cost",
            "price before",
            "want to know the price",
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
            "which plan",
            "what should i choose",
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
            "free sounds enough",
            "business sounds right",
        },
    )


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

    if _contains(normalized, {"what do i get for 20 dollars", "20 dollars", "twenty dollars"}):
        suffix = (
            " For coding and writing, Plus is usually the first paid plan to try; if limits are already frustrating, compare Pro."
            if known_context
            else ""
        )
        return f"{plus_price} {plus_features} {caveat}{suffix}"
    if _contains(normalized, {"how much is plus", "plus cost", "pay for plus", "is plus twenty"}):
        suffix = " Since your use sounds heavy, compare Pro if you regularly hit limits." if heavy_context else ""
        return f"{plus_price} {caveat}{suffix}"
    if _contains(normalized, {"how much is pro", "pro cost", "pay for pro", "pro one hundred"}):
        return f"{pro_price} {caveat}"
    if "business" in normalized:
        return f"{business_price} {caveat}"
    if "enterprise" in normalized:
        return "Enterprise pricing is not a public fixed individual price in this fixture; the official route is contact sales. " + caveat
    return (
        f"Sure. Free is the no-cost option. {plus_price} {pro_price} "
        "Business is for teams, and Enterprise routes to contact sales. "
        f"{caveat} Are you mainly comparing Plus and Pro?"
    )


def _plus_sufficiency_response(normalized: str, turns: list[dict[str, Any]]) -> str:
    if not _known_use_case(normalized, turns):
        return (
            "Plus is usually the first paid individual plan to compare when Free or Go feels limited. "
            "Pro is for heavier individual usage, especially if limits, files, or advanced tools are already frustrating. "
            "To choose cleanly, the deciding factor is whether your main use is coding, writing, research, files, or something lighter."
        )
    heavy = _known_heavy_use(normalized, turns)
    if heavy:
        return (
            "For coding and writing, Plus is usually the first paid plan to try. "
            "Since you said your use is a little heavy, Pro is worth comparing if you regularly hit limits, use files heavily, "
            "or need the highest individual usage. If you want the safer starting point, Plus first; if limits are already frustrating, Pro. "
            "Are you mostly hitting limits, or just trying to choose before upgrading?"
        )
    return (
        "For coding and writing, Plus is usually the first paid plan to try. "
        "Pro is worth comparing only if you regularly hit limits, use files heavily, or need the highest individual usage. "
        "If you want the safer starting point, Plus first; if limits are already frustrating, Pro."
    )


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


def _signup_response(turns: list[dict[str, Any]]) -> str:
    if _known_use_case("", turns):
        return (
            "If you decide to upgrade, individual plans use the official ChatGPT plans page or profile upgrade flow. "
            "I cannot send a link, book anything, or take payment here. For coding and writing, choose Plus first unless limits are already frustrating; then compare Pro."
        )
    return (
        "If you decide to upgrade, individual plans use the official ChatGPT plans page or profile upgrade flow, and Enterprise uses contact sales. "
        "I cannot send a link, book anything, or take payment here."
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
        return (
            "public_plan_known_use_and_heavy_continue_progress" if continuing else "public_plan_known_use_and_heavy_repeat_progress",
            (
                "To move it forward: start with Plus if you want the safer paid step; compare Pro if limits, files, or advanced tools are already blocking your coding and writing."
                if continuing
                else "You already gave both use case and intensity. For coding and writing on the heavy side, Plus is the safer paid starting point; Pro is the comparison if limits are already frustrating."
            ),
            "plan_fit",
        )
    if _known_use_case(normalized, turns):
        return (
            "public_plan_known_use_case_continue_progress" if continuing else "public_plan_known_use_case_repeat_progress",
            (
                "To move it forward: Plus is the safer first paid plan for that individual use; Pro is worth comparing only if limits, files, or heavier usage are already frustrating."
                if continuing
                else "You already gave the use case. For that kind of individual work, Plus is the safer first paid plan; Pro is the comparison if limits, files, or heavier usage are already frustrating."
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
            "plus sounds good",
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
        or _contains(normalized, {"how do i sign up", "where do i upgrade", "show me the official page", "where is the plan page", "sounds good how do i sign up", "how do we sign up", "can you send me a link", "send me a link"})
    ):
        return _frame(
            **base,
            semantic="public_plan_self_serve_next_step_answered",
            response=_signup_response(turns),
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
            response=_signup_response(turns),
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
                "if limits, tools, or team needs matter. I can explain Free versus paid only if that would be useful, or I can stop here."
            ),
            target_gap="openai_adoption_state",
            dialogue_focus="low_intent",
            polarity="low_pressure",
        )

    if _current_chatgpt_user(normalized):
        if _another_ai_user(normalized):
            return _frame(
                **base,
                semantic="public_plan_current_chatgpt_or_other_ai_user",
                response=(
                    "Got it - sounds like you're already using ChatGPT or another AI tool. "
                    "The useful comparison is whether ChatGPT covers something your current setup does not. "
                    "What matters most: coding, writing, research, files, team admin, or privacy controls?"
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
        return _frame(
            **base,
            semantic="public_plan_known_use_and_heavy_answered",
            response=_plus_sufficiency_response(normalized, turns),
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
        return _frame(
            **base,
            semantic="public_plan_use_case_confirmed",
            response=(
                "That ChatGPT use case makes plan fit relevant. Plus is usually the first paid plan to compare; Pro is for heavier individual use. "
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
