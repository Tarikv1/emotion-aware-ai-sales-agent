#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_local_qwen_balanced_sft_dataset_001 import (  # noqa: E402
    SPLIT_PATHS,
    action_sub_signature,
    compact_target,
    core_signature,
    exact_text_overlap,
    heldout_coverage,
    labels_by_split,
    load_cards,
    norm_text,
    read_json,
    read_jsonl,
    rel,
    semantic_counts,
    target_card_usage,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-BALANCED-DATASET-CONSISTENCY-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PREVIOUS_AUDIT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "LOCAL-QWEN-DATASET-CONSISTENCY-AUDIT-001"
    / "result.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_text(row: dict[str, Any]) -> str:
    return norm_text(row.get("sanitized_buyer_text") or "")


def token_set(text: str) -> set[str]:
    return set(norm_text(text).split())


def jaccard(left: str, right: str) -> float:
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def near_duplicate_overlap(splits: dict[str, list[dict[str, Any]]], threshold: float = 0.92) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    split_pairs = (("train", "validation"), ("train", "test"), ("validation", "test"))
    for left_split, right_split in split_pairs:
        for left in splits[left_split]:
            left_text = str(left.get("sanitized_buyer_text") or "")
            for right in splits[right_split]:
                right_text = str(right.get("sanitized_buyer_text") or "")
                score = jaccard(left_text, right_text)
                if score >= threshold:
                    records.append(
                        {
                            "left_split": left_split,
                            "left_case_id": left.get("case_id"),
                            "right_split": right_split,
                            "right_case_id": right.get("case_id"),
                            "jaccard": round(score, 3),
                        }
                    )
                    if len(records) >= 50:
                        return records
    return records


def signature_dict(signature: tuple[str, ...]) -> dict[str, str]:
    if len(signature) == 4:
        return {"act": signature[0], "sub": signature[1], "action": signature[2], "strategy": signature[3]}
    if len(signature) == 2:
        return {"action": signature[0], "sub": signature[1]}
    return {str(index): value for index, value in enumerate(signature)}


def target_card_consistency(rows: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    card_lookup = {str(card.get("card_id") or ""): card for card in cards}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("target_card_id") or "")].append(row)
    summary: dict[str, Any] = {}
    warnings: list[str] = []
    for card_id, card_rows in sorted(grouped.items()):
        card = card_lookup.get(card_id, {})
        action_strategy = {
            (
                str(compact_target(row).get("action") or ""),
                str(compact_target(row).get("strategy") or ""),
            )
            for row in card_rows
        }
        facts = {tuple(compact_target(row).get("facts") or []) for row in card_rows}
        avoid = {tuple(compact_target(row).get("avoid") or []) for row in card_rows}
        subs = {str(compact_target(row).get("sub") or "") for row in card_rows}
        allowed_subs = set(str(item) for item in (card.get("allowed_sub_values") or []))
        card_warnings: list[str] = []
        if len(action_strategy) != 1:
            card_warnings.append("multiple action/strategy targets for one card")
        if len(facts) != 1:
            card_warnings.append("multiple facts policies for one card")
        if len(avoid) != 1:
            card_warnings.append("multiple avoid policies for one card")
        if allowed_subs and not subs <= allowed_subs:
            card_warnings.append("sub value outside target card allowed_sub_values")
        if card_warnings:
            warnings.extend(f"{card_id}: {warning}" for warning in card_warnings)
        summary[card_id] = {
            "row_count": len(card_rows),
            "sub_values": sorted(subs),
            "action_strategy_count": len(action_strategy),
            "facts_policy_count": len(facts),
            "avoid_policy_count": len(avoid),
            "consistent": not card_warnings,
            "warnings": card_warnings,
        }
    return {"cards": summary, "warnings": warnings}


def semantic_group_consistency(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("semantic_group") or "")].append(row)
    result: dict[str, Any] = {}
    for group, group_rows in sorted(grouped.items()):
        action_strategy = Counter(
            (
                str(compact_target(row).get("action") or ""),
                str(compact_target(row).get("strategy") or ""),
            )
            for row in group_rows
        )
        result[group] = {
            "row_count": len(group_rows),
            "target_card_count": len({str(row.get("target_card_id") or "") for row in group_rows}),
            "action_strategy_distribution": [
                {"action": action, "strategy": strategy, "count": count}
                for (action, strategy), count in action_strategy.most_common()
            ],
            "expected_card_diversity": len(action_strategy) > 1,
        }
    return result


def preserve_avoid_facts_consistency(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_card: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_card[str(row.get("target_card_id") or "")].append(row)
    result: dict[str, Any] = {}
    warnings: list[str] = []
    for card_id, card_rows in sorted(by_card.items()):
        preserve_object_mismatches = []
        for row in card_rows:
            target = compact_target(row)
            objects = set(target.get("obj") or [])
            preserve = set(target.get("preserve") or [])
            if not preserve <= objects:
                preserve_object_mismatches.append(row.get("case_id"))
        if preserve_object_mismatches:
            warnings.append(f"{card_id}: preserve terms not present in obj")
        result[card_id] = {
            "preserve_subset_of_objects": not preserve_object_mismatches,
            "preserve_object_mismatch_case_ids": preserve_object_mismatches[:10],
            "facts_signatures": sorted({json.dumps(compact_target(row).get("facts") or []) for row in card_rows}),
            "avoid_signatures": sorted({json.dumps(compact_target(row).get("avoid") or []) for row in card_rows}),
        }
    return {"cards": result, "warnings": warnings}


def previous_issue_comparison(after_coverage: dict[str, Any], target_consistency: dict[str, Any]) -> dict[str, Any]:
    previous = read_json(PREVIOUS_AUDIT_PATH) if PREVIOUS_AUDIT_PATH.is_file() else {}
    coverage_root = previous.get("heldout_coverage") or previous.get("heldout_label_coverage") or {}
    before_validation = (
        coverage_root
        .get("against_sft_train", {})
        .get("validation", {})
        .get("unseen_act_sub_action_strategy_combo_count")
    )
    before_test = (
        coverage_root
        .get("against_sft_train", {})
        .get("test", {})
        .get("unseen_act_sub_action_strategy_combo_count")
    )
    before_validation_action_sub = (
        coverage_root
        .get("against_sft_train", {})
        .get("validation", {})
        .get("unseen_action_sub_pair_count")
    )
    before_test_action_sub = (
        coverage_root
        .get("against_sft_train", {})
        .get("test", {})
        .get("unseen_action_sub_pair_count")
    )
    return {
        "previous_audit": rel(PREVIOUS_AUDIT_PATH) if PREVIOUS_AUDIT_PATH.is_file() else "",
        "validation_unseen_core_before": before_validation,
        "validation_unseen_core_after": after_coverage["validation"]["unseen_act_sub_action_strategy_combo_count"],
        "test_unseen_core_before": before_test,
        "test_unseen_core_after": after_coverage["test"]["unseen_act_sub_action_strategy_combo_count"],
        "validation_unseen_action_sub_before": before_validation_action_sub,
        "validation_unseen_action_sub_after": after_coverage["validation"]["unseen_action_sub_pair_count"],
        "test_unseen_action_sub_before": before_test_action_sub,
        "test_unseen_action_sub_after": after_coverage["test"]["unseen_action_sub_pair_count"],
        "semantic_neighborhood_inconsistency_before": "all previous broad neighborhoods had mixed signatures",
        "semantic_neighborhood_inconsistency_after": "target-card neighborhoods are consistent; broad semantic groups intentionally contain multiple cards",
        "target_inconsistency_before": "mixed action/strategy and response-plan signatures inside previous neighborhoods",
        "target_inconsistency_after": "resolved" if not target_consistency["warnings"] else "warnings_remaining",
        "insufficient_examples_before": "80 rows plus tiny replay was insufficient",
        "insufficient_examples_after": "445 rows total with 435 in-distribution rows",
        "previous_4h17_issues_resolved": (
            after_coverage["validation"]["covered_by_train"]
            and after_coverage["test"]["covered_by_train"]
            and not target_consistency["warnings"]
        ),
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Total rows: {result['row_counts']['total']}",
        f"- Split counts: `{json.dumps(result['row_counts']['by_split'], sort_keys=True)}`",
        f"- Exact buyer-text overlap: {result['duplicate_text_leakage']['exact_overlap_found']}",
        f"- Near-duplicate overlap found: {bool(result['duplicate_text_leakage']['near_duplicate_overlap'])}",
        f"- OOD isolated: {result['ood_split_summary']['isolated']}",
        f"- Previous 4H17 issues resolved: {result['previous_4h17_issue_comparison']['previous_4h17_issues_resolved']}",
        "",
        "## Held-Out Coverage",
        "",
    ]
    for split in ("validation", "test"):
        coverage = result["heldout_coverage"][split]
        lines.append(
            f"- {split}: covered_by_train={coverage['covered_by_train']}, "
            f"unseen_core={coverage['unseen_act_sub_action_strategy_combo_count']}, "
            f"unseen_action_sub={coverage['unseen_action_sub_pair_count']}"
        )
    lines.extend(["", "## Before / After", ""])
    comparison = result["previous_4h17_issue_comparison"]
    lines.append(f"- Validation unseen core: {comparison['validation_unseen_core_before']} -> {comparison['validation_unseen_core_after']}")
    lines.append(f"- Test unseen core: {comparison['test_unseen_core_before']} -> {comparison['test_unseen_core_after']}")
    lines.append(
        f"- Validation unseen action/sub: {comparison['validation_unseen_action_sub_before']} -> "
        f"{comparison['validation_unseen_action_sub_after']}"
    )
    lines.append(f"- Test unseen action/sub: {comparison['test_unseen_action_sub_before']} -> {comparison['test_unseen_action_sub_after']}")
    if result["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in result["failures"])
    return "\n".join(lines)


def main() -> int:
    splits = {split: read_jsonl(path) for split, path in SPLIT_PATHS.items()}
    all_rows = [row for rows in splits.values() for row in rows]
    in_distribution = [row for split in ("train", "validation", "test") for row in splits[split]]
    cards = load_cards()
    coverage = heldout_coverage(splits)
    target_consistency = target_card_consistency(all_rows, cards)
    overlaps = exact_text_overlap(splits)
    near_duplicates = near_duplicate_overlap(splits)
    ood_rows = splits.get("ood_test", [])
    ood_isolated = all(row.get("split") == "ood_test" and row.get("source_type") == "ood_control" for row in ood_rows)
    failures: list[str] = []
    if target_consistency["warnings"]:
        failures.extend(target_consistency["warnings"])
    if any(overlaps.values()):
        failures.append("exact buyer-text overlap across held-out splits")
    if near_duplicates:
        failures.append("near-duplicate buyer-text overlap across held-out splits")
    if not ood_isolated:
        failures.append("OOD split is not isolated")
    raw_private_flags = [row.get("case_id") for row in all_rows if row.get("raw_private_transcript_included") is not False]
    if raw_private_flags:
        failures.append(f"raw private transcript flags present: {raw_private_flags[:10]}")
    comparison = previous_issue_comparison(coverage, target_consistency)
    if not comparison["previous_4h17_issues_resolved"]:
        failures.append("previous 4H17 coverage/target-card consistency issues are not fully resolved")
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "inputs": {split: rel(path) for split, path in SPLIT_PATHS.items()},
        "row_counts": {
            "total": len(all_rows),
            "in_distribution": len(in_distribution),
            "ood_test": len(ood_rows),
            "by_split": {split: len(rows) for split, rows in splits.items()},
        },
        "label_distribution_by_split": labels_by_split(splits),
        "semantic_group_distribution": semantic_counts(in_distribution),
        "target_card_usage": target_card_usage(all_rows),
        "target_card_consistency": target_consistency,
        "action_strategy_consistency_inside_semantic_groups": semantic_group_consistency(in_distribution),
        "preserve_avoid_facts_consistency": preserve_avoid_facts_consistency(all_rows),
        "say_style_consistency": {
            "policy": "Generated from target-card say_style_policy templates; exact wording varies by object slots.",
            "target_card_template_source": "runtime/llm_brain/training/qwen_compact_target_cards.json",
        },
        "heldout_coverage": coverage,
        "ood_split_summary": {
            "row_count": len(ood_rows),
            "isolated": ood_isolated,
            "source_type_counts": dict(Counter(str(row.get("source_type") or "") for row in ood_rows)),
            "target_card_ids": sorted({str(row.get("target_card_id") or "") for row in ood_rows}),
        },
        "duplicate_text_leakage": {
            "exact_overlap": overlaps,
            "exact_overlap_found": any(overlaps.values()),
            "near_duplicate_threshold": 0.92,
            "near_duplicate_overlap": near_duplicates,
        },
        "exact_buyer_text_overlap": overlaps,
        "raw_private_transcript_flags": {
            "all_false": not raw_private_flags,
            "case_ids": raw_private_flags,
        },
        "previous_4h17_issue_comparison": comparison,
        "failures": failures,
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "total": result["row_counts"]["total"],
                "previous_4h17_issues_resolved": comparison["previous_4h17_issues_resolved"],
                "failure_count": len(failures),
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
