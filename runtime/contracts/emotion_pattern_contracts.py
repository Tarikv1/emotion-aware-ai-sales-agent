from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from runtime.contracts.emotion_state_contracts import ALLOWED_POLICY_EFFECTS, REQUIRED_BLOCKED_POLICY_EFFECTS

PATTERN_CANDIDATE_FIELDS = frozenset({
    "candidate_id", "hypothesis", "feature_definition", "target_operational_signal",
    "discovery_dataset_version", "unique_speaker_count", "independent_turn_count",
    "annotation_agreement", "status", "runtime_influence_allowed",
})
FEATURE_DEFINITION_FIELDS = frozenset({
    "relationship", "direction", "null_comparator", "minimum_observed_effect",
    "eligible_turn_definition", "search_budget", "tested_hypothesis_count",
    "max_qualifying_turns_per_speaker",
})
ANNOTATION_AGREEMENT_FIELDS = frozenset({
    "metric", "point_estimate", "lower_95_ci", "upper_95_ci", "status",
})
PATTERN_CONTENT_FIELDS = frozenset({
    "pattern_version", "source_snapshot_hashes", "feature_schema_version", "label_schema_version",
    "speaker_split_manifest_hash", "text_only_baseline", "acoustic_only_result", "multimodal_result",
    "calibration_result", "confidence_intervals", "slice_results", "known_limits",
    "allowed_runtime_effects", "blocked_runtime_effects", "rollback_version", "minimum_engine_version",
    "maximum_engine_version", "compatible_evidence_schema_versions", "compatible_state_schema_versions",
    "registry_sequence",
})
APPROVAL_FIELDS = frozenset({
    "approval_stage", "candidate_content_digest", "decision", "reviewer_id", "decision_timestamp",
    "approved_constraints", "evidence_artifact_digests", "signing_key_id", "signature_algorithm",
    "approval_record_digest", "approval_signature",
})
ENVELOPE_FIELDS = frozenset({
    "pattern_content", "candidate_content_digest", "shadow_authorization", "shadow_report_digest",
    "runtime_activation_approval", "envelope_digest",
})


class PatternContractError(ValueError):
    pass


class RuntimeActivationBlocked(PatternContractError):
    pass


def _require_json_domain(
    value: Any,
    label: str,
    active_container_ids: set[int] | None = None,
) -> None:
    if value is None or type(value) in {str, int, bool}:
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise PatternContractError(f"{label} contains a non-finite float")
        return
    if type(value) not in {dict, list}:
        raise PatternContractError(f"{label} contains a non-JSON value")

    if active_container_ids is None:
        active_container_ids = set()
    container_id = id(value)
    if container_id in active_container_ids:
        raise PatternContractError(f"{label} contains a circular reference")
    active_container_ids.add(container_id)
    try:
        if type(value) is list:
            for index, item in enumerate(value):
                _require_json_domain(item, f"{label}[{index}]", active_container_ids)
            return
        for key, item in value.items():
            if type(key) is not str:
                raise PatternContractError(f"{label} object keys must be strings")
            _require_json_domain(item, f"{label}.{key}", active_container_ids)
    finally:
        active_container_ids.remove(container_id)


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    if type(payload) is not dict:
        raise PatternContractError("canonical JSON payload must be an object")
    _require_json_domain(payload, "canonical JSON payload")
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise PatternContractError("canonical JSON payload cannot be serialized") from error


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest().upper()


def content_digest(pattern_content: dict[str, Any]) -> str:
    validate_pattern_content(pattern_content)
    return _sha256(pattern_content)


def approval_record_digest(approval: dict[str, Any]) -> str:
    unsigned = {
        key: value
        for key, value in approval.items()
        if key not in {"approval_record_digest", "approval_signature"}
    }
    return _sha256(unsigned)


def envelope_digest(envelope: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in envelope.items() if key != "envelope_digest"}
    return _sha256(unsigned)


def _require_exact(payload: dict[str, Any], fields: frozenset[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise PatternContractError(f"{label} must be an object")
    if set(payload) != fields:
        raise PatternContractError(f"{label} fields mismatch")


def _require_sha256(value: Any, label: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise PatternContractError(f"{label} must be an uppercase SHA-256 digest")


def _require_nonempty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PatternContractError(f"{label} must be a nonempty string")


def validate_pattern_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact(payload, PATTERN_CANDIDATE_FIELDS, "PatternCandidateV1")
    for field in ("candidate_id", "hypothesis", "target_operational_signal", "discovery_dataset_version"):
        _require_nonempty_string(payload[field], field)
    if payload["status"] != "candidate_hypothesis_only":
        raise PatternContractError("PatternCandidateV1 must remain a hypothesis")
    if payload["runtime_influence_allowed"] is not False:
        raise PatternContractError("PatternCandidateV1 cannot influence runtime")
    if type(payload["unique_speaker_count"]) is not int or payload["unique_speaker_count"] < 5:
        raise PatternContractError("PatternCandidateV1 requires at least five unique speakers")
    if type(payload["independent_turn_count"]) is not int or payload["independent_turn_count"] < 10:
        raise PatternContractError("PatternCandidateV1 requires at least ten independently labelled turns")
    if payload["target_operational_signal"] not in {
        "hesitation", "frustration", "confusion", "interest", "disengagement"
    }:
        raise PatternContractError("PatternCandidateV1 target signal is invalid")
    feature = payload["feature_definition"]
    if not isinstance(feature, dict):
        raise PatternContractError("feature_definition must be an object")
    _require_exact(feature, FEATURE_DEFINITION_FIELDS, "PatternCandidateV1.feature_definition")
    for field in ("relationship", "null_comparator", "eligible_turn_definition"):
        _require_nonempty_string(feature[field], f"feature_definition.{field}")
    if feature["direction"] not in {"increase", "decrease", "nonmonotonic"}:
        raise PatternContractError("feature_definition.direction is invalid")
    if (
        type(feature["minimum_observed_effect"]) not in {int, float}
        or not math.isfinite(feature["minimum_observed_effect"])
    ):
        raise PatternContractError("feature_definition.minimum_observed_effect must be finite numeric")
    if type(feature["search_budget"]) is not int or feature["search_budget"] < 1:
        raise PatternContractError("feature_definition.search_budget must be positive")
    if (
        type(feature["tested_hypothesis_count"]) is not int
        or not 1 <= feature["tested_hypothesis_count"] <= feature["search_budget"]
    ):
        raise PatternContractError("feature_definition.tested_hypothesis_count is outside the frozen budget")
    if type(feature["max_qualifying_turns_per_speaker"]) is not int or feature[
        "max_qualifying_turns_per_speaker"
    ] != 2:
        raise PatternContractError("candidate discovery permits at most two qualifying turns per speaker")
    agreement = payload["annotation_agreement"]
    if not isinstance(agreement, dict):
        raise PatternContractError("annotation_agreement must be an object")
    _require_exact(agreement, ANNOTATION_AGREEMENT_FIELDS, "PatternCandidateV1.annotation_agreement")
    if agreement["metric"] != "nominal_krippendorff_alpha":
        raise PatternContractError("candidate annotation agreement metric is invalid")
    if agreement["status"] == "not_evaluated_in_phase_a":
        if any(agreement[field] is not None for field in ("point_estimate", "lower_95_ci", "upper_95_ci")):
            raise PatternContractError("unevaluated annotation agreement cannot carry estimates")
    elif agreement["status"] == "estimated":
        values = [agreement[field] for field in ("point_estimate", "lower_95_ci", "upper_95_ci")]
        if any(type(value) not in {int, float} or not -1.0 <= value <= 1.0 for value in values):
            raise PatternContractError("annotation agreement estimates are invalid")
        if not agreement["lower_95_ci"] <= agreement["point_estimate"] <= agreement["upper_95_ci"]:
            raise PatternContractError("annotation agreement interval is invalid")
    else:
        raise PatternContractError("annotation agreement status is invalid")
    return payload


def validate_pattern_content(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact(payload, PATTERN_CONTENT_FIELDS, "PatternPackageContentV1")
    _require_json_domain(payload, "PatternPackageContentV1")
    for field in (
        "pattern_version", "feature_schema_version", "label_schema_version", "rollback_version",
        "minimum_engine_version", "maximum_engine_version",
    ):
        _require_nonempty_string(payload[field], field)
    hashes = payload["source_snapshot_hashes"]
    if (
        not isinstance(hashes, list)
        or not hashes
        or any(not isinstance(digest, str) for digest in hashes)
        or len(hashes) != len(set(hashes))
    ):
        raise PatternContractError("source_snapshot_hashes must be a nonempty unique list")
    for digest in hashes:
        _require_sha256(digest, "source_snapshot_hash")
    _require_sha256(payload["speaker_split_manifest_hash"], "speaker_split_manifest_hash")
    if payload["compatible_evidence_schema_versions"] != ["CustomerTurnEvidenceV1"]:
        raise PatternContractError("evidence schema compatibility is invalid for Phase A")
    if payload["compatible_state_schema_versions"] != ["PerceivedCustomerStateV1"]:
        raise PatternContractError("state schema compatibility is invalid for Phase A")
    for field in (
        "text_only_baseline", "acoustic_only_result", "multimodal_result", "calibration_result",
        "confidence_intervals", "slice_results",
    ):
        if not isinstance(payload[field], dict):
            raise PatternContractError(f"{field} must be an object")
    if (
        not isinstance(payload["known_limits"], list)
        or not payload["known_limits"]
        or any(not isinstance(limit, str) or not limit.strip() for limit in payload["known_limits"])
    ):
        raise PatternContractError("known_limits must be a nonempty list")
    if type(payload["registry_sequence"]) is not int or payload["registry_sequence"] < 1:
        raise PatternContractError("registry_sequence must be a positive integer")
    allowed = payload["allowed_runtime_effects"]
    blocked = payload["blocked_runtime_effects"]
    if (
        not isinstance(allowed, list)
        or any(not isinstance(item, str) for item in allowed)
        or len(allowed) != len(set(allowed))
        or set(allowed) - ALLOWED_POLICY_EFFECTS
    ):
        raise PatternContractError("pattern content contains an invalid or expanding runtime effect")
    if (
        not isinstance(blocked, list)
        or any(not isinstance(item, str) for item in blocked)
        or len(blocked) != len(set(blocked))
    ):
        raise PatternContractError("blocked_runtime_effects must be a unique list")
    if set(blocked) != REQUIRED_BLOCKED_POLICY_EFFECTS:
        raise PatternContractError("pattern content must preserve every blocked runtime effect")
    if set(allowed) & set(blocked):
        raise PatternContractError("allowed and blocked runtime effects overlap")
    return payload


def validate_detached_approval_shape(payload: dict[str, Any], expected_stage: str) -> dict[str, Any]:
    _require_exact(payload, APPROVAL_FIELDS, "DetachedPatternApprovalV1")
    if payload["approval_stage"] != expected_stage:
        raise PatternContractError("approval stage mismatch")
    if payload["signature_algorithm"] != "Ed25519":
        raise PatternContractError("signature algorithm must be Ed25519")
    _require_sha256(payload["candidate_content_digest"], "candidate_content_digest")
    if not isinstance(payload["evidence_artifact_digests"], list):
        raise PatternContractError("evidence_artifact_digests must be a list")
    for digest in payload["evidence_artifact_digests"]:
        _require_sha256(digest, "evidence_artifact_digest")
    for field in ("decision", "reviewer_id", "decision_timestamp", "signing_key_id", "approval_signature"):
        _require_nonempty_string(payload[field], field)
    if (
        not isinstance(payload["approved_constraints"], list)
        or not payload["approved_constraints"]
        or any(
            not isinstance(constraint, str) or not constraint.strip()
            for constraint in payload["approved_constraints"]
        )
    ):
        raise PatternContractError("approved_constraints must be a nonempty string list")
    _require_sha256(payload["approval_record_digest"], "approval_record_digest")
    if approval_record_digest(payload) != payload["approval_record_digest"]:
        raise PatternContractError("approval record digest mismatch")
    return payload


def validate_envelope_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact(payload, ENVELOPE_FIELDS, "ApprovedPatternEnvelopeV1")
    content = validate_pattern_content(payload["pattern_content"])
    _require_sha256(payload["candidate_content_digest"], "candidate_content_digest")
    _require_sha256(payload["shadow_report_digest"], "shadow_report_digest")
    _require_sha256(payload["envelope_digest"], "envelope_digest")
    if content_digest(content) != payload["candidate_content_digest"]:
        raise PatternContractError("candidate content digest mismatch")
    shadow = validate_detached_approval_shape(payload["shadow_authorization"], "shadow_authorization")
    runtime = validate_detached_approval_shape(payload["runtime_activation_approval"], "runtime_activation")
    if shadow["candidate_content_digest"] != payload["candidate_content_digest"]:
        raise PatternContractError("shadow authorization targets another candidate")
    if runtime["candidate_content_digest"] != payload["candidate_content_digest"]:
        raise PatternContractError("runtime approval targets another candidate")
    if payload["shadow_report_digest"] not in runtime["evidence_artifact_digests"]:
        raise PatternContractError("runtime approval does not bind the shadow report")
    if envelope_digest(payload) != payload["envelope_digest"]:
        raise PatternContractError("envelope digest mismatch")
    return payload


def authorize_runtime(payload: dict[str, Any]) -> None:
    validate_envelope_integrity(payload)
    raise RuntimeActivationBlocked(
        "EMOTION-STATE-001 Phase A has no signature verifier, trust store, promotion ACL, or runtime activation path"
    )


def _expect_pattern_error(callback: Any) -> None:
    try:
        callback()
    except PatternContractError:
        return
    raise AssertionError("expected PatternContractError")


def _fixture_approval(stage: str, candidate_digest: str, evidence_digests: list[str]) -> dict[str, Any]:
    approval = {
        "approval_stage": stage,
        "candidate_content_digest": candidate_digest,
        "decision": "approved_for_structural_fixture_only",
        "reviewer_id": "fixture-reviewer-not-authorized",
        "decision_timestamp": "2026-07-14T00:00:00Z",
        "approved_constraints": ["runtime_activation_blocked"],
        "evidence_artifact_digests": evidence_digests,
        "signing_key_id": "fixture-key-not-trusted",
        "signature_algorithm": "Ed25519",
    }
    approval["approval_record_digest"] = approval_record_digest(approval)
    approval["approval_signature"] = "test-fixture-not-a-valid-signature"
    return approval


def pattern_contract_self_check() -> str:
    candidate = {
        "candidate_id": "fixture-candidate-1",
        "hypothesis": "fixture relationship for structural validation only",
        "feature_definition": {
            "relationship": "synthetic structural relationship",
            "direction": "increase",
            "null_comparator": "no_association",
            "minimum_observed_effect": 0.0,
            "eligible_turn_definition": "synthetic_fixture_turns_only",
            "search_budget": 1,
            "tested_hypothesis_count": 1,
            "max_qualifying_turns_per_speaker": 2,
        },
        "target_operational_signal": "confusion",
        "discovery_dataset_version": "synthetic-fixture-v1",
        "unique_speaker_count": 5,
        "independent_turn_count": 10,
        "annotation_agreement": {
            "metric": "nominal_krippendorff_alpha",
            "point_estimate": None,
            "lower_95_ci": None,
            "upper_95_ci": None,
            "status": "not_evaluated_in_phase_a",
        },
        "status": "candidate_hypothesis_only",
        "runtime_influence_allowed": False,
    }
    validate_pattern_candidate(candidate)
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(candidate, unique_speaker_count=4)))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(candidate, runtime_influence_allowed=True)))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(
        candidate,
        feature_definition=dict(candidate["feature_definition"], max_qualifying_turns_per_speaker=3),
    )))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(
        candidate,
        feature_definition=dict(candidate["feature_definition"], max_qualifying_turns_per_speaker=2.0),
    )))
    _expect_pattern_error(lambda: validate_pattern_candidate(dict(
        candidate,
        feature_definition=dict(candidate["feature_definition"], minimum_observed_effect=float("inf")),
    )))

    content = {
        "pattern_version": "fixture-pattern-v1",
        "source_snapshot_hashes": ["A" * 64],
        "feature_schema_version": "feature-v1",
        "label_schema_version": "label-v1",
        "speaker_split_manifest_hash": "B" * 64,
        "text_only_baseline": {"macro_f1": 0.50},
        "acoustic_only_result": {"macro_f1": 0.40},
        "multimodal_result": {"macro_f1": 0.56},
        "calibration_result": {"brier": 0.18},
        "confidence_intervals": {"macro_f1_lift": [0.01, 0.11]},
        "slice_results": {},
        "known_limits": ["synthetic_fixture_only"],
        "allowed_runtime_effects": ["preserve", "soften", "clarify", "abstain"],
        "blocked_runtime_effects": sorted(REQUIRED_BLOCKED_POLICY_EFFECTS),
        "rollback_version": "text-only",
        "minimum_engine_version": "1",
        "maximum_engine_version": "1",
        "compatible_evidence_schema_versions": ["CustomerTurnEvidenceV1"],
        "compatible_state_schema_versions": ["PerceivedCustomerStateV1"],
        "registry_sequence": 1,
    }
    _expect_pattern_error(lambda: validate_pattern_content(dict(content, registry_sequence=True)))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        slice_results={"bad": float("nan")},
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        slice_results={"bad": float("inf")},
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        slice_results={"bad": (1, 2)},
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        slice_results={"bad": b"not-json"},
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        slice_results={"bad": {1, 2}},
    )))
    string_key_digest = content_digest(dict(content, slice_results={"1": "x"}))
    assert len(string_key_digest) == 64
    _expect_pattern_error(lambda: content_digest(dict(content, slice_results={1: "x"})))
    assert canonical_json_bytes({"1": "x"}) == b'{"1":"x"}'
    _expect_pattern_error(lambda: canonical_json_bytes({1: "x"}))
    candidate_digest = content_digest(content)
    shadow_report_digest = "C" * 64
    shadow = _fixture_approval("shadow_authorization", candidate_digest, [])
    runtime = _fixture_approval("runtime_activation", candidate_digest, [shadow_report_digest])
    envelope = {
        "pattern_content": content,
        "candidate_content_digest": candidate_digest,
        "shadow_authorization": shadow,
        "shadow_report_digest": shadow_report_digest,
        "runtime_activation_approval": runtime,
    }
    envelope["envelope_digest"] = envelope_digest(envelope)
    validate_envelope_integrity(envelope)
    assert candidate_digest == content_digest(json.loads(canonical_json_bytes(content)))

    tampered_content = json.loads(canonical_json_bytes(envelope))
    tampered_content["pattern_content"]["registry_sequence"] = 2
    _expect_pattern_error(lambda: validate_envelope_integrity(tampered_content))

    tampered_approval = json.loads(canonical_json_bytes(envelope))
    tampered_approval["runtime_activation_approval"]["reviewer_id"] = "forged-reviewer"
    _expect_pattern_error(lambda: validate_envelope_integrity(tampered_approval))

    unbound_runtime = _fixture_approval("runtime_activation", candidate_digest, [])
    unbound_envelope = dict(envelope, runtime_activation_approval=unbound_runtime)
    unbound_envelope["envelope_digest"] = envelope_digest(unbound_envelope)
    _expect_pattern_error(lambda: validate_envelope_integrity(unbound_envelope))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        allowed_runtime_effects=["increase_persuasion_intensity"],
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        blocked_runtime_effects=["expand_action_set"],
    )))
    _expect_pattern_error(lambda: validate_pattern_content(dict(
        content,
        source_snapshot_hashes=["a" * 64],
    )))
    expected_runtime_block = (
        "EMOTION-STATE-001 Phase A has no signature verifier, trust store, "
        "promotion ACL, or runtime activation path"
    )
    try:
        authorize_runtime(envelope)
    except RuntimeActivationBlocked as error:
        if type(error) is not RuntimeActivationBlocked:
            raise AssertionError("authorize_runtime raised a RuntimeActivationBlocked subclass") from error
        if str(error) != expected_runtime_block:
            raise AssertionError("authorize_runtime block message mismatch") from error
    except PatternContractError as error:
        raise AssertionError("authorize_runtime raised the wrong pattern contract error") from error
    else:
        raise AssertionError("authorize_runtime unexpectedly returned")
    return "pass"
