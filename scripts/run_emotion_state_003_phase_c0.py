from __future__ import annotations

import json
import math
import os
import re
import stat
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from scripts.emotion_state_phase_c_contracts import (
    CLAIM_OR_CONSUMPTION_FLAG_NAMES,
    EMITTED_ABSTENTION_COUNT_ORDER,
    EXPECTED_COUNTS_BY_ABSTENTION_REASON,
    EXPECTED_COUNTS_BY_FAMILY,
    EXPECTED_COUNTS_BY_MODALITY_FAMILY,
    EXPECTED_COUNTS_BY_SIGNAL_FAMILY,
    EXPECTED_SCENARIO_CLASSIFICATIONS,
    EXPECTED_SCENARIO_IDS,
    FAMILY_COUNT_ORDER,
    FORBIDDEN_PHASE_C_KEY_FRAGMENTS,
    INVARIANT_NAMES,
    MODALITY_FAMILY_COUNT_ORDER,
    PHASE_C_RESULT_FIELDS,
    REJECTION_CASE_IDS,
    SAFETY_INVARIANT_NAMES,
    SIGNAL_FAMILY_COUNT_ORDER,
    PhaseCContractError,
    PhaseCScenarioEvaluationV1,
    PhaseCScenarioOutcomeV1,
    canonical_json_bytes,
    load_json_strict,
    sha256_bytes,
    validate_phase_c_policy,
    validate_phase_c_scenario_payload,
)
from scripts.emotion_state_phase_c_temporal_tracker import (
    evaluate_phase_c_scenarios,
)


class RunnerError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
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
SCENARIO_COUNT_FIELDS = frozenset({
    "total",
    "passed",
    "failed",
    "rejection_cases",
})
COMPLEXITY_FIELDS = frozenset({
    "numeric_policy_parameter_count",
    "scenario_count",
    "operational_signal_count",
    "synthetic_evidence_class_count",
    "runtime_files_modified",
})
EXPECTED_COMPLEXITY = MappingProxyType({
    "numeric_policy_parameter_count": 36,
    "scenario_count": 30,
    "operational_signal_count": 5,
    "synthetic_evidence_class_count": 5,
    "runtime_files_modified": 0,
})
EXPECTED_REJECTION_COUNT_BY_CASE = MappingProxyType({
    case_id: (
        4
        if case_id == "forbidden_phase_b_field_rejected"
        else int(case_id in REJECTION_CASE_IDS)
    )
    for case_id in EXPECTED_SCENARIO_IDS
})
HEX_SHA256 = re.compile(r"^[0-9A-F]{64}$")
RESULT_FORBIDDEN_IDENTITY_PREFIXES = (
    "evidence:uuid:",
    "session:",
    "turn:",
    "event:",
    "campaign:",
    "version:",
    "ind:",
)
RESULT_FORBIDDEN_KEYS = frozenset({
    "case_id",
    "evidence_atoms",
    "accepted_frames",
    "confidence_by_signal",
    "transcript_text",
    "audio_bytes",
})
PAIR_CHILDREN = frozenset({"result.json", "report.md"})
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _count_exact_int_leaves(value: Any) -> int:
    if type(value) is int:
        return 1
    if type(value) is dict:
        return sum(_count_exact_int_leaves(item) for item in value.values())
    if type(value) in (list, tuple):
        return sum(_count_exact_int_leaves(item) for item in value)
    return 0


def _json_object_from_bytes(payload: bytes, code: str) -> dict[str, Any]:
    if type(payload) is not bytes:
        raise RunnerError(code)

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
        value = json.loads(
            decoded,
            parse_constant=reject_constant,
            parse_float=finite_float,
            object_pairs_hook=unique_object,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise RunnerError(code) from exc
    if type(value) is not dict:
        raise RunnerError(code)
    return value


def _load_canonical_inputs(
    policy_bytes: bytes,
    scenario_bytes: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = _json_object_from_bytes(policy_bytes, "policy_bytes_invalid")
    scenarios = _json_object_from_bytes(
        scenario_bytes,
        "scenario_bytes_invalid",
    )
    try:
        validate_phase_c_policy(policy)
        if canonical_json_bytes(policy) != policy_bytes:
            raise RunnerError("policy_bytes_invalid")
    except PhaseCContractError as exc:
        raise RunnerError("policy_bytes_invalid") from exc
    try:
        validate_phase_c_scenario_payload(scenarios, policy)
        if canonical_json_bytes(scenarios) != scenario_bytes:
            raise RunnerError("scenario_bytes_invalid")
    except PhaseCContractError as exc:
        raise RunnerError("scenario_bytes_invalid") from exc
    return policy, scenarios


def _exact_count_tuple(
    value: Any,
    order: tuple[str, ...],
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple or len(value) != len(order):
        raise RunnerError("evaluation_invalid")
    for index, row in enumerate(value):
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or row[0] != order[index]
            or type(row[1]) is not int
            or row[1] < 0
        ):
            raise RunnerError("evaluation_invalid")
    return value


def _validate_evaluation(
    evaluation: PhaseCScenarioEvaluationV1,
) -> PhaseCScenarioEvaluationV1:
    if type(evaluation) is not PhaseCScenarioEvaluationV1:
        raise RunnerError("evaluation_invalid")
    for value in (
        evaluation.total_scenarios,
        evaluation.passed_scenarios,
        evaluation.failed_scenarios,
    ):
        if type(value) is not int or value < 0:
            raise RunnerError("evaluation_invalid")
    if (
        evaluation.total_scenarios != len(EXPECTED_SCENARIO_IDS)
        or evaluation.passed_scenarios + evaluation.failed_scenarios
        != evaluation.total_scenarios
        or type(evaluation.outcomes) is not tuple
        or len(evaluation.outcomes) != evaluation.total_scenarios
    ):
        raise RunnerError("evaluation_invalid")

    outcome_abstention_totals = {
        name: 0
        for name in EMITTED_ABSTENTION_COUNT_ORDER
    }
    outcome_invariant_totals = {name: 0 for name in INVARIANT_NAMES}
    passed = 0
    for index, outcome in enumerate(evaluation.outcomes):
        case_id = EXPECTED_SCENARIO_IDS[index]
        if (
            type(outcome) is not PhaseCScenarioOutcomeV1
            or outcome.case_id != case_id
            or (
                outcome.family,
                outcome.signal_family,
                outcome.modality_family,
            )
            != EXPECTED_SCENARIO_CLASSIFICATIONS[case_id]
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
            or outcome.rejection_count
            != EXPECTED_REJECTION_COUNT_BY_CASE[case_id]
        ):
            raise RunnerError("evaluation_invalid")
        abstention_counts = _exact_count_tuple(
            outcome.abstention_reason_counts,
            EMITTED_ABSTENTION_COUNT_ORDER,
        )
        for name, value in abstention_counts:
            outcome_abstention_totals[name] += value
        for name in outcome.failed_invariants:
            outcome_invariant_totals[name] += 1
        passed += int(outcome.passed)

    if (
        passed != evaluation.passed_scenarios
        or evaluation.failed_scenarios
        != evaluation.total_scenarios - passed
    ):
        raise RunnerError("evaluation_invalid")

    family = _exact_count_tuple(
        evaluation.counts_by_family,
        FAMILY_COUNT_ORDER,
    )
    signal = _exact_count_tuple(
        evaluation.counts_by_signal,
        SIGNAL_FAMILY_COUNT_ORDER,
    )
    modality = _exact_count_tuple(
        evaluation.counts_by_modality,
        MODALITY_FAMILY_COUNT_ORDER,
    )
    abstention = _exact_count_tuple(
        evaluation.counts_by_abstention_reason,
        EMITTED_ABSTENTION_COUNT_ORDER,
    )
    invariants = _exact_count_tuple(
        evaluation.invariant_counts,
        INVARIANT_NAMES,
    )
    if (
        dict(family) != dict(EXPECTED_COUNTS_BY_FAMILY)
        or dict(signal) != dict(EXPECTED_COUNTS_BY_SIGNAL_FAMILY)
        or dict(modality) != dict(EXPECTED_COUNTS_BY_MODALITY_FAMILY)
        or dict(abstention) != outcome_abstention_totals
        or dict(invariants) != outcome_invariant_totals
    ):
        raise RunnerError("evaluation_invalid")
    if (
        evaluation.failed_scenarios == 0
        and dict(abstention) != dict(EXPECTED_COUNTS_BY_ABSTENTION_REASON)
    ):
        raise RunnerError("evaluation_invalid")
    if (
        type(evaluation.deterministic_replay_passed) is not bool
        or type(evaluation.privacy_boundary_passed) is not bool
        or evaluation.deterministic_replay_passed
        != (outcome_invariant_totals["deterministic_replay"] == 0)
        or evaluation.privacy_boundary_passed
        != all(
            outcome_invariant_totals[name] == 0
            for name in (
                "rejection_no_mutation",
                "session_isolation",
                "semantic_output",
                "privacy_boundary",
            )
        )
    ):
        raise RunnerError("evaluation_invalid")
    return evaluation


def _snapshot_decision_mapping(
    value: Any,
    names: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RunnerError("decision_inputs")
    try:
        observed_keys = tuple(value)
        if (
            len(value) != len(names)
            or len(observed_keys) != len(names)
            or set(observed_keys) != set(names)
        ):
            raise RunnerError("decision_inputs")
        return {name: value[name] for name in names}
    except RunnerError:
        raise
    except Exception as exc:
        raise RunnerError("decision_inputs") from exc


def decide_phase_c_checkpoint(
    *,
    failed_scenarios: int,
    invariant_counts: Mapping[str, int],
    deterministic_replay_passed: bool,
    privacy_boundary_passed: bool,
    claim_or_consumption_flags: Mapping[str, bool],
) -> str:
    invariant_snapshot = _snapshot_decision_mapping(
        invariant_counts,
        INVARIANT_NAMES,
    )
    claim_snapshot = _snapshot_decision_mapping(
        claim_or_consumption_flags,
        CLAIM_OR_CONSUMPTION_FLAG_NAMES,
    )
    if (
        type(failed_scenarios) is not int
        or failed_scenarios < 0
        or any(
            type(value) is not int or value < 0
            for value in invariant_snapshot.values()
        )
        or type(deterministic_replay_passed) is not bool
        or type(privacy_boundary_passed) is not bool
        or any(
            type(value) is not bool
            for value in claim_snapshot.values()
        )
    ):
        raise RunnerError("decision_inputs")
    claim_or_consumption_boundary_failed = any(
        claim_snapshot[name]
        for name in CLAIM_OR_CONSUMPTION_FLAG_NAMES
    )
    safety_invariant_failed = any(
        invariant_snapshot[name] > 0
        for name in SAFETY_INVARIANT_NAMES
    )
    if (
        claim_or_consumption_boundary_failed
        or safety_invariant_failed
        or not deterministic_replay_passed
        or not privacy_boundary_passed
    ):
        return "discard"
    if failed_scenarios:
        return "revise"
    return "keep"


def _canonical_count_mapping(
    rows: tuple[tuple[str, int], ...],
) -> dict[str, int]:
    return {name: dict(rows)[name] for name in sorted(dict(rows))}


def build_phase_c_result(
    evaluation: PhaseCScenarioEvaluationV1,
    policy_bytes: bytes,
    scenario_bytes: bytes,
) -> dict[str, Any]:
    validated = _validate_evaluation(evaluation)
    policy, _scenarios = _load_canonical_inputs(policy_bytes, scenario_bytes)
    numeric_parameter_count = _count_exact_int_leaves(policy)
    if numeric_parameter_count != 36:
        raise RunnerError("policy_bytes_invalid")
    claim_flags = {
        name: False
        for name in CLAIM_OR_CONSUMPTION_FLAG_NAMES
    }
    invariant_counts = dict(validated.invariant_counts)
    decision = decide_phase_c_checkpoint(
        failed_scenarios=validated.failed_scenarios,
        invariant_counts=invariant_counts,
        deterministic_replay_passed=validated.deterministic_replay_passed,
        privacy_boundary_passed=validated.privacy_boundary_passed,
        claim_or_consumption_flags=claim_flags,
    )
    without_digest: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_ID,
        "policy_id": POLICY_ID,
        "evidence_policy_version": EVIDENCE_POLICY_VERSION,
        "policy_sha256": sha256_bytes(policy_bytes),
        "scenario_sha256": sha256_bytes(scenario_bytes),
        "scenario_counts": {
            "total": len(EXPECTED_SCENARIO_IDS),
            "passed": validated.passed_scenarios,
            "failed": validated.failed_scenarios,
            "rejection_cases": len(REJECTION_CASE_IDS),
        },
        "counts_by_family": _canonical_count_mapping(
            validated.counts_by_family,
        ),
        "counts_by_signal": _canonical_count_mapping(
            validated.counts_by_signal,
        ),
        "counts_by_modality": _canonical_count_mapping(
            validated.counts_by_modality,
        ),
        "counts_by_abstention_reason": _canonical_count_mapping(
            validated.counts_by_abstention_reason,
        ),
        "invariant_counts": _canonical_count_mapping(
            validated.invariant_counts,
        ),
        "deterministic_replay_passed": (
            validated.deterministic_replay_passed
        ),
        "privacy_boundary_passed": validated.privacy_boundary_passed,
        **claim_flags,
        "complexity": {
            **EXPECTED_COMPLEXITY,
            "numeric_policy_parameter_count": numeric_parameter_count,
        },
        "decision": decision,
    }
    result = {
        **without_digest,
        "aggregate_output_sha256": sha256_bytes(
            canonical_json_bytes(without_digest),
        ),
    }
    return validate_phase_c_result_payload(result)


def _exact_nonnegative_count_mapping(
    value: Any,
    names: tuple[str, ...],
) -> dict[str, int]:
    expected_keys = tuple(sorted(names))
    if (
        type(value) is not dict
        or tuple(value) != expected_keys
        or any(
            type(item) is not int or item < 0
            for item in value.values()
        )
    ):
        raise RunnerError("result_payload_invalid")
    return value


def _aggregate_content_is_forbidden(value: Any) -> bool:
    if type(value) is dict:
        for key, child in value.items():
            if (
                type(key) is not str
                or key.lower() in RESULT_FORBIDDEN_KEYS
                or any(
                    fragment in key.lower()
                    for fragment in FORBIDDEN_PHASE_C_KEY_FRAGMENTS
                )
                or _aggregate_content_is_forbidden(child)
            ):
                return True
        return False
    if type(value) is list:
        return any(_aggregate_content_is_forbidden(item) for item in value)
    if type(value) is str:
        lowered = value.lower()
        return (
            lowered.startswith(RESULT_FORBIDDEN_IDENTITY_PREFIXES)
            or any(case_id in lowered for case_id in EXPECTED_SCENARIO_IDS)
        )
    return type(value) not in (bool, int)


def validate_phase_c_result_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict or set(payload) != PHASE_C_RESULT_FIELDS:
        raise RunnerError("result_payload_invalid")
    if (
        payload["schema_version"] != RESULT_SCHEMA_VERSION
        or payload["checkpoint_id"] != CHECKPOINT_ID
        or payload["policy_id"] != POLICY_ID
        or payload["evidence_policy_version"] != EVIDENCE_POLICY_VERSION
        or any(
            type(payload[name]) is not str
            or HEX_SHA256.fullmatch(payload[name]) is None
            for name in (
                "policy_sha256",
                "scenario_sha256",
                "aggregate_output_sha256",
            )
        )
    ):
        raise RunnerError("result_payload_invalid")
    scenario_counts = payload["scenario_counts"]
    if (
        type(scenario_counts) is not dict
        or set(scenario_counts) != SCENARIO_COUNT_FIELDS
        or any(
            type(value) is not int or value < 0
            for value in scenario_counts.values()
        )
        or scenario_counts["total"] != len(EXPECTED_SCENARIO_IDS)
        or scenario_counts["passed"] + scenario_counts["failed"]
        != scenario_counts["total"]
        or scenario_counts["rejection_cases"] != len(REJECTION_CASE_IDS)
    ):
        raise RunnerError("result_payload_invalid")
    family = _exact_nonnegative_count_mapping(
        payload["counts_by_family"],
        FAMILY_COUNT_ORDER,
    )
    signal = _exact_nonnegative_count_mapping(
        payload["counts_by_signal"],
        SIGNAL_FAMILY_COUNT_ORDER,
    )
    modality = _exact_nonnegative_count_mapping(
        payload["counts_by_modality"],
        MODALITY_FAMILY_COUNT_ORDER,
    )
    abstention = _exact_nonnegative_count_mapping(
        payload["counts_by_abstention_reason"],
        EMITTED_ABSTENTION_COUNT_ORDER,
    )
    invariants = _exact_nonnegative_count_mapping(
        payload["invariant_counts"],
        INVARIANT_NAMES,
    )
    failed = scenario_counts["failed"]
    if (
        family != dict(sorted(EXPECTED_COUNTS_BY_FAMILY.items()))
        or signal != dict(sorted(EXPECTED_COUNTS_BY_SIGNAL_FAMILY.items()))
        or modality != dict(
            sorted(EXPECTED_COUNTS_BY_MODALITY_FAMILY.items())
        )
        or (
            failed == 0
            and abstention
            != dict(sorted(EXPECTED_COUNTS_BY_ABSTENTION_REASON.items()))
        )
        or any(value > failed for value in invariants.values())
        or (failed == 0 and any(invariants.values()))
        or (failed > 0 and sum(invariants.values()) < failed)
    ):
        raise RunnerError("result_payload_invalid")
    if (
        type(payload["deterministic_replay_passed"]) is not bool
        or type(payload["privacy_boundary_passed"]) is not bool
        or payload["deterministic_replay_passed"]
        != (invariants["deterministic_replay"] == 0)
        or payload["privacy_boundary_passed"]
        != all(
            invariants[name] == 0
            for name in (
                "rejection_no_mutation",
                "session_isolation",
                "semantic_output",
                "privacy_boundary",
            )
        )
        or any(payload[name] is not False for name in CLAIM_OR_CONSUMPTION_FLAG_NAMES)
    ):
        raise RunnerError("result_payload_invalid")
    complexity = payload["complexity"]
    if (
        type(complexity) is not dict
        or set(complexity) != COMPLEXITY_FIELDS
        or any(type(value) is not int for value in complexity.values())
        or complexity != EXPECTED_COMPLEXITY
    ):
        raise RunnerError("result_payload_invalid")
    expected_decision = decide_phase_c_checkpoint(
        failed_scenarios=failed,
        invariant_counts={
            name: invariants[name]
            for name in INVARIANT_NAMES
        },
        deterministic_replay_passed=payload[
            "deterministic_replay_passed"
        ],
        privacy_boundary_passed=payload["privacy_boundary_passed"],
        claim_or_consumption_flags={
            name: payload[name]
            for name in CLAIM_OR_CONSUMPTION_FLAG_NAMES
        },
    )
    if payload["decision"] != expected_decision:
        raise RunnerError("result_payload_invalid")
    without_digest = {
        key: value
        for key, value in payload.items()
        if key != "aggregate_output_sha256"
    }
    if payload["aggregate_output_sha256"] != sha256_bytes(
        canonical_json_bytes(without_digest),
    ):
        raise RunnerError("result_payload_invalid")
    if _aggregate_content_is_forbidden(payload):
        raise RunnerError("result_payload_invalid")
    canonical_json_bytes(payload)
    return payload


def _compact(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _report_template(result: dict[str, Any], final_digest: str) -> str:
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
        "",
    ))


def render_phase_c_report(result: dict[str, Any]) -> str:
    validate_phase_c_result_payload(result)
    final_digest = sha256_bytes(canonical_json_bytes(result))
    return _report_template(result, final_digest)


def _normalized_separators(value: str) -> str:
    return value.replace("\\", "/")


def _has_relative_segment(value: str) -> bool:
    return any(
        segment in (".", "..")
        for segment in _normalized_separators(value).split("/")
    )


def resolve_output_root(
    mode: str,
    requested_root: os.PathLike[str] | str | None = None,
) -> Path:
    if type(mode) is not str or mode not in ("candidate", "canonical"):
        raise RunnerError("runner_mode")
    selected = CANDIDATE_ROOT if mode == "candidate" else CANONICAL_ROOT
    selected_text = os.fspath(selected)
    if requested_root is not None:
        try:
            requested_text = os.fspath(requested_root)
        except TypeError as exc:
            raise RunnerError("output_root_not_allowlisted") from exc
        if (
            type(requested_text) is not str
            or _has_relative_segment(requested_text)
            or _normalized_separators(requested_text)
            != _normalized_separators(selected_text)
        ):
            raise RunnerError("output_root_not_allowlisted")
    lexical = os.path.abspath(os.path.normpath(selected_text))
    project = os.path.abspath(os.path.normpath(os.fspath(ROOT)))
    try:
        inside = os.path.commonpath((project, lexical)) == project
    except ValueError as exc:
        raise RunnerError("output_path_escape") from exc
    if not inside:
        raise RunnerError("output_path_escape")
    return Path(lexical)


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise RunnerError("output_ancestor_type") from exc


def _is_reparse(metadata: Any) -> bool:
    return bool(
        getattr(metadata, "st_file_attributes", 0)
        & REPARSE_POINT
    )


def _require_directory_metadata(path: Path, metadata: Any) -> None:
    if stat.S_ISLNK(metadata.st_mode) or _is_reparse(metadata):
        raise RunnerError("output_reparse_or_link")
    if not stat.S_ISDIR(metadata.st_mode):
        raise RunnerError("output_ancestor_type")


def _require_directory_chain(path: Path) -> None:
    project = resolve_output_project_root()
    try:
        relative = os.path.relpath(path, project)
    except ValueError as exc:
        raise RunnerError("output_path_escape") from exc
    if relative == os.pardir or relative.startswith(os.pardir + os.sep):
        raise RunnerError("output_path_escape")
    current = project
    metadata = _lstat(current)
    if metadata is None:
        raise RunnerError("output_ancestor_type")
    _require_directory_metadata(current, metadata)
    if relative == os.curdir:
        return
    for segment in Path(relative).parts:
        current = current / segment
        metadata = _lstat(current)
        if metadata is None:
            raise RunnerError("output_ancestor_type")
        _require_directory_metadata(current, metadata)


def resolve_output_project_root() -> Path:
    return Path(os.path.abspath(os.path.normpath(os.fspath(ROOT))))


def _existing_target_code(path: Path, code: str) -> None:
    metadata = _lstat(path)
    if metadata is None:
        return
    if stat.S_ISLNK(metadata.st_mode) or _is_reparse(metadata):
        raise RunnerError("output_reparse_or_link")
    raise RunnerError(code)


def _mode_for_output_root(output_root: os.PathLike[str] | str) -> tuple[str, Path]:
    try:
        requested = os.fspath(output_root)
    except TypeError as exc:
        raise RunnerError("output_root_not_allowlisted") from exc
    if type(requested) is not str or _has_relative_segment(requested):
        raise RunnerError("output_root_not_allowlisted")
    normalized = _normalized_separators(requested)
    for mode, selected in (
        ("candidate", CANDIDATE_ROOT),
        ("canonical", CANONICAL_ROOT),
    ):
        if normalized == _normalized_separators(os.fspath(selected)):
            return mode, resolve_output_root(mode, requested)
    raise RunnerError("output_root_not_allowlisted")


def _prepare_output_parent(mode: str, final: Path, stage: Path) -> None:
    parent = final.parent
    if mode == "candidate":
        _require_directory_chain(parent.parent)
        metadata = _lstat(parent)
        if metadata is None:
            try:
                os.mkdir(parent)
            except OSError as exc:
                raise RunnerError("stage_write_failed") from exc
            metadata = _lstat(parent)
        if metadata is None:
            raise RunnerError("output_ancestor_type")
        _require_directory_metadata(parent, metadata)
    else:
        _require_directory_chain(parent)

    _existing_target_code(final, "output_exists")
    _existing_target_code(stage, "stage_exists")
    if mode == "candidate":
        try:
            children = tuple(entry.name for entry in os.scandir(parent))
        except OSError as exc:
            raise RunnerError("output_parent_children") from exc
        if children:
            raise RunnerError("output_parent_children")


def _write_exclusive_file(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    stream = None
    try:
        stream = os.fdopen(descriptor, "wb", closefd=False)
        written = stream.write(payload)
        if written != len(payload):
            raise OSError("short write")
        stream.flush()
        os.fsync(stream.fileno())
    finally:
        try:
            if stream is not None:
                stream.close()
        finally:
            os.close(descriptor)


def _regular_file_bytes(path: Path) -> bytes:
    before = _lstat(path)
    if (
        before is None
        or stat.S_ISLNK(before.st_mode)
        or _is_reparse(before)
        or not stat.S_ISREG(before.st_mode)
    ):
        raise RunnerError("stage_readback_failed")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RunnerError("stage_readback_failed") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _directory_identity(opened) != _directory_identity(before)
        ):
            raise RunnerError("stage_readback_failed")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    after = _lstat(path)
    if (
        after is None
        or stat.S_ISLNK(after.st_mode)
        or _is_reparse(after)
        or not stat.S_ISREG(after.st_mode)
        or _directory_identity(after) != _directory_identity(before)
    ):
        raise RunnerError("stage_readback_failed")
    return b"".join(chunks)


def _verify_pair_directory(
    root: Path,
    result_bytes: bytes,
    report_bytes: bytes,
    failure_code: str,
) -> None:
    try:
        metadata = _lstat(root)
    except RunnerError as exc:
        raise RunnerError(failure_code) from exc
    if (
        metadata is None
        or stat.S_ISLNK(metadata.st_mode)
        or _is_reparse(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        raise RunnerError(failure_code)
    try:
        children = tuple(sorted(entry.name for entry in os.scandir(root)))
    except OSError as exc:
        raise RunnerError(failure_code) from exc
    if children != tuple(sorted(PAIR_CHILDREN)):
        raise RunnerError(failure_code)
    try:
        actual_result = _regular_file_bytes(root / "result.json")
        actual_report = _regular_file_bytes(root / "report.md")
    except RunnerError as exc:
        raise RunnerError(failure_code) from exc
    if actual_result != result_bytes or actual_report != report_bytes:
        raise RunnerError(failure_code)


def _directory_identity(metadata: Any) -> tuple[int, int]:
    return metadata.st_dev, metadata.st_ino


def _cleanup_verified_stage(
    stage: Path,
    identity: tuple[int, int],
) -> None:
    metadata = _lstat(stage)
    if metadata is None:
        return
    if (
        stat.S_ISLNK(metadata.st_mode)
        or _is_reparse(metadata)
        or not stat.S_ISDIR(metadata.st_mode)
        or _directory_identity(metadata) != identity
    ):
        return
    try:
        children = tuple(entry.name for entry in os.scandir(stage))
    except OSError:
        return
    if any(name not in PAIR_CHILDREN for name in children):
        return
    for name in children:
        child = stage / name
        child_metadata = _lstat(child)
        if (
            child_metadata is None
            or stat.S_ISLNK(child_metadata.st_mode)
            or _is_reparse(child_metadata)
            or not stat.S_ISREG(child_metadata.st_mode)
        ):
            return
    try:
        for name in children:
            os.unlink(stage / name)
        os.rmdir(stage)
    except OSError:
        return


def _validated_pair_bytes(
    result_bytes: bytes,
    report_bytes: bytes,
) -> dict[str, Any]:
    try:
        result = _json_object_from_bytes(
            result_bytes,
            "result_bytes_invalid",
        )
        validate_phase_c_result_payload(result)
        if canonical_json_bytes(result) != result_bytes:
            raise RunnerError("result_bytes_invalid")
    except (PhaseCContractError, RunnerError) as exc:
        if isinstance(exc, RunnerError) and exc.code == "result_bytes_invalid":
            raise
        raise RunnerError("result_bytes_invalid") from exc
    if type(report_bytes) is not bytes:
        raise RunnerError("report_bytes_invalid")
    try:
        report = report_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise RunnerError("report_bytes_invalid") from exc
    if (
        b"\r" in report_bytes
        or report.encode("utf-8") != report_bytes
        or render_phase_c_report(result).encode("utf-8") != report_bytes
    ):
        raise RunnerError("report_bytes_invalid")
    return result


def write_phase_c_pair(
    output_root: os.PathLike[str] | str,
    result_bytes: bytes,
    report_bytes: bytes,
) -> Path:
    _validated_pair_bytes(result_bytes, report_bytes)
    mode, final = _mode_for_output_root(output_root)
    stage = Path(f"{final}.stage")
    _prepare_output_parent(mode, final, stage)
    stage_identity: tuple[int, int] | None = None
    renamed = False
    try:
        try:
            os.mkdir(stage)
        except OSError as exc:
            raise RunnerError("stage_write_failed") from exc
        metadata = _lstat(stage)
        if metadata is None:
            raise RunnerError("stage_write_failed")
        _require_directory_metadata(stage, metadata)
        parent_metadata = _lstat(final.parent)
        if (
            parent_metadata is None
            or metadata.st_dev != parent_metadata.st_dev
        ):
            raise RunnerError("stage_write_failed")
        stage_identity = _directory_identity(metadata)
        try:
            _write_exclusive_file(stage / "result.json", result_bytes)
            _write_exclusive_file(stage / "report.md", report_bytes)
        except OSError as exc:
            raise RunnerError("stage_write_failed") from exc
        _verify_pair_directory(
            stage,
            result_bytes,
            report_bytes,
            "stage_readback_failed",
        )
        _existing_target_code(final, "output_exists")
        try:
            os.rename(stage, final)
        except OSError as exc:
            raise RunnerError("atomic_rename_failed") from exc
        renamed = True
        _verify_pair_directory(
            final,
            result_bytes,
            report_bytes,
            "final_readback_failed",
        )
        return final
    except RunnerError:
        if not renamed and stage_identity is not None:
            _cleanup_verified_stage(stage, stage_identity)
        raise


def _parse_cli_mode(argv: Sequence[str]) -> str:
    if (
        type(argv) not in (list, tuple)
        or len(argv) != 1
        or type(argv[0]) is not str
        or argv[0] not in ("candidate", "canonical")
    ):
        raise RunnerError("runner_mode")
    return argv[0]


def main(argv: Sequence[str] | None = None) -> int:
    mode = _parse_cli_mode(sys.argv[1:] if argv is None else argv)
    policy = validate_phase_c_policy(load_json_strict(POLICY_PATH))
    raw_scenarios = load_json_strict(SCENARIO_PATH)
    parsed = validate_phase_c_scenario_payload(raw_scenarios, policy)
    scenarios = {scenario.case_id: scenario for scenario in parsed}
    policy_bytes = canonical_json_bytes(policy)
    scenario_bytes = canonical_json_bytes(raw_scenarios)
    evaluation = evaluate_phase_c_scenarios(policy, scenarios)
    first_result = build_phase_c_result(
        evaluation,
        policy_bytes,
        scenario_bytes,
    )
    second_result = build_phase_c_result(
        evaluation,
        policy_bytes,
        scenario_bytes,
    )
    first_result_bytes = canonical_json_bytes(first_result)
    second_result_bytes = canonical_json_bytes(second_result)
    first_report_bytes = render_phase_c_report(first_result).encode("utf-8")
    second_report_bytes = render_phase_c_report(second_result).encode("utf-8")
    if (
        first_result_bytes != second_result_bytes
        or first_report_bytes != second_report_bytes
    ):
        raise RunnerError("stage_readback_failed")
    output_root = resolve_output_root(mode)
    write_phase_c_pair(
        output_root,
        first_result_bytes,
        first_report_bytes,
    )
    print(f"mode: {mode}")
    print(f"decision: {first_result['decision']}")
    print(f"result_sha256: {sha256_bytes(first_result_bytes)}")
    print(f"report_sha256: {sha256_bytes(first_report_bytes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
