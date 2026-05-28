#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from typing import Any

from prosody_quality_common import (
    BACKEND_POLICY_PATH,
    FISH_TAXONOMY_EVIDENCE,
    MAPPING_PATH,
    PLANNER_EVIDENCE,
    REQUIRED_CONTEXTS,
    SALES_MAPPING_EVIDENCE,
    TAXONOMY_AUDIT_DIR,
    TAXONOMY_PATH,
    base_boundary_flags,
    count_by,
    group_by_signature,
    has_raw_tag,
    label_index,
    load_json,
    write_json,
    write_report,
)


OLD_TEMPLATE_PHRASES = (
    "internal style intent only for",
    "use sentence length, punctuation, and word choice to approximate",
    "may map to fish-style inline control for",
)


def repeated_template_hint(label: dict[str, Any], hint_counts: Counter[str]) -> bool:
    backend_mapping = label.get("backend_mapping", {}) if isinstance(label.get("backend_mapping"), dict) else {}
    hints = " ".join(str(backend_mapping.get(name, "")) for name in ("elevenlabs_hint", "plain_text_hint", "future_fish_hint")).lower()
    if any(phrase in hints for phrase in OLD_TEMPLATE_PHRASES):
        return True
    elevenlabs_hint = str(backend_mapping.get("elevenlabs_hint", "")).strip().lower()
    return bool(elevenlabs_hint and hint_counts[elevenlabs_hint] > 20)


def needs_specific_backend_hint(label: dict[str, Any]) -> bool:
    backend_mapping = label.get("backend_mapping", {}) if isinstance(label.get("backend_mapping"), dict) else {}
    elevenlabs_hint = str(backend_mapping.get("elevenlabs_hint", "")).lower()
    plain_text_hint = str(backend_mapping.get("plain_text_hint", "")).lower()
    if len(elevenlabs_hint) < 70 or len(plain_text_hint) < 45:
        return True
    if "bracket" not in elevenlabs_hint and "tag" not in elevenlabs_hint:
        return True
    return False


def label_usefulness(
    label: dict[str, Any],
    selected_count: int,
    true_duplicate: bool,
    template_hint: bool,
    specific_hint_missing: bool,
) -> str:
    category = str(label.get("category", ""))
    if category == "unsafe_or_disallowed" or label.get("risk_level") == "high":
        return "risky"
    if true_duplicate and selected_count == 0:
        return "redundant"
    if template_hint or specific_hint_missing:
        return "too_vague"
    if selected_count >= 3 or category in {"repair", "objection_handling", "boundary_respect", "source_and_truthfulness"}:
        return "high_value"
    if selected_count > 0:
        return "useful"
    if len(str(label.get("description", ""))) < 60:
        return "needs_human_review"
    return "useful"


def live_readiness(label: dict[str, Any], usefulness: str, risky_unblocked: bool) -> str:
    category = str(label.get("category", ""))
    if category == "unsafe_or_disallowed" or label.get("risk_level") == "high":
        return "integration_blocker" if risky_unblocked else "disallowed"
    if usefulness in {"too_vague", "needs_human_review", "redundant"}:
        return "evidence_only"
    if label.get("internal_only") is True and label.get("allowed_in_live") is False:
        return "safe_for_future_live_style_hint" if label.get("risk_level") == "low" else "internal_only"
    return "internal_only"


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    mapping = load_json(MAPPING_PATH)
    policy = load_json(BACKEND_POLICY_PATH)
    fish_evidence = load_json(FISH_TAXONOMY_EVIDENCE)
    sales_evidence = load_json(SALES_MAPPING_EVIDENCE)
    planner_evidence = load_json(PLANNER_EVIDENCE)

    labels = taxonomy.get("labels", [])
    labels_by_id = label_index(taxonomy)
    selected_counts = Counter(
        label_id
        for item in mapping.get("mappings", [])
        for label_id in item.get("selected_prosody_labels", [])
    )

    description_duplicates = group_by_signature(labels, ("description",))
    when_duplicates = group_by_signature(labels, ("when_to_use",))
    tag_context_duplicates = group_by_signature(labels, ("fish_inspired_tags", "sales_contexts"))
    true_duplicate_label_ids = sorted(
        {
            label_id
            for group in description_duplicates + when_duplicates
            for label_id in group["ids"]
        }
    )
    acceptable_family_similarity_ids = sorted(
        {
            label_id
            for group in tag_context_duplicates
            for label_id in group["ids"]
            if label_id not in true_duplicate_label_ids
        }
    )
    family_group_size = {
        label_id: group["count"]
        for group in tag_context_duplicates
        for label_id in group["ids"]
    }

    hint_counts = Counter(
        str((label.get("backend_mapping") or {}).get("elevenlabs_hint", "")).strip().lower()
        for label in labels
        if isinstance(label.get("backend_mapping"), dict)
    )

    safety_failures: list[str] = []
    backend_failures: list[str] = []
    label_assessments: list[dict[str, Any]] = []
    repeated_template_label_ids: list[str] = []
    needs_specific_hint_label_ids: list[str] = []
    risky_but_blocked: list[str] = []
    risky_and_unblocked: list[str] = []
    integration_blockers: list[str] = []

    for label in labels:
        label_id = str(label.get("label_id", ""))
        category = str(label.get("category", ""))
        backend_mapping = label.get("backend_mapping", {}) if isinstance(label.get("backend_mapping"), dict) else {}
        is_high_risk = category == "unsafe_or_disallowed" or label.get("risk_level") == "high"
        unblocked = is_high_risk and (
            label.get("allowed_in_live") is not False
            or label.get("internal_only") is not True
            or (category == "unsafe_or_disallowed" and "live_call" not in label.get("disallowed_for", []))
        )
        if is_high_risk and unblocked:
            risky_and_unblocked.append(label_id)
            safety_failures.append(f"{label_id}: risky label is not fully blocked")
        elif is_high_risk:
            risky_but_blocked.append(label_id)
        if category == "unsafe_or_disallowed" and label.get("allowed_in_live") is not False:
            safety_failures.append(f"{label_id}: unsafe label marked live-safe")
        if label.get("fish_inspired_tags") and label.get("internal_only") is not True:
            safety_failures.append(f"{label_id}: Fish-inspired tags are not internal_only")
        if label.get("allowed_in_live") is True:
            safety_failures.append(f"{label_id}: allowed_in_live true before integration gate")
        text = " ".join(str(label.get(field, "")) for field in ("label_id", "display_name", "description", "when_to_use", "when_not_to_use", "safety_notes")).lower()
        if any(term in text for term in ("allow fake side effect", "use raw url", "speak internal policy language")) and category not in {"safety_and_compliance", "unsafe_or_disallowed"}:
            safety_failures.append(f"{label_id}: risky allowance language requires review")

        for hint_name in ("elevenlabs_hint", "plain_text_hint", "future_fish_hint", "kokoro_hint", "liquid_hint"):
            value = str(backend_mapping.get(hint_name, ""))
            if not value.strip():
                backend_failures.append(f"{label_id}.{hint_name}: missing")
        elevenlabs_hint = str(backend_mapping.get("elevenlabs_hint", ""))
        future_fish_hint = str(backend_mapping.get("future_fish_hint", "")).lower()
        liquid_hint = str(backend_mapping.get("liquid_hint", "")).lower()
        if has_raw_tag(elevenlabs_hint):
            backend_failures.append(f"{label_id}: ElevenLabs hint contains raw bracket tag")
        if "future" not in future_fish_hint and "later" not in future_fish_hint:
            backend_failures.append(f"{label_id}: future_fish_hint is not future-only")
        if "active" in liquid_hint and "no current" not in liquid_hint:
            backend_failures.append(f"{label_id}: liquid_hint may imply active TTS")

        template_hint = repeated_template_hint(label, hint_counts)
        specific_hint_missing = needs_specific_backend_hint(label)
        if template_hint:
            repeated_template_label_ids.append(label_id)
        if specific_hint_missing:
            needs_specific_hint_label_ids.append(label_id)

        true_duplicate = label_id in true_duplicate_label_ids
        usefulness = label_usefulness(
            label,
            selected_counts[label_id],
            true_duplicate,
            template_hint,
            specific_hint_missing,
        )
        readiness = live_readiness(label, usefulness, unblocked)
        if readiness == "integration_blocker":
            integration_blockers.append(label_id)
        label_assessments.append(
            {
                "label_id": label_id,
                "category": category,
                "selected_count": selected_counts[label_id],
                "duplicate_tag_context_group_size": family_group_size.get(label_id, 1),
                "quality_classification": (
                    "risky_and_unblocked"
                    if unblocked
                    else "risky_but_blocked"
                    if is_high_risk
                    else "true_duplicate"
                    if true_duplicate
                    else "repeated_template_hint"
                    if template_hint
                    else "needs_specific_backend_hint"
                    if specific_hint_missing
                    else "acceptable_family_similarity"
                    if label_id in acceptable_family_similarity_ids
                    else "no_action_needed"
                ),
                "sales_usefulness": usefulness,
                "live_readiness": readiness,
                "risk_level": label.get("risk_level"),
                "status": "needs_human_review" if usefulness in {"too_vague", "redundant"} else "pass",
            }
        )

    category_counts = count_by(labels, "category")
    underrepresented = sorted(category for category, count in category_counts.items() if count < 7)
    overrepresented = sorted(category for category, count in category_counts.items() if count > 20)
    coverage_tags = {tag for item in mapping.get("mappings", []) for tag in item.get("coverage_tags", [])}
    coverage_gaps = sorted(REQUIRED_CONTEXTS - coverage_tags)

    eleven_policy = policy.get("backend_policies", {}).get("elevenlabs_current_provider", {})
    if eleven_policy.get("raw_fish_tag_injection_allowed") is not False:
        safety_failures.append("backend policy allows raw Fish tags in ElevenLabs")

    risky_count = sum(1 for item in label_assessments if item["sales_usefulness"] == "risky")
    too_vague_count = sum(1 for item in label_assessments if item["sales_usefulness"] == "too_vague")
    redundant_count = sum(1 for item in label_assessments if item["sales_usefulness"] == "redundant")
    blocker_count = len(safety_failures) + len(backend_failures)
    warning_count = (
        len(true_duplicate_label_ids)
        + len(repeated_template_label_ids)
        + len(needs_specific_hint_label_ids)
        + len(underrepresented)
        + len(overrepresented)
        + len(coverage_gaps)
    )

    result = {
        "experiment_id": "PROSODY-TAXONOMY-QUALITY-AUDIT-001",
        "phase": "4I4",
        "status": "pass" if blocker_count == 0 else "fail",
        "taxonomy": "runtime/audio_backends/prosody_sales_taxonomy.json",
        "taxonomy_label_count": len(labels),
        "category_count": len(category_counts),
        "category_counts": category_counts,
        "underrepresented_categories": underrepresented,
        "overrepresented_categories": overrepresented,
        "unsafe_disallowed_label_count": category_counts.get("unsafe_or_disallowed", 0),
        "duplicate_label_count": len(true_duplicate_label_ids),
        "true_duplicate_count": len(true_duplicate_label_ids),
        "acceptable_family_similarity_count": len(acceptable_family_similarity_ids),
        "duplicate_groups": {
            "true_duplicate_same_description": description_duplicates[:20],
            "true_duplicate_same_when_to_use": when_duplicates[:20],
            "acceptable_family_similarity_same_fish_tags_and_sales_contexts": tag_context_duplicates[:30],
        },
        "labels_that_should_be_merged": (description_duplicates + when_duplicates)[:20],
        "labels_that_should_stay_separate": [
            "unsafe.* labels stay separate because validators need explicit blocked style families",
            "source.* and trust.* labels overlap by design but separate truthfulness from buyer confidence",
            "repair.* and clarify.* labels stay separate to avoid loop-prone repeated qualification",
            "category-family Fish-inspired tag overlap is acceptable when descriptions and backend hints differ",
        ],
        "coverage_gaps": coverage_gaps,
        "safety_failures": safety_failures,
        "backend_mapping_failures": backend_failures,
        "backend_mapping_boilerplate_label_count": len(repeated_template_label_ids),
        "repeated_template_hint_count": len(repeated_template_label_ids),
        "needs_specific_backend_hint_count": len(needs_specific_hint_label_ids),
        "risky_but_blocked_count": len(risky_but_blocked),
        "risky_unblocked_count": len(risky_and_unblocked),
        "risky_and_unblocked_count": len(risky_and_unblocked),
        "integration_blocker_count": len(integration_blockers) + len(backend_failures),
        "sales_usefulness_counts": dict(Counter(item["sales_usefulness"] for item in label_assessments)),
        "quality_classification_counts": dict(Counter(item["quality_classification"] for item in label_assessments)),
        "live_readiness_counts": dict(Counter(item["live_readiness"] for item in label_assessments)),
        "risky_label_count": risky_count,
        "too_vague_label_count": too_vague_count,
        "redundant_label_count": redundant_count,
        "needs_human_review_count": sum(1 for item in label_assessments if item["status"] == "needs_human_review"),
        "label_assessments": label_assessments,
        "source_evidence_checked": {
            "fish_taxonomy_evidence_label_count": fish_evidence.get("taxonomy_label_count"),
            "sales_mapping_evidence_mapping_count": sales_evidence.get("sales_mapping_count"),
            "planner_evidence_examples_count": planner_evidence.get("examples_count"),
        },
        "blocker_count": blocker_count,
        "warning_count": warning_count,
        "fish_tags_internal_only": all(label.get("internal_only") is True for label in labels if label.get("fish_inspired_tags")),
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "unsafe_labels_blocked": not safety_failures and not risky_and_unblocked,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(TAXONOMY_AUDIT_DIR / "result.json", result)
    write_report(
        TAXONOMY_AUDIT_DIR / "report.md",
        "PROSODY-TAXONOMY-QUALITY-AUDIT-001",
        [
            f"Status: {result['status']}",
            f"- taxonomy_label_count: {len(labels)}",
            f"- true_duplicate_count: {len(true_duplicate_label_ids)}",
            f"- acceptable_family_similarity_count: {len(acceptable_family_similarity_ids)}",
            f"- risky_label_count: {risky_count}",
            f"- risky_unblocked_count: {len(risky_and_unblocked)}",
            f"- too_vague_label_count: {too_vague_count}",
            f"- backend_mapping_boilerplate_label_count: {len(repeated_template_label_ids)}",
            f"- blocker_count: {blocker_count}",
            f"- warning_count: {warning_count}",
            "- Main result: exact duplicate semantics are separated from acceptable family similarity.",
            "- Main recommendation: no live wiring; proceed only when downstream mapping and planner checks also have no blockers.",
            "- No provider calls, audio generation, Fish inference, Liquid inference, Kokoro inference, live wiring, runtime behavior change, or response text change.",
        ],
    )
    print(__import__("json").dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
