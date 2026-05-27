from __future__ import annotations

import re
from typing import Any

from runtime.llm_brain.conversation_brain_schema import validate_conversation_brain_output


RAW_URL_RE = re.compile(r"https?://\S+", re.I)
INTERNAL_POLICY_RE = re.compile(
    r"internal policy|source-grounded|guardrail|approved qualified reviewer|"
    r"human_followup_owner|appointment_target|current call scope|reasoning trace",
    re.I,
)
SIDE_EFFECT_RE = re.compile(
    r"\b(sent|send|emailed|created|booked|scheduled|updated|wrote|logged)\b"
    r".{0,48}\b(email|calendar|invite|crm|hubspot|salesforce|ticket|record)\b",
    re.I,
)
AFFILIATION_RE = re.compile(r"\bwe at openai\b|\bour openai\b|\bi work for openai\b|\bofficial openai\b", re.I)
CAMPAIGN_LEAKAGE_RE = re.compile(
    r"routesignal|prod-102|source bundle|campaign id|live-demo|runtime policy|"
    r"semantic frame|state_update|safety_flags",
    re.I,
)
UNSUPPORTED_FACT_RE = re.compile(
    r"guarantee|guaranteed|unlimited access|always gives|every newest model|100%|"
    r"will definitely|automatically upgrades|no limits",
    re.I,
)
TEAM_LANGUAGE_RE = re.compile(r"\byour team\b|\bfor the team\b|\bteam plan\b|\bbusiness workspace\b", re.I)
PRODUCT_CLAIM_RE = re.compile(
    r"\b(chatgpt|free|plus|pro|business|enterprise|openai|contact sales)\b|"
    r"\b(profile upgrade|official chatgpt|official pricing|official plan)\b",
    re.I,
)
FACTUAL_PRODUCT_CLAIM_VERB_RE = re.compile(
    r"\b(is|are|has|have|includes|offers|costs|listed|compares|gives|routes|uses|"
    r"upgrade|upgrades|available|designed|points|pricing)\b",
    re.I,
)


def normalize(text: Any) -> str:
    return " ".join(str(text or "").lower().split())


def sentence_count(text: str) -> int:
    fragments = [item.strip() for item in re.split(r"[.!?]+", text) if item.strip()]
    return max(1, len(fragments)) if text.strip() else 0


def buyer_text(case: dict[str, Any]) -> str:
    return str(case.get("sanitized_buyer_text") or case.get("raw_buyer_text") or "")


def is_terminal_thanks_turn(payload: dict[str, Any], case: dict[str, Any]) -> bool:
    text = normalize(buyer_text(case))
    semantic = payload.get("semantic_frame") if isinstance(payload, dict) else {}
    strategy = payload.get("sales_strategy") if isinstance(payload, dict) else {}
    semantic_text = normalize(" ".join(str(semantic.get(key, "")) for key in ("semantic_family", "speech_act", "sub_intent")))
    return (
        ("thanks" in text or "thank" in text)
        and "thank" in semantic_text
        and isinstance(strategy, dict)
        and strategy.get("should_ask_question") is False
    )


def should_skip_buyer_word_preservation(phrase: str, payload: dict[str, Any], case: dict[str, Any]) -> bool:
    normalized_phrase = normalize(phrase)
    if normalized_phrase == "check" and is_terminal_thanks_turn(payload, case):
        return True
    return False


def approved_fact_summary_text(case: dict[str, Any]) -> str:
    summaries = case.get("approved_campaign_fact_summaries") or {}
    if isinstance(summaries, dict):
        return normalize(" ".join(str(value) for value in summaries.values()))
    if isinstance(summaries, list):
        return normalize(" ".join(str(value) for value in summaries))
    return ""


def draft_has_factual_product_claim(draft: str) -> bool:
    for sentence in re.split(r"(?<=[.!?])\s+", draft.strip()):
        stripped = sentence.strip()
        if not stripped or stripped.endswith("?"):
            continue
        if PRODUCT_CLAIM_RE.search(stripped) and FACTUAL_PRODUCT_CLAIM_VERB_RE.search(stripped):
            return True
    return False


def draft_product_claim_supported(draft: str, case: dict[str, Any]) -> bool:
    normalized_draft = normalize(draft)
    approved_text = approved_fact_summary_text(case)
    approved_ids = set(case.get("approved_campaign_fact_ids") or [])
    if not draft_has_factual_product_claim(draft):
        return True
    if not approved_ids and not approved_text:
        return False
    if not approved_text:
        return True
    product_terms = {
        "chatgpt",
        "free",
        "plus",
        "pro",
        "business",
        "enterprise",
        "openai",
        "profile upgrade",
        "official chatgpt",
        "official pricing",
        "official plan",
        "contact sales",
    }
    mentioned_terms = [term for term in product_terms if term in normalized_draft]
    return all(term in approved_text for term in mentioned_terms)


def verify_conversation_brain_output(payload: dict[str, Any], case: dict[str, Any]) -> list[str]:
    errors = validate_conversation_brain_output(payload)
    if errors:
        return errors

    text = buyer_text(case)
    normalized_buyer = normalize(text)
    draft = str(payload["draft_response"])
    normalized_draft = normalize(draft)
    semantic = payload["semantic_frame"]
    state_update = payload["state_update"]
    strategy = payload["sales_strategy"]
    response_plan = payload["response_plan"]
    safety_flags = payload["safety_flags"]

    for flag, is_risky in safety_flags.items():
        if flag == "needs_fact_check" and is_risky:
            needed = set(response_plan["campaign_facts_needed"])
            approved = set(case.get("approved_campaign_fact_ids") or [])
            if not needed:
                errors.append("needs_fact_check_without_requested_facts")
            elif needed - approved:
                errors.append(f"needs_fact_check_unapproved_fact_request:{sorted(needed - approved)}")
            elif not draft_product_claim_supported(draft, case):
                errors.append("needs_fact_check_unsupported_draft_claim")
            continue
        if is_risky:
            errors.append(f"safety_flag_block:{flag}")

    for phrase in response_plan["buyer_words_to_preserve"]:
        if should_skip_buyer_word_preservation(phrase, payload, case):
            continue
        if phrase and normalize(phrase) not in normalized_draft:
            errors.append(f"buyer_word_not_preserved:{phrase}")

    for phrase in response_plan["must_not_include"]:
        normalized_phrase = normalize(phrase)
        if normalized_phrase == "team" and "not a team" in normalized_draft:
            continue
        if phrase and normalized_phrase in normalized_draft:
            errors.append(f"must_not_include_present:{phrase}")

    if "voice" in normalized_buyer and "writing" not in normalized_buyer:
        if "writing" in normalized_draft and "voice" not in normalized_draft:
            errors.append("voice_to_writing")

    expected_conjunction = (case.get("expected_semantic_frame") or {}).get("conjunction_relation")
    actual_conjunction = semantic.get("conjunction_relation")
    if expected_conjunction in {"and", "or"} and actual_conjunction != expected_conjunction:
        errors.append(f"conjunction_relation_mismatch:{expected_conjunction}->{actual_conjunction}")
        if expected_conjunction == "and" and actual_conjunction == "or":
            errors.append("and_or_drift")
        if expected_conjunction == "or" and actual_conjunction == "and":
            errors.append("or_and_drift")

    negated_team = any(
        phrase in normalized_buyer
        for phrase in (
            "not a team",
            "no team",
            "by myself",
            "personal use",
            "just me",
            "only me",
        )
    )
    if negated_team:
        if state_update["should_update_team_state"]:
            errors.append("negated_team_state")
        if TEAM_LANGUAGE_RE.search(draft):
            errors.append("negated_team_language")

    next_action_flags = [
        "should_ask_question",
        "should_recommend",
        "should_reframe_objection",
        "should_close",
        "should_disqualify",
    ]
    if sum(1 for flag in next_action_flags if strategy[flag]) > 1:
        errors.append("multiple_next_action_flags")
    one_next_step = normalize(strategy["one_next_step"])
    if not one_next_step:
        errors.append("one_next_step_missing")
    if " and then " in one_next_step or ";" in one_next_step:
        errors.append("one_next_step_contains_multiple_steps")

    max_sentence_count = response_plan["max_sentence_count"]
    if sentence_count(draft) > max_sentence_count:
        errors.append(f"voice_length_sentence_count:{sentence_count(draft)}>{max_sentence_count}")
    if len(draft.split()) > 70:
        errors.append("voice_length_word_count")

    combined_text = "\n".join([draft, *payload["reasons"], *response_plan["must_include"]])
    if RAW_URL_RE.search(combined_text):
        errors.append("raw_url")
    if INTERNAL_POLICY_RE.search(combined_text):
        errors.append("internal_policy_language")
    if SIDE_EFFECT_RE.search(combined_text):
        errors.append("side_effect_claim")
    if AFFILIATION_RE.search(combined_text):
        errors.append("affiliation_claim")
    if CAMPAIGN_LEAKAGE_RE.search(combined_text):
        errors.append("campaign_leakage")
    if UNSUPPORTED_FACT_RE.search(combined_text):
        errors.append("unsupported_product_claim")
    if draft_has_factual_product_claim(draft) and not draft_product_claim_supported(draft, case):
        errors.append("unsupported_product_claim_without_approved_fact")

    if "approved_campaign_fact_ids" in case:
        approved = set(case.get("approved_campaign_fact_ids") or [])
        needed = set(response_plan["campaign_facts_needed"])
        unsupported_needed = sorted(needed - approved)
        if unsupported_needed:
            errors.append(f"campaign_fact_not_approved:{unsupported_needed}")

    return errors
