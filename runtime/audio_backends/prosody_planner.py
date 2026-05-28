"""Deterministic sales prosody planner prototype.

This module is config-only at runtime: it loads local JSON files, scores local
sales-state mappings, and returns an internal prosody plan. It does not call
providers, load models, install packages, or alter live spoken text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent
TAXONOMY_PATH = CONFIG_DIR / "prosody_sales_taxonomy.json"
MAPPING_PATH = CONFIG_DIR / "sales_prosody_mapping.json"
RULES_PATH = CONFIG_DIR / "prosody_composition_rules.json"
BACKEND_POLICY_PATH = CONFIG_DIR / "prosody_backend_mapping_policy.json"

MATCH_FIELDS = (
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
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def load_prosody_taxonomy() -> dict[str, Any]:
    return _load_json(TAXONOMY_PATH)


def load_sales_prosody_mapping() -> dict[str, Any]:
    return _load_json(MAPPING_PATH)


def load_composition_rules() -> dict[str, Any]:
    return _load_json(RULES_PATH)


def _load_backend_policy() -> dict[str, Any]:
    return _load_json(BACKEND_POLICY_PATH)


def _normalize_context(context: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "buyer_emotion": "neutral",
        "buyer_friction_level": "low",
        "buyer_confusion_level": "none",
        "buyer_skepticism_level": "none",
        "buyer_engagement_level": "medium",
        "sales_move": "answer",
        "objection_type": "none",
        "decision_stage": "discovery",
        "close_readiness": "not_ready",
        "safety_boundary_detected": False,
        "buyer_said_already_told_you": False,
        "asr_uncertainty_detected": False,
        "backend_id": "plain_text_fallback",
    }
    for key, value in context.items():
        normalized[key] = value
    return normalized


def _score_mapping(mapping: dict[str, Any], context: dict[str, Any]) -> int:
    score = 0
    for field in MATCH_FIELDS:
        expected = mapping.get(field)
        actual = context.get(field)
        if expected == actual:
            score += 3 if isinstance(expected, bool) else 2
        elif expected in ("any", None, ""):
            score += 0
        elif isinstance(expected, str) and expected == "none" and actual in (None, "", "none", False):
            score += 1
    return score


def _conditions_match(conditions: dict[str, Any], context: dict[str, Any]) -> bool:
    for key, expected in conditions.items():
        if expected == "any":
            continue
        actual = context.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
            continue
        if actual != expected:
            return False
    return True


def _dedupe(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    deduped: list[Any] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _label_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["label_id"]: item
        for item in taxonomy.get("labels", [])
        if isinstance(item, dict) and isinstance(item.get("label_id"), str)
    }


def _select_mapping(mappings: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    if not mappings:
        raise ValueError("sales prosody mapping has no mappings")
    return max(mappings, key=lambda mapping: (_score_mapping(mapping, context), mapping.get("mapping_id", "")))


def _select_rules(rules: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        rule
        for rule in rules
        if isinstance(rule.get("input_conditions"), dict)
        and _conditions_match(rule["input_conditions"], context)
    ]


def _backend_hints(policy: dict[str, Any], backend_id: str) -> dict[str, Any]:
    aliases = policy.get("backend_aliases", {})
    policy_key = aliases.get(backend_id, backend_id) if isinstance(aliases, dict) else backend_id
    backend_policies = policy.get("backend_policies", {})
    backend_policy = backend_policies.get(policy_key, {}) if isinstance(backend_policies, dict) else {}
    return {
        "backend_id": backend_id,
        "policy_key": policy_key,
        "mapping_allowed_now": backend_policy.get("mapping_allowed_now", False),
        "tag_injection_allowed": backend_policy.get("raw_fish_tag_injection_allowed", False),
        "notes": backend_policy.get("mapping_strategy", []),
    }


def plan_prosody_for_sales_turn(context: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_context(context)
    taxonomy = load_prosody_taxonomy()
    mapping_payload = load_sales_prosody_mapping()
    rules_payload = load_composition_rules()
    policy = _load_backend_policy()

    labels_by_id = _label_index(taxonomy)
    selected_mapping = _select_mapping(mapping_payload.get("mappings", []), normalized)
    selected_rules = _select_rules(rules_payload.get("composition_rules", []), normalized)

    selected_label_ids = list(selected_mapping.get("selected_prosody_labels", []))
    avoid_label_ids: list[str] = []
    for rule in selected_rules:
        selected_label_ids.extend(rule.get("selected_label_ids", []))
        avoid_label_ids.extend(rule.get("avoid_label_ids", []))
    requested_label_ids = _dedupe(selected_label_ids)
    unknown_label_ids = [label_id for label_id in requested_label_ids if label_id not in labels_by_id]
    unsafe_selected_ids = [
        label_id
        for label_id in requested_label_ids
        if label_id in labels_by_id and labels_by_id[label_id].get("category") == "unsafe_or_disallowed"
    ]
    avoid_label_ids = [label_id for label_id in _dedupe(avoid_label_ids) if label_id in labels_by_id]
    avoid_set = set(avoid_label_ids)
    selected_label_ids = [
        label_id
        for label_id in requested_label_ids
        if label_id in labels_by_id
        and labels_by_id[label_id].get("category") != "unsafe_or_disallowed"
        and label_id not in avoid_set
    ]
    warnings: list[str] = []
    if unknown_label_ids:
        warnings.append(f"unknown labels ignored: {unknown_label_ids}")
    if unsafe_selected_ids:
        warnings.append(f"unsafe labels blocked from selection: {unsafe_selected_ids}")
    if not selected_rules:
        warnings.append("no composition rule matched; using best sales-state mapping only")

    first_rule = selected_rules[0] if selected_rules else {}
    output_style = first_rule.get("output_style", {}) if isinstance(first_rule.get("output_style"), dict) else {}
    fish_tags: list[str] = []
    for label_id in selected_label_ids:
        fish_tags.extend(labels_by_id[label_id].get("fish_inspired_tags", []))

    return {
        "cleanup_version": taxonomy.get("cleanup_version", "none"),
        "taxonomy_version": taxonomy.get("schema_version", 1),
        "voice_intent": selected_mapping.get("sales_move", normalized["sales_move"]),
        "selected_prosody_labels": selected_label_ids,
        "pace": output_style.get("pace") or selected_mapping.get("pace", "medium"),
        "warmth": output_style.get("warmth") or selected_mapping.get("warmth", "neutral_warm"),
        "confidence": output_style.get("confidence") or selected_mapping.get("confidence", "calm"),
        "energy": output_style.get("energy") or selected_mapping.get("energy", "medium"),
        "pause_policy": output_style.get("pause_policy") or selected_mapping.get("pause_policy", "none"),
        "emphasis_terms": selected_mapping.get("emphasis_policy", []),
        "avoid": _dedupe(list(selected_mapping.get("avoid_styles", [])) + avoid_label_ids),
        "backend_hints": _backend_hints(policy, str(normalized.get("backend_id") or "plain_text_fallback")),
        "planner_warnings": warnings,
        "internal_only_label_ids": [label_id for label_id in selected_label_ids if labels_by_id[label_id].get("internal_only") is True],
        "fish_inspired_tags_internal_only": True,
        "fish_inspired_tags_internal_only_values": _dedupe(fish_tags),
        "spoken_text_tag_injection_allowed": False,
        "live_runtime_wiring_changed": False,
        "matched_mapping_id": selected_mapping.get("mapping_id"),
        "matched_rule_ids": [rule.get("rule_id") for rule in selected_rules],
    }


def validate_prosody_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = {
        "voice_intent",
        "selected_prosody_labels",
        "pace",
        "warmth",
        "confidence",
        "energy",
        "pause_policy",
        "emphasis_terms",
        "avoid",
        "backend_hints",
        "fish_inspired_tags_internal_only",
        "spoken_text_tag_injection_allowed",
        "live_runtime_wiring_changed",
    }
    missing = sorted(required_fields - set(plan))
    if missing:
        errors.append(f"missing required fields: {missing}")
    if plan.get("spoken_text_tag_injection_allowed") is not False:
        errors.append("spoken text tag injection must remain false")
    if plan.get("live_runtime_wiring_changed") is not False:
        errors.append("live runtime wiring must remain false")
    if plan.get("fish_inspired_tags_internal_only") is not True:
        errors.append("Fish-inspired tags must remain internal only")
    if not isinstance(plan.get("selected_prosody_labels"), list) or not plan.get("selected_prosody_labels"):
        errors.append("selected_prosody_labels must be a non-empty list")
    backend_hints = plan.get("backend_hints")
    if not isinstance(backend_hints, dict):
        errors.append("backend_hints must be a dict")
    elif backend_hints.get("tag_injection_allowed") is not False:
        errors.append("backend_hints.tag_injection_allowed must remain false")
    else:
        hint_texts: list[str] = []
        for value in backend_hints.values():
            if isinstance(value, str):
                hint_texts.append(value)
            elif isinstance(value, list):
                hint_texts.extend(str(item) for item in value)
        if any("[" in value and "]" in value for value in hint_texts):
            errors.append("backend_hints must not contain raw bracket tags")
    return errors
