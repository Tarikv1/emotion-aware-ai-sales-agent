from __future__ import annotations

import ast
import copy
import dataclasses
import importlib
import inspect
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Mapping as ABCMapping
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest import mock

import scripts.emotion_state_phase_c_contracts as phase_c_contracts
from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    PhaseCEventRejected,
    PhaseCEventWatermarkV1,
    PhaseCOutputSemanticError,
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
    REQUIRED_BLOCKED_POLICY_EFFECTS,
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

REJECTION_CASE_IDS = (
    "duplicate_event_rejected",
    "duplicate_reference_rejected",
    "closed_turn_correction_rejected",
    "cross_session_rejected",
    "cross_campaign_rejected",
    "wrong_campaign_version_rejected",
    "noncanonical_atom_order_rejected",
    "forbidden_phase_b_field_rejected",
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

    def assert_scenario_code(
        self,
        payload: dict[str, Any],
        expected_code: str,
    ) -> None:
        with self.assertRaises(PhaseCContractError) as captured:
            phase_c_contracts.validate_phase_c_scenario_payload(
                payload,
                self.policy,
            )
        self.assertEqual(captured.exception.code, expected_code)

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

    def test_loader_rejects_reviewed_order_reference_and_hysteresis_bypasses(self) -> None:
        original = load_json_strict(SCENARIO_PATH)

        reversed_reasons = copy.deepcopy(original)
        contradiction = reversed_reasons["scenarios"][
            EXPECTED_SCENARIO_IDS_FOR_TEST.index("same_signal_contradiction")
        ]
        contradiction["expected_steps"][0]["expected_output"][
            "abstention_reasons"
        ].reverse()
        self.assert_scenario_code(
            reversed_reasons,
            "scenario_abstention_reason_order",
        )

        reversed_keys = copy.deepcopy(original)
        switch = reversed_keys["scenarios"][
            EXPECTED_SCENARIO_IDS_FOR_TEST.index(
                "switch_after_two_confirmations",
            )
        ]
        switch["expected_steps"][2]["expected_internal"][
            "seen_independence_keys"
        ].reverse()
        self.assert_scenario_code(
            reversed_keys,
            "scenario_internal_key_order",
        )

        unknown_key = copy.deepcopy(original)
        switch = unknown_key["scenarios"][
            EXPECTED_SCENARIO_IDS_FOR_TEST.index(
                "switch_after_two_confirmations",
            )
        ]
        switch["expected_steps"][2]["expected_internal"][
            "seen_independence_keys"
        ][0] = "bogus"
        self.assert_scenario_code(
            unknown_key,
            "scenario_internal_unknown_key",
        )

        impossible_hysteresis = copy.deepcopy(original)
        expected_internal = impossible_hysteresis["scenarios"][0][
            "expected_steps"
        ][0]["expected_internal"]
        expected_internal["internal_incumbent"] = None
        expected_internal["incumbent_tenure"] = 0
        expected_internal["switch_challenger"] = "frustration"
        expected_internal["switch_confirmation_keys"] = [
            expected_internal["seen_independence_keys"][0],
        ]
        self.assert_scenario_code(
            impossible_hysteresis,
            "expected_internal_hysteresis",
        )

    def test_loader_binds_every_case_recipe_to_frozen_authority(self) -> None:
        original = load_json_strict(SCENARIO_PATH)
        for scenario_index, scenario in enumerate(original["scenarios"]):
            mutated = copy.deepcopy(original)
            frame = mutated["scenarios"][scenario_index]["sessions"][0][
                "frames"
            ][0]
            frame["event_id"] = f"event:{scenario['case_id']}:authority-drift"
            with self.subTest(case_id=scenario["case_id"]):
                self.assert_scenario_code(
                    mutated,
                    "scenario_authority_digest",
                )

    def test_loader_binds_every_attempt_disposition_and_rejection_recipe(self) -> None:
        original = load_json_strict(SCENARIO_PATH)
        accepted_template = copy.deepcopy(
            original["scenarios"][0]["expected_steps"][0],
        )
        forbidden_parameters = (
            "acoustic_features",
            "probabilities",
            "model_id",
            "dataset_id",
        )
        for scenario_index, scenario in enumerate(original["scenarios"]):
            for attempt_index, attempt in enumerate(scenario["attempt_order"]):
                mutated = copy.deepcopy(original)
                candidate_attempt = mutated["scenarios"][scenario_index][
                    "attempt_order"
                ][attempt_index]
                candidate_step = mutated["scenarios"][scenario_index][
                    "expected_steps"
                ][attempt_index]
                if attempt["mutation_kind"] == "add_forbidden_field":
                    parameter_index = forbidden_parameters.index(
                        attempt["mutation_parameter"],
                    )
                    candidate_attempt["mutation_parameter"] = (
                        forbidden_parameters[(parameter_index + 1) % 4]
                    )
                else:
                    candidate_attempt["mutation_kind"] = "add_forbidden_field"
                    candidate_attempt["mutation_parameter"] = "acoustic_features"
                    candidate_step.clear()
                    candidate_step.update({
                        "disposition": "rejected",
                        "rejection_code": "forbidden_field",
                        "prior_state_bytes_unchanged": True,
                    })
                with self.subTest(
                    authority="attempt",
                    case_id=scenario["case_id"],
                    attempt_index=attempt_index,
                ):
                    self.assert_scenario_code(
                        mutated,
                        "scenario_attempt_authority",
                    )

                mutated = copy.deepcopy(original)
                candidate_step = mutated["scenarios"][scenario_index][
                    "expected_steps"
                ][attempt_index]
                if candidate_step["disposition"] == "accepted":
                    candidate_step.clear()
                    candidate_step.update({
                        "disposition": "rejected",
                        "rejection_code": "duplicate_event",
                        "prior_state_bytes_unchanged": True,
                    })
                else:
                    candidate_step.clear()
                    candidate_step.update(copy.deepcopy(accepted_template))
                with self.subTest(
                    authority="disposition",
                    case_id=scenario["case_id"],
                    attempt_index=attempt_index,
                ):
                    self.assert_scenario_code(
                        mutated,
                        "scenario_disposition_authority",
                    )

                if scenario["expected_steps"][attempt_index][
                    "disposition"
                ] == "rejected":
                    mutated = copy.deepcopy(original)
                    candidate_step = mutated["scenarios"][scenario_index][
                        "expected_steps"
                    ][attempt_index]
                    candidate_step["rejection_code"] = (
                        "cross_session"
                        if candidate_step["rejection_code"] != "cross_session"
                        else "duplicate_event"
                    )
                    with self.subTest(
                        authority="rejection",
                        case_id=scenario["case_id"],
                        attempt_index=attempt_index,
                    ):
                        self.assert_scenario_code(
                            mutated,
                            "scenario_rejection_authority",
                        )

    def test_materializer_rejects_direct_dataclass_bypasses_exactly(self) -> None:
        scenarios = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )
        scenario = scenarios[0]
        attempt = scenario.attempt_order[0]

        bad_alias = dataclasses.replace(
            attempt,
            state_session_alias="C",
        )
        with self.assertRaises(PhaseCContractError) as captured:
            phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                scenario,
                bad_alias,
            )
        self.assertEqual(captured.exception.code, "scenario_attempt_alias")

        direct_attempt_bypasses = (
            (
                "frame_alias",
                dataclasses.replace(attempt, frame_session_alias="C"),
                "scenario_attempt_alias",
            ),
            (
                "frame_index",
                dataclasses.replace(attempt, frame_index=99),
                "scenario_attempt_frame_index",
            ),
            (
                "mutation_kind",
                dataclasses.replace(attempt, mutation_kind="future"),
                "scenario_attempt_mutation",
            ),
            (
                "none_parameter",
                dataclasses.replace(attempt, mutation_parameter="dataset_id"),
                "scenario_attempt_mutation_parameter",
            ),
            (
                "reverse_size",
                dataclasses.replace(attempt, mutation_kind="reverse_atom_order"),
                "scenario_attempt_reverse_size",
            ),
            (
                "forbidden_parameter",
                dataclasses.replace(
                    attempt,
                    mutation_kind="add_forbidden_field",
                    mutation_parameter="future",
                ),
                "scenario_attempt_mutation_parameter",
            ),
        )
        for name, bypass, expected_code in direct_attempt_bypasses:
            with self.subTest(name=name):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                        scenario,
                        bypass,
                    )
                self.assertEqual(captured.exception.code, expected_code)

        not_a_member = dataclasses.replace(
            attempt,
            mutation_kind="add_forbidden_field",
            mutation_parameter="acoustic_features",
        )
        with self.assertRaises(PhaseCContractError) as captured:
            phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                scenario,
                not_a_member,
            )
        self.assertEqual(
            captured.exception.code,
            "scenario_attempt_membership",
        )

        bad_sessions = dataclasses.replace(
            scenario,
            sessions=(scenario.sessions[0], scenario.sessions[0]),
        )
        with self.assertRaises(PhaseCContractError) as captured:
            phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                bad_sessions,
                attempt,
            )
        self.assertEqual(
            captured.exception.code,
            "scenario_session_aliases",
        )

        two_session_scenario = scenarios[
            EXPECTED_SCENARIO_IDS_FOR_TEST.index(
                "simultaneous_sessions_isolated",
            )
        ]
        wrong_session_order = dataclasses.replace(
            two_session_scenario,
            sessions=tuple(reversed(two_session_scenario.sessions)),
        )
        with self.assertRaises(PhaseCContractError) as captured:
            phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                wrong_session_order,
                two_session_scenario.attempt_order[0],
            )
        self.assertEqual(
            captured.exception.code,
            "scenario_session_aliases",
        )

        wrong_disposition = dataclasses.replace(
            scenario,
            expected_steps=(
                phase_c_contracts.PhaseCExpectedRejectedStepV1(
                    disposition="rejected",
                    rejection_code="duplicate_event",
                    prior_state_bytes_unchanged=True,
                ),
            ),
        )
        with self.assertRaises(PhaseCContractError) as captured:
            phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                wrong_disposition,
                attempt,
            )
        self.assertEqual(
            captured.exception.code,
            "scenario_disposition_authority",
        )

    def test_materializer_binds_direct_dataclass_frames_and_goldens(self) -> None:
        scenario = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )[0]
        attempt = scenario.attempt_order[0]

        original_session = scenario.sessions[0]
        drifted_frame = dataclasses.replace(
            original_session.frames[0],
            event_id="event:explicit_confusion_entry:A:authority-drift",
        )
        frame_drift = dataclasses.replace(
            scenario,
            sessions=(
                dataclasses.replace(
                    original_session,
                    frames=(drifted_frame,),
                ),
            ),
        )

        accepted = scenario.expected_steps[0]
        self.assertIsInstance(
            accepted,
            phase_c_contracts.PhaseCExpectedAcceptedStepV1,
        )
        output_payload = json.loads(
            accepted.expected_output_bytes.decode("utf-8"),
        )
        output_payload["trajectory"] = "stable"
        output_drift = dataclasses.replace(
            scenario,
            expected_steps=(
                dataclasses.replace(
                    accepted,
                    expected_output_bytes=canonical_json_bytes(output_payload),
                ),
            ),
        )

        internal = accepted.expected_internal
        internal_drift = dataclasses.replace(
            scenario,
            expected_steps=(
                dataclasses.replace(
                    accepted,
                    expected_internal=dataclasses.replace(
                        internal,
                        gross_supporting_units=(
                            ("confusion", 699),
                            *internal.gross_supporting_units[1:],
                        ),
                    ),
                ),
            ),
        )

        for name, mutated in (
            ("frame", frame_drift),
            ("output", output_drift),
            ("internal", internal_drift),
        ):
            with self.subTest(name=name):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                        mutated,
                        attempt,
                    )
                self.assertEqual(
                    captured.exception.code,
                    "scenario_dataclass_authority_digest",
                )

    def test_materializer_rejects_lossy_internal_normalization_bypasses(self) -> None:
        scenario = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )[0]
        attempt = scenario.attempt_order[0]
        accepted = scenario.expected_steps[0]
        self.assertIsInstance(
            accepted,
            phase_c_contracts.PhaseCExpectedAcceptedStepV1,
        )
        internal = accepted.expected_internal
        key = internal.seen_independence_keys[0]

        mutations = (
            (
                "dense_outer_list",
                dataclasses.replace(
                    internal,
                    gross_supporting_units=list(
                        internal.gross_supporting_units,
                    ),
                ),
                "expected_internal_gross_supporting_units_shape",
            ),
            (
                "seen_keys_list",
                dataclasses.replace(
                    internal,
                    seen_independence_keys=list(
                        internal.seen_independence_keys,
                    ),
                ),
                "expected_internal_seen_independence_keys_shape",
            ),
            (
                "dense_duplicate",
                dataclasses.replace(
                    internal,
                    gross_supporting_units=(
                        ("confusion", 999),
                        *internal.gross_supporting_units,
                    ),
                ),
                "expected_internal_gross_supporting_units_shape",
            ),
            (
                "entry_duplicate",
                dataclasses.replace(
                    internal,
                    entry_confirmation_keys_by_signal=(
                        ("confusion", (key,)),
                        *internal.entry_confirmation_keys_by_signal,
                    ),
                ),
                "expected_internal_entry_shape",
            ),
        )
        for name, mutated_internal, expected_code in mutations:
            mutated = dataclasses.replace(
                scenario,
                expected_steps=(
                    dataclasses.replace(
                        accepted,
                        expected_internal=mutated_internal,
                    ),
                ),
            )
            with self.subTest(name=name):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                        mutated,
                        attempt,
                    )
                self.assertEqual(captured.exception.code, expected_code)

    def test_materializer_rejects_every_internal_dataclass_shape_family(self) -> None:
        scenario = phase_c_contracts.load_and_validate_phase_c_scenarios(
            SCENARIO_PATH,
            self.policy,
        )[0]
        attempt = scenario.attempt_order[0]
        accepted = scenario.expected_steps[0]
        self.assertIsInstance(
            accepted,
            phase_c_contracts.PhaseCExpectedAcceptedStepV1,
        )
        internal = accepted.expected_internal

        mutations: list[tuple[str, str, Any, str]] = []
        for field in (
            "gross_supporting_units",
            "gross_opposing_units",
            "uncapped_net_support",
            "capped_net_support",
        ):
            authority = getattr(internal, field)
            code = f"expected_internal_{field}_shape"
            mutations.extend((
                (f"{field}_outer", field, list(authority), code),
                (
                    f"{field}_entry",
                    field,
                    (list(authority[0]), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_order",
                    field,
                    (authority[1], authority[0], *authority[2:]),
                    code,
                ),
                (
                    f"{field}_duplicate",
                    field,
                    (authority[0], *authority),
                    code,
                ),
                (
                    f"{field}_bool",
                    field,
                    ((authority[0][0], True), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_negative",
                    field,
                    ((authority[0][0], -1), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_arity_one",
                    field,
                    ((authority[0][0],), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_arity_three",
                    field,
                    ((authority[0][0], authority[0][1], 0), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_key_type",
                    field,
                    ((1, authority[0][1]), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_wrong_key",
                    field,
                    (("unknown", authority[0][1]), *authority[1:]),
                    code,
                ),
                (
                    f"{field}_duplicate_key",
                    field,
                    (
                        authority[0],
                        (authority[0][0], authority[1][1]),
                        *authority[2:],
                    ),
                    code,
                ),
                (
                    f"{field}_unit_float",
                    field,
                    ((authority[0][0], 1.0), *authority[1:]),
                    code,
                ),
            ))

        for field in (
            "contradictory_signals",
            "seen_independence_keys",
            "switch_confirmation_keys",
            "contributing_evidence_refs",
            "seen_evidence_refs",
            "retired_independence_keys",
        ):
            authority = getattr(internal, field)
            code = f"expected_internal_{field}_shape"
            mutations.extend((
                (f"{field}_outer", field, list(authority), code),
                (f"{field}_item", field, (*authority, 1), code),
            ))

        entry = internal.entry_confirmation_keys_by_signal
        mutations.extend((
            (
                "entry_outer",
                "entry_confirmation_keys_by_signal",
                list(entry),
                "expected_internal_entry_shape",
            ),
            (
                "entry_row",
                "entry_confirmation_keys_by_signal",
                (list(entry[0]), *entry[1:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_order",
                "entry_confirmation_keys_by_signal",
                (entry[1], entry[0], *entry[2:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_nested",
                "entry_confirmation_keys_by_signal",
                ((entry[0][0], list(entry[0][1])), *entry[1:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_nested_item",
                "entry_confirmation_keys_by_signal",
                ((entry[0][0], (1,)), *entry[1:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_arity_one",
                "entry_confirmation_keys_by_signal",
                ((entry[0][0],), *entry[1:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_arity_three",
                "entry_confirmation_keys_by_signal",
                ((entry[0][0], entry[0][1], ()), *entry[1:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_signal_type",
                "entry_confirmation_keys_by_signal",
                ((1, entry[0][1]), *entry[1:]),
                "expected_internal_entry_shape",
            ),
            (
                "entry_duplicate_signal",
                "entry_confirmation_keys_by_signal",
                (
                    entry[0],
                    (entry[0][0], entry[1][1]),
                    *entry[2:],
                ),
                "expected_internal_entry_shape",
            ),
            (
                "entry_nested_duplicate",
                "entry_confirmation_keys_by_signal",
                (
                    (
                        entry[0][0],
                        (internal.seen_independence_keys[0],) * 2,
                    ),
                    *entry[1:],
                ),
                "expected_internal_entry_shape",
            ),
        ))

        for field in (
            "internal_incumbent",
            "switch_challenger",
            "last_emitted_selected_signal",
        ):
            mutations.append((
                field,
                field,
                1,
                "expected_internal_scalar_type",
            ))
        for field in (
            "incumbent_tenure",
            "release_streak",
            "accepted_turn_count",
        ):
            mutations.extend((
                (
                    f"{field}_bool",
                    field,
                    True,
                    "expected_internal_counter",
                ),
                (
                    f"{field}_negative",
                    field,
                    -1,
                    "expected_internal_counter",
                ),
            ))
        mutations.extend((
            (
                "last_support_bool",
                "last_emitted_selected_support",
                True,
                "expected_internal_last_support",
            ),
            (
                "last_support_negative",
                "last_emitted_selected_support",
                -1,
                "expected_internal_last_support",
            ),
        ))

        for name, field, value, expected_code in mutations:
            mutated_internal = dataclasses.replace(
                internal,
                **{field: value},
            )
            mutated = dataclasses.replace(
                scenario,
                expected_steps=(
                    dataclasses.replace(
                        accepted,
                        expected_internal=mutated_internal,
                    ),
                ),
            )
            with self.subTest(name=name):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
                        mutated,
                        attempt,
                    )
                self.assertEqual(captured.exception.code, expected_code)


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


class PhaseCTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        self.scenarios = {
            scenario.case_id: scenario
            for scenario in phase_c_contracts.load_and_validate_phase_c_scenarios(
                SCENARIO_PATH,
                self.policy,
            )
        }
        self.tracker = importlib.import_module(
            "scripts.emotion_state_phase_c_temporal_tracker",
        )

    def case(self, case_id: str) -> Any:
        return self.scenarios[case_id]

    def parsed_frame(
        self,
        atoms: list[dict[str, object]],
        *,
        counter: int = 1,
    ) -> PhaseCSyntheticEvidenceFrameV1:
        return parse_phase_c_frame(
            _frame(
                event_id=f"event-{counter}",
                turn_id=f"turn-{counter}",
                turn_sequence=counter,
                atoms=atoms,
            ),
            self.policy,
        )


class PhaseCFixedPointFoldTests(PhaseCTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.explicit_high = parse_phase_c_atom(
            _atom(
                counter=9001,
                evidence_class="unsolicited_explicit_statement",
            ),
            self.policy,
        )
        self.transcript_medium = parse_phase_c_atom(
            _atom(
                counter=9002,
                evidence_class="transcript_meaning",
                quality="medium",
            ),
            self.policy,
        )
        self.acoustic_low = parse_phase_c_atom(
            _atom(
                counter=9003,
                modality="acoustic",
                evidence_class="synthetic_acoustic_symbol",
                quality="low",
            ),
            self.policy,
        )
        self.unusable_proxy = parse_phase_c_atom(
            _atom(
                counter=9004,
                modality="dialogue",
                evidence_class="weak_behavioral_proxy",
                quality="unusable",
            ),
            self.policy,
        )

    def fold_case(self, case_id: str, attempted_step: int) -> Any:
        scenario = self.case(case_id)
        previous = None
        seen_keys: frozenset[str] = frozenset()
        fold = None
        for index, attempt in enumerate(scenario.attempt_order):
            session = next(
                item
                for item in scenario.sessions
                if item.session_alias == attempt.frame_session_alias
            )
            frame = session.frames[attempt.frame_index]
            fold = self.tracker.fold_frame_support(
                previous,
                frame,
                self.policy,
                seen_keys,
            )
            previous = fold.accumulator
            seen_keys = seen_keys | frozenset(fold.accepted_independence_keys)
            if index == attempted_step:
                return fold
        self.fail(f"attempted step is outside case: {attempted_step}")

    def _quality_cap(self, accumulator: Any, signal: str) -> int:
        by_direction = dict(
            dict(accumulator.highest_quality_by_signal_direction)[signal],
        )
        live = [quality for quality in by_direction.values() if quality is not None]
        if not live:
            return 0
        quality = min(
            live,
            key=self.policy["canonical_quality_order"].index,
        )
        return self.policy["total_quality_caps"][quality]

    def _assert_code(
        self,
        expected_code: str,
        previous: Any,
        frame: PhaseCSyntheticEvidenceFrameV1,
        seen_keys: Any = frozenset(),
    ) -> None:
        with self.assertRaises(PhaseCContractError) as captured:
            self.tracker.fold_frame_support(
                previous,
                frame,
                self.policy,
                seen_keys,
            )
        self.assertEqual(captured.exception.code, expected_code)

    def test_atom_units_round_down_exactly(self) -> None:
        self.assertEqual(
            self.tracker.atom_support_units(self.explicit_high, self.policy),
            700,
        )
        self.assertEqual(
            self.tracker.atom_support_units(self.transcript_medium, self.policy),
            337,
        )
        self.assertEqual(
            self.tracker.atom_support_units(self.acoustic_low, self.policy),
            72,
        )
        self.assertEqual(
            self.tracker.atom_support_units(self.unusable_proxy, self.policy),
            0,
        )

    def test_decay_agreement_saturation_and_caps_are_exact(self) -> None:
        self.assertEqual(self.tracker.decay_units(700, self.policy), 560)
        fold = self.fold_case("multimodal_two_turn_entry", attempted_step=0)
        self.assertEqual(
            dict(fold.accumulator.capped_net_support)["frustration"],
            730,
        )
        saturation = self.fold_case("support_saturation", attempted_step=0)
        self.assertEqual(
            dict(saturation.accumulator.gross_supporting_units)["confusion"],
            1000,
        )
        self.assertEqual(
            dict(saturation.accumulator.capped_net_support)["confusion"],
            1000,
        )

    def test_quality_acoustic_and_contradiction_caps_are_exact(self) -> None:
        contradiction = self.fold_case(
            "same_signal_contradiction",
            attempted_step=0,
        )
        accumulator = contradiction.accumulator
        self.assertEqual(
            dict(accumulator.gross_supporting_units)["confusion"],
            1000,
        )
        self.assertEqual(
            dict(accumulator.gross_opposing_units)["confusion"],
            300,
        )
        self.assertEqual(
            dict(accumulator.uncapped_net_support)["confusion"],
            700,
        )
        self.assertEqual(
            dict(accumulator.capped_net_support)["confusion"],
            350,
        )
        acoustic = self.fold_case("acoustic_only_capped", attempted_step=2)
        self.assertEqual(
            dict(acoustic.accumulator.capped_net_support)["hesitation"],
            400,
        )

    def test_one_side_metadata_clears_without_clearing_the_other_side(self) -> None:
        initial = self.parsed_frame(
            [
                _atom(
                    counter=9101,
                    evidence_class="weak_behavioral_proxy",
                    modality="dialogue",
                    quality="high",
                ),
                _atom(
                    counter=9102,
                    direction="opposes",
                    evidence_class="unsolicited_explicit_statement",
                    quality="low",
                ),
            ],
            counter=101,
        )
        empty = self.parsed_frame([], counter=102)
        fold = self.tracker.fold_frame_support(
            None,
            initial,
            self.policy,
            frozenset(),
        )
        self.assertEqual(
            dict(fold.accumulator.gross_supporting_units)["confusion"],
            100,
        )
        self.assertEqual(
            dict(fold.accumulator.gross_opposing_units)["confusion"],
            280,
        )
        self.assertEqual(self._quality_cap(fold.accumulator, "confusion"), 1000)
        for _ in range(17):
            fold = self.tracker.fold_frame_support(
                fold.accumulator,
                empty,
                self.policy,
                frozenset(),
            )
        accumulator = fold.accumulator
        self.assertEqual(
            dict(accumulator.gross_supporting_units)["confusion"],
            0,
        )
        self.assertGreater(
            dict(accumulator.gross_opposing_units)["confusion"],
            0,
        )
        quality = dict(
            dict(accumulator.highest_quality_by_signal_direction)["confusion"],
        )
        self.assertIsNone(quality["supports"])
        self.assertEqual(quality["opposes"], "low")
        provenance = dict(
            dict(accumulator.modality_refs_by_signal_direction)["confusion"],
        )
        self.assertTrue(
            all(not refs for _, refs in dict(provenance["supports"]).items()),
        )
        self.assertEqual(
            dict(provenance["opposes"])["text"],
            (initial.evidence_atoms[1].evidence_ref,),
        )
        self.assertEqual(self._quality_cap(accumulator, "confusion"), 400)

    def test_seen_key_with_fresh_reference_cannot_create_agreement(self) -> None:
        repeated_key = "ind:fixture:already-seen"
        frame = self.parsed_frame(
            [
                _atom(
                    counter=9201,
                    evidence_class="transcript_meaning",
                ),
                _atom(
                    counter=9202,
                    modality="acoustic",
                    evidence_class="synthetic_acoustic_symbol",
                    independence_key=repeated_key,
                ),
            ],
            counter=103,
        )
        fold = self.tracker.fold_frame_support(
            None,
            frame,
            self.policy,
            frozenset({repeated_key}),
        )
        self.assertEqual(
            dict(fold.accumulator.gross_supporting_units)["confusion"],
            450,
        )
        self.assertEqual(
            fold.accepted_evidence_refs,
            tuple(atom.evidence_ref for atom in frame.evidence_atoms),
        )
        self.assertEqual(
            fold.accepted_independence_keys,
            (frame.evidence_atoms[0].independence_key,),
        )
        self.assertEqual(
            fold.contributing_evidence_refs,
            (frame.evidence_atoms[0].evidence_ref,),
        )

    def test_total_quality_caps_are_independent_of_acoustic_cap(self) -> None:
        previous = None
        seen: frozenset[str] = frozenset()
        for offset in range(3):
            frame = self.parsed_frame(
                [
                    _atom(
                        counter=9301 + offset,
                        evidence_class="transcript_meaning",
                        quality="medium",
                    ),
                ],
                counter=110 + offset,
            )
            fold = self.tracker.fold_frame_support(
                previous,
                frame,
                self.policy,
                seen,
            )
            previous = fold.accumulator
            seen |= frozenset(fold.accepted_independence_keys)
        self.assertEqual(
            dict(fold.accumulator.gross_supporting_units)["confusion"],
            821,
        )
        self.assertEqual(
            dict(fold.accumulator.capped_net_support)["confusion"],
            750,
        )

        previous = None
        seen = frozenset()
        for offset in range(2):
            frame = self.parsed_frame(
                [
                    _atom(
                        counter=9401 + offset,
                        evidence_class="unsolicited_explicit_statement",
                        quality="low",
                    ),
                ],
                counter=120 + offset,
            )
            fold = self.tracker.fold_frame_support(
                previous,
                frame,
                self.policy,
                seen,
            )
            previous = fold.accumulator
            seen |= frozenset(fold.accepted_independence_keys)
        self.assertEqual(
            dict(fold.accumulator.gross_supporting_units)["confusion"],
            504,
        )
        self.assertEqual(
            dict(fold.accumulator.capped_net_support)["confusion"],
            400,
        )
        self.assertFalse(fold.acoustic_only)

    def test_same_modality_atoms_do_not_create_agreement_bonus(self) -> None:
        frame = self.parsed_frame(
            [
                _atom(
                    counter=9501,
                    evidence_class="transcript_meaning",
                ),
                _atom(
                    counter=9502,
                    evidence_class="transcript_meaning",
                ),
            ],
            counter=130,
        )
        fold = self.tracker.fold_frame_support(
            None,
            frame,
            self.policy,
            frozenset(),
        )
        self.assertEqual(
            dict(fold.accumulator.gross_supporting_units)["confusion"],
            900,
        )

    def test_dense_metadata_and_zero_unit_audio_flags_are_exact(self) -> None:
        frame = self.parsed_frame(
            [
                _atom(
                    counter=9601,
                    modality="acoustic",
                    evidence_class="synthetic_acoustic_symbol",
                    quality="unusable",
                ),
            ],
            counter=140,
        )
        fold = self.tracker.fold_frame_support(
            None,
            frame,
            self.policy,
            frozenset(),
        )
        self.assertEqual(
            tuple(key for key, _ in fold.accumulator.gross_supporting_units),
            tuple(self.policy["canonical_signal_order"]),
        )
        self.assertTrue(fold.low_audio_quality_only)
        self.assertFalse(fold.missing_input)
        self.assertFalse(fold.acoustic_only)
        self.assertEqual(
            fold.accepted_evidence_refs,
            (frame.evidence_atoms[0].evidence_ref,),
        )
        self.assertEqual(
            fold.accepted_independence_keys,
            (frame.evidence_atoms[0].independence_key,),
        )
        self.assertEqual(fold.contributing_evidence_refs, ())
        self.assertTrue(
            all(not keys for _, keys in fold.confirming_keys_by_signal),
        )
        for _, directions in (
            fold.accumulator.highest_quality_by_signal_direction
        ):
            self.assertEqual(
                directions,
                (("supports", None), ("opposes", None)),
            )
        for _, directions in fold.accumulator.modality_refs_by_signal_direction:
            for _, modalities in directions:
                self.assertEqual(
                    modalities,
                    (("text", ()), ("dialogue", ()), ("acoustic", ())),
                )

    def test_direct_dataclass_and_seen_key_mutations_fail_closed_exactly(self) -> None:
        frame = self.parsed_frame(
            [
                _atom(
                    counter=9701,
                    evidence_class="unsolicited_explicit_statement",
                ),
            ],
            counter=150,
        )
        valid = self.tracker.fold_frame_support(
            None,
            frame,
            self.policy,
            frozenset(),
        ).accumulator
        empty = self.parsed_frame([], counter=151)

        self._assert_code(
            "accumulator_field_type",
            dataclasses.replace(
                valid,
                gross_supporting_units=list(valid.gross_supporting_units),
            ),
            empty,
        )
        self._assert_code(
            "accumulator_projection",
            dataclasses.replace(
                valid,
                capped_net_support=(
                    ("confusion", 699),
                    *valid.capped_net_support[1:],
                ),
            ),
            empty,
        )
        self._assert_code(
            "accumulator_side_metadata",
            dataclasses.replace(
                valid,
                highest_quality_by_signal_direction=(
                    (
                        "confusion",
                        (("supports", None), ("opposes", None)),
                    ),
                    *valid.highest_quality_by_signal_direction[1:],
                ),
            ),
            empty,
        )
        self._assert_code(
            "accumulator_modality_order",
            dataclasses.replace(
                valid,
                modality_refs_by_signal_direction=(
                    (
                        "confusion",
                        (
                            (
                                "supports",
                                (
                                    ("dialogue", ()),
                                    ("text", (frame.evidence_atoms[0].evidence_ref,)),
                                    ("acoustic", ()),
                                ),
                            ),
                            valid.modality_refs_by_signal_direction[0][1][1],
                        ),
                    ),
                    *valid.modality_refs_by_signal_direction[1:],
                ),
            ),
            empty,
        )
        self._assert_code(
            "seen_independence_keys_type",
            valid,
            empty,
            set(),
        )
        invalid_frame = dataclasses.replace(
            empty,
            evidence_atoms=list(empty.evidence_atoms),
        )
        self._assert_code(
            "frame_field_type",
            valid,
            invalid_frame,
        )

    def test_provenance_preserves_bucket_history_and_canonical_union(self) -> None:
        first = self.parsed_frame(
            [
                _atom(
                    counter=9999,
                    evidence_class="transcript_meaning",
                ),
            ],
            counter=160,
        )
        second = self.parsed_frame(
            [
                _atom(
                    counter=9800,
                    evidence_class="transcript_meaning",
                ),
            ],
            counter=161,
        )
        first_fold = self.tracker.fold_frame_support(
            None,
            first,
            self.policy,
            frozenset(),
        )
        second_fold = self.tracker.fold_frame_support(
            first_fold.accumulator,
            second,
            self.policy,
            frozenset(first_fold.accepted_independence_keys),
        )
        expected = (
            first.evidence_atoms[0].evidence_ref,
            second.evidence_atoms[0].evidence_ref,
        )
        confusion = dict(
            dict(
                second_fold.accumulator.modality_refs_by_signal_direction,
            )["confusion"],
        )
        self.assertEqual(dict(confusion["supports"])["text"], expected)
        self.assertEqual(second_fold.contributing_evidence_refs, expected)

    def test_all_ordinary_folds_match_frozen_task3_projections(self) -> None:
        checked = 0
        for scenario in self.scenarios.values():
            accumulators: dict[str, Any] = {}
            seen_by_session: dict[str, frozenset[str]] = {}
            for index, (attempt, expected) in enumerate(
                zip(scenario.attempt_order, scenario.expected_steps),
            ):
                if expected.disposition != "accepted":
                    continue
                if (
                    scenario.case_id == "latest_turn_correction_replay"
                    and index == 1
                ):
                    continue
                session = next(
                    item
                    for item in scenario.sessions
                    if item.session_alias == attempt.frame_session_alias
                )
                frame = session.frames[attempt.frame_index]
                state_alias = attempt.state_session_alias
                seen = seen_by_session.get(state_alias, frozenset())
                fold = self.tracker.fold_frame_support(
                    accumulators.get(state_alias),
                    frame,
                    self.policy,
                    seen,
                )
                projection = expected.expected_internal
                with self.subTest(
                    case_id=scenario.case_id,
                    attempted_step=index,
                ):
                    self.assertEqual(
                        fold.accumulator.gross_supporting_units,
                        projection.gross_supporting_units,
                    )
                    self.assertEqual(
                        fold.accumulator.gross_opposing_units,
                        projection.gross_opposing_units,
                    )
                    self.assertEqual(
                        fold.accumulator.uncapped_net_support,
                        projection.uncapped_net_support,
                    )
                    self.assertEqual(
                        fold.accumulator.capped_net_support,
                        projection.capped_net_support,
                    )
                    self.assertEqual(
                        fold.accumulator.contradictory_signals,
                        projection.contradictory_signals,
                    )
                    self.assertEqual(
                        fold.contributing_evidence_refs,
                        projection.contributing_evidence_refs,
                    )
                accumulators[state_alias] = fold.accumulator
                seen_by_session[state_alias] = seen | frozenset(
                    fold.accepted_independence_keys,
                )
                checked += 1
        self.assertEqual(checked, 51)

    def test_fold_validator_rejects_key_order_and_confirmation_bypasses(self) -> None:
        frame = self.parsed_frame(
            [
                _atom(
                    counter=9811,
                    evidence_class="transcript_meaning",
                ),
                _atom(
                    counter=9812,
                    modality="dialogue",
                    evidence_class="dialogue_context",
                ),
                _atom(
                    counter=9813,
                    modality="acoustic",
                    evidence_class="synthetic_acoustic_symbol",
                    quality="unusable",
                ),
            ],
            counter=170,
        )
        fold = self.tracker.fold_frame_support(
            None,
            frame,
            self.policy,
            frozenset(),
        )
        first_key, second_key, unusable_key = (
            atom.independence_key for atom in frame.evidence_atoms
        )

        def confirming(
            confusion: tuple[str, ...],
            disengagement: tuple[str, ...] = (),
        ) -> tuple[tuple[str, tuple[str, ...]], ...]:
            return (
                ("confusion", confusion),
                ("disengagement", disengagement),
                *fold.confirming_keys_by_signal[2:],
            )

        cases = (
            (
                dataclasses.replace(
                    fold,
                    accepted_independence_keys=tuple(
                        reversed(fold.accepted_independence_keys),
                    ),
                ),
                "fold_accepted_key_order",
            ),
            (
                dataclasses.replace(
                    fold,
                    confirming_keys_by_signal=confirming((second_key,)),
                ),
                "fold_confirming_key_order",
            ),
            (
                dataclasses.replace(
                    fold,
                    confirming_keys_by_signal=confirming((), (first_key,)),
                ),
                "fold_confirming_key_order",
            ),
            (
                dataclasses.replace(
                    fold,
                    confirming_keys_by_signal=confirming((unusable_key,)),
                ),
                "fold_confirming_key_order",
            ),
        )
        for mutated, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.validate_phase_c_frame_fold(
                        mutated,
                        frame,
                        self.policy,
                    )
                self.assertEqual(captured.exception.code, expected_code)

    def test_nested_string_subclass_labels_fail_closed_exactly(self) -> None:
        class StringSubclass(str):
            pass

        frame = self.parsed_frame(
            [
                _atom(
                    counter=9821,
                    evidence_class="unsolicited_explicit_statement",
                ),
            ],
            counter=180,
        )
        fold = self.tracker.fold_frame_support(
            None,
            frame,
            self.policy,
            frozenset(),
        )
        accumulator = fold.accumulator
        quality = accumulator.highest_quality_by_signal_direction
        provenance = accumulator.modality_refs_by_signal_direction
        contradiction = self.fold_case(
            "same_signal_contradiction",
            attempted_step=0,
        ).accumulator
        cases = (
            (
                dataclasses.replace(
                    accumulator,
                    highest_quality_by_signal_direction=(
                        (StringSubclass("confusion"), quality[0][1]),
                        *quality[1:],
                    ),
                ),
                "accumulator_signal_order",
            ),
            (
                dataclasses.replace(
                    accumulator,
                    highest_quality_by_signal_direction=(
                        (
                            "confusion",
                            (
                                (
                                    StringSubclass("supports"),
                                    quality[0][1][0][1],
                                ),
                                quality[0][1][1],
                            ),
                        ),
                        *quality[1:],
                    ),
                ),
                "accumulator_direction_order",
            ),
            (
                dataclasses.replace(
                    accumulator,
                    modality_refs_by_signal_direction=(
                        (StringSubclass("confusion"), provenance[0][1]),
                        *provenance[1:],
                    ),
                ),
                "accumulator_signal_order",
            ),
            (
                dataclasses.replace(
                    accumulator,
                    modality_refs_by_signal_direction=(
                        (
                            "confusion",
                            (
                                (
                                    StringSubclass("supports"),
                                    provenance[0][1][0][1],
                                ),
                                provenance[0][1][1],
                            ),
                        ),
                        *provenance[1:],
                    ),
                ),
                "accumulator_direction_order",
            ),
            (
                dataclasses.replace(
                    accumulator,
                    modality_refs_by_signal_direction=(
                        (
                            "confusion",
                            (
                                (
                                    "supports",
                                    (
                                        (
                                            StringSubclass("text"),
                                            provenance[0][1][0][1][0][1],
                                        ),
                                        *provenance[0][1][0][1][1:],
                                    ),
                                ),
                                provenance[0][1][1],
                            ),
                        ),
                        *provenance[1:],
                    ),
                ),
                "accumulator_modality_order",
            ),
            (
                dataclasses.replace(
                    contradiction,
                    contradictory_signals=(
                        StringSubclass("confusion"),
                    ),
                ),
                "accumulator_contradiction",
            ),
        )
        empty = self.parsed_frame([], counter=181)
        for mutated, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                self._assert_code(expected_code, mutated, empty)

        confirming_signal = dataclasses.replace(
            fold,
            confirming_keys_by_signal=(
                (
                    StringSubclass("confusion"),
                    fold.confirming_keys_by_signal[0][1],
                ),
                *fold.confirming_keys_by_signal[1:],
            ),
        )
        confirming_key = dataclasses.replace(
            fold,
            confirming_keys_by_signal=(
                (
                    "confusion",
                    (
                        StringSubclass(
                            fold.confirming_keys_by_signal[0][1][0],
                        ),
                    ),
                ),
                *fold.confirming_keys_by_signal[1:],
            ),
        )
        for mutated in (confirming_signal, confirming_key):
            with self.subTest(mutated=repr(mutated.confirming_keys_by_signal[0])):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.validate_phase_c_frame_fold(
                        mutated,
                        frame,
                        self.policy,
                    )
                self.assertEqual(
                    captured.exception.code,
                    "fold_confirming_key_order",
                )


class PhaseCHysteresisAndOutputTests(PhaseCTestCase):
    """Task 5 behavioral and semantic-contract coverage.

    The expected internal values are frozen scenario authority, never outputs
    generated by this test module.
    """

    def run_case(self, case_id: str) -> Any:
        scenario = self.case(case_id)
        self.assertEqual(len(scenario.sessions), 1)
        return self.tracker.replay_validated_frames(
            scenario.sessions[0].frames,
            self.policy,
        )

    def test_explicit_entry_and_three_turn_transcript_entry(self) -> None:
        explicit = self.run_case("explicit_confusion_entry")
        self.assertEqual(explicit.outputs[-1]["selected_policy_signal"], "confusion")
        transcript = self.run_case("transcript_three_turn_entry")
        self.assertEqual(
            [step.hysteresis.internal_incumbent for step in transcript.states],
            [None, None, "confusion"],
        )

    def test_release_and_switch_are_exact(self) -> None:
        release = self.run_case("release_after_two_below_threshold")
        self.assertEqual(
            [step.hysteresis.internal_incumbent for step in release.states],
            ["frustration", "frustration", "frustration", "frustration", "frustration", None],
        )
        switch = self.run_case("switch_after_two_confirmations")
        self.assertEqual(
            [step.hysteresis.internal_incumbent for step in switch.states],
            ["frustration", "frustration", "frustration", "confusion"],
        )

    def test_output_is_unapproved_not_inferable_and_monotonic_vocabulary_only(self) -> None:
        result = self.run_case("explicit_frustration_entry").outputs[-1]
        self.assertFalse(result["runtime_approved"])
        self.assertEqual(result["valence_estimate"], "not_inferable")
        self.assertEqual(result["activation_estimate"], "not_inferable")
        self.assertEqual(result["engagement_estimate"], "not_inferable")
        self.assertEqual(
            set(result["blocked_policy_effects"]),
            REQUIRED_BLOCKED_POLICY_EFFECTS,
        )

    def test_frozen_internal_hysteresis_and_emission_fields_match_authority(self) -> None:
        for case_id in (
            "explicit_confusion_entry",
            "transcript_three_turn_entry",
            "release_after_two_below_threshold",
            "switch_after_two_confirmations",
            "entry_tie_abstains",
            "incumbent_survives_unqualified_challenger",
        ):
            scenario = self.case(case_id)
            replay = self.run_case(case_id)
            for state, expected in zip(replay.states, scenario.expected_steps):
                with self.subTest(case_id=case_id, turn=state.watermark.last_turn_sequence):
                    self.assertEqual(expected.disposition, "accepted")
                    frozen = expected.expected_internal
                    self.assertEqual(
                        state.hysteresis.entry_confirmation_keys_by_signal,
                        frozen.entry_confirmation_keys_by_signal,
                    )
                    self.assertEqual(state.hysteresis.switch_challenger, frozen.switch_challenger)
                    self.assertEqual(state.hysteresis.switch_confirmation_keys, frozen.switch_confirmation_keys)
                    self.assertEqual(state.hysteresis.release_streak, frozen.release_streak)
                    self.assertEqual(state.hysteresis.incumbent_tenure, frozen.incumbent_tenure)
                    self.assertEqual(state.last_emitted_selected_signal, frozen.last_emitted_selected_signal)
                    self.assertEqual(state.last_emitted_selected_support, frozen.last_emitted_selected_support)

    def test_perceived_nonobjects_fail_before_field_access(self) -> None:
        replay = self.run_case("explicit_confusion_entry")
        state = replay.final_state
        frame = self.case("explicit_confusion_entry").sessions[0].frames[-1]
        fold = self.tracker.fold_frame_support(None, frame, self.policy, frozenset())
        context = self.tracker.PhaseCProjectionContextV1(None, None, fold, frame)
        for value in (None, [], "", 0, False):
            with self.subTest(value=repr(value)):
                with self.assertRaises(phase_c_contracts.PhaseCOutputSemanticError) as captured:
                    phase_c_contracts.validate_phase_c_perceived_state(value, state, context, self.policy)
                self.assertEqual(captured.exception.code, "perceived_not_object")

    def test_output_field_mutations_fail_closed_in_stable_order(self) -> None:
        replay = self.run_case("explicit_confusion_entry")
        payload = replay.outputs[-1]
        state = replay.final_state
        frame = self.case("explicit_confusion_entry").sessions[0].frames[-1]
        fold = self.tracker.fold_frame_support(None, frame, self.policy, frozenset())
        context = self.tracker.PhaseCProjectionContextV1(None, None, fold, frame)
        wrong = {
            "call_session_id": None, "campaign_profile_id": None,
            "campaign_profile_version": None, "turn_id": None,
            "turn_sequence": "0", "valence_estimate": None,
            "activation_estimate": None, "engagement_estimate": None,
            "operational_signals": (), "confidence_by_signal": (),
            "selected_policy_signal": None,
            "selected_signal_confidence_bucket": None,
            "overall_evidence_quality": None, "trajectory": None,
            "evidence_refs": (), "signal_provenance_by_modality": (),
            "allowed_policy_effects": (), "blocked_policy_effects": (),
            "abstained": 0, "abstention_reasons": (),
            "evidence_policy_version": None, "runtime_approved": 0,
        }
        self.assertEqual(set(wrong), set(payload))
        for field, value in wrong.items():
            for label, mutated in (
                ("missing", {key: item for key, item in payload.items() if key != field}),
                ("wrong_type", dict(payload, **{field: value})),
            ):
                with self.subTest(field=field, label=label):
                    with self.assertRaises(phase_c_contracts.PhaseCOutputSemanticError) as captured:
                        phase_c_contracts.validate_phase_c_perceived_state(mutated, state, context, self.policy)
                    self.assertEqual(
                        captured.exception.code,
                        "perceived_field_set" if label == "missing" else "perceived_field_type",
                    )
        extra = dict(payload, extra="blocked")
        with self.assertRaises(phase_c_contracts.PhaseCOutputSemanticError) as captured:
            phase_c_contracts.validate_phase_c_perceived_state(extra, state, context, self.policy)
        self.assertEqual(captured.exception.code, "perceived_field_set")

    def test_semantic_mutations_fail_closed(self) -> None:
        replay = self.run_case("explicit_confusion_entry")
        payload = replay.outputs[-1]
        state = replay.final_state
        frame = self.case("explicit_confusion_entry").sessions[0].frames[-1]
        fold = self.tracker.fold_frame_support(None, frame, self.policy, frozenset())
        context = self.tracker.PhaseCProjectionContextV1(None, None, fold, frame)
        mutations = (
            ("signal_projection", dict(payload, selected_policy_signal="interest")),
            ("confidence_projection", dict(payload, confidence_by_signal={})),
            ("confidence_bucket", dict(payload, selected_signal_confidence_bucket="low")),
            ("provenance_projection", dict(payload, signal_provenance_by_modality={})),
            ("evidence_ref_union", dict(payload, evidence_refs=[])),
            ("allowed_effects", dict(payload, allowed_policy_effects=["preserve"])),
            ("noncanonical_output_order", dict(payload, blocked_policy_effects=list(reversed(payload["blocked_policy_effects"])))),
            ("inferable_estimate", dict(payload, valence_estimate="inferable")),
            (
                "evidence_policy_version",
                dict(
                    payload,
                    evidence_policy_version="emotion-state-evidence-v1",
                ),
            ),
            ("runtime_approved", dict(payload, runtime_approved=True)),
        )
        for code, mutated in mutations:
            with self.subTest(code=code):
                with self.assertRaises(phase_c_contracts.PhaseCOutputSemanticError) as captured:
                    phase_c_contracts.validate_phase_c_perceived_state(mutated, state, context, self.policy)
                self.assertEqual(captured.exception.code, code)


class PhaseCTaskFiveBoundaryCorrectionTests(PhaseCTestCase):
    """Direct Task 5 boundaries; these builders never invoke fold arithmetic."""

    def run_case(self, case_id: str) -> Any:
        scenario = self.case(case_id)
        self.assertEqual(len(scenario.sessions), 1)
        return self.tracker.replay_validated_frames(
            scenario.sessions[0].frames,
            self.policy,
        )

    def _frame_for(self, *, signal: str = "confusion", key: str = "ind:fixture:5:1", explicit: bool = False, sequence: int = 0) -> PhaseCSyntheticEvidenceFrameV1:
        return self.parsed_frame([_atom(
            counter=880000 + sequence,
            signal=signal,
            independence_key=key,
            evidence_class=("unsolicited_explicit_statement" if explicit else "transcript_meaning"),
        )], counter=880000 + sequence)

    def _dense_fold(self, frame: PhaseCSyntheticEvidenceFrameV1, nets: dict[str, int], *, confirming: str | None = None, low_audio: bool = False, missing: bool = False) -> Any:
        signals = tuple(self.policy["canonical_signal_order"])
        directions = tuple(self.policy["canonical_direction_order"])
        modalities = tuple(self.policy["canonical_modality_order"])
        refs = {
            signal: (
                frame.evidence_atoms[0].evidence_ref
                if signal == frame.evidence_atoms[0].operational_signal
                else f"evidence:uuid:00000000-0000-4000-8000-{880100 + signals.index(signal):012d}"
            )
            for signal in signals
        }
        accumulator = phase_c_contracts.PhaseCSignalAccumulatorV1(
            gross_supporting_units=tuple((signal, nets[signal]) for signal in signals),
            gross_opposing_units=tuple((signal, 0) for signal in signals),
            uncapped_net_support=tuple((signal, nets[signal]) for signal in signals),
            capped_net_support=tuple((signal, nets[signal]) for signal in signals),
            highest_quality_by_signal_direction=tuple(
                (signal, (("supports", "high" if nets[signal] else None), ("opposes", None)))
                for signal in signals
            ),
            contradictory_signals=(),
            modality_refs_by_signal_direction=tuple(
                (signal, tuple(
                    (direction, tuple(
                        (modality, (refs[signal],) if direction == "supports" and modality == "text" and nets[signal] else ())
                        for modality in modalities
                    )) for direction in directions
                )) for signal in signals
            ),
        )
        keys = tuple(
            (signal, (confirming,) if signal == frame.evidence_atoms[0].operational_signal and confirming is not None else ())
            for signal in signals
        )
        return phase_c_contracts.PhaseCFrameFoldV1(
            accumulator=accumulator,
            accepted_evidence_refs=(frame.evidence_atoms[0].evidence_ref,),
            contributing_evidence_refs=tuple(refs[signal] for signal in signals if nets[signal]),
            accepted_independence_keys=(confirming,) if confirming is not None else (),
            confirming_keys_by_signal=keys,
            acoustic_only=False,
            missing_input=missing,
            low_audio_quality_only=low_audio,
        )

    def _hysteresis(self, incumbent: str | None, *, tenure: int = 0, entries: dict[str, tuple[str, ...]] | None = None, challenger: str | None = None, switch_keys: tuple[str, ...] = (), release: int = 0) -> Any:
        return phase_c_contracts.PhaseCHysteresisV1(
            incumbent, tenure,
            tuple((signal, (entries or {}).get(signal, ())) for signal in self.policy["canonical_signal_order"]),
            challenger, switch_keys, release,
        )

    def _state(self, frame: PhaseCSyntheticEvidenceFrameV1, fold: Any, hysteresis: Any, *, prior: str | None = None, support: int | None = None) -> Any:
        watermark = phase_c_contracts.validate_phase_c_event_identity(
            frame, phase_c_contracts.initial_phase_c_watermark(frame),
        )
        state = phase_c_contracts.PhaseCTemporalSessionStateV1(
            "PhaseCTemporalSessionStateV1", self.policy["policy_id"],
            sha256_bytes(canonical_json_bytes(self.policy)), frame.call_session_id,
            frame.campaign_profile_id, frame.campaign_profile_version, watermark,
            (frame,), ((frame.event_id, fold.accepted_evidence_refs, fold.accepted_independence_keys),),
            fold.accumulator, hysteresis, fold.accepted_evidence_refs,
            fold.accepted_independence_keys, (), fold.contributing_evidence_refs,
            1, prior, support,
        )
        phase_c_contracts.validate_phase_c_temporal_state(state, self.policy)
        return state

    def _projection_fixture(self, *, nets: dict[str, int] | None = None, incumbent: str = "confusion", prior: str | None = None, support: int | None = None, sequence: int = 0) -> tuple[dict[str, Any], Any, Any]:
        frame = self._frame_for(signal=incumbent, key=f"ind:fixture:5:{sequence + 1}", sequence=sequence)
        dense_nets = {signal: 0 for signal in self.policy["canonical_signal_order"]}
        dense_nets.update(nets or {incumbent: 800, "interest": 200})
        fold = self._dense_fold(frame, dense_nets, confirming=frame.evidence_atoms[0].independence_key)
        provisional = self._state(frame, fold, self._hysteresis(incumbent, tenure=1), prior=prior, support=support)
        context = phase_c_contracts.PhaseCProjectionContextV1(prior, support, fold, frame)
        payload = self.tracker.project_perceived_customer_state(provisional, context, self.policy)
        selected = payload["selected_policy_signal"]
        final = dataclasses.replace(
            provisional,
            last_emitted_selected_signal=None if selected == "none" else selected,
            last_emitted_selected_support=None if selected == "none" else dense_nets[selected],
        )
        return payload, final, context

    def _semantic_code(self, payload: object, state: Any, context: Any) -> str:
        with self.assertRaises(phase_c_contracts.PhaseCOutputSemanticError) as captured:
            phase_c_contracts.validate_phase_c_perceived_state(payload, state, context, self.policy)
        return captured.exception.code

    def test_every_applicable_frozen_output_is_byte_authoritative(self) -> None:
        def is_task_five_replay_applicable(scenario: Any) -> bool:
            if len(scenario.sessions) != 1:
                return False
            frames = scenario.sessions[0].frames
            if not frames or not scenario.expected_steps:
                return False
            if any(step.disposition != "accepted" for step in scenario.expected_steps):
                return False
            first = frames[0]
            identity = (
                first.call_session_id,
                first.campaign_profile_id,
                first.campaign_profile_version,
            )
            if any(frame.input_revision != 0 for frame in frames):
                return False
            if any(
                (
                    frame.call_session_id,
                    frame.campaign_profile_id,
                    frame.campaign_profile_version,
                ) != identity
                for frame in frames
            ):
                return False
            if any(
                later.turn_sequence <= earlier.turn_sequence
                for earlier, later in zip(frames, frames[1:])
            ):
                return False
            turn_ids = tuple(frame.turn_id for frame in frames)
            event_ids = tuple(frame.event_id for frame in frames)
            evidence_refs = tuple(
                atom.evidence_ref
                for frame in frames
                for atom in frame.evidence_atoms
            )
            return (
                len(turn_ids) == len(set(turn_ids))
                and len(event_ids) == len(set(event_ids))
                and len(evidence_refs) == len(set(evidence_refs))
            )

        applicable = tuple(
            scenario
            for scenario in self.scenarios.values()
            if is_task_five_replay_applicable(scenario)
        )
        self.assertEqual(len(applicable), 20)
        self.assertIn(
            "canonical_replay_bytes",
            {scenario.case_id for scenario in applicable},
        )
        for scenario in applicable:
            case_id = scenario.case_id
            scenario = self.case(case_id)
            replay = self.run_case(case_id)
            for actual_state, actual_output, expected in zip(replay.states, replay.outputs, scenario.expected_steps):
                frozen = expected.expected_internal
                frozen_output = json.loads(expected.expected_output_bytes.decode("utf-8"))
                with self.subTest(case_id=case_id, turn=actual_state.watermark.last_turn_sequence):
                    self.assertEqual(actual_state.hysteresis.entry_confirmation_keys_by_signal, frozen.entry_confirmation_keys_by_signal)
                    self.assertEqual(actual_state.hysteresis.switch_challenger, frozen.switch_challenger)
                    self.assertEqual(actual_state.hysteresis.switch_confirmation_keys, frozen.switch_confirmation_keys)
                    self.assertEqual(actual_state.hysteresis.release_streak, frozen.release_streak)
                    self.assertEqual(actual_state.hysteresis.incumbent_tenure, frozen.incumbent_tenure)
                    self.assertEqual(
                        canonical_json_bytes(actual_output),
                        expected.expected_output_bytes,
                    )
                    for field in ("confidence_by_signal", "signal_provenance_by_modality", "evidence_refs", "overall_evidence_quality", "trajectory", "abstention_reasons"):
                        self.assertEqual(actual_output[field], frozen_output[field])

    def test_semantic_mutation_inventory_and_order(self) -> None:
        payload, state, context = self._projection_fixture()
        mutations = (
            ("signal_projection", dict(payload, operational_signals=["possible_interest"])),
            ("signal_projection", dict(payload, operational_signals=["none", "confusion"])),
            ("confidence_projection", dict(payload, confidence_by_signal={"confusion": 0.8})),
            ("confidence_projection", dict(payload, confidence_by_signal={"confusion": 0.7, "possible_interest": 0.2})),
            ("provenance_projection", dict(payload, signal_provenance_by_modality={"confusion": {"text": payload["evidence_refs"]}})),
            ("noncanonical_output_order", dict(payload, evidence_refs=list(reversed(payload["evidence_refs"])))),
            ("noncanonical_output_order", dict(payload, operational_signals=list(reversed(payload["operational_signals"])))),
            ("noncanonical_output_order", dict(payload, evidence_refs=list(reversed(payload["evidence_refs"])))),
            ("noncanonical_output_order", dict(payload, allowed_policy_effects=list(reversed(payload["allowed_policy_effects"])))),
            ("noncanonical_output_order", dict(payload, blocked_policy_effects=list(reversed(payload["blocked_policy_effects"])))),
        )
        for code, mutated in mutations:
            with self.subTest(code=code, payload=mutated):
                self.assertEqual(self._semantic_code(mutated, state, context), code)
        abstained = dict(payload, selected_policy_signal="none", operational_signals=["none"], confidence_by_signal={}, signal_provenance_by_modality={}, evidence_refs=[], allowed_policy_effects=["preserve"], abstained=True, abstention_reasons=[])
        self.assertEqual(self._semantic_code(abstained, state, context), "signal_projection")

    def test_semantic_abstention_effect_estimate_and_reason_mutations(self) -> None:
        payload, state, context = self._projection_fixture()
        cases = (
            ("inferable_estimate", dict(payload, valence_estimate="inferable")),
            ("inferable_estimate", dict(payload, activation_estimate="inferable")),
            ("inferable_estimate", dict(payload, engagement_estimate="inferable")),
            ("forbidden_abstention_reason", dict(payload, abstention_reasons=["stale_input"])),
            ("forbidden_abstention_reason", dict(payload, abstention_reasons=["phase_a_no_audio"])),
            ("runtime_approved", dict(payload, runtime_approved=True)),
            ("blocked_effects", dict(payload, blocked_policy_effects=payload["blocked_policy_effects"][:-1])),
        )
        for code, mutated in cases:
            with self.subTest(code=code):
                self.assertEqual(self._semantic_code(mutated, state, context), code)

    def test_exact_thresholds_hysteresis_visibility_and_confidence(self) -> None:
        nets = {signal: 0 for signal in self.policy["canonical_signal_order"]}
        frame = self._frame_for(explicit=True)
        for net, incumbent in ((550, "confusion"), (549, None)):
            current = dict(nets, confusion=net)
            fold = self._dense_fold(frame, current, confirming=frame.evidence_atoms[0].independence_key)
            result = self.tracker.update_hysteresis(None, fold, frame, self.policy)
            with self.subTest(entry=net): self.assertEqual(result.internal_incumbent, incumbent)
        for net, visible in ((200, ["confusion"]), (199, ["none"])):
            payload, _, _ = self._projection_fixture(nets=dict(nets, confusion=net))
            with self.subTest(visibility=net): self.assertEqual(payload["operational_signals"], visible)
        for net, bucket in ((549, "low"), (550, "medium"), (749, "medium"), (750, "high")):
            payload, _, _ = self._projection_fixture(nets=dict(nets, confusion=net))
            with self.subTest(confidence=net): self.assertEqual(payload["selected_signal_confidence_bucket"], bucket)

    def test_release_switch_advantage_and_tie_boundaries(self) -> None:
        nets = {signal: 0 for signal in self.policy["canonical_signal_order"]}
        frame = self._frame_for(signal="confusion", key="ind:fixture:5:new", sequence=1)
        prev_frame = self._frame_for(signal="frustration", key="ind:fixture:5:old", sequence=0)
        previous = self._state(prev_frame, self._dense_fold(prev_frame, dict(nets, frustration=500), confirming=prev_frame.evidence_atoms[0].independence_key), self._hysteresis("frustration", tenure=3, challenger="confusion", switch_keys=("ind:fixture:5:old",)))
        stays = self.tracker.update_hysteresis(previous, self._dense_fold(frame, dict(nets, frustration=350), confirming=None), frame, self.policy)
        self.assertEqual((stays.internal_incumbent, stays.release_streak), ("frustration", 0))
        releases = self.tracker.update_hysteresis(dataclasses.replace(previous, hysteresis=self._hysteresis("frustration", tenure=3, release=1)), self._dense_fold(frame, dict(nets, frustration=349), confirming=None), frame, self.policy)
        self.assertEqual((releases.internal_incumbent, releases.release_streak), (None, 0))
        for challenger, incumbent, expected in ((650, 499, "confusion"), (649, 499, "frustration"), (700, 550, "confusion"), (700, 551, "frustration")):
            fold = self._dense_fold(frame, dict(nets, confusion=challenger, frustration=incumbent), confirming=frame.evidence_atoms[0].independence_key)
            result = self.tracker.update_hysteresis(previous, fold, frame, self.policy)
            with self.subTest(challenger=challenger, incumbent=incumbent): self.assertEqual(result.internal_incumbent, expected)
        tied = self.tracker.update_hysteresis(previous, self._dense_fold(frame, dict(nets, confusion=650, disengagement=650, frustration=500), confirming=frame.evidence_atoms[0].independence_key), frame, self.policy)
        self.assertEqual((tied.switch_challenger, tied.switch_confirmation_keys), (None, ()))

    def test_direct_trajectory_boundaries(self) -> None:
        for signal, delta, expected in (("interest", 100, "improving"), ("interest", -100, "worsening"), ("confusion", 100, "worsening"), ("confusion", -100, "improving"), ("interest", 99, "stable"), ("confusion", -99, "stable")):
            current = 700
            payload, _, _ = self._projection_fixture(nets={signal: current}, incumbent=signal, prior=signal, support=current - delta)
            with self.subTest(signal=signal, delta=delta): self.assertEqual(payload["trajectory"], expected)

    def test_replay_preconditions_and_hysteresis_cross_fields_fail_closed(self) -> None:
        frame = self._frame_for()
        with self.assertRaises(PhaseCContractError) as captured:
            self.tracker.replay_validated_frames((), self.policy)
        self.assertEqual(captured.exception.code, "replay_frames")
        correction = dataclasses.replace(frame, input_revision=1)
        with self.assertRaises(PhaseCContractError) as captured:
            self.tracker.replay_validated_frames((correction,), self.policy)
        self.assertEqual(captured.exception.code, "replay_correction_not_supported")
        for malformed in (
            self._hysteresis(None, tenure=1),
            self._hysteresis(None, challenger="confusion"),
            self._hysteresis("confusion", tenure=0),
            self._hysteresis("confusion", tenure=1, entries={"confusion": ("ind:fixture:5:x",)}),
        ):
            with self.subTest(malformed=malformed):
                with self.assertRaises(PhaseCContractError):
                    phase_c_contracts.validate_phase_c_hysteresis(malformed, self.policy)

    def test_nested_exact_types_fail_closed(self) -> None:
        class StringSubclass(str):
            pass
        payload, state, context = self._projection_fixture()
        nested_key = StringSubclass("confusion")
        cases = (
            ("perceived_field_type", dict(payload, confidence_by_signal={nested_key: 0.8, "possible_interest": 0.2})),
            ("perceived_field_type", dict(payload, confidence_by_signal={"confusion": 0.8, "possible_interest": 0})),
            ("perceived_field_type", dict(payload, signal_provenance_by_modality={nested_key: payload["signal_provenance_by_modality"]["confusion"], "possible_interest": payload["signal_provenance_by_modality"]["possible_interest"]})),
        )
        for code, mutated in cases:
            with self.subTest(code=code):
                self.assertEqual(self._semantic_code(mutated, state, context), code)

    def _last_replay_fixture(self, case_id: str) -> tuple[dict[str, Any], Any, Any]:
        scenario = self.case(case_id)
        frames = scenario.sessions[0].frames
        replay = self.run_case(case_id)
        previous = replay.states[-2] if len(replay.states) > 1 else None
        frame = frames[-1]
        fold = self.tracker.fold_frame_support(
            None if previous is None else previous.accumulator,
            frame,
            self.policy,
            frozenset() if previous is None else frozenset(previous.seen_independence_keys),
        )
        context = phase_c_contracts.PhaseCProjectionContextV1(
            None if previous is None else previous.last_emitted_selected_signal,
            None if previous is None else previous.last_emitted_selected_support,
            fold,
            frame,
        )
        return replay.outputs[-1], replay.final_state, context

    def test_final_nested_type_inventory_precedes_all_semantic_operations(self) -> None:
        class StringSubclass(str):
            pass

        class FloatSubclass(float):
            pass

        payload, state, context = self._projection_fixture()
        signal = payload["operational_signals"][0]
        provenance = payload["signal_provenance_by_modality"]
        first_provenance_signal = next(iter(provenance))
        modality = next(iter(provenance[first_provenance_signal]))
        mutations: list[tuple[str, dict[str, Any]]] = []

        for label, value in (
            ("ordinary", 7),
            ("unhashable", []),
            ("subclass", StringSubclass(signal)),
        ):
            mutations.append((
                f"operational_{label}",
                dict(payload, operational_signals=[value, *payload["operational_signals"][1:]]),
            ))
        for label, value in (
            ("ordinary_key", 7),
            ("subclass_key", StringSubclass(signal)),
        ):
            confidence = {
                (value if key == signal else key): item
                for key, item in payload["confidence_by_signal"].items()
            }
            mutations.append((f"confidence_{label}", dict(payload, confidence_by_signal=confidence)))
        for label, value in (
            ("ordinary_value", 7),
            ("unhashable_value", []),
            ("subclass_value", FloatSubclass(payload["confidence_by_signal"][signal])),
        ):
            confidence = dict(payload["confidence_by_signal"])
            confidence[signal] = value
            mutations.append((f"confidence_{label}", dict(payload, confidence_by_signal=confidence)))
        for label, value in (
            ("ordinary", 7),
            ("unhashable", []),
            ("subclass", StringSubclass(payload["evidence_refs"][0])),
        ):
            mutations.append((
                f"evidence_ref_{label}",
                dict(payload, evidence_refs=[value, *payload["evidence_refs"][1:]]),
            ))

        signal_key_mutations = (
            ("ordinary", 7),
            ("subclass", StringSubclass(first_provenance_signal)),
        )
        for label, value in signal_key_mutations:
            mutated_provenance = {
                (value if key == first_provenance_signal else key): copy.deepcopy(item)
                for key, item in provenance.items()
            }
            mutations.append((
                f"provenance_signal_key_{label}",
                dict(payload, signal_provenance_by_modality=mutated_provenance),
            ))
        for label, value in (
            ("ordinary", 7),
            ("subclass", StringSubclass(modality)),
        ):
            mutated_provenance = copy.deepcopy(provenance)
            modality_map = mutated_provenance[first_provenance_signal]
            mutated_provenance[first_provenance_signal] = {
                (value if key == modality else key): item
                for key, item in modality_map.items()
            }
            mutations.append((
                f"provenance_modality_key_{label}",
                dict(payload, signal_provenance_by_modality=mutated_provenance),
            ))
        mutated_provenance = copy.deepcopy(provenance)
        mutated_provenance[first_provenance_signal][modality] = tuple(
            mutated_provenance[first_provenance_signal][modality],
        )
        mutations.append((
            "provenance_reference_list_type",
            dict(payload, signal_provenance_by_modality=mutated_provenance),
        ))
        for label, value in (
            ("ordinary", 7),
            ("unhashable", []),
            (
                "subclass",
                StringSubclass(provenance[first_provenance_signal][modality][0]),
            ),
        ):
            mutated_provenance = copy.deepcopy(provenance)
            references = mutated_provenance[first_provenance_signal][modality]
            references[0] = value
            mutations.append((
                f"provenance_reference_{label}",
                dict(payload, signal_provenance_by_modality=mutated_provenance),
            ))

        for field in ("allowed_policy_effects", "blocked_policy_effects"):
            for label, value in (
                ("ordinary", 7),
                ("unhashable", []),
                ("subclass", StringSubclass(payload[field][0])),
            ):
                mutations.append((
                    f"{field}_{label}",
                    dict(payload, **{field: [value, *payload[field][1:]]}),
                ))

        abstained_payload, abstained_state, abstained_context = self._last_replay_fixture(
            "empty_frame_missing_input",
        )
        for label, value in (
            ("ordinary", 7),
            ("unhashable", []),
            ("subclass", StringSubclass(abstained_payload["abstention_reasons"][0])),
        ):
            mutated = dict(
                abstained_payload,
                abstention_reasons=[
                    value,
                    *abstained_payload["abstention_reasons"][1:],
                ],
            )
            with self.subTest(field=f"abstention_reasons_{label}"):
                self.assertEqual(
                    self._semantic_code(mutated, abstained_state, abstained_context),
                    "perceived_field_type",
                )

        for label, mutated in mutations:
            with self.subTest(field=label):
                self.assertEqual(
                    self._semantic_code(mutated, state, context),
                    "perceived_field_type",
                )

    def test_final_hysteresis_cross_fields_fail_closed(self) -> None:
        valid = (
            self._hysteresis(
                None,
                entries={"confusion": ("ind:fixture:5:entry",)},
            ),
            self._hysteresis(
                "frustration",
                tenure=2,
                challenger="confusion",
                switch_keys=("ind:fixture:5:switch",),
            ),
            self._hysteresis("frustration", tenure=2, release=1),
        )
        for hysteresis in valid:
            with self.subTest(valid=hysteresis):
                phase_c_contracts.validate_phase_c_hysteresis(
                    hysteresis,
                    self.policy,
                )

        invalid = (
            self._hysteresis(
                "frustration",
                tenure=2,
                challenger="confusion",
            ),
            self._hysteresis(
                "confusion",
                tenure=2,
                challenger="confusion",
                switch_keys=("ind:fixture:5:switch",),
            ),
            self._hysteresis(
                "frustration",
                tenure=2,
                challenger="confusion",
                switch_keys=("ind:fixture:5:switch",),
                release=1,
            ),
            self._hysteresis(
                None,
                entries={
                    "confusion": ("ind:fixture:5:entry-a",),
                    "interest": ("ind:fixture:5:entry-b",),
                },
            ),
        )
        for hysteresis in invalid:
            with self.subTest(invalid=hysteresis):
                with self.assertRaises(PhaseCContractError) as captured:
                    phase_c_contracts.validate_phase_c_hysteresis(
                        hysteresis,
                        self.policy,
                    )
                self.assertEqual(captured.exception.code, "hysteresis_cross_field")

        nets = {signal: 0 for signal in self.policy["canonical_signal_order"]}
        previous_frame = self._frame_for(
            signal="frustration",
            key="ind:fixture:5:incumbent",
        )
        previous_fold = self._dense_fold(
            previous_frame,
            dict(nets, frustration=500),
            confirming=previous_frame.evidence_atoms[0].independence_key,
        )
        previous = self._state(
            previous_frame,
            previous_fold,
            self._hysteresis("frustration", tenure=2),
        )
        challenger_frame = self._frame_for(
            signal="confusion",
            key="ind:fixture:5:no-key",
            sequence=1,
        )
        challenger_fold = self._dense_fold(
            challenger_frame,
            dict(nets, confusion=700, frustration=500),
            confirming=None,
        )
        result = self.tracker.update_hysteresis(
            previous,
            challenger_fold,
            challenger_frame,
            self.policy,
        )
        self.assertEqual(result.internal_incumbent, "frustration")
        self.assertIsNone(result.switch_challenger)
        self.assertEqual(result.switch_confirmation_keys, ())

    def test_final_semantic_order_abstention_and_effect_boundaries(self) -> None:
        payload, state, context = self._projection_fixture()
        confidence_reordered = dict(payload)
        confidence_reordered["confidence_by_signal"] = dict(
            reversed(tuple(payload["confidence_by_signal"].items())),
        )
        provenance_reordered = dict(payload)
        provenance_reordered["signal_provenance_by_modality"] = dict(
            reversed(tuple(payload["signal_provenance_by_modality"].items())),
        )
        for label, mutated in (
            ("confidence_map", confidence_reordered),
            ("provenance_signal_map", provenance_reordered),
        ):
            with self.subTest(order=label):
                self.assertEqual(
                    self._semantic_code(mutated, state, context),
                    "noncanonical_output_order",
                )

        multimodal, multimodal_state, multimodal_context = self._last_replay_fixture(
            "multimodal_two_turn_entry",
        )
        modality_reordered = copy.deepcopy(multimodal)
        signal = next(iter(modality_reordered["signal_provenance_by_modality"]))
        modality_reordered["signal_provenance_by_modality"][signal] = dict(
            reversed(tuple(
                modality_reordered["signal_provenance_by_modality"][signal].items(),
            )),
        )
        self.assertEqual(
            self._semantic_code(
                modality_reordered,
                multimodal_state,
                multimodal_context,
            ),
            "noncanonical_output_order",
        )

        abstained, abstained_state, abstained_context = self._last_replay_fixture(
            "empty_frame_missing_input",
        )
        reason_reordered = dict(
            abstained,
            abstention_reasons=list(reversed(abstained["abstention_reasons"])),
        )
        self.assertEqual(
            self._semantic_code(reason_reordered, abstained_state, abstained_context),
            "noncanonical_output_order",
        )
        self.assertEqual(
            self._semantic_code(
                dict(payload, abstained=True, abstention_reasons=[]),
                state,
                context,
            ),
            "abstention_semantics",
        )
        self.assertEqual(
            self._semantic_code(
                dict(payload, abstention_reasons=["missing_input"]),
                state,
                context,
            ),
            "abstention_semantics",
        )

        acoustic, acoustic_state, acoustic_context = self._last_replay_fixture(
            "acoustic_only_capped",
        )
        expanded_effects = ["preserve", "soften"]
        self.assertEqual(
            self._semantic_code(
                dict(acoustic, allowed_policy_effects=expanded_effects),
                acoustic_state,
                acoustic_context,
            ),
            "allowed_effects",
        )
        self.assertEqual(
            self._semantic_code(
                dict(abstained, allowed_policy_effects=expanded_effects),
                abstained_state,
                abstained_context,
            ),
            "allowed_effects",
        )

    def test_final_replay_precondition_inventory(self) -> None:
        scenario = self.case("transcript_three_turn_entry")
        frames = scenario.sessions[0].frames
        first, second = frames[:2]
        cases: tuple[tuple[str, object, str], ...] = (
            ("non_tuple", [first], "replay_frames"),
            ("empty", (), "replay_frames"),
            (
                "session_mismatch",
                (first, dataclasses.replace(second, call_session_id="session:other")),
                "replay_identity",
            ),
            (
                "campaign_mismatch",
                (first, dataclasses.replace(second, campaign_profile_id="campaign:other")),
                "replay_identity",
            ),
            (
                "version_mismatch",
                (
                    first,
                    dataclasses.replace(second, campaign_profile_version="version:other"),
                ),
                "replay_identity",
            ),
            (
                "non_increasing_sequence",
                (first, dataclasses.replace(second, turn_sequence=first.turn_sequence)),
                "replay_turn_sequence",
            ),
            (
                "duplicate_turn_id",
                (first, dataclasses.replace(second, turn_id=first.turn_id)),
                "replay_duplicate_identity",
            ),
            (
                "duplicate_event_id",
                (first, dataclasses.replace(second, event_id=first.event_id)),
                "replay_duplicate_identity",
            ),
            (
                "duplicate_evidence_ref",
                (
                    first,
                    dataclasses.replace(
                        second,
                        evidence_atoms=(
                            dataclasses.replace(
                                second.evidence_atoms[0],
                                evidence_ref=first.evidence_atoms[0].evidence_ref,
                            ),
                            *second.evidence_atoms[1:],
                        ),
                    ),
                ),
                "replay_duplicate_identity",
            ),
            (
                "nonzero_revision",
                (dataclasses.replace(first, input_revision=1),),
                "replay_correction_not_supported",
            ),
        )
        for label, mutated_frames, code in cases:
            with self.subTest(precondition=label):
                with self.assertRaises(PhaseCContractError) as captured:
                    self.tracker.replay_validated_frames(
                        mutated_frames,
                        self.policy,
                    )
                self.assertEqual(captured.exception.code, code)

    def test_projection_implementation_is_readable_and_independent(self) -> None:
        source = inspect.getsource(
            self.tracker.project_perceived_customer_state,
        )
        self.assertNotIn(";", source)
        self.assertNotIn(
            "from runtime.contracts.emotion_state_contracts import",
            source,
        )
        self.assertNotIn("_phase_c_output_expected", source)
        self.assertNotIn("validate_phase_c_perceived_state", source)
        self.assertLessEqual(max(map(len, source.splitlines())), 119)

    def test_nested_provenance_reference_order_is_canonical_only(self) -> None:
        payload, state, context = self._last_replay_fixture(
            "multimodal_two_turn_entry",
        )
        signal = next(iter(payload["signal_provenance_by_modality"]))
        modality_map = payload["signal_provenance_by_modality"][signal]
        modality = next(
            key for key, references in modality_map.items()
            if len(references) >= 2
        )

        reordered = copy.deepcopy(payload)
        reordered["signal_provenance_by_modality"][signal][modality] = list(
            reversed(modality_map[modality]),
        )
        self.assertEqual(
            self._semantic_code(reordered, state, context),
            "noncanonical_output_order",
        )

        missing = copy.deepcopy(payload)
        missing["signal_provenance_by_modality"][signal][modality] = (
            modality_map[modality][:-1]
        )
        duplicate = copy.deepcopy(payload)
        duplicate["signal_provenance_by_modality"][signal][modality] = [
            modality_map[modality][0],
            modality_map[modality][0],
        ]
        moved = copy.deepcopy(payload)
        other_modality = next(key for key in modality_map if key != modality)
        moved_reference = moved["signal_provenance_by_modality"][signal][
            modality
        ].pop()
        moved["signal_provenance_by_modality"][signal][other_modality].append(
            moved_reference,
        )
        for label, mutated in (
            ("missing", missing),
            ("duplicate", duplicate),
            ("moved", moved),
        ):
            with self.subTest(content=label):
                self.assertEqual(
                    self._semantic_code(mutated, state, context),
                    "provenance_projection",
                )

    def test_projection_context_fails_closed_before_arithmetic(self) -> None:
        class StringSubclass(str):
            pass

        class IntSubclass(int):
            pass

        payload, state, context = self._projection_fixture(
            prior="confusion",
            support=700,
        )
        valid_projected = self.tracker.project_perceived_customer_state(
            state,
            context,
            self.policy,
        )
        self.assertEqual(valid_projected, payload)
        self.assertEqual(
            phase_c_contracts.validate_phase_c_perceived_state(
                payload,
                state,
                context,
                self.policy,
            ),
            payload,
        )

        invalid_contexts = (
            None,
            dataclasses.replace(
                context,
                prior_emitted_selected_signal=None,
                prior_emitted_selected_support=700,
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_signal="confusion",
                prior_emitted_selected_support=None,
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_signal=7,
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_signal=StringSubclass("confusion"),
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_signal="not-canonical",
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_support="700",
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_support=True,
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_support=IntSubclass(700),
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_support=-1,
            ),
            dataclasses.replace(
                context,
                prior_emitted_selected_support=self.policy["scale"] + 1,
            ),
            dataclasses.replace(context, fold=None),
            dataclasses.replace(context, frame=None),
        )
        for invalid in invalid_contexts:
            with self.subTest(context=repr(invalid)):
                with self.assertRaises(PhaseCContractError):
                    self.tracker.project_perceived_customer_state(
                        state,
                        invalid,
                        self.policy,
                    )
                self.assertEqual(
                    self._semantic_code(payload, state, invalid),
                    "perceived_field_type",
                )

        paired_wrong = dataclasses.replace(
            context,
            prior_emitted_selected_signal="confusion",
            prior_emitted_selected_support=None,
        )
        with self.assertRaises(
            phase_c_contracts.PhaseCOutputSemanticError,
        ) as nonobject:
            phase_c_contracts.validate_phase_c_perceived_state(
                None,
                state,
                paired_wrong,
                self.policy,
            )
        self.assertEqual(nonobject.exception.code, "perceived_not_object")
        missing_field = dict(payload)
        missing_field.pop("trajectory")
        self.assertEqual(
            self._semantic_code(missing_field, state, paired_wrong),
            "perceived_field_set",
        )

    def test_top_level_output_key_types_follow_field_set_precedence(self) -> None:
        class StringSubclass(str):
            pass

        payload, state, context = self._projection_fixture()
        subclass_key = {
            (
                StringSubclass(key)
                if key == "call_session_id"
                else key
            ): value
            for key, value in payload.items()
        }
        self.assertEqual(set(subclass_key), set(payload))
        self.assertEqual(
            self._semantic_code(subclass_key, state, context),
            "perceived_field_type",
        )
        nonstring_key = dict(payload)
        nonstring_key[7] = nonstring_key.pop("call_session_id")
        self.assertEqual(
            self._semantic_code(nonstring_key, state, context),
            "perceived_field_set",
        )


class PhaseCAdvanceTests(PhaseCTestCase):
    def execute_attempt(self, state, scenario, attempt):
        payload = phase_c_contracts.materialize_phase_c_scenario_attempt_payload(
            scenario,
            attempt,
        )
        frame = parse_phase_c_frame(payload, self.policy)
        return self.tracker.advance(state, frame, self.policy)

    def advance(self, state, frame):
        return self.tracker.advance(state, frame, self.policy)

    def fold_frames(self, frames):
        state = None
        output = None
        for frame in frames:
            state, output = self.advance(state, frame)
        return state, output

    def canonical_state(self, state):
        return self.tracker.canonical_session_state_bytes(state)

    def custom_frame(
        self,
        *,
        turn_sequence,
        input_revision=0,
        atoms,
        session_id="session:phase-c0-advance",
        turn_id=None,
        event_id=None,
    ):
        payload = _frame(
            event_id=event_id or f"event:phase-c0-advance:{turn_sequence}:{input_revision}",
            turn_id=turn_id or f"turn:phase-c0-advance:{turn_sequence}",
            turn_sequence=turn_sequence,
            input_revision=input_revision,
            atoms=atoms,
        )
        payload["call_session_id"] = session_id
        payload["campaign_profile_id"] = "campaign:phase-c0"
        payload["campaign_profile_version"] = "version:1"
        return parse_phase_c_frame(payload, self.policy)

    def test_latest_revision_replaces_and_replays(self) -> None:
        scenario = self.case("latest_turn_correction_replay")
        frames = scenario.sessions[0].frames
        first_state, first_output = self.advance(None, frames[0])
        corrected_state, corrected_output = self.advance(first_state, frames[1])
        normalized = dataclasses.replace(
            frames[1],
            event_id="event-normalized-fresh",
            input_revision=0,
        )
        fresh_state, fresh_output = self.fold_frames([normalized])
        self.assertEqual(
            self.tracker.canonical_semantic_replay_bytes(
                corrected_state,
                corrected_output,
            ),
            self.tracker.canonical_semantic_replay_bytes(
                fresh_state,
                fresh_output,
            ),
        )
        self.assertEqual(
            len(corrected_state.watermark.event_history_by_id),
            2,
        )
        self.assertNotEqual(
            self.canonical_state(corrected_state),
            self.canonical_state(fresh_state),
        )
        self.assertEqual(corrected_output["selected_policy_signal"], "interest")
        self.assertNotEqual(first_output, corrected_output)

    def test_identical_replay_rejects_without_mutation(self) -> None:
        frame = self.case("explicit_confusion_entry").sessions[0].frames[0]
        state, _ = self.advance(None, frame)
        before = self.canonical_state(state)
        snapshot = copy.deepcopy(state)
        with self.assertRaises(PhaseCEventRejected) as captured:
            self.advance(state, frame)
        self.assertEqual(captured.exception.code, "duplicate_event")
        self.assertEqual(state, snapshot)
        self.assertEqual(self.canonical_state(state), before)

    def test_every_rejection_preserves_prior_state_bytes_and_object(self) -> None:
        for case_id in REJECTION_CASE_IDS:
            scenario = self.case(case_id)
            state = None
            for attempt, expected in zip(
                scenario.attempt_order,
                scenario.expected_steps,
                strict=True,
            ):
                if expected.disposition == "accepted":
                    state, _output = self.execute_attempt(
                        state,
                        scenario,
                        attempt,
                    )
                    continue
                before = self.canonical_state(state)
                object_snapshot = copy.deepcopy(state)
                identity = state
                with self.subTest(
                    case_id=case_id,
                    rejection_code=expected.rejection_code,
                ):
                    with self.assertRaises(PhaseCContractError) as caught:
                        self.execute_attempt(state, scenario, attempt)
                    self.assertEqual(
                        caught.exception.code,
                        expected.rejection_code,
                    )
                    self.assertIs(state, identity)
                    self.assertEqual(state, object_snapshot)
                    self.assertEqual(before, self.canonical_state(state))

    def test_accepted_scenario_outputs_remain_frozen_authority(self) -> None:
        for scenario in self.scenarios.values():
            states = {
                session.session_alias: None
                for session in scenario.sessions
            }
            for attempt, expected in zip(
                scenario.attempt_order,
                scenario.expected_steps,
                strict=True,
            ):
                if expected.disposition != "accepted":
                    continue
                state, output = self.execute_attempt(
                    states[attempt.state_session_alias],
                    scenario,
                    attempt,
                )
                states[attempt.state_session_alias] = state
                with self.subTest(
                    case_id=scenario.case_id,
                    frame_index=attempt.frame_index,
                ):
                    self.assertEqual(
                        canonical_json_bytes(output),
                        expected.expected_output_bytes,
                    )

    def test_interleaved_sessions_equal_separate_folds(self) -> None:
        scenario = self.case("simultaneous_sessions_isolated")
        sessions = {item.session_alias: item for item in scenario.sessions}
        interleaved_states = {alias: None for alias in sessions}
        for attempt in scenario.attempt_order:
            state, _output = self.execute_attempt(
                interleaved_states[attempt.state_session_alias],
                scenario,
                attempt,
            )
            interleaved_states[attempt.state_session_alias] = state
        separate_states = {
            alias: self.fold_frames(session.frames)[0]
            for alias, session in sessions.items()
        }
        self.assertEqual(
            {
                alias: self.canonical_state(state)
                for alias, state in interleaved_states.items()
            },
            {
                alias: self.canonical_state(state)
                for alias, state in separate_states.items()
            },
        )

    def test_cross_feeding_interleaved_session_frames_rejects(self) -> None:
        scenario = self.case("simultaneous_sessions_isolated")
        sessions = {item.session_alias: item for item in scenario.sessions}
        aliases = tuple(sessions)
        left_state, _ = self.advance(None, sessions[aliases[0]].frames[0])
        right_state, _ = self.advance(None, sessions[aliases[1]].frames[0])
        with self.assertRaisesRegex(PhaseCEventRejected, "cross_session"):
            self.advance(left_state, sessions[aliases[1]].frames[1])
        with self.assertRaisesRegex(PhaseCEventRejected, "cross_session"):
            self.advance(right_state, sessions[aliases[0]].frames[1])

    def test_correction_can_retain_immediately_replaced_reference_and_key(self) -> None:
        atom = _atom(
            counter=910001,
            signal="interest",
            independence_key="ind:phase-c0:retained",
        )
        first = self.custom_frame(
            turn_sequence=0,
            atoms=[atom],
        )
        correction = self.custom_frame(
            turn_sequence=0,
            input_revision=1,
            atoms=[copy.deepcopy(atom)],
        )
        state, _ = self.advance(None, first)
        corrected, _ = self.advance(state, correction)
        self.assertEqual(corrected.retired_independence_keys, ())
        self.assertEqual(
            corrected.seen_evidence_refs,
            (atom["evidence_ref"],),
        )
        self.assertEqual(len(corrected.evidence_history_by_event), 2)

    def test_multi_revision_replay_uses_same_retired_seed(self) -> None:
        old_key = "ind:phase-c0:a-old"
        middle_key = "ind:phase-c0:b-middle"
        latest_key = "ind:phase-c0:c-latest"
        first = self.custom_frame(
            turn_sequence=0,
            atoms=[
                _atom(
                    counter=920001,
                    signal="interest",
                    independence_key=old_key,
                ),
            ],
        )
        correction_one = self.custom_frame(
            turn_sequence=0,
            input_revision=1,
            atoms=[
                _atom(
                    counter=920002,
                    signal="interest",
                    independence_key=middle_key,
                ),
            ],
        )
        correction_two = self.custom_frame(
            turn_sequence=0,
            input_revision=2,
            atoms=[
                _atom(
                    counter=920003,
                    signal="interest",
                    independence_key=old_key,
                ),
                _atom(
                    counter=920004,
                    signal="interest",
                    independence_key=latest_key,
                ),
            ],
        )
        state, _ = self.advance(None, first)
        state, _ = self.advance(state, correction_one)
        state, output = self.advance(state, correction_two)
        self.assertEqual(
            frozenset(state.retired_independence_keys),
            frozenset({old_key, middle_key}),
        )
        old_reference = next(
            atom.evidence_ref
            for atom in correction_two.evidence_atoms
            if atom.independence_key == old_key
        )
        self.assertNotIn(old_reference, state.contributing_evidence_refs)

        normalized = dataclasses.replace(
            correction_two,
            event_id="event:phase-c0:normalized:multi",
            input_revision=0,
        )
        watermark = validate_phase_c_event_identity(
            normalized,
            initial_phase_c_watermark(normalized),
        )
        refs = tuple(
            sorted(atom.evidence_ref for atom in normalized.evidence_atoms)
        )
        keys = tuple(
            sorted(atom.independence_key for atom in normalized.evidence_atoms)
        )
        normalized_state, normalized_output, _ = (
            self.tracker.replay_frame_semantics(
                (normalized,),
                self.policy,
                retired_independence_keys=frozenset(
                    state.retired_independence_keys,
                ),
                evidence_history_by_event=(
                    (normalized.event_id, refs, keys),
                ),
                historical_seen_evidence_refs=refs,
                historical_seen_independence_keys=keys,
                watermark=watermark,
            )
        )
        self.assertEqual(
            self.tracker.canonical_semantic_replay_bytes(state, output),
            self.tracker.canonical_semantic_replay_bytes(
                normalized_state,
                normalized_output,
            ),
        )

    def test_shared_key_drop_does_not_retire_while_another_turn_retains_it(self) -> None:
        shared = "ind:phase-c0:shared"
        first = self.custom_frame(
            turn_sequence=0,
            atoms=[_atom(counter=930001, independence_key=shared)],
        )
        second = self.custom_frame(
            turn_sequence=1,
            atoms=[_atom(counter=930002, independence_key=shared)],
        )
        corrected_second = self.custom_frame(
            turn_sequence=1,
            input_revision=1,
            atoms=[
                _atom(
                    counter=930003,
                    independence_key="ind:phase-c0:replacement",
                ),
            ],
        )
        state, _ = self.fold_frames((first, second))
        state, _ = self.advance(state, corrected_second)
        self.assertNotIn(shared, state.retired_independence_keys)
        self.assertIn(shared, state.seen_independence_keys)

    def test_retired_key_stays_zero_across_later_turn_and_replay(self) -> None:
        retired = "ind:phase-c0:permanent-retired"
        first = self.custom_frame(
            turn_sequence=0,
            atoms=[
                _atom(
                    counter=940001,
                    signal="interest",
                    independence_key=retired,
                ),
            ],
        )
        correction = self.custom_frame(
            turn_sequence=0,
            input_revision=1,
            atoms=[
                _atom(
                    counter=940002,
                    signal="interest",
                    independence_key="ind:phase-c0:replacement-live",
                ),
            ],
        )
        reintroduced = self.custom_frame(
            turn_sequence=1,
            atoms=[
                _atom(
                    counter=940003,
                    signal="interest",
                    independence_key=retired,
                ),
            ],
        )
        later = self.custom_frame(
            turn_sequence=2,
            atoms=[],
        )
        state, _ = self.advance(None, first)
        state, _ = self.advance(state, correction)
        state, _ = self.advance(state, reintroduced)
        self.assertIn(retired, state.retired_independence_keys)
        self.assertNotIn(
            reintroduced.evidence_atoms[0].evidence_ref,
            state.contributing_evidence_refs,
        )
        state, output = self.advance(state, later)
        self.tracker.validate_phase_c_state_replay(state, self.policy)
        self.tracker.validate_phase_c_replayed_output(
            output,
            state,
            self.policy,
        )
        self.assertIn(retired, state.retired_independence_keys)

    def test_dropped_reference_rejects_and_dropped_key_cannot_contribute(self) -> None:
        dropped_key = "ind:phase-c0:dropped"
        dropped_atom = _atom(
            counter=950001,
            signal="interest",
            independence_key=dropped_key,
        )
        first = self.custom_frame(
            turn_sequence=0,
            atoms=[dropped_atom],
        )
        correction = self.custom_frame(
            turn_sequence=0,
            input_revision=1,
            atoms=[
                _atom(
                    counter=950002,
                    signal="interest",
                    independence_key="ind:phase-c0:kept",
                ),
            ],
        )
        state, _ = self.advance(None, first)
        state, _ = self.advance(state, correction)
        recycled_reference = self.custom_frame(
            turn_sequence=1,
            atoms=[copy.deepcopy(dropped_atom)],
        )
        before = self.canonical_state(state)
        with self.assertRaises(PhaseCEventRejected) as captured:
            self.advance(state, recycled_reference)
        self.assertEqual(
            captured.exception.code,
            "duplicate_evidence_reference",
        )
        self.assertEqual(before, self.canonical_state(state))

        fresh_reference = self.custom_frame(
            turn_sequence=1,
            atoms=[
                _atom(
                    counter=950004,
                    signal="interest",
                    independence_key=dropped_key,
                ),
            ],
        )
        next_state, _ = self.advance(state, fresh_reference)
        self.assertNotIn(
            fresh_reference.evidence_atoms[0].evidence_ref,
            next_state.contributing_evidence_refs,
        )

    def test_malformed_prior_state_families_reject_before_incoming_frame(self) -> None:
        class StringSubclass(str):
            pass

        one_frame = self.case("explicit_confusion_entry").sessions[0].frames[0]
        base, _ = self.advance(None, one_frame)
        two_frames = self.case(
            "repeated_independence_zero_addition",
        ).sessions[0].frames
        ordered, _ = self.fold_frames(two_frames)
        correction_frames = self.case(
            "latest_turn_correction_replay",
        ).sessions[0].frames
        corrected, _ = self.fold_frames(correction_frames)
        malformed_history = list(corrected.evidence_history_by_event)
        extra_reference = _atom(counter=970001)["evidence_ref"]
        first_event_id, first_references, first_keys = malformed_history[0]
        malformed_history[0] = (
            first_event_id,
            tuple(sorted((*first_references, extra_reference))),
            first_keys,
        )
        malformed_seen_references = []
        for _event_id, references, _keys in malformed_history:
            for reference in references:
                if reference not in malformed_seen_references:
                    malformed_seen_references.append(reference)
        accumulator = dataclasses.replace(
            base.accumulator,
            gross_supporting_units=(
                ("confusion", 699),
                *base.accumulator.gross_supporting_units[1:],
            ),
        )
        bad_watermark = dataclasses.replace(
            base.watermark,
            turn_sequence_by_id=((one_frame.turn_id, 1),),
            turn_id_by_sequence=((1, one_frame.turn_id),),
            last_turn_sequence=1,
        )
        mutations = (
            (
                "schema_scalar_type",
                dataclasses.replace(
                    base,
                    schema_version=StringSubclass(base.schema_version),
                ),
            ),
            ("schema", dataclasses.replace(base, schema_version="wrong")),
            ("policy_id", dataclasses.replace(base, policy_id="wrong")),
            ("policy_hash", dataclasses.replace(base, policy_sha256="0" * 64)),
            (
                "identity",
                dataclasses.replace(base, call_session_id="session:other"),
            ),
            (
                "identity_maps",
                dataclasses.replace(base, watermark=bad_watermark),
            ),
            (
                "evidence_history",
                dataclasses.replace(
                    base,
                    evidence_history_by_event=(
                        (one_frame.event_id, (), ()),
                    ),
                ),
            ),
            (
                "accepted_frame_order",
                dataclasses.replace(
                    ordered,
                    accepted_frames=tuple(reversed(ordered.accepted_frames)),
                ),
            ),
            (
                "accumulator",
                dataclasses.replace(base, accumulator=accumulator),
            ),
            (
                "hysteresis",
                dataclasses.replace(
                    base,
                    hysteresis=dataclasses.replace(
                        base.hysteresis,
                        incumbent_tenure=0,
                    ),
                ),
            ),
            (
                "provenance",
                dataclasses.replace(base, contributing_evidence_refs=()),
            ),
            (
                "accepted_turn_count",
                dataclasses.replace(base, accepted_turn_count=2),
            ),
            (
                "last_emitted",
                dataclasses.replace(
                    base,
                    last_emitted_selected_support=699,
                ),
            ),
            (
                "collection_type",
                dataclasses.replace(
                    base,
                    accepted_frames=list(base.accepted_frames),
                ),
            ),
            (
                "ledger_scalar_type",
                dataclasses.replace(
                    base,
                    seen_evidence_refs=(
                        StringSubclass(base.seen_evidence_refs[0]),
                    ),
                ),
            ),
            (
                "historical_ref_key_pairing",
                dataclasses.replace(
                    corrected,
                    evidence_history_by_event=tuple(malformed_history),
                    seen_evidence_refs=tuple(malformed_seen_references),
                ),
            ),
        )
        for family, malformed in mutations:
            with self.subTest(family=family):
                with self.assertRaises(PhaseCContractError) as captured:
                    self.advance(malformed, object())
                if family == "schema_scalar_type":
                    self.assertEqual(
                        captured.exception.code,
                        "session_state_field_type",
                    )
                self.assertFalse(
                    captured.exception.code.startswith("frame_"),
                    captured.exception.code,
                )

    def test_post_parse_source_mutation_cannot_change_frozen_frame(self) -> None:
        payload = _frame(
            event_id="event:phase-c0:frozen",
            turn_id="turn:phase-c0:frozen",
            atoms=[_atom(counter=960001)],
        )
        frame = parse_phase_c_frame(payload, self.policy)
        frozen_bytes = canonical_json_bytes(
            phase_c_contracts.phase_c_frame_to_payload(frame),
        )
        payload["evidence_atoms"][0]["independence_key"] = "ind:mutated"
        payload["evidence_atoms"].append(_atom(counter=960002))
        self.assertEqual(
            canonical_json_bytes(
                phase_c_contracts.phase_c_frame_to_payload(frame),
            ),
            frozen_bytes,
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            frame.event_id = "event:mutated"

    def test_phase_c_modules_expose_no_user_defined_mutable_containers(self) -> None:
        for module in (phase_c_contracts, self.tracker):
            mutable = {
                name: type(value).__name__
                for name, value in vars(module).items()
                if (
                    not name.startswith("__")
                    and type(value) in {dict, list, set}
                )
            }
            self.assertEqual(mutable, {}, module.__name__)

    def test_independent_replayed_output_validation_and_runtime_rejection(self) -> None:
        scenario = self.case("explicit_confusion_entry")
        state, output = self.fold_frames(scenario.sessions[0].frames)
        self.assertIs(
            self.tracker.validate_phase_c_replayed_output(
                output,
                state,
                self.policy,
            ),
            output,
        )
        mutated = copy.deepcopy(output)
        mutated["runtime_approved"] = True
        with self.assertRaises(PhaseCOutputSemanticError) as captured:
            self.tracker.validate_phase_c_replayed_output(
                mutated,
                state,
                self.policy,
            )
        self.assertEqual(captured.exception.code, "runtime_approved")

    def test_replay_validators_never_call_advance(self) -> None:
        scenario = self.case("explicit_confusion_entry")
        state, output = self.fold_frames(scenario.sessions[0].frames)
        with mock.patch.object(
            self.tracker,
            "advance",
            side_effect=AssertionError("advance must not be used"),
        ):
            self.tracker.validate_phase_c_state_replay(state, self.policy)
            self.tracker.validate_phase_c_replayed_output(
                output,
                state,
                self.policy,
            )


TASK_7_FAMILY_COUNT_ORDER = (
    "entry",
    "independence",
    "rejection",
    "abstention",
    "contradiction",
    "hysteresis",
    "correction",
    "isolation",
    "determinism",
    "saturation",
)
TASK_7_SIGNAL_FAMILY_COUNT_ORDER = (
    "confusion",
    "disengagement",
    "frustration",
    "hesitation",
    "interest",
    "mixed",
    "none",
)
TASK_7_MODALITY_FAMILY_COUNT_ORDER = (
    "text",
    "dialogue",
    "acoustic",
    "multimodal",
    "none",
)
TASK_7_EMITTED_ABSTENTION_COUNT_ORDER = (
    "insufficient_evidence",
    "contradictory_evidence",
    "low_audio_quality",
    "missing_input",
)
TASK_7_INVARIANT_NAMES = (
    "golden_projection",
    "rejection_no_mutation",
    "correction_semantic_replay",
    "session_isolation",
    "deterministic_replay",
    "semantic_output",
    "privacy_boundary",
)
TASK_7_SAFETY_INVARIANT_NAMES = (
    "rejection_no_mutation",
    "session_isolation",
    "deterministic_replay",
    "semantic_output",
    "privacy_boundary",
)
TASK_7_EXPECTED_COUNTS_BY_FAMILY = {
    "entry": 7,
    "independence": 1,
    "rejection": 8,
    "abstention": 4,
    "contradiction": 2,
    "hysteresis": 4,
    "correction": 1,
    "isolation": 1,
    "determinism": 1,
    "saturation": 1,
}
TASK_7_EXPECTED_COUNTS_BY_SIGNAL_FAMILY = {
    "confusion": 13,
    "disengagement": 1,
    "frustration": 3,
    "hesitation": 4,
    "interest": 3,
    "mixed": 5,
    "none": 1,
}
TASK_7_EXPECTED_COUNTS_BY_MODALITY_FAMILY = {
    "text": 23,
    "dialogue": 1,
    "acoustic": 2,
    "multimodal": 3,
    "none": 1,
}
TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON = {
    "insufficient_evidence": 24,
    "contradictory_evidence": 1,
    "low_audio_quality": 1,
    "missing_input": 11,
}
TASK_7_UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE = {
    "duplicate_event_rejected": "rejection_no_mutation",
    "duplicate_reference_rejected": "rejection_no_mutation",
    "closed_turn_correction_rejected": "rejection_no_mutation",
    "cross_session_rejected": "session_isolation",
    "cross_campaign_rejected": "session_isolation",
    "wrong_campaign_version_rejected": "session_isolation",
    "noncanonical_atom_order_rejected": "privacy_boundary",
    "forbidden_phase_b_field_rejected": "privacy_boundary",
}


def _mechanical_negative_evaluation(
    test_case: PhaseCTestCase,
):
    replacement = test_case.tracker.replay_validated_frames(
        test_case.case("empty_frame_missing_input").sessions[0].frames,
        test_case.policy,
    )
    original = test_case.tracker._execute_scenario_attempt

    def injected(prior, scenario, attempt, policy):
        expected = scenario.expected_steps[scenario.attempt_order.index(attempt)]
        if (
            scenario.case_id == "explicit_confusion_entry"
            and expected.disposition == "accepted"
        ):
            return replacement.final_state, replacement.outputs[-1]
        return original(prior, scenario, attempt, policy)

    with mock.patch.object(
        test_case.tracker,
        "_execute_scenario_attempt",
        side_effect=injected,
    ):
        return test_case.tracker.evaluate_phase_c_scenarios(
            test_case.policy,
            test_case.scenarios,
        )


def _semantic_negative_evaluation(
    test_case: PhaseCTestCase,
):
    replacement = test_case.tracker.replay_validated_frames(
        test_case.case("explicit_confusion_entry").sessions[0].frames,
        test_case.policy,
    )
    invalid_output = copy.deepcopy(replacement.outputs[-1])
    invalid_output["runtime_approved"] = True
    original = test_case.tracker._execute_scenario_attempt

    def injected(prior, scenario, attempt, policy):
        expected = scenario.expected_steps[scenario.attempt_order.index(attempt)]
        if (
            scenario.case_id == "explicit_confusion_entry"
            and expected.disposition == "accepted"
        ):
            return replacement.final_state, invalid_output
        return original(prior, scenario, attempt, policy)

    with mock.patch.object(
        test_case.tracker,
        "_execute_scenario_attempt",
        side_effect=injected,
    ):
        return test_case.tracker.evaluate_phase_c_scenarios(
            test_case.policy,
            test_case.scenarios,
        )


def _structural_semantic_negative_evaluation(
    test_case: PhaseCTestCase,
):
    replacement = test_case.tracker.replay_validated_frames(
        test_case.case("explicit_confusion_entry").sessions[0].frames,
        test_case.policy,
    )
    original = test_case.tracker._execute_scenario_attempt

    def injected(prior, scenario, attempt, policy):
        expected = scenario.expected_steps[scenario.attempt_order.index(attempt)]
        if (
            scenario.case_id == "explicit_confusion_entry"
            and expected.disposition == "accepted"
        ):
            return replacement.final_state, object()
        return original(prior, scenario, attempt, policy)

    with mock.patch.object(
        test_case.tracker,
        "_execute_scenario_attempt",
        side_effect=injected,
    ):
        return test_case.tracker.evaluate_phase_c_scenarios(
            test_case.policy,
            test_case.scenarios,
        )


def _no_follow_metadata_snapshot(metadata: Any) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        getattr(metadata, "st_file_attributes", 0),
        getattr(metadata, "st_reparse_tag", 0),
    )


def _bounded_regular_file_snapshot(
    path: Path,
    before: Any,
) -> tuple[str, Any]:
    if before.st_size > 65536:
        return ("oversized", before.st_size)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        return ("open_error", exc.errno)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _no_follow_metadata_snapshot(opened)
            != _no_follow_metadata_snapshot(before)
        ):
            return (
                "changed_before_read",
                _no_follow_metadata_snapshot(opened),
            )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(8192, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        payload = b"".join(chunks)
        if (
            len(payload) != opened.st_size
            or _no_follow_metadata_snapshot(after)
            != _no_follow_metadata_snapshot(opened)
        ):
            return (
                "changed_during_read",
                _no_follow_metadata_snapshot(after),
            )
        return ("sha256", sha256_bytes(payload))
    finally:
        os.close(descriptor)


def _bounded_no_follow_root_snapshot(path: Path) -> tuple[Any, ...]:
    try:
        root_metadata = os.lstat(path)
    except FileNotFoundError:
        return ("absent",)
    except OSError as exc:
        return ("root_lstat_error", exc.errno)
    root_snapshot = _no_follow_metadata_snapshot(root_metadata)
    if (
        stat.S_ISLNK(root_metadata.st_mode)
        or getattr(root_metadata, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        return ("root_reparse_or_link", root_snapshot)
    if not stat.S_ISDIR(root_metadata.st_mode):
        return ("root_not_directory", root_snapshot)
    try:
        names = tuple(sorted(os.listdir(path)))
    except OSError as exc:
        return ("root_list_error", root_snapshot, exc.errno)
    children: list[tuple[Any, ...]] = []
    for name in names:
        child = path / name
        try:
            metadata = os.lstat(child)
        except FileNotFoundError:
            children.append((name, "absent_during_snapshot"))
            continue
        except OSError as exc:
            children.append((name, "lstat_error", exc.errno))
            continue
        metadata_snapshot = _no_follow_metadata_snapshot(metadata)
        is_reparse = bool(
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        )
        if stat.S_ISLNK(metadata.st_mode) or is_reparse:
            content = ("reparse_or_link",)
        elif stat.S_ISREG(metadata.st_mode):
            content = _bounded_regular_file_snapshot(
                child,
                metadata,
            )
        else:
            content = ("not_regular",)
        children.append((name, metadata_snapshot, content))
    return ("directory", root_snapshot, names, tuple(children))


class PhaseCScenarioEvaluationTests(PhaseCTestCase):
    def evaluation(self):
        return self.tracker.evaluate_phase_c_scenarios(
            self.policy,
            self.scenarios,
        )

    def assert_single_failure(
        self,
        evaluation,
        expected_invariants,
    ) -> None:
        self.assertEqual(evaluation.passed_scenarios, 29)
        self.assertEqual(evaluation.failed_scenarios, 1)
        failed = tuple(
            outcome
            for outcome in evaluation.outcomes
            if not outcome.passed
        )
        self.assertEqual(len(failed), 1)
        self.assertEqual(
            failed[0].failed_invariants,
            tuple(
                name
                for name in TASK_7_INVARIANT_NAMES
                if name in expected_invariants
            ),
        )
        self.assertEqual(
            dict(evaluation.invariant_counts),
            {
                name: int(name in expected_invariants)
                for name in TASK_7_INVARIANT_NAMES
            },
        )

    def test_task_7_exact_frozen_types_constants_and_mapping_immutability(
        self,
    ) -> None:
        self.assertEqual(
            tuple(
                field.name
                for field in dataclasses.fields(
                    phase_c_contracts.PhaseCScenarioOutcomeV1,
                )
            ),
            (
                "case_id",
                "family",
                "signal_family",
                "modality_family",
                "passed",
                "failed_invariants",
                "rejection_count",
                "abstention_reason_counts",
            ),
        )
        self.assertEqual(
            tuple(
                field.name
                for field in dataclasses.fields(
                    phase_c_contracts.PhaseCScenarioEvaluationV1,
                )
            ),
            (
                "total_scenarios",
                "passed_scenarios",
                "failed_scenarios",
                "outcomes",
                "counts_by_family",
                "counts_by_signal",
                "counts_by_modality",
                "counts_by_abstention_reason",
                "invariant_counts",
                "deterministic_replay_passed",
                "privacy_boundary_passed",
            ),
        )
        self.assertEqual(
            phase_c_contracts.REJECTION_CASE_IDS,
            REJECTION_CASE_IDS,
        )
        self.assertEqual(
            phase_c_contracts.FAMILY_COUNT_ORDER,
            TASK_7_FAMILY_COUNT_ORDER,
        )
        self.assertEqual(
            phase_c_contracts.SIGNAL_FAMILY_COUNT_ORDER,
            TASK_7_SIGNAL_FAMILY_COUNT_ORDER,
        )
        self.assertEqual(
            phase_c_contracts.MODALITY_FAMILY_COUNT_ORDER,
            TASK_7_MODALITY_FAMILY_COUNT_ORDER,
        )
        self.assertEqual(
            phase_c_contracts.EMITTED_ABSTENTION_COUNT_ORDER,
            TASK_7_EMITTED_ABSTENTION_COUNT_ORDER,
        )
        self.assertEqual(
            phase_c_contracts.INVARIANT_NAMES,
            TASK_7_INVARIANT_NAMES,
        )
        self.assertEqual(
            phase_c_contracts.SAFETY_INVARIANT_NAMES,
            TASK_7_SAFETY_INVARIANT_NAMES,
        )
        mappings = (
            (
                phase_c_contracts.UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE,
                TASK_7_UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE,
            ),
            (
                phase_c_contracts.EXPECTED_COUNTS_BY_FAMILY,
                TASK_7_EXPECTED_COUNTS_BY_FAMILY,
            ),
            (
                phase_c_contracts.EXPECTED_COUNTS_BY_SIGNAL_FAMILY,
                TASK_7_EXPECTED_COUNTS_BY_SIGNAL_FAMILY,
            ),
            (
                phase_c_contracts.EXPECTED_COUNTS_BY_MODALITY_FAMILY,
                TASK_7_EXPECTED_COUNTS_BY_MODALITY_FAMILY,
            ),
            (
                phase_c_contracts.EXPECTED_COUNTS_BY_ABSTENTION_REASON,
                TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON,
            ),
        )
        for actual, expected in mappings:
            with self.subTest(mapping=expected):
                self.assertEqual(type(actual).__name__, "mappingproxy")
                self.assertEqual(dict(actual), expected)
                with self.assertRaises(TypeError):
                    actual[next(iter(expected))] = 999

    def test_all_30_frozen_scenarios_match_golden_expectations(self) -> None:
        evaluation = self.evaluation()
        self.assertEqual(evaluation.total_scenarios, 30)
        self.assertEqual(evaluation.passed_scenarios, 30)
        self.assertEqual(evaluation.failed_scenarios, 0)
        self.assertEqual(
            tuple(item.case_id for item in evaluation.outcomes),
            EXPECTED_SCENARIO_IDS_FOR_TEST,
        )
        self.assertTrue(all(item.passed for item in evaluation.outcomes))
        self.assertTrue(
            all(item.failed_invariants == () for item in evaluation.outcomes),
        )

    def test_green_aggregate_uses_exact_dense_order_counts_and_algebra(
        self,
    ) -> None:
        evaluation = self.evaluation()
        self.assertEqual(
            evaluation.counts_by_family,
            tuple(
                (name, TASK_7_EXPECTED_COUNTS_BY_FAMILY[name])
                for name in TASK_7_FAMILY_COUNT_ORDER
            ),
        )
        self.assertEqual(
            evaluation.counts_by_signal,
            tuple(
                (name, TASK_7_EXPECTED_COUNTS_BY_SIGNAL_FAMILY[name])
                for name in TASK_7_SIGNAL_FAMILY_COUNT_ORDER
            ),
        )
        self.assertEqual(
            evaluation.counts_by_modality,
            tuple(
                (name, TASK_7_EXPECTED_COUNTS_BY_MODALITY_FAMILY[name])
                for name in TASK_7_MODALITY_FAMILY_COUNT_ORDER
            ),
        )
        self.assertEqual(
            evaluation.counts_by_abstention_reason,
            tuple(
                (name, TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON[name])
                for name in TASK_7_EMITTED_ABSTENTION_COUNT_ORDER
            ),
        )
        self.assertEqual(
            evaluation.invariant_counts,
            tuple((name, 0) for name in TASK_7_INVARIANT_NAMES),
        )
        self.assertTrue(evaluation.deterministic_replay_passed)
        self.assertTrue(evaluation.privacy_boundary_passed)
        by_case = {outcome.case_id: outcome for outcome in evaluation.outcomes}
        for case_id in EXPECTED_SCENARIO_IDS_FOR_TEST:
            with self.subTest(case_id=case_id):
                outcome = by_case[case_id]
                self.assertEqual(
                    (
                        outcome.family,
                        outcome.signal_family,
                        outcome.modality_family,
                    ),
                    EXPECTED_SCENARIO_CLASSIFICATIONS_FOR_TEST[case_id],
                )
                self.assertEqual(
                    tuple(name for name, _count in outcome.abstention_reason_counts),
                    TASK_7_EMITTED_ABSTENTION_COUNT_ORDER,
                )
                expected_rejections = (
                    4
                    if case_id == "forbidden_phase_b_field_rejected"
                    else int(case_id in REJECTION_CASE_IDS)
                )
                self.assertEqual(outcome.rejection_count, expected_rejections)

    def test_expected_outputs_are_not_built_by_the_reducer_renderer(self) -> None:
        source = inspect.getsource(
            self.tracker.evaluate_phase_c_scenarios,
        )
        self.assertNotIn("render_phase_c_report", source)
        self.assertNotIn("build_phase_c_result", source)

    def test_evaluator_has_no_io_runner_validator_or_fault_injection_api(
        self,
    ) -> None:
        source = inspect.getsource(
            self.tracker.evaluate_phase_c_scenarios,
        )
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)
        self.assertNotIn("load_json", source)
        signature = inspect.signature(
            self.tracker.evaluate_phase_c_scenarios,
        )
        self.assertEqual(tuple(signature.parameters), ("policy", "scenarios"))
        module_source = inspect.getsource(self.tracker)
        self.assertNotIn("emotion_state_phase_c_runner", module_source)
        self.assertNotIn("emotion_state_phase_c_validator", module_source)

    def test_golden_mutation_is_detected(self) -> None:
        scenario = self.case("explicit_confusion_entry")
        expected = scenario.expected_steps[0]
        mutated_internal = dataclasses.replace(
            expected.expected_internal,
            capped_net_support=(
                ("confusion", 699),
                *expected.expected_internal.capped_net_support[1:],
            ),
        )
        mutated = dataclasses.replace(
            scenario,
            expected_steps=(
                dataclasses.replace(
                    expected,
                    expected_internal=mutated_internal,
                ),
            ),
        )
        scenarios = dict(self.scenarios)
        scenarios[scenario.case_id] = mutated
        evaluation = self.tracker.evaluate_phase_c_scenarios(
            self.policy,
            scenarios,
        )
        self.assertEqual(evaluation.failed_scenarios, 1)
        outcome = evaluation.outcomes[0]
        self.assertIn("golden_projection", outcome.failed_invariants)

    def test_every_unexpected_rejection_acceptance_maps_to_safety_invariant(
        self,
    ) -> None:
        fixture = self.tracker.replay_validated_frames(
            self.case("explicit_confusion_entry").sessions[0].frames,
            self.policy,
        )
        accepted = (fixture.final_state, fixture.outputs[-1])
        original = self.tracker._execute_scenario_attempt
        for case_id, safety_invariant in (
            TASK_7_UNEXPECTED_ACCEPTANCE_SAFETY_INVARIANT_BY_CASE.items()
        ):
            def injected(prior, scenario, attempt, policy):
                index = scenario.attempt_order.index(attempt)
                expected = scenario.expected_steps[index]
                if (
                    scenario.case_id == case_id
                    and expected.disposition == "rejected"
                ):
                    return accepted
                return original(prior, scenario, attempt, policy)

            with self.subTest(case_id=case_id):
                with mock.patch.object(
                    self.tracker,
                    "_execute_scenario_attempt",
                    side_effect=injected,
                ):
                    evaluation = self.evaluation()
                outcome = next(
                    item
                    for item in evaluation.outcomes
                    if item.case_id == case_id
                )
                self.assertIn("golden_projection", outcome.failed_invariants)
                self.assertIn(safety_invariant, outcome.failed_invariants)
                self.assertEqual(evaluation.failed_scenarios, 1)

    def test_unexpected_acceptance_never_installs_rejected_successor(
        self,
    ) -> None:
        fixture = self.tracker.replay_validated_frames(
            self.case("explicit_confusion_entry").sessions[0].frames,
            self.policy,
        )
        accepted = (fixture.final_state, fixture.outputs[-1])
        original = self.tracker._execute_scenario_attempt
        observed_priors = []

        def injected(prior, scenario, attempt, policy):
            if scenario.case_id == "forbidden_phase_b_field_rejected":
                observed_priors.append(prior)
                return accepted
            return original(prior, scenario, attempt, policy)

        with mock.patch.object(
            self.tracker,
            "_execute_scenario_attempt",
            side_effect=injected,
        ):
            evaluation = self.evaluation()
        self.assertEqual(observed_priors, [None, None, None, None])
        self.assertEqual(evaluation.failed_scenarios, 1)

    def test_unexpected_acceptance_detects_changed_aliased_prior(self) -> None:
        fixture = self.tracker.replay_validated_frames(
            self.case("explicit_confusion_entry").sessions[0].frames,
            self.policy,
        )
        accepted = (fixture.final_state, fixture.outputs[-1])
        original = self.tracker._execute_scenario_attempt

        def injected(prior, scenario, attempt, policy):
            expected = scenario.expected_steps[
                scenario.attempt_order.index(attempt)
            ]
            if (
                scenario.case_id == "cross_session_rejected"
                and expected.disposition == "rejected"
            ):
                object.__setattr__(
                    prior,
                    "accepted_turn_count",
                    prior.accepted_turn_count + 1,
                )
                return accepted
            return original(prior, scenario, attempt, policy)

        with mock.patch.object(
            self.tracker,
            "_execute_scenario_attempt",
            side_effect=injected,
        ):
            evaluation = self.evaluation()
        self.assert_single_failure(
            evaluation,
            {
                "golden_projection",
                "rejection_no_mutation",
                "session_isolation",
            },
        )
        outcome = next(
            item
            for item in evaluation.outcomes
            if item.case_id == "cross_session_rejected"
        )
        self.assertEqual(
            outcome.failed_invariants,
            (
                "golden_projection",
                "rejection_no_mutation",
                "session_isolation",
            ),
        )
        self.assertEqual(
            dict(evaluation.invariant_counts),
            {
                "golden_projection": 1,
                "rejection_no_mutation": 1,
                "correction_semantic_replay": 0,
                "session_isolation": 1,
                "deterministic_replay": 0,
                "semantic_output": 0,
                "privacy_boundary": 0,
            },
        )
        self.assertFalse(evaluation.privacy_boundary_passed)

    def test_negative_evaluation_keeps_actual_abstention_counts(self) -> None:
        evaluation = _mechanical_negative_evaluation(self)
        self.assert_single_failure(evaluation, {"golden_projection"})
        actual = dict(evaluation.counts_by_abstention_reason)
        self.assertEqual(
            actual["missing_input"],
            TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON["missing_input"] + 1,
        )
        self.assertEqual(
            actual["insufficient_evidence"],
            TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON[
                "insufficient_evidence"
            ] + 1,
        )
        self.assertEqual(
            actual["contradictory_evidence"],
            TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON[
                "contradictory_evidence"
            ],
        )
        self.assertEqual(
            actual["low_audio_quality"],
            TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON["low_audio_quality"],
        )

    def test_invalid_returned_dict_is_semantic_and_privacy_failure(self) -> None:
        evaluation = _semantic_negative_evaluation(self)
        self.assert_single_failure(
            evaluation,
            {"golden_projection", "semantic_output"},
        )
        self.assertFalse(evaluation.privacy_boundary_passed)

    def test_direct_semantic_exception_is_not_mechanical_only(self) -> None:
        original = self.tracker._execute_scenario_attempt

        def injected(prior, scenario, attempt, policy):
            expected = scenario.expected_steps[scenario.attempt_order.index(attempt)]
            if (
                scenario.case_id == "explicit_confusion_entry"
                and expected.disposition == "accepted"
            ):
                raise PhaseCOutputSemanticError("runtime_approved")
            return original(prior, scenario, attempt, policy)

        with mock.patch.object(
            self.tracker,
            "_execute_scenario_attempt",
            side_effect=injected,
        ):
            evaluation = self.evaluation()
        self.assert_single_failure(
            evaluation,
            {"golden_projection", "semantic_output"},
        )
        self.assertFalse(evaluation.privacy_boundary_passed)

    def test_non_mapping_nonserializable_output_fails_closed(self) -> None:
        evaluation = _structural_semantic_negative_evaluation(self)
        self.assert_single_failure(
            evaluation,
            {"golden_projection", "semantic_output"},
        )
        self.assertFalse(evaluation.privacy_boundary_passed)

    def test_semantic_validation_precedes_comparison_install_and_count(
        self,
    ) -> None:
        evaluation = _semantic_negative_evaluation(self)
        self.assertEqual(
            dict(evaluation.counts_by_abstention_reason),
            TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON,
        )
        next_outcome = evaluation.outcomes[1]
        self.assertTrue(next_outcome.passed)

    def test_special_replay_correction_and_isolation_checks_execute(
        self,
    ) -> None:
        with mock.patch.object(
            self.tracker,
            "canonical_semantic_replay_bytes",
            wraps=self.tracker.canonical_semantic_replay_bytes,
        ) as semantic_bytes, mock.patch.object(
            self.tracker,
            "replay_validated_frames",
            wraps=self.tracker.replay_validated_frames,
        ) as replay, mock.patch.object(
            self.tracker,
            "advance",
            wraps=self.tracker.advance,
        ) as advance:
            evaluation = self.evaluation()
        self.assertEqual(evaluation.failed_scenarios, 0)
        self.assertGreaterEqual(semantic_bytes.call_count, 2)
        self.assertGreaterEqual(replay.call_count, 5)
        self.assertGreater(advance.call_count, 0)

    def test_deterministic_replay_fail_open_mutation_is_classified(self) -> None:
        target = self.case("canonical_replay_bytes").sessions[0].frames
        original = self.tracker.replay_validated_frames
        target_calls = 0

        def injected(frames, policy):
            nonlocal target_calls
            result = original(frames, policy)
            if frames != target:
                return result
            target_calls += 1
            if target_calls != 2:
                return result
            mutated_output = copy.deepcopy(result.outputs[-1])
            mutated_output["runtime_approved"] = True
            return dataclasses.replace(
                result,
                outputs=(*result.outputs[:-1], mutated_output),
            )

        with mock.patch.object(
            self.tracker,
            "replay_validated_frames",
            side_effect=injected,
        ):
            evaluation = self.evaluation()
        self.assert_single_failure(evaluation, {"deterministic_replay"})
        self.assertTrue(evaluation.privacy_boundary_passed)

    def test_correction_semantic_fail_open_mutation_is_classified(self) -> None:
        with mock.patch.object(
            self.tracker,
            "canonical_semantic_replay_bytes",
            side_effect=(b"corrected", b"fresh"),
        ):
            evaluation = self.evaluation()
        self.assert_single_failure(
            evaluation,
            {"correction_semantic_replay"},
        )
        self.assertTrue(evaluation.privacy_boundary_passed)

    def test_session_cross_feed_fail_open_mutation_is_classified(self) -> None:
        original = self.tracker.advance

        def injected(prior, frame, policy):
            if (
                prior is not None
                and "simultaneous_sessions_isolated"
                in prior.call_session_id
                and prior.call_session_id != frame.call_session_id
            ):
                return prior, {}
            return original(prior, frame, policy)

        with mock.patch.object(
            self.tracker,
            "advance",
            side_effect=injected,
        ):
            evaluation = self.evaluation()
        self.assert_single_failure(evaluation, {"session_isolation"})
        self.assertFalse(evaluation.privacy_boundary_passed)

    def test_invalid_output_is_not_installed_before_next_attempt(self) -> None:
        original = self.tracker._execute_scenario_attempt
        observed_priors = []

        def injected(prior, scenario, attempt, policy):
            if scenario.case_id == "transcript_three_turn_entry":
                observed_priors.append(prior)
                successor, output = original(
                    prior,
                    scenario,
                    attempt,
                    policy,
                )
                if len(observed_priors) == 1:
                    invalid = copy.deepcopy(output)
                    invalid["runtime_approved"] = True
                    return successor, invalid
                return successor, output
            return original(prior, scenario, attempt, policy)

        with mock.patch.object(
            self.tracker,
            "_execute_scenario_attempt",
            side_effect=injected,
        ):
            evaluation = self.evaluation()
        self.assertIsNone(observed_priors[0])
        self.assertIsNone(observed_priors[1])
        self.assert_single_failure(
            evaluation,
            {"golden_projection", "semantic_output"},
        )

    def test_exact_internal_projection_has_only_18_authority_fields(
        self,
    ) -> None:
        replay = self.tracker.replay_validated_frames(
            self.case("explicit_confusion_entry").sessions[0].frames,
            self.policy,
        )
        projection = self.tracker.exact_internal_projection(
            replay.final_state,
        )
        self.assertEqual(
            tuple(projection),
            (
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
            ),
        )
        for name in (
            "gross_supporting_units",
            "gross_opposing_units",
            "uncapped_net_support",
            "capped_net_support",
            "entry_confirmation_keys_by_signal",
        ):
            with self.subTest(name=name):
                self.assertIs(type(projection[name]), dict)
                self.assertEqual(
                    tuple(projection[name]),
                    tuple(self.policy["canonical_signal_order"]),
                )

    def test_privacy_inspection_recursively_fails_closed(self) -> None:
        forbidden_values = (
            {"nested": [{"raw_audio": False}]},
            {"nested": ["evidence:uuid:00000000-0000-4000-8000-000000000001"]},
            {"nested": ["ind:explicit_confusion_entry:A:0:0:0"]},
            {"nested": ["explicit_confusion_entry"]},
            {"nested": [object()]},
        )
        for value in forbidden_values:
            with self.subTest(value=repr(value)):
                self.assertTrue(
                    self.tracker._phase_c_privacy_inspection_failed(value),
                )
        self.assertFalse(
            self.tracker._phase_c_privacy_inspection_failed({
                "counts": {
                    "entry": 7,
                    "semantic_output": 0,
                },
                "deterministic_replay_passed": True,
                "privacy_boundary_passed": True,
            }),
        )

    def test_privacy_inspection_rejects_exact_recipe_identity_prefixes(
        self,
    ) -> None:
        identities = (
            "evidence:uuid:00000000-0000-4000-8000-000000000001",
            "ind:fixture:1:1",
            "session:fixture:A",
            "turn:fixture:0",
            "event:fixture:A:0:0",
            "campaign:phase-c0",
            "version:1",
        )
        for identity in identities:
            with self.subTest(identity=identity):
                self.assertTrue(
                    self.tracker._phase_c_privacy_inspection_failed({
                        "nested": [identity],
                    }),
                )

    def test_privacy_failure_rebuilds_exact_outcome_algebra_once(self) -> None:
        with mock.patch.object(
            self.tracker,
            "_phase_c_privacy_inspection_failed",
            return_value=True,
        ):
            evaluation = self.evaluation()
        self.assert_single_failure(evaluation, {"privacy_boundary"})
        self.assertEqual(
            evaluation.outcomes[0].case_id,
            "explicit_confusion_entry",
        )
        self.assertFalse(evaluation.privacy_boundary_passed)

    def test_aggregate_retains_only_allowlisted_immutable_fields(self) -> None:
        evaluation = self.evaluation()
        self.assertTrue(evaluation.outcomes)
        for outcome in evaluation.outcomes:
            values = dataclasses.asdict(outcome)
            self.assertEqual(
                set(values),
                {
                    "case_id",
                    "family",
                    "signal_family",
                    "modality_family",
                    "passed",
                    "failed_invariants",
                    "rejection_count",
                    "abstention_reason_counts",
                },
            )
            self.assertTrue(
                all(
                    fragment not in repr(values)
                    for fragment in (
                        "accepted_frames",
                        "evidence_atoms",
                        "watermark",
                        "event_id",
                        "turn_id",
                        "call_session_id",
                        "evidence:uuid:",
                        "ind:",
                    )
                ),
            )


class PhaseCAggregateRunnerTests(PhaseCTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from scripts import emotion_state_phase_c_temporal_tracker
        from scripts import run_emotion_state_003_phase_c0

        cls.tracker = emotion_state_phase_c_temporal_tracker
        cls.runner = run_emotion_state_003_phase_c0
        cls.raw_policy = load_json_strict(POLICY_PATH)
        cls.policy = validate_phase_c_policy(copy.deepcopy(cls.raw_policy))
        cls.raw_scenarios = load_json_strict(SCENARIO_PATH)
        parsed = phase_c_contracts.validate_phase_c_scenario_payload(
            copy.deepcopy(cls.raw_scenarios),
            cls.policy,
        )
        cls.scenarios = {scenario.case_id: scenario for scenario in parsed}
        cls.evaluation = cls.tracker.evaluate_phase_c_scenarios(
            cls.policy,
            cls.scenarios,
        )
        cls.policy_bytes = canonical_json_bytes(cls.raw_policy)
        cls.scenario_bytes = canonical_json_bytes(cls.raw_scenarios)

    def setUp(self) -> None:
        pass

    @contextmanager
    def candidate_root(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            root = Path(temporary) / "emotion-state-003-phase-c0" / "candidate"
            with mock.patch.object(self.runner, "CANDIDATE_ROOT", root):
                yield root

    def pair_bytes(self) -> tuple[bytes, bytes, dict[str, Any]]:
        result = self.runner.build_phase_c_result(
            self.evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        report = self.runner.render_phase_c_report(result)
        return canonical_json_bytes(result), report.encode("utf-8"), result

    def rebound(self, result: dict[str, Any]) -> dict[str, Any]:
        rebound = copy.deepcopy(result)
        rebound.pop("aggregate_output_sha256", None)
        digest = sha256_bytes(canonical_json_bytes(rebound))
        rebound["aggregate_output_sha256"] = digest
        return rebound

    def test_result_is_aggregate_only_and_decision_is_keep(self) -> None:
        result = self.runner.build_phase_c_result(
            self.evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.assertEqual(result["decision"], "keep")
        self.assertEqual(result["scenario_counts"]["total"], 30)
        self.assertEqual(result["scenario_counts"]["failed"], 0)
        self.assertEqual(result["scenario_counts"]["rejection_cases"], 8)
        self.assertEqual(
            result["complexity"]["numeric_policy_parameter_count"],
            36,
        )
        self.assertEqual(
            result["policy_sha256"],
            sha256_bytes(canonical_json_bytes(self.raw_policy)),
        )
        self.assertEqual(
            result["scenario_sha256"],
            sha256_bytes(canonical_json_bytes(self.raw_scenarios)),
        )
        serialized = canonical_json_bytes(result).decode("utf-8").lower()
        for forbidden in (
            "evidence:uuid:",
            "session:",
            "turn:",
            "event:",
            "campaign:",
            "version:",
            "ind:",
            "case_id",
            "evidence_atoms",
            "accepted_frames",
            "confidence_by_signal",
            "transcript_text",
            "audio_bytes",
        ):
            self.assertNotIn(forbidden, serialized)
        for case_id in EXPECTED_SCENARIO_IDS_FOR_TEST:
            self.assertNotIn(case_id, serialized)

    def test_result_schema_identities_shapes_and_selfless_digest_are_exact(
        self,
    ) -> None:
        result = self.runner.build_phase_c_result(
            self.evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.assertEqual(set(result), self.runner.PHASE_C_RESULT_FIELDS)
        self.assertEqual(
            (
                result["schema_version"],
                result["checkpoint_id"],
                result["policy_id"],
                result["evidence_policy_version"],
            ),
            (
                "EmotionStatePhaseC0AggregateResultV1",
                "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics",
                "emotion-state-phase-c0-synthetic-v1",
                "emotion-state-evidence-v2",
            ),
        )
        self.assertEqual(
            set(result["scenario_counts"]),
            {"total", "passed", "failed", "rejection_cases"},
        )
        self.assertEqual(
            set(result["complexity"]),
            {
                "numeric_policy_parameter_count",
                "scenario_count",
                "operational_signal_count",
                "synthetic_evidence_class_count",
                "runtime_files_modified",
            },
        )
        self.assertEqual(
            tuple(result["counts_by_family"]),
            tuple(sorted(TASK_7_FAMILY_COUNT_ORDER)),
        )
        self.assertEqual(
            tuple(result["counts_by_signal"]),
            tuple(sorted(TASK_7_SIGNAL_FAMILY_COUNT_ORDER)),
        )
        self.assertEqual(
            tuple(result["counts_by_modality"]),
            tuple(sorted(TASK_7_MODALITY_FAMILY_COUNT_ORDER)),
        )
        self.assertEqual(
            tuple(result["counts_by_abstention_reason"]),
            tuple(sorted(TASK_7_EMITTED_ABSTENTION_COUNT_ORDER)),
        )
        self.assertEqual(
            tuple(result["invariant_counts"]),
            tuple(sorted(TASK_7_INVARIANT_NAMES)),
        )
        without_digest = copy.deepcopy(result)
        aggregate_digest = without_digest.pop("aggregate_output_sha256")
        self.assertEqual(
            aggregate_digest,
            sha256_bytes(canonical_json_bytes(without_digest)),
        )

    def test_recursive_numeric_policy_count_excludes_booleans(self) -> None:
        self.assertEqual(
            self.runner._count_exact_int_leaves({
                "a": 1,
                "b": True,
                "c": [2, False, {"d": 3}],
                "e": "4",
            }),
            3,
        )

    def test_noncanonical_policy_or_scenario_bytes_fail_closed(self) -> None:
        for policy_bytes, scenario_bytes in (
            (self.policy_bytes.replace(b"\n", b"\r\n"), self.scenario_bytes),
            (self.policy_bytes + b"\n", self.scenario_bytes),
            (self.policy_bytes, self.scenario_bytes.replace(b"\n", b"\r\n")),
            (self.policy_bytes, self.scenario_bytes + b"\n"),
        ):
            with self.subTest(
                policy_length=len(policy_bytes),
                scenario_length=len(scenario_bytes),
            ):
                with self.assertRaises(self.runner.RunnerError):
                    self.runner.build_phase_c_result(
                        self.evaluation,
                        policy_bytes,
                        scenario_bytes,
                    )

    def test_duplicate_key_and_nonfinite_input_bytes_fail_closed(self) -> None:
        duplicate_policy = (
            b'{"policy_id":"emotion-state-phase-c0-synthetic-v1",'
            b'"policy_id":"emotion-state-phase-c0-synthetic-v1"}\n'
        )
        nonfinite_scenarios = b'{"schema_version":NaN}\n'
        for policy_bytes, scenario_bytes in (
            (duplicate_policy, self.scenario_bytes),
            (self.policy_bytes, nonfinite_scenarios),
        ):
            with self.assertRaises(self.runner.RunnerError):
                self.runner.build_phase_c_result(
                    self.evaluation,
                    policy_bytes,
                    scenario_bytes,
                )

    def test_report_is_deterministic_exact_lf_and_hash_binds_result(
        self,
    ) -> None:
        result = self.runner.build_phase_c_result(
            self.evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        first = self.runner.render_phase_c_report(result)
        second = self.runner.render_phase_c_report(copy.deepcopy(result))
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        self.assertFalse(first.endswith("\n\n"))
        self.assertNotIn("\r", first)
        digest = sha256_bytes(canonical_json_bytes(result))
        self.assertIn(f"result.json sha256:{digest}", first)
        self.assertEqual(first, self.runner._report_template(result, digest))
        for required in (
            "Scope: synthetic mechanics only; no customer emotion inference or runtime policy enforcement is proven.",
            "Runtime status: not approved and not activated.",
            "Boundary status: no Phase B input, public/private data, provider, call, conversation simulation, or source adaptation was used.",
            "Readiness: production readiness is not proven.",
        ):
            self.assertIn(required, first)
        for case_id in EXPECTED_SCENARIO_IDS_FOR_TEST:
            self.assertNotIn(case_id, first)

    def test_output_root_is_exactly_allowlisted(self) -> None:
        with self.assertRaisesRegex(
            self.runner.RunnerError,
            "output_root_not_allowlisted",
        ):
            self.runner.resolve_output_root("candidate", ROOT / "outside")
        with self.assertRaisesRegex(self.runner.RunnerError, "runner_mode"):
            self.runner.resolve_output_root("Candidate")
        with self.candidate_root() as root:
            self.assertEqual(
                self.runner.resolve_output_root("candidate", root),
                root,
            )
            for escaped in (
                f"{root.parent}{os.sep}.{os.sep}candidate",
                (
                    f"{root.parent}{os.sep}..{os.sep}"
                    f"{root.parent.name}{os.sep}candidate"
                ),
            ):
                with self.subTest(escaped=str(escaped)):
                    with self.assertRaisesRegex(
                        self.runner.RunnerError,
                        "output_root_not_allowlisted",
                    ):
                        self.runner.resolve_output_root(
                            "candidate",
                            str(escaped),
                        )

    def test_cli_accepts_exactly_one_mode_without_output_root(self) -> None:
        self.assertEqual(self.runner._parse_cli_mode(["candidate"]), "candidate")
        self.assertEqual(self.runner._parse_cli_mode(["canonical"]), "canonical")
        for argv in ([], ["Candidate"], ["candidate", "outside"]):
            with self.subTest(argv=argv):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "runner_mode",
                ):
                    self.runner._parse_cli_mode(argv)

    def test_direct_script_invalid_launch_reaches_runner_mode_without_output(
        self,
    ) -> None:
        candidate = self.runner.CANDIDATE_ROOT
        stage = Path(f"{candidate}.stage")
        for arguments in ((), ("invalid-mode",)):
            before = tuple(
                _bounded_no_follow_root_snapshot(path)
                for path in (candidate, stage)
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "run_emotion_state_003_phase_c0.py"),
                    *arguments,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            with self.subTest(arguments=arguments):
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("RunnerError: runner_mode", completed.stderr)
                self.assertNotIn("ModuleNotFoundError", completed.stderr)
                self.assertEqual(completed.stdout, "")
                self.assertEqual(
                    tuple(
                        _bounded_no_follow_root_snapshot(path)
                        for path in (candidate, stage)
                    ),
                    before,
                )

    def test_safety_failure_discards_and_mechanical_failure_revises(
        self,
    ) -> None:
        zero = {name: 0 for name in TASK_7_INVARIANT_NAMES}
        safe_flags = {
            name: False
            for name in self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES
        }
        unsafe = dict(zero)
        unsafe["privacy_boundary"] = 1
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                failed_scenarios=1,
                invariant_counts=unsafe,
                deterministic_replay_passed=True,
                privacy_boundary_passed=False,
                claim_or_consumption_flags=safe_flags,
            ),
            "discard",
        )
        mechanical = dict(zero)
        mechanical["golden_projection"] = 1
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                failed_scenarios=1,
                invariant_counts=mechanical,
                deterministic_replay_passed=True,
                privacy_boundary_passed=True,
                claim_or_consumption_flags=safe_flags,
            ),
            "revise",
        )
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                failed_scenarios=0,
                invariant_counts=zero,
                deterministic_replay_passed=True,
                privacy_boundary_passed=True,
                claim_or_consumption_flags=safe_flags,
            ),
            "keep",
        )

    def test_decision_inputs_use_exact_keys_types_and_precedence(self) -> None:
        zero = {name: 0 for name in TASK_7_INVARIANT_NAMES}
        safe_flags = {
            name: False
            for name in self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES
        }
        mutations = (
            {"failed_scenarios": True},
            {"failed_scenarios": -1},
            {"invariant_counts": {**zero, "extra": 0}},
            {"invariant_counts": {**zero, "golden_projection": True}},
            {"deterministic_replay_passed": 1},
            {"privacy_boundary_passed": 1},
            {
                "claim_or_consumption_flags": {
                    **safe_flags,
                    "extra": False,
                },
            },
            {
                "claim_or_consumption_flags": {
                    **safe_flags,
                    "phase_b_inputs_consumed": 0,
                },
            },
        )
        baseline = {
            "failed_scenarios": 0,
            "invariant_counts": zero,
            "deterministic_replay_passed": True,
            "privacy_boundary_passed": True,
            "claim_or_consumption_flags": safe_flags,
        }
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                **{
                    **baseline,
                    "invariant_counts": dict(reversed(tuple(zero.items()))),
                    "claim_or_consumption_flags": dict(
                        reversed(tuple(safe_flags.items())),
                    ),
                },
            ),
            "keep",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "decision_inputs",
                ):
                    self.runner.decide_phase_c_checkpoint(
                        **{**baseline, **mutation},
                    )
        for flag in self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES:
            with self.subTest(flag=flag):
                flags = {**safe_flags, flag: True}
                self.assertEqual(
                    self.runner.decide_phase_c_checkpoint(
                        **{
                            **baseline,
                            "failed_scenarios": 1,
                            "claim_or_consumption_flags": flags,
                        },
                    ),
                    "discard",
                )

    def test_decision_snapshots_hostile_mappings_once_and_fails_closed(
        self,
    ) -> None:
        class DisagreeingMapping(ABCMapping):
            def __init__(
                self,
                keys,
                hidden,
                advertised,
                *,
                failing_key=None,
            ):
                self._keys = tuple(keys)
                self._hidden = dict(hidden)
                self._advertised = tuple(advertised)
                self._failing_key = failing_key
                self.accesses = []
                self.values_calls = 0

            def __iter__(self):
                return iter(self._keys)

            def __len__(self):
                return len(self._keys)

            def __getitem__(self, key):
                self.accesses.append(key)
                if key == self._failing_key:
                    raise PermissionError("hidden access failure")
                return self._hidden[key]

            def values(self):
                self.values_calls += 1
                return iter(self._advertised)

        zero = {name: 0 for name in TASK_7_INVARIANT_NAMES}
        safe_flags = {
            name: False
            for name in self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES
        }

        valid_invariants = DisagreeingMapping(
            reversed(TASK_7_INVARIANT_NAMES),
            zero,
            (object(),),
        )
        valid_flags = DisagreeingMapping(
            reversed(self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES),
            safe_flags,
            (object(),),
        )
        self.assertEqual(
            self.runner.decide_phase_c_checkpoint(
                failed_scenarios=0,
                invariant_counts=valid_invariants,
                deterministic_replay_passed=True,
                privacy_boundary_passed=True,
                claim_or_consumption_flags=valid_flags,
            ),
            "keep",
        )
        self.assertEqual(
            valid_invariants.accesses,
            list(TASK_7_INVARIANT_NAMES),
        )
        self.assertEqual(
            valid_flags.accesses,
            list(self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES),
        )
        self.assertEqual(valid_invariants.values_calls, 0)
        self.assertEqual(valid_flags.values_calls, 0)

        hostile_inputs = (
            (
                DisagreeingMapping(
                    TASK_7_INVARIANT_NAMES,
                    {**zero, "golden_projection": -1},
                    zero.values(),
                ),
                safe_flags,
            ),
            (
                DisagreeingMapping(
                    TASK_7_INVARIANT_NAMES,
                    {**zero, "privacy_boundary": "hidden"},
                    zero.values(),
                ),
                safe_flags,
            ),
            (
                zero,
                DisagreeingMapping(
                    self.runner.CLAIM_OR_CONSUMPTION_FLAG_NAMES,
                    {**safe_flags, "provider_or_call_used": 1},
                    safe_flags.values(),
                ),
            ),
            (
                DisagreeingMapping(
                    TASK_7_INVARIANT_NAMES,
                    zero,
                    zero.values(),
                    failing_key="session_isolation",
                ),
                safe_flags,
            ),
        )
        for invariant_counts, claim_flags in hostile_inputs:
            with self.subTest(
                invariants=type(invariant_counts).__name__,
                flags=type(claim_flags).__name__,
            ):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "decision_inputs",
                ):
                    self.runner.decide_phase_c_checkpoint(
                        failed_scenarios=0,
                        invariant_counts=invariant_counts,
                        deterministic_replay_passed=True,
                        privacy_boundary_passed=True,
                        claim_or_consumption_flags=claim_flags,
                    )

    def test_mechanical_negative_evaluation_builds_coherent_revise_pair(
        self,
    ) -> None:
        evaluation = _mechanical_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.runner.validate_phase_c_result_payload(result)
        self.assertEqual(result["scenario_counts"]["failed"], 1)
        self.assertEqual(result["decision"], "revise")
        self.assertEqual(
            result["counts_by_abstention_reason"]["missing_input"],
            TASK_7_EXPECTED_COUNTS_BY_ABSTENTION_REASON["missing_input"] + 1,
        )
        report = self.runner.render_phase_c_report(result)
        self.assertIn("Decision: revise", report)

    def test_semantic_negative_evaluation_builds_coherent_discard_pair(
        self,
    ) -> None:
        evaluation = _semantic_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.runner.validate_phase_c_result_payload(result)
        self.assertEqual(result["invariant_counts"]["semantic_output"], 1)
        self.assertFalse(result["privacy_boundary_passed"])
        self.assertEqual(result["decision"], "discard")
        report = self.runner.render_phase_c_report(result)
        self.assertIn("Decision: discard", report)

    def test_non_json_output_still_builds_coherent_discard_pair(self) -> None:
        evaluation = _structural_semantic_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        self.runner.validate_phase_c_result_payload(result)
        self.assertEqual(result["scenario_counts"]["failed"], 1)
        self.assertEqual(result["invariant_counts"]["semantic_output"], 1)
        self.assertEqual(result["decision"], "discard")

    def test_evaluation_validation_rejects_forged_shapes_and_algebra(
        self,
    ) -> None:
        first = self.evaluation.outcomes[0]
        first_abstention = dict(first.abstention_reason_counts)
        mutations = (
            dataclasses.replace(self.evaluation, total_scenarios=True),
            dataclasses.replace(self.evaluation, passed_scenarios=31),
            dataclasses.replace(
                self.evaluation,
                counts_by_family=tuple(reversed(self.evaluation.counts_by_family)),
            ),
            dataclasses.replace(
                self.evaluation,
                invariant_counts=(
                    *self.evaluation.invariant_counts,
                    ("extra", 0),
                ),
            ),
            dataclasses.replace(
                self.evaluation,
                deterministic_replay_passed=1,
            ),
            dataclasses.replace(
                self.evaluation,
                outcomes=(
                    dataclasses.replace(first, case_id="forged"),
                    *self.evaluation.outcomes[1:],
                ),
            ),
            dataclasses.replace(
                self.evaluation,
                outcomes=(
                    dataclasses.replace(first, passed=False),
                    *self.evaluation.outcomes[1:],
                ),
            ),
            dataclasses.replace(
                self.evaluation,
                outcomes=(
                    dataclasses.replace(
                        first,
                        failed_invariants=("unknown",),
                        passed=False,
                    ),
                    *self.evaluation.outcomes[1:],
                ),
                passed_scenarios=29,
                failed_scenarios=1,
            ),
            dataclasses.replace(
                self.evaluation,
                outcomes=(
                    dataclasses.replace(first, rejection_count=1),
                    *self.evaluation.outcomes[1:],
                ),
            ),
            dataclasses.replace(
                self.evaluation,
                outcomes=(
                    dataclasses.replace(
                        first,
                        abstention_reason_counts=tuple(
                            (
                                name,
                                value + int(name == "missing_input"),
                            )
                            for name, value in first_abstention.items()
                        ),
                    ),
                    *self.evaluation.outcomes[1:],
                ),
            ),
            dataclasses.replace(
                self.evaluation,
                privacy_boundary_passed=False,
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=repr(mutation)[:120]):
                with self.assertRaises(self.runner.RunnerError):
                    self.runner.build_phase_c_result(
                        mutation,
                        self.policy_bytes,
                        self.scenario_bytes,
                    )

    def test_producer_validator_rejects_fail_open_result_mutations(
        self,
    ) -> None:
        result = self.runner.build_phase_c_result(
            self.evaluation,
            self.policy_bytes,
            self.scenario_bytes,
        )
        mutations: list[dict[str, Any]] = []
        extra = copy.deepcopy(result)
        extra["extra"] = False
        mutations.append(extra)
        missing = copy.deepcopy(result)
        missing.pop("production_readiness_proven")
        mutations.append(missing)
        nested = copy.deepcopy(result)
        nested["scenario_counts"]["extra"] = 0
        mutations.append(self.rebound(nested))
        bool_count = copy.deepcopy(result)
        bool_count["scenario_counts"]["total"] = True
        mutations.append(self.rebound(bool_count))
        missing_category = copy.deepcopy(result)
        missing_category["counts_by_family"].pop("entry")
        mutations.append(self.rebound(missing_category))
        changed_complexity = copy.deepcopy(result)
        changed_complexity["complexity"]["runtime_files_modified"] = 1
        mutations.append(self.rebound(changed_complexity))
        changed_decision = copy.deepcopy(result)
        changed_decision["decision"] = "revise"
        mutations.append(self.rebound(changed_decision))
        true_flag = copy.deepcopy(result)
        true_flag["phase_b_inputs_consumed"] = True
        true_flag["decision"] = "discard"
        mutations.append(self.rebound(true_flag))
        forbidden = copy.deepcopy(result)
        forbidden["policy_sha256"] = "case_id:" + ("0" * 56)
        mutations.append(self.rebound(forbidden))
        bad_digest = copy.deepcopy(result)
        bad_digest["aggregate_output_sha256"] = "0" * 64
        mutations.append(bad_digest)
        replay_mismatch = copy.deepcopy(result)
        replay_mismatch["deterministic_replay_passed"] = False
        replay_mismatch["decision"] = "discard"
        mutations.append(self.rebound(replay_mismatch))
        for mutation in mutations:
            with self.subTest(keys=tuple(mutation)):
                with self.assertRaises(self.runner.RunnerError):
                    self.runner.validate_phase_c_result_payload(mutation)

    def test_valid_pair_is_written_atomically_and_read_back_exactly(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            stage = Path(f"{root}.stage")
            written = self.runner.write_phase_c_pair(
                root,
                result_bytes,
                report_bytes,
            )
            self.assertEqual(written, root)
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {"result.json", "report.md"},
            )
            self.assertEqual((root / "result.json").read_bytes(), result_bytes)
            self.assertEqual((root / "report.md").read_bytes(), report_bytes)
            self.assertNotIn(b"\r", result_bytes)
            self.assertNotIn(b"\r", report_bytes)
            self.assertFalse(stage.exists())

    def test_absent_candidate_parent_is_created_and_unexpected_child_rejects(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            self.assertFalse(root.parent.exists())
            self.runner.write_phase_c_pair(root, result_bytes, report_bytes)
            self.assertTrue(root.parent.is_dir())
        with self.candidate_root() as root:
            root.parent.mkdir()
            (root.parent / "unexpected").mkdir()
            with self.assertRaisesRegex(
                self.runner.RunnerError,
                "output_parent_children",
            ):
                self.runner.write_phase_c_pair(
                    root,
                    result_bytes,
                    report_bytes,
                )
            self.assertFalse(root.exists())

    def test_existing_final_or_stage_fails_before_write_and_never_overwrites(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            self.runner.write_phase_c_pair(root, result_bytes, report_bytes)
            first_result = (root / "result.json").read_bytes()
            first_report = (root / "report.md").read_bytes()
            with self.assertRaisesRegex(
                self.runner.RunnerError,
                "output_exists",
            ):
                self.runner.write_phase_c_pair(
                    root,
                    result_bytes,
                    report_bytes,
                )
            self.assertEqual((root / "result.json").read_bytes(), first_result)
            self.assertEqual((root / "report.md").read_bytes(), first_report)
        with self.candidate_root() as root:
            root.parent.mkdir()
            stage = Path(f"{root}.stage")
            stage.mkdir()
            with self.assertRaisesRegex(
                self.runner.RunnerError,
                "stage_exists",
            ):
                self.runner.write_phase_c_pair(
                    root,
                    result_bytes,
                    report_bytes,
                )
            self.assertFalse(root.exists())
            self.assertEqual(tuple(stage.iterdir()), ())

    def test_no_follow_metadata_rejects_symlink_reparse_parent_and_child(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        for target_kind, metadata_kind in (
            ("parent", "reparse"),
            ("child", "reparse"),
            ("parent", "symlink"),
            ("child", "symlink"),
        ):
            with self.subTest(
                target_kind=target_kind,
                metadata_kind=metadata_kind,
            ):
                with self.candidate_root() as root:
                    root.parent.mkdir()
                    if target_kind == "child":
                        root.mkdir()
                    real_lstat = os.lstat

                    def injected(path):
                        metadata = real_lstat(path)
                        candidate = Path(path)
                        target = root.parent if target_kind == "parent" else root
                        if candidate == target:
                            values = {
                                name: getattr(metadata, name)
                                for name in dir(metadata)
                                if name.startswith("st_")
                            }
                            if metadata_kind == "reparse":
                                values["st_file_attributes"] = reparse_flag
                            else:
                                values["st_mode"] = stat.S_IFLNK
                            return SimpleNamespace(**values)
                        return metadata

                    with mock.patch.object(
                        self.runner.os,
                        "lstat",
                        side_effect=injected,
                    ):
                        with self.assertRaisesRegex(
                            self.runner.RunnerError,
                            "output_reparse_or_link",
                        ):
                            self.runner.write_phase_c_pair(
                                root,
                                result_bytes,
                                report_bytes,
                            )

    def test_unexpected_file_child_and_non_directory_ancestor_reject(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            root.parent.mkdir()
            root.write_bytes(b"occupied")
            with self.assertRaisesRegex(
                self.runner.RunnerError,
                "output_exists",
            ):
                self.runner.write_phase_c_pair(
                    root,
                    result_bytes,
                    report_bytes,
                )
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            blocked = Path(temporary) / "blocked"
            blocked.write_bytes(b"not-a-directory")
            root = blocked / "emotion-state-003-phase-c0" / "candidate"
            with mock.patch.object(self.runner, "CANDIDATE_ROOT", root):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "output_ancestor_type",
                ):
                    self.runner.write_phase_c_pair(
                        root,
                        result_bytes,
                        report_bytes,
                    )

    def test_injected_pre_rename_failure_cleans_only_verified_stage(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            stage = Path(f"{root}.stage")
            with mock.patch.object(
                self.runner.os,
                "rename",
                side_effect=OSError("injected"),
            ):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "atomic_rename_failed",
                ):
                    self.runner.write_phase_c_pair(
                        root,
                        result_bytes,
                        report_bytes,
                    )
            self.assertFalse(root.exists())
            self.assertFalse(stage.exists())
            self.assertTrue(root.parent.is_dir())

    def test_stage_readback_failure_cleans_and_final_readback_failure_retains_pair(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            with mock.patch.object(
                self.runner,
                "_verify_pair_directory",
                side_effect=self.runner.RunnerError(
                    "stage_readback_failed",
                ),
            ):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "stage_readback_failed",
                ):
                    self.runner.write_phase_c_pair(
                        root,
                        result_bytes,
                        report_bytes,
                    )
            self.assertFalse(root.exists())
            self.assertFalse(Path(f"{root}.stage").exists())
        with self.candidate_root() as root:
            with mock.patch.object(
                self.runner,
                "_verify_pair_directory",
                side_effect=(
                    None,
                    self.runner.RunnerError("final_readback_failed"),
                ),
            ):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "final_readback_failed",
                ):
                    self.runner.write_phase_c_pair(
                        root,
                        result_bytes,
                        report_bytes,
                    )
            self.assertTrue(root.is_dir())
            self.assertFalse(Path(f"{root}.stage").exists())
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {"result.json", "report.md"},
            )

    def test_root_metadata_errors_are_remapped_to_supplied_readback_code(
        self,
    ) -> None:
        for failure_code in (
            "stage_readback_failed",
            "final_readback_failed",
        ):
            with self.subTest(failure_code=failure_code):
                with self.candidate_root() as root:
                    with mock.patch.object(
                        self.runner.os,
                        "lstat",
                        side_effect=PermissionError("injected"),
                    ):
                        with self.assertRaisesRegex(
                            self.runner.RunnerError,
                            failure_code,
                        ):
                            self.runner._verify_pair_directory(
                                root,
                                b"result",
                                b"report",
                                failure_code,
                            )

    def test_injected_write_failure_cleans_stage_without_touching_sibling(
        self,
    ) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        with self.candidate_root() as root:
            root.parent.mkdir()
            sibling = root.parent.parent / "sibling"
            sibling.write_bytes(b"preserve")
            original = self.runner._write_exclusive_file
            calls = 0

            def injected(path, payload):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected")
                return original(path, payload)

            with mock.patch.object(
                self.runner,
                "_write_exclusive_file",
                side_effect=injected,
            ):
                with self.assertRaisesRegex(
                    self.runner.RunnerError,
                    "stage_write_failed",
                ):
                    self.runner.write_phase_c_pair(
                        root,
                        result_bytes,
                        report_bytes,
                    )
            self.assertFalse(root.exists())
            self.assertFalse(Path(f"{root}.stage").exists())
            self.assertEqual(sibling.read_bytes(), b"preserve")

    def test_writer_rejects_noncanonical_result_or_report_marker(self) -> None:
        result_bytes, report_bytes, _ = self.pair_bytes()
        cases = (
            (
                result_bytes.replace(b"\n", b"\r\n"),
                report_bytes,
                "result_bytes_invalid",
            ),
            (
                result_bytes,
                report_bytes.replace(b"result.json sha256:", b"result.json sha256:0"),
                "report_bytes_invalid",
            ),
            (
                result_bytes,
                report_bytes.replace(b"\n", b"\r\n"),
                "report_bytes_invalid",
            ),
        )
        for candidate_result, candidate_report, code in cases:
            with self.subTest(code=code):
                with self.candidate_root() as root:
                    with self.assertRaisesRegex(
                        self.runner.RunnerError,
                        code,
                    ):
                        self.runner.write_phase_c_pair(
                            root,
                            candidate_result,
                            candidate_report,
                        )
                    self.assertFalse(root.exists())
                    self.assertFalse(Path(f"{root}.stage").exists())

    def test_runner_module_exposes_no_mutable_container_globals(self) -> None:
        mutable_globals = {
            name: type(value).__name__
            for name, value in vars(self.runner).items()
            if not name.startswith("__")
            and type(value) in (dict, list, set)
        }
        self.assertEqual(mutable_globals, {})


TASK_9_RESULT_FIELDS_FOR_TEST = (
    "schema_version",
    "checkpoint_id",
    "policy_id",
    "evidence_policy_version",
    "policy_sha256",
    "scenario_sha256",
    "aggregate_output_sha256",
    "scenario_counts",
    "counts_by_family",
    "counts_by_signal",
    "counts_by_modality",
    "counts_by_abstention_reason",
    "invariant_counts",
    "deterministic_replay_passed",
    "privacy_boundary_passed",
    "phase_b_inputs_consumed",
    "public_or_private_data_consumed",
    "runtime_modified_or_activated",
    "provider_or_call_used",
    "policy_enforcement_proven",
    "emotion_accuracy_proven",
    "production_readiness_proven",
    "complexity",
    "decision",
)
TASK_9_SCALAR_FIELDS_FOR_TEST = (
    "schema_version",
    "checkpoint_id",
    "policy_id",
    "evidence_policy_version",
    "policy_sha256",
    "scenario_sha256",
    "aggregate_output_sha256",
    "deterministic_replay_passed",
    "privacy_boundary_passed",
    "phase_b_inputs_consumed",
    "public_or_private_data_consumed",
    "runtime_modified_or_activated",
    "provider_or_call_used",
    "policy_enforcement_proven",
    "emotion_accuracy_proven",
    "production_readiness_proven",
    "decision",
)
TASK_9_CLAIM_FIELDS_FOR_TEST = (
    "phase_b_inputs_consumed",
    "public_or_private_data_consumed",
    "runtime_modified_or_activated",
    "provider_or_call_used",
    "policy_enforcement_proven",
    "emotion_accuracy_proven",
    "production_readiness_proven",
)
TASK_9_AGGREGATE_MAPPING_FIELDS_FOR_TEST = (
    "scenario_counts",
    "counts_by_family",
    "counts_by_signal",
    "counts_by_modality",
    "counts_by_abstention_reason",
    "invariant_counts",
    "complexity",
)
TASK_9_SCOPE_LINES_FOR_TEST = (
    (
        "Scope: synthetic mechanics only; no customer emotion inference "
        "or runtime policy enforcement is proven."
    ),
    "Runtime status: not approved and not activated.",
    (
        "Boundary status: no Phase B input, public/private data, provider, "
        "call, conversation simulation, or source adaptation was used."
    ),
    "Readiness: production readiness is not proven.",
)
TASK_9_RENDERED_VALUE_PREFIXES_FOR_TEST = (
    "- Scenario counts: ",
    "- Counts by family: ",
    "- Counts by signal family: ",
    "- Counts by modality family: ",
    "- Counts by abstention reason: ",
    "- Invariant counts: ",
    "- Deterministic replay passed: ",
    "- Privacy boundary passed: ",
    "- Numeric policy parameters: ",
    "- Scenarios: ",
    "- Operational signals: ",
    "- Synthetic evidence classes: ",
    "- Runtime files modified: ",
)


def _task_9_rebind_aggregate_digest(payload: dict[str, Any]) -> None:
    if "aggregate_output_sha256" not in payload:
        return
    core = {
        key: value
        for key, value in payload.items()
        if key != "aggregate_output_sha256"
    }
    payload["aggregate_output_sha256"] = sha256_bytes(
        canonical_json_bytes(core),
    )


def build_result_contract_mutations(
    result: dict[str, Any],
) -> list[tuple[str, dict[str, Any], str]]:
    mutations: list[tuple[str, dict[str, Any], str]] = []

    def add(
        name: str,
        payload: dict[str, Any],
        code: str,
        *,
        rebind: bool = True,
    ) -> None:
        if rebind:
            _task_9_rebind_aggregate_digest(payload)
        mutations.append((name, payload, code))

    for field in TASK_9_RESULT_FIELDS_FOR_TEST:
        payload = copy.deepcopy(result)
        payload.pop(field)
        add(
            f"missing_top_level_{field}",
            payload,
            "result_field_set",
        )

    payload = copy.deepcopy(result)
    payload["unexpected"] = 0
    add("extra_top_level_field", payload, "result_field_set")

    for field in TASK_9_SCALAR_FIELDS_FOR_TEST:
        payload = copy.deepcopy(result)
        payload[field] = 0
        add(
            f"wrong_exact_type_{field}",
            payload,
            "result_scalar_type",
            rebind=(field != "aggregate_output_sha256"),
        )

    for field in TASK_9_AGGREGATE_MAPPING_FIELDS_FOR_TEST:
        mapping = result[field]
        first_key = next(iter(mapping))

        payload = copy.deepcopy(result)
        payload[field].pop(first_key)
        add(f"missing_nested_key_{field}", payload, "result_nested_shape")

        payload = copy.deepcopy(result)
        payload[field]["unexpected"] = 0
        add(f"extra_nested_key_{field}", payload, "result_nested_shape")

        payload = copy.deepcopy(result)
        payload[field][first_key] += 1
        add(
            f"wrong_nested_value_{field}",
            payload,
            (
                "result_complexity"
                if field == "complexity"
                else "result_count_algebra"
            ),
        )

        payload = copy.deepcopy(result)
        payload[field] = []
        add(f"wrong_container_type_{field}", payload, "result_nested_shape")

    for field, code in (
        ("policy_sha256", "result_policy_hash"),
        ("scenario_sha256", "result_scenario_hash"),
        ("aggregate_output_sha256", "result_aggregate_digest"),
    ):
        payload = copy.deepcopy(result)
        payload[field] = "0" * 64
        add(
            f"wrong_{field}",
            payload,
            code,
            rebind=(field != "aggregate_output_sha256"),
        )

    payload = copy.deepcopy(result)
    payload["decision"] = "revise"
    add("decision_contradiction", payload, "result_decision_semantics")

    payload = copy.deepcopy(result)
    payload["scenario_counts"]["passed"] = 29
    payload["scenario_counts"]["failed"] = 1
    payload["invariant_counts"]["golden_projection"] = 1
    add("failed_count_contradiction", payload, "result_decision_semantics")

    for field in TASK_9_CLAIM_FIELDS_FOR_TEST:
        payload = copy.deepcopy(result)
        payload[field] = True
        add(
            f"claim_boundary_contradiction_{field}",
            payload,
            "result_boundary_flags",
        )

    for field, invariant in (
        ("deterministic_replay_passed", "deterministic_replay"),
        ("privacy_boundary_passed", "privacy_boundary"),
    ):
        payload = copy.deepcopy(result)
        payload[field] = False
        add(
            f"replay_privacy_algebra_{field}",
            payload,
            "result_replay_privacy_algebra",
        )

        payload = copy.deepcopy(result)
        payload["scenario_counts"]["passed"] = 29
        payload["scenario_counts"]["failed"] = 1
        payload["invariant_counts"][invariant] = 1
        payload[field] = False
        add(
            f"safety_boolean_contradiction_{field}",
            payload,
            "result_decision_semantics",
        )

    payload = copy.deepcopy(result)
    payload["counts_by_family"]["entry"] = {
        "transcript_text": 7,
    }
    add("forbidden_nested_key", payload, "result_nested_shape")

    payload = copy.deepcopy(result)
    payload["counts_by_family"]["entry"] = "session:forbidden"
    add("forbidden_nested_value", payload, "result_nested_shape")

    return mutations


def _task_9_compact(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def render_report_fixture_without_semantic_validation(
    result: dict[str, Any],
) -> str:
    final_digest = sha256_bytes(canonical_json_bytes(result))
    return "\n".join((
        "# EMOTION-STATE-003 Phase C0 Synthetic Temporal Mechanics",
        "",
        f"- Checkpoint: {result['checkpoint_id']}",
        f"- Decision: {result['decision']}",
        f"- Result schema: {result['schema_version']}",
        f"- Policy SHA-256: {result['policy_sha256']}",
        f"- Scenario SHA-256: {result['scenario_sha256']}",
        (
            "- Aggregate-output SHA-256: "
            f"{result['aggregate_output_sha256']}"
        ),
        f"- result.json sha256:{final_digest}",
        "",
        "## Aggregate",
        "",
        f"- Scenario counts: {_task_9_compact(result['scenario_counts'])}",
        f"- Counts by family: {_task_9_compact(result['counts_by_family'])}",
        (
            "- Counts by signal family: "
            f"{_task_9_compact(result['counts_by_signal'])}"
        ),
        (
            "- Counts by modality family: "
            f"{_task_9_compact(result['counts_by_modality'])}"
        ),
        (
            "- Counts by abstention reason: "
            f"{_task_9_compact(result['counts_by_abstention_reason'])}"
        ),
        f"- Invariant counts: {_task_9_compact(result['invariant_counts'])}",
        (
            "- Deterministic replay passed: "
            f"{_task_9_compact(result['deterministic_replay_passed'])}"
        ),
        (
            "- Privacy boundary passed: "
            f"{_task_9_compact(result['privacy_boundary_passed'])}"
        ),
        "",
        "## Complexity",
        "",
        (
            "- Numeric policy parameters: "
            f"{result['complexity']['numeric_policy_parameter_count']}"
        ),
        f"- Scenarios: {result['complexity']['scenario_count']}",
        (
            "- Operational signals: "
            f"{result['complexity']['operational_signal_count']}"
        ),
        (
            "- Synthetic evidence classes: "
            f"{result['complexity']['synthetic_evidence_class_count']}"
        ),
        (
            "- Runtime files modified: "
            f"{result['complexity']['runtime_files_modified']}"
        ),
        "",
        "## Interpretation",
        "",
        *TASK_9_SCOPE_LINES_FOR_TEST,
        "",
    ))


def _validator_independence_violations(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    forbidden_module = "run_emotion_state_003_phase_c0"
    forbidden_names = {
        "PHASE_C_RESULT_FIELDS",
        "decide_phase_c_checkpoint",
        "build_phase_c_result",
        "validate_phase_c_result_payload",
        "compute_aggregate_output_sha256",
        "render_phase_c_report",
        "write_phase_c_pair",
    }
    forbidden_aliases: set[str] = set()
    forbidden_module_aliases: set[str] = set()
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                origin = alias.name.rsplit(".", 1)[-1]
                if origin == forbidden_module:
                    violations.append(f"import:{alias.name}")
                    forbidden_module_aliases.add(alias.asname or origin)
        elif isinstance(node, ast.ImportFrom):
            origin_module = (node.module or "").rsplit(".", 1)[-1]
            if origin_module == forbidden_module:
                violations.append(f"importfrom:{node.module}")
            for alias in node.names:
                if alias.name == forbidden_module:
                    violations.append(f"importmodule:{alias.name}")
                    forbidden_module_aliases.add(
                        alias.asname or alias.name,
                    )
                if alias.name in forbidden_names:
                    violations.append(f"importname:{alias.name}")
                    forbidden_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in forbidden_names or node.id in forbidden_aliases:
                violations.append(f"name:{node.id}")
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if node.attr in forbidden_names:
                violations.append(f"attribute:{node.attr}")
            if (
                isinstance(node.value, ast.Name)
                and node.value.id in forbidden_module_aliases
            ):
                violations.append(f"module_alias:{node.value.id}.{node.attr}")
    return tuple(sorted(set(violations)))


class PhaseCIndependentValidatorTests(PhaseCTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from scripts import emotion_state_phase_c_temporal_tracker
        from scripts import run_emotion_state_003_phase_c0
        from scripts import validate_emotion_state_003_phase_c0

        cls.tracker = emotion_state_phase_c_temporal_tracker
        cls.runner = run_emotion_state_003_phase_c0
        cls.validator = validate_emotion_state_003_phase_c0
        cls.raw_policy = load_json_strict(POLICY_PATH)
        cls.policy = validate_phase_c_policy(copy.deepcopy(cls.raw_policy))
        cls.raw_scenarios = load_json_strict(SCENARIO_PATH)
        parsed = phase_c_contracts.validate_phase_c_scenario_payload(
            copy.deepcopy(cls.raw_scenarios),
            cls.policy,
        )
        cls.scenarios = {scenario.case_id: scenario for scenario in parsed}
        evaluation = cls.tracker.evaluate_phase_c_scenarios(
            cls.policy,
            cls.scenarios,
        )
        cls.valid_result_payload = cls.runner.build_phase_c_result(
            evaluation,
            canonical_json_bytes(cls.raw_policy),
            canonical_json_bytes(cls.raw_scenarios),
        )
        cls.valid_report_bytes = cls.runner.render_phase_c_report(
            cls.valid_result_payload,
        ).encode("utf-8")
        cls.fresh_evaluation_projection = (
            cls.validator.build_fresh_evaluation_projection(
                cls.policy,
                cls.scenarios,
            )
        )

    def setUp(self) -> None:
        pass

    def run_validator(
        self,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(
                    ROOT
                    / "scripts"
                    / "validate_emotion_state_003_phase_c0.py"
                ),
                *arguments,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def valid_result(self) -> dict[str, Any]:
        return copy.deepcopy(self.valid_result_payload)

    def result_mutations(
        self,
        result: dict[str, Any],
    ) -> list[tuple[str, dict[str, Any], str]]:
        return build_result_contract_mutations(result)

    @contextmanager
    def allowlisted_reader_root(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            root = Path(temporary) / "candidate"
            root.mkdir()
            (root / "result.json").write_bytes(
                canonical_json_bytes(self.valid_result_payload),
            )
            (root / "report.md").write_bytes(self.valid_report_bytes)
            with mock.patch.object(self.validator, "CANDIDATE_ROOT", root):
                yield root

    def pair_open_paths(self, open_spy: mock.Mock) -> tuple[Path, ...]:
        return tuple(
            Path(call.args[0])
            for call in open_spy.call_args_list
            if call.args
            and Path(call.args[0]).name in ("result.json", "report.md")
        )

    def test_validator_sections_pass_on_fixtures(self) -> None:
        for section in ("contracts", "scenarios", "synthetic"):
            completed = self.run_validator(section)
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            self.assertEqual(completed.stdout, f"{section}:pass\n")
            self.assertEqual(completed.stderr, "")

    def test_contracts_section_reads_only_the_policy_contract(self) -> None:
        def load_only_policy(path):
            if Path(path) != POLICY_PATH:
                raise AssertionError("contracts must not read scenarios")
            return copy.deepcopy(self.raw_policy)

        with mock.patch.object(
            self.validator,
            "load_json_strict",
            side_effect=load_only_policy,
        ):
            self.validator._run_section("contracts", None)

    def test_scenarios_section_does_not_run_synthetic_evaluation(self) -> None:
        with mock.patch.object(
            self.validator.temporal_tracker,
            "evaluate_phase_c_scenarios",
            side_effect=AssertionError("scenarios must not evaluate"),
        ):
            self.validator._run_section("scenarios", None)

    def test_fresh_projection_maps_evaluator_contract_failure(self) -> None:
        with mock.patch.object(
            self.validator.temporal_tracker,
            "evaluate_phase_c_scenarios",
            side_effect=PhaseCContractError("injected"),
        ):
            with self.assertRaisesRegex(
                self.validator.ValidationError,
                "synthetic_projection",
            ):
                self.validator.build_fresh_evaluation_projection(
                    self.policy,
                    self.scenarios,
                )

    def test_every_result_scalar_and_mapping_shape_mutation_rejects(self) -> None:
        result = self.valid_result()
        names = []
        for name, payload, expected_code in self.result_mutations(result):
            names.append(name)
            with self.subTest(mutation=name):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    expected_code,
                ):
                    self.validator.validate_candidate_payload(
                        payload,
                        self.fresh_evaluation_projection,
                    )
        self.assertEqual(names, sorted(names, key=names.index))
        self.assertEqual(len(names), len(set(names)))

    def test_valid_pair_passes_independent_validation(self) -> None:
        validated = self.validator.validate_pair_bytes(
            canonical_json_bytes(self.valid_result_payload),
            self.valid_report_bytes,
            self.fresh_evaluation_projection,
        )
        self.assertEqual(validated, self.valid_result_payload)

    def test_renderer_equality_cannot_mask_semantic_contradiction(self) -> None:
        result = self.valid_result()
        result["decision"] = "keep"
        result["scenario_counts"]["passed"] = 29
        result["scenario_counts"]["failed"] = 1
        result["invariant_counts"]["golden_projection"] = 1
        _task_9_rebind_aggregate_digest(result)
        report = render_report_fixture_without_semantic_validation(result)
        with self.assertRaisesRegex(
            self.validator.ValidationError,
            "result_decision_semantics",
        ):
            self.validator.validate_pair_bytes(
                canonical_json_bytes(result),
                report.encode("utf-8"),
                self.fresh_evaluation_projection,
            )

    def test_coherent_pair_mutation_cannot_diverge_from_fresh_evaluation(
        self,
    ) -> None:
        result = self.valid_result()
        result["scenario_counts"]["passed"] = 29
        result["scenario_counts"]["failed"] = 1
        result["invariant_counts"]["golden_projection"] = 1
        result["decision"] = "revise"
        _task_9_rebind_aggregate_digest(result)
        report = render_report_fixture_without_semantic_validation(result)
        with self.assertRaisesRegex(
            self.validator.ValidationError,
            "result_evaluation_binding",
        ):
            self.validator.validate_pair_bytes(
                canonical_json_bytes(result),
                report.encode("utf-8"),
                self.fresh_evaluation_projection,
            )

    def test_actual_negative_evaluation_pair_validates_as_revise(self) -> None:
        evaluation = _mechanical_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            canonical_json_bytes(self.raw_policy),
            canonical_json_bytes(self.raw_scenarios),
        )
        report = self.runner.render_phase_c_report(result).encode("utf-8")
        with mock.patch.object(
            self.validator.temporal_tracker,
            "evaluate_phase_c_scenarios",
            return_value=evaluation,
        ):
            fresh = self.validator.build_fresh_evaluation_projection(
                self.policy,
                self.scenarios,
            )
        self.validator.validate_pair_bytes(
            canonical_json_bytes(result),
            report,
            fresh,
        )
        self.assertEqual(result["decision"], "revise")
        self.assertEqual(result["scenario_counts"]["failed"], 1)

    def test_actual_semantic_negative_pair_validates_as_discard(self) -> None:
        evaluation = _semantic_negative_evaluation(self)
        result = self.runner.build_phase_c_result(
            evaluation,
            canonical_json_bytes(self.raw_policy),
            canonical_json_bytes(self.raw_scenarios),
        )
        report = self.runner.render_phase_c_report(result).encode("utf-8")
        with mock.patch.object(
            self.validator.temporal_tracker,
            "evaluate_phase_c_scenarios",
            return_value=evaluation,
        ):
            fresh = self.validator.build_fresh_evaluation_projection(
                self.policy,
                self.scenarios,
            )
        self.validator.validate_pair_bytes(
            canonical_json_bytes(result),
            report,
            fresh,
        )
        self.assertEqual(result["invariant_counts"]["semantic_output"], 1)
        self.assertEqual(result["decision"], "discard")

    def test_fresh_projection_requires_two_identical_valid_evaluations(
        self,
    ) -> None:
        valid = self.tracker.evaluate_phase_c_scenarios(
            self.policy,
            self.scenarios,
        )
        changed = dataclasses.replace(
            valid,
            outcomes=tuple(reversed(valid.outcomes)),
        )
        with mock.patch.object(
            self.validator.temporal_tracker,
            "evaluate_phase_c_scenarios",
            side_effect=(valid, changed),
        ):
            with self.assertRaisesRegex(
                self.validator.ValidationError,
                "synthetic_projection",
            ):
                self.validator.build_fresh_evaluation_projection(
                    self.policy,
                    self.scenarios,
                )

    def test_result_decoder_rejects_duplicate_nonfinite_and_nonobject(
        self,
    ) -> None:
        cases = (
            b'{"x":1,"x":2}\n',
            b'{"x":NaN}\n',
            b"[]\n",
            b"\xff",
        )
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "result_json",
                ):
                    self.validator.validate_pair_bytes(
                        payload,
                        self.valid_report_bytes,
                        self.fresh_evaluation_projection,
                    )

    def test_report_scope_line_mutations_reject_before_determinism(self) -> None:
        report = self.valid_report_bytes.decode("utf-8")
        for index, line in enumerate(TASK_9_SCOPE_LINES_FOR_TEST):
            for action in ("delete", "alter"):
                with self.subTest(index=index, action=action):
                    if action == "delete":
                        mutated_lines = report.splitlines()
                        mutated_lines.remove(line)
                        mutated = "\n".join(mutated_lines) + "\n"
                    else:
                        mutated = report.replace(
                            line,
                            line + " altered",
                            1,
                        )
                    with self.assertRaisesRegex(
                        self.validator.ValidationError,
                        "report_scope_boundary",
                    ):
                        self.validator.validate_pair_bytes(
                            canonical_json_bytes(self.valid_result_payload),
                            mutated.encode("utf-8"),
                            self.fresh_evaluation_projection,
                        )

    def test_report_hash_line_endings_and_terminal_lf_mutations_reject(
        self,
    ) -> None:
        result_bytes = canonical_json_bytes(self.valid_result_payload)
        cases = (
            (
                self.valid_report_bytes.replace(
                    b"result.json sha256:",
                    b"result.json sha256:0",
                    1,
                ),
                "report_result_hash_binding",
            ),
            (self.valid_report_bytes.replace(b"\n", b"\r\n"), "report_encoding"),
            (self.valid_report_bytes[:-1], "report_encoding"),
            (self.valid_report_bytes + b"\n", "report_encoding"),
            (b"\xff", "report_encoding"),
        )
        for report_bytes, code in cases:
            with self.subTest(code=code, size=len(report_bytes)):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    code,
                ):
                    self.validator.validate_pair_bytes(
                        result_bytes,
                        report_bytes,
                        self.fresh_evaluation_projection,
                    )

    def test_every_rendered_aggregate_and_complexity_value_is_bound(
        self,
    ) -> None:
        report = self.valid_report_bytes.decode("utf-8")
        lines = report.splitlines()
        for prefix in TASK_9_RENDERED_VALUE_PREFIXES_FOR_TEST:
            index = next(
                offset
                for offset, line in enumerate(lines)
                if line.startswith(prefix)
            )
            mutated_lines = list(lines)
            mutated_lines[index] = lines[index] + "0"
            mutated = ("\n".join(mutated_lines) + "\n").encode("utf-8")
            with self.subTest(prefix=prefix):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "report_determinism",
                ):
                    self.validator.validate_pair_bytes(
                        canonical_json_bytes(self.valid_result_payload),
                        mutated,
                        self.fresh_evaluation_projection,
                    )

    def test_reader_accepts_only_exact_pair_after_child_validation(self) -> None:
        with self.allowlisted_reader_root() as root:
            events: list[str] = []
            real_lstat = os.lstat
            real_listdir = os.listdir
            real_open = open

            def tracked_lstat(path):
                candidate = Path(path)
                if candidate.parent == root:
                    events.append(f"lstat:{candidate.name}")
                return real_lstat(path)

            def tracked_listdir(path):
                if Path(path) == root:
                    events.append("listdir")
                return real_listdir(path)

            def tracked_open(path, *args, **kwargs):
                candidate = Path(path)
                if candidate.parent == root:
                    events.append(f"open:{candidate.name}")
                return real_open(path, *args, **kwargs)

            with (
                mock.patch.object(
                    self.validator.os,
                    "lstat",
                    side_effect=tracked_lstat,
                ),
                mock.patch.object(
                    self.validator.os,
                    "listdir",
                    side_effect=tracked_listdir,
                ),
                mock.patch("builtins.open", side_effect=tracked_open),
            ):
                result_bytes, report_bytes = (
                    self.validator.read_allowlisted_pair(
                        "candidate",
                        str(root),
                    )
                )
            self.assertEqual(
                result_bytes,
                canonical_json_bytes(self.valid_result_payload),
            )
            self.assertEqual(report_bytes, self.valid_report_bytes)
            first_open = next(
                index
                for index, event in enumerate(events)
                if event.startswith("open:")
            )
            self.assertLess(events.index("listdir"), first_open)
            self.assertLess(events.index("lstat:result.json"), first_open)
            self.assertLess(events.index("lstat:report.md"), first_open)

    def test_reader_rejects_outside_alias_and_missing_root_before_open(
        self,
    ) -> None:
        with self.allowlisted_reader_root() as root:
            cases = (
                ("outside", str(root.parent / "outside"), "root_not_allowlisted"),
                (
                    "dot",
                    f"{root.parent}{os.sep}.{os.sep}{root.name}",
                    "root_lexical_alias",
                ),
                (
                    "dotdot",
                    f"{root}{os.sep}..{os.sep}{root.name}",
                    "root_lexical_alias",
                ),
            )
            for name, requested, code in cases:
                with self.subTest(name=name):
                    with mock.patch(
                        "builtins.open",
                        wraps=open,
                    ) as open_spy:
                        with self.assertRaisesRegex(
                            self.validator.ValidationError,
                            code,
                        ):
                            self.validator.read_allowlisted_pair(
                                "candidate",
                                requested,
                            )
                    self.assertEqual(self.pair_open_paths(open_spy), ())

        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            missing = Path(temporary) / "candidate"
            with (
                mock.patch.object(
                    self.validator,
                    "CANDIDATE_ROOT",
                    missing,
                ),
                mock.patch("builtins.open", wraps=open) as open_spy,
            ):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "root_missing",
                ):
                    self.validator.read_allowlisted_pair(
                        "candidate",
                        str(missing),
                    )
            self.assertEqual(self.pair_open_paths(open_spy), ())

    def test_reader_rejects_reparse_ancestor_root_and_file_before_open(
        self,
    ) -> None:
        reparse_flag = getattr(
            stat,
            "FILE_ATTRIBUTE_REPARSE_POINT",
            0x400,
        )
        for target_name in ("ancestor", "root", "file"):
            with self.subTest(target=target_name):
                with self.allowlisted_reader_root() as root:
                    target = {
                        "ancestor": root.parent,
                        "root": root,
                        "file": root / "result.json",
                    }[target_name]
                    real_lstat = os.lstat

                    def injected(path):
                        metadata = real_lstat(path)
                        if Path(path) == target:
                            values = {
                                name: getattr(metadata, name)
                                for name in dir(metadata)
                                if name.startswith("st_")
                            }
                            values["st_file_attributes"] = reparse_flag
                            return SimpleNamespace(**values)
                        return metadata

                    with (
                        mock.patch.object(
                            self.validator.os,
                            "lstat",
                            side_effect=injected,
                        ),
                        mock.patch("builtins.open", wraps=open) as open_spy,
                    ):
                        with self.assertRaisesRegex(
                            self.validator.ValidationError,
                            "root_reparse_or_link",
                        ):
                            self.validator.read_allowlisted_pair(
                                "candidate",
                                str(root),
                            )
                    self.assertEqual(self.pair_open_paths(open_spy), ())

    def test_reader_rejects_wrong_file_type_and_unexpected_child_before_open(
        self,
    ) -> None:
        with self.allowlisted_reader_root() as root:
            (root / "report.md").unlink()
            (root / "report.md").mkdir()
            with mock.patch("builtins.open", wraps=open) as open_spy:
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "root_file_type",
                ):
                    self.validator.read_allowlisted_pair(
                        "candidate",
                        str(root),
                    )
            self.assertEqual(self.pair_open_paths(open_spy), ())

        with self.allowlisted_reader_root() as root:
            (root / "unexpected").write_bytes(b"unexpected")
            with mock.patch("builtins.open", wraps=open) as open_spy:
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "root_children",
                ):
                    self.validator.read_allowlisted_pair(
                        "candidate",
                        str(root),
                    )
            self.assertEqual(self.pair_open_paths(open_spy), ())

    def test_reader_rejects_metadata_change_across_read(self) -> None:
        with self.allowlisted_reader_root() as root:
            real_fstat = os.fstat
            calls = 0

            def injected(descriptor):
                nonlocal calls
                calls += 1
                metadata = real_fstat(descriptor)
                if calls == 2:
                    values = {
                        name: getattr(metadata, name)
                        for name in dir(metadata)
                        if name.startswith("st_")
                    }
                    values["st_mtime_ns"] = metadata.st_mtime_ns + 1
                    return SimpleNamespace(**values)
                return metadata

            with (
                mock.patch.object(
                    self.validator.os,
                    "fstat",
                    side_effect=injected,
                ),
                mock.patch("builtins.open", wraps=open) as open_spy,
            ):
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "root_changed_during_read",
                ):
                    self.validator.read_allowlisted_pair(
                        "candidate",
                        str(root),
                    )
            self.assertEqual(
                self.pair_open_paths(open_spy),
                (root / "result.json",),
            )

    def test_reader_rejects_oversized_file_before_open(self) -> None:
        with self.allowlisted_reader_root() as root:
            (root / "result.json").write_bytes(b"x" * 65537)
            with mock.patch("builtins.open", wraps=open) as open_spy:
                with self.assertRaisesRegex(
                    self.validator.ValidationError,
                    "root_file_size",
                ):
                    self.validator.read_allowlisted_pair(
                        "candidate",
                        str(root),
                    )
            self.assertEqual(self.pair_open_paths(open_spy), ())

    def test_cli_arity_section_and_root_contract(self) -> None:
        valid = (
            (["contracts"], ("contracts", None)),
            (["scenarios"], ("scenarios", None)),
            (["synthetic"], ("synthetic", None)),
            (
                [
                    "candidate",
                    "--root",
                    ".tmp/emotion-state-003-phase-c0/candidate",
                ],
                (
                    "candidate",
                    ".tmp/emotion-state-003-phase-c0/candidate",
                ),
            ),
            (["checkpoint"], ("checkpoint", None)),
        )
        for arguments, expected in valid:
            with self.subTest(arguments=arguments):
                self.assertEqual(
                    self.validator.parse_cli_args(arguments),
                    expected,
                )
        invalid = (
            [],
            ["unknown"],
            ["contracts", "extra"],
            ["candidate"],
            ["candidate", "--root"],
            ["candidate", "wrong", "root"],
            ["checkpoint", "--root", "x"],
        )
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(
                    self.validator.CliUsageError,
                    "cli_arguments",
                ):
                    self.validator.parse_cli_args(arguments)

    def test_cli_wrong_arity_and_section_exit_two_without_disclosure(
        self,
    ) -> None:
        for arguments in ((), ("unknown",), ("candidate",)):
            completed = self.run_validator(*arguments)
            with self.subTest(arguments=arguments):
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertEqual(completed.stderr, "")

    def test_ast_independence_rejects_origin_and_alias_bypasses(self) -> None:
        source = (
            ROOT / "scripts" / "validate_emotion_state_003_phase_c0.py"
        ).read_text(encoding="utf-8")
        self.assertEqual(_validator_independence_violations(source), ())
        bypasses = (
            "import scripts.run_emotion_state_003_phase_c0 as hidden\n"
            "hidden.render_phase_c_report({})\n",
            "from scripts import run_emotion_state_003_phase_c0 as hidden\n"
            "print(hidden.main)\n",
            "from scripts.run_emotion_state_003_phase_c0 "
            "import build_phase_c_result as hidden\nhidden(None, b'', b'')\n",
            "from scripts.emotion_state_phase_c_contracts "
            "import PHASE_C_RESULT_FIELDS as hidden\nprint(hidden)\n",
            "import scripts.emotion_state_phase_c_contracts as contracts\n"
            "print(contracts.PHASE_C_RESULT_FIELDS)\n",
        )
        for bypass in bypasses:
            with self.subTest(source=bypass):
                self.assertTrue(_validator_independence_violations(bypass))

    def test_validator_exposes_no_mutable_container_globals(self) -> None:
        mutable_globals = {
            name: type(value).__name__
            for name, value in vars(self.validator).items()
            if not name.startswith("__")
            and type(value) in (dict, list, set)
        }
        self.assertEqual(mutable_globals, {})

    def test_validator_public_validation_requires_fresh_projection(self) -> None:
        parameters = inspect.signature(
            self.validator.validate_candidate_payload,
        ).parameters
        self.assertEqual(
            parameters["fresh_evaluation_projection"].default,
            inspect.Parameter.empty,
        )
        pair_parameters = inspect.signature(
            self.validator.validate_pair_bytes,
        ).parameters
        self.assertEqual(
            pair_parameters["fresh_evaluation_projection"].default,
            inspect.Parameter.empty,
        )


class PhaseCCandidatePromotionTests(PhaseCTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from scripts import emotion_state_phase_c_temporal_tracker
        from scripts import run_emotion_state_003_phase_c0
        from scripts import validate_emotion_state_003_phase_c0

        cls.tracker = emotion_state_phase_c_temporal_tracker
        cls.runner = run_emotion_state_003_phase_c0
        cls.validator = validate_emotion_state_003_phase_c0
        cls.raw_policy = load_json_strict(POLICY_PATH)
        cls.raw_scenarios = load_json_strict(SCENARIO_PATH)

    def test_accepted_checkpoint_equals_two_fresh_in_memory_renders(self) -> None:
        checkpoint_result, checkpoint_report = (
            self.validator.read_allowlisted_pair(
                section="checkpoint",
            )
        )
        renders = []
        for _ in range(2):
            evaluation = self.tracker.evaluate_phase_c_scenarios(
                self.policy,
                self.scenarios,
            )
            result = self.runner.build_phase_c_result(
                evaluation,
                canonical_json_bytes(self.raw_policy),
                canonical_json_bytes(self.raw_scenarios),
            )
            result_bytes = canonical_json_bytes(result)
            report_bytes = self.runner.render_phase_c_report(result).encode("utf-8")
            renders.append((result_bytes, report_bytes))
        self.assertEqual(renders[0], renders[1])
        self.assertEqual(
            sha256_bytes(checkpoint_result),
            sha256_bytes(renders[0][0]),
        )
        self.assertEqual(
            sha256_bytes(checkpoint_result),
            sha256_bytes(renders[1][0]),
        )
        self.assertEqual(
            sha256_bytes(checkpoint_report),
            sha256_bytes(renders[0][1]),
        )
        self.assertEqual(
            sha256_bytes(checkpoint_report),
            sha256_bytes(renders[1][1]),
        )


class PhaseCCloseoutContractTests(unittest.TestCase):
    PROTOCOL_PATH = (
        ROOT
        / "research"
        / "experiments"
        / "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics.md"
    )
    CANONICAL_ROOT = (
        ROOT
        / "research"
        / "experiments"
        / "generated"
        / "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics"
    )
    CLOSEOUT_PATHS = (
        ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
        ROOT / "docs" / "product" / "COMMANDS.md",
        ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
        ROOT / "docs" / "thesis" / "ROADMAP.md",
        PROTOCOL_PATH,
    )
    EXPECTED_TRACE_VALUES = (
        "9BB996F886E9AFFBCDA40A6FB71BE10E1CD07D3B114B4E3FBCDAA1DF71171F15",
        "D01FBD7677537A0A91D01E0EA8354D079491C13BBD81EC8BAC97E7BBC4520FB0",
        "3BBB7FC8F4DFB223837EA8D8B8E92EC46AA0ACF70EA1A6CA4649D41266E43030",
        "FD1ADA58FD5C0B614DB429AD6B5434C988E95942FBEB1FEB87D779C14F9E4EA4",
        "fd92aae6acf146d9271888bb264ecd29269cb870",
        "5c461612f667e1a8727eedb9d2c08d9951b3aed0",
        "4c77f72bf7dc85e2e4587b9c03646716e5aec0ff",
        "77a2fb50ba00210cc75d410240c17115be83a415",
        "62b6b65cf307270bfc2e98c7c08617252859948d",
        "C0/I0/M0",
    )

    def protocol_status(self) -> str:
        protocol = self.PROTOCOL_PATH.read_text(encoding="utf-8")
        status = protocol.split("## Status", 1)[1].split("##", 1)[0]
        return next(line for line in status.splitlines() if line.strip())

    def test_protocol_has_exact_accepted_status_and_trace(self) -> None:
        self.assertEqual(
            self.protocol_status(),
            "Canonical Phase C0 synthetic mechanics checkpoint accepted.",
        )
        protocol = self.PROTOCOL_PATH.read_text(encoding="utf-8")
        self.assertIn("Candidate decision: `keep`", protocol)
        for value in self.EXPECTED_TRACE_VALUES:
            with self.subTest(value=value):
                self.assertIn(value, protocol)

    def test_every_closeout_reference_binds_scope_and_existing_trace(self) -> None:
        stable_scope = (
            "synthetic mechanics only",
            "Phase B lockbox remains closed and cannot be reused",
        )
        static_closeout_scope = "no runtime, provider, data, or Phase D authority"
        roadmap_scope = (
            "no runtime, provider, data",
            "successor-phase authority",
        )
        for path in self.CLOSEOUT_PATHS:
            text = path.read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            with self.subTest(path=path):
                self.assertIn("EMOTION-STATE-003", normalized)
                self.assertIn("Candidate decision: `keep`", normalized)
                self.assertIn("177/177", normalized)
                for value in self.EXPECTED_TRACE_VALUES:
                    self.assertIn(value, normalized)
                for boundary in stable_scope:
                    self.assertIn(boundary, normalized)
                if path == ROOT / "docs" / "thesis" / "ROADMAP.md":
                    for boundary in roadmap_scope:
                        self.assertIn(boundary, normalized)
                else:
                    self.assertIn(static_closeout_scope, normalized)

    def test_closeout_retains_required_nonclaims(self) -> None:
        protocol = self.PROTOCOL_PATH.read_text(encoding="utf-8")
        for nonclaim in (
            "does not prove emotion accuracy",
            "customer internal state",
            "policy enforcement",
            "conversion improvement",
            "real-call performance",
            "production readiness",
        ):
            with self.subTest(nonclaim=nonclaim):
                self.assertIn(nonclaim, protocol)

    def test_canonical_directory_contains_exact_pair(self) -> None:
        self.assertTrue(self.CANONICAL_ROOT.is_dir())
        self.assertEqual(
            {path.name for path in self.CANONICAL_ROOT.iterdir()},
            {"result.json", "report.md"},
        )

    def test_phase_c0_commands_do_not_reuse_phase_b_lockbox(self) -> None:
        commands = (ROOT / "docs" / "product" / "COMMANDS.md").read_text(
            encoding="utf-8",
        )
        section_heading = (
            "## EMOTION-STATE-003 Phase C0 Synthetic Mechanics Checkpoint"
        )
        self.assertIn(section_heading, commands)
        phase_c0 = commands.split(section_heading, 1)[1]
        phase_c0 = phase_c0.split("\n## ", 1)[0]
        self.assertNotIn(".tmp/emotion-state-002-phase-b", phase_c0)
        self.assertNotIn("run_emotion_state_002_phase_b.py", phase_c0)
        self.assertNotIn("admit-lockbox", phase_c0)
        self.assertNotIn(" lockbox`", phase_c0)

    def test_roadmap_records_completed_closeout_boundary(self) -> None:
        roadmap = (
            ROOT / "docs" / "thesis" / "ROADMAP.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(roadmap.split())
        self.assertNotIn(
            "An independent C0/I0/M0 review is required before the "
            "six-file closeout commit.",
            normalized.replace("`", ""),
        )
        self.assertNotIn(
            "Implementation, merge, runtime activation, provider access, "
            "private data, calls, conversational simulations, source "
            "adaptation, and Phase D remain outside the current plan-only "
            "scope.",
            normalized,
        )
        self.assertIn("Phase C0 final review returned `C0/I0/M0`", normalized)
        self.assertIn(
            "48499cf1690338210c57bd720ef466a5f7abf0c7",
            normalized,
        )
        self.assertIn("The checkpoint remains unmerged", normalized)
        self.assertIn("successor-phase authority", normalized)
        self.assertIn(
            "The implementation and accepted local checkpoint described above "
            "are now complete.",
            normalized,
        )
        self.assertIn(
            "candidate, canonical, and push remained distinct gates.",
            normalized,
        )
        self.assertIn(
            "Push, merge, runtime activation, public or private data access, "
            "provider access, calls, conversational simulations, source "
            "adaptation, and successor-phase authority remain outside this "
            "checkpoint.",
            normalized,
        )
