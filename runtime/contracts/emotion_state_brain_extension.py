from __future__ import annotations

from copy import deepcopy
from typing import Any

from runtime.contracts.emotion_state_contracts import (
    EmotionStateContractError,
    REQUIRED_BLOCKED_POLICY_EFFECTS,
    validate_decision_reference,
    validate_perceived_customer_state,
)

EXTENSION_SCHEMA_VERSION = "emotion-state-brain-extension-v1"


class BrainExtensionBlocked(ValueError):
    pass


def build_offline_brain_extension(
    state: dict[str, Any],
    text_only_policy_decision_ref: str,
) -> dict[str, Any]:
    try:
        validate_perceived_customer_state(state)
    except EmotionStateContractError as exc:
        raise BrainExtensionBlocked("invalid PerceivedCustomerStateV1") from exc
    try:
        validate_decision_reference(text_only_policy_decision_ref, "text_only_policy_decision_ref")
    except EmotionStateContractError as exc:
        raise BrainExtensionBlocked("invalid text-only policy decision reference") from exc
    if set(state["blocked_policy_effects"]) != REQUIRED_BLOCKED_POLICY_EFFECTS:
        raise BrainExtensionBlocked("monotonic blocked effects are incomplete")
    return {
        "schema_version": EXTENSION_SCHEMA_VERSION,
        "buyer_state_patch": {
            "emotional_signal": state["selected_policy_signal"],
            "emotion_confidence": state["selected_signal_confidence_bucket"],
            "evidence_refs": list(state["evidence_refs"]),
        },
        "state_evidence_by_modality": deepcopy(state["signal_provenance_by_modality"]),
        "allowed_policy_effects": list(state["allowed_policy_effects"]),
        "blocked_policy_effects": list(state["blocked_policy_effects"]),
        "text_only_policy_decision_ref": text_only_policy_decision_ref,
        "runtime_connection_allowed": False,
        "runtime_approved": False,
    }


def apply_extension_to_brain_packet(packet: dict[str, Any], extension: dict[str, Any]) -> None:
    del packet, extension
    raise BrainExtensionBlocked("BRAIN-002 v1 mutation and runtime connection are blocked under EMOTION-STATE-001")


def _expect_brain_block(callback: Any) -> None:
    try:
        callback()
    except BrainExtensionBlocked:
        return
    raise AssertionError("expected BrainExtensionBlocked")


def brain_extension_self_check() -> str:
    state = {
        "call_session_id": "session-fixture-1",
        "campaign_profile_id": "emotion-state-phase-a-fixture",
        "campaign_profile_version": "fixture-v1",
        "turn_id": "turn-1",
        "turn_sequence": 1,
        "valence_estimate": "not_inferable",
        "activation_estimate": "not_inferable",
        "engagement_estimate": "not_inferable",
        "operational_signals": ["possible_confusion"],
        "confidence_by_signal": {"possible_confusion": 0.6},
        "selected_policy_signal": "possible_confusion",
        "selected_signal_confidence_bucket": "medium",
        "overall_evidence_quality": "text_only",
        "trajectory": "insufficient_history",
        "evidence_refs": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
        "signal_provenance_by_modality": {
            "possible_confusion": {
                "text": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
                "acoustic": [],
            },
        },
        "allowed_policy_effects": ["preserve", "clarify", "soften"],
        "blocked_policy_effects": sorted(REQUIRED_BLOCKED_POLICY_EFFECTS),
        "abstained": False,
        "abstention_reasons": [],
        "evidence_policy_version": "emotion-state-evidence-v1",
        "runtime_approved": False,
    }
    decision_ref = "decision:uuid:33333333-3333-4333-8333-333333333333"
    extension = build_offline_brain_extension(state, decision_ref)
    assert set({
        "state_evidence_by_modality", "allowed_policy_effects", "blocked_policy_effects",
        "text_only_policy_decision_ref",
    }).issubset(extension)
    assert extension["runtime_connection_allowed"] is False
    assert extension["runtime_approved"] is False
    extension["state_evidence_by_modality"]["possible_confusion"]["text"].append(
        "evidence:uuid:44444444-4444-4444-8444-444444444444"
    )
    assert len(state["signal_provenance_by_modality"]["possible_confusion"]["text"]) == 1
    incomplete = dict(state, blocked_policy_effects=["expand_action_set"])
    _expect_brain_block(lambda: build_offline_brain_extension(incomplete, decision_ref))
    _expect_brain_block(lambda: build_offline_brain_extension(state, " "))
    _expect_brain_block(lambda: build_offline_brain_extension(state, "raw decision sentence"))
    _expect_brain_block(lambda: build_offline_brain_extension(state, "x" * 161))
    _expect_brain_block(lambda: build_offline_brain_extension(state, None))
    _expect_brain_block(lambda: apply_extension_to_brain_packet({}, extension))
    return "pass"
