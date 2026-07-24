from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Final


class PhaseCContractError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


FROZEN_POLICY_CANONICAL_JSON: Final[str] = r'''{
  "abstained_allowed_effects": ["preserve"],
  "abstention_primary_priority": ["contradictory_evidence", "low_audio_quality", "missing_input", "insufficient_evidence"],
  "abstention_reason_order": ["phase_a_no_audio", "insufficient_evidence", "contradictory_evidence", "low_audio_quality", "missing_input", "stale_input"],
  "acoustic_only_cap": 400,
  "acoustic_only_allowed_effects": ["preserve"],
  "agreement_bonus": 100,
  "agreement_eligibility": "newly_contributing_positive_support_atoms_only",
  "agreement_requirements": {"distinct_evidence_refs": 2, "distinct_independence_keys": 2, "distinct_modalities": 2},
  "allowed_effect_order": ["preserve", "soften", "shorten", "clarify", "acknowledge", "handoff", "abstain", "stop"],
  "allowed_effects_by_signal": {
    "confusion": ["preserve", "shorten", "clarify", "acknowledge", "handoff"],
    "disengagement": ["preserve", "soften", "shorten", "acknowledge", "handoff"],
    "frustration": ["preserve", "soften", "shorten", "acknowledge", "handoff"],
    "hesitation": ["preserve", "clarify", "acknowledge"],
    "interest": ["preserve"]
  },
  "allowed_modalities_by_evidence_class": {
    "dialogue_context": ["dialogue"],
    "synthetic_acoustic_symbol": ["acoustic"],
    "transcript_meaning": ["text"],
    "unsolicited_explicit_statement": ["text"],
    "weak_behavioral_proxy": ["dialogue"]
  },
  "base_support_units": {"dialogue_context": 300, "synthetic_acoustic_symbol": 180, "transcript_meaning": 450, "unsolicited_explicit_statement": 700, "weak_behavioral_proxy": 100},
  "blocked_effect_order": ["expand_action_set", "increase_persuasion_intensity", "create_new_close", "override_refusal", "override_do_not_call", "rewrite_protected_text", "exploit_vulnerability", "voice_only_emotional_appeal", "unsupported_claim", "automatic_close_or_payment"],
  "canonical_direction_order": ["supports", "opposes"],
  "canonical_evidence_class_order": ["unsolicited_explicit_statement", "transcript_meaning", "dialogue_context", "synthetic_acoustic_symbol", "weak_behavioral_proxy"],
  "canonical_modality_order": ["text", "dialogue", "acoustic"],
  "canonical_quality_order": ["high", "medium", "low", "unusable"],
  "canonical_signal_order": ["confusion", "disengagement", "frustration", "hesitation", "interest"],
  "confirmation_counts": {"entry": 2, "explicit_statement_entry": 1, "release": 2, "switch": 2},
  "confirmation_key_policy": "one_canonical_new_supporting_key_per_signal_per_turn",
  "confidence_bucket_thresholds": {"high": 750, "medium": 550},
  "contradiction_cap": 350,
  "contradiction_thresholds": {"gross_opposition": 300, "gross_support": 300},
  "correction_policy": "most_recent_turn_exact_next_revision_only",
  "evidence_policy_version": "emotion-state-evidence-v2",
  "emitted_abstention_reasons": ["insufficient_evidence", "contradictory_evidence", "low_audio_quality", "missing_input"],
  "entry_threshold": 550,
  "explicit_entry_evidence_class": "unsolicited_explicit_statement",
  "fixture_only": true,
  "minimum_switch_advantage": 150,
  "policy_id": "emotion-state-phase-c0-synthetic-v1",
  "quality_multipliers": {"high": 1000, "low": 400, "medium": 750, "unusable": 0},
  "quality_cap_basis": "highest_nonzero_current_contributing_quality",
  "release_threshold": 350,
  "retained_support_milli": 800,
  "rounding_policy": "integer_floor_toward_zero",
  "scale": 1000,
  "schema_version": "PhaseCFrozenEvidencePolicyV1",
  "support_saturation": 1000,
  "switch_threshold": 650,
  "tie_policy": {"incumbent": "retain_unless_all_switch_conditions_pass", "no_incumbent": "abstain"},
  "total_quality_caps": {"high": 1000, "low": 400, "medium": 750, "unusable": 0},
  "trajectory_delta_threshold": 100,
  "visibility_threshold": 200
}'''


def canonical_json_bytes(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PhaseCContractError("payload is not canonical JSON") from exc
    return (text + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise PhaseCContractError(f"non-finite JSON constant is forbidden: {value}")


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise PhaseCContractError(f"non-finite JSON number is forbidden: {value}")
    return parsed


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PhaseCContractError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PhaseCContractError(f"invalid JSON: {path.name}") from exc
    if type(value) is not dict:
        raise PhaseCContractError("top-level JSON value must be an object")
    return value


def _validate_exact(actual: Any, expected: Any, path: str) -> None:
    if type(expected) is dict:
        if type(actual) is not dict or set(actual) != set(expected):
            raise PhaseCContractError(f"policy object mismatch: {path}")
        for key in expected:
            _validate_exact(actual[key], expected[key], f"{path}.{key}")
        return
    if type(expected) is list:
        if type(actual) is not list or len(actual) != len(expected):
            raise PhaseCContractError(f"policy array mismatch: {path}")
        for index, expected_value in enumerate(expected):
            _validate_exact(actual[index], expected_value, f"{path}[{index}]")
        return
    if type(actual) is not type(expected) or actual != expected:
        raise PhaseCContractError(f"policy scalar mismatch: {path}")


def validate_phase_c_policy(payload: dict[str, Any]) -> dict[str, Any]:
    expected = json.loads(
        FROZEN_POLICY_CANONICAL_JSON,
        parse_constant=_reject_constant,
        object_pairs_hook=_unique_object,
    )
    _validate_exact(payload, expected, "policy")
    return payload
