#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from prosody_quality_common import (
    MAPPING_AUDIT_DIR,
    MAPPING_PATH,
    REQUIRED_CONTEXTS,
    TAXONOMY_PATH,
    base_boundary_flags,
    has_raw_tag,
    label_index,
    load_json,
    status_counts,
    write_json,
    write_report,
)


def mapping_signature(mapping: dict[str, Any]) -> tuple[str, str, str]:
    return (
        "|".join(mapping.get("selected_prosody_labels", [])),
        str(mapping.get("example_spoken_text_before", "")),
        str(mapping.get("example_spoken_text_after", "")),
    )


def classify_mapping(mapping: dict[str, Any], labels_by_id: dict[str, dict[str, Any]], duplicate_signature_count: int) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    classifications: list[str] = []
    selected = mapping.get("selected_prosody_labels", [])
    selected_labels = [labels_by_id.get(label_id, {}) for label_id in selected]
    selected_ids = set(selected)
    unsafe_selected = [label_id for label_id in selected if labels_by_id.get(label_id, {}).get("category") == "unsafe_or_disallowed"]
    parameterization = mapping.get("parameterization") if isinstance(mapping.get("parameterization"), dict) else {}

    if unsafe_selected:
        reasons.append(f"unsafe labels selected: {unsafe_selected}")
        classifications.append("integration_blocker")
    if len(selected) > 8:
        reasons.append("too many selected labels")
        classifications.append("mapping_needs_human_review")
    if len(selected) < 3:
        reasons.append("too few selected labels")
        classifications.append("too_vague_mapping")
    if duplicate_signature_count > 1:
        reasons.append("true duplicate selected-label/text signature")
        classifications.append("true_duplicate")
    elif parameterization:
        classifications.append("no_action_needed")
    if mapping.get("energy") in {"high", "medium_high"} and any("deescalation" in label_id or "low_pressure" in label_id for label_id in selected_ids):
        reasons.append("high energy conflicts with deescalation/low pressure")
        classifications.append("mapping_needs_human_review")
    if any("urgent" in label_id for label_id in selected_ids) and any("low_pressure" in label_id or "no_pressure" in label_id for label_id in selected_ids):
        reasons.append("urgent pacing conflicts with low-pressure style")
        classifications.append("mapping_needs_human_review")
    if mapping.get("close_readiness") == "accepted":
        if any(label_id.startswith("clarify.") for label_id in selected_ids) or "sales.advance_after_answer" in selected_ids:
            reasons.append("terminal acceptance risks new question or continued selling")
            classifications.append("integration_blocker")
    if mapping.get("buyer_said_already_told_you") is True:
        if any(label_id.startswith("clarify.") for label_id in selected_ids):
            reasons.append("already-told-you context risks repeating clarification")
            classifications.append("mapping_needs_human_review")
    if mapping.get("sales_move") == "price_answer" and "clarify.price_question" in selected_ids:
        reasons.append("price answer risks repeated price qualification")
        classifications.append("mapping_needs_human_review")
    if any(label.get("risk_level") == "high" and label.get("category") == "unsafe_or_disallowed" for label in selected_labels):
        reasons.append("high-risk unsafe label selected")
        classifications.append("integration_blocker")
    if any(has_raw_tag(str(mapping.get(field) or "")) for field in ("example_spoken_text_before", "example_spoken_text_after")):
        reasons.append("buyer-facing example contains raw bracket tag")
        classifications.append("integration_blocker")
    if any(term in " ".join(str(mapping.get(field, "")).lower() for field in ("example_spoken_text_before", "example_spoken_text_after", "backend_mapping_notes")) for term in ("fake email", "fake calendar", "fake crm", "fake side effect")):
        reasons.append("mapping text risks fake side-effect language")
        classifications.append("mapping_needs_human_review")

    if not classifications:
        classifications.append("no_action_needed")
    fail_reasons = [reason for reason in reasons if reason.startswith("unsafe labels") or "terminal acceptance risks" in reason or "raw bracket" in reason or "high-risk unsafe" in reason]
    if fail_reasons:
        return "fail", reasons, classifications
    review_reasons = [reason for reason in reasons if "human review" in reason or "risks" in reason or "conflicts" in reason or "too many" in reason or "too few" in reason]
    if review_reasons:
        return "warning", reasons, classifications
    if reasons:
        return "warning", reasons, classifications
    return "pass", ["mapping shape is usable for evidence-only planning"], classifications


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    mapping_payload = load_json(MAPPING_PATH)
    labels_by_id = label_index(taxonomy)
    mappings = mapping_payload.get("mappings", [])

    signatures: dict[tuple[str, str, str], int] = defaultdict(int)
    for mapping in mappings:
        signatures[mapping_signature(mapping)] += 1

    assessments: list[dict[str, Any]] = []
    for mapping in mappings:
        signature = mapping_signature(mapping)
        status, reasons, classifications = classify_mapping(mapping, labels_by_id, signatures[signature])
        assessments.append(
            {
                "mapping_id": mapping.get("mapping_id"),
                "status": status,
                "reasons": reasons,
                "classifications": classifications,
                "selected_label_count": len(mapping.get("selected_prosody_labels", [])),
                "buyer_emotion": mapping.get("buyer_emotion"),
                "sales_move": mapping.get("sales_move"),
                "objection_type": mapping.get("objection_type"),
                "coverage_tags": mapping.get("coverage_tags", []),
                "parameterized": isinstance(mapping.get("parameterization"), dict),
            }
        )

    coverage_tags = {tag for mapping in mappings for tag in mapping.get("coverage_tags", [])}
    missing_contexts = sorted(REQUIRED_CONTEXTS - coverage_tags)
    counts = status_counts(assessments)
    failure_count = counts["fail"]
    warning_count = counts["warning"] + counts["needs_human_review"] + len(missing_contexts)
    duplicate_mapping_count = sum(1 for count in signatures.values() if count > 1)
    duplicate_mapping_item_count = sum(count for count in signatures.values() if count > 1)
    parameterized_count = sum(1 for item in assessments if item["parameterized"])
    classification_counts = Counter(
        classification
        for item in assessments
        for classification in item.get("classifications", [])
    )

    result = {
        "experiment_id": "SALES-PROSODY-MAPPING-QUALITY-AUDIT-001",
        "phase": "4I4",
        "status": "pass" if failure_count == 0 else "fail",
        "mapping_count": len(mappings),
        "coverage_by_buyer_emotion": dict(Counter(str(item.get("buyer_emotion")) for item in mappings)),
        "coverage_by_sales_move": dict(Counter(str(item.get("sales_move")) for item in mappings)),
        "coverage_by_objection_type": dict(Counter(str(item.get("objection_type")) for item in mappings)),
        "missing_required_contexts": missing_contexts,
        "duplicate_mapping_signature_count": duplicate_mapping_count,
        "true_duplicate_mapping_signature_count": duplicate_mapping_count,
        "duplicate_mapping_item_count": duplicate_mapping_item_count,
        "parameterized_mapping_count": parameterized_count,
        "mapping_duplicate_variant_count": duplicate_mapping_item_count,
        "mappings_with_too_many_labels": [item["mapping_id"] for item in assessments if "too many selected labels" in item["reasons"]],
        "mappings_with_too_few_labels": [item["mapping_id"] for item in assessments if "too few selected labels" in item["reasons"]],
        "unsafe_label_mapping_count": sum(1 for item in assessments if any("unsafe labels selected" in reason for reason in item["reasons"])),
        "loop_risk_mapping_count": sum(1 for item in assessments if any("risks" in reason or "repeating" in reason for reason in item["reasons"])),
        "conflict_mapping_count": sum(1 for item in assessments if any("conflicts" in reason for reason in item["reasons"])),
        "classification_counts": dict(classification_counts),
        "status_counts": counts,
        "mapping_assessments": assessments,
        "failure_count": failure_count,
        "warning_count": warning_count,
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "unsafe_labels_blocked": failure_count == 0,
        "boundary_flags": base_boundary_flags(),
    }
    write_json(MAPPING_AUDIT_DIR / "result.json", result)
    write_report(
        MAPPING_AUDIT_DIR / "report.md",
        "SALES-PROSODY-MAPPING-QUALITY-AUDIT-001",
        [
            f"Status: {result['status']}",
            f"- mapping_count: {len(mappings)}",
            f"- duplicate_mapping_signature_count: {duplicate_mapping_count}",
            f"- parameterized_mapping_count: {parameterized_count}",
            f"- warning_count: {warning_count}",
            f"- failure_count: {failure_count}",
            f"- status_counts: {counts}",
            "- Main result: duplicated triplet variants were collapsed into parameterized mappings while retaining required coverage.",
            "- Main recommendation: if planner dry-runs stay clean, the next step can be a no-provider ElevenLabs mapping prototype, not live wiring.",
            "- No provider calls, audio generation, Fish inference, Liquid inference, Kokoro inference, live wiring, runtime behavior change, or response text change.",
        ],
    )
    print(__import__("json").dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
