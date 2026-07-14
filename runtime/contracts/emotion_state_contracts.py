from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

TURN_EVIDENCE_FIELDS = frozenset({
    "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "event_id", "input_revision", "event_timestamp",
    "call_scoped_speaker_id", "start_time_ms", "end_time_ms", "audio_quality_status",
    "audio_quality_reasons", "acoustic_features", "acoustic_feature_confidence",
    "transcript_signals", "explicit_customer_statements", "dialogue_context_refs",
    "speaker_baseline_status", "extraction_status", "source_timestamps", "persistence_allowed",
})
TURN_AUDIT_FIELDS = frozenset({
    "ephemeral_audit_session_id", "turn_sequence", "audio_analysis_status",
    "audio_quality_bucket", "enumerated_signal_types", "abstained",
    "abstention_reason_codes", "processing_latency_ms", "evidence_policy_version",
    "runtime_approved", "contains_raw_audio", "contains_raw_transcript",
})
OPERATIONAL_AGGREGATE_FIELDS = frozenset({
    "aggregation_window", "eligible_call_count", "audio_analysis_availability_rate",
    "audio_quality_bucket_counts", "abstention_rate", "processing_latency_percentiles",
    "evidence_policy_version_counts", "contains_call_level_rows", "contains_raw_audio",
    "contains_raw_transcript", "contains_signal_labels",
})
PERCEIVED_STATE_FIELDS = frozenset({
    "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id",
    "turn_sequence", "valence_estimate", "activation_estimate", "engagement_estimate",
    "operational_signals", "confidence_by_signal", "selected_policy_signal",
    "selected_signal_confidence_bucket", "overall_evidence_quality", "trajectory",
    "evidence_refs", "signal_provenance_by_modality", "allowed_policy_effects",
    "blocked_policy_effects", "abstained", "abstention_reasons", "evidence_policy_version",
    "runtime_approved",
})
FORBIDDEN_BODY_KEYS = frozenset({
    "raw_audio", "audio_bytes", "raw_transcript", "transcript_text", "customer_name",
    "customer_phone", "customer_email", "speaker_embedding", "voiceprint", "provider_payload",
    "api_key", "secret", "hidden_reasoning",
})
FORBIDDEN_KEY_FRAGMENTS = (
    "raw_audio", "audio_bytes", "raw_transcript", "transcript_text", "speaker_embedding",
    "voiceprint", "provider_payload", "api_key", "access_token", "auth_token", "password",
    "secret", "private_key", "hidden_reasoning",
)
REFERENCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$")
EVIDENCE_REFERENCE_PATTERN = re.compile(
    r"^evidence:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
DECISION_REFERENCE_PATTERN = re.compile(
    r"^decision:uuid:[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
BASE_OPERATIONAL_SIGNALS = frozenset({
    "hesitation", "frustration", "confusion", "interest", "disengagement",
})
STATE_OPERATIONAL_SIGNALS = BASE_OPERATIONAL_SIGNALS | frozenset({
    "possible_hesitation", "possible_frustration", "possible_confusion",
    "possible_interest", "possible_disengagement", "none",
})
ALLOWED_POLICY_EFFECTS = frozenset({
    "preserve", "soften", "shorten", "clarify", "acknowledge", "handoff", "stop", "abstain",
})
REQUIRED_BLOCKED_POLICY_EFFECTS = frozenset({
    "expand_action_set", "increase_persuasion_intensity", "create_new_close",
    "override_refusal", "override_do_not_call", "rewrite_protected_text",
    "exploit_vulnerability", "voice_only_emotional_appeal", "unsupported_claim",
    "automatic_close_or_payment",
})
AUDIO_QUALITY_STATUSES = frozenset({"usable", "degraded", "unusable", "unavailable"})
AUDIO_QUALITY_REASON_CODES = frozenset({
    "phase_a_no_audio", "low_signal", "clipping", "noise", "too_short",
    "missing_audio", "unsupported_format", "contradictory_evidence",
})
EXTRACTION_STATUSES = frozenset({"offline_fixture_only", "complete", "partial", "abstained", "failed", "unavailable"})
SPEAKER_BASELINE_STATUSES = frozenset({"not_started", "collecting", "available", "unusable"})
ABSTENTION_REASON_CODES = frozenset({
    "phase_a_no_audio", "insufficient_evidence", "contradictory_evidence",
    "low_audio_quality", "missing_input", "stale_input",
})
EVIDENCE_QUALITY_VALUES = frozenset({"text_only", "acoustic_only", "multimodal", "insufficient", "low_quality"})
TRAJECTORY_VALUES = frozenset({"stable", "improving", "worsening", "insufficient_history", "contradictory"})
AGGREGATION_WINDOW_FIELDS = frozenset({"window_start_date", "window_end_date", "timezone"})
EVIDENCE_POLICY_VERSION_PATTERN = re.compile(r"^emotion-state-evidence-v[1-9][0-9]*$")
CANONICAL_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
EXPLICIT_STATEMENT_FIELDS = frozenset({
    "evidence_class", "redacted_reference_id", "operational_signal",
})


class EmotionStateContractError(ValueError):
    pass


@dataclass(frozen=True)
class EventWatermarkV1:
    expected_session_id: str
    expected_campaign_profile_id: str
    expected_campaign_profile_version: str
    last_turn_sequence: int
    turn_sequence_by_id: tuple[tuple[str, int], ...]
    turn_id_by_sequence: tuple[tuple[int, str], ...]
    last_input_revision_by_turn: tuple[tuple[str, int], ...]
    seen_event_ids: frozenset[str]
    event_history_by_id: tuple[tuple[str, str, int], ...] = ()


def _find_forbidden_paths(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            child_path = f"{path}.{key}"
            if normalized in FORBIDDEN_BODY_KEYS or any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
                found.append(child_path)
            found.extend(_find_forbidden_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_forbidden_paths(child, f"{path}[{index}]"))
    return found


def _key_is_forbidden(key: Any) -> bool:
    normalized = str(key).lower()
    return normalized in FORBIDDEN_BODY_KEYS or any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS)


def _require_fields(payload: dict[str, Any], required: frozenset[str], contract: str) -> None:
    if not isinstance(payload, dict):
        raise EmotionStateContractError(f"{contract} must be an object")
    missing = sorted(required - set(payload))
    if missing:
        raise EmotionStateContractError(f"{contract} missing fields: {missing}")
    forbidden: list[str] = []
    for key, value in payload.items():
        if key not in required and _key_is_forbidden(key):
            forbidden.append(f"$.{key}")
        forbidden.extend(_find_forbidden_paths(value, f"$.{key}"))
    if forbidden:
        raise EmotionStateContractError(f"{contract} contains forbidden fields: {forbidden}")
    unknown = sorted(set(payload) - required)
    if unknown:
        raise EmotionStateContractError(f"{contract} unknown fields: {unknown}")


def validate_opaque_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or REFERENCE_ID_PATTERN.fullmatch(value) is None:
        raise EmotionStateContractError(f"{field} must be a bounded opaque reference, not free text")


def validate_evidence_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or EVIDENCE_REFERENCE_PATTERN.fullmatch(value) is None:
        raise EmotionStateContractError(
            f"{field} must be a typed content-independent evidence UUID, not transcript text"
        )


def validate_decision_reference(value: Any, field: str) -> None:
    if not isinstance(value, str) or DECISION_REFERENCE_PATTERN.fullmatch(value) is None:
        raise EmotionStateContractError(
            f"{field} must be a typed content-independent decision UUID, not free text"
        )


def _validate_event_watermark(
    watermark: EventWatermarkV1,
) -> tuple[dict[str, int], dict[int, str], dict[str, int], dict[str, tuple[str, int]]]:
    if not isinstance(watermark, EventWatermarkV1):
        raise EmotionStateContractError("event watermark type is invalid")
    for field, value in (
        ("expected_session_id", watermark.expected_session_id),
        ("expected_campaign_profile_id", watermark.expected_campaign_profile_id),
        ("expected_campaign_profile_version", watermark.expected_campaign_profile_version),
    ):
        validate_opaque_reference(value, f"watermark.{field}")
    if type(watermark.last_turn_sequence) is not int or watermark.last_turn_sequence < -1:
        raise EmotionStateContractError("event watermark last_turn_sequence is invalid")
    tuple_fields = (
        watermark.turn_sequence_by_id,
        watermark.turn_id_by_sequence,
        watermark.last_input_revision_by_turn,
    )
    if (
        any(type(value) is not tuple for value in tuple_fields)
        or type(watermark.seen_event_ids) is not frozenset
        or type(watermark.event_history_by_id) is not tuple
    ):
        raise EmotionStateContractError("event watermark collections must be immutable")
    if any(type(pair) is not tuple or len(pair) != 2 for value in tuple_fields for pair in value):
        raise EmotionStateContractError("event watermark entries are invalid")
    if any(type(entry) is not tuple or len(entry) != 3 for entry in watermark.event_history_by_id):
        raise EmotionStateContractError("event watermark history entries are invalid")
    sequence_by_id = dict(watermark.turn_sequence_by_id)
    id_by_sequence = dict(watermark.turn_id_by_sequence)
    revision_by_turn = dict(watermark.last_input_revision_by_turn)
    if any(len(mapping) != len(source) for mapping, source in (
        (sequence_by_id, watermark.turn_sequence_by_id),
        (id_by_sequence, watermark.turn_id_by_sequence),
        (revision_by_turn, watermark.last_input_revision_by_turn),
    )):
        raise EmotionStateContractError("event watermark contains duplicate map keys")
    for turn_id, sequence in sequence_by_id.items():
        validate_opaque_reference(turn_id, "watermark.turn_id")
        if type(sequence) is not int or sequence < 0:
            raise EmotionStateContractError("event watermark turn sequence is invalid")
    for sequence, turn_id in id_by_sequence.items():
        if type(sequence) is not int or sequence < 0:
            raise EmotionStateContractError("event watermark reverse turn sequence is invalid")
        validate_opaque_reference(turn_id, "watermark.reverse_turn_id")
    for turn_id, revision in revision_by_turn.items():
        validate_opaque_reference(turn_id, "watermark.revision_turn_id")
        if type(revision) is not int or revision < 0:
            raise EmotionStateContractError("event watermark revision is invalid")
    for event_id in watermark.seen_event_ids:
        validate_opaque_reference(event_id, "watermark.seen_event_id")
    event_history_by_id: dict[str, tuple[str, int]] = {}
    turn_revision_history: set[tuple[str, int]] = set()
    revisions_by_turn: dict[str, list[int]] = {}
    for event_id, turn_id, revision in watermark.event_history_by_id:
        validate_opaque_reference(event_id, "watermark.history_event_id")
        validate_opaque_reference(turn_id, "watermark.history_turn_id")
        if type(revision) is not int or revision < 0:
            raise EmotionStateContractError("event watermark history revision is invalid")
        if event_id in event_history_by_id:
            raise EmotionStateContractError("event watermark history contains duplicate event IDs")
        if (turn_id, revision) in turn_revision_history:
            raise EmotionStateContractError("event watermark history contains duplicate turn revisions")
        event_history_by_id[event_id] = (turn_id, revision)
        turn_revision_history.add((turn_id, revision))
        revisions_by_turn.setdefault(turn_id, []).append(revision)
    if {sequence: turn_id for turn_id, sequence in sequence_by_id.items()} != id_by_sequence:
        raise EmotionStateContractError("event watermark turn maps are inconsistent")
    if set(revision_by_turn) != set(sequence_by_id):
        raise EmotionStateContractError("event watermark revision map is inconsistent")
    if frozenset(event_history_by_id) != watermark.seen_event_ids:
        raise EmotionStateContractError("event watermark seen events and history are inconsistent")
    if set(revisions_by_turn) != set(sequence_by_id):
        raise EmotionStateContractError("event watermark history turn coverage is inconsistent")
    for turn_id, last_revision in revision_by_turn.items():
        revisions = sorted(revisions_by_turn[turn_id])
        if len(revisions) != last_revision + 1 or revisions != list(range(len(revisions))):
            raise EmotionStateContractError("event watermark revision history is inconsistent")
    expected_last_sequence = max(id_by_sequence, default=-1)
    if watermark.last_turn_sequence != expected_last_sequence:
        raise EmotionStateContractError("event watermark last_turn_sequence is inconsistent")
    return sequence_by_id, id_by_sequence, revision_by_turn, event_history_by_id


def _require_reference_list(value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise EmotionStateContractError(f"{field} must contain typed evidence UUID references, not free text")
    for reference in value:
        validate_evidence_reference(reference, field)
    if len(value) != len(set(value)):
        raise EmotionStateContractError(f"{field} must contain unique references")


def _require_enum_list(value: Any, allowed: frozenset[str], field: str) -> None:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) or item not in allowed for item in value)
        or len(value) != len(set(value))
    ):
        raise EmotionStateContractError(f"{field} contains an unknown value")


def _require_enum_value(value: Any, allowed: set[str] | frozenset[str], field: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise EmotionStateContractError(f"{field} is invalid")


def _is_finite_scalar(value: Any) -> bool:
    if type(value) not in {int, float}:
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _require_numeric_map(value: Any, field: str, *, minimum: float | None = None, maximum: float | None = None) -> None:
    if not isinstance(value, dict):
        raise EmotionStateContractError(f"{field} must be an object of scalar values")
    for key, number in value.items():
        validate_opaque_reference(key, f"{field} key")
        if not _is_finite_scalar(number):
            raise EmotionStateContractError(f"{field}.{key} must be a finite scalar")
        if minimum is not None and number < minimum:
            raise EmotionStateContractError(f"{field}.{key} is below its minimum")
        if maximum is not None and number > maximum:
            raise EmotionStateContractError(f"{field}.{key} is above its maximum")


def _require_rate(value: Any, field: str) -> None:
    if not _is_finite_scalar(value) or not 0.0 <= value <= 1.0:
        raise EmotionStateContractError(f"{field} must be a finite rate in [0, 1]")


def _require_count_map(value: Any, field: str, *, expected_total: int) -> None:
    if not isinstance(value, dict) or not value:
        raise EmotionStateContractError(f"{field} must be a nonempty count object")
    total = 0
    for key, count in value.items():
        validate_opaque_reference(key, f"{field} key")
        if type(count) is not int or count < 0:
            raise EmotionStateContractError(f"{field}.{key} must be a nonnegative integer")
        total += count
    if total != expected_total:
        raise EmotionStateContractError(f"{field} must sum to eligible_call_count")


def _validate_aggregation_window(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != AGGREGATION_WINDOW_FIELDS:
        raise EmotionStateContractError("aggregation_window fields mismatch")
    if value["timezone"] != "UTC":
        raise EmotionStateContractError("aggregation_window timezone must be UTC")
    if any(
        not isinstance(value[field], str) or CANONICAL_DATE_PATTERN.fullmatch(value[field]) is None
        for field in ("window_start_date", "window_end_date")
    ):
        raise EmotionStateContractError("aggregation_window dates must use canonical YYYY-MM-DD")
    try:
        start = date.fromisoformat(value["window_start_date"])
        end = date.fromisoformat(value["window_end_date"])
    except (TypeError, ValueError) as exc:
        raise EmotionStateContractError("aggregation_window dates must use YYYY-MM-DD") from exc
    if end < start:
        raise EmotionStateContractError("aggregation_window end precedes start")


def _validate_explicit_statements(value: Any) -> None:
    if not isinstance(value, list):
        raise EmotionStateContractError("explicit_customer_statements must be a list")
    for statement in value:
        if not isinstance(statement, dict) or set(statement) != EXPLICIT_STATEMENT_FIELDS:
            raise EmotionStateContractError("explicit statement fields mismatch")
        if statement["evidence_class"] != "direct_explicit":
            raise EmotionStateContractError("explicit statement evidence class mismatch")
        if statement["operational_signal"] not in BASE_OPERATIONAL_SIGNALS:
            raise EmotionStateContractError("explicit statement signal is invalid")
        _require_reference_list([statement["redacted_reference_id"]], "redacted_reference_id")


def _require_false(payload: dict[str, Any], fields: tuple[str, ...], contract: str) -> None:
    for field in fields:
        if payload.get(field) is not False:
            raise EmotionStateContractError(f"{contract}.{field} must be false")


def validate_customer_turn_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, TURN_EVIDENCE_FIELDS, "CustomerTurnEvidenceV1")
    _require_false(payload, ("persistence_allowed",), "CustomerTurnEvidenceV1")
    if type(payload["turn_sequence"]) is not int or payload["turn_sequence"] < 0:
        raise EmotionStateContractError("turn_sequence must be a nonnegative integer")
    if type(payload["input_revision"]) is not int or payload["input_revision"] < 0:
        raise EmotionStateContractError("input_revision must be a nonnegative integer")
    for field in (
        "call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id", "event_id",
        "call_scoped_speaker_id", "audio_quality_status", "speaker_baseline_status", "extraction_status",
    ):
        validate_opaque_reference(payload[field], field)
    if not payload["call_scoped_speaker_id"].startswith(f"{payload['call_session_id']}:"):
        raise EmotionStateContractError("call_scoped_speaker_id must be bound to the current call session")
    if type(payload["start_time_ms"]) is not int or type(payload["end_time_ms"]) is not int:
        raise EmotionStateContractError("turn timestamps must be integers")
    if payload["start_time_ms"] < 0 or payload["end_time_ms"] <= payload["start_time_ms"]:
        raise EmotionStateContractError("turn timestamp range is invalid")
    try:
        event_timestamp = datetime.fromisoformat(payload["event_timestamp"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise EmotionStateContractError("event_timestamp must be ISO-8601") from exc
    if event_timestamp.tzinfo is None:
        raise EmotionStateContractError("event_timestamp must include a timezone")
    if payload["audio_quality_status"] not in AUDIO_QUALITY_STATUSES:
        raise EmotionStateContractError("audio_quality_status is invalid")
    _require_enum_list(payload["audio_quality_reasons"], AUDIO_QUALITY_REASON_CODES, "audio_quality_reasons")
    if payload["speaker_baseline_status"] not in SPEAKER_BASELINE_STATUSES:
        raise EmotionStateContractError("speaker_baseline_status is invalid")
    if payload["extraction_status"] not in EXTRACTION_STATUSES:
        raise EmotionStateContractError("extraction_status is invalid")
    _require_numeric_map(payload["acoustic_features"], "acoustic_features")
    _require_numeric_map(payload["acoustic_feature_confidence"], "acoustic_feature_confidence", minimum=0.0, maximum=1.0)
    _require_numeric_map(payload["source_timestamps"], "source_timestamps", minimum=0.0)
    _require_enum_list(payload["transcript_signals"], STATE_OPERATIONAL_SIGNALS, "transcript_signals")
    _validate_explicit_statements(payload["explicit_customer_statements"])
    _require_reference_list(payload["dialogue_context_refs"], "dialogue_context_refs")
    return payload


def validate_customer_turn_audit(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, TURN_AUDIT_FIELDS, "CustomerTurnAuditV1")
    unknown = sorted(set(payload) - TURN_AUDIT_FIELDS)
    if unknown:
        raise EmotionStateContractError(f"CustomerTurnAuditV1 unknown fields: {unknown}")
    _require_false(payload, ("runtime_approved", "contains_raw_audio", "contains_raw_transcript"), "CustomerTurnAuditV1")
    validate_opaque_reference(payload["ephemeral_audit_session_id"], "ephemeral_audit_session_id")
    validate_opaque_reference(payload["evidence_policy_version"], "evidence_policy_version")
    if EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(payload["evidence_policy_version"]) is None:
        raise EmotionStateContractError("audit evidence_policy_version is invalid")
    if type(payload["turn_sequence"]) is not int or payload["turn_sequence"] < 0:
        raise EmotionStateContractError("audit turn_sequence must be a nonnegative integer")
    _require_enum_value(
        payload["audio_analysis_status"],
        {"unavailable", "complete", "partial", "failed", "abstained"},
        "audio_analysis_status",
    )
    if payload["audio_quality_bucket"] not in AUDIO_QUALITY_STATUSES:
        raise EmotionStateContractError("audio_quality_bucket is invalid")
    _require_enum_list(payload["enumerated_signal_types"], STATE_OPERATIONAL_SIGNALS, "enumerated_signal_types")
    _require_enum_list(payload["abstention_reason_codes"], ABSTENTION_REASON_CODES, "abstention_reason_codes")
    if type(payload["abstained"]) is not bool:
        raise EmotionStateContractError("abstained must be boolean")
    if payload["abstained"] != bool(payload["abstention_reason_codes"]):
        raise EmotionStateContractError("audit abstention flag and reasons are inconsistent")
    if type(payload["processing_latency_ms"]) is not int or payload["processing_latency_ms"] < 0:
        raise EmotionStateContractError("processing_latency_ms must be a nonnegative integer")
    return payload


def validate_operational_aggregate(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, OPERATIONAL_AGGREGATE_FIELDS, "OperationalAggregateV1")
    unknown = sorted(set(payload) - OPERATIONAL_AGGREGATE_FIELDS)
    if unknown:
        raise EmotionStateContractError(f"OperationalAggregateV1 unknown fields: {unknown}")
    if type(payload["eligible_call_count"]) is not int or payload["eligible_call_count"] < 10:
        raise EmotionStateContractError("OperationalAggregateV1 requires at least ten eligible calls")
    _require_false(
        payload,
        ("contains_call_level_rows", "contains_raw_audio", "contains_raw_transcript", "contains_signal_labels"),
        "OperationalAggregateV1",
    )
    _validate_aggregation_window(payload["aggregation_window"])
    _require_rate(payload["audio_analysis_availability_rate"], "audio_analysis_availability_rate")
    _require_rate(payload["abstention_rate"], "abstention_rate")
    quality_counts = payload["audio_quality_bucket_counts"]
    if not isinstance(quality_counts, dict) or set(quality_counts) - AUDIO_QUALITY_STATUSES:
        raise EmotionStateContractError("audio_quality_bucket_counts contains an unknown cohort bucket")
    _require_count_map(quality_counts, "audio_quality_bucket_counts", expected_total=payload["eligible_call_count"])
    percentiles = payload["processing_latency_percentiles"]
    if not isinstance(percentiles, dict) or set(percentiles) != {"p50", "p95"}:
        raise EmotionStateContractError("processing_latency_percentiles must contain p50 and p95 only")
    _require_numeric_map(percentiles, "processing_latency_percentiles", minimum=0.0)
    if percentiles["p95"] < percentiles["p50"]:
        raise EmotionStateContractError("processing latency percentiles are non-monotonic")
    policy_counts = payload["evidence_policy_version_counts"]
    if not isinstance(policy_counts, dict) or any(
        not isinstance(version, str) or EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(version) is None
        for version in policy_counts
    ):
        raise EmotionStateContractError("evidence_policy_version_counts contains a non-version identifier")
    _require_count_map(
        policy_counts,
        "evidence_policy_version_counts",
        expected_total=payload["eligible_call_count"],
    )
    return payload


def validate_perceived_customer_state(payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(payload, PERCEIVED_STATE_FIELDS, "PerceivedCustomerStateV1")
    _require_false(payload, ("runtime_approved",), "PerceivedCustomerStateV1")
    for field in ("call_session_id", "campaign_profile_id", "campaign_profile_version", "turn_id", "evidence_policy_version"):
        validate_opaque_reference(payload[field], field)
    if EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(payload["evidence_policy_version"]) is None:
        raise EmotionStateContractError("state evidence_policy_version is invalid")
    if type(payload["turn_sequence"]) is not int or payload["turn_sequence"] < 0:
        raise EmotionStateContractError("state turn_sequence must be a nonnegative integer")
    if payload["valence_estimate"] != "not_inferable" and (
        type(payload["valence_estimate"]) is not int or payload["valence_estimate"] not in {-2, -1, 0, 1, 2}
    ):
        raise EmotionStateContractError("valence_estimate is invalid")
    for field in ("activation_estimate", "engagement_estimate"):
        if payload[field] != "not_inferable" and (
            type(payload[field]) is not int or payload[field] not in {1, 2, 3, 4, 5}
        ):
            raise EmotionStateContractError(f"{field} is invalid")
    if payload["selected_signal_confidence_bucket"] not in {"low", "medium", "high"}:
        raise EmotionStateContractError("invalid selected_signal_confidence_bucket")
    _require_enum_list(payload["operational_signals"], STATE_OPERATIONAL_SIGNALS, "operational_signals")
    if "none" in payload["operational_signals"] and payload["operational_signals"] != ["none"]:
        raise EmotionStateContractError("none cannot coexist with operational signals")
    _require_numeric_map(payload["confidence_by_signal"], "confidence_by_signal", minimum=0.0, maximum=1.0)
    signal_keys = set(payload["operational_signals"]) - {"none"}
    if set(payload["confidence_by_signal"]) != signal_keys:
        raise EmotionStateContractError("confidence_by_signal must match operational_signals")
    if payload["selected_policy_signal"] not in STATE_OPERATIONAL_SIGNALS:
        raise EmotionStateContractError("selected_policy_signal is invalid")
    _require_enum_value(payload["overall_evidence_quality"], EVIDENCE_QUALITY_VALUES, "overall_evidence_quality")
    if payload["trajectory"] not in TRAJECTORY_VALUES:
        raise EmotionStateContractError("trajectory is invalid")
    _require_enum_list(payload["allowed_policy_effects"], ALLOWED_POLICY_EFFECTS, "allowed_policy_effects")
    _require_enum_list(payload["blocked_policy_effects"], REQUIRED_BLOCKED_POLICY_EFFECTS, "blocked_policy_effects")
    if set(payload["blocked_policy_effects"]) != REQUIRED_BLOCKED_POLICY_EFFECTS:
        raise EmotionStateContractError("blocked_policy_effects must contain every monotonic safety block")
    _require_reference_list(payload["evidence_refs"], "evidence_refs")
    if len(payload["evidence_refs"]) != len(set(payload["evidence_refs"])):
        raise EmotionStateContractError("evidence_refs must be unique")
    provenance = payload["signal_provenance_by_modality"]
    if not isinstance(provenance, dict) or set(provenance) != signal_keys:
        raise EmotionStateContractError("modality provenance must cover every operational signal")
    provenance_ref_union: set[str] = set()
    nonempty_modalities: set[str] = set()
    for signal, modality_refs in provenance.items():
        if not isinstance(modality_refs, dict) or not set(modality_refs).issubset({"text", "acoustic", "dialogue"}):
            raise EmotionStateContractError(f"invalid modality provenance for {signal}")
        signal_ref_union: set[str] = set()
        for modality, references in modality_refs.items():
            _require_reference_list(references, f"signal_provenance_by_modality.{signal}.{modality}")
            if references:
                nonempty_modalities.add(modality)
            signal_ref_union.update(references)
        if not signal_ref_union:
            raise EmotionStateContractError(f"signal {signal} has no evidence provenance")
        provenance_ref_union.update(signal_ref_union)
    if provenance_ref_union != set(payload["evidence_refs"]):
        raise EmotionStateContractError("evidence_refs must equal the signal provenance reference union")
    evidence_quality = payload["overall_evidence_quality"]
    if evidence_quality == "text_only" and nonempty_modalities != {"text"}:
        raise EmotionStateContractError("text_only evidence quality requires text-only provenance")
    if evidence_quality == "acoustic_only" and nonempty_modalities != {"acoustic"}:
        raise EmotionStateContractError("acoustic_only evidence quality requires acoustic-only provenance")
    if evidence_quality == "multimodal" and len(nonempty_modalities) < 2:
        raise EmotionStateContractError("multimodal evidence quality requires multiple modalities")
    _require_enum_list(payload["abstention_reasons"], ABSTENTION_REASON_CODES, "abstention_reasons")
    if type(payload["abstained"]) is not bool:
        raise EmotionStateContractError("abstained must be boolean")
    if payload["abstained"]:
        if not payload["abstention_reasons"] or payload["selected_policy_signal"] != "none":
            raise EmotionStateContractError("abstained state must select none and provide a reason")
        if payload["allowed_policy_effects"] != ["preserve"]:
            raise EmotionStateContractError("abstained acoustic state must preserve the text-only policy without a delta")
    else:
        if payload["abstention_reasons"]:
            raise EmotionStateContractError("non-abstained state cannot carry abstention reasons")
        if payload["selected_policy_signal"] not in signal_keys:
            raise EmotionStateContractError("selected policy signal lacks state evidence")
    return payload


def validate_event_identity(
    payload: dict[str, Any],
    *,
    watermark: EventWatermarkV1,
) -> EventWatermarkV1:
    validate_customer_turn_evidence(payload)
    sequence_by_id, id_by_sequence, revision_by_turn, event_history_by_id = _validate_event_watermark(watermark)
    if payload["call_session_id"] != watermark.expected_session_id:
        raise EmotionStateContractError("cross-session event")
    if payload["campaign_profile_id"] != watermark.expected_campaign_profile_id:
        raise EmotionStateContractError("cross-campaign event")
    if payload["campaign_profile_version"] != watermark.expected_campaign_profile_version:
        raise EmotionStateContractError("stale or wrong campaign profile version")
    if payload["event_id"] in watermark.seen_event_ids:
        raise EmotionStateContractError("duplicate event")
    turn_sequence = payload["turn_sequence"]
    turn_id = payload["turn_id"]
    input_revision = payload["input_revision"]
    if turn_id in sequence_by_id and sequence_by_id[turn_id] != turn_sequence:
        raise EmotionStateContractError("turn_id rebound to another sequence")
    if turn_sequence in id_by_sequence and id_by_sequence[turn_sequence] != turn_id:
        raise EmotionStateContractError("turn_sequence rebound to another turn_id")
    if turn_sequence < watermark.last_turn_sequence:
        raise EmotionStateContractError("stale or non-monotonic turn")
    if turn_id in sequence_by_id:
        if turn_sequence != watermark.last_turn_sequence:
            raise EmotionStateContractError("correction targets a closed turn")
        if input_revision != revision_by_turn[turn_id] + 1:
            raise EmotionStateContractError("correction input revision must increment by exactly one")
    else:
        if turn_sequence <= watermark.last_turn_sequence:
            raise EmotionStateContractError("new turn is not monotonic")
        if input_revision != 0:
            raise EmotionStateContractError("new turn must begin at input revision zero")
        sequence_by_id[turn_id] = turn_sequence
        id_by_sequence[turn_sequence] = turn_id
    revision_by_turn[turn_id] = input_revision
    event_history_by_id[payload["event_id"]] = (turn_id, input_revision)
    return EventWatermarkV1(
        expected_session_id=watermark.expected_session_id,
        expected_campaign_profile_id=watermark.expected_campaign_profile_id,
        expected_campaign_profile_version=watermark.expected_campaign_profile_version,
        last_turn_sequence=max(watermark.last_turn_sequence, turn_sequence),
        turn_sequence_by_id=tuple(sorted(sequence_by_id.items())),
        turn_id_by_sequence=tuple(sorted(id_by_sequence.items())),
        last_input_revision_by_turn=tuple(sorted(revision_by_turn.items())),
        seen_event_ids=frozenset(event_history_by_id),
        event_history_by_id=tuple(sorted(
            (event_id, identity[0], identity[1])
            for event_id, identity in event_history_by_id.items()
        )),
    )


def serialize_default_live_record(contract_name: str, payload: dict[str, Any]) -> str:
    if contract_name != "OperationalAggregateV1":
        raise EmotionStateContractError(f"{contract_name} is not default-persistable")
    validate_operational_aggregate(payload)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))

def _expect_contract_error(callback: Any) -> None:
    try:
        callback()
    except EmotionStateContractError:
        return
    raise AssertionError("expected EmotionStateContractError")


def _expect_named_contract_errors(cases: tuple[tuple[str, Any], ...]) -> None:
    failures: list[str] = []
    for name, callback in cases:
        try:
            callback()
        except EmotionStateContractError:
            continue
        except Exception as exc:
            failures.append(f"{name}: raised {type(exc).__name__}, not EmotionStateContractError")
        else:
            failures.append(f"{name}: accepted")
    if failures:
        raise AssertionError("; ".join(failures))


def _expect_named_contract_successes(cases: tuple[tuple[str, Any], ...]) -> None:
    failures: list[str] = []
    for name, callback in cases:
        try:
            callback()
        except Exception as exc:
            failures.append(f"{name}: raised {type(exc).__name__}")
    if failures:
        raise AssertionError("; ".join(failures))


def _require_rejected_or_revalidatable_event(
    payload: dict[str, Any],
    *,
    watermark: EventWatermarkV1,
) -> None:
    try:
        returned_watermark = validate_event_identity(payload, watermark=watermark)
    except EmotionStateContractError:
        return
    _validate_event_watermark(returned_watermark)


def contract_self_check() -> str:
    evidence = {
        "call_session_id": "session-fixture-1",
        "campaign_profile_id": "emotion-state-phase-a-fixture",
        "campaign_profile_version": "fixture-v1",
        "turn_id": "turn-1",
        "turn_sequence": 1,
        "event_id": "event-1",
        "input_revision": 0,
        "event_timestamp": "2026-07-14T00:00:00Z",
        "call_scoped_speaker_id": "session-fixture-1:speaker-1",
        "start_time_ms": 0,
        "end_time_ms": 1000,
        "audio_quality_status": "unavailable",
        "audio_quality_reasons": ["phase_a_no_audio"],
        "acoustic_features": {},
        "acoustic_feature_confidence": {},
        "transcript_signals": ["possible_confusion"],
        "explicit_customer_statements": [{
            "evidence_class": "direct_explicit",
            "redacted_reference_id": "evidence:uuid:22222222-2222-4222-8222-222222222222",
            "operational_signal": "confusion",
        }],
        "dialogue_context_refs": ["evidence:uuid:11111111-1111-4111-8111-111111111111"],
        "speaker_baseline_status": "not_started",
        "extraction_status": "offline_fixture_only",
        "source_timestamps": {},
        "persistence_allowed": False,
    }
    audit = {
        "ephemeral_audit_session_id": "audit-fixture-1",
        "turn_sequence": 1,
        "audio_analysis_status": "unavailable",
        "audio_quality_bucket": "unavailable",
        "enumerated_signal_types": ["possible_confusion"],
        "abstained": True,
        "abstention_reason_codes": ["phase_a_no_audio"],
        "processing_latency_ms": 0,
        "evidence_policy_version": "emotion-state-evidence-v1",
        "runtime_approved": False,
        "contains_raw_audio": False,
        "contains_raw_transcript": False,
    }
    aggregate = {
        "aggregation_window": {
            "window_start_date": "2026-07-01",
            "window_end_date": "2026-07-14",
            "timezone": "UTC",
        },
        "eligible_call_count": 10,
        "audio_analysis_availability_rate": 0.0,
        "audio_quality_bucket_counts": {"unavailable": 10},
        "abstention_rate": 1.0,
        "processing_latency_percentiles": {"p50": 0, "p95": 0},
        "evidence_policy_version_counts": {"emotion-state-evidence-v1": 10},
        "contains_call_level_rows": False,
        "contains_raw_audio": False,
        "contains_raw_transcript": False,
        "contains_signal_labels": False,
    }
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
        "blocked_policy_effects": [
            "expand_action_set", "increase_persuasion_intensity", "create_new_close",
            "override_refusal", "override_do_not_call", "rewrite_protected_text",
            "exploit_vulnerability", "voice_only_emotional_appeal", "unsupported_claim",
            "automatic_close_or_payment",
        ],
        "abstained": False,
        "abstention_reasons": [],
        "evidence_policy_version": "emotion-state-evidence-v1",
        "runtime_approved": False,
    }
    validate_customer_turn_evidence(evidence)
    validate_customer_turn_audit(audit)
    validate_operational_aggregate(aggregate)
    validate_perceived_customer_state(state)
    abstained_state = dict(
        state,
        valence_estimate="not_inferable",
        activation_estimate="not_inferable",
        engagement_estimate="not_inferable",
        operational_signals=["none"],
        confidence_by_signal={},
        selected_policy_signal="none",
        selected_signal_confidence_bucket="low",
        overall_evidence_quality="insufficient",
        evidence_refs=[],
        signal_provenance_by_modality={},
        allowed_policy_effects=["preserve"],
        abstained=True,
        abstention_reasons=["insufficient_evidence"],
    )
    validate_perceived_customer_state(abstained_state)
    initial_watermark = EventWatermarkV1(
        expected_session_id="session-fixture-1",
        expected_campaign_profile_id="emotion-state-phase-a-fixture",
        expected_campaign_profile_version="fixture-v1",
        last_turn_sequence=-1,
        turn_sequence_by_id=(),
        turn_id_by_sequence=(),
        last_input_revision_by_turn=(),
        seen_event_ids=frozenset(),
    )
    first_watermark = validate_event_identity(evidence, watermark=initial_watermark)
    corrected = dict(evidence, event_id="event-2", input_revision=1)
    corrected_watermark = validate_event_identity(corrected, watermark=first_watermark)
    second_correction = dict(evidence, event_id="event-3", input_revision=2)
    second_corrected_watermark = validate_event_identity(second_correction, watermark=corrected_watermark)
    _validate_event_watermark(first_watermark)
    _validate_event_watermark(corrected_watermark)
    _validate_event_watermark(second_corrected_watermark)
    assert initial_watermark.turn_sequence_by_id == ()
    assert corrected_watermark.last_input_revision_by_turn == (("turn-1", 1),)
    assert second_corrected_watermark.last_input_revision_by_turn == (("turn-1", 2),)
    assert json.loads(serialize_default_live_record("OperationalAggregateV1", aggregate)) == aggregate
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, raw_transcript="blocked")))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, acoustic_features={"provider_payload": {}})))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, dialogue_context_refs=["raw transcript sentence"])))
    for transcript_like_reference in (
        "I-am-confused-about-price",
        "I_am_confused_about_price",
        "I%20am%20confused",
        "Ich-bin-verwirrt-wegen-des-Preises",
    ):
        _expect_contract_error(lambda reference=transcript_like_reference: validate_customer_turn_evidence(dict(
            evidence,
            dialogue_context_refs=[reference],
        )))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, event_timestamp="2026-07-14T00:00:00")))
    _expect_contract_error(lambda: validate_customer_turn_evidence(dict(evidence, call_scoped_speaker_id="reusable-speaker-1")))
    _expect_contract_error(lambda: validate_customer_turn_audit(dict(audit, reviewer_notes="blocked")))
    _expect_contract_error(lambda: validate_customer_turn_audit(dict(audit, enumerated_signal_types=["raw transcript sentence"])))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(aggregate, eligible_call_count=9)))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(aggregate, eligible_unique_speaker_count=10)))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(
        aggregate,
        audio_quality_bucket_counts={"call-fixture-1": 10},
    )))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(
        aggregate,
        aggregation_window="session-fixture-1",
    )))
    _expect_contract_error(lambda: validate_operational_aggregate(dict(
        aggregate,
        evidence_policy_version_counts={"call-fixture-1": 10},
    )))
    _expect_contract_error(lambda: serialize_default_live_record("CustomerTurnEvidenceV1", evidence))
    _expect_contract_error(lambda: validate_event_identity(evidence, watermark=first_watermark))
    _expect_contract_error(lambda: validate_event_identity(
        dict(
            evidence,
            event_id="event-cross-session",
            call_session_id="another-session",
            call_scoped_speaker_id="another-session:speaker-1",
        ),
        watermark=initial_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-stale-revision"),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-wrong-campaign", campaign_profile_version="fixture-v2"),
        watermark=initial_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-stale-turn", turn_id="turn-stale", turn_sequence=0),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-sequence-rebound", turn_id="turn-2"),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        dict(evidence, event_id="event-id-rebound", turn_sequence=2),
        watermark=first_watermark,
    ))
    _expect_contract_error(lambda: validate_event_identity(
        evidence,
        watermark=EventWatermarkV1(
            expected_session_id="session-fixture-1",
            expected_campaign_profile_id="emotion-state-phase-a-fixture",
            expected_campaign_profile_version="fixture-v1",
            last_turn_sequence=0,
            turn_sequence_by_id=(),
            turn_id_by_sequence=(),
            last_input_revision_by_turn=(),
            seen_event_ids=frozenset(),
        ),
    ))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(state, runtime_approved=True)))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(
        state,
        operational_signals=["possible_confusion", "none"],
    )))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(state, abstained=True)))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(
        abstained_state,
        allowed_policy_effects=["preserve", "soften"],
    )))
    _expect_contract_error(lambda: validate_perceived_customer_state(dict(
        state,
        blocked_policy_effects=["expand_action_set"],
    )))
    watermark_history_without_events = EventWatermarkV1(
        expected_session_id="session-fixture-1",
        expected_campaign_profile_id="emotion-state-phase-a-fixture",
        expected_campaign_profile_version="fixture-v1",
        last_turn_sequence=1,
        turn_sequence_by_id=(("turn-1", 1),),
        turn_id_by_sequence=((1, "turn-1"),),
        last_input_revision_by_turn=(("turn-1", 0),),
        seen_event_ids=frozenset(),
        event_history_by_id=(("event-1", "turn-1", 0),),
    )
    watermark_events_without_history = EventWatermarkV1(
        expected_session_id="session-fixture-1",
        expected_campaign_profile_id="emotion-state-phase-a-fixture",
        expected_campaign_profile_version="fixture-v1",
        last_turn_sequence=-1,
        turn_sequence_by_id=(),
        turn_id_by_sequence=(),
        last_input_revision_by_turn=(),
        seen_event_ids=frozenset({"event-1"}),
        event_history_by_id=(("event-1", "turn-ghost", 0),),
    )
    watermark_same_cardinality_substitution = EventWatermarkV1(
        expected_session_id="session-fixture-1",
        expected_campaign_profile_id="emotion-state-phase-a-fixture",
        expected_campaign_profile_version="fixture-v1",
        last_turn_sequence=1,
        turn_sequence_by_id=(("turn-1", 1),),
        turn_id_by_sequence=((1, "turn-1"),),
        last_input_revision_by_turn=(("turn-1", 0),),
        seen_event_ids=frozenset({"substituted-event-1"}),
        event_history_by_id=(("event-1", "turn-1", 0),),
    )
    acoustic_only_reference = "evidence:uuid:33333333-3333-4333-8333-333333333333"
    text_only_with_acoustic_only_provenance = dict(
        state,
        evidence_refs=[acoustic_only_reference],
        signal_provenance_by_modality={
            "possible_confusion": {"acoustic": [acoustic_only_reference]},
        },
    )
    _expect_named_contract_errors((
        (
            "WATERMARK_HISTORY_WITHOUT_EVENTS_REPLAY",
            lambda: validate_event_identity(
                dict(evidence, input_revision=1),
                watermark=watermark_history_without_events,
            ),
        ),
        (
            "WATERMARK_EVENTS_WITHOUT_HISTORY",
            lambda: validate_event_identity(
                dict(evidence, event_id="event-2"),
                watermark=watermark_events_without_history,
            ),
        ),
        (
            "WATERMARK_SAME_CARDINALITY_EVENT_SUBSTITUTION",
            lambda: validate_event_identity(
                dict(evidence, input_revision=1),
                watermark=watermark_same_cardinality_substitution,
            ),
        ),
        (
            "TEXT_ONLY_WITH_ACOUSTIC_ONLY_PROVENANCE",
            lambda: validate_perceived_customer_state(text_only_with_acoustic_only_provenance),
        ),
        (
            "NONCANONICAL_COMPACT_AGGREGATION_DATE",
            lambda: validate_operational_aggregate(dict(
                aggregate,
                aggregation_window=dict(
                    aggregate["aggregation_window"],
                    window_start_date="20260701",
                ),
            )),
        ),
        (
            "NONCANONICAL_ISO_WEEK_AGGREGATION_DATE",
            lambda: validate_operational_aggregate(dict(
                aggregate,
                aggregation_window=dict(
                    aggregate["aggregation_window"],
                    window_start_date="2026-W27-3",
                ),
            )),
        ),
        (
            "HUGE_INTEGER_PERCENTILE_NORMALIZED",
            lambda: validate_operational_aggregate(dict(
                aggregate,
                processing_latency_percentiles={"p50": 0, "p95": 10 ** 10000},
            )),
        ),
        (
            "SKIPPED_CORRECTION_REV2_FROM_REV0",
            lambda: validate_event_identity(
                dict(evidence, event_id="event-skipped-correction", input_revision=2),
                watermark=first_watermark,
            ),
        ),
        (
            "UNHASHABLE_AUDIO_ANALYSIS_STATUS",
            lambda: validate_customer_turn_audit(dict(audit, audio_analysis_status=[])),
        ),
        (
            "UNHASHABLE_OVERALL_EVIDENCE_QUALITY",
            lambda: validate_perceived_customer_state(dict(state, overall_evidence_quality=[])),
        ),
    ))
    _expect_named_contract_successes((
        (
            "SKIPPED_CORRECTION_REJECTED_OR_RETURNED_WATERMARK_REVALIDATES",
            lambda: _require_rejected_or_revalidatable_event(
                dict(evidence, event_id="event-skipped-correction", input_revision=2),
                watermark=first_watermark,
            ),
        ),
        (
            "NORMAL_CORRECTIONS_0_TO_1_TO_2_REVALIDATE",
            lambda: _validate_event_watermark(second_corrected_watermark),
        ),
    ))
    return "pass"
