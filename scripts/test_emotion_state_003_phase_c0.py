from __future__ import annotations

import copy
import dataclasses
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    PhaseCEventRejected,
    PhaseCEventWatermarkV1,
    PhaseCSyntheticEvidenceAtomV1,
    PhaseCSyntheticEvidenceFrameV1,
    atom_sort_key,
    canonical_json_bytes,
    initial_phase_c_watermark,
    load_json_strict,
    parse_phase_c_atom,
    parse_phase_c_frame,
    phase_c_frame_to_payload,
    sha256_bytes,
    validate_phase_c_atom,
    validate_phase_c_event_identity,
    validate_phase_c_event_watermark,
    validate_phase_c_frame,
    validate_phase_c_policy,
)
from runtime.contracts.emotion_state_contracts import (
    EventWatermarkV1 as RuntimeEventWatermarkV1,
    EmotionStateContractError,
    validate_event_identity,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-003-phase-c0-policy.json"
)


def _atom(
    *,
    counter: int,
    signal: str = "confusion",
    direction: str = "supports",
    modality: str = "text",
    evidence_class: str = "transcript_meaning",
    quality: str = "high",
    independence_key: str | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "PhaseCSyntheticEvidenceAtomV1",
        "evidence_ref": (
            "evidence:uuid:00000000-0000-4000-8000-"
            f"{counter:012d}"
        ),
        "independence_key": independence_key or f"ind:fixture:1:{counter}",
        "operational_signal": signal,
        "direction": direction,
        "modality": modality,
        "evidence_class": evidence_class,
        "quality_bucket": quality,
    }


def _frame(
    *,
    event_id: str = "event-1",
    turn_id: str = "turn-1",
    turn_sequence: int = 0,
    input_revision: int = 0,
    atoms: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "PhaseCSyntheticEvidenceFrameV1",
        "fixture_only": True,
        "call_session_id": "session-a",
        "campaign_profile_id": "campaign-a",
        "campaign_profile_version": "campaign-v1",
        "turn_id": turn_id,
        "turn_sequence": turn_sequence,
        "event_id": event_id,
        "input_revision": input_revision,
        "evidence_atoms": atoms or [],
    }


def _deep_forbidden_value(fragment: str, depth: int) -> dict[str, object]:
    value: object = {f"safe_{fragment}": "blocked"}
    for index in range(depth):
        value = {f"nest_{index}": [value]}
    return value


class PhaseCInputContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))

    def test_valid_frame_parses_to_immutable_types(self) -> None:
        frame = parse_phase_c_frame(_frame(atoms=[_atom(counter=1)]), self.policy)
        self.assertEqual(frame.turn_sequence, 0)
        self.assertIsInstance(frame.evidence_atoms, tuple)
        self.assertEqual(frame.evidence_atoms[0].operational_signal, "confusion")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            frame.turn_id = "changed"  # type: ignore[misc]

    def test_atom_missing_extra_type_and_enum_mutations_fail_closed(self) -> None:
        payload = _atom(counter=1)
        for key in tuple(payload):
            mutated = dict(payload)
            mutated.pop(key)
            with self.subTest(missing=key):
                with self.assertRaisesRegex(PhaseCContractError, "atom_missing_fields"):
                    parse_phase_c_atom(mutated, self.policy)
        for key, value in (("extra", True), ("operational_signal", 1), ("quality_bucket", "unknown")):
            mutated = dict(payload)
            mutated[key] = value
            with self.subTest(mutation=key):
                expected = "atom_unknown_fields" if key == "extra" else ("atom_field_type" if key == "operational_signal" else "unknown_atom_enum")
                with self.assertRaisesRegex(PhaseCContractError, expected):
                    parse_phase_c_atom(mutated, self.policy)

    def test_frame_missing_extra_and_exact_type_mutations_fail_closed(self) -> None:
        payload = _frame(atoms=[_atom(counter=1)])
        for key in tuple(payload):
            mutated = dict(payload)
            mutated.pop(key)
            with self.subTest(missing=key):
                with self.assertRaisesRegex(PhaseCContractError, "frame_missing_fields"):
                    parse_phase_c_frame(mutated, self.policy)
        cases = {
            "extra": (True, "frame_unknown_fields"),
            "fixture_only": (1, "fixture_only_required"),
            "turn_sequence": (True, "frame_field_type"),
            "input_revision": (True, "frame_field_type"),
            "evidence_atoms": ((), "frame_field_type"),
        }
        for key, (value, code) in cases.items():
            mutated = dict(payload)
            mutated[key] = value
            with self.subTest(mutation=key):
                with self.assertRaisesRegex(PhaseCContractError, code):
                    parse_phase_c_frame(mutated, self.policy)

    def test_raw_phase_b_surfaces_and_unknown_fields_reject(self) -> None:
        for key in ("acoustic_features", "probabilities", "model_id", "dataset_id"):
            payload = _frame(atoms=[_atom(counter=1)])
            payload[key] = {}
            with self.subTest(key=key):
                with self.assertRaisesRegex(PhaseCContractError, "forbidden_field"):
                    parse_phase_c_frame(payload, self.policy)

    def test_forbidden_key_fragments_reject_at_every_nesting_depth_and_precede_shape_errors(self) -> None:
        for fragment in ("raw_audio", "customer_email", "private_key", "hidden_reasoning"):
            for depth in range(4):
                payload = _frame(atoms=[_atom(counter=1)])
                payload["opaque"] = _deep_forbidden_value(fragment, depth)
                with self.subTest(fragment=fragment, depth=depth):
                    with self.assertRaisesRegex(PhaseCContractError, "forbidden_field"):
                        parse_phase_c_frame(payload, self.policy)

    def test_reference_identifier_pairing_and_counter_validation_reject(self) -> None:
        atom = _atom(counter=1)
        atom["evidence_ref"] = "evidence:uuid:not-a-uuid"
        with self.assertRaisesRegex(PhaseCContractError, "invalid_evidence_reference"):
            parse_phase_c_atom(atom, self.policy)
        atom = _atom(counter=1, modality="dialogue")
        with self.assertRaisesRegex(PhaseCContractError, "class_modality_mismatch"):
            parse_phase_c_atom(atom, self.policy)
        for field in ("turn_id", "event_id", "call_session_id"):
            payload = _frame(atoms=[_atom(counter=1)])
            payload[field] = " bad"
            with self.subTest(field=field):
                with self.assertRaisesRegex(PhaseCContractError, "invalid_opaque_identifier"):
                    parse_phase_c_frame(payload, self.policy)
        for field in ("turn_sequence", "input_revision"):
            payload = _frame(atoms=[_atom(counter=1)])
            payload[field] = -1
            with self.subTest(field=field):
                with self.assertRaisesRegex(PhaseCContractError, "invalid_event_counter"):
                    parse_phase_c_frame(payload, self.policy)

    def test_fixture_duplicate_and_noncanonical_atom_order_reject(self) -> None:
        payload = _frame(atoms=[_atom(counter=1)])
        payload["fixture_only"] = False
        with self.assertRaisesRegex(PhaseCContractError, "fixture_only_required"):
            parse_phase_c_frame(payload, self.policy)
        duplicate_ref = _frame(atoms=[_atom(counter=1), _atom(counter=1, independence_key="ind:fixture:1:2")])
        with self.assertRaisesRegex(PhaseCContractError, "duplicate_evidence_reference"):
            parse_phase_c_frame(duplicate_ref, self.policy)
        duplicate_key = _frame(atoms=[_atom(counter=1), _atom(counter=2, independence_key="ind:fixture:1:1")])
        with self.assertRaisesRegex(PhaseCContractError, "duplicate_independence_key"):
            parse_phase_c_frame(duplicate_key, self.policy)
        atoms = [_atom(counter=1, signal="confusion"), _atom(counter=2, signal="interest")]
        with self.assertRaisesRegex(PhaseCContractError, "noncanonical_atom_order"):
            parse_phase_c_frame(_frame(atoms=list(reversed(atoms))), self.policy)

    def test_dataclass_validation_bypass_resistance_and_fresh_round_trip(self) -> None:
        frame = parse_phase_c_frame(_frame(atoms=[_atom(counter=1)]), self.policy)
        payload_one = phase_c_frame_to_payload(frame)
        payload_two = phase_c_frame_to_payload(frame)
        self.assertEqual(payload_one, payload_two)
        self.assertIsNot(payload_one, payload_two)
        self.assertIsNot(payload_one["evidence_atoms"], payload_two["evidence_atoms"])
        self.assertEqual(parse_phase_c_frame(payload_one, self.policy), frame)
        malformed_atom = PhaseCSyntheticEvidenceAtomV1(**{**dataclasses.asdict(frame.evidence_atoms[0]), "quality_bucket": "invalid"})
        with self.assertRaisesRegex(PhaseCContractError, "unknown_atom_enum"):
            validate_phase_c_atom(malformed_atom, self.policy)
        malformed_frame = PhaseCSyntheticEvidenceFrameV1(
            **{**frame.__dict__, "fixture_only": False},
        )
        with self.assertRaisesRegex(PhaseCContractError, "fixture_only_required"):
            validate_phase_c_frame(malformed_frame, self.policy)


def _runtime_identity_projection(frame: PhaseCSyntheticEvidenceFrameV1) -> dict[str, object]:
    return {
        "call_session_id": frame.call_session_id,
        "campaign_profile_id": frame.campaign_profile_id,
        "campaign_profile_version": frame.campaign_profile_version,
        "turn_id": frame.turn_id,
        "turn_sequence": frame.turn_sequence,
        "event_id": frame.event_id,
        "input_revision": frame.input_revision,
        "event_timestamp": "2026-07-24T00:00:00Z",
        "call_scoped_speaker_id": f"{frame.call_session_id}:speaker",
        "start_time_ms": frame.turn_sequence * 1000,
        "end_time_ms": (frame.turn_sequence + 1) * 1000,
        "audio_quality_status": "unavailable",
        "audio_quality_reasons": ["phase_a_no_audio"],
        "acoustic_features": {},
        "acoustic_feature_confidence": {},
        "transcript_signals": [],
        "explicit_customer_statements": [],
        "dialogue_context_refs": [],
        "speaker_baseline_status": "not_started",
        "extraction_status": "offline_fixture_only",
        "source_timestamps": {},
        "persistence_allowed": False,
    }


class PhaseCEventIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        self.first = parse_phase_c_frame(_frame(atoms=[_atom(counter=1)]), self.policy)

    def _runtime_initial(self) -> RuntimeEventWatermarkV1:
        return RuntimeEventWatermarkV1(
            expected_session_id=self.first.call_session_id,
            expected_campaign_profile_id=self.first.campaign_profile_id,
            expected_campaign_profile_version=self.first.campaign_profile_version,
            last_turn_sequence=-1,
            turn_sequence_by_id=(),
            turn_id_by_sequence=(),
            last_input_revision_by_turn=(),
            seen_event_ids=frozenset(),
            event_history_by_id=(),
        )

    def test_runtime_parity_for_new_turn_and_correction_sequence(self) -> None:
        frames = (
            self.first,
            parse_phase_c_frame(_frame(event_id="event-2", input_revision=1, atoms=[_atom(counter=2)]), self.policy),
            parse_phase_c_frame(_frame(event_id="event-3", turn_id="turn-2", turn_sequence=1, atoms=[_atom(counter=3)]), self.policy),
        )
        phase_watermark = initial_phase_c_watermark(self.first)
        runtime_watermark = self._runtime_initial()
        for frame in frames:
            prior_phase = phase_watermark
            phase_watermark = validate_phase_c_event_identity(frame, phase_watermark)
            runtime_watermark = validate_event_identity(
                _runtime_identity_projection(frame), watermark=runtime_watermark,
            )
            self.assertIsNot(phase_watermark, prior_phase)
            self.assertEqual(phase_watermark.turn_sequence_by_id, runtime_watermark.turn_sequence_by_id)
            self.assertEqual(phase_watermark.turn_id_by_sequence, runtime_watermark.turn_id_by_sequence)
            self.assertEqual(phase_watermark.last_input_revision_by_turn, runtime_watermark.last_input_revision_by_turn)
            self.assertEqual(phase_watermark.seen_event_ids, runtime_watermark.seen_event_ids)
            self.assertEqual(phase_watermark.event_history_by_id, runtime_watermark.event_history_by_id)

    def test_identity_rejection_order_matches_runtime_accept_reject_boundary(self) -> None:
        phase_watermark = validate_phase_c_event_identity(
            self.first, initial_phase_c_watermark(self.first),
        )
        runtime_watermark = validate_event_identity(
            _runtime_identity_projection(self.first), watermark=self._runtime_initial(),
        )
        cases = (
            ("cross_session", _frame(event_id="event-2", atoms=[_atom(counter=2)],)),
            ("cross_campaign", _frame(event_id="event-2", atoms=[_atom(counter=2)])),
            ("wrong_campaign_version", _frame(event_id="event-2", atoms=[_atom(counter=2)])),
            ("duplicate_event", _frame(event_id="event-1", input_revision=1, atoms=[_atom(counter=2)])),
            ("turn_id_rebound", _frame(event_id="event-2", turn_sequence=1, input_revision=1, atoms=[_atom(counter=2)])),
            ("turn_sequence_rebound", _frame(event_id="event-2", turn_id="turn-2", atoms=[_atom(counter=2)])),
            ("invalid_revision", _frame(event_id="event-2", input_revision=3, atoms=[_atom(counter=2)])),
        )
        for expected, raw in cases:
            if expected == "cross_session":
                raw["call_session_id"] = "session-b"
            elif expected == "cross_campaign":
                raw["campaign_profile_id"] = "campaign-b"
            elif expected == "wrong_campaign_version":
                raw["campaign_profile_version"] = "campaign-v2"
            frame = parse_phase_c_frame(raw, self.policy)
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(PhaseCEventRejected, expected):
                    validate_phase_c_event_identity(frame, phase_watermark)
                with self.assertRaises(EmotionStateContractError):
                    validate_event_identity(_runtime_identity_projection(frame), watermark=runtime_watermark)
        second = parse_phase_c_frame(
            _frame(event_id="event-3", turn_id="turn-2", turn_sequence=1, atoms=[_atom(counter=3)]), self.policy,
        )
        phase_after_second = validate_phase_c_event_identity(second, phase_watermark)
        runtime_after_second = validate_event_identity(
            _runtime_identity_projection(second), watermark=runtime_watermark,
        )
        stale = parse_phase_c_frame(
            _frame(event_id="event-4", input_revision=1, atoms=[_atom(counter=4)]), self.policy,
        )
        with self.assertRaisesRegex(PhaseCEventRejected, "stale_turn"):
            validate_phase_c_event_identity(stale, phase_after_second)
        with self.assertRaises(EmotionStateContractError):
            validate_event_identity(_runtime_identity_projection(stale), watermark=runtime_after_second)

    def test_watermark_validator_rejects_direct_dataclass_inconsistency(self) -> None:
        watermark = validate_phase_c_event_identity(
            self.first, initial_phase_c_watermark(self.first),
        )
        malformed = PhaseCEventWatermarkV1(
            **{**watermark.__dict__, "turn_sequence_by_id": (("turn-1", 0), ("turn-1", 0))},
        )
        with self.assertRaises(PhaseCContractError):
            validate_phase_c_event_watermark(malformed)
        with self.assertRaises(PhaseCContractError):
            validate_phase_c_event_watermark("not-a-watermark")  # type: ignore[arg-type]


def build_policy_leaf_mutations(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    mutations: list[tuple[str, dict[str, Any]]] = []
    for path in _leaf_paths(payload):
        original = _value_at_path(payload, path)
        mutated = copy.deepcopy(payload)
        _replace_at_path(mutated, path, _mutate_leaf(original))
        mutations.append((".".join(str(part) for part in path), mutated))
    return mutations


def _leaf_paths(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
    if type(value) is dict:
        paths: list[tuple[str | int, ...]] = []
        for key in sorted(value):
            paths.extend(_leaf_paths(value[key], (*path, key)))
        return paths
    if type(value) is list:
        paths = []
        for index, item in enumerate(value):
            paths.extend(_leaf_paths(item, (*path, index)))
        return paths
    return [path]


def _value_at_path(payload: dict[str, Any], path: tuple[str | int, ...]) -> Any:
    value: Any = payload
    for part in path:
        value = value[part]
    return value


def _replace_at_path(payload: dict[str, Any], path: tuple[str | int, ...], value: Any) -> None:
    target: Any = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def _mutate_leaf(value: Any) -> Any:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return f"{value}-mutated"
    raise TypeError(f"unsupported policy leaf type: {type(value).__name__}")


class PhaseCPolicyContractTests(unittest.TestCase):
    def test_frozen_policy_is_exact_and_canonical(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        validated = validate_phase_c_policy(payload)
        self.assertEqual(validated["policy_id"], "emotion-state-phase-c0-synthetic-v1")
        self.assertEqual(validated["evidence_policy_version"], "emotion-state-evidence-v2")
        self.assertEqual(validated["base_support_units"]["unsolicited_explicit_statement"], 700)
        self.assertEqual(validated["contradiction_cap"], 350)
        self.assertEqual(validated["acoustic_only_cap"], 400)
        canonical = canonical_json_bytes(validated)
        self.assertEqual(
            json.loads(canonical.decode("utf-8")),
            json.loads(POLICY_PATH.read_text(encoding="utf-8")),
        )
        self.assertRegex(sha256_bytes(canonical), r"^[0-9A-F]{64}$")

    def test_every_top_level_policy_mutation_fails_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for key in tuple(payload):
            mutated = copy.deepcopy(payload)
            mutated.pop(key)
            with self.subTest(missing=key):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)
        extra = copy.deepcopy(payload)
        extra["future"] = True
        with self.assertRaises(PhaseCContractError):
            validate_phase_c_policy(extra)

    def test_every_policy_leaf_mutation_fails_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for name, mutated in build_policy_leaf_mutations(payload):
            with self.subTest(mutation=name):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)

    def test_nonfinite_and_bool_numeric_values_fail_closed(self) -> None:
        payload = load_json_strict(POLICY_PATH)
        for invalid in (True, float("nan"), float("inf"), -1):
            mutated = copy.deepcopy(payload)
            mutated["entry_threshold"] = invalid
            with self.subTest(invalid=repr(invalid)):
                with self.assertRaises(PhaseCContractError):
                    validate_phase_c_policy(mutated)

    def test_strict_loader_rejects_numeric_overflow_literals(self) -> None:
        for literal in ("1e9999", "-1e9999"):
            with self.subTest(literal=literal):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "overflow.json"
                    path.write_text(f'{{"value":{literal}}}', encoding="utf-8")
                    with self.assertRaises(PhaseCContractError):
                        load_json_strict(path)

    def test_exact_output_eol_attributes_are_narrow(self) -> None:
        self.assertEqual(
            (ROOT / ".gitattributes").read_text(
                encoding="utf-8",
            ).splitlines(),
            [
                "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json text eol=lf",
                "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md text eol=lf",
            ],
        )
