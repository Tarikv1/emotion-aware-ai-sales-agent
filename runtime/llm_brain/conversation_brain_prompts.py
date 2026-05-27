from __future__ import annotations

import json
from typing import Any

from runtime.llm_brain.conversation_brain_schema import (
    ACTIVE_MODEL_COMPARISON_THIS_PHASE,
    PRIMARY_MODEL_ID,
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


def conversation_brain_schema_prompt() -> str:
    schema = {
        "top_level": list(REQUIRED_TOP_LEVEL_FIELDS),
        "semantic_frame": list(REQUIRED_SEMANTIC_FRAME_FIELDS),
        "state_update": list(REQUIRED_STATE_UPDATE_FIELDS),
        "sales_strategy": list(REQUIRED_SALES_STRATEGY_FIELDS),
        "response_plan": list(REQUIRED_RESPONSE_PLAN_FIELDS),
        "safety_flags": list(REQUIRED_SAFETY_FLAG_FIELDS),
    }
    return json.dumps(schema, indent=2, ensure_ascii=False)


def render_conversation_brain_prompt(context: dict[str, Any]) -> str:
    safe_context = {
        "normalized_transcript": context.get("normalized_transcript") or "",
        "prior_state": context.get("prior_state") or {},
        "approved_campaign_fact_ids": context.get("approved_campaign_fact_ids") or [],
        "last_agent_question": context.get("last_agent_question") or "",
        "campaign_id": context.get("campaign_id") or "",
    }
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
            "Required output schema:",
            conversation_brain_schema_prompt(),
            "",
            "Input context:",
            json.dumps(safe_context, indent=2, ensure_ascii=False),
        ]
    )
