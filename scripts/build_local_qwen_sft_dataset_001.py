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


def canonical_strategy(value: str, semantic_family: str) -> str:
    normalized = " ".join(str(value or "").lower().split())
    if "diagnose before" in normalized:
        return "diagnose_before_recommend"
    if "value before" in normalized:
        return "value_reframe" if semantic_family == "price" else "value_before_plan_selection"
    if "respect boundary" in normalized:
        return "respect_boundary"
    if "answer directly" in normalized:
        return "answer_without_inventing_facts"
    if semantic_family == "close_readiness":
        return "terminal_close"
    if semantic_family == "competitor_objection":
        return "compare_options"
    return "orient"


def canonical_action(sales: dict[str, Any], semantic: dict[str, Any]) -> str:
    next_action = str(sales.get("next_action") or "")
    semantic_family = str(semantic.get("semantic_family") or "")
    sub_intent = str(semantic.get("sub_intent") or "")
    if sales.get("should_disqualify") is True or "no_interest" in sub_intent or "wrong_product" in sub_intent:
        return "disqualify"
    if sales.get("should_close") is True or semantic_family == "close_readiness" or "terminal" in sub_intent:
        return "close"
    if sales.get("should_reframe_objection") is True or "price" in semantic_family or "objection" in next_action:
        return "reframe_objection"
    if sales.get("should_recommend") is True:
        return "recommend"
    if "price" in next_action or "cost" in sub_intent:
        return "answer_price"
    if "upgrade" in next_action or "upgrade" in sub_intent or "subscription" in sub_intent:
        return "answer_plan_change"
    if "compare" in next_action:
        return "answer_plan_fit"
    if sales.get("should_ask_question") is True:
        if "intensity" in next_action or semantic_family == "use_case_scope":
            return "ask_intensity"
        if "use_case" in next_action or semantic_family == "adoption_state":
            return "ask_gap"
        return "clarify"
    if semantic_family in {"orientation_or_explanation", "source_question", "affiliation_question", "signup_question"}:
        return "explain"
    if "boundary" in next_action:
        return "respect_boundary"
    return "clarify"


def update_from_state(state: dict[str, Any], semantic: dict[str, Any]) -> dict[str, Any]:
    adoption_value = str(semantic.get("sub_intent") or "known") if state.get("should_update_adoption_state") else ""
    intensity = str(state.get("usage_intensity") or "")
    if not state.get("should_update_usage_intensity") or intensity == "unknown":
        intensity = ""
    return {
        "adoption": adoption_value,
        "use": string_list(state.get("use_case_values")) if state.get("should_update_use_case") else [],
        "intensity": intensity,
        "team": state.get("should_update_team_state") is True,
        "recommend": str(semantic.get("sub_intent") or "recommend") if state.get("should_update_recommendation") else "",
        "close": str(semantic.get("sub_intent") or "close") if state.get("should_update_close_readiness") else "",
    }


def compact_from_full(full: dict[str, Any]) -> dict[str, Any]:
    semantic = full.get("semantic_frame") if isinstance(full.get("semantic_frame"), dict) else {}
    state = full.get("state_update") if isinstance(full.get("state_update"), dict) else {}
    sales = full.get("sales_strategy") if isinstance(full.get("sales_strategy"), dict) else {}
    response_plan = full.get("response_plan") if isinstance(full.get("response_plan"), dict) else {}
    strategy = canonical_strategy(str(sales.get("persuasion_strategy") or ""), str(semantic.get("semantic_family") or ""))
    action = canonical_action(sales, semantic)
    return {
        "act": str(semantic.get("semantic_family") or "negative_control"),
        "sub": str(semantic.get("sub_intent") or "silence_001"),
        "obj": string_list(semantic.get("object_mentions")),
        "rel": str(semantic.get("conjunction_relation") or "none"),
        "neg": str(semantic.get("negation_scope") or "none"),
        "buyer": str(semantic.get("buyer_state") or "unknown"),
        "intent": str(semantic.get("commercial_intent") or "unknown"),
        "update": update_from_state(state, semantic),
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
    failure_case_count = 0

    for index, case in enumerate(gold_cases):
        case_id = str(case.get("case_id") or "")
        deterministic_full = mock_outputs.get(case_id)
        full_source = "deterministic_good_output"
        if not isinstance(deterministic_full, dict):
            deterministic_full = expected_full_from_case(case, "")
            full_source = "gold_expected_output"
        compact = compact_from_full(deterministic_full)
        compact, repairs = repair_compact_until_verifier_passes(compact, case)
        repair_counts.update(repair for repair in repairs if not repair.startswith("needs_human_review"))
        compact_errors = validate_compact_conversation_brain_output(compact)
        contract_errors = validate_compact_value_contract(compact)
        expanded, adapter_errors = expand_compact_planner_output(compact)
        verifier_errors = verify_conversation_brain_output(expanded, verifier_case(case)) if not adapter_errors else adapter_errors
        if compact_errors or contract_errors or adapter_errors or verifier_errors or any(
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
