#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
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
    LABEL_FIELDS,
    audit_side_effects,
    classify_sales_move,
    compact_prediction,
    compact_public_summary,
    compact_target,
    counter_records,
    eval_failed,
    field_mismatches,
    read_json,
    read_jsonl,
    rel,
    report_json_block,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-EVAL-FAILURE-AUDIT-001"
EVAL_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001"
DATASET_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001"
EVAL_RESULT_PATH = GENERATED_DIR / EVAL_ID / "result.json"
DATASET_DIR = GENERATED_DIR / DATASET_ID
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
AUDIT_SPLITS = ("validation", "test", "ood_test")
PLAN_FIELDS = ("action", "strategy", "facts", "preserve", "avoid", "say")
CLASS_NAMES = (
    "schema_failure",
    "compact_contract_failure",
    "verifier_failure",
    "safety_failure",
    "strict_semantic_failure",
    "equivalence_failure",
    "exact_match_failure",
    "response_plan_failure",
    "wrong_act",
    "wrong_sub",
    "wrong_action",
    "wrong_strategy",
    "wrong_buyer",
    "wrong_intent",
    "wrong_rel",
    "wrong_neg",
    "wrong_update",
    "wrong_preserve",
    "wrong_avoid",
    "wrong_facts",
    "wrong_say",
    "wrong_sales_move",
    "too_generic",
    "acceptable_alternative",
    "gold_too_strict",
    "true_model_failure",
    "dataset_target_issue",
    "training_signal_issue",
    "decoding_issue",
    "latency_issue",
)


def split_path(split: str) -> Path:
    return DATASET_DIR / ("ood_test.jsonl" if split == "ood_test" else f"{split}.jsonl")


def rows_by_case() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for split in AUDIT_SPLITS:
        path = split_path(split)
        for row in read_jsonl(path):
            case_id = str(row.get("case_id") or "")
            if case_id:
                copied = dict(row)
                copied["_audit_split"] = split
                rows[case_id] = copied
    return rows


def train_target_card_counts() -> Counter[str]:
    counter: Counter[str] = Counter()
    path = DATASET_DIR / "mixed_train.jsonl"
    if not path.is_file():
        return counter
    for row in read_jsonl(path):
        counter[str(row.get("target_card_id") or "unknown")] += 1
    return counter


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


def snippet(value: Any, *, limit: int = 160) -> str:
    text = " ".join(str(value or "").split())
    lowered = text.lower()
    if any(term in lowered for term in ("data/private", "private transcript", "normalized_transcript")):
        return "[redacted]"
    if len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def is_latency_issue(case: dict[str, Any]) -> bool:
    latency = case.get("latency_metrics") if isinstance(case.get("latency_metrics"), dict) else {}
    total_ms = latency.get("total_generation_latency_ms")
    return bool(latency.get("timed_out")) or (isinstance(total_ms, (int, float)) and total_ms >= 10000)


def is_too_generic(case: dict[str, Any], predicted: dict[str, Any]) -> bool:
    if int(case.get("generic_label_count") or 0) > 0:
        return True
    say = " ".join(str(predicted.get("say") or "").lower().split())
    generic_phrases = ("good question", "it depends", "i can help", "let me know")
    return any(phrase in say for phrase in generic_phrases)


def classify_case(
    case: dict[str, Any],
    row: dict[str, Any],
    target_card_train_counts: Counter[str],
) -> dict[str, Any]:
    expected = compact_target(row)
    predicted = compact_prediction(case)
    mismatches = field_mismatches(expected, predicted)
    classes: set[str] = set()
    if case.get("schema_valid") is not True or case.get("malformed_output") is True:
        classes.add("schema_failure")
    if case.get("compact_contract_valid") is not True:
        classes.add("compact_contract_failure")
    if case.get("verifier_pass") is not True:
        classes.add("verifier_failure")
    if case.get("safety_pass") is not True:
        classes.add("safety_failure")
    if case.get("strict_gold_semantic_match") is not True:
        classes.add("strict_semantic_failure")
    if case.get("equivalence_match") is not True:
        classes.add("equivalence_failure")
    if case.get("exact_match") is not True:
        classes.add("exact_match_failure")
    if case.get("strict_gold_response_plan_match") is not True or any(field in mismatches for field in PLAN_FIELDS):
        classes.add("response_plan_failure")

    for field in ("act", "sub", "action", "strategy", "buyer", "intent", "rel", "neg", "update", "facts", "say"):
        if field in mismatches:
            classes.add(f"wrong_{field}")
    if "preserve" in mismatches:
        classes.add("wrong_preserve")
    if "avoid" in mismatches:
        classes.add("wrong_avoid")
    if classify_sales_move(expected, predicted):
        classes.add("wrong_sales_move")
    if is_too_generic(case, predicted):
        classes.add("too_generic")
    if "schema_failure" in classes or "compact_contract_failure" in classes or case.get("malformed_output") is True:
        classes.add("decoding_issue")
    if is_latency_issue(case):
        classes.add("latency_issue")

    core_matches = all(expected.get(field) == predicted.get(field) for field in CORE_FIELDS)
    label_matches = all(expected.get(field) == predicted.get(field) for field in LABEL_FIELDS)
    safe_and_valid = (
        case.get("schema_valid") is True
        and case.get("compact_contract_valid") is True
        and case.get("verifier_pass") is True
        and case.get("safety_pass") is True
    )
    acceptable = bool(safe_and_valid and core_matches and not classify_sales_move(expected, predicted))
    if acceptable:
        classes.add("acceptable_alternative")
    if acceptable and ("response_plan_failure" in classes or "exact_match_failure" in classes):
        classes.add("gold_too_strict")
        classes.add("dataset_target_issue")
    if not acceptable:
        classes.add("true_model_failure")

    target_card_id = str(row.get("target_card_id") or case.get("target_card_id") or "unknown")
    train_count = target_card_train_counts.get(target_card_id, 0)
    if train_count <= 3 and not acceptable:
        classes.add("dataset_target_issue")
    if "true_model_failure" in classes and "decoding_issue" not in classes:
        classes.add("training_signal_issue")
    if label_matches and set(mismatches).issubset(set(PLAN_FIELDS)):
        classes.add("acceptable_alternative")

    for name in CLASS_NAMES:
        if name not in classes:
            continue
    return {
        "classes": sorted(classes),
        "field_mismatches": mismatches,
        "expected": expected,
        "predicted": predicted,
    }


def confusion(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
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


def build_audit() -> dict[str, Any]:
    eval_result = read_json(EVAL_RESULT_PATH)
    rows = rows_by_case()
    card_counts = train_target_card_counts()
    failed_records: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    semantic_group_counts: Counter[str] = Counter()
    target_card_counts: Counter[str] = Counter()
    missed_labels: Counter[tuple[str, str]] = Counter()
    wrong_labels: Counter[tuple[str, str]] = Counter()

    for case in eval_cases(eval_result):
        if not eval_failed(case):
            continue
        case_id = str(case.get("case_id") or "")
        row = rows.get(case_id, {})
        classification = classify_case(case, row, card_counts)
        expected = classification["expected"]
        predicted = classification["predicted"]
        split = str(case.get("split") or row.get("_audit_split") or "unknown")
        semantic_group = str(row.get("semantic_group") or case.get("semantic_group") or "unknown")
        target_card_id = str(row.get("target_card_id") or case.get("target_card_id") or "unknown")
        for class_name in classification["classes"]:
            class_counts[class_name] += 1
        split_counts[split] += 1
        semantic_group_counts[semantic_group] += 1
        target_card_counts[target_card_id] += 1
        for field in ("act", "sub", "action", "strategy", "buyer", "intent", "rel", "neg"):
            expected_value = str(expected.get(field) or "")
            predicted_value = str(predicted.get(field) or "")
            if expected_value != predicted_value:
                missed_labels[(field, expected_value)] += 1
                wrong_labels[(field, predicted_value)] += 1
        failed_records.append(
            {
                "case_id": case_id,
                "split": split,
                "semantic_group": semantic_group,
                "target_card_id": target_card_id,
                "source_type": row.get("source_type") or case.get("source_type"),
                "buyer_text_excerpt": snippet(row.get("sanitized_buyer_text")),
                "classes": classification["classes"],
                "field_mismatches": classification["field_mismatches"],
                "expected": compact_public_summary(expected),
                "predicted": compact_public_summary(predicted),
                "predicted_say_excerpt": snippet(predicted.get("say")),
                "compact_contract_errors": [snippet(item, limit=220) for item in case.get("compact_contract_errors") or []],
                "verifier_errors": [snippet(item, limit=220) for item in case.get("verifier_errors") or []],
                "parse_errors": [snippet(item, limit=220) for item in case.get("parse_errors") or []],
                "latency_metrics": case.get("latency_metrics") or {},
            }
        )

    for name in CLASS_NAMES:
        class_counts.setdefault(name, 0)

    verifier_passed_strict_failed = [
        {
            "case_id": record["case_id"],
            "split": record["split"],
            "semantic_group": record["semantic_group"],
            "target_card_id": record["target_card_id"],
            "field_mismatches": record["field_mismatches"],
            "classes": record["classes"],
        }
        for record in failed_records
        if "strict_semantic_failure" in record["classes"] and "verifier_failure" not in record["classes"]
    ]
    schema_or_contract_failed = [
        {
            "case_id": record["case_id"],
            "split": record["split"],
            "target_card_id": record["target_card_id"],
            "classes": record["classes"],
            "compact_contract_errors": record["compact_contract_errors"][:4],
            "parse_errors": record["parse_errors"][:4],
        }
        for record in failed_records
        if "schema_failure" in record["classes"] or "compact_contract_failure" in record["classes"]
    ]
    safe_but_commercially_wrong = [
        {
            "case_id": record["case_id"],
            "split": record["split"],
            "semantic_group": record["semantic_group"],
            "target_card_id": record["target_card_id"],
            "buyer_text_excerpt": record["buyer_text_excerpt"],
            "classes": record["classes"],
            "expected": {field: record["expected"].get(field) for field in CORE_FIELDS},
            "predicted": {field: record["predicted"].get(field) for field in CORE_FIELDS},
        }
        for record in failed_records
        if "safety_failure" not in record["classes"]
        and ("wrong_sales_move" in record["classes"] or "wrong_action" in record["classes"] or "wrong_strategy" in record["classes"])
    ]
    unsafe_or_side_effect_risky = [
        {
            "case_id": record["case_id"],
            "split": record["split"],
            "target_card_id": record["target_card_id"],
            "buyer_text_excerpt": record["buyer_text_excerpt"],
            "classes": record["classes"],
            "verifier_errors": record["verifier_errors"][:4],
            "predicted_say_excerpt": record["predicted_say_excerpt"],
        }
        for record in failed_records
        if "safety_failure" in record["classes"]
    ]

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "eval_result": rel(EVAL_RESULT_PATH),
            "dataset_dir": rel(DATASET_DIR),
        },
        "failed_case_count": len(failed_records),
        "failure_counts_by_class": dict(sorted(class_counts.items())),
        "failure_counts_by_semantic_group": dict(sorted(semantic_group_counts.items())),
        "failure_counts_by_target_card_id": dict(sorted(target_card_counts.items())),
        "failure_counts_by_split": dict(sorted(split_counts.items())),
        "top_expected_labels_missed": [
            {"field": field, "expected": value, "count": count}
            for (field, value), count in missed_labels.most_common(25)
        ],
        "top_predicted_wrong_labels": [
            {"field": field, "predicted": value, "count": count}
            for (field, value), count in wrong_labels.most_common(25)
        ],
        "confusion_matrices": {
            "action": confusion(failed_records, "action"),
            "sub_intent": confusion(failed_records, "sub"),
            "strategy": confusion(failed_records, "strategy"),
        },
        "wrong_output_examples_sanitized": failed_records[:15],
        "verifier_passed_but_strict_semantic_failed": verifier_passed_strict_failed[:60],
        "schema_or_contract_failed_cases": schema_or_contract_failed[:60],
        "safe_but_commercially_wrong_cases": safe_but_commercially_wrong[:60],
        "unsafe_or_side_effect_risky_cases": unsafe_or_side_effect_risky[:60],
        "failed_cases": failed_records,
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


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Summary",
        "",
        f"- status: {result['status']}",
        f"- failed_case_count: {result['failed_case_count']}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- training_rerun: {str(result['training_rerun']).lower()}",
        f"- provider_side_effects_made: {str(result['provider_side_effects_made']).lower()}",
        f"- adapter_live_ready: {str(result['adapter_live_ready']).lower()}",
        f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
        "",
        "## Failure Counts By Class",
        "",
        report_json_block(result["failure_counts_by_class"]),
        "",
        "## Failure Counts By Semantic Group",
        "",
        report_json_block(result["failure_counts_by_semantic_group"]),
        "",
        "## Failure Counts By Target Card",
        "",
        report_json_block(result["failure_counts_by_target_card_id"]),
        "",
        "## Failure Counts By Split",
        "",
        report_json_block(result["failure_counts_by_split"]),
        "",
        "## Top Expected Labels Missed",
        "",
        report_json_block(result["top_expected_labels_missed"][:15]),
        "",
        "## Top Predicted Wrong Labels",
        "",
        report_json_block(result["top_predicted_wrong_labels"][:15]),
        "",
        "## Action Confusion Matrix",
        "",
        report_json_block(result["confusion_matrices"]["action"][:20]),
        "",
        "## Sub-Intent Confusion Matrix",
        "",
        report_json_block(result["confusion_matrices"]["sub_intent"][:20]),
        "",
        "## Strategy Confusion Matrix",
        "",
        report_json_block(result["confusion_matrices"]["strategy"][:20]),
        "",
        "## Sanitized Wrong Output Examples",
        "",
        report_json_block(result["wrong_output_examples_sanitized"][:8]),
        "",
        "## Verifier Passed But Strict Semantic Failed",
        "",
        report_json_block(result["verifier_passed_but_strict_semantic_failed"][:20]),
        "",
        "## Schema Or Contract Failed",
        "",
        report_json_block(result["schema_or_contract_failed_cases"][:20]),
        "",
        "## Safe But Commercially Wrong",
        "",
        report_json_block(result["safe_but_commercially_wrong_cases"][:20]),
        "",
        "## Unsafe Or Side-Effect Risky",
        "",
        report_json_block(result["unsafe_or_side_effect_risky_cases"][:20]),
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def main() -> int:
    result = build_audit()
    write_json(RESULT_PATH, result)
    write_report(result)
    print(
        json.dumps(
            {
                "experiment_id": EXPERIMENT_ID,
                "status": result["status"],
                "failed_case_count": result["failed_case_count"],
                "top_classes": counter_records(Counter(result["failure_counts_by_class"]), limit=8),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
