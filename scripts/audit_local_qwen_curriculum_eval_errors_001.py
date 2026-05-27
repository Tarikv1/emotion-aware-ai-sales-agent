#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    CORE_FIELDS,
    GENERATED_DIR,
    audit_side_effects,
    classify_sales_move,
    compact_prediction,
    compact_public_summary,
    compact_target,
    curriculum_eval_cases,
    curriculum_split_paths,
    eval_failed,
    field_mismatches,
    label_signature,
    read_json,
    rel,
    report_json_block,
    rows_by_case_from_paths,
    semantic_groups,
    signature_to_dict,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-EVAL-ERROR-AUDIT-001"
PLAN_EXPERIMENT_ID = "LOCAL-QWEN-NEXT-TRAINING-PLAN-001"
EVAL_RESULT_PATH = GENERATED_DIR / "LOCAL-QWEN-LORA-CURRICULUM-EVAL-001" / "result.json"
DATASET_AUDIT_PATH = GENERATED_DIR / "LOCAL-QWEN-DATASET-CONSISTENCY-AUDIT-001" / "result.json"
FORGETTING_AUDIT_PATH = GENERATED_DIR / "LOCAL-QWEN-CURRICULUM-FORGETTING-AUDIT-001" / "result.json"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PLAN_OUT_DIR = GENERATED_DIR / PLAN_EXPERIMENT_ID
PLAN_RESULT_PATH = PLAN_OUT_DIR / "result.json"
PLAN_REPORT_PATH = PLAN_OUT_DIR / "report.md"

FAILED_SPLITS = ("tiny_comparison", "validation", "test")


def classify_case(case: dict[str, Any], expected: dict[str, Any], predicted: dict[str, Any]) -> dict[str, Any]:
    mismatches = field_mismatches(expected, predicted)
    semantic_mismatches = [str(item) for item in case.get("semantic_mismatches") or []]
    response_mismatch = bool(case.get("gold_response_plan_mismatches")) or any(
        item.startswith("response_plan.") for item in semantic_mismatches
    )
    wrong_flags = {
        "wrong_act": "act" in mismatches,
        "wrong_sub": "sub" in mismatches,
        "wrong_action": "action" in mismatches,
        "wrong_strategy": "strategy" in mismatches,
        "wrong_update": "update" in mismatches,
        "wrong_preserve_avoid": "preserve" in mismatches or "avoid" in mismatches,
        "wrong_facts": "facts" in mismatches,
        "wrong_say": "say" in mismatches,
    }
    same_core = not any(wrong_flags[key] for key in ("wrong_act", "wrong_sub", "wrong_action", "wrong_strategy"))
    only_say_wrong = mismatches == ["say"]
    response_plan_only = response_mismatch and all(item.startswith("response_plan.") for item in semantic_mismatches)
    acceptable_alternative = bool(
        case.get("schema_valid") is True
        and case.get("compact_contract_valid") is True
        and case.get("verifier_pass") is True
        and (same_core or only_say_wrong or response_plan_only)
        and not classify_sales_move(expected, predicted)
    )
    unacceptable_wrong_sales_move = classify_sales_move(expected, predicted)
    classes: list[str] = []
    if case.get("schema_valid") is not True or case.get("malformed_output") is True:
        classes.append("schema_issue")
    if case.get("compact_contract_valid") is not True:
        classes.append("compact_contract_issue")
    if case.get("verifier_pass") is not True:
        classes.append("verifier_issue")
    if case.get("strict_gold_semantic_match") is not True:
        classes.append("strict_semantic_mismatch")
    if case.get("strict_gold_response_plan_match") is not True or response_mismatch:
        classes.append("response_plan_mismatch")
    for flag, enabled in wrong_flags.items():
        if enabled:
            classes.append(flag)
    if acceptable_alternative:
        classes.append("acceptable_alternative")
    if unacceptable_wrong_sales_move:
        classes.append("unacceptable_wrong_sales_move")
    if not classes:
        classes.append("needs_human_review")
    return {
        "classes": sorted(set(classes)),
        "field_mismatches": mismatches,
        "acceptable_alternative": acceptable_alternative,
        "unacceptable_wrong_sales_move": unacceptable_wrong_sales_move,
    }


def summarize_confusion(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter()
    for record in records:
        expected = str((record.get("expected") or {}).get(field) or "")
        predicted = str((record.get("predicted") or {}).get(field) or "")
        if expected != predicted:
            counter[(expected, predicted)] += 1
    return [
        {"expected": expected, "predicted": predicted, "count": count}
        for (expected, predicted), count in counter.most_common()
    ]


def build_error_audit() -> dict[str, Any]:
    eval_result = read_json(EVAL_RESULT_PATH)
    split_paths = curriculum_split_paths(eval_result)
    rows_by_case = rows_by_case_from_paths(split_paths)
    records: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    wrong_label_counter: Counter[tuple[str, str]] = Counter()
    missed_label_counter: Counter[tuple[str, str]] = Counter()
    need_more_counter: Counter[tuple[tuple[str, Any], ...]] = Counter()

    for case in curriculum_eval_cases(eval_result, FAILED_SPLITS):
        if not eval_failed(case):
            continue
        case_id = str(case.get("case_id") or "")
        row = rows_by_case.get(case_id, {})
        expected = compact_target(row)
        predicted = compact_prediction(case)
        classification = classify_case(case, expected, predicted)
        for item in classification["classes"]:
            class_counts[item] += 1
        for field in ("act", "sub", "action", "strategy"):
            expected_value = str(expected.get(field) or "")
            predicted_value = str(predicted.get(field) or "")
            if expected_value != predicted_value:
                wrong_label_counter[(field, predicted_value)] += 1
                missed_label_counter[(field, expected_value)] += 1
        expected_core = label_signature(expected, CORE_FIELDS)
        if "strict_semantic_mismatch" in classification["classes"] or "unacceptable_wrong_sales_move" in classification["classes"]:
            need_more_counter[expected_core] += 1
        records.append(
            {
                "case_id": case_id,
                "split": case.get("split"),
                "groups": semantic_groups(row),
                "classes": classification["classes"],
                "field_mismatches": classification["field_mismatches"],
                "semantic_mismatches": case.get("semantic_mismatches") or [],
                "verifier_errors": case.get("verifier_errors") or [],
                "expected": compact_public_summary(expected),
                "predicted": compact_public_summary(predicted),
            }
        )
    for required in (
        "schema_issue",
        "verifier_issue",
        "strict_semantic_mismatch",
        "response_plan_mismatch",
        "wrong_act",
        "wrong_sub",
        "wrong_action",
        "wrong_strategy",
        "wrong_update",
        "wrong_preserve_avoid",
        "wrong_facts",
        "wrong_say",
        "acceptable_alternative",
        "unacceptable_wrong_sales_move",
    ):
        class_counts.setdefault(required, 0)

    deterministic_better = [
        record["case_id"]
        for record in records
        if "unacceptable_wrong_sales_move" in record["classes"]
        or "verifier_issue" in record["classes"]
        or any(item in record["classes"] for item in ("wrong_act", "wrong_sub", "wrong_action", "wrong_strategy"))
    ]
    acceptable_strict = [record["case_id"] for record in records if "acceptable_alternative" in record["classes"]]
    more_examples = [
        {"expected_core": signature_to_dict(signature), "failed_case_count": count}
        for signature, count in need_more_counter.most_common()
    ]
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {"curriculum_eval_result": rel(EVAL_RESULT_PATH)},
        "failed_case_count": len(records),
        "failed_cases": records,
        "class_counts": dict(sorted(class_counts.items())),
        "top_wrong_labels_predicted": [
            {"field": field, "predicted": value, "count": count}
            for (field, value), count in wrong_label_counter.most_common()
        ],
        "top_expected_labels_missed": [
            {"field": field, "expected": value, "count": count}
            for (field, value), count in missed_label_counter.most_common()
        ],
        "confusion_matrix": {
            "action": summarize_confusion(records, "action"),
            "sub": summarize_confusion(records, "sub"),
        },
        "deterministic_baseline_clearly_better_case_ids": deterministic_better,
        "model_output_acceptable_but_strict_gold_too_narrow_case_ids": acceptable_strict,
        "cases_needing_more_training_examples": more_examples,
        "side_effects": audit_side_effects(),
    }


def option_scores(dataset_audit: dict[str, Any], forgetting_audit: dict[str, Any], error_audit: dict[str, Any]) -> dict[str, int]:
    validation_unseen = (
        (dataset_audit.get("heldout_label_coverage") or {})
        .get("against_sft_train", {})
        .get("validation", {})
        .get("unseen_act_sub_action_strategy_combo_count", 0)
    )
    test_unseen = (
        (dataset_audit.get("heldout_label_coverage") or {})
        .get("against_sft_train", {})
        .get("test", {})
        .get("unseen_act_sub_action_strategy_combo_count", 0)
    )
    strict_failures = int(error_audit.get("class_counts", {}).get("strict_semantic_mismatch", 0) or 0)
    unacceptable = int(error_audit.get("class_counts", {}).get("unacceptable_wrong_sales_move", 0) or 0)
    acceptable = int(error_audit.get("class_counts", {}).get("acceptable_alternative", 0) or 0)
    forgetting = int((forgetting_audit.get("summary") or {}).get("forgotten_tiny_case_count", 0) or 0)
    replay_issue = bool((forgetting_audit.get("training_replay_diagnostics") or {}).get("sequential_overwrite_without_mixed_replay"))
    return {
        "option_1_data_expansion_needed": int(validation_unseen) + int(test_unseen) + strict_failures + unacceptable,
        "option_2_curriculum_replay_fix": forgetting + (8 if replay_issue else 0),
        "option_3_label_simplification": 10 if strict_failures >= 20 and unacceptable >= 8 else 4,
        "option_4_eval_strictness_adjustment": acceptable * 3,
        "option_5_constrained_decoding_or_grammar": int(error_audit.get("class_counts", {}).get("compact_contract_issue", 0) or 0),
    }


def build_next_training_plan(error_audit: dict[str, Any]) -> dict[str, Any]:
    dataset_audit = read_json(DATASET_AUDIT_PATH)
    forgetting_audit = read_json(FORGETTING_AUDIT_PATH)
    scores = option_scores(dataset_audit, forgetting_audit, error_audit)
    selected = max(scores.items(), key=lambda item: item[1])[0]
    if selected == "option_5_constrained_decoding_or_grammar" and scores["option_1_data_expansion_needed"] > 0:
        selected = "option_1_data_expansion_needed"
    return {
        "experiment_id": PLAN_EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "selected_option": selected,
        "option_scores": scores,
        "adapter_live_ready": False,
        "quality_gate_passed": False,
        "more_training_recommended_now": False,
        "data_expansion_recommended": True,
        "label_simplification_recommended": selected == "option_3_label_simplification",
        "eval_strictness_adjustment_recommended": scores["option_4_eval_strictness_adjustment"] > 0,
        "curriculum_replay_fix_recommended": True,
        "constrained_decoding_or_grammar_recommended": scores["option_5_constrained_decoding_or_grammar"] > 0,
        "recommendation": {
            "primary": "Do not train more from the current 80-row curriculum. Expand to 300-500 balanced rows first, preserve held-out splits, and only then retrain with replay.",
            "minimum_dataset_work": [
                "Create balanced paraphrases per semantic neighborhood.",
                "Add rare safety, terminal, price, current-tool, personal-use, and use-case variants.",
                "Keep validation/test held out by case intent and paraphrase family, not only by case ID.",
                "Run the dataset consistency audit before any new QLoRA run.",
            ],
            "required_curriculum_change_after_data_passes": [
                "Final training stage must mix tiny + stage2 + stage3 examples.",
                "Use replay weighting or balanced sampling for tiny and rare groups.",
                "Track tiny-overfit retention as a hard regression gate.",
            ],
            "eval_change": [
                "Keep schema, verifier, safety, and side-effect checks strict.",
                "Add narrow semantic-equivalence rules for same action/strategy with acceptable response-plan wording.",
            ],
        },
        "live_wiring": {
            "recommended": False,
            "reason": "Held-out strict metrics and verifier pass rates do not justify live dialogue wiring.",
        },
        "side_effects": audit_side_effects(),
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- failed_case_count: {result['failed_case_count']}",
        f"- acceptable_alternative_count: {result['class_counts'].get('acceptable_alternative', 0)}",
        f"- unacceptable_wrong_sales_move_count: {result['class_counts'].get('unacceptable_wrong_sales_move', 0)}",
        f"- local_model_calls_made: {str(result['side_effects']['local_model_calls_made']).lower()}",
        f"- provider_calls_made: {str(result['side_effects']['provider_calls_made']).lower()}",
        "",
        "## Class Counts",
        "",
        report_json_block(result["class_counts"]),
        "",
        "## Wrong Labels",
        "",
        report_json_block(
            {
                "top_wrong_labels_predicted": result["top_wrong_labels_predicted"][:20],
                "top_expected_labels_missed": result["top_expected_labels_missed"][:20],
            }
        ),
        "",
        "## Confusion Matrix",
        "",
        report_json_block(result["confusion_matrix"]),
    ]
    return "\n".join(lines)


def build_plan_report(plan: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {PLAN_EXPERIMENT_ID}",
            "",
            f"- status: {plan['status']}",
            f"- selected_option: {plan['selected_option']}",
            f"- adapter_live_ready: {str(plan['adapter_live_ready']).lower()}",
            f"- more_training_recommended_now: {str(plan['more_training_recommended_now']).lower()}",
            f"- data_expansion_recommended: {str(plan['data_expansion_recommended']).lower()}",
            f"- curriculum_replay_fix_recommended: {str(plan['curriculum_replay_fix_recommended']).lower()}",
            f"- label_simplification_recommended: {str(plan['label_simplification_recommended']).lower()}",
            f"- eval_strictness_adjustment_recommended: {str(plan['eval_strictness_adjustment_recommended']).lower()}",
            "",
            "## Recommendation",
            "",
            report_json_block(plan["recommendation"]),
            "",
            "## Option Scores",
            "",
            report_json_block(plan["option_scores"]),
        ]
    )


def main() -> int:
    error_audit = build_error_audit()
    write_json(RESULT_PATH, error_audit)
    write_text(REPORT_PATH, build_report(error_audit))

    plan = build_next_training_plan(error_audit)
    write_json(PLAN_RESULT_PATH, plan)
    write_text(PLAN_REPORT_PATH, build_plan_report(plan))
    print(
        json.dumps(
            {
                "status": error_audit["status"],
                "failed_case_count": error_audit["failed_case_count"],
                "class_counts": error_audit["class_counts"],
                "next_training_selected_option": plan["selected_option"],
                "more_training_recommended_now": plan["more_training_recommended_now"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
