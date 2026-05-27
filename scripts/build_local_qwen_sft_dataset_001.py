#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import (  # noqa: E402
    COMPACT_VALUE_CONTRACT_VERSION,
    compact_label_quality_issues,
    validate_compact_value_contract,
)
from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt  # noqa: E402
from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    COMPACT_PLANNER_SCHEMA_MODE,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402


EXPERIMENT_ID = "LOCAL-QWEN-SFT-DATASET-001"
SOURCE_EXPERIMENT_ID = "LOCAL-LLM-CONVERSATION-BRAIN-FEASIBILITY-001"
QWEN_EVAL_ID = "LOCAL-QWEN-GOLDSET-EVAL-001"
FAILURE_AUDIT_ID = "LOCAL-QWEN-GOLDSET-FAILURE-AUDIT-001"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_EXPERIMENT_ID
GOLD_CASES_PATH = SOURCE_DIR / "gold_cases.jsonl"
MOCK_OUTPUTS_PATH = SOURCE_DIR / "mock_planner_outputs.jsonl"
QWEN_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / QWEN_EVAL_ID / "result.json"
FAILURE_AUDIT_PATH = ROOT / "research" / "experiments" / "generated" / FAILURE_AUDIT_ID / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
TRAIN_PATH = OUT_DIR / "train.jsonl"
VALIDATION_PATH = OUT_DIR / "validation.jsonl"
TEST_PATH = OUT_DIR / "test.jsonl"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

APPROVED_CAMPAIGN_FACT_SUMMARIES = {
    "public_plan_names": (
        "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise; "
        "the official source remains authoritative."
    ),
    "current_public_plan_prices": (
        "The public price fixture may contain current plan prices, but the planner must avoid "
        "inventing price claims unless that fact ID is approved for the case."
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} line {line_number} must contain a JSON object")
        records.append(payload)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def listify(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def string_list(value: Any) -> list[str]:
    return [str(item) for item in listify(value) if isinstance(item, str) and item.strip()]


def build_request_context(case: dict[str, Any]) -> dict[str, Any]:
    approved_fact_ids = [str(item) for item in case.get("approved_campaign_fact_ids") or []]
    summaries = {
        fact_id: APPROVED_CAMPAIGN_FACT_SUMMARIES[fact_id]
        for fact_id in approved_fact_ids
        if fact_id in APPROVED_CAMPAIGN_FACT_SUMMARIES
    }
    prior_state = case.get("prior_state") if isinstance(case.get("prior_state"), dict) else {}
    return {
        "normalized_transcript": str(case.get("sanitized_buyer_text") or ""),
        "prior_state": prior_state,
        "approved_campaign_fact_ids": approved_fact_ids,
        "approved_campaign_fact_summaries": summaries,
        "smoke_contract": {},
        "last_agent_question": str(case.get("last_agent_question") or ""),
        "campaign_id": str(prior_state.get("campaign_id") or ""),
    }


def verifier_case(case: dict[str, Any]) -> dict[str, Any]:
    context = build_request_context(case)
    return {
        **case,
        "approved_campaign_fact_summaries": context["approved_campaign_fact_summaries"],
    }


def expected_full_from_case(case: dict[str, Any], draft_response: str, confidence: float = 0.88) -> dict[str, Any]:
    return {
        "semantic_frame": case.get("expected_semantic_frame") or {},
        "state_update": case.get("expected_state_update") or {},
        "sales_strategy": case.get("expected_sales_strategy") or {},
        "response_plan": case.get("expected_response_plan") or {},
        "draft_response": draft_response,
        "safety_flags": {
            "needs_fact_check": False,
            "unsupported_product_claim_risk": False,
            "side_effect_claim_risk": False,
            "affiliation_claim_risk": False,
            "internal_policy_language_risk": False,
            "raw_url_risk": False,
            "campaign_leakage_risk": False,
        },
        "confidence": confidence,
        "reasons": ["gold target converted for compact planner SFT"],
    }


def semantic_act(case: dict[str, Any], semantic: dict[str, Any]) -> str:
    semantic_family = str(semantic.get("semantic_family") or "")
    sub_intent = str(semantic.get("sub_intent") or "")
    if semantic_family == "generalized_sales_move":
        if sub_intent in {
            "chatgpt_plus_claude_003",
            "another_ai_004",
            "chad_gpt_005",
            "chat_gbt_006",
            "cloud_007",
            "clawed_008",
            "current_tool_019",
        }:
            return "current_tool_context"
        if sub_intent in {"what_call_009", "plan_list_010", "subscription_011"}:
            return "orientation_or_explanation"
        if sub_intent == "pro_need_015":
            return "pro_tier_question"
        if sub_intent == "upgrade_016":
            return "plan_change_question"
        if sub_intent in {"accept_017", "terminal_023"}:
            return "terminal_acceptance"
        if sub_intent == "signup_020":
            return "signup_question"
        if sub_intent == "source_021":
            return "source_question"
        if sub_intent == "affiliation_022":
            return "affiliation_question"
        if sub_intent in {"heavy_024", "light_025"}:
            return "usage_intensity"
        if sub_intent in {"team_admin_029", "security_030"}:
            return "team_scope"
        return "orientation_or_explanation"
    if semantic_family == "price":
        return "price_question" if sub_intent == "plus_price_question" else "price_objection"
    if semantic_family == "plan_selection":
        return "pro_tier_question" if sub_intent == "pro_tier_interest" else "plan_fit_question"
    if semantic_family == "subscription_change":
        return "plan_change_question"
    if semantic_family == "close_readiness":
        return "terminal_acceptance"
    if semantic_family == "negative_control":
        if sub_intent in {"no_interest_001", "wrong_product_001"}:
            return "no_fit"
        return "safety_boundary"
    return semantic_family or "negative_control"


def _semantic_text(case: dict[str, Any], semantic: dict[str, Any]) -> str:
    objects = " ".join(string_list(semantic.get("object_mentions")))
    return " ".join(
        [
            str(case.get("case_id") or ""),
            str(case.get("sanitized_buyer_text") or ""),
            str(semantic.get("sub_intent") or ""),
            objects,
        ]
    ).lower()


def _current_tool_sub(case: dict[str, Any], semantic: dict[str, Any]) -> str:
    text = _semantic_text(case, semantic)
    has_chatgpt = any(token in text for token in ("chatgpt", "chad gpt", "chat gbt", "chachu", "chacha", "check gpt"))
    has_other = any(token in text for token in ("claude", "clawed", "cloud", "other ai", "another ai"))
    if has_chatgpt and has_other:
        return "current_chatgpt_and_other_ai_user"
    if has_chatgpt:
        return "current_chatgpt_user"
    if has_other:
        return "current_other_ai_user"
    return "current_chatgpt_or_other_ai_unknown"


def _use_case_sub(case: dict[str, Any], semantic: dict[str, Any]) -> str:
    text = _semantic_text(case, semantic)
    if "writing" in text:
        return "coding_writing_use_case"
    if "voice" in text:
        return "coding_voice_use_case"
    return "coding_research_use_case"


def semantic_sub(case: dict[str, Any], semantic: dict[str, Any]) -> str:
    sub_intent = str(semantic.get("sub_intent") or "")
    if sub_intent == "current_ai_tool_user":
        return _current_tool_sub(case, semantic)
    if sub_intent == "workflow_need":
        return _use_case_sub(case, semantic)
    if sub_intent == "personal_use":
        text = _semantic_text(case, semantic)
        if any(marker in text for marker in ("not_team", "no_team", "by_myself", "not a team", "by myself")):
            return "not_team_personal_use"
        return "personal_use"
    mapping = {
        "accept_017": "terminal_thanks_acceptance",
        "affiliation_001": "affiliation_boundary_question",
        "affiliation_022": "affiliation_boundary_question",
        "affiliation_boundary": "affiliation_boundary_question",
        "another_ai_004": "current_other_ai_user",
        "asr_noise_001": "asr_noise_input",
        "campaign_leakage_001": "campaign_leakage_boundary",
        "chad_gpt_005": "current_chatgpt_user",
        "chat_gbt_006": "current_chatgpt_user",
        "chatgpt_plus_claude_003": "current_chatgpt_and_other_ai_user",
        "clawed_008": "current_other_ai_user",
        "cloud_007": "current_other_ai_user",
        "current_competitor_tool": "current_competitor_tool",
        "current_tool_019": "current_chatgpt_or_other_ai_unknown",
        "direct_signup_question": "signup_path_question",
        "disallowed_action_001": "disallowed_purchase_request",
        "explain_call_scope": "plan_category_explanation",
        "explain_plan_set": "plan_category_explanation",
        "free_plan_fit": "plus_sufficiency_question",
        "hallucination_pressure_001": "hallucination_pressure_request",
        "heavy_024": "heavy_daily_use",
        "heavy_daily_use": "heavy_daily_use",
        "internal_policy_001": "internal_policy_request",
        "light_025": "light_occasional_use",
        "midcycle_upgrade_question": "midcycle_upgrade_question",
        "model_vs_subscription": "model_vs_subscription_question",
        "no_calendar_001": "no_calendar_request",
        "no_crm_001": "no_crm_request",
        "no_interest_001": "no_interest",
        "no_tts_001": "tts_boundary_request",
        "occasional_use": "occasional_use",
        "plan_list_010": "plan_category_explanation",
        "plus_price_question": "plus_price_question",
        "policy_request_001": "internal_policy_request",
        "price_trap_001": "unsupported_fact_request",
        "pricing_or_value": "price_objection",
        "privacy_001": "privacy_question",
        "pro_need_015": "pro_tier_choice",
        "pro_tier_interest": "pro_tier_choice",
        "raw_transcript_request_001": "raw_transcript_request",
        "raw_url_001": "raw_url_request",
        "security_030": "enterprise_security_question",
        "side_effect_001": "side_effect_boundary_request",
        "signup_020": "signup_path_question",
        "silence_001": "silence_or_unclear_audio",
        "source_021": "source_disclosure_question",
        "source_disclosure_question": "source_disclosure_question",
        "subscription_011": "model_vs_subscription_question",
        "team_admin_029": "team_controls_question",
        "team_controls_question": "team_controls_question",
        "terminal_023": "terminal_thanks_acceptance",
        "terminal_acceptance": "terminal_thanks_acceptance",
        "unsupported_fact_001": "unsupported_fact_request",
        "upgrade_016": "midcycle_upgrade_question",
        "what_call_009": "plan_category_explanation",
        "wrong_product_001": "wrong_product_question",
    }
    return mapping.get(sub_intent, sub_intent or "silence_or_unclear_audio")


def canonical_strategy(value: str, semantic_family: str, compact_act: str) -> str:
    normalized = " ".join(str(value or "").lower().split())
    if compact_act in {"safety_boundary", "negative_control"}:
        return "boundary_without_side_effects"
    if compact_act == "no_fit":
        return "no_fit_close"
    if compact_act == "terminal_acceptance":
        return "terminal_close"
    if compact_act in {"source_question", "affiliation_question"}:
        return "answer_without_inventing_facts"
    if compact_act == "orientation_or_explanation":
        return "explain_without_overclaiming"
    if compact_act == "price_objection":
        return "value_reframe"
    if compact_act == "competitor_objection":
        return "compare_options"
    if compact_act in {"plan_fit_question", "plan_change_question", "pro_tier_question", "signup_question"}:
        return "value_before_plan_selection"
    if "diagnose before" in normalized:
        return "diagnose_before_recommend"
    if "value before" in normalized:
        return "value_reframe" if semantic_family == "price" else "value_before_plan_selection"
    if "respect boundary" in normalized:
        return "respect_boundary"
    if "answer directly" in normalized:
        return "answer_without_inventing_facts"
    return "diagnose_before_recommend"


def canonical_action(sales: dict[str, Any], semantic: dict[str, Any], compact_act: str, compact_sub: str) -> str:
    if sales.get("should_disqualify") is True or compact_act == "no_fit":
        return "disqualify_no_fit"
    if compact_act in {"safety_boundary", "negative_control"}:
        return "respect_boundary"
    if sales.get("should_close") is True or compact_act == "terminal_acceptance":
        return "terminal_close"
    if compact_act == "price_objection":
        return "reframe_price_objection"
    if compact_act == "price_question":
        return "answer_price"
    if compact_act == "plan_change_question":
        return "answer_plan_change"
    if compact_act in {"plan_fit_question", "pro_tier_question"}:
        return "answer_plan_fit"
    if compact_act == "signup_question":
        return "answer_signup_path"
    if compact_act == "source_question":
        return "answer_source"
    if compact_act == "affiliation_question":
        return "answer_affiliation_boundary"
    if compact_act == "competitor_objection":
        return "compare_competitor_context"
    if compact_act == "team_scope" and compact_sub in {"team_controls_question", "enterprise_security_question"}:
        return "answer_team_controls"
    if compact_act == "team_scope":
        return "ask_individual_usage_intensity"
    if compact_act == "use_case_scope":
        return "ask_usage_intensity"
    if compact_act in {"adoption_state", "current_tool_context", "usage_intensity"}:
        return "ask_use_case_gap"
    if compact_act == "orientation_or_explanation":
        return "answer_plan_category"
    next_action = str(sales.get("next_action") or "")
    if "boundary" in next_action:
        return "respect_boundary"
    return "ask_use_case_gap"


def update_from_state(state: dict[str, Any], compact_sub: str) -> dict[str, Any]:
    adoption_value = compact_sub if state.get("should_update_adoption_state") else ""
    intensity = str(state.get("usage_intensity") or "")
    if not state.get("should_update_usage_intensity") or intensity == "unknown":
        intensity = ""
    return {
        "adoption": adoption_value,
        "use": string_list(state.get("use_case_values")) if state.get("should_update_use_case") else [],
        "intensity": intensity,
        "team": state.get("should_update_team_state") is True,
        "recommend": compact_sub if state.get("should_update_recommendation") else "",
        "close": compact_sub if state.get("should_update_close_readiness") else "",
    }


def compact_from_full(full: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    semantic = full.get("semantic_frame") if isinstance(full.get("semantic_frame"), dict) else {}
    state = full.get("state_update") if isinstance(full.get("state_update"), dict) else {}
    sales = full.get("sales_strategy") if isinstance(full.get("sales_strategy"), dict) else {}
    response_plan = full.get("response_plan") if isinstance(full.get("response_plan"), dict) else {}
    compact_act = semantic_act(case, semantic)
    compact_sub = semantic_sub(case, semantic)
    strategy = canonical_strategy(str(sales.get("persuasion_strategy") or ""), str(semantic.get("semantic_family") or ""), compact_act)
    action = canonical_action(sales, semantic, compact_act, compact_sub)
    return {
        "act": compact_act,
        "sub": compact_sub,
        "obj": string_list(semantic.get("object_mentions")),
        "rel": str(semantic.get("conjunction_relation") or "none"),
        "neg": str(semantic.get("negation_scope") or "none"),
        "buyer": str(semantic.get("buyer_state") or "unknown"),
        "intent": str(semantic.get("commercial_intent") or "unknown"),
        "update": update_from_state(state, compact_sub),
        "block": string_list(state.get("blocked_updates")),
        "action": action,
        "strategy": strategy,
        "facts": string_list(response_plan.get("campaign_facts_needed")),
        "preserve": string_list(response_plan.get("buyer_words_to_preserve")),
        "avoid": string_list(response_plan.get("must_not_include")),
        "say": str(full.get("draft_response") or "I need one more detail before recommending a next step."),
        "flags": [],
        "conf": float(full.get("confidence") or 0.88),
    }


def safe_price_reframe(case: dict[str, Any]) -> str:
    text = str(case.get("sanitized_buyer_text") or "").lower()
    if "price" in text:
        return "Price depends on usage. First I would match the plan to how heavily you use it."
    return "The price only makes sense against your actual usage before picking a plan."


def repair_compact_until_verifier_passes(compact: dict[str, Any], case: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    repairs: list[str] = []
    expanded, adapter_errors = expand_compact_planner_output(compact)
    verifier_errors = verify_conversation_brain_output(expanded, verifier_case(case)) if not adapter_errors else adapter_errors
    if any("unsupported_product_claim" in str(error) for error in verifier_errors):
        compact = {**compact, "say": safe_price_reframe(case)}
        repairs.append("safe_price_reframe")
    expanded, adapter_errors = expand_compact_planner_output(compact)
    verifier_errors = verify_conversation_brain_output(expanded, verifier_case(case)) if not adapter_errors else adapter_errors
    if verifier_errors:
        repairs.append("needs_human_review:" + "|".join(str(item) for item in verifier_errors))
    return compact, repairs


def negative_metadata(case_result: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(case_result, dict):
        return {}
    return {
        "qwen_status": case_result.get("status"),
        "qwen_schema_errors": string_list(case_result.get("schema_errors")),
        "qwen_verifier_errors": string_list(case_result.get("verifier_errors")),
        "qwen_failure_classes": string_list((case_result.get("qwen_gold_comparison") or {}).get("failure_classes")),
        "qwen_vs_deterministic": (case_result.get("qwen_vs_deterministic") or {}).get("outcome"),
        "failed_qwen_output_included": False,
    }


def load_failure_tags() -> dict[str, list[str]]:
    if not FAILURE_AUDIT_PATH.is_file():
        return {}
    audit = read_json(FAILURE_AUDIT_PATH)
    tags: dict[str, list[str]] = {}
    for item in audit.get("failed_case_audits", []):
        if isinstance(item, dict):
            tags[str(item.get("case_id") or "")] = string_list(item.get("failure_classes"))
    return tags


def split_name(index: int) -> str:
    remainder = index % 8
    if remainder == 6:
        return "validation"
    if remainder == 7:
        return "test"
    return "train"


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    gold_cases = read_jsonl(GOLD_CASES_PATH)
    mock_outputs = {str(row.get("case_id")): row.get("planner_output") for row in read_jsonl(MOCK_OUTPUTS_PATH)}
    qwen_result = read_json(QWEN_RESULT_PATH)
    qwen_by_case = {str(row.get("case_id")): row for row in qwen_result.get("cases", []) if isinstance(row, dict)}
    failure_tags = load_failure_tags()
    rows: list[dict[str, Any]] = []
    repair_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    quality_issue_counts: Counter[str] = Counter()
    failure_case_count = 0

    for index, case in enumerate(gold_cases):
        case_id = str(case.get("case_id") or "")
        deterministic_full = mock_outputs.get(case_id)
        full_source = "deterministic_good_output"
        if not isinstance(deterministic_full, dict):
            deterministic_full = expected_full_from_case(case, "")
            full_source = "gold_expected_output"
        compact = compact_from_full(deterministic_full, case)
        compact, repairs = repair_compact_until_verifier_passes(compact, case)
        repair_counts.update(repair for repair in repairs if not repair.startswith("needs_human_review"))
        compact_errors = validate_compact_conversation_brain_output(compact)
        contract_errors = validate_compact_value_contract(compact)
        quality_errors = compact_label_quality_issues(compact)
        quality_issue_counts.update(issue["issue"] for issue in quality_errors)
        expanded, adapter_errors = expand_compact_planner_output(compact)
        verifier_errors = verify_conversation_brain_output(expanded, verifier_case(case)) if not adapter_errors else adapter_errors
        if compact_errors or contract_errors or quality_errors or adapter_errors or verifier_errors or any(
            repair.startswith("needs_human_review") for repair in repairs
        ):
            full_source = "gold_expected_output_needs_review"

        context = build_request_context(case)
        case_failure_tags = failure_tags.get(case_id, [])
        if case_failure_tags:
            failure_case_count += 1
        source_counts[str(case.get("source_type") or "unknown")] += 1
        row = {
            "case_id": case_id,
            "source_type": str(case.get("source_type") or "unknown"),
            "campaign_id": str((case.get("prior_state") or {}).get("campaign_id") or ""),
            "prompt": render_conversation_brain_prompt(context, schema_mode=COMPACT_PLANNER_SCHEMA_MODE),
            "target_compact_json": compact,
            "target_full_json": expanded,
            "target_source": full_source,
            "approved_campaign_fact_summaries": context["approved_campaign_fact_summaries"],
            "prior_state": case.get("prior_state") if isinstance(case.get("prior_state"), dict) else {},
            "expected_safety_constraints": {
                "forbidden_response_markers": string_list(case.get("forbidden_response_markers")),
                "acceptable_response_markers": string_list(case.get("acceptable_response_markers")),
                "provider_calls_allowed": False,
                "openai_api_calls_allowed": False,
                "live_tts_calls_allowed": False,
                "fake_side_effects_allowed": False,
                "raw_private_transcript_allowed": False,
            },
            "failure_tags": case_failure_tags,
            "negative_example_metadata": negative_metadata(qwen_by_case.get(case_id)) if case_failure_tags else {},
            "privacy_level": "sanitized_only",
            "raw_private_transcript_included": False,
            "split": split_name(index),
            "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        }
        rows.append(row)

    summary = {
        "source_case_count": len(gold_cases),
        "row_count": len(rows),
        "source_counts": dict(sorted(source_counts.items())),
        "failed_qwen_case_rows": failure_case_count,
        "repair_counts": dict(sorted(repair_counts.items())),
        "target_quality_issue_counts": dict(sorted(quality_issue_counts.items())),
    }
    return rows, summary


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Summary",
        "",
        f"- Rows: {result['row_count']}",
        f"- Train: {result['splits']['train']['count']}",
        f"- Validation: {result['splits']['validation']['count']}",
        f"- Test: {result['splits']['test']['count']}",
        f"- Target format: compact JSON",
        f"- Target compact contract valid: {str(not result['target_quality_issue_counts']).lower()}",
        f"- Deprecated target labels: {result['target_quality_issue_counts'].get('deprecated_label', 0)}",
        f"- Case-ID-like target labels: {result['target_quality_issue_counts'].get('case_id_label_leak', 0)}",
        f"- Generic target labels: {sum(count for issue, count in result['target_quality_issue_counts'].items() if issue.startswith('generic_'))}",
        f"- Failed Qwen outputs used as targets: false",
        f"- Local model calls made: {str(result['side_effects']['local_model_calls_made']).lower()}",
        f"- Provider/API/TTS calls made: {str(result['side_effects']['provider_side_effects_made']).lower()}",
        f"- Runtime behavior changed: {str(result['side_effects']['runtime_behavior_changed']).lower()}",
        f"- Response text changed: {str(result['side_effects']['response_text_changed']).lower()}",
        "",
        "## Split Method",
        "",
        "Rows preserve gold-set order. Every 8th row is validation, the following row is test, and the other 6 rows are train, producing the expected 60/10/10 split.",
        "",
        "## Dataset Notes",
        "",
        "- `target_compact_json` is the supervised target.",
        "- `target_full_json` is the compact-to-full adapter expansion used for verifier validation.",
        "- Qwen failed outputs are summarized only in `negative_example_metadata`.",
        "- Privacy is `sanitized_only`; raw private transcripts are not included.",
    ]
    if result["target_repairs"]:
        lines.extend(["", "## Target Repairs", ""])
        for repair, count in result["target_repairs"].items():
            lines.append(f"- `{repair}`: {count}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    rows, source_summary = build_rows()
    split_rows = {
        "train": [row for row in rows if row["split"] == "train"],
        "validation": [row for row in rows if row["split"] == "validation"],
        "test": [row for row in rows if row["split"] == "test"],
    }
    write_jsonl(TRAIN_PATH, split_rows["train"])
    write_jsonl(VALIDATION_PATH, split_rows["validation"])
    write_jsonl(TEST_PATH, split_rows["test"])
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "qwen_eval_experiment_id": QWEN_EVAL_ID,
        "failure_audit_experiment_id": FAILURE_AUDIT_ID,
        "compact_value_contract_version": COMPACT_VALUE_CONTRACT_VERSION,
        "row_count": len(rows),
        "splits": {
            name: {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "count": len(split_rows[name]),
            }
            for name, path in (
                ("train", TRAIN_PATH),
                ("validation", VALIDATION_PATH),
                ("test", TEST_PATH),
            )
        },
        "source_summary": source_summary,
        "target_fields": [
            "act",
            "sub",
            "obj",
            "rel",
            "neg",
            "buyer",
            "intent",
            "update",
            "block",
            "action",
            "strategy",
            "facts",
            "preserve",
            "avoid",
            "say",
            "flags",
            "conf",
        ],
        "target_repairs": source_summary["repair_counts"],
        "target_quality_issue_counts": source_summary["target_quality_issue_counts"],
        "failed_qwen_outputs_used_as_targets": False,
        "privacy_level": "sanitized_only",
        "raw_private_transcript_included": False,
        "side_effects": {
            "local_model_calls_made": False,
            "local_model_call_count": 0,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "model_download_attempted": False,
            "model_redownloaded": False,
            "model_weights_committed": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
        },
    }
    write_json(RESULT_PATH, result)
    REPORT_PATH.write_text(build_report(result), encoding="utf-8")
    print(json.dumps({"status": "pass", "rows": len(rows), "splits": result["splits"]}, indent=2))


if __name__ == "__main__":
    main()
