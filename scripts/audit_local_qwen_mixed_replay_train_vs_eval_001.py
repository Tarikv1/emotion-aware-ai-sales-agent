#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    audit_side_effects,
    compact_prediction,
    compact_target,
    eval_failed,
    read_json,
    read_jsonl,
    rel,
    report_json_block,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAIN-VS-EVAL-AUDIT-001"
EVAL_ID = "LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001"
MIXED_DATASET_ID = "LOCAL-QWEN-MIXED-REPLAY-TRAINING-DATASET-001"
BALANCED_DATASET_ID = "LOCAL-QWEN-BALANCED-SFT-DATASET-001"
FAILURE_AUDIT_ID = "LOCAL-QWEN-MIXED-REPLAY-EVAL-FAILURE-AUDIT-001"
EVAL_RESULT_PATH = GENERATED_DIR / EVAL_ID / "result.json"
MIXED_DATASET_DIR = GENERATED_DIR / MIXED_DATASET_ID
BALANCED_DATASET_DIR = GENERATED_DIR / BALANCED_DATASET_ID
FAILURE_AUDIT_PATH = GENERATED_DIR / FAILURE_AUDIT_ID / "result.json"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EVAL_SPLITS = ("validation", "test", "ood_test")


def rows_for_split(dataset_dir: Path, split: str) -> list[dict[str, Any]]:
    path = dataset_dir / ("ood_test.jsonl" if split == "ood_test" else f"{split}.jsonl")
    return read_jsonl(path) if path.is_file() else []


def rows_by_case(dataset_dir: Path, splits: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for split in splits:
        for row in rows_for_split(dataset_dir, split):
            case_id = str(row.get("case_id") or "")
            if case_id:
                copied = dict(row)
                copied["_audit_split"] = split
                rows[case_id] = copied
    return rows


def eval_split_payloads(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    adapter = result.get("mixed_replay_adapter") if isinstance(result.get("mixed_replay_adapter"), dict) else {}
    splits = adapter.get("splits") if isinstance(adapter.get("splits"), dict) else {}
    return {split: payload for split, payload in splits.items() if isinstance(payload, dict)}


def metric_rate(metrics: dict[str, Any], key: str) -> float:
    count = int(metrics.get("case_count") or 0)
    return round((int(metrics.get(key) or 0) / count), 4) if count else 0.0


def split_rate_summary(payloads: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for split, payload in payloads.items():
        metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
        summary[split] = {
            "case_count": metrics.get("case_count", payload.get("case_count")),
            "schema_rate": metric_rate(metrics, "schema_valid_count"),
            "compact_contract_rate": metric_rate(metrics, "compact_contract_valid_count"),
            "verifier_rate": metric_rate(metrics, "verifier_pass_count"),
            "strict_semantic_rate": metric_rate(metrics, "strict_gold_semantic_match_count"),
            "response_plan_rate": metric_rate(metrics, "strict_gold_response_plan_match_count"),
            "equivalence_rate": metric_rate(metrics, "equivalence_match_count"),
            "exact_rate": metric_rate(metrics, "exact_match_count"),
            "safety_rate": metric_rate(metrics, "safety_pass_count"),
        }
    return summary


def case_pass(case: dict[str, Any], *, strict_response: bool = False) -> bool:
    if strict_response:
        return not eval_failed(case)
    return (
        case.get("schema_valid") is True
        and case.get("compact_contract_valid") is True
        and case.get("verifier_pass") is True
        and case.get("safety_pass") is True
        and case.get("strict_gold_semantic_match") is True
    )


def group_performance(
    cases: list[dict[str, Any]],
    rows: dict[str, dict[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    totals: Counter[str] = Counter()
    passes: Counter[str] = Counter()
    response_passes: Counter[str] = Counter()
    for case in cases:
        row = rows.get(str(case.get("case_id") or ""), {})
        value = str(row.get(key) or case.get(key) or "unknown")
        totals[value] += 1
        if case_pass(case):
            passes[value] += 1
        if case_pass(case, strict_response=True):
            response_passes[value] += 1
    records: list[dict[str, Any]] = []
    for value, total in totals.most_common():
        records.append(
            {
                key: value,
                "case_count": total,
                "semantic_pass_count": passes[value],
                "semantic_pass_rate": round(passes[value] / total, 4) if total else 0.0,
                "full_pass_count": response_passes[value],
                "full_pass_rate": round(response_passes[value] / total, 4) if total else 0.0,
            }
        )
    return records


def row_text_len(row: dict[str, Any]) -> int:
    return len(str(row.get("sanitized_buyer_text") or ""))


def target_json_len(row: dict[str, Any]) -> int:
    return len(json.dumps(compact_target(row), sort_keys=True, ensure_ascii=False))


def bucket_lengths(cases: list[dict[str, Any]], rows: dict[str, dict[str, Any]], measure: str) -> dict[str, Any]:
    values: list[tuple[int, bool]] = []
    for case in cases:
        row = rows.get(str(case.get("case_id") or ""), {})
        length = row_text_len(row) if measure == "buyer_text" else target_json_len(row)
        values.append((length, case_pass(case)))
    if not values:
        return {"count": 0}
    sorted_lengths = sorted(length for length, _ in values)
    median = statistics.median(sorted_lengths)
    low = [(length, passed) for length, passed in values if length <= median]
    high = [(length, passed) for length, passed in values if length > median]

    def summarize(items: list[tuple[int, bool]]) -> dict[str, Any]:
        if not items:
            return {"case_count": 0, "average_length": 0, "semantic_pass_rate": 0}
        return {
            "case_count": len(items),
            "average_length": round(sum(length for length, _ in items) / len(items), 2),
            "semantic_pass_rate": round(sum(1 for _, passed in items if passed) / len(items), 4),
        }

    return {"median": median, "low_or_equal": summarize(low), "high": summarize(high)}


def label_counts(rows: list[dict[str, Any]], field: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = compact_target(row).get(field)
        if isinstance(value, str):
            counter[value] += 1
    return counter


def rare_label_failure_summary(cases: list[dict[str, Any]], rows: dict[str, dict[str, Any]], train_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    summary: dict[str, list[dict[str, Any]]] = {}
    for field in ("act", "sub", "action", "strategy"):
        train_counter = label_counts(train_rows, field)
        failed_counter: Counter[str] = Counter()
        total_counter: Counter[str] = Counter()
        for case in cases:
            row = rows.get(str(case.get("case_id") or ""), {})
            expected = str(compact_target(row).get(field) or "")
            if not expected:
                continue
            total_counter[expected] += 1
            if not case_pass(case):
                failed_counter[expected] += 1
        records: list[dict[str, Any]] = []
        for label, train_count in train_counter.most_common()[::-1]:
            heldout_total = total_counter.get(label, 0)
            if train_count > 5 and heldout_total == 0:
                continue
            records.append(
                {
                    "label": label,
                    "train_count": train_count,
                    "heldout_case_count": heldout_total,
                    "heldout_semantic_failure_count": failed_counter.get(label, 0),
                    "heldout_semantic_failure_rate": round(failed_counter.get(label, 0) / heldout_total, 4) if heldout_total else None,
                }
            )
        summary[field] = records[:25]
    return summary


def say_diversity_by_card(train_rows: list[dict[str, Any]], cases: list[dict[str, Any]], rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    say_by_card: dict[str, set[str]] = defaultdict(set)
    train_by_card: Counter[str] = Counter()
    for row in train_rows:
        card = str(row.get("target_card_id") or "unknown")
        train_by_card[card] += 1
        say = str(compact_target(row).get("say") or "")
        if say:
            say_by_card[card].add(say)
    heldout_total: Counter[str] = Counter()
    heldout_fail: Counter[str] = Counter()
    for case in cases:
        row = rows.get(str(case.get("case_id") or ""), {})
        card = str(row.get("target_card_id") or case.get("target_card_id") or "unknown")
        heldout_total[card] += 1
        if not case_pass(case):
            heldout_fail[card] += 1
    records: list[dict[str, Any]] = []
    for card, total in heldout_total.most_common():
        records.append(
            {
                "target_card_id": card,
                "train_count": train_by_card.get(card, 0),
                "unique_train_say_count": len(say_by_card.get(card, set())),
                "heldout_case_count": total,
                "heldout_semantic_failure_count": heldout_fail.get(card, 0),
                "heldout_semantic_failure_rate": round(heldout_fail.get(card, 0) / total, 4) if total else 0,
            }
        )
    return records


def source_or_group_category(row: dict[str, Any]) -> str:
    group = str(row.get("semantic_group") or "")
    card = str(row.get("target_card_id") or "")
    text = f"{group} {card}".lower()
    if "safety" in text or "boundary" in text or "negative" in text or "wrong_product" in text:
        return "safety_boundary"
    if "price" in text or "value" in text or "recommend" in text or "plan_fit" in text:
        return "price_value_recommendation"
    if "explanation" in text or "orientation" in text or "plan_category" in text:
        return "explanation"
    return "other_sales"


def category_performance(cases: list[dict[str, Any]], rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    totals: Counter[str] = Counter()
    fails: Counter[str] = Counter()
    verifier_fails: Counter[str] = Counter()
    for case in cases:
        row = rows.get(str(case.get("case_id") or ""), {})
        category = source_or_group_category(row)
        totals[category] += 1
        if not case_pass(case):
            fails[category] += 1
        if case.get("verifier_pass") is not True or case.get("safety_pass") is not True:
            verifier_fails[category] += 1
    return [
        {
            "category": category,
            "case_count": count,
            "semantic_failure_count": fails[category],
            "semantic_failure_rate": round(fails[category] / count, 4) if count else 0,
            "safety_or_verifier_failure_count": verifier_fails[category],
        }
        for category, count in totals.most_common()
    ]


def build_audit() -> dict[str, Any]:
    eval_result = read_json(EVAL_RESULT_PATH)
    failure_audit = read_json(FAILURE_AUDIT_PATH)
    mixed_result = read_json(MIXED_DATASET_DIR / "result.json")
    balanced_result = read_json(BALANCED_DATASET_DIR / "result.json")
    split_payloads = eval_split_payloads(eval_result)
    rows = rows_by_case(MIXED_DATASET_DIR, ("mixed_train", *EVAL_SPLITS))
    train_rows = rows_for_split(MIXED_DATASET_DIR, "mixed_train")
    eval_cases = [
        case
        for split in EVAL_SPLITS
        for case in (split_payloads.get(split, {}).get("cases") or [])
        if isinstance(case, dict)
    ]
    train_cases = [case for case in (split_payloads.get("train_sample", {}).get("cases") or []) if isinstance(case, dict)]
    heldout_rows = rows_by_case(MIXED_DATASET_DIR, EVAL_SPLITS)
    split_rates = split_rate_summary(split_payloads)

    train_semantic_rate = split_rates.get("train_sample", {}).get("strict_semantic_rate", 0)
    validation_semantic_rate = split_rates.get("validation", {}).get("strict_semantic_rate", 0)
    test_semantic_rate = split_rates.get("test", {}).get("strict_semantic_rate", 0)
    heldout_semantic_rate = round(
        (
            int(split_payloads.get("validation", {}).get("metrics", {}).get("strict_gold_semantic_match_count") or 0)
            + int(split_payloads.get("test", {}).get("metrics", {}).get("strict_gold_semantic_match_count") or 0)
        )
        / max(
            1,
            int(split_payloads.get("validation", {}).get("metrics", {}).get("case_count") or 0)
            + int(split_payloads.get("test", {}).get("metrics", {}).get("case_count") or 0),
        ),
        4,
    )

    train_card_counts: Counter[str] = Counter(str(row.get("target_card_id") or "unknown") for row in train_rows)
    heldout_fail_by_card: Counter[str] = Counter()
    heldout_total_by_card: Counter[str] = Counter()
    for case in eval_cases:
        row = heldout_rows.get(str(case.get("case_id") or ""), {})
        card = str(row.get("target_card_id") or case.get("target_card_id") or "unknown")
        heldout_total_by_card[card] += 1
        if not case_pass(case):
            heldout_fail_by_card[card] += 1

    underrepresented_cards = [
        {"target_card_id": card, "train_count": count}
        for card, count in sorted(train_card_counts.items(), key=lambda item: (item[1], item[0]))
        if count <= 5
    ]
    represented_but_fail = [
        {
            "target_card_id": card,
            "train_count": train_card_counts.get(card, 0),
            "heldout_case_count": total,
            "heldout_semantic_failure_count": heldout_fail_by_card.get(card, 0),
            "heldout_semantic_failure_rate": round(heldout_fail_by_card.get(card, 0) / total, 4) if total else 0,
        }
        for card, total in heldout_total_by_card.most_common()
        if train_card_counts.get(card, 0) > 0 and heldout_fail_by_card.get(card, 0) > 0
    ]
    represented_but_fail.sort(key=lambda item: (-item["heldout_semantic_failure_count"], item["target_card_id"]))

    train_group = group_performance(train_cases, rows, "semantic_group")
    heldout_group = group_performance(eval_cases, heldout_rows, "semantic_group")
    heldout_group_by_name = {item["semantic_group"]: item for item in heldout_group}
    train_pass_heldout_fail = [
        {
            "semantic_group": item["semantic_group"],
            "train_sample_semantic_pass_rate": item["semantic_pass_rate"],
            "heldout_semantic_pass_rate": heldout_group_by_name.get(item["semantic_group"], {}).get("semantic_pass_rate"),
            "heldout_case_count": heldout_group_by_name.get(item["semantic_group"], {}).get("case_count", 0),
        }
        for item in train_group
        if item["semantic_pass_rate"] >= 0.5
        and heldout_group_by_name.get(item["semantic_group"], {}).get("semantic_pass_rate", 1) < 0.5
    ]

    failure_classes = failure_audit.get("failure_counts_by_class") if isinstance(failure_audit.get("failure_counts_by_class"), dict) else {}
    label_confusions = sum(int(failure_classes.get(name, 0) or 0) for name in ("wrong_act", "wrong_sub", "wrong_action", "wrong_strategy"))
    format_instability = sum(int(failure_classes.get(name, 0) or 0) for name in ("schema_failure", "compact_contract_failure", "decoding_issue"))
    safety_fails = int(failure_classes.get("safety_failure", 0) or 0)
    gold_strict = int(failure_classes.get("gold_too_strict", 0) or 0)

    classification = {
        "overfitting": bool(train_semantic_rate >= heldout_semantic_rate + 0.25),
        "underfitting": bool(split_rates.get("train_sample", {}).get("response_plan_rate", 0) < 0.25),
        "label_sparsity": bool(underrepresented_cards or any(item.get("train_count", 0) <= 5 for item in represented_but_fail[:10])),
        "label_confusion": bool(label_confusions >= 30),
        "output_format_instability": bool(format_instability >= 10),
        "sales_action_decision_failure": bool(int(failure_classes.get("wrong_sales_move", 0) or 0) >= 10),
        "safety_verifier_conflict": bool(safety_fails >= 10),
        "acceptable_gold_strictness_issue": bool(gold_strict >= 20),
    }

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "eval_result": rel(EVAL_RESULT_PATH),
            "mixed_replay_dataset_result": rel(MIXED_DATASET_DIR / "result.json"),
            "balanced_sft_dataset_result": rel(BALANCED_DATASET_DIR / "result.json"),
            "failure_audit_result": rel(FAILURE_AUDIT_PATH),
        },
        "split_rate_summary": split_rates,
        "train_sample_vs_heldout": {
            "train_sample_strict_semantic_rate": train_semantic_rate,
            "validation_strict_semantic_rate": validation_semantic_rate,
            "test_strict_semantic_rate": test_semantic_rate,
            "validation_test_strict_semantic_rate": heldout_semantic_rate,
            "train_sample_much_better_than_heldout": train_semantic_rate >= heldout_semantic_rate + 0.25,
            "caveat": "train_sample is the first 40 mixed-train rows, not a full train-set evaluation.",
        },
        "semantic_groups_pass_train_fail_heldout": train_pass_heldout_fail,
        "semantic_group_performance": {
            "train_sample": train_group,
            "heldout": heldout_group,
        },
        "target_cards_underrepresented_in_train": underrepresented_cards[:50],
        "target_cards_represented_but_still_fail": represented_but_fail[:50],
        "source_type_correlation": group_performance(eval_cases, heldout_rows, "source_type"),
        "buyer_text_length_correlation": bucket_lengths(eval_cases, heldout_rows, "buyer_text"),
        "target_json_length_correlation": bucket_lengths(eval_cases, heldout_rows, "target_json"),
        "say_diversity_correlation": say_diversity_by_card(train_rows, eval_cases, heldout_rows)[:50],
        "rare_label_failure_correlation": rare_label_failure_summary(eval_cases, heldout_rows, train_rows),
        "sales_safety_explanation_category_performance": category_performance(eval_cases, heldout_rows),
        "balanced_dataset_context": {
            "total_rows": balanced_result.get("total_rows"),
            "split_counts": balanced_result.get("split_counts"),
            "target_card_usage": balanced_result.get("target_card_usage"),
        },
        "mixed_dataset_context": {
            "mixed_train_row_count": mixed_result.get("mixed_train_row_count"),
            "split_counts": mixed_result.get("split_counts"),
            "source_type_counts": mixed_result.get("source_type_counts"),
            "semantic_group_counts": mixed_result.get("semantic_group_counts"),
            "target_card_counts": mixed_result.get("target_card_counts"),
        },
        "classification": classification,
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
        f"- train_sample_much_better_than_heldout: {str(result['train_sample_vs_heldout']['train_sample_much_better_than_heldout']).lower()}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- training_rerun: {str(result['training_rerun']).lower()}",
        f"- adapter_live_ready: {str(result['adapter_live_ready']).lower()}",
        f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
        "",
        "## Train Sample Vs Held-Out",
        "",
        report_json_block(result["train_sample_vs_heldout"]),
        "",
        "## Classification",
        "",
        report_json_block(result["classification"]),
        "",
        "## Semantic Groups Passing Train But Failing Held-Out",
        "",
        report_json_block(result["semantic_groups_pass_train_fail_heldout"]),
        "",
        "## Target Cards Underrepresented In Train",
        "",
        report_json_block(result["target_cards_underrepresented_in_train"][:30]),
        "",
        "## Target Cards Represented But Still Fail",
        "",
        report_json_block(result["target_cards_represented_but_still_fail"][:30]),
        "",
        "## Source Type Correlation",
        "",
        report_json_block(result["source_type_correlation"]),
        "",
        "## Length Correlations",
        "",
        report_json_block(
            {
                "buyer_text_length": result["buyer_text_length_correlation"],
                "target_json_length": result["target_json_length_correlation"],
            }
        ),
        "",
        "## Say Diversity Correlation",
        "",
        report_json_block(result["say_diversity_correlation"][:20]),
        "",
        "## Rare Label Failure Correlation",
        "",
        report_json_block(result["rare_label_failure_correlation"]),
        "",
        "## Safety/Sales/Explanation Category Performance",
        "",
        report_json_block(result["sales_safety_explanation_category_performance"]),
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
                "train_vs_heldout": result["train_sample_vs_heldout"],
                "classification": result["classification"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
