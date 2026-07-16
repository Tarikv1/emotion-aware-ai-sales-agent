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
from scripts.emotion_state_public_dataset_contracts import (
    AMI_DATASET_ID,
    CREMA_DATASET_ID,
    SELECTED_PUBLIC_DATASETS,
)


ALLOWED_SPEAKER_BASES = frozenset({
    "public_dataset_actor_id",
    "public_dataset_participant_id",
    "synthetic_fixture_speaker_id",
})
CONTROLLED_SYNTHETIC_FIXTURE_DATASET_IDS = frozenset({
    "synthetic-fixture-dataset-v1",
    "synthetic-fixture-dataset-a-v1",
    "synthetic-fixture-dataset-b-v1",
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
COUNT_MAP_METRICS = frozenset({
    "audio_quality_bucket_counts",
    "evidence_policy_version_counts",
})
SCALAR_METRICS = frozenset({
    "eligible_call_count",
    "audio_analysis_availability_rate",
    "abstention_rate",
})
METRIC_ALLOWLIST_VERSION_V1 = "emotion-state-operational-aggregate-v1"
MIN_DISCOVERY_SPEAKERS = 5
MIN_DISCOVERY_TURNS = 10
MAX_DISCOVERY_TURNS_PER_SPEAKER = 2
MIN_RELEASE_SPEAKERS = 10
MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER = 1
MAX_AUTHORITATIVE_HISTORY_ENTRIES = 256
MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES = 4_194_304
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
FIXED_COHORT_REPLACEMENT_FIELDS = (
    "source_label",
    "unique_speaker_basis",
    "dedup_evidence_digest",
    "eligible_record_count",
    "unique_speaker_count",
)

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
RECORD_EVIDENCE_FIELDS = RECORD_ALLOWED_FIELDS - {"canonical_record_digest"}
CANONICAL_RECORD_PROJECTION = "emotion-state-cohort-record-evidence-v1"
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
CREMA_ACTOR_ID_PATTERN_TEXT = r"^[0-9]{4}$"
AMI_PARTICIPANT_ID_PATTERN_TEXT = r"^[MF][IET][EDO][0-9]{3}(?:PM|ID|ME|UID)?$"
SYNTHETIC_FIXTURE_SPEAKER_ID_PATTERN_TEXT = r"^fixture-speaker-[0-9]{3}$"
CREMA_ACTOR_ID_PATTERN = re.compile(CREMA_ACTOR_ID_PATTERN_TEXT)
AMI_PARTICIPANT_ID_PATTERN = re.compile(AMI_PARTICIPANT_ID_PATTERN_TEXT)
SYNTHETIC_FIXTURE_SPEAKER_ID_PATTERN = re.compile(
    SYNTHETIC_FIXTURE_SPEAKER_ID_PATTERN_TEXT
)


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


def canonical_record_digest(record: Any) -> str:
    if not isinstance(record, dict) or set(record) - RECORD_ALLOWED_FIELDS:
        raise ValueError("record evidence contains forbidden or unknown fields")
    evidence_fields = set(record) - {"canonical_record_digest"}
    if evidence_fields != RECORD_EVIDENCE_FIELDS:
        raise ValueError("canonical record evidence fields mismatch")
    evidence = {
        field: deepcopy(record[field])
        for field in sorted(RECORD_EVIDENCE_FIELDS)
    }
    return _sha256({
        "projection": CANONICAL_RECORD_PROJECTION,
        "record_evidence": evidence,
    })


def _validate_record_provenance(
    record: dict[str, Any],
    *,
    record_index: int,
    source_label: str | None = None,
    speaker_basis: str | None = None,
    require_complete_evidence: bool,
) -> str:
    dataset_id = record.get("dataset_manifest_id")
    if not isinstance(dataset_id, str):
        raise ValueError(
            f"record {record_index}.dataset_manifest_id must be a string naming an "
            "approved public dataset or controlled synthetic fixture dataset"
        )
    if dataset_id == CREMA_DATASET_ID:
        expected_source_label = "public-only"
        expected_basis = "public_dataset_actor_id"
        speaker_pattern = CREMA_ACTOR_ID_PATTERN
        speaker_error = "must be a four-digit CREMA actor identifier"
    elif dataset_id == AMI_DATASET_ID:
        expected_source_label = "public-only"
        expected_basis = "public_dataset_participant_id"
        speaker_pattern = AMI_PARTICIPANT_ID_PATTERN
        speaker_error = "must be an official-format AMI participant identifier"
    elif dataset_id in CONTROLLED_SYNTHETIC_FIXTURE_DATASET_IDS:
        expected_source_label = "synthetic-only"
        expected_basis = "synthetic_fixture_speaker_id"
        speaker_pattern = SYNTHETIC_FIXTURE_SPEAKER_ID_PATTERN
        speaker_error = "must use the controlled synthetic fixture speaker ID syntax"
    else:
        raise ValueError(
            f"record {record_index}.dataset_manifest_id is not an approved public "
            "dataset or controlled synthetic fixture dataset"
        )
    if source_label is not None and source_label != expected_source_label:
        raise ValueError(
            f"record {record_index} dataset provenance does not match source_label"
        )
    if speaker_basis is not None and speaker_basis != expected_basis:
        dataset_name = "CREMA" if dataset_id == CREMA_DATASET_ID else (
            "AMI" if dataset_id == AMI_DATASET_ID else "synthetic fixture"
        )
        raise ValueError(
            f"record {record_index} {dataset_name} dataset does not match speaker basis"
        )
    speaker_id = record.get("source_speaker_id")
    if not isinstance(speaker_id, str) or not speaker_id.strip():
        if require_complete_evidence:
            raise ValueError(
                f"record {record_index}.source_speaker_id {speaker_error}"
            )
        return dataset_id
    if speaker_pattern.fullmatch(speaker_id) is None:
        raise ValueError(f"record {record_index}.source_speaker_id {speaker_error}")
    complete = (
        set(record) == RECORD_ALLOWED_FIELDS
        and isinstance(record.get("source_timestamp"), str)
        and isinstance(record.get("canonical_record_digest"), str)
    )
    if not complete:
        if require_complete_evidence:
            raise ValueError(
                f"record {record_index} canonical record evidence must be complete"
            )
        return dataset_id
    timestamp = record["source_timestamp"]
    if TIMESTAMP_PATTERN.fullmatch(timestamp) is None:
        raise ValueError(f"record {record_index}.source_timestamp must be canonical UTC")
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError(f"record {record_index}.source_timestamp is invalid") from exc
    digest = record["canonical_record_digest"]
    if SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError(
            f"record {record_index}.canonical_record_digest must be uppercase SHA-256"
        )
    if digest != canonical_record_digest(record):
        raise ValueError(f"record {record_index} canonical record digest mismatch")
    return dataset_id


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


def _validate_count_map_support(
    metrics: dict[str, Any],
    counts: dict[str, Any],
) -> None:
    for metric in COUNT_MAP_METRICS.intersection(metrics):
        values = metrics[metric]
        support = counts.get(metric)
        if not isinstance(values, dict) or not isinstance(support, dict):
            raise ValueError(f"count-map metric {metric} support shape mismatch")
        if any(
            type(value) is not int or support.get(cell_name, 0) != value
            for cell_name, value in values.items()
        ) or set(support) - set(values):
            raise ValueError(
                f"count-map metric {metric} values must match membership-derived support"
            )


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
    if not SCALAR_METRICS <= set(metrics):
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


def _validate_fixed_cohort_replacement(
    successor: dict[str, Any],
    target: dict[str, Any],
    *,
    label: str,
) -> None:
    if (
        target["release_status"] != "released"
        or target["dedup_evidence_digest"] is None
    ):
        raise ValueError(
            f"{label} replacement target must be released with non-null dedup evidence"
        )
    if any(
        successor[field] != target[field]
        for field in FIXED_COHORT_REPLACEMENT_FIELDS
    ):
        raise ValueError(f"{label} replacement must preserve the fixed cohort evidence")


def _authoritative_history_active_heads(
    history: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    active: dict[str, dict[str, Any]] = {}
    release_chain: dict[str, str] = {}
    chains: dict[str, dict[str, Any]] = {}
    for index, release in enumerate(history):
        release_digest = canonical_release_digest(release)
        if release_digest in seen:
            raise ValueError("authoritative release history contains a duplicate release")
        target_digest = release["release_replaces_digest"]
        if target_digest is None:
            for chain in chains.values():
                if (
                    release["fixed_window_id"] == chain["fixed_window_id"]
                    or _windows_overlap(
                        release["aggregation_window"],
                        chain["aggregation_window"],
                    )
                ):
                    raise ValueError(
                        "authoritative release history contains overlapping "
                        "distinct window chains"
                    )
            chain_id = release_digest
            chains[chain_id] = {
                "aggregation_window": release["aggregation_window"],
                "fixed_window_id": release["fixed_window_id"],
                "metric_allowlist_version": release["metric_allowlist_version"],
            }
        else:
            target = active.get(target_digest)
            if target is None:
                if target_digest in seen:
                    raise ValueError(
                        "authoritative release history replacement targets a stale head"
                    )
                raise ValueError(
                    "authoritative release history replacement must target exactly one "
                    "earlier active head"
                )
            chain_id = release_chain[target_digest]
            if (
                release["aggregation_window"] != target["aggregation_window"]
                or release["fixed_window_id"] != target["fixed_window_id"]
            ):
                raise ValueError(
                    "authoritative release history replacement must preserve the exact "
                    "window and fixed-window ID"
                )
            if (
                release["metric_allowlist_version"]
                != target["metric_allowlist_version"]
            ):
                raise ValueError(
                    "authoritative release history replacement must preserve the exact "
                    "metric allowlist"
                )
            _validate_fixed_cohort_replacement(
                release,
                target,
                label="authoritative release history",
            )
            del active[target_digest]
        seen[release_digest] = release
        active[release_digest] = release
        release_chain[release_digest] = chain_id
    return active


def _validate_authoritative_release_history(
    history: Any,
    history_digest: Any,
) -> list[dict[str, Any]]:
    if not isinstance(history, list):
        raise ValueError("authoritative_release_history must be a list")
    if len(history) > MAX_AUTHORITATIVE_HISTORY_ENTRIES:
        raise ValueError(
            "authoritative_release_history exceeds "
            "MAX_AUTHORITATIVE_HISTORY_ENTRIES=256"
        )
    if (
        not isinstance(history_digest, str)
        or SHA256_PATTERN.fullmatch(history_digest) is None
    ):
        raise ValueError("authoritative release history digest must be uppercase SHA-256")
    canonical_history_bytes = _canonical_json_bytes(history)
    if len(canonical_history_bytes) > MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES:
        raise ValueError(
            "authoritative_release_history exceeds "
            "MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES=4194304"
        )
    canonical_history_digest = hashlib.sha256(
        canonical_history_bytes
    ).hexdigest().upper()
    if canonical_history_digest != history_digest:
        raise ValueError("authoritative release history digest mismatch")
    validated: list[dict[str, Any]] = []
    for index, prior_release in enumerate(history):
        if not isinstance(prior_release, dict):
            raise ValueError(f"authoritative release history entry {index} must be an object")
        validated.append(validate_cohort_release(prior_release))
    _authoritative_history_active_heads(validated)
    return validated


def _validate_replacement_request(
    request: dict[str, Any],
) -> dict[str, Any] | None:
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
        return None
    if previous_digest != replaces_digest:
        raise ValueError("replacement digest bindings must match")
    active_heads = _authoritative_history_active_heads(history)
    previous = active_heads.get(previous_digest)
    if previous is None:
        raise ValueError("replacement must target exactly one active history head")
    if (
        previous["fixed_window_id"] != current_window_id
        or previous["aggregation_window"] != current_window
    ):
        raise ValueError("replacement must preserve the exact window and fixed-window ID")
    if replacement_scope != "entire_prior_release":
        raise ValueError("replacement must replace the entire prior release")
    if request["metric_allowlist_version"] != previous["metric_allowlist_version"]:
        raise ValueError("replacement must preserve the exact metric allowlist")
    if (
        previous["release_status"] != "released"
        or previous["dedup_evidence_digest"] is None
    ):
        raise ValueError(
            "candidate replacement target must be released with non-null dedup evidence"
        )
    return previous


def _validate_request(
    request: Any,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
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
    replacement_target = _validate_replacement_request(request)
    if request["metric_allowlist_version"] != METRIC_ALLOWLIST_VERSION_V1:
        raise ValueError("unsupported metric allowlist version")
    return request, replacement_target


def _validate_source_basis_pair(source_label: str, basis: Any) -> str:
    if not isinstance(basis, str) or basis not in ALLOWED_SPEAKER_BASES:
        raise ValueError("forbidden or unsupported speaker basis")
    if basis.startswith("public_dataset_") and source_label != "public-only":
        raise ValueError("public dataset speaker basis requires public-only metadata")
    if basis == "synthetic_fixture_speaker_id" and source_label != "synthetic-only":
        raise ValueError("synthetic fixture speaker basis requires synthetic-only metadata")
    return basis


def _speaker_basis_status(request: dict[str, Any]) -> tuple[str | None, list[str]]:
    basis = request["unique_speaker_basis"]
    if basis is None:
        return None, ["speaker_basis_missing"]
    if not isinstance(basis, str):
        raise ValueError("forbidden or unsupported speaker basis")
    if basis == RESERVED_DISABLED_SPEAKER_BASE:
        raise ValueError("reserved speaker basis is disabled pending separate privacy and security review")
    return _validate_source_basis_pair(request["source_label"], basis), []


def evaluate_discovery_gate(records: Any) -> dict[str, bool | int]:
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    eligible: list[dict[str, Any]] = []
    dataset_ids: set[str] = set()
    canonical_record_digests: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or set(record) - RECORD_ALLOWED_FIELDS:
            raise ValueError(f"record {index} contains forbidden or unknown fields")
        if "eligible" not in record or type(record["eligible"]) is not bool:
            raise ValueError(f"record {index}.eligible must be boolean")
        dataset_id = _validate_record_provenance(
            record,
            record_index=index,
            require_complete_evidence=True,
        )
        dataset_ids.add(dataset_id)
        digest = record["canonical_record_digest"]
        if digest in canonical_record_digests:
            raise ValueError(
                "discovery input contains duplicate canonical_record_digest"
            )
        canonical_record_digests.add(digest)
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

    if len(dataset_ids) > 1:
        raise ValueError("cross-corpus discovery input is blocked")

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
    speaker_basis: str | None,
    source_label: str,
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
        dataset_id = _validate_record_provenance(
            record,
            record_index=index,
            source_label=source_label,
            speaker_basis=speaker_basis,
            require_complete_evidence=False,
        )
        dataset_ids.add(dataset_id)
        if not record["eligible"]:
            continue
        speaker_id = record.get("source_speaker_id")
        if (
            not isinstance(speaker_id, str)
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
    unique_count = len(namespaced_keys) if speaker_basis is not None else 0
    if speaker_basis is None or namespaced_key_missing or deterministic_evidence_missing:
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
    for record in selected:
        for metric in COUNT_MAP_METRICS:
            if len(record["metric_cell_memberships"][metric]) != 1:
                raise ValueError(
                    "selected record must have exactly one membership cell for each "
                    f"count-map metric; count-map membership support is invalid: {metric}"
                )
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
    request, replacement_target = _validate_request(request)
    basis, reasons = _speaker_basis_status(request)
    selected, unique_count, dedup_digest, selection_reasons = _select_contributions(
        records,
        speaker_basis=basis,
        source_label=request["source_label"],
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
        _validate_count_map_support(aggregate, derived_counts)
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
    validated = validate_cohort_release(payload)
    if replacement_target is not None:
        _validate_fixed_cohort_replacement(
            validated,
            replacement_target,
            label="candidate",
        )
    return validated


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
    basis = payload["unique_speaker_basis"]
    if basis is not None:
        _validate_source_basis_pair(payload["source_label"], basis)
    if payload["dependency_keys"] != list(DEPENDENCY_KEYS):
        raise ValueError("CohortReleaseEvidenceV1 dependency keys mismatch")
    if (
        type(payload["max_contribution_per_speaker"]) is not int
        or payload["max_contribution_per_speaker"]
        != MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER
    ):
        raise ValueError("CohortReleaseEvidenceV1 contribution cap mismatch")
    _require_sha256_or_none(payload["dedup_evidence_digest"], "dedup_evidence_digest")
    if basis is None and (
        payload["eligible_record_count"] != 0
        or payload["unique_speaker_count"] != 0
        or payload["dedup_evidence_digest"] is not None
    ):
        raise ValueError(
            "basis-null evidence must have zero selected and unique speakers "
            "and null dedup evidence"
        )
    input_count = payload["input_record_count"]
    eligible_count = payload["eligible_record_count"]
    unique_count = payload["unique_speaker_count"]
    if not 0 <= eligible_count <= unique_count <= input_count:
        raise ValueError(
            "record counts must satisfy 0 <= eligible_record_count <= "
            "unique_speaker_count <= input_record_count"
        )
    dedup_digest = payload["dedup_evidence_digest"]
    if dedup_digest is None and eligible_count != 0:
        raise ValueError("null dedup evidence requires zero eligible records")
    if dedup_digest is not None and eligible_count != unique_count:
        raise ValueError(
            "non-null dedup evidence requires eligible and unique record counts to match"
        )
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
        if metric in SCALAR_METRICS and support != payload["eligible_record_count"]:
            raise ValueError(
                f"scalar metric {metric} support must equal eligible_record_count"
            )
    _validate_count_map_support(metrics, counts)
    for metric in COUNT_MAP_METRICS.intersection(metrics):
        if (
            sum(metrics[metric].values()) > payload["eligible_record_count"]
            or sum(counts[metric].values()) > payload["eligible_record_count"]
        ):
            raise ValueError(
                f"count-map metric {metric} total must not exceed eligible_record_count"
            )
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
        speaker_index = index % unique_speaker_count
        if dataset_manifest_id == CREMA_DATASET_ID:
            speaker_id = f"{1001 + speaker_index:04d}"
        elif dataset_manifest_id == AMI_DATASET_ID:
            speaker_id = f"MIO{16 + speaker_index:03d}"
        else:
            speaker_id = f"fixture-speaker-{speaker_index:03d}"
        timestamp = (start + timedelta(minutes=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        record = {
            "dataset_manifest_id": dataset_manifest_id,
            "source_speaker_id": speaker_id,
            "source_timestamp": timestamp,
            "eligible": True,
            "metric_cell_memberships": {
                "eligible_call_count": ["__scalar__"],
                "audio_analysis_availability_rate": ["__scalar__"],
                "audio_quality_bucket_counts": ["unavailable"],
                "abstention_rate": ["__scalar__"],
                "processing_latency_percentiles": ["p50", "p95"],
                "evidence_policy_version_counts": ["emotion-state-evidence-v1"],
            },
        }
        record["canonical_record_digest"] = canonical_record_digest(record)
        records.append(record)
    return records


def fixture_cross_corpus_records() -> list[dict[str, Any]]:
    return (
        fixture_records(
            5,
            5,
            dataset_manifest_id="synthetic-fixture-dataset-a-v1",
        )
        + fixture_records(
            5,
            5,
            dataset_manifest_id="synthetic-fixture-dataset-b-v1",
        )
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


def cohort_release_schema_descriptor() -> dict[str, Any]:
    return {
        "schema_id": "emotion-state-cohort-release-evidence-v1",
        "schema_version": 1,
        "contract_name": "CohortReleaseEvidenceV1",
        "description": RELEASE_SCOPE,
        "required_fields": [
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
        ],
        "allowed_source_labels": sorted(ALLOWED_SOURCE_LABELS),
        "allowed_speaker_bases": sorted(ALLOWED_SPEAKER_BASES),
        "reserved_disabled_speaker_basis": RESERVED_DISABLED_SPEAKER_BASE,
        "release_statuses": ["released", "suppressed"],
        "allowed_suppression_reason_codes": sorted(
            ALLOWED_SUPPRESSION_REASON_CODES
        ),
        "max_contribution_per_speaker": MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER,
        "minimum_unique_speakers": MIN_RELEASE_SPEAKERS,
        "minimum_unique_speakers_per_output_cell": MIN_RELEASE_SPEAKERS,
        "metric_allowlist_version": METRIC_ALLOWLIST_VERSION_V1,
        "metric_allowlist": list(METRIC_ALLOWLIST_V1),
        "false_constants": {
            field: False
            for field in BOOLEAN_BOUNDARY_FIELDS
        },
        "cross_corpus_identity_evidence_digest": None,
        "record_provenance": {
            "canonical_record_projection": CANONICAL_RECORD_PROJECTION,
            "approved_public_datasets": {
                CREMA_DATASET_ID: {
                    "source_label": "public-only",
                    "unique_speaker_basis": "public_dataset_actor_id",
                    "source_speaker_id_pattern": CREMA_ACTOR_ID_PATTERN_TEXT,
                },
                AMI_DATASET_ID: {
                    "source_label": "public-only",
                    "unique_speaker_basis": "public_dataset_participant_id",
                    "source_speaker_id_pattern": AMI_PARTICIPANT_ID_PATTERN_TEXT,
                },
            },
            "controlled_synthetic_fixture_dataset_ids": sorted(
                CONTROLLED_SYNTHETIC_FIXTURE_DATASET_IDS
            ),
            "synthetic_fixture_source_label": "synthetic-only",
            "synthetic_fixture_speaker_basis": "synthetic_fixture_speaker_id",
            "synthetic_fixture_speaker_id_pattern": (
                SYNTHETIC_FIXTURE_SPEAKER_ID_PATTERN_TEXT
            ),
            "structural_validation_authenticates_external_material": False,
        },
        "authoritative_history_boundary": {
            "history_order_semantics": "append_dependency_order",
            "max_authoritative_history_entries": (
                MAX_AUTHORITATIVE_HISTORY_ENTRIES
            ),
            "max_authoritative_history_canonical_bytes": (
                MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES
            ),
            "external_append_only_registry_required": True,
            "signed_sequence_authentication_implemented": False,
            "unrelated_root_relative_append_order_authenticated": False,
        },
        "notes": (
            "Only fixed closed windows, append-ordered whole-release replacement "
            "chains, contribution-capped cohort metrics, and cells supported by at "
            "least ten proven unique speakers may be serialized. Structural "
            "validation does not authenticate external dataset material or the "
            "external append-only release registry."
        ),
    }


def cohort_release_fixture_descriptor() -> dict[str, Any]:
    return {
        "fixture_id": "emotion-state-001-cohort-release-fixtures-v1",
        "schema_version": 1,
        "contract_name": "CohortReleaseEvidenceV1",
        "source_label": "synthetic-only",
        "description": RELEASE_SCOPE,
        "release_statuses": ["released", "suppressed"],
        "minimum_discovery_unique_speakers": MIN_DISCOVERY_SPEAKERS,
        "minimum_discovery_retained_turns": MIN_DISCOVERY_TURNS,
        "max_discovery_turns_per_speaker": MAX_DISCOVERY_TURNS_PER_SPEAKER,
        "max_authoritative_history_entries": MAX_AUTHORITATIVE_HISTORY_ENTRIES,
        "max_authoritative_history_canonical_bytes": (
            MAX_AUTHORITATIVE_HISTORY_CANONICAL_BYTES
        ),
        "minimum_release_unique_speakers": MIN_RELEASE_SPEAKERS,
        "minimum_unique_speakers_per_output_cell": MIN_RELEASE_SPEAKERS,
        "max_contribution_per_speaker": MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER,
        "scenarios": {
            "twelve_calls_four_speakers": {
                "record_count": 12,
                "unique_speaker_count": 4,
                "expected_release_status": "suppressed",
                "expected_reason_code": "minimum_unique_speakers_not_met",
            },
            "ten_calls_ten_speakers": {
                "record_count": 10,
                "unique_speaker_count": 10,
                "expected_release_status": "released",
            },
            "twenty_turns_five_speakers": {
                "record_count": 20,
                "unique_speaker_count": 5,
                "max_discovery_turns_per_speaker": 2,
                "discovery_floor_met": True,
                "release_floor_met": False,
                "expected_release_status": "suppressed",
                "expected_reason_code": "minimum_unique_speakers_not_met",
            },
            "duplicate_public_actor_ids": {
                "source_label": "public-only",
                "dataset_manifest_id": CREMA_DATASET_ID,
                "record_count": 12,
                "unique_speaker_count": 10,
                "unique_speaker_basis": "public_dataset_actor_id",
                "expected_contribution_count": 10,
                "expected_release_status": "released",
            },
            "cross_corpus_same_bare_id": {
                "dataset_manifest_ids": [
                    "synthetic-fixture-dataset-a-v1",
                    "synthetic-fixture-dataset-b-v1",
                ],
                "dataset_count": 2,
                "bare_id_count_per_dataset": 5,
                "namespaced_key_count": 10,
                "cross_corpus_identity_evidence_digest": None,
                "expected_release_status": "suppressed",
                "expected_reason_code": "cross_corpus_identity_not_proven",
            },
            "missing_speaker_basis": {
                "unique_speaker_basis": None,
                "expected_release_status": "suppressed",
                "expected_reason_code": "speaker_basis_missing",
            },
            "call_id_as_speaker": {
                "rejected_basis_values": ["call_id", "session_id", "turn_id"],
                "expected_result": "rejected",
            },
            "forbidden_identity_basis": {
                "rejected_basis_values": [
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
                ],
                "expected_result": "rejected",
            },
            "over_contribution": {
                "record_count": 12,
                "unique_speaker_count": 10,
                "max_contribution_per_speaker": 1,
                "expected_contribution_count": 10,
                "expected_release_status": "released",
                "selection_order": [
                    "dataset_manifest_id",
                    "source_speaker_id",
                    "source_timestamp",
                    "canonical_record_digest",
                ],
            },
            "sparse_output_cell": {
                "cell_unique_speaker_count": 9,
                "minimum_unique_speakers_per_output_cell": 10,
                "expected_release_status": "released",
                "expected_serialization": "omitted",
            },
            "overlapping_release": {
                "window_relationship": "overlapping",
                "expected_result": "rejected",
            },
            "valid_replacement": {
                "window_relationship": "replacement",
                "replacement_scope": "entire_prior_release",
                "binds_prior_canonical_digest": True,
                "preserves_exact_window": True,
                "preserves_metric_allowlist": True,
                "expected_release_status": "released",
            },
        },
        "private_data_access_allowed": False,
        "provider_operations_allowed": False,
        "runtime_influence_allowed": False,
    }


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
