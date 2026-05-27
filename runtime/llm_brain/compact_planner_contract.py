from __future__ import annotations

import re
from typing import Any


"""Compact planner value contract for local Qwen SFT targets.

This contract is for training-data normalization only. It does not enable the
local LLM at runtime, change dialogue routing, or replace deterministic
response text. The goal is to keep compact planner targets short, consistent,
semantic, and verifier-compatible before any later fine-tuning phase.
"""


COMPACT_VALUE_CONTRACT_VERSION = "LOCAL-QWEN-COMPACT-PLANNER-CONTRACT-002"

DEPRECATED_COMPACT_ACT_VALUES: tuple[str, ...] = (
    "close_readiness",
    "generalized_sales_move",
    "plan_selection",
    "price",
    "subscription_change",
)

DEPRECATED_COMPACT_SUB_VALUES: tuple[str, ...] = (
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
    "current_tool_019",
    "direct_signup_question",
    "disallowed_action_001",
    "explain_call_scope",
    "explain_plan_set",
    "free_plan_fit",
    "hallucination_pressure_001",
    "heavy_024",
    "internal_policy_001",
    "light_025",
    "model_vs_subscription",
    "no_calendar_001",
    "no_crm_001",
    "no_interest_001",
    "no_tts_001",
    "plan_list_010",
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
    "subscription_011",
    "team_admin_029",
    "terminal_023",
    "terminal_acceptance",
    "unsupported_fact_001",
    "upgrade_016",
    "what_call_009",
    "workflow_need",
    "wrong_product_001",
)

DEPRECATED_COMPACT_ACTION_VALUES: tuple[str, ...] = (
    "answer_or_ask_one_next_step",
    "answer_scope_then_ask_fit",
    "answer_then_next_step",
    "ask_gap",
    "ask_intensity",
    "ask_use_case",
    "clarify",
    "close",
    "disqualify",
    "explain",
    "recommend",
    "reframe_objection",
)

DEPRECATED_COMPACT_STRATEGY_VALUES: tuple[str, ...] = ("orient",)

CASE_ID_LIKE_LABEL_RE = re.compile(r"(?:^|_)(?:live|paraphrase|negative)_[a-z0-9_]*_\d{3}$|_\d{3}$", re.I)
GENERIC_ACTION_VALUES: tuple[str, ...] = DEPRECATED_COMPACT_ACTION_VALUES
GENERIC_SUB_INTENT_VALUES: tuple[str, ...] = (
    "current_ai_tool_user",
    "pricing_or_value",
    "workflow_need",
)
OVERLY_GENERIC_ACT_VALUES: tuple[str, ...] = ("generalized_sales_move",)

DEPRECATED_COMPACT_LABELS_BY_FIELD: dict[str, tuple[str, ...]] = {
    "act": DEPRECATED_COMPACT_ACT_VALUES,
    "sub": DEPRECATED_COMPACT_SUB_VALUES,
    "action": DEPRECATED_COMPACT_ACTION_VALUES,
    "strategy": DEPRECATED_COMPACT_STRATEGY_VALUES,
}

ALLOWED_COMPACT_VALUES: dict[str, tuple[str, ...]] = {
    "act": (
        "adoption_state",
        "affiliation_question",
        "competitor_objection",
        "current_tool_context",
        "negative_control",
        "no_fit",
        "orientation_or_explanation",
        "plan_change_question",
        "plan_fit_question",
        "price_objection",
        "price_question",
        "pro_tier_question",
        "safety_boundary",
        "signup_question",
        "source_question",
        "team_scope",
        "terminal_acceptance",
        "usage_intensity",
        "use_case_scope",
    ),
    "sub": (
        "affiliation_boundary_question",
        "asr_noise_input",
        "campaign_leakage_boundary",
        "coding_research_use_case",
        "coding_voice_use_case",
        "coding_writing_use_case",
        "current_chatgpt_and_other_ai_user",
        "current_chatgpt_or_other_ai_unknown",
        "current_chatgpt_user",
        "current_competitor_tool",
        "current_other_ai_user",
        "disallowed_purchase_request",
        "enterprise_security_question",
        "hallucination_pressure_request",
        "heavy_daily_use",
        "internal_policy_request",
        "light_occasional_use",
        "midcycle_upgrade_question",
        "model_vs_subscription_question",
        "no_calendar_request",
        "no_crm_request",
        "no_interest",
        "not_team_personal_use",
        "occasional_use",
        "personal_use",
        "plan_category_explanation",
        "plus_price_question",
        "plus_sufficiency_question",
        "price_objection",
        "privacy_question",
        "pro_tier_choice",
        "raw_transcript_request",
        "raw_url_request",
        "side_effect_boundary_request",
        "signup_path_question",
        "silence_or_unclear_audio",
        "source_disclosure_question",
        "team_controls_question",
        "terminal_thanks_acceptance",
        "tts_boundary_request",
        "unsupported_fact_request",
        "wrong_product_question",
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
        "answer_affiliation_boundary",
        "answer_plan_category",
        "answer_plan_change",
        "answer_plan_fit",
        "answer_price",
        "answer_signup_path",
        "answer_source",
        "answer_team_controls",
        "answer_without_inventing_facts",
        "ask_individual_usage_intensity",
        "ask_usage_intensity",
        "ask_use_case_gap",
        "compare_competitor_context",
        "disqualify_no_fit",
        "recommend_plan",
        "reframe_price_objection",
        "respect_boundary",
        "terminal_close",
    ),
    "strategy": (
        "answer_without_inventing_facts",
        "boundary_without_side_effects",
        "choice_close",
        "compare_options",
        "diagnose_before_recommend",
        "explain_without_overclaiming",
        "no_fit_close",
        "preserve_buyer_words",
        "respect_boundary",
        "terminal_close",
        "value_before_plan_selection",
        "value_reframe",
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


def allowed_values_for(field_name: str) -> tuple[str, ...]:
    return ALLOWED_COMPACT_VALUES.get(field_name, ())


def is_case_id_like_label(value: Any) -> bool:
    return isinstance(value, str) and bool(CASE_ID_LIKE_LABEL_RE.search(value.strip()))


def compact_label_quality_issues(payload: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field_name in ("act", "sub", "action", "strategy"):
        value = payload.get(field_name)
        if not isinstance(value, str):
            continue
        allowed = set(allowed_values_for(field_name))
        if value not in allowed:
            issues.append({"field": field_name, "value": value, "issue": "not_allowed"})
        if value in DEPRECATED_COMPACT_LABELS_BY_FIELD.get(field_name, ()):
            issues.append({"field": field_name, "value": value, "issue": "deprecated_label"})
        if is_case_id_like_label(value):
            issues.append({"field": field_name, "value": value, "issue": "case_id_label_leak"})
        if field_name == "act" and value in OVERLY_GENERIC_ACT_VALUES:
            issues.append({"field": field_name, "value": value, "issue": "generic_act"})
        if field_name == "sub" and value in GENERIC_SUB_INTENT_VALUES:
            issues.append({"field": field_name, "value": value, "issue": "generic_sub_intent"})
        if field_name == "action" and value in GENERIC_ACTION_VALUES:
            issues.append({"field": field_name, "value": value, "issue": "generic_action"})
        if field_name == "strategy" and value in DEPRECATED_COMPACT_STRATEGY_VALUES:
            issues.append({"field": field_name, "value": value, "issue": "generic_strategy"})
    return issues


def compact_contract_valid(payload: dict[str, Any]) -> bool:
    return not validate_compact_value_contract(payload)


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
    for issue in compact_label_quality_issues(payload):
        if issue["issue"] == "not_allowed":
            continue
        errors.append(f"compact.{issue['field']} {issue['issue']}: {issue['value']!r}")
    return errors
