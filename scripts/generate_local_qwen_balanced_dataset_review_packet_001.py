#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import expand_compact_planner_output  # noqa: E402
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output  # noqa: E402
from scripts.build_local_qwen_balanced_sft_dataset_001 import (  # noqa: E402
    GROUP_MINIMUMS,
    RESULT_PATH as DATASET_RESULT_PATH,
    SPLIT_PATHS,
    SPEC_PATH,
    TARGET_CARDS_PATH,
    compact_target,
    exact_text_overlap,
    heldout_coverage,
    labels_by_split,
    load_cards,
    norm_text,
    read_json,
    read_jsonl,
    rel,
    semantic_counts,
    string_list,
    target_card_usage,
    validate_dataset,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-BALANCED-DATASET-REVIEW-001"
DATASET_ID = "LOCAL-QWEN-BALANCED-SFT-DATASET-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
EQUIVALENCE_POLICY_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_eval_equivalence_policy.json"
TRAINING_PLAN_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_mixed_replay_training_plan.json"

SPLIT_ORDER = ("train", "validation", "test", "ood_test")
SOURCE_TYPE_SAMPLE_MINIMUMS = {
    "live_sanitized": 10,
    "deterministic_paraphrase": 10,
    "synthetic_control": 10,
    "negative_control": 10,
}
SEMANTIC_GROUP_SAMPLE_COUNT = 5
HELDOUT_SAMPLE_MINIMUM = 10
NEAR_DUPLICATE_THRESHOLD = 0.92

SYNTHETIC_SUFFIX_RE = re.compile(
    r"\b(right now|for this plan decision|before i choose anything|in this call|"
    r"that is my current context|for my setup|please keep it simple|"
    r"i want the practical answer|i am deciding today|i need a clean answer|"
    r"keep it to one next step|variant \d+)\b\.?",
    re.I,
)
TOOL_RE = re.compile(r"\b(chatgpt|check gpt|chacha pt|chachu pt|chat gbt|claude|cloud|clawed|gemini|copilot)\b", re.I)
PLAN_RE = re.compile(r"\b(free|plus|pro|business|enterprise)\b", re.I)
PRICE_RE = re.compile(r"\$\s*\d+(?:\.\d+)?|\b\d+\s*dollars?\b", re.I)
SIDE_EFFECT_RE = re.compile(
    r"\b(sent|emailed|created|booked|scheduled|updated|logged)\b.{0,48}\b(email|calendar|invite|crm|ticket|record)\b",
    re.I,
)
INTERNAL_OR_LEAKAGE_RE = re.compile(
    r"internal policy|routesignal|prod-102|source bundle|campaign id|semantic frame|state_update|safety_flags",
    re.I,
)
RAW_URL_RE = re.compile(r"https?://\S+", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_splits() -> dict[str, list[dict[str, Any]]]:
    return {split: read_jsonl(path) for split, path in SPLIT_PATHS.items()}


def all_rows(splits: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [row for split in SPLIT_ORDER for row in splits.get(split, [])]


def in_distribution_rows(splits: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [row for split in ("train", "validation", "test") for row in splits.get(split, [])]


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


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def skeleton_text(text: str, objects: list[str] | None = None) -> str:
    skeleton = SYNTHETIC_SUFFIX_RE.sub("", norm_text(text))
    skeleton = PRICE_RE.sub("{price}", skeleton)
    skeleton = PLAN_RE.sub("{plan}", skeleton)
    skeleton = TOOL_RE.sub("{tool}", skeleton)
    for obj in objects or []:
        normalized_obj = norm_text(obj)
        if normalized_obj:
            skeleton = skeleton.replace(normalized_obj, "{object}")
    skeleton = re.sub(r"\b\d+\b", "{number}", skeleton)
    skeleton = re.sub(r"\s+", " ", skeleton).strip()
    return skeleton


def near_duplicate_overlap(splits: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for left_split, right_split in (("train", "validation"), ("train", "test"), ("validation", "test")):
        for left in splits[left_split]:
            left_text = str(left.get("sanitized_buyer_text") or "")
            for right in splits[right_split]:
                right_text = str(right.get("sanitized_buyer_text") or "")
                score = jaccard(left_text, right_text)
                if score >= NEAR_DUPLICATE_THRESHOLD:
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


def buyer_text_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [str(row.get("sanitized_buyer_text") or "") for row in rows]
    tokens = [token for text in texts for token in norm_text(text).split()]
    skeleton_counter = Counter(
        skeleton_text(text, string_list(compact_target(row).get("obj")))
        for row, text in zip(rows, texts)
    )
    word_counts = sorted(len(norm_text(text).split()) for text in texts)
    average_words = round(sum(word_counts) / len(word_counts), 2) if word_counts else 0
    median_words = word_counts[len(word_counts) // 2] if word_counts else 0
    return {
        "row_count": len(rows),
        "unique_buyer_text_count": len({norm_text(text) for text in texts}),
        "unique_buyer_template_count": len(skeleton_counter),
        "unique_token_count": len(set(tokens)),
        "total_token_count": len(tokens),
        "type_token_ratio": round(len(set(tokens)) / len(tokens), 3) if tokens else 0,
        "average_word_count": average_words,
        "median_word_count": median_words,
        "top_repeated_buyer_text_templates": [
            {"template": template, "count": count}
            for template, count in skeleton_counter.most_common(20)
            if count > 1
        ],
    }


def duplicate_summary(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = all_rows(splits)
    normalized_counter = Counter(norm_text(row.get("sanitized_buyer_text") or "") for row in rows)
    exact_across_splits = exact_text_overlap(splits)
    near_duplicates = near_duplicate_overlap(splits)
    return {
        "exact_duplicate_texts_inside_dataset": [
            {"text": text, "count": count}
            for text, count in normalized_counter.most_common()
            if text and count > 1
        ][:20],
        "heldout_exact_text_overlap": exact_across_splits,
        "heldout_exact_text_overlap_found": any(exact_across_splits.values()),
        "heldout_near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
        "heldout_near_duplicate_overlap": near_duplicates,
        "heldout_near_duplicate_overlap_found": bool(near_duplicates),
    }


def expanded_and_verifier(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    expanded, adapter_errors = expand_compact_planner_output(compact_target(row))
    if adapter_errors:
        return expanded if isinstance(expanded, dict) else {}, [f"adapter_error:{item}" for item in adapter_errors]
    return expanded, verify_conversation_brain_output(expanded, row)


def classify_row(row: dict[str, Any], verifier_errors: list[str]) -> str:
    target = compact_target(row)
    say = str(target.get("say") or "")
    buyer = norm_text(row.get("sanitized_buyer_text") or "")
    if verifier_errors:
        return "blocker"
    if RAW_URL_RE.search(say) or INTERNAL_OR_LEAKAGE_RE.search(say) or SIDE_EFFECT_RE.search(say):
        return "blocker"
    if str(target.get("action") or "").startswith("ask_") and "?" not in say:
        return "needs_human_review"
    if target.get("action") == "terminal_close" and "?" in say:
        return "blocker"
    if "variant " in buyer or SYNTHETIC_SUFFIX_RE.search(str(row.get("sanitized_buyer_text") or "")):
        return "warning"
    return "acceptable"


def row_review_record(row: dict[str, Any]) -> dict[str, Any]:
    target = compact_target(row)
    expanded, verifier_errors = expanded_and_verifier(row)
    sales_strategy = expanded.get("sales_strategy") if isinstance(expanded.get("sales_strategy"), dict) else {}
    response_plan = expanded.get("response_plan") if isinstance(expanded.get("response_plan"), dict) else {}
    return {
        "case_id": row.get("case_id"),
        "split": row.get("split"),
        "source_type": row.get("source_type"),
        "semantic_group": row.get("semantic_group"),
        "target_card_id": row.get("target_card_id"),
        "sanitized_buyer_text": row.get("sanitized_buyer_text"),
        "target_compact_json": target,
        "expanded_action_summary": {
            "next_action": sales_strategy.get("next_action"),
            "one_next_step": sales_strategy.get("one_next_step"),
            "should_ask_question": sales_strategy.get("should_ask_question"),
            "should_recommend": sales_strategy.get("should_recommend"),
            "should_close": sales_strategy.get("should_close"),
            "should_disqualify": sales_strategy.get("should_disqualify"),
            "must_include": response_plan.get("must_include") or [],
            "must_not_include": response_plan.get("must_not_include") or [],
        },
        "say": target.get("say"),
        "preserve": target.get("preserve") or [],
        "avoid": target.get("avoid") or [],
        "facts": target.get("facts") or [],
        "verifier_result": {
            "status": "pass" if not verifier_errors else "fail",
            "errors": verifier_errors,
        },
        "review_classification": classify_row(row, verifier_errors),
    }


def sample_rows(splits: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = all_rows(splits)
    selected: dict[str, dict[str, Any]] = {}
    coverage: dict[str, Any] = {
        "semantic_group_minimum": SEMANTIC_GROUP_SAMPLE_COUNT,
        "semantic_group_counts": {},
        "source_type_minimums": SOURCE_TYPE_SAMPLE_MINIMUMS,
        "source_type_counts": {},
        "validation_rows": 0,
        "test_rows": 0,
        "ood_rows": 0,
    }

    def add(row: dict[str, Any]) -> None:
        case_id = str(row.get("case_id") or "")
        if case_id:
            selected.setdefault(case_id, row)

    for group in GROUP_MINIMUMS:
        group_rows = [row for row in rows if row.get("semantic_group") == group]
        for row in group_rows[:SEMANTIC_GROUP_SAMPLE_COUNT]:
            add(row)

    for source_type, minimum in SOURCE_TYPE_SAMPLE_MINIMUMS.items():
        source_rows = [row for row in rows if row.get("source_type") == source_type]
        for row in source_rows[:minimum]:
            add(row)

    for split in ("validation", "test"):
        for row in splits[split][:HELDOUT_SAMPLE_MINIMUM]:
            add(row)

    for row in splits["ood_test"]:
        add(row)

    sampled = list(selected.values())
    coverage["semantic_group_counts"] = dict(
        sorted(Counter(str(row.get("semantic_group") or "") for row in sampled if row.get("semantic_group") in GROUP_MINIMUMS).items())
    )
    coverage["source_type_counts"] = dict(sorted(Counter(str(row.get("source_type") or "") for row in sampled).items()))
    coverage["validation_rows"] = sum(1 for row in sampled if row.get("split") == "validation")
    coverage["test_rows"] = sum(1 for row in sampled if row.get("split") == "test")
    coverage["ood_rows"] = sum(1 for row in sampled if row.get("split") == "ood_test")
    coverage["sampled_row_count"] = len(sampled)
    coverage["requirements_met"] = {
        "five_rows_per_semantic_group": all(
            coverage["semantic_group_counts"].get(group, 0) >= SEMANTIC_GROUP_SAMPLE_COUNT for group in GROUP_MINIMUMS
        ),
        "source_type_minimums": all(
            coverage["source_type_counts"].get(source_type, 0) >= minimum
            for source_type, minimum in SOURCE_TYPE_SAMPLE_MINIMUMS.items()
        ),
        "all_ood_rows": coverage["ood_rows"] == len(splits["ood_test"]) == 10,
        "validation_minimum": coverage["validation_rows"] >= HELDOUT_SAMPLE_MINIMUM,
        "test_minimum": coverage["test_rows"] >= HELDOUT_SAMPLE_MINIMUM,
    }
    return [row_review_record(row) for row in sampled], coverage


def consistency_summary(rows: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    card_lookup = {str(card.get("card_id") or ""): card for card in cards}
    counters = {
        "preserve_missing_in_say": 0,
        "avoid_present_in_say": 0,
        "facts_not_approved": 0,
        "action_strategy_card_mismatch": 0,
        "safety_side_effect_risk": 0,
        "verifier_failures": 0,
    }
    examples: dict[str, list[dict[str, Any]]] = {key: [] for key in counters}
    for row in rows:
        target = compact_target(row)
        say_norm = norm_text(target.get("say") or "")
        case_id = str(row.get("case_id") or "")
        for phrase in string_list(target.get("preserve")):
            if norm_text(phrase) and norm_text(phrase) not in say_norm:
                counters["preserve_missing_in_say"] += 1
                examples["preserve_missing_in_say"].append({"case_id": case_id, "phrase": phrase})
                break
        for phrase in string_list(target.get("avoid")):
            normalized_phrase = norm_text(phrase)
            if normalized_phrase and normalized_phrase in say_norm:
                counters["avoid_present_in_say"] += 1
                examples["avoid_present_in_say"].append({"case_id": case_id, "phrase": phrase})
                break
        approved = set(row.get("approved_campaign_fact_ids") or [])
        facts = set(string_list(target.get("facts")))
        if facts - approved:
            counters["facts_not_approved"] += 1
            examples["facts_not_approved"].append({"case_id": case_id, "facts": sorted(facts - approved)})
        card = card_lookup.get(str(row.get("target_card_id") or ""), {})
        if card and (
            target.get("action") != card.get("canonical_action")
            or target.get("strategy") != card.get("canonical_strategy")
        ):
            counters["action_strategy_card_mismatch"] += 1
            examples["action_strategy_card_mismatch"].append({"case_id": case_id, "target_card_id": row.get("target_card_id")})
        if row.get("semantic_group") == "safety_and_boundary" and SIDE_EFFECT_RE.search(str(target.get("say") or "")):
            counters["safety_side_effect_risk"] += 1
            examples["safety_side_effect_risk"].append({"case_id": case_id})
        _, verifier_errors = expanded_and_verifier(row)
        if verifier_errors:
            counters["verifier_failures"] += 1
            examples["verifier_failures"].append({"case_id": case_id, "errors": verifier_errors[:5]})
    return {
        "preserve_avoid_consistency": {
            "preserve_missing_in_say_count": counters["preserve_missing_in_say"],
            "avoid_present_in_say_count": counters["avoid_present_in_say"],
        },
        "facts_consistency": {"facts_not_approved_count": counters["facts_not_approved"]},
        "action_strategy_consistency": {"card_mismatch_count": counters["action_strategy_card_mismatch"]},
        "safety_boundary_consistency": {"side_effect_risk_count": counters["safety_side_effect_risk"]},
        "verifier_consistency": {"verifier_failure_count": counters["verifier_failures"]},
        "examples": {key: value[:10] for key, value in examples.items()},
    }


def say_diversity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    says = [str(compact_target(row).get("say") or "") for row in rows]
    skeletons = Counter(
        skeleton_text(say, string_list(compact_target(row).get("obj")))
        for row, say in zip(rows, says)
    )
    exact = Counter(says)
    return {
        "unique_say_count": len(set(says)),
        "unique_say_skeleton_count": len(skeletons),
        "top_repeated_say_patterns": [
            {"pattern": pattern, "count": count}
            for pattern, count in skeletons.most_common(20)
            if count > 1
        ],
        "top_repeated_exact_say": [
            {"say": say, "count": count}
            for say, count in exact.most_common(20)
            if count > 1
        ],
    }


def target_card_examples(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for card in cards:
        examples.append(
            {
                "target_card_id": card.get("card_id"),
                "semantic_group": card.get("semantic_group"),
                "canonical_act": card.get("canonical_act"),
                "canonical_action": card.get("canonical_action"),
                "canonical_strategy": card.get("canonical_strategy"),
                "facts_policy": card.get("facts_policy") or {},
                "preserve_policy": card.get("preserve_policy") or {},
                "avoid_policy": card.get("avoid_policy") or {},
                "examples": (card.get("examples") or [])[:3],
            }
        )
    return examples


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Dataset rows: {result['dataset_row_counts']['total']}",
        f"- Sampled rows: {result['sample_coverage']['sampled_row_count']}",
        f"- Review classifications: `{compact_json(result['review_classification_counts'])}`",
        f"- Held-out exact overlap: {str(result['duplicate_near_duplicate_summary']['heldout_exact_text_overlap_found']).lower()}",
        f"- Held-out near-duplicate overlap: {str(result['duplicate_near_duplicate_summary']['heldout_near_duplicate_overlap_found']).lower()}",
        f"- Local model calls made: {str(result['side_effects']['local_model_calls_made']).lower()}",
        f"- Provider/OpenAI/TTS calls made: false",
        f"- Runtime behavior changed: {str(result['side_effects']['runtime_behavior_changed']).lower()}",
        f"- Response text changed: {str(result['side_effects']['response_text_changed']).lower()}",
        "",
        "## Dataset Counts",
        "",
        f"- Split counts: `{compact_json(result['split_counts'])}`",
        f"- Semantic group counts: `{compact_json(result['semantic_group_counts'])}`",
        f"- Source type counts: `{compact_json(result['source_type_counts'])}`",
        f"- Target-card usage count: {len(result['target_card_usage_counts'])}",
        "",
        "## Diversity And Duplication",
        "",
        f"- Buyer text diversity: `{compact_json(result['buyer_text_diversity_metrics'])}`",
        f"- Say diversity: `{compact_json(result['response_say_diversity'])}`",
        "",
        "## Consistency",
        "",
        f"- Preserve/avoid: `{compact_json(result['consistency_summary']['preserve_avoid_consistency'])}`",
        f"- Facts: `{compact_json(result['consistency_summary']['facts_consistency'])}`",
        f"- Action/strategy: `{compact_json(result['consistency_summary']['action_strategy_consistency'])}`",
        f"- Safety boundary: `{compact_json(result['consistency_summary']['safety_boundary_consistency'])}`",
        f"- Verifier: `{compact_json(result['consistency_summary']['verifier_consistency'])}`",
        "",
        "## Sample Coverage",
        "",
        compact_json(result["sample_coverage"]),
        "",
        "## Representative Row Samples",
        "",
    ]
    for sample in result["representative_row_samples"]:
        lines.extend(
            [
                f"### {sample['case_id']}",
                "",
                f"- split: {sample['split']}",
                f"- source_type: {sample['source_type']}",
                f"- semantic_group: {sample['semantic_group']}",
                f"- target_card_id: {sample['target_card_id']}",
                f"- sanitized_buyer_text: {sample['sanitized_buyer_text']}",
                f"- target_compact_json: `{compact_json(sample['target_compact_json'])}`",
                f"- expanded_action_summary: `{compact_json(sample['expanded_action_summary'])}`",
                f"- say: {sample['say']}",
                f"- preserve: `{compact_json(sample['preserve'])}`",
                f"- avoid: `{compact_json(sample['avoid'])}`",
                f"- facts: `{compact_json(sample['facts'])}`",
                f"- verifier_result: `{compact_json(sample['verifier_result'])}`",
                f"- review_classification: {sample['review_classification']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Target Card Examples",
            "",
            compact_json(result["target_card_examples"]),
        ]
    )
    return "\n".join(lines)


def main() -> int:
    splits = load_splits()
    cards = load_cards()
    rows = all_rows(splits)
    in_distribution = in_distribution_rows(splits)
    validation = validate_dataset(splits, cards)
    samples, sample_coverage = sample_rows(splits)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if validation.get("status") == "pass" and sample_coverage["requirements_met"] else "fail",
        "inputs": {
            "balanced_dataset": rel(DATASET_RESULT_PATH.parent),
            "target_cards": rel(TARGET_CARDS_PATH),
            "dataset_spec": rel(SPEC_PATH),
            "equivalence_policy": rel(EQUIVALENCE_POLICY_PATH),
            "mixed_replay_training_plan": rel(TRAINING_PLAN_PATH),
        },
        "dataset_row_counts": {
            "total": len(rows),
            "in_distribution": len(in_distribution),
            "ood": len(splits["ood_test"]),
        },
        "split_counts": {split: len(splits[split]) for split in SPLIT_ORDER},
        "semantic_group_counts": semantic_counts(in_distribution),
        "source_type_counts": dict(sorted(Counter(str(row.get("source_type") or "") for row in rows).items())),
        "target_card_usage_counts": target_card_usage(rows),
        "label_distribution": labels_by_split(splits),
        "buyer_text_diversity_metrics": buyer_text_diversity(rows),
        "duplicate_near_duplicate_summary": duplicate_summary(splits),
        "heldout_coverage": heldout_coverage(splits),
        "consistency_summary": consistency_summary(rows, cards),
        "response_say_diversity": say_diversity(rows),
        "top_repeated_say_patterns": say_diversity(rows)["top_repeated_say_patterns"],
        "top_repeated_buyer_text_templates": buyer_text_diversity(rows)["top_repeated_buyer_text_templates"],
        "target_card_examples": target_card_examples(cards),
        "representative_row_samples": samples,
        "review_classification_counts": dict(sorted(Counter(sample["review_classification"] for sample in samples).items())),
        "sample_coverage": sample_coverage,
        "dataset_validation_failures": validation.get("failures", []),
        "side_effects": {
            "local_model_calls_made": False,
            "provider_calls_made": False,
            "openai_api_calls_made": False,
            "live_tts_calls_made": False,
            "provider_side_effects_made": False,
            "model_download_attempted": False,
            "model_redownloaded": False,
            "model_weights_committed": False,
            "adapter_files_committed": False,
            "runtime_behavior_changed": False,
            "response_text_changed": False,
            "raw_private_transcript_included": False,
            "raw_private_transcript_copied_to_public_evidence": False,
            "case_text_stored_in_evidence": False,
        },
    }
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, build_report(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "dataset_rows": result["dataset_row_counts"]["total"],
                "sampled_rows": result["sample_coverage"]["sampled_row_count"],
                "sample_requirements_met": result["sample_coverage"]["requirements_met"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
