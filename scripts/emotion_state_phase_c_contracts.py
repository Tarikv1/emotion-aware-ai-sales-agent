from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping


class PhaseCContractError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class PhaseCEventRejected(PhaseCContractError):
    pass


@dataclass(frozen=True)
class PhaseCSyntheticEvidenceAtomV1:
    schema_version: str
    evidence_ref: str
    independence_key: str
    operational_signal: str
    direction: str
    modality: str
    evidence_class: str
    quality_bucket: str


@dataclass(frozen=True)
class PhaseCSyntheticEvidenceFrameV1:
    schema_version: str
    fixture_only: bool
    call_session_id: str
    campaign_profile_id: str
    campaign_profile_version: str
    turn_id: str
    turn_sequence: int
    event_id: str
    input_revision: int
    evidence_atoms: tuple[PhaseCSyntheticEvidenceAtomV1, ...]


@dataclass(frozen=True)
class PhaseCEventWatermarkV1:
    expected_session_id: str
    expected_campaign_profile_id: str
    expected_campaign_profile_version: str
    last_turn_sequence: int
    turn_sequence_by_id: tuple[tuple[str, int], ...]
    turn_id_by_sequence: tuple[tuple[int, str], ...]
    last_input_revision_by_turn: tuple[tuple[str, int], ...]
    seen_event_ids: frozenset[str]
    event_history_by_id: tuple[tuple[str, str, int], ...]


ATOM_FIELDS = frozenset({
    "schema_version", "evidence_ref", "independence_key",
    "operational_signal", "direction", "modality", "evidence_class",
    "quality_bucket",
})
FRAME_FIELDS = frozenset({
    "schema_version", "fixture_only", "call_session_id",
    "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "evidence_atoms",
})
ATOM_FIELD_ORDER = (
    "schema_version", "evidence_ref", "independence_key",
    "operational_signal", "direction", "modality", "evidence_class",
    "quality_bucket",
)
FRAME_FIELD_ORDER = (
    "schema_version", "fixture_only", "call_session_id",
    "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "evidence_atoms",
)
OPAQUE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REF_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
FORBIDDEN_PHASE_C_KEY_FRAGMENTS = (
    "acoustic_features", "probabilities", "model_id", "dataset_id",
    "audio_bytes", "raw_audio", "transcript_text", "raw_transcript",
    "customer_name", "customer_phone", "customer_email",
    "speaker_embedding", "voiceprint", "provider_payload", "api_key",
    "access_token", "auth_token", "password", "secret", "private_key",
    "hidden_reasoning",
)
CLASS_MODALITY = MappingProxyType({
    "unsolicited_explicit_statement": "text",
    "transcript_meaning": "text",
    "dialogue_context": "dialogue",
    "synthetic_acoustic_symbol": "acoustic",
    "weak_behavioral_proxy": "dialogue",
})


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


def _scan_forbidden_phase_c_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if type(key) is str and any(
                fragment in key.lower()
                for fragment in FORBIDDEN_PHASE_C_KEY_FRAGMENTS
            ):
                raise PhaseCContractError("forbidden_field")
            _scan_forbidden_phase_c_keys(child)
    elif type(value) is list:
        for child in value:
            _scan_forbidden_phase_c_keys(child)


def _require_fields(payload: dict[str, Any], fields: frozenset[str], prefix: str) -> None:
    if not fields.issubset(payload):
        raise PhaseCContractError(f"{prefix}_missing_fields")
    if set(payload) != fields:
        raise PhaseCContractError(f"{prefix}_unknown_fields")


def _require_opaque_identifier(value: Any) -> None:
    if type(value) is not str or OPAQUE_ID_PATTERN.fullmatch(value) is None:
        raise PhaseCContractError("invalid_opaque_identifier")


def _validate_atom_payload(
    payload: dict[str, Any],
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceAtomV1:
    _scan_forbidden_phase_c_keys(payload)
    _require_fields(payload, ATOM_FIELDS, "atom")
    if payload["schema_version"] != "PhaseCSyntheticEvidenceAtomV1":
        raise PhaseCContractError("atom_schema")
    if any(type(payload[field]) is not str for field in ATOM_FIELD_ORDER):
        raise PhaseCContractError("atom_field_type")
    if EVIDENCE_REF_PATTERN.fullmatch(payload["evidence_ref"]) is None:
        raise PhaseCContractError("invalid_evidence_reference")
    _require_opaque_identifier(payload["independence_key"])
    enum_orders = (
        ("operational_signal", "canonical_signal_order"),
        ("direction", "canonical_direction_order"),
        ("modality", "canonical_modality_order"),
        ("evidence_class", "canonical_evidence_class_order"),
        ("quality_bucket", "canonical_quality_order"),
    )
    if any(payload[field] not in policy[order] for field, order in enum_orders):
        raise PhaseCContractError("unknown_atom_enum")
    if CLASS_MODALITY[payload["evidence_class"]] != payload["modality"]:
        raise PhaseCContractError("class_modality_mismatch")
    return PhaseCSyntheticEvidenceAtomV1(
        **{field: payload[field] for field in ATOM_FIELD_ORDER},
    )


def parse_phase_c_atom(
    payload: Any,
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceAtomV1:
    validate_phase_c_policy(policy)
    _scan_forbidden_phase_c_keys(payload)
    if type(payload) is not dict:
        raise PhaseCContractError("atom_not_object")
    atom = _validate_atom_payload(dict(payload), policy)
    validate_phase_c_atom(atom, policy)
    return atom


def _atom_to_payload(atom: PhaseCSyntheticEvidenceAtomV1) -> dict[str, Any]:
    if type(atom) is not PhaseCSyntheticEvidenceAtomV1:
        raise PhaseCContractError("atom_field_type")
    return {field: getattr(atom, field) for field in ATOM_FIELD_ORDER}


def validate_phase_c_atom(
    atom: PhaseCSyntheticEvidenceAtomV1,
    policy: dict[str, Any],
) -> None:
    validate_phase_c_policy(policy)
    _validate_atom_payload(_atom_to_payload(atom), policy)


def atom_sort_key(
    atom: PhaseCSyntheticEvidenceAtomV1,
    policy: dict[str, Any],
) -> tuple[int, int, int, int, int, str, str]:
    validate_phase_c_atom(atom, policy)
    signal_order = policy["canonical_signal_order"]
    direction_order = policy["canonical_direction_order"]
    modality_order = policy["canonical_modality_order"]
    evidence_class_order = policy["canonical_evidence_class_order"]
    quality_order = policy["canonical_quality_order"]
    return (
        signal_order.index(atom.operational_signal),
        direction_order.index(atom.direction),
        modality_order.index(atom.modality),
        evidence_class_order.index(atom.evidence_class),
        quality_order.index(atom.quality_bucket),
        atom.independence_key,
        atom.evidence_ref,
    )


def _validate_frame_payload(
    payload: dict[str, Any],
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceFrameV1:
    _scan_forbidden_phase_c_keys(payload)
    _require_fields(payload, FRAME_FIELDS, "frame")
    if payload["schema_version"] != "PhaseCSyntheticEvidenceFrameV1":
        raise PhaseCContractError("frame_schema")
    if payload["fixture_only"] is not True:
        raise PhaseCContractError("fixture_only_required")
    string_fields = (
        "call_session_id", "campaign_profile_id", "campaign_profile_version",
        "turn_id", "event_id",
    )
    if (
        type(payload["fixture_only"]) is not bool
        or any(type(payload[field]) is not str for field in string_fields)
        or type(payload["turn_sequence"]) is not int
        or type(payload["input_revision"]) is not int
        or type(payload["evidence_atoms"]) is not list
    ):
        raise PhaseCContractError("frame_field_type")
    for field in string_fields:
        _require_opaque_identifier(payload[field])
    atoms_list: list[PhaseCSyntheticEvidenceAtomV1] = []
    for item in payload["evidence_atoms"]:
        if type(item) is not dict:
            raise PhaseCContractError("atom_not_object")
        atoms_list.append(_validate_atom_payload(dict(item), policy))
    atoms = tuple(atoms_list)
    if len({atom.evidence_ref for atom in atoms}) != len(atoms):
        raise PhaseCContractError("duplicate_evidence_reference")
    if len({atom.independence_key for atom in atoms}) != len(atoms):
        raise PhaseCContractError("duplicate_independence_key")
    if atoms != tuple(sorted(atoms, key=lambda atom: atom_sort_key(atom, policy))):
        raise PhaseCContractError("noncanonical_atom_order")
    if payload["turn_sequence"] < 0 or payload["input_revision"] < 0:
        raise PhaseCContractError("invalid_event_counter")
    return PhaseCSyntheticEvidenceFrameV1(
        schema_version=payload["schema_version"],
        fixture_only=payload["fixture_only"],
        call_session_id=payload["call_session_id"],
        campaign_profile_id=payload["campaign_profile_id"],
        campaign_profile_version=payload["campaign_profile_version"],
        turn_id=payload["turn_id"],
        turn_sequence=payload["turn_sequence"],
        event_id=payload["event_id"],
        input_revision=payload["input_revision"],
        evidence_atoms=atoms,
    )


def parse_phase_c_frame(
    payload: Any,
    policy: dict[str, Any],
) -> PhaseCSyntheticEvidenceFrameV1:
    validate_phase_c_policy(policy)
    _scan_forbidden_phase_c_keys(payload)
    if type(payload) is not dict:
        raise PhaseCContractError("frame_not_object")
    frame = _validate_frame_payload(dict(payload), policy)
    validate_phase_c_frame(frame, policy)
    return frame


def _frame_to_payload(frame: PhaseCSyntheticEvidenceFrameV1) -> dict[str, Any]:
    if type(frame) is not PhaseCSyntheticEvidenceFrameV1:
        raise PhaseCContractError("frame_field_type")
    if type(frame.evidence_atoms) is not tuple:
        raise PhaseCContractError("frame_field_type")
    return {
        "schema_version": frame.schema_version,
        "fixture_only": frame.fixture_only,
        "call_session_id": frame.call_session_id,
        "campaign_profile_id": frame.campaign_profile_id,
        "campaign_profile_version": frame.campaign_profile_version,
        "turn_id": frame.turn_id,
        "turn_sequence": frame.turn_sequence,
        "event_id": frame.event_id,
        "input_revision": frame.input_revision,
        "evidence_atoms": [_atom_to_payload(atom) for atom in frame.evidence_atoms],
    }


def validate_phase_c_frame(
    frame: PhaseCSyntheticEvidenceFrameV1,
    policy: dict[str, Any],
) -> None:
    validate_phase_c_policy(policy)
    _validate_frame_payload(_frame_to_payload(frame), policy)


def _frozen_phase_c_policy() -> dict[str, Any]:
    return validate_phase_c_policy(json.loads(FROZEN_POLICY_CANONICAL_JSON))


def phase_c_frame_to_payload(
    frame: PhaseCSyntheticEvidenceFrameV1,
) -> dict[str, Any]:
    policy = _frozen_phase_c_policy()
    validate_phase_c_frame(frame, policy)
    payload = _frame_to_payload(frame)
    if parse_phase_c_frame(payload, policy) != frame:
        raise PhaseCContractError("frame_round_trip_failed")
    return payload


def _validate_phase_c_event_identity_frame(frame: PhaseCSyntheticEvidenceFrameV1) -> None:
    if type(frame) is not PhaseCSyntheticEvidenceFrameV1:
        raise PhaseCContractError("frame_field_type")
    if frame.schema_version != "PhaseCSyntheticEvidenceFrameV1" or frame.fixture_only is not True:
        raise PhaseCContractError("frame_schema")
    if (
        any(type(getattr(frame, field)) is not str for field in (
            "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id", "event_id",
        ))
        or type(frame.turn_sequence) is not int
        or type(frame.input_revision) is not int
        or frame.turn_sequence < 0
        or frame.input_revision < 0
        or type(frame.evidence_atoms) is not tuple
    ):
        raise PhaseCContractError("frame_field_type")
    for field in (
        "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id", "event_id",
    ):
        _require_opaque_identifier(getattr(frame, field))


def _validated_phase_c_event_watermark_maps(
    watermark: PhaseCEventWatermarkV1,
) -> tuple[dict[str, int], dict[int, str], dict[str, int], dict[str, tuple[str, int]]]:
    if type(watermark) is not PhaseCEventWatermarkV1:
        raise PhaseCContractError("event_watermark_type")
    for value in (
        watermark.expected_session_id,
        watermark.expected_campaign_profile_id,
        watermark.expected_campaign_profile_version,
    ):
        _require_opaque_identifier(value)
    if type(watermark.last_turn_sequence) is not int or watermark.last_turn_sequence < -1:
        raise PhaseCContractError("event_watermark_counter")
    tuple_maps = (
        watermark.turn_sequence_by_id,
        watermark.turn_id_by_sequence,
        watermark.last_input_revision_by_turn,
    )
    if (
        any(type(value) is not tuple for value in tuple_maps)
        or type(watermark.seen_event_ids) is not frozenset
        or type(watermark.event_history_by_id) is not tuple
    ):
        raise PhaseCContractError("event_watermark_collections")
    if any(type(pair) is not tuple or len(pair) != 2 for pairs in tuple_maps for pair in pairs):
        raise PhaseCContractError("event_watermark_entries")
    if any(type(entry) is not tuple or len(entry) != 3 for entry in watermark.event_history_by_id):
        raise PhaseCContractError("event_watermark_history")
    for turn_id, sequence in watermark.turn_sequence_by_id:
        _require_opaque_identifier(turn_id)
        if type(sequence) is not int or sequence < 0:
            raise PhaseCContractError("event_watermark_sequence")
    for sequence, turn_id in watermark.turn_id_by_sequence:
        if type(sequence) is not int or sequence < 0:
            raise PhaseCContractError("event_watermark_sequence")
        _require_opaque_identifier(turn_id)
    for turn_id, revision in watermark.last_input_revision_by_turn:
        _require_opaque_identifier(turn_id)
        if type(revision) is not int or revision < 0:
            raise PhaseCContractError("event_watermark_revision")
    sequence_by_id = dict(watermark.turn_sequence_by_id)
    id_by_sequence = dict(watermark.turn_id_by_sequence)
    revision_by_turn = dict(watermark.last_input_revision_by_turn)
    if any(len(mapping) != len(source) for mapping, source in (
        (sequence_by_id, watermark.turn_sequence_by_id),
        (id_by_sequence, watermark.turn_id_by_sequence),
        (revision_by_turn, watermark.last_input_revision_by_turn),
    )):
        raise PhaseCContractError("event_watermark_duplicate_map_key")
    for event_id in watermark.seen_event_ids:
        _require_opaque_identifier(event_id)
    history_by_id: dict[str, tuple[str, int]] = {}
    seen_turn_revisions: set[tuple[str, int]] = set()
    revisions_by_turn: dict[str, list[int]] = {}
    for event_id, turn_id, revision in watermark.event_history_by_id:
        _require_opaque_identifier(event_id)
        _require_opaque_identifier(turn_id)
        if type(revision) is not int or revision < 0:
            raise PhaseCContractError("event_watermark_revision")
        if event_id in history_by_id or (turn_id, revision) in seen_turn_revisions:
            raise PhaseCContractError("event_watermark_duplicate_history")
        history_by_id[event_id] = (turn_id, revision)
        seen_turn_revisions.add((turn_id, revision))
        revisions_by_turn.setdefault(turn_id, []).append(revision)
    if (
        len(sequence_by_id) != len(id_by_sequence)
        or len(set(sequence_by_id.values())) != len(sequence_by_id)
        or len(set(id_by_sequence.values())) != len(id_by_sequence)
        or {sequence: turn_id for turn_id, sequence in sequence_by_id.items()} != id_by_sequence
    ):
        raise PhaseCContractError("event_watermark_turn_map_inverse")
    if set(revision_by_turn) != set(sequence_by_id) or set(revisions_by_turn) != set(sequence_by_id):
        raise PhaseCContractError("event_watermark_coverage")
    if frozenset(history_by_id) != watermark.seen_event_ids:
        raise PhaseCContractError("event_watermark_event_history")
    for turn_id, last_revision in revision_by_turn.items():
        revisions = sorted(revisions_by_turn[turn_id])
        if revisions != list(range(last_revision + 1)):
            raise PhaseCContractError("event_watermark_revision_history")
    if watermark.last_turn_sequence != max(id_by_sequence, default=-1):
        raise PhaseCContractError("event_watermark_last_turn")
    return sequence_by_id, id_by_sequence, revision_by_turn, history_by_id


def validate_phase_c_event_watermark(
    watermark: PhaseCEventWatermarkV1,
) -> tuple[dict[str, int], dict[int, str], dict[str, int], dict[str, tuple[str, int]]]:
    return _validated_phase_c_event_watermark_maps(watermark)


def initial_phase_c_watermark(frame: PhaseCSyntheticEvidenceFrameV1) -> PhaseCEventWatermarkV1:
    validate_phase_c_frame(frame, _frozen_phase_c_policy())
    return PhaseCEventWatermarkV1(
        expected_session_id=frame.call_session_id,
        expected_campaign_profile_id=frame.campaign_profile_id,
        expected_campaign_profile_version=frame.campaign_profile_version,
        last_turn_sequence=-1,
        turn_sequence_by_id=(),
        turn_id_by_sequence=(),
        last_input_revision_by_turn=(),
        seen_event_ids=frozenset(),
        event_history_by_id=(),
    )


def validate_phase_c_event_identity(
    frame: PhaseCSyntheticEvidenceFrameV1,
    watermark: PhaseCEventWatermarkV1,
) -> PhaseCEventWatermarkV1:
    sequence_by_id, id_by_sequence, revision_by_turn, history_by_id = (
        validate_phase_c_event_watermark(watermark)
    )
    validate_phase_c_frame(frame, _frozen_phase_c_policy())

    def reject(code: str) -> None:
        raise PhaseCEventRejected(code)

    if frame.call_session_id != watermark.expected_session_id:
        reject("cross_session")
    if frame.campaign_profile_id != watermark.expected_campaign_profile_id:
        reject("cross_campaign")
    if frame.campaign_profile_version != watermark.expected_campaign_profile_version:
        reject("wrong_campaign_version")
    if frame.event_id in watermark.seen_event_ids:
        reject("duplicate_event")
    if frame.turn_id in sequence_by_id and sequence_by_id[frame.turn_id] != frame.turn_sequence:
        reject("turn_id_rebound")
    if frame.turn_sequence in id_by_sequence and id_by_sequence[frame.turn_sequence] != frame.turn_id:
        reject("turn_sequence_rebound")
    if frame.turn_sequence < watermark.last_turn_sequence:
        reject("stale_turn")
    if frame.turn_id in sequence_by_id:
        if frame.input_revision != revision_by_turn[frame.turn_id] + 1:
            reject("invalid_revision")
    else:
        if frame.turn_sequence <= watermark.last_turn_sequence:
            reject("stale_turn")
        if frame.input_revision != 0:
            reject("invalid_revision")
        sequence_by_id[frame.turn_id] = frame.turn_sequence
        id_by_sequence[frame.turn_sequence] = frame.turn_id
    revision_by_turn[frame.turn_id] = frame.input_revision
    history_by_id[frame.event_id] = (frame.turn_id, frame.input_revision)
    return PhaseCEventWatermarkV1(
        expected_session_id=watermark.expected_session_id,
        expected_campaign_profile_id=watermark.expected_campaign_profile_id,
        expected_campaign_profile_version=watermark.expected_campaign_profile_version,
        last_turn_sequence=max(watermark.last_turn_sequence, frame.turn_sequence),
        turn_sequence_by_id=tuple(sorted(sequence_by_id.items())),
        turn_id_by_sequence=tuple(sorted(id_by_sequence.items())),
        last_input_revision_by_turn=tuple(sorted(revision_by_turn.items())),
        seen_event_ids=frozenset(history_by_id),
        event_history_by_id=tuple(sorted(
            (event_id, turn_id, revision)
            for event_id, (turn_id, revision) in history_by_id.items()
        )),
    )
