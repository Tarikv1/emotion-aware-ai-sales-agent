from __future__ import annotations

from typing import Any


"""Compact planner value contract for local Qwen SFT targets.

This contract is for training-data normalization only. It does not enable the
local LLM at runtime, change dialogue routing, or replace deterministic
response text. The goal is to keep compact planner targets short, consistent,
and verifier-compatible before any later fine-tuning phase.
"""


ALLOWED_COMPACT_VALUES: dict[str, tuple[str, ...]] = {
    "act": (
        "adoption_state",
        "affiliation_question",
        "close_readiness",
        "competitor_objection",
        "generalized_sales_move",
        "negative_control",
        "orientation_or_explanation",
        "plan_selection",
        "price",
        "signup_question",
        "source_question",
        "subscription_change",
        "team_scope",
        "usage_intensity",
        "use_case_scope",
    ),
    "sub": (
        "accept_017",
        "affiliation_001",
        "affiliation_022",
        "affiliation_boundary",
        "another_ai_004",
        "asr_noise_001",
        "campaign_leakage_001",
        "chad_gpt_005",
        "chat_gbt_006",
        "chatgpt_plus_claude_003",
        "clawed_008",
        "cloud_007",
        "current_ai_tool_user",
        "current_competitor_tool",
        "current_tool_019",
        "direct_signup_question",
        "disallowed_action_001",
        "explain_call_scope",
        "explain_plan_set",
        "free_plan_fit",
        "hallucination_pressure_001",
        "heavy_024",
        "heavy_daily_use",
        "internal_policy_001",
        "light_025",
        "midcycle_upgrade_question",
        "model_vs_subscription",
        "no_calendar_001",
        "no_crm_001",
        "no_interest_001",
        "no_tts_001",
        "occasional_use",
        "personal_use",
        "plan_list_010",
        "plus_price_question",
        "policy_request_001",
        "price_trap_001",
        "pricing_or_value",
        "privacy_001",
        "pro_need_015",
        "pro_tier_interest",
        "raw_transcript_request_001",
        "raw_url_001",
        "security_030",
        "side_effect_001",
        "signup_020",
        "silence_001",
        "source_021",
        "source_disclosure_question",
        "subscription_011",
        "team_admin_029",
        "team_controls_question",
        "terminal_023",
        "terminal_acceptance",
        "unsupported_fact_001",
        "upgrade_016",
        "what_call_009",
        "workflow_need",
        "wrong_product_001",
    ),
    "rel": ("and", "or", "both", "unknown", "none"),
    "neg": ("team_state", "unknown", "none"),
    "buyer": (
        "evaluating",
        "high_usage",
        "individual_user",
        "light_usage",
        "price_sensitive",
        "skeptical",
        "confused",
        "not_interested",
        "unknown",
    ),
    "intent": ("high", "medium", "low", "evaluation", "information", "boundary", "unknown", "none"),
    "action": (
        "explain",
        "ask_gap",
        "ask_use_case",
        "ask_intensity",
        "answer_price",
        "answer_plan_fit",
        "answer_plan_change",
        "recommend",
        "reframe_objection",
        "close",
        "disqualify",
        "clarify",
        "answer_or_ask_one_next_step",
        "answer_scope_then_ask_fit",
        "answer_then_next_step",
        "ask_individual_usage_intensity",
        "ask_usage_intensity",
        "ask_use_case_gap",
        "avoid_over_recommending_pro",
        "compare_plus_vs_pro",
        "respect_boundary",
    ),
    "strategy": (
        "orient",
        "diagnose_before_recommend",
        "preserve_buyer_words",
        "compare_options",
        "value_reframe",
        "choice_close",
        "no_fit_close",
        "terminal_close",
        "answer_without_inventing_facts",
        "respect_boundary",
        "value_before_plan_selection",
    ),
    "flags": (
        "needs_fact_check",
        "unsupported_claim",
        "unsupported_product_claim",
        "unsupported_product_claim_risk",
        "side_effect",
        "side_effect_claim_risk",
        "affiliation",
        "affiliation_claim_risk",
        "internal_policy",
        "internal_policy_language_risk",
        "raw_url",
        "raw_url_risk",
        "campaign_leakage",
        "campaign_leakage_risk",
    ),
}


COMPACT_VALUE_CONTRACT_VERSION = "LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-001"


def allowed_values_for(field_name: str) -> tuple[str, ...]:
    return ALLOWED_COMPACT_VALUES.get(field_name, ())


def validate_compact_value_contract(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field_name in ("act", "sub", "rel", "neg", "buyer", "intent", "action", "strategy"):
        value = payload.get(field_name)
        allowed = set(allowed_values_for(field_name))
        if isinstance(value, str) and value not in allowed:
            errors.append(f"compact.{field_name} value not allowed: {value!r}")
    flags = payload.get("flags")
    allowed_flags = set(allowed_values_for("flags"))
    if isinstance(flags, list):
        for flag in flags:
            if isinstance(flag, str) and flag not in allowed_flags:
                errors.append(f"compact.flags value not allowed: {flag!r}")
    return errors
