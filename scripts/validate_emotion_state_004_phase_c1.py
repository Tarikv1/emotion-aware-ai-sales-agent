from __future__ import annotations

import ast
import ctypes
import json
import os
import re
import stat
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from ctypes import wintypes
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Final

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


class ValidationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class CliUsageError(ValueError):
    pass


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
CANDIDATE_ROOT: Final = (
    ROOT
    / ".tmp"
    / "emotion-state-004-phase-c1"
    / "candidate"
)
CANONICAL_ROOT: Final = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission"
)
VALIDATOR_PATH: Final = (
    ROOT / "scripts" / "validate_emotion_state_004_phase_c1.py"
)
CONTRACTS_PATH: Final = (
    ROOT / "scripts" / "emotion_state_phase_c1_contracts.py"
)

RESULT_SCHEMA_VERSION: Final = "EmotionStatePhaseC1AggregateResultV2"
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
RESULT_FIELDS: Final = frozenset(
    {
        "schema_version",
        "checkpoint_id",
        "protocol_id",
        "target_signals",
        "implementation_head",
        "validator_blob_id",
        "protocol_sha256",
        "search_ledger_sha256",
        "source_evidence_ledger_sha256",
        "source_review_receipt_sha256",
        "aggregate_content_sha256",
        "search_counts",
        "search_lane_counts",
        "source_counts",
        "source_signature_counts",
        "card_counts_by_status",
        "reason_code_counts",
        "per_signal",
        "overall_decision",
        "c2_eligible_signals",
        "boundary",
        "limitations",
        "runtime_approved",
    }
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
FALLBACK_REASON_CODES: Final = frozenset(REASON_CODE_ORDER[37:])
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
PAIR_CHILDREN: Final = frozenset({"result.json", "report.md"})
CANONICAL_RESULT_RELATIVE: Final = (
    "research/experiments/generated/"
    "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission/"
    "result.json"
)
CANONICAL_REPORT_RELATIVE: Final = (
    "research/experiments/generated/"
    "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission/"
    "report.md"
)
INPUT_RELATIVE_PATHS: Final = (
    (
        "protocol_sha256",
        "research/experiments/configs/"
        "emotion-state-004-phase-c1-discovery-protocol.json",
    ),
    (
        "search_ledger_sha256",
        "research/sources/emotion_state/phase_c1_search_ledger.json",
    ),
    (
        "source_evidence_ledger_sha256",
        "research/sources/emotion_state/"
        "phase_c1_source_evidence_ledger.json",
    ),
    (
        "source_review_receipt_sha256",
        "research/sources/emotion_state/"
        "phase_c1_source_review_receipt.json",
    ),
)
VALIDATOR_RELATIVE_PATH: Final = (
    "scripts/validate_emotion_state_004_phase_c1.py"
)
CONTRACTS_RELATIVE_PATH: Final = (
    "scripts/emotion_state_phase_c1_contracts.py"
)
MAX_AGGREGATE_RESULT_BYTES: Final = 512 * 1024
MAX_PAIR_FILE_BYTES: Final = 1024 * 1024
MAX_INPUT_FILE_BYTES: Final = 8 * 1024 * 1024
MAX_GIT_METADATA_BYTES: Final = 4096
try:
    REPARSE_POINT: Final = stat.FILE_ATTRIBUTE_REPARSE_POINT
except AttributeError:
    REPARSE_POINT = 0x400
try:
    _O_DIRECTORY = os.O_DIRECTORY
except AttributeError:
    _O_DIRECTORY = None
try:
    _O_NOFOLLOW = os.O_NOFOLLOW
except AttributeError:
    _O_NOFOLLOW = None
_LOWER_GIT_ID_RE: Final = re.compile(r"^[0-9a-f]{40}$")
_LOWER_HEX_RE: Final = re.compile(r"^[0-9a-f]+$")
_SHA256_RE: Final = re.compile(r"^[0-9A-F]{64}$")
_EXHAUSTIVE_CITATION_STOPS: Final = frozenset(
    {"no_eligible_candidates", "source_list_exhausted"}
)
_DISCOVERY_DISPOSITIONS: Final = (
    "retained_candidate",
    "duplicate",
    "excluded",
    "unresolved",
)
_CITATION_DIRECTIONS: Final = ("backward", "forward")
_FALLBACK_STATUSES: Final = ("feasible", "infeasible", "unresolved")


def _contract_error(exc: phase_c1.PhaseC1ContractError) -> ValidationError:
    return ValidationError(exc.code)


def _canonical_input_object(data: bytes, *, source: str) -> dict[str, object]:
    if type(data) is not bytes:
        raise ValidationError(f"{source}_bytes")
    try:
        payload = phase_c1.load_json_strict(data, source=source)
        if type(payload) is not dict:
            raise ValidationError(f"{source}_object")
        if phase_c1.canonical_json_bytes(payload) != data:
            raise ValidationError(f"{source}_canonical")
        return payload
    except phase_c1.PhaseC1ContractError as exc:
        raise _contract_error(exc) from exc


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


def _canonical_dataclass_bytes(
    value: object,
    schema_version: str,
) -> bytes:
    payload = _json_value(value)
    if type(payload) is not dict:
        raise ValidationError("input_projection")
    return phase_c1.canonical_json_bytes(
        {"schema_version": schema_version, **payload}
    )


def _card_sha256(card: phase_c1.PhaseC1EvidenceCardV1) -> str:
    return phase_c1.sha256_bytes(
        phase_c1.canonical_json_bytes(_json_value(card))
    )


def _ordered_reasons(
    protocol: phase_c1.PhaseC1ProtocolV1,
    reasons: set[str],
) -> tuple[str, ...]:
    return tuple(
        code for code in protocol.reason_code_order if code in reasons
    )


def _review_is_admitted(
    review: phase_c1.PhaseC1SourceReviewReceiptV1,
) -> bool:
    return (
        review.verdict == "admitted"
        and review.critical_findings == 0
        and review.important_findings == 0
        and review.minor_findings == 0
        and not review.raw_rows_read
        and not review.private_data_read
        and not review.model_evaluation_run
        and not review.provider_accessed
        and not review.runtime_modified
    )


def _reliability_rule(
    protocol: phase_c1.PhaseC1ProtocolV1,
    metric_id: str,
) -> Mapping[str, int | str] | None:
    for rule in protocol.reliability_rules:
        if rule.get("metric_id") == metric_id:
            return rule
    return None


def _derive_reliability(
    evidence: phase_c1.PhaseC1ReliabilityEvidenceV1,
    *,
    independent_rater_count: int | None,
    protocol: phase_c1.PhaseC1ProtocolV1,
) -> tuple[str, tuple[str, ...]]:
    reasons: set[str] = set()
    rule = _reliability_rule(protocol, evidence.metric_id)
    if rule is None:
        reasons.add("reliability_metric_unapproved")
    if independent_rater_count is None:
        reasons.add("rater_count_unresolved")
    elif independent_rater_count < 2:
        reasons.add("reliability_effective_sample_insufficient")
    if not evidence.preadjudication:
        reasons.add("reliability_not_preadjudication")
    if not evidence.verifiable:
        reasons.add("reliability_unverifiable")

    rated = evidence.rated_unit_count
    positives = evidence.published_positive_count
    if rated is None:
        reasons.add("reliability_effective_sample_insufficient")
    if positives is None:
        reasons.update(
            {
                "published_positive_count_missing",
                "reliability_effective_sample_insufficient",
            }
        )
    elif rated is not None and positives > rated:
        raise ValidationError("positive_count_exceeds_rated_units")
    elif positives < int(
        protocol.positive_support_rule[
            "minimum_published_positive_count"
        ]
    ):
        reasons.update(
            {
                "positive_support_below_93",
                "reliability_effective_sample_insufficient",
            }
        )

    intervals = (
        evidence.point_micros,
        evidence.lower_95_micros,
        evidence.upper_95_micros,
    )
    if any(value is None for value in intervals):
        reasons.add("reliability_interval_uncertain")
    blocked = {
        "rater_count_unresolved",
        "reliability_effective_sample_insufficient",
        "published_positive_count_missing",
        "positive_support_below_93",
    }
    if (
        not evidence.verifiable
        or not evidence.preadjudication
        or rule is None
        or bool(blocked.intersection(reasons))
        or any(value is None for value in intervals)
    ):
        return "defer", _ordered_reasons(protocol, reasons)

    point, lower, upper = intervals
    assert point is not None and lower is not None and upper is not None
    if (
        point >= int(rule["pass_point_min_micros"])
        and lower >= int(rule["pass_lower_95_min_micros"])
    ):
        return "pass", _ordered_reasons(protocol, reasons)
    if upper < int(rule["reject_upper_95_max_exclusive_micros"]):
        reasons.add("reliability_upper_below_0_67")
        return "rejected", _ordered_reasons(protocol, reasons)
    reasons.add("reliability_interval_uncertain")
    return "defer", _ordered_reasons(protocol, reasons)


def _derive_candidate(
    source: phase_c1.PhaseC1SourceReceiptV1,
    card: phase_c1.PhaseC1EvidenceCardV1,
    *,
    protocol: phase_c1.PhaseC1ProtocolV1,
) -> dict[str, object]:
    rejected: set[str] = set()
    unresolved: set[str] = set()
    definition = next(
        (
            document
            for document in source.documents
            if document.document_id == card.native_definition_document_id
        ),
        None,
    )
    if definition is None:
        raise ValidationError("native_definition_document_missing")
    if not definition.authoritative:
        unresolved.add("authoritative_provenance_unverified")
    if not definition.public_without_login:
        unresolved.add("access_unresolved")
    construct = next(
        (
            item
            for item in protocol.signal_constructs
            if item.get("signal") == card.signal
        ),
        None,
    )
    if construct is None:
        raise ValidationError("signal_construct_order")
    if card.native_label in construct["excluded_proxies"]:
        rejected.add("proxy_construct")
    if source.source_id != card.source_id:
        raise ValidationError("source_reference_missing")

    source_rejections = {
        ("access_status", "login_required"): "access_requires_login",
        ("access_status", "restricted"): "access_restricted",
        ("license_status", "incompatible"): "license_incompatible",
        ("ethical_use_status", "incompatible"): "ethical_use_incompatible",
        ("conversation_status", "acted_or_scripted"): "acted_or_scripted",
        (
            "conversation_status",
            "mixed_unseparated",
        ): "mixed_unseparated_conversation",
    }
    for (field, value), reason in source_rejections.items():
        if getattr(source, field) == value:
            rejected.add(reason)
    source_unresolved = {
        "access_status": "access_unresolved",
        "license_status": "license_unresolved",
        "ethical_use_status": "ethical_use_unresolved",
        "conversation_status": "conversation_status_unresolved",
    }
    for field, reason in source_unresolved.items():
        if getattr(source, field) == "unresolved":
            unresolved.add(reason)

    if card.construct_correspondence == "proxy_construct":
        rejected.add("proxy_construct")
    elif card.construct_correspondence == "target_absent":
        rejected.add("target_label_absent")
    elif card.construct_correspondence != "direct_target_construct":
        unresolved.add("directness_unresolved")
    if card.annotation_modality == "unresolved":
        unresolved.add("source_documentation_incomplete")
    if card.temporal_unit == "conversation":
        rejected.add("conversation_level_only")
    elif card.temporal_unit == "other":
        rejected.add("temporal_unit_incompatible")
    elif card.temporal_unit == "unresolved":
        unresolved.add("temporal_unit_unresolved")
    if card.observer_method == "self_report":
        rejected.add("self_report_label")
    elif card.observer_method == "llm_generated":
        rejected.add("llm_generated_label")
    elif card.observer_method == "automated_proxy":
        rejected.add("proxy_construct")
    elif card.observer_method == "adjudicated_only_human_label":
        unresolved.add("reliability_not_preadjudication")
    elif card.observer_method == "unresolved":
        unresolved.add("observer_method_unresolved")
    if card.independent_rater_count is None:
        unresolved.add("rater_count_unresolved")
    elif card.independent_rater_count < 2:
        rejected.add("single_rater")

    if rejected:
        status = "rejected"
        reasons = _ordered_reasons(protocol, rejected)
    elif unresolved:
        status = "unresolved"
        reasons = _ordered_reasons(protocol, unresolved)
    else:
        reliability_status, reliability_reasons = _derive_reliability(
            card.reliability,
            independent_rater_count=card.independent_rater_count,
            protocol=protocol,
        )
        if reliability_status == "pass":
            status, reasons = "admissible", ()
        elif reliability_status == "rejected":
            status = "rejected"
            reasons = ("reliability_upper_below_0_67",)
        else:
            status, reasons = "unresolved", reliability_reasons
    if (
        card.claimed_status != status
        or card.claimed_reason_codes != reasons
    ):
        raise ValidationError("card_claim_mismatch")
    return {
        "card_id": card.card_id,
        "status": status,
        "reason_codes": reasons,
    }


def _derived_material_status(
    material: phase_c1.PhaseC1FallbackMaterialEvidenceV1,
    source: phase_c1.PhaseC1SourceReceiptV1,
    all_document_ids: set[str],
) -> str:
    source_document_ids = {
        document.document_id for document in source.documents
    }
    document_groups = (
        material.material_evidence_document_ids,
        material.license_evidence_document_ids,
        material.ethical_use_evidence_document_ids,
        material.rater_feasibility_evidence_document_ids,
    )
    for documents in document_groups:
        if any(document not in all_document_ids for document in documents):
            raise ValidationError("fallback_fact_document_unknown")
        if any(document not in source_document_ids for document in documents):
            raise ValidationError("fallback_fact_document_wrong_source")
    if any(not documents for documents in document_groups):
        return "unresolved"
    facts = (
        material.public_spontaneous_material_status,
        material.license_status,
        material.ethical_use_status,
        material.minimum_three_raters_status,
    )
    if facts == ("available", "compatible", "compatible", "feasible"):
        return "feasible"
    if (
        "unresolved" not in facts
        and any(
            value in {"unavailable", "incompatible", "infeasible"}
            for value in facts
        )
    ):
        return "infeasible"
    return "unresolved"


def _derive_fallback(
    signal: str,
    *,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
) -> str:
    assessments = source_ledger.fallback_assessments
    if tuple(item.signal for item in assessments) != TARGET_SIGNALS:
        raise ValidationError("fallback_signal_missing")
    assessment = assessments[TARGET_SIGNALS.index(signal)]
    if not assessment.preregistration_only or assessment.execution_authorized:
        raise ValidationError("fallback_authorization")
    expected_order = search_ledger.fallback_material_candidate_order
    if (
        tuple(item.source_id for item in assessment.material_evidence)
        != expected_order
    ):
        raise ValidationError("fallback_material_order_mismatch")
    sources = {
        source.source_id: source for source in source_ledger.sources
    }
    all_document_ids = {
        document.document_id
        for source in source_ledger.sources
        for document in source.documents
    }
    statuses: list[str] = []
    for material in assessment.material_evidence:
        source = sources.get(material.source_id)
        if (
            source is None
            or "fallback_material_candidate" not in source.phase_c1_roles
        ):
            raise ValidationError("source_reference_missing")
        status = _derived_material_status(
            material,
            source,
            all_document_ids,
        )
        if material.status != status:
            raise ValidationError("fallback_material_status_mismatch")
        statuses.append(status)
    derived = (
        "feasible"
        if "feasible" in statuses
        else "infeasible"
        if search_ledger.fail_ready_by_signal[signal]
        and (not statuses or all(status == "infeasible" for status in statuses))
        else "unresolved"
    )
    reasons = (
        ("annotation_fallback_feasible",)
        if derived == "feasible"
        else ()
        if derived == "infeasible"
        else ("annotation_fallback_unresolved",)
    )
    if assessment.status != derived or assessment.reason_codes != reasons:
        raise ValidationError("fallback_reason_mismatch")
    return derived


def _derive_signal(
    signal: str,
    *,
    dispositions: tuple[dict[str, object], ...],
    cards: Mapping[str, phase_c1.PhaseC1EvidenceCardV1],
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
) -> dict[str, object]:
    selected = tuple(
        item
        for item in dispositions
        if cards[str(item["card_id"])].signal == signal
    )
    admissible = tuple(
        str(item["card_id"])
        for item in selected
        if item["status"] == "admissible"
    )
    rejected = sum(item["status"] == "rejected" for item in selected)
    unresolved = sum(item["status"] == "unresolved" for item in selected)
    fallback = _derive_fallback(
        signal,
        search_ledger=search_ledger,
        source_ledger=source_ledger,
    )
    fail_guard_blocked = (
        search_ledger.overflow_count_by_signal[signal] > 0
        or search_ledger.fallback_material_overflow_count > 0
        or any(
            query.status != "complete" or query.truncated
            for query in search_ledger.query_records
            if query.signal == signal
            or query.query_kind == "fallback_material"
        )
        or search_ledger.backward_citation_stop_by_signal[signal]
        in {"budget_reached", "incomplete"}
        or search_ledger.forward_citation_stop_by_signal[signal]
        in {"budget_reached", "incomplete"}
    )
    if admissible:
        decision = "pass"
    elif (
        unresolved
        or fail_guard_blocked
        or not search_ledger.fail_ready_by_signal[signal]
        or fallback in {"feasible", "unresolved"}
    ):
        decision = "defer"
    else:
        decision = "fail"
    return {
        "signal": signal,
        "decision": decision,
        "admissible_card_ids": admissible,
        "rejected_card_count": rejected,
        "unresolved_card_count": unresolved,
        "annotation_fallback": fallback,
        "c2_eligible": decision == "pass",
    }


def _validate_search_derivations(
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
) -> None:
    expected_queries: list[
        tuple[str, str, str, str | None, str]
    ] = []
    for signal in protocol.target_signals:
        for channel in protocol.source_channels:
            channel_id = str(channel["channel_id"])
            for index, template in enumerate(
                protocol.query_templates,
                start=1,
            ):
                expected_queries.append(
                    (
                        f"c1-query-{signal}-{channel_id}-{index:02d}",
                        "direct_label_source",
                        channel_id,
                        signal,
                        template.format(signal=signal),
                    )
                )
    for channel in protocol.source_channels:
        channel_id = str(channel["channel_id"])
        for index, template in enumerate(
            protocol.fallback_material_query_templates,
            start=1,
        ):
            expected_queries.append(
                (
                    "c1-query-fallback-material-"
                    f"{channel_id}-{index:02d}",
                    "fallback_material",
                    channel_id,
                    None,
                    template,
                )
            )
    actual_queries = tuple(
        (
            query.query_id,
            query.query_kind,
            query.channel_id,
            query.signal,
            query.query_text,
        )
        for query in search_ledger.query_records
    )
    if (
        actual_queries != tuple(expected_queries)
        or len(actual_queries) != protocol.expected_total_query_count
        or sum(
            query.query_kind == "direct_label_source"
            for query in search_ledger.query_records
        )
        != protocol.expected_seed_query_count
        or sum(
            query.query_kind == "fallback_material"
            for query in search_ledger.query_records
        )
        != protocol.expected_fallback_material_query_count
    ):
        raise ValidationError("independent_search_query_grid")

    direct_candidates: dict[str, list[str]] = {
        signal: [] for signal in TARGET_SIGNALS
    }
    fallback_candidates: list[str] = []
    unresolved_by_signal = {
        signal: False for signal in TARGET_SIGNALS
    }
    fallback_unresolved = False
    for query in search_ledger.query_records:
        for discovery in query.discovery_records:
            if discovery.disposition == "retained_candidate":
                if discovery.candidate_source_id is None:
                    raise ValidationError(
                        "independent_candidate_source"
                    )
                if query.query_kind == "fallback_material":
                    fallback_candidates.append(
                        discovery.candidate_source_id
                    )
                else:
                    if query.signal not in TARGET_SIGNALS:
                        raise ValidationError(
                            "independent_search_signal"
                        )
                    direct_candidates[query.signal].append(
                        discovery.candidate_source_id
                    )
            elif discovery.disposition == "unresolved":
                if query.query_kind == "fallback_material":
                    fallback_unresolved = True
                else:
                    if query.signal not in TARGET_SIGNALS:
                        raise ValidationError(
                            "independent_search_signal"
                        )
                    unresolved_by_signal[query.signal] = True
    for direction in _CITATION_DIRECTIONS:
        for signal in TARGET_SIGNALS:
            records = tuple(
                citation
                for citation in search_ledger.citation_records
                if citation.signal == signal
                and citation.direction == direction
            )
            claimed_count = (
                search_ledger.backward_citation_count_by_signal[signal]
                if direction == "backward"
                else search_ledger.forward_citation_count_by_signal[signal]
            )
            if len(records) != claimed_count:
                raise ValidationError("independent_citation_count")
            for citation in records:
                if citation.disposition == "retained_candidate":
                    if citation.candidate_source_id is None:
                        raise ValidationError(
                            "independent_candidate_source"
                        )
                    direct_candidates[signal].append(
                        citation.candidate_source_id
                    )
                elif citation.disposition == "unresolved":
                    unresolved_by_signal[signal] = True

    derived_candidate_order: dict[str, tuple[str, ...]] = {}
    derived_overflow: dict[str, int] = {}
    for signal in TARGET_SIGNALS:
        unique = tuple(dict.fromkeys(direct_candidates[signal]))
        derived_candidate_order[signal] = unique[
            : protocol.max_detailed_candidates_per_signal
        ]
        derived_overflow[signal] = max(
            0,
            len(unique) - protocol.max_detailed_candidates_per_signal,
        )
    unique_fallback = tuple(dict.fromkeys(fallback_candidates))
    derived_fallback_order = unique_fallback[
        : protocol.max_detailed_fallback_material_candidates
    ]
    derived_fallback_overflow = max(
        0,
        len(unique_fallback)
        - protocol.max_detailed_fallback_material_candidates,
    )
    if (
        dict(search_ledger.candidate_order_by_signal)
        != derived_candidate_order
        or dict(search_ledger.overflow_count_by_signal)
        != derived_overflow
        or search_ledger.fallback_material_candidate_order
        != derived_fallback_order
        or search_ledger.fallback_material_overflow_count
        != derived_fallback_overflow
    ):
        raise ValidationError("independent_candidate_order")

    fallback_queries_ready = all(
        query.status == "complete" and not query.truncated
        for query in search_ledger.query_records
        if query.query_kind == "fallback_material"
    )
    derived_fail_ready: dict[str, bool] = {}
    for signal in TARGET_SIGNALS:
        direct_queries_ready = all(
            query.status == "complete" and not query.truncated
            for query in search_ledger.query_records
            if query.signal == signal
        )
        derived_fail_ready[signal] = (
            direct_queries_ready
            and fallback_queries_ready
            and search_ledger.backward_citation_stop_by_signal[signal]
            in _EXHAUSTIVE_CITATION_STOPS
            and search_ledger.forward_citation_stop_by_signal[signal]
            in _EXHAUSTIVE_CITATION_STOPS
            and not unresolved_by_signal[signal]
            and not fallback_unresolved
            and derived_overflow[signal] == 0
            and derived_fallback_overflow == 0
        )
    derived_search_complete = (
        all(
            query.status == "complete" and not query.truncated
            for query in search_ledger.query_records
        )
        and all(
            search_ledger.backward_citation_stop_by_signal[signal]
            in _EXHAUSTIVE_CITATION_STOPS
            and search_ledger.forward_citation_stop_by_signal[signal]
            in _EXHAUSTIVE_CITATION_STOPS
            for signal in TARGET_SIGNALS
        )
    )
    if dict(search_ledger.fail_ready_by_signal) != derived_fail_ready:
        raise ValidationError("independent_fail_ready")
    if search_ledger.search_complete != derived_search_complete:
        raise ValidationError("independent_search_complete")


def derive_phase_c1_projection_independently(
    *,
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
    review_receipt: phase_c1.PhaseC1SourceReviewReceiptV1,
) -> dict[str, object]:
    protocol_bytes = _canonical_dataclass_bytes(
        protocol,
        "EmotionStatePhaseC1DiscoveryProtocolV1",
    )
    search_bytes = _canonical_dataclass_bytes(
        search_ledger,
        "EmotionStatePhaseC1SearchLedgerV1",
    )
    source_bytes = _canonical_dataclass_bytes(
        source_ledger,
        "EmotionStatePhaseC1SourceEvidenceLedgerV1",
    )
    if (
        protocol.checkpoint_id != CHECKPOINT_ID
        or protocol.protocol_id != PROTOCOL_ID
        or protocol.target_signals != TARGET_SIGNALS
        or protocol.reason_code_order != REASON_CODE_ORDER
        or search_ledger.protocol_sha256
        != phase_c1.sha256_bytes(protocol_bytes)
        or source_ledger.protocol_sha256
        != phase_c1.sha256_bytes(protocol_bytes)
        or source_ledger.search_ledger_sha256
        != phase_c1.sha256_bytes(search_bytes)
        or review_receipt.protocol_sha256
        != phase_c1.sha256_bytes(protocol_bytes)
        or review_receipt.search_ledger_sha256
        != phase_c1.sha256_bytes(search_bytes)
        or review_receipt.source_evidence_ledger_sha256
        != phase_c1.sha256_bytes(source_bytes)
    ):
        raise ValidationError("projection_input_binding")
    if not _review_is_admitted(review_receipt):
        raise ValidationError("projection_review_binding")
    _validate_search_derivations(protocol, search_ledger)

    sources = {
        source.source_id: source for source in source_ledger.sources
    }
    cards = {card.card_id: card for card in source_ledger.cards}
    if len(cards) != len(source_ledger.cards):
        raise ValidationError("candidate_card_missing_or_duplicate")
    expected_pairs = tuple(
        (signal, source_id)
        for signal in protocol.target_signals
        for source_id in search_ledger.candidate_order_by_signal[signal]
    )
    actual_pairs = tuple(
        (card.signal, card.source_id) for card in source_ledger.cards
    )
    if actual_pairs != expected_pairs:
        raise ValidationError("candidate_card_missing_or_duplicate")
    dispositions: list[dict[str, object]] = []
    for card in source_ledger.cards:
        source = sources.get(card.source_id)
        if source is None:
            raise ValidationError("source_reference_missing")
        dispositions.append(
            _derive_candidate(source, card, protocol=protocol)
        )
    decision_rows = tuple(
        _derive_signal(
            signal,
            dispositions=tuple(dispositions),
            cards=cards,
            search_ledger=search_ledger,
            source_ledger=source_ledger,
        )
        for signal in protocol.target_signals
    )
    decisions = tuple(str(item["decision"]) for item in decision_rows)
    if all(value == "pass" for value in decisions):
        overall = "proceed_full_to_c2"
    elif any(value == "pass" for value in decisions):
        overall = "proceed_partial_to_c2"
    elif any(value == "defer" for value in decisions):
        overall = "defer_c2"
    else:
        overall = "stop_c2"
    return {
        "candidate_dispositions": dispositions,
        "signal_decisions": list(decision_rows),
        "overall_decision": overall,
        "c2_eligible_signals": [
            str(item["signal"])
            for item in decision_rows
            if item["c2_eligible"] is True
        ],
    }


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


def _disposition_counts(records: tuple[object, ...]) -> dict[str, int]:
    return {
        disposition: sum(
            getattr(record, "disposition") == disposition
            for record in records
        )
        for disposition in _DISCOVERY_DISPOSITIONS
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
        "nonexhaustive_citation_stop_count": sum(
            stop not in _EXHAUSTIVE_CITATION_STOPS
            for signal in protocol.target_signals
            for stop in (
                search_ledger.backward_citation_stop_by_signal[signal],
                search_ledger.forward_citation_stop_by_signal[signal],
            )
        ),
        "search_complete": search_ledger.search_complete,
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
        for direction in _CITATION_DIRECTIONS:
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
                raise ValidationError("source_signature_collision")
            existing["count"] = int(existing["count"]) + 1
    return [entries[digest] for digest in sorted(entries)], source_hashes


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


def _effective_sample_sufficient(
    card: phase_c1.PhaseC1EvidenceCardV1,
) -> bool:
    reliability = card.reliability
    return (
        type(card.independent_rater_count) is int
        and card.independent_rater_count >= 2
        and type(reliability.rated_unit_count) is int
        and reliability.rated_unit_count > 0
        and type(reliability.published_positive_count) is int
        and reliability.published_positive_count >= 93
        and reliability.rated_unit_count
        >= reliability.published_positive_count
    )


def _diagnostic(
    card: phase_c1.PhaseC1EvidenceCardV1,
    *,
    source: phase_c1.PhaseC1SourceReceiptV1,
    source_signature_sha256: str,
    protocol: phase_c1.PhaseC1ProtocolV1,
) -> dict[str, object]:
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
    reliability = card.reliability
    return {
        "evidence_card_sha256": _card_sha256(card),
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
        "effective_sample_sufficient": _effective_sample_sufficient(card),
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


def _derive_expected_result(
    *,
    implementation_head: str,
    validator_blob_id: str,
    protocol_bytes: bytes,
    search_ledger_bytes: bytes,
    source_ledger_bytes: bytes,
    review_receipt_bytes: bytes,
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
    review_receipt: phase_c1.PhaseC1SourceReviewReceiptV1,
) -> dict[str, object]:
    if (
        _LOWER_GIT_ID_RE.fullmatch(implementation_head) is None
        or _LOWER_GIT_ID_RE.fullmatch(validator_blob_id) is None
    ):
        raise ValidationError("implementation_identity")
    projection = derive_phase_c1_projection_independently(
        protocol=protocol,
        search_ledger=search_ledger,
        source_ledger=source_ledger,
        review_receipt=review_receipt,
    )
    dispositions = {
        str(item["card_id"]): item
        for item in projection["candidate_dispositions"]
    }
    cards_by_id = {card.card_id: card for card in source_ledger.cards}
    sources_by_id = {
        source.source_id: source for source in source_ledger.sources
    }
    signatures, source_signature_by_id = _source_signature_counts(
        source_ledger,
        protocol=protocol,
        search_ledger=search_ledger,
    )
    fallback_status_counts = {
        assessment.signal: {
            status: sum(
                material.status == status
                for material in assessment.material_evidence
            )
            for status in _FALLBACK_STATUSES
        }
        for assessment in source_ledger.fallback_assessments
    }
    decision_by_signal = {
        str(item["signal"]): item
        for item in projection["signal_decisions"]
    }
    per_signal: list[dict[str, object]] = []
    for signal in protocol.target_signals:
        decision = decision_by_signal[signal]
        signal_cards = tuple(
            card for card in source_ledger.cards if card.signal == signal
        )
        per_signal.append(
            {
                "signal": signal,
                "decision": decision["decision"],
                "admissible_evidence_card_sha256s": [
                    _card_sha256(cards_by_id[card_id])
                    for card_id in decision["admissible_card_ids"]
                ],
                "rejected_card_count": decision["rejected_card_count"],
                "unresolved_card_count": decision["unresolved_card_count"],
                "annotation_fallback": decision["annotation_fallback"],
                "fallback_material_status_counts": (
                    fallback_status_counts[signal]
                ),
                "reliability_diagnostics": [
                    _diagnostic(
                        card,
                        source=sources_by_id[card.source_id],
                        source_signature_sha256=source_signature_by_id[
                            card.source_id
                        ],
                        protocol=protocol,
                    )
                    for card in signal_cards
                ],
                "c2_eligible": decision["c2_eligible"],
            }
        )
    result: dict[str, object] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "checkpoint_id": CHECKPOINT_ID,
        "protocol_id": PROTOCOL_ID,
        "target_signals": list(protocol.target_signals),
        "implementation_head": implementation_head,
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
        "search_lane_counts": _search_lane_counts(protocol, search_ledger),
        "source_counts": _source_counts(source_ledger),
        "source_signature_counts": signatures,
        "card_counts_by_status": {
            status: sum(
                item["status"] == status
                for item in dispositions.values()
            )
            for status in ("admissible", "rejected", "unresolved")
        },
        "reason_code_counts": _count_reasons(
            protocol,
            search_ledger,
            source_ledger,
        ),
        "per_signal": per_signal,
        "overall_decision": projection["overall_decision"],
        "c2_eligible_signals": projection["c2_eligible_signals"],
        "boundary": {field: False for field in BOUNDARY_FIELDS},
        "limitations": list(LIMITATIONS),
        "runtime_approved": False,
    }
    result["aggregate_content_sha256"] = phase_c1.sha256_bytes(
        phase_c1.canonical_json_bytes(result)
    )
    if len(phase_c1.canonical_json_bytes(result)) > MAX_AGGREGATE_RESULT_BYTES:
        raise ValidationError("result_size")
    return result


def _forbidden_content(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                return True
            normalized = key.casefold().replace("-", "_")
            if normalized in RESULT_FORBIDDEN_KEYS:
                return True
            if _forbidden_content(item):
                return True
        return False
    if isinstance(value, list):
        return any(_forbidden_content(item) for item in value)
    return False


def _validate_result_against_inputs(
    payload: object,
    inputs: Mapping[str, object],
) -> dict[str, object]:
    if type(payload) is not dict:
        raise ValidationError("result_object")
    if frozenset(payload) != RESULT_FIELDS:
        raise ValidationError("result_fields")
    if _forbidden_content(payload):
        raise ValidationError("forbidden_content")
    implementation_head = payload.get("implementation_head")
    validator_blob_id = payload.get("validator_blob_id")
    if type(implementation_head) is not str:
        raise ValidationError("implementation_identity")
    if type(validator_blob_id) is not str:
        raise ValidationError("implementation_identity")
    expected = _derive_expected_result(
        implementation_head=implementation_head,
        validator_blob_id=validator_blob_id,
        protocol_bytes=inputs["protocol_bytes"],
        search_ledger_bytes=inputs["search_ledger_bytes"],
        source_ledger_bytes=inputs["source_ledger_bytes"],
        review_receipt_bytes=inputs["review_receipt_bytes"],
        protocol=inputs["protocol"],
        search_ledger=inputs["search_ledger"],
        source_ledger=inputs["source_ledger"],
        review_receipt=inputs["review_receipt"],
    )
    try:
        payload_bytes = phase_c1.canonical_json_bytes(payload)
    except (TypeError, ValueError) as exc:
        raise ValidationError("result_encoding") from exc
    if len(payload_bytes) > MAX_AGGREGATE_RESULT_BYTES:
        raise ValidationError("result_size")
    if payload_bytes != phase_c1.canonical_json_bytes(expected):
        raise ValidationError("input_projection_binding")
    return expected


def validate_phase_c1_result_payload(payload: object) -> dict[str, object]:
    return _validate_result_against_inputs(
        payload,
        validate_phase_c1_inputs(),
    )


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


def render_expected_report_independently(
    payload: Mapping[str, object],
) -> bytes:
    try:
        final_result_sha256 = phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(payload)
        )
        lines = [
            (
                "# EMOTION-STATE-004 Phase C1 Operational-Signal "
                "Evidence Admission"
            ),
            "",
            f"- Checkpoint: {payload['checkpoint_id']}",
            f"- Result schema: {payload['schema_version']}",
            f"- Protocol: {payload['protocol_id']}",
            f"- Implementation HEAD: {payload['implementation_head']}",
            f"- Validator blob: {payload['validator_blob_id']}",
            f"- Protocol SHA-256: {payload['protocol_sha256']}",
            f"- Search-ledger SHA-256: {payload['search_ledger_sha256']}",
            (
                "- Source-evidence-ledger SHA-256: "
                f"{payload['source_evidence_ledger_sha256']}"
            ),
            (
                "- Source-review-receipt SHA-256: "
                f"{payload['source_review_receipt_sha256']}"
            ),
            (
                "- Aggregate-content SHA-256: "
                f"{payload['aggregate_content_sha256']}"
            ),
            f"- result.json SHA-256: {final_result_sha256}",
            "",
            "## Aggregate",
            "",
            f"- Overall decision: {payload['overall_decision']}",
            f"- Search counts: {_compact(payload['search_counts'])}",
            f"- Source counts: {_compact(payload['source_counts'])}",
            (
                "- Candidate-card counts by status: "
                f"{_compact(payload['card_counts_by_status'])}"
            ),
            "- Reason-code counts:",
        ]
        reason_counts = payload["reason_code_counts"]
        if not isinstance(reason_counts, Mapping):
            raise ValidationError("report_result")
        for reason in REASON_CODE_ORDER:
            lines.append(f"  - {reason}: {reason_counts[reason]}")
        lines.extend(("", "## Per-Signal Decisions", ""))
        per_signal = payload["per_signal"]
        if not isinstance(per_signal, list):
            raise ValidationError("report_result")
        for raw_item in per_signal:
            if not isinstance(raw_item, Mapping):
                raise ValidationError("report_result")
            item = raw_item
            lines.extend(
                (
                    (
                        f"- {item['signal']}: decision={item['decision']}; "
                        f"c2_eligible={_compact(item['c2_eligible'])}; "
                        "annotation_fallback="
                        f"{item['annotation_fallback']}"
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
            if not isinstance(diagnostics, list):
                raise ValidationError("report_result")
            if not diagnostics:
                lines.append("    - unavailable")
            for raw_diagnostic in diagnostics:
                if not isinstance(raw_diagnostic, Mapping):
                    raise ValidationError("report_result")
                diagnostic = raw_diagnostic
                lines.append(
                    "    - "
                    "evidence_card_sha256="
                    f"{diagnostic['evidence_card_sha256']}; "
                    f"metric_id={diagnostic['metric_id']}; "
                    "point_micros="
                    f"{_available(diagnostic['point_micros'])}; "
                    "lower_95_micros="
                    f"{_available(diagnostic['lower_95_micros'])}; "
                    "upper_95_micros="
                    f"{_available(diagnostic['upper_95_micros'])}; "
                    "independent_rater_count="
                    f"{_available(diagnostic['independent_rater_count'])}; "
                    "rated_unit_count="
                    f"{_available(diagnostic['rated_unit_count'])}; "
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
        eligible = payload["c2_eligible_signals"]
        if not isinstance(eligible, list):
            raise ValidationError("report_result")
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
                    f"{_compact(payload['search_counts']['search_complete'])}."
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
                    "A partial decision admits only the named signal or "
                    "signals; it does not validate the others."
                ),
                "",
                "## Limitations",
                "",
            )
        )
        limitations = payload["limitations"]
        if not isinstance(limitations, list):
            raise ValidationError("report_result")
        lines.extend(f"- {limitation}" for limitation in limitations)
        lines.extend(
            (
                "",
                "## Closed Boundary",
                "",
                "Runtime approval: false.",
                "- No customer emotion was inferred.",
                (
                    "- No private data, participant rows, transcript rows, "
                    "or audio were read."
                ),
                "- No provider was accessed and no runtime was modified.",
                (
                    "- No real-call, latency, safety, conversion, production, "
                    "or commercial behavior is proven."
                ),
                "",
            )
        )
        return "\n".join(lines).encode("utf-8")
    except ValidationError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError("report_result") from exc


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
        raise ValidationError("root_not_absolute")
    return Path(os.path.abspath(os.path.normpath(raw)))


def _is_reparse_or_link(metadata: Any) -> bool:
    return (
        stat.S_ISLNK(metadata.st_mode)
        or bool(
            getattr(metadata, "st_file_attributes", 0)
            & REPARSE_POINT
        )
    )


def _safe_lstat(path: Path, *, missing_code: str) -> os.stat_result:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError as exc:
        raise ValidationError(missing_code) from exc
    except OSError as exc:
        raise ValidationError("path_metadata") from exc
    if _is_reparse_or_link(metadata):
        raise ValidationError("path_reparse_or_link")
    return metadata


def _metadata_identity(metadata: Any) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _directory_chain(target: Path) -> tuple[os.stat_result, ...]:
    root = _lexical_absolute(ROOT)
    target = _lexical_absolute(target)
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ValidationError("root_not_allowlisted") from exc
    metadata_items: list[os.stat_result] = []
    current = root
    root_metadata = _safe_lstat(current, missing_code="root_missing")
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise ValidationError("root_directory_type")
    metadata_items.append(root_metadata)
    for part in relative.parts:
        current = current / part
        metadata = _safe_lstat(current, missing_code="root_missing")
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValidationError("root_directory_type")
        metadata_items.append(metadata)
    return tuple(metadata_items)


def _read_stable_file(
    path: Path,
    expected: os.stat_result,
    *,
    maximum_bytes: int,
) -> bytes:
    if (
        _is_reparse_or_link(expected)
        or not stat.S_ISREG(expected.st_mode)
        or expected.st_size > maximum_bytes
    ):
        raise ValidationError("file_type_or_size")
    try:
        with open(path, "rb") as handle:
            before = os.fstat(handle.fileno())
            if (
                _is_reparse_or_link(before)
                or not stat.S_ISREG(before.st_mode)
                or _metadata_identity(before) != _metadata_identity(expected)
            ):
                raise ValidationError("file_changed_during_read")
            payload = handle.read(maximum_bytes + 1)
            after = os.fstat(handle.fileno())
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError("file_changed_during_read") from exc
    if (
        len(payload) > maximum_bytes
        or _is_reparse_or_link(after)
        or not stat.S_ISREG(after.st_mode)
        or _metadata_identity(after) != _metadata_identity(before)
    ):
        raise ValidationError("file_changed_during_read")
    return payload


def _read_exact_tracked_file(path: Path) -> bytes:
    root = _lexical_absolute(ROOT)
    target = _lexical_absolute(path)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValidationError("input_path") from exc
    with _AnchoredDirectory(
        target.parent,
        allowed_children=frozenset({target.name}),
    ) as anchor:
        file_metadata = anchor.child_metadata(target.name)
        payload = anchor.read_child(
            target.name,
            file_metadata,
            maximum_bytes=MAX_INPUT_FILE_BYTES,
        )
        anchor.validate()
        return payload


def _validate_validator_dependency_ast(payload: bytes) -> None:
    if type(payload) is not bytes:
        raise ValidationError("validator_dependency_ast")
    try:
        source = payload.decode("utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError) as exc:
        raise ValidationError("validator_dependency_ast") from exc

    expected_import_inventory = (
        ("from", 0, "__future__", (("annotations", None),)),
        ("import", (("ast", None),)),
        ("import", (("ctypes", None),)),
        ("import", (("json", None),)),
        ("import", (("os", None),)),
        ("import", (("re", None),)),
        ("import", (("stat", None),)),
        ("import", (("subprocess", None),)),
        ("import", (("sys", None),)),
        ("import", (("threading", None),)),
        (
            "from",
            0,
            "collections.abc",
            (("Mapping", None), ("Sequence", None)),
        ),
        ("from", 0, "ctypes", (("wintypes", None),)),
        (
            "from",
            0,
            "dataclasses",
            (("fields", None), ("is_dataclass", None)),
        ),
        ("from", 0, "pathlib", (("Path", None),)),
        (
            "from",
            0,
            "typing",
            (("Any", None), ("Final", None)),
        ),
        (
            "from",
            0,
            "scripts",
            (("emotion_state_phase_c1_contracts", "phase_c1"),),
        ),
    )
    import_nodes = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ),
        key=lambda node: (node.lineno, node.col_offset),
    )
    observed_imports: list[object] = []
    for node in import_nodes:
        if isinstance(node, ast.Import):
            observed_imports.append(
                (
                    "import",
                    tuple(
                        (alias.name, alias.asname)
                        for alias in node.names
                    ),
                )
            )
        else:
            observed_imports.append(
                (
                    "from",
                    node.level,
                    node.module,
                    tuple(
                        (alias.name, alias.asname)
                        for alias in node.names
                    ),
                )
            )
    if tuple(observed_imports) != expected_import_inventory:
        raise ValidationError("validator_dependency_ast")
    imported_binding_names: set[str] = set()
    for node in import_nodes:
        for alias in node.names:
            if alias.asname is not None:
                imported_binding_names.add(alias.asname)
            elif isinstance(node, ast.Import):
                imported_binding_names.add(alias.name.split(".", 1)[0])
            else:
                imported_binding_names.add(alias.name)

    project_module_prefix = ".".join(("scripts", ""))
    import_builtin_name = "".join(("__im", "port__"))
    compile_builtin_name = "".join(("com", "pile"))
    execution_names = frozenset(
        {
            "".join(("ex", "ec")),
            "".join(("ev", "al")),
            compile_builtin_name,
            import_builtin_name,
        }
    )
    dynamic_attribute_names = execution_names | frozenset(
        {"".join(("import", "_module"))}
    )
    forbidden_name_ids = execution_names | frozenset(
        {
            "".join(("__built", "ins__")),
            "".join(("glo", "bals")),
            "".join(("lo", "cals")),
            "".join(("va", "rs")),
            "".join(("set", "attr")),
            "".join(("del", "attr")),
            "".join(("has", "attr")),
            "".join(("d", "ir")),
            "".join(("break", "point")),
            "__loader__",
            "__spec__",
            "help",
            "quit",
            "exit",
            "copyright",
            "credits",
            "license",
        }
    )
    getattr_name = "".join(("get", "attr"))
    allowed_getattr_sources = (
        "getattr(value, field.name)",
        "getattr(source, field)",
        "getattr(record, 'disposition')",
        "getattr(metadata, 'st_file_attributes', 0)",
    )
    allowed_getattr_shapes = frozenset(
        ast.dump(
            ast.parse(source, mode="eval").body,
            include_attributes=False,
        )
        for source in allowed_getattr_sources
    )
    getattr_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == getattr_name
    )
    allowed_getattr_name_nodes: set[int] = set()
    for call in getattr_calls:
        if (
            ast.dump(call, include_attributes=False)
            not in allowed_getattr_shapes
        ):
            raise ValidationError("validator_dependency_ast")
        allowed_getattr_name_nodes.add(id(call.func))

    module_attribute_inventories = (
        (
            "ast",
            frozenset(
                {
                    "AST",
                    "Assign",
                    "AsyncFunctionDef",
                    "Attribute",
                    "Call",
                    "ClassDef",
                    "Constant",
                    "Expr",
                    "FunctionDef",
                    "Import",
                    "ImportFrom",
                    "Name",
                    "Subscript",
                    "arg",
                    "dump",
                    "iter_child_nodes",
                    "iter_fields",
                    "parse",
                    "walk",
                }
            ),
        ),
        ("json", frozenset({"dumps"})),
        ("re", frozenset({"compile"})),
        (
            "stat",
            frozenset(
                {
                    "FILE_ATTRIBUTE_REPARSE_POINT",
                    "S_ISDIR",
                    "S_ISLNK",
                    "S_ISREG",
                }
            ),
        ),
        ("threading", frozenset({"Event", "Thread"})),
        (
            "wintypes",
            frozenset(
                {
                    "BOOL",
                    "DWORD",
                    "FILETIME",
                    "HANDLE",
                    "LPCWSTR",
                    "LPVOID",
                }
            ),
        ),
        (
            "ctypes",
            frozenset(
                {
                    "POINTER",
                    "Structure",
                    "WinDLL",
                    "byref",
                    "c_void_p",
                }
            ),
        ),
        ("sys", frozenset({"argv", "path", "stderr"})),
        (
            "os",
            frozenset(
                {
                    "O_RDONLY",
                    "O_DIRECTORY",
                    "O_NOFOLLOW",
                    "PathLike",
                    "close",
                    "curdir",
                    "environ",
                    "fspath",
                    "fstat",
                    "lstat",
                    "name",
                    "open",
                    "pardir",
                    "path",
                    "read",
                    "scandir",
                    "stat",
                    "stat_result",
                }
            ),
        ),
        (
            "subprocess",
            frozenset(
                {
                    "DEVNULL",
                    "PIPE",
                    "Popen",
                    "SubprocessError",
                    "TimeoutExpired",
                }
            ),
        ),
        (
            "phase_c1",
            frozenset(
                {
                    "PhaseC1ContractError",
                    "PhaseC1EvidenceCardV1",
                    "PhaseC1FallbackMaterialEvidenceV1",
                    "PhaseC1ProtocolV1",
                    "PhaseC1QueryRecordV1",
                    "PhaseC1ReliabilityEvidenceV1",
                    "PhaseC1SearchLedgerV1",
                    "PhaseC1SourceEvidenceLedgerV1",
                    "PhaseC1SourceReceiptV1",
                    "PhaseC1SourceReviewReceiptV1",
                    "canonical_json_bytes",
                    "load_json_strict",
                    "sha256_bytes",
                    "validate_discovery_protocol",
                    "validate_search_ledger",
                    "validate_source_evidence_ledger",
                    "validate_source_review_receipt",
                }
            ),
        ),
    )
    module_alias_names = frozenset(
        module_name
        for module_name, _allowed_attributes in (
            module_attribute_inventories
        )
    )
    stdout_write_shape = ast.dump(
        ast.parse(
            (
                "sys.stdout.buffer.write("
                "phase_c1.canonical_json_bytes(payload))"
            ),
            mode="eval",
        ).body,
        include_attributes=False,
    )
    stdout_write_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "buffer"
        and isinstance(node.func.value.value, ast.Attribute)
        and node.func.value.value.attr == "stdout"
        and isinstance(node.func.value.value.value, ast.Name)
        and node.func.value.value.value.id == "sys"
    )
    parent_by_child_id = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    if (
        len(stdout_write_calls) != 1
        or ast.dump(
            stdout_write_calls[0],
            include_attributes=False,
        ) != stdout_write_shape
        or not isinstance(
            parent_by_child_id.get(id(stdout_write_calls[0])),
            ast.Expr,
        )
    ):
        raise ValidationError("validator_dependency_ast")
    stdout_ancestor: ast.AST | None = parent_by_child_id.get(
        id(stdout_write_calls[0]),
    )
    while (
        stdout_ancestor is not None
        and not isinstance(
            stdout_ancestor,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    ):
        stdout_ancestor = parent_by_child_id.get(id(stdout_ancestor))
    if (
        not isinstance(stdout_ancestor, ast.FunctionDef)
        or stdout_ancestor.name != "main"
    ):
        raise ValidationError("validator_dependency_ast")
    stdout_call = stdout_write_calls[0]
    stdout_root_attribute = stdout_call.func.value.value
    stdout_module_name = stdout_root_attribute.value
    allowed_stdout_root_attribute_nodes = {
        id(stdout_root_attribute),
    }
    allowed_stdout_module_name_nodes = {
        id(stdout_module_name),
    }
    allowed_module_name_load_nodes = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in module_alias_names
        and any(
            node.value.id == module_name
            and node.attr in allowed_attributes
            for module_name, allowed_attributes in (
                module_attribute_inventories
            )
        )
    } | allowed_stdout_module_name_nodes
    os_path_attribute_inventory = frozenset(
        {
            "abspath",
            "dirname",
            "isabs",
            "join",
            "normcase",
            "normpath",
        }
    )
    allowed_os_path_nodes = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name)
        and node.value.value.id == "os"
        and node.value.attr == "path"
        and node.attr in os_path_attribute_inventory
    }
    allowed_windll_shape = ast.dump(
        ast.parse(
            "ctypes.WinDLL('kernel32', use_last_error=True)",
            mode="eval",
        ).body,
        include_attributes=False,
    )
    windll_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "ctypes"
        and node.func.attr == "WinDLL"
    )
    if len(windll_calls) != 3:
        raise ValidationError("validator_dependency_ast")
    allowed_windll_nodes: set[int] = set()
    allowed_kernel32_name_nodes: set[int] = set()
    for call in windll_calls:
        if ast.dump(call, include_attributes=False) != allowed_windll_shape:
            raise ValidationError("validator_dependency_ast")
        assignments = tuple(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and node.value is call
        )
        if (
            len(assignments) != 1
            or len(assignments[0].targets) != 1
            or not isinstance(assignments[0].targets[0], ast.Name)
            or assignments[0].targets[0].id != "kernel32"
        ):
            raise ValidationError("validator_dependency_ast")
        allowed_windll_nodes.add(id(call.func))
        allowed_kernel32_name_nodes.add(id(assignments[0].targets[0]))
    kernel32_attribute_inventory = frozenset(
        {
            "CloseHandle",
            "CreateFileW",
            "GetFileInformationByHandle",
        }
    )
    allowed_kernel32_name_nodes.update(
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "kernel32"
        and node.attr in kernel32_attribute_inventory
    )

    allowed_popen_shape = ast.dump(
        ast.parse(
            (
                "subprocess.Popen("
                "command, "
                "cwd=repository_root, "
                "stdin=subprocess.DEVNULL, "
                "stdout=subprocess.PIPE, "
                "stderr=subprocess.PIPE, "
                "shell=False, "
                "close_fds=True, "
                "env=_git_environment())"
            ),
            mode="eval",
        ).body,
        include_attributes=False,
    )
    popen_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "Popen"
    )
    if (
        len(popen_calls) != 1
        or ast.dump(popen_calls[0], include_attributes=False)
        != allowed_popen_shape
    ):
        raise ValidationError("validator_dependency_ast")
    git_functions = tuple(
        node
        for node in ast.walk(tree)
        if type(node).__name__ == "FunctionDef"
        and node.name == "_git"
    )
    if (
        len(git_functions) != 1
        or git_functions[0].args.vararg is None
        or git_functions[0].args.vararg.arg != "arguments"
        or git_functions[0].decorator_list
    ):
        raise ValidationError("validator_dependency_ast")
    git_function = git_functions[0]
    git_function_source = "\n".join(
        source.splitlines()[
            git_function.lineno - 1 : git_function.end_lineno
        ]
    )
    git_function_digest = phase_c1.sha256_bytes(
        git_function_source.encode("utf-8")
    )
    git_function_node_ids = {
        id(node) for node in ast.walk(git_function)
    }
    for node in ast.walk(git_function):
        if (
            isinstance(node, ast.Name)
            and node.id == "arguments"
            and type(node.ctx).__name__ in {"Store", "Del"}
        ):
            raise ValidationError("validator_dependency_ast")

    allowed_command_assignment_shape = ast.dump(
        ast.parse(
            (
                "command = ["
                "'git', "
                "'--no-replace-objects', "
                "'--no-lazy-fetch', "
                "*arguments]"
            )
        ).body[0],
        include_attributes=False,
    )
    command_assignments = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "command"
            for target in node.targets
        )
    )
    if (
        len(command_assignments) != 1
        or id(command_assignments[0]) not in git_function_node_ids
        or ast.dump(
            command_assignments[0],
            include_attributes=False,
        )
        != allowed_command_assignment_shape
    ):
        raise ValidationError("validator_dependency_ast")
    command_assignment = command_assignments[0]
    assert len(command_assignment.targets) == 1
    command_target = command_assignment.targets[0]
    assert isinstance(command_target, ast.Name)
    if (
        len(popen_calls[0].args) != 1
        or not isinstance(popen_calls[0].args[0], ast.Name)
        or popen_calls[0].args[0].id != "command"
        or id(popen_calls[0]) not in git_function_node_ids
    ):
        raise ValidationError("validator_dependency_ast")
    allowed_command_name_nodes = {
        id(command_target),
        id(popen_calls[0].args[0]),
    }

    popen_assignments = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and node.value is popen_calls[0]
    )
    if (
        len(popen_assignments) != 1
        or id(popen_assignments[0]) not in git_function_node_ids
        or len(popen_assignments[0].targets) != 1
        or not isinstance(popen_assignments[0].targets[0], ast.Name)
        or popen_assignments[0].targets[0].id != "process"
    ):
        raise ValidationError("validator_dependency_ast")
    process_target = popen_assignments[0].targets[0]
    assert isinstance(process_target, ast.Name)

    process_arguments = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.arg)
        and node.arg == "process"
    )
    drain_functions = tuple(
        node
        for node in ast.walk(tree)
        if type(node).__name__ == "FunctionDef"
        and node.name == "_drain_git_pipe"
    )
    expected_process_annotation = ast.dump(
        ast.parse("subprocess.Popen[bytes]", mode="eval").body,
        include_attributes=False,
    )
    if (
        len(process_arguments) != 1
        or len(drain_functions) != 1
        or drain_functions[0].decorator_list
        or process_arguments[0]
        not in drain_functions[0].args.kwonlyargs
        or process_arguments[0].annotation is None
        or ast.dump(
            process_arguments[0].annotation,
            include_attributes=False,
        )
        != expected_process_annotation
    ):
        raise ValidationError("validator_dependency_ast")
    drain_function = drain_functions[0]
    drain_function_source = "\n".join(
        source.splitlines()[
            drain_function.lineno - 1 : drain_function.end_lineno
        ]
    )
    drain_function_digest = phase_c1.sha256_bytes(
        drain_function_source.encode("utf-8")
    )
    function_digest_pair = (
        git_function_digest,
        drain_function_digest,
    )
    production_digest_pair = (
        "06BC2A8B843E1266FC15F8265F8432C31DF5B1A3D6D3CED1E6814E9A8CB2212C",
        "E72C768B2FF2A64CF701582082F24B3C31B93F1CF205CDDB9061F6D81DA438AA",
    )
    synthetic_digest_pair = (
        "9437743ECD3D1387A92AB494515896FAEDBAD11D41B9B0A00058F5AAE5A895D3",
        "3B9D2B3C00321F990A2F28AEDD5D836EA1B934145A37D44E5C6D879BB3FE86A4",
    )
    if function_digest_pair == synthetic_digest_pair:
        definition_inventory = tuple(
            (type(node).__name__, node.name)
            for node in tree.body
            if isinstance(
                node,
                (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef),
            )
        )
        if definition_inventory != (
            ("FunctionDef", "_drain_git_pipe"),
            ("FunctionDef", "_git"),
            ("FunctionDef", "main"),
        ):
            raise ValidationError("validator_dependency_ast")
    elif function_digest_pair != production_digest_pair:
        raise ValidationError("validator_dependency_ast")

    arguments_assignments = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "arguments"
            for target in node.targets
        )
    )
    main_functions = tuple(
        node
        for node in ast.walk(tree)
        if type(node).__name__ == "FunctionDef"
        and node.name == "main"
    )
    expected_arguments_assignment = ast.dump(
        ast.parse(
            "arguments = sys.argv[1:] if argv is None else argv"
        ).body[0],
        include_attributes=False,
    )
    if (
        len(arguments_assignments) != 1
        or len(main_functions) != 1
        or id(arguments_assignments[0])
        not in {id(node) for node in ast.walk(main_functions[0])}
        or ast.dump(
            arguments_assignments[0],
            include_attributes=False,
        )
        != expected_arguments_assignment
    ):
        raise ValidationError("validator_dependency_ast")
    arguments_target = arguments_assignments[0].targets[0]
    assert isinstance(arguments_target, ast.Name)

    thread_assignment_sources = (
        (
            "stdout_thread",
            (
                "stdout_thread = threading.Thread("
                "target=_drain_git_pipe, "
                "kwargs={"
                "'stream': process.stdout, "
                "'maximum_bytes': maximum_output_bytes, "
                "'chunks': stdout_chunks, "
                "'overflow': overflow, "
                "'errors': drain_errors, "
                "'process': process}, "
                "daemon=True)"
            ),
        ),
        (
            "stderr_thread",
            (
                "stderr_thread = threading.Thread("
                "target=_drain_git_pipe, "
                "kwargs={"
                "'stream': process.stderr, "
                "'maximum_bytes': maximum_output_bytes, "
                "'chunks': stderr_chunks, "
                "'overflow': overflow, "
                "'errors': drain_errors, "
                "'process': process}, "
                "daemon=True)"
            ),
        ),
    )
    thread_assignment_nodes: dict[str, ast.Name] = {}
    expected_thread_call_shapes: list[str] = []
    for thread_name, assignment_source in thread_assignment_sources:
        expected_assignment = ast.parse(assignment_source).body[0]
        assert isinstance(expected_assignment, ast.Assign)
        expected_thread_call_shapes.append(
            ast.dump(
                expected_assignment.value,
                include_attributes=False,
            )
        )
        assignments = tuple(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == thread_name
                for target in node.targets
            )
        )
        if (
            len(assignments) != 1
            or id(assignments[0]) not in git_function_node_ids
            or ast.dump(assignments[0], include_attributes=False)
            != ast.dump(expected_assignment, include_attributes=False)
        ):
            raise ValidationError("validator_dependency_ast")
        target = assignments[0].targets[0]
        assert isinstance(target, ast.Name)
        thread_assignment_nodes[thread_name] = target
    thread_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "threading"
        and node.func.attr == "Thread"
    )
    if (
        len(thread_calls) != 2
        or tuple(
            sorted(
                (
                    ast.dump(node, include_attributes=False)
                    for node in thread_calls
                ),
                key=repr,
            )
        )
        != tuple(sorted(expected_thread_call_shapes, key=repr))
    ):
        raise ValidationError("validator_dependency_ast")

    allowed_process_name_nodes = {
        id(node)
        for function in (drain_function, git_function)
        for node in ast.walk(function)
        if isinstance(node, ast.Name) and node.id == "process"
    }
    allowed_thread_name_nodes = {
        thread_name: {
            id(node)
            for node in ast.walk(git_function)
            if isinstance(node, ast.Name)
            and node.id == thread_name
        }
        for thread_name in ("stderr_thread", "stdout_thread")
    }

    protected_binding_names = imported_binding_names | {
        "_drain_git_pipe",
        "_git",
        "arguments",
        "command",
        "process",
        "stderr_thread",
        "stdout_thread",
    }
    allowed_binding_node_ids = {
        "_drain_git_pipe": {id(drain_function)},
        "_git": {id(git_function)},
        "arguments": {
            id(git_function.args.vararg),
            id(arguments_target),
        },
        "command": {id(command_target)},
        "process": {
            id(process_arguments[0]),
            id(process_target),
        },
        "stderr_thread": {
            id(thread_assignment_nodes["stderr_thread"])
        },
        "stdout_thread": {
            id(thread_assignment_nodes["stdout_thread"])
        },
    }
    observed_bindings: list[tuple[str, object]] = []
    for node in ast.walk(tree):
        node_type = type(node).__name__
        if (
            isinstance(node, ast.Name)
            and type(node.ctx).__name__ in {"Store", "Del"}
        ):
            observed_bindings.append((node.id, node))
        elif isinstance(node, ast.arg):
            observed_bindings.append((node.arg, node))
        elif node_type in {
            "AsyncFunctionDef",
            "ClassDef",
            "FunctionDef",
        }:
            observed_bindings.append((node.name, node))
        elif (
            node_type == "ExceptHandler"
            and node.name is not None
        ):
            observed_bindings.append((node.name, node))
        elif node_type in {"MatchAs", "MatchStar"}:
            if node.name is not None:
                observed_bindings.append((node.name, node))
        elif (
            node_type == "MatchMapping"
            and node.rest is not None
        ):
            observed_bindings.append((node.rest, node))
        elif node_type in {"Global", "Nonlocal"}:
            observed_bindings.extend(
                (name, node) for name in node.names
            )
    for binding_name, binding_node in observed_bindings:
        if (
            binding_name in protected_binding_names
            and id(binding_node)
            not in allowed_binding_node_ids.get(binding_name, set())
        ):
            raise ValidationError("validator_dependency_ast")

    allowed_popen_nodes = {id(popen_calls[0].func)}
    for argument in ast.walk(tree):
        if (
            isinstance(argument, ast.arg)
            and isinstance(argument.annotation, ast.Subscript)
            and isinstance(argument.annotation.value, ast.Attribute)
            and isinstance(argument.annotation.value.value, ast.Name)
            and argument.annotation.value.value.id == "subprocess"
            and argument.annotation.value.attr == "Popen"
            and isinstance(argument.annotation.slice, ast.Name)
            and argument.annotation.slice.id == "bytes"
        ):
            allowed_popen_nodes.add(id(argument.annotation.value))

    allowed_git_call_sources = (
        (
            "_git(repository_root, 'rev-parse', '--verify', "
            "'HEAD^{commit}')"
        ),
        (
            "_git(repository_root, 'rev-parse', '--verify', "
            "f'{commit}^{{commit}}')"
        ),
        (
            "_git(repository_root, 'ls-tree', '-z', commit, '--', "
            "_literal_pathspec(relative_path))"
        ),
        (
            "_git(repository_root, 'ls-files', '--stage', '-z', "
            "'--', _literal_pathspec(relative_path))"
        ),
        (
            "_git(repository_root, 'cat-file', '-s', object_id, "
            "maximum_output_bytes=128)"
        ),
        (
            "_git(repository_root, 'cat-file', 'blob', object_id, "
            "maximum_output_bytes=maximum_bytes)"
        ),
        (
            "_git(repository_root, 'log', '--format=%H', "
            "'--diff-filter=A', '--no-renames', head, '--', "
            "_literal_pathspec(relative_path))"
        ),
        (
            "_git(repository_root, 'diff-tree', '--no-commit-id', "
            "'--name-status', '-r', '-z', '--no-renames', "
            "pair_commit, '--')"
        ),
        (
            "_git(repository_root, 'merge-base', '--is-ancestor', "
            "ancestor, descendant, expected_codes=(0, 1))"
        ),
        "_git(requested, 'rev-parse', '--show-toplevel')",
        (
            "_git(repository, 'rev-list', '--parents', '-n', '1', "
            "pair_commit)"
        ),
    )
    allowed_git_call_shapes = tuple(
        ast.dump(
            ast.parse(source, mode="eval").body,
            include_attributes=False,
        )
        for source in allowed_git_call_sources
    )
    git_calls = tuple(
        sorted(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_git"
            ),
            key=lambda node: (node.lineno, node.col_offset),
        )
    )
    if (
        len(git_calls) != len(allowed_git_call_shapes)
        or tuple(
            ast.dump(node, include_attributes=False)
            for node in git_calls
        )
        != allowed_git_call_shapes
    ):
        raise ValidationError("validator_dependency_ast")
    allowed_git_name_nodes = {
        id(node.func) for node in git_calls
    }

    forbidden_reflection_attributes = frozenset(
        {
            "__builtins__",
            "__class__",
            "__closure__",
            "__code__",
            "__defaults__",
            "__dict__",
            "__func__",
            "__getattribute__",
            "__globals__",
            "__kwdefaults__",
            "__loader__",
            "__mro__",
            "__origin__",
            "__self__",
            "__spec__",
            "__subclasses__",
            "__traceback__",
            "__wrapped__",
            "f_builtins",
            "f_globals",
            "f_locals",
            "tb_frame",
        }
    )
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and node.id in forbidden_name_ids
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id in imported_binding_names
            and type(node.ctx).__name__ in {"Store", "Del"}
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id in module_alias_names
            and id(node) not in allowed_module_name_load_nodes
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id == "process"
            and id(node) not in allowed_process_name_nodes
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id in allowed_thread_name_nodes
            and id(node) not in allowed_thread_name_nodes[node.id]
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id == "command"
            and id(node) not in allowed_command_name_nodes
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id == "_git"
            and id(node) not in allowed_git_name_nodes
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id == "kernel32"
            and id(node) not in allowed_kernel32_name_nodes
        ):
            raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Name)
            and node.id == getattr_name
            and id(node) not in allowed_getattr_name_nodes
        ):
            raise ValidationError("validator_dependency_ast")
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in dynamic_attribute_names
                and not (
                    node.func.attr == compile_builtin_name
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "re"
                )
            ):
                raise ValidationError("validator_dependency_ast")
        if isinstance(node, ast.Attribute):
            if node.attr in forbidden_reflection_attributes:
                raise ValidationError("validator_dependency_ast")
            if (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "os"
                and node.value.attr == "path"
                and node.attr not in os_path_attribute_inventory
            ):
                raise ValidationError("validator_dependency_ast")
            if isinstance(node.value, ast.Name):
                for module_name, allowed_attributes in (
                    module_attribute_inventories
                ):
                    if (
                        node.value.id == module_name
                        and node.attr not in allowed_attributes
                        and id(node) not in allowed_stdout_root_attribute_nodes
                    ):
                        raise ValidationError(
                            "validator_dependency_ast"
                        )
                if (
                    node.value.id == "os"
                    and node.attr == "path"
                    and id(node) not in allowed_os_path_nodes
                ):
                    raise ValidationError("validator_dependency_ast")
                if (
                    node.value.id == "ctypes"
                    and node.attr == "WinDLL"
                    and id(node) not in allowed_windll_nodes
                ):
                    raise ValidationError("validator_dependency_ast")
                if (
                    node.value.id == "subprocess"
                    and node.attr == "Popen"
                    and id(node) not in allowed_popen_nodes
                ):
                    raise ValidationError("validator_dependency_ast")
                if (
                    node.value.id == "kernel32"
                    and node.attr not in kernel32_attribute_inventory
                ):
                    raise ValidationError("validator_dependency_ast")
        if (
            isinstance(node, ast.Constant)
            and type(node.value) is str
            and project_module_prefix in node.value
        ):
            raise ValidationError("validator_dependency_ast")


def validate_phase_c1_inputs() -> dict[str, object]:
    protocol_bytes = _read_exact_tracked_file(PROTOCOL_PATH)
    search_ledger_bytes = _read_exact_tracked_file(SEARCH_LEDGER_PATH)
    source_ledger_bytes = _read_exact_tracked_file(SOURCE_LEDGER_PATH)
    review_receipt_bytes = _read_exact_tracked_file(SOURCE_REVIEW_PATH)
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
    except phase_c1.PhaseC1ContractError as exc:
        raise _contract_error(exc) from exc
    if (
        protocol.checkpoint_id != CHECKPOINT_ID
        or protocol.protocol_id != PROTOCOL_ID
        or protocol.target_signals != TARGET_SIGNALS
        or protocol.reason_code_order != REASON_CODE_ORDER
    ):
        raise ValidationError("protocol_contract")
    if not _review_is_admitted(review_receipt):
        raise ValidationError("source_review_not_admitted")
    input_sha256s = {
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
    }
    return {
        "protocol_bytes": protocol_bytes,
        "search_ledger_bytes": search_ledger_bytes,
        "source_ledger_bytes": source_ledger_bytes,
        "review_receipt_bytes": review_receipt_bytes,
        "protocol": protocol,
        "search_ledger": search_ledger,
        "source_ledger": source_ledger,
        "review_receipt": review_receipt,
        "input_sha256s": input_sha256s,
    }


def validate_pair_bytes(
    result_bytes: bytes,
    report_bytes: bytes,
) -> dict[str, object]:
    if type(result_bytes) is not bytes:
        raise ValidationError("result_encoding")
    if len(result_bytes) > MAX_AGGREGATE_RESULT_BYTES:
        raise ValidationError("result_size")
    result = _canonical_input_object(result_bytes, source="result")
    if phase_c1.canonical_json_bytes(result) != result_bytes:
        raise ValidationError("result_canonical")
    validated = validate_phase_c1_result_payload(result)
    if type(report_bytes) is not bytes or len(report_bytes) > MAX_PAIR_FILE_BYTES:
        raise ValidationError("report_encoding")
    try:
        report_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise ValidationError("report_encoding") from exc
    if (
        b"\r" in report_bytes
        or not report_bytes.endswith(b"\n")
        or report_bytes.endswith(b"\n\n")
    ):
        raise ValidationError("report_encoding")
    expected_report = render_expected_report_independently(validated)
    if report_bytes != expected_report:
        raise ValidationError("report_determinism")
    result_hash_marker = (
        f"- result.json SHA-256: {phase_c1.sha256_bytes(result_bytes)}"
    ).encode("ascii")
    if report_bytes.splitlines().count(result_hash_marker) != 1:
        raise ValidationError("report_result_hash_binding")
    return validated


class _WindowsFileInformation(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


def _windows_handle_identity(handle: int) -> tuple[int, int, int, int, int]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_WindowsFileInformation),
    ]
    get_information.restype = wintypes.BOOL
    information = _WindowsFileInformation()
    if not get_information(handle, ctypes.byref(information)):
        raise ValidationError("root_anchor")
    file_index = (
        information.nFileIndexHigh << 32
    ) | information.nFileIndexLow
    file_size = (
        information.nFileSizeHigh << 32
    ) | information.nFileSizeLow
    last_write = (
        information.ftLastWriteTime.dwHighDateTime << 32
    ) | information.ftLastWriteTime.dwLowDateTime
    return (
        information.dwVolumeSerialNumber,
        file_index,
        information.dwFileAttributes,
        file_size,
        last_write,
    )


def _open_windows_directory_handle(
    target: Path,
    expected: os.stat_result,
) -> tuple[int, tuple[int, int, int, int, int]]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        os.fspath(target),
        0x80000000,
        0x00000001 | 0x00000002,
        None,
        3,
        0x02000000 | 0x00200000,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle is None or handle == invalid_handle:
        raise ValidationError("root_anchor")
    try:
        identity = _windows_handle_identity(handle)
        if (
            identity[2] & REPARSE_POINT
            or not identity[2] & 0x00000010
            or identity[:2] != (expected.st_dev, expected.st_ino)
        ):
            raise ValidationError("root_anchor")
    except BaseException:
        kernel32.CloseHandle(handle)
        raise
    return handle, identity


def _close_windows_handle(handle: int) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    if not close_handle(handle):
        raise ValidationError("root_anchor")


class _AnchoredDirectory:
    def __init__(
        self,
        target: Path,
        *,
        allowed_children: frozenset[str] = PAIR_CHILDREN,
    ) -> None:
        if (
            type(allowed_children) is not frozenset
            or not allowed_children
            or any(
                type(name) is not str
                or not name
                or "/" in name
                or "\\" in name
                or name in {".", ".."}
                for name in allowed_children
            )
        ):
            raise ValidationError("root_children")
        self.target = target
        self.allowed_children = allowed_children
        self.before: os.stat_result | None = None
        self.descriptor: int | None = None
        self.windows_handle: int | None = None
        self.anchor_identity: object | None = None

    def __enter__(self) -> _AnchoredDirectory:
        before_chain = _directory_chain(self.target)
        before = before_chain[-1]
        if not stat.S_ISDIR(before.st_mode):
            raise ValidationError("root_directory_type")
        self.before = before
        if os.name == "nt":
            handle, identity = _open_windows_directory_handle(
                self.target,
                before,
            )
            self.windows_handle = handle
            self.anchor_identity = identity
            return self
        directory_flag = _O_DIRECTORY
        no_follow_flag = _O_NOFOLLOW
        if directory_flag is None or no_follow_flag is None:
            raise ValidationError("root_anchor")
        try:
            descriptor = os.open(
                self.target,
                os.O_RDONLY | directory_flag | no_follow_flag,
            )
        except OSError as exc:
            raise ValidationError("root_anchor") from exc
        try:
            anchored = os.fstat(descriptor)
            if (
                _is_reparse_or_link(anchored)
                or not stat.S_ISDIR(anchored.st_mode)
                or _metadata_identity(anchored)
                != _metadata_identity(before)
            ):
                raise ValidationError("root_anchor")
        except BaseException:
            os.close(descriptor)
            raise
        self.descriptor = descriptor
        self.anchor_identity = _metadata_identity(anchored)
        return self

    def __exit__(self, *unused: object) -> None:
        error: ValidationError | None = None
        if self.descriptor is not None:
            try:
                os.close(self.descriptor)
            except OSError as exc:
                error = ValidationError("root_anchor")
                error.__cause__ = exc
            self.descriptor = None
        if self.windows_handle is not None:
            try:
                _close_windows_handle(self.windows_handle)
            except ValidationError as exc:
                error = exc
            self.windows_handle = None
        if error is not None and unused and unused[0] is None:
            raise error

    def bounded_children(
        self,
        maximum_children: int,
    ) -> tuple[str, ...]:
        if maximum_children < 1:
            raise ValidationError("root_children")
        locator: object
        if os.name == "nt":
            locator = self.target
        else:
            if self.descriptor is None:
                raise ValidationError("root_anchor")
            locator = self.descriptor
        children: list[str] = []
        try:
            with os.scandir(locator) as entries:
                for entry in entries:
                    if type(entry.name) is not str:
                        raise ValidationError("root_children")
                    children.append(entry.name)
                    if len(children) == maximum_children:
                        break
        except ValidationError:
            raise
        except OSError as exc:
            raise ValidationError("root_children") from exc
        return tuple(children)

    def child_metadata(self, name: str) -> os.stat_result:
        if type(name) is not str or name not in self.allowed_children:
            raise ValidationError("root_children")
        if os.name == "nt":
            return _safe_lstat(
                self.target / name,
                missing_code="root_child_missing",
            )
        if self.descriptor is None:
            raise ValidationError("root_anchor")
        try:
            metadata = os.stat(
                name,
                dir_fd=self.descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError as exc:
            raise ValidationError("root_child_missing") from exc
        except OSError as exc:
            raise ValidationError("path_metadata") from exc
        if _is_reparse_or_link(metadata):
            raise ValidationError("path_reparse_or_link")
        return metadata

    def read_child(
        self,
        name: str,
        expected: os.stat_result,
        *,
        maximum_bytes: int,
    ) -> bytes:
        if os.name == "nt":
            return _read_stable_file(
                self.target / name,
                expected,
                maximum_bytes=maximum_bytes,
            )
        if self.descriptor is None:
            raise ValidationError("root_anchor")
        no_follow_flag = _O_NOFOLLOW
        if no_follow_flag is None:
            raise ValidationError("root_anchor")
        try:
            child_descriptor = os.open(
                name,
                os.O_RDONLY | no_follow_flag,
                dir_fd=self.descriptor,
            )
        except OSError as exc:
            raise ValidationError("file_changed_during_read") from exc
        try:
            before = os.fstat(child_descriptor)
            if (
                _is_reparse_or_link(before)
                or not stat.S_ISREG(before.st_mode)
                or _metadata_identity(before)
                != _metadata_identity(expected)
                or before.st_size > maximum_bytes
            ):
                raise ValidationError("file_changed_during_read")
            chunks: list[bytes] = []
            remaining = maximum_bytes + 1
            while remaining > 0:
                chunk = os.read(
                    child_descriptor,
                    min(64 * 1024, remaining),
                )
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            payload = b"".join(chunks)
            after = os.fstat(child_descriptor)
        except ValidationError:
            raise
        except OSError as exc:
            raise ValidationError("file_changed_during_read") from exc
        finally:
            os.close(child_descriptor)
        if (
            len(payload) > maximum_bytes
            or _is_reparse_or_link(after)
            or not stat.S_ISREG(after.st_mode)
            or _metadata_identity(after) != _metadata_identity(before)
        ):
            raise ValidationError("file_changed_during_read")
        return payload

    def validate(self) -> None:
        if self.before is None or self.anchor_identity is None:
            raise ValidationError("root_anchor")
        if os.name == "nt":
            if self.windows_handle is None:
                raise ValidationError("root_anchor")
            current_identity: object = _windows_handle_identity(
                self.windows_handle
            )
        else:
            if self.descriptor is None:
                raise ValidationError("root_anchor")
            current = os.fstat(self.descriptor)
            current_identity = _metadata_identity(current)
        if current_identity != self.anchor_identity:
            raise ValidationError("root_changed_during_read")
        live = _safe_lstat(self.target, missing_code="root_missing")
        if _metadata_identity(live) != _metadata_identity(self.before):
            raise ValidationError("root_changed_during_read")


def read_allowlisted_phase_c1_pair(
    root: os.PathLike[str] | str,
) -> tuple[bytes, bytes]:
    raw = os.fspath(root)
    if type(raw) is not str:
        raise ValidationError("root_not_allowlisted")
    target = _lexical_absolute(raw)
    candidate = _lexical_absolute(CANDIDATE_ROOT)
    canonical = _lexical_absolute(CANONICAL_ROOT)
    target_key = os.path.normcase(os.fspath(target))
    if target_key not in {
        os.path.normcase(os.fspath(candidate)),
        os.path.normcase(os.fspath(canonical)),
    }:
        raise ValidationError("root_not_allowlisted")
    with _AnchoredDirectory(target) as anchor:
        children = anchor.bounded_children(3)
        if len(children) != 2 or frozenset(children) != PAIR_CHILDREN:
            raise ValidationError("root_children")
        metadata: dict[str, os.stat_result] = {}
        for name in ("result.json", "report.md"):
            child_metadata = anchor.child_metadata(name)
            if (
                not stat.S_ISREG(child_metadata.st_mode)
                or child_metadata.st_size > MAX_PAIR_FILE_BYTES
            ):
                raise ValidationError("root_file_type_or_size")
            metadata[name] = child_metadata
        result_bytes = anchor.read_child(
            "result.json",
            metadata["result.json"],
            maximum_bytes=MAX_PAIR_FILE_BYTES,
        )
        report_bytes = anchor.read_child(
            "report.md",
            metadata["report.md"],
            maximum_bytes=MAX_PAIR_FILE_BYTES,
        )
        anchor.validate()
        return result_bytes, report_bytes


def _git_environment() -> dict[str, str]:
    blocked_exact = {
        "SSH_ASKPASS",
        "SSH_ASKPASS_REQUIRE",
        "GIT_SSH",
        "GIT_SSH_COMMAND",
    }
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
        and key.upper() not in blocked_exact
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    )
    return environment


def _drain_git_pipe(
    stream: Any,
    *,
    maximum_bytes: int,
    chunks: list[bytes],
    overflow: threading.Event,
    errors: list[BaseException],
    process: subprocess.Popen[bytes],
) -> None:
    total = 0
    try:
        while True:
            chunk = stream.read(64 * 1024)
            if not chunk:
                break
            if type(chunk) is not bytes:
                raise OSError("non-bytes Git pipe")
            retained = max(0, maximum_bytes + 1 - total)
            if retained:
                kept = chunk[:retained]
                chunks.append(kept)
                total += len(kept)
            if len(chunk) > retained or total > maximum_bytes:
                overflow.set()
                try:
                    process.kill()
                except OSError:
                    pass
    except BaseException as exc:
        errors.append(exc)
        overflow.set()
        try:
            process.kill()
        except OSError:
            pass


def _git(
    repository_root: Path,
    *arguments: str,
    expected_codes: tuple[int, ...] = (0,),
    maximum_output_bytes: int = 8 * 1024 * 1024,
) -> tuple[int, bytes]:
    if any(type(argument) is not str for argument in arguments):
        raise ValidationError("git_arguments")
    command = [
        "git",
        "--no-replace-objects",
        "--no-lazy-fetch",
        *arguments,
    ]
    if (
        type(maximum_output_bytes) is not int
        or maximum_output_bytes < 0
    ):
        raise ValidationError("git_arguments")
    try:
        process = subprocess.Popen(
            command,
            cwd=repository_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            close_fds=True,
            env=_git_environment(),
        )
    except OSError as exc:
        raise ValidationError("git_execution") from exc
    if process.stdout is None or process.stderr is None:
        try:
            process.kill()
        except OSError:
            pass
        raise ValidationError("git_execution")
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    drain_errors: list[BaseException] = []
    overflow = threading.Event()
    started_threads: list[threading.Thread] = []
    try:
        stdout_thread = threading.Thread(
            target=_drain_git_pipe,
            kwargs={
                "stream": process.stdout,
                "maximum_bytes": maximum_output_bytes,
                "chunks": stdout_chunks,
                "overflow": overflow,
                "errors": drain_errors,
                "process": process,
            },
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_drain_git_pipe,
            kwargs={
                "stream": process.stderr,
                "maximum_bytes": maximum_output_bytes,
                "chunks": stderr_chunks,
                "overflow": overflow,
                "errors": drain_errors,
                "process": process,
            },
            daemon=True,
        )
        stdout_thread.start()
        started_threads.append(stdout_thread)
        stderr_thread.start()
        started_threads.append(stderr_thread)
    except Exception as exc:
        try:
            process.kill()
        except OSError:
            pass
        try:
            process.wait(timeout=2)
        except (OSError, subprocess.SubprocessError):
            pass
        for stream in (process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
        for started_thread in started_threads:
            try:
                started_thread.join(timeout=2)
            except RuntimeError:
                pass
        raise ValidationError("git_execution") from exc
    timed_out = False
    try:
        returncode = process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            process.kill()
        except OSError:
            pass
        try:
            returncode = process.wait(timeout=2)
        except (OSError, subprocess.SubprocessError):
            returncode = -1
    except (OSError, subprocess.SubprocessError):
        timed_out = True
        try:
            process.kill()
        except OSError:
            pass
        try:
            returncode = process.wait(timeout=2)
        except (OSError, subprocess.SubprocessError):
            returncode = -1
    stdout_thread.join(timeout=2)
    stderr_thread.join(timeout=2)
    if stdout_thread.is_alive() or stderr_thread.is_alive():
        try:
            process.kill()
        except OSError:
            pass
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
    try:
        process.stdout.close()
        process.stderr.close()
    except OSError:
        timed_out = True
    if (
        timed_out
        or stdout_thread.is_alive()
        or stderr_thread.is_alive()
        or drain_errors
    ):
        raise ValidationError("git_execution")
    stdout = b"".join(stdout_chunks)
    stderr = b"".join(stderr_chunks)
    if (
        overflow.is_set()
        or returncode not in expected_codes
        or len(stdout) > maximum_output_bytes
        or len(stderr) > maximum_output_bytes
    ):
        raise ValidationError("git_command")
    return returncode, stdout


def _one_ascii_line(payload: bytes, *, code: str) -> str:
    try:
        text = payload.decode("ascii")
    except UnicodeError as exc:
        raise ValidationError(code) from exc
    if "\r" in text or not text.endswith("\n"):
        raise ValidationError(code)
    lines = text.splitlines()
    if len(lines) != 1:
        raise ValidationError(code)
    return lines[0]


def _head_commit(repository_root: Path) -> str:
    _returncode, payload = _git(
        repository_root,
        "rev-parse",
        "--verify",
        "HEAD^{commit}",
    )
    value = _one_ascii_line(payload, code="git_head")
    if _LOWER_GIT_ID_RE.fullmatch(value) is None:
        raise ValidationError("git_head")
    return value


def _verify_commit(repository_root: Path, commit: str) -> None:
    if _LOWER_GIT_ID_RE.fullmatch(commit) is None:
        raise ValidationError("implementation_identity")
    _returncode, payload = _git(
        repository_root,
        "rev-parse",
        "--verify",
        f"{commit}^{{commit}}",
    )
    if _one_ascii_line(payload, code="git_commit") != commit:
        raise ValidationError("git_commit")


def _literal_pathspec(relative_path: str) -> str:
    if (
        not relative_path
        or relative_path.startswith(("/", "\\"))
        or "\\" in relative_path
        or _raw_path_has_alias(relative_path)
    ):
        raise ValidationError("git_path")
    return f":(literal){relative_path}"


def _tree_entry(
    repository_root: Path,
    commit: str,
    relative_path: str,
    *,
    required: bool = True,
) -> tuple[str, str] | None:
    if _LOWER_GIT_ID_RE.fullmatch(commit) is None:
        raise ValidationError("git_commit")
    _returncode, payload = _git(
        repository_root,
        "ls-tree",
        "-z",
        commit,
        "--",
        _literal_pathspec(relative_path),
    )
    if payload == b"" and not required:
        return None
    if not payload.endswith(b"\0") or payload.count(b"\0") != 1:
        raise ValidationError("git_tree")
    record = payload[:-1]
    try:
        header, path_bytes = record.split(b"\t", 1)
        mode_bytes, object_type, object_id_bytes = header.split(b" ", 2)
        path = path_bytes.decode("utf-8")
        mode = mode_bytes.decode("ascii")
        object_id = object_id_bytes.decode("ascii")
    except (ValueError, UnicodeError) as exc:
        raise ValidationError("git_tree") from exc
    if (
        path != relative_path
        or object_type != b"blob"
        or mode not in {"100644", "100755"}
        or _LOWER_GIT_ID_RE.fullmatch(object_id) is None
    ):
        raise ValidationError("git_tree")
    return mode, object_id


def _index_entry(
    repository_root: Path,
    relative_path: str,
) -> tuple[str, str] | None:
    _returncode, payload = _git(
        repository_root,
        "ls-files",
        "--stage",
        "-z",
        "--",
        _literal_pathspec(relative_path),
    )
    if payload == b"":
        return None
    if not payload.endswith(b"\0") or payload.count(b"\0") != 1:
        raise ValidationError("git_index")
    try:
        header, path_bytes = payload[:-1].split(b"\t", 1)
        mode_bytes, object_id_bytes, stage_bytes = header.split(b" ", 2)
        mode = mode_bytes.decode("ascii")
        object_id = object_id_bytes.decode("ascii")
        path = path_bytes.decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise ValidationError("git_index") from exc
    if (
        path != relative_path
        or stage_bytes != b"0"
        or mode not in {"100644", "100755"}
        or _LOWER_GIT_ID_RE.fullmatch(object_id) is None
    ):
        raise ValidationError("git_index")
    return mode, object_id


def _blob_bytes(
    repository_root: Path,
    object_id: str,
    *,
    maximum_bytes: int,
) -> bytes:
    if _LOWER_GIT_ID_RE.fullmatch(object_id) is None:
        raise ValidationError("git_blob")
    _returncode, size_payload = _git(
        repository_root,
        "cat-file",
        "-s",
        object_id,
        maximum_output_bytes=128,
    )
    size_line = _one_ascii_line(size_payload, code="git_blob_size")
    try:
        object_size = int(size_line)
    except ValueError as exc:
        raise ValidationError("git_blob_size") from exc
    if object_size < 0 or object_size > maximum_bytes:
        raise ValidationError("git_blob_size")
    _returncode, payload = _git(
        repository_root,
        "cat-file",
        "blob",
        object_id,
        maximum_output_bytes=maximum_bytes,
    )
    if len(payload) != object_size:
        raise ValidationError("git_blob_size")
    return payload


def _addition_commit(
    repository_root: Path,
    head: str,
    relative_path: str,
) -> str:
    _returncode, payload = _git(
        repository_root,
        "log",
        "--format=%H",
        "--diff-filter=A",
        "--no-renames",
        head,
        "--",
        _literal_pathspec(relative_path),
    )
    try:
        text = payload.decode("ascii")
    except UnicodeError as exc:
        raise ValidationError("pair_introduction") from exc
    if "\r" in text or (text and not text.endswith("\n")):
        raise ValidationError("pair_introduction")
    commits = text.splitlines()
    if (
        len(commits) != 1
        or _LOWER_GIT_ID_RE.fullmatch(commits[0]) is None
    ):
        raise ValidationError("pair_introduction")
    return commits[0]


def _pair_changed_paths(
    repository_root: Path,
    pair_commit: str,
) -> tuple[str, ...]:
    _returncode, payload = _git(
        repository_root,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-r",
        "-z",
        "--no-renames",
        pair_commit,
        "--",
    )
    if not payload.endswith(b"\0"):
        raise ValidationError("pair_changed_paths")
    parts = payload[:-1].split(b"\0")
    pairs: list[tuple[bytes, bytes]] = []
    if all(b"\t" in part for part in parts):
        for part in parts:
            status, path = part.split(b"\t", 1)
            pairs.append((status, path))
    else:
        if len(parts) % 2:
            raise ValidationError("pair_changed_paths")
        pairs = [
            (parts[index], parts[index + 1])
            for index in range(0, len(parts), 2)
        ]
    try:
        decoded = tuple(
            path.decode("utf-8")
            for status, path in pairs
            if status == b"A"
        )
    except UnicodeError as exc:
        raise ValidationError("pair_changed_paths") from exc
    if len(decoded) != len(pairs):
        raise ValidationError("pair_changed_paths")
    return decoded


def _require_ancestor(
    repository_root: Path,
    ancestor: str,
    descendant: str,
) -> None:
    returncode, _payload = _git(
        repository_root,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        expected_codes=(0, 1),
    )
    if returncode != 0:
        raise ValidationError("lineage_ancestry")


def _optional_metadata(path: Path) -> os.stat_result | None:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ValidationError("git_metadata") from exc
    if _is_reparse_or_link(metadata):
        raise ValidationError("git_metadata")
    return metadata


def _git_metadata_line(payload: bytes, *, prefix: str = "") -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise ValidationError("git_metadata") from exc
    if (
        "\0" in text
        or "\r" in text
        or not text.endswith("\n")
        or len(text.splitlines()) != 1
    ):
        raise ValidationError("git_metadata")
    line = text[:-1]
    if prefix:
        if not line.startswith(prefix):
            raise ValidationError("git_metadata")
        line = line[len(prefix) :]
    if not line:
        raise ValidationError("git_metadata")
    return line


def _resolve_git_metadata_path(base: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = base / candidate
    return Path(os.path.abspath(os.path.normpath(candidate)))


def _repository_git_directories(
    repository_root: Path,
) -> tuple[Path, Path]:
    dot_git = repository_root / ".git"
    dot_git_metadata = _optional_metadata(dot_git)
    if dot_git_metadata is None:
        raise ValidationError("git_metadata")
    if stat.S_ISDIR(dot_git_metadata.st_mode):
        git_directory = dot_git
    elif stat.S_ISREG(dot_git_metadata.st_mode):
        gitfile = _read_stable_file(
            dot_git,
            dot_git_metadata,
            maximum_bytes=MAX_GIT_METADATA_BYTES,
        )
        git_directory = _resolve_git_metadata_path(
            dot_git.parent,
            _git_metadata_line(gitfile, prefix="gitdir: "),
        )
    else:
        raise ValidationError("git_metadata")
    git_directory_metadata = _safe_lstat(
        git_directory,
        missing_code="git_metadata",
    )
    if not stat.S_ISDIR(git_directory_metadata.st_mode):
        raise ValidationError("git_metadata")

    common_file = git_directory / "commondir"
    common_file_metadata = _optional_metadata(common_file)
    if common_file_metadata is None:
        common_directory = git_directory
    else:
        if not stat.S_ISREG(common_file_metadata.st_mode):
            raise ValidationError("git_metadata")
        common_bytes = _read_stable_file(
            common_file,
            common_file_metadata,
            maximum_bytes=MAX_GIT_METADATA_BYTES,
        )
        common_directory = _resolve_git_metadata_path(
            git_directory,
            _git_metadata_line(common_bytes),
        )
    common_metadata = _safe_lstat(
        common_directory,
        missing_code="git_metadata",
    )
    if not stat.S_ISDIR(common_metadata.st_mode):
        raise ValidationError("git_metadata")
    return git_directory, common_directory


def _reject_repository_object_alternates(repository_root: Path) -> None:
    git_directory, common_directory = _repository_git_directories(
        repository_root
    )
    directories = (
        git_directory
        if git_directory == common_directory
        else (git_directory, common_directory)
    )
    if isinstance(directories, Path):
        directories = (directories,)
    for directory in directories:
        alternates = directory / "objects" / "info" / "alternates"
        try:
            os.lstat(alternates)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValidationError("git_alternates") from exc
        raise ValidationError("git_alternates")


def _verify_repository_root(repository_root: Path) -> tuple[Path, str]:
    requested = _lexical_absolute(repository_root)
    expected = _lexical_absolute(ROOT)
    if os.path.normcase(os.fspath(requested)) != os.path.normcase(
        os.fspath(expected)
    ):
        raise ValidationError("repository_root")
    metadata = _safe_lstat(requested, missing_code="repository_root")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError("repository_root")
    _reject_repository_object_alternates(requested)
    _returncode, payload = _git(
        requested,
        "rev-parse",
        "--show-toplevel",
    )
    reported = _one_ascii_line(payload, code="repository_root")
    reported_path = Path(os.path.abspath(os.path.normpath(reported)))
    if os.path.normcase(os.fspath(reported_path)) != os.path.normcase(
        os.fspath(requested)
    ):
        raise ValidationError("repository_root")
    return requested, _head_commit(requested)


def _validate_implementation_bindings(
    repository_root: Path,
    *,
    implementation_head: str,
    live_head: str,
    result: Mapping[str, object],
) -> None:
    for field, relative_path in INPUT_RELATIVE_PATHS:
        implementation_entry = _tree_entry(
            repository_root,
            implementation_head,
            relative_path,
        )
        live_entry = _tree_entry(repository_root, live_head, relative_path)
        if implementation_entry != live_entry:
            raise ValidationError("input_descendant_rebinding")
        assert implementation_entry is not None
        blob = _blob_bytes(
            repository_root,
            implementation_entry[1],
            maximum_bytes=MAX_INPUT_FILE_BYTES,
        )
        if result.get(field) != phase_c1.sha256_bytes(blob):
            raise ValidationError("input_implementation_binding")
    implementation_validator = _tree_entry(
        repository_root,
        implementation_head,
        VALIDATOR_RELATIVE_PATH,
    )
    live_validator = _tree_entry(
        repository_root,
        live_head,
        VALIDATOR_RELATIVE_PATH,
    )
    if implementation_validator != live_validator:
        raise ValidationError("validator_descendant_rebinding")
    assert implementation_validator is not None
    if result.get("validator_blob_id") != implementation_validator[1]:
        raise ValidationError("validator_blob_binding")
    committed_validator_bytes = _blob_bytes(
        repository_root,
        implementation_validator[1],
        maximum_bytes=MAX_INPUT_FILE_BYTES,
    )
    current_validator_bytes = _read_exact_tracked_file(VALIDATOR_PATH)
    if current_validator_bytes != committed_validator_bytes:
        raise ValidationError("validator_worktree_binding")
    _validate_validator_dependency_ast(committed_validator_bytes)

    implementation_contracts = _tree_entry(
        repository_root,
        implementation_head,
        CONTRACTS_RELATIVE_PATH,
    )
    live_contracts = _tree_entry(
        repository_root,
        live_head,
        CONTRACTS_RELATIVE_PATH,
    )
    if implementation_contracts != live_contracts:
        raise ValidationError("contracts_descendant_rebinding")
    assert implementation_contracts is not None
    committed_contracts_bytes = _blob_bytes(
        repository_root,
        implementation_contracts[1],
        maximum_bytes=MAX_INPUT_FILE_BYTES,
    )
    current_contracts_bytes = _read_exact_tracked_file(CONTRACTS_PATH)
    if current_contracts_bytes != committed_contracts_bytes:
        raise ValidationError("contracts_worktree_binding")


def _validate_canonical_index_state(
    repository_root: Path,
    *,
    live_head: str,
    require_absent: bool,
) -> None:
    for relative_path in (
        CANONICAL_RESULT_RELATIVE,
        CANONICAL_REPORT_RELATIVE,
    ):
        head_entry = _tree_entry(
            repository_root,
            live_head,
            relative_path,
            required=False,
        )
        index_entry = _index_entry(repository_root, relative_path)
        if require_absent:
            if head_entry is not None or index_entry is not None:
                raise ValidationError("canonical_precommit_index")
        elif head_entry is None or index_entry != head_entry:
            raise ValidationError("canonical_index_drift")


def validate_checkpoint_lineage(repository_root: Path) -> None:
    repository, live_head = _verify_repository_root(repository_root)
    _validate_canonical_index_state(
        repository,
        live_head=live_head,
        require_absent=False,
    )
    result_bytes, report_bytes = read_allowlisted_phase_c1_pair(
        CANONICAL_ROOT
    )
    result = validate_pair_bytes(result_bytes, report_bytes)
    implementation_head = result["implementation_head"]
    if type(implementation_head) is not str:
        raise ValidationError("implementation_identity")
    _verify_commit(repository, implementation_head)
    result_introduction = _addition_commit(
        repository,
        live_head,
        CANONICAL_RESULT_RELATIVE,
    )
    report_introduction = _addition_commit(
        repository,
        live_head,
        CANONICAL_REPORT_RELATIVE,
    )
    if result_introduction != report_introduction:
        raise ValidationError("pair_introduction")
    pair_commit = result_introduction
    _returncode, parent_payload = _git(
        repository,
        "rev-list",
        "--parents",
        "-n",
        "1",
        pair_commit,
    )
    parent_line = _one_ascii_line(parent_payload, code="pair_parent")
    if parent_line.split(" ") != [pair_commit, implementation_head]:
        raise ValidationError("pair_parent")
    changed_paths = _pair_changed_paths(repository, pair_commit)
    if frozenset(changed_paths) != frozenset(
        {CANONICAL_RESULT_RELATIVE, CANONICAL_REPORT_RELATIVE}
    ) or len(changed_paths) != 2:
        raise ValidationError("pair_changed_paths")
    _require_ancestor(repository, implementation_head, live_head)
    _require_ancestor(repository, pair_commit, live_head)

    for relative_path, current_bytes in (
        (CANONICAL_RESULT_RELATIVE, result_bytes),
        (CANONICAL_REPORT_RELATIVE, report_bytes),
    ):
        pair_entry = _tree_entry(repository, pair_commit, relative_path)
        live_entry = _tree_entry(repository, live_head, relative_path)
        if pair_entry != live_entry:
            raise ValidationError("pair_descendant_rebinding")
        assert pair_entry is not None
        pair_bytes = _blob_bytes(
            repository,
            pair_entry[1],
            maximum_bytes=MAX_PAIR_FILE_BYTES,
        )
        if pair_bytes != current_bytes:
            raise ValidationError("pair_worktree_drift")
    _validate_implementation_bindings(
        repository,
        implementation_head=implementation_head,
        live_head=live_head,
        result=result,
    )


def _validate_precommit_lineage(
    result: Mapping[str, object],
) -> None:
    repository, live_head = _verify_repository_root(ROOT)
    implementation_head = result.get("implementation_head")
    if (
        type(implementation_head) is not str
        or live_head != implementation_head
    ):
        raise ValidationError("implementation_head")
    _verify_commit(repository, implementation_head)
    _validate_canonical_index_state(
        repository,
        live_head=live_head,
        require_absent=True,
    )
    _validate_implementation_bindings(
        repository,
        implementation_head=implementation_head,
        live_head=live_head,
        result=result,
    )


def validate_phase_c1_pair(root: Path) -> dict[str, object]:
    result_bytes, report_bytes = read_allowlisted_phase_c1_pair(root)
    result = validate_pair_bytes(result_bytes, report_bytes)
    target = _lexical_absolute(root)
    candidate = _lexical_absolute(CANDIDATE_ROOT)
    canonical = _lexical_absolute(CANONICAL_ROOT)
    if os.path.normcase(os.fspath(target)) == os.path.normcase(
        os.fspath(candidate)
    ):
        _validate_precommit_lineage(result)
        return result
    if os.path.normcase(os.fspath(target)) != os.path.normcase(
        os.fspath(canonical)
    ):
        raise ValidationError("root_not_allowlisted")
    repository, live_head = _verify_repository_root(ROOT)
    result_entry = _tree_entry(
        repository,
        live_head,
        CANONICAL_RESULT_RELATIVE,
        required=False,
    )
    report_entry = _tree_entry(
        repository,
        live_head,
        CANONICAL_REPORT_RELATIVE,
        required=False,
    )
    if result_entry is None and report_entry is None:
        _validate_precommit_lineage(result)
    elif result_entry is None or report_entry is None:
        raise ValidationError("canonical_tracking_state")
    else:
        validate_checkpoint_lineage(repository)
    return result


def _candidate_receipt_paths() -> tuple[Path, Path, Path, Path, Path, Path]:
    root = CANDIDATE_ROOT.parent
    return (
        root / "candidate-receipt.json",
        root / "candidate-validation.json",
        root / "candidate-review.json",
        root / "candidate-receipt.stage",
        root / "candidate-validation.stage",
        root / "candidate-review.stage",
    )


def _canonical_candidate_receipt(payload: bytes) -> dict[str, object]:
    value = phase_c1.load_json_strict(payload, source="candidate_receipt")
    required = frozenset((
        "schema_version", "checkpoint_id", "transaction_id", "status",
        "implementation_head", "validator_blob_id", "protocol_sha256",
        "search_ledger_sha256", "source_evidence_ledger_sha256",
        "source_review_receipt_sha256", "result_sha256", "report_sha256",
    ))
    if not isinstance(value, dict) or set(value) != required or phase_c1.canonical_json_bytes(value) != payload:
        raise ValidationError("candidate_receipt")
    if value.get("schema_version") != "EmotionStatePhaseC1CandidateReceiptV1" or value.get("checkpoint_id") != CHECKPOINT_ID or value.get("status") != "candidate_ready":
        raise ValidationError("candidate_receipt")
    for key, width in (("transaction_id", 32), ("implementation_head", 40), ("validator_blob_id", 40), ("protocol_sha256", 64), ("search_ledger_sha256", 64), ("source_evidence_ledger_sha256", 64), ("source_review_receipt_sha256", 64), ("result_sha256", 64), ("report_sha256", 64)):
        item = value.get(key)
        if type(item) is not str or len(item) != width or _LOWER_HEX_RE.fullmatch(item) is None:
            raise ValidationError("candidate_receipt")
    selfless = dict(value)
    selfless["transaction_id"] = ""
    if value["transaction_id"] != phase_c1.sha256_bytes(phase_c1.canonical_json_bytes(selfless)).lower()[:32]:
        raise ValidationError("candidate_receipt")
    return value


def _candidate_validation_payload(receipt: Mapping[str, object], *, result_bytes: bytes, report_bytes: bytes) -> dict[str, object]:
    authorities = (
        ("protocol_sha256", PROTOCOL_PATH),
        ("search_ledger_sha256", SEARCH_LEDGER_PATH),
        ("source_evidence_ledger_sha256", SOURCE_LEDGER_PATH),
        ("source_review_receipt_sha256", SOURCE_REVIEW_PATH),
    )
    for field, path in authorities:
        if receipt[field] != phase_c1.sha256_bytes(_read_exact_tracked_file(path)).lower():
            raise ValidationError("candidate_binding")
    result = validate_pair_bytes(result_bytes, report_bytes)
    _validate_precommit_lineage(result)
    if result.get("implementation_head") != receipt["implementation_head"] or result.get("validator_blob_id") != receipt["validator_blob_id"]:
        raise ValidationError("candidate_binding")
    if phase_c1.sha256_bytes(result_bytes).lower() != receipt["result_sha256"] or phase_c1.sha256_bytes(report_bytes).lower() != receipt["report_sha256"]:
        raise ValidationError("candidate_binding")
    return {
        "schema_version": "EmotionStatePhaseC1CandidateValidationV1",
        "checkpoint_id": CHECKPOINT_ID,
        "implementation_head": receipt["implementation_head"],
        "candidate_transaction_id": receipt["transaction_id"],
        "candidate_result_sha256": receipt["result_sha256"],
        "candidate_report_sha256": receipt["report_sha256"],
        "protocol_sha256": receipt["protocol_sha256"],
        "search_ledger_sha256": receipt["search_ledger_sha256"],
        "source_evidence_ledger_sha256": receipt["source_evidence_ledger_sha256"],
        "source_review_receipt_sha256": receipt["source_review_receipt_sha256"],
        "validator_blob_id": receipt["validator_blob_id"],
        "verdict": "pass",
        "runtime_approved": False,
    }


def _validate_candidate_review(receipt: Mapping[str, object], validation_bytes: bytes, review_bytes: bytes) -> None:
    review = phase_c1.load_json_strict(review_bytes, source="candidate_review")
    expected = {
        "schema_version": "EmotionStatePhaseC1CandidateReviewV1",
        "checkpoint_id": CHECKPOINT_ID,
        "candidate_transaction_id": receipt["transaction_id"],
        "implementation_head": receipt["implementation_head"],
        "candidate_result_sha256": receipt["result_sha256"],
        "candidate_report_sha256": receipt["report_sha256"],
        "candidate_validation_sha256": phase_c1.sha256_bytes(validation_bytes).lower(),
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
    if not isinstance(review, dict) or phase_c1.canonical_json_bytes(review) != review_bytes or review != expected:
        raise ValidationError("candidate_review")


def validate_phase_c1_candidate_receipts() -> dict[str, object]:
    receipt_path, validation_path, review_path, receipt_stage, validation_stage, review_stage = _candidate_receipt_paths()
    if any(path.exists() or path.is_symlink() for path in (receipt_stage, validation_stage, review_stage)):
        raise ValidationError("candidate_receipt_stage")
    result_bytes, report_bytes = read_allowlisted_phase_c1_pair(CANDIDATE_ROOT)
    receipt = _canonical_candidate_receipt(_read_exact_tracked_file(receipt_path))
    validation = _candidate_validation_payload(receipt, result_bytes=result_bytes, report_bytes=report_bytes)
    validation_bytes = phase_c1.canonical_json_bytes(validation)
    if validation_path.exists() or validation_path.is_symlink():
        if _read_exact_tracked_file(validation_path) != validation_bytes:
            raise ValidationError("candidate_validation")
        if not (review_path.exists() or review_path.is_symlink()):
            raise ValidationError("candidate_review")
    if review_path.exists() or review_path.is_symlink():
        if not (validation_path.exists() or validation_path.is_symlink()):
            raise ValidationError("candidate_review")
        _validate_candidate_review(receipt, validation_bytes, _read_exact_tracked_file(review_path))
    return validation


def parse_cli_args(argv: Sequence[str]) -> str:
    if (
        type(argv) not in (list, tuple)
        or not ((len(argv) == 1 and argv[0] in {"inputs", "projection", "candidate", "canonical", "checkpoint"}) or (len(argv) == 2 and argv[0] == "candidate" and argv[1] == "--json"))
    ):
        raise CliUsageError("cli_arguments")
    return "candidate_json" if len(argv) == 2 else argv[0]


def _run_section(section: str) -> None:
    if section == "inputs":
        validate_phase_c1_inputs()
        return
    if section == "projection":
        inputs = validate_phase_c1_inputs()
        derive_phase_c1_projection_independently(
            protocol=inputs["protocol"],
            search_ledger=inputs["search_ledger"],
            source_ledger=inputs["source_ledger"],
            review_receipt=inputs["review_receipt"],
        )
        return
    if section == "candidate":
        validate_phase_c1_candidate_receipts()
        return
    if section == "candidate_json":
        return
        return
    if section == "canonical":
        validate_phase_c1_pair(CANONICAL_ROOT)
        return
    if section == "checkpoint":
        validate_checkpoint_lineage(ROOT)
        return
    raise ValidationError("section")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        section = parse_cli_args(arguments)
    except CliUsageError as exc:
        print(
            "EMOTION-STATE-004 Phase C1 validation failed:"
            f" {exc}",
            file=sys.stderr,
        )
        return 2
    try:
        if section == "candidate_json":
            payload = validate_phase_c1_candidate_receipts()
            sys.stdout.buffer.write(phase_c1.canonical_json_bytes(payload))
            return 0
        _run_section(section)
    except ValidationError as exc:
        print(
            "EMOTION-STATE-004 Phase C1 validation failed:"
            f" {exc.code}",
            file=sys.stderr,
        )
        return 1
    except (
        OSError,
        phase_c1.PhaseC1ContractError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        print(
            "EMOTION-STATE-004 Phase C1 validation failed:"
            " internal_error",
            file=sys.stderr,
        )
        return 1
    print(f"{section}:pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
