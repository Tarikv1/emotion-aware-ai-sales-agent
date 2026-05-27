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
    GROUP_ORDER,
    LABEL_FIELDS,
    audit_side_effects,
    compact_prediction,
    compact_public_summary,
    compact_target,
    counter_records,
    curriculum_eval_cases,
    eval_failed,
    field_mismatches,
    group_signature_summary,
    label_signature,
    read_json,
    read_jsonl,
    rel,
    report_json_block,
    response_plan_signature,
    rows_by_case_from_paths,
    semantic_groups,
    signature_to_dict,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-DATASET-CONSISTENCY-AUDIT-001"
SFT_DIR = GENERATED_DIR / "LOCAL-QWEN-SFT-DATASET-001"
CURRICULUM_DIR = GENERATED_DIR / "LOCAL-QWEN-CURRICULUM-DATASET-001"
EVAL_RESULT_PATH = GENERATED_DIR / "LOCAL-QWEN-LORA-CURRICULUM-EVAL-001" / "result.json"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SFT_SPLITS = {
    "sft_train": SFT_DIR / "train.jsonl",
    "sft_validation": SFT_DIR / "validation.jsonl",
    "sft_test": SFT_DIR / "test.jsonl",
}
CURRICULUM_SPLITS = {
    "curriculum_stage1_tiny": CURRICULUM_DIR / "stage1_tiny.jsonl",
    "curriculum_stage2_20": CURRICULUM_DIR / "stage2_20.jsonl",
    "curriculum_stage3_60": CURRICULUM_DIR / "stage3_60.jsonl",
    "curriculum_validation": CURRICULUM_DIR / "validation.jsonl",
    "curriculum_test": CURRICULUM_DIR / "test.jsonl",
}


def load_split_rows() -> dict[str, list[dict[str, Any]]]:
    rows_by_split: dict[str, list[dict[str, Any]]] = {}
    for split_name, path in {**SFT_SPLITS, **CURRICULUM_SPLITS}.items():
        rows = read_jsonl(path)
        for row in rows:
            row["_audit_split"] = split_name
        rows_by_split[split_name] = rows
    return rows_by_split


def label_distribution(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    distribution: dict[str, Any] = {}
    for split_name, rows in rows_by_split.items():
        split_summary: dict[str, Any] = {"row_count": len(rows)}
        for field in LABEL_FIELDS:
            counter = Counter(str(compact_target(row).get(field) or "") for row in rows)
            split_summary[field] = dict(sorted(counter.items()))
        distribution[split_name] = split_summary
    return distribution


def values_for(rows: list[dict[str, Any]], field: str) -> set[str]:
    return {str(compact_target(row).get(field) or "") for row in rows if compact_target(row).get(field) is not None}


def signature_set(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> set[tuple[tuple[str, Any], ...]]:
    return {label_signature(compact_target(row), fields) for row in rows}


def coverage_for_split(split_name: str, rows: list[dict[str, Any]], train_rows: list[dict[str, Any]]) -> dict[str, Any]:
    train_values = {field: values_for(train_rows, field) for field in LABEL_FIELDS}
    train_all_combos = signature_set(train_rows, LABEL_FIELDS)
    train_action_sub = signature_set(train_rows, ("action", "sub"))
    train_core = signature_set(train_rows, CORE_FIELDS)

    unseen_labels = {
        field: sorted(values_for(rows, field) - train_values[field])
        for field in LABEL_FIELDS
        if values_for(rows, field) - train_values[field]
    }
    unseen_all_combos = sorted(signature_set(rows, LABEL_FIELDS) - train_all_combos)
    unseen_action_sub = sorted(signature_set(rows, ("action", "sub")) - train_action_sub)
    unseen_core = sorted(signature_set(rows, CORE_FIELDS) - train_core)
    return {
        "split": split_name,
        "row_count": len(rows),
        "unseen_labels_by_field": unseen_labels,
        "unseen_label_combination_count": len(unseen_all_combos),
        "unseen_label_combinations": [signature_to_dict(item) for item in unseen_all_combos[:50]],
        "unseen_action_sub_pair_count": len(unseen_action_sub),
        "unseen_action_sub_pairs": [signature_to_dict(item) for item in unseen_action_sub[:50]],
        "unseen_act_sub_action_strategy_combo_count": len(unseen_core),
        "unseen_act_sub_action_strategy_combos": [signature_to_dict(item) for item in unseen_core[:50]],
        "has_split_distribution_issue": bool(unseen_labels or unseen_all_combos or unseen_action_sub or unseen_core),
    }


def heldout_coverage(rows_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    sft_train = rows_by_split["sft_train"]
    curriculum_train_all = rows_by_split["curriculum_stage1_tiny"] + rows_by_split["curriculum_stage3_60"]
    return {
        "against_sft_train": {
            "validation": coverage_for_split("sft_validation", rows_by_split["sft_validation"], sft_train),
            "test": coverage_for_split("sft_test", rows_by_split["sft_test"], sft_train),
        },
        "against_curriculum_tiny_plus_stage3": {
            "validation": coverage_for_split("curriculum_validation", rows_by_split["curriculum_validation"], curriculum_train_all),
            "test": coverage_for_split("curriculum_test", rows_by_split["curriculum_test"], curriculum_train_all),
        },
    }


def unique_curriculum_rows(rows_by_split: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    ordered = (
        rows_by_split["curriculum_stage1_tiny"]
        + rows_by_split["curriculum_stage3_60"]
        + rows_by_split["curriculum_validation"]
        + rows_by_split["curriculum_test"]
    )
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in ordered:
        case_id = str(row.get("case_id") or "")
        key = case_id or json.dumps(compact_target(row), sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def similar_input_consistency(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {group: [] for group in GROUP_ORDER}
    ungrouped: list[str] = []
    for row in rows:
        groups = semantic_groups(row)
        if not groups:
            ungrouped.append(str(row.get("case_id") or ""))
        for group in groups:
            grouped[group].append(row)

    summaries: dict[str, Any] = {}
    for group, group_rows in grouped.items():
        summary = group_signature_summary(group_rows)
        summary["classification"] = (
            "target_consistent"
            if summary["action_strategy_consistent"] and summary["preserve_consistent"] and summary["facts_consistent"]
            else "target_inconsistency_or_group_too_broad"
        )
        summary["consistency_warnings"] = []
        if not summary["action_strategy_consistent"]:
            summary["consistency_warnings"].append("multiple action/strategy targets in same semantic neighborhood")
        if not summary["preserve_consistent"]:
            summary["consistency_warnings"].append("preserve fields vary inside same semantic neighborhood")
        if not summary["facts_consistent"]:
            summary["consistency_warnings"].append("facts fields vary inside same semantic neighborhood")
        if not summary["say_style_consistent"]:
            summary["consistency_warnings"].append("say style varies inside same semantic neighborhood")
        summaries[group] = summary
    return {"groups": summaries, "ungrouped_case_ids": sorted(ungrouped)}


def cases_by_group(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for group in semantic_groups(row):
            grouped[group].append(row)
    return grouped


def group_conflict_index(rows: list[dict[str, Any]]) -> dict[str, bool]:
    summary = similar_input_consistency(rows)["groups"]
    return {
        group: bool(payload.get("consistency_warnings"))
        for group, payload in summary.items()
        if isinstance(payload, dict)
    }


def train_signature_counts(train_rows: list[dict[str, Any]]) -> Counter[tuple[tuple[str, Any], ...]]:
    return Counter(label_signature(compact_target(row), CORE_FIELDS) for row in train_rows)


def gold_strictness_review(
    rows_by_split: dict[str, list[dict[str, Any]]],
    consistency: dict[str, Any],
) -> dict[str, Any]:
    eval_result = read_json(EVAL_RESULT_PATH)
    split_paths = {
        split_name: CURRICULUM_SPLITS[{
            "tiny_comparison": "curriculum_stage1_tiny",
            "validation": "curriculum_validation",
            "test": "curriculum_test",
        }[split_name]]
        for split_name in ("tiny_comparison", "validation", "test")
    }
    rows_by_case = rows_by_case_from_paths(split_paths)
    train_counts = train_signature_counts(rows_by_split["curriculum_stage3_60"])
    coverage = heldout_coverage(rows_by_split)["against_sft_train"]
    coverage_issue_cases: set[str] = set()
    for split_key, payload in (("validation", coverage["validation"]), ("test", coverage["test"])):
        split_rows = rows_by_split[f"sft_{split_key}"]
        train_core = signature_set(rows_by_split["sft_train"], CORE_FIELDS)
        for row in split_rows:
            if label_signature(compact_target(row), CORE_FIELDS) not in train_core:
                coverage_issue_cases.add(str(row.get("case_id") or ""))

    conflicts = group_conflict_index(unique_curriculum_rows(rows_by_split))
    records: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    signal_counts: Counter[str] = Counter()
    for case in curriculum_eval_cases(eval_result, ("tiny_comparison", "validation", "test")):
        if not eval_failed(case):
            continue
        case_id = str(case.get("case_id") or "")
        row = rows_by_case.get(case_id, {})
        expected = compact_target(row)
        predicted = compact_prediction(case)
        mismatches = field_mismatches(expected, predicted)
        same_core = all(field not in mismatches for field in CORE_FIELDS)
        same_action_strategy = all(field not in mismatches for field in ("action", "strategy"))
        same_except_say = [field for field in mismatches if field != "say"] == []
        response_plan_only = bool(case.get("semantic_mismatches")) and all(
            str(item).startswith("response_plan.") for item in case.get("semantic_mismatches") or []
        )
        groups = semantic_groups(row) if row else []
        signals: list[str] = []
        if same_action_strategy and "say" in mismatches:
            signals.append("same_action_strategy_different_say")
        if same_except_say:
            signals.append("semantic_fields_match_exact_text_differs")
        if response_plan_only:
            signals.append("response_plan_mismatch_only")
        if same_core and case.get("verifier_pass") is True and case.get("compact_contract_valid") is True:
            signals.append("same_core_semantics_verifier_passed")

        classifications: set[str] = set()
        if same_except_say or response_plan_only or (same_core and same_action_strategy and case.get("verifier_pass") is True):
            classifications.add("gold_label_too_strict")
        if groups and any(conflicts.get(group) for group in groups):
            classifications.add("target_inconsistency")
        if case_id in coverage_issue_cases:
            classifications.add("split_distribution_issue")
        expected_core = label_signature(expected, CORE_FIELDS)
        if train_counts.get(expected_core, 0) < 3:
            classifications.add("insufficient_training_examples")
        if not classifications or any(field in mismatches for field in CORE_FIELDS + ("update", "facts", "preserve", "avoid")):
            classifications.add("true_model_failure")
        if case.get("verifier_pass") is not True and not same_core:
            classifications.add("true_model_failure")

        for item in classifications:
            class_counts[item] += 1
        for item in signals:
            signal_counts[item] += 1
        records.append(
            {
                "case_id": case_id,
                "split": case.get("split"),
                "groups": groups,
                "classifications": sorted(classifications),
                "strictness_signals": sorted(signals),
                "field_mismatches": mismatches,
                "semantic_mismatches": case.get("semantic_mismatches") or [],
                "verifier_errors": case.get("verifier_errors") or [],
                "expected": compact_public_summary(expected),
                "predicted": compact_public_summary(predicted),
            }
        )
    for required in (
        "true_model_failure",
        "gold_label_too_strict",
        "target_inconsistency",
        "split_distribution_issue",
        "insufficient_training_examples",
    ):
        class_counts.setdefault(required, 0)
    for required in (
        "same_action_strategy_different_say",
        "semantic_fields_match_exact_text_differs",
        "response_plan_mismatch_only",
        "same_core_semantics_verifier_passed",
    ):
        signal_counts.setdefault(required, 0)
    return {
        "failed_case_count": len(records),
        "classification_counts": dict(sorted(class_counts.items())),
        "strictness_signal_counts": dict(sorted(signal_counts.items())),
        "cases": records,
        "notes": [
            "gold_label_too_strict is assigned only when compact core semantics or response-plan-only evidence suggests the output may be acceptable under a narrower equivalence rule.",
            "true_model_failure is retained whenever core labels, state updates, facts, preserve, or avoid fields diverge.",
        ],
    }


def build_report(result: dict[str, Any]) -> str:
    coverage = result["heldout_label_coverage"]["against_sft_train"]
    group_summary = result["similar_input_consistency"]["groups"]
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- source_eval: `{result['inputs']['curriculum_eval_result']}`",
        f"- local_model_calls_made: {str(result['side_effects']['local_model_calls_made']).lower()}",
        f"- provider_calls_made: {str(result['side_effects']['provider_calls_made']).lower()}",
        f"- runtime_behavior_changed: {str(result['side_effects']['runtime_behavior_changed']).lower()}",
        f"- response_text_changed: {str(result['side_effects']['response_text_changed']).lower()}",
        "",
        "## Held-Out Coverage",
        "",
        f"- validation unseen act/sub/action/strategy combos: {coverage['validation']['unseen_act_sub_action_strategy_combo_count']}",
        f"- test unseen act/sub/action/strategy combos: {coverage['test']['unseen_act_sub_action_strategy_combo_count']}",
        f"- validation unseen action/sub pairs: {coverage['validation']['unseen_action_sub_pair_count']}",
        f"- test unseen action/sub pairs: {coverage['test']['unseen_action_sub_pair_count']}",
        "",
        "## Similar-Input Consistency",
        "",
    ]
    for group in GROUP_ORDER:
        payload = group_summary.get(group) or {}
        lines.extend(
            [
                f"### {group}",
                "",
                f"- cases: {payload.get('case_count', 0)}",
                f"- action_strategy_consistent: {str(payload.get('action_strategy_consistent')).lower()}",
                f"- preserve_consistent: {str(payload.get('preserve_consistent')).lower()}",
                f"- facts_consistent: {str(payload.get('facts_consistent')).lower()}",
                f"- warnings: {', '.join(payload.get('consistency_warnings') or []) or 'none'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Gold Strictness Review",
            "",
            report_json_block(
                {
                    "classification_counts": result["gold_strictness_review"]["classification_counts"],
                    "strictness_signal_counts": result["gold_strictness_review"]["strictness_signal_counts"],
                }
            ),
            "",
            "## Side Effects",
            "",
            report_json_block(result["side_effects"]),
        ]
    )
    return "\n".join(lines)


def main() -> int:
    rows_by_split = load_split_rows()
    unique_rows = unique_curriculum_rows(rows_by_split)
    consistency = similar_input_consistency(unique_rows)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "sft_train": rel(SFT_SPLITS["sft_train"]),
            "sft_validation": rel(SFT_SPLITS["sft_validation"]),
            "sft_test": rel(SFT_SPLITS["sft_test"]),
            "curriculum_stage1_tiny": rel(CURRICULUM_SPLITS["curriculum_stage1_tiny"]),
            "curriculum_stage2_20": rel(CURRICULUM_SPLITS["curriculum_stage2_20"]),
            "curriculum_stage3_60": rel(CURRICULUM_SPLITS["curriculum_stage3_60"]),
            "curriculum_validation": rel(CURRICULUM_SPLITS["curriculum_validation"]),
            "curriculum_test": rel(CURRICULUM_SPLITS["curriculum_test"]),
            "curriculum_eval_result": rel(EVAL_RESULT_PATH),
        },
        "label_distribution_by_split": label_distribution(rows_by_split),
        "heldout_label_coverage": heldout_coverage(rows_by_split),
        "similar_input_consistency": consistency,
        "target_response_plan_consistency": {
            group: {
                "case_count": payload["case_count"],
                "action_strategy_distribution": payload["action_strategy_distribution"],
                "facts_distribution": payload["facts_distribution"],
                "preserve_distribution": payload["preserve_distribution"],
                "avoid_distribution": payload["avoid_distribution"],
                "say_style_distribution": payload["say_style_distribution"],
                "response_plan_signature_count": payload["response_plan_signature_count"],
                "classification": payload["classification"],
            }
            for group, payload in consistency["groups"].items()
        },
        "gold_strictness_review": gold_strictness_review(rows_by_split, consistency),
        "side_effects": audit_side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "validation_unseen_core": result["heldout_label_coverage"]["against_sft_train"]["validation"][
                    "unseen_act_sub_action_strategy_combo_count"
                ],
                "test_unseen_core": result["heldout_label_coverage"]["against_sft_train"]["test"][
                    "unseen_act_sub_action_strategy_combo_count"
                ],
                "gold_strictness_classes": result["gold_strictness_review"]["classification_counts"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
