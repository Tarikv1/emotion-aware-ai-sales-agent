#!/usr/bin/env python3
from __future__ import annotations

import json
import re

from prosody_quality_common import (
    BACKEND_POLICY_PATH,
    CLEANUP_EVIDENCE_DIR,
    CLEANUP_PLAN_DIR,
    DRY_RUN_AUDIT_DIR,
    MAPPING_PATH,
    RULES_PATH,
    TAXONOMY_PATH,
    assert_common_no_side_effects,
    count_by,
    load_json,
)


REQUIRED_CATEGORIES = {
    "pacing",
    "pause",
    "volume",
    "pitch",
    "tone",
    "warmth",
    "confidence",
    "energy",
    "clarity",
    "emotion_response",
    "objection_handling",
    "trust_building",
    "sales_delivery",
    "plan_explanation",
    "recommendation_delivery",
    "closing_delivery",
    "repair",
    "clarification",
    "boundary_respect",
    "phone_call_delivery",
    "multilingual_delivery",
    "source_and_truthfulness",
    "safety_and_compliance",
    "unsafe_or_disallowed",
}


def has_raw_tag(value: str) -> bool:
    return bool(re.search(r"\[[^\]\n]{2,80}\]", value))


def main() -> int:
    failures: list[str] = []
    cleanup_result_path = CLEANUP_EVIDENCE_DIR / "result.json"
    cleanup_report_path = CLEANUP_EVIDENCE_DIR / "report.md"
    cleanup_plan_path = CLEANUP_PLAN_DIR / "result.json"
    for path in (cleanup_plan_path, cleanup_result_path, cleanup_report_path):
        if not path.is_file():
            failures.append(f"missing cleanup artifact: {path}")

    taxonomy = load_json(TAXONOMY_PATH)
    mapping_payload = load_json(MAPPING_PATH)
    rules_payload = load_json(RULES_PATH)
    policy = load_json(BACKEND_POLICY_PATH)
    cleanup = load_json(cleanup_result_path) if cleanup_result_path.is_file() else {}
    dry_run = load_json(DRY_RUN_AUDIT_DIR / "result.json") if (DRY_RUN_AUDIT_DIR / "result.json").is_file() else {}

    labels = taxonomy.get("labels", [])
    mappings = mapping_payload.get("mappings", [])
    rules = rules_payload.get("composition_rules", [])
    category_counts = count_by(labels, "category")
    categories = set(category_counts)

    if len(labels) < 220:
        failures.append(f"taxonomy label count must be >= 220, got {len(labels)}")
    missing_categories = sorted(REQUIRED_CATEGORIES - categories)
    if missing_categories:
        failures.append(f"required categories missing after cleanup: {missing_categories}")
    unsafe_labels = [label for label in labels if label.get("category") == "unsafe_or_disallowed" or str(label.get("label_id", "")).startswith("unsafe.")]
    if len(unsafe_labels) < 10:
        failures.append(f"unsafe/disallowed labels were not preserved, got {len(unsafe_labels)}")
    for label in unsafe_labels:
        label_id = label.get("label_id")
        if label.get("allowed_in_live") is not False:
            failures.append(f"{label_id}: unsafe label marked live-allowed")
        if label.get("internal_only") is not True:
            failures.append(f"{label_id}: unsafe label must remain internal_only")
        if label.get("risk_level") != "high":
            failures.append(f"{label_id}: unsafe label must be high risk")
    for label in labels:
        label_id = label.get("label_id")
        if label.get("fish_inspired_tags") and label.get("internal_only") is not True:
            failures.append(f"{label_id}: Fish tags must remain internal only")
        backend_mapping = label.get("backend_mapping", {}) if isinstance(label.get("backend_mapping"), dict) else {}
        if has_raw_tag(str(backend_mapping.get("elevenlabs_hint") or "")):
            failures.append(f"{label_id}: raw Fish-style tag leaked into ElevenLabs hint")

    backend_policies = policy.get("backend_policies", {}) if isinstance(policy.get("backend_policies"), dict) else {}
    elevenlabs = backend_policies.get("elevenlabs_current_provider", {})
    if elevenlabs.get("current_voice_path") is not True:
        failures.append("ElevenLabs current path changed")
    if elevenlabs.get("raw_fish_tag_injection_allowed") is not False:
        failures.append("ElevenLabs raw Fish tag injection must remain false")
    liquid = backend_policies.get("liquid_audio", {})
    if liquid.get("current_tts_backend") is not False or liquid.get("status") != "architecture_inspiration_only":
        failures.append("Liquid must remain architecture inspiration only and not active TTS")

    if len(mappings) < 80:
        failures.append(f"mapping count must be >= 80, got {len(mappings)}")
    if len(rules) < 40:
        failures.append(f"composition rules count must be >= 40, got {len(rules)}")
    if int(dry_run.get("dry_run_status_counts", {}).get("fail", 0)) != 0:
        failures.append("planner dry-run has failures")

    for key in (
        "provider_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if cleanup.get(key) is not False:
            failures.append(f"cleanup.{key} must be false")
    if cleanup.get("live_wiring_allowed") is not False:
        failures.append("cleanup must keep live_wiring_allowed false")
    if cleanup.get("fish_tags_internal_only") is not True:
        failures.append("cleanup must keep Fish tags internal only")
    if cleanup.get("raw_fish_tags_allowed_in_elevenlabs_text") is not False:
        failures.append("cleanup must block raw Fish tags in ElevenLabs text")
    recommendation = str(cleanup.get("cleanup_decision") or "").lower()
    if "prototype" in recommendation and "no provider" not in recommendation:
        failures.append("prototype recommendation must be no-provider only")
    if "live" in recommendation and "live wiring" in recommendation:
        failures.append("cleanup decision must not recommend live wiring")
    failures.extend(assert_common_no_side_effects(cleanup))

    output = {
        "status": "pass" if not failures else "fail",
        "cleanup_result": str(cleanup_result_path),
        "taxonomy_label_count": len(labels),
        "mapping_count": len(mappings),
        "composition_rule_count": len(rules),
        "planner_dry_run_status_counts": dry_run.get("dry_run_status_counts"),
        "cleanup_decision": cleanup.get("cleanup_decision"),
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
