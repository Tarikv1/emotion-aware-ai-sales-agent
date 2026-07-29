from __future__ import annotations

import json
import math
import os
import re
import stat
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Sequence

_IMPORT_ROOT = Path(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)),
)
if os.fspath(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_IMPORT_ROOT))

import scripts.emotion_state_phase_c_temporal_tracker as temporal_tracker
from scripts.emotion_state_phase_c_contracts import (
    PhaseCContractError,
    PhaseCExpectedAcceptedStepV1,
    PhaseCExpectedRejectedStepV1,
    PhaseCScenarioEvaluationV1,
    PhaseCScenarioOutcomeV1,
    PhaseCScenarioV1,
    canonical_json_bytes,
    load_json_strict,
    sha256_bytes,
    validate_phase_c_policy,
    validate_phase_c_scenario_payload,
)


class ValidationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class CliUsageError(ValueError):
    pass


ROOT = _IMPORT_ROOT
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
CANDIDATE_ROOT = (
    ROOT
    / ".tmp"
    / "emotion-state-003-phase-c0"
    / "candidate"
)
CANONICAL_ROOT = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics"
)

RESULT_SCHEMA_VERSION = "EmotionStatePhaseC0AggregateResultV1"
CHECKPOINT_ID = "EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics"
POLICY_ID = "emotion-state-phase-c0-synthetic-v1"
EVIDENCE_POLICY_VERSION = "emotion-state-evidence-v2"

VALIDATOR_RESULT_FIELDS = frozenset({
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
})
STRING_SCALAR_FIELDS = (
    "schema_version",
    "checkpoint_id",
    "policy_id",
    "evidence_policy_version",
    "policy_sha256",
    "scenario_sha256",
    "aggregate_output_sha256",
    "decision",
)
CLAIM_OR_CONSUMPTION_FIELDS = (
    "phase_b_inputs_consumed",
    "public_or_private_data_consumed",
    "runtime_modified_or_activated",
    "provider_or_call_used",
    "policy_enforcement_proven",
    "emotion_accuracy_proven",
    "production_readiness_proven",
)
BOOLEAN_SCALAR_FIELDS = (
    "deterministic_replay_passed",
    "privacy_boundary_passed",
    *CLAIM_OR_CONSUMPTION_FIELDS,
)
SCENARIO_COUNT_FIELDS = (
    "total",
    "passed",
    "failed",
    "rejection_cases",
)
FAMILY_COUNT_ORDER = (
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
SIGNAL_COUNT_ORDER = (
    "confusion",
    "disengagement",
    "frustration",
    "hesitation",
    "interest",
    "mixed",
    "none",
)
MODALITY_COUNT_ORDER = (
    "text",
    "dialogue",
    "acoustic",
    "multimodal",
    "none",
)
ABSTENTION_COUNT_ORDER = (
    "insufficient_evidence",
    "contradictory_evidence",
    "low_audio_quality",
    "missing_input",
)
INVARIANT_NAMES = (
    "golden_projection",
    "rejection_no_mutation",
    "correction_semantic_replay",
    "session_isolation",
    "deterministic_replay",
    "semantic_output",
    "privacy_boundary",
)
SAFETY_INVARIANT_NAMES = (
    "rejection_no_mutation",
    "session_isolation",
    "deterministic_replay",
    "semantic_output",
    "privacy_boundary",
)
PRIVACY_INVARIANT_NAMES = (
    "rejection_no_mutation",
    "session_isolation",
    "semantic_output",
    "privacy_boundary",
)
COMPLEXITY_FIELDS = (
    "numeric_policy_parameter_count",
    "scenario_count",
    "operational_signal_count",
    "synthetic_evidence_class_count",
    "runtime_files_modified",
)
EXPECTED_COMPLEXITY_BASE = MappingProxyType({
    "scenario_count": 30,
    "operational_signal_count": 5,
    "synthetic_evidence_class_count": 5,
    "runtime_files_modified": 0,
})
EXPECTED_FAMILY_COUNTS = MappingProxyType({
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
})
EXPECTED_SIGNAL_COUNTS = MappingProxyType({
    "confusion": 13,
    "disengagement": 1,
    "frustration": 3,
    "hesitation": 4,
    "interest": 3,
    "mixed": 5,
    "none": 1,
})
EXPECTED_MODALITY_COUNTS = MappingProxyType({
    "text": 23,
    "dialogue": 1,
    "acoustic": 2,
    "multimodal": 3,
    "none": 1,
})
EXPECTED_GOLDEN_ABSTENTION_COUNTS = MappingProxyType({
    "insufficient_evidence": 24,
    "contradictory_evidence": 1,
    "low_audio_quality": 1,
    "missing_input": 11,
})
EXPECTED_SCENARIO_IDS = (
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
FORBIDDEN_KEY_FRAGMENTS = (
    "acoustic_features",
    "probabilities",
    "model_id",
    "dataset_id",
    "audio_bytes",
    "raw_audio",
    "transcript_text",
    "raw_transcript",
    "customer_name",
    "customer_phone",
    "customer_email",
    "speaker_embedding",
    "voiceprint",
    "provider_payload",
    "api_key",
    "access_token",
    "auth_token",
    "password",
    "secret",
    "private_key",
    "hidden_reasoning",
)
FORBIDDEN_IDENTITY_PREFIXES = (
    "evidence:uuid:",
    "session:",
    "turn:",
    "event:",
    "campaign:",
    "version:",
    "ind:",
)
SCOPE_LINES = (
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
PROJECTION_FIELDS = (
    "scenario_counts",
    "counts_by_family",
    "counts_by_signal",
    "counts_by_modality",
    "counts_by_abstention_reason",
    "invariant_counts",
    "deterministic_replay_passed",
    "privacy_boundary_passed",
    "decision",
)
PAIR_CHILDREN = frozenset({"result.json", "report.md"})
HEX_SHA256 = re.compile(r"^[0-9A-F]{64}$")
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
MAX_PAIR_FILE_BYTES = 65536


def _strict_json_object_bytes(payload: bytes, code: str) -> dict[str, Any]:
    if type(payload) is not bytes:
        raise ValidationError(code)

    def reject_constant(_value: str) -> None:
        raise ValueError("nonfinite")

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite")
        return parsed

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result

    try:
        decoded = payload.decode("utf-8")
        parsed = json.loads(
            decoded,
            parse_constant=reject_constant,
            parse_float=finite_float,
            object_pairs_hook=unique_object,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError(code) from exc
    if type(parsed) is not dict:
        raise ValidationError(code)
    return parsed


def _load_validated_inputs() -> tuple[
    dict[str, Any],
    dict[str, Any],
    tuple[PhaseCScenarioV1, ...],
]:
    try:
        policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
        raw_scenarios = load_json_strict(SCENARIO_PATH)
        scenarios = validate_phase_c_scenario_payload(raw_scenarios, policy)
    except (OSError, PhaseCContractError) as exc:
        raise ValidationError("input_contracts") from exc
    return policy, raw_scenarios, scenarios


def _count_exact_int_leaves(value: Any) -> int:
    if type(value) is int:
        return 1
    if type(value) is dict:
        return sum(_count_exact_int_leaves(child) for child in value.values())
    if type(value) in (list, tuple):
        return sum(_count_exact_int_leaves(child) for child in value)
    return 0


def _ordered_scenarios(
    scenarios: object,
) -> tuple[PhaseCScenarioV1, ...]:
    if type(scenarios) is dict:
        ordered = tuple(scenarios.values())
        if tuple(scenarios) != tuple(
            scenario.case_id
            for scenario in ordered
            if type(scenario) is PhaseCScenarioV1
        ):
            raise ValidationError("synthetic_projection")
    elif type(scenarios) is tuple:
        ordered = scenarios
    else:
        raise ValidationError("synthetic_projection")
    if (
        len(ordered) != 30
        or any(type(scenario) is not PhaseCScenarioV1 for scenario in ordered)
        or tuple(scenario.case_id for scenario in ordered)
        != EXPECTED_SCENARIO_IDS
    ):
        raise ValidationError("synthetic_projection")
    return ordered


def _expected_classification_counts(
    scenarios: tuple[PhaseCScenarioV1, ...],
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    family = {
        name: sum(scenario.family == name for scenario in scenarios)
        for name in FAMILY_COUNT_ORDER
    }
    signal = {
        name: sum(scenario.signal_family == name for scenario in scenarios)
        for name in SIGNAL_COUNT_ORDER
    }
    modality = {
        name: sum(scenario.modality_family == name for scenario in scenarios)
        for name in MODALITY_COUNT_ORDER
    }
    if (
        family != EXPECTED_FAMILY_COUNTS
        or signal != EXPECTED_SIGNAL_COUNTS
        or modality != EXPECTED_MODALITY_COUNTS
    ):
        raise ValidationError("synthetic_projection")
    return family, signal, modality


def _golden_abstention_counts(
    scenarios: tuple[PhaseCScenarioV1, ...],
) -> dict[str, int]:
    counts = {name: 0 for name in ABSTENTION_COUNT_ORDER}
    for scenario in scenarios:
        for expected in scenario.expected_steps:
            if type(expected) is PhaseCExpectedRejectedStepV1:
                continue
            if type(expected) is not PhaseCExpectedAcceptedStepV1:
                raise ValidationError("synthetic_projection")
            output = _strict_json_object_bytes(
                expected.expected_output_bytes,
                "synthetic_projection",
            )
            reasons = output.get("abstention_reasons")
            if (
                type(reasons) is not list
                or any(
                    type(reason) is not str or reason not in counts
                    for reason in reasons
                )
            ):
                raise ValidationError("synthetic_projection")
            for reason in reasons:
                counts[reason] += 1
    if counts != EXPECTED_GOLDEN_ABSTENTION_COUNTS:
        raise ValidationError("synthetic_projection")
    return counts


def _exact_count_tuple(
    value: Any,
    order: tuple[str, ...],
) -> dict[str, int]:
    if type(value) is not tuple or len(value) != len(order):
        raise ValidationError("synthetic_projection")
    result: dict[str, int] = {}
    for index, row in enumerate(value):
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or row[0] != order[index]
            or type(row[1]) is not int
            or row[1] < 0
        ):
            raise ValidationError("synthetic_projection")
        result[row[0]] = row[1]
    return result


def _derive_local_decision(
    *,
    failed_scenarios: int,
    invariant_counts: dict[str, int],
    deterministic_replay_passed: bool,
    privacy_boundary_passed: bool,
    claim_flags: dict[str, bool],
) -> str:
    if (
        any(claim_flags[name] for name in CLAIM_OR_CONSUMPTION_FIELDS)
        or any(
            invariant_counts[name] > 0
            for name in SAFETY_INVARIANT_NAMES
        )
        or not deterministic_replay_passed
        or not privacy_boundary_passed
    ):
        return "discard"
    if failed_scenarios:
        return "revise"
    return "keep"


def _project_evaluation(
    evaluation: Any,
    scenarios: tuple[PhaseCScenarioV1, ...],
) -> dict[str, Any]:
    if type(evaluation) is not PhaseCScenarioEvaluationV1:
        raise ValidationError("synthetic_projection")
    if any(
        type(value) is not int or value < 0
        for value in (
            evaluation.total_scenarios,
            evaluation.passed_scenarios,
            evaluation.failed_scenarios,
        )
    ):
        raise ValidationError("synthetic_projection")
    if (
        evaluation.total_scenarios != 30
        or evaluation.passed_scenarios + evaluation.failed_scenarios != 30
        or type(evaluation.outcomes) is not tuple
        or len(evaluation.outcomes) != 30
    ):
        raise ValidationError("synthetic_projection")

    abstention_from_outcomes = {
        name: 0
        for name in ABSTENTION_COUNT_ORDER
    }
    invariants_from_outcomes = {name: 0 for name in INVARIANT_NAMES}
    passed = 0
    for scenario, outcome in zip(
        scenarios,
        evaluation.outcomes,
        strict=True,
    ):
        expected_rejections = sum(
            type(step) is PhaseCExpectedRejectedStepV1
            for step in scenario.expected_steps
        )
        if (
            type(outcome) is not PhaseCScenarioOutcomeV1
            or outcome.case_id != scenario.case_id
            or (
                outcome.family,
                outcome.signal_family,
                outcome.modality_family,
            )
            != (
                scenario.family,
                scenario.signal_family,
                scenario.modality_family,
            )
            or type(outcome.passed) is not bool
            or type(outcome.failed_invariants) is not tuple
            or outcome.failed_invariants
            != tuple(
                name
                for name in INVARIANT_NAMES
                if name in outcome.failed_invariants
            )
            or len(set(outcome.failed_invariants))
            != len(outcome.failed_invariants)
            or outcome.passed != (not outcome.failed_invariants)
            or type(outcome.rejection_count) is not int
            or outcome.rejection_count != expected_rejections
        ):
            raise ValidationError("synthetic_projection")
        abstention = _exact_count_tuple(
            outcome.abstention_reason_counts,
            ABSTENTION_COUNT_ORDER,
        )
        for name in ABSTENTION_COUNT_ORDER:
            abstention_from_outcomes[name] += abstention[name]
        for name in outcome.failed_invariants:
            invariants_from_outcomes[name] += 1
        passed += int(outcome.passed)

    if (
        passed != evaluation.passed_scenarios
        or evaluation.failed_scenarios != 30 - passed
    ):
        raise ValidationError("synthetic_projection")

    expected_family, expected_signal, expected_modality = (
        _expected_classification_counts(scenarios)
    )
    family = _exact_count_tuple(
        evaluation.counts_by_family,
        FAMILY_COUNT_ORDER,
    )
    signal = _exact_count_tuple(
        evaluation.counts_by_signal,
        SIGNAL_COUNT_ORDER,
    )
    modality = _exact_count_tuple(
        evaluation.counts_by_modality,
        MODALITY_COUNT_ORDER,
    )
    abstention = _exact_count_tuple(
        evaluation.counts_by_abstention_reason,
        ABSTENTION_COUNT_ORDER,
    )
    invariants = _exact_count_tuple(
        evaluation.invariant_counts,
        INVARIANT_NAMES,
    )
    if (
        family != expected_family
        or signal != expected_signal
        or modality != expected_modality
        or abstention != abstention_from_outcomes
        or invariants != invariants_from_outcomes
        or (
            evaluation.failed_scenarios == 0
            and abstention != _golden_abstention_counts(scenarios)
        )
        or type(evaluation.deterministic_replay_passed) is not bool
        or type(evaluation.privacy_boundary_passed) is not bool
        or evaluation.deterministic_replay_passed
        != (invariants["deterministic_replay"] == 0)
        or evaluation.privacy_boundary_passed
        != all(invariants[name] == 0 for name in PRIVACY_INVARIANT_NAMES)
    ):
        raise ValidationError("synthetic_projection")

    decision = _derive_local_decision(
        failed_scenarios=evaluation.failed_scenarios,
        invariant_counts=invariants,
        deterministic_replay_passed=(
            evaluation.deterministic_replay_passed
        ),
        privacy_boundary_passed=evaluation.privacy_boundary_passed,
        claim_flags={
            name: False
            for name in CLAIM_OR_CONSUMPTION_FIELDS
        },
    )
    return {
        "scenario_counts": {
            "total": 30,
            "passed": evaluation.passed_scenarios,
            "failed": evaluation.failed_scenarios,
            "rejection_cases": 8,
        },
        "counts_by_family": {
            name: family[name]
            for name in sorted(family)
        },
        "counts_by_signal": {
            name: signal[name]
            for name in sorted(signal)
        },
        "counts_by_modality": {
            name: modality[name]
            for name in sorted(modality)
        },
        "counts_by_abstention_reason": {
            name: abstention[name]
            for name in sorted(abstention)
        },
        "invariant_counts": {
            name: invariants[name]
            for name in sorted(invariants)
        },
        "deterministic_replay_passed": (
            evaluation.deterministic_replay_passed
        ),
        "privacy_boundary_passed": evaluation.privacy_boundary_passed,
        "decision": decision,
    }


def _validate_fresh_projection(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(PROJECTION_FIELDS):
        raise ValidationError("synthetic_projection")
    scenario_counts = _exact_nonnegative_mapping(
        value["scenario_counts"],
        SCENARIO_COUNT_FIELDS,
        "synthetic_projection",
    )
    family = _exact_nonnegative_mapping(
        value["counts_by_family"],
        FAMILY_COUNT_ORDER,
        "synthetic_projection",
    )
    signal = _exact_nonnegative_mapping(
        value["counts_by_signal"],
        SIGNAL_COUNT_ORDER,
        "synthetic_projection",
    )
    modality = _exact_nonnegative_mapping(
        value["counts_by_modality"],
        MODALITY_COUNT_ORDER,
        "synthetic_projection",
    )
    abstention = _exact_nonnegative_mapping(
        value["counts_by_abstention_reason"],
        ABSTENTION_COUNT_ORDER,
        "synthetic_projection",
    )
    invariants = _exact_nonnegative_mapping(
        value["invariant_counts"],
        INVARIANT_NAMES,
        "synthetic_projection",
    )
    if (
        scenario_counts["total"] != 30
        or scenario_counts["passed"] + scenario_counts["failed"] != 30
        or scenario_counts["rejection_cases"] != 8
        or family != EXPECTED_FAMILY_COUNTS
        or signal != EXPECTED_SIGNAL_COUNTS
        or modality != EXPECTED_MODALITY_COUNTS
        or (
            scenario_counts["failed"] == 0
            and abstention != EXPECTED_GOLDEN_ABSTENTION_COUNTS
        )
        or any(
            count > scenario_counts["failed"]
            for count in invariants.values()
        )
        or (
            scenario_counts["failed"] == 0
            and any(invariants.values())
        )
        or (
            scenario_counts["failed"] > 0
            and sum(invariants.values()) < scenario_counts["failed"]
        )
        or type(value["deterministic_replay_passed"]) is not bool
        or type(value["privacy_boundary_passed"]) is not bool
        or value["deterministic_replay_passed"]
        != (invariants["deterministic_replay"] == 0)
        or value["privacy_boundary_passed"]
        != all(invariants[name] == 0 for name in PRIVACY_INVARIANT_NAMES)
        or type(value["decision"]) is not str
        or value["decision"]
        != _derive_local_decision(
            failed_scenarios=scenario_counts["failed"],
            invariant_counts=invariants,
            deterministic_replay_passed=value[
                "deterministic_replay_passed"
            ],
            privacy_boundary_passed=value["privacy_boundary_passed"],
            claim_flags={
                name: False
                for name in CLAIM_OR_CONSUMPTION_FIELDS
            },
        )
    ):
        raise ValidationError("synthetic_projection")
    return value


def build_fresh_evaluation_projection(
    policy: dict[str, Any],
    scenarios: object,
) -> dict[str, Any]:
    try:
        validated_policy = validate_phase_c_policy(policy)
    except PhaseCContractError as exc:
        raise ValidationError("synthetic_projection") from exc
    ordered = _ordered_scenarios(scenarios)
    try:
        first_evaluation = temporal_tracker.evaluate_phase_c_scenarios(
            validated_policy,
            scenarios,
        )
        second_evaluation = temporal_tracker.evaluate_phase_c_scenarios(
            validated_policy,
            scenarios,
        )
    except PhaseCContractError as exc:
        raise ValidationError("synthetic_projection") from exc
    first = _project_evaluation(first_evaluation, ordered)
    second = _project_evaluation(second_evaluation, ordered)
    _validate_fresh_projection(first)
    _validate_fresh_projection(second)
    if canonical_json_bytes(first) != canonical_json_bytes(second):
        raise ValidationError("synthetic_nondeterminism")
    return first


def _exact_nonnegative_mapping(
    value: Any,
    names: tuple[str, ...],
    code: str,
) -> dict[str, int]:
    if (
        type(value) is not dict
        or set(value) != set(names)
        or any(
            type(item) is not int or item < 0
            for item in value.values()
        )
    ):
        raise ValidationError(code)
    return value


def _forbidden_content(value: Any) -> bool:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                return True
            lowered = key.lower()
            if (
                any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS)
                or any(case_id in lowered for case_id in EXPECTED_SCENARIO_IDS)
                or _forbidden_content(child)
            ):
                return True
        return False
    if type(value) is list:
        return any(_forbidden_content(child) for child in value)
    if type(value) is str:
        lowered = value.lower()
        return (
            lowered.startswith(FORBIDDEN_IDENTITY_PREFIXES)
            or any(case_id in lowered for case_id in EXPECTED_SCENARIO_IDS)
        )
    return type(value) not in (bool, int)


def validate_candidate_payload(
    payload: dict[str, Any],
    fresh_evaluation_projection: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValidationError("result_not_object")
    if set(payload) != VALIDATOR_RESULT_FIELDS:
        raise ValidationError("result_field_set")
    if (
        any(type(payload[name]) is not str for name in STRING_SCALAR_FIELDS)
        or any(
            type(payload[name]) is not bool
            for name in BOOLEAN_SCALAR_FIELDS
        )
    ):
        raise ValidationError("result_scalar_type")
    if (
        payload["schema_version"] != RESULT_SCHEMA_VERSION
        or payload["checkpoint_id"] != CHECKPOINT_ID
        or payload["policy_id"] != POLICY_ID
        or payload["evidence_policy_version"] != EVIDENCE_POLICY_VERSION
    ):
        raise ValidationError("result_identity")

    scenario_counts = _exact_nonnegative_mapping(
        payload["scenario_counts"],
        SCENARIO_COUNT_FIELDS,
        "result_nested_shape",
    )
    family = _exact_nonnegative_mapping(
        payload["counts_by_family"],
        FAMILY_COUNT_ORDER,
        "result_nested_shape",
    )
    signal = _exact_nonnegative_mapping(
        payload["counts_by_signal"],
        SIGNAL_COUNT_ORDER,
        "result_nested_shape",
    )
    modality = _exact_nonnegative_mapping(
        payload["counts_by_modality"],
        MODALITY_COUNT_ORDER,
        "result_nested_shape",
    )
    abstention = _exact_nonnegative_mapping(
        payload["counts_by_abstention_reason"],
        ABSTENTION_COUNT_ORDER,
        "result_nested_shape",
    )
    invariants = _exact_nonnegative_mapping(
        payload["invariant_counts"],
        INVARIANT_NAMES,
        "result_nested_shape",
    )
    complexity = _exact_nonnegative_mapping(
        payload["complexity"],
        COMPLEXITY_FIELDS,
        "result_nested_shape",
    )

    failed = scenario_counts["failed"]
    _validate_fresh_projection(fresh_evaluation_projection)
    if (
        scenario_counts["total"] != 30
        or scenario_counts["passed"] + failed != 30
        or scenario_counts["rejection_cases"] != 8
        or family != EXPECTED_FAMILY_COUNTS
        or signal != EXPECTED_SIGNAL_COUNTS
        or modality != EXPECTED_MODALITY_COUNTS
        or (
            failed == 0
            and abstention != EXPECTED_GOLDEN_ABSTENTION_COUNTS
        )
        or (
            failed > 0
            and canonical_json_bytes(abstention)
            != canonical_json_bytes(
                fresh_evaluation_projection[
                    "counts_by_abstention_reason"
                ],
            )
        )
        or any(value > failed for value in invariants.values())
        or (failed == 0 and any(invariants.values()))
        or (failed > 0 and sum(invariants.values()) < failed)
    ):
        raise ValidationError("result_count_algebra")

    policy, raw_scenarios, _scenarios = _load_validated_inputs()
    if (
        HEX_SHA256.fullmatch(payload["policy_sha256"]) is None
        or payload["policy_sha256"]
        != sha256_bytes(canonical_json_bytes(policy))
    ):
        raise ValidationError("result_policy_hash")
    if (
        HEX_SHA256.fullmatch(payload["scenario_sha256"]) is None
        or payload["scenario_sha256"]
        != sha256_bytes(canonical_json_bytes(raw_scenarios))
    ):
        raise ValidationError("result_scenario_hash")
    if any(payload[name] is not False for name in CLAIM_OR_CONSUMPTION_FIELDS):
        raise ValidationError("result_boundary_flags")
    if (
        payload["deterministic_replay_passed"]
        != (invariants["deterministic_replay"] == 0)
        or payload["privacy_boundary_passed"]
        != all(invariants[name] == 0 for name in PRIVACY_INVARIANT_NAMES)
    ):
        raise ValidationError("result_replay_privacy_algebra")
    expected_decision = _derive_local_decision(
        failed_scenarios=failed,
        invariant_counts=invariants,
        deterministic_replay_passed=payload[
            "deterministic_replay_passed"
        ],
        privacy_boundary_passed=payload["privacy_boundary_passed"],
        claim_flags={
            name: payload[name]
            for name in CLAIM_OR_CONSUMPTION_FIELDS
        },
    )
    if payload["decision"] != expected_decision:
        raise ValidationError("result_decision_semantics")
    if any(
        canonical_json_bytes(payload[name])
        != canonical_json_bytes(fresh_evaluation_projection[name])
        for name in PROJECTION_FIELDS
    ):
        raise ValidationError("result_evaluation_binding")

    expected_complexity = {
        **EXPECTED_COMPLEXITY_BASE,
        "numeric_policy_parameter_count": _count_exact_int_leaves(policy),
    }
    if (
        expected_complexity["numeric_policy_parameter_count"] != 36
        or complexity != expected_complexity
    ):
        raise ValidationError("result_complexity")
    if _forbidden_content(payload):
        raise ValidationError("result_forbidden_content")
    without_digest = {
        key: value
        for key, value in payload.items()
        if key != "aggregate_output_sha256"
    }
    if (
        HEX_SHA256.fullmatch(payload["aggregate_output_sha256"]) is None
        or payload["aggregate_output_sha256"]
        != sha256_bytes(canonical_json_bytes(without_digest))
    ):
        raise ValidationError("result_aggregate_digest")
    return payload


def _compact(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def render_expected_report_independently(result: dict[str, Any]) -> str:
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
        f"- Scenario counts: {_compact(result['scenario_counts'])}",
        f"- Counts by family: {_compact(result['counts_by_family'])}",
        (
            "- Counts by signal family: "
            f"{_compact(result['counts_by_signal'])}"
        ),
        (
            "- Counts by modality family: "
            f"{_compact(result['counts_by_modality'])}"
        ),
        (
            "- Counts by abstention reason: "
            f"{_compact(result['counts_by_abstention_reason'])}"
        ),
        f"- Invariant counts: {_compact(result['invariant_counts'])}",
        (
            "- Deterministic replay passed: "
            f"{_compact(result['deterministic_replay_passed'])}"
        ),
        (
            "- Privacy boundary passed: "
            f"{_compact(result['privacy_boundary_passed'])}"
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
        *SCOPE_LINES,
        "",
    ))


def validate_pair_bytes(
    result_bytes: bytes,
    report_bytes: bytes,
    fresh_evaluation_projection: dict[str, Any],
) -> dict[str, Any]:
    result = _strict_json_object_bytes(result_bytes, "result_json")
    if canonical_json_bytes(result) != result_bytes:
        raise ValidationError("result_json")
    validated = validate_candidate_payload(
        result,
        fresh_evaluation_projection,
    )
    if type(report_bytes) is not bytes:
        raise ValidationError("report_encoding")
    try:
        report = report_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ValidationError("report_encoding") from exc
    if (
        "\r" in report
        or not report.endswith("\n")
        or report.endswith("\n\n")
    ):
        raise ValidationError("report_encoding")
    lines = report.splitlines()
    positions: list[int] = []
    for expected in SCOPE_LINES:
        matches = [
            index
            for index, line in enumerate(lines)
            if line == expected
        ]
        if len(matches) != 1:
            raise ValidationError("report_scope_boundary")
        positions.append(matches[0])
    if positions != sorted(positions):
        raise ValidationError("report_scope_boundary")
    marker = f"- result.json sha256:{sha256_bytes(result_bytes)}"
    if lines.count(marker) != 1:
        raise ValidationError("report_result_hash_binding")
    if report != render_expected_report_independently(validated):
        raise ValidationError("report_determinism")
    return validated


def _raw_path_has_alias(value: str) -> bool:
    return any(
        segment in (".", "..")
        for segment in value.replace("\\", "/").split("/")
    )


def _lexical_absolute(value: os.PathLike[str] | str) -> Path:
    raw = os.fspath(value)
    if type(raw) is not str:
        raise ValidationError("root_not_allowlisted")
    if _raw_path_has_alias(raw):
        raise ValidationError("root_lexical_alias")
    if not os.path.isabs(raw):
        raw = os.path.join(os.fspath(ROOT), raw)
    return Path(os.path.abspath(os.path.normpath(raw)))


def _is_reparse_or_link(metadata: Any) -> bool:
    return (
        stat.S_ISLNK(metadata.st_mode)
        or bool(
            getattr(metadata, "st_file_attributes", 0)
            & REPARSE_POINT
        )
    )


def _safe_lstat(path: Path) -> os.stat_result:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as exc:
        raise ValidationError("root_missing") from exc
    except OSError as exc:
        raise ValidationError("root_metadata") from exc
    if _is_reparse_or_link(metadata):
        raise ValidationError("root_reparse_or_link")
    return metadata


def _directory_chain(target: Path) -> None:
    try:
        relative = target.relative_to(ROOT)
    except ValueError as exc:
        raise ValidationError("root_not_allowlisted") from exc
    current = ROOT
    metadata = _safe_lstat(current)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError("root_directory_type")
    for part in relative.parts:
        current = current / part
        metadata = _safe_lstat(current)
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValidationError("root_directory_type")


def _metadata_identity(metadata: Any) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _read_stable_file(path: Path, expected: os.stat_result) -> bytes:
    try:
        with open(path, "rb") as handle:
            before = os.fstat(handle.fileno())
            if (
                _is_reparse_or_link(before)
                or not stat.S_ISREG(before.st_mode)
                or _metadata_identity(before) != _metadata_identity(expected)
            ):
                raise ValidationError("root_changed_during_read")
            payload = handle.read(MAX_PAIR_FILE_BYTES + 1)
            after = os.fstat(handle.fileno())
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError("root_changed_during_read") from exc
    if (
        len(payload) > MAX_PAIR_FILE_BYTES
        or _is_reparse_or_link(after)
        or not stat.S_ISREG(after.st_mode)
        or _metadata_identity(after) != _metadata_identity(before)
    ):
        raise ValidationError("root_changed_during_read")
    return payload


def read_allowlisted_pair(
    section: str,
    requested_root: os.PathLike[str] | str | None = None,
) -> tuple[bytes, bytes]:
    if section == "candidate":
        if requested_root is None:
            raise ValidationError("root_not_allowlisted")
        target = _lexical_absolute(requested_root)
        expected = _lexical_absolute(CANDIDATE_ROOT)
    elif section == "checkpoint":
        if requested_root is not None:
            raise ValidationError("root_not_allowlisted")
        target = _lexical_absolute(CANONICAL_ROOT)
        expected = target
    else:
        raise ValidationError("root_section")
    if os.path.normcase(os.fspath(target)) != os.path.normcase(
        os.fspath(expected),
    ):
        raise ValidationError("root_not_allowlisted")

    _directory_chain(target)
    try:
        children = os.listdir(target)
    except OSError as exc:
        raise ValidationError("root_children") from exc
    if (
        len(children) != len(PAIR_CHILDREN)
        or set(children) != PAIR_CHILDREN
    ):
        raise ValidationError("root_children")

    metadata: dict[str, os.stat_result] = {}
    for name in ("result.json", "report.md"):
        child = target / name
        child_metadata = _safe_lstat(child)
        if not stat.S_ISREG(child_metadata.st_mode):
            raise ValidationError("root_file_type")
        if child_metadata.st_size > MAX_PAIR_FILE_BYTES:
            raise ValidationError("root_file_size")
        metadata[name] = child_metadata
    result_bytes = _read_stable_file(
        target / "result.json",
        metadata["result.json"],
    )
    report_bytes = _read_stable_file(
        target / "report.md",
        metadata["report.md"],
    )
    return result_bytes, report_bytes


def parse_cli_args(
    argv: Sequence[str],
) -> tuple[str, str | None]:
    if type(argv) not in (list, tuple):
        raise CliUsageError("cli_arguments")
    if len(argv) == 1 and argv[0] in (
        "contracts",
        "scenarios",
        "synthetic",
        "checkpoint",
    ):
        return argv[0], None
    if (
        len(argv) == 3
        and argv[0] == "candidate"
        and argv[1] == "--root"
        and type(argv[2]) is str
    ):
        return "candidate", argv[2]
    raise CliUsageError("cli_arguments")


def _section_inputs() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, PhaseCScenarioV1],
]:
    policy, raw_scenarios, parsed = _load_validated_inputs()
    scenarios = {scenario.case_id: scenario for scenario in parsed}
    return policy, raw_scenarios, scenarios


def _run_section(section: str, requested_root: str | None) -> None:
    if section == "contracts":
        try:
            validate_phase_c_policy(load_json_strict(POLICY_PATH))
        except (OSError, PhaseCContractError) as exc:
            raise ValidationError("contracts_invalid") from exc
        return
    policy, _raw_scenarios, scenarios = _section_inputs()
    if section == "scenarios":
        return
    projection = build_fresh_evaluation_projection(policy, scenarios)
    if section == "synthetic":
        return
    result_bytes, report_bytes = read_allowlisted_pair(
        section,
        requested_root,
    )
    validate_pair_bytes(result_bytes, report_bytes, projection)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        section, requested_root = parse_cli_args(arguments)
    except CliUsageError:
        return 2
    try:
        _run_section(section, requested_root)
    except ValidationError as exc:
        print(f"{section}:fail:{exc.code}", file=sys.stderr)
        return 1
    except (OSError, PhaseCContractError, ValueError, TypeError):
        print(f"{section}:fail:internal_error", file=sys.stderr)
        return 1
    print(f"{section}:pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
