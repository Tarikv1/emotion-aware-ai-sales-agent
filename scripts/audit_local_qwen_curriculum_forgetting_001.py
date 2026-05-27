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
    eval_failed,
    field_mismatches,
    group_signature_summary,
    label_signature,
    read_json,
    read_jsonl,
    rel,
    report_json_block,
    rows_by_case_from_paths,
    semantic_groups,
    signature_to_dict,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-CURRICULUM-FORGETTING-AUDIT-001"
TINY_RESULT_PATH = GENERATED_DIR / "LOCAL-QWEN-LORA-TINY-OVERFIT-001" / "result.json"
CURRICULUM_EVAL_RESULT_PATH = GENERATED_DIR / "LOCAL-QWEN-LORA-CURRICULUM-EVAL-001" / "result.json"
CURRICULUM_TRAINING_RESULT_PATH = GENERATED_DIR / "LOCAL-QWEN-LORA-CURRICULUM-TRAINING-001" / "result.json"
CURRICULUM_DIR = GENERATED_DIR / "LOCAL-QWEN-CURRICULUM-DATASET-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

STAGE_PATHS = {
    "tiny": CURRICULUM_DIR / "stage1_tiny.jsonl",
    "20": CURRICULUM_DIR / "stage2_20.jsonl",
    "60": CURRICULUM_DIR / "stage3_60.jsonl",
}


def tiny_adapter_case_lookup(tiny_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    evaluation = tiny_result.get("evaluation") if isinstance(tiny_result.get("evaluation"), dict) else {}
    models = evaluation.get("models") if isinstance(evaluation.get("models"), dict) else {}
    tiny_adapter = models.get("tiny_adapter") if isinstance(models.get("tiny_adapter"), dict) else {}
    return {
        str(case.get("case_id") or ""): case
        for case in tiny_adapter.get("cases") or []
        if isinstance(case, dict) and case.get("case_id")
    }


def pass_summary(case: dict[str, Any]) -> dict[str, bool]:
    return {
        "schema_valid": case.get("schema_valid") is True,
        "verifier_pass": case.get("verifier_pass") is True,
        "compact_contract_valid": case.get("compact_contract_valid") is True,
        "strict_gold_semantic_match": case.get("strict_gold_semantic_match") is True,
        "strict_gold_response_plan_match": case.get("strict_gold_response_plan_match") is True
        or case.get("gold_response_plan_match") is True,
        "exact_match": case.get("exact_match") is True or case.get("exact_target_match") is True,
    }


def stage_rows() -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for stage, path in STAGE_PATHS.items():
        rows = read_jsonl(path)
        for row in rows:
            row["_audit_split"] = f"stage_{stage}"
        result[stage] = rows
    return result


def exact_stage_presence(tiny_case_ids: set[str], rows_by_stage: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    presence: dict[str, Any] = {}
    for stage in ("20", "60"):
        stage_ids = {str(row.get("case_id") or "") for row in rows_by_stage[stage]}
        overlap = sorted(tiny_case_ids & stage_ids)
        presence[stage] = {
            "tiny_case_id_overlap_count": len(overlap),
            "tiny_case_id_overlap": overlap,
            "tiny_replay_included": bool(overlap),
        }
    return presence


def similar_stage_conflicts(rows_by_stage: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    tiny_rows = rows_by_stage["tiny"]
    later_rows = rows_by_stage["20"] + rows_by_stage["60"]
    records: list[dict[str, Any]] = []
    conflict_count = 0
    for tiny in tiny_rows:
        tiny_groups = set(semantic_groups(tiny))
        if not tiny_groups:
            continue
        similar = [row for row in later_rows if tiny_groups & set(semantic_groups(row))]
        if not similar:
            records.append(
                {
                    "tiny_case_id": tiny.get("case_id"),
                    "groups": sorted(tiny_groups),
                    "similar_later_count": 0,
                    "classification": "insufficient_later_examples",
                }
            )
            continue
        all_rows = [tiny] + similar
        summary = group_signature_summary(all_rows)
        conflict = not summary["action_strategy_consistent"] or not summary["preserve_consistent"] or not summary["facts_consistent"]
        if conflict:
            conflict_count += 1
        records.append(
            {
                "tiny_case_id": tiny.get("case_id"),
                "groups": sorted(tiny_groups),
                "similar_later_count": len(similar),
                "classification": "conflicting_similar_targets" if conflict else "similar_targets_consistent",
                "action_strategy_signature_count": summary["action_strategy_signature_count"],
                "facts_signature_count": summary["facts_signature_count"],
                "preserve_signature_count": summary["preserve_signature_count"],
            }
        )
    return {"conflict_count": conflict_count, "cases": records}


def training_replay_diagnostics(training_result: dict[str, Any], rows_by_stage: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    stage_results = training_result.get("stage_results") if isinstance(training_result.get("stage_results"), list) else []
    row_counts = {
        str(item.get("stage")): int(item.get("row_count") or 0)
        for item in stage_results
        if isinstance(item, dict) and item.get("stage") is not None
    }
    expected_counts = {stage: len(rows) for stage, rows in rows_by_stage.items()}
    sequential_single_stage = bool(stage_results) and all(row_counts.get(stage) == expected_counts.get(stage) for stage in row_counts)
    final_stage = str((stage_results[-1] if stage_results else {}).get("stage") or "")
    final_stage_only_rows = row_counts.get(final_stage) == expected_counts.get(final_stage) if final_stage else False
    tiny_replay_later = any(
        str(row.get("case_id") or "") in {str(tiny.get("case_id") or "") for tiny in rows_by_stage["tiny"]}
        for stage in ("20", "60")
        for row in rows_by_stage[stage]
    )
    config = training_result.get("config") if isinstance(training_result.get("config"), dict) else {}
    learning_rate = config.get("learning_rate")
    steps = training_result.get("train_steps_by_stage") if isinstance(training_result.get("train_steps_by_stage"), dict) else {}
    likely_forgetting_pressure = (
        sequential_single_stage
        and final_stage == "60"
        and not tiny_replay_later
        and isinstance(learning_rate, (int, float))
        and float(learning_rate) >= 0.0002
    )
    return {
        "completed_stages": training_result.get("completed_stages"),
        "train_steps_by_stage": steps,
        "train_row_counts_by_stage": row_counts,
        "sequential_stage_training_detected": sequential_single_stage,
        "sequential_overwrite_without_mixed_replay": sequential_single_stage and final_stage_only_rows,
        "final_stage": final_stage,
        "final_stage_used_only_stage3_rows": final_stage == "60" and final_stage_only_rows,
        "tiny_replay_examples_in_later_stages": tiny_replay_later,
        "learning_rate": learning_rate,
        "learning_rate_steps_likely_caused_forgetting": likely_forgetting_pressure,
        "recommended_curriculum_shape": "mixed tiny+stage2+stage3 replay with balanced sampling before any retrain",
        "replay_weighting_or_balanced_sampling_recommended": True,
    }


def forgotten_cases(
    tiny_result: dict[str, Any],
    curriculum_eval: dict[str, Any],
    rows_by_case: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    tiny_lookup = tiny_adapter_case_lookup(tiny_result)
    curriculum_lookup = {
        str(case.get("case_id") or ""): case
        for case in curriculum_eval_cases(curriculum_eval, ("tiny_comparison",))
        if case.get("case_id")
    }
    records: list[dict[str, Any]] = []
    for case_id, tiny_case in sorted(tiny_lookup.items()):
        curriculum_case = curriculum_lookup.get(case_id, {})
        tiny_pass = all(pass_summary(tiny_case).values())
        curriculum_pass = all(pass_summary(curriculum_case).values()) if curriculum_case else False
        if not tiny_pass or curriculum_pass:
            continue
        row = rows_by_case.get(case_id, {})
        expected = compact_target(row)
        predicted = compact_prediction(curriculum_case)
        mismatches = field_mismatches(expected, predicted)
        records.append(
            {
                "case_id": case_id,
                "groups": semantic_groups(row),
                "tiny_adapter": pass_summary(tiny_case),
                "curriculum_adapter": pass_summary(curriculum_case),
                "field_mismatches": mismatches,
                "failure_classes": curriculum_case.get("failure_classes") or [],
                "semantic_mismatches": curriculum_case.get("semantic_mismatches") or [],
                "verifier_errors": curriculum_case.get("verifier_errors") or [],
                "unacceptable_wrong_sales_move": classify_sales_move(expected, predicted),
                "expected": compact_public_summary(expected),
                "curriculum_predicted": compact_public_summary(predicted),
            }
        )
    return records


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- forgotten_tiny_case_count: {result['summary']['forgotten_tiny_case_count']}",
        f"- sequential_overwrite_without_mixed_replay: {str(result['training_replay_diagnostics']['sequential_overwrite_without_mixed_replay']).lower()}",
        f"- tiny_replay_examples_in_later_stages: {str(result['training_replay_diagnostics']['tiny_replay_examples_in_later_stages']).lower()}",
        f"- learning_rate_steps_likely_caused_forgetting: {str(result['training_replay_diagnostics']['learning_rate_steps_likely_caused_forgetting']).lower()}",
        f"- local_model_calls_made: {str(result['side_effects']['local_model_calls_made']).lower()}",
        f"- provider_calls_made: {str(result['side_effects']['provider_calls_made']).lower()}",
        "",
        "## Forgetting",
        "",
        report_json_block(result["summary"]),
        "",
        "## Replay Diagnostics",
        "",
        report_json_block(result["training_replay_diagnostics"]),
        "",
        "## Similar Later-Stage Conflicts",
        "",
        report_json_block(
            {
                "conflict_count": result["similar_later_stage_conflicts"]["conflict_count"],
                "case_classifications": Counter(
                    item["classification"] for item in result["similar_later_stage_conflicts"]["cases"]
                ),
            }
        ),
    ]
    return "\n".join(lines)


def main() -> int:
    tiny_result = read_json(TINY_RESULT_PATH)
    curriculum_eval = read_json(CURRICULUM_EVAL_RESULT_PATH)
    training_result = read_json(CURRICULUM_TRAINING_RESULT_PATH)
    rows_by_stage = stage_rows()
    rows_by_case = rows_by_case_from_paths({"tiny_comparison": STAGE_PATHS["tiny"]})
    forgotten = forgotten_cases(tiny_result, curriculum_eval, rows_by_case)
    tiny_case_ids = {str(row.get("case_id") or "") for row in rows_by_stage["tiny"]}
    stage_presence = exact_stage_presence(tiny_case_ids, rows_by_stage)
    conflicts = similar_stage_conflicts(rows_by_stage)
    replay = training_replay_diagnostics(training_result, rows_by_stage)
    failure_classes = Counter(kind for case in forgotten for kind in case.get("failure_classes") or [])
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "tiny_result": rel(TINY_RESULT_PATH),
            "curriculum_eval_result": rel(CURRICULUM_EVAL_RESULT_PATH),
            "curriculum_training_result": rel(CURRICULUM_TRAINING_RESULT_PATH),
            "stage1_tiny": rel(STAGE_PATHS["tiny"]),
            "stage2_20": rel(STAGE_PATHS["20"]),
            "stage3_60": rel(STAGE_PATHS["60"]),
        },
        "tiny_adapter_vs_curriculum_on_tiny": {
            "tiny_adapter_summary": ((tiny_result.get("evaluation") or {}).get("comparison") or {}).get("tiny_adapter"),
            "curriculum_tiny_metrics": ((curriculum_eval.get("curriculum_adapter") or {}).get("splits") or {})
            .get("tiny_comparison", {})
            .get("metrics"),
        },
        "summary": {
            "forgotten_tiny_case_count": len(forgotten),
            "forgotten_case_ids": [case["case_id"] for case in forgotten],
            "failure_class_counts": dict(sorted(failure_classes.items())),
            "adapter_live_ready": False,
            "quality_gate_passed": False,
        },
        "forgotten_cases": forgotten,
        "tiny_cases_in_later_stages": stage_presence,
        "similar_later_stage_conflicts": conflicts,
        "training_replay_diagnostics": replay,
        "recommendations": {
            "continue_training_now": False,
            "final_stage_should_mix_tiny_stage2_stage3": True,
            "use_replay_weighting_or_balanced_sampling": True,
            "diagnostic_read": "Forgetting is expected under sequential stage-only training when the final 60-row stage does not replay tiny examples.",
        },
        "side_effects": audit_side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "forgotten_tiny_case_count": len(forgotten),
                "sequential_overwrite_without_mixed_replay": replay["sequential_overwrite_without_mixed_replay"],
                "tiny_replay_examples_in_later_stages": replay["tiny_replay_examples_in_later_stages"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
