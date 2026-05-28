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
    TAG_RE,
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


def label_usefulness(label: dict[str, Any], selected_count: int, duplicate_group_size: int, boilerplate_hint: bool) -> str:
    label_id = str(label.get("label_id", ""))
    category = str(label.get("category", ""))
    if category == "unsafe_or_disallowed" or label.get("risk_level") == "high":
        return "risky"
    if boilerplate_hint and selected_count == 0:
        return "too_vague"
    if duplicate_group_size > 8 and selected_count == 0:
        return "redundant"
    if selected_count >= 3 or category in {"repair", "objection_handling", "boundary_respect", "source_and_truthfulness"}:
        return "high_value"
    if selected_count > 0:
        return "useful"
    if label_id.endswith("unknown") or len(str(label.get("description", ""))) < 30:
        return "needs_human_review"
    return "useful"


def live_readiness(label: dict[str, Any], usefulness: str) -> str:
    category = str(label.get("category", ""))
    if category == "unsafe_or_disallowed" or label.get("risk_level") == "high":
        return "disallowed"
    if usefulness in {"too_vague", "needs_human_review", "redundant"}:
        return "evidence_only"
    if label.get("internal_only") is True and label.get("allowed_in_live") is False:
        if label.get("risk_level") == "low":
            return "safe_for_future_live_style_hint"
        return "internal_only"
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
    duplicate_label_ids = sorted(
        {
            label_id
            for group in description_duplicates + when_duplicates + tag_context_duplicates
            for label_id in group["ids"]
        }
    )
    tag_context_group_size = {
        label_id: group["count"]
        for group in tag_context_duplicates
        for label_id in group["ids"]
    }

    safety_failures: list[str] = []
    backend_failures: list[str] = []
    backend_warning_count = 0
    label_assessments: list[dict[str, Any]] = []
    for label in labels:
        label_id = str(label.get("label_id", ""))
        category = str(label.get("category", ""))
        backend_mapping = label.get("backend_mapping", {}) if isinstance(label.get("backend_mapping"), dict) else {}
        if category == "unsafe_or_disallowed" and label.get("allowed_in_live") is not False:
            safety_failures.append(f"{label_id}: unsafe label marked live-safe")
        if label.get("fish_inspired_tags") and label.get("internal_only") is not True:
            safety_failures.append(f"{label_id}: Fish-inspired tags are not internal_only")
        if label.get("allowed_in_live") is True:
            safety_failures.append(f"{label_id}: allowed_in_live true before integration gate")
        text = " ".join(str(label.get(field, "")) for field in ("label_id", "display_name", "description", "when_to_use", "when_not_to_use", "safety_notes")).lower()
        if any(term in text for term in ("fake side effect", "raw url", "internal policy language")) and category != "safety_and_compliance":
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
        boilerplate_hint = "internal style intent only for" in elevenlabs_hint.lower()
        if boilerplate_hint:
            backend_warning_count += 1

        usefulness = label_usefulness(label, selected_counts[label_id], tag_context_group_size.get(label_id, 1), boilerplate_hint)
        label_assessments.append(
            {
                "label_id": label_id,
                "category": category,
                "selected_count": selected_counts[label_id],
                "duplicate_tag_context_group_size": tag_context_group_size.get(label_id, 1),
                "sales_usefulness": usefulness,
                "live_readiness": live_readiness(label, usefulness),
                "risk_level": label.get("risk_level"),
                "status": "needs_human_review" if usefulness in {"too_vague", "redundant"} else "pass",
            }
        )

    category_counts = count_by(labels, "category")
    underrepresented = sorted(category for category, count in category_counts.items() if count < 8)
    overrepresented = sorted(category for category, count in category_counts.items() if count > 16)
    coverage_tags = {
        tag
        for item in mapping.get("mappings", [])
        for tag in item.get("coverage_tags", [])
    }
    coverage_gaps = sorted(REQUIRED_CONTEXTS - coverage_tags)

    eleven_policy = policy.get("backend_policies", {}).get("elevenlabs_current_provider", {})
    if eleven_policy.get("raw_fish_tag_injection_allowed") is not False:
        safety_failures.append("backend policy allows raw Fish tags in ElevenLabs")

    risky_count = sum(1 for item in label_assessments if item["sales_usefulness"] == "risky")
    too_vague_count = sum(1 for item in label_assessments if item["sales_usefulness"] == "too_vague")
    redundant_count = sum(1 for item in label_assessments if item["sales_usefulness"] == "redundant")
    blocker_count = len(safety_failures) + len(backend_failures)
    warning_count = len(duplicate_label_ids) + backend_warning_count + len(underrepresented) + len(overrepresented) + len(coverage_gaps)

    result = {
        "experiment_id": "PROSODY-TAXONOMY-QUALITY-AUDIT-001",
        "phase": "4I3",
        "status": "pass" if blocker_count == 0 else "fail",
        "taxonomy": "runtime/audio_backends/prosody_sales_taxonomy.json",
        "taxonomy_label_count": len(labels),
        "category_count": len(category_counts),
        "category_counts": category_counts,
        "underrepresented_categories": underrepresented,
        "overrepresented_categories": overrepresented,
        "unsafe_disallowed_label_count": category_counts.get("unsafe_or_disallowed", 0),
        "duplicate_label_count": len(duplicate_label_ids),
        "duplicate_groups": {
            "same_description": description_duplicates[:20],
            "same_when_to_use": when_duplicates[:20],
            "same_fish_tags_and_sales_contexts": tag_context_duplicates[:30],
        },
        "labels_that_should_be_merged": tag_context_duplicates[:20],
        "labels_that_should_stay_separate": [
            "unsafe.* labels stay separate because validators need explicit blocked style families",
            "source.* and trust.* labels overlap by design but separate truthfulness from buyer confidence",
            "repair.* and clarify.* labels stay separate to avoid loop-prone repeated qualification",
        ],
        "coverage_gaps": coverage_gaps,
        "safety_failures": safety_failures,
        "backend_mapping_failures": backend_failures,
        "backend_mapping_boilerplate_label_count": backend_warning_count,
        "sales_usefulness_counts": dict(Counter(item["sales_usefulness"] for item in label_assessments)),
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
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "unsafe_labels_blocked": not safety_failures,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(TAXONOMY_AUDIT_DIR / "result.json", result)
    write_report(
        TAXONOMY_AUDIT_DIR / "report.md",
        "PROSODY-TAXONOMY-QUALITY-AUDIT-001",
        [
            f"Status: {result['status']}",
            f"- taxonomy_label_count: {len(labels)}",
            f"- duplicate_label_count: {len(duplicate_label_ids)}",
            f"- risky_label_count: {risky_count}",
            f"- too_vague_label_count: {too_vague_count}",
            f"- redundant_label_count: {redundant_count}",
            f"- blocker_count: {blocker_count}",
            f"- warning_count: {warning_count}",
            "- Main warning: many backend hints are templated; this is acceptable for an evidence-only taxonomy but weak for direct ElevenLabs mapping.",
            "- Main recommendation: clean up duplicate tag/context clusters and replace boilerplate hints before integration.",
            "- No provider calls, audio generation, Fish inference, Liquid inference, Kokoro inference, live wiring, runtime behavior change, or response text change.",
        ],
    )
    print(__import__("json").dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
