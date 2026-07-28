from __future__ import annotations

import ctypes
import errno
import json
import os
import re
import hashlib
import stat
import subprocess
import sys
import threading
import weakref
from contextlib import ExitStack, contextmanager
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, Iterator, Sequence

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


@dataclass(frozen=True, slots=True)
class PhaseC1RunnerPaths:
    """The complete, non-caller-configurable Task 9 publication topology."""

    project_root: Path
    protocol_path: Path
    search_ledger_path: Path
    source_ledger_path: Path
    source_review_path: Path
    ignored_root: Path
    candidate_root: Path
    candidate_receipt_path: Path
    candidate_receipt_stage_path: Path
    candidate_validation_path: Path
    candidate_validation_stage_path: Path
    candidate_review_path: Path
    candidate_review_stage_path: Path
    publication_lock_path: Path
    publication_journal_path: Path
    publication_journal_stage_path: Path
    candidate_stage_path: Path
    canonical_stage_path: Path
    canonical_root: Path


PRODUCTION_PATHS: Final = PhaseC1RunnerPaths(
    project_root=ROOT,
    protocol_path=PROTOCOL_PATH,
    search_ledger_path=SEARCH_LEDGER_PATH,
    source_ledger_path=SOURCE_LEDGER_PATH,
    source_review_path=SOURCE_REVIEW_PATH,
    ignored_root=ROOT / ".tmp" / "emotion-state-004-phase-c1",
    candidate_root=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate",
    candidate_receipt_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate-receipt.json",
    candidate_receipt_stage_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate-receipt.stage",
    candidate_validation_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate-validation.json",
    candidate_validation_stage_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate-validation.stage",
    candidate_review_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate-review.json",
    candidate_review_stage_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate-review.stage",
    publication_lock_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "publication.lock",
    publication_journal_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "publication-journal.json",
    publication_journal_stage_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "publication-journal.stage",
    candidate_stage_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "candidate.stage",
    canonical_stage_path=ROOT / ".tmp" / "emotion-state-004-phase-c1" / "canonical.stage",
    canonical_root=ROOT / "research" / "experiments" / "generated" / "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission",
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


# Task 9 deliberately keeps publication state out of the public object graph.
# The objects below are merely weak-key capability handles; all meaningful state
# remains module private and disappears when a handle is collected.
class PreparedPhaseC1Publication:
    __slots__ = ("__weakref__",)

    def __new__(cls, _private: object) -> "PreparedPhaseC1Publication":
        raise TypeError("PreparedPhaseC1Publication is capability-only")


class PhaseC1PublicationLockCapability:
    __slots__ = ("__weakref__",)

    def __new__(cls, _private: object) -> "PhaseC1PublicationLockCapability":
        raise TypeError("PhaseC1PublicationLockCapability is capability-only")


@dataclass(frozen=True, slots=True)
class _PreparedPhaseC1State:
    paths: PhaseC1RunnerPaths
    project_root_identity: tuple[int, int]
    parent_identities: tuple[tuple[str, tuple[int, int]], ...]
    expected_head: str
    validator_blob_id: str
    operation: str
    protocol_bytes: bytes
    search_ledger_bytes: bytes
    source_ledger_bytes: bytes
    source_review_bytes: bytes
    result_bytes: bytes
    report_bytes: bytes
    candidate_receipt_bytes: bytes
    candidate_validation_bytes: bytes | None
    candidate_review_bytes: bytes | None


@dataclass(frozen=True, slots=True)
class _LockState:
    prepared: PreparedPhaseC1Publication
    operation: str
    root_identity: tuple[int, int]
    handle: object
    ignored_root_authority: _HeldPhaseC1DirectoryAuthority


@dataclass(frozen=True, slots=True)
class _HeldPhaseC1DirectoryAuthority:
    path: Path
    stable_identity: tuple[int, ...]
    posix_descriptor: int | None
    windows_handle: int | None
    invalidated: bool = False


@dataclass(slots=True)
class _HeldPhaseC1RegularFileAuthority:
    path: Path
    stable_identity: tuple[int, ...]
    sha256: str
    size_bytes: int
    posix_descriptor: int | None
    windows_handle: int | None
    closed: bool = False


@dataclass(frozen=True, slots=True)
class PhaseC1PublicationReceipt:
    status: str
    transaction_id: str


_PUBLICATION_STATE_LOCK = threading.RLock()
_PREPARED_PUBLICATION_STATES: weakref.WeakKeyDictionary[PreparedPhaseC1Publication, _PreparedPhaseC1State] = weakref.WeakKeyDictionary()
_LOCK_CAPABILITY_STATES: weakref.WeakKeyDictionary[PhaseC1PublicationLockCapability, _LockState] = weakref.WeakKeyDictionary()
_PHASE_C1_FILE_CREATE_CONTEXT = threading.local()
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_JOURNAL_STATUSES = frozenset(("staging_candidate", "candidate_ready", "staging_canonical", "accepted"))
_LEGAL_JOURNAL_TRANSITIONS = frozenset((
    ("candidate", None, "staging_candidate"),
    ("candidate", "staging_candidate", "candidate_ready"),
    ("acceptance", "candidate_ready", "staging_canonical"),
    ("acceptance", "staging_canonical", "staging_canonical"),
    ("acceptance", "staging_canonical", "accepted"),
))
_JOURNAL_FIELDS = frozenset((
    "schema_version", "checkpoint_id", "transaction_id", "sequence",
    "previous_journal_sha256", "status", "expected_head", "implementation_head",
    "validator_blob_id", "protocol_sha256", "search_ledger_sha256",
    "source_evidence_ledger_sha256", "source_review_receipt_sha256",
    "result_sha256", "report_sha256", "candidate_receipt_sha256",
    "candidate_validation_sha256", "candidate_review_sha256",
    "journal_content_sha256",
))
_CANDIDATE_RECEIPT_FIELDS = frozenset((
    "schema_version", "checkpoint_id", "transaction_id", "status",
    "implementation_head", "validator_blob_id", "protocol_sha256",
    "search_ledger_sha256", "source_evidence_ledger_sha256",
    "source_review_receipt_sha256", "result_sha256", "report_sha256",
))


def _publication_error(code: str) -> RunnerError:
    return RunnerError(code)


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _identity(path: Path, *, directory: bool | None = None) -> tuple[int, int]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise _publication_error("path_missing") from exc
    if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_reparse_tag", 0):
        raise _publication_error("path_reparse")
    if directory is True and not stat.S_ISDIR(metadata.st_mode):
        raise _publication_error("path_directory")
    if directory is False and not stat.S_ISREG(metadata.st_mode):
        raise _publication_error("path_regular")
    return (metadata.st_dev, metadata.st_ino)


def _under(root: Path, child: Path) -> bool:
    try:
        Path(child).resolve(strict=False).is_relative_to(Path(root).resolve(strict=False))
    except (OSError, ValueError):
        return False
    return True


def _assert_paths_shape(paths: PhaseC1RunnerPaths) -> None:
    if not isinstance(paths, PhaseC1RunnerPaths):
        raise _publication_error("paths")
    root = paths.project_root
    if not isinstance(root, Path) or not root.is_absolute():
        raise _publication_error("paths")
    ignored_root = root / ".tmp" / "emotion-state-004-phase-c1"
    expected = PhaseC1RunnerPaths(
        project_root=root,
        protocol_path=(
            root
            / "research"
            / "experiments"
            / "configs"
            / "emotion-state-004-phase-c1-discovery-protocol.json"
        ),
        search_ledger_path=(
            root
            / "research"
            / "sources"
            / "emotion_state"
            / "phase_c1_search_ledger.json"
        ),
        source_ledger_path=(
            root
            / "research"
            / "sources"
            / "emotion_state"
            / "phase_c1_source_evidence_ledger.json"
        ),
        source_review_path=(
            root
            / "research"
            / "sources"
            / "emotion_state"
            / "phase_c1_source_review_receipt.json"
        ),
        ignored_root=ignored_root,
        candidate_root=ignored_root / "candidate",
        candidate_receipt_path=(
            ignored_root / "candidate-receipt.json"
        ),
        candidate_receipt_stage_path=(
            ignored_root / "candidate-receipt.stage"
        ),
        candidate_validation_path=(
            ignored_root / "candidate-validation.json"
        ),
        candidate_validation_stage_path=(
            ignored_root / "candidate-validation.stage"
        ),
        candidate_review_path=(
            ignored_root / "candidate-review.json"
        ),
        candidate_review_stage_path=(
            ignored_root / "candidate-review.stage"
        ),
        publication_lock_path=ignored_root / "publication.lock",
        publication_journal_path=(
            ignored_root / "publication-journal.json"
        ),
        publication_journal_stage_path=(
            ignored_root / "publication-journal.stage"
        ),
        candidate_stage_path=ignored_root / "candidate.stage",
        canonical_stage_path=ignored_root / "canonical.stage",
        canonical_root=(
            root
            / "research"
            / "experiments"
            / "generated"
            / (
                "EMOTION-STATE-004-phase-c1-operational-signal-"
                "evidence-admission"
            )
        ),
    )
    if paths != expected:
        raise _publication_error("paths")
    _identity(root, directory=True)


def _current_repository_head() -> str:
    try:
        value = subprocess.check_output(
            ("git", "-C", os.fspath(PRODUCTION_PATHS.project_root), "rev-parse", "HEAD"),
            stderr=subprocess.DEVNULL,
        ).decode("ascii").strip()
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise _publication_error("head") from exc
    if _HEX40.fullmatch(value) is None:
        raise _publication_error("head")
    return value


def _resolve_phase_c1_validator_state(expected_head: str) -> dict[str, object]:
    """Resolve the committed validator blob and reject a dirty implementation."""
    root = PRODUCTION_PATHS.project_root
    try:
        head = subprocess.check_output(("git", "-C", os.fspath(root), "rev-parse", "HEAD"), stderr=subprocess.DEVNULL).decode("ascii").strip()
        dirty = subprocess.check_output(("git", "-C", os.fspath(root), "status", "--porcelain", "--", "scripts/validate_emotion_state_004_phase_c1.py"), stderr=subprocess.DEVNULL)
        blob = subprocess.check_output(("git", "-C", os.fspath(root), "rev-parse", f"{expected_head}:scripts/validate_emotion_state_004_phase_c1.py"), stderr=subprocess.DEVNULL).decode("ascii").strip()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return {"repository_head": None, "validator_blob_id": None, "is_clean": False}
    return {"repository_head": head, "validator_blob_id": blob if _HEX40.fullmatch(blob) else None, "is_clean": not bool(dirty)}


def _read_phase_c1_tracked_input_bytes(paths: PhaseC1RunnerPaths) -> tuple[bytes, bytes, bytes, bytes]:
    values: list[bytes] = []
    for path in (paths.protocol_path, paths.search_ledger_path, paths.source_ledger_path, paths.source_review_path):
        _identity(path, directory=False)
        try:
            values.append(path.read_bytes())
        except OSError as exc:
            raise _publication_error("tracked_read") from exc
    return tuple(values)  # type: ignore[return-value]


def _tracked_parent_identities(
    paths: PhaseC1RunnerPaths,
    *,
    include_canonical_target: bool = False,
) -> tuple[tuple[str, tuple[int, int]], ...]:
    parents: tuple[tuple[str, Path], ...] = (
        ("protocol", paths.protocol_path.parent),
        ("search", paths.search_ledger_path.parent),
        ("source", paths.source_ledger_path.parent),
        ("review", paths.source_review_path.parent),
    )
    if include_canonical_target:
        parents += (
            ("canonical_target", paths.canonical_root.parent),
        )
    return tuple((name, _identity(path, directory=True)) for name, path in parents)


def _make_candidate_receipt(state: _PreparedPhaseC1State) -> bytes:
    payload: dict[str, str] = {
        "schema_version": "EmotionStatePhaseC1CandidateReceiptV1",
        "checkpoint_id": CHECKPOINT_ID,
        "transaction_id": "",
        "status": "candidate_ready",
        "implementation_head": state.expected_head,
        "validator_blob_id": state.validator_blob_id,
        "protocol_sha256": _digest(state.protocol_bytes),
        "search_ledger_sha256": _digest(state.search_ledger_bytes),
        "source_evidence_ledger_sha256": _digest(state.source_ledger_bytes),
        "source_review_receipt_sha256": _digest(state.source_review_bytes),
        "result_sha256": _digest(state.result_bytes),
        "report_sha256": _digest(state.report_bytes),
    }
    payload["transaction_id"] = _digest(phase_c1.canonical_json_bytes(payload))[:32]
    return phase_c1.canonical_json_bytes(payload)


def _parse_exact_json(payload: bytes, *, source: str) -> dict[str, object]:
    try:
        value = phase_c1.load_json_strict(payload, source=source)
    except (ValueError, TypeError, phase_c1.PhaseC1ContractError) as exc:
        raise _publication_error(source) from exc
    if not isinstance(value, dict) or phase_c1.canonical_json_bytes(value) != payload:
        raise _publication_error(source)
    return value


def _validate_candidate_receipt_bytes(payload: bytes, state: _PreparedPhaseC1State) -> dict[str, object]:
    receipt = _parse_exact_json(payload, source="candidate_receipt")
    if set(receipt) != _CANDIDATE_RECEIPT_FIELDS:
        raise _publication_error("candidate_receipt")
    expected = _parse_exact_json(_make_candidate_receipt(state), source="candidate_receipt_expected")
    if receipt != expected or any(type(value) is not str or not value.isascii() for value in receipt.values()):
        raise _publication_error("candidate_receipt")
    return receipt


def _validate_phase_c1_pair_at_path(path: Path, state: _PreparedPhaseC1State) -> None:
    _identity(path, directory=True)
    children = {item.name for item in path.iterdir()}
    if children != {"result.json", "report.md"}:
        raise _publication_error("pair_children")
    result_path = path / "result.json"
    report_path = path / "report.md"
    _identity(result_path, directory=False)
    _identity(report_path, directory=False)
    if result_path.read_bytes() != state.result_bytes or report_path.read_bytes() != state.report_bytes:
        raise _publication_error("pair_bytes")
    try:
        result = phase_c1.load_json_strict(state.result_bytes, source="publication_result")
        if not isinstance(result, dict):
            raise ValueError()
        validate_phase_c1_result_payload(result, protocol_bytes=state.protocol_bytes, search_ledger_bytes=state.search_ledger_bytes, source_ledger_bytes=state.source_ledger_bytes, review_receipt_bytes=state.source_review_bytes)
        if render_phase_c1_report(result, protocol_bytes=state.protocol_bytes, search_ledger_bytes=state.search_ledger_bytes, source_ledger_bytes=state.source_ledger_bytes, review_receipt_bytes=state.source_review_bytes) != state.report_bytes:
            raise ValueError()
    except (ValueError, TypeError, phase_c1.PhaseC1ContractError, RunnerError) as exc:
        raise _publication_error("pair_semantics") from exc


def _validate_phase_c1_stage_prefix(
    path: Path,
    state: _PreparedPhaseC1State,
) -> tuple[str, ...]:
    _identity(path, directory=True)
    children = tuple(item.name for item in path.iterdir())
    child_set = frozenset(children)
    if child_set not in (
        frozenset(),
        frozenset({"result.json"}),
        frozenset({"result.json", "report.md"}),
    ):
        raise _publication_error("pair_stage_prefix")
    for name, expected in (
        ("result.json", state.result_bytes),
        ("report.md", state.report_bytes),
    ):
        child = path / name
        if name in child_set:
            _identity(child, directory=False)
            if child.read_bytes() != expected:
                raise _publication_error("pair_stage_prefix")
    return tuple(
        name
        for name in ("result.json", "report.md")
        if name in child_set
    )


def _validate_phase_c1_cleanup_prefix(
    path: Path,
    *,
    result_bytes: bytes,
    report_bytes: bytes,
    allow_result_only: bool = False,
) -> tuple[str, ...]:
    if (
        type(result_bytes) is not bytes
        or type(report_bytes) is not bytes
        or type(allow_result_only) is not bool
    ):
        raise _publication_error("pair_cleanup_prefix")
    _identity(path, directory=True)
    child_set = frozenset(item.name for item in path.iterdir())
    allowed_prefixes = (
        frozenset(),
        frozenset({"report.md"}),
        frozenset({"result.json", "report.md"}),
    ) + (
        (frozenset({"result.json"}),)
        if allow_result_only
        else ()
    )
    if child_set not in allowed_prefixes:
        raise _publication_error("pair_cleanup_prefix")
    for name, expected in (
        ("result.json", result_bytes),
        ("report.md", report_bytes),
    ):
        if name not in child_set:
            continue
        child = path / name
        _identity(child, directory=False)
        if child.read_bytes() != expected:
            raise _publication_error("pair_cleanup_prefix")
    return tuple(
        name
        for name in ("result.json", "report.md")
        if name in child_set
    )


def _validate_phase_c1_candidate_receipt_at_path(path: Path, state: _PreparedPhaseC1State) -> dict[str, object]:
    _identity(path, directory=False)
    return _validate_candidate_receipt_bytes(path.read_bytes(), state)


def _create_new_phase_c1_file(path: Path, payload: bytes) -> object:
    parent_authority = getattr(
        _PHASE_C1_FILE_CREATE_CONTEXT,
        "parent_authority",
        None,
    )
    if parent_authority is not None:
        return _create_new_phase_c1_file_at_authority(
            path,
            payload,
            parent_authority=parent_authority,
        )
    handle: object | None = None
    try:
        handle = open(path, "xb")
        handle.write(payload)
        handle.flush()
        return handle
    except OSError as exc:
        if handle is not None:
            try:
                handle.close()  # type: ignore[attr-defined]
            except OSError:
                pass
        raise _publication_error("create_new") from exc


def _fsync_phase_c1_open_file(handle: object) -> None:
    try:
        os.fsync(handle.fileno())  # type: ignore[attr-defined]
    except OSError as exc:
        raise _publication_error("file_fsync") from exc
    finally:
        try:
            handle.close()  # type: ignore[attr-defined]
        except OSError:
            pass


def _flush_phase_c1_windows_directory(path: Path) -> None:
    from ctypes import wintypes

    class _WindowsDirectoryInformation(ctypes.Structure):
        _fields_ = (
            ("file_attributes", wintypes.DWORD),
            ("creation_time", wintypes.FILETIME),
            ("last_access_time", wintypes.FILETIME),
            ("last_write_time", wintypes.FILETIME),
            ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD),
            ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        )

    directory = Path(path)

    def path_identity() -> tuple[int, int, int]:
        metadata = directory.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or getattr(metadata, "st_reparse_tag", 0)
            or not stat.S_ISDIR(metadata.st_mode)
        ):
            raise OSError("directory barrier target is unsafe")
        inode = int(metadata.st_ino)
        return (
            int(metadata.st_dev),
            (inode >> 32) & 0xFFFFFFFF,
            inode & 0xFFFFFFFF,
        )

    expected_identity = path_identity()
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_WindowsDirectoryInformation),
    )
    get_information.restype = wintypes.BOOL
    flush = kernel32.FlushFileBuffers
    flush.argtypes = (wintypes.HANDLE,)
    flush.restype = wintypes.BOOL
    close = kernel32.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL

    handle = create_file(
        os.fspath(directory),
        0x40000000,
        0x00000001 | 0x00000002 | 0x00000004,
        None,
        3,
        0x02000000 | 0x00200000 | 0x80000000,
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle is None or handle == invalid_handle:
        raise OSError(
            ctypes.get_last_error(),
            "unable to open directory barrier",
        )

    active_error = False
    try:
        information = _WindowsDirectoryInformation()
        if not get_information(handle, ctypes.byref(information)):
            raise OSError(
                ctypes.get_last_error(),
                "unable to inspect directory barrier",
            )
        opened_identity = (
            int(information.volume_serial_number),
            int(information.file_index_high),
            int(information.file_index_low),
        )
        if (
            information.file_attributes & 0x00000400
            or not information.file_attributes & 0x00000010
            or opened_identity != expected_identity
        ):
            raise OSError("directory barrier identity is unsafe")
        if not flush(handle):
            raise OSError(
                ctypes.get_last_error(),
                "unable to flush directory barrier",
            )
        if path_identity() != expected_identity:
            raise OSError("directory barrier identity changed")
    except BaseException:
        active_error = True
        raise
    finally:
        if not close(handle) and not active_error:
            raise OSError(
                ctypes.get_last_error(),
                "unable to close directory barrier",
            )


def _phase_c1_windows_handle_information(
    handle: int,
) -> tuple[tuple[int, int], int]:
    from ctypes import wintypes

    class _WindowsHandleInformation(ctypes.Structure):
        _fields_ = (
            ("file_attributes", wintypes.DWORD),
            ("creation_time", wintypes.FILETIME),
            ("last_access_time", wintypes.FILETIME),
            ("last_write_time", wintypes.FILETIME),
            ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD),
            ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        )

    information = _WindowsHandleInformation()
    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).GetFileInformationByHandle
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_WindowsHandleInformation),
    )
    function.restype = wintypes.BOOL
    if not function(handle, ctypes.byref(information)):
        raise OSError(
            ctypes.get_last_error(),
            "unable to inspect held directory authority",
        )
    return (
        (
            int(information.volume_serial_number),
            (
                int(information.file_index_high) << 32
            ) | int(information.file_index_low),
        ),
        int(information.file_attributes),
    )


def _open_phase_c1_windows_directory_handle(
    path: Path,
    *,
    access: int,
    share_mode: int,
) -> int:
    from ctypes import wintypes

    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).CreateFileW
    function.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    function.restype = wintypes.HANDLE
    handle = function(
        os.fspath(path),
        access,
        share_mode,
        None,
        3,  # OPEN_EXISTING
        0x02000000 | 0x00200000,  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle is None or handle == invalid_handle:
        raise OSError(
            ctypes.get_last_error(),
            "unable to open held directory authority",
        )
    return int(handle)


def _close_phase_c1_windows_handle(handle: int) -> None:
    from ctypes import wintypes

    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).CloseHandle
    function.argtypes = (wintypes.HANDLE,)
    function.restype = wintypes.BOOL
    if not function(handle):
        raise OSError(
            ctypes.get_last_error(),
            "unable to close held directory authority",
        )


def _phase_c1_windows_regular_file_information(
    handle: int,
) -> tuple[tuple[int, int], int, int, int]:
    from ctypes import wintypes

    class _WindowsFileInformation(ctypes.Structure):
        _fields_ = (
            ("file_attributes", wintypes.DWORD),
            ("creation_time", wintypes.FILETIME),
            ("last_access_time", wintypes.FILETIME),
            ("last_write_time", wintypes.FILETIME),
            ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD),
            ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        )

    information = _WindowsFileInformation()
    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).GetFileInformationByHandle
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_WindowsFileInformation),
    )
    function.restype = wintypes.BOOL
    if not function(handle, ctypes.byref(information)):
        raise OSError(
            ctypes.get_last_error(),
            "unable to inspect held regular file",
        )
    identity = (
        int(information.volume_serial_number),
        (
            int(information.file_index_high) << 32
        ) | int(information.file_index_low),
    )
    size = (
        int(information.file_size_high) << 32
    ) | int(information.file_size_low)
    return (
        identity,
        size,
        int(information.number_of_links),
        int(information.file_attributes),
    )


def _open_phase_c1_windows_regular_file_handle(path: Path) -> int:
    from ctypes import wintypes

    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).CreateFileW
    function.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    function.restype = wintypes.HANDLE
    handle = function(
        os.fspath(path),
        0x80000000 | 0x00010000,  # GENERIC_READ | DELETE
        0x00000001,  # FILE_SHARE_READ; deny write and delete sharing
        None,
        3,  # OPEN_EXISTING
        0x00200000 | 0x00000080,  # OPEN_REPARSE_POINT | NORMAL
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle is None or handle == invalid_handle:
        raise OSError(
            ctypes.get_last_error(),
            "unable to open held regular file",
        )
    return int(handle)


def _open_phase_c1_windows_regular_file_readback_handle(
    path: Path,
) -> int:
    from ctypes import wintypes

    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).CreateFileW
    function.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    function.restype = wintypes.HANDLE
    handle = function(
        os.fspath(path),
        0x80000000,  # GENERIC_READ
        0x00000001 | 0x00000004,  # FILE_SHARE_READ | FILE_SHARE_DELETE
        None,
        3,  # OPEN_EXISTING
        0x00200000 | 0x00000080,  # OPEN_REPARSE_POINT | NORMAL
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle is None or handle == invalid_handle:
        raise OSError(
            ctypes.get_last_error(),
            "unable to open committed regular file for held readback",
        )
    return int(handle)


def _read_phase_c1_windows_regular_file_handle(
    handle: int,
    *,
    maximum_bytes: int,
) -> bytes:
    from ctypes import wintypes

    seek = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).SetFilePointerEx
    seek.argtypes = (
        wintypes.HANDLE,
        ctypes.c_longlong,
        ctypes.POINTER(ctypes.c_longlong),
        wintypes.DWORD,
    )
    seek.restype = wintypes.BOOL
    if not seek(handle, 0, None, 0):
        raise OSError(
            ctypes.get_last_error(),
            "unable to seek held regular file",
        )
    read = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).ReadFile
    read.argtypes = (
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    )
    read.restype = wintypes.BOOL
    chunks: list[bytes] = []
    remaining = maximum_bytes + 1
    while remaining:
        requested = min(1_048_576, remaining)
        buffer = ctypes.create_string_buffer(requested)
        count = wintypes.DWORD()
        if not read(
            handle,
            buffer,
            requested,
            ctypes.byref(count),
            None,
        ):
            raise OSError(
                ctypes.get_last_error(),
                "unable to read held regular file",
            )
        if count.value == 0:
            break
        chunks.append(buffer.raw[:count.value])
        remaining -= count.value
    payload = b"".join(chunks)
    if len(payload) > maximum_bytes:
        raise _publication_error("regular_file_authority")
    return payload


def _read_held_phase_c1_regular_file_bytes(
    authority: _HeldPhaseC1RegularFileAuthority,
) -> bytes:
    if (
        type(authority) is not _HeldPhaseC1RegularFileAuthority
        or authority.closed
    ):
        raise _publication_error("regular_file_authority")
    try:
        if os.name == "nt":
            if (
                authority.windows_handle is None
                or authority.posix_descriptor is not None
            ):
                raise _publication_error("regular_file_authority")
            return _read_phase_c1_windows_regular_file_handle(
                authority.windows_handle,
                maximum_bytes=authority.size_bytes,
            )
        if (
            authority.posix_descriptor is None
            or authority.windows_handle is not None
        ):
            raise _publication_error("regular_file_authority")
        os.lseek(authority.posix_descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        remaining = authority.size_bytes + 1
        while remaining:
            chunk = os.read(
                authority.posix_descriptor,
                min(1_048_576, remaining),
            )
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) > authority.size_bytes:
            raise _publication_error("regular_file_authority")
        return payload
    except OSError as exc:
        raise _publication_error("regular_file_authority") from exc


def _verify_held_phase_c1_regular_file_authority(
    authority: _HeldPhaseC1RegularFileAuthority,
    *,
    require_path: bool = True,
) -> None:
    if (
        type(authority) is not _HeldPhaseC1RegularFileAuthority
        or authority.closed
        or type(require_path) is not bool
    ):
        raise _publication_error("regular_file_authority")
    try:
        if os.name == "nt":
            if (
                authority.windows_handle is None
                or authority.posix_descriptor is not None
            ):
                raise _publication_error("regular_file_authority")
            identity, size, links, attributes = (
                _phase_c1_windows_regular_file_information(
                    authority.windows_handle,
                )
            )
            if (
                identity != authority.stable_identity
                or size != authority.size_bytes
                or links != 1
                or attributes & (0x00000010 | 0x00000400)
            ):
                raise _publication_error("regular_file_authority")
        else:
            if (
                authority.posix_descriptor is None
                or authority.windows_handle is not None
            ):
                raise _publication_error("regular_file_authority")
            opened = os.fstat(authority.posix_descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_size != authority.size_bytes
                or (int(opened.st_dev), int(opened.st_ino))
                != authority.stable_identity
            ):
                raise _publication_error("regular_file_authority")
        if require_path:
            inspected = authority.path.lstat()
            if (
                stat.S_ISLNK(inspected.st_mode)
                or getattr(inspected, "st_reparse_tag", 0)
                or not stat.S_ISREG(inspected.st_mode)
                or inspected.st_nlink != 1
                or (int(inspected.st_dev), int(inspected.st_ino))
                != authority.stable_identity
            ):
                raise _publication_error("regular_file_authority")
        payload = _read_held_phase_c1_regular_file_bytes(authority)
        if (
            len(payload) != authority.size_bytes
            or _digest(payload) != authority.sha256
        ):
            raise _publication_error("regular_file_authority")
    except OSError as exc:
        raise _publication_error("regular_file_authority") from exc


def _close_held_phase_c1_regular_file_authority(
    authority: _HeldPhaseC1RegularFileAuthority,
) -> None:
    if type(authority) is not _HeldPhaseC1RegularFileAuthority:
        raise _publication_error("regular_file_authority")
    if authority.closed:
        return
    try:
        if os.name == "nt":
            if authority.windows_handle is None:
                raise _publication_error("regular_file_authority")
            _close_phase_c1_windows_handle(authority.windows_handle)
            authority.windows_handle = None
        else:
            if authority.posix_descriptor is None:
                raise _publication_error("regular_file_authority")
            os.close(authority.posix_descriptor)
            authority.posix_descriptor = None
        authority.closed = True
    except OSError as exc:
        raise _publication_error("regular_file_authority") from exc


def _transition_phase_c1_windows_regular_file_to_readback(
    authority: _HeldPhaseC1RegularFileAuthority,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    if os.name != "nt":
        return
    if (
        type(authority) is not _HeldPhaseC1RegularFileAuthority
        or authority.closed
        or authority.windows_handle is None
        or authority.posix_descriptor is not None
        or type(parent_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or authority.path.parent != parent_authority.path
    ):
        raise _publication_error("regular_file_authority")
    _verify_held_phase_c1_regular_file_authority(authority)
    replacement_handle: int | None = None
    transitioned = False
    try:
        replacement_handle = (
            _open_phase_c1_windows_regular_file_readback_handle(
                authority.path,
            )
        )
        identity, size, links, attributes = (
            _phase_c1_windows_regular_file_information(
                replacement_handle,
            )
        )
        payload = _read_phase_c1_windows_regular_file_handle(
            replacement_handle,
            maximum_bytes=authority.size_bytes,
        )
        if (
            identity != authority.stable_identity
            or size != authority.size_bytes
            or links != 1
            or attributes & (0x00000010 | 0x00000400)
            or len(payload) != authority.size_bytes
            or _digest(payload) != authority.sha256
        ):
            raise _publication_error("regular_file_authority")
        original_handle = authority.windows_handle
        _close_phase_c1_windows_handle(original_handle)
        authority.windows_handle = replacement_handle
        replacement_handle = None
        transitioned = True
        _verify_held_phase_c1_regular_file_authority(authority)
    except RunnerError:
        if transitioned:
            _restore_phase_c1_committed_regular_file(
                authority,
                parent_authority=parent_authority,
            )
        raise
    except OSError as exc:
        raise _publication_error("regular_file_authority") from exc
    finally:
        if replacement_handle is not None:
            try:
                _close_phase_c1_windows_handle(replacement_handle)
            except OSError:
                pass


def _matching_phase_c1_regular_file_entry(
    authority: _HeldPhaseC1RegularFileAuthority,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> Path:
    if (
        type(authority) is not _HeldPhaseC1RegularFileAuthority
        or type(parent_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or authority.path.parent != parent_authority.path
    ):
        raise _publication_error("regular_file_restore")
    _verify_held_phase_c1_directory_authority(parent_authority)
    _verify_held_phase_c1_regular_file_authority(
        authority,
        require_path=False,
    )
    matches: list[Path] = []
    try:
        if os.name == "nt":
            entries = tuple(parent_authority.path.iterdir())
            for entry in entries:
                metadata = entry.lstat()
                if (
                    not stat.S_ISLNK(metadata.st_mode)
                    and not getattr(metadata, "st_reparse_tag", 0)
                    and stat.S_ISREG(metadata.st_mode)
                    and (int(metadata.st_dev), int(metadata.st_ino))
                    == authority.stable_identity
                ):
                    matches.append(entry)
        else:
            if parent_authority.posix_descriptor is None:
                raise _publication_error("directory_authority")
            for name in os.listdir(parent_authority.posix_descriptor):
                metadata = os.stat(
                    name,
                    dir_fd=parent_authority.posix_descriptor,
                    follow_symlinks=False,
                )
                if (
                    stat.S_ISREG(metadata.st_mode)
                    and (int(metadata.st_dev), int(metadata.st_ino))
                    == authority.stable_identity
                ):
                    matches.append(parent_authority.path / name)
    except OSError as exc:
        raise _publication_error("regular_file_restore") from exc
    if len(matches) != 1:
        raise _publication_error("regular_file_restore")
    return matches[0]


def _restore_phase_c1_committed_regular_file(
    authority: _HeldPhaseC1RegularFileAuthority,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    destination = authority.path
    moved = _matching_phase_c1_regular_file_entry(
        authority,
        parent_authority=parent_authority,
    )
    if moved == destination:
        raise _publication_error("regular_file_restore")
    try:
        if os.name == "nt":
            if (
                parent_authority.windows_handle is None
                or authority.windows_handle is None
            ):
                raise _publication_error("regular_file_restore")
            repair_handle = _open_phase_c1_windows_regular_file_handle(
                moved,
            )
            try:
                identity, size, links, attributes = (
                    _phase_c1_windows_regular_file_information(
                        repair_handle,
                    )
                )
                payload = _read_phase_c1_windows_regular_file_handle(
                    repair_handle,
                    maximum_bytes=authority.size_bytes,
                )
                if (
                    identity != authority.stable_identity
                    or size != authority.size_bytes
                    or links != 1
                    or attributes & (0x00000010 | 0x00000400)
                    or _digest(payload) != authority.sha256
                ):
                    raise _publication_error("regular_file_restore")
                _rename_phase_c1_windows_regular_file_handle(
                    repair_handle,
                    destination.name,
                    destination_parent_handle=(
                        parent_authority.windows_handle
                    ),
                    replace=True,
                )
            finally:
                _close_phase_c1_windows_handle(repair_handle)
        else:
            if parent_authority.posix_descriptor is None:
                raise _publication_error("regular_file_restore")
            _renameat2_phase_c1_regular_file(
                moved.name,
                destination.name,
                parent_descriptor=parent_authority.posix_descriptor,
                flags=0,
            )
    except OSError as exc:
        raise _publication_error("regular_file_restore") from exc
    _verify_held_phase_c1_regular_file_authority(authority)
    _verify_held_phase_c1_directory_authority(parent_authority)


def _verify_committed_phase_c1_regular_file(
    authority: _HeldPhaseC1RegularFileAuthority,
    *,
    expected_payload: bytes,
    stage_path: Path,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    error_code: str,
) -> None:
    try:
        _verify_held_phase_c1_regular_file_authority(authority)
        if (
            _read_held_phase_c1_regular_file_bytes(authority)
            != expected_payload
        ):
            raise _publication_error(error_code)
    except RunnerError:
        _restore_phase_c1_committed_regular_file(
            authority,
            parent_authority=parent_authority,
        )
        raise
    if os.path.lexists(stage_path):
        raise _publication_error(error_code)


@contextmanager
def _held_phase_c1_regular_file_authority(
    path: Path,
    *,
    expected_bytes: bytes,
) -> Iterator[_HeldPhaseC1RegularFileAuthority]:
    target = Path(path)
    if type(expected_bytes) is not bytes:
        raise _publication_error("regular_file_authority")
    try:
        before = target.lstat()
    except OSError as exc:
        raise _publication_error("regular_file_authority") from exc
    if (
        stat.S_ISLNK(before.st_mode)
        or getattr(before, "st_reparse_tag", 0)
        or not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
    ):
        raise _publication_error("regular_file_authority")

    if os.name == "nt":
        try:
            handle = _open_phase_c1_windows_regular_file_handle(target)
        except OSError as exc:
            raise _publication_error("regular_file_authority") from exc
        authority = _HeldPhaseC1RegularFileAuthority(
            path=target,
            stable_identity=(int(before.st_dev), int(before.st_ino)),
            sha256=_digest(expected_bytes),
            size_bytes=len(expected_bytes),
            posix_descriptor=None,
            windows_handle=handle,
        )
    else:
        nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
        if not nofollow_flag:
            raise _publication_error("regular_file_authority")
        try:
            descriptor = os.open(
                target,
                os.O_RDONLY | nofollow_flag,
            )
        except OSError as exc:
            raise _publication_error("regular_file_authority") from exc
        authority = _HeldPhaseC1RegularFileAuthority(
            path=target,
            stable_identity=(int(before.st_dev), int(before.st_ino)),
            sha256=_digest(expected_bytes),
            size_bytes=len(expected_bytes),
            posix_descriptor=descriptor,
            windows_handle=None,
        )

    active_error = False
    try:
        _verify_held_phase_c1_regular_file_authority(authority)
        if (
            _read_held_phase_c1_regular_file_bytes(authority)
            != expected_bytes
        ):
            raise _publication_error("regular_file_authority")
        yield authority
        if not authority.closed:
            _verify_held_phase_c1_regular_file_authority(authority)
    except BaseException:
        active_error = True
        raise
    finally:
        if not authority.closed:
            try:
                _close_held_phase_c1_regular_file_authority(authority)
            except RunnerError:
                if not active_error:
                    raise


def _verify_held_phase_c1_directory_authority(
    authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    if (
        type(authority) is not _HeldPhaseC1DirectoryAuthority
        or authority.invalidated
    ):
        raise _publication_error("directory_authority")
    try:
        if os.name == "nt":
            if (
                authority.windows_handle is None
                or authority.posix_descriptor is not None
            ):
                raise _publication_error("directory_authority")
            identity, attributes = _phase_c1_windows_handle_information(
                authority.windows_handle,
            )
            if (
                identity != authority.stable_identity
                or not attributes & 0x00000010
                or attributes & 0x00000400
            ):
                raise _publication_error("directory_authority")
        else:
            if (
                authority.posix_descriptor is None
                or authority.windows_handle is not None
            ):
                raise _publication_error("directory_authority")
            opened = os.fstat(authority.posix_descriptor)
            if (
                not stat.S_ISDIR(opened.st_mode)
                or (int(opened.st_dev), int(opened.st_ino))
                != authority.stable_identity
            ):
                raise _publication_error("directory_authority")
        if _identity(authority.path, directory=True) != authority.stable_identity:
            raise _publication_error("directory_authority")
    except RunnerError:
        object.__setattr__(authority, "invalidated", True)
        raise
    except OSError as exc:
        object.__setattr__(authority, "invalidated", True)
        raise _publication_error("directory_authority") from exc


@contextmanager
def _held_phase_c1_directory_authority(
    path: Path,
    *,
    verify_on_exit: bool = True,
    delete_access: bool = False,
) -> Iterator[_HeldPhaseC1DirectoryAuthority]:
    target = Path(path)
    if (
        type(verify_on_exit) is not bool
        or type(delete_access) is not bool
    ):
        raise _publication_error("directory_authority")
    stable_identity = _identity(target, directory=True)
    if os.name == "nt":
        try:
            handle = _open_phase_c1_windows_directory_handle(
                target,
                access=(
                    0x80000000
                    | 0x40000000
                    | (0x00010000 if delete_access else 0)
                ),  # GENERIC_READ | GENERIC_WRITE | optional DELETE
                share_mode=0x00000001 | 0x00000002,  # no FILE_SHARE_DELETE
            )
        except OSError as exc:
            raise _publication_error("directory_authority") from exc
        active_error = False
        try:
            identity, attributes = _phase_c1_windows_handle_information(
                handle,
            )
            if (
                identity != stable_identity
                or not attributes & 0x00000010
                or attributes & 0x00000400
                or _identity(target, directory=True) != stable_identity
            ):
                raise _publication_error("directory_authority")
            authority = _HeldPhaseC1DirectoryAuthority(
                path=target,
                stable_identity=stable_identity,
                posix_descriptor=None,
                windows_handle=handle,
            )
            _verify_held_phase_c1_directory_authority(authority)
            yield authority
            if verify_on_exit and not authority.invalidated:
                _verify_held_phase_c1_directory_authority(authority)
        except BaseException:
            active_error = True
            raise
        finally:
            try:
                _close_phase_c1_windows_handle(handle)
            except OSError as exc:
                if not active_error:
                    raise _publication_error("directory_authority") from exc
        return

    directory_flag = getattr(os, "O_DIRECTORY", 0)
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not directory_flag or not nofollow_flag:
        raise _publication_error("directory_authority")
    try:
        descriptor = os.open(
            target,
            os.O_RDONLY | directory_flag | nofollow_flag,
        )
    except OSError as exc:
        raise _publication_error("directory_authority") from exc
    active_error = False
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or (int(opened.st_dev), int(opened.st_ino))
            != stable_identity
            or _identity(target, directory=True) != stable_identity
        ):
            raise _publication_error("directory_authority")
        authority = _HeldPhaseC1DirectoryAuthority(
            path=target,
            stable_identity=stable_identity,
            posix_descriptor=descriptor,
            windows_handle=None,
        )
        _verify_held_phase_c1_directory_authority(authority)
        yield authority
        if verify_on_exit and not authority.invalidated:
            _verify_held_phase_c1_directory_authority(authority)
    except BaseException:
        active_error = True
        raise
    finally:
        try:
            os.close(descriptor)
        except OSError as exc:
            if not active_error:
                raise _publication_error("directory_authority") from exc


@contextmanager
def _create_and_hold_phase_c1_stage_directory(
    path: Path,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> Iterator[_HeldPhaseC1DirectoryAuthority]:
    target = Path(path)
    if (
        type(parent_authority) is not _HeldPhaseC1DirectoryAuthority
        or target.parent != parent_authority.path
        or not target.name
        or target.name in {".", ".."}
        or "/" in target.name
        or "\\" in target.name
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(parent_authority)

    if os.name == "nt":
        try:
            target.mkdir()
        except OSError as exc:
            raise _publication_error("stage_create") from exc
        with _held_phase_c1_directory_authority(
            target,
        ) as authority:
            yield authority
        return

    directory_flag = getattr(os, "O_DIRECTORY", 0)
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if (
        parent_authority.posix_descriptor is None
        or parent_authority.windows_handle is not None
        or not directory_flag
        or not nofollow_flag
    ):
        raise _publication_error("directory_authority")
    try:
        os.mkdir(
            target.name,
            0o700,
            dir_fd=parent_authority.posix_descriptor,
        )
    except OSError as exc:
        raise _publication_error("stage_create") from exc

    descriptor: int | None = None
    active_error = False
    try:
        descriptor = os.open(
            target.name,
            os.O_RDONLY | directory_flag | nofollow_flag,
            dir_fd=parent_authority.posix_descriptor,
        )
        opened = os.fstat(descriptor)
        named = os.stat(
            target.name,
            dir_fd=parent_authority.posix_descriptor,
            follow_symlinks=False,
        )
        stable_identity = (
            int(opened.st_dev),
            int(opened.st_ino),
        )
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(named.st_mode)
            or (
                int(named.st_dev),
                int(named.st_ino),
            )
            != stable_identity
        ):
            raise _publication_error("directory_authority")
        authority = _HeldPhaseC1DirectoryAuthority(
            path=target,
            stable_identity=stable_identity,
            posix_descriptor=descriptor,
            windows_handle=None,
        )
        _verify_held_phase_c1_directory_authority(authority)
        yield authority
        if not authority.invalidated:
            _verify_held_phase_c1_directory_authority(authority)
    except BaseException:
        active_error = True
        raise
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError as exc:
                if not active_error:
                    raise _publication_error(
                        "directory_authority",
                    ) from exc


@contextmanager
def _phase_c1_bound_child_creation(
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> Iterator[None]:
    if (
        type(parent_authority) is not _HeldPhaseC1DirectoryAuthority
        or getattr(
            _PHASE_C1_FILE_CREATE_CONTEXT,
            "parent_authority",
            None,
        )
        is not None
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(parent_authority)
    _PHASE_C1_FILE_CREATE_CONTEXT.parent_authority = parent_authority
    try:
        yield
    finally:
        del _PHASE_C1_FILE_CREATE_CONTEXT.parent_authority


def _create_new_phase_c1_file_at_authority(
    path: Path,
    payload: bytes,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> object:
    target = Path(path)
    if (
        type(payload) is not bytes
        or type(parent_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or target.parent != parent_authority.path
        or not target.name
        or target.name in {".", ".."}
        or "/" in target.name
        or "\\" in target.name
    ):
        raise _publication_error("create_new")
    _verify_held_phase_c1_directory_authority(parent_authority)
    handle: object | None = None
    descriptor: int | None = None
    try:
        if os.name == "nt":
            if (
                parent_authority.windows_handle is None
                or parent_authority.posix_descriptor is not None
            ):
                raise _publication_error("directory_authority")
            # The held directory denies delete sharing, so the pathname cannot
            # be redirected between verification and this exclusive create.
            handle = open(target, "xb")
        else:
            if (
                parent_authority.posix_descriptor is None
                or parent_authority.windows_handle is not None
            ):
                raise _publication_error("directory_authority")
            nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
            if not nofollow_flag:
                raise _publication_error("create_new")
            descriptor = os.open(
                target.name,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | nofollow_flag,
                0o666,
                dir_fd=parent_authority.posix_descriptor,
            )
            handle = os.fdopen(descriptor, "wb")
            descriptor = None
        handle.write(payload)  # type: ignore[attr-defined]
        handle.flush()  # type: ignore[attr-defined]
        _verify_held_phase_c1_directory_authority(parent_authority)
        return handle
    except BaseException as exc:
        if handle is not None:
            try:
                handle.close()  # type: ignore[attr-defined]
            except OSError:
                pass
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if isinstance(exc, OSError):
            raise _publication_error("create_new") from exc
        raise


def _create_phase_c1_receipt_stage(
    path: Path,
    payload: bytes,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> object:
    target = Path(path)
    if (
        target.name
        not in {
            "candidate-receipt.stage",
            "candidate-validation.stage",
            "candidate-review.stage",
        }
        or target.parent != parent_authority.path
    ):
        raise _publication_error("receipt_stage")
    with _phase_c1_bound_child_creation(parent_authority):
        return _create_new_phase_c1_file(target, payload)


def _open_phase_c1_publication_lock_file(
    path: Path,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> object:
    target = Path(path)
    if (
        type(parent_authority) is not _HeldPhaseC1DirectoryAuthority
        or target.parent != parent_authority.path
        or target.name != "publication.lock"
    ):
        raise _publication_error("lock_open")
    _verify_held_phase_c1_directory_authority(parent_authority)
    handle: object | None = None
    descriptor: int | None = None
    try:
        if os.name == "nt":
            if (
                parent_authority.windows_handle is None
                or parent_authority.posix_descriptor is not None
            ):
                raise _publication_error("directory_authority")
            before = target.lstat()
            if (
                stat.S_ISLNK(before.st_mode)
                or getattr(before, "st_reparse_tag", 0)
                or not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
            ):
                raise _publication_error("lock_open")
            handle = open(target, "r+b")
            opened = os.fstat(handle.fileno())  # type: ignore[attr-defined]
            after = target.lstat()
        else:
            if (
                parent_authority.posix_descriptor is None
                or parent_authority.windows_handle is not None
            ):
                raise _publication_error("directory_authority")
            nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
            if not nofollow_flag:
                raise _publication_error("lock_open")
            before = os.stat(
                target.name,
                dir_fd=parent_authority.posix_descriptor,
                follow_symlinks=False,
            )
            descriptor = os.open(
                target.name,
                os.O_RDWR | nofollow_flag,
                0o666,
                dir_fd=parent_authority.posix_descriptor,
            )
            opened = os.fstat(descriptor)
            after = os.stat(
                target.name,
                dir_fd=parent_authority.posix_descriptor,
                follow_symlinks=False,
            )
            handle = os.fdopen(descriptor, "r+b")
            descriptor = None
        identities = tuple(
            (int(value.st_dev), int(value.st_ino))
            for value in (before, opened, after)
        )
        if (
            len(frozenset(identities)) != 1
            or any(
                not stat.S_ISREG(value.st_mode)
                or value.st_nlink != 1
                for value in (before, opened, after)
            )
        ):
            raise _publication_error("lock_open")
        handle.seek(0)  # type: ignore[attr-defined]
        if (
            handle.read()  # type: ignore[attr-defined]
            != b"phase-c1-publication-lock\n"
        ):
            raise _publication_error("lock_open")
        handle.seek(0)  # type: ignore[attr-defined]
        _verify_held_phase_c1_directory_authority(parent_authority)
        return handle
    except BaseException as exc:
        if handle is not None:
            try:
                handle.close()  # type: ignore[attr-defined]
            except OSError:
                pass
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if isinstance(exc, OSError):
            raise _publication_error("lock_open") from exc
        raise


def _rename_phase_c1_directory_at_authority(
    stage: Path,
    destination_name: str,
    *,
    authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    source = Path(stage)
    if (
        type(authority) is not _HeldPhaseC1DirectoryAuthority
        or not destination_name
        or destination_name in {".", ".."}
        or "/" in destination_name
        or "\\" in destination_name
    ):
        raise _publication_error("directory_authority")
    source_identity = _identity(source, directory=True)
    if os.name == "nt":
        if (
            authority.windows_handle is None
            or authority.posix_descriptor is not None
        ):
            raise _publication_error("directory_authority")
        try:
            source_handle = _open_phase_c1_windows_directory_handle(
                source,
                access=0x00010000,  # DELETE
                share_mode=0x00000001 | 0x00000002 | 0x00000004,
            )
        except OSError as exc:
            raise _publication_error("directory_rename") from exc
        active_error = False
        try:
            opened_identity, attributes = (
                _phase_c1_windows_handle_information(source_handle)
            )
            if (
                opened_identity != source_identity
                or not attributes & 0x00000010
                or attributes & 0x00000400
                or _identity(source, directory=True) != source_identity
            ):
                raise _publication_error("directory_rename")

            from ctypes import wintypes

            encoded_name = destination_name.encode("utf-16-le")

            class _FileRenameInformationEx(ctypes.Structure):
                _fields_ = (
                    ("flags", wintypes.DWORD),
                    ("root_directory", wintypes.HANDLE),
                    ("file_name_length", wintypes.DWORD),
                    ("file_name", wintypes.WCHAR * 1),
                )

            name_offset = _FileRenameInformationEx.file_name.offset
            information_size = name_offset + len(encoded_name)
            buffer = ctypes.create_string_buffer(information_size)
            information = _FileRenameInformationEx.from_buffer(buffer)
            information.flags = 0
            information.root_directory = authority.windows_handle
            information.file_name_length = len(encoded_name)
            ctypes.memmove(
                ctypes.addressof(buffer) + name_offset,
                encoded_name,
                len(encoded_name),
            )

            class _IoStatusBlock(ctypes.Structure):
                _fields_ = (
                    ("status", ctypes.c_void_p),
                    ("information", ctypes.c_size_t),
                )

            io_status = _IoStatusBlock()
            function = ctypes.WinDLL(
                "ntdll",
                use_last_error=True,
            ).NtSetInformationFile
            function.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(_IoStatusBlock),
                wintypes.LPVOID,
                wintypes.DWORD,
                ctypes.c_int,
            )
            function.restype = ctypes.c_long
            status_code = function(
                source_handle,
                ctypes.byref(io_status),
                buffer,
                information_size,
                65,  # FileRenameInformationEx
            )
            if status_code != 0:
                raise OSError(
                    status_code & 0xFFFFFFFF,
                    "unable to perform held-authority rename",
                )
        except BaseException:
            active_error = True
            raise
        finally:
            try:
                _close_phase_c1_windows_handle(source_handle)
            except OSError:
                if not active_error:
                    raise
        return

    if (
        authority.posix_descriptor is None
        or authority.windows_handle is not None
    ):
        raise _publication_error("directory_authority")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    nofollow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not directory_flag or not nofollow_flag:
        raise OSError(errno.ENOSYS, "held directory flags are unavailable")
    try:
        source_parent_descriptor = os.open(
            source.parent,
            os.O_RDONLY | directory_flag | nofollow_flag,
        )
    except OSError:
        raise
    try:
        opened_parent = os.fstat(source_parent_descriptor)
        source_parent_identity = _identity(source.parent, directory=True)
        if (
            not stat.S_ISDIR(opened_parent.st_mode)
            or (int(opened_parent.st_dev), int(opened_parent.st_ino))
            != source_parent_identity
        ):
            raise OSError(errno.ESTALE, "source parent identity changed")
        opened_source = os.stat(
            source.name,
            dir_fd=source_parent_descriptor,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISDIR(opened_source.st_mode)
            or (int(opened_source.st_dev), int(opened_source.st_ino))
            != source_identity
        ):
            raise OSError(errno.ESTALE, "source directory identity changed")
        library = ctypes.CDLL(None, use_errno=True)
        try:
            renameat2 = library.renameat2
        except AttributeError as exc:
            raise OSError(
                errno.ENOSYS,
                "renameat2 is unavailable",
            ) from exc
        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        if renameat2(
            source_parent_descriptor,
            os.fsencode(source.name),
            authority.posix_descriptor,
            os.fsencode(destination_name),
            1,  # RENAME_NOREPLACE
        ) != 0:
            error_number = ctypes.get_errno()
            raise OSError(
                error_number,
                os.strerror(error_number),
            )
    finally:
        os.close(source_parent_descriptor)


def _phase_c1_rename_collision(exc: OSError) -> bool:
    numbers = {
        value
        for value in (
            getattr(exc, "errno", None),
            getattr(exc, "winerror", None),
            exc.args[0] if exc.args else None,
        )
        if isinstance(value, int)
    }
    return bool(
        numbers
        & {
            errno.EEXIST,
            errno.ENOTEMPTY,
            80,  # ERROR_FILE_EXISTS
            183,  # ERROR_ALREADY_EXISTS
            0xC0000035,  # STATUS_OBJECT_NAME_COLLISION
        }
    )


def _rename_phase_c1_windows_regular_file_handle(
    handle: int,
    destination_name: str,
    *,
    destination_parent_handle: int,
    replace: bool,
) -> None:
    from ctypes import wintypes

    encoded_name = destination_name.encode("utf-16-le")

    class _FileRenameInformationEx(ctypes.Structure):
        _fields_ = (
            ("flags", wintypes.DWORD),
            ("root_directory", wintypes.HANDLE),
            ("file_name_length", wintypes.DWORD),
            ("file_name", wintypes.WCHAR * 1),
        )

    name_offset = _FileRenameInformationEx.file_name.offset
    information_size = name_offset + len(encoded_name)
    buffer = ctypes.create_string_buffer(information_size)
    information = _FileRenameInformationEx.from_buffer(buffer)
    information.flags = 0x00000001 if replace else 0
    information.root_directory = destination_parent_handle
    information.file_name_length = len(encoded_name)
    ctypes.memmove(
        ctypes.addressof(buffer) + name_offset,
        encoded_name,
        len(encoded_name),
    )

    class _IoStatusBlock(ctypes.Structure):
        _fields_ = (
            ("status", ctypes.c_void_p),
            ("information", ctypes.c_size_t),
        )

    io_status = _IoStatusBlock()
    function = ctypes.WinDLL(
        "ntdll",
        use_last_error=True,
    ).NtSetInformationFile
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_IoStatusBlock),
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.c_int,
    )
    function.restype = ctypes.c_long
    status_code = function(
        handle,
        ctypes.byref(io_status),
        buffer,
        information_size,
        65,  # FileRenameInformationEx
    )
    if status_code != 0:
        raise OSError(
            status_code & 0xFFFFFFFF,
            "unable to commit held regular file",
        )


def _renameat2_phase_c1_regular_file(
    source_name: str,
    destination_name: str,
    *,
    parent_descriptor: int,
    flags: int,
) -> None:
    library = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = library.renameat2
    except AttributeError as exc:
        raise OSError(
            errno.ENOSYS,
            "renameat2 is unavailable",
        ) from exc
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    if renameat2(
        parent_descriptor,
        os.fsencode(source_name),
        parent_descriptor,
        os.fsencode(destination_name),
        flags,
    ) != 0:
        error_number = ctypes.get_errno()
        raise OSError(
            error_number,
            os.strerror(error_number),
        )


def _commit_phase_c1_regular_file_at_authority(
    active_stage: _HeldPhaseC1RegularFileAuthority,
    destination_name: str,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    replace: bool,
    predecessor_authority: _HeldPhaseC1RegularFileAuthority | None,
) -> None:
    if (
        type(active_stage) is not _HeldPhaseC1RegularFileAuthority
        or type(parent_authority) is not _HeldPhaseC1DirectoryAuthority
        or type(replace) is not bool
        or not destination_name
        or destination_name in {".", ".."}
        or "/" in destination_name
        or "\\" in destination_name
        or active_stage.path.parent != parent_authority.path
    ):
        raise _publication_error("regular_file_commit")
    destination = parent_authority.path / destination_name
    if predecessor_authority is not None and (
        type(predecessor_authority)
        is not _HeldPhaseC1RegularFileAuthority
        or predecessor_authority.path != destination
        or predecessor_authority.closed
        or not replace
    ):
        raise _publication_error("regular_file_commit")
    _verify_held_phase_c1_directory_authority(parent_authority)
    _verify_held_phase_c1_regular_file_authority(active_stage)
    if predecessor_authority is not None:
        _verify_held_phase_c1_regular_file_authority(
            predecessor_authority,
        )

    if os.name == "nt":
        if (
            parent_authority.windows_handle is None
            or parent_authority.posix_descriptor is not None
            or active_stage.windows_handle is None
            or active_stage.posix_descriptor is not None
        ):
            raise _publication_error("regular_file_commit")
        replace_existing = predecessor_authority is not None
        if predecessor_authority is not None:
            # Windows cannot replace a destination while its own handle denies
            # delete sharing. Release it only after exact identity/byte
            # verification. The exclusive publication lock is the controlled
            # single-writer boundary for this intentionally tiny release-to-
            # rename window; this is not hostile-process conditional replace.
            _close_held_phase_c1_regular_file_authority(
                predecessor_authority,
            )
        _rename_phase_c1_windows_regular_file_handle(
            active_stage.windows_handle,
            destination_name,
            destination_parent_handle=parent_authority.windows_handle,
            replace=replace_existing,
        )
    else:
        if (
            parent_authority.posix_descriptor is None
            or parent_authority.windows_handle is not None
            or active_stage.posix_descriptor is None
            or active_stage.windows_handle is not None
        ):
            raise _publication_error("regular_file_commit")
        _renameat2_phase_c1_regular_file(
            active_stage.path.name,
            destination_name,
            parent_descriptor=parent_authority.posix_descriptor,
            flags=(
                0
                if predecessor_authority is not None
                else 1  # RENAME_NOREPLACE
            ),
        )
        if predecessor_authority is not None:
            _close_held_phase_c1_regular_file_authority(
                predecessor_authority,
            )

    active_stage.path = destination
    _verify_held_phase_c1_regular_file_authority(active_stage)
    _verify_held_phase_c1_directory_authority(parent_authority)


def _publish_phase_c1_journal_stage_at_authority(
    target: Path,
    stage: Path,
    *,
    expected_payload: bytes,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    stage_authority: _HeldPhaseC1RegularFileAuthority,
    predecessor_authority: _HeldPhaseC1RegularFileAuthority | None,
) -> None:
    destination = Path(target)
    source = Path(stage)
    if (
        type(expected_payload) is not bytes
        or destination.parent != parent_authority.path
        or source.parent != parent_authority.path
        or stage_authority.path != source
        or (
            predecessor_authority is not None
            and predecessor_authority.path != destination
        )
    ):
        raise _publication_error("journal_replace")
    _verify_held_phase_c1_regular_file_authority(stage_authority)
    if (
        _read_held_phase_c1_regular_file_bytes(stage_authority)
        != expected_payload
    ):
        raise _publication_error("journal_replace")
    try:
        _commit_phase_c1_regular_file_at_authority(
            stage_authority,
            destination.name,
            parent_authority=parent_authority,
            replace=True,
            predecessor_authority=predecessor_authority,
        )
    except OSError as exc:
        raise _publication_error("journal_replace") from exc


def _publish_phase_c1_receipt_stage_at_authority(
    target: Path,
    stage: Path,
    *,
    expected_payload: bytes,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    stage_authority: _HeldPhaseC1RegularFileAuthority,
) -> None:
    destination = Path(target)
    source = Path(stage)
    if (
        type(expected_payload) is not bytes
        or destination.parent != parent_authority.path
        or source.parent != parent_authority.path
        or stage_authority.path != source
    ):
        raise _publication_error("receipt_rename")
    _verify_held_phase_c1_regular_file_authority(stage_authority)
    if (
        _read_held_phase_c1_regular_file_bytes(stage_authority)
        != expected_payload
    ):
        raise _publication_error("receipt_rename")
    try:
        _commit_phase_c1_regular_file_at_authority(
            stage_authority,
            destination.name,
            parent_authority=parent_authority,
            replace=False,
            predecessor_authority=None,
        )
    except OSError as exc:
        if _phase_c1_rename_collision(exc):
            raise _publication_error("target_exists") from exc
        raise _publication_error("receipt_rename") from exc


def _rename_phase_c1_directory_no_overwrite(
    target: Path,
    stage: Path,
    *,
    authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    destination = Path(target)
    source = Path(stage)
    if (
        type(authority) is not _HeldPhaseC1DirectoryAuthority
        or destination.parent != authority.path
        or not destination.name
        or destination.name in {".", ".."}
        or "/" in destination.name
        or "\\" in destination.name
    ):
        raise _publication_error("directory_authority")
    _identity(source, directory=True)
    _verify_held_phase_c1_directory_authority(authority)
    try:
        _rename_phase_c1_directory_at_authority(
            source,
            destination.name,
            authority=authority,
        )
    except OSError as exc:
        _verify_held_phase_c1_directory_authority(authority)
        if _phase_c1_rename_collision(exc):
            raise _publication_error("target_exists") from exc
        raise _publication_error("directory_rename") from exc
    _verify_held_phase_c1_directory_authority(authority)


def _fsync_phase_c1_directory(
    path: Path,
    *,
    authority: _HeldPhaseC1DirectoryAuthority | None = None,
) -> None:
    if authority is not None:
        if (
            type(authority) is not _HeldPhaseC1DirectoryAuthority
            or Path(path) != authority.path
        ):
            raise _publication_error("directory_authority")
        _verify_held_phase_c1_directory_authority(authority)
        try:
            if os.name == "nt":
                if authority.windows_handle is None:
                    raise _publication_error("directory_authority")
                from ctypes import wintypes

                function = ctypes.WinDLL(
                    "kernel32",
                    use_last_error=True,
                ).FlushFileBuffers
                function.argtypes = (wintypes.HANDLE,)
                function.restype = wintypes.BOOL
                if not function(authority.windows_handle):
                    raise OSError(
                        ctypes.get_last_error(),
                        "unable to flush held directory authority",
                    )
            else:
                if authority.posix_descriptor is None:
                    raise _publication_error("directory_authority")
                os.fsync(authority.posix_descriptor)
        except OSError as exc:
            raise _publication_error("directory_fsync") from exc
        _verify_held_phase_c1_directory_authority(authority)
        return

    _identity(path, directory=True)
    if os.name == "nt":
        try:
            _flush_phase_c1_windows_directory(path)
        except OSError as exc:
            raise _publication_error("directory_fsync") from exc
        return
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise _publication_error("directory_fsync") from exc


def _validate_and_rename_phase_c1_directory(
    target: Path,
    stage: Path,
    state: _PreparedPhaseC1State,
    *,
    authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    _validate_phase_c1_pair_at_path(stage, state)
    _rename_phase_c1_directory_no_overwrite(
        target,
        stage,
        authority=authority,
    )


def _rename_phase_c1_file_no_overwrite(
    target: Path,
    stage: Path,
    *,
    expected_payload: bytes,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    stage_authority: _HeldPhaseC1RegularFileAuthority,
) -> None:
    _publish_phase_c1_receipt_stage_at_authority(
        target,
        stage,
        expected_payload=expected_payload,
        parent_authority=parent_authority,
        stage_authority=stage_authority,
    )
    _transition_phase_c1_windows_regular_file_to_readback(
        stage_authority,
        parent_authority=parent_authority,
    )


def _replace_phase_c1_file(
    target: Path,
    stage: Path,
    *,
    expected_payload: bytes,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    stage_authority: _HeldPhaseC1RegularFileAuthority,
    predecessor_authority: _HeldPhaseC1RegularFileAuthority | None,
) -> None:
    _publish_phase_c1_journal_stage_at_authority(
        target,
        stage,
        expected_payload=expected_payload,
        parent_authority=parent_authority,
        stage_authority=stage_authority,
        predecessor_authority=predecessor_authority,
    )
    _transition_phase_c1_windows_regular_file_to_readback(
        stage_authority,
        parent_authority=parent_authority,
    )


def _delete_phase_c1_windows_open_handle(handle: int) -> None:
    from ctypes import wintypes

    class _FileDispositionInformation(ctypes.Structure):
        _fields_ = (("delete_file", wintypes.BOOL),)

    information = _FileDispositionInformation(True)
    function = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    ).SetFileInformationByHandle
    function.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    )
    function.restype = wintypes.BOOL
    if not function(
        handle,
        4,  # FileDispositionInfo
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        raise OSError(
            ctypes.get_last_error(),
            "unable to delete held publication target",
        )


def _delete_held_phase_c1_regular_file(
    authority: _HeldPhaseC1RegularFileAuthority,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    if (
        type(authority) is not _HeldPhaseC1RegularFileAuthority
        or type(parent_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or authority.path.parent != parent_authority.path
    ):
        raise _publication_error("cleanup_target")
    _verify_held_phase_c1_directory_authority(parent_authority)
    _verify_held_phase_c1_regular_file_authority(authority)
    try:
        if os.name == "nt":
            if (
                authority.windows_handle is None
                or parent_authority.windows_handle is None
            ):
                raise _publication_error("cleanup_target")
            _delete_phase_c1_windows_open_handle(
                authority.windows_handle,
            )
            _close_held_phase_c1_regular_file_authority(authority)
        else:
            if (
                authority.posix_descriptor is None
                or parent_authority.posix_descriptor is None
            ):
                raise _publication_error("cleanup_target")
            observed = os.stat(
                authority.path.name,
                dir_fd=parent_authority.posix_descriptor,
                follow_symlinks=False,
            )
            if (
                not stat.S_ISREG(observed.st_mode)
                or (int(observed.st_dev), int(observed.st_ino))
                != authority.stable_identity
            ):
                raise _publication_error("cleanup_target")
            os.unlink(
                authority.path.name,
                dir_fd=parent_authority.posix_descriptor,
            )
            deleted = os.fstat(authority.posix_descriptor)
            if (
                (int(deleted.st_dev), int(deleted.st_ino))
                != authority.stable_identity
                or deleted.st_nlink != 0
            ):
                raise _publication_error("cleanup_target")
            _close_held_phase_c1_regular_file_authority(authority)
    except OSError as exc:
        raise _publication_error("cleanup") from exc
    if os.path.lexists(authority.path):
        raise _publication_error("cleanup")
    _verify_held_phase_c1_directory_authority(parent_authority)


def _phase_c1_directory_child_names(
    authority: _HeldPhaseC1DirectoryAuthority,
) -> frozenset[str]:
    _verify_held_phase_c1_directory_authority(authority)
    try:
        if os.name == "nt":
            return frozenset(
                child.name for child in authority.path.iterdir()
            )
        if authority.posix_descriptor is None:
            raise _publication_error("directory_authority")
        return frozenset(os.listdir(authority.posix_descriptor))
    except OSError as exc:
        raise _publication_error("cleanup_target") from exc


def _delete_held_phase_c1_directory_children(
    target: Path,
    *,
    expected_children: tuple[tuple[str, bytes], ...],
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    allowed_child_orders = (
        (),
        ("result.json",),
        ("report.md",),
        ("result.json", "report.md"),
    )
    child_names = tuple(name for name, _payload in expected_children)
    if (
        type(expected_children) is not tuple
        or child_names not in allowed_child_orders
        or any(
            type(name) is not str or type(payload) is not bytes
            for name, payload in expected_children
        )
        or type(root_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or Path(target).parent != root_authority.path
    ):
        raise _publication_error("cleanup_target")
    _verify_held_phase_c1_directory_authority(root_authority)
    with _held_phase_c1_directory_authority(
        target,
        verify_on_exit=False,
        delete_access=True,
    ) as target_authority:
        _verify_held_phase_c1_directory_authority(target_authority)
        if (
            _phase_c1_directory_child_names(target_authority)
            != frozenset(name for name, _payload in expected_children)
        ):
            raise _publication_error("cleanup_target")
        with ExitStack() as children:
            child_authorities = tuple(
                children.enter_context(
                    _held_phase_c1_regular_file_authority(
                        target / name,
                        expected_bytes=payload,
                    )
                )
                for name, payload in expected_children
            )
            _verify_held_phase_c1_directory_authority(
                target_authority,
            )
            for child_authority in child_authorities:
                _delete_held_phase_c1_regular_file(
                    child_authority,
                    parent_authority=target_authority,
                )
        if _phase_c1_directory_child_names(target_authority):
            raise _publication_error("cleanup_target")
        try:
            if os.name == "nt":
                if target_authority.windows_handle is None:
                    raise _publication_error("cleanup_target")
                _delete_phase_c1_windows_open_handle(
                    target_authority.windows_handle,
                )
            else:
                if root_authority.posix_descriptor is None:
                    raise _publication_error("cleanup_target")
                observed = os.stat(
                    target.name,
                    dir_fd=root_authority.posix_descriptor,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(observed.st_mode)
                    or (int(observed.st_dev), int(observed.st_ino))
                    != target_authority.stable_identity
                ):
                    raise _publication_error("cleanup_target")
                os.rmdir(
                    target.name,
                    dir_fd=root_authority.posix_descriptor,
                )
        except OSError as exc:
            raise _publication_error("cleanup") from exc
    if os.path.lexists(target):
        raise _publication_error("cleanup")
    _verify_held_phase_c1_directory_authority(root_authority)


def _delete_held_phase_c1_pair_directory(
    target: Path,
    *,
    result_bytes: bytes,
    report_bytes: bytes,
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    _delete_held_phase_c1_directory_children(
        target,
        expected_children=(
            ("result.json", result_bytes),
            ("report.md", report_bytes),
        ),
        root_authority=root_authority,
    )


def _delete_verified_phase_c1_cleanup_target(
    paths: PhaseC1RunnerPaths,
    target: Path,
    *,
    root_authority: _HeldPhaseC1DirectoryAuthority,
    expected_bytes: bytes | None = None,
    expected_pair: tuple[bytes, bytes] | None = None,
    allow_pair_cleanup_prefix: bool = False,
) -> None:
    allowed = (paths.candidate_root, paths.candidate_receipt_path, paths.candidate_validation_path, paths.candidate_review_path)
    if (
        target not in allowed
        or not _under(paths.ignored_root, target)
        or type(root_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or root_authority.path != paths.ignored_root
        or type(allow_pair_cleanup_prefix) is not bool
        or (
            target == paths.candidate_root
            and (
                expected_pair is None
                or len(expected_pair) != 2
                or any(type(item) is not bytes for item in expected_pair)
                or expected_bytes is not None
            )
        )
        or (
            target != paths.candidate_root
            and (
                expected_pair is not None
                or allow_pair_cleanup_prefix
            )
        )
    ):
        raise _publication_error("cleanup_target")
    _verify_held_phase_c1_directory_authority(root_authority)
    if not target.exists() and not target.is_symlink():
        return
    if target == paths.candidate_root:
        assert expected_pair is not None
        expected_children = (
            (
                ("result.json", expected_pair[0]),
                ("report.md", expected_pair[1]),
            )
            if not allow_pair_cleanup_prefix
            else tuple(
                (
                    name,
                    (
                        expected_pair[0]
                        if name == "result.json"
                        else expected_pair[1]
                    ),
                )
                for name in _validate_phase_c1_cleanup_prefix(
                    target,
                    result_bytes=expected_pair[0],
                    report_bytes=expected_pair[1],
                )
            )
        )
        _delete_held_phase_c1_directory_children(
            target,
            expected_children=expected_children,
            root_authority=root_authority,
        )
    else:
        if expected_bytes is None:
            raise _publication_error("cleanup_target")
        with _held_phase_c1_regular_file_authority(
            target,
            expected_bytes=expected_bytes,
        ) as target_authority:
            _delete_held_phase_c1_regular_file(
                target_authority,
                parent_authority=root_authority,
            )
    _verify_held_phase_c1_directory_authority(root_authority)


def _allowed_ignored_children(paths: PhaseC1RunnerPaths, *, operation: str) -> None:
    if not paths.ignored_root.exists():
        return
    _identity(paths.ignored_root, directory=True)
    allowed = {
        "source-cache", "research", "publication.lock", "publication-journal.json",
        "publication-journal.stage", "candidate", "candidate.stage", "canonical.stage",
        "candidate-receipt.json", "candidate-receipt.stage", "candidate-validation.json",
        "candidate-validation.stage", "candidate-review.json", "candidate-review.stage",
    }
    for child in paths.ignored_root.iterdir():
        if child.name not in allowed:
            raise _publication_error("ignored_child")
        _identity(child, directory=child.name in {"source-cache", "research", "candidate", "candidate.stage", "canonical.stage"})


def _ensure_ignored_root(paths: PhaseC1RunnerPaths) -> None:
    try:
        paths.ignored_root.mkdir(parents=True, exist_ok=True)
        paths.canonical_root.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise _publication_error("ignored_root") from exc
    _identity(paths.ignored_root, directory=True)


def _journal_payload(state: _PreparedPhaseC1State, *, status: str, sequence: int, previous: bytes | None, validation: bytes | None = None, review: bytes | None = None) -> bytes:
    receipt = _validate_candidate_receipt_bytes(state.candidate_receipt_bytes, state)
    payload: dict[str, object] = {
        "schema_version": "EmotionStatePhaseC1PublicationJournalV1",
        "checkpoint_id": CHECKPOINT_ID,
        "transaction_id": receipt["transaction_id"],
        "sequence": sequence,
        "previous_journal_sha256": "0" * 64 if previous is None else _digest(previous),
        "status": status,
        "expected_head": state.expected_head,
        "implementation_head": state.expected_head,
        "validator_blob_id": state.validator_blob_id,
        "protocol_sha256": _digest(state.protocol_bytes),
        "search_ledger_sha256": _digest(state.search_ledger_bytes),
        "source_evidence_ledger_sha256": _digest(state.source_ledger_bytes),
        "source_review_receipt_sha256": _digest(state.source_review_bytes),
        "result_sha256": _digest(state.result_bytes),
        "report_sha256": _digest(state.report_bytes),
        "candidate_receipt_sha256": _digest(state.candidate_receipt_bytes),
        "candidate_validation_sha256": None if validation is None else _digest(validation),
        "candidate_review_sha256": None if review is None else _digest(review),
        "journal_content_sha256": "",
    }
    if status == "accepted" and (validation is None or review is None):
        raise _publication_error("journal_receipts")
    payload["journal_content_sha256"] = _digest(phase_c1.canonical_json_bytes(payload))
    return phase_c1.canonical_json_bytes(payload)


def _validate_journal_bytes(payload: bytes, state: _PreparedPhaseC1State, *, predecessor: bytes | None = None) -> dict[str, object]:
    journal = _parse_exact_json(payload, source="journal")
    if set(journal) != _JOURNAL_FIELDS or journal.get("schema_version") != "EmotionStatePhaseC1PublicationJournalV1":
        raise _publication_error("journal")
    if journal.get("status") not in _JOURNAL_STATUSES or type(journal.get("sequence")) is not int or journal["sequence"] < 0:
        raise _publication_error("journal")
    selfless = dict(journal)
    actual = selfless.get("journal_content_sha256")
    selfless["journal_content_sha256"] = ""
    if type(actual) is not str or actual != _digest(phase_c1.canonical_json_bytes(selfless)):
        raise _publication_error("journal")
    expected_previous = "0" * 64 if predecessor is None else _digest(predecessor)
    previous_value = journal.get("previous_journal_sha256")
    if (
        (predecessor is not None and previous_value != expected_previous)
        or (predecessor is None and (type(previous_value) is not str or _HEX64.fullmatch(previous_value) is None))
        or (predecessor is None and journal["sequence"] == 0 and previous_value != expected_previous)
        or (predecessor is None and journal["sequence"] > 0 and previous_value == expected_previous)
    ):
        raise _publication_error("journal")
    if journal["status"] == "accepted" and state.operation == "accepted_cleanup_recovery" and (state.candidate_validation_bytes is None or state.candidate_review_bytes is None):
        expected = dict(journal)
        expected["candidate_receipt_sha256"] = _digest(state.candidate_receipt_bytes)
        expected["protocol_sha256"] = _digest(state.protocol_bytes)
        expected["search_ledger_sha256"] = _digest(state.search_ledger_bytes)
        expected["source_evidence_ledger_sha256"] = _digest(state.source_ledger_bytes)
        expected["source_review_receipt_sha256"] = _digest(state.source_review_bytes)
        expected["result_sha256"] = _digest(state.result_bytes)
        expected["report_sha256"] = _digest(state.report_bytes)
        expected["implementation_head"] = state.expected_head
        expected["expected_head"] = state.expected_head
        expected["validator_blob_id"] = state.validator_blob_id
        expected["checkpoint_id"] = CHECKPOINT_ID
    else:
        expected = _parse_exact_json(_journal_payload(state, status=str(journal["status"]), sequence=int(journal["sequence"]), previous=predecessor, validation=state.candidate_validation_bytes, review=state.candidate_review_bytes) if journal["status"] in {"staging_canonical", "accepted"} else _journal_payload(state, status=str(journal["status"]), sequence=int(journal["sequence"]), previous=predecessor), source="expected_journal")
    # Status/sequence/predecessor and optional receipt hashes are the only
    # transition-dependent values; every binding must equal this state.
    for key in _JOURNAL_FIELDS - {"status", "sequence", "previous_journal_sha256", "journal_content_sha256"}:
        if journal.get(key) != expected.get(key):
            raise _publication_error("journal")
    if journal["status"] == "accepted" and (journal["candidate_validation_sha256"] is None or journal["candidate_review_sha256"] is None):
        raise _publication_error("journal")
    return journal


def _validate_journal_envelope(
    payload: bytes,
    *,
    source: str,
) -> dict[str, object]:
    journal = _parse_exact_json(payload, source=source)
    if (
        set(journal) != _JOURNAL_FIELDS
        or journal.get("schema_version")
        != "EmotionStatePhaseC1PublicationJournalV1"
        or journal.get("status") not in _JOURNAL_STATUSES
        or type(journal.get("sequence")) is not int
        or journal["sequence"] < 0
    ):
        raise _publication_error("journal")
    selfless = dict(journal)
    actual = selfless.get("journal_content_sha256")
    selfless["journal_content_sha256"] = ""
    if (
        type(actual) is not str
        or actual != _digest(phase_c1.canonical_json_bytes(selfless))
    ):
        raise _publication_error("journal")
    previous = journal.get("previous_journal_sha256")
    if (
        type(previous) is not str
        or _HEX64.fullmatch(previous) is None
        or (journal["sequence"] == 0 and previous != "0" * 64)
        or (journal["sequence"] > 0 and previous == "0" * 64)
    ):
        raise _publication_error("journal")
    return journal


def _inspect_phase_c1_journal_stage(
    paths: PhaseC1RunnerPaths,
) -> tuple[
    bytes | None,
    dict[str, object] | None,
    bytes | None,
    dict[str, object] | None,
]:
    current_exists = (
        paths.publication_journal_path.exists()
        or paths.publication_journal_path.is_symlink()
    )
    stage_exists = (
        paths.publication_journal_stage_path.exists()
        or paths.publication_journal_stage_path.is_symlink()
    )
    current_bytes: bytes | None = None
    current_payload: dict[str, object] | None = None
    if current_exists:
        _identity(paths.publication_journal_path, directory=False)
        current_bytes = paths.publication_journal_path.read_bytes()
        current_payload = _validate_journal_envelope(
            current_bytes,
            source="journal",
        )
    stage_bytes: bytes | None = None
    stage_payload: dict[str, object] | None = None
    if stage_exists:
        _identity(paths.publication_journal_stage_path, directory=False)
        stage_bytes = paths.publication_journal_stage_path.read_bytes()
        stage_payload = _validate_journal_envelope(
            stage_bytes,
            source="journal_stage",
        )
        if current_bytes is None or current_payload is None:
            if (
                stage_payload["sequence"] != 0
                or stage_payload["previous_journal_sha256"]
                != "0" * 64
            ):
                raise _publication_error("journal_stage")
        elif (
            stage_payload["sequence"]
            != current_payload["sequence"] + 1
            or stage_payload["previous_journal_sha256"]
            != _digest(current_bytes)
        ):
            raise _publication_error("journal_stage")
    return current_bytes, current_payload, stage_bytes, stage_payload


def _read_valid_current_journal(
    state: _PreparedPhaseC1State,
    *,
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> tuple[bytes | None, dict[str, object] | None]:
    paths = state.paths
    if (
        type(root_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or root_authority.path != paths.ignored_root
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(root_authority)
    current, current_payload, stage, stage_payload = (
        _inspect_phase_c1_journal_stage(paths)
    )
    if stage is not None:
        assert stage_payload is not None
        if current is None or current_payload is None:
            _validate_journal_bytes(stage, state, predecessor=None)
            _require_legal_journal_transition(
                operation=state.operation,
                source=None,
                target=str(stage_payload["status"]),
            )
        else:
            _validate_journal_bytes(current, state)
            _validate_journal_bytes(
                stage,
                state,
                predecessor=current,
            )
            _require_legal_journal_transition(
                operation=state.operation,
                source=str(current_payload["status"]),
                target=str(stage_payload["status"]),
            )
        _delete_verified_stage(
            paths.publication_journal_stage_path,
            parent_authority=root_authority,
            expected_bytes=stage,
        )
    if current is None:
        return None, None
    return current, _validate_journal_bytes(current, state)


def _delete_verified_stage(
    path: Path,
    *,
    parent_authority: _HeldPhaseC1DirectoryAuthority,
    expected_bytes: bytes | None = None,
    expected_children: tuple[tuple[str, bytes], ...] | None = None,
) -> None:
    if (
        type(parent_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or Path(path).parent != parent_authority.path
        or (expected_bytes is None) == (expected_children is None)
        or (
            expected_bytes is not None
            and type(expected_bytes) is not bytes
        )
        or (
            expected_children is not None
            and (
                type(expected_children) is not tuple
                or len(expected_children) > 2
                or any(
                    type(name) is not str or type(payload) is not bytes
                    for name, payload in expected_children
                )
            )
        )
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(parent_authority)
    if expected_bytes is not None:
        with _held_phase_c1_regular_file_authority(
            path,
            expected_bytes=expected_bytes,
        ) as stage_authority:
            _delete_held_phase_c1_regular_file(
                stage_authority,
                parent_authority=parent_authority,
            )
    else:
        assert expected_children is not None
        _delete_held_phase_c1_directory_children(
            path,
            expected_children=expected_children,
            root_authority=parent_authority,
        )
    _verify_held_phase_c1_directory_authority(parent_authority)


def _require_legal_journal_transition(
    *,
    operation: str,
    source: str | None,
    target: str,
) -> None:
    if (operation, source, target) not in _LEGAL_JOURNAL_TRANSITIONS:
        raise _publication_error("journal_transition")


def _advance_journal(
    state: _PreparedPhaseC1State,
    *,
    status: str,
    current: bytes | None,
    root_authority: _HeldPhaseC1DirectoryAuthority | None = None,
) -> bytes:
    paths = state.paths
    current_journal = (
        None
        if current is None
        else _validate_journal_bytes(current, state)
    )
    _require_legal_journal_transition(
        operation=state.operation,
        source=(
            None
            if current_journal is None
            else str(current_journal["status"])
        ),
        target=status,
    )
    sequence = (
        0
        if current_journal is None
        else int(current_journal["sequence"]) + 1
    )
    payload = _journal_payload(state, status=status, sequence=sequence, previous=current, validation=state.candidate_validation_bytes, review=state.candidate_review_bytes)
    if (
        type(root_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or root_authority.path != paths.ignored_root
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(root_authority)
    owned_stage = False
    replaced_stage = False
    stage_authority: _HeldPhaseC1RegularFileAuthority | None = None
    with ExitStack() as authorities:
        predecessor_authority = (
            None
            if current is None
            else authorities.enter_context(
                _held_phase_c1_regular_file_authority(
                    paths.publication_journal_path,
                    expected_bytes=current,
                )
            )
        )
        if (
            predecessor_authority is None
            and (
                paths.publication_journal_path.exists()
                or paths.publication_journal_path.is_symlink()
            )
        ):
            raise _publication_error("journal")
        try:
            with _phase_c1_bound_child_creation(root_authority):
                handle = _create_new_phase_c1_file(
                    paths.publication_journal_stage_path, payload,
                )
            owned_stage = True
            try:
                _fsync_phase_c1_open_file(handle)
            finally:
                try:
                    handle.close()  # type: ignore[attr-defined]
                except OSError:
                    pass
            if paths.publication_journal_stage_path.read_bytes() != payload:
                raise _publication_error("journal_stage")
            _validate_journal_bytes(payload, state, predecessor=current)
            stage_authority = authorities.enter_context(
                _held_phase_c1_regular_file_authority(
                    paths.publication_journal_stage_path,
                    expected_bytes=payload,
                )
            )
            _replace_phase_c1_file(
                paths.publication_journal_path,
                paths.publication_journal_stage_path,
                expected_payload=payload,
                parent_authority=root_authority,
                stage_authority=stage_authority,
                predecessor_authority=predecessor_authority,
            )
            replaced_stage = True
            _fsync_phase_c1_directory(
                paths.ignored_root,
                authority=root_authority,
            )
            _verify_committed_phase_c1_regular_file(
                stage_authority,
                expected_payload=payload,
                stage_path=paths.publication_journal_stage_path,
                parent_authority=root_authority,
                error_code="journal",
            )
            return payload
        except BaseException:
            if (
                stage_authority is not None
                and not stage_authority.closed
            ):
                _close_held_phase_c1_regular_file_authority(
                    stage_authority,
                )
            if (
                owned_stage
                and not replaced_stage
                and paths.publication_journal_stage_path.is_file()
                and not paths.publication_journal_stage_path.is_symlink()
                and paths.publication_journal_stage_path.read_bytes() == payload
            ):
                _delete_verified_stage(
                    paths.publication_journal_stage_path,
                    parent_authority=root_authority,
                    expected_bytes=payload,
                )
            raise
        finally:
            owned_stage = False


def _write_pair(
    state: _PreparedPhaseC1State,
    *,
    stage: Path,
    target: Path,
    authority: _HeldPhaseC1DirectoryAuthority,
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    if (
        type(authority) is not _HeldPhaseC1DirectoryAuthority
        or target.parent != authority.path
        or type(root_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or root_authority.path != state.paths.ignored_root
        or stage.parent != root_authority.path
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(authority)
    _verify_held_phase_c1_directory_authority(root_authority)
    if stage.exists() or stage.is_symlink():
        raise _publication_error("pair_target_exists")
    try:
        with _create_and_hold_phase_c1_stage_directory(
            stage,
            parent_authority=root_authority,
        ) as stage_authority:
            # Acquire the stage authority before exposing any verification
            # seam after creation. POSIX child creation is then dirfd-bound;
            # Windows retains the cooperative publication lock and
            # non-delete-shared directory handles.
            _verify_held_phase_c1_directory_authority(root_authority)
            _verify_held_phase_c1_directory_authority(stage_authority)
            with _phase_c1_bound_child_creation(stage_authority):
                result = _create_new_phase_c1_file(
                    stage / "result.json",
                    state.result_bytes,
                )
                try:
                    _fsync_phase_c1_open_file(result)
                finally:
                    try:
                        result.close()  # type: ignore[attr-defined]
                    except OSError:
                        pass
                _verify_held_phase_c1_directory_authority(stage_authority)
                _verify_held_phase_c1_directory_authority(root_authority)
                report = _create_new_phase_c1_file(
                    stage / "report.md",
                    state.report_bytes,
                )
                try:
                    _fsync_phase_c1_open_file(report)
                finally:
                    try:
                        report.close()  # type: ignore[attr-defined]
                    except OSError:
                        pass
            _fsync_phase_c1_directory(
                stage,
                authority=stage_authority,
            )
            _verify_held_phase_c1_directory_authority(stage_authority)
            _validate_phase_c1_pair_at_path(stage, state)
            _verify_held_phase_c1_directory_authority(stage_authority)
    except BaseException:
        if stage.exists() and not stage.is_symlink():
            creation_prefix = _validate_phase_c1_stage_prefix(
                stage,
                state,
            )
            _delete_verified_stage(
                stage,
                parent_authority=root_authority,
                expected_children=tuple(
                    (
                        name,
                        (
                            state.result_bytes
                            if name == "result.json"
                            else state.report_bytes
                        ),
                    )
                    for name in creation_prefix
                ),
            )
        raise
    _verify_held_phase_c1_directory_authority(root_authority)
    _validate_and_rename_phase_c1_directory(
        target,
        stage,
        state,
        authority=authority,
    )
    _verify_held_phase_c1_directory_authority(root_authority)
    _fsync_phase_c1_directory(
        target.parent,
        authority=authority,
    )
    _validate_phase_c1_pair_at_path(target, state)


def _publish_candidate_receipt(
    state: _PreparedPhaseC1State,
    *,
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    paths = state.paths
    if (
        type(root_authority)
        is not _HeldPhaseC1DirectoryAuthority
        or root_authority.path != paths.ignored_root
    ):
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(root_authority)
    final_exists = (
        paths.candidate_receipt_path.exists()
        or paths.candidate_receipt_path.is_symlink()
    )
    stage_exists = (
        paths.candidate_receipt_stage_path.exists()
        or paths.candidate_receipt_stage_path.is_symlink()
    )
    if final_exists:
        if stage_exists:
            raise _publication_error("receipt_stage")
        _validate_phase_c1_candidate_receipt_at_path(paths.candidate_receipt_path, state)
        return
    if stage_exists:
        _identity(paths.candidate_receipt_stage_path, directory=False)
        if (
            paths.candidate_receipt_stage_path.read_bytes()
            != state.candidate_receipt_bytes
        ):
            raise _publication_error("receipt_stage")
        _validate_candidate_receipt_bytes(
            state.candidate_receipt_bytes,
            state,
        )
    else:
        _verify_held_phase_c1_directory_authority(root_authority)
        handle = _create_phase_c1_receipt_stage(
            paths.candidate_receipt_stage_path,
            state.candidate_receipt_bytes,
            parent_authority=root_authority,
        )
        try:
            _fsync_phase_c1_open_file(handle)
        finally:
            try:
                handle.close()  # type: ignore[attr-defined]
            except OSError:
                pass
        if (
            paths.candidate_receipt_stage_path.read_bytes()
            != state.candidate_receipt_bytes
        ):
            raise _publication_error("receipt_stage")
        _validate_candidate_receipt_bytes(
            state.candidate_receipt_bytes,
            state,
        )
    with _held_phase_c1_regular_file_authority(
        paths.candidate_receipt_stage_path,
        expected_bytes=state.candidate_receipt_bytes,
    ) as stage_authority:
        _rename_phase_c1_file_no_overwrite(
            paths.candidate_receipt_path,
            paths.candidate_receipt_stage_path,
            expected_payload=state.candidate_receipt_bytes,
            parent_authority=root_authority,
            stage_authority=stage_authority,
        )
        _fsync_phase_c1_directory(
            paths.ignored_root,
            authority=root_authority,
        )
        _verify_committed_phase_c1_regular_file(
            stage_authority,
            expected_payload=state.candidate_receipt_bytes,
            stage_path=paths.candidate_receipt_stage_path,
            parent_authority=root_authority,
            error_code="candidate_receipt",
        )
        try:
            _validate_phase_c1_candidate_receipt_at_path(
                paths.candidate_receipt_path,
                state,
            )
        except RunnerError:
            _restore_phase_c1_committed_regular_file(
                stage_authority,
                parent_authority=root_authority,
            )
            raise


def _validate_prepare_state(state: _PreparedPhaseC1State) -> None:
    paths = state.paths
    _assert_paths_shape(paths)
    if _current_repository_head() != state.expected_head:
        raise _publication_error("head")
    if _identity(paths.project_root, directory=True) != state.project_root_identity:
        raise _publication_error("root_identity")
    if _tracked_parent_identities(
        paths,
        include_canonical_target=state.operation
        in {"acceptance", "accepted_cleanup_recovery"},
    ) != state.parent_identities:
        raise _publication_error("parent_identity")
    inputs = _read_phase_c1_tracked_input_bytes(paths)
    if inputs != (state.protocol_bytes, state.search_ledger_bytes, state.source_ledger_bytes, state.source_review_bytes):
        raise _publication_error("tracked_changed")
    result = phase_c1.load_json_strict(state.result_bytes, source="result")
    if not isinstance(result, dict):
        raise _publication_error("result")
    validate_phase_c1_result_payload(result, protocol_bytes=state.protocol_bytes, search_ledger_bytes=state.search_ledger_bytes, source_ledger_bytes=state.source_ledger_bytes, review_receipt_bytes=state.source_review_bytes)
    if render_phase_c1_report(result, protocol_bytes=state.protocol_bytes, search_ledger_bytes=state.search_ledger_bytes, source_ledger_bytes=state.source_ledger_bytes, review_receipt_bytes=state.source_review_bytes) != state.report_bytes:
        raise _publication_error("report")
    if state.operation == "candidate" and (paths.canonical_root.exists() or paths.canonical_root.is_symlink()):
        raise _publication_error("canonical_exists")
    _allowed_ignored_children(paths, operation=state.operation)


def _new_prepared(state: _PreparedPhaseC1State) -> PreparedPhaseC1Publication:
    prepared = object.__new__(PreparedPhaseC1Publication)
    with _PUBLICATION_STATE_LOCK:
        _PREPARED_PUBLICATION_STATES[prepared] = state
    return prepared


def _state_for(prepared: object) -> _PreparedPhaseC1State:
    if not isinstance(prepared, PreparedPhaseC1Publication):
        raise _publication_error("prepared")
    with _PUBLICATION_STATE_LOCK:
        state = _PREPARED_PUBLICATION_STATES.get(prepared)
    if state is None:
        raise _publication_error("prepared")
    return state


def prepare_phase_c1_candidate(*, expected_head: str) -> PreparedPhaseC1Publication:
    if type(expected_head) is not str or _HEX40.fullmatch(expected_head) is None:
        raise _publication_error("expected_head")
    paths = PRODUCTION_PATHS
    _assert_paths_shape(paths)
    if _current_repository_head() != expected_head:
        raise _publication_error("head")
    validator_state = _resolve_phase_c1_validator_state(expected_head)
    blob = validator_state.get("validator_blob_id")
    if validator_state.get("repository_head") != expected_head or validator_state.get("is_clean") is not True or type(blob) is not str or _HEX40.fullmatch(blob) is None:
        raise _publication_error("validator_state")
    inputs = _read_phase_c1_tracked_input_bytes(paths)
    result = build_phase_c1_result(head_commit=expected_head, validator_blob_id=blob, protocol_bytes=inputs[0], search_ledger_bytes=inputs[1], source_ledger_bytes=inputs[2], review_receipt_bytes=inputs[3])
    result_bytes = phase_c1.canonical_json_bytes(result)
    report_bytes = render_phase_c1_report(result, protocol_bytes=inputs[0], search_ledger_bytes=inputs[1], source_ledger_bytes=inputs[2], review_receipt_bytes=inputs[3])
    state = _PreparedPhaseC1State(
        paths,
        _identity(paths.project_root, directory=True),
        _tracked_parent_identities(paths),
        expected_head,
        blob,
        "candidate",
        inputs[0],
        inputs[1],
        inputs[2],
        inputs[3],
        result_bytes,
        report_bytes,
        b"",
        None,
        None,
    )
    receipt = _make_candidate_receipt(state)
    return _new_prepared(_PreparedPhaseC1State(paths=state.paths, project_root_identity=state.project_root_identity, parent_identities=state.parent_identities, expected_head=state.expected_head, validator_blob_id=state.validator_blob_id, operation=state.operation, protocol_bytes=state.protocol_bytes, search_ledger_bytes=state.search_ledger_bytes, source_ledger_bytes=state.source_ledger_bytes, source_review_bytes=state.source_review_bytes, result_bytes=state.result_bytes, report_bytes=state.report_bytes, candidate_receipt_bytes=receipt, candidate_validation_bytes=None, candidate_review_bytes=None))


def _read_exact_receipt(path: Path, *, name: str) -> bytes:
    if path.name != name:
        raise _publication_error("receipt_name")
    _identity(path, directory=False)
    return path.read_bytes()


def _validate_validation_and_review(state: _PreparedPhaseC1State, validation: bytes, review: bytes) -> None:
    candidate = _validate_candidate_receipt_bytes(state.candidate_receipt_bytes, state)
    validation_payload = _parse_exact_json(validation, source="candidate_validation")
    expected_validation = {
        "schema_version": "EmotionStatePhaseC1CandidateValidationV1",
        "checkpoint_id": CHECKPOINT_ID,
        "implementation_head": state.expected_head,
        "candidate_transaction_id": candidate["transaction_id"],
        "candidate_result_sha256": _digest(state.result_bytes),
        "candidate_report_sha256": _digest(state.report_bytes),
        "protocol_sha256": _digest(state.protocol_bytes),
        "search_ledger_sha256": _digest(state.search_ledger_bytes),
        "source_evidence_ledger_sha256": _digest(state.source_ledger_bytes),
        "source_review_receipt_sha256": _digest(state.source_review_bytes),
        "validator_blob_id": state.validator_blob_id,
        "verdict": "pass",
        "runtime_approved": False,
    }
    if validation_payload != expected_validation:
        raise _publication_error("candidate_validation")
    review_payload = _parse_exact_json(review, source="candidate_review")
    expected_review = {
        "schema_version": "EmotionStatePhaseC1CandidateReviewV1",
        "checkpoint_id": CHECKPOINT_ID,
        "candidate_transaction_id": candidate["transaction_id"],
        "implementation_head": state.expected_head,
        "candidate_result_sha256": _digest(state.result_bytes),
        "candidate_report_sha256": _digest(state.report_bytes),
        "candidate_validation_sha256": _digest(validation),
        "review_scope": "all_candidate_inputs_decisions_pair_report_and_boundaries",
        "verdict": "admitted",
        "critical_findings": 0,
        "important_findings": 0,
        "minor_findings": 0,
        "raw_rows_read": False,
        "private_data_read": False,
        "model_evaluation_run": False,
        "provider_accessed": False,
        "runtime_modified": False,
    }
    if review_payload != expected_review:
        raise _publication_error("candidate_review")


def _state_from_candidate_receipt(*, expected_head: str, paths: PhaseC1RunnerPaths, candidate_receipt: bytes, validation: bytes | None, review: bytes | None, result: bytes, report: bytes) -> _PreparedPhaseC1State:
    if _current_repository_head() != expected_head:
        raise _publication_error("head")
    validator_state = _resolve_phase_c1_validator_state(expected_head)
    blob = validator_state.get("validator_blob_id")
    if validator_state.get("repository_head") != expected_head or validator_state.get("is_clean") is not True or type(blob) is not str or _HEX40.fullmatch(blob) is None:
        raise _publication_error("validator_state")
    inputs = _read_phase_c1_tracked_input_bytes(paths)
    state = _PreparedPhaseC1State(paths=paths, project_root_identity=_identity(paths.project_root, directory=True), parent_identities=_tracked_parent_identities(paths, include_canonical_target=True), expected_head=expected_head, validator_blob_id=blob, operation="acceptance", protocol_bytes=inputs[0], search_ledger_bytes=inputs[1], source_ledger_bytes=inputs[2], source_review_bytes=inputs[3], result_bytes=result, report_bytes=report, candidate_receipt_bytes=candidate_receipt, candidate_validation_bytes=validation, candidate_review_bytes=review)
    _validate_candidate_receipt_bytes(candidate_receipt, state)
    _validate_phase_c1_pair_at_path(paths.candidate_root, state)
    if validation is not None and review is not None:
        _validate_validation_and_review(state, validation, review)
    return state


def _prepare_phase_c1_acceptance(*, expected_head: str, candidate_receipt_name: str, candidate_validation_name: str, candidate_review_name: str) -> PreparedPhaseC1Publication:
    if (candidate_receipt_name, candidate_validation_name, candidate_review_name) != ("candidate-receipt.json", "candidate-validation.json", "candidate-review.json"):
        raise _publication_error("receipt_name")
    if type(expected_head) is not str or _HEX40.fullmatch(expected_head) is None:
        raise _publication_error("expected_head")
    paths = PRODUCTION_PATHS
    _assert_paths_shape(paths)
    _allowed_ignored_children(paths, operation="acceptance")
    (
        journal_bytes,
        journal_envelope,
        _journal_stage_bytes,
        _journal_stage_envelope,
    ) = _inspect_phase_c1_journal_stage(paths)
    journal_status = (
        None
        if journal_envelope is None
        else str(journal_envelope["status"])
    )
    for stage in (paths.candidate_receipt_stage_path, paths.candidate_validation_stage_path, paths.candidate_review_stage_path):
        if stage.exists() or stage.is_symlink():
            raise _publication_error("receipt_stage")
    # Accepted recovery is deliberately handled before candidate-artifact
    # requirements: cleanup may legitimately have removed any subset.
    if journal_status == "accepted":
        if not paths.canonical_root.exists():
            raise _publication_error("canonical_journal")
        assert journal_bytes is not None
        if paths.publication_journal_stage_path.exists() or paths.publication_journal_stage_path.is_symlink():
            raise _publication_error("journal_stage")
        # Build a state from the canonical pair and trusted journal bindings.
        _identity(paths.canonical_root, directory=True)
        result = (paths.canonical_root / "result.json").read_bytes()
        report = (paths.canonical_root / "report.md").read_bytes()
        # Candidate receipt is reproducible from the pair and current inputs.
        inputs = _read_phase_c1_tracked_input_bytes(paths)
        resolver = _resolve_phase_c1_validator_state(expected_head)
        blob = resolver.get("validator_blob_id")
        if resolver.get("repository_head") != expected_head or resolver.get("is_clean") is not True or type(blob) is not str:
            raise _publication_error("validator_state")
        blank = _PreparedPhaseC1State(paths, _identity(paths.project_root, directory=True), _tracked_parent_identities(paths, include_canonical_target=True), expected_head, blob, "accepted_cleanup_recovery", inputs[0], inputs[1], inputs[2], inputs[3], result, report, b"", None, None)
        receipt = _make_candidate_receipt(blank)
        validation = paths.candidate_validation_path.read_bytes() if paths.candidate_validation_path.exists() else None
        review = paths.candidate_review_path.read_bytes() if paths.candidate_review_path.exists() else None
        state = _PreparedPhaseC1State(paths, blank.project_root_identity, blank.parent_identities, expected_head, blob, "accepted_cleanup_recovery", *inputs, result, report, receipt, validation, review)
        journal = _validate_journal_bytes(journal_bytes, state, predecessor=None)
        if journal.get("status") != "accepted" or journal.get("candidate_receipt_sha256") != _digest(receipt):
            raise _publication_error("journal")
        _validate_phase_c1_pair_at_path(paths.canonical_root, state)
        for path, expected_hash in ((paths.candidate_validation_path, journal.get("candidate_validation_sha256")), (paths.candidate_review_path, journal.get("candidate_review_sha256"))):
            if path.exists() and _digest(path.read_bytes()) != expected_hash:
                raise _publication_error("accepted_receipt")
        return _new_prepared(state)
    if journal_status not in {"candidate_ready", "staging_canonical"}:
        raise _publication_error("journal")
    candidate_receipt = _read_exact_receipt(paths.candidate_receipt_path, name="candidate-receipt.json")
    validation = _read_exact_receipt(paths.candidate_validation_path, name="candidate-validation.json")
    review = _read_exact_receipt(paths.candidate_review_path, name="candidate-review.json")
    _identity(paths.candidate_root, directory=True)
    result = (paths.candidate_root / "result.json").read_bytes()
    report = (paths.candidate_root / "report.md").read_bytes()
    state = _state_from_candidate_receipt(expected_head=expected_head, paths=paths, candidate_receipt=candidate_receipt, validation=validation, review=review, result=result, report=report)
    assert journal_bytes is not None
    journal_payload = _validate_journal_bytes(
        journal_bytes, state, predecessor=None,
    )
    if paths.canonical_root.exists() or paths.canonical_root.is_symlink():
        if journal_payload.get("status") != "staging_canonical":
            raise _publication_error("canonical_journal")
        _validate_phase_c1_pair_at_path(paths.canonical_root, state)
    return _new_prepared(state)


@contextmanager
def persistent_phase_c1_publication_lock(prepared: PreparedPhaseC1Publication) -> Iterator[PhaseC1PublicationLockCapability]:
    state = _state_for(prepared)
    _assert_paths_shape(state.paths)
    if _identity(state.paths.project_root, directory=True) != state.project_root_identity:
        raise _publication_error("root_identity")
    _ensure_ignored_root(state.paths)
    with _held_phase_c1_directory_authority(
        state.paths.ignored_root,
        verify_on_exit=False,
    ) as ignored_root_authority:
        _verify_held_phase_c1_directory_authority(
            ignored_root_authority,
        )
        lock_path = state.paths.publication_lock_path
        if lock_path.exists() or lock_path.is_symlink():
            _identity(lock_path, directory=False)
        else:
            with _phase_c1_bound_child_creation(
                ignored_root_authority,
            ):
                handle = _create_new_phase_c1_file(
                    lock_path,
                    b"phase-c1-publication-lock\n",
                )
            try:
                _fsync_phase_c1_open_file(handle)
            finally:
                try:
                    handle.close()  # type: ignore[attr-defined]
                except OSError:
                    pass
        handle = _open_phase_c1_publication_lock_file(
            lock_path,
            parent_authority=ignored_root_authority,
        )
        locked = False
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                try:
                    msvcrt.locking(
                        handle.fileno(),
                        msvcrt.LK_NBLCK,
                        1,
                    )
                except OSError as exc:
                    raise _publication_error("lock_busy") from exc
            else:
                import fcntl
                try:
                    fcntl.flock(
                        handle.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB,
                    )
                except OSError as exc:
                    raise _publication_error("lock_busy") from exc
            locked = True
            _verify_held_phase_c1_directory_authority(
                ignored_root_authority,
            )
            capability = object.__new__(
                PhaseC1PublicationLockCapability,
            )
            with _PUBLICATION_STATE_LOCK:
                _LOCK_CAPABILITY_STATES[capability] = _LockState(
                    prepared,
                    state.operation,
                    _identity(
                        state.paths.project_root,
                        directory=True,
                    ),
                    handle,
                    ignored_root_authority,
                )
            try:
                yield capability
            finally:
                with _PUBLICATION_STATE_LOCK:
                    _LOCK_CAPABILITY_STATES.pop(capability, None)
        finally:
            if locked:
                try:
                    if os.name == "nt":
                        import msvcrt
                        handle.seek(0)
                        msvcrt.locking(
                            handle.fileno(),
                            msvcrt.LK_UNLCK,
                            1,
                        )
                    else:
                        import fcntl
                        fcntl.flock(
                            handle.fileno(),
                            fcntl.LOCK_UN,
                        )
                except OSError:
                    pass
            handle.close()


def _consume_capability(
    prepared: PreparedPhaseC1Publication,
    capability: object,
) -> tuple[
    _PreparedPhaseC1State,
    _HeldPhaseC1DirectoryAuthority,
]:
    state = _state_for(prepared)
    if not isinstance(capability, PhaseC1PublicationLockCapability):
        raise _publication_error("capability")
    with _PUBLICATION_STATE_LOCK:
        binding = _LOCK_CAPABILITY_STATES.get(capability)
    if binding is None or binding.prepared is not prepared or binding.operation != state.operation or binding.root_identity != _identity(state.paths.project_root, directory=True):
        raise _publication_error("capability")
    with _PUBLICATION_STATE_LOCK:
        _PREPARED_PUBLICATION_STATES.pop(prepared, None)
    return state, binding.ignored_root_authority


def _recover_candidate(
    state: _PreparedPhaseC1State,
    current: bytes | None,
    journal: dict[str, object] | None,
    *,
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> PhaseC1PublicationReceipt:
    paths = state.paths
    _verify_held_phase_c1_directory_authority(root_authority)
    if journal is not None and journal["status"] not in {"staging_candidate", "candidate_ready"}:
        raise _publication_error("journal")
    if paths.canonical_stage_path.exists() or paths.canonical_stage_path.is_symlink():
        raise _publication_error("canonical_stage")
    if journal is None and (
        paths.candidate_root.exists()
        or paths.candidate_root.is_symlink()
    ):
        raise _publication_error("candidate_root")
    if journal is not None and journal["status"] == "candidate_ready":
        if (
            paths.candidate_stage_path.exists()
            or paths.candidate_stage_path.is_symlink()
        ):
            raise _publication_error("candidate_stage")
        _validate_phase_c1_pair_at_path(paths.candidate_root, state)
        _validate_phase_c1_candidate_receipt_at_path(
            paths.candidate_receipt_path, state,
        )
        transaction = _parse_exact_json(
            state.candidate_receipt_bytes, source="receipt",
        )["transaction_id"]
        return PhaseC1PublicationReceipt(
            "candidate_ready", str(transaction),
        )
    if paths.candidate_stage_path.exists() or paths.candidate_stage_path.is_symlink():
        if paths.candidate_root.exists():
            raise _publication_error("candidate_stage")
        stage_prefix = _validate_phase_c1_cleanup_prefix(
            paths.candidate_stage_path,
            result_bytes=state.result_bytes,
            report_bytes=state.report_bytes,
            allow_result_only=(
                journal is not None
                and journal.get("status") == "staging_candidate"
            ),
        )
        if journal is None:
            if stage_prefix != ("result.json", "report.md"):
                raise _publication_error("candidate_stage")
            current = _advance_journal(
                state,
                status="staging_candidate",
                current=None,
                root_authority=root_authority,
            )
            journal = _validate_journal_bytes(
                current,
                state,
                predecessor=None,
            )
        elif journal.get("status") != "staging_candidate":
            raise _publication_error("candidate_stage")
        _delete_verified_stage(
            paths.candidate_stage_path,
            parent_authority=root_authority,
            expected_children=tuple(
                (
                    name,
                    (
                        state.result_bytes
                        if name == "result.json"
                        else state.report_bytes
                    ),
                )
                for name in stage_prefix
            ),
        )
    if not paths.candidate_root.exists():
        current = _advance_journal(
            state,
            status="staging_candidate",
            current=current,
            root_authority=root_authority,
        ) if journal is None else current
        _write_pair(
            state,
            stage=paths.candidate_stage_path,
            target=paths.candidate_root,
            authority=root_authority,
            root_authority=root_authority,
        )
    else:
        _validate_phase_c1_pair_at_path(paths.candidate_root, state)
        if journal is None:
            current = _advance_journal(
                state,
                status="staging_candidate",
                current=None,
                root_authority=root_authority,
            )
    _publish_candidate_receipt(
        state,
        root_authority=root_authority,
    )
    _advance_journal(
        state,
        status="candidate_ready",
        current=current,
        root_authority=root_authority,
    )
    transaction = _parse_exact_json(state.candidate_receipt_bytes, source="receipt")["transaction_id"]
    return PhaseC1PublicationReceipt("candidate_ready", str(transaction))


def _revalidate_acceptance_receipts(
    state: _PreparedPhaseC1State,
) -> None:
    if (
        state.candidate_validation_bytes is None
        or state.candidate_review_bytes is None
    ):
        raise _publication_error("operation")
    retained = (
        (
            state.paths.candidate_receipt_path,
            state.candidate_receipt_bytes,
        ),
        (
            state.paths.candidate_validation_path,
            state.candidate_validation_bytes,
        ),
        (
            state.paths.candidate_review_path,
            state.candidate_review_bytes,
        ),
    )
    observed: list[bytes] = []
    for path, expected in retained:
        _identity(path, directory=False)
        payload = path.read_bytes()
        if payload != expected:
            raise _publication_error("acceptance_receipt")
        observed.append(payload)
    _validate_candidate_receipt_bytes(observed[0], state)
    _validate_validation_and_review(
        state,
        observed[1],
        observed[2],
    )


def _verify_accepted_cleanup_targets(
    state: _PreparedPhaseC1State,
    journal: Mapping[str, object],
) -> None:
    paths = state.paths
    allow_absent = state.operation == "accepted_cleanup_recovery"
    candidate_exists = (
        paths.candidate_root.exists()
        or paths.candidate_root.is_symlink()
    )
    if candidate_exists:
        if allow_absent:
            _validate_phase_c1_cleanup_prefix(
                paths.candidate_root,
                result_bytes=state.result_bytes,
                report_bytes=state.report_bytes,
            )
        else:
            _validate_phase_c1_pair_at_path(paths.candidate_root, state)
    elif not allow_absent:
        raise _publication_error("cleanup_target_missing")

    retained_files = (
        (
            paths.candidate_receipt_path,
            state.candidate_receipt_bytes,
            "candidate_receipt_sha256",
            True,
        ),
        (
            paths.candidate_validation_path,
            state.candidate_validation_bytes,
            "candidate_validation_sha256",
            False,
        ),
        (
            paths.candidate_review_path,
            state.candidate_review_bytes,
            "candidate_review_sha256",
            False,
        ),
    )
    for path, expected_bytes, journal_field, is_candidate_receipt in (
        retained_files
    ):
        retained = path.exists() or path.is_symlink()
        if not retained:
            if not allow_absent:
                raise _publication_error("cleanup_target_missing")
            continue
        _identity(path, directory=False)
        payload = path.read_bytes()
        if (
            type(journal.get(journal_field)) is not str
            or _digest(payload) != journal[journal_field]
            or (
                expected_bytes is not None
                and payload != expected_bytes
            )
        ):
            raise _publication_error("cleanup_target")
        if is_candidate_receipt:
            _validate_candidate_receipt_bytes(payload, state)


def _cleanup_accepted(
    state: _PreparedPhaseC1State,
    *,
    root_authority: _HeldPhaseC1DirectoryAuthority,
) -> None:
    cleanup_targets = (
        (
            state.paths.candidate_root,
            None,
            (state.result_bytes, state.report_bytes),
        ),
        (
            state.paths.candidate_receipt_path,
            state.candidate_receipt_bytes,
            None,
        ),
        (
            state.paths.candidate_validation_path,
            state.candidate_validation_bytes,
            None,
        ),
        (
            state.paths.candidate_review_path,
            state.candidate_review_bytes,
            None,
        ),
    )
    for target, expected_bytes, expected_pair in cleanup_targets:
        _delete_verified_phase_c1_cleanup_target(
            state.paths,
            target,
            root_authority=root_authority,
            expected_bytes=expected_bytes,
            expected_pair=expected_pair,
            allow_pair_cleanup_prefix=(
                target == state.paths.candidate_root
                and state.operation == "accepted_cleanup_recovery"
            ),
        )
    _fsync_phase_c1_directory(
        state.paths.ignored_root,
        authority=root_authority,
    )


def _prepared_phase_c1_parent_identity(
    state: _PreparedPhaseC1State,
    name: str,
) -> tuple[int, int]:
    matches = tuple(
        identity
        for label, identity in state.parent_identities
        if label == name
    )
    if len(matches) != 1:
        raise _publication_error("parent_identity")
    return matches[0]


def _finalize_phase_c1_publication_state(
    state: _PreparedPhaseC1State,
    *,
    root_authority: _HeldPhaseC1DirectoryAuthority,
    canonical_authority: _HeldPhaseC1DirectoryAuthority | None,
) -> PhaseC1PublicationReceipt:
    current, journal = _read_valid_current_journal(
        state,
        root_authority=root_authority,
    )
    if state.operation == "candidate":
        if canonical_authority is not None:
            raise _publication_error("directory_authority")
        return _recover_candidate(
            state,
            current,
            journal,
            root_authority=root_authority,
        )
    if canonical_authority is None:
        raise _publication_error("directory_authority")
    _verify_held_phase_c1_directory_authority(canonical_authority)
    if state.operation == "accepted_cleanup_recovery":
        if journal is None or journal.get("status") != "accepted":
            raise _publication_error("journal")
        _validate_phase_c1_pair_at_path(state.paths.canonical_root, state)
        _verify_accepted_cleanup_targets(state, journal)
        _verify_held_phase_c1_directory_authority(canonical_authority)
        _cleanup_accepted(
            state,
            root_authority=root_authority,
        )
        transaction = _parse_exact_json(
            state.candidate_receipt_bytes,
            source="receipt",
        )["transaction_id"]
        return PhaseC1PublicationReceipt("accepted", str(transaction))
    if (
        state.operation != "acceptance"
        or state.candidate_validation_bytes is None
        or state.candidate_review_bytes is None
    ):
        raise _publication_error("operation")
    if (
        journal is None
        or journal.get("status")
        not in {"candidate_ready", "staging_canonical"}
    ):
        raise _publication_error("journal")
    _validate_phase_c1_pair_at_path(state.paths.candidate_root, state)
    _revalidate_acceptance_receipts(state)
    _verify_held_phase_c1_directory_authority(canonical_authority)
    if (
        state.paths.canonical_stage_path.exists()
        or state.paths.canonical_stage_path.is_symlink()
    ):
        if state.paths.canonical_root.exists():
            raise _publication_error("canonical_stage")
        canonical_stage_prefix = _validate_phase_c1_stage_prefix(
            state.paths.canonical_stage_path,
            state,
        )
        _delete_verified_stage(
            state.paths.canonical_stage_path,
            parent_authority=root_authority,
            expected_children=tuple(
                (
                    name,
                    (
                        state.result_bytes
                        if name == "result.json"
                        else state.report_bytes
                    ),
                )
                for name in canonical_stage_prefix
            ),
        )
    if state.paths.canonical_root.exists():
        _validate_phase_c1_pair_at_path(
            state.paths.canonical_root,
            state,
        )
    else:
        current = _advance_journal(
            state,
            status="staging_canonical",
            current=current,
            root_authority=root_authority,
        )
        _write_pair(
            state,
            stage=state.paths.canonical_stage_path,
            target=state.paths.canonical_root,
            authority=canonical_authority,
            root_authority=root_authority,
        )
    accepted = _advance_journal(
        state,
        status="accepted",
        current=current,
        root_authority=root_authority,
    )
    accepted_journal = _validate_journal_bytes(
        accepted,
        state,
        predecessor=current,
    )
    _verify_accepted_cleanup_targets(state, accepted_journal)
    _verify_held_phase_c1_directory_authority(canonical_authority)
    _cleanup_accepted(
        state,
        root_authority=root_authority,
    )
    transaction = _parse_exact_json(
        state.candidate_receipt_bytes,
        source="receipt",
    )["transaction_id"]
    return PhaseC1PublicationReceipt("accepted", str(transaction))


def finalize_phase_c1_publication(prepared: PreparedPhaseC1Publication, *, capability: object) -> PhaseC1PublicationReceipt:
    try:
        state, root_authority = _consume_capability(
            prepared,
            capability,
        )
        _validate_prepare_state(state)
        if (
            type(root_authority)
            is not _HeldPhaseC1DirectoryAuthority
            or root_authority.path != state.paths.ignored_root
        ):
            raise _publication_error("directory_authority")
        # The first check can expose a POSIX namespace swap immediately
        # after checking the held fd. The second check must reject that new
        # pathname before journal, receipt, pair, or recovery mutation.
        _verify_held_phase_c1_directory_authority(root_authority)
        _verify_held_phase_c1_directory_authority(root_authority)
        _ensure_ignored_root(state.paths)
        if state.operation == "candidate":
            return _finalize_phase_c1_publication_state(
                state,
                root_authority=root_authority,
                canonical_authority=None,
            )
        expected_parent_identity = _prepared_phase_c1_parent_identity(
            state,
            "canonical_target",
        )
        with _held_phase_c1_directory_authority(
            state.paths.canonical_root.parent,
        ) as canonical_authority:
            if (
                canonical_authority.stable_identity
                != expected_parent_identity
            ):
                raise _publication_error("parent_identity")
            return _finalize_phase_c1_publication_state(
                state,
                root_authority=root_authority,
                canonical_authority=canonical_authority,
            )
    except OSError as exc:
        raise _publication_error("publication_io") from exc


def parse_cli_args(argv: Sequence[str]) -> tuple[str, str]:
    if type(argv) not in (tuple, list):
        raise _publication_error("cli_arguments")
    values = tuple(argv)
    if len(values) == 7 and values[0] == "prepare" and values[1:3] == ("--mode", "candidate") and values[3] == "--expected-head" and values[5:7] == ("--receipt", "candidate-receipt.json") and _HEX40.fullmatch(values[4] if isinstance(values[4], str) else ""):
        return ("candidate", values[4])
    if len(values) == 9 and values[0] == "accept" and values[1] == "--expected-head" and values[3:5] == ("--receipt", "candidate-receipt.json") and values[5:7] == ("--validation", "candidate-validation.json") and values[7:9] == ("--review", "candidate-review.json") and _HEX40.fullmatch(values[2] if isinstance(values[2], str) else ""):
        return ("accept", values[2])
    raise _publication_error("cli_arguments")


def _run_phase_c1_publication_cli(argv: Sequence[str]) -> PhaseC1PublicationReceipt:
    operation, expected_head = parse_cli_args(argv)
    if operation == "candidate":
        prepared = prepare_phase_c1_candidate(expected_head=expected_head)
    else:
        prepared = _prepare_phase_c1_acceptance(expected_head=expected_head, candidate_receipt_name="candidate-receipt.json", candidate_validation_name="candidate-validation.json", candidate_review_name="candidate-review.json")
    with persistent_phase_c1_publication_lock(prepared) as capability:
        return finalize_phase_c1_publication(prepared, capability=capability)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        _run_phase_c1_publication_cli(arguments)
    except RunnerError as exc:
        print(
            "EMOTION-STATE-004 Phase C1 publication failed:"
            f" {exc.code}",
            file=sys.stderr,
        )
        return 2 if exc.code == "cli_arguments" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
