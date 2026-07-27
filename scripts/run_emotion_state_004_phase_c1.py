from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from functools import cache
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

RESULT_SCHEMA_VERSION: Final = "EmotionStatePhaseC1AggregateResultV1"
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
_UNRESOLVED_RECORD_ONLY_REASON_CODES: Final = frozenset(
    {
        "source_identity_unverified",
        "raw_annotation_rows_required",
    }
)
REASON_CONTRIBUTOR_CLASSES: Final = MappingProxyType(
    {
        **{
            code: (
                "excluded_discovery_record",
                "excluded_citation_record",
                "rejected_card",
            )
            for code in REASON_CODE_ORDER[:14]
        },
        **{
            code: (
                (
                    "unresolved_discovery_record",
                    "unresolved_citation_record",
                )
                if code in _UNRESOLVED_RECORD_ONLY_REASON_CODES
                else (
                    "unresolved_discovery_record",
                    "unresolved_citation_record",
                    "unresolved_card",
                )
            )
            for code in REASON_CODE_ORDER[14:33]
        },
        **{code: () for code in REASON_CODE_ORDER[33:37]},
        "annotation_fallback_feasible": (
            "feasible_fallback_assessment",
        ),
        "annotation_fallback_unresolved": (
            "unresolved_fallback_assessment",
        ),
    }
)
_REJECTED_CARD_EXCLUSIVE_REASON_GROUPS: Final = (
    ("access_requires_login", "access_restricted"),
    ("acted_or_scripted", "mixed_unseparated_conversation"),
    ("conversation_level_only", "temporal_unit_incompatible"),
    ("self_report_label", "llm_generated_label"),
)
_REJECTED_CARD_INDEPENDENT_REASON_CODES: Final = (
    "license_incompatible",
    "ethical_use_incompatible",
    "proxy_construct",
    "target_label_absent",
    "single_rater",
)
_REJECTED_CARD_SOLO_REASON_CODE: Final = "reliability_upper_below_0_67"
_UNRESOLVED_ELIGIBILITY_INDEPENDENT_REASON_CODES: Final = (
    "authoritative_provenance_unverified",
    "access_unresolved",
    "license_unresolved",
    "ethical_use_unresolved",
    "conversation_status_unresolved",
    "directness_unresolved",
    "temporal_unit_unresolved",
    "rater_count_unresolved",
    "source_documentation_incomplete",
)
_UNRESOLVED_ELIGIBILITY_OBSERVER_REASON_CODE: Final = (
    "observer_method_unresolved"
)
_UNRESOLVED_SHARED_REASON_CODE: Final = "reliability_not_preadjudication"
_UNRESOLVED_RELIABILITY_INDEPENDENT_REASON_CODES: Final = (
    "reliability_metric_unapproved",
    "reliability_unverifiable",
    "reliability_interval_uncertain",
)
_UNRESOLVED_EFFECTIVE_SAMPLE_REASON_CODE: Final = (
    "reliability_effective_sample_insufficient"
)
_UNRESOLVED_POSITIVE_SUPPORT_REASON_CODES: Final = (
    "positive_support_below_93",
    "published_positive_count_missing",
)
_UNRESOLVED_HIDDEN_ELIGIBILITY_REASON_CODES: Final = (
    tuple(
        code for code in _UNRESOLVED_ELIGIBILITY_INDEPENDENT_REASON_CODES
        if code != "rater_count_unresolved"
    )
    + (_UNRESOLVED_ELIGIBILITY_OBSERVER_REASON_CODE,)
    + (_UNRESOLVED_SHARED_REASON_CODE,)
)
_UNRESOLVED_HIDDEN_ELIGIBILITY_INDEPENDENT_REASON_CODES: Final = tuple(
    code for code in _UNRESOLVED_ELIGIBILITY_INDEPENDENT_REASON_CODES
    if code != "rater_count_unresolved"
)
_UNRESOLVED_HIDDEN_RELIABILITY_REASON_CODE: Final = (
    "reliability_unverifiable"
)
_OBSERVABLE_CARD_REASON_CODES: Final = (
    "reliability_upper_below_0_67",
    "single_rater",
    "rater_count_unresolved",
    "reliability_metric_unapproved",
    "reliability_effective_sample_insufficient",
    "positive_support_below_93",
    "reliability_interval_uncertain",
    "published_positive_count_missing",
)
_OBSERVABLE_REJECTION_REASON_COUNT: Final = 2
_OBSERVABLE_REASON_BITS: Final = MappingProxyType(
    {code: 1 << index for index, code in enumerate(_OBSERVABLE_CARD_REASON_CODES)}
)
_ReasonVector = tuple[int, ...]
_UnresolvedPathOption = tuple[int, int, int, int, int]
_UnresolvedPathTotals = tuple[int, int, int, int]
_ObservableAction = tuple[int, _ReasonVector, _UnresolvedPathTotals]
_ObservableSignature = tuple[
    tuple[int, ...], tuple[_UnresolvedPathOption, ...]
]
_ObservableDiagnosticGroup = tuple[
    tuple[Mapping[str, object], ...], int, int
]
_OBSERVABLE_FAMILY_RANGES: Final = (
    (0, _OBSERVABLE_REJECTION_REASON_COUNT),
    (_OBSERVABLE_REJECTION_REASON_COUNT, len(_OBSERVABLE_CARD_REASON_CODES)),
)
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
        "reliability_diagnostics",
        "c2_eligible",
    }
)
RELIABILITY_DIAGNOSTIC_FIELDS: Final = frozenset(
    {
        "evidence_card_sha256",
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
) -> dict[str, object]:
    reliability = card.reliability
    diagnostic: dict[str, object] = {
        "evidence_card_sha256": evidence_card_sha256,
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


def build_phase_c1_result(
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
                "reliability_diagnostics": [
                    _reliability_diagnostic(
                        card,
                        evidence_card_sha256=card_sha256_by_id[
                            card.card_id
                        ],
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
        "source_counts": _source_counts(source_ledger),
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
    validate_phase_c1_result_payload(result)
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


def _maximum_rejected_card_reason_occurrences(
    reason_counts: Mapping[str, int],
    card_count: int,
) -> int:
    if card_count == 0:
        return 0
    maximum = -1
    solo_limit = min(
        reason_counts[_REJECTED_CARD_SOLO_REASON_CODE],
        card_count,
    )
    for solo_cards in range(solo_limit + 1):
        ordinary_cards = card_count - solo_cards
        ordinary_occurrences = sum(
            min(
                sum(reason_counts[code] for code in group),
                ordinary_cards,
            )
            for group in _REJECTED_CARD_EXCLUSIVE_REASON_GROUPS
        )
        ordinary_occurrences += sum(
            min(reason_counts[code], ordinary_cards)
            for code in _REJECTED_CARD_INDEPENDENT_REASON_CODES
        )
        total_occurrences = solo_cards + ordinary_occurrences
        if total_occurrences >= card_count:
            maximum = max(maximum, total_occurrences)
    return maximum


def _maximum_unresolved_card_reason_occurrences(
    reason_counts: Mapping[str, int],
    card_count: int,
) -> int:
    if card_count == 0:
        return 0
    maximum = -1
    shared_count = reason_counts[_UNRESOLVED_SHARED_REASON_CODE]
    for eligibility_cards in range(card_count + 1):
        reliability_cards = card_count - eligibility_cards
        for eligibility_shared_capacity in range(
            min(shared_count, eligibility_cards) + 1
        ):
            reliability_shared_capacity = min(
                shared_count - eligibility_shared_capacity,
                reliability_cards,
            )
            eligibility_occurrences = sum(
                min(reason_counts[code], eligibility_cards)
                for code in _UNRESOLVED_ELIGIBILITY_INDEPENDENT_REASON_CODES
            )
            eligibility_occurrences += min(
                reason_counts[
                    _UNRESOLVED_ELIGIBILITY_OBSERVER_REASON_CODE
                ]
                + eligibility_shared_capacity,
                eligibility_cards,
            )
            if eligibility_occurrences < eligibility_cards:
                continue

            reliability_base_occurrences = sum(
                min(reason_counts[code], reliability_cards)
                for code in _UNRESOLVED_RELIABILITY_INDEPENDENT_REASON_CODES
            )
            reliability_base_occurrences += reliability_shared_capacity
            effective_sample_occurrences = min(
                reason_counts[
                    _UNRESOLVED_EFFECTIVE_SAMPLE_REASON_CODE
                ],
                reliability_cards,
            )
            reliability_base_occurrences += effective_sample_occurrences
            if reliability_base_occurrences < reliability_cards:
                continue
            reliability_occurrences = (
                reliability_base_occurrences
                + min(
                    sum(
                        reason_counts[code]
                        for code in _UNRESOLVED_POSITIVE_SUPPORT_REASON_CODES
                    ),
                    effective_sample_occurrences,
                )
            )
            maximum = max(
                maximum,
                eligibility_occurrences + reliability_occurrences,
            )
    return maximum


def _reason_mask(*codes: str) -> int:
    return sum(_OBSERVABLE_REASON_BITS[code] for code in codes)


def _mask_vector(mask: int, count: int = 1) -> _ReasonVector:
    return tuple(
        count if mask & (1 << index) else 0
        for index in range(len(_OBSERVABLE_CARD_REASON_CODES))
    )


def _add_vectors(
    left: tuple[int, ...], right: tuple[int, ...]
) -> tuple[int, ...]:
    return tuple(
        left_value + right_value
        for left_value, right_value in zip(left, right, strict=True)
    )


def _add_bounded_vector(
    left: _ReasonVector,
    right: _ReasonVector,
    capacities: _ReasonVector,
) -> _ReasonVector | None:
    combined = _add_vectors(left, right)
    if any(
        value > capacity
        for value, capacity in zip(combined, capacities, strict=True)
    ):
        return None
    return combined


def _reason_family_totals(vector: _ReasonVector) -> tuple[int, int]:
    return (
        sum(vector[:_OBSERVABLE_REJECTION_REASON_COUNT]),
        sum(vector[_OBSERVABLE_REJECTION_REASON_COUNT:]),
    )


def _diagnostic_rejects_frozen_alpha_rule(
    diagnostic: Mapping[str, object],
) -> bool:
    interval = tuple(
        diagnostic[field]
        for field in ("point_micros", "lower_95_micros", "upper_95_micros")
    )
    return (
        diagnostic["metric_id"] == "krippendorff_alpha"
        and diagnostic["effective_sample_sufficient"] is True
        and all(type(value) is int for value in interval)
        and interval[2] < 670_000
    )


def _rejected_observable_options(
    diagnostic: Mapping[str, object],
) -> tuple[int, ...]:
    raters = diagnostic["independent_rater_count"]
    if type(raters) is int and raters < 2:
        return (_reason_mask("single_rater"),)
    options = [0]
    if _diagnostic_rejects_frozen_alpha_rule(diagnostic):
        options.append(_reason_mask("reliability_upper_below_0_67"))
    return tuple(options)


def _unresolved_path_options(
    diagnostic: Mapping[str, object],
    reason_counts: Mapping[str, int],
) -> tuple[_UnresolvedPathOption, ...]:
    raters = diagnostic["independent_rater_count"]
    if raters is None:
        return (
            (
                _reason_mask("rater_count_unresolved"),
                1,
                0,
                0,
                0,
            ),
        )
    if type(raters) is int and raters < 2:
        return ()

    options: list[_UnresolvedPathOption] = []
    if any(
            reason_counts[code] > 0
            for code in _UNRESOLVED_HIDDEN_ELIGIBILITY_REASON_CODES
    ):
        options.append((0, 1, 1, 0, 0))
    positives = diagnostic["published_positive_count"]
    point = diagnostic["point_micros"]
    lower = diagnostic["lower_95_micros"]
    upper = diagnostic["upper_95_micros"]
    interval_uncertain = any(
        value is None for value in (point, lower, upper)
    ) or (
        diagnostic["metric_id"] == "krippendorff_alpha"
        and diagnostic["effective_sample_sufficient"] is True
        and not _diagnostic_passes_frozen_alpha_rule(diagnostic)
        and not _diagnostic_rejects_frozen_alpha_rule(diagnostic)
    )
    reasons = tuple(
        code
        for code, applies in (
            (
                "reliability_metric_unapproved",
                diagnostic["metric_id"] != "krippendorff_alpha",
            ),
            (
                "reliability_effective_sample_insufficient",
                diagnostic["effective_sample_sufficient"] is False,
            ),
            ("positive_support_below_93", type(positives) is int and positives < 93),
            ("reliability_interval_uncertain", interval_uncertain),
            ("published_positive_count_missing", positives is None),
        )
        if applies
    )
    if reasons:
        options.append((_reason_mask(*reasons), 0, 0, 1, 0))
    elif (
        reason_counts[_UNRESOLVED_SHARED_REASON_CODE] > 0
        or reason_counts[_UNRESOLVED_HIDDEN_RELIABILITY_REASON_CODE] > 0
    ):
        options.append((0, 0, 0, 1, 1))
    return tuple(dict.fromkeys(options))


def _observable_signature_actions(
    rejected_options: tuple[int, ...],
    unresolved_options: tuple[_UnresolvedPathOption, ...],
    *,
    signature_count: int,
    capacities: _ReasonVector,
) -> tuple[_ObservableAction, ...]:
    zero = tuple(0 for _ in capacities)
    zero_paths = (0, 0, 0, 0)

    def repeated_rejected_totals(
        options: tuple[int, ...], count: int
    ) -> tuple[_ReasonVector, ...]:
        if count == 0:
            return (zero,)
        if not options:
            return ()
        nonzero = tuple(mask for mask in options if mask)
        if 0 not in options:
            vectors = (
                (_mask_vector(nonzero[0], count),)
                if len(nonzero) == 1
                else ()
            )
        elif len(nonzero) <= 1:
            mask = nonzero[0] if nonzero else 0
            vectors = tuple(
                _mask_vector(mask, selected)
                for selected in range(count + 1)
            )
        else:
            vectors = ()
        return tuple(
            vector for vector in vectors
            if _add_bounded_vector(zero, vector, capacities) is not None
        )

    def repeated_unresolved_totals(
        options: tuple[_UnresolvedPathOption, ...],
        count: int,
    ) -> tuple[tuple[_ReasonVector, _UnresolvedPathTotals], ...]:
        if count == 0:
            return ((zero, zero_paths),)
        if not options:
            return ()

        allocations: list[tuple[int, ...]] = []

        def allocate(
            option_index: int,
            remaining: int,
            selected: tuple[int, ...],
        ) -> None:
            if option_index == len(options) - 1:
                allocations.append(selected + (remaining,))
                return
            for option_count in range(remaining + 1):
                allocate(
                    option_index + 1,
                    remaining - option_count,
                    selected + (option_count,),
                )

        allocate(0, count, ())
        totals: set[tuple[_ReasonVector, _UnresolvedPathTotals]] = set()
        for allocation in allocations:
            vector = zero
            paths = zero_paths
            for (
                mask,
                eligibility_cards,
                eligibility_hidden_required,
                reliability_cards,
                reliability_hidden_required,
            ), option_count in zip(options, allocation, strict=True):
                vector = _add_vectors(
                    vector,
                    _mask_vector(mask, option_count),
                )
                paths = _add_vectors(
                    paths,
                    (
                        eligibility_cards * option_count,
                        eligibility_hidden_required * option_count,
                        reliability_cards * option_count,
                        reliability_hidden_required * option_count,
                    ),
                )
            if _add_bounded_vector(zero, vector, capacities) is not None:
                totals.add((vector, paths))
        return tuple(sorted(totals))

    actions = {
        (rejected_count, combined, paths)
        for rejected_count in range(signature_count + 1)
        for rejected_total in repeated_rejected_totals(
            rejected_options, rejected_count
        )
        for unresolved_total, paths in repeated_unresolved_totals(
            unresolved_options, signature_count - rejected_count
        )
        if (
            combined := _add_bounded_vector(
                rejected_total, unresolved_total, capacities
            )
        )
        is not None
    }
    return tuple(
        sorted(
            actions,
            key=lambda action: (
                -sum(action[1]),
                action[0],
                action[1],
                action[2],
            ),
        )
    )


def _observable_signature_groups(
    diagnostics: tuple[Mapping[str, object], ...],
    *,
    capacities: _ReasonVector,
    reason_counts: Mapping[str, int],
) -> tuple[tuple[_ObservableAction, ...], ...] | None:
    signature_counts: dict[_ObservableSignature, int] = {}
    for diagnostic in diagnostics:
        signature = (
            _rejected_observable_options(diagnostic),
            _unresolved_path_options(diagnostic, reason_counts),
        )
        signature_counts[signature] = signature_counts.get(signature, 0) + 1

    groups: list[tuple[_ObservableAction, ...]] = []
    for signature, count in sorted(signature_counts.items()):
        actions = _observable_signature_actions(
            *signature,
            signature_count=count,
            capacities=capacities,
        )
        if not actions:
            return None
        groups.append(actions)
    return tuple(sorted(groups, key=lambda actions: (len(actions), actions)))


def _exact_unresolved_card_reason_allocation_feasible(
    *,
    reason_counts: Mapping[str, int],
    unresolved_card_reason_occurrences: int,
    observable_reason_occurrences: int,
    path_totals: _UnresolvedPathTotals,
) -> bool:
    (
        eligibility_cards,
        eligibility_hidden_required,
        reliability_cards,
        reliability_hidden_required,
    ) = path_totals
    hidden_occurrences = (
        unresolved_card_reason_occurrences - observable_reason_occurrences
    )
    if (
        hidden_occurrences < 0
        or eligibility_hidden_required > eligibility_cards
        or reliability_hidden_required > reliability_cards
    ):
        return False

    eligibility_independent_maximum = sum(
        min(reason_counts[code], eligibility_cards)
        for code in _UNRESOLVED_HIDDEN_ELIGIBILITY_INDEPENDENT_REASON_CODES
    )
    observer_count = reason_counts[
        _UNRESOLVED_ELIGIBILITY_OBSERVER_REASON_CODE
    ]
    shared_count = reason_counts[_UNRESOLVED_SHARED_REASON_CODE]
    reliability_independent_maximum = min(
        reason_counts[_UNRESOLVED_HIDDEN_RELIABILITY_REASON_CODE],
        reliability_cards,
    )

    for eligibility_shared_used in range(
        min(shared_count, eligibility_cards) + 1
    ):
        eligibility_maximum = (
            eligibility_independent_maximum
            + eligibility_shared_used
            + min(
                observer_count,
                eligibility_cards - eligibility_shared_used,
            )
        )
        eligibility_minimum = max(
            eligibility_hidden_required,
            eligibility_shared_used,
        )
        if eligibility_minimum > eligibility_maximum:
            continue

        remaining_shared = shared_count - eligibility_shared_used
        for reliability_shared_used in range(
            min(remaining_shared, reliability_cards) + 1
        ):
            reliability_minimum = max(
                reliability_hidden_required,
                reliability_shared_used,
            )
            reliability_maximum = (
                reliability_shared_used
                + reliability_independent_maximum
            )
            if reliability_minimum > reliability_maximum:
                continue
            if (
                eligibility_minimum + reliability_minimum
                <= hidden_occurrences
                <= eligibility_maximum + reliability_maximum
            ):
                return True
    return False


def _observable_reason_allocation_feasible(
    groups: tuple[_ObservableDiagnosticGroup, ...],
    *,
    reason_counts: Mapping[str, int],
    maximum_rejection_search_records: int,
    unresolved_search_records: int,
    unresolved_card_reason_occurrences: int,
    search_statistics: dict[str, int] | None = None,
) -> bool:
    capacities = tuple(
        reason_counts[code] for code in _OBSERVABLE_CARD_REASON_CODES
    )
    requirements = (
        max(
            0,
            sum(capacities[:_OBSERVABLE_REJECTION_REASON_COUNT])
            - maximum_rejection_search_records,
        ),
        max(
            0,
            sum(capacities[_OBSERVABLE_REJECTION_REASON_COUNT:])
            - unresolved_search_records,
        ),
    )
    zero = tuple(0 for _ in capacities)
    zero_categories = (0, 0)
    zero_paths = (0, 0, 0, 0)
    explored_state_count = 0
    signature_group_count = 0

    def finish(result: bool) -> bool:
        if search_statistics is not None:
            search_statistics.update(
                {
                    "signature_group_count": signature_group_count,
                    "explored_state_count": explored_state_count,
                }
            )
        return result

    signature_groups_by_signal: list[
        tuple[tuple[_ObservableAction, ...], ...]
    ] = []
    rejected_targets: list[int] = []
    for diagnostics, rejected, unresolved in groups:
        if rejected + unresolved != len(diagnostics):
            return finish(False)
        signal_groups = _observable_signature_groups(
            diagnostics,
            capacities=capacities,
            reason_counts=reason_counts,
        )
        if signal_groups is None:
            return finish(False)
        signature_group_count += len(signal_groups)
        signature_groups_by_signal.append(signal_groups)
        rejected_targets.append(rejected)

    @cache
    def signal_bounds(
        signal_index: int,
        group_index: int,
        rejected_needed: int,
    ) -> tuple[int, int] | None:
        signal_groups = signature_groups_by_signal[signal_index]
        if group_index == len(signal_groups):
            return zero_categories if rejected_needed == 0 else None
        candidates = [
            _add_vectors(_reason_family_totals(vector), suffix)
            for rejected_count, vector, _paths in signal_groups[group_index]
            if rejected_count <= rejected_needed
            for suffix in (
                signal_bounds(
                    signal_index,
                    group_index + 1,
                    rejected_needed - rejected_count,
                ),
            )
            if suffix is not None
        ]
        if not candidates:
            return None
        return tuple(
            max(families[index] for families in candidates)
            for index in range(2)
        )

    @cache
    def search(
        signal_index: int,
        group_index: int,
        rejected_used: int,
        used: _ReasonVector,
        path_totals: _UnresolvedPathTotals,
    ) -> bool:
        nonlocal explored_state_count
        if signal_index == len(groups):
            return all(
                observed >= required
                for observed, required in zip(
                    _reason_family_totals(used),
                    requirements,
                    strict=True,
                )
            ) and _exact_unresolved_card_reason_allocation_feasible(
                reason_counts=reason_counts,
                unresolved_card_reason_occurrences=(
                    unresolved_card_reason_occurrences
                ),
                observable_reason_occurrences=sum(
                    used[_OBSERVABLE_REJECTION_REASON_COUNT:]
                ),
                path_totals=path_totals,
            )
        signal_groups = signature_groups_by_signal[signal_index]
        if group_index == len(signal_groups):
            if rejected_used != rejected_targets[signal_index]:
                return False
            return search(
                signal_index + 1,
                0,
                0,
                used,
                path_totals,
            )
        explored_state_count += 1

        needed_rejected = (
            rejected_targets[signal_index] - rejected_used
        )
        bounds = signal_bounds(
            signal_index,
            group_index,
            needed_rejected,
        )
        if bounds is None:
            return False
        maximum_by_family = bounds
        for future_signal in range(signal_index + 1, len(groups)):
            future = signal_bounds(
                future_signal,
                0,
                rejected_targets[future_signal],
            )
            if future is None:
                return False
            maximum_by_family = _add_vectors(
                maximum_by_family,
                future,
            )

        for family_index, (start, stop) in enumerate(
            _OBSERVABLE_FAMILY_RANGES
        ):
            current_occurrences = sum(used[start:stop])
            remaining_capacity = sum(
                capacity - value
                for capacity, value in zip(
                    capacities[start:stop],
                    used[start:stop],
                    strict=True,
                )
            )
            maximum_additions = min(
                maximum_by_family[family_index],
                remaining_capacity,
            )
            if (
                current_occurrences + maximum_additions
                < requirements[family_index]
            ):
                return False

        for rejected_count, addition, path_addition in signal_groups[
            group_index
        ]:
            if (
                rejected_used + rejected_count
                > rejected_targets[signal_index]
            ):
                continue
            combined = _add_bounded_vector(
                used,
                addition,
                capacities,
            )
            combined_paths = _add_vectors(path_totals, path_addition)
            if combined is not None and search(
                signal_index,
                group_index + 1,
                rejected_used + rejected_count,
                combined,
                combined_paths,
            ):
                return True
        return False

    return finish(search(0, 0, 0, zero, zero_paths))


def _validate_diagnostic(value: object) -> dict[str, object]:
    diagnostic = _exact_dict(
        value,
        RELIABILITY_DIAGNOSTIC_FIELDS,
        code="reliability_diagnostics",
    )
    _sha256(
        diagnostic["evidence_card_sha256"],
        code="reliability_diagnostics",
    )
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
        type(diagnostic["effective_sample_sufficient"]) is not bool
        or diagnostic["effective_sample_sufficient"]
        != _effective_sample_sufficient(diagnostic)
    ):
        raise RunnerError("reliability_diagnostics")
    return diagnostic


def _diagnostic_passes_frozen_alpha_rule(
    diagnostic: Mapping[str, object],
) -> bool:
    point = diagnostic["point_micros"]
    lower = diagnostic["lower_95_micros"]
    upper = diagnostic["upper_95_micros"]
    return (
        diagnostic["metric_id"] == "krippendorff_alpha"
        and diagnostic["effective_sample_sufficient"] is True
        and type(point) is int
        and type(lower) is int
        and type(upper) is int
        and point >= 800_000
        and lower >= 670_000
    )


def validate_phase_c1_result_payload(
    payload: Mapping[str, object],
) -> None:
    _forbidden_content(payload)
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

    search_counts = _validate_search_counts(result["search_counts"])
    source_counts = _validate_source_counts(
        result["source_counts"],
        detailed_candidate_count=search_counts["detailed_candidate_count"],
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
    aggregate_search_blocker = (
        not search_counts["search_complete"]
        or search_counts["candidate_overflow_count"] > 0
        or search_counts["unresolved_discovery_record_count"] > 0
        or search_counts["unresolved_citation_record_count"] > 0
    )

    raw_per_signal = result["per_signal"]
    if type(raw_per_signal) is not list or len(raw_per_signal) != 5:
        raise RunnerError("per_signal")
    parsed_per_signal: list[dict[str, object]] = []
    all_diagnostic_hashes: list[str] = []
    observable_diagnostic_groups: list[
        tuple[
            tuple[Mapping[str, object], ...],
            int,
            int,
        ]
    ] = []
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
            _validate_diagnostic(value) for value in diagnostics
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
        diagnostics_by_hash = {
            diagnostic["evidence_card_sha256"]: diagnostic
            for diagnostic in parsed_diagnostics
        }
        if (
            len(set(diagnostic_hashes)) != len(diagnostic_hashes)
            or any(value not in diagnostic_hashes for value in admissible_hashes)
            or any(
                not _diagnostic_passes_frozen_alpha_rule(
                    diagnostics_by_hash[value]
                )
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
        if (
            len(parsed_diagnostics)
            != len(admissible_hashes) + rejected + unresolved
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
        observable_diagnostic_groups.append(
            (
                tuple(
                    diagnostic
                    for diagnostic in parsed_diagnostics
                    if diagnostic["evidence_card_sha256"]
                    not in admissible_hashes
                ),
                rejected,
                unresolved,
            )
        )
        parsed_per_signal.append(item)
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
    if (
        reason_counts["annotation_fallback_feasible"]
        != fallback_status_counts["feasible"]
        or reason_counts["annotation_fallback_unresolved"]
        != fallback_status_counts["unresolved"]
    ):
        raise RunnerError("reason_code_counts")
    if (
        source_counts["fallback_material_candidate_source_count"] == 0
        and (
            fallback_status_counts["feasible"] > 0
            or (
                not aggregate_search_blocker
                and fallback_status_counts["infeasible"]
                != len(TARGET_SIGNALS)
            )
        )
    ):
        raise RunnerError("source_counts")

    resolved_citation_record_count = (
        search_counts["backward_citation_record_count"]
        + search_counts["forward_citation_record_count"]
        - search_counts["unresolved_citation_record_count"]
    )
    minimum_retained_citation_record_count = max(
        0,
        search_counts["detailed_candidate_count"]
        + search_counts["candidate_overflow_count"]
        - search_counts["retained_candidate_record_count"],
    )
    excluded_citation_record_capacity = (
        resolved_citation_record_count
        - minimum_retained_citation_record_count
    )
    contributor_capacities = {
        "excluded_discovery_record": search_counts[
            "excluded_discovery_record_count"
        ],
        "excluded_citation_record": excluded_citation_record_capacity,
        "rejected_card": status_counts["rejected"],
        "unresolved_discovery_record": search_counts[
            "unresolved_discovery_record_count"
        ],
        "unresolved_citation_record": search_counts[
            "unresolved_citation_record_count"
        ],
        "unresolved_card": status_counts["unresolved"],
        "feasible_fallback_assessment": fallback_status_counts["feasible"],
        "unresolved_fallback_assessment": fallback_status_counts[
            "unresolved"
        ],
    }
    if any(
        reason_counts[code]
        > sum(
            contributor_capacities[contributor_class]
            for contributor_class in contributor_classes
        )
        for code, contributor_classes in REASON_CONTRIBUTOR_CLASSES.items()
    ):
        raise RunnerError("reason_code_counts")

    rejection_occurrences = sum(
        reason_counts[code] for code in REJECTION_REASON_CODES
    )
    rejection_minimum = (
        search_counts["excluded_discovery_record_count"]
        + status_counts["rejected"]
    )
    rejection_maximum = (
        search_counts["excluded_discovery_record_count"]
        + search_counts["backward_citation_record_count"]
        + search_counts["forward_citation_record_count"]
        - search_counts["unresolved_citation_record_count"]
        + status_counts["rejected"] * len(REJECTION_REASON_CODES)
    )
    unresolved_occurrences = sum(
        reason_counts[code] for code in UNRESOLVED_REASON_CODES
    )
    unresolved_search_occurrences = (
        search_counts["unresolved_discovery_record_count"]
        + search_counts["unresolved_citation_record_count"]
    )
    unresolved_minimum = (
        unresolved_search_occurrences + status_counts["unresolved"]
    )
    unresolved_maximum = (
        unresolved_search_occurrences
        + status_counts["unresolved"] * len(UNRESOLVED_REASON_CODES)
    )
    if (
        not rejection_minimum
        <= rejection_occurrences
        <= rejection_maximum
        or not unresolved_minimum
        <= unresolved_occurrences
        <= unresolved_maximum
        or any(reason_counts[code] != 0 for code in SEARCH_META_REASON_CODES)
    ):
        raise RunnerError("reason_code_counts")

    maximum_rejected_card_occurrences = (
        _maximum_rejected_card_reason_occurrences(
            reason_counts,
            status_counts["rejected"],
        )
    )
    minimum_rejected_card_occurrences = max(
        status_counts["rejected"],
        rejection_occurrences
        - (
            search_counts["excluded_discovery_record_count"]
            + excluded_citation_record_capacity
        ),
    )
    maximum_requested_rejected_card_occurrences = min(
        maximum_rejected_card_occurrences,
        rejection_occurrences
        - search_counts["excluded_discovery_record_count"],
    )
    record_only_unresolved_occurrences = sum(
        reason_counts[code]
        for code in _UNRESOLVED_RECORD_ONLY_REASON_CODES
    )
    unresolved_card_occurrences = (
        unresolved_occurrences - unresolved_search_occurrences
    )
    maximum_unresolved_card_occurrences = (
        _maximum_unresolved_card_reason_occurrences(
            reason_counts,
            status_counts["unresolved"],
        )
    )
    if (
        minimum_rejected_card_occurrences
        > maximum_requested_rejected_card_occurrences
        or record_only_unresolved_occurrences
        > unresolved_search_occurrences
        or unresolved_card_occurrences < status_counts["unresolved"]
        or unresolved_card_occurrences
        > maximum_unresolved_card_occurrences
    ):
        raise RunnerError("reason_code_counts")

    maximum_excluded_citation_record_count = min(
        excluded_citation_record_capacity,
        rejection_occurrences
        - search_counts["excluded_discovery_record_count"]
        - status_counts["rejected"],
    )
    nonduplicate_discovery_record_count = (
        search_counts["returned_discovery_record_count"]
        - search_counts["duplicate_discovery_record_count"]
    )
    citation_anchor_count_without_exclusions = (
        nonduplicate_discovery_record_count
        + minimum_retained_citation_record_count
        + search_counts["unresolved_citation_record_count"]
    )
    if (
        resolved_citation_record_count > 0
        and citation_anchor_count_without_exclusions == 0
        and maximum_excluded_citation_record_count == 0
    ):
        raise RunnerError("reason_code_counts")
    if not _observable_reason_allocation_feasible(
        tuple(observable_diagnostic_groups),
        reason_counts=reason_counts,
        maximum_rejection_search_records=(
            search_counts["excluded_discovery_record_count"]
            + maximum_excluded_citation_record_count
        ),
        unresolved_search_records=(
            unresolved_search_occurrences
            - record_only_unresolved_occurrences
        ),
        unresolved_card_reason_occurrences=unresolved_card_occurrences,
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
        or (
            result["overall_decision"] == "stop_c2"
            and aggregate_search_blocker
        )
    ):
        raise RunnerError("overall_decision")
    if (
        aggregate_search_blocker
        and fallback_status_counts["infeasible"] == len(TARGET_SIGNALS)
    ):
        raise RunnerError("per_signal")

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
    try:
        phase_c1.canonical_json_bytes(result)
    except (TypeError, ValueError) as exc:
        raise RunnerError("result_json") from exc


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


def render_phase_c1_report(result: Mapping[str, object]) -> bytes:
    validate_phase_c1_result_payload(result)
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
