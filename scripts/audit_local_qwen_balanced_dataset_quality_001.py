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
    SPLIT_PATHS,
    compact_target,
    exact_text_overlap,
    heldout_coverage,
    load_cards,
    norm_text,
    read_jsonl,
    rel,
    semantic_counts,
    string_list,
    target_card_usage,
    validate_dataset,
    write_json,
    write_text,
)
from scripts.generate_local_qwen_balanced_dataset_review_packet_001 import (  # noqa: E402
    DATASET_ID,
    NEAR_DUPLICATE_THRESHOLD,
    all_rows,
    compact_json,
    in_distribution_rows,
    jaccard,
    load_splits,
    near_duplicate_overlap,
    skeleton_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-BALANCED-DATASET-QUALITY-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SPLIT_ORDER = ("train", "validation", "test", "ood_test")

SIDE_EFFECT_RE = re.compile(
    r"\b(sent|emailed|created|booked|scheduled|updated|logged)\b.{0,48}\b(email|calendar|invite|crm|ticket|record)\b",
    re.I,
)
INTERNAL_POLICY_RE = re.compile(
    r"internal policy|guardrail|approved qualified reviewer|source-grounded|reasoning trace|semantic frame|state_update|safety_flags",
    re.I,
)
CAMPAIGN_LEAKAGE_RE = re.compile(r"routesignal|prod-102|campaign id|public-openai-chatgpt-plans|source bundle|live-demo", re.I)
RAW_URL_RE = re.compile(r"https?://\S+", re.I)
UNSUPPORTED_FACT_RE = re.compile(r"guaranteed|unlimited access|always gives|100%|will definitely|no limits", re.I)
TEAM_LANGUAGE_RE = re.compile(r"\byour team\b|\bfor the team\b|\bteam plan\b|\bbusiness workspace\b", re.I)

ISSUE_ORDER = ("blocker", "warning", "needs_human_review", "acceptable")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def issue(
    severity: str,
    category: str,
    code: str,
    message: str,
    row: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "severity": severity,
        "category": category,
        "code": code,
        "message": message,
    }
    if row is not None:
        payload.update(
            {
                "case_id": row.get("case_id"),
                "split": row.get("split"),
                "source_type": row.get("source_type"),
                "semantic_group": row.get("semantic_group"),
                "target_card_id": row.get("target_card_id"),
            }
        )
    if details:
        payload["details"] = details
    return payload


def expanded_and_errors(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    expanded, adapter_errors = expand_compact_planner_output(compact_target(row))
    if adapter_errors:
        return expanded if isinstance(expanded, dict) else {}, [f"adapter_error:{item}" for item in adapter_errors]
    return expanded, verify_conversation_brain_output(expanded, row)


def target_signature(row: dict[str, Any], include_say: bool = True) -> str:
    target = compact_target(row)
    fields = {
        "act": target.get("act"),
        "sub": target.get("sub"),
        "obj": target.get("obj"),
        "rel": target.get("rel"),
        "neg": target.get("neg"),
        "update": target.get("update"),
        "block": target.get("block"),
        "action": target.get("action"),
        "strategy": target.get("strategy"),
        "facts": target.get("facts"),
        "preserve": target.get("preserve"),
        "avoid": target.get("avoid"),
    }
    if include_say:
        fields["say"] = target.get("say")
    return compact_json(fields)


def is_negative_team_text(text: str) -> bool:
    normalized = norm_text(text)
    return any(
        phrase in normalized
        for phrase in (
            "not a team",
            "no team",
            "by myself",
            "personal use",
            "just me",
            "only me",
        )
    )


def naturalness_issues(row: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(row.get("sanitized_buyer_text") or "")
    normalized = norm_text(text)
    issues: list[dict[str, Any]] = []
    if not text:
        issues.append(issue("blocker", "naturalness", "missing_buyer_text", "Buyer text is empty.", row))
        return issues
    if len(normalized.split()) < 3 and row.get("split") != "ood_test":
        issues.append(issue("warning", "naturalness", "very_short_buyer_text", "Buyer text is very short.", row))
    if "variant " in normalized:
        issues.append(issue("warning", "naturalness", "explicit_variant_suffix", "Buyer text exposes a mechanical variant suffix.", row))
    if any(
        suffix in normalized
        for suffix in (
            "for this plan decision",
            "before i choose anything",
            "that is my current context",
            "i want the practical answer",
            "keep it to one next step",
        )
    ):
        issues.append(issue("warning", "naturalness", "templated_context_suffix", "Buyer text uses a repeated control suffix.", row))
    return issues


def semantic_consistency_issues(row: dict[str, Any], card_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    target = compact_target(row)
    card = card_lookup.get(str(row.get("target_card_id") or ""))
    issues: list[dict[str, Any]] = []
    if not card:
        return [issue("blocker", "semantic_consistency", "missing_target_card", "Row references a missing target card.", row)]
    if target.get("act") != card.get("canonical_act"):
        issues.append(issue("blocker", "semantic_consistency", "act_card_mismatch", "Target act differs from target card.", row))
    if target.get("action") != card.get("canonical_action") or target.get("strategy") != card.get("canonical_strategy"):
        issues.append(
            issue(
                "blocker",
                "semantic_consistency",
                "action_strategy_card_mismatch",
                "Target action/strategy differs from target card.",
                row,
                {
                    "target_action": target.get("action"),
                    "card_action": card.get("canonical_action"),
                    "target_strategy": target.get("strategy"),
                    "card_strategy": card.get("canonical_strategy"),
                },
            )
        )
    allowed_subs = set(str(item) for item in (card.get("allowed_sub_values") or []))
    if allowed_subs and str(target.get("sub") or "") not in allowed_subs:
        issues.append(issue("blocker", "semantic_consistency", "sub_card_mismatch", "Target sub is outside target-card allowed_sub_values.", row))
    expected_rel = (row.get("expected_semantic_frame") or {}).get("conjunction_relation")
    if expected_rel in {"and", "or"} and target.get("rel") != expected_rel:
        issues.append(issue("blocker", "fidelity", "and_or_drift", "Target rel differs from expected conjunction relation.", row))
    if expected_rel in {"and", "or"} and (row.get("expected_semantic_frame") or {}).get("conjunction_relation") != target.get("rel"):
        issues.append(issue("blocker", "semantic_consistency", "expected_relation_mismatch", "Expected semantic relation and compact target relation differ.", row))
    expected_neg = (row.get("expected_semantic_frame") or {}).get("negation_scope")
    if expected_neg == "team_state" and target.get("neg") != "team_state":
        issues.append(issue("blocker", "fidelity", "not_team_team_drift", "Team negation is missing from compact target.", row))
    return issues


def response_plan_issues(row: dict[str, Any]) -> list[dict[str, Any]]:
    target = compact_target(row)
    say = str(target.get("say") or "")
    say_norm = norm_text(say)
    buyer_norm = norm_text(row.get("sanitized_buyer_text") or "")
    issues: list[dict[str, Any]] = []
    for phrase in string_list(target.get("preserve")):
        normalized_phrase = norm_text(phrase)
        if normalized_phrase and normalized_phrase not in say_norm:
            issues.append(issue("blocker", "fidelity", "buyer_word_preservation_miss", "Preserve phrase is missing from say.", row, {"phrase": phrase}))
    for phrase in string_list(target.get("avoid")):
        normalized_phrase = norm_text(phrase)
        if normalized_phrase and normalized_phrase in say_norm:
            if normalized_phrase == "team" and "not a team" in say_norm:
                continue
            issues.append(issue("blocker", "fidelity", "avoid_phrase_present", "Avoid phrase appears in say.", row, {"phrase": phrase}))
    facts = set(string_list(target.get("facts")))
    approved = set(row.get("approved_campaign_fact_ids") or [])
    if facts - approved:
        issues.append(issue("blocker", "facts", "unsupported_fact_id", "Target facts include IDs not approved for the row.", row, {"facts": sorted(facts - approved)}))
    if target.get("action") == "terminal_close" and "?" in say:
        issues.append(issue("blocker", "semantic_consistency", "terminal_case_asks_question", "Terminal cases must not ask a new question.", row))
    if str(target.get("action") or "").startswith("ask_") and "?" not in say:
        issues.append(issue("blocker", "sales_usefulness", "ask_action_without_question", "Ask action does not ask a question in say.", row))
    if "voice" in buyer_norm and "writing" not in buyer_norm and "writing" in say_norm and "voice" not in say_norm:
        issues.append(issue("blocker", "fidelity", "voice_writing_drift", "Voice-only buyer wording drifted into writing.", row))
    if is_negative_team_text(str(row.get("sanitized_buyer_text") or "")):
        if target.get("neg") != "team_state":
            issues.append(issue("blocker", "fidelity", "not_team_negation_missing", "Buyer said not-team/personal use but target neg is not team_state.", row))
        if (target.get("update") or {}).get("team") is True:
            issues.append(issue("blocker", "fidelity", "not_team_state_updated_true", "Buyer said not-team/personal use but update.team is true.", row))
        if TEAM_LANGUAGE_RE.search(say):
            issues.append(issue("blocker", "fidelity", "not_team_say_team_language", "Buyer said not-team/personal use but say uses team plan language.", row))
    return issues


def safety_issues(row: dict[str, Any]) -> list[dict[str, Any]]:
    target = compact_target(row)
    say = str(target.get("say") or "")
    issues: list[dict[str, Any]] = []
    if RAW_URL_RE.search(say):
        issues.append(issue("blocker", "safety", "raw_url_in_say", "Say includes a raw URL.", row))
    if SIDE_EFFECT_RE.search(say):
        issues.append(issue("blocker", "safety", "fake_side_effect", "Say claims an email/calendar/CRM/ticket side effect.", row))
    if INTERNAL_POLICY_RE.search(say):
        issues.append(issue("blocker", "safety", "internal_policy_language", "Say includes internal policy or schema language.", row))
    if CAMPAIGN_LEAKAGE_RE.search(say):
        issues.append(issue("blocker", "safety", "campaign_leakage", "Say leaks campaign/runtime identifiers.", row))
    if UNSUPPORTED_FACT_RE.search(say):
        issues.append(issue("blocker", "facts", "unsupported_product_claim", "Say includes an unsupported guarantee or product claim.", row))
    if row.get("semantic_group") == "safety_and_boundary" and SIDE_EFFECT_RE.search(say):
        issues.append(issue("blocker", "safety", "safety_boundary_side_effect_claim", "Safety-boundary row claims a side effect.", row))
    expected = row.get("expected_safety_constraints") if isinstance(row.get("expected_safety_constraints"), dict) else {}
    if expected.get("provider_calls_allowed") is not False:
        issues.append(issue("blocker", "safety", "provider_calls_allowed", "Row safety constraints allow provider calls.", row))
    if expected.get("fake_side_effects_allowed") is not False:
        issues.append(issue("blocker", "safety", "fake_side_effects_allowed", "Row safety constraints allow fake side effects.", row))
    if expected.get("raw_private_transcript_allowed") is not False:
        issues.append(issue("blocker", "privacy", "raw_private_transcript_allowed", "Row safety constraints allow raw private transcripts.", row))
    return issues


def sales_usefulness_issues(row: dict[str, Any]) -> list[dict[str, Any]]:
    target = compact_target(row)
    say = str(target.get("say") or "")
    say_norm = norm_text(say)
    issues: list[dict[str, Any]] = []
    if say_norm in {"got it", "understood", "okay", "sure", "i can help"}:
        issues.append(issue("warning", "sales_usefulness", "generic_say", "Say is too generic to move the conversation.", row))
    if len(say_norm.split()) < 5 and row.get("split") != "ood_test":
        issues.append(issue("warning", "sales_usefulness", "too_short_say", "Say is probably too short for planner supervision.", row))
    action = str(target.get("action") or "")
    if action in {"recommend_plan", "reframe_price_objection", "compare_competitor_context"}:
        useful_terms = ("fit", "use", "value", "price", "current", "plus", "pro", "free", "compare", "plan")
        if not any(term in say_norm for term in useful_terms):
            issues.append(issue("warning", "sales_usefulness", "weak_sales_progression", "Sales move lacks a useful plan/value/use-case term.", row))
    if say_norm.startswith("i would ") and action not in {"respect_boundary", "answer_without_inventing_facts"}:
        issues.append(issue("needs_human_review", "sales_usefulness", "passive_planner_wording", "Say uses planner-style 'I would' wording.", row))
    return issues


def privacy_issues(row: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if row.get("privacy_level") != "sanitized_only":
        issues.append(issue("blocker", "privacy", "privacy_level_not_sanitized_only", "Row privacy level must stay sanitized_only.", row))
    if row.get("raw_private_transcript_included") is not False:
        issues.append(issue("blocker", "privacy", "raw_private_transcript_included", "Row includes a raw private transcript flag.", row))
    return issues


def row_issues(row: dict[str, Any], card_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    expanded, verifier_errors = expanded_and_errors(row)
    issues: list[dict[str, Any]] = []
    issues.extend(privacy_issues(row))
    issues.extend(naturalness_issues(row))
    issues.extend(semantic_consistency_issues(row, card_lookup))
    issues.extend(response_plan_issues(row))
    issues.extend(safety_issues(row))
    issues.extend(sales_usefulness_issues(row))
    if verifier_errors:
        issues.append(
            issue(
                "blocker",
                "fidelity",
                "expanded_target_verifier_failure",
                "Expanded target failed the deterministic verifier.",
                row,
                {"verifier_errors": verifier_errors[:12]},
            )
        )
    strategy = expanded.get("sales_strategy") if isinstance(expanded.get("sales_strategy"), dict) else {}
    if str(compact_target(row).get("action") or "").startswith("ask_") and strategy.get("should_ask_question") is not True:
        issues.append(
            issue(
                "warning",
                "semantic_consistency",
                "expanded_ask_flag_not_set",
                "Expanded target action starts with ask_ but should_ask_question is not true.",
                row,
            )
        )
    return issues


def over_template_risk(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    buyer_skeleton_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    say_skeleton_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    target_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        target = compact_target(row)
        objects = string_list(target.get("obj"))
        buyer_skeleton_cases[skeleton_text(str(row.get("sanitized_buyer_text") or ""), objects)].append(row)
        say_skeleton_cases[skeleton_text(str(target.get("say") or ""), objects)].append(row)
        target_cases[target_signature(row)].append(row)

    issues: list[dict[str, Any]] = []
    repeated_buyer = []
    repeated_say = []
    repeated_targets = []
    for skeleton, case_rows in sorted(buyer_skeleton_cases.items(), key=lambda item: len(item[1]), reverse=True):
        if len(case_rows) >= 8:
            repeated_buyer.append({"skeleton": skeleton, "count": len(case_rows), "case_ids": [row.get("case_id") for row in case_rows[:12]]})
            issues.append(
                issue(
                    "warning",
                    "over_template_risk",
                    "repeated_buyer_text_skeleton",
                    "Buyer text skeleton repeats heavily.",
                    case_rows[0],
                    {"skeleton": skeleton, "count": len(case_rows)},
                )
            )
    for skeleton, case_rows in sorted(say_skeleton_cases.items(), key=lambda item: len(item[1]), reverse=True):
        if len(case_rows) >= 8:
            repeated_say.append({"skeleton": skeleton, "count": len(case_rows), "case_ids": [row.get("case_id") for row in case_rows[:12]]})
            issues.append(
                issue(
                    "warning",
                    "over_template_risk",
                    "repeated_say_skeleton",
                    "Say skeleton repeats heavily.",
                    case_rows[0],
                    {"skeleton": skeleton, "count": len(case_rows)},
                )
            )
    for signature, case_rows in sorted(target_cases.items(), key=lambda item: len(item[1]), reverse=True):
        if len(case_rows) > 1:
            repeated_targets.append({"target_signature": signature, "count": len(case_rows), "case_ids": [row.get("case_id") for row in case_rows[:12]]})

    one_word_target_changes = []
    changed_meaning_same_target = []
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[str(row.get("semantic_group") or "")].append(row)
    for group_rows in by_group.values():
        for index, left in enumerate(group_rows):
            for right in group_rows[index + 1 :]:
                score = jaccard(str(left.get("sanitized_buyer_text") or ""), str(right.get("sanitized_buyer_text") or ""))
                left_core = target_signature(left, include_say=False)
                right_core = target_signature(right, include_say=False)
                if score >= 0.72 and left_core != right_core and len(one_word_target_changes) < 40:
                    one_word_target_changes.append(
                        {
                            "left_case_id": left.get("case_id"),
                            "right_case_id": right.get("case_id"),
                            "jaccard": round(score, 3),
                        }
                    )
                if score <= 0.38 and left_core == right_core and len(changed_meaning_same_target) < 40:
                    changed_meaning_same_target.append(
                        {
                            "left_case_id": left.get("case_id"),
                            "right_case_id": right.get("case_id"),
                            "jaccard": round(score, 3),
                        }
                    )
    if one_word_target_changes:
        issues.append(
            issue(
                "needs_human_review",
                "over_template_risk",
                "small_text_change_large_target_change",
                "Similar buyer texts sometimes map to different target signatures; spot-check for justified object/sub changes.",
                details={"pair_count": len(one_word_target_changes), "examples": one_word_target_changes[:10]},
            )
        )
    if changed_meaning_same_target:
        issues.append(
            issue(
                "needs_human_review",
                "over_template_risk",
                "large_text_change_same_target",
                "Dissimilar buyer texts sometimes map to the same target signature; spot-check for over-broad targets.",
                details={"pair_count": len(changed_meaning_same_target), "examples": changed_meaning_same_target[:10]},
            )
        )

    return (
        {
            "repeated_buyer_text_skeletons": repeated_buyer[:20],
            "repeated_say_skeletons": repeated_say[:20],
            "repeated_exact_target_outputs": repeated_targets[:20],
            "small_text_change_large_target_change": one_word_target_changes,
            "large_text_change_same_target": changed_meaning_same_target,
        },
        issues,
    )


def split_sanity(splits: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    coverage = heldout_coverage(splits)
    exact_overlap = exact_text_overlap(splits)
    near_overlap = near_duplicate_overlap(splits)
    train_rows = splits["train"]
    validation_test_rows = splits["validation"] + splits["test"]
    train_cards = {str(row.get("target_card_id") or "") for row in train_rows}
    heldout_cards = {str(row.get("target_card_id") or "") for row in validation_test_rows}
    train_groups = {str(row.get("semantic_group") or "") for row in train_rows}
    heldout_groups = {str(row.get("semantic_group") or "") for row in validation_test_rows}
    ood_isolated = all(row.get("split") == "ood_test" and row.get("source_type") == "ood_control" for row in splits["ood_test"])
    issues: list[dict[str, Any]] = []
    if any(exact_overlap.values()):
        issues.append(issue("blocker", "split_sanity", "heldout_exact_text_overlap", "Validation/test has exact text overlap."))
    if near_overlap:
        issues.append(issue("blocker", "split_sanity", "heldout_near_duplicate_overlap", "Validation/test has near-duplicate text overlap."))
    for split in ("validation", "test"):
        if not coverage[split]["covered_by_train"]:
            issues.append(issue("blocker", "split_sanity", f"{split}_uncovered_label_combo", f"{split} has label combinations not covered by train."))
    if heldout_cards - train_cards:
        issues.append(issue("blocker", "split_sanity", "heldout_target_card_not_in_train", "Validation/test target-card IDs are missing from train.", details={"target_card_ids": sorted(heldout_cards - train_cards)}))
    if heldout_groups - train_groups:
        issues.append(issue("blocker", "split_sanity", "heldout_semantic_group_not_in_train", "Validation/test semantic groups are missing from train.", details={"semantic_groups": sorted(heldout_groups - train_groups)}))
    if not ood_isolated:
        issues.append(issue("blocker", "split_sanity", "ood_not_isolated", "OOD rows are not isolated in ood_test."))
    return (
        {
            "validation_test_exact_text_overlap_false": not any(exact_overlap.values()),
            "validation_test_near_duplicate_overlap_false": not bool(near_overlap),
            "ood_isolated": ood_isolated,
            "train_covers_validation_test_label_combinations": all(coverage[split]["covered_by_train"] for split in ("validation", "test")),
            "train_covers_validation_test_target_card_ids": not (heldout_cards - train_cards),
            "train_covers_validation_test_semantic_groups": not (heldout_groups - train_groups),
            "near_duplicate_threshold": NEAR_DUPLICATE_THRESHOLD,
            "heldout_coverage": coverage,
            "exact_text_overlap": exact_overlap,
            "near_duplicate_overlap": near_overlap,
        },
        issues,
    )


def row_classifications(rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in issues:
        case_id = item.get("case_id")
        if case_id:
            by_case[str(case_id)].append(item)
    classifications: dict[str, str] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "")
        severities = {item["severity"] for item in by_case.get(case_id, [])}
        if "blocker" in severities:
            classifications[case_id] = "blocker"
        elif "needs_human_review" in severities:
            classifications[case_id] = "needs_human_review"
        elif "warning" in severities:
            classifications[case_id] = "warning"
        else:
            classifications[case_id] = "acceptable"
    return {
        "classification_counts": dict(sorted(Counter(classifications.values()).items())),
        "rows": classifications,
    }


def build_report(result: dict[str, Any]) -> str:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- Status: {result['status']}",
        f"- Blockers: {result['issue_counts_by_severity'].get('blocker', 0)}",
        f"- Warnings: {result['issue_counts_by_severity'].get('warning', 0)}",
        f"- Needs human review: {result['issue_counts_by_severity'].get('needs_human_review', 0)}",
        f"- Acceptable rows: {result['row_classifications']['classification_counts'].get('acceptable', 0)}",
        f"- Dataset rows: {result['row_counts']['total']}",
        f"- Local model calls made: false",
        f"- Provider/OpenAI/TTS calls made: false",
        f"- Runtime behavior changed: false",
        f"- Response text changed: false",
        "",
        "## Quality Checks",
        "",
        f"- Naturalness issues: {result['issue_counts_by_category'].get('naturalness', 0)}",
        f"- Semantic consistency issues: {result['issue_counts_by_category'].get('semantic_consistency', 0)}",
        f"- Sales usefulness issues: {result['issue_counts_by_category'].get('sales_usefulness', 0)}",
        f"- Fidelity issues: {result['issue_counts_by_category'].get('fidelity', 0)}",
        f"- Over-template risk issues: {result['issue_counts_by_category'].get('over_template_risk', 0)}",
        f"- Split sanity blockers: {len([item for item in result['issues'] if item['category'] == 'split_sanity' and item['severity'] == 'blocker'])}",
        "",
        "## Split Sanity",
        "",
        compact_json(result["split_sanity"]),
        "",
        "## Over-Template Risk",
        "",
        compact_json(result["over_template_risk"]),
        "",
        "## Blockers",
        "",
    ]
    blockers = [item for item in result["issues"] if item["severity"] == "blocker"]
    lines.append(compact_json(blockers[:100] if blockers else []))
    lines.extend(["", "## Warnings And Human Review", ""])
    warnings = [item for item in result["issues"] if item["severity"] in {"warning", "needs_human_review"}]
    lines.append(compact_json(warnings[:200] if warnings else []))
    lines.extend(["", "## Row Classification Counts", "", compact_json(result["row_classifications"]["classification_counts"])])
    return "\n".join(lines)


def main() -> int:
    splits = load_splits()
    rows = all_rows(splits)
    cards = load_cards()
    card_lookup = {str(card.get("card_id") or ""): card for card in cards}
    issues: list[dict[str, Any]] = []
    for row in rows:
        issues.extend(row_issues(row, card_lookup))
    over_template, over_template_issues = over_template_risk(rows)
    split_payload, split_issues = split_sanity(splits)
    issues.extend(over_template_issues)
    issues.extend(split_issues)
    validation = validate_dataset(splits, cards)
    if validation.get("status") != "pass":
        for failure in validation.get("failures", []):
            issues.append(issue("blocker", "dataset_validation", "balanced_dataset_validator_failure", failure))
    severity_counts = Counter(item["severity"] for item in issues)
    for severity in ISSUE_ORDER:
        severity_counts.setdefault(severity, 0)
    category_counts = Counter(item["category"] for item in issues)
    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass" if severity_counts["blocker"] == 0 else "fail",
        "dataset_id": DATASET_ID,
        "inputs": {split: rel(path) for split, path in SPLIT_PATHS.items()},
        "row_counts": {
            "total": len(rows),
            "in_distribution": len(in_distribution_rows(splits)),
            "ood_test": len(splits["ood_test"]),
            "by_split": {split: len(splits[split]) for split in SPLIT_ORDER},
        },
        "semantic_group_counts": semantic_counts(in_distribution_rows(splits)),
        "source_type_counts": dict(sorted(Counter(str(row.get("source_type") or "") for row in rows).items())),
        "target_card_usage_counts": target_card_usage(rows),
        "issue_counts_by_severity": dict(sorted(severity_counts.items())),
        "issue_counts_by_category": dict(sorted(category_counts.items())),
        "blocker_count": severity_counts["blocker"],
        "warning_count": severity_counts["warning"],
        "needs_human_review_count": severity_counts["needs_human_review"],
        "issues": issues,
        "row_classifications": row_classifications(rows, issues),
        "over_template_risk": over_template,
        "split_sanity": split_payload,
        "approval_relevant_blockers": [
            item
            for item in issues
            if item["severity"] == "blocker"
            and item["category"] in {"fidelity", "safety", "split_sanity", "semantic_consistency", "facts", "privacy", "dataset_validation"}
        ],
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
                "blocker_count": result["blocker_count"],
                "warning_count": result["warning_count"],
                "needs_human_review_count": result["needs_human_review_count"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
