from __future__ import annotations

from typing import Any

from runtime.action_selector.action_selector_contract import action_labels, normalize_text, validate_selector_output
from runtime.action_selector.non_llm_action_selector import RuleBasedActionSelector
from runtime.action_selector.shadow_mode_contract import (
    DISAGREEMENT_TYPES,
    ShadowModeInput,
    ShadowModeOutput,
    load_shadow_config,
)


def build_shadow_input(
    *,
    turn_id: str,
    campaign_id: str,
    buyer_utterance_text: str,
    normalized_buyer_text: str = "",
    existing_runtime_action_id: str = "",
    existing_runtime_response_text: str = "",
    memory_summary: str = "",
    known_context: dict[str, Any] | None = None,
    safety_boundary_detected: bool = False,
    previous_action_id: str = "",
    previous_answered_topic: str = "",
    evidence_source: str = "",
) -> dict[str, Any]:
    payload = ShadowModeInput(
        turn_id=turn_id,
        campaign_id=campaign_id,
        buyer_utterance_text=buyer_utterance_text,
        normalized_buyer_text=normalized_buyer_text or normalize_text(buyer_utterance_text),
        existing_runtime_action_id=existing_runtime_action_id,
        existing_runtime_response_text=existing_runtime_response_text,
        memory_summary=memory_summary,
        known_context=known_context or {},
        safety_boundary_detected=safety_boundary_detected,
        previous_action_id=previous_action_id,
        previous_answered_topic=previous_answered_topic,
        evidence_source=evidence_source,
    )
    return payload.to_dict()


def _family_lookup(config: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    families = config.get("compatible_action_families")
    if not isinstance(families, dict):
        return result
    for family, actions in families.items():
        for action in actions if isinstance(actions, list) else []:
            result[str(action)] = str(family)
    return result


def _more_specific(selector_action_id: str, runtime_action_id: str, config: dict[str, Any]) -> bool:
    mapping = config.get("more_specific_than") if isinstance(config.get("more_specific_than"), dict) else {}
    values = mapping.get(runtime_action_id)
    return isinstance(values, list) and selector_action_id in values


def classify_shadow_agreement(
    *,
    selector_action_id: str,
    runtime_action_id: str = "",
    expected_action_id: str = "",
    safety_status: str = "safe",
    fallback_required: bool = False,
) -> dict[str, Any]:
    config = load_shadow_config()
    labels = action_labels()
    if selector_action_id not in labels or safety_status.startswith("unsafe"):
        return {"agreement_with_runtime": False, "disagreement_type": "unsafe_selector"}
    comparator = runtime_action_id or expected_action_id
    if not comparator:
        return {"agreement_with_runtime": False, "disagreement_type": "unknown"}
    if selector_action_id == comparator:
        return {"agreement_with_runtime": bool(runtime_action_id), "disagreement_type": "same_action"}

    family_lookup = _family_lookup(config)
    selector_family = family_lookup.get(selector_action_id)
    comparator_family = family_lookup.get(comparator)
    if selector_family and selector_family == comparator_family:
        if _more_specific(selector_action_id, comparator, config):
            return {"agreement_with_runtime": bool(runtime_action_id), "disagreement_type": "selector_more_specific"}
        if _more_specific(comparator, selector_action_id, config):
            return {"agreement_with_runtime": bool(runtime_action_id), "disagreement_type": "runtime_more_specific"}
        return {"agreement_with_runtime": bool(runtime_action_id), "disagreement_type": "compatible_action"}

    if fallback_required:
        return {"agreement_with_runtime": False, "disagreement_type": "selector_possible_regression"}
    if selector_action_id in set(config.get("safety_priority_actions") or []) and comparator not in set(config.get("safety_priority_actions") or []):
        return {"agreement_with_runtime": False, "disagreement_type": "selector_possible_improvement"}
    if comparator in set(config.get("safety_priority_actions") or []) and selector_action_id not in set(config.get("safety_priority_actions") or []):
        return {"agreement_with_runtime": False, "disagreement_type": "selector_possible_regression"}
    return {"agreement_with_runtime": False, "disagreement_type": "unknown"}


def validate_shadow_result(result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if result.get("side_effects_allowed") is not False:
        failures.append("side_effects_allowed_must_be_false")
    if result.get("buyer_facing_text_generated") is not False:
        failures.append("buyer_facing_text_generated_must_be_false")
    if result.get("live_runtime_wiring_allowed") is not False:
        failures.append("live_runtime_wiring_allowed_must_be_false")
    if result.get("should_not_change_runtime") is not True:
        failures.append("should_not_change_runtime_must_be_true")
    if result.get("disagreement_type") not in DISAGREEMENT_TYPES:
        failures.append(f"unknown_disagreement_type:{result.get('disagreement_type')}")
    selector_payload = {
        "action_id": result.get("selector_action_id"),
        "confidence": result.get("selector_confidence", 0.0),
        "reasons": result.get("selector_reasons") or [],
        "matched_features": result.get("selector_matched_features") or [],
        "side_effects_allowed": False,
        "live_runtime_wiring_allowed": False,
    }
    failures.extend(validate_selector_output(selector_payload))
    forbidden_text_keys = {"say", "response_text", "buyer_facing_response", "draft_response"}
    extra = sorted(forbidden_text_keys & set(result))
    if extra:
        failures.append(f"shadow_result_contains_buyer_facing_text:{extra}")
    return failures


def run_selector_shadow(shadow_input: dict[str, Any], expected_action_id: str = "", selector: Any | None = None) -> dict[str, Any]:
    parsed = ShadowModeInput.from_payload(shadow_input)
    resolved_selector = selector or RuleBasedActionSelector()
    selector_output = resolved_selector.select(parsed.to_selector_payload()).to_dict()
    safety_status = "safe"
    if selector_output.get("safety_block") is True:
        safety_status = "boundary_safe"
    if selector_output.get("action_id") not in action_labels():
        safety_status = "unsafe_uncontrolled_action"

    classification = classify_shadow_agreement(
        selector_action_id=str(selector_output.get("action_id") or ""),
        runtime_action_id=parsed.existing_runtime_action_id,
        expected_action_id=expected_action_id,
        safety_status=safety_status,
        fallback_required=selector_output.get("fallback_required") is True,
    )
    output = ShadowModeOutput(
        selector_action_id=str(selector_output.get("action_id") or ""),
        selector_confidence=float(selector_output.get("confidence") or 0.0),
        selector_reasons=[str(item) for item in selector_output.get("reasons") or []],
        selector_matched_features=[str(item) for item in selector_output.get("matched_features") or []],
        agreement_with_runtime=classification["agreement_with_runtime"],
        disagreement_type=classification["disagreement_type"],
        safety_status=safety_status,
        fallback_required=selector_output.get("fallback_required") is True,
    ).to_dict()
    failures = validate_shadow_result(output)
    if failures:
        output["safety_status"] = "unsafe_shadow_result"
        output["validation_failures"] = failures
    else:
        output["validation_failures"] = []
    return output
