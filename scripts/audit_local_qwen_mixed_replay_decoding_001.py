#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.compact_planner_contract import allowed_values_for  # noqa: E402
from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    audit_side_effects,
    eval_failed,
    read_json,
    rel,
    report_json_block,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-DECODING-AUDIT-001"
DECISION_ID = "LOCAL-QWEN-MIXED-REPLAY-NEXT-DECISION-001"
EVAL_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001"
FAILURE_AUDIT_ID = "LOCAL-QWEN-MIXED-REPLAY-EVAL-FAILURE-AUDIT-001"
TRAIN_VS_EVAL_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAIN-VS-EVAL-AUDIT-001"
EVAL_RESULT_PATH = GENERATED_DIR / EVAL_ID / "result.json"
FAILURE_AUDIT_PATH = GENERATED_DIR / FAILURE_AUDIT_ID / "result.json"
TRAIN_VS_EVAL_PATH = GENERATED_DIR / TRAIN_VS_EVAL_ID / "result.json"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DECISION_DIR = GENERATED_DIR / DECISION_ID
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"
AUDIT_SPLITS = ("validation", "test", "ood_test")


def eval_cases(result: dict[str, Any]) -> list[dict[str, Any]]:
    adapter = result.get("mixed_replay_adapter") if isinstance(result.get("mixed_replay_adapter"), dict) else {}
    splits = adapter.get("splits") if isinstance(adapter.get("splits"), dict) else {}
    cases: list[dict[str, Any]] = []
    for split in AUDIT_SPLITS:
        payload = splits.get(split) if isinstance(splits.get(split), dict) else {}
        for case in payload.get("cases") or []:
            if isinstance(case, dict):
                cases.append(case)
    return cases


def latency(case: dict[str, Any]) -> dict[str, Any]:
    return case.get("latency_metrics") if isinstance(case.get("latency_metrics"), dict) else {}


def complete_stop(case: dict[str, Any]) -> bool:
    data = latency(case)
    return data.get("completed_json_object") is True and data.get("stopped_after_first_json_object") is True


def invalid_field_from_error(error: str) -> tuple[str, str] | None:
    match = re.search(r"compact\.([a-z_]+) value not allowed: '([^']+)'", error)
    if match:
        return match.group(1), match.group(2)
    match = re.search(r"^([a-z_]+):not_allowed:([^ ]+)", error)
    if match:
        return match.group(1), match.group(2)
    return None


def compact_contract_failure_fields(case: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for error in case.get("compact_contract_errors") or []:
        text = str(error)
        field = invalid_field_from_error(text)
        if field:
            fields.append(field[0])
            continue
        match = re.search(r"compact\.([a-z_]+)", text)
        if match:
            fields.append(match.group(1))
    return fields


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def build_decoding_audit() -> dict[str, Any]:
    eval_result = read_json(EVAL_RESULT_PATH)
    cases = eval_cases(eval_result)
    failed = [case for case in cases if eval_failed(case)]
    passed = [case for case in cases if not eval_failed(case)]
    contract_field_counter: Counter[str] = Counter()
    invalid_label_counter: Counter[tuple[str, str]] = Counter()
    for case in cases:
        for field in compact_contract_failure_fields(case):
            contract_field_counter[field] += 1
        for error in case.get("compact_contract_errors") or []:
            parsed = invalid_field_from_error(str(error))
            if parsed:
                invalid_label_counter[parsed] += 1

    malformed = [case for case in cases if case.get("malformed_output") is True]
    incomplete_json = [
        case
        for case in cases
        if any("incomplete or invalid" in str(error).lower() for error in case.get("parse_errors") or [])
        or (case.get("malformed_output") is True and not complete_stop(case))
    ]
    extra_text = [
        case
        for case in cases
        if any("extra" in str(error).lower() or "trailing" in str(error).lower() for error in case.get("parse_errors") or [])
    ]
    truncated = [
        case
        for case in cases
        if latency(case).get("output_truncated") is True
        or (
            latency(case).get("tokens_generated") is not None
            and latency(case).get("max_output_tokens") is not None
            and int(latency(case).get("tokens_generated") or 0) >= int(latency(case).get("max_output_tokens") or 0)
            and complete_stop(case) is False
        )
    ]
    timed_out = [case for case in cases if latency(case).get("timed_out") is True]
    failed_tokens = [
        float(latency(case).get("tokens_generated"))
        for case in failed
        if latency(case).get("tokens_generated") is not None
    ]
    passed_tokens = [
        float(latency(case).get("tokens_generated"))
        for case in passed
        if latency(case).get("tokens_generated") is not None
    ]
    complete_stop_count = sum(1 for case in cases if complete_stop(case))
    format_failure_case_ids = {
        str(case.get("case_id") or "")
        for case in cases
        if case.get("schema_valid") is not True
        or case.get("compact_contract_valid") is not True
        or case.get("malformed_output") is True
    }
    semantic_failure_case_ids = {
        str(case.get("case_id") or "")
        for case in cases
        if case.get("strict_gold_semantic_match") is not True
        or case.get("strict_gold_response_plan_match") is not True
        or case.get("equivalence_match") is not True
    }
    invalid_label_records = [
        {
            "field": field,
            "value": value,
            "count": count,
            "allowed_values_sample": list(allowed_values_for(field))[:20] if field in {"act", "sub", "action", "strategy"} else [],
        }
        for (field, value), count in invalid_label_counter.most_common()
    ]
    constrained_fixable_count = len(format_failure_case_ids)
    constrained_fixable_fraction_of_failed = round(constrained_fixable_count / len(failed), 4) if failed else 0
    mostly_semantic = len(semantic_failure_case_ids) > len(format_failure_case_ids) * 3
    constrained_decoding_would_fix_large_percentage = constrained_fixable_fraction_of_failed >= 0.35

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {"eval_result": rel(EVAL_RESULT_PATH)},
        "case_count": len(cases),
        "failed_case_count": len(failed),
        "malformed_output_count": len(malformed),
        "incomplete_json_count": len(incomplete_json),
        "extra_text_outside_json_count": len(extra_text),
        "invalid_compact_field_count": sum(contract_field_counter.values()),
        "compact_contract_failures_by_field": dict(sorted(contract_field_counter.items())),
        "max_output_token_truncation_count": len(truncated),
        "timeout_count": len(timed_out),
        "first_complete_json_stop_behavior": {
            "completed_and_stopped_after_first_json_count": complete_stop_count,
            "case_count": len(cases),
            "rate": round(complete_stop_count / len(cases), 4) if cases else 0,
            "non_stop_case_ids": [str(case.get("case_id") or "") for case in cases if not complete_stop(case)][:30],
        },
        "average_generated_tokens": {
            "full_pass": average(passed_tokens),
            "failed": average(failed_tokens),
        },
        "format_failure_case_count": len(format_failure_case_ids),
        "semantic_failure_case_count": len(semantic_failure_case_ids),
        "failures_are_mostly_semantic_not_formatting": mostly_semantic,
        "invalid_label_values": invalid_label_records,
        "constrained_decoding_or_label_normalization": {
            "estimated_fixable_case_count": constrained_fixable_count,
            "estimated_fixable_fraction_of_failed": constrained_fixable_fraction_of_failed,
            "would_fix_large_percentage": constrained_decoding_would_fix_large_percentage,
            "interpretation": "Constrained decoding would remove malformed/invalid-label cases, but the dominant failure mass is semantic and response-plan selection.",
        },
        "side_effects": audit_side_effects(),
        "local_model_calls_made": False,
        "training_rerun": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "adapter_live_ready": False,
        "live_wiring_allowed": False,
        "raw_private_transcript_copied_to_public_evidence": False,
    }


def option_scores(failure_audit: dict[str, Any], train_vs_eval: dict[str, Any], decoding: dict[str, Any]) -> dict[str, int]:
    class_counts = failure_audit.get("failure_counts_by_class") if isinstance(failure_audit.get("failure_counts_by_class"), dict) else {}
    tv_class = train_vs_eval.get("classification") if isinstance(train_vs_eval.get("classification"), dict) else {}
    return {
        "option_1_more_data": 6 if tv_class.get("label_sparsity") else 2,
        "option_2_label_simplification": int(class_counts.get("wrong_sub", 0) or 0)
        + int(class_counts.get("wrong_action", 0) or 0)
        + int(class_counts.get("wrong_strategy", 0) or 0),
        "option_3_constrained_decoding": int(decoding.get("format_failure_case_count") or 0),
        "option_4_two_head_architecture": int(class_counts.get("wrong_action", 0) or 0)
        + int(class_counts.get("wrong_strategy", 0) or 0)
        + int(class_counts.get("wrong_sales_move", 0) or 0)
        + int(class_counts.get("training_signal_issue", 0) or 0),
        "option_5_retrieval_example_conditioning": 10 if tv_class.get("label_sparsity") else 4,
        "option_6_smaller_task_for_lora": int(class_counts.get("wrong_say", 0) or 0)
        + int(class_counts.get("response_plan_failure", 0) or 0),
        "option_7_different_base_model_comparison": 3,
    }


def build_next_decision(decoding: dict[str, Any]) -> dict[str, Any]:
    failure_audit = read_json(FAILURE_AUDIT_PATH)
    train_vs_eval = read_json(TRAIN_VS_EVAL_PATH)
    class_counts = failure_audit.get("failure_counts_by_class") if isinstance(failure_audit.get("failure_counts_by_class"), dict) else {}
    train_class = train_vs_eval.get("classification") if isinstance(train_vs_eval.get("classification"), dict) else {}
    scores = option_scores(failure_audit, train_vs_eval, decoding)
    recommended_options = [
        "option_4_two_head_architecture",
        "option_2_label_simplification",
        "option_6_smaller_task_for_lora",
        "option_3_constrained_decoding",
    ]
    rejected = {
        "option_1_more_data": "Not the immediate next step: train_sample is better than held-out, but represented target cards still fail and train response-plan exactness is weak.",
        "option_5_retrieval_example_conditioning": "Useful later as an offline ablation, but it does not address structured-label brittleness by itself.",
        "option_7_different_base_model_comparison": "Premature before reducing task shape; a different base could mask the architecture issue without proving it.",
    }
    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "failure_audit": rel(FAILURE_AUDIT_PATH),
            "train_vs_eval_audit": rel(TRAIN_VS_EVAL_PATH),
            "decoding_audit": rel(RESULT_PATH),
        },
        "recommended_next_option": "option_4_two_head_architecture",
        "recommended_options": recommended_options,
        "option_scores": scores,
        "rationale": {
            "dominant_blocker": "Structured semantic and response-plan selection, not pure JSON formatting.",
            "evidence": {
                "strict_semantic_failures": class_counts.get("strict_semantic_failure"),
                "response_plan_failures": class_counts.get("response_plan_failure"),
                "wrong_action": class_counts.get("wrong_action"),
                "wrong_strategy": class_counts.get("wrong_strategy"),
                "wrong_sales_move": class_counts.get("wrong_sales_move"),
                "format_failure_case_count": decoding.get("format_failure_case_count"),
                "semantic_failure_case_count": decoding.get("semantic_failure_case_count"),
                "train_sample_much_better_than_heldout": (train_vs_eval.get("train_sample_vs_heldout") or {}).get("train_sample_much_better_than_heldout"),
                "train_underfitting_response_plan": train_class.get("underfitting"),
            },
        },
        "rejected_options": rejected,
        "more_training_recommended_immediately": False,
        "data_expansion_recommended": False,
        "data_expansion_recommendation": "Do not expand to 1000-2000 rows yet; first simplify the target and decide which head owns labels.",
        "label_simplification_recommended": True,
        "constrained_decoding_recommended": True,
        "constrained_decoding_scope": "Secondary guardrail for invalid labels/schema drift, not the main quality fix.",
        "two_head_architecture_recommended": True,
        "retrieval_example_conditioning_recommended": "defer",
        "different_base_model_comparison_recommended": "defer",
        "local_lora_scope_recommended": "Train local LLM only for buyer-facing say/objection wording after deterministic labels are stable.",
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "quality_gate_passed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "provider_side_effects_made": False,
        "local_model_calls_made": False,
        "training_rerun": False,
        "recommendation_does_not_claim_live_readiness": True,
        "side_effects": audit_side_effects(),
    }


def write_decoding_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Summary",
        "",
        f"- status: {result['status']}",
        f"- case_count: {result['case_count']}",
        f"- failed_case_count: {result['failed_case_count']}",
        f"- malformed_output_count: {result['malformed_output_count']}",
        f"- incomplete_json_count: {result['incomplete_json_count']}",
        f"- invalid_compact_field_count: {result['invalid_compact_field_count']}",
        f"- failures_are_mostly_semantic_not_formatting: {str(result['failures_are_mostly_semantic_not_formatting']).lower()}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- training_rerun: {str(result['training_rerun']).lower()}",
        "",
        "## Compact Contract Failures By Field",
        "",
        report_json_block(result["compact_contract_failures_by_field"]),
        "",
        "## First Complete JSON Stop Behavior",
        "",
        report_json_block(result["first_complete_json_stop_behavior"]),
        "",
        "## Generated Tokens",
        "",
        report_json_block(result["average_generated_tokens"]),
        "",
        "## Invalid Label Values",
        "",
        report_json_block(result["invalid_label_values"]),
        "",
        "## Constrained Decoding Interpretation",
        "",
        report_json_block(result["constrained_decoding_or_label_normalization"]),
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def write_decision_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {DECISION_ID}",
        "",
        "## Recommendation",
        "",
        f"- recommended_next_option: `{result['recommended_next_option']}`",
        f"- more_training_recommended_immediately: {str(result['more_training_recommended_immediately']).lower()}",
        f"- data_expansion_recommended: {str(result['data_expansion_recommended']).lower()}",
        f"- label_simplification_recommended: {str(result['label_simplification_recommended']).lower()}",
        f"- constrained_decoding_recommended: {str(result['constrained_decoding_recommended']).lower()}",
        f"- two_head_architecture_recommended: {str(result['two_head_architecture_recommended']).lower()}",
        f"- adapter_live_ready: {str(result['adapter_live_ready']).lower()}",
        f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
        "",
        "## Rationale",
        "",
        report_json_block(result["rationale"]),
        "",
        "## Recommended Options",
        "",
        report_json_block(result["recommended_options"]),
        "",
        "## Rejected Or Deferred Options",
        "",
        report_json_block(result["rejected_options"]),
        "",
        "## Option Scores",
        "",
        report_json_block(result["option_scores"]),
    ]
    write_text(DECISION_REPORT_PATH, "\n".join(lines))


def main() -> int:
    decoding = build_decoding_audit()
    write_json(RESULT_PATH, decoding)
    write_decoding_report(decoding)
    decision = build_next_decision(decoding)
    write_json(DECISION_RESULT_PATH, decision)
    write_decision_report(decision)
    print(
        json.dumps(
            {
                "experiment_id": EXPERIMENT_ID,
                "status": decoding["status"],
                "mostly_semantic": decoding["failures_are_mostly_semantic_not_formatting"],
                "decision": decision["recommended_next_option"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
