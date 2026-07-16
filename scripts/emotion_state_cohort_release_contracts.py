from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any

from runtime.contracts.emotion_pattern_contracts import validate_pattern_candidate
from runtime.contracts.emotion_state_contracts import (
    AUDIO_QUALITY_STATUSES,
    EVIDENCE_POLICY_VERSION_PATTERN,
    validate_operational_aggregate,
)
from scripts.emotion_state_public_dataset_contracts import SELECTED_PUBLIC_DATASETS


ALLOWED_SPEAKER_BASES = frozenset({
    "public_dataset_actor_id",
    "public_dataset_participant_id",
    "synthetic_fixture_speaker_id",
})
RESERVED_DISABLED_SPEAKER_BASE = "privacy_reviewed_pseudonymous_cohort_token"
FORBIDDEN_SPEAKER_BASES = frozenset({
    "call_id",
    "session_id",
    "turn_id",
    "name",
    "phone_number",
    "email_address",
    "account_id",
    "crm_id",
    "undocumented_identifier_hash",
    "voiceprint",
    "speaker_embedding",
    "biometric_match",
    "provider_identity_prediction",
    "model_identity_prediction",
    "probabilistic_dedup_as_certain",
})
METRIC_ALLOWLIST_V1 = (
    "eligible_call_count",
    "audio_analysis_availability_rate",
    "audio_quality_bucket_counts",
    "abstention_rate",
    "processing_latency_percentiles",
    "evidence_policy_version_counts",
)
METRIC_ALLOWLIST_VERSION_V1 = "emotion-state-operational-aggregate-v1"
MIN_DISCOVERY_SPEAKERS = 5
MIN_DISCOVERY_TURNS = 10
MAX_DISCOVERY_TURNS_PER_SPEAKER = 2
MIN_RELEASE_SPEAKERS = 10
MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER = 1
MIN_CONFIRMATORY_SPEAKERS = 30
MIN_CONFIRMATORY_POSITIVE_TURNS = 30
MIN_CONFIRMATORY_NEGATIVE_TURNS = 30
RELEASE_SCOPE = "suppression-based, privacy-minimized contribution gate"
ALLOWED_SUPPRESSION_REASON_CODES = frozenset({
    "speaker_basis_missing",
    "dataset_namespaced_speaker_key_missing",
    "deterministic_contribution_evidence_missing",
    "cross_corpus_identity_not_proven",
    "minimum_unique_speakers_not_met",
})

COHORT_RELEASE_FIELDS = frozenset({
    "release_scope",
    "source_label",
    "aggregation_window",
    "input_record_count",
    "eligible_record_count",
    "unique_speaker_count",
    "unique_speaker_basis",
    "dependency_keys",
    "max_contribution_per_speaker",
    "dedup_evidence_digest",
    "minimum_unique_speakers",
    "metric_allowlist_version",
    "minimum_unique_speakers_per_output_cell",
    "fixed_window_id",
    "window_overlaps_previous_release",
    "previous_release_digest",
    "release_replaces_digest",
    "direct_identifiers_present",
    "voiceprint_used",
    "speaker_tokens_persisted",
    "contains_per_speaker_rows",
    "contains_demographic_slices",
    "contains_state_or_signal_labels",
    "release_status",
    "suppression_reason_codes",
    "runtime_influence_allowed",
    "aggregate_metrics",
    "output_cell_unique_speaker_counts",
})
BOOLEAN_BOUNDARY_FIELDS = (
    "window_overlaps_previous_release",
    "direct_identifiers_present",
    "voiceprint_used",
    "speaker_tokens_persisted",
    "contains_per_speaker_rows",
    "contains_demographic_slices",
    "contains_state_or_signal_labels",
    "runtime_influence_allowed",
)
REQUEST_FIELDS = frozenset({
    "release_scope",
    "source_label",
    "operational_aggregate",
    "unique_speaker_basis",
    "dependency_keys",
    "metric_allowlist_version",
    "fixed_window_id",
    "window_policy",
    "window_relationship",
    "ad_hoc_filters",
    "slice_dimensions",
    "complementary_query",
    "differencing_query",
    "authoritative_release_history",
    "authoritative_release_history_digest",
    "previous_release_digest",
    "release_replaces_digest",
    "replacement_scope",
    "cross_corpus_identity_evidence_digest",
})
RECORD_ALLOWED_FIELDS = frozenset({
    "dataset_manifest_id",
    "source_speaker_id",
    "source_timestamp",
    "canonical_record_digest",
    "eligible",
    "metric_cell_memberships",
})
CONFIRMATORY_FIELDS = frozenset({
    "overall_unique_speaker_count",
    "promoted_labels",
    "per_promoted_label",
    "power_precision_requirement_passed",
})
CONFIRMATORY_LABEL_FIELDS = frozenset({
    "consensus_positive_turn_count",
    "consensus_negative_turn_count",
})
DEPENDENCY_KEYS = ("speaker", "source_corpus")
ALLOWED_SOURCE_LABELS = frozenset({"public-only", "synthetic-only"})
SHA256_PATTERN = re.compile(r"[0-9A-F]{64}")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _canonical_json_bytes(payload: Any) -> bytes:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("payload must be canonical JSON data") from exc


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest().upper()


def _require_exact_fields(payload: Any, fields: frozenset[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    if set(payload) != fields:
        raise ValueError(f"{label} fields mismatch")


def _require_nonempty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")


def _require_sha256_or_none(value: Any, label: str) -> None:
    if value is not None and (
        not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None
    ):
        raise ValueError(f"{label} must be null or an uppercase SHA-256 digest")


def _fixed_window_id(window: dict[str, Any]) -> str:
    return (
        f"utc-{window['window_start_date']}--{window['window_end_date']}"
    )


def _validate_aggregation_window(window: Any) -> dict[str, Any]:
    if (
        not isinstance(window, dict)
        or set(window) != {"window_start_date", "window_end_date", "timezone"}
        or window.get("timezone") != "UTC"
    ):
        raise ValueError("CohortReleaseEvidenceV1 fixed aggregation window is invalid")
    if any(
        not isinstance(window[field], str)
        or DATE_PATTERN.fullmatch(window[field]) is None
        for field in ("window_start_date", "window_end_date")
    ):
        raise ValueError("aggregation window dates must use canonical YYYY-MM-DD")
    try:
        start = datetime.strptime(window["window_start_date"], "%Y-%m-%d")
        end = datetime.strptime(window["window_end_date"], "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("aggregation window contains an invalid date") from exc
    if end < start:
        raise ValueError("aggregation window end precedes start")
    return window


def _validate_metric_cell_memberships(
    value: Any,
    aggregate: dict[str, Any],
    *,
    record_index: int,
) -> dict[str, list[str]]:
    if not isinstance(value, dict) or set(value) != set(METRIC_ALLOWLIST_V1):
        raise ValueError(
            f"record {record_index}.metric_cell_memberships must cover the metric allowlist"
        )
    for metric in METRIC_ALLOWLIST_V1:
        cells = value[metric]
        if (
            not isinstance(cells, list)
            or any(not isinstance(cell, str) or not cell for cell in cells)
            or len(cells) != len(set(cells))
        ):
            raise ValueError(
                f"record {record_index}.metric_cell_memberships.{metric} "
                "must be a unique string list"
            )
        aggregate_value = aggregate[metric]
        if isinstance(aggregate_value, dict):
            if any(cell not in aggregate_value for cell in cells):
                raise ValueError(
                    f"record {record_index}.metric_cell_memberships.{metric} "
                    "contains an unknown aggregate cell"
                )
        elif cells != ["__scalar__"]:
            raise ValueError(
                f"record {record_index}.metric_cell_memberships.{metric} "
                "must contain only __scalar__"
            )
    return value


def _derive_cell_support(
    selected: list[dict[str, Any]],
) -> dict[str, int | dict[str, int]]:
    support: dict[str, set[tuple[str, str]] | dict[str, set[tuple[str, str]]]] = {}
    for metric in METRIC_ALLOWLIST_V1:
        if selected and selected[0]["metric_cell_memberships"][metric] == ["__scalar__"]:
            support[metric] = set()
        else:
            support[metric] = {}
    for record in selected:
        speaker_key = (record["dataset_manifest_id"], record["source_speaker_id"])
        for metric, cells in record["metric_cell_memberships"].items():
            if cells == ["__scalar__"]:
                metric_support = support[metric]
                if not isinstance(metric_support, set):
                    raise ValueError("scalar metric membership shape mismatch")
                metric_support.add(speaker_key)
            else:
                metric_support = support[metric]
                if not isinstance(metric_support, dict):
                    raise ValueError("dictionary metric membership shape mismatch")
                for cell in cells:
                    metric_support.setdefault(cell, set()).add(speaker_key)
    counts: dict[str, int | dict[str, int]] = {}
    for metric, metric_support in support.items():
        if isinstance(metric_support, set):
            counts[metric] = len(metric_support)
        else:
            counts[metric] = {
                cell: len(speakers)
                for cell, speakers in metric_support.items()
            }
    return counts


def _filter_supported_cells(
    aggregate: dict[str, Any],
    counts: dict[str, Any],
    *,
    unique_speaker_count: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    released_metrics: dict[str, Any] = {}
    released_counts: dict[str, Any] = {}
    for metric in METRIC_ALLOWLIST_V1:
        value = aggregate[metric]
        support = counts[metric]
        if isinstance(value, dict):
            metric_values: dict[str, Any] = {}
            metric_counts: dict[str, int] = {}
            for cell_name, cell_value in value.items():
                count = support.get(cell_name, 0)
                if count > unique_speaker_count:
                    raise ValueError("output-cell speaker count exceeds the proven cohort")
                if count >= MIN_RELEASE_SPEAKERS:
                    metric_values[cell_name] = deepcopy(cell_value)
                    metric_counts[cell_name] = count
            if metric_values:
                released_metrics[metric] = metric_values
                released_counts[metric] = metric_counts
        else:
            if support > unique_speaker_count:
                raise ValueError("output-cell speaker count exceeds the proven cohort")
            if support >= MIN_RELEASE_SPEAKERS:
                released_metrics[metric] = deepcopy(value)
                released_counts[metric] = support
    return released_metrics, released_counts


def _require_finite_number(value: Any, label: str, *, minimum: float = 0.0) -> None:
    if type(value) not in {int, float} or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{label} must be a finite number at least {minimum}")


def _validate_sparse_aggregate_metrics(
    metrics: dict[str, Any],
    *,
    eligible_record_count: int,
) -> None:
    required_scalar_metrics = {
        "eligible_call_count",
        "audio_analysis_availability_rate",
        "abstention_rate",
    }
    if not required_scalar_metrics <= set(metrics):
        raise ValueError("released aggregate metrics must retain every scalar metric")
    eligible_call_count = metrics["eligible_call_count"]
    if type(eligible_call_count) is not int or eligible_call_count != eligible_record_count:
        raise ValueError("released eligible_call_count must equal the capped contribution count")
    for metric in ("audio_analysis_availability_rate", "abstention_rate"):
        value = metrics[metric]
        _require_finite_number(value, metric)
        if value > 1.0:
            raise ValueError(f"{metric} must not exceed one")
    if "audio_quality_bucket_counts" in metrics:
        counts = metrics["audio_quality_bucket_counts"]
        if (
            not isinstance(counts, dict)
            or not counts
            or any(
                not isinstance(bucket, str)
                or bucket not in AUDIO_QUALITY_STATUSES
                or type(count) is not int
                or count < 0
                for bucket, count in counts.items()
            )
        ):
            raise ValueError("released audio quality cells are malformed")
    if "processing_latency_percentiles" in metrics:
        percentiles = metrics["processing_latency_percentiles"]
        if (
            not isinstance(percentiles, dict)
            or not percentiles
            or any(
                not isinstance(name, str) or name not in {"p50", "p95"}
                for name in percentiles
            )
        ):
            raise ValueError("released processing latency percentile cells are malformed")
        for name, value in percentiles.items():
            _require_finite_number(value, f"processing_latency_percentiles.{name}")
        if {"p50", "p95"} <= set(percentiles) and percentiles["p95"] < percentiles["p50"]:
            raise ValueError("released processing latency percentiles are non-monotonic")
    if "evidence_policy_version_counts" in metrics:
        counts = metrics["evidence_policy_version_counts"]
        if (
            not isinstance(counts, dict)
            or not counts
            or any(
                not isinstance(version, str)
                or EVIDENCE_POLICY_VERSION_PATTERN.fullmatch(version) is None
                or type(count) is not int
                or count < 0
                for version, count in counts.items()
            )
        ):
            raise ValueError("released evidence-policy version cells are malformed")


def _validate_window_request(request: dict[str, Any]) -> None:
    if request["window_policy"] != "fixed_closed_non_overlapping":
        raise ValueError("release window must be fixed, closed, and non-overlapping")
    relationship = request["window_relationship"]
    if (
        not isinstance(relationship, str)
        or relationship not in {"new_non_overlapping", "replacement"}
    ):
        raise ValueError("overlapping, nested, repeated, or complementary windows are blocked")
    for field in ("ad_hoc_filters", "slice_dimensions"):
        value = request[field]
        if not isinstance(value, list):
            raise ValueError(f"{field} must be a list")
        if value:
            raise ValueError("filtered and sliced cohort releases are blocked")
    for field in ("complementary_query", "differencing_query"):
        if type(request[field]) is not bool or request[field] is not False:
            raise ValueError("complementary and differencing queries are blocked")


def canonical_release_history_digest(history: Any) -> str:
    if not isinstance(history, list):
        raise ValueError("authoritative_release_history must be a list")
    return _sha256(history)


def _windows_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_start = datetime.strptime(left["window_start_date"], "%Y-%m-%d")
    left_end = datetime.strptime(left["window_end_date"], "%Y-%m-%d")
    right_start = datetime.strptime(right["window_start_date"], "%Y-%m-%d")
    right_end = datetime.strptime(right["window_end_date"], "%Y-%m-%d")
    return left_start <= right_end and right_start <= left_end


def _validate_authoritative_release_history(
    history: Any,
    history_digest: Any,
) -> list[dict[str, Any]]:
    if not isinstance(history, list):
        raise ValueError("authoritative_release_history must be a list")
    if (
        not isinstance(history_digest, str)
        or SHA256_PATTERN.fullmatch(history_digest) is None
    ):
        raise ValueError("authoritative release history digest must be uppercase SHA-256")
    if canonical_release_history_digest(history) != history_digest:
        raise ValueError("authoritative release history digest mismatch")
    validated: list[dict[str, Any]] = []
    for index, prior_release in enumerate(history):
        if not isinstance(prior_release, dict):
            raise ValueError(f"authoritative release history entry {index} must be an object")
        validated.append(validate_cohort_release(prior_release))
    canonical_order = sorted(
        validated,
        key=lambda release: (
            release["aggregation_window"]["window_start_date"],
            release["aggregation_window"]["window_end_date"],
            release["fixed_window_id"],
            canonical_release_digest(release),
        ),
    )
    if validated != canonical_order:
        raise ValueError("authoritative release history must use canonical window order")
    release_digests = [canonical_release_digest(release) for release in validated]
    if len(release_digests) != len(set(release_digests)):
        raise ValueError("authoritative release history contains a duplicate release")
    for left_index, left in enumerate(validated):
        for right in validated[left_index + 1:]:
            if _windows_overlap(left["aggregation_window"], right["aggregation_window"]):
                raise ValueError("authoritative release history contains overlapping windows")
    return validated


def _validate_replacement_request(request: dict[str, Any]) -> None:
    relationship = request["window_relationship"]
    previous_digest = request["previous_release_digest"]
    replaces_digest = request["release_replaces_digest"]
    replacement_scope = request["replacement_scope"]
    _require_sha256_or_none(previous_digest, "previous_release_digest")
    _require_sha256_or_none(replaces_digest, "release_replaces_digest")
    history = request["authoritative_release_history"]
    current_window = request["operational_aggregate"]["aggregation_window"]
    current_window_id = request["fixed_window_id"]
    if relationship == "new_non_overlapping":
        if any(value is not None for value in (
            previous_digest, replaces_digest, replacement_scope,
        )):
            raise ValueError("a new release cannot bind or duplicate a previous window")
        for prior_release in history:
            if (
                current_window_id == prior_release["fixed_window_id"]
                or _windows_overlap(current_window, prior_release["aggregation_window"])
            ):
                raise ValueError("new release window overlaps or duplicates authoritative history")
        return
    matches = [
        prior_release
        for prior_release in history
        if prior_release["fixed_window_id"] == current_window_id
        and prior_release["aggregation_window"] == current_window
    ]
    if len(matches) != 1:
        raise ValueError("replacement requires exactly one matching authoritative history entry")
    previous = matches[0]
    canonical_previous_digest = canonical_release_digest(previous)
    if previous_digest != canonical_previous_digest or replaces_digest != canonical_previous_digest:
        raise ValueError("replacement must bind the prior canonical release digest")
    if replacement_scope != "entire_prior_release":
        raise ValueError("replacement must replace the entire prior release")
    if request["metric_allowlist_version"] != previous["metric_allowlist_version"]:
        raise ValueError("replacement must preserve the exact metric allowlist")


def _validate_request(request: Any) -> dict[str, Any]:
    _require_exact_fields(request, REQUEST_FIELDS, "cohort release request")
    if request["release_scope"] != RELEASE_SCOPE:
        raise ValueError("release_scope must name the privacy-minimized contribution gate")
    if (
        not isinstance(request["source_label"], str)
        or request["source_label"] not in ALLOWED_SOURCE_LABELS
    ):
        raise ValueError("source_label must identify synthetic or public metadata")
    aggregate = validate_operational_aggregate(request["operational_aggregate"])
    if request["dependency_keys"] != list(DEPENDENCY_KEYS):
        raise ValueError("dependency_keys must bind speaker and source_corpus")
    _require_nonempty_string(request["fixed_window_id"], "fixed_window_id")
    if request["fixed_window_id"] != _fixed_window_id(aggregate["aggregation_window"]):
        raise ValueError("fixed_window_id does not bind the aggregation window")
    if request["cross_corpus_identity_evidence_digest"] is not None:
        raise ValueError("cross_corpus_identity_evidence_digest must remain null in Phase A")
    request["authoritative_release_history"] = _validate_authoritative_release_history(
        request["authoritative_release_history"],
        request["authoritative_release_history_digest"],
    )
    _validate_window_request(request)
    _validate_replacement_request(request)
    if request["metric_allowlist_version"] != METRIC_ALLOWLIST_VERSION_V1:
        raise ValueError("unsupported metric allowlist version")
    return request


def _speaker_basis_status(request: dict[str, Any]) -> tuple[str | None, list[str]]:
    basis = request["unique_speaker_basis"]
    if basis is None:
        return None, ["speaker_basis_missing"]
    if not isinstance(basis, str):
        raise ValueError("forbidden or unsupported speaker basis")
    if basis == RESERVED_DISABLED_SPEAKER_BASE:
        raise ValueError("reserved speaker basis is disabled pending separate privacy and security review")
    if basis not in ALLOWED_SPEAKER_BASES:
        raise ValueError("forbidden or unsupported speaker basis")
    if basis.startswith("public_dataset_") and request["source_label"] != "public-only":
        raise ValueError("public dataset speaker basis requires public-only metadata")
    if basis == "synthetic_fixture_speaker_id" and request["source_label"] != "synthetic-only":
        raise ValueError("synthetic fixture speaker basis requires synthetic-only metadata")
    return basis, []


def evaluate_discovery_gate(records: Any) -> dict[str, bool | int]:
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    eligible: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) - RECORD_ALLOWED_FIELDS:
            raise ValueError(f"record {index} contains forbidden or unknown fields")
        if "eligible" not in record or type(record["eligible"]) is not bool:
            raise ValueError(f"record {index}.eligible must be boolean")
        dataset_id = record.get("dataset_manifest_id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise ValueError(f"record {index}.dataset_manifest_id must be a nonempty string")
        if not record["eligible"]:
            continue
        speaker_id = record.get("source_speaker_id")
        if not isinstance(speaker_id, str) or not speaker_id.strip():
            raise ValueError(f"record {index}.source_speaker_id must be a nonempty string")
        timestamp = record.get("source_timestamp")
        if not isinstance(timestamp, str) or TIMESTAMP_PATTERN.fullmatch(timestamp) is None:
            raise ValueError(f"record {index}.source_timestamp must be canonical UTC")
        try:
            datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError(f"record {index}.source_timestamp is invalid") from exc
        digest = record.get("canonical_record_digest")
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError(f"record {index}.canonical_record_digest must be uppercase SHA-256")
        eligible.append(record)

    retained_per_speaker: dict[tuple[str, str], int] = {}
    retained_turn_count = 0
    for record in sorted(
        eligible,
        key=lambda item: (
            item["dataset_manifest_id"],
            item["source_speaker_id"],
            item["source_timestamp"],
            item["canonical_record_digest"],
        ),
    ):
        speaker_key = (record["dataset_manifest_id"], record["source_speaker_id"])
        retained_count = retained_per_speaker.get(speaker_key, 0)
        if retained_count >= MAX_DISCOVERY_TURNS_PER_SPEAKER:
            continue
        retained_per_speaker[speaker_key] = retained_count + 1
        retained_turn_count += 1

    unique_speaker_count = len(retained_per_speaker)
    return {
        "discovery_eligible": (
            unique_speaker_count >= MIN_DISCOVERY_SPEAKERS
            and retained_turn_count >= MIN_DISCOVERY_TURNS
        ),
        "unique_speaker_count": unique_speaker_count,
        "retained_turn_count": retained_turn_count,
    }


def _select_contributions(
    records: Any,
    *,
    basis_available: bool,
    aggregate: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, str | None, list[str]]:
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    eligible: list[dict[str, Any]] = []
    reasons: list[str] = []
    namespaced_keys: set[tuple[str, str]] = set()
    dataset_ids: set[str] = set()
    deterministic_evidence_missing = False
    namespaced_key_missing = False
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) - RECORD_ALLOWED_FIELDS:
            raise ValueError(f"record {index} contains forbidden or unknown fields")
        if "eligible" not in record:
            raise ValueError(f"record {index} is missing eligible")
        if type(record["eligible"]) is not bool:
            raise ValueError(f"record {index}.eligible must be boolean")
        if "metric_cell_memberships" not in record:
            raise ValueError(f"record {index}.metric_cell_memberships is required")
        _validate_metric_cell_memberships(
            record["metric_cell_memberships"],
            aggregate,
            record_index=index,
        )
        dataset_id = record.get("dataset_manifest_id")
        dataset_id_valid = isinstance(dataset_id, str) and bool(dataset_id.strip())
        if dataset_id_valid:
            dataset_ids.add(dataset_id)
        else:
            namespaced_key_missing = True
        if not record["eligible"]:
            continue
        speaker_id = record.get("source_speaker_id")
        if (
            not dataset_id_valid
            or not isinstance(speaker_id, str)
            or not speaker_id.strip()
        ):
            namespaced_key_missing = True
            continue
        namespaced_keys.add((dataset_id, speaker_id))
        timestamp = record.get("source_timestamp")
        digest = record.get("canonical_record_digest")
        if timestamp is None or digest is None:
            deterministic_evidence_missing = True
            continue
        if not isinstance(timestamp, str) or TIMESTAMP_PATTERN.fullmatch(timestamp) is None:
            raise ValueError(f"record {index}.source_timestamp must be canonical UTC")
        try:
            datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as exc:
            raise ValueError(f"record {index}.source_timestamp is invalid") from exc
        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            raise ValueError(f"record {index}.canonical_record_digest must be uppercase SHA-256")
        eligible.append(record)
    if namespaced_key_missing:
        reasons.append("dataset_namespaced_speaker_key_missing")
    if deterministic_evidence_missing:
        reasons.append("deterministic_contribution_evidence_missing")
    if len(dataset_ids) > 1:
        reasons.append("cross_corpus_identity_not_proven")
    unique_count = len(namespaced_keys) if basis_available else 0
    if not basis_available or namespaced_key_missing or deterministic_evidence_missing:
        return [], unique_count, None, reasons
    selected_by_speaker: dict[tuple[str, str], dict[str, Any]] = {}
    for record in sorted(
        eligible,
        key=lambda item: (
            item["dataset_manifest_id"],
            item["source_speaker_id"],
            item["source_timestamp"],
            item["canonical_record_digest"],
        ),
    ):
        key = (record["dataset_manifest_id"], record["source_speaker_id"])
        selected_by_speaker.setdefault(key, record)
    selected = list(selected_by_speaker.values())
    evidence_projection = [
        {
            "dataset_manifest_id": record["dataset_manifest_id"],
            "source_speaker_id": record["source_speaker_id"],
            "source_timestamp": record["source_timestamp"],
            "canonical_record_digest": record["canonical_record_digest"],
        }
        for record in selected
    ]
    return selected, unique_count, _sha256(evidence_projection), reasons


def build_cohort_release(records: Any, request: Any) -> dict[str, Any]:
    request = _validate_request(request)
    basis, reasons = _speaker_basis_status(request)
    selected, unique_count, dedup_digest, selection_reasons = _select_contributions(
        records,
        basis_available=basis is not None,
        aggregate=request["operational_aggregate"],
    )
    reasons.extend(selection_reasons)
    if unique_count < MIN_RELEASE_SPEAKERS:
        reasons.append("minimum_unique_speakers_not_met")
    reasons = list(dict.fromkeys(reasons))
    released = not reasons
    aggregate = request["operational_aggregate"]
    if released and aggregate["eligible_call_count"] != len(selected):
        raise ValueError("operational aggregate must use the contribution-capped cohort")
    if released:
        derived_counts = _derive_cell_support(selected)
        aggregate_metrics, output_counts = _filter_supported_cells(
            aggregate,
            derived_counts,
            unique_speaker_count=unique_count,
        )
    else:
        aggregate_metrics, output_counts = {}, {}
    payload = {
        "release_scope": RELEASE_SCOPE,
        "source_label": request["source_label"],
        "aggregation_window": deepcopy(aggregate["aggregation_window"]),
        "input_record_count": len(records),
        "eligible_record_count": len(selected),
        "unique_speaker_count": unique_count,
        "unique_speaker_basis": basis,
        "dependency_keys": list(DEPENDENCY_KEYS),
        "max_contribution_per_speaker": MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER,
        "dedup_evidence_digest": dedup_digest,
        "minimum_unique_speakers": MIN_RELEASE_SPEAKERS,
        "metric_allowlist_version": METRIC_ALLOWLIST_VERSION_V1,
        "minimum_unique_speakers_per_output_cell": MIN_RELEASE_SPEAKERS,
        "fixed_window_id": request["fixed_window_id"],
        "window_overlaps_previous_release": False,
        "previous_release_digest": request["previous_release_digest"],
        "release_replaces_digest": request["release_replaces_digest"],
        "direct_identifiers_present": False,
        "voiceprint_used": False,
        "speaker_tokens_persisted": False,
        "contains_per_speaker_rows": False,
        "contains_demographic_slices": False,
        "contains_state_or_signal_labels": False,
        "release_status": "released" if released else "suppressed",
        "suppression_reason_codes": reasons,
        "runtime_influence_allowed": False,
        "aggregate_metrics": aggregate_metrics,
        "output_cell_unique_speaker_counts": output_counts,
    }
    return validate_cohort_release(payload)


def validate_cohort_release(payload: Any) -> dict[str, Any]:
    _require_exact_fields(payload, COHORT_RELEASE_FIELDS, "CohortReleaseEvidenceV1")
    _canonical_json_bytes(payload)
    if payload["release_scope"] != RELEASE_SCOPE:
        raise ValueError("CohortReleaseEvidenceV1 release scope mismatch")
    if (
        not isinstance(payload["source_label"], str)
        or payload["source_label"] not in ALLOWED_SOURCE_LABELS
    ):
        raise ValueError("CohortReleaseEvidenceV1 source label is invalid")
    window = _validate_aggregation_window(payload["aggregation_window"])
    if payload["fixed_window_id"] != _fixed_window_id(window):
        raise ValueError("CohortReleaseEvidenceV1 fixed aggregation window is invalid")
    for field in ("input_record_count", "eligible_record_count", "unique_speaker_count"):
        if type(payload[field]) is not int or payload[field] < 0:
            raise ValueError(f"CohortReleaseEvidenceV1 {field} must be a nonnegative integer")
    if payload["input_record_count"] < payload["eligible_record_count"]:
        raise ValueError("eligible record count exceeds input record count")
    basis = payload["unique_speaker_basis"]
    if basis is not None and (
        not isinstance(basis, str) or basis not in ALLOWED_SPEAKER_BASES
    ):
        raise ValueError("CohortReleaseEvidenceV1 speaker basis is invalid")
    if payload["dependency_keys"] != list(DEPENDENCY_KEYS):
        raise ValueError("CohortReleaseEvidenceV1 dependency keys mismatch")
    if (
        type(payload["max_contribution_per_speaker"]) is not int
        or payload["max_contribution_per_speaker"]
        != MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER
    ):
        raise ValueError("CohortReleaseEvidenceV1 contribution cap mismatch")
    _require_sha256_or_none(payload["dedup_evidence_digest"], "dedup_evidence_digest")
    if (
        type(payload["minimum_unique_speakers"]) is not int
        or payload["minimum_unique_speakers"] != MIN_RELEASE_SPEAKERS
    ):
        raise ValueError("CohortReleaseEvidenceV1 speaker minimum mismatch")
    if (
        type(payload["minimum_unique_speakers_per_output_cell"]) is not int
        or payload["minimum_unique_speakers_per_output_cell"] != MIN_RELEASE_SPEAKERS
    ):
        raise ValueError("CohortReleaseEvidenceV1 output-cell minimum mismatch")
    if payload["metric_allowlist_version"] != METRIC_ALLOWLIST_VERSION_V1:
        raise ValueError("CohortReleaseEvidenceV1 metric allowlist mismatch")
    for field in BOOLEAN_BOUNDARY_FIELDS:
        if type(payload[field]) is not bool or payload[field] is not False:
            raise ValueError(f"CohortReleaseEvidenceV1 boundary must remain false: {field}")
    previous_digest = payload["previous_release_digest"]
    replaces_digest = payload["release_replaces_digest"]
    _require_sha256_or_none(previous_digest, "previous_release_digest")
    _require_sha256_or_none(replaces_digest, "release_replaces_digest")
    if (previous_digest is None) != (replaces_digest is None) or (
        previous_digest is not None and previous_digest != replaces_digest
    ):
        raise ValueError("replacement digest bindings are inconsistent")
    status = payload["release_status"]
    if not isinstance(status, str) or status not in {"released", "suppressed"}:
        raise ValueError("CohortReleaseEvidenceV1 release status is invalid")
    reasons = payload["suppression_reason_codes"]
    if (
        not isinstance(reasons, list)
        or any(not isinstance(reason, str) or not reason for reason in reasons)
        or len(reasons) != len(set(reasons))
    ):
        raise ValueError("suppression_reason_codes must be a unique string list")
    reason_set = set(reasons)
    if reason_set - ALLOWED_SUPPRESSION_REASON_CODES:
        raise ValueError("suppression_reason_codes contains an unknown code")
    if ("speaker_basis_missing" in reason_set) != (basis is None):
        raise ValueError("speaker-basis suppression reason contradicts the evidence")
    minimum_not_met = (
        payload["unique_speaker_count"] < payload["minimum_unique_speakers"]
    )
    if ("minimum_unique_speakers_not_met" in reason_set) != minimum_not_met:
        raise ValueError("minimum-speaker suppression reason contradicts the evidence")
    dedup_missing = payload["dedup_evidence_digest"] is None
    if (
        "deterministic_contribution_evidence_missing" in reason_set
        and not dedup_missing
    ):
        raise ValueError("deterministic-evidence suppression reason contradicts the digest")
    if (
        "dataset_namespaced_speaker_key_missing" in reason_set
        and not dedup_missing
    ):
        raise ValueError("speaker-key suppression reason contradicts the digest")
    if (
        dedup_missing
        and basis is not None
        and not reason_set.intersection({
            "dataset_namespaced_speaker_key_missing",
            "deterministic_contribution_evidence_missing",
        })
    ):
        raise ValueError("missing dedup evidence lacks a corresponding suppression reason")
    metrics = payload["aggregate_metrics"]
    counts = payload["output_cell_unique_speaker_counts"]
    if not isinstance(metrics, dict) or set(metrics) - set(METRIC_ALLOWLIST_V1):
        raise ValueError("aggregate_metrics exceeds the metric allowlist")
    if not isinstance(counts, dict) or set(counts) != set(metrics):
        raise ValueError("released metric cells and speaker counts must match")
    if status == "suppressed":
        if not reasons or metrics or counts:
            raise ValueError("suppressed release must omit every aggregate cell")
    else:
        if reasons:
            raise ValueError("released cohort cannot carry suppression reasons")
        if payload["unique_speaker_count"] < MIN_RELEASE_SPEAKERS:
            raise ValueError("released cohort does not meet the speaker minimum")
        if payload["eligible_record_count"] != payload["unique_speaker_count"]:
            raise ValueError("released cohort violates the contribution cap")
        if payload["dedup_evidence_digest"] is None or basis is None:
            raise ValueError("released cohort lacks unique-speaker evidence")
        _validate_sparse_aggregate_metrics(
            metrics,
            eligible_record_count=payload["eligible_record_count"],
        )
    for metric, value in metrics.items():
        support = counts[metric]
        if isinstance(value, dict):
            if not isinstance(support, dict) or set(support) != set(value) or not value:
                raise ValueError(f"released cells mismatch for {metric}")
            support_values = support.values()
        else:
            support_values = (support,)
        if any(
            type(count) is not int
            or count < MIN_RELEASE_SPEAKERS
            or count > payload["unique_speaker_count"]
            for count in support_values
        ):
            raise ValueError(f"released cell for {metric} lacks ten proven speakers")
    return payload


def canonical_release_digest(payload: dict[str, Any]) -> str:
    validate_cohort_release(payload)
    return _sha256(payload)


def validate_confirmatory_floor(evidence: Any) -> dict[str, Any]:
    _require_exact_fields(evidence, CONFIRMATORY_FIELDS, "confirmatory floor evidence")
    labels = evidence["promoted_labels"]
    if (
        not isinstance(labels, list)
        or not labels
        or any(not isinstance(label, str) or not label.strip() for label in labels)
        or len(labels) != len(set(labels))
    ):
        raise ValueError("promoted_labels must be a nonempty ordered unique string list")
    per_label = evidence["per_promoted_label"]
    if not isinstance(per_label, dict) or set(per_label) != set(labels):
        raise ValueError("promoted_labels must exactly match per_promoted_label keys")
    speakers = evidence["overall_unique_speaker_count"]
    if type(speakers) is not int or speakers < MIN_CONFIRMATORY_SPEAKERS:
        raise ValueError("confirmatory promotion requires at least thirty unique speakers")
    if evidence["power_precision_requirement_passed"] is not True:
        raise ValueError("confirmatory power and precision requirement has not passed")
    for label in labels:
        counts = per_label[label]
        _require_exact_fields(counts, CONFIRMATORY_LABEL_FIELDS, f"confirmatory label {label}")
        positive = counts["consensus_positive_turn_count"]
        negative = counts["consensus_negative_turn_count"]
        if type(positive) is not int or positive < MIN_CONFIRMATORY_POSITIVE_TURNS:
            raise ValueError(f"{label} requires thirty consensus-positive turns")
        if type(negative) is not int or negative < MIN_CONFIRMATORY_NEGATIVE_TURNS:
            raise ValueError(f"{label} requires thirty consensus-negative turns")
    return evidence


def validate_phase_a_pattern_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = validate_pattern_candidate(payload)
    if candidate["discovery_dataset_version"] in SELECTED_PUBLIC_DATASETS:
        raise ValueError(
            "Phase A public dataset gate rejects an operational-signal PatternCandidateV1"
        )
    return candidate


def fixture_records(
    record_count: int,
    unique_speaker_count: int,
    *,
    dataset_manifest_id: str = "synthetic-fixture-dataset-v1",
) -> list[dict[str, Any]]:
    if (
        type(record_count) is not int
        or type(unique_speaker_count) is not int
        or record_count < 0
        or unique_speaker_count < 1
    ):
        raise ValueError("fixture record and speaker counts are invalid")
    _require_nonempty_string(dataset_manifest_id, "dataset_manifest_id")
    start = datetime(2026, 7, 1, tzinfo=timezone.utc)
    records: list[dict[str, Any]] = []
    for index in range(record_count):
        speaker_id = f"fixture-speaker-{index % unique_speaker_count:03d}"
        timestamp = (start + timedelta(minutes=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        digest = _sha256({
            "dataset_manifest_id": dataset_manifest_id,
            "fixture_index": index,
            "source_speaker_id": speaker_id,
            "source_timestamp": timestamp,
        })
        records.append({
            "dataset_manifest_id": dataset_manifest_id,
            "source_speaker_id": speaker_id,
            "source_timestamp": timestamp,
            "canonical_record_digest": digest,
            "eligible": True,
            "metric_cell_memberships": {
                "eligible_call_count": ["__scalar__"],
                "audio_analysis_availability_rate": ["__scalar__"],
                "audio_quality_bucket_counts": ["unavailable"],
                "abstention_rate": ["__scalar__"],
                "processing_latency_percentiles": ["p50", "p95"],
                "evidence_policy_version_counts": ["emotion-state-evidence-v1"],
            },
        })
    return records


def fixture_cross_corpus_records() -> list[dict[str, Any]]:
    return (
        fixture_records(5, 5, dataset_manifest_id="synthetic-corpus-a-v1")
        + fixture_records(5, 5, dataset_manifest_id="synthetic-corpus-b-v1")
    )


def fixture_request(**overrides: Any) -> dict[str, Any]:
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
    request: dict[str, Any] = {
        "release_scope": RELEASE_SCOPE,
        "source_label": "synthetic-only",
        "operational_aggregate": aggregate,
        "unique_speaker_basis": "synthetic_fixture_speaker_id",
        "dependency_keys": list(DEPENDENCY_KEYS),
        "metric_allowlist_version": METRIC_ALLOWLIST_VERSION_V1,
        "fixed_window_id": _fixed_window_id(aggregate["aggregation_window"]),
        "window_policy": "fixed_closed_non_overlapping",
        "window_relationship": "new_non_overlapping",
        "ad_hoc_filters": [],
        "slice_dimensions": [],
        "complementary_query": False,
        "differencing_query": False,
        "authoritative_release_history": [],
        "authoritative_release_history_digest": canonical_release_history_digest([]),
        "previous_release_digest": None,
        "release_replaces_digest": None,
        "replacement_scope": None,
        "cross_corpus_identity_evidence_digest": None,
    }
    request.update(deepcopy(overrides))
    return request


def cohort_release_contract_self_check() -> str:
    suppressed = build_cohort_release(fixture_records(12, 4), fixture_request())
    if suppressed["release_status"] != "suppressed":
        raise AssertionError("four-speaker fixture was not suppressed")
    released = build_cohort_release(fixture_records(10, 10), fixture_request())
    if released["release_status"] != "released":
        raise AssertionError("ten-speaker fixture was not released")
    if any(field in released for field in ("speaker_keys", "per_speaker_rows")):
        raise AssertionError("cohort release retained speaker-level material")
    cross_corpus = build_cohort_release(fixture_cross_corpus_records(), fixture_request())
    if "cross_corpus_identity_not_proven" not in cross_corpus["suppression_reason_codes"]:
        raise AssertionError("cross-corpus fixture was not suppressed")
    validate_confirmatory_floor({
        "overall_unique_speaker_count": 30,
        "promoted_labels": ["confusion"],
        "per_promoted_label": {
            "confusion": {
                "consensus_positive_turn_count": 30,
                "consensus_negative_turn_count": 30,
            },
        },
        "power_precision_requirement_passed": True,
    })
    return "pass"
