#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_sales_taxonomy.json"
RULES_PATH = ROOT / "runtime" / "audio_backends" / "prosody_composition_rules.json"
MAPPING_PATH = ROOT / "runtime" / "audio_backends" / "sales_prosody_mapping.json"
POLICY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_backend_mapping_policy.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "SALES-PROSODY-MAPPING-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "SALES-PROSODY-MAPPING-001" / "report.md"

REQUIRED_RULE_SCENARIOS = {
    "confused_buyer_plan_explanation",
    "confused_buyer_price",
    "skeptical_buyer_source_question",
    "skeptical_buyer_competitor_objection",
    "impatient_buyer_direct_price",
    "price_objection_heavy_use",
    "price_objection_low_budget",
    "current_tool_objection",
    "privacy_concern",
    "buyer_already_told_you",
    "buyer_correction",
    "asr_uncertainty",
    "buyer_same_question_again",
    "use_case_discovery",
    "intensity_discovery",
    "team_vs_individual_clarification",
    "recommendation_after_enough_context",
    "plus_vs_pro_comparison",
    "pro_tier_selection",
    "no_fit_close",
    "terminal_acceptance",
    "boundary_no_email",
    "boundary_no_crm",
    "boundary_no_calendar",
    "source_affiliation_answer",
    "opening_permission_check",
    "barge_in_recovery",
    "buyer_frustration",
    "buyer_disengaged",
    "buyer_interested",
    "buyer_not_using_ai",
    "buyer_using_chatgpt_and_other_tools",
    "buyer_chatgpt_or_maybe_claude",
    "plans_are_models_or_subscriptions",
    "signup_path",
    "upgrade_path",
    "data_privacy_training",
    "wrong_product_question",
    "unsupported_claim_request",
    "final_goodbye",
}
REQUIRED_MAPPING_COVERAGE = {
    "confusion",
    "skepticism",
    "impatience",
    "price_objection",
    "competitor_objection",
    "privacy_objection",
    "source_affiliation_question",
    "plan_explanation",
    "direct_price_question",
    "recommendation",
    "close",
    "no_fit",
    "terminal_acceptance",
    "buyer_correction",
    "asr_uncertainty",
    "already_told_you",
    "same_question_again",
    "disengaged",
    "interested",
    "boundary_request",
    "wrong_product",
    "unsupported_claim",
}
REQUIRED_RULE_FIELDS = {
    "rule_id",
    "input_conditions",
    "selected_label_ids",
    "avoid_label_ids",
    "output_style",
    "text_shaping_guidance",
    "backend_notes",
    "safety_notes",
}
REQUIRED_MAPPING_FIELDS = {
    "mapping_id",
    "buyer_emotion",
    "buyer_friction_level",
    "buyer_confusion_level",
    "buyer_skepticism_level",
    "buyer_engagement_level",
    "sales_move",
    "objection_type",
    "decision_stage",
    "close_readiness",
    "safety_boundary_detected",
    "buyer_said_already_told_you",
    "asr_uncertainty_detected",
    "selected_prosody_labels",
    "pace",
    "warmth",
    "confidence",
    "energy",
    "pause_policy",
    "emphasis_policy",
    "avoid_styles",
    "example_spoken_text_before",
    "example_spoken_text_after",
    "backend_mapping_notes",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


def has_raw_tag(text: str) -> bool:
    return bool(re.search(r"\[[^\]\n]{2,80}\]", text))


def assert_false_flags(payload: dict[str, Any], prefix: str, failures: list[str]) -> None:
    flags = payload.get("boundary_flags", {}) if isinstance(payload.get("boundary_flags"), dict) else {}
    for key in (
        "provider_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "fish_inference_performed",
        "fish_install_performed",
        "local_model_generation_made",
        "live_runtime_wiring_changed",
        "runtime_behavior_changed",
        "response_text_changed",
        "spoken_text_tag_injection_allowed",
    ):
        if flags.get(key) is not False:
            failures.append(f"{prefix}.boundary_flags.{key} must be false")


def main() -> int:
    failures: list[str] = []
    try:
        taxonomy = load_json(TAXONOMY_PATH)
        rules_payload = load_json(RULES_PATH)
        mapping_payload = load_json(MAPPING_PATH)
        policy = load_json(POLICY_PATH)
    except AssertionError as exc:
        print(json.dumps({"status": "fail", "failures": [str(exc)]}, indent=2))
        return 1

    label_ids = {
        item.get("label_id")
        for item in taxonomy.get("labels", [])
        if isinstance(item, dict) and isinstance(item.get("label_id"), str)
    }
    rules = rules_payload.get("composition_rules")
    if not isinstance(rules, list):
        failures.append("composition_rules must be a list")
        rules = []
    if len(rules) < 40:
        failures.append(f"composition rule count must be >= 40, got {len(rules)}")
    rule_scenarios = set()
    for rule in rules:
        if not isinstance(rule, dict):
            failures.append("composition rule entries must be objects")
            continue
        rule_id = str(rule.get("rule_id") or "")
        scenario = rule_id.replace("rule.", "")
        rule_scenarios.add(scenario)
        missing = sorted(REQUIRED_RULE_FIELDS - set(rule))
        if missing:
            failures.append(f"{rule_id} missing fields: {missing}")
        for field_name in ("selected_label_ids", "avoid_label_ids"):
            values = rule.get(field_name)
            if not isinstance(values, list):
                failures.append(f"{rule_id}.{field_name} must be a list")
                continue
            unknown = sorted(str(value) for value in values if value not in label_ids)
            if unknown:
                failures.append(f"{rule_id}.{field_name} has unknown label IDs: {unknown}")
        style = rule.get("output_style")
        if not isinstance(style, dict):
            failures.append(f"{rule_id}.output_style must be an object")
        else:
            for key in ("pace", "warmth", "confidence", "energy", "pause_policy"):
                if not style.get(key):
                    failures.append(f"{rule_id}.output_style.{key} is required")
    missing_rule_scenarios = sorted(REQUIRED_RULE_SCENARIOS - rule_scenarios)
    if missing_rule_scenarios:
        failures.append(f"missing required composition scenarios: {missing_rule_scenarios}")

    mappings = mapping_payload.get("mappings")
    if not isinstance(mappings, list):
        failures.append("sales mappings must be a list")
        mappings = []
    if len(mappings) < 100:
        failures.append(f"sales mapping count must be >= 100, got {len(mappings)}")
    mapping_coverage: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            failures.append("sales mapping entries must be objects")
            continue
        mapping_id = str(mapping.get("mapping_id") or "")
        missing = sorted(REQUIRED_MAPPING_FIELDS - set(mapping))
        if missing:
            failures.append(f"{mapping_id} missing fields: {missing}")
        selected = mapping.get("selected_prosody_labels")
        if not isinstance(selected, list) or not selected:
            failures.append(f"{mapping_id}.selected_prosody_labels must be a non-empty list")
        else:
            unknown = sorted(str(value) for value in selected if value not in label_ids)
            if unknown:
                failures.append(f"{mapping_id} has unknown selected labels: {unknown}")
        mapping_coverage.update(mapping.get("coverage_tags") or [])
        for text_field in ("example_spoken_text_before", "example_spoken_text_after"):
            value = str(mapping.get(text_field) or "")
            if has_raw_tag(value):
                failures.append(f"{mapping_id}.{text_field} contains a raw bracket tag")
    missing_mapping_coverage = sorted(REQUIRED_MAPPING_COVERAGE - mapping_coverage)
    if missing_mapping_coverage:
        failures.append(f"missing required mapping coverage: {missing_mapping_coverage}")

    assert_false_flags(rules_payload, "composition_rules", failures)
    assert_false_flags(mapping_payload, "sales_prosody_mapping", failures)

    backend_policies = policy.get("backend_policies", {}) if isinstance(policy.get("backend_policies"), dict) else {}
    if backend_policies.get("elevenlabs_current_provider", {}).get("raw_fish_tag_injection_allowed") is not False:
        failures.append("backend policy must block Fish tag injection into ElevenLabs")
    if backend_policies.get("liquid_audio", {}).get("status") != "architecture_inspiration_only":
        failures.append("Liquid must remain architecture inspiration only")

    for evidence_path in (RESULT_PATH, REPORT_PATH):
        if not evidence_path.is_file():
            failures.append(f"missing evidence file: {rel(evidence_path)}")
    if RESULT_PATH.is_file():
        result = load_json(RESULT_PATH)
        if int(result.get("composition_rule_count") or -1) != len(rules):
            failures.append("sales mapping evidence composition rule count mismatch")
        if int(result.get("sales_mapping_count") or -1) != len(mappings):
            failures.append("sales mapping evidence mapping count mismatch")
        if int(result.get("examples_count") or 0) < 40:
            failures.append("sales mapping evidence must include at least 40 examples")
        for example in result.get("examples", []):
            if not isinstance(example, dict):
                failures.append("evidence examples must be objects")
                continue
            if example.get("tag_injection_allowed") is not False:
                failures.append(f"{example.get('example_id')} must block tag injection")
            if example.get("buyer_facing_text_contains_raw_fish_tags") is not False:
                failures.append(f"{example.get('example_id')} must not contain buyer-facing Fish tags")
            for field_name in ("plain_text", "prosody_shaped_text"):
                if has_raw_tag(str(example.get(field_name) or "")):
                    failures.append(f"{example.get('example_id')}.{field_name} contains a raw bracket tag")

    output = {
        "status": "pass" if not failures else "fail",
        "composition_rules": rel(RULES_PATH),
        "composition_rule_count": len(rules),
        "sales_mapping": rel(MAPPING_PATH),
        "sales_mapping_count": len(mappings),
        "mapping_coverage_count": len(mapping_coverage),
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "failures": failures,
    }
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
