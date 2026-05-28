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
    label_index,
    load_json,
    status_counts,
    write_json,
    write_report,
)


def classify_mapping(mapping: dict[str, Any], labels_by_id: dict[str, dict[str, Any]], duplicate_signature_count: int) -> tuple[str, list[str]]:
    reasons: list[str] = []
    selected = mapping.get("selected_prosody_labels", [])
    selected_labels = [labels_by_id.get(label_id, {}) for label_id in selected]
    selected_ids = set(selected)
    unsafe_selected = [label_id for label_id in selected if labels_by_id.get(label_id, {}).get("category") == "unsafe_or_disallowed"]
    if unsafe_selected:
        reasons.append(f"unsafe labels selected: {unsafe_selected}")
    if len(selected) > 8:
        reasons.append("too many selected labels")
    if len(selected) < 3:
        reasons.append("too few selected labels")
    if duplicate_signature_count > 1:
        reasons.append("duplicate selected-label/text signature")
    if mapping.get("energy") in {"high", "medium_high"} and any("deescalation" in label_id or "low_pressure" in label_id for label_id in selected_ids):
        reasons.append("high energy conflicts with deescalation/low pressure")
    if any("urgent" in label_id for label_id in selected_ids) and any("low_pressure" in label_id or "no_pressure" in label_id for label_id in selected_ids):
        reasons.append("urgent pacing conflicts with low-pressure style")
    if mapping.get("close_readiness") == "accepted":
        if any(label_id.startswith("clarify.") for label_id in selected_ids) or "sales.advance_after_answer" in selected_ids:
            reasons.append("terminal acceptance risks new question or continued selling")
    if mapping.get("buyer_said_already_told_you") is True:
        if any(label_id.startswith("clarify.") for label_id in selected_ids):
            reasons.append("already-told-you context risks repeating clarification")
    if mapping.get("sales_move") == "price_answer":
        if "clarify.price_question" in selected_ids:
            reasons.append("price answer risks repeated price qualification")
    if any(label.get("risk_level") == "high" and label.get("category") != "unsafe_or_disallowed" for label in selected_labels):
        reasons.append("high-risk label needs human review before mapping")

    fail_reasons = [reason for reason in reasons if reason.startswith("unsafe labels") or "terminal acceptance risks" in reason]
    if fail_reasons:
        return "fail", reasons
    review_reasons = [reason for reason in reasons if "human review" in reason]
    if review_reasons:
        return "needs_human_review", reasons
    if reasons:
        return "warning", reasons
    return "pass", ["mapping shape is usable for evidence-only planning"]


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    mapping_payload = load_json(MAPPING_PATH)
    labels_by_id = label_index(taxonomy)
    mappings = mapping_payload.get("mappings", [])

    signatures: dict[tuple[str, str, str], int] = defaultdict(int)
    for mapping in mappings:
        signature = (
            "|".join(mapping.get("selected_prosody_labels", [])),
            str(mapping.get("example_spoken_text_before", "")),
            str(mapping.get("example_spoken_text_after", "")),
        )
        signatures[signature] += 1

    assessments: list[dict[str, Any]] = []
    for mapping in mappings:
        signature = (
            "|".join(mapping.get("selected_prosody_labels", [])),
            str(mapping.get("example_spoken_text_before", "")),
            str(mapping.get("example_spoken_text_after", "")),
        )
        status, reasons = classify_mapping(mapping, labels_by_id, signatures[signature])
        assessments.append(
            {
                "mapping_id": mapping.get("mapping_id"),
                "status": status,
                "reasons": reasons,
                "selected_label_count": len(mapping.get("selected_prosody_labels", [])),
                "buyer_emotion": mapping.get("buyer_emotion"),
                "sales_move": mapping.get("sales_move"),
                "objection_type": mapping.get("objection_type"),
                "coverage_tags": mapping.get("coverage_tags", []),
            }
        )

    coverage_tags = {tag for mapping in mappings for tag in mapping.get("coverage_tags", [])}
    missing_contexts = sorted(REQUIRED_CONTEXTS - coverage_tags)
    counts = status_counts(assessments)
    failure_count = counts["fail"]
    warning_count = counts["warning"] + counts["needs_human_review"] + len(missing_contexts)
    duplicate_mapping_count = sum(1 for count in signatures.values() if count > 1)

    result = {
        "experiment_id": "SALES-PROSODY-MAPPING-QUALITY-AUDIT-001",
        "phase": "4I3",
        "status": "pass" if failure_count == 0 else "fail",
        "mapping_count": len(mappings),
        "coverage_by_buyer_emotion": dict(Counter(str(item.get("buyer_emotion")) for item in mappings)),
        "coverage_by_sales_move": dict(Counter(str(item.get("sales_move")) for item in mappings)),
        "coverage_by_objection_type": dict(Counter(str(item.get("objection_type")) for item in mappings)),
        "missing_required_contexts": missing_contexts,
        "duplicate_mapping_signature_count": duplicate_mapping_count,
        "mappings_with_too_many_labels": [item["mapping_id"] for item in assessments if "too many selected labels" in item["reasons"]],
        "mappings_with_too_few_labels": [item["mapping_id"] for item in assessments if "too few selected labels" in item["reasons"]],
        "unsafe_label_mapping_count": sum(1 for item in assessments if any("unsafe labels selected" in reason for reason in item["reasons"])),
        "loop_risk_mapping_count": sum(1 for item in assessments if any("risks" in reason or "repeating" in reason for reason in item["reasons"])),
        "conflict_mapping_count": sum(1 for item in assessments if any("conflicts" in reason for reason in item["reasons"])),
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
            f"- warning_count: {warning_count}",
            f"- failure_count: {failure_count}",
            f"- status_counts: {counts}",
            "- Main warning: the 4I2 mapping intentionally creates repeated low/medium/base variants; this is useful for coverage but noisy for integration.",
            "- Main recommendation: collapse duplicate variants before any live mapping.",
            "- No provider calls, audio generation, Fish inference, Liquid inference, Kokoro inference, live wiring, runtime behavior change, or response text change.",
        ],
    )
    print(__import__("json").dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
