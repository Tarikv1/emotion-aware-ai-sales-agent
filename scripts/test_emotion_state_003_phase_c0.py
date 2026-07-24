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

import scripts.emotion_state_phase_c_contracts as phase_c_contracts
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
    PERCEIVED_STATE_FIELDS,
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
SCENARIO_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "cases"
    / "emotion-state-003-phase-c0-scenarios.json"
)

EXPECTED_SCENARIO_IDS_FOR_TEST = (
    "explicit_confusion_entry",
    "explicit_disengagement_entry",
    "explicit_frustration_entry",
    "explicit_hesitation_entry",
    "explicit_interest_entry",
    "transcript_three_turn_entry",
    "repeated_independence_zero_addition",
    "duplicate_event_rejected",
    "duplicate_reference_rejected",
    "acoustic_only_capped",
    "multimodal_two_turn_entry",
    "same_signal_contradiction",
    "low_quality_acoustic_abstains",
    "empty_frame_missing_input",
    "release_after_two_below_threshold",
    "switch_after_two_confirmations",
    "entry_tie_abstains",
    "incumbent_survives_unqualified_challenger",
    "latest_turn_correction_replay",
    "closed_turn_correction_rejected",
    "cross_session_rejected",
    "cross_campaign_rejected",
    "wrong_campaign_version_rejected",
    "noncanonical_atom_order_rejected",
    "forbidden_phase_b_field_rejected",
    "simultaneous_sessions_isolated",
    "canonical_replay_bytes",
    "dialogue_only_low_quality",
    "support_saturation",
    "opposition_below_contradiction_threshold",
)
EXPECTED_SCENARIO_CLASSIFICATIONS_FOR_TEST = {
    "explicit_confusion_entry": ("entry", "confusion", "text"),
    "explicit_disengagement_entry": ("entry", "disengagement", "text"),
    "explicit_frustration_entry": ("entry", "frustration", "text"),
    "explicit_hesitation_entry": ("entry", "hesitation", "text"),
    "explicit_interest_entry": ("entry", "interest", "text"),
    "transcript_three_turn_entry": ("entry", "confusion", "text"),
    "repeated_independence_zero_addition": ("independence", "interest", "text"),
    "duplicate_event_rejected": ("rejection", "confusion", "text"),
    "duplicate_reference_rejected": ("rejection", "confusion", "text"),
    "acoustic_only_capped": ("abstention", "hesitation", "acoustic"),
    "multimodal_two_turn_entry": ("entry", "frustration", "multimodal"),
    "same_signal_contradiction": ("contradiction", "confusion", "multimodal"),
    "low_quality_acoustic_abstains": ("abstention", "hesitation", "acoustic"),
    "empty_frame_missing_input": ("abstention", "none", "none"),
    "release_after_two_below_threshold": ("hysteresis", "frustration", "text"),
    "switch_after_two_confirmations": ("hysteresis", "mixed", "text"),
    "entry_tie_abstains": ("hysteresis", "mixed", "text"),
    "incumbent_survives_unqualified_challenger": ("hysteresis", "mixed", "text"),
    "latest_turn_correction_replay": ("correction", "interest", "text"),
    "closed_turn_correction_rejected": ("rejection", "confusion", "text"),
    "cross_session_rejected": ("rejection", "confusion", "text"),
    "cross_campaign_rejected": ("rejection", "confusion", "text"),
    "wrong_campaign_version_rejected": ("rejection", "confusion", "text"),
    "noncanonical_atom_order_rejected": ("rejection", "mixed", "text"),
    "forbidden_phase_b_field_rejected": ("rejection", "confusion", "text"),
    "simultaneous_sessions_isolated": ("isolation", "mixed", "text"),
    "canonical_replay_bytes": ("determinism", "confusion", "text"),
    "dialogue_only_low_quality": ("abstention", "hesitation", "dialogue"),
    "support_saturation": ("saturation", "confusion", "text"),
    "opposition_below_contradiction_threshold": (
        "contradiction",
        "confusion",
        "multimodal",
    ),
}
EXPECTED_INTERNAL_FIELDS_FOR_TEST = frozenset({
    "gross_supporting_units",
    "gross_opposing_units",
    "uncapped_net_support",
    "capped_net_support",
    "contradictory_signals",
    "seen_independence_keys",
    "internal_incumbent",
    "incumbent_tenure",
    "entry_confirmation_keys_by_signal",
    "switch_challenger",
    "switch_confirmation_keys",
    "release_streak",
    "contributing_evidence_refs",
    "seen_evidence_refs",
    "retired_independence_keys",
    "accepted_turn_count",
    "last_emitted_selected_signal",
    "last_emitted_selected_support",
})


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


def _render_scenario_recipe_rows(payload: dict[str, Any]) -> tuple[str, ...]:
    class_codes = {
        "unsolicited_explicit_statement": "U",
        "transcript_meaning": "T",
        "dialogue_context": "D",
        "synthetic_acoustic_symbol": "A",
        "weak_behavioral_proxy": "W",
    }
    direction_codes = {"supports": "+", "opposes": "-"}
    quality_codes = {"high": "H", "medium": "M", "low": "L", "unusable": "X"}
    rows: list[str] = []
    for case_ordinal, scenario in enumerate(payload["scenarios"], start=1):
        case_id = scenario["case_id"]
        known_atoms: dict[tuple[str, int, int, int], dict[str, Any]] = {}
        rendered_frames: list[str] = []
        aliases = [session["session_alias"] for session in scenario["sessions"]]
        for session_ordinal, session in enumerate(scenario["sessions"], start=1):
            alias = session["session_alias"]
            for frame in session["frames"]:
                sequence = frame["turn_sequence"]
                revision = frame["input_revision"]
                label = f"{alias}.{sequence}r{revision}"
                rendered_atoms: list[str] = []
                for atom_index, atom in enumerate(frame["evidence_atoms"]):
                    token = (
                        f"{class_codes[atom['evidence_class']]}"
                        f"({atom['operational_signal']},"
                        f"{direction_codes[atom['direction']]},"
                        f"{quality_codes[atom['quality_bucket']]})"
                    )
                    default_ref = (
                        "evidence:uuid:00000000-0000-4000-8000-"
                        f"{case_ordinal:02d}{session_ordinal:02d}"
                        f"{sequence:03d}{revision:02d}{atom_index:03d}"
                    )
                    default_key = (
                        f"ind:{case_id}:{alias}:{sequence}:{revision}:{atom_index}"
                    )
                    if atom["evidence_ref"] != default_ref:
                        source = next(
                            source_label
                            for source_label, source in (
                                (
                                    f"{a}.{t}r{r}.{i}",
                                    known,
                                )
                                for (a, t, r, i), known in known_atoms.items()
                            )
                            if source["evidence_ref"] == atom["evidence_ref"]
                        )
                        token += f"{{ref=@{source}}}"
                    if atom["independence_key"] != default_key:
                        source = next(
                            source_label
                            for source_label, source in (
                                (
                                    f"{a}.{t}r{r}.{i}",
                                    known,
                                )
                                for (a, t, r, i), known in known_atoms.items()
                            )
                            if source["independence_key"] == atom["independence_key"]
                        )
                        token += f"{{key=@{source}}}"
                    known_atoms[(alias, sequence, revision, atom_index)] = atom
                    rendered_atoms.append(token)
                rendered = f"{label}[{','.join(rendered_atoms)}]"
                default_event = f"event:{case_id}:{alias}:{sequence}:{revision}"
                if frame["event_id"] != default_event:
                    event_source = next(
                        f"{other_alias}.{other['turn_sequence']}r{other['input_revision']}"
                        for other_session in scenario["sessions"]
                        for other_alias in [other_session["session_alias"]]
                        for other in other_session["frames"]
                        if other is not frame
                        and other["event_id"] == frame["event_id"]
                    )
                    rendered += f"{{event=@{event_source}}}"
                if frame["campaign_profile_id"] != "campaign:phase-c0":
                    rendered += (
                        "{campaign_id="
                        f"{frame['campaign_profile_id']}"
                        "}"
                    )
                if frame["campaign_profile_version"] != "version:1":
                    rendered += (
                        "{campaign_version="
                        f"{frame['campaign_profile_version']}"
                        "}"
                    )
                rendered_frames.append(rendered)
        rendered_attempts: list[str] = []
        for attempt in scenario["attempt_order"]:
            frame = scenario["sessions"][
                aliases.index(attempt["frame_session_alias"])
            ]["frames"][attempt["frame_index"]]
            suffix = f"/{attempt['mutation_kind']}"
            if attempt["mutation_parameter"] is not None:
                suffix += f":{attempt['mutation_parameter']}"
            rendered_attempts.append(
                f"{attempt['state_session_alias']}<-"
                f"{attempt['frame_session_alias']}."
                f"{frame['turn_sequence']}r{frame['input_revision']}{suffix}"
            )
        rows.append(
            f"{'; '.join(rendered_frames)} | {'; '.join(rendered_attempts)}"
        )
    return tuple(rows)


EXPECTED_SCENARIO_RECIPE_ROWS_FOR_TEST = (
    "A.0r0[U(confusion,+,H)] | A<-A.0r0/none",
    "A.0r0[U(disengagement,+,H)] | A<-A.0r0/none",
    "A.0r0[U(frustration,+,H)] | A<-A.0r0/none",
    "A.0r0[U(hesitation,+,H)] | A<-A.0r0/none",
    "A.0r0[U(interest,+,H)] | A<-A.0r0/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]; A.2r0[T(confusion,+,H)] | A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none",
    "A.0r0[T(interest,+,H)]; A.1r0[T(interest,+,H){key=@A.0r0.0}] | A<-A.0r0/none; A<-A.1r0/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]{event=@A.0r0} | A<-A.0r0/none; A<-A.1r0/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H){ref=@A.0r0.0}] | A<-A.0r0/none; A<-A.1r0/none",
    "A.0r0[A(hesitation,+,H)]; A.1r0[A(hesitation,+,H)]; A.2r0[A(hesitation,+,H)] | A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none",
    "A.0r0[T(frustration,+,H),A(frustration,+,H)]; A.1r0[T(frustration,+,H),A(frustration,+,H)] | A<-A.0r0/none; A<-A.1r0/none",
    "A.0r0[U(confusion,+,H),D(confusion,+,H),D(confusion,-,H)] | A<-A.0r0/none",
    "A.0r0[A(hesitation,+,L)] | A<-A.0r0/none",
    "A.0r0[] | A<-A.0r0/none",
    "A.0r0[U(frustration,+,H)]; A.1r0[]; A.2r0[]; A.3r0[]; A.4r0[]; A.5r0[] | A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none; A<-A.3r0/none; A<-A.4r0/none; A<-A.5r0/none",
    "A.0r0[U(frustration,+,H)]; A.1r0[U(confusion,+,H)]; A.2r0[T(confusion,+,H)]; A.3r0[T(confusion,+,H)] | A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none; A<-A.3r0/none",
    "A.0r0[U(confusion,+,H),U(frustration,+,H)] | A<-A.0r0/none",
    "A.0r0[U(frustration,+,H)]; A.1r0[U(confusion,+,H)]; A.2r0[T(confusion,+,H)]; A.3r0[] | A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none; A<-A.3r0/none",
    "A.0r0[T(interest,+,H)]; A.0r1[U(interest,+,H)] | A<-A.0r0/none; A<-A.0r1/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[]; A.0r1[U(confusion,+,H)] | A<-A.0r0/none; A<-A.1r0/none; A<-A.0r1/none",
    "A.0r0[T(confusion,+,H)]; B.0r0[T(confusion,+,H)] | A<-A.0r0/none; A<-B.0r0/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]{campaign_id=campaign:phase-c0-other} | A<-A.0r0/none; A<-A.1r0/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[T(confusion,+,H)]{campaign_version=version:2} | A<-A.0r0/none; A<-A.1r0/none",
    "A.0r0[U(confusion,+,H),U(frustration,+,H)] | A<-A.0r0/reverse_atom_order",
    "A.0r0[U(confusion,+,H)] | A<-A.0r0/add_forbidden_field:acoustic_features; A<-A.0r0/add_forbidden_field:probabilities; A<-A.0r0/add_forbidden_field:model_id; A<-A.0r0/add_forbidden_field:dataset_id",
    "A.0r0[U(confusion,+,H)]; A.1r0[]; B.0r0[U(interest,+,H)]; B.1r0[] | A<-A.0r0/none; B<-B.0r0/none; A<-A.1r0/none; B<-B.1r0/none",
    "A.0r0[T(confusion,+,H)]; A.1r0[]; A.2r0[U(confusion,+,H)] | A<-A.0r0/none; A<-A.1r0/none; A<-A.2r0/none",
    "A.0r0[D(hesitation,+,H),W(hesitation,+,X)] | A<-A.0r0/none",
    "A.0r0[U(confusion,+,H),T(confusion,+,H)] | A<-A.0r0/none",
    "A.0r0[U(confusion,+,H),W(confusion,-,H)] | A<-A.0r0/none",
)


class PhaseCScenarioContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))

    def test_scenario_ids_order_count_and_classifications_are_frozen(self) -> None:
        scenarios = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )
        self.assertEqual(
            tuple(item.case_id for item in scenarios),
            EXPECTED_SCENARIO_IDS_FOR_TEST,
        )
        self.assertEqual(len(scenarios), 30)
        self.assertEqual(
            {
                item.case_id: (
                    item.family,
                    item.signal_family,
                    item.modality_family,
                )
                for item in scenarios
            },
            EXPECTED_SCENARIO_CLASSIFICATIONS_FOR_TEST,
        )

    def test_frames_and_attempts_expand_to_every_exact_recipe_row(self) -> None:
        raw = load_json_strict(SCENARIO_PATH)
        self.assertEqual(
            _render_scenario_recipe_rows(raw),
            EXPECTED_SCENARIO_RECIPE_ROWS_FOR_TEST,
        )

    def test_forbidden_surfaces_exist_only_as_negative_mutation_parameters(self) -> None:
        raw = load_json_strict(SCENARIO_PATH)
        allowed = {
            "acoustic_features",
            "probabilities",
            "model_id",
            "dataset_id",
        }
        observed = []
        for scenario in raw["scenarios"]:
            serialized_frames = canonical_json_bytes(
                {"sessions": scenario["sessions"]},
            ).decode("utf-8").lower()
            for forbidden in allowed | {
                "audio_bytes",
                "transcript_text",
                "customer_name",
            }:
                self.assertNotIn(forbidden, serialized_frames)
            for attempt in scenario["attempt_order"]:
                if attempt["mutation_kind"] == "add_forbidden_field":
                    observed.append(attempt["mutation_parameter"])
        self.assertEqual(set(observed), allowed)

    def test_every_expected_projection_has_exact_fields_and_stable_bytes(self) -> None:
        raw = load_json_strict(SCENARIO_PATH)
        scenarios = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )
        for raw_scenario, scenario in zip(raw["scenarios"], scenarios, strict=True):
            for raw_step, parsed_step in zip(
                raw_scenario["expected_steps"],
                scenario.expected_steps,
                strict=True,
            ):
                if raw_step["disposition"] != "accepted":
                    self.assertEqual(
                        set(raw_step),
                        {
                            "disposition",
                            "rejection_code",
                            "prior_state_bytes_unchanged",
                        },
                    )
                    continue
                self.assertEqual(set(raw_step["expected_output"]), PERCEIVED_STATE_FIELDS)
                self.assertEqual(
                    set(raw_step["expected_internal"]),
                    EXPECTED_INTERNAL_FIELDS_FOR_TEST,
                )
                self.assertEqual(
                    parsed_step.expected_output_bytes,
                    canonical_json_bytes(raw_step["expected_output"]),
                )

    def test_scenario_canonical_identity_is_checkout_eol_independent(self) -> None:
        payload = load_json_strict(SCENARIO_PATH)
        canonical = canonical_json_bytes(payload)
        self.assertEqual(
            json.loads(canonical.decode("utf-8")),
            json.loads(SCENARIO_PATH.read_text(encoding="utf-8")),
        )
        self.assertEqual(
            phase_c_contracts.scenario_payload_sha256(payload),
            sha256_bytes(canonical),
        )

    def test_mutation_materialization_is_allowlisted_and_never_mutates_base(self) -> None:
        scenarios = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )
        observed: set[str] = set()
        for scenario in scenarios:
            for attempt in scenario.attempt_order:
                before = repr(scenario.sessions)
                candidate = phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                    scenario,
                    attempt,
                )
                self.assertEqual(repr(scenario.sessions), before)
                if attempt.mutation_kind == "none":
                    parse_phase_c_frame(candidate, self.policy)
                elif attempt.mutation_kind == "reverse_atom_order":
                    with self.assertRaisesRegex(
                        PhaseCContractError,
                        "noncanonical_atom_order",
                    ):
                        parse_phase_c_frame(candidate, self.policy)
                else:
                    observed.add(attempt.mutation_parameter)
                    self.assertIn(attempt.mutation_parameter, candidate)
                    with self.assertRaisesRegex(PhaseCContractError, "forbidden_field"):
                        parse_phase_c_frame(candidate, self.policy)
        self.assertEqual(
            observed,
            {"acoustic_features", "probabilities", "model_id", "dataset_id"},
        )

    def test_loader_fails_closed_on_container_alias_attempt_and_expectation_mutations(self) -> None:
        original = load_json_strict(SCENARIO_PATH)
        mutations: list[dict[str, Any]] = []
        for field, value in (
            ("schema_version", "future"),
            ("policy_id", "future"),
        ):
            mutated = copy.deepcopy(original)
            mutated[field] = value
            mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][1]["case_id"] = mutated["scenarios"][0]["case_id"]
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["family"] = "future"
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][20]["sessions"].reverse()
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["sessions"][0]["session_alias"] = "C"
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["attempt_order"][0]["frame_index"] = 99
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["expected_steps"] = []
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["expected_steps"][0]["future"] = True
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["expected_steps"][0]["expected_internal"].pop(
            "release_streak",
        )
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["expected_steps"][0]["expected_output"][
            "runtime_approved"
        ] = True
        mutations.append(mutated)
        mutated = copy.deepcopy(original)
        mutated["scenarios"][0]["sessions"][0]["frames"][0]["nested"] = {
            "raw_audio": "forbidden",
        }
        mutations.append(mutated)
        for index, payload in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(PhaseCContractError):
                    phase_c_contracts.validate_phase_c_scenario_payload(
                        payload,
                        self.policy,
                    )


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
        with self.assertRaises(PhaseCContractError) as caught:
            validate_phase_c_event_watermark("not-a-watermark")  # type: ignore[arg-type]
        self.assertEqual(caught.exception.code, "event_watermark_type")


class PhaseCIdentityHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        self.frame = parse_phase_c_frame(_frame(atoms=[_atom(counter=1)]), self.policy)

    def _non_bijective_watermark(self) -> PhaseCEventWatermarkV1:
        return PhaseCEventWatermarkV1(
            expected_session_id="session-a",
            expected_campaign_profile_id="campaign-a",
            expected_campaign_profile_version="campaign-v1",
            last_turn_sequence=0,
            turn_sequence_by_id=(("turn-1", 0), ("turn-2", 0)),
            turn_id_by_sequence=((0, "turn-2"),),
            last_input_revision_by_turn=(("turn-1", 0), ("turn-2", 0)),
            seen_event_ids=frozenset({"event-1", "event-2"}),
            event_history_by_id=(("event-1", "turn-1", 0), ("event-2", "turn-2", 0)),
        )

    def test_non_bijective_forward_turn_map_rejects_exactly(self) -> None:
        with self.assertRaises(PhaseCContractError) as caught:
            validate_phase_c_event_watermark(self._non_bijective_watermark())
        self.assertEqual(caught.exception.code, "event_watermark_turn_map_inverse")

    def test_direct_frame_with_malformed_atom_rejects_in_initial_and_identity(self) -> None:
        malformed_atom = PhaseCSyntheticEvidenceAtomV1(
            **{**self.frame.evidence_atoms[0].__dict__, "quality_bucket": "invalid"},
        )
        malformed_frame = PhaseCSyntheticEvidenceFrameV1(
            **{**self.frame.__dict__, "evidence_atoms": (malformed_atom,)},
        )
        with self.assertRaises(PhaseCContractError) as initial_error:
            initial_phase_c_watermark(malformed_frame)
        self.assertEqual(initial_error.exception.code, "unknown_atom_enum")
        watermark = initial_phase_c_watermark(self.frame)
        with self.assertRaises(PhaseCContractError) as identity_error:
            validate_phase_c_event_identity(malformed_frame, watermark)
        self.assertEqual(identity_error.exception.code, "unknown_atom_enum")

    def test_malformed_watermark_wins_before_cross_session_or_malformed_frame(self) -> None:
        bad_atom = PhaseCSyntheticEvidenceAtomV1(
            **{**self.frame.evidence_atoms[0].__dict__, "quality_bucket": "invalid"},
        )
        bad_frame = PhaseCSyntheticEvidenceFrameV1(
            **{
                **self.frame.__dict__,
                "call_session_id": "session-b",
                "evidence_atoms": (bad_atom,),
            },
        )
        with self.assertRaises(PhaseCContractError) as caught:
            validate_phase_c_event_identity(bad_frame, self._non_bijective_watermark())
        self.assertEqual(caught.exception.code, "event_watermark_turn_map_inverse")

    def test_exact_input_mutations_cover_types_enums_forbidden_and_sort_key(self) -> None:
        atom = _atom(counter=1)
        for field in ("evidence_ref", "independence_key", "operational_signal", "direction", "modality", "evidence_class", "quality_bucket"):
            mutated = dict(atom)
            mutated[field] = 1
            with self.subTest(atom_type=field):
                with self.assertRaisesRegex(PhaseCContractError, "atom_field_type"):
                    parse_phase_c_atom(mutated, self.policy)
        for field in ("operational_signal", "direction", "modality", "evidence_class", "quality_bucket"):
            mutated = dict(atom)
            mutated[field] = "not-an-enum"
            with self.subTest(atom_enum=field):
                with self.assertRaisesRegex(PhaseCContractError, "unknown_atom_enum"):
                    parse_phase_c_atom(mutated, self.policy)
        for fragment in (
            "acoustic_features", "probabilities", "model_id", "dataset_id", "audio_bytes", "raw_audio",
            "transcript_text", "raw_transcript", "customer_name", "customer_phone", "customer_email",
            "speaker_embedding", "voiceprint", "provider_payload", "api_key", "access_token", "auth_token",
            "password", "secret", "private_key", "hidden_reasoning",
        ):
            payload = _frame(atoms=[_atom(counter=1)])
            payload["outer"] = [{"inner_" + fragment: {"safe": True}}]
            with self.subTest(forbidden=fragment):
                with self.assertRaisesRegex(PhaseCContractError, "forbidden_field"):
                    parse_phase_c_frame(payload, self.policy)
        ordered = parse_phase_c_atom(_atom(counter=1), self.policy)
        self.assertEqual(
            atom_sort_key(ordered, self.policy),
            (0, 0, 0, 1, 0, "ind:fixture:1:1", "evidence:uuid:00000000-0000-4000-8000-000000000001"),
        )

    def test_identity_rejections_keep_input_watermark_unchanged_and_report_codes(self) -> None:
        watermark = validate_phase_c_event_identity(self.frame, initial_phase_c_watermark(self.frame))
        cases = {
            "cross_session": _frame(event_id="event-2", atoms=[_atom(counter=2)]),
            "cross_campaign": _frame(event_id="event-2", atoms=[_atom(counter=2)]),
            "wrong_campaign_version": _frame(event_id="event-2", atoms=[_atom(counter=2)]),
            "duplicate_event": _frame(event_id="event-1", input_revision=1, atoms=[_atom(counter=2)]),
            "turn_id_rebound": _frame(event_id="event-2", turn_sequence=1, input_revision=1, atoms=[_atom(counter=2)]),
            "turn_sequence_rebound": _frame(event_id="event-2", turn_id="turn-2", atoms=[_atom(counter=2)]),
            "invalid_revision": _frame(event_id="event-2", input_revision=3, atoms=[_atom(counter=2)]),
        }
        for expected, raw in cases.items():
            if expected == "cross_session": raw["call_session_id"] = "session-b"
            if expected == "cross_campaign": raw["campaign_profile_id"] = "campaign-b"
            if expected == "wrong_campaign_version": raw["campaign_profile_version"] = "campaign-v2"
            before = repr(watermark)
            with self.subTest(expected=expected):
                with self.assertRaises(PhaseCEventRejected) as caught:
                    validate_phase_c_event_identity(parse_phase_c_frame(raw, self.policy), watermark)
                self.assertEqual(caught.exception.code, expected)
                self.assertEqual(repr(watermark), before)
        newer = parse_phase_c_frame(
            _frame(event_id="event-3", turn_id="turn-2", turn_sequence=1, atoms=[_atom(counter=3)]), self.policy,
        )
        after_newer = validate_phase_c_event_identity(newer, watermark)
        stale = parse_phase_c_frame(
            _frame(event_id="event-4", input_revision=1, atoms=[_atom(counter=4)]), self.policy,
        )
        before_stale = repr(after_newer)
        with self.assertRaises(PhaseCEventRejected) as caught:
            validate_phase_c_event_identity(stale, after_newer)
        self.assertEqual(caught.exception.code, "stale_turn")
        self.assertEqual(repr(after_newer), before_stale)

    def test_complete_scalar_shape_and_watermark_invariant_matrix(self) -> None:
        for payload, parser, code in (([], parse_phase_c_atom, "atom_not_object"), ([], parse_phase_c_frame, "frame_not_object")):
            with self.subTest(non_object=code):
                with self.assertRaisesRegex(PhaseCContractError, code):
                    parser(payload, self.policy)
        atom = _atom(counter=1)
        for field in tuple(atom):
            mutated = dict(atom)
            mutated[field] = 1
            expected = "atom_schema" if field == "schema_version" else "atom_field_type"
            with self.subTest(atom_scalar=field):
                with self.assertRaisesRegex(PhaseCContractError, expected):
                    parse_phase_c_atom(mutated, self.policy)
        frame = _frame(atoms=[_atom(counter=1)])
        for field in tuple(frame):
            mutated = dict(frame)
            mutated[field] = True if field in ("turn_sequence", "input_revision") else 1
            expected = "frame_schema" if field == "schema_version" else ("fixture_only_required" if field == "fixture_only" else "frame_field_type")
            with self.subTest(frame_scalar=field):
                with self.assertRaisesRegex(PhaseCContractError, expected):
                    parse_phase_c_frame(mutated, self.policy)
        malformed_key = _atom(counter=1, independence_key=" bad")
        with self.assertRaisesRegex(PhaseCContractError, "invalid_opaque_identifier"):
            parse_phase_c_atom(malformed_key, self.policy)
        malformed_ref = _atom(counter=1)
        malformed_ref["evidence_ref"] = "evidence:uuid:bad"
        with self.assertRaisesRegex(PhaseCContractError, "invalid_evidence_reference"):
            parse_phase_c_atom(malformed_ref, self.policy)
        good = validate_phase_c_event_identity(self.frame, initial_phase_c_watermark(self.frame))
        cases = (
            ({"turn_sequence_by_id": []}, "event_watermark_collections"),
            ({"turn_sequence_by_id": (("turn-1",),)}, "event_watermark_entries"),
            ({"turn_id_by_sequence": ((0, "turn-1"), (0, "turn-1"))}, "event_watermark_duplicate_map_key"),
            ({"last_input_revision_by_turn": (("turn-1", 0), ("turn-1", 0))}, "event_watermark_duplicate_map_key"),
            ({"seen_event_ids": frozenset()}, "event_watermark_event_history"),
            ({"event_history_by_id": (("event-1", "turn-1", 0), ("event-2", "turn-1", 0))}, "event_watermark_duplicate_history"),
            ({"last_input_revision_by_turn": (("turn-1", 1),)}, "event_watermark_revision_history"),
            ({"last_turn_sequence": 1}, "event_watermark_last_turn"),
            ({"last_turn_sequence": True}, "event_watermark_counter"),
            ({"expected_session_id": " bad"}, "invalid_opaque_identifier"),
        )
        for overrides, expected in cases:
            candidate = PhaseCEventWatermarkV1(**{**good.__dict__, **overrides})
            with self.subTest(watermark=expected):
                with self.assertRaises(PhaseCContractError) as caught:
                    validate_phase_c_event_watermark(candidate)
                self.assertEqual(caught.exception.code, expected)
        tie_low = parse_phase_c_atom(_atom(counter=2, independence_key="ind:fixture:1:a"), self.policy)
        tie_high = parse_phase_c_atom(_atom(counter=1, independence_key="ind:fixture:1:b"), self.policy)
        self.assertLess(atom_sort_key(tie_low, self.policy), atom_sort_key(tie_high, self.policy))


class PhaseCWatermarkCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        frame = parse_phase_c_frame(_frame(atoms=[_atom(counter=1)]), policy)
        self.good = validate_phase_c_event_identity(frame, initial_phase_c_watermark(frame))

    def _assert_code(self, overrides: dict[str, object], expected: str) -> None:
        watermark = PhaseCEventWatermarkV1(**{**self.good.__dict__, **overrides})
        with self.assertRaises(PhaseCContractError) as caught:
            validate_phase_c_event_watermark(watermark)
        self.assertEqual(caught.exception.code, expected)

    def test_sequence_and_revision_positions_reject_exactly(self) -> None:
        cases = (
            ({"turn_sequence_by_id": (("turn-1", True),)}, "event_watermark_sequence"),
            ({"turn_sequence_by_id": (("turn-1", -1),)}, "event_watermark_sequence"),
            ({"turn_id_by_sequence": ((True, "turn-1"),)}, "event_watermark_sequence"),
            ({"turn_id_by_sequence": ((-1, "turn-1"),)}, "event_watermark_sequence"),
            ({"last_input_revision_by_turn": (("turn-1", True),)}, "event_watermark_revision"),
            ({"last_input_revision_by_turn": (("turn-1", -1),)}, "event_watermark_revision"),
            ({"event_history_by_id": (("event-1", "turn-1", True),)}, "event_watermark_revision"),
            ({"event_history_by_id": (("event-1", "turn-1", -1),)}, "event_watermark_revision"),
        )
        for overrides, expected in cases:
            with self.subTest(overrides=repr(overrides)):
                self._assert_code(overrides, expected)

    def test_history_shape_coverage_and_distinct_duplicate_paths_reject_exactly(self) -> None:
        cases = (
            ({"event_history_by_id": (("event-1", "turn-1"),)}, "event_watermark_history"),
            ({"turn_sequence_by_id": (("turn-1", 0), ("turn-1", 0))}, "event_watermark_duplicate_map_key"),
            ({"last_input_revision_by_turn": ()}, "event_watermark_coverage"),
            ({"event_history_by_id": (("event-1", "turn-2", 0),)}, "event_watermark_coverage"),
            ({"event_history_by_id": (("event-1", "turn-1", 0), ("event-1", "turn-1", 1))}, "event_watermark_duplicate_history"),
            ({"event_history_by_id": (("event-1", "turn-1", 0), ("event-2", "turn-1", 0))}, "event_watermark_duplicate_history"),
        )
        for overrides, expected in cases:
            with self.subTest(expected=expected, overrides=repr(overrides)):
                self._assert_code(overrides, expected)

    def test_every_opaque_identifier_position_rejects_exactly(self) -> None:
        cases = (
            {"turn_sequence_by_id": ((" bad", 0),)},
            {"turn_id_by_sequence": ((0, " bad"),)},
            {"last_input_revision_by_turn": ((" bad", 0),)},
            {"seen_event_ids": frozenset({" bad"})},
            {"event_history_by_id": ((" bad", "turn-1", 0),)},
            {"event_history_by_id": (("event-1", " bad", 0),)},
        )
        for overrides in cases:
            with self.subTest(overrides=repr(overrides)):
                self._assert_code(overrides, "invalid_opaque_identifier")


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
