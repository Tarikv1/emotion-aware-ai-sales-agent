from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

_IMPORT_ROOT = Path(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
)
_IMPORT_ROOT_TEXT = os.fspath(_IMPORT_ROOT)
_IMPORT_ROOT_KEY = os.path.normcase(_IMPORT_ROOT_TEXT)
sys.path[:] = [
    entry
    for entry in sys.path
    if os.path.normcase(os.path.abspath(entry or os.curdir)) != _IMPORT_ROOT_KEY
]
sys.path.insert(0, _IMPORT_ROOT_TEXT)

from scripts import emotion_state_phase_c1_contracts as phase_c1
from scripts import emotion_state_phase_c1_decision as decision


class RunnerError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


ROOT: Final = _IMPORT_ROOT
PROTOCOL_PATH: Final = (
    ROOT
    / "research"
    / "experiments"
    / "configs"
    / "emotion-state-004-phase-c1-discovery-protocol.json"
)
SEARCH_LEDGER_PATH: Final = (
    ROOT
    / "research"
    / "sources"
    / "emotion_state"
    / "phase_c1_search_ledger.json"
)
SOURCE_LEDGER_PATH: Final = (
    ROOT
    / "research"
    / "sources"
    / "emotion_state"
    / "phase_c1_source_evidence_ledger.json"
)
SOURCE_REVIEW_PATH: Final = (
    ROOT
    / "research"
    / "sources"
    / "emotion_state"
    / "phase_c1_source_review_receipt.json"
)

RESULT_SCHEMA_VERSION: Final = "EmotionStatePhaseC1AggregateResultV2"
SOURCE_LEDGER_SCHEMA_VERSION: Final = (
    "EmotionStatePhaseC1SourceEvidenceLedgerV1"
)
SOURCE_LEDGER_ENVELOPE_FIELDS: Final = frozenset(
    {
        "schema_version",
        "protocol_sha256",
        "search_ledger_sha256",
        "sources",
        "cards",
        "fallback_assessments",
    }
)
CHECKPOINT_ID: Final = (
    "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission"
)
PROTOCOL_ID: Final = "emotion-state-phase-c1-discovery-v1"
TARGET_SIGNALS: Final = (
    "hesitation",
    "frustration",
    "confusion",
    "interest",
    "disengagement",
)
MAX_DETAILED_CANDIDATES_PER_SIGNAL: Final = 20
MAX_DETAILED_FALLBACK_MATERIAL_CANDIDATES: Final = 10
MAX_DOCUMENTS_PER_SOURCE: Final = 5
MAX_AGGREGATE_RESULT_BYTES: Final = 512 * 1024
REASON_CODE_ORDER: Final = (
    "access_requires_login",
    "access_restricted",
    "license_incompatible",
    "ethical_use_incompatible",
    "acted_or_scripted",
    "mixed_unseparated_conversation",
    "proxy_construct",
    "target_label_absent",
    "conversation_level_only",
    "temporal_unit_incompatible",
    "single_rater",
    "self_report_label",
    "llm_generated_label",
    "reliability_upper_below_0_67",
    "source_identity_unverified",
    "authoritative_provenance_unverified",
    "access_unresolved",
    "license_unresolved",
    "ethical_use_unresolved",
    "conversation_status_unresolved",
    "directness_unresolved",
    "temporal_unit_unresolved",
    "observer_method_unresolved",
    "rater_count_unresolved",
    "reliability_metric_unapproved",
    "reliability_not_preadjudication",
    "reliability_unverifiable",
    "reliability_effective_sample_insufficient",
    "positive_support_below_93",
    "reliability_interval_uncertain",
    "published_positive_count_missing",
    "source_documentation_incomplete",
    "raw_annotation_rows_required",
    "search_query_incomplete",
    "query_result_truncated",
    "candidate_overflow",
    "citation_budget_incomplete",
    "annotation_fallback_feasible",
    "annotation_fallback_unresolved",
)
REJECTION_REASON_CODES: Final = frozenset(REASON_CODE_ORDER[:14])
UNRESOLVED_REASON_CODES: Final = frozenset(REASON_CODE_ORDER[14:33])
SEARCH_META_REASON_CODES: Final = frozenset(REASON_CODE_ORDER[33:37])
LIMITATIONS: Final = (
    "Observer labels measure perception, not hidden internal emotion.",
    "Language, culture, speaker, population, and domain bias remain.",
    "Public conversational corpora may not resemble sales calls.",
    "Recording modality and bounded context may change judgments.",
    "Rare signals may prevent reliable annotation or later evaluation.",
    (
        "License, consent, or incomplete documentation may leave a promising "
        "source unresolved."
    ),
    "Agreement does not prove construct truth.",
    "Partial admission does not validate the other signals.",
    (
        "No public-data result alone proves real-call, provider, latency, "
        "safety, conversion, or production behavior."
    ),
    (
        "Sparse source signatures and per-card categorical diagnostics may "
        "fingerprint public source configurations."
    ),
)
BOUNDARY_FIELDS: Final = (
    "audio_read",
    "annotation_rows_read",
    "customer_emotion_inferred",
    "dataset_material_read",
    "llm_labels_used",
    "model_evaluation_run",
    "participant_rows_read",
    "private_data_read",
    "provider_accessed",
    "runtime_modified",
    "search_result_text_persisted",
    "transcript_rows_read",
)
SEARCH_COUNT_FIELDS: Final = frozenset(
    {
        "direct_label_query_count",
        "fallback_material_query_count",
        "total_query_count",
        "complete_query_count",
        "incomplete_query_count",
        "truncated_query_count",
        "returned_discovery_record_count",
        "retained_candidate_record_count",
        "duplicate_discovery_record_count",
        "excluded_discovery_record_count",
        "unresolved_discovery_record_count",
        "detailed_candidate_count",
        "candidate_overflow_count",
        "backward_citation_record_count",
        "forward_citation_record_count",
        "unresolved_citation_record_count",
        "nonexhaustive_citation_stop_count",
        "search_complete",
    }
)
SOURCE_COUNT_FIELDS: Final = frozenset(
    {
        "source_count",
        "document_count",
        "existing_annotation_evidence_source_count",
        "fallback_material_candidate_source_count",
    }
)
CARD_STATUS_FIELDS: Final = frozenset(
    {"admissible", "rejected", "unresolved"}
)
PER_SIGNAL_FIELDS: Final = frozenset(
    {
        "signal",
        "decision",
        "admissible_evidence_card_sha256s",
        "rejected_card_count",
        "unresolved_card_count",
        "annotation_fallback",
        "fallback_material_status_counts",
        "reliability_diagnostics",
        "c2_eligible",
    }
)
FALLBACK_MATERIAL_STATUS_COUNT_FIELDS: Final = frozenset(
    {"feasible", "infeasible", "unresolved"}
)
RELIABILITY_DIAGNOSTIC_FIELDS: Final = frozenset(
    {
        "evidence_card_sha256",
        "source_signature_sha256",
        "claimed_status",
        "claimed_reason_codes",
        "definition_document_authoritative",
        "definition_document_public_without_login",
        "native_label_is_excluded_proxy",
        "annotation_modality",
        "construct_correspondence",
        "temporal_unit",
        "observer_method",
        "metric_id",
        "point_micros",
        "lower_95_micros",
        "upper_95_micros",
        "independent_rater_count",
        "rated_unit_count",
        "published_positive_count",
        "effective_sample_sufficient",
        "uncertain_or_unratable_rate_micros",
        "class_prevalence_micros",
        "positive_agreement_micros",
        "negative_agreement_micros",
        "preadjudication_disagreement_micros",
        "preadjudication",
        "verifiable",
    }
)
QUERY_LANE_COUNT_FIELDS: Final = frozenset(
    {"total", "complete", "incomplete", "truncated"}
)
DISPOSITION_COUNT_FIELDS: Final = frozenset(
    {"retained_candidate", "duplicate", "excluded", "unresolved"}
)
CITATION_LANE_FIELDS: Final = frozenset(
    {"disposition_counts", "stop_status"}
)
DIRECT_SEARCH_LANE_FIELDS: Final = frozenset(
    {
        "query_counts",
        "candidate_order_count",
        "candidate_overflow_count",
        "discovery_disposition_counts",
        "citations",
    }
)
FALLBACK_SEARCH_LANE_FIELDS: Final = frozenset(
    {
        "query_counts",
        "candidate_order_count",
        "candidate_overflow_count",
        "discovery_disposition_counts",
    }
)
SEARCH_LANE_FIELDS: Final = frozenset(
    {"direct_by_signal", "fallback_material"}
)
SOURCE_SIGNATURE_FIELDS: Final = frozenset(
    {
        "source_signature_sha256",
        "count",
        "direct_membership_by_signal",
        "fallback_material_membership",
        "existing_annotation_evidence_role",
        "fallback_material_candidate_role",
        "access_status",
        "license_status",
        "ethical_use_status",
        "conversation_status",
        "document_count",
        "document_category_mask",
    }
)
RESULT_FORBIDDEN_KEYS: Final = frozenset(
    {
        "annotation_row",
        "annotation_rows",
        "audio",
        "audio_path",
        "card_id",
        "customer_id",
        "feature",
        "features",
        "label_row",
        "label_rows",
        "model_metric",
        "native_label",
        "participant",
        "participant_id",
        "prediction",
        "probability",
        "source_id",
        "source_path",
        "source_title",
        "speaker_id",
        "title",
        "transcript",
        "transcript_text",
        "url",
        "utterance",
    }
)

_LOWER_GIT_ID_RE: Final = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE: Final = re.compile(r"^[0-9A-F]{64}$")
_OVERALL_DECISIONS: Final = (
    "proceed_full_to_c2",
    "proceed_partial_to_c2",
    "defer_c2",
    "stop_c2",
)
_SIGNAL_DECISIONS: Final = ("pass", "defer", "fail")
_FALLBACK_STATUSES: Final = ("feasible", "infeasible", "unresolved")
_EXHAUSTIVE_CITATION_STOPS: Final = frozenset(
    {"no_eligible_candidates", "source_list_exhausted"}
)
_SIGNALS_WITH_EXCLUDED_PROXIES: Final = frozenset(TARGET_SIGNALS)


def _raise_contract(exc: phase_c1.PhaseC1ContractError) -> RunnerError:
    return RunnerError(exc.code)


def _canonical_input_object(data: bytes, *, source: str) -> dict[str, object]:
    if type(data) is not bytes:
        raise RunnerError(f"{source}_bytes")
    try:
        payload = phase_c1.load_json_strict(data, source=source)
        if type(payload) is not dict:
            raise RunnerError(f"{source}_object")
        if phase_c1.canonical_json_bytes(payload) != data:
            raise RunnerError(f"{source}_canonical")
        return payload
    except phase_c1.PhaseC1ContractError as exc:
        raise _raise_contract(exc) from exc


def _json_value(value: object) -> object:
    if is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _card_sha256(card: phase_c1.PhaseC1EvidenceCardV1) -> str:
    return phase_c1.sha256_bytes(
        phase_c1.canonical_json_bytes(_json_value(card))
    )


def _source_card_hashes_by_signal(
    source_ledger_bytes: bytes,
    *,
    expected_sha256: str,
) -> Mapping[str, tuple[str, ...]]:
    if type(source_ledger_bytes) is not bytes:
        raise RunnerError("source_ledger_bytes")
    if phase_c1.sha256_bytes(source_ledger_bytes) != expected_sha256:
        raise RunnerError("source_ledger_hash")
    payload = _canonical_input_object(
        source_ledger_bytes,
        source="source_ledger",
    )
    ledger = _exact_dict(
        payload,
        SOURCE_LEDGER_ENVELOPE_FIELDS,
        code="source_ledger_fields",
    )
    if ledger["schema_version"] != SOURCE_LEDGER_SCHEMA_VERSION:
        raise RunnerError("source_ledger_schema")
    raw_cards = ledger["cards"]
    if type(raw_cards) is not list:
        raise RunnerError("source_ledger_cards")
    hashes_by_signal: dict[str, list[str]] = {
        signal: [] for signal in TARGET_SIGNALS
    }
    try:
        for raw_card in raw_cards:
            card = phase_c1.parse_evidence_card(raw_card)
            hashes_by_signal[card.signal].append(_card_sha256(card))
    except phase_c1.PhaseC1ContractError as exc:
        raise _raise_contract(exc) from exc
    return MappingProxyType(
        {
            signal: tuple(hashes_by_signal[signal])
            for signal in TARGET_SIGNALS
        }
    )


def _effective_sample_sufficient(
    diagnostic: Mapping[str, object],
) -> bool:
    raters = diagnostic["independent_rater_count"]
    rated = diagnostic["rated_unit_count"]
    positives = diagnostic["published_positive_count"]
    return (
        type(raters) is int
        and raters >= 2
        and type(rated) is int
        and rated > 0
        and type(positives) is int
        and positives >= 93
        and rated >= positives
    )


def _reliability_diagnostic(
    card: phase_c1.PhaseC1EvidenceCardV1,
    *,
    evidence_card_sha256: str,
    source: phase_c1.PhaseC1SourceReceiptV1,
    source_signature_sha256: str,
    protocol: phase_c1.PhaseC1ProtocolV1,
) -> dict[str, object]:
    reliability = card.reliability
    definition = next(
        document
        for document in source.documents
        if document.document_id == card.native_definition_document_id
    )
    construct = next(
        item
        for item in protocol.signal_constructs
        if item["signal"] == card.signal
    )
    diagnostic: dict[str, object] = {
        "evidence_card_sha256": evidence_card_sha256,
        "source_signature_sha256": source_signature_sha256,
        "claimed_status": card.claimed_status,
        "claimed_reason_codes": list(card.claimed_reason_codes),
        "definition_document_authoritative": definition.authoritative,
        "definition_document_public_without_login": (
            definition.public_without_login
        ),
        "native_label_is_excluded_proxy": (
            card.native_label in construct["excluded_proxies"]
        ),
        "annotation_modality": card.annotation_modality,
        "construct_correspondence": card.construct_correspondence,
        "temporal_unit": card.temporal_unit,
        "observer_method": card.observer_method,
        "metric_id": reliability.metric_id,
        "point_micros": reliability.point_micros,
        "lower_95_micros": reliability.lower_95_micros,
        "upper_95_micros": reliability.upper_95_micros,
        "independent_rater_count": card.independent_rater_count,
        "rated_unit_count": reliability.rated_unit_count,
        "published_positive_count": reliability.published_positive_count,
        "effective_sample_sufficient": False,
        "uncertain_or_unratable_rate_micros": (
            reliability.uncertain_or_unratable_rate_micros
        ),
        "class_prevalence_micros": reliability.class_prevalence_micros,
        "positive_agreement_micros": reliability.positive_agreement_micros,
        "negative_agreement_micros": reliability.negative_agreement_micros,
        "preadjudication_disagreement_micros": (
            reliability.preadjudication_disagreement_micros
        ),
        "preadjudication": reliability.preadjudication,
        "verifiable": reliability.verifiable,
    }
    diagnostic["effective_sample_sufficient"] = (
        _effective_sample_sufficient(diagnostic)
    )
    return diagnostic


def _count_reasons(
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
) -> dict[str, int]:
    counts = {reason: 0 for reason in protocol.reason_code_order}

    def add(reasons: tuple[str, ...]) -> None:
        for reason in dict.fromkeys(reasons):
            counts[reason] += 1

    for query in search_ledger.query_records:
        for record in query.discovery_records:
            if record.reason_code is not None:
                add((record.reason_code,))
    for record in search_ledger.citation_records:
        if record.reason_code is not None:
            add((record.reason_code,))
    for card in source_ledger.cards:
        add(card.claimed_reason_codes)
    for assessment in source_ledger.fallback_assessments:
        add(assessment.reason_codes)
    return counts


def _search_counts(
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
) -> dict[str, object]:
    direct_queries = tuple(
        query
        for query in search_ledger.query_records
        if query.query_kind == "direct_label_source"
    )
    fallback_queries = tuple(
        query
        for query in search_ledger.query_records
        if query.query_kind == "fallback_material"
    )
    discovery_records = tuple(
        record
        for query in search_ledger.query_records
        for record in query.discovery_records
    )
    detailed_candidates = tuple(
        dict.fromkeys(
            source_id
            for signal in protocol.target_signals
            for source_id in search_ledger.candidate_order_by_signal[signal]
        )
    )
    detailed_candidates = tuple(
        dict.fromkeys(
            detailed_candidates
            + search_ledger.fallback_material_candidate_order
        )
    )
    nonexhaustive_stops = sum(
        stop not in _EXHAUSTIVE_CITATION_STOPS
        for signal in protocol.target_signals
        for stop in (
            search_ledger.backward_citation_stop_by_signal[signal],
            search_ledger.forward_citation_stop_by_signal[signal],
        )
    )
    return {
        "direct_label_query_count": len(direct_queries),
        "fallback_material_query_count": len(fallback_queries),
        "total_query_count": len(search_ledger.query_records),
        "complete_query_count": sum(
            query.status == "complete"
            for query in search_ledger.query_records
        ),
        "incomplete_query_count": sum(
            query.status == "incomplete"
            for query in search_ledger.query_records
        ),
        "truncated_query_count": sum(
            query.truncated for query in search_ledger.query_records
        ),
        "returned_discovery_record_count": len(discovery_records),
        "retained_candidate_record_count": sum(
            record.disposition == "retained_candidate"
            for record in discovery_records
        ),
        "duplicate_discovery_record_count": sum(
            record.disposition == "duplicate"
            for record in discovery_records
        ),
        "excluded_discovery_record_count": sum(
            record.disposition == "excluded"
            for record in discovery_records
        ),
        "unresolved_discovery_record_count": sum(
            record.disposition == "unresolved"
            for record in discovery_records
        ),
        "detailed_candidate_count": len(detailed_candidates),
        "candidate_overflow_count": (
            sum(search_ledger.overflow_count_by_signal.values())
            + search_ledger.fallback_material_overflow_count
        ),
        "backward_citation_record_count": sum(
            record.direction == "backward"
            for record in search_ledger.citation_records
        ),
        "forward_citation_record_count": sum(
            record.direction == "forward"
            for record in search_ledger.citation_records
        ),
        "unresolved_citation_record_count": sum(
            record.disposition == "unresolved"
            for record in search_ledger.citation_records
        ),
        "nonexhaustive_citation_stop_count": nonexhaustive_stops,
        "search_complete": search_ledger.search_complete,
    }


def _disposition_counts(
    records: tuple[object, ...],
) -> dict[str, int]:
    return {
        disposition: sum(
            getattr(record, "disposition") == disposition
            for record in records
        )
        for disposition in phase_c1.DISCOVERY_DISPOSITIONS
    }


def _query_lane_counts(
    queries: tuple[phase_c1.PhaseC1QueryRecordV1, ...],
) -> dict[str, int]:
    return {
        "total": len(queries),
        "complete": sum(query.status == "complete" for query in queries),
        "incomplete": sum(
            query.status == "incomplete" for query in queries
        ),
        "truncated": sum(query.truncated for query in queries),
    }


def _search_lane_counts(
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
) -> dict[str, object]:
    direct: dict[str, object] = {}
    for signal in protocol.target_signals:
        queries = tuple(
            query
            for query in search_ledger.query_records
            if query.signal == signal
        )
        discovery = tuple(
            record for query in queries for record in query.discovery_records
        )
        citations: dict[str, object] = {}
        for direction in phase_c1.CITATION_DIRECTIONS:
            records = tuple(
                record
                for record in search_ledger.citation_records
                if record.signal == signal and record.direction == direction
            )
            stop = (
                search_ledger.backward_citation_stop_by_signal[signal]
                if direction == "backward"
                else search_ledger.forward_citation_stop_by_signal[signal]
            )
            citations[direction] = {
                "disposition_counts": _disposition_counts(records),
                "stop_status": stop,
            }
        direct[signal] = {
            "query_counts": _query_lane_counts(queries),
            "candidate_order_count": len(
                search_ledger.candidate_order_by_signal[signal]
            ),
            "candidate_overflow_count": (
                search_ledger.overflow_count_by_signal[signal]
            ),
            "discovery_disposition_counts": _disposition_counts(discovery),
            "citations": citations,
        }
    fallback_queries = tuple(
        query
        for query in search_ledger.query_records
        if query.query_kind == "fallback_material"
    )
    fallback_discovery = tuple(
        record
        for query in fallback_queries
        for record in query.discovery_records
    )
    return {
        "direct_by_signal": direct,
        "fallback_material": {
            "query_counts": _query_lane_counts(fallback_queries),
            "candidate_order_count": len(
                search_ledger.fallback_material_candidate_order
            ),
            "candidate_overflow_count": (
                search_ledger.fallback_material_overflow_count
            ),
            "discovery_disposition_counts": _disposition_counts(
                fallback_discovery
            ),
        },
    }


def _document_category_mask(
    source: phase_c1.PhaseC1SourceReceiptV1,
) -> int:
    mask = 0
    for document in source.documents:
        bit_index = (
            (2 if document.authoritative else 0)
            + (1 if document.public_without_login else 0)
        )
        mask |= 1 << bit_index
    return mask


def _source_signature_payload(
    source: phase_c1.PhaseC1SourceReceiptV1,
    *,
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
) -> dict[str, object]:
    return {
        "direct_membership_by_signal": {
            signal: (
                source.source_id
                in search_ledger.candidate_order_by_signal[signal]
            )
            for signal in protocol.target_signals
        },
        "fallback_material_membership": (
            source.source_id
            in search_ledger.fallback_material_candidate_order
        ),
        "existing_annotation_evidence_role": (
            "existing_annotation_evidence" in source.phase_c1_roles
        ),
        "fallback_material_candidate_role": (
            "fallback_material_candidate" in source.phase_c1_roles
        ),
        "access_status": source.access_status,
        "license_status": source.license_status,
        "ethical_use_status": source.ethical_use_status,
        "conversation_status": source.conversation_status,
        "document_count": len(source.documents),
        "document_category_mask": _document_category_mask(source),
    }


def _source_signature_counts(
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
    *,
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    entries: dict[str, dict[str, object]] = {}
    source_hashes: dict[str, str] = {}
    for source in source_ledger.sources:
        signature = _source_signature_payload(
            source,
            protocol=protocol,
            search_ledger=search_ledger,
        )
        digest = phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(signature)
        )
        source_hashes[source.source_id] = digest
        existing = entries.get(digest)
        if existing is None:
            entries[digest] = {
                "source_signature_sha256": digest,
                "count": 1,
                **signature,
            }
        else:
            if {
                key: value
                for key, value in existing.items()
                if key not in {"source_signature_sha256", "count"}
            } != signature:
                raise RunnerError("source_signature_collision")
            existing["count"] = int(existing["count"]) + 1
    return (
        [entries[digest] for digest in sorted(entries)],
        source_hashes,
    )


def _source_counts(
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
) -> dict[str, int]:
    return {
        "source_count": len(source_ledger.sources),
        "document_count": sum(
            len(source.documents) for source in source_ledger.sources
        ),
        "existing_annotation_evidence_source_count": sum(
            "existing_annotation_evidence" in source.phase_c1_roles
            for source in source_ledger.sources
        ),
        "fallback_material_candidate_source_count": sum(
            "fallback_material_candidate" in source.phase_c1_roles
            for source in source_ledger.sources
        ),
    }


def _project_phase_c1_result(
    *,
    head_commit: str,
    validator_blob_id: str,
    protocol_bytes: bytes,
    search_ledger_bytes: bytes,
    source_ledger_bytes: bytes,
    review_receipt_bytes: bytes,
) -> dict[str, object]:
    if (
        type(head_commit) is not str
        or _LOWER_GIT_ID_RE.fullmatch(head_commit) is None
        or type(validator_blob_id) is not str
        or _LOWER_GIT_ID_RE.fullmatch(validator_blob_id) is None
    ):
        raise RunnerError("implementation_identity")

    protocol_payload = _canonical_input_object(
        protocol_bytes,
        source="protocol",
    )
    search_payload = _canonical_input_object(
        search_ledger_bytes,
        source="search_ledger",
    )
    source_payload = _canonical_input_object(
        source_ledger_bytes,
        source="source_ledger",
    )
    review_payload = _canonical_input_object(
        review_receipt_bytes,
        source="source_review",
    )
    try:
        protocol = phase_c1.validate_discovery_protocol(protocol_payload)
        search_ledger = phase_c1.validate_search_ledger(
            search_payload,
            protocol=protocol,
        )
        source_ledger = phase_c1.validate_source_evidence_ledger(
            source_payload,
            protocol=protocol,
            search_ledger_bytes=search_ledger_bytes,
        )
        review_receipt = phase_c1.validate_source_review_receipt(
            review_payload,
            protocol=protocol,
            search_ledger_bytes=search_ledger_bytes,
            source_evidence_ledger_bytes=source_ledger_bytes,
        )
        projection = decision.project_phase_c1_admission(
            protocol=protocol,
            search_ledger=search_ledger,
            source_ledger=source_ledger,
            review_receipt=review_receipt,
        )
    except phase_c1.PhaseC1ContractError as exc:
        raise _raise_contract(exc) from exc

    if (
        protocol.checkpoint_id != CHECKPOINT_ID
        or protocol.protocol_id != PROTOCOL_ID
        or protocol.target_signals != TARGET_SIGNALS
        or protocol.reason_code_order != REASON_CODE_ORDER
    ):
        raise RunnerError("protocol_contract")

    card_sha256_by_id = {
        card.card_id: _card_sha256(card)
        for card in source_ledger.cards
    }
    signature_counts, source_signature_sha256_by_id = (
        _source_signature_counts(
            source_ledger,
            protocol=protocol,
            search_ledger=search_ledger,
        )
    )
    sources_by_id = {
        source.source_id: source for source in source_ledger.sources
    }
    cards_by_signal = {
        signal: tuple(
            card
            for card in source_ledger.cards
            if card.signal == signal
        )
        for signal in protocol.target_signals
    }
    signal_projection = {
        item.signal: item for item in projection.signal_decisions
    }
    fallback_material_status_counts_by_signal = {
        assessment.signal: {
            status: sum(
                material.status == status
                for material in assessment.material_evidence
            )
            for status in _FALLBACK_STATUSES
        }
        for assessment in source_ledger.fallback_assessments
    }
    per_signal: list[dict[str, object]] = []
    for signal in protocol.target_signals:
        item = signal_projection[signal]
        per_signal.append(
            {
                "signal": signal,
                "decision": item.decision,
                "admissible_evidence_card_sha256s": [
                    card_sha256_by_id[card_id]
                    for card_id in item.admissible_card_ids
                ],
                "rejected_card_count": item.rejected_card_count,
                "unresolved_card_count": item.unresolved_card_count,
                "annotation_fallback": item.annotation_fallback,
                "fallback_material_status_counts": (
                    fallback_material_status_counts_by_signal[signal]
                ),
                "reliability_diagnostics": [
                    _reliability_diagnostic(
                        card,
                        evidence_card_sha256=card_sha256_by_id[
                            card.card_id
                        ],
                        source=sources_by_id[card.source_id],
                        source_signature_sha256=(
                            source_signature_sha256_by_id[card.source_id]
                        ),
                        protocol=protocol,
                    )
                    for card in cards_by_signal[signal]
                ],
                "c2_eligible": item.c2_eligible,
            }
        )

    status_counts = {
        status: sum(
            item.status == status
            for item in projection.candidate_dispositions
        )
        for status in ("admissible", "rejected", "unresolved")
    }
    result: dict[str, object] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_ID,
        "protocol_id": PROTOCOL_ID,
        "target_signals": list(protocol.target_signals),
        "implementation_head": head_commit,
        "validator_blob_id": validator_blob_id,
        "protocol_sha256": phase_c1.sha256_bytes(protocol_bytes),
        "search_ledger_sha256": phase_c1.sha256_bytes(
            search_ledger_bytes
        ),
        "source_evidence_ledger_sha256": phase_c1.sha256_bytes(
            source_ledger_bytes
        ),
        "source_review_receipt_sha256": phase_c1.sha256_bytes(
            review_receipt_bytes
        ),
        "aggregate_content_sha256": "",
        "search_counts": _search_counts(protocol, search_ledger),
        "search_lane_counts": _search_lane_counts(
            protocol,
            search_ledger,
        ),
        "source_counts": _source_counts(source_ledger),
        "source_signature_counts": signature_counts,
        "card_counts_by_status": status_counts,
        "reason_code_counts": _count_reasons(
            protocol,
            search_ledger,
            source_ledger,
        ),
        "per_signal": per_signal,
        "overall_decision": projection.overall_decision,
        "c2_eligible_signals": list(projection.c2_eligible_signals),
        "boundary": {field: False for field in BOUNDARY_FIELDS},
        "limitations": list(LIMITATIONS),
        "runtime_approved": False,
    }
    result["aggregate_content_sha256"] = phase_c1.sha256_bytes(
        phase_c1.canonical_json_bytes(result)
    )
    if len(phase_c1.canonical_json_bytes(result)) > MAX_AGGREGATE_RESULT_BYTES:
        raise RunnerError("result_size")
    return result


def build_phase_c1_result(
    *,
    head_commit: str,
    validator_blob_id: str,
    protocol_bytes: bytes,
    search_ledger_bytes: bytes,
    source_ledger_bytes: bytes,
    review_receipt_bytes: bytes,
) -> dict[str, object]:
    result = _project_phase_c1_result(
        head_commit=head_commit,
        validator_blob_id=validator_blob_id,
        protocol_bytes=protocol_bytes,
        search_ledger_bytes=search_ledger_bytes,
        source_ledger_bytes=source_ledger_bytes,
        review_receipt_bytes=review_receipt_bytes,
    )
    validate_phase_c1_result_payload(
        result,
        protocol_bytes=protocol_bytes,
        search_ledger_bytes=search_ledger_bytes,
        source_ledger_bytes=source_ledger_bytes,
        review_receipt_bytes=review_receipt_bytes,
    )
    return result


def _forbidden_content(value: object) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if (
                isinstance(key, str)
                and key.casefold() in RESULT_FORBIDDEN_KEYS
            ):
                raise RunnerError("forbidden_content")
            _forbidden_content(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _forbidden_content(child)


def _exact_dict(
    value: object,
    expected_fields: frozenset[str],
    *,
    code: str,
) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != expected_fields:
        raise RunnerError(code)
    return value


def _nonnegative_int(value: object, *, code: str) -> int:
    if type(value) is not int or value < 0:
        raise RunnerError(code)
    return value


def _optional_positive_int(value: object, *, code: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value <= 0:
        raise RunnerError(code)
    return value


def _optional_millionths(value: object, *, code: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 1_000_000:
        raise RunnerError(code)
    return value


def _optional_alpha_millionths(
    value: object,
    *,
    code: str,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not -1_000_000 <= value <= 1_000_000:
        raise RunnerError(code)
    return value


def _sha256(value: object, *, code: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise RunnerError(code)
    return value


def _validate_search_counts(value: object) -> dict[str, object]:
    counts = _exact_dict(
        value,
        SEARCH_COUNT_FIELDS,
        code="search_counts",
    )
    if type(counts["search_complete"]) is not bool:
        raise RunnerError("search_counts")
    numeric = {
        field: _nonnegative_int(count, code="search_counts")
        for field, count in counts.items()
        if field != "search_complete"
    }
    candidate_record_count = (
        numeric["detailed_candidate_count"]
        + numeric["candidate_overflow_count"]
    )
    resolved_citation_record_count = (
        numeric["backward_citation_record_count"]
        + numeric["forward_citation_record_count"]
        - numeric["unresolved_citation_record_count"]
    )
    minimum_retained_citation_record_count = max(
        0,
        candidate_record_count
        - numeric["retained_candidate_record_count"],
    )
    nonduplicate_discovery_record_count = (
        numeric["returned_discovery_record_count"]
        - numeric["duplicate_discovery_record_count"]
    )
    if (
        numeric["direct_label_query_count"] != 80
        or numeric["fallback_material_query_count"] != 8
        or numeric["total_query_count"] != 88
        or numeric["complete_query_count"]
        + numeric["incomplete_query_count"]
        != 88
        or numeric["truncated_query_count"]
        > numeric["complete_query_count"]
        or numeric["returned_discovery_record_count"]
        != sum(
            numeric[field]
            for field in (
                "retained_candidate_record_count",
                "duplicate_discovery_record_count",
                "excluded_discovery_record_count",
                "unresolved_discovery_record_count",
            )
        )
        or numeric["unresolved_citation_record_count"]
        > (
            numeric["backward_citation_record_count"]
            + numeric["forward_citation_record_count"]
        )
        or numeric["returned_discovery_record_count"]
        > numeric["complete_query_count"] * 25
        or numeric["backward_citation_record_count"] > 5 * 5
        or numeric["forward_citation_record_count"] > 5 * 5
        or numeric["detailed_candidate_count"] > 5 * 20 + 10
        or (
            numeric["candidate_overflow_count"] > 0
            and numeric["detailed_candidate_count"]
            < MAX_DETAILED_FALLBACK_MATERIAL_CANDIDATES
        )
        or (
            numeric["duplicate_discovery_record_count"] > 0
            and nonduplicate_discovery_record_count == 0
        )
        or minimum_retained_citation_record_count
        > resolved_citation_record_count
        or numeric["nonexhaustive_citation_stop_count"] > 10
        or counts["search_complete"]
        != (
            numeric["incomplete_query_count"] == 0
            and numeric["truncated_query_count"] == 0
            and numeric["nonexhaustive_citation_stop_count"] == 0
        )
    ):
        raise RunnerError("search_counts")
    return counts


def _validate_source_counts(
    value: object,
    *,
    detailed_candidate_count: int,
) -> dict[str, object]:
    counts = _exact_dict(
        value,
        SOURCE_COUNT_FIELDS,
        code="source_counts",
    )
    parsed = {
        field: _nonnegative_int(count, code="source_counts")
        for field, count in counts.items()
    }
    if (
        parsed["source_count"] != detailed_candidate_count
        or parsed["document_count"] < parsed["source_count"]
        or parsed["document_count"]
        > parsed["source_count"] * MAX_DOCUMENTS_PER_SOURCE
        or parsed["existing_annotation_evidence_source_count"]
        > parsed["source_count"]
        or parsed["fallback_material_candidate_source_count"]
        > parsed["source_count"]
        or (
            parsed["existing_annotation_evidence_source_count"]
            + parsed["fallback_material_candidate_source_count"]
            < parsed["source_count"]
        )
    ):
        raise RunnerError("source_counts")
    return counts


def _validate_query_lane_counts(
    value: object,
    *,
    expected_total: int,
) -> dict[str, int]:
    counts = _exact_dict(
        value,
        QUERY_LANE_COUNT_FIELDS,
        code="search_lane_counts",
    )
    parsed = {
        field: _nonnegative_int(count, code="search_lane_counts")
        for field, count in counts.items()
    }
    if (
        parsed["total"] != expected_total
        or parsed["complete"] + parsed["incomplete"] != expected_total
        or parsed["truncated"] > parsed["complete"]
    ):
        raise RunnerError("search_lane_counts")
    return parsed


def _validate_disposition_counts(value: object) -> dict[str, int]:
    counts = _exact_dict(
        value,
        DISPOSITION_COUNT_FIELDS,
        code="search_lane_counts",
    )
    return {
        field: _nonnegative_int(count, code="search_lane_counts")
        for field, count in counts.items()
    }


def _validate_search_lane_counts(
    value: object,
    *,
    search_counts: Mapping[str, object],
) -> tuple[
    dict[str, dict[str, object]],
    dict[str, object],
    dict[str, bool],
]:
    lanes = _exact_dict(
        value,
        SEARCH_LANE_FIELDS,
        code="search_lane_counts",
    )
    raw_direct = _exact_dict(
        lanes["direct_by_signal"],
        frozenset(TARGET_SIGNALS),
        code="search_lane_counts",
    )
    direct: dict[str, dict[str, object]] = {}
    aggregate_discovery = {
        disposition: 0 for disposition in phase_c1.DISCOVERY_DISPOSITIONS
    }
    aggregate_citations = {
        direction: {
            disposition: 0
            for disposition in phase_c1.DISCOVERY_DISPOSITIONS
        }
        for direction in phase_c1.CITATION_DIRECTIONS
    }
    nonexhaustive_stops = 0
    for signal in TARGET_SIGNALS:
        lane = _exact_dict(
            raw_direct[signal],
            DIRECT_SEARCH_LANE_FIELDS,
            code="search_lane_counts",
        )
        queries = _validate_query_lane_counts(
            lane["query_counts"],
            expected_total=16,
        )
        candidate_count = _nonnegative_int(
            lane["candidate_order_count"],
            code="search_lane_counts",
        )
        overflow = _nonnegative_int(
            lane["candidate_overflow_count"],
            code="search_lane_counts",
        )
        if candidate_count > MAX_DETAILED_CANDIDATES_PER_SIGNAL:
            raise RunnerError("search_lane_counts")
        discovery = _validate_disposition_counts(
            lane["discovery_disposition_counts"]
        )
        if (
            sum(discovery.values()) > queries["complete"] * 25
            or (
                overflow > 0
                and candidate_count != MAX_DETAILED_CANDIDATES_PER_SIGNAL
            )
            or (
                discovery["duplicate"] > 0
                and sum(
                    discovery[disposition]
                    for disposition in (
                        "retained_candidate",
                        "excluded",
                        "unresolved",
                    )
                )
                == 0
            )
        ):
            raise RunnerError("search_lane_counts")
        raw_citations = _exact_dict(
            lane["citations"],
            frozenset(phase_c1.CITATION_DIRECTIONS),
            code="search_lane_counts",
        )
        parsed_citations: dict[str, dict[str, object]] = {}
        anchor_available = sum(
            discovery[disposition]
            for disposition in ("retained_candidate", "excluded", "unresolved")
        ) > 0
        for direction in phase_c1.CITATION_DIRECTIONS:
            citation = _exact_dict(
                raw_citations[direction],
                CITATION_LANE_FIELDS,
                code="search_lane_counts",
            )
            dispositions = _validate_disposition_counts(
                citation["disposition_counts"]
            )
            if sum(dispositions.values()) > 5:
                raise RunnerError("search_lane_counts")
            nonduplicate = sum(
                dispositions[item]
                for item in ("retained_candidate", "excluded", "unresolved")
            )
            if (
                dispositions["duplicate"] > 0
                and not anchor_available
                and nonduplicate == 0
            ):
                raise RunnerError("search_lane_counts")
            stop = citation["stop_status"]
            if stop not in phase_c1.CITATION_STOP_STATUSES:
                raise RunnerError("search_lane_counts")
            if stop == "no_eligible_candidates" and sum(
                dispositions.values()
            ) != 0:
                raise RunnerError("search_lane_counts")
            if stop not in _EXHAUSTIVE_CITATION_STOPS:
                nonexhaustive_stops += 1
            if nonduplicate > 0:
                anchor_available = True
            parsed_citations[direction] = {
                "disposition_counts": dispositions,
                "stop_status": stop,
            }
            for disposition, count in dispositions.items():
                aggregate_citations[direction][disposition] += count
        retained_supply = (
            discovery["retained_candidate"]
            + sum(
                parsed_citations[direction]["disposition_counts"][
                    "retained_candidate"
                ]
                for direction in phase_c1.CITATION_DIRECTIONS
            )
        )
        if retained_supply != candidate_count + overflow:
            raise RunnerError("search_lane_counts")
        for disposition, count in discovery.items():
            aggregate_discovery[disposition] += count
        direct[signal] = {
            "query_counts": queries,
            "candidate_order_count": candidate_count,
            "candidate_overflow_count": overflow,
            "discovery_disposition_counts": discovery,
            "citations": parsed_citations,
        }

    fallback_lane = _exact_dict(
        lanes["fallback_material"],
        FALLBACK_SEARCH_LANE_FIELDS,
        code="search_lane_counts",
    )
    fallback_queries = _validate_query_lane_counts(
        fallback_lane["query_counts"],
        expected_total=8,
    )
    fallback_candidate_count = _nonnegative_int(
        fallback_lane["candidate_order_count"],
        code="search_lane_counts",
    )
    fallback_overflow = _nonnegative_int(
        fallback_lane["candidate_overflow_count"],
        code="search_lane_counts",
    )
    if fallback_candidate_count > MAX_DETAILED_FALLBACK_MATERIAL_CANDIDATES:
        raise RunnerError("search_lane_counts")
    fallback_discovery = _validate_disposition_counts(
        fallback_lane["discovery_disposition_counts"]
    )
    if (
        sum(fallback_discovery.values()) > fallback_queries["complete"] * 25
        or (
            fallback_overflow > 0
            and fallback_candidate_count
            != MAX_DETAILED_FALLBACK_MATERIAL_CANDIDATES
        )
        or (
            fallback_discovery["duplicate"] > 0
            and sum(
                fallback_discovery[disposition]
                for disposition in (
                    "retained_candidate",
                    "excluded",
                    "unresolved",
                )
            )
            == 0
        )
    ):
        raise RunnerError("search_lane_counts")
    if (
        fallback_discovery["retained_candidate"]
        != fallback_candidate_count + fallback_overflow
    ):
        raise RunnerError("search_lane_counts")
    for disposition, count in fallback_discovery.items():
        aggregate_discovery[disposition] += count
    fallback: dict[str, object] = {
        "query_counts": fallback_queries,
        "candidate_order_count": fallback_candidate_count,
        "candidate_overflow_count": fallback_overflow,
        "discovery_disposition_counts": fallback_discovery,
    }

    if (
        search_counts["direct_label_query_count"]
        != sum(
            lane["query_counts"]["total"] for lane in direct.values()
        )
        or search_counts["fallback_material_query_count"]
        != fallback_queries["total"]
        or search_counts["complete_query_count"]
        != (
            sum(
                lane["query_counts"]["complete"]
                for lane in direct.values()
            )
            + fallback_queries["complete"]
        )
        or search_counts["incomplete_query_count"]
        != (
            sum(
                lane["query_counts"]["incomplete"]
                for lane in direct.values()
            )
            + fallback_queries["incomplete"]
        )
        or search_counts["truncated_query_count"]
        != (
            sum(
                lane["query_counts"]["truncated"]
                for lane in direct.values()
            )
            + fallback_queries["truncated"]
        )
        or search_counts["returned_discovery_record_count"]
        != sum(aggregate_discovery.values())
        or search_counts["retained_candidate_record_count"]
        != aggregate_discovery["retained_candidate"]
        or search_counts["duplicate_discovery_record_count"]
        != aggregate_discovery["duplicate"]
        or search_counts["excluded_discovery_record_count"]
        != aggregate_discovery["excluded"]
        or search_counts["unresolved_discovery_record_count"]
        != aggregate_discovery["unresolved"]
        or search_counts["candidate_overflow_count"]
        != (
            sum(
                lane["candidate_overflow_count"]
                for lane in direct.values()
            )
            + fallback_overflow
        )
        or search_counts["backward_citation_record_count"]
        != sum(aggregate_citations["backward"].values())
        or search_counts["forward_citation_record_count"]
        != sum(aggregate_citations["forward"].values())
        or search_counts["unresolved_citation_record_count"]
        != (
            aggregate_citations["backward"]["unresolved"]
            + aggregate_citations["forward"]["unresolved"]
        )
        or search_counts["nonexhaustive_citation_stop_count"]
        != nonexhaustive_stops
    ):
        raise RunnerError("search_lane_counts")

    query_search_complete = (
        all(
            lane["query_counts"]["incomplete"] == 0
            and lane["query_counts"]["truncated"] == 0
            for lane in direct.values()
        )
        and fallback_queries["incomplete"] == 0
        and fallback_queries["truncated"] == 0
        and nonexhaustive_stops == 0
    )
    if search_counts["search_complete"] != query_search_complete:
        raise RunnerError("search_lane_counts")
    fallback_ready = (
        fallback_queries["incomplete"] == 0
        and fallback_queries["truncated"] == 0
    )
    fallback_unresolved = fallback_discovery["unresolved"] > 0
    fail_ready: dict[str, bool] = {}
    for signal, lane in direct.items():
        fail_ready[signal] = (
            lane["query_counts"]["incomplete"] == 0
            and lane["query_counts"]["truncated"] == 0
            and fallback_ready
            and all(
                lane["citations"][direction]["stop_status"]
                in _EXHAUSTIVE_CITATION_STOPS
                for direction in phase_c1.CITATION_DIRECTIONS
            )
            and lane["discovery_disposition_counts"]["unresolved"] == 0
            and all(
                lane["citations"][direction]["disposition_counts"][
                    "unresolved"
                ]
                == 0
                for direction in phase_c1.CITATION_DIRECTIONS
            )
            and not fallback_unresolved
            and lane["candidate_overflow_count"] == 0
            and fallback_overflow == 0
        )
    return direct, fallback, fail_ready


def _validate_source_signature_counts(
    value: object,
    *,
    source_counts: Mapping[str, object],
    search_counts: Mapping[str, object],
    direct_lanes: Mapping[str, Mapping[str, object]],
    fallback_lane: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    if type(value) is not list:
        raise RunnerError("source_signature_counts")
    parsed: dict[str, dict[str, object]] = {}
    source_total = 0
    document_total = 0
    role_totals = {
        "existing_annotation_evidence_role": 0,
        "fallback_material_candidate_role": 0,
    }
    membership_totals = {signal: 0 for signal in TARGET_SIGNALS}
    fallback_membership_total = 0
    for raw_entry in value:
        entry = _exact_dict(
            raw_entry,
            SOURCE_SIGNATURE_FIELDS,
            code="source_signature_counts",
        )
        digest = _sha256(
            entry["source_signature_sha256"],
            code="source_signature_counts",
        )
        if digest in parsed:
            raise RunnerError("source_signature_counts")
        count = _nonnegative_int(
            entry["count"],
            code="source_signature_counts",
        )
        if count == 0:
            raise RunnerError("source_signature_counts")
        membership = _exact_dict(
            entry["direct_membership_by_signal"],
            frozenset(TARGET_SIGNALS),
            code="source_signature_counts",
        )
        if any(type(membership[signal]) is not bool for signal in TARGET_SIGNALS):
            raise RunnerError("source_signature_counts")
        boolean_fields = (
            "fallback_material_membership",
            "existing_annotation_evidence_role",
            "fallback_material_candidate_role",
        )
        if any(type(entry[field]) is not bool for field in boolean_fields):
            raise RunnerError("source_signature_counts")
        if (
            entry["access_status"] not in phase_c1.ACCESS_STATUSES
            or entry["license_status"] not in phase_c1.LICENSE_STATUSES
            or entry["ethical_use_status"]
            not in phase_c1.ETHICAL_USE_STATUSES
            or entry["conversation_status"]
            not in phase_c1.CONVERSATION_STATUSES
        ):
            raise RunnerError("source_signature_counts")
        document_count = _nonnegative_int(
            entry["document_count"],
            code="source_signature_counts",
        )
        mask = entry["document_category_mask"]
        if (
            type(mask) is not int
            or not 1 <= mask <= 0b1111
            or not 1 <= document_count <= MAX_DOCUMENTS_PER_SOURCE
            or mask.bit_count() > document_count
        ):
            raise RunnerError("source_signature_counts")
        if (
            entry["access_status"] == "login_required"
            and mask & 0b1010
        ):
            raise RunnerError("source_signature_counts")
        if (
            any(membership.values())
            and not entry["existing_annotation_evidence_role"]
        ):
            raise RunnerError("source_signature_counts")
        if (
            entry["fallback_material_membership"]
            and not entry["fallback_material_candidate_role"]
        ):
            raise RunnerError("source_signature_counts")
        signature = {
            key: item
            for key, item in entry.items()
            if key not in {"source_signature_sha256", "count"}
        }
        if digest != phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(signature)
        ):
            raise RunnerError("source_signature_counts")
        source_total += count
        document_total += count * document_count
        for field in role_totals:
            role_totals[field] += count * int(entry[field])
        for signal in TARGET_SIGNALS:
            membership_totals[signal] += count * int(membership[signal])
        fallback_membership_total += count * int(
            entry["fallback_material_membership"]
        )
        parsed[digest] = entry
    if list(parsed) != sorted(parsed):
        raise RunnerError("source_signature_counts")
    detailed_membership_total = sum(
        entry["count"]
        for entry in parsed.values()
        if (
            any(entry["direct_membership_by_signal"].values())
            or entry["fallback_material_membership"]
        )
    )
    if (
        source_total != source_counts["source_count"]
        or document_total != source_counts["document_count"]
        or role_totals["existing_annotation_evidence_role"]
        != source_counts["existing_annotation_evidence_source_count"]
        or role_totals["fallback_material_candidate_role"]
        != source_counts["fallback_material_candidate_source_count"]
        or any(
            membership_totals[signal]
            != direct_lanes[signal]["candidate_order_count"]
            for signal in TARGET_SIGNALS
        )
        or fallback_membership_total
        != fallback_lane["candidate_order_count"]
        or detailed_membership_total
        != search_counts["detailed_candidate_count"]
    ):
        raise RunnerError("source_signature_counts")
    return parsed


def _validate_diagnostic(
    value: object,
    *,
    signal: str,
    signatures: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    diagnostic = _exact_dict(
        value,
        RELIABILITY_DIAGNOSTIC_FIELDS,
        code="reliability_diagnostics",
    )
    _sha256(
        diagnostic["evidence_card_sha256"],
        code="reliability_diagnostics",
    )
    source_signature_sha256 = _sha256(
        diagnostic["source_signature_sha256"],
        code="reliability_diagnostics",
    )
    signature = signatures.get(source_signature_sha256)
    if signature is None:
        raise RunnerError("reliability_diagnostics")
    if diagnostic["claimed_status"] not in (
        "admissible",
        "rejected",
        "unresolved",
    ):
        raise RunnerError("reliability_diagnostics")
    reasons = diagnostic["claimed_reason_codes"]
    if (
        type(reasons) is not list
        or any(reason not in REASON_CODE_ORDER for reason in reasons)
        or reasons
        != [reason for reason in REASON_CODE_ORDER if reason in reasons]
    ):
        raise RunnerError("reliability_diagnostics")
    for field in (
        "definition_document_authoritative",
        "definition_document_public_without_login",
        "native_label_is_excluded_proxy",
        "preadjudication",
        "verifiable",
    ):
        if type(diagnostic[field]) is not bool:
            raise RunnerError("reliability_diagnostics")
    if (
        diagnostic["annotation_modality"]
        not in phase_c1.ANNOTATION_MODALITIES
        or diagnostic["construct_correspondence"]
        not in phase_c1.CONSTRUCT_CORRESPONDENCE_VALUES
        or diagnostic["temporal_unit"] not in phase_c1.TEMPORAL_UNITS
        or diagnostic["observer_method"] not in phase_c1.OBSERVER_METHODS
    ):
        raise RunnerError("reliability_diagnostics")
    document_bit_index = (
        (
            2
            if diagnostic["definition_document_authoritative"]
            else 0
        )
        + (
            1
            if diagnostic["definition_document_public_without_login"]
            else 0
        )
    )
    if not (
        signature["document_category_mask"] & (1 << document_bit_index)
    ):
        raise RunnerError("reliability_diagnostics")
    if (
        diagnostic["native_label_is_excluded_proxy"]
        and signal not in _SIGNALS_WITH_EXCLUDED_PROXIES
    ):
        raise RunnerError("reliability_diagnostics")
    if diagnostic["metric_id"] != "krippendorff_alpha":
        raise RunnerError("reliability_diagnostics")
    for field in (
        "point_micros",
        "lower_95_micros",
        "upper_95_micros",
    ):
        _optional_alpha_millionths(
            diagnostic[field],
            code="reliability_diagnostics",
        )
    for field in (
        "uncertain_or_unratable_rate_micros",
        "class_prevalence_micros",
        "positive_agreement_micros",
        "negative_agreement_micros",
        "preadjudication_disagreement_micros",
    ):
        _optional_millionths(
            diagnostic[field],
            code="reliability_diagnostics",
        )
    for field in (
        "independent_rater_count",
        "rated_unit_count",
        "published_positive_count",
    ):
        _optional_positive_int(
            diagnostic[field],
            code="reliability_diagnostics",
        )
    intervals = (
        diagnostic["lower_95_micros"],
        diagnostic["point_micros"],
        diagnostic["upper_95_micros"],
    )
    present_intervals = tuple(
        value for value in intervals if value is not None
    )
    if (
        len(present_intervals) > 1
        and present_intervals != tuple(sorted(present_intervals))
    ):
        raise RunnerError("reliability_diagnostics")
    if (
        diagnostic["rated_unit_count"] is not None
        and diagnostic["published_positive_count"] is not None
        and diagnostic["published_positive_count"]
        > diagnostic["rated_unit_count"]
    ):
        raise RunnerError("reliability_diagnostics")
    if (
        type(diagnostic["effective_sample_sufficient"]) is not bool
        or diagnostic["effective_sample_sufficient"]
        != _effective_sample_sufficient(diagnostic)
    ):
        raise RunnerError("reliability_diagnostics")
    return diagnostic


def _derived_diagnostic_disposition(
    diagnostic: Mapping[str, object],
    signature: Mapping[str, object],
) -> tuple[str, tuple[str, ...]]:
    rejected: set[str] = set()
    unresolved: set[str] = set()
    if not diagnostic["definition_document_authoritative"]:
        unresolved.add("authoritative_provenance_unverified")
    if not diagnostic["definition_document_public_without_login"]:
        unresolved.add("access_unresolved")
    if diagnostic["native_label_is_excluded_proxy"]:
        rejected.add("proxy_construct")
    if signature["access_status"] == "login_required":
        rejected.add("access_requires_login")
    elif signature["access_status"] == "restricted":
        rejected.add("access_restricted")
    elif signature["access_status"] == "unresolved":
        unresolved.add("access_unresolved")
    if signature["license_status"] == "incompatible":
        rejected.add("license_incompatible")
    elif signature["license_status"] == "unresolved":
        unresolved.add("license_unresolved")
    if signature["ethical_use_status"] == "incompatible":
        rejected.add("ethical_use_incompatible")
    elif signature["ethical_use_status"] == "unresolved":
        unresolved.add("ethical_use_unresolved")
    if signature["conversation_status"] == "acted_or_scripted":
        rejected.add("acted_or_scripted")
    elif signature["conversation_status"] == "mixed_unseparated":
        rejected.add("mixed_unseparated_conversation")
    elif signature["conversation_status"] == "unresolved":
        unresolved.add("conversation_status_unresolved")
    if diagnostic["construct_correspondence"] == "proxy_construct":
        rejected.add("proxy_construct")
    elif diagnostic["construct_correspondence"] == "target_absent":
        rejected.add("target_label_absent")
    elif diagnostic["construct_correspondence"] != "direct_target_construct":
        unresolved.add("directness_unresolved")
    if diagnostic["annotation_modality"] == "unresolved":
        unresolved.add("source_documentation_incomplete")
    if diagnostic["temporal_unit"] == "conversation":
        rejected.add("conversation_level_only")
    elif diagnostic["temporal_unit"] == "other":
        rejected.add("temporal_unit_incompatible")
    elif diagnostic["temporal_unit"] == "unresolved":
        unresolved.add("temporal_unit_unresolved")
    if diagnostic["observer_method"] == "self_report":
        rejected.add("self_report_label")
    elif diagnostic["observer_method"] == "llm_generated":
        rejected.add("llm_generated_label")
    elif diagnostic["observer_method"] == "automated_proxy":
        rejected.add("proxy_construct")
    elif diagnostic["observer_method"] == "adjudicated_only_human_label":
        unresolved.add("reliability_not_preadjudication")
    elif diagnostic["observer_method"] == "unresolved":
        unresolved.add("observer_method_unresolved")
    raters = diagnostic["independent_rater_count"]
    if raters is None:
        unresolved.add("rater_count_unresolved")
    elif raters < 2:
        rejected.add("single_rater")
    if rejected:
        return (
            "rejected",
            tuple(code for code in REASON_CODE_ORDER if code in rejected),
        )
    if unresolved:
        return (
            "unresolved",
            tuple(code for code in REASON_CODE_ORDER if code in unresolved),
        )

    reliability_reasons: set[str] = set()
    if not diagnostic["preadjudication"]:
        reliability_reasons.add("reliability_not_preadjudication")
    if not diagnostic["verifiable"]:
        reliability_reasons.add("reliability_unverifiable")
    rated = diagnostic["rated_unit_count"]
    positives = diagnostic["published_positive_count"]
    if rated is None:
        reliability_reasons.add(
            "reliability_effective_sample_insufficient"
        )
    if positives is None:
        reliability_reasons.update(
            {
                "published_positive_count_missing",
                "reliability_effective_sample_insufficient",
            }
        )
    elif positives < 93:
        reliability_reasons.update(
            {
                "positive_support_below_93",
                "reliability_effective_sample_insufficient",
            }
        )
    intervals = (
        diagnostic["point_micros"],
        diagnostic["lower_95_micros"],
        diagnostic["upper_95_micros"],
    )
    if any(value is None for value in intervals):
        reliability_reasons.add("reliability_interval_uncertain")
    if (
        reliability_reasons
        or not diagnostic["effective_sample_sufficient"]
    ):
        return (
            "unresolved",
            tuple(
                code
                for code in REASON_CODE_ORDER
                if code in reliability_reasons
            ),
        )
    point, lower, upper = intervals
    assert point is not None and lower is not None and upper is not None
    if point >= 800_000 and lower >= 670_000:
        return "admissible", ()
    if upper < 670_000:
        return "rejected", ("reliability_upper_below_0_67",)
    return "unresolved", ("reliability_interval_uncertain",)


def _validate_phase_c1_result_local(
    payload: Mapping[str, object],
    *,
    source_ledger_bytes: bytes,
) -> None:
    _forbidden_content(payload)
    try:
        encoded_result = phase_c1.canonical_json_bytes(payload)
    except (TypeError, ValueError) as exc:
        raise RunnerError("result_json") from exc
    if len(encoded_result) > MAX_AGGREGATE_RESULT_BYTES:
        raise RunnerError("result_size")
    result = _exact_dict(
        payload,
        phase_c1.PHASE_C1_RESULT_FIELDS,
        code="result_fields",
    )
    if (
        result["schema_version"] != RESULT_SCHEMA_VERSION
        or result["checkpoint_id"] != CHECKPOINT_ID
        or result["protocol_id"] != PROTOCOL_ID
        or result["target_signals"] != list(TARGET_SIGNALS)
        or type(result["implementation_head"]) is not str
        or _LOWER_GIT_ID_RE.fullmatch(result["implementation_head"])
        is None
        or type(result["validator_blob_id"]) is not str
        or _LOWER_GIT_ID_RE.fullmatch(result["validator_blob_id"]) is None
    ):
        raise RunnerError("result_identity")
    for field in (
        "protocol_sha256",
        "search_ledger_sha256",
        "source_evidence_ledger_sha256",
        "source_review_receipt_sha256",
        "aggregate_content_sha256",
    ):
        _sha256(result[field], code="result_hash")
    source_card_hashes_by_signal = _source_card_hashes_by_signal(
        source_ledger_bytes,
        expected_sha256=result["source_evidence_ledger_sha256"],
    )

    search_counts = _validate_search_counts(result["search_counts"])
    source_counts = _validate_source_counts(
        result["source_counts"],
        detailed_candidate_count=search_counts["detailed_candidate_count"],
    )
    direct_lanes, fallback_lane, fail_ready_by_signal = (
        _validate_search_lane_counts(
            result["search_lane_counts"],
            search_counts=search_counts,
        )
    )
    signatures = _validate_source_signature_counts(
        result["source_signature_counts"],
        source_counts=source_counts,
        search_counts=search_counts,
        direct_lanes=direct_lanes,
        fallback_lane=fallback_lane,
    )
    status_counts = _exact_dict(
        result["card_counts_by_status"],
        CARD_STATUS_FIELDS,
        code="card_status_counts",
    )
    for value in status_counts.values():
        _nonnegative_int(value, code="card_status_counts")
    reason_counts = _exact_dict(
        result["reason_code_counts"],
        frozenset(REASON_CODE_ORDER),
        code="reason_code_counts",
    )
    for value in reason_counts.values():
        _nonnegative_int(value, code="reason_code_counts")
    raw_per_signal = result["per_signal"]
    if type(raw_per_signal) is not list or len(raw_per_signal) != 5:
        raise RunnerError("per_signal")
    parsed_per_signal: list[dict[str, object]] = []
    all_diagnostic_hashes: list[str] = []
    derived_card_reason_counts = {
        code: 0 for code in REASON_CODE_ORDER
    }
    diagnostic_signature_counts = {
        signal: {digest: 0 for digest in signatures}
        for signal in TARGET_SIGNALS
    }
    for expected_signal, raw_item in zip(
        TARGET_SIGNALS,
        raw_per_signal,
        strict=True,
    ):
        item = _exact_dict(
            raw_item,
            PER_SIGNAL_FIELDS,
            code="per_signal",
        )
        if (
            item["signal"] != expected_signal
            or item["decision"] not in _SIGNAL_DECISIONS
            or item["annotation_fallback"] not in _FALLBACK_STATUSES
            or type(item["c2_eligible"]) is not bool
        ):
            raise RunnerError("per_signal")
        fallback_material_status_counts = _exact_dict(
            item["fallback_material_status_counts"],
            FALLBACK_MATERIAL_STATUS_COUNT_FIELDS,
            code="per_signal",
        )
        if (
            any(
                type(count) is not int or count < 0
                for count in fallback_material_status_counts.values()
            )
            or sum(fallback_material_status_counts.values())
            != fallback_lane["candidate_order_count"]
        ):
            raise RunnerError("per_signal")
        admissible = item["admissible_evidence_card_sha256s"]
        diagnostics = item["reliability_diagnostics"]
        if type(admissible) is not list or type(diagnostics) is not list:
            raise RunnerError("per_signal")
        admissible_hashes = tuple(
            _sha256(value, code="per_signal") for value in admissible
        )
        if len(set(admissible_hashes)) != len(admissible_hashes):
            raise RunnerError("per_signal")
        parsed_diagnostics = tuple(
            _validate_diagnostic(
                value,
                signal=expected_signal,
                signatures=signatures,
            )
            for value in diagnostics
        )
        if (
            len(parsed_diagnostics) > MAX_DETAILED_CANDIDATES_PER_SIGNAL
        ):
            raise RunnerError("per_signal")
        if (
            len(parsed_diagnostics)
            > source_counts["existing_annotation_evidence_source_count"]
        ):
            raise RunnerError("source_counts")
        diagnostic_hashes = tuple(
            item["evidence_card_sha256"]
            for item in parsed_diagnostics
        )
        if (
            diagnostic_hashes
            != source_card_hashes_by_signal[expected_signal]
        ):
            raise RunnerError("evidence_card_binding")
        diagnostics_by_hash = {
            diagnostic["evidence_card_sha256"]: diagnostic
            for diagnostic in parsed_diagnostics
        }
        local_dispositions: dict[str, tuple[str, tuple[str, ...]]] = {}
        for diagnostic in parsed_diagnostics:
            signature = signatures[
                diagnostic["source_signature_sha256"]
            ]
            if not signature["direct_membership_by_signal"][
                expected_signal
            ]:
                raise RunnerError("reliability_diagnostics")
            disposition = _derived_diagnostic_disposition(
                diagnostic,
                signature,
            )
            if (
                diagnostic["claimed_status"] != disposition[0]
                or diagnostic["claimed_reason_codes"]
                != list(disposition[1])
            ):
                raise RunnerError("reliability_diagnostics")
            local_dispositions[
                diagnostic["evidence_card_sha256"]
            ] = disposition
            diagnostic_signature_counts[expected_signal][
                diagnostic["source_signature_sha256"]
            ] += 1
            for reason in disposition[1]:
                derived_card_reason_counts[reason] += 1
        if (
            len(set(diagnostic_hashes)) != len(diagnostic_hashes)
            or any(value not in diagnostic_hashes for value in admissible_hashes)
            or any(
                local_dispositions[value][0] != "admissible"
                for value in admissible_hashes
            )
        ):
            raise RunnerError("reliability_diagnostics")
        rejected = _nonnegative_int(
            item["rejected_card_count"],
            code="per_signal",
        )
        unresolved = _nonnegative_int(
            item["unresolved_card_count"],
            code="per_signal",
        )
        locally_rejected = sum(
            status == "rejected"
            for status, _ in local_dispositions.values()
        )
        locally_unresolved = sum(
            status == "unresolved"
            for status, _ in local_dispositions.values()
        )
        if (
            len(parsed_diagnostics)
            != len(admissible_hashes) + rejected + unresolved
            or rejected != locally_rejected
            or unresolved != locally_unresolved
            or set(admissible_hashes)
            != {
                digest
                for digest, (status, _) in local_dispositions.items()
                if status == "admissible"
            }
            or (item["decision"] == "pass") != bool(admissible_hashes)
            or (
                item["decision"] == "fail"
                and (
                    unresolved > 0
                    or item["annotation_fallback"] != "infeasible"
                )
            )
            or (
                item["decision"] == "defer"
                and unresolved == 0
                and item["annotation_fallback"] == "infeasible"
            )
        ):
            raise RunnerError("per_signal")
        all_diagnostic_hashes.extend(diagnostic_hashes)
        parsed_per_signal.append(item)
    for signal in TARGET_SIGNALS:
        for digest, signature in signatures.items():
            expected = (
                signature["count"]
                if signature["direct_membership_by_signal"][signal]
                else 0
            )
            if diagnostic_signature_counts[signal][digest] != expected:
                raise RunnerError("source_signature_counts")
    if len(set(all_diagnostic_hashes)) != len(all_diagnostic_hashes):
        raise RunnerError("reliability_diagnostics")
    if (
        len(all_diagnostic_hashes)
        > source_counts["existing_annotation_evidence_source_count"]
        * len(TARGET_SIGNALS)
    ):
        raise RunnerError("source_counts")
    if source_counts["source_count"] > (
        min(
            len(all_diagnostic_hashes),
            source_counts["existing_annotation_evidence_source_count"],
        )
        + min(
            source_counts["fallback_material_candidate_source_count"],
            MAX_DETAILED_FALLBACK_MATERIAL_CANDIDATES,
        )
    ):
        raise RunnerError("source_counts")
    maximum_retained_discovery_record_count = (
        len(all_diagnostic_hashes)
        + source_counts["fallback_material_candidate_source_count"]
        + search_counts["candidate_overflow_count"]
    )
    if (
        search_counts["retained_candidate_record_count"]
        > maximum_retained_discovery_record_count
    ):
        raise RunnerError("search_counts")
    if (
        search_counts["candidate_overflow_count"] > 0
        and source_counts["fallback_material_candidate_source_count"]
        < MAX_DETAILED_FALLBACK_MATERIAL_CANDIDATES
        and all(
            len(item["reliability_diagnostics"])
            < MAX_DETAILED_CANDIDATES_PER_SIGNAL
            for item in parsed_per_signal
        )
    ):
        raise RunnerError("search_counts")

    derived_status_counts = {
        "admissible": sum(
            len(item["admissible_evidence_card_sha256s"])
            for item in parsed_per_signal
        ),
        "rejected": sum(
            item["rejected_card_count"] for item in parsed_per_signal
        ),
        "unresolved": sum(
            item["unresolved_card_count"] for item in parsed_per_signal
        ),
    }
    if status_counts != derived_status_counts:
        raise RunnerError("card_status_counts")

    fallback_status_counts = {
        status: sum(
            item["annotation_fallback"] == status
            for item in parsed_per_signal
        )
        for status in _FALLBACK_STATUSES
    }
    fallback_candidate_count = fallback_lane["candidate_order_count"]
    for item in parsed_per_signal:
        signal = item["signal"]
        fallback_status = item["annotation_fallback"]
        fail_ready = fail_ready_by_signal[signal]
        material_status_counts = item["fallback_material_status_counts"]
        derived_fallback_status = (
            "feasible"
            if material_status_counts["feasible"] > 0
            else "infeasible"
            if (
                fail_ready
                and (
                    fallback_candidate_count == 0
                    or material_status_counts["infeasible"]
                    == fallback_candidate_count
                )
            )
            else "unresolved"
        )
        if fallback_status != derived_fallback_status:
            raise RunnerError("per_signal")
        expected_decision = (
            "pass"
            if item["admissible_evidence_card_sha256s"]
            else "defer"
            if (
                item["unresolved_card_count"] > 0
                or not fail_ready
                or fallback_status in {"feasible", "unresolved"}
            )
            else "fail"
        )
        if (
            item["decision"] != expected_decision
            or item["c2_eligible"] != (expected_decision == "pass")
        ):
            raise RunnerError("per_signal")

    fallback_reason_counts = {
        code: 0 for code in REASON_CODE_ORDER
    }
    fallback_reason_counts["annotation_fallback_feasible"] = (
        fallback_status_counts["feasible"]
    )
    fallback_reason_counts["annotation_fallback_unresolved"] = (
        fallback_status_counts["unresolved"]
    )
    residual_reason_counts: dict[str, int] = {}
    for code in REASON_CODE_ORDER:
        residual = (
            reason_counts[code]
            - derived_card_reason_counts[code]
            - fallback_reason_counts[code]
        )
        if residual < 0:
            raise RunnerError("reason_code_counts")
        residual_reason_counts[code] = residual
    excluded_citation_record_count = sum(
        direct_lanes[signal]["citations"][direction][
            "disposition_counts"
        ]["excluded"]
        for signal in TARGET_SIGNALS
        for direction in phase_c1.CITATION_DIRECTIONS
    )
    expected_rejection_records = (
        search_counts["excluded_discovery_record_count"]
        + excluded_citation_record_count
    )
    expected_unresolved_records = (
        search_counts["unresolved_discovery_record_count"]
        + search_counts["unresolved_citation_record_count"]
    )
    if (
        any(reason_counts[code] != 0 for code in SEARCH_META_REASON_CODES)
        or sum(
            residual_reason_counts[code]
            for code in REJECTION_REASON_CODES
        )
        != expected_rejection_records
        or sum(
            residual_reason_counts[code]
            for code in UNRESOLVED_REASON_CODES
        )
        != expected_unresolved_records
        or any(
            residual_reason_counts[code] != 0
            for code in REASON_CODE_ORDER
            if code
            not in REJECTION_REASON_CODES | UNRESOLVED_REASON_CODES
        )
    ):
        raise RunnerError("reason_code_counts")

    passed = [
        item["signal"]
        for item in parsed_per_signal
        if item["decision"] == "pass"
    ]
    eligible = result["c2_eligible_signals"]
    eligible_flags = [
        item["signal"]
        for item in parsed_per_signal
        if item["c2_eligible"]
    ]
    if (
        type(eligible) is not list
        or eligible != passed
        or eligible_flags != passed
        or any(type(signal) is not str for signal in eligible)
    ):
        raise RunnerError("c2_eligibility")
    derived_overall = (
        "proceed_full_to_c2"
        if len(passed) == 5
        else "proceed_partial_to_c2"
        if passed
        else "defer_c2"
        if any(
            item["decision"] == "defer" for item in parsed_per_signal
        )
        else "stop_c2"
    )
    if (
        result["overall_decision"] not in _OVERALL_DECISIONS
        or result["overall_decision"] != derived_overall
    ):
        raise RunnerError("overall_decision")

    boundary = _exact_dict(
        result["boundary"],
        frozenset(BOUNDARY_FIELDS),
        code="boundary",
    )
    if any(value is not False for value in boundary.values()):
        raise RunnerError("boundary")
    if result["limitations"] != list(LIMITATIONS):
        raise RunnerError("limitations")
    if result["runtime_approved"] is not False:
        raise RunnerError("runtime_approved")

    selfless = dict(result)
    selfless["aggregate_content_sha256"] = ""
    expected_digest = phase_c1.sha256_bytes(
        phase_c1.canonical_json_bytes(selfless)
    )
    if result["aggregate_content_sha256"] != expected_digest:
        raise RunnerError("aggregate_content_sha256")


def validate_phase_c1_result_payload(
    payload: Mapping[str, object],
    *,
    protocol_bytes: bytes,
    search_ledger_bytes: bytes,
    source_ledger_bytes: bytes,
    review_receipt_bytes: bytes,
) -> None:
    _validate_phase_c1_result_local(
        payload,
        source_ledger_bytes=source_ledger_bytes,
    )
    result = _exact_dict(
        payload,
        phase_c1.PHASE_C1_RESULT_FIELDS,
        code="result_fields",
    )
    for field, source, authority_bytes in (
        ("protocol_sha256", "protocol", protocol_bytes),
        ("search_ledger_sha256", "search_ledger", search_ledger_bytes),
        (
            "source_evidence_ledger_sha256",
            "source_ledger",
            source_ledger_bytes,
        ),
        (
            "source_review_receipt_sha256",
            "source_review",
            review_receipt_bytes,
        ),
    ):
        if type(authority_bytes) is not bytes:
            raise RunnerError(f"{source}_bytes")
        if phase_c1.sha256_bytes(authority_bytes) != result[field]:
            raise RunnerError(f"{source}_hash")
    expected_result = _project_phase_c1_result(
        head_commit=result["implementation_head"],
        validator_blob_id=result["validator_blob_id"],
        protocol_bytes=protocol_bytes,
        search_ledger_bytes=search_ledger_bytes,
        source_ledger_bytes=source_ledger_bytes,
        review_receipt_bytes=review_receipt_bytes,
    )
    if phase_c1.canonical_json_bytes(
        result
    ) != phase_c1.canonical_json_bytes(expected_result):
        raise RunnerError("input_projection_binding")

def _compact(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _available(value: object) -> str:
    return "unavailable" if value is None else _compact(value)


def _render_phase_c1_report_local(
    result: Mapping[str, object],
    *,
    source_ledger_bytes: bytes,
) -> bytes:
    _validate_phase_c1_result_local(
        result,
        source_ledger_bytes=source_ledger_bytes,
    )
    final_result_sha256 = phase_c1.sha256_bytes(
        phase_c1.canonical_json_bytes(result)
    )
    lines = [
        "# EMOTION-STATE-004 Phase C1 Operational-Signal Evidence Admission",
        "",
        f"- Checkpoint: {result['checkpoint_id']}",
        f"- Result schema: {result['schema_version']}",
        f"- Protocol: {result['protocol_id']}",
        f"- Implementation HEAD: {result['implementation_head']}",
        f"- Validator blob: {result['validator_blob_id']}",
        f"- Protocol SHA-256: {result['protocol_sha256']}",
        f"- Search-ledger SHA-256: {result['search_ledger_sha256']}",
        (
            "- Source-evidence-ledger SHA-256: "
            f"{result['source_evidence_ledger_sha256']}"
        ),
        (
            "- Source-review-receipt SHA-256: "
            f"{result['source_review_receipt_sha256']}"
        ),
        (
            "- Aggregate-content SHA-256: "
            f"{result['aggregate_content_sha256']}"
        ),
        f"- result.json SHA-256: {final_result_sha256}",
        "",
        "## Aggregate",
        "",
        f"- Overall decision: {result['overall_decision']}",
        f"- Search counts: {_compact(result['search_counts'])}",
        f"- Source counts: {_compact(result['source_counts'])}",
        (
            "- Candidate-card counts by status: "
            f"{_compact(result['card_counts_by_status'])}"
        ),
        "- Reason-code counts:",
    ]
    reason_counts = result["reason_code_counts"]
    for reason in REASON_CODE_ORDER:
        lines.append(f"  - {reason}: {reason_counts[reason]}")

    lines.extend(("", "## Per-Signal Decisions", ""))
    for item in result["per_signal"]:
        lines.extend(
            (
                (
                    f"- {item['signal']}: decision={item['decision']}; "
                    f"c2_eligible={_compact(item['c2_eligible'])}; "
                    f"annotation_fallback={item['annotation_fallback']}"
                ),
                (
                    "  - Admissible evidence-card SHA-256 values: "
                    f"{_compact(item['admissible_evidence_card_sha256s'])}"
                ),
                (
                    "  - Rejected/unresolved card counts: "
                    f"{item['rejected_card_count']}/"
                    f"{item['unresolved_card_count']}"
                ),
                "  - Reliability diagnostics:",
            )
        )
        diagnostics = item["reliability_diagnostics"]
        if not diagnostics:
            lines.append("    - unavailable")
        for diagnostic in diagnostics:
            lines.append(
                "    - "
                f"evidence_card_sha256={diagnostic['evidence_card_sha256']}; "
                f"metric_id={diagnostic['metric_id']}; "
                f"point_micros={_available(diagnostic['point_micros'])}; "
                f"lower_95_micros={_available(diagnostic['lower_95_micros'])}; "
                f"upper_95_micros={_available(diagnostic['upper_95_micros'])}; "
                "independent_rater_count="
                f"{_available(diagnostic['independent_rater_count'])}; "
                f"rated_unit_count={_available(diagnostic['rated_unit_count'])}; "
                "published_positive_count="
                f"{_available(diagnostic['published_positive_count'])}; "
                "effective_sample_sufficient="
                f"{_compact(diagnostic['effective_sample_sufficient'])}; "
                "uncertain_or_unratable_rate_micros="
                f"{_available(diagnostic['uncertain_or_unratable_rate_micros'])}; "
                "class_prevalence_micros="
                f"{_available(diagnostic['class_prevalence_micros'])}; "
                "positive_agreement_micros="
                f"{_available(diagnostic['positive_agreement_micros'])}; "
                "negative_agreement_micros="
                f"{_available(diagnostic['negative_agreement_micros'])}; "
                "preadjudication_disagreement_micros="
                f"{_available(diagnostic['preadjudication_disagreement_micros'])}"
            )

    eligible = result["c2_eligible_signals"]
    lines.extend(
        (
            "",
            "## C2 Eligibility",
            "",
            (
                "- Eligible signals: "
                + (", ".join(eligible) if eligible else "none")
            ),
            (
                "- This research decision does not itself authorize C2, "
                "runtime activation, or policy adaptation."
            ),
            "",
            "## Reliability And Search Boundary",
            "",
            (
                "- Reliability diagnostics are rowless published metadata; "
                "unreported values are shown as unavailable."
            ),
            (
                "- Search complete: "
                f"{_compact(result['search_counts']['search_complete'])}."
            ),
            "- No model evaluation was run.",
            "",
            "## Interpretation",
            "",
            (
                "This checkpoint assesses independent observer-label "
                "admissibility, not hidden customer emotion."
            ),
            (
                "A partial decision admits only the named signal or signals; "
                "it does not validate the others."
            ),
            "",
            "## Limitations",
            "",
        )
    )
    lines.extend(f"- {limitation}" for limitation in result["limitations"])
    lines.extend(
        (
            "",
            "## Closed Boundary",
            "",
            "Runtime approval: false.",
            "- No customer emotion was inferred.",
            "- No private data, participant rows, transcript rows, or audio were read.",
            "- No provider was accessed and no runtime was modified.",
            (
                "- No real-call, latency, safety, conversion, production, or "
                "commercial behavior is proven."
            ),
            "",
        )
    )
    return "\n".join(lines).encode("utf-8")


def render_phase_c1_report(
    result: Mapping[str, object],
    *,
    protocol_bytes: bytes,
    search_ledger_bytes: bytes,
    source_ledger_bytes: bytes,
    review_receipt_bytes: bytes,
) -> bytes:
    validate_phase_c1_result_payload(
        result,
        protocol_bytes=protocol_bytes,
        search_ledger_bytes=search_ledger_bytes,
        source_ledger_bytes=source_ledger_bytes,
        review_receipt_bytes=review_receipt_bytes,
    )
    return _render_phase_c1_report_local(
        result,
        source_ledger_bytes=source_ledger_bytes,
    )
