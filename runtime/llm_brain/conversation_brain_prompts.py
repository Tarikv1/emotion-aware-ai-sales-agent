from __future__ import annotations

import json
from typing import Any

from runtime.llm_brain.conversation_brain_schema import (
    ACTIVE_MODEL_COMPARISON_THIS_PHASE,
    COMPACT_PLANNER_SCHEMA_MODE,
    FULL_PLANNER_SCHEMA_MODE,
    PRIMARY_MODEL_ID,
    REQUIRED_COMPACT_PLANNER_FIELDS,
    REQUIRED_RESPONSE_PLAN_FIELDS,
    REQUIRED_SAFETY_FLAG_FIELDS,
    REQUIRED_SALES_STRATEGY_FIELDS,
    REQUIRED_SEMANTIC_FRAME_FIELDS,
    REQUIRED_STATE_UPDATE_FIELDS,
    REQUIRED_TOP_LEVEL_FIELDS,
)


SYSTEM_PROMPT = """You are a local-only sales conversation brain.
Return strict JSON only.
You do not own product truth, campaign facts, pricing, source claims, side effects, email, calendar, CRM, TTS, or ASR.
Preserve the buyer's current words, conjunctions, and negation.
If product facts are needed, request campaign fact IDs instead of inventing claims.
Do not write internal policy language in draft_response."""


ARCHITECTURE_TARGET = (
    "ASR transcript -> transcript normalization -> local LLM conversation brain -> "
    "structured semantic/sales frame -> deterministic verifier -> campaign fact/source-bundle lookup -> "
    "controlled spoken response -> TTS"
)


def conversation_brain_key_spellings_prompt() -> str:
    sections = {
        "top_level": REQUIRED_TOP_LEVEL_FIELDS,
        "semantic_frame": REQUIRED_SEMANTIC_FRAME_FIELDS,
        "state_update": REQUIRED_STATE_UPDATE_FIELDS,
        "sales_strategy": REQUIRED_SALES_STRATEGY_FIELDS,
        "response_plan": REQUIRED_RESPONSE_PLAN_FIELDS,
        "safety_flags": REQUIRED_SAFETY_FLAG_FIELDS,
    }
    return "\n".join(f"- {section}: {', '.join(fields)}" for section, fields in sections.items())


def compact_conversation_brain_key_spellings_prompt() -> str:
    return ", ".join(REQUIRED_COMPACT_PLANNER_FIELDS)


def full_valid_json_example() -> str:
    example = {
        "semantic_frame": {field: "<short string>" for field in REQUIRED_SEMANTIC_FRAME_FIELDS},
        "state_update": {
            "should_update_adoption_state": False,
            "should_update_use_case": False,
            "use_case_values": [],
            "should_update_usage_intensity": False,
            "usage_intensity": "<short string>",
            "should_update_team_state": False,
            "should_update_recommendation": False,
            "should_update_close_readiness": False,
            "blocked_updates": [],
            "reason": "<short string>",
        },
        "sales_strategy": {
            "next_action": "<short string>",
            "should_answer_directly": False,
            "should_ask_question": False,
            "should_recommend": False,
            "should_reframe_objection": False,
            "should_close": False,
            "should_disqualify": False,
            "persuasion_strategy": "<short string>",
            "one_next_step": "<short string>",
        },
        "response_plan": {
            "must_include": [],
            "must_not_include": [],
            "campaign_facts_needed": [],
            "buyer_words_to_preserve": [],
            "response_tone": "<short string>",
            "max_sentence_count": 2,
        },
        "draft_response": "<one or two short spoken sentences>",
        "safety_flags": {field: False for field in REQUIRED_SAFETY_FLAG_FIELDS},
        "confidence": 0.5,
        "reasons": ["<short reason>"],
    }
    example["semantic_frame"].update(
        {
            "semantic_family": "use_case_scope",
            "speech_act": "use_case_statement",
            "sub_intent": "workflow_need",
            "object_type": "use_case",
            "object_mentions": ["coding workflow", "voice"],
            "conjunction_relation": "and",
            "negation_scope": "none",
            "buyer_state": "evaluating",
            "buyer_emotion_hint": "neutral",
            "commercial_intent": "medium",
            "current_utterance_fidelity_notes": "preserve exact current buyer words",
        }
    )
    example["state_update"].update(
        {
            "should_update_use_case": True,
            "use_case_values": ["coding workflow", "voice"],
            "usage_intensity": "unknown",
            "reason": "buyer named use case scope",
        }
    )
    example["sales_strategy"].update(
        {
            "next_action": "ask_usage_intensity",
            "should_answer_directly": True,
            "should_ask_question": True,
            "persuasion_strategy": "diagnose before recommending",
            "one_next_step": "ask_usage_intensity",
        }
    )
    example["response_plan"].update(
        {
            "must_include": ["coding workflow", "voice"],
            "must_not_include": ["writing"],
            "campaign_facts_needed": ["public_plan_names"],
            "buyer_words_to_preserve": ["coding workflow", "voice"],
            "response_tone": "plain spoken sales; explanation_request can use 2-4 sentences",
            "max_sentence_count": 2,
        }
    )
    example["draft_response"] = "I hear coding workflow and voice. How heavily would you use it?"
    example["confidence"] = 0.82
    example["reasons"] = ["preserves buyer wording", "asks one next step"]
    return json.dumps(example, ensure_ascii=False, separators=(",", ":"))


def compact_valid_json_example() -> str:
    example = {
        "act": "use_case_scope",
        "sub": "coding_voice",
        "obj": ["coding workflow", "voice"],
        "rel": "and",
        "neg": "none",
        "buyer": "evaluating",
        "intent": "evaluation",
        "update": {
            "adoption": "",
            "use": ["coding workflow", "voice"],
            "intensity": "",
            "team": False,
            "recommend": "",
            "close": "",
        },
        "block": [],
        "action": "ask_intensity",
        "strategy": "diagnose_before_recommend",
        "facts": [],
        "preserve": ["coding workflow", "voice"],
        "avoid": ["writing"],
        "say": "Got it - coding workflow and voice. Are you using it lightly, moderately, or heavily?",
        "flags": [],
        "conf": 0.84,
    }
    return json.dumps(example, ensure_ascii=False, separators=(",", ":"))


def _safe_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "normalized_transcript": context.get("normalized_transcript") or "",
        "prior_state": context.get("prior_state") or {},
        "approved_campaign_fact_ids": context.get("approved_campaign_fact_ids") or [],
        "approved_campaign_fact_summaries": context.get("approved_campaign_fact_summaries") or {},
        "smoke_contract": context.get("smoke_contract") or {},
        "last_agent_question": context.get("last_agent_question") or "",
        "campaign_id": context.get("campaign_id") or "",
    }


def render_conversation_brain_prompt(
    context: dict[str, Any],
    *,
    schema_mode: str = FULL_PLANNER_SCHEMA_MODE,
) -> str:
    safe_context = {
        **_safe_context(context),
    }
    if schema_mode == COMPACT_PLANNER_SCHEMA_MODE:
        return "\n".join(
            [
                SYSTEM_PROMPT,
                "",
                "Architecture target:",
                ARCHITECTURE_TARGET,
                "",
                "Primary local model for this phase:",
                PRIMARY_MODEL_ID,
                f"active_model_comparison_this_phase: {str(ACTIVE_MODEL_COMPARISON_THIS_PHASE).lower()}",
                "",
                "Return exactly one compact minified single-line JSON object only. No markdown, prose, labels, nulls, comments, indentation, or extra keys.",
                "Use exactly these compact top-level keys in this order:",
                compact_conversation_brain_key_spellings_prompt(),
                "",
                "Compact valid JSON example, shape only; do not copy values:",
                compact_valid_json_example(),
                "",
                "Compact key meanings:",
                "- act=speech act or semantic family; sub=sub-intent; obj=current buyer objects/words.",
                "- rel preserves and/or/none exactly; neg preserves negation scope.",
                "- buyer=buyer state; intent=commercial intent.",
                "- update.use is current use-case values; update.team must stay false when buyer says by myself/not a team.",
                "- block lists blocked state updates; facts lists approved fact IDs needed before factual claims.",
                "- preserve lists buyer words repeated exactly in say; avoid lists words/claims say must not include.",
                "- flags may include needs_fact_check, unsupported_claim, side_effect, affiliation, internal_policy, raw_url, campaign_leakage.",
                "- say is buyer-facing wording only; no schema/policy language.",
                "",
                "Rules:",
                "- For smoke cases, keep the compact JSON short.",
                "- This compact planner JSON does not globally limit future spoken answers.",
                "- Keep say concise unless buyer asks for explanation, objection handling, or detailed comparison.",
                "- Dynamic say length: direct price/signup short; explanation medium; objection medium; detailed comparison may be longer.",
                "- Preserve current buyer words, AND/OR, and negation; voice remains voice, not writing.",
                "- If buyer says by myself, not a team, no team, personal use, just me, or only me, set neg to team_state; never none.",
                "- preserve is strict: every phrase in preserve must appear in say exactly, not as a paraphrase or changed tense.",
                "- If say uses solo, put preserve []; if preserve includes by myself or not a team, say must include by myself or not a team exactly.",
                "- If preserve includes upgrade later, say must include upgrade later exactly, not upgrading later.",
                "- Do not invent product claims; use only approved fact summaries below.",
                "- If a needed fact is not approved, put the fact ID in facts and avoid the claim in say.",
                "- No fake side effects: do not claim email, calendar, CRM, ticket, or TTS actions happened.",
                "- No internal policy language, raw URLs, affiliation claims, or unsupported guarantees.",
                "- For thanks/check closing turns, do not ask a new question; use a short acceptance close.",
                "- If input context includes smoke_contract, follow it exactly; it is a local verifier hint for this smoke only.",
                "- If smoke_contract.preferred_draft_response exists, use it exactly as say.",
                "- If smoke_contract.buyer_words_to_preserve_allowed exists, preserve only allowed phrases that appear exactly in say.",
                "",
                "Input context:",
                json.dumps(safe_context, ensure_ascii=False, separators=(",", ":")),
            ]
        )

    return "\n".join(
        [
            SYSTEM_PROMPT,
            "",
            "Architecture target:",
            ARCHITECTURE_TARGET,
            "",
            "Primary local model for this phase:",
            PRIMARY_MODEL_ID,
            f"active_model_comparison_this_phase: {str(ACTIVE_MODEL_COMPARISON_THIS_PHASE).lower()}",
            "",
            "Return exactly one minified single-line JSON object only. No markdown, prose, schema labels, nulls, comments, indentation, or extra keys.",
            "Use these exact key spellings:",
            conversation_brain_key_spellings_prompt(),
            "",
            "Compact valid JSON example, shape only; do not copy values:",
            full_valid_json_example(),
            "",
            "Rules:",
            "- Keep planner JSON compact; this does not permanently limit future final spoken responses.",
            "- Do not pretty-print. No newlines. String values should usually be 1-5 words.",
            "- reasons must contain exactly one short string.",
            "- Keep all response_plan arrays to 0-2 items unless the buyer names more plan objects.",
            "- draft_response should be short for smoke, but response_plan may allow longer final spoken responses when buyer need justifies it.",
            "- Array fields must be arrays of strings, never a single string.",
            "- Boolean fields must be true or false, not strings.",
            "- Use only approved fact summaries below. If draft_response uses only those facts, needs_fact_check must be false.",
            "- If a fact is needed but not approved, request it in campaign_facts_needed and avoid the claim in draft_response.",
            "- buyer_words_to_preserve must list only exact buyer words that draft_response repeats exactly. If draft_response will not repeat them, use [].",
            "- Do not paraphrase buyer_words_to_preserve: by myself is not by yourself; not a team is not not on a team.",
            "- For by myself/not a team, either repeat by myself or not a team exactly in draft_response, or set buyer_words_to_preserve to [].",
            "- If draft_response repeats not a team, do not put the bare word team in must_not_include; use your team, team plan, or Business workspace instead.",
            "- For plan menus like Free, Plus, Pro, Business, and Enterprise, use conjunction_relation and, not or.",
            "- max_sentence_count must be greater than or equal to the actual draft_response sentence count.",
            "- For thanks/check closing turns, do not ask a new question; use one short closing sentence and use buyer_words_to_preserve [] unless the sentence repeats check or thanks exactly.",
            "- If input context includes smoke_contract, follow it exactly; it is a local verifier hint for this smoke only.",
            "- Set max_sentence_count by buyer need: direct_price_question/signup-close 1-2; explanation_request 2-4; plan comparison or objection handling 3-5 if detail is requested; source/affiliation 1-3; confused buyer short answer first plus one optional follow-up.",
            "- If the schema cannot express response-length nuance, put it in response_tone or sales_strategy.one_next_step.",
            "",
            "Common mistakes to avoid:",
            "- should_reframe_objction is invalid; use should_reframe_objection.",
            "- Preserve voice as voice, not writing.",
            "- Preserve and vs or.",
            "- Do not set needs_fact_check=true when using only approved facts.",
            "- Do not invent unsupported product claims.",
            "- For by myself/not a team, keep should_update_team_state false and avoid team language.",
            "",
            "Input context:",
            json.dumps(safe_context, ensure_ascii=False, separators=(",", ":")),
        ]
    )
