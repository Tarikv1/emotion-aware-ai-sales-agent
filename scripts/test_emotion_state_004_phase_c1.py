from __future__ import annotations

import ast
import copy
import contextlib
import gc
import hashlib
import io
import inspect
import json
import multiprocessing
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Callable, ContextManager, Iterator
import weakref

import scripts.emotion_state_phase_c1_contracts as phase_c1
import scripts.emotion_state_phase_c1_decision as decision
import scripts.run_emotion_state_004_phase_c1 as runner
import scripts.validate_emotion_state_004_phase_c1 as validator


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SIGNALS = (
    "hesitation",
    "frustration",
    "confusion",
    "interest",
    "disengagement",
)

RETIRED_V1_TEST_METHOD_NAMES = (
    "test_reason_contributor_map_is_complete_and_exact",
    "test_per_reason_cap_rejects_repeated_single_item_reason",
    "test_per_reason_caps_preserve_exact_contributor_boundaries",
    "test_shared_unresolved_search_reason_pool_is_not_double_used",
    "test_rejected_card_reason_groups_require_compatible_allocation",
    "test_unresolved_card_reason_families_require_compatible_allocation",
    "test_observable_reliability_reasons_bind_to_card_diagnostics",
    "test_search_reason_reservation_preserves_valid_card_allocation",
    "test_record_only_reasons_reserve_unresolved_search_slots",
    "test_unresolved_card_and_search_reason_composition_is_exact",
    "test_hidden_unresolved_reason_paths_are_exact_and_multiplicative",
    "test_observable_reason_allocation_is_bounded_per_diagnostic",
    "test_observable_reason_allocation_search_is_bounded",
)

EXPECTED_PHASE_C1_RESULT_FIELDS = frozenset(
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

EXPECTED_RELIABILITY_DIAGNOSTIC_FIELDS = frozenset(
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

EXPECTED_PHASE_C1_LIMITATIONS = (
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

EXPECTED_SIGNAL_CONSTRUCTS = (
    MappingProxyType(
        {
            "signal": "hesitation",
            "observer_construct": (
                "observer-perceived hesitation or indecision expressed in the "
                "local conversational unit"
            ),
            "direct_label_requirement": (
                "authoritative source documentation explicitly defines the "
                "annotated construct as hesitation; no post-hoc synonym mapping"
            ),
            "excluded_proxies": (
                "disfluency",
                "low_confidence",
                "pause_or_silence",
                "response_latency",
                "uncertainty",
            ),
        }
    ),
    MappingProxyType(
        {
            "signal": "frustration",
            "observer_construct": (
                "observer-perceived frustration expressed in the local "
                "conversational unit"
            ),
            "direct_label_requirement": (
                "authoritative source documentation explicitly defines the "
                "annotated construct as frustration; no post-hoc synonym mapping"
            ),
            "excluded_proxies": (
                "anger",
                "complaint_topic",
                "dissatisfaction",
                "negative_valence",
                "stress",
            ),
        }
    ),
    MappingProxyType(
        {
            "signal": "confusion",
            "observer_construct": (
                "observer-perceived confusion or lack of comprehension in the "
                "local conversational unit"
            ),
            "direct_label_requirement": (
                "authoritative source documentation explicitly defines the "
                "annotated construct as confusion; no post-hoc synonym mapping"
            ),
            "excluded_proxies": (
                "ambiguity",
                "asr_error",
                "hesitation",
                "question_dialogue_act",
                "uncertainty",
            ),
        }
    ),
    MappingProxyType(
        {
            "signal": "interest",
            "observer_construct": (
                "observer-perceived interest directed toward the current topic "
                "or interaction in the local conversational unit"
            ),
            "direct_label_requirement": (
                "authoritative source documentation explicitly defines the "
                "annotated construct as interest; no post-hoc synonym mapping"
            ),
            "excluded_proxies": (
                "agreement",
                "arousal",
                "engagement",
                "gaze",
                "participation",
                "positive_valence",
                "purchase_intent",
                "response_length",
            ),
        }
    ),
    MappingProxyType(
        {
            "signal": "disengagement",
            "observer_construct": (
                "observer-perceived withdrawal of attention or participation "
                "from the interaction in the local conversational unit"
            ),
            "direct_label_requirement": (
                "authoritative source documentation explicitly defines the "
                "annotated construct as disengagement; no post-hoc synonym mapping"
            ),
            "excluded_proxies": (
                "boredom",
                "call_completion",
                "do_not_call_intent",
                "low_arousal",
                "refusal_intent",
                "silence",
                "stop_intent",
                "turn_ending",
            ),
        }
    ),
)

EXPECTED_REASON_CODE_ORDER = (
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

EXPECTED_ANNOTATION_FALLBACK_PROTOCOL = MappingProxyType(
    {
        "execution_authorized": False,
        "requires_separate_checkpoint": True,
        "material_scope": (
            "appropriately_licensed_public_spontaneous_conversations_only"
        ),
        "minimum_independent_raters_per_segment": 3,
        "labels": ("present", "absent", "uncertain_or_unratable"),
        "signals_independent": True,
        "signal_cooccurrence_allowed": True,
        "bounded_context_frozen_before_annotation": True,
        "annotators_blinded_to_model_outputs": True,
        "annotators_blinded_to_sales_decisions": True,
        "annotators_blinded_to_other_raters": True,
        "training_and_pilot_excluded_from_later_evaluation": True,
        "codebook_revision_phase": "pilot_only",
        "raw_disagreement_preserved": True,
        "majority_vote_as_ground_truth_allowed": False,
        "llm_labels_allowed": False,
        "private_conversations_allowed": False,
        "customer_calls_allowed": False,
        "protected_characteristic_inference_allowed": False,
        "speaker_and_conversation_ids_use": "later_disjoint_grouping_only",
        "sample_size_method": (
            "preregistered_reliability_precision_and_pilot_prevalence"
        ),
    }
)

EXPECTED_DISCOVERY_ENDPOINTS = (
    "https://api.openalex.org/works",
    "https://api.crossref.org/works",
    "https://zenodo.org/api/records",
    "https://huggingface.co/api/datasets",
)

EXPECTED_GITATTRIBUTES_RULES = (
    (
        "/research/experiments/configs/"
        "emotion-state-004-phase-c1-discovery-protocol.json text eol=lf"
    ),
    (
        "/research/experiments/cases/"
        "emotion-state-004-phase-c1-contract-fixtures.json text eol=lf"
    ),
    (
        "/research/sources/emotion_state/"
        "phase_c1_search_ledger.json text eol=lf"
    ),
    (
        "/research/sources/emotion_state/"
        "phase_c1_source_evidence_ledger.json text eol=lf"
    ),
    (
        "/research/sources/emotion_state/"
        "phase_c1_source_review_receipt.json text eol=lf"
    ),
    (
        "/research/experiments/generated/"
        "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission/"
        "result.json text eol=lf"
    ),
    (
        "/research/experiments/generated/"
        "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission/"
        "report.md text eol=lf"
    ),
)

EXPECTED_PHASE_C0_GITATTRIBUTES_RULES = (
    "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/result.json text eol=lf",
    "/research/experiments/generated/EMOTION-STATE-003-phase-c0-synthetic-temporal-mechanics/report.md text eol=lf",
)

SEARCH_LEDGER_PATH = (
    ROOT
    / "research"
    / "sources"
    / "emotion_state"
    / "phase_c1_search_ledger.json"
)

SOURCE_LEDGER_PATH = (
    ROOT
    / "research"
    / "sources"
    / "emotion_state"
    / "phase_c1_source_evidence_ledger.json"
)

REVIEW_PATH = (
    ROOT
    / "research"
    / "sources"
    / "emotion_state"
    / "phase_c1_source_review_receipt.json"
)

EXPECTED_FIXTURE_PAYLOAD = {
    "schema_version": "EmotionStatePhaseC1ContractFixturesV1",
    "valid_source_ids": ["c1-source-0001", "c1-source-0002"],
    "valid_card_ids": [
        "c1-card-confusion-0001",
        "c1-card-hesitation-0001",
    ],
    "signals": list(EXPECTED_SIGNALS),
    "forbidden_payload_keys": [
        "audio",
        "customer_id",
        "feature",
        "model_metric",
        "participant_id",
        "prediction",
        "probability",
        "transcript",
        "utterance",
    ],
}

EXPECTED_EXPERIMENT_NOTE_START = """\
# EMOTION-STATE-004 Phase C1 Operational-Signal Evidence Admission

## Status

Protocol frozen. Task 7 completed the bounded public-metadata discovery run;
Task 8 froze its rowless source-ledger package under an `admitted` review.
That review admits no signal evidence.

## Question

Does direct, temporally local, independently rated observer-label evidence
exist for hesitation, frustration, confusion, interest, or disengagement in
spontaneous conversation?

## Claim Boundary

This checkpoint assesses rowless source and label admissibility only. It does
not assess customer internal emotion, model quality, sales performance,
provider behavior, real calls, runtime behavior, or production readiness.
"""


def _https(value: str) -> str:
    return "https" + "://" + value


@dataclass(frozen=True)
class _ReceiptMutation:
    name: str
    apply: Callable[[dict[str, object]], None]


class _PhaseC1FixtureMixin:
    protocol_path = (
        ROOT
        / "research"
        / "experiments"
        / "configs"
        / "emotion-state-004-phase-c1-discovery-protocol.json"
    )

    def valid_protocol_payload(self) -> dict[str, object]:
        payload = phase_c1.load_json_strict(
            self.protocol_path.read_bytes(),
            source="protocol",
        )
        self.assertIsInstance(payload, dict)
        return payload

    @staticmethod
    def valid_transport_receipt() -> dict[str, object]:
        return {
            "schema_version": "EmotionStatePhaseC1TransportReceiptV1",
            "receipt_id": "c1-transport-0001",
            "purpose": "seed_query",
            "request_key": "c1-query-hesitation-openalex-01",
            "retrieved_at_utc": "2026-07-26T12:00:00Z",
            "requested_url": _https(
                "api.openalex.org/works?search=hesitation"
            ),
            "final_url": _https(
                "api.openalex.org/works?search=hesitation"
            ),
            "outcome": "complete",
            "incomplete_reason": None,
            "http_status_code": 200,
            "redirect_hop_count": 0,
            "redirect_chain": [],
            "response_sha256": "A" * 64,
            "response_byte_count": 512,
            "response_content_type": "application/json",
        }

    def valid_transport_ledger(self) -> dict[str, object]:
        protocol_bytes = self.protocol_path.read_bytes()
        return {
            "schema_version": "EmotionStatePhaseC1TransportReceiptLedgerV1",
            "protocol_sha256": hashlib.sha256(
                protocol_bytes
            ).hexdigest().upper(),
            "receipts": [self.valid_transport_receipt()],
        }

    @staticmethod
    def valid_source_payload() -> dict[str, object]:
        return {
            "source_id": "c1-source-0001",
            "title": "Synthetic public conversation source",
            "source_kind": "public_dataset",
            "phase_c1_roles": [
                "existing_annotation_evidence",
                "fallback_material_candidate",
            ],
            "version": "v1",
            "documents": [
                {
                    "document_id": "c1-document-0001",
                    "role": "annotation_manual",
                    "authoritative_url": "https://api.openalex.org/works",
                    "publisher_domain": "openalex.org",
                    "retrieved_at_utc": "2026-07-26T12:00:00Z",
                    "cached_sha256": "B" * 64,
                    "content_type": "application/pdf",
                    "byte_count": 512,
                    "authoritative": True,
                    "public_without_login": True,
                    "transport_receipt_sha256": "A" * 64,
                }
            ],
            "access_status": "public_no_login",
            "license_status": "compatible",
            "license_identifier": "CC-BY-4.0",
            "ethical_use_status": "compatible",
            "conversation_status": "spontaneous_conversation",
            "domain": "conversational-research",
            "languages": ["en"],
            "population_scope": "Public conversational participants",
            "modalities": ["audio"],
        }

    @staticmethod
    def valid_card_payload() -> dict[str, object]:
        return {
            "card_id": "c1-card-confusion-0001",
            "source_id": "c1-source-0001",
            "signal": "confusion",
            "native_label": "confusion",
            "native_definition_document_id": "c1-document-0001",
            "native_definition_locator": "section-2-page-1",
            "native_definition_excerpt_sha256": "C" * 64,
            "annotation_modality": "audio_only",
            "construct_correspondence": "direct_target_construct",
            "temporal_unit": "bounded_segment",
            "bounded_context_description": (
                "bounded_segment_within_conversation"
            ),
            "observer_method": "independent_human_observer",
            "independent_rater_count": 3,
            "reliability": {
                "metric_id": "krippendorff_alpha",
                "point_micros": 840_000,
                "lower_95_micros": 700_000,
                "upper_95_micros": 900_000,
                "rated_unit_count": 100,
                "published_positive_count": 93,
                "preadjudication": True,
                "verifiable": True,
                "uncertain_or_unratable_rate_micros": 10_000,
                "class_prevalence_micros": 500_000,
                "positive_agreement_micros": 850_000,
                "negative_agreement_micros": 860_000,
                "preadjudication_disagreement_micros": 150_000,
            },
            "claimed_status": "admissible",
            "claimed_reason_codes": [],
            "limitations": ["Synthetic metadata-only limitation"],
        }

    def valid_search_ledger_bytes(self) -> bytes:
        payload = {
            "candidate_order_by_signal": {
                "hesitation": [],
                "frustration": [],
                "confusion": ["c1-source-0001"],
                "interest": [],
                "disengagement": [],
            },
            "fallback_material_candidate_order": [],
            "fail_ready_by_signal": {
                signal: False for signal in EXPECTED_SIGNALS
            },
            "query_records": [
                {
                    "transport_receipt_sha256": "A" * 64,
                    "discovery_records": [],
                }
            ],
            "citation_records": [],
            "citation_transport_receipt_sha256s_by_signal": {
                signal: {"backward": [], "forward": []}
                for signal in EXPECTED_SIGNALS
            },
        }
        return phase_c1.canonical_json_bytes(payload)

    @staticmethod
    def phase_c1_query_grid() -> tuple[
        tuple[str, str, str, str | None, str],
        ...,
    ]:
        channels = ("openalex", "crossref", "zenodo", "huggingface")
        direct_templates = (
            "{signal} annotated spontaneous conversation corpus",
            "{signal} turn-level dialogue annotation dataset",
            "perceived {signal} speech inter-rater agreement corpus",
            "{signal} multimodal interaction segment annotation",
        )
        fallback_templates = (
            "public spontaneous conversation corpus annotation permitted",
            (
                "public spontaneous dialogue dataset license annotation "
                "redistribution"
            ),
        )
        rows: list[tuple[str, str, str, str | None, str]] = []
        for signal in EXPECTED_SIGNALS:
            for channel in channels:
                for rank, template in enumerate(direct_templates, start=1):
                    rows.append(
                        (
                            f"c1-query-{signal}-{channel}-{rank:02d}",
                            "direct_label_source",
                            channel,
                            signal,
                            template.format(signal=signal),
                        )
                    )
        for channel in channels:
            for rank, template in enumerate(fallback_templates, start=1):
                rows.append(
                    (
                        f"c1-query-fallback-material-{channel}-{rank:02d}",
                        "fallback_material",
                        channel,
                        None,
                        template,
                    )
                )
        return tuple(rows)

    @staticmethod
    def fixture_hash(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest().upper()

    def valid_search_ledger_payload(self) -> dict[str, object]:
        query_records = [
            {
                "query_id": query_id,
                "query_kind": query_kind,
                "channel_id": channel_id,
                "signal": signal,
                "query_text": query_text,
                "status": "complete",
                "incomplete_reason": None,
                "result_limit": 25,
                "response_sha256": self.fixture_hash(
                    f"response:{query_id}"
                ),
                "response_byte_count": 512,
                "transport_receipt_sha256": self.fixture_hash(
                    f"transport:{query_id}"
                ),
                "result_count": 0,
                "returned_count": 0,
                "truncated": False,
                "discovery_records": [],
            }
            for (
                query_id,
                query_kind,
                channel_id,
                signal,
                query_text,
            ) in self.phase_c1_query_grid()
        ]
        return {
            "schema_version": "EmotionStatePhaseC1SearchLedgerV1",
            "protocol_sha256": hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            "query_records": query_records,
            "citation_records": [],
            "candidate_order_by_signal": {
                signal: [] for signal in EXPECTED_SIGNALS
            },
            "overflow_count_by_signal": {
                signal: 0 for signal in EXPECTED_SIGNALS
            },
            "fallback_material_candidate_order": [],
            "fallback_material_overflow_count": 0,
            "backward_citation_count_by_signal": {
                signal: 0 for signal in EXPECTED_SIGNALS
            },
            "forward_citation_count_by_signal": {
                signal: 0 for signal in EXPECTED_SIGNALS
            },
            "backward_citation_stop_by_signal": {
                signal: "source_list_exhausted"
                for signal in EXPECTED_SIGNALS
            },
            "forward_citation_stop_by_signal": {
                signal: "source_list_exhausted"
                for signal in EXPECTED_SIGNALS
            },
            "citation_transport_receipt_sha256s_by_signal": {
                signal: {"backward": [], "forward": []}
                for signal in EXPECTED_SIGNALS
            },
            "fail_ready_by_signal": {
                signal: True for signal in EXPECTED_SIGNALS
            },
            "search_complete": True,
        }

    def discovery_record(
        self,
        *,
        query_id: str,
        rank: int,
        record_number: int,
        disposition: str = "retained_candidate",
        source_id: str | None = "c1-source-0001",
        duplicate_of: str | None = None,
        reason_code: str | None = None,
        documentation_hashes: list[str] | None = None,
    ) -> dict[str, object]:
        if documentation_hashes is None:
            documentation_hashes = (
                [self.fixture_hash(f"document:{record_number}")]
                if disposition == "retained_candidate"
                else []
            )
        return {
            "discovery_record_id": f"c1-discovery-{record_number:04d}",
            "query_id": query_id,
            "rank": rank,
            "identity_sha256": self.fixture_hash(
                f"identity:{record_number}"
            ),
            "disposition": disposition,
            "candidate_source_id": source_id,
            "duplicate_of_discovery_record_id": duplicate_of,
            "reason_code": reason_code,
            "documentation_transport_receipt_sha256s": (
                documentation_hashes
            ),
        }

    def retained_citation_candidate(
        self,
        *,
        signal: str,
        source_id: str,
        direction: str = "backward",
        rank: int = 1,
    ) -> dict[str, object]:
        return {
            "citation_record_id": (
                f"c1-citation-{signal}-{direction}-{rank:02d}"
            ),
            "signal": signal,
            "direction": direction,
            "rank": rank,
            "parent_source_id": "c1-source-0001",
            "parent_source_document_sha256": self.fixture_hash(
                f"parent:{signal}:{direction}:{rank}"
            ),
            "transport_receipt_sha256": self.fixture_hash(
                f"citation-transport:{signal}:{direction}:{rank}"
            ),
            "identity_sha256": self.fixture_hash(
                f"citation-identity:{signal}:{direction}:{rank}"
            ),
            "disposition": "retained_candidate",
            "candidate_source_id": source_id,
            "duplicate_of_record_id": None,
            "reason_code": None,
            "documentation_transport_receipt_sha256s": [
                self.fixture_hash(
                    f"citation-document:{signal}:{direction}:{rank}"
                )
            ],
        }

    @staticmethod
    def valid_fallback_material() -> dict[str, object]:
        return {
            "source_id": "c1-source-0001",
            "status": "unresolved",
            "public_spontaneous_material_status": "unresolved",
            "license_status": "unresolved",
            "ethical_use_status": "unresolved",
            "minimum_three_raters_status": "unresolved",
            "material_evidence_document_ids": [],
            "license_evidence_document_ids": [],
            "ethical_use_evidence_document_ids": [],
            "rater_feasibility_evidence_document_ids": [],
        }

    def valid_source_evidence_ledger(
        self,
        search_ledger_bytes: bytes,
    ) -> dict[str, object]:
        return {
            "schema_version": "EmotionStatePhaseC1SourceEvidenceLedgerV1",
            "protocol_sha256": hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            "search_ledger_sha256": hashlib.sha256(
                search_ledger_bytes
            ).hexdigest().upper(),
            "sources": [self.valid_source_payload()],
            "cards": [self.valid_card_payload()],
            "fallback_assessments": [
                {
                    "signal": signal,
                    "status": "unresolved",
                    "material_evidence": [],
                    "preregistration_only": True,
                    "execution_authorized": False,
                    "reason_codes": ["annotation_fallback_unresolved"],
                }
                for signal in EXPECTED_SIGNALS
            ],
        }

    def valid_source_review_receipt(
        self,
        search_ledger_bytes: bytes,
        source_ledger_bytes: bytes,
    ) -> dict[str, object]:
        return {
            "schema_version": "EmotionStatePhaseC1SourceReviewReceiptV1",
            "protocol_sha256": hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            "search_ledger_sha256": hashlib.sha256(
                search_ledger_bytes
            ).hexdigest().upper(),
            "source_evidence_ledger_sha256": hashlib.sha256(
                source_ledger_bytes
            ).hexdigest().upper(),
            "transport_ledger_sha256": "D" * 64,
            "reviewed_transport_receipt_sha256s": ["A" * 64],
            "reviewed_document_sha256s": ["B" * 64],
            "review_scope": (
                "all_transport_discovery_citation_source_cards_and_search_completeness"
            ),
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

    @staticmethod
    def invalid_transport_mutations() -> tuple[_ReceiptMutation, ...]:
        return (
            _ReceiptMutation(
                "unknown_transport_body",
                lambda item: item.__setitem__("body", "{}"),
            ),
            _ReceiptMutation(
                "private_requested_url",
                lambda item: item.__setitem__(
                    "requested_url",
                    "https://127.0.0.1/source",
                ),
            ),
            _ReceiptMutation(
                "localhost_final_url",
                lambda item: item.__setitem__(
                    "final_url",
                    "https://localhost/source",
                ),
            ),
            _ReceiptMutation(
                "public_ip_literal",
                lambda item: item.__setitem__(
                    "requested_url",
                    _https("8.8.8.8/source"),
                ),
            ),
            _ReceiptMutation(
                "fragment",
                lambda item: item.__setitem__(
                    "requested_url",
                    _https("api.openalex.org/source#fragment"),
                ),
            ),
            _ReceiptMutation(
                "dot_segment",
                lambda item: item.__setitem__(
                    "requested_url",
                    _https("api.openalex.org/a/../source"),
                ),
            ),
            _ReceiptMutation(
                "backslash",
                lambda item: item.__setitem__(
                    "requested_url",
                    _https("api.openalex.org/a\\source"),
                ),
            ),
            _ReceiptMutation(
                "credential_query_parameter",
                lambda item: item.__setitem__(
                    "requested_url",
                    _https("api.openalex.org/works?token=secret"),
                ),
            ),
            _ReceiptMutation(
                "redirect_count_mismatch",
                lambda item: item.__setitem__("redirect_hop_count", 1),
            ),
            _ReceiptMutation(
                "private_redirect",
                lambda item: (
                    item.__setitem__("redirect_hop_count", 1),
                    item.__setitem__(
                        "redirect_chain",
                        [_https("127.0.0.1/source")],
                    ),
                ),
            ),
            _ReceiptMutation(
                "boolean_byte_count",
                lambda item: item.__setitem__("response_byte_count", True),
            ),
            _ReceiptMutation(
                "zero_byte_count",
                lambda item: item.__setitem__("response_byte_count", 0),
            ),
            _ReceiptMutation(
                "content_type_parameters",
                lambda item: item.__setitem__(
                    "response_content_type",
                    "application/json; charset=utf-8",
                ),
            ),
            _ReceiptMutation(
                "unknown_purpose",
                lambda item: item.__setitem__("purpose", "browser_body"),
            ),
            _ReceiptMutation(
                "bad_request_key",
                lambda item: item.__setitem__("request_key", "query-1"),
            ),
            _ReceiptMutation(
                "bad_timestamp",
                lambda item: item.__setitem__(
                    "retrieved_at_utc",
                    "2026-07-26T12:00:00+00:00",
                ),
            ),
            _ReceiptMutation(
                "incomplete_without_reason",
                lambda item: item.__setitem__("outcome", "incomplete"),
            ),
        )


class PhaseC1TrackedSourceLedgerTests(
    _PhaseC1FixtureMixin,
    unittest.TestCase,
):
    def load_protocol(self) -> phase_c1.PhaseC1ProtocolV1:
        protocol_bytes = self.protocol_path.read_bytes()
        return phase_c1.validate_discovery_protocol(
            phase_c1.load_json_strict(protocol_bytes, source="protocol")
        )

    def load_json(self, path: Path) -> dict[str, object]:
        payload = phase_c1.load_json_strict(
            path.read_bytes(),
            source=path.as_posix(),
        )
        self.assertIsInstance(payload, dict)
        return payload

    def test_tracked_ledgers_and_review_receipt_are_exactly_bound(self) -> None:
        protocol = self.load_protocol()
        search_bytes = SEARCH_LEDGER_PATH.read_bytes()
        source_bytes = SOURCE_LEDGER_PATH.read_bytes()
        search = phase_c1.validate_search_ledger(
            phase_c1.load_json_strict(search_bytes, source="search ledger"),
            protocol=protocol,
        )
        source = phase_c1.validate_source_evidence_ledger(
            phase_c1.load_json_strict(source_bytes, source="source ledger"),
            protocol=protocol,
            search_ledger_bytes=search_bytes,
        )
        review = phase_c1.validate_source_review_receipt(
            self.load_json(REVIEW_PATH),
            protocol=protocol,
            search_ledger_bytes=search_bytes,
            source_evidence_ledger_bytes=source_bytes,
        )
        expected_queries = phase_c1.expected_phase_c1_queries(protocol)
        self.assertEqual(len(search.query_records), 88)
        self.assertEqual(
            tuple(record.query_id for record in search.query_records),
            tuple(query[0] for query in expected_queries),
        )
        self.assertEqual(
            len({record.query_id for record in search.query_records}),
            88,
        )
        source_ids = {item.source_id for item in source.sources}
        card_ids = {item.card_id for item in source.cards}
        document_hash_order = tuple(
            document.cached_sha256
            for item in source.sources
            for document in item.documents
        )
        document_owner_by_id = {
            document.document_id: item.source_id
            for item in source.sources
            for document in item.documents
        }
        document_owner_by_sha256 = {
            document.cached_sha256: item.source_id
            for item in source.sources
            for document in item.documents
        }
        sources_by_id = {item.source_id: item for item in source.sources}
        expected_source_order = tuple(
            dict.fromkeys(
                source_id
                for signal in protocol.target_signals
                for source_id in search.candidate_order_by_signal[signal]
            )
            | dict.fromkeys(search.fallback_material_candidate_order)
        )
        self.assertEqual(len(source_ids), len(source.sources))
        self.assertEqual(
            tuple(item.source_id for item in source.sources),
            expected_source_order,
        )
        self.assertEqual(len(card_ids), len(source.cards))
        expected_card_pairs = tuple(
            (signal, source_id)
            for signal in protocol.target_signals
            for source_id in search.candidate_order_by_signal[signal]
        )
        actual_card_pairs = tuple(
            (item.signal, item.source_id)
            for item in source.cards
        )
        self.assertEqual(actual_card_pairs, expected_card_pairs)
        self.assertEqual(len(set(actual_card_pairs)), len(source.cards))
        self.assertEqual(
            review.reviewed_document_sha256s,
            document_hash_order,
        )
        for citation in search.citation_records:
            self.assertIn(citation.parent_source_id, sources_by_id)
            self.assertEqual(
                document_owner_by_sha256[
                    citation.parent_source_document_sha256
                ],
                citation.parent_source_id,
            )
        for assessment in source.fallback_assessments:
            self.assertEqual(
                tuple(item.source_id for item in assessment.material_evidence),
                search.fallback_material_candidate_order,
            )
            for material in assessment.material_evidence:
                self.assertIn(
                    "fallback_material_candidate",
                    sources_by_id[material.source_id].phase_c1_roles,
                )
                for evidence_ids in (
                    material.material_evidence_document_ids,
                    material.license_evidence_document_ids,
                    material.ethical_use_evidence_document_ids,
                    material.rater_feasibility_evidence_document_ids,
                ):
                    self.assertTrue(
                        all(
                            document_owner_by_id[document_id]
                            == material.source_id
                            for document_id in evidence_ids
                        )
                    )
        transport_hashes = [
            record.transport_receipt_sha256
            for record in search.query_records
        ]
        for record in search.query_records:
            for discovered in record.discovery_records:
                transport_hashes.extend(
                    discovered.documentation_transport_receipt_sha256s
                )
        for signal in protocol.target_signals:
            for direction in ("backward", "forward"):
                transport_hashes.extend(
                    search.citation_transport_receipt_sha256s_by_signal[
                        signal
                    ][direction]
                )
        for citation in search.citation_records:
            transport_hashes.extend(
                citation.documentation_transport_receipt_sha256s
            )
        transport_hashes.extend(
            document.transport_receipt_sha256
            for item in source.sources
            for document in item.documents
        )
        self.assertEqual(
            review.reviewed_transport_receipt_sha256s,
            tuple(dict.fromkeys(transport_hashes)),
        )
        self.assertEqual(
            search.search_complete,
            all(record.status == "complete" for record in search.query_records)
            and not any(record.truncated for record in search.query_records)
            and all(
                status in {"no_eligible_candidates", "source_list_exhausted"}
                for status in search.backward_citation_stop_by_signal.values()
            )
            and all(
                status in {"no_eligible_candidates", "source_list_exhausted"}
                for status in search.forward_citation_stop_by_signal.values()
            ),
        )
        fallback_queries_complete = all(
            record.status == "complete" and not record.truncated
            for record in search.query_records
            if record.query_kind == "fallback_material"
        )
        fallback_identity_resolved = not any(
            discovered.disposition == "unresolved"
            for record in search.query_records
            if record.query_kind == "fallback_material"
            for discovered in record.discovery_records
        )
        for signal in protocol.target_signals:
            signal_queries_complete = all(
                record.status == "complete"
                for record in search.query_records
                if record.signal == signal
            )
            self.assertEqual(
                search.fail_ready_by_signal[signal],
                signal_queries_complete
                and fallback_queries_complete
                and fallback_identity_resolved
                and search.fallback_material_overflow_count == 0
                and not any(
                    record.truncated
                    for record in search.query_records
                    if record.signal == signal
                )
                and not any(
                    discovered.disposition == "unresolved"
                    for record in search.query_records
                    if record.signal == signal
                    for discovered in record.discovery_records
                )
                and not any(
                    citation.disposition == "unresolved"
                    for citation in search.citation_records
                    if citation.signal == signal
                )
                and search.backward_citation_stop_by_signal[signal]
                in {"no_eligible_candidates", "source_list_exhausted"}
                and search.forward_citation_stop_by_signal[signal]
                in {"no_eligible_candidates", "source_list_exhausted"}
                and search.overflow_count_by_signal[signal] == 0,
            )
        self.assertEqual(review.verdict, "admitted")
        self.assertEqual(review.critical_findings, 0)
        self.assertEqual(review.important_findings, 0)
        self.assertEqual(review.minor_findings, 0)
        self.assertFalse(review.raw_rows_read)


class PhaseC1ProtocolContractTests(
    _PhaseC1FixtureMixin,
    unittest.TestCase,
):
    def test_protocol_is_exact_canonical_and_has_80_plus_8_queries(self) -> None:
        raw = self.protocol_path.read_bytes()
        payload = phase_c1.load_json_strict(raw, source="protocol")
        parsed = phase_c1.validate_discovery_protocol(payload)
        self.assertEqual(parsed.target_signals, EXPECTED_SIGNALS)
        self.assertEqual(
            len(parsed.target_signals)
            * len(parsed.query_templates)
            * len(parsed.source_channels),
            80,
        )
        self.assertEqual(
            len(parsed.fallback_material_query_templates)
            * len(parsed.source_channels),
            8,
        )
        self.assertEqual(parsed.expected_total_query_count, 88)
        self.assertEqual(
            dict(parsed.max_response_bytes_by_transport_purpose),
            {
                "seed_query": 2_000_000,
                "citation_discovery": 2_000_000,
                "authoritative_document": 20_000_000,
            },
        )
        self.assertEqual(
            {
                key: tuple(values)
                for key, values in (
                    parsed.allowed_response_content_types_by_transport_purpose.items()
                )
            },
            {
                "seed_query": ("application/json",),
                "citation_discovery": (
                    "application/json",
                    "text/html",
                    "text/plain",
                ),
                "authoritative_document": (
                    "application/json",
                    "application/pdf",
                    "application/xml",
                    "text/html",
                    "text/plain",
                    "text/xml",
                ),
            },
        )
        self.assertEqual(parsed.max_total_source_cache_bytes, 512_000_000)
        self.assertEqual(
            parsed.annotation_fallback_protocol,
            EXPECTED_ANNOTATION_FALLBACK_PROTOCOL,
        )
        self.assertEqual(parsed.signal_constructs, EXPECTED_SIGNAL_CONSTRUCTS)
        self.assertEqual(
            parsed.reason_code_order,
            EXPECTED_REASON_CODE_ORDER,
        )
        self.assertFalse(
            parsed.annotation_fallback_protocol["execution_authorized"]
        )
        self.assertEqual(raw, phase_c1.canonical_json_bytes(payload))

    def test_unknown_metric_and_every_top_level_omission_fail_closed(self) -> None:
        payload = self.valid_protocol_payload()
        for key in tuple(payload):
            with self.subTest(missing=key):
                candidate = copy.deepcopy(payload)
                del candidate[key]
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    phase_c1.validate_discovery_protocol(candidate)

        candidate = copy.deepcopy(payload)
        candidate["extra"] = True
        with self.assertRaises(phase_c1.PhaseC1ContractError):
            phase_c1.validate_discovery_protocol(candidate)

        mutations = (
            lambda item: item.__setitem__(
                "target_signals",
                list(reversed(EXPECTED_SIGNALS)),
            ),
            lambda item: item["reliability_rules"][0].__setitem__(
                "metric_id",
                "cohen_kappa",
            ),
            lambda item: item.__setitem__("expected_seed_query_count", True),
            lambda item: item.__setitem__("expected_total_query_count", 80),
            lambda item: item["annotation_fallback_protocol"].__setitem__(
                "execution_authorized",
                True,
            ),
            lambda item: item["annotation_fallback_protocol"].__setitem__(
                "minimum_independent_raters_per_segment",
                2,
            ),
            lambda item: item["annotation_fallback_protocol"].__setitem__(
                "majority_vote_as_ground_truth_allowed",
                True,
            ),
            lambda item: item["annotation_fallback_protocol"].__setitem__(
                "extra",
                "unknown",
            ),
            lambda item: item["signal_constructs"][0]["excluded_proxies"].pop(),
            lambda item: item["signal_constructs"][0].__setitem__(
                "direct_label_requirement",
                "changed after discovery",
            ),
            lambda item: item["reason_code_order"].reverse(),
            lambda item: item["observer_method_order"].remove(
                "independent_human_observer"
            ),
            lambda item: item[
                "max_response_bytes_by_transport_purpose"
            ].__setitem__("seed_query", 0),
            lambda item: item[
                "allowed_response_content_types_by_transport_purpose"
            ]["seed_query"].append("text/html"),
            lambda item: item.__setitem__(
                "max_total_source_cache_bytes",
                True,
            ),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(payload)
            mutate(candidate)
            with self.assertRaises(phase_c1.PhaseC1ContractError):
                phase_c1.validate_discovery_protocol(candidate)

    def test_protocol_nested_values_are_recursively_immutable(self) -> None:
        parsed = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        with self.assertRaises(TypeError):
            parsed.annotation_fallback_protocol["execution_authorized"] = True
        with self.assertRaises(TypeError):
            parsed.signal_constructs[0]["excluded_proxies"] = ()
        self.assertIsInstance(
            parsed.signal_constructs[0]["excluded_proxies"],
            tuple,
        )

    def test_strict_json_helpers_reject_duplicate_nonfinite_and_bad_utf8(
        self,
    ) -> None:
        invalid_cases = (
            b'{"duplicate": 1, "duplicate": 2}',
            b'{"not_finite": NaN}',
            b"\xff",
        )
        for raw in invalid_cases:
            with self.subTest(raw=raw):
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    phase_c1.load_json_strict(raw, source="fixture")
        canonical = phase_c1.canonical_json_bytes({"z": 1, "a": "é"})
        self.assertEqual(canonical, '{\n  "a": "é",\n  "z": 1\n}\n'.encode())
        self.assertEqual(
            phase_c1.sha256_bytes(b"phase-c1"),
            hashlib.sha256(b"phase-c1").hexdigest().upper(),
        )

    def test_fixture_and_documentation_are_canonical_rowless_and_plan_only(
        self,
    ) -> None:
        fixture_path = (
            ROOT
            / "research"
            / "experiments"
            / "cases"
            / "emotion-state-004-phase-c1-contract-fixtures.json"
        )
        raw = fixture_path.read_bytes()
        payload = phase_c1.load_json_strict(raw, source="fixtures")
        self.assertEqual(payload, EXPECTED_FIXTURE_PAYLOAD)
        self.assertEqual(raw, phase_c1.canonical_json_bytes(payload))

        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        attribute_lines = attributes.splitlines()
        for rule in EXPECTED_PHASE_C0_GITATTRIBUTES_RULES:
            self.assertEqual(attribute_lines.count(rule), 1)
        for rule in EXPECTED_GITATTRIBUTES_RULES:
            self.assertEqual(attribute_lines.count(rule), 1)
        phase_c1_rules = tuple(
            line
            for line in attribute_lines
            if "emotion-state-004-phase-c1" in line.lower()
            or "/emotion_state/phase_c1_" in line
        )
        self.assertEqual(phase_c1_rules, EXPECTED_GITATTRIBUTES_RULES)
        self.assertFalse(
            any(
                "emotion-state-004-phase-c1" in line.lower() and "*" in line
                for line in attribute_lines
            )
        )

        note_path = (
            ROOT
            / "research"
            / "experiments"
            / "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission.md"
        )
        note = note_path.read_text(encoding="utf-8")
        self.assertTrue(note.startswith(EXPECTED_EXPERIMENT_NOTE_START))
        self.assertNotIn("\r", note)

    def test_discovery_endpoint_registry_entry_records_bounded_task7_use(
        self,
    ) -> None:
        registry_path = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
        registry = registry_path.read_text(encoding="utf-8")
        heading = "### EMOTION-STATE Phase C1 planned discovery endpoints"
        start = registry.index(heading)
        end = registry.index("\n## ", start)
        section = registry[start:end].strip()
        expected = """\
### EMOTION-STATE Phase C1 planned discovery endpoints

- Type: bounded public scholarly/dataset discovery metadata
- Sources:
  - https://api.openalex.org/works
  - https://api.crossref.org/works
  - https://zenodo.org/api/records
  - https://huggingface.co/api/datasets
- Project use: Task 7 discovery seed only; Task 8 froze the resulting rowless
  ledger package without reopening the network.
- Current status: Task 7 accessed bounded public metadata under the frozen
  protocol. Task 8 reviewed exact frozen bytes only. No authoritative URL was
  retained, so this existing endpoint entry is the only Phase C1 registry
  update.
- Thesis caution: discovery-service results are not authoritative source
  evidence and cannot admit a signal. The admitted Task 8 package creates no
  candidate/canonical pair, signal decision, or C2/model/runtime/provider/call
  authority."""
        self.assertEqual(section, expected)
        positions = [section.index(url) for url in EXPECTED_DISCOVERY_ENDPOINTS]
        self.assertEqual(positions, sorted(positions))
        for url in EXPECTED_DISCOVERY_ENDPOINTS:
            self.assertEqual(section.count(url), 1)


class PhaseC1TransportReceiptContractTests(
    _PhaseC1FixtureMixin,
    unittest.TestCase,
):
    def test_complete_receipt_is_canonical_bounded_and_rowless(self) -> None:
        receipt = phase_c1.parse_transport_receipt(
            self.valid_transport_receipt()
        )
        self.assertEqual(receipt.purpose, "seed_query")
        self.assertEqual(receipt.retrieved_at_utc, "2026-07-26T12:00:00Z")
        self.assertEqual(receipt.redirect_hop_count, 0)
        self.assertEqual(receipt.redirect_chain, ())
        self.assertEqual(receipt.outcome, "complete")
        self.assertEqual(receipt.response_byte_count, 512)
        self.assertEqual(receipt.response_content_type, "application/json")

    def test_unknown_redirect_private_url_or_transport_body_rejects(self) -> None:
        for mutation in self.invalid_transport_mutations():
            with self.subTest(mutation=mutation.name):
                payload = self.valid_transport_receipt()
                mutation.apply(payload)
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    phase_c1.parse_transport_receipt(payload)

    def test_incomplete_receipt_records_only_observed_bounded_facts(self) -> None:
        payload = self.valid_transport_receipt()
        payload.update(
            {
                "final_url": None,
                "outcome": "incomplete",
                "incomplete_reason": "network_error",
                "http_status_code": None,
                "response_sha256": None,
                "response_byte_count": None,
                "response_content_type": None,
            }
        )
        parsed = phase_c1.parse_transport_receipt(payload)
        self.assertEqual(parsed.outcome, "incomplete")
        self.assertEqual(parsed.incomplete_reason, "network_error")
        self.assertIsNone(parsed.final_url)
        self.assertIsNone(parsed.response_sha256)

    def test_authoritative_document_request_key_rejects_alias(self) -> None:
        payload = self.valid_transport_receipt()
        payload.update(
            {
                "purpose": "authoritative_document",
                "request_key": "c1-document-0001",
                "response_content_type": "application/pdf",
            }
        )
        parsed = phase_c1.parse_transport_receipt(payload)
        self.assertEqual(parsed.request_key, "c1-document-0001")

        payload["request_key"] = "c1-doc-0001"
        with self.assertRaises(phase_c1.PhaseC1ContractError):
            phase_c1.parse_transport_receipt(payload)

    def test_transport_ledger_applies_protocol_response_caps(self) -> None:
        payload = self.valid_transport_ledger()
        payload["receipts"][0]["response_byte_count"] = 2_000_001
        with self.assertRaises(phase_c1.PhaseC1ContractError):
            phase_c1.validate_transport_receipt_ledger(
                payload,
                protocol=phase_c1.validate_discovery_protocol(
                    self.valid_protocol_payload()
                ),
            )

    def test_forged_protocol_cannot_relax_response_cap(self) -> None:
        protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        forged_caps = dict(
            protocol.max_response_bytes_by_transport_purpose
        )
        forged_caps["seed_query"] = 2_000_001
        forged_protocol = replace(
            protocol,
            max_response_bytes_by_transport_purpose=MappingProxyType(
                forged_caps
            ),
        )
        payload = self.valid_transport_ledger()
        payload["receipts"][0]["response_byte_count"] = 2_000_001

        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError,
            "^transport_protocol$",
        ):
            phase_c1.validate_transport_receipt_ledger(
                payload,
                protocol=forged_protocol,
            )

    def test_forged_protocol_cannot_relax_content_type_allowlist(self) -> None:
        protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        forged_allowlist = {
            purpose: tuple(content_types)
            for purpose, content_types in (
                protocol.allowed_response_content_types_by_transport_purpose.items()
            )
        }
        forged_allowlist["seed_query"] = (
            "application/json",
            "text/plain",
        )
        forged_protocol = replace(
            protocol,
            allowed_response_content_types_by_transport_purpose=(
                MappingProxyType(forged_allowlist)
            ),
        )
        payload = self.valid_transport_ledger()
        payload["receipts"][0]["response_content_type"] = "text/plain"

        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError,
            "^transport_protocol$",
        ):
            phase_c1.validate_transport_receipt_ledger(
                payload,
                protocol=forged_protocol,
            )

    def test_forged_protocol_cannot_relax_total_unique_cache_cap(self) -> None:
        protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        forged_protocol = replace(
            protocol,
            max_total_source_cache_bytes=520_000_000,
        )
        payload = self.valid_transport_ledger()
        payload["receipts"] = []
        for index in range(1, 27):
            receipt = self.valid_transport_receipt()
            receipt.update(
                {
                    "receipt_id": f"c1-transport-{index:04d}",
                    "purpose": "authoritative_document",
                    "request_key": f"c1-document-{index:04d}",
                    "response_sha256": f"{index:064X}",
                    "response_byte_count": 20_000_000,
                    "response_content_type": "application/pdf",
                }
            )
            payload["receipts"].append(receipt)

        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError,
            "^transport_protocol$",
        ):
            phase_c1.validate_transport_receipt_ledger(
                payload,
                protocol=forged_protocol,
            )

    def test_non_fqdn_malformed_and_special_use_hosts_reject_without_dns(
        self,
    ) -> None:
        rejected_hosts = (
            "intranet",
            "printer.local",
            "service.internal",
            "reserved.invalid",
            "fixture.test",
            "docs.example",
            "router.home.arpa",
            "node.localdomain",
            "gateway.lan",
            "service.onion",
            "bad..example.com",
            "-bad.example.com",
            "bad-.example.com",
            "bad_host.example.com",
            "127.1",
            "0177.0000.0000.0001",
            "0x7f.0x0.0x0.0x1",
            "0x7f.0.0.1",
            "0177.0x0.0.01",
        )
        for host in rejected_hosts:
            with self.subTest(host=host):
                payload = self.valid_transport_receipt()
                payload["requested_url"] = _https(f"{host}/source")
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    phase_c1.parse_transport_receipt(payload)

    def test_numeric_dns_label_with_textual_domain_remains_allowed(
        self,
    ) -> None:
        for host in ("123.openalex.org", "api.123.openalex.org"):
            with self.subTest(host=host):
                payload = self.valid_transport_receipt()
                url = _https(f"{host}/source")
                payload["requested_url"] = url
                payload["final_url"] = url
                parsed = phase_c1.parse_transport_receipt(payload)
                self.assertEqual(parsed.requested_url, url)

    def test_forbidden_row_query_names_reject_in_every_transport_url(
        self,
    ) -> None:
        forbidden_query_names = (
            "%61UDIO",
            "CUSTOMER%5FID",
            "%66EATURE",
            "MODEL%5FMETRIC",
            "PARTICIPANT%5FID",
            "%70REDICTION",
            "PROBABILITY",
            "tran%C5%BFcript",
            "%75TTERANCE",
        )
        for query_name in forbidden_query_names:
            for location in ("requested_url", "final_url", "redirect_chain"):
                with self.subTest(
                    query_name=query_name,
                    location=location,
                ):
                    payload = self.valid_transport_receipt()
                    forbidden_url = _https(
                        f"api.openalex.org/works?{query_name}=row"
                    )
                    if location == "redirect_chain":
                        payload["redirect_hop_count"] = 1
                        payload["redirect_chain"] = [forbidden_url]
                    else:
                        payload[location] = forbidden_url
                    with self.assertRaises(phase_c1.PhaseC1ContractError):
                        phase_c1.parse_transport_receipt(payload)

    def test_discovery_query_and_pagination_names_remain_allowed(self) -> None:
        allowed_query_names = (
            "search",
            "query.bibliographic",
            "q",
            "size",
            "per-page",
            "rows",
            "limit",
        )
        for query_name in allowed_query_names:
            with self.subTest(query_name=query_name):
                payload = self.valid_transport_receipt()
                url = _https(
                    f"api.openalex.org/works?{query_name}=hesitation"
                )
                payload["requested_url"] = url
                payload["final_url"] = url
                parsed = phase_c1.parse_transport_receipt(payload)
                self.assertEqual(parsed.requested_url, url)

    def test_transport_ledger_rejects_unknown_duplicate_and_protocol_drift(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        mutations = []

        unknown = self.valid_transport_ledger()
        unknown["extra"] = True
        mutations.append(unknown)

        duplicate = self.valid_transport_ledger()
        duplicate["receipts"].append(copy.deepcopy(duplicate["receipts"][0]))
        mutations.append(duplicate)

        wrong_protocol = self.valid_transport_ledger()
        wrong_protocol["protocol_sha256"] = "B" * 64
        mutations.append(wrong_protocol)

        for payload in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    phase_c1.validate_transport_receipt_ledger(
                        payload,
                        protocol=protocol,
                    )


class PhaseC1SearchLedgerContractTests(
    _PhaseC1FixtureMixin,
    unittest.TestCase,
):
    def setUp(self) -> None:
        self.protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )

    def assert_contract_code(
        self,
        payload: dict[str, object],
        expected: str,
    ) -> None:
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            phase_c1.validate_search_ledger(
                payload,
                protocol=self.protocol,
            )
        self.assertEqual(raised.exception.code, expected)

    def add_discovery(
        self,
        payload: dict[str, object],
        query_index: int,
        record: dict[str, object],
        *,
        result_count: int | None = None,
    ) -> None:
        query = payload["query_records"][query_index]
        self.assertIsInstance(query, dict)
        query["discovery_records"].append(record)
        query["returned_count"] = len(query["discovery_records"])
        query["result_count"] = (
            query["returned_count"]
            if result_count is None
            else result_count
        )
        query["truncated"] = query["result_count"] > query["returned_count"]

    def add_citation(
        self,
        payload: dict[str, object],
        citation: dict[str, object],
    ) -> None:
        signal = citation["signal"]
        direction = citation["direction"]
        payload["citation_records"].append(citation)
        payload[
            f"{direction}_citation_count_by_signal"
        ][signal] += 1
        payload["citation_transport_receipt_sha256s_by_signal"][
            signal
        ][direction].append(citation["transport_receipt_sha256"])

    def test_expected_query_grid_has_exact_order_and_88_total(self) -> None:
        expected = phase_c1.expected_phase_c1_queries(self.protocol)
        self.assertEqual(len(expected), 88)
        self.assertEqual(
            expected[0],
            (
                "c1-query-hesitation-openalex-01",
                "direct_label_source",
                "openalex",
                "hesitation",
                "hesitation annotated spontaneous conversation corpus",
            ),
        )
        self.assertEqual(
            expected[-1],
            (
                "c1-query-fallback-material-huggingface-02",
                "fallback_material",
                "huggingface",
                None,
                (
                    "public spontaneous dialogue dataset license annotation "
                    "redistribution"
                ),
            ),
        )
        self.assertEqual(
            sum(item[1] == "direct_label_source" for item in expected),
            80,
        )
        self.assertEqual(
            sum(item[1] == "fallback_material" for item in expected),
            8,
        )
        self.assertEqual(expected, self.phase_c1_query_grid())

    def test_valid_ledger_returns_exact_immutable_contract_types(self) -> None:
        parsed = phase_c1.validate_search_ledger(
            self.valid_search_ledger_payload(),
            protocol=self.protocol,
        )
        self.assertEqual(
            tuple(field.name for field in fields(parsed)),
            (
                "protocol_sha256",
                "query_records",
                "citation_records",
                "candidate_order_by_signal",
                "overflow_count_by_signal",
                "fallback_material_candidate_order",
                "fallback_material_overflow_count",
                "backward_citation_count_by_signal",
                "forward_citation_count_by_signal",
                "backward_citation_stop_by_signal",
                "forward_citation_stop_by_signal",
                "citation_transport_receipt_sha256s_by_signal",
                "fail_ready_by_signal",
                "search_complete",
            ),
        )
        self.assertIsInstance(
            parsed.query_records[0],
            phase_c1.PhaseC1QueryRecordV1,
        )
        self.assertEqual(parsed.query_records[0].discovery_records, ())
        self.assertIsInstance(parsed.candidate_order_by_signal, MappingProxyType)
        self.assertIsInstance(
            parsed.citation_transport_receipt_sha256s_by_signal[
                "hesitation"
            ],
            MappingProxyType,
        )
        with self.assertRaises(FrozenInstanceError):
            parsed.search_complete = False
        with self.assertRaises(TypeError):
            parsed.candidate_order_by_signal["hesitation"] = ()

    def test_missing_reordered_or_duplicate_query_rejects(self) -> None:
        mutations = (
            lambda item: item["query_records"].pop(),
            lambda item: item["query_records"].reverse(),
            lambda item: item["query_records"].append(
                copy.deepcopy(item["query_records"][0])
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                candidate = self.valid_search_ledger_payload()
                mutate(candidate)
                self.assert_contract_code(candidate, "search_query_grid")

    def test_closed_shapes_reject_unknown_auxiliary_and_row_text(self) -> None:
        structural_mutations = (
            ("search_ledger_fields", lambda item: item.__setitem__("extra", {})),
            (
                "query_fields",
                lambda item: item["query_records"][0].__setitem__(
                    "auxiliary", {}
                ),
            ),
        )
        for expected, mutate in structural_mutations:
            with self.subTest(expected=expected):
                payload = self.valid_search_ledger_payload()
                mutate(payload)
                self.assert_contract_code(payload, expected)

        forbidden_keys = (
            "title",
            "abstract",
            "author",
            "author_names",
            "participant",
            "participant_id",
            "snippet",
            "raw_snippet",
            "html",
            "cookies",
            "headers",
            "credential",
            "credentials",
            "local_path",
        )
        for forbidden in forbidden_keys:
            with self.subTest(forbidden=forbidden):
                payload = self.valid_search_ledger_payload()
                payload[forbidden] = "forbidden row or transport body"
                self.assert_contract_code(payload, "forbidden_search_content")

    def test_discovery_and_citation_exact_fields_reject_body_envelopes(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        record = self.discovery_record(
            query_id=payload["query_records"][0]["query_id"],
            rank=1,
            record_number=1,
        )
        self.add_discovery(payload, 0, record)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001"
        ]
        valid = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertIsInstance(
            valid.query_records[0].discovery_records[0],
            phase_c1.PhaseC1DiscoveryRecordV1,
        )

        record["body"] = "forbidden"
        self.assert_contract_code(payload, "forbidden_search_content")

        payload = self.valid_search_ledger_payload()
        citation = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0002",
        )
        self.add_citation(payload, citation)
        payload["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0002"
        ]
        citation["depth"] = 2
        self.assert_contract_code(payload, "citation_fields")

    def test_complete_query_reconciles_counts_hashes_cap_and_truncation(
        self,
    ) -> None:
        mutations = (
            (
                "query_result_limit",
                lambda item: item["query_records"][0].__setitem__(
                    "result_limit", 24
                ),
            ),
            (
                "query_response_pair",
                lambda item: item["query_records"][0].__setitem__(
                    "response_sha256", None
                ),
            ),
            (
                "query_response_hash",
                lambda item: item["query_records"][0].__setitem__(
                    "response_sha256", "a" * 64
                ),
            ),
            (
                "query_response_bytes",
                lambda item: item["query_records"][0].__setitem__(
                    "response_byte_count", 2_000_001
                ),
            ),
            (
                "query_result_reconciliation",
                lambda item: item["query_records"][0].__setitem__(
                    "returned_count", 1
                ),
            ),
            (
                "query_result_reconciliation",
                lambda item: item["query_records"][0].update(
                    {"result_count": 0, "returned_count": 1}
                ),
            ),
            (
                "query_truncated",
                lambda item: item["query_records"][0].update(
                    {"result_count": 1, "truncated": False}
                ),
            ),
            (
                "query_complete",
                lambda item: item["query_records"][0].__setitem__(
                    "incomplete_reason", "network_error"
                ),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                payload = self.valid_search_ledger_payload()
                mutate(payload)
                self.assert_contract_code(payload, expected)

    def test_incomplete_query_is_preserved_and_forces_not_fail_ready(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        record = payload["query_records"][0]
        record["status"] = "incomplete"
        record["incomplete_reason"] = "rate_limit_pressure"
        record["response_sha256"] = None
        record["response_byte_count"] = None
        record["result_count"] = 0
        record["returned_count"] = 0
        record["truncated"] = False
        record["discovery_records"] = []
        payload["search_complete"] = False
        payload["fail_ready_by_signal"]["hesitation"] = False
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertFalse(parsed.search_complete)
        self.assertFalse(parsed.fail_ready_by_signal["hesitation"])

        payload = self.valid_search_ledger_payload()
        record = payload["query_records"][0]
        record.update(
            {
                "status": "incomplete",
                "incomplete_reason": "invalid_response",
                "result_count": 0,
                "returned_count": 0,
                "truncated": False,
                "discovery_records": [],
            }
        )
        payload["search_complete"] = False
        payload["fail_ready_by_signal"]["hesitation"] = False
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertIsNotNone(parsed.query_records[0].response_sha256)

    def test_incomplete_query_mismatch_mutations_have_exact_codes(self) -> None:
        def make_incomplete() -> dict[str, object]:
            payload = self.valid_search_ledger_payload()
            query = payload["query_records"][0]
            query.update(
                {
                    "status": "incomplete",
                    "incomplete_reason": "network_error",
                    "response_sha256": None,
                    "response_byte_count": None,
                    "result_count": 0,
                    "returned_count": 0,
                    "truncated": False,
                    "discovery_records": [],
                }
            )
            payload["search_complete"] = False
            payload["fail_ready_by_signal"]["hesitation"] = False
            return payload

        mutations = (
            (
                "query_incomplete_reason",
                lambda item: item["query_records"][0].__setitem__(
                    "incomplete_reason", None
                ),
            ),
            (
                "query_incomplete",
                lambda item: item["query_records"][0].__setitem__(
                    "result_count", 1
                ),
            ),
            (
                "query_incomplete",
                lambda item: item["query_records"][0].__setitem__(
                    "truncated", True
                ),
            ),
            (
                "query_incomplete",
                lambda item: item["query_records"][0][
                    "discovery_records"
                ].append({}),
            ),
            (
                "query_response_pair",
                lambda item: item["query_records"][0].__setitem__(
                    "response_sha256", "A" * 64
                ),
            ),
            (
                "query_status",
                lambda item: item["query_records"][0].__setitem__(
                    "status", "partial"
                ),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                payload = make_incomplete()
                mutate(payload)
                self.assert_contract_code(payload, expected)

    def test_returned_records_must_reconcile_and_truncation_blocks_fail(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        record = payload["query_records"][0]
        record["returned_count"] = 2
        record["discovery_records"] = record["discovery_records"][:1]
        self.assert_contract_code(payload, "query_result_reconciliation")

        payload = self.valid_search_ledger_payload()
        payload["query_records"][0].update(
            {"result_count": 1, "returned_count": 0, "truncated": True}
        )
        payload["search_complete"] = False
        payload["fail_ready_by_signal"]["hesitation"] = False
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertFalse(parsed.fail_ready_by_signal["hesitation"])

    def test_discovery_dispositions_are_disjoint_and_reason_partitioned(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        query_id = payload["query_records"][0]["query_id"]
        valid_records = (
            self.discovery_record(
                query_id=query_id,
                rank=1,
                record_number=1,
            ),
            self.discovery_record(
                query_id=query_id,
                rank=1,
                record_number=1,
                disposition="excluded",
                source_id=None,
                reason_code="target_label_absent",
                documentation_hashes=["D" * 64],
            ),
            self.discovery_record(
                query_id=query_id,
                rank=1,
                record_number=1,
                disposition="unresolved",
                source_id=None,
                reason_code="source_identity_unverified",
            ),
        )
        for record in valid_records:
            with self.subTest(disposition=record["disposition"]):
                candidate = self.valid_search_ledger_payload()
                self.add_discovery(candidate, 0, record)
                if record["disposition"] == "retained_candidate":
                    candidate["candidate_order_by_signal"]["hesitation"] = [
                        "c1-source-0001"
                    ]
                else:
                    candidate["fail_ready_by_signal"]["hesitation"] = (
                        record["disposition"] == "excluded"
                    )
                phase_c1.validate_search_ledger(
                    candidate,
                    protocol=self.protocol,
                )

        mutations = (
            (
                "discovery_disposition_fields",
                lambda item: item["query_records"][0][
                    "discovery_records"
                ][0].__setitem__("candidate_source_id", None),
            ),
            (
                "documentation_transport_hashes",
                lambda item: item["query_records"][0][
                    "discovery_records"
                ][0].__setitem__(
                    "documentation_transport_receipt_sha256s", []
                ),
            ),
            (
                "documentation_transport_hashes",
                lambda item: item["query_records"][0][
                    "discovery_records"
                ][0].__setitem__(
                    "documentation_transport_receipt_sha256s",
                    ["D" * 64, "D" * 64],
                ),
            ),
            (
                "documentation_transport_hashes",
                lambda item: item["query_records"][0][
                    "discovery_records"
                ][0].__setitem__(
                    "documentation_transport_receipt_sha256s",
                    [f"{index:064X}" for index in range(6)],
                ),
            ),
            (
                "discovery_reason_partition",
                lambda item: item["query_records"][0][
                    "discovery_records"
                ][0].update(
                    {
                        "disposition": "excluded",
                        "candidate_source_id": None,
                        "reason_code": "source_identity_unverified",
                    }
                ),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                candidate = self.valid_search_ledger_payload()
                record = self.discovery_record(
                    query_id=candidate["query_records"][0]["query_id"],
                    rank=1,
                    record_number=1,
                )
                self.add_discovery(candidate, 0, record)
                candidate["candidate_order_by_signal"]["hesitation"] = [
                    "c1-source-0001"
                ]
                mutate(candidate)
                self.assert_contract_code(candidate, expected)

    def test_discovery_ids_ranks_and_backward_duplicate_references(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        query_id = payload["query_records"][0]["query_id"]
        first = self.discovery_record(
            query_id=query_id,
            rank=1,
            record_number=1,
            disposition="excluded",
            source_id=None,
            reason_code="target_label_absent",
            documentation_hashes=["D" * 64],
        )
        second = self.discovery_record(
            query_id=query_id,
            rank=2,
            record_number=2,
            disposition="duplicate",
            source_id=None,
            duplicate_of="c1-discovery-0001",
        )
        second["identity_sha256"] = first["identity_sha256"]
        self.add_discovery(payload, 0, first)
        self.add_discovery(payload, 0, second)
        phase_c1.validate_search_ledger(payload, protocol=self.protocol)

        mutation_cases = (
            (
                "discovery_record_id",
                lambda records: records[0].__setitem__(
                    "discovery_record_id", "discovery-1"
                ),
            ),
            (
                "discovery_rank",
                lambda records: records[1].__setitem__("rank", 3),
            ),
            (
                "discovery_query_id",
                lambda records: records[0].__setitem__(
                    "query_id", "c1-query-hesitation-openalex-02"
                ),
            ),
            (
                "discovery_duplicate_reference",
                lambda records: records[1].__setitem__(
                    "duplicate_of_discovery_record_id",
                    "c1-discovery-0002",
                ),
            ),
            (
                "duplicate_discovery_record_id",
                lambda records: records[1].__setitem__(
                    "discovery_record_id", "c1-discovery-0001"
                ),
            ),
        )
        for expected, mutate in mutation_cases:
            with self.subTest(expected=expected):
                candidate = copy.deepcopy(payload)
                mutate(candidate["query_records"][0]["discovery_records"])
                self.assert_contract_code(candidate, expected)

    def test_duplicate_back_references_bind_the_same_identity(self) -> None:
        payload = self.valid_search_ledger_payload()
        query_id = payload["query_records"][0]["query_id"]
        first = self.discovery_record(
            query_id=query_id,
            rank=1,
            record_number=1,
            disposition="excluded",
            source_id=None,
            reason_code="target_label_absent",
            documentation_hashes=["D" * 64],
        )
        second = self.discovery_record(
            query_id=query_id,
            rank=2,
            record_number=2,
            disposition="duplicate",
            source_id=None,
            duplicate_of="c1-discovery-0001",
        )
        self.add_discovery(payload, 0, first)
        self.add_discovery(payload, 0, second)
        self.assert_contract_code(
            payload,
            "discovery_duplicate_identity",
        )

        second["identity_sha256"] = first["identity_sha256"]
        phase_c1.validate_search_ledger(payload, protocol=self.protocol)

        citation = self.retained_citation_candidate(
            signal="hesitation",
            source_id="c1-source-0002",
        )
        citation.update(
            {
                "disposition": "duplicate",
                "candidate_source_id": None,
                "duplicate_of_record_id": "c1-discovery-0001",
                "documentation_transport_receipt_sha256s": [],
            }
        )
        self.add_citation(payload, citation)
        self.assert_contract_code(payload, "citation_duplicate_identity")

    def test_duplicate_references_are_confined_to_their_identity_lane(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        hesitation_query = payload["query_records"][0]
        confusion_query = payload["query_records"][32]
        first = self.discovery_record(
            query_id=hesitation_query["query_id"],
            rank=1,
            record_number=1,
            disposition="excluded",
            source_id=None,
            reason_code="target_label_absent",
            documentation_hashes=["D" * 64],
        )
        duplicate = self.discovery_record(
            query_id=confusion_query["query_id"],
            rank=1,
            record_number=2,
            disposition="duplicate",
            source_id=None,
            duplicate_of=first["discovery_record_id"],
        )
        duplicate["identity_sha256"] = first["identity_sha256"]
        self.add_discovery(payload, 0, first)
        self.add_discovery(payload, 32, duplicate)
        self.assert_contract_code(payload, "discovery_duplicate_lane")

        payload = self.valid_search_ledger_payload()
        hesitation_query = payload["query_records"][0]
        fallback_query = payload["query_records"][80]
        first = self.discovery_record(
            query_id=hesitation_query["query_id"],
            rank=1,
            record_number=1,
            disposition="excluded",
            source_id=None,
            reason_code="target_label_absent",
            documentation_hashes=["D" * 64],
        )
        duplicate = self.discovery_record(
            query_id=fallback_query["query_id"],
            rank=1,
            record_number=2,
            disposition="duplicate",
            source_id=None,
            duplicate_of=first["discovery_record_id"],
        )
        duplicate["identity_sha256"] = first["identity_sha256"]
        self.add_discovery(payload, 0, first)
        self.add_discovery(payload, 80, duplicate)
        self.assert_contract_code(payload, "discovery_duplicate_lane")

        payload = self.valid_search_ledger_payload()
        hesitation_query = payload["query_records"][0]
        first = self.discovery_record(
            query_id=hesitation_query["query_id"],
            rank=1,
            record_number=1,
            disposition="excluded",
            source_id=None,
            reason_code="target_label_absent",
            documentation_hashes=["D" * 64],
        )
        self.add_discovery(payload, 0, first)
        citation = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0002",
        )
        citation.update(
            {
                "identity_sha256": first["identity_sha256"],
                "disposition": "duplicate",
                "candidate_source_id": None,
                "duplicate_of_record_id": first["discovery_record_id"],
                "documentation_transport_receipt_sha256s": [],
            }
        )
        self.add_citation(payload, citation)
        self.assert_contract_code(payload, "citation_duplicate_lane")

    def test_repeated_identity_or_source_identity_alias_must_be_duplicate(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        query = payload["query_records"][0]
        first = self.discovery_record(
            query_id=query["query_id"],
            rank=1,
            record_number=1,
            source_id="c1-source-0001",
        )
        second = self.discovery_record(
            query_id=query["query_id"],
            rank=2,
            record_number=2,
            source_id="c1-source-0002",
        )
        second["identity_sha256"] = first["identity_sha256"]
        self.add_discovery(payload, 0, first)
        self.add_discovery(payload, 0, second)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001",
            "c1-source-0002",
        ]
        self.assert_contract_code(
            payload,
            "duplicate_identity_unaccounted",
        )

        payload = self.valid_search_ledger_payload()
        query = payload["query_records"][0]
        first = self.discovery_record(
            query_id=query["query_id"],
            rank=1,
            record_number=1,
            source_id="c1-source-0001",
        )
        second = self.discovery_record(
            query_id=query["query_id"],
            rank=2,
            record_number=2,
            source_id="c1-source-0001",
        )
        self.add_discovery(payload, 0, first)
        self.add_discovery(payload, 0, second)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001"
        ]
        self.assert_contract_code(payload, "candidate_source_identity")

        payload = self.valid_search_ledger_payload()
        hesitation_query = payload["query_records"][0]
        confusion_query = payload["query_records"][32]
        hesitation = self.discovery_record(
            query_id=hesitation_query["query_id"],
            rank=1,
            record_number=1,
            source_id="c1-source-0001",
        )
        confusion = self.discovery_record(
            query_id=confusion_query["query_id"],
            rank=1,
            record_number=2,
            source_id="c1-source-0001",
        )
        confusion["identity_sha256"] = hesitation["identity_sha256"]
        self.add_discovery(payload, 0, hesitation)
        self.add_discovery(payload, 32, confusion)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001"
        ]
        payload["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0001"
        ]
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertEqual(
            parsed.candidate_order_by_signal["hesitation"],
            ("c1-source-0001",),
        )
        self.assertEqual(
            parsed.candidate_order_by_signal["confusion"],
            ("c1-source-0001",),
        )

        payload = self.valid_search_ledger_payload()
        hesitation_query = payload["query_records"][0]
        confusion_query = payload["query_records"][32]
        hesitation = self.discovery_record(
            query_id=hesitation_query["query_id"],
            rank=1,
            record_number=1,
            source_id="c1-source-0001",
        )
        confusion = self.discovery_record(
            query_id=confusion_query["query_id"],
            rank=1,
            record_number=2,
            source_id="c1-source-0002",
        )
        confusion["identity_sha256"] = hesitation["identity_sha256"]
        self.add_discovery(payload, 0, hesitation)
        self.add_discovery(payload, 32, confusion)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001"
        ]
        payload["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0002"
        ]
        self.assert_contract_code(payload, "candidate_identity_source")

    def test_same_identity_is_retained_in_direct_and_fallback_lanes(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        direct_query = payload["query_records"][0]
        fallback_query = payload["query_records"][80]
        direct = self.discovery_record(
            query_id=direct_query["query_id"],
            rank=1,
            record_number=1,
            source_id="c1-source-0001",
        )
        fallback = self.discovery_record(
            query_id=fallback_query["query_id"],
            rank=1,
            record_number=2,
            source_id="c1-source-0001",
        )
        fallback["identity_sha256"] = direct["identity_sha256"]
        self.add_discovery(payload, 0, direct)
        self.add_discovery(payload, 80, fallback)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001"
        ]
        payload["fallback_material_candidate_order"] = [
            "c1-source-0001"
        ]
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertEqual(
            parsed.candidate_order_by_signal["hesitation"],
            ("c1-source-0001",),
        )
        self.assertEqual(
            parsed.fallback_material_candidate_order,
            ("c1-source-0001",),
        )

    def test_transport_receipt_hashes_cannot_cross_attempt_authorities(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        payload["query_records"][1]["transport_receipt_sha256"] = payload[
            "query_records"
        ][0]["transport_receipt_sha256"]
        self.assert_contract_code(
            payload,
            "duplicate_query_transport_receipt",
        )

        payload = self.valid_search_ledger_payload()
        shared = self.fixture_hash("shared-citation-attempt")
        payload["citation_transport_receipt_sha256s_by_signal"][
            "confusion"
        ]["backward"].append(shared)
        payload["citation_transport_receipt_sha256s_by_signal"][
            "interest"
        ]["forward"].append(shared)
        self.assert_contract_code(
            payload,
            "citation_transport_attempts",
        )

        payload = self.valid_search_ledger_payload()
        query_hash = payload["query_records"][0][
            "transport_receipt_sha256"
        ]
        payload["citation_transport_receipt_sha256s_by_signal"][
            "confusion"
        ]["backward"].append(query_hash)
        self.assert_contract_code(payload, "transport_receipt_authority")

        payload = self.valid_search_ledger_payload()
        query = payload["query_records"][0]
        record = self.discovery_record(
            query_id=query["query_id"],
            rank=1,
            record_number=1,
            documentation_hashes=[query["transport_receipt_sha256"]],
        )
        self.add_discovery(payload, 0, record)
        payload["candidate_order_by_signal"]["hesitation"] = [
            "c1-source-0001"
        ]
        self.assert_contract_code(payload, "transport_receipt_authority")

    def test_candidate_orders_and_overflow_are_independently_derived(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        for index in range(21):
            query_index = 0
            query = payload["query_records"][query_index]
            record = self.discovery_record(
                query_id=query["query_id"],
                rank=index + 1,
                record_number=index + 1,
                source_id=f"c1-source-{index + 1:04d}",
            )
            self.add_discovery(payload, query_index, record)
        payload["candidate_order_by_signal"]["hesitation"] = [
            f"c1-source-{index:04d}" for index in range(1, 21)
        ]
        payload["overflow_count_by_signal"]["hesitation"] = 1
        payload["fail_ready_by_signal"]["hesitation"] = False
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertEqual(
            len(parsed.candidate_order_by_signal["hesitation"]),
            20,
        )
        self.assertEqual(parsed.overflow_count_by_signal["hesitation"], 1)

        for field, expected in (
            ("candidate_order_by_signal", "search_candidate_order"),
            ("overflow_count_by_signal", "search_candidate_overflow"),
        ):
            with self.subTest(field=field):
                candidate = copy.deepcopy(payload)
                if field == "candidate_order_by_signal":
                    candidate[field]["hesitation"].reverse()
                else:
                    candidate[field]["hesitation"] = 0
                self.assert_contract_code(candidate, expected)

    def test_fallback_order_cap_and_overflow_are_independently_derived(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        first_fallback = 80
        record_number = 1
        for query_index in range(first_fallback, 88):
            for rank in range(1, 3):
                query = payload["query_records"][query_index]
                record = self.discovery_record(
                    query_id=query["query_id"],
                    rank=rank,
                    record_number=record_number,
                    source_id=f"c1-source-{record_number:04d}",
                )
                self.add_discovery(payload, query_index, record)
                record_number += 1
        payload["fallback_material_candidate_order"] = [
            f"c1-source-{index:04d}" for index in range(1, 11)
        ]
        payload["fallback_material_overflow_count"] = 6
        payload["fail_ready_by_signal"] = {
            signal: False for signal in EXPECTED_SIGNALS
        }
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertEqual(
            parsed.fallback_material_candidate_order,
            tuple(f"c1-source-{index:04d}" for index in range(1, 11)),
        )
        self.assertEqual(parsed.fallback_material_overflow_count, 6)

        candidate = copy.deepcopy(payload)
        candidate["fallback_material_overflow_count"] = 5
        self.assert_contract_code(
            candidate,
            "fallback_material_overflow_mismatch",
        )

    def test_query_and_record_caps_reject_before_derived_orders(self) -> None:
        payload = self.valid_search_ledger_payload()
        query = payload["query_records"][0]
        for rank in range(1, 27):
            query["discovery_records"].append(
                self.discovery_record(
                    query_id=query["query_id"],
                    rank=rank,
                    record_number=rank,
                    disposition="excluded",
                    source_id=None,
                    reason_code="target_label_absent",
                    documentation_hashes=[f"{rank:064X}"],
                )
            )
        query["result_count"] = 26
        query["returned_count"] = 26
        self.assert_contract_code(payload, "query_returned_cap")

    def test_citation_records_and_stop_statuses_are_hash_bound(self) -> None:
        payload = self.valid_search_ledger_payload()
        payload["backward_citation_stop_by_signal"]["confusion"] = (
            "budget_reached"
        )
        payload["fail_ready_by_signal"]["confusion"] = False
        payload["search_complete"] = False
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertFalse(parsed.fail_ready_by_signal["confusion"])
        self.assertFalse(parsed.search_complete)

        payload = self.valid_search_ledger_payload()
        payload["backward_citation_count_by_signal"]["confusion"] += 1
        self.assert_contract_code(payload, "citation_count_mismatch")

    def test_citation_attempt_hashes_are_closed_bounded_and_directional(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        citation = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0002",
        )
        self.add_citation(payload, citation)
        payload["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0002"
        ]
        phase_c1.validate_search_ledger(payload, protocol=self.protocol)

        mutations = (
            (
                "citation_transport_attempt_missing",
                lambda item: item[
                    "citation_transport_receipt_sha256s_by_signal"
                ]["confusion"]["backward"].clear(),
            ),
            (
                "citation_transport_attempts",
                lambda item: item[
                    "citation_transport_receipt_sha256s_by_signal"
                ]["confusion"]["backward"].append(
                    citation["transport_receipt_sha256"]
                ),
            ),
            (
                "citation_transport_attempts",
                lambda item: item[
                    "citation_transport_receipt_sha256s_by_signal"
                ]["confusion"]["backward"].extend(
                    [f"{index:064X}" for index in range(2, 7)]
                ),
            ),
            (
                "citation_transport_attempt_missing",
                lambda item: (
                    item[
                        "citation_transport_receipt_sha256s_by_signal"
                    ]["confusion"]["backward"].clear(),
                    item[
                        "citation_transport_receipt_sha256s_by_signal"
                    ]["confusion"]["forward"].append(
                        citation["transport_receipt_sha256"]
                    ),
                ),
            ),
            (
                "citation_attempt_fields",
                lambda item: item[
                    "citation_transport_receipt_sha256s_by_signal"
                ]["confusion"].__setitem__("sideways", []),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                candidate = copy.deepcopy(payload)
                mutate(candidate)
                self.assert_contract_code(candidate, expected)

    def test_citation_ids_order_ranks_dispositions_and_documentation(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        first = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0002",
        )
        second = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0003",
            rank=2,
        )
        self.add_citation(payload, first)
        self.add_citation(payload, second)
        payload["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0002",
            "c1-source-0003",
        ]
        phase_c1.validate_search_ledger(payload, protocol=self.protocol)

        mutations = (
            (
                "citation_record_id",
                lambda records: records[0].__setitem__(
                    "citation_record_id", "citation-1"
                ),
            ),
            (
                "citation_record_id",
                lambda records: records[1].__setitem__("rank", 3),
            ),
            (
                "citation_order",
                lambda records: records.reverse(),
            ),
            (
                "citation_disposition_fields",
                lambda records: records[0].__setitem__(
                    "candidate_source_id", None
                ),
            ),
            (
                "documentation_transport_hashes",
                lambda records: records[0].__setitem__(
                    "documentation_transport_receipt_sha256s", []
                ),
            ),
            (
                "citation_reason_partition",
                lambda records: records[0].update(
                    {
                        "disposition": "excluded",
                        "candidate_source_id": None,
                        "reason_code": "source_identity_unverified",
                    }
                ),
            ),
            (
                "duplicate_citation_record_id",
                lambda records: records[1].__setitem__(
                    "citation_record_id",
                    records[0]["citation_record_id"],
                ),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                candidate = copy.deepcopy(payload)
                mutate(candidate["citation_records"])
                self.assert_contract_code(candidate, expected)

    def test_citation_duplicate_must_reference_earlier_canonical_record(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        query_id = payload["query_records"][0]["query_id"]
        discovery = self.discovery_record(
            query_id=query_id,
            rank=1,
            record_number=1,
            disposition="excluded",
            source_id=None,
            reason_code="target_label_absent",
            documentation_hashes=["D" * 64],
        )
        self.add_discovery(payload, 0, discovery)
        citation = self.retained_citation_candidate(
            signal="hesitation",
            source_id="c1-source-0002",
        )
        citation.update(
            {
                "disposition": "duplicate",
                "candidate_source_id": None,
                "duplicate_of_record_id": "c1-discovery-0001",
                "documentation_transport_receipt_sha256s": [],
            }
        )
        citation["identity_sha256"] = discovery["identity_sha256"]
        self.add_citation(payload, citation)
        phase_c1.validate_search_ledger(payload, protocol=self.protocol)

        citation["duplicate_of_record_id"] = citation["citation_record_id"]
        self.assert_contract_code(
            payload,
            "citation_duplicate_reference",
        )

    def test_citation_directions_share_the_same_signal_identity_lane(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        backward = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0001",
        )
        forward = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0002",
            direction="forward",
        )
        forward.update(
            {
                "identity_sha256": backward["identity_sha256"],
                "disposition": "duplicate",
                "candidate_source_id": None,
                "duplicate_of_record_id": backward[
                    "citation_record_id"
                ],
                "documentation_transport_receipt_sha256s": [],
            }
        )
        self.add_citation(payload, backward)
        self.add_citation(payload, forward)
        payload["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0001"
        ]
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertEqual(
            parsed.candidate_order_by_signal["confusion"],
            ("c1-source-0001",),
        )

    def test_retained_citation_enters_bounded_candidate_order(self) -> None:
        payload = self.valid_search_ledger_payload()
        citation = self.retained_citation_candidate(
            signal="confusion",
            source_id="c1-source-0002",
        )
        self.add_citation(payload, citation)
        payload["candidate_order_by_signal"]["confusion"].append(
            "c1-source-0002"
        )
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertIn(
            "c1-source-0002",
            parsed.candidate_order_by_signal["confusion"],
        )

        payload["candidate_order_by_signal"]["confusion"] = []
        self.assert_contract_code(payload, "search_candidate_order")

    def test_citation_candidates_share_detail_cap_and_record_overflow(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        for query_index in range(19):
            actual_query_index = 0
            query = payload["query_records"][actual_query_index]
            record = self.discovery_record(
                query_id=query["query_id"],
                rank=query_index + 1,
                record_number=query_index + 1,
                source_id=f"c1-source-{query_index + 1:04d}",
            )
            self.add_discovery(payload, actual_query_index, record)
        for rank, source_number in ((1, 20), (2, 21)):
            citation = self.retained_citation_candidate(
                signal="hesitation",
                source_id=f"c1-source-{source_number:04d}",
                rank=rank,
            )
            self.add_citation(payload, citation)
        payload["candidate_order_by_signal"]["hesitation"] = [
            f"c1-source-{index:04d}" for index in range(1, 21)
        ]
        payload["overflow_count_by_signal"]["hesitation"] = 1
        payload["fail_ready_by_signal"]["hesitation"] = False
        parsed = phase_c1.validate_search_ledger(
            payload,
            protocol=self.protocol,
        )
        self.assertEqual(parsed.overflow_count_by_signal["hesitation"], 1)
        self.assertNotIn(
            "c1-source-0021",
            parsed.candidate_order_by_signal["hesitation"],
        )

    def test_search_complete_and_fail_ready_are_exhaustively_derived(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        payload["search_complete"] = False
        self.assert_contract_code(payload, "search_complete")

        payload = self.valid_search_ledger_payload()
        payload["fail_ready_by_signal"]["interest"] = False
        self.assert_contract_code(payload, "search_fail_ready")

        exhaustive_stops = (
            "no_eligible_candidates",
            "source_list_exhausted",
        )
        for stop in exhaustive_stops:
            with self.subTest(stop=stop):
                candidate = self.valid_search_ledger_payload()
                candidate["backward_citation_stop_by_signal"][
                    "interest"
                ] = stop
                parsed = phase_c1.validate_search_ledger(
                    candidate,
                    protocol=self.protocol,
                )
                self.assertTrue(parsed.fail_ready_by_signal["interest"])

        for stop in ("budget_reached", "incomplete"):
            with self.subTest(stop=stop):
                candidate = self.valid_search_ledger_payload()
                candidate["backward_citation_stop_by_signal"][
                    "interest"
                ] = stop
                if stop == "budget_reached":
                    for rank in range(1, 6):
                        citation = self.retained_citation_candidate(
                            signal="interest",
                            source_id=f"c1-source-{rank:04d}",
                            rank=rank,
                        )
                        self.add_citation(candidate, citation)
                    candidate["candidate_order_by_signal"]["interest"] = [
                        f"c1-source-{rank:04d}" for rank in range(1, 6)
                    ]
                candidate["fail_ready_by_signal"]["interest"] = False
                candidate["search_complete"] = False
                parsed = phase_c1.validate_search_ledger(
                    candidate,
                    protocol=self.protocol,
                )
                self.assertFalse(parsed.fail_ready_by_signal["interest"])
                self.assertFalse(parsed.search_complete)

    def test_record_reason_partitions_and_documentation_lineage(
        self,
    ) -> None:
        aggregate_only_reasons = (
            "search_query_incomplete",
            "query_result_truncated",
            "candidate_overflow",
            "citation_budget_incomplete",
            "annotation_fallback_feasible",
            "annotation_fallback_unresolved",
        )
        for reason in aggregate_only_reasons:
            with self.subTest(record="discovery", reason=reason):
                payload = self.valid_search_ledger_payload()
                query = payload["query_records"][0]
                record = self.discovery_record(
                    query_id=query["query_id"],
                    rank=1,
                    record_number=1,
                    disposition="unresolved",
                    source_id=None,
                    reason_code=reason,
                )
                self.add_discovery(payload, 0, record)
                payload["fail_ready_by_signal"]["hesitation"] = False
                self.assert_contract_code(
                    payload,
                    "discovery_reason_partition",
                )

            with self.subTest(record="citation", reason=reason):
                payload = self.valid_search_ledger_payload()
                record = self.retained_citation_candidate(
                    signal="confusion",
                    source_id="c1-source-0001",
                )
                record.update(
                    {
                        "disposition": "unresolved",
                        "candidate_source_id": None,
                        "reason_code": reason,
                        "documentation_transport_receipt_sha256s": [],
                    }
                )
                self.add_citation(payload, record)
                payload["fail_ready_by_signal"]["confusion"] = False
                self.assert_contract_code(
                    payload,
                    "citation_reason_partition",
                )

        for reason in (
            "source_identity_unverified",
            "authoritative_provenance_unverified",
            "access_unresolved",
        ):
            with self.subTest(pre_screen_reason=reason):
                payload = self.valid_search_ledger_payload()
                query = payload["query_records"][0]
                record = self.discovery_record(
                    query_id=query["query_id"],
                    rank=1,
                    record_number=1,
                    disposition="unresolved",
                    source_id=None,
                    reason_code=reason,
                )
                self.add_discovery(payload, 0, record)
                payload["fail_ready_by_signal"]["hesitation"] = False
                phase_c1.validate_search_ledger(
                    payload,
                    protocol=self.protocol,
                )

        for documentation_hashes in (
            [],
            [self.fixture_hash("screened-unresolved-document")],
        ):
            with self.subTest(
                screened_documentation_count=len(documentation_hashes)
            ):
                payload = self.valid_search_ledger_payload()
                query = payload["query_records"][0]
                record = self.discovery_record(
                    query_id=query["query_id"],
                    rank=1,
                    record_number=1,
                    disposition="unresolved",
                    source_id=None,
                    reason_code="source_documentation_incomplete",
                    documentation_hashes=documentation_hashes,
                )
                self.add_discovery(payload, 0, record)
                payload["fail_ready_by_signal"]["hesitation"] = False
                if documentation_hashes:
                    phase_c1.validate_search_ledger(
                        payload,
                        protocol=self.protocol,
                    )
                else:
                    self.assert_contract_code(
                        payload,
                        "documentation_transport_hashes",
                    )

                payload = self.valid_search_ledger_payload()
                record = self.retained_citation_candidate(
                    signal="confusion",
                    source_id="c1-source-0001",
                )
                record.update(
                    {
                        "disposition": "unresolved",
                        "candidate_source_id": None,
                        "reason_code": (
                            "source_documentation_incomplete"
                        ),
                        "documentation_transport_receipt_sha256s": (
                            documentation_hashes
                        ),
                    }
                )
                self.add_citation(payload, record)
                payload["fail_ready_by_signal"]["confusion"] = False
                if documentation_hashes:
                    phase_c1.validate_search_ledger(
                        payload,
                        protocol=self.protocol,
                    )
                else:
                    self.assert_contract_code(
                        payload,
                        "documentation_transport_hashes",
                    )

    def test_overflow_or_incomplete_citation_cannot_claim_fail_ready(
        self,
    ) -> None:
        payload = self.valid_search_ledger_payload()
        payload["overflow_count_by_signal"]["confusion"] = 1
        payload["fail_ready_by_signal"]["confusion"] = True
        self.assert_contract_code(payload, "search_fail_ready")

        payload = self.valid_search_ledger_payload()
        payload["backward_citation_stop_by_signal"]["confusion"] = (
            "incomplete"
        )
        self.assert_contract_code(payload, "search_fail_ready")

    def test_signal_and_direction_maps_are_exact_closed_boolean_shapes(
        self,
    ) -> None:
        mutations = (
            (
                "search_signal_order",
                lambda item: item["candidate_order_by_signal"].__setitem__(
                    "other", []
                ),
            ),
            (
                "search_candidate_overflow",
                lambda item: item["overflow_count_by_signal"].__setitem__(
                    "hesitation", True
                ),
            ),
            (
                "citation_count_map",
                lambda item: item[
                    "backward_citation_count_by_signal"
                ].pop("hesitation"),
            ),
            (
                "citation_stop_map",
                lambda item: item[
                    "forward_citation_stop_by_signal"
                ].__setitem__("hesitation", "done"),
            ),
            (
                "citation_attempt_signal_map",
                lambda item: item[
                    "citation_transport_receipt_sha256s_by_signal"
                ].pop("hesitation"),
            ),
            (
                "search_fail_ready",
                lambda item: item["fail_ready_by_signal"].__setitem__(
                    "hesitation", 1
                ),
            ),
            (
                "search_complete",
                lambda item: item.__setitem__("search_complete", 1),
            ),
        )
        for expected, mutate in mutations:
            with self.subTest(expected=expected):
                payload = self.valid_search_ledger_payload()
                mutate(payload)
                self.assert_contract_code(payload, expected)


class PhaseC1SourceContractTests(_PhaseC1FixtureMixin, unittest.TestCase):
    def test_direct_spontaneous_segment_card_parses_to_immutable_types(
        self,
    ) -> None:
        source = phase_c1.parse_source_receipt(self.valid_source_payload())
        card = phase_c1.parse_evidence_card(self.valid_card_payload())
        self.assertEqual(source.source_id, "c1-source-0001")
        self.assertEqual(card.signal, "confusion")
        self.assertEqual(
            card.construct_correspondence,
            "direct_target_construct",
        )
        self.assertEqual(card.temporal_unit, "bounded_segment")
        self.assertEqual(card.reliability.point_micros, 840_000)

    def test_rows_text_predictions_and_unknown_fields_reject_recursively(
        self,
    ) -> None:
        for forbidden in (
            "audio",
            "customer_id",
            "feature",
            "model_metric",
            "participant_id",
            "prediction",
            "probability",
            "transcript",
            "utterance",
        ):
            payload = self.valid_card_payload()
            payload[forbidden] = "forbidden"
            with self.assertRaisesRegex(
                phase_c1.PhaseC1ContractError,
                "forbidden_content",
            ):
                phase_c1.parse_evidence_card(payload)

    def test_private_login_http_and_unbounded_document_receipts_reject(
        self,
    ) -> None:
        invalid_urls = (
            "http://example.org/source",
            "https://localhost/source",
            "https://127.0.0.1/source",
            "https://" + "169.254.169.254/latest/meta-data/",
        )
        for value in invalid_urls:
            payload = self.valid_source_payload()
            payload["documents"][0]["authoritative_url"] = value
            with self.assertRaises(phase_c1.PhaseC1ContractError):
                phase_c1.parse_source_receipt(payload)

    def test_source_card_and_reliability_mutations_have_exact_codes(
        self,
    ) -> None:
        mutations = (
            ("source_id_mismatch", self.valid_source_payload, lambda item: item.__setitem__("source_id", "source-1"), phase_c1.parse_source_receipt),
            ("source_role_missing_or_unknown", self.valid_source_payload, lambda item: item.__setitem__("phase_c1_roles", ["unknown"]), phase_c1.parse_source_receipt),
            ("document_hash_malformed", self.valid_source_payload, lambda item: item["documents"][0].__setitem__("cached_sha256", "bad"), phase_c1.parse_source_receipt),
            ("document_role_unknown", self.valid_source_payload, lambda item: item["documents"][0].__setitem__("role", "other"), phase_c1.parse_source_receipt),
            ("document_transport_receipt_missing", self.valid_source_payload, lambda item: item["documents"][0].__setitem__("transport_receipt_sha256", "bad"), phase_c1.parse_source_receipt),
            ("login_claim_with_public_document", self.valid_source_payload, lambda item: item.__setitem__("access_status", "login_required"), phase_c1.parse_source_receipt),
            ("proxy_card_claimed_admissible", self.valid_card_payload, lambda item: item.__setitem__("construct_correspondence", "proxy_construct"), phase_c1.parse_evidence_card),
            ("native_definition_hash_malformed", self.valid_card_payload, lambda item: item.__setitem__("native_definition_excerpt_sha256", "bad"), phase_c1.parse_evidence_card),
            ("native_definition_locator_unbounded", self.valid_card_payload, lambda item: item.__setitem__("native_definition_locator", "x" * 513), phase_c1.parse_evidence_card),
            ("annotation_modality_unknown", self.valid_card_payload, lambda item: item.__setitem__("annotation_modality", "unknown"), phase_c1.parse_evidence_card),
            ("annotation_modality_unresolved_claimed_admissible", self.valid_card_payload, lambda item: item.__setitem__("annotation_modality", "unresolved"), phase_c1.parse_evidence_card),
            ("observer_method_unknown", self.valid_card_payload, lambda item: item.__setitem__("observer_method", "unknown"), phase_c1.parse_evidence_card),
            ("self_report_claimed_admissible", self.valid_card_payload, lambda item: item.__setitem__("observer_method", "self_report"), phase_c1.parse_evidence_card),
            ("conversation_card_claimed_admissible", self.valid_card_payload, lambda item: item.__setitem__("temporal_unit", "conversation"), phase_c1.parse_evidence_card),
            ("single_rater_claimed_admissible", self.valid_card_payload, lambda item: item.__setitem__("independent_rater_count", 1), phase_c1.parse_evidence_card),
            ("metric_not_allowlisted", self.valid_card_payload, lambda item: item["reliability"].__setitem__("metric_id", "cohen_kappa"), phase_c1.parse_evidence_card),
            ("alpha_interval_not_ordered", self.valid_card_payload, lambda item: item["reliability"].__setitem__("lower_95_micros", 850_000), phase_c1.parse_evidence_card),
            ("secondary_diagnostic_boolean", self.valid_card_payload, lambda item: item["reliability"].__setitem__("positive_agreement_micros", True), phase_c1.parse_evidence_card),
            ("secondary_diagnostic_out_of_range", self.valid_card_payload, lambda item: item["reliability"].__setitem__("positive_agreement_micros", 1_000_001), phase_c1.parse_evidence_card),
            ("admissible_reliability_postadjudication", self.valid_card_payload, lambda item: item["reliability"].__setitem__("preadjudication", False), phase_c1.parse_evidence_card),
            ("positive_count_boolean", self.valid_card_payload, lambda item: item["reliability"].__setitem__("published_positive_count", True), phase_c1.parse_evidence_card),
            ("positive_count_exceeds_rated_units", self.valid_card_payload, lambda item: item["reliability"].__setitem__("published_positive_count", 101), phase_c1.parse_evidence_card),
            ("card_signal_not_in_protocol", self.valid_card_payload, lambda item: item.__setitem__("signal", "other"), phase_c1.parse_evidence_card),
            ("source_reference_missing", self.valid_card_payload, lambda item: item.__setitem__("source_id", "missing"), phase_c1.parse_evidence_card),
            ("reason_codes_unsorted", self.valid_card_payload, lambda item: item.__setitem__("claimed_reason_codes", ["annotation_fallback_unresolved", "access_requires_login"]), phase_c1.parse_evidence_card),
            ("limitation_duplicate", self.valid_card_payload, lambda item: item.__setitem__("limitations", ["same", "same"]), phase_c1.parse_evidence_card),
        )
        for expected, build, mutate, parser in mutations:
            with self.subTest(mutation=expected):
                payload = build()
                mutate(payload)
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    parser(payload)
                self.assertEqual(raised.exception.code, expected)

    def test_source_ledger_and_review_mutations_have_exact_codes(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        search_bytes = self.valid_search_ledger_bytes()
        valid_ledger = self.valid_source_evidence_ledger(search_bytes)
        phase_c1.validate_source_evidence_ledger(
            valid_ledger, protocol=protocol, search_ledger_bytes=search_bytes
        )

        source_mutations = (
            ("document_role_duplicate", lambda item: item["sources"][0]["documents"].append({**copy.deepcopy(item["sources"][0]["documents"][0]), "document_id": "c1-document-0002", "cached_sha256": "E" * 64})),
            ("duplicate_document_id", lambda item: item["sources"][0]["documents"].append({**copy.deepcopy(item["sources"][0]["documents"][0]), "role": "license", "cached_sha256": "E" * 64})),
            ("duplicate_document_hash", lambda item: item["sources"][0]["documents"].append({**copy.deepcopy(item["sources"][0]["documents"][0]), "document_id": "c1-document-0002", "role": "license"})),
            ("native_definition_document_missing", lambda item: item["cards"][0].__setitem__("native_definition_document_id", "c1-document-9999")),
            ("acted_source_claimed_admissible", lambda item: item["sources"][0].__setitem__("conversation_status", "acted_or_scripted")),
            ("candidate_card_missing_or_duplicate", lambda item: item.__setitem__("cards", [])),
            ("card_outside_candidate_pair", lambda item: item["cards"].append({**copy.deepcopy(item["cards"][0]), "card_id": "c1-card-hesitation-0002", "signal": "hesitation"})),
            ("fallback_signal_missing", lambda item: item.__setitem__("fallback_assessments", item["fallback_assessments"][:-1])),
            ("fallback_status_unknown", lambda item: item["fallback_assessments"][0].__setitem__("status", "unknown")),
            ("fallback_reason_mismatch", lambda item: item["fallback_assessments"][0].__setitem__("reason_codes", [])),
            ("fallback_material_order_mismatch", lambda item: item["fallback_assessments"][0].__setitem__("material_evidence", [{"source_id": "c1-source-0001", "status": "unresolved", "public_spontaneous_material_status": "unresolved", "license_status": "unresolved", "ethical_use_status": "unresolved", "minimum_three_raters_status": "unresolved", "material_evidence_document_ids": [], "license_evidence_document_ids": [], "ethical_use_evidence_document_ids": [], "rater_feasibility_evidence_document_ids": []}])),
            ("fallback_search_hash_mismatch", lambda item: item.__setitem__("search_ledger_sha256", "F" * 64)),
        )
        for expected, mutate in source_mutations:
            with self.subTest(mutation=expected):
                payload = copy.deepcopy(valid_ledger)
                mutate(payload)
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.validate_source_evidence_ledger(
                        payload, protocol=protocol, search_ledger_bytes=search_bytes
                    )
                self.assertEqual(raised.exception.code, expected)

        fallback_search = phase_c1.load_json_strict(search_bytes, source="search")
        self.assertIsInstance(fallback_search, dict)
        fallback_search["fallback_material_candidate_order"] = [
            "c1-source-0001"
        ]
        fallback_search_bytes = phase_c1.canonical_json_bytes(fallback_search)
        fallback_ledger = self.valid_source_evidence_ledger(
            fallback_search_bytes
        )
        for assessment in fallback_ledger["fallback_assessments"]:
            assessment["material_evidence"] = [self.valid_fallback_material()]
        fallback_mutations = (
            ("fallback_material_status_mismatch", lambda item: item["fallback_assessments"][0]["material_evidence"][0].__setitem__("status", "feasible")),
            ("fallback_fact_evidence_missing", lambda item: item["fallback_assessments"][0]["material_evidence"][0].update({"status": "feasible", "public_spontaneous_material_status": "available", "license_status": "compatible", "ethical_use_status": "compatible", "minimum_three_raters_status": "feasible"})),
            ("fallback_fact_document_unknown", lambda item: item["fallback_assessments"][0]["material_evidence"][0]["material_evidence_document_ids"].append("c1-document-9999")),
        )
        for expected, mutate in fallback_mutations:
            with self.subTest(mutation=expected):
                payload = copy.deepcopy(fallback_ledger)
                mutate(payload)
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.validate_source_evidence_ledger(
                        payload, protocol=protocol,
                        search_ledger_bytes=fallback_search_bytes,
                    )
                self.assertEqual(raised.exception.code, expected)

        wrong_source_search = phase_c1.load_json_strict(
            search_bytes, source="search"
        )
        self.assertIsInstance(wrong_source_search, dict)
        wrong_source_search["fallback_material_candidate_order"] = [
            "c1-source-0002"
        ]
        wrong_source_search_bytes = phase_c1.canonical_json_bytes(
            wrong_source_search
        )
        wrong_source_ledger = self.valid_source_evidence_ledger(
            wrong_source_search_bytes
        )
        second_source = self.valid_source_payload()
        second_source["source_id"] = "c1-source-0002"
        second_source["documents"][0]["document_id"] = "c1-document-0002"
        second_source["documents"][0]["cached_sha256"] = "E" * 64
        wrong_source_ledger["sources"].append(second_source)
        for assessment in wrong_source_ledger["fallback_assessments"]:
            material = self.valid_fallback_material()
            material["source_id"] = "c1-source-0002"
            material["material_evidence_document_ids"] = [
                "c1-document-0001"
            ]
            assessment["material_evidence"] = [material]
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            phase_c1.validate_source_evidence_ledger(
                wrong_source_ledger, protocol=protocol,
                search_ledger_bytes=wrong_source_search_bytes,
            )
        self.assertEqual(
            raised.exception.code,
            "fallback_fact_document_wrong_source",
        )

        source_bytes = phase_c1.canonical_json_bytes(valid_ledger)
        review = self.valid_source_review_receipt(search_bytes, source_bytes)
        review_mutations = (
            ("reviewed_document_hash_omitted", lambda item: item.__setitem__("reviewed_document_sha256s", [])),
            ("reviewed_transport_hash_mismatch", lambda item: item.__setitem__("reviewed_transport_receipt_sha256s", [])),
            ("review_admitted_with_findings", lambda item: item.__setitem__("critical_findings", 1)),
            ("review_admitted_with_boundary_violation", lambda item: item.__setitem__("runtime_modified", True)),
        )
        for expected, mutate in review_mutations:
            with self.subTest(mutation=expected):
                payload = copy.deepcopy(review)
                mutate(payload)
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.validate_source_review_receipt(
                        payload, protocol=protocol, search_ledger_bytes=search_bytes,
                        source_evidence_ledger_bytes=source_bytes,
                    )
                self.assertEqual(raised.exception.code, expected)

    def test_review_transport_hashes_group_categories_before_deduplication(
        self,
    ) -> None:
        source_payload = self.valid_source_payload()
        source_payload["documents"][0]["transport_receipt_sha256"] = "F" * 64
        source = phase_c1.parse_source_receipt(source_payload)
        search = {
            "query_records": [
                {
                    "transport_receipt_sha256": "A" * 64,
                    "discovery_records": [
                        {"documentation_transport_receipt_sha256s": ["C" * 64, "A" * 64]}
                    ],
                },
                {
                    "transport_receipt_sha256": "B" * 64,
                    "discovery_records": [
                        {"documentation_transport_receipt_sha256s": ["D" * 64, "C" * 64]}
                    ],
                },
            ],
            "citation_records": [
                {
                    "transport_receipt_sha256": "E" * 64,
                    "documentation_transport_receipt_sha256s": ["D" * 64],
                }
            ],
            "citation_transport_receipt_sha256s_by_signal": {
                "hesitation": {
                    "backward": ["E" * 64, "1" * 64],
                    "forward": ["2" * 64],
                },
                "frustration": {
                    "backward": ["3" * 64],
                    "forward": [],
                },
                "confusion": {"backward": [], "forward": []},
                "interest": {"backward": [], "forward": []},
                "disengagement": {"backward": [], "forward": []},
            },
        }
        self.assertEqual(
            phase_c1._review_transport_hashes(search, (source,)),
            (
                "A" * 64,
                "B" * 64,
                "C" * 64,
                "D" * 64,
                "E" * 64,
                "1" * 64,
                "2" * 64,
                "3" * 64,
                "F" * 64,
            ),
        )

    def test_ledger_rejects_cross_source_duplicate_document_identity(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(self.valid_protocol_payload())
        search = phase_c1.load_json_strict(
            self.valid_search_ledger_bytes(), source="search"
        )
        self.assertIsInstance(search, dict)
        search["candidate_order_by_signal"]["hesitation"] = ["c1-source-0001"]
        search["candidate_order_by_signal"]["confusion"] = ["c1-source-0002"]
        search_bytes = phase_c1.canonical_json_bytes(search)
        source_one = self.valid_source_payload()
        source_two = self.valid_source_payload()
        source_two["source_id"] = "c1-source-0002"
        source_two["documents"][0]["document_id"] = "c1-document-0002"
        source_two["documents"][0]["cached_sha256"] = "E" * 64
        hesitation_card = self.valid_card_payload()
        hesitation_card.update({"card_id": "c1-card-hesitation-0001", "signal": "hesitation"})
        confusion_card = self.valid_card_payload()
        confusion_card.update({"source_id": "c1-source-0002", "native_definition_document_id": "c1-document-0002"})
        ledger = self.valid_source_evidence_ledger(search_bytes)
        ledger["sources"] = [source_one, source_two]
        ledger["cards"] = [hesitation_card, confusion_card]
        for field, value, expected in (
            ("document_id", "c1-document-0001", "duplicate_document_id"),
            ("cached_sha256", "B" * 64, "duplicate_document_hash"),
        ):
            with self.subTest(field=field):
                payload = copy.deepcopy(ledger)
                payload["sources"][1]["documents"][0][field] = value
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.validate_source_evidence_ledger(
                        payload, protocol=protocol, search_ledger_bytes=search_bytes
                    )
                self.assertEqual(raised.exception.code, expected)

    def test_partial_reliability_intervals_reject_when_any_pair_is_inverted(
        self,
    ) -> None:
        mutations = (
            {"lower_95_micros": 900_000, "upper_95_micros": None},
            {"point_micros": 900_000, "lower_95_micros": None, "upper_95_micros": 840_000},
            {"point_micros": None, "lower_95_micros": 900_000, "upper_95_micros": 840_000},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                payload = self.valid_card_payload()
                payload["reliability"].update(mutation)
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.parse_evidence_card(payload)
                self.assertEqual(raised.exception.code, "alpha_interval_not_ordered")

    def test_percent_encoded_url_hazards_reject_for_transport_and_documents(
        self,
    ) -> None:
        rejected_paths = (
            "/%2e%2e/source",
            "/%252e%252e/source",
            "/a%5cb",
            "/a%255cb",
            "/%00source",
            "/%2500source",
            "/a%2fb",
            "/bad%",
        )
        registered_url = self.valid_source_payload()["documents"][0][
            "authoritative_url"
        ]
        base_url = registered_url.removesuffix("/works")
        for path in rejected_paths:
            with self.subTest(path=path, receipt="transport"):
                url = f"{base_url}{path}"
                receipt = self.valid_transport_receipt()
                receipt["requested_url"] = url
                receipt["final_url"] = url
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.parse_transport_receipt(receipt)
                self.assertEqual(raised.exception.code, "transport_requested_url")
            with self.subTest(path=path, receipt="document"):
                url = f"{base_url}{path}"
                source = self.valid_source_payload()
                source["documents"][0]["authoritative_url"] = url
                with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
                    phase_c1.parse_source_receipt(source)
                self.assertEqual(raised.exception.code, "document_url")

        safe_url = f"{registered_url}%20metadata"
        receipt = self.valid_transport_receipt()
        receipt["requested_url"] = safe_url
        receipt["final_url"] = safe_url
        self.assertEqual(phase_c1.parse_transport_receipt(receipt).requested_url, safe_url)
        source = self.valid_source_payload()
        source["documents"][0]["authoritative_url"] = safe_url
        self.assertEqual(phase_c1.parse_source_receipt(source).documents[0].authoritative_url, safe_url)

    def test_missing_card_source_reference_rejects_before_pair_checks(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(self.valid_protocol_payload())
        search_bytes = self.valid_search_ledger_bytes()
        ledger = self.valid_source_evidence_ledger(search_bytes)
        card_reference = copy.deepcopy(ledger)
        card_reference["cards"][0]["source_id"] = "c1-source-9999"
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            phase_c1.validate_source_evidence_ledger(
                card_reference, protocol=protocol, search_ledger_bytes=search_bytes
            )
        self.assertEqual(raised.exception.code, "source_reference_missing")

    def test_missing_fallback_source_reference_rejects_before_order_checks(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(self.valid_protocol_payload())
        search_bytes = self.valid_search_ledger_bytes()
        ledger = self.valid_source_evidence_ledger(search_bytes)
        fallback_reference = copy.deepcopy(ledger)
        fallback_reference["fallback_assessments"][0]["material_evidence"] = [
            {**self.valid_fallback_material(), "source_id": "c1-source-9999"}
        ]
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            phase_c1.validate_source_evidence_ledger(
                fallback_reference, protocol=protocol, search_ledger_bytes=search_bytes
            )
        self.assertEqual(raised.exception.code, "source_reference_missing")

    def test_complete_but_reordered_sources_reject_with_source_order(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(self.valid_protocol_payload())
        search = phase_c1.load_json_strict(
            self.valid_search_ledger_bytes(), source="search"
        )
        self.assertIsInstance(search, dict)
        search["candidate_order_by_signal"]["interest"] = ["c1-source-0002"]
        search_bytes = phase_c1.canonical_json_bytes(search)
        wrong_order = self.valid_source_evidence_ledger(search_bytes)
        interest_card = self.valid_card_payload()
        interest_card.update(
            {
                "card_id": "c1-card-interest-0002",
                "signal": "interest",
                "source_id": "c1-source-0002",
                "native_definition_document_id": "c1-document-0002",
            }
        )
        wrong_order["cards"].append(interest_card)
        expected_pairs = tuple(
            (signal, source_id)
            for signal in EXPECTED_SIGNALS
            for source_id in search["candidate_order_by_signal"][signal]
        )
        actual_pairs = tuple(
            (card["signal"], card["source_id"])
            for card in wrong_order["cards"]
        )
        self.assertEqual(actual_pairs, expected_pairs)
        source_two = self.valid_source_payload()
        source_two["source_id"] = "c1-source-0002"
        source_two["documents"][0]["document_id"] = "c1-document-0002"
        source_two["documents"][0]["cached_sha256"] = "E" * 64
        wrong_order["sources"].append(source_two)
        wrong_order["sources"].reverse()
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            phase_c1.validate_source_evidence_ledger(
                wrong_order, protocol=protocol, search_ledger_bytes=search_bytes
            )
        self.assertEqual(raised.exception.code, "source_order")

    def test_existing_noncandidate_source_rejects_with_card_outside_pair(
        self,
    ) -> None:
        protocol = phase_c1.validate_discovery_protocol(self.valid_protocol_payload())
        search = phase_c1.load_json_strict(
            self.valid_search_ledger_bytes(), source="search"
        )
        self.assertIsInstance(search, dict)
        search["candidate_order_by_signal"]["interest"] = ["c1-source-0002"]
        outside_search_bytes = phase_c1.canonical_json_bytes(search)
        outside = self.valid_source_evidence_ledger(outside_search_bytes)
        source_two = self.valid_source_payload()
        source_two["source_id"] = "c1-source-0002"
        source_two["documents"][0]["document_id"] = "c1-document-0002"
        source_two["documents"][0]["cached_sha256"] = "E" * 64
        outside["sources"].append(source_two)
        outside["cards"][0]["source_id"] = "c1-source-0002"
        outside["cards"][0]["native_definition_document_id"] = "c1-document-0002"
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            phase_c1.validate_source_evidence_ledger(
                outside, protocol=protocol, search_ledger_bytes=outside_search_bytes
            )
        self.assertEqual(raised.exception.code, "card_outside_candidate_pair")

class PhaseC1SourceReviewPackageContractTests(
    _PhaseC1FixtureMixin, unittest.TestCase
):
    """Synthetic cross-ledger fixtures, deliberately independent of Task 7."""

    @staticmethod
    def _receipt_hash(receipt: dict[str, object]) -> str:
        return hashlib.sha256(phase_c1.canonical_json_bytes(receipt)).hexdigest().upper()

    def _receipt(
        self,
        receipt_id: int,
        *,
        purpose: str,
        request_key: str,
        response_label: str,
        byte_count: int = 512,
        content_type: str = "application/json",
    ) -> dict[str, object]:
        return {
            "schema_version": "EmotionStatePhaseC1TransportReceiptV1",
            "receipt_id": f"c1-transport-{receipt_id:04d}",
            "purpose": purpose,
            "request_key": request_key,
            "retrieved_at_utc": "2026-07-26T12:00:00Z",
            "requested_url": "https://api.openalex.org/works",
            "final_url": "https://api.openalex.org/works",
            "outcome": "complete",
            "incomplete_reason": None,
            "http_status_code": 200,
            "redirect_hop_count": 0,
            "redirect_chain": [],
            "response_sha256": self.fixture_hash(response_label),
            "response_byte_count": byte_count,
            "response_content_type": content_type,
        }

    def source_review_package(self) -> dict[str, object]:
        """Return a complete hand-derived rowless package and receipt bytes."""
        search = self.valid_search_ledger_payload()
        receipts: list[dict[str, object]] = []
        for number, query in enumerate(search["query_records"], start=1):
            assert isinstance(query, dict)
            query_id = query["query_id"]
            assert isinstance(query_id, str)
            receipt = self._receipt(
                number,
                purpose="seed_query",
                request_key=query_id,
                response_label=f"seed:{query_id}",
            )
            query["transport_receipt_sha256"] = self._receipt_hash(receipt)
            query["response_sha256"] = receipt["response_sha256"]
            query["response_byte_count"] = receipt["response_byte_count"]
            receipts.append(receipt)

        source_one_receipt = self._receipt(
            89,
            purpose="authoritative_document",
            request_key="c1-document-0001",
            response_label="source-one",
            byte_count=513,
            content_type="application/pdf",
        )
        source_two_receipt = self._receipt(
            90,
            purpose="authoritative_document",
            request_key="c1-document-0002",
            response_label="source-two",
            byte_count=514,
            content_type="application/pdf",
        )
        citation_attempt_receipt = self._receipt(
            91,
            purpose="citation_discovery",
            request_key="c1-citation-transport-hesitation-backward-01",
            response_label="citation-attempt",
        )
        citation_document_receipt = self._receipt(
            92,
            purpose="authoritative_document",
            request_key="c1-document-0003",
            response_label="citation-document",
            content_type="text/html",
        )
        receipts.extend(
            (
                source_one_receipt,
                source_two_receipt,
                citation_attempt_receipt,
                citation_document_receipt,
            )
        )
        source_one_hash = self._receipt_hash(source_one_receipt)
        source_two_hash = self._receipt_hash(source_two_receipt)
        citation_attempt_hash = self._receipt_hash(citation_attempt_receipt)
        citation_document_hash = self._receipt_hash(citation_document_receipt)

        confusion_query = search["query_records"][32]
        assert isinstance(confusion_query, dict)
        confusion_query["result_count"] = 1
        confusion_query["returned_count"] = 1
        confusion_query["discovery_records"] = [
            self.discovery_record(
                query_id="c1-query-confusion-openalex-01",
                rank=1,
                record_number=1,
                documentation_hashes=[source_one_hash],
            )
        ]
        fallback_query = search["query_records"][80]
        assert isinstance(fallback_query, dict)
        fallback_query["result_count"] = 1
        fallback_query["returned_count"] = 1
        fallback_query["discovery_records"] = [
            self.discovery_record(
                query_id="c1-query-fallback-material-openalex-01",
                rank=1,
                record_number=2,
                source_id="c1-source-0002",
                documentation_hashes=[source_two_hash],
            )
        ]
        search["candidate_order_by_signal"]["confusion"] = [
            "c1-source-0001"
        ]
        search["fallback_material_candidate_order"] = ["c1-source-0002"]
        search["citation_records"] = [
            {
                "citation_record_id": "c1-citation-hesitation-backward-01",
                "signal": "hesitation",
                "direction": "backward",
                "rank": 1,
                "parent_source_id": "c1-source-0001",
                "parent_source_document_sha256": source_one_receipt[
                    "response_sha256"
                ],
                "transport_receipt_sha256": citation_attempt_hash,
                "identity_sha256": self.fixture_hash("citation-identity"),
                "disposition": "excluded",
                "candidate_source_id": None,
                "duplicate_of_record_id": None,
                "reason_code": "target_label_absent",
                "documentation_transport_receipt_sha256s": [
                    citation_document_hash
                ],
            }
        ]
        search["backward_citation_count_by_signal"]["hesitation"] = 1
        search["citation_transport_receipt_sha256s_by_signal"]["hesitation"][
            "backward"
        ] = [citation_attempt_hash]
        search_bytes = phase_c1.canonical_json_bytes(search)

        source_one = self.valid_source_payload()
        source_one["documents"][0].update(
            {
                "cached_sha256": source_one_receipt["response_sha256"],
                "byte_count": source_one_receipt["response_byte_count"],
                "transport_receipt_sha256": source_one_hash,
            }
        )
        source_two = copy.deepcopy(source_one)
        source_two.update(
            {
                "source_id": "c1-source-0002",
                "title": "Synthetic fallback source",
                "phase_c1_roles": ["fallback_material_candidate"],
            }
        )
        source_two["documents"][0].update(
            {
                "document_id": "c1-document-0002",
                "cached_sha256": source_two_receipt["response_sha256"],
                "byte_count": source_two_receipt["response_byte_count"],
                "transport_receipt_sha256": source_two_hash,
            }
        )
        source = self.valid_source_evidence_ledger(search_bytes)
        source["sources"] = [source_one, source_two]
        for assessment in source["fallback_assessments"]:
            assessment["material_evidence"] = [
                {
                    **self.valid_fallback_material(),
                    "source_id": "c1-source-0002",
                }
            ]
        source_bytes = phase_c1.canonical_json_bytes(source)
        transport = {
            "schema_version": "EmotionStatePhaseC1TransportReceiptLedgerV1",
            "protocol_sha256": hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            "receipts": receipts,
        }
        transport_bytes = phase_c1.canonical_json_bytes(transport)
        review = self.valid_source_review_receipt(search_bytes, source_bytes)
        review["transport_ledger_sha256"] = hashlib.sha256(
            transport_bytes
        ).hexdigest().upper()
        review["reviewed_transport_receipt_sha256s"] = [
            query["transport_receipt_sha256"]
            for query in search["query_records"]
        ] + [
            source_one_hash,
            source_two_hash,
            citation_attempt_hash,
            citation_document_hash,
        ]
        review["reviewed_document_sha256s"] = [
            source_one_receipt["response_sha256"],
            source_two_receipt["response_sha256"],
        ]
        return {
            "protocol": phase_c1.validate_discovery_protocol(
                self.valid_protocol_payload()
            ),
            "search": search,
            "source": source,
            "transport": transport,
            "review": review,
        }

    def _validate(self, package: dict[str, object]) -> object:
        search_bytes = phase_c1.canonical_json_bytes(package["search"])
        source_bytes = phase_c1.canonical_json_bytes(package["source"])
        transport_bytes = phase_c1.canonical_json_bytes(package["transport"])
        return phase_c1.validate_source_review_package_before_freeze(
            package["review"],
            protocol=package["protocol"],
            search_ledger_bytes=search_bytes,
            source_evidence_ledger_bytes=source_bytes,
            transport_ledger_bytes=transport_bytes,
        )

    def _rebind_review(self, package: dict[str, object]) -> None:
        """Keep outer byte bindings valid so each mutation reaches its lane."""
        search_bytes = phase_c1.canonical_json_bytes(package["search"])
        package["source"]["search_ledger_sha256"] = hashlib.sha256(
            search_bytes
        ).hexdigest().upper()
        source_bytes = phase_c1.canonical_json_bytes(package["source"])
        transport_bytes = phase_c1.canonical_json_bytes(package["transport"])
        package["review"].update(
            {
                "search_ledger_sha256": hashlib.sha256(
                    search_bytes
                ).hexdigest().upper(),
                "source_evidence_ledger_sha256": hashlib.sha256(
                    source_bytes
                ).hexdigest().upper(),
                "transport_ledger_sha256": hashlib.sha256(
                    transport_bytes
                ).hexdigest().upper(),
            }
        )
        source = phase_c1.validate_source_evidence_ledger(
            package["source"],
            protocol=package["protocol"],
            search_ledger_bytes=search_bytes,
        )
        package["review"]["reviewed_document_sha256s"] = [
            document.cached_sha256
            for item in source.sources
            for document in item.documents
        ]
        package["review"]["reviewed_transport_receipt_sha256s"] = list(
            phase_c1._review_transport_hashes(package["search"], source.sources)
        )

    def test_valid_package_binds_each_canonical_receipt_once(self) -> None:
        package = self.source_review_package()
        review = self._validate(package)
        self.assertEqual(review.verdict, "admitted")

    def test_rejects_transport_ledger_hash_and_exact_receipt_union_faults(
        self,
    ) -> None:
        mutations = (
            lambda package: package["review"].__setitem__(
                "transport_ledger_sha256", "F" * 64
            ),
            lambda package: package["transport"]["receipts"].pop(),
            lambda package: package["transport"]["receipts"].append(
                self._receipt(
                    93,
                    purpose="citation_discovery",
                    request_key=(
                        "c1-citation-transport-hesitation-forward-01"
                    ),
                    response_label="unreferenced",
                )
            ),
            lambda package: package["transport"]["receipts"][88].__setitem__(
                "response_byte_count", 515
            ),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=mutate):
                package = self.source_review_package()
                mutate(package)
                if index:
                    self._rebind_review(package)
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    self._validate(package)

    def test_rejects_query_and_citation_transport_binding_faults(self) -> None:
        def swap_query_receipts(package: dict[str, object]) -> None:
            first = package["search"]["query_records"][0]
            second = package["search"]["query_records"][1]
            first_hash = first["transport_receipt_sha256"]
            first["transport_receipt_sha256"] = second[
                "transport_receipt_sha256"
            ]
            second["transport_receipt_sha256"] = first_hash

        def citation_mutation(
            package: dict[str, object], request_key: str | None = None
        ) -> None:
            receipt = package["transport"]["receipts"][90]
            receipt["purpose"] = "citation_discovery"
            if request_key is not None:
                receipt["request_key"] = request_key

        mutations = (
            swap_query_receipts,
            lambda package: (
                package["transport"]["receipts"][0].__setitem__(
                    "purpose", "authoritative_document"
                ),
                package["transport"]["receipts"][0].__setitem__(
                    "request_key", "c1-document-9999"
                ),
                package["search"]["query_records"][0].__setitem__(
                    "transport_receipt_sha256",
                    self._receipt_hash(package["transport"]["receipts"][0]),
                ),
            ),
            lambda package: citation_mutation(
                package, "c1-citation-transport-hesitation-backward-01"
            ) or package["transport"]["receipts"][90].update(
                {
                    "purpose": "authoritative_document",
                    "request_key": "c1-document-0004",
                }
            ),
            lambda package: citation_mutation(
                package,
                "c1-citation-transport-frustration-backward-01",
            ),
            lambda package: citation_mutation(
                package,
                "c1-citation-transport-hesitation-forward-01",
            ),
            lambda package: citation_mutation(
                package,
                "c1-citation-transport-hesitation-backward-02",
            ),
            lambda package: package["transport"]["receipts"][90].update(
                {"outcome": "incomplete", "incomplete_reason": "network_error"}
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                package = self.source_review_package()
                mutate(package)
                citation = package["transport"]["receipts"][90]
                citation_hash = self._receipt_hash(citation)
                package["search"]["citation_records"][0][
                    "transport_receipt_sha256"
                ] = citation_hash
                package["search"]["citation_transport_receipt_sha256s_by_signal"][
                    "hesitation"
                ]["backward"] = [citation_hash]
                self._rebind_review(package)
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    self._validate(package)

    def test_rejects_document_and_owner_transport_binding_faults(self) -> None:
        mutations = (
            lambda package: package["transport"]["receipts"][91].update(
                {
                    "purpose": "citation_discovery",
                    "request_key": (
                        "c1-citation-transport-hesitation-forward-01"
                    ),
                }
            ),
            lambda package: package["source"]["sources"][0]["documents"][0].__setitem__(
                "cached_sha256", "E" * 64
            ),
            lambda package: package["source"]["sources"][0]["documents"][0].__setitem__(
                "byte_count", 515
            ),
            lambda package: package["source"]["sources"][0]["documents"][0].__setitem__(
                "content_type", "application/json"
            ),
            lambda package: package["search"]["query_records"][32][
                "discovery_records"
            ][0].__setitem__(
                "documentation_transport_receipt_sha256s",
                [self._receipt_hash(package["transport"]["receipts"][91])],
            ),
            lambda package: package["search"]["citation_records"][0].__setitem__(
                "parent_source_id", "c1-source-0002"
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                package = self.source_review_package()
                mutate(package)
                self._rebind_review(package)
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    self._validate(package)

    def test_rejects_query_outcome_reason_hash_and_byte_mismatches(self) -> None:
        mutations = (
            lambda package: package["transport"]["receipts"][0].update(
                {"outcome": "incomplete", "incomplete_reason": "network_error"}
            ),
            lambda package: package["search"]["query_records"][0].__setitem__(
                "response_sha256", "E" * 64
            ),
            lambda package: package["search"]["query_records"][0].__setitem__(
                "response_byte_count", 511
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                package = self.source_review_package()
                mutate(package)
                if package["transport"]["receipts"][0]["outcome"] == "incomplete":
                    query = package["search"]["query_records"][0]
                    query["transport_receipt_sha256"] = self._receipt_hash(
                        package["transport"]["receipts"][0]
                    )
                    query.update(
                        {
                            "status": "incomplete",
                            "incomplete_reason": "rate_limit_pressure",
                            "response_sha256": None,
                            "response_byte_count": None,
                        }
                    )
                    package["search"]["fail_ready_by_signal"]["hesitation"] = False
                    package["search"]["search_complete"] = False
                self._rebind_review(package)
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    self._validate(package)

    def test_rejects_query_request_key_mismatch_alone(self) -> None:
        package = self.source_review_package()
        first_receipt = package["transport"]["receipts"][0]
        second_receipt = package["transport"]["receipts"][1]
        first_request_key = first_receipt["request_key"]
        first_receipt["request_key"] = second_receipt["request_key"]
        second_receipt["request_key"] = first_request_key
        package["search"]["query_records"][0][
            "transport_receipt_sha256"
        ] = self._receipt_hash(first_receipt)
        package["search"]["query_records"][1][
            "transport_receipt_sha256"
        ] = self._receipt_hash(second_receipt)
        self._rebind_review(package)
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            self._validate(package)
        self.assertEqual(raised.exception.code, "query_transport_binding")

    def test_rejects_query_outcome_mismatch_alone(self) -> None:
        package = self.source_review_package()
        receipt = package["transport"]["receipts"][0]
        receipt.update(
            {
                "outcome": "incomplete",
                "incomplete_reason": "network_error",
            }
        )
        package["search"]["query_records"][0][
            "transport_receipt_sha256"
        ] = self._receipt_hash(receipt)
        self._rebind_review(package)
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            self._validate(package)
        self.assertEqual(raised.exception.code, "query_transport_binding")

    def test_rejects_citation_documentation_with_non_document_purpose(
        self,
    ) -> None:
        package = self.source_review_package()
        receipt = package["transport"]["receipts"][91]
        receipt.update(
            {
                "purpose": "citation_discovery",
                "request_key": (
                    "c1-citation-transport-hesitation-forward-01"
                ),
            }
        )
        package["search"]["citation_records"][0][
            "documentation_transport_receipt_sha256s"
        ] = [self._receipt_hash(receipt)]
        self._rebind_review(package)
        with self.assertRaises(phase_c1.PhaseC1ContractError) as raised:
            self._validate(package)
        self.assertEqual(
            raised.exception.code,
            "citation_documentation_transport_purpose",
        )

    def test_rejects_source_document_request_key_mismatch(self) -> None:
        package = self.source_review_package()
        package["transport"]["receipts"][88]["request_key"] = (
            "c1-document-0004"
        )
        source_one_hash = self._receipt_hash(package["transport"]["receipts"][88])
        package["source"]["sources"][0]["documents"][0][
            "transport_receipt_sha256"
        ] = source_one_hash
        package["search"]["query_records"][32]["discovery_records"][0][
            "documentation_transport_receipt_sha256s"
        ] = [source_one_hash]
        self._rebind_review(package)
        with self.assertRaises(phase_c1.PhaseC1ContractError):
            self._validate(package)

    def test_rejects_discovery_documentation_with_non_document_purpose(
        self,
    ) -> None:
        package = self.source_review_package()
        receipt = package["transport"]["receipts"][88]
        receipt.update(
            {
                "purpose": "citation_discovery",
                "request_key": "c1-citation-transport-hesitation-forward-01",
            }
        )
        source_one_hash = self._receipt_hash(receipt)
        package["source"]["sources"][0]["documents"][0][
            "transport_receipt_sha256"
        ] = source_one_hash
        package["search"]["query_records"][32]["discovery_records"][0][
            "documentation_transport_receipt_sha256s"
        ] = [source_one_hash]
        self._rebind_review(package)
        with self.assertRaises(phase_c1.PhaseC1ContractError):
            self._validate(package)


class PhaseC1DecisionTests(_PhaseC1FixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )

    def reliability(
        self, **overrides: object
    ) -> phase_c1.PhaseC1ReliabilityEvidenceV1:
        payload = self.valid_card_payload()["reliability"]
        self.assertIsInstance(payload, dict)
        payload.update(
            {
                "rated_unit_count": 200,
                "published_positive_count": 100,
                "preadjudication": True,
                "verifiable": True,
            }
        )
        payload.update(overrides)
        return phase_c1.parse_evidence_card(
            {**self.valid_card_payload(), "reliability": payload}
        ).reliability

    def source(
        self, **overrides: object
    ) -> phase_c1.PhaseC1SourceReceiptV1:
        payload = self.valid_source_payload()
        payload.update(overrides)
        if payload["access_status"] == "login_required":
            payload["documents"][0]["public_without_login"] = False
        return phase_c1.parse_source_receipt(payload)

    def direct_card(
        self, **overrides: object
    ) -> phase_c1.PhaseC1EvidenceCardV1:
        payload = self.valid_card_payload()
        payload.update(overrides)
        if isinstance(payload["claimed_reason_codes"], tuple):
            payload["claimed_reason_codes"] = list(payload["claimed_reason_codes"])
        return phase_c1.parse_evidence_card(payload)

    def search_ledger(
        self,
        *,
        fail_ready: bool = True,
        candidate_signals: tuple[str, ...] = (),
    ) -> phase_c1.PhaseC1SearchLedgerV1:
        protocol_sha256 = hashlib.sha256(
            self.protocol_path.read_bytes()
        ).hexdigest().upper()
        return phase_c1.PhaseC1SearchLedgerV1(
            protocol_sha256=protocol_sha256,
            query_records=(),
            citation_records=(),
            candidate_order_by_signal=MappingProxyType(
                {
                    signal: ("c1-source-0001",)
                    if signal in candidate_signals else ()
                    for signal in EXPECTED_SIGNALS
                }
            ),
            overflow_count_by_signal=MappingProxyType(
                {signal: 0 for signal in EXPECTED_SIGNALS}
            ),
            fallback_material_candidate_order=(),
            fallback_material_overflow_count=0,
            backward_citation_count_by_signal=MappingProxyType(
                {signal: 0 for signal in EXPECTED_SIGNALS}
            ),
            forward_citation_count_by_signal=MappingProxyType(
                {signal: 0 for signal in EXPECTED_SIGNALS}
            ),
            backward_citation_stop_by_signal=MappingProxyType(
                {signal: "source_list_exhausted" for signal in EXPECTED_SIGNALS}
            ),
            forward_citation_stop_by_signal=MappingProxyType(
                {signal: "source_list_exhausted" for signal in EXPECTED_SIGNALS}
            ),
            citation_transport_receipt_sha256s_by_signal=MappingProxyType(
                {
                    signal: MappingProxyType({"backward": (), "forward": ()})
                    for signal in EXPECTED_SIGNALS
                }
            ),
            fail_ready_by_signal=MappingProxyType(
                {signal: fail_ready for signal in EXPECTED_SIGNALS}
            ),
            search_complete=fail_ready,
        )

    def source_ledger(
        self,
        cards: tuple[phase_c1.PhaseC1EvidenceCardV1, ...] = (),
        assessments: tuple[
            phase_c1.PhaseC1AnnotationFallbackAssessmentV1, ...
        ] | None = None,
    ) -> phase_c1.PhaseC1SourceEvidenceLedgerV1:
        if assessments is None:
            assessments = tuple(
                phase_c1.PhaseC1AnnotationFallbackAssessmentV1(
                    signal=signal,
                    status="infeasible",
                    material_evidence=(),
                    preregistration_only=True,
                    execution_authorized=False,
                    reason_codes=(),
                )
                for signal in EXPECTED_SIGNALS
            )
        return phase_c1.PhaseC1SourceEvidenceLedgerV1(
            protocol_sha256=hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            search_ledger_sha256="A" * 64,
            sources=(self.source(),),
            cards=cards,
            fallback_assessments=assessments,
        )

    def unresolved_assessments(
        self,
    ) -> tuple[phase_c1.PhaseC1AnnotationFallbackAssessmentV1, ...]:
        return tuple(
            phase_c1.PhaseC1AnnotationFallbackAssessmentV1(
                signal=signal,
                status="unresolved",
                material_evidence=(),
                preregistration_only=True,
                execution_authorized=False,
                reason_codes=("annotation_fallback_unresolved",),
            )
            for signal in EXPECTED_SIGNALS
        )

    def review_receipt(
        self, **overrides: object
    ) -> phase_c1.PhaseC1SourceReviewReceiptV1:
        values: dict[str, object] = {
            "protocol_sha256": hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            "search_ledger_sha256": "A" * 64,
            "source_evidence_ledger_sha256": "B" * 64,
            "transport_ledger_sha256": "C" * 64,
            "reviewed_transport_receipt_sha256s": (),
            "reviewed_document_sha256s": (),
            "review_scope": "all_transport_discovery_citation_source_cards_and_search_completeness",
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
        values.update(overrides)
        return phase_c1.PhaseC1SourceReviewReceiptV1(**values)  # type: ignore[arg-type]

    @staticmethod
    def canonical_dataclass_bytes(value: object, schema_version: str) -> bytes:
        def thaw(item: object) -> object:
            if is_dataclass(item):
                return {field.name: thaw(getattr(item, field.name)) for field in fields(item)}
            if isinstance(item, MappingProxyType) or isinstance(item, dict):
                return {str(key): thaw(entry) for key, entry in item.items()}
            if isinstance(item, tuple):
                return [thaw(entry) for entry in item]
            return item
        payload = thaw(value)
        self_payload = {"schema_version": schema_version, **payload}
        return phase_c1.canonical_json_bytes(self_payload)

    def coherent_inputs(
        self,
        *,
        search: phase_c1.PhaseC1SearchLedgerV1 | None = None,
        source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1 | None = None,
    ) -> tuple[
        phase_c1.PhaseC1SearchLedgerV1,
        phase_c1.PhaseC1SourceEvidenceLedgerV1,
        phase_c1.PhaseC1SourceReviewReceiptV1,
    ]:
        search = self.search_ledger() if search is None else search
        search_bytes = self.canonical_dataclass_bytes(
            search, "EmotionStatePhaseC1SearchLedgerV1"
        )
        source_ledger = self.source_ledger() if source_ledger is None else source_ledger
        source_ledger = replace(
            source_ledger, search_ledger_sha256=phase_c1.sha256_bytes(search_bytes)
        )
        source_bytes = self.canonical_dataclass_bytes(
            source_ledger, "EmotionStatePhaseC1SourceEvidenceLedgerV1"
        )
        protocol_bytes = self.canonical_dataclass_bytes(
            self.protocol, "EmotionStatePhaseC1DiscoveryProtocolV1"
        )
        review = self.review_receipt(
            protocol_sha256=phase_c1.sha256_bytes(protocol_bytes),
            search_ledger_sha256=phase_c1.sha256_bytes(search_bytes),
            source_evidence_ledger_sha256=phase_c1.sha256_bytes(source_bytes),
        )
        return search, source_ledger, review

    def validated_projection_inputs(
        self,
        *,
        admissible_signals: tuple[str, ...] = ("confusion",),
        unresolved_signals: tuple[str, ...] = (),
        alpha_rejecting_unresolved_case: str | None = None,
    ) -> tuple[
        phase_c1.PhaseC1SearchLedgerV1,
        phase_c1.PhaseC1SourceEvidenceLedgerV1,
        phase_c1.PhaseC1SourceReviewReceiptV1,
    ]:
        self.assertFalse(set(admissible_signals).intersection(unresolved_signals))
        self.assertIn(
            alpha_rejecting_unresolved_case,
            (
                None,
                "license_status",
                "annotation_modality",
                "observer_method",
                "adjudicated_only_human_label",
            ),
        )
        retained_signals = tuple(
            signal
            for signal in EXPECTED_SIGNALS
            if signal in admissible_signals or signal in unresolved_signals
        )
        search_payload = self.valid_search_ledger_payload()
        sources: list[dict[str, object]] = []
        cards: list[dict[str, object]] = []
        for source_number, signal in enumerate(retained_signals, start=1):
            source_id = f"c1-source-{source_number:04d}"
            document_id = f"c1-document-{source_number:04d}"
            query = next(
                record
                for record in search_payload["query_records"]
                if record["query_id"] == f"c1-query-{signal}-openalex-01"
            )
            discovery = self.discovery_record(
                query_id=query["query_id"],
                rank=1,
                record_number=source_number,
            )
            discovery["candidate_source_id"] = source_id
            query["discovery_records"] = [discovery]
            query["returned_count"] = 1
            query["result_count"] = 1
            search_payload["candidate_order_by_signal"][signal] = [source_id]

            source_payload = self.valid_source_payload()
            source_payload["source_id"] = source_id
            source_payload["documents"][0].update(
                {
                    "document_id": document_id,
                    "cached_sha256": self.fixture_hash(
                        f"source-document:{source_number}"
                    ),
                    "transport_receipt_sha256": self.fixture_hash(
                        f"source-transport:{source_number}"
                    ),
                }
            )
            if (
                signal == "confusion"
                and alpha_rejecting_unresolved_case == "license_status"
            ):
                source_payload["license_status"] = "unresolved"
            sources.append(source_payload)

            card_payload = self.valid_card_payload()
            card_payload.update(
                {
                    "card_id": f"c1-card-{signal}-0001",
                    "source_id": source_id,
                    "signal": signal,
                    "native_label": signal,
                    "native_definition_document_id": document_id,
                }
            )
            if signal in unresolved_signals:
                card_payload["reliability"]["verifiable"] = False
                card_payload["claimed_status"] = "unresolved"
                card_payload["claimed_reason_codes"] = [
                    "reliability_unverifiable"
                ]
            if signal == "confusion" and alpha_rejecting_unresolved_case is not None:
                card_payload["reliability"].update(
                    {
                        "point_micros": 650_000,
                        "lower_95_micros": 590_000,
                        "upper_95_micros": 669_999,
                    }
                )
                unresolved_reason = {
                    "license_status": "license_unresolved",
                    "annotation_modality": "source_documentation_incomplete",
                    "observer_method": "observer_method_unresolved",
                    "adjudicated_only_human_label": (
                        "reliability_not_preadjudication"
                    ),
                }[alpha_rejecting_unresolved_case]
                if alpha_rejecting_unresolved_case == "annotation_modality":
                    card_payload["annotation_modality"] = "unresolved"
                elif alpha_rejecting_unresolved_case == "observer_method":
                    card_payload["observer_method"] = "unresolved"
                elif (
                    alpha_rejecting_unresolved_case
                    == "adjudicated_only_human_label"
                ):
                    card_payload["observer_method"] = (
                        "adjudicated_only_human_label"
                    )
                card_payload["claimed_status"] = "unresolved"
                card_payload["claimed_reason_codes"] = [unresolved_reason]
            cards.append(card_payload)

        search = phase_c1.validate_search_ledger(search_payload, protocol=self.protocol)
        search_bytes = phase_c1.canonical_json_bytes(search_payload)
        source_payload = self.valid_source_evidence_ledger(search_bytes)
        source_payload["sources"] = sources
        source_payload["cards"] = cards
        for assessment in source_payload["fallback_assessments"]:
            assessment["status"] = "infeasible"
            assessment["reason_codes"] = []
        source_ledger = phase_c1.validate_source_evidence_ledger(
            source_payload, protocol=self.protocol, search_ledger_bytes=search_bytes
        )
        source_bytes = phase_c1.canonical_json_bytes(source_payload)
        review_payload = {
            "schema_version": "EmotionStatePhaseC1SourceReviewReceiptV1",
            "protocol_sha256": hashlib.sha256(self.protocol_path.read_bytes()).hexdigest().upper(),
            "search_ledger_sha256": phase_c1.sha256_bytes(search_bytes),
            "source_evidence_ledger_sha256": phase_c1.sha256_bytes(source_bytes),
            "transport_ledger_sha256": "D" * 64,
            "reviewed_transport_receipt_sha256s": list(phase_c1._review_transport_hashes(search_payload, source_ledger.sources)),
            "reviewed_document_sha256s": [document.cached_sha256 for source in source_ledger.sources for document in source.documents],
            "review_scope": "all_transport_discovery_citation_source_cards_and_search_completeness",
            "verdict": "admitted", "critical_findings": 0,
            "important_findings": 0, "minor_findings": 0,
            "raw_rows_read": False, "private_data_read": False,
            "model_evaluation_run": False, "provider_accessed": False,
            "runtime_modified": False,
        }
        review = phase_c1.validate_source_review_receipt(
            review_payload, protocol=self.protocol, search_ledger_bytes=search_bytes,
            source_evidence_ledger_bytes=source_bytes,
        )
        return search, source_ledger, review

    def validated_fallback_inputs(
        self,
        material_kinds: tuple[str, ...],
    ) -> tuple[
        phase_c1.PhaseC1SearchLedgerV1,
        phase_c1.PhaseC1SourceEvidenceLedgerV1,
    ]:
        search_payload = self.valid_search_ledger_payload()
        sources: list[dict[str, object]] = []
        materials: list[dict[str, object]] = []
        fallback_source_ids: list[str] = []
        fallback_queries = [
            record
            for record in search_payload["query_records"]
            if record["query_kind"] == "fallback_material"
        ]
        for source_number, kind in enumerate(material_kinds, start=1):
            source_id = f"c1-source-{source_number:04d}"
            document_id = f"c1-document-{source_number:04d}"
            fallback_source_ids.append(source_id)
            query = fallback_queries[source_number - 1]
            discovery = self.discovery_record(
                query_id=query["query_id"],
                rank=1,
                record_number=source_number,
            )
            discovery["candidate_source_id"] = source_id
            query["discovery_records"] = [discovery]
            query["returned_count"] = 1
            query["result_count"] = 1

            source_payload = self.valid_source_payload()
            source_payload["source_id"] = source_id
            source_payload["phase_c1_roles"] = ["fallback_material_candidate"]
            source_payload["documents"][0].update(
                {
                    "document_id": document_id,
                    "cached_sha256": self.fixture_hash(
                        f"fallback-document:{source_number}"
                    ),
                    "transport_receipt_sha256": self.fixture_hash(
                        f"fallback-transport:{source_number}"
                    ),
                }
            )
            sources.append(source_payload)

            material = self.valid_fallback_material()
            material["source_id"] = source_id
            if kind == "feasible":
                material.update(
                    {
                        "status": "feasible",
                        "public_spontaneous_material_status": "available",
                        "license_status": "compatible",
                        "ethical_use_status": "compatible",
                        "minimum_three_raters_status": "feasible",
                        "material_evidence_document_ids": [document_id],
                        "license_evidence_document_ids": [document_id],
                        "ethical_use_evidence_document_ids": [document_id],
                        "rater_feasibility_evidence_document_ids": [
                            document_id
                        ],
                    }
                )
            elif kind == "missing_evidence":
                material.update(
                    {
                        "status": "unresolved",
                        "public_spontaneous_material_status": "available",
                        "license_status": "compatible",
                        "ethical_use_status": "compatible",
                        "minimum_three_raters_status": "feasible",
                        "material_evidence_document_ids": [],
                        "license_evidence_document_ids": [document_id],
                        "ethical_use_evidence_document_ids": [document_id],
                        "rater_feasibility_evidence_document_ids": [
                            document_id
                        ],
                    }
                )
            elif kind == "infeasible":
                material.update(
                    {
                        "status": "infeasible",
                        "public_spontaneous_material_status": "unavailable",
                        "license_status": "compatible",
                        "ethical_use_status": "compatible",
                        "minimum_three_raters_status": "feasible",
                        "material_evidence_document_ids": [document_id],
                        "license_evidence_document_ids": [document_id],
                        "ethical_use_evidence_document_ids": [document_id],
                        "rater_feasibility_evidence_document_ids": [
                            document_id
                        ],
                    }
                )
            elif kind != "unresolved":
                self.fail(f"unknown fallback material kind: {kind}")
            materials.append(material)

        search_payload["fallback_material_candidate_order"] = (
            fallback_source_ids
        )
        search = phase_c1.validate_search_ledger(
            search_payload, protocol=self.protocol
        )
        search_bytes = phase_c1.canonical_json_bytes(search_payload)
        source_payload = self.valid_source_evidence_ledger(search_bytes)
        source_payload["sources"] = sources
        source_payload["cards"] = []
        assessment_status = (
            "feasible"
            if "feasible" in material_kinds
            else "infeasible"
            if all(kind == "infeasible" for kind in material_kinds)
            else "unresolved"
        )
        assessment_reasons = (
            ["annotation_fallback_feasible"]
            if assessment_status == "feasible"
            else []
            if assessment_status == "infeasible"
            else ["annotation_fallback_unresolved"]
        )
        for assessment in source_payload["fallback_assessments"]:
            assessment["status"] = assessment_status
            assessment["material_evidence"] = copy.deepcopy(materials)
            assessment["reason_codes"] = assessment_reasons
        source_ledger = phase_c1.validate_source_evidence_ledger(
            source_payload,
            protocol=self.protocol,
            search_ledger_bytes=search_bytes,
        )
        return search, source_ledger

    def test_alpha_rule_is_ordered_exhaustive_and_disjoint(self) -> None:
        cases = (
            (self.reliability(verifiable=False), "defer"),
            (self.reliability(published_positive_count=92, point_micros=900_000, lower_95_micros=850_000, upper_95_micros=930_000), "defer"),
            (self.reliability(point_micros=800_000, lower_95_micros=670_000, upper_95_micros=860_000), "pass"),
            (self.reliability(point_micros=650_000, lower_95_micros=590_000, upper_95_micros=669_999), "rejected"),
            (self.reliability(point_micros=650_000, lower_95_micros=550_000, upper_95_micros=750_000), "defer"),
        )
        self.assertEqual(
            tuple(
                decision.derive_reliability_status(
                    evidence, independent_rater_count=2, protocol=self.protocol
                )[0]
                for evidence, _ in cases
            ),
            tuple(expected for _, expected in cases),
        )

    def test_positive_support_boundary_matches_decimal_wilson_rule(self) -> None:
        rule = self.protocol.positive_support_rule
        with localcontext() as context:
            context.prec = 50
            scale = Decimal(int(self.protocol.reliability_scale))
            p = Decimal(int(rule["worst_case_probability_micros"])) / scale
            z = Decimal(int(rule["z_micros"])) / scale
            widths = {}
            for count in (92, 93):
                n = Decimal(count)
                denominator = Decimal(1) + (z * z / n)
                half_width = z * ((p * (Decimal(1) - p) / n + z * z / (Decimal(4) * n * n)).sqrt()) / denominator
                widths[count] = half_width * scale
        self.assertGreater(widths[92], Decimal(int(rule["max_half_width_micros"])))
        self.assertLessEqual(widths[93], Decimal(int(rule["max_half_width_micros"])))
        self.assertEqual(
            decision.derive_reliability_status(self.reliability(published_positive_count=92), independent_rater_count=2, protocol=self.protocol)[0],
            "defer",
        )
        self.assertEqual(
            decision.derive_reliability_status(self.reliability(published_positive_count=93), independent_rater_count=2, protocol=self.protocol)[0],
            "pass",
        )

    def test_known_rejection_precedes_unresolved_metadata(self) -> None:
        disposition = decision.derive_candidate_disposition(
            self.source(conversation_status="acted_or_scripted", license_status="unresolved"),
            replace(self.direct_card(), claimed_status="rejected", claimed_reason_codes=("acted_or_scripted",)),
            protocol=self.protocol,
        )
        self.assertEqual(disposition.status, "rejected")
        self.assertIn("acted_or_scripted", disposition.reason_codes)

    def test_candidate_derivation_covers_closed_rejections_and_defers(self) -> None:
        cases = (
            (self.source(access_status="login_required"), self.direct_card(claimed_status="rejected", claimed_reason_codes=("access_requires_login",)), "rejected", "access_requires_login"),
            (self.source(license_status="incompatible"), self.direct_card(claimed_status="rejected", claimed_reason_codes=("license_incompatible",)), "rejected", "license_incompatible"),
            (self.source(ethical_use_status="incompatible"), self.direct_card(claimed_status="rejected", claimed_reason_codes=("ethical_use_incompatible",)), "rejected", "ethical_use_incompatible"),
            (self.source(conversation_status="mixed_unseparated"), self.direct_card(claimed_status="rejected", claimed_reason_codes=("mixed_unseparated_conversation",)), "rejected", "mixed_unseparated_conversation"),
            (self.source(), self.direct_card(construct_correspondence="proxy_construct", claimed_status="rejected", claimed_reason_codes=("proxy_construct",)), "rejected", "proxy_construct"),
            (self.source(), self.direct_card(construct_correspondence="target_absent", claimed_status="rejected", claimed_reason_codes=("target_label_absent",)), "rejected", "target_label_absent"),
            (self.source(), self.direct_card(temporal_unit="conversation", claimed_status="rejected", claimed_reason_codes=("conversation_level_only",)), "rejected", "conversation_level_only"),
            (self.source(), self.direct_card(observer_method="self_report", claimed_status="rejected", claimed_reason_codes=("self_report_label",)), "rejected", "self_report_label"),
            (self.source(), self.direct_card(observer_method="llm_generated", claimed_status="rejected", claimed_reason_codes=("llm_generated_label",)), "rejected", "llm_generated_label"),
            (self.source(access_status="unresolved"), replace(self.direct_card(), claimed_status="unresolved", claimed_reason_codes=("access_unresolved",)), "unresolved", "access_unresolved"),
            (self.source(), self.direct_card(annotation_modality="unresolved", claimed_status="unresolved", claimed_reason_codes=("source_documentation_incomplete",)), "unresolved", "source_documentation_incomplete"),
            (self.source(), self.direct_card(observer_method="adjudicated_only_human_label", claimed_status="unresolved", claimed_reason_codes=("reliability_not_preadjudication",)), "unresolved", "reliability_not_preadjudication"),
        )
        for source, card, status, reason in cases:
            with self.subTest(reason=reason):
                actual = decision.derive_candidate_disposition(source, card, protocol=self.protocol)
                self.assertEqual((actual.status, actual.reason_codes), (status, (reason,)))

    def test_candidate_reason_table_covers_remaining_observable_frozen_codes(self) -> None:
        unresolved_card = replace(self.direct_card(), claimed_status="unresolved")
        cases = (
            (self.source(access_status="restricted"), self.direct_card(), "rejected", ("access_restricted",)),
            (self.source(), replace(self.direct_card(), temporal_unit="other"), "rejected", ("temporal_unit_incompatible",)),
            (self.source(), replace(self.direct_card(), independent_rater_count=1), "rejected", ("single_rater",)),
            (self.source(license_status="unresolved"), unresolved_card, "unresolved", ("license_unresolved",)),
            (self.source(ethical_use_status="unresolved"), unresolved_card, "unresolved", ("ethical_use_unresolved",)),
            (self.source(conversation_status="unresolved"), unresolved_card, "unresolved", ("conversation_status_unresolved",)),
            (self.source(), replace(unresolved_card, construct_correspondence="unresolved"), "unresolved", ("directness_unresolved",)),
            (self.source(), replace(unresolved_card, temporal_unit="unresolved"), "unresolved", ("temporal_unit_unresolved",)),
            (self.source(), replace(unresolved_card, observer_method="unresolved"), "unresolved", ("observer_method_unresolved",)),
            (self.source(), replace(unresolved_card, independent_rater_count=None), "unresolved", ("rater_count_unresolved",)),
            (self.source(), replace(unresolved_card, reliability=replace(self.reliability(), verifiable=False)), "unresolved", ("reliability_unverifiable",)),
            (self.source(), replace(unresolved_card, reliability=replace(self.reliability(), published_positive_count=92)), "unresolved", ("reliability_effective_sample_insufficient", "positive_support_below_93")),
        )
        for source, card, status, reasons in cases:
            with self.subTest(reasons=reasons):
                actual = decision.derive_candidate_disposition(source, card, protocol=self.protocol)
                self.assertEqual((actual.status, actual.reason_codes), (status, reasons))

    def test_reliability_missing_and_boundary_cases_are_unresolved_or_rejected(self) -> None:
        cases = (
            (self.reliability(published_positive_count=None), "defer", ("reliability_effective_sample_insufficient", "published_positive_count_missing")),
            (self.reliability(point_micros=800_000, lower_95_micros=None, upper_95_micros=900_000), "defer", ("reliability_interval_uncertain",)),
            (self.reliability(point_micros=800_000, lower_95_micros=669_999, upper_95_micros=900_000), "defer", ("reliability_interval_uncertain",)),
            (self.reliability(point_micros=650_000, lower_95_micros=590_000, upper_95_micros=670_000), "defer", ("reliability_interval_uncertain",)),
            (self.reliability(point_micros=650_000, lower_95_micros=590_000, upper_95_micros=669_999), "rejected", ("reliability_upper_below_0_67",)),
        )
        for evidence, expected_status, expected_reasons in cases:
            with self.subTest(evidence=evidence):
                self.assertEqual(
                    decision.derive_reliability_status(evidence, independent_rater_count=2, protocol=self.protocol),
                    (expected_status, expected_reasons),
                )

    def test_unapproved_metric_and_postadjudication_evidence_defer(self) -> None:
        unapproved = replace(self.reliability(), metric_id="cohen_kappa")
        self.assertEqual(
            decision.derive_reliability_status(
                unapproved, independent_rater_count=2, protocol=self.protocol
            ),
            ("defer", ("reliability_metric_unapproved",)),
        )
        postadjudication = replace(self.direct_card(), reliability=replace(self.reliability(), preadjudication=False))
        disposition = decision.derive_candidate_disposition(
            self.source(), postadjudication, protocol=self.protocol
        )
        self.assertEqual(
            (disposition.status, disposition.reason_codes),
            ("unresolved", ("reliability_not_preadjudication",)),
        )

    def test_disengagement_native_label_cannot_relabel_refusal_or_dnc(self) -> None:
        payload = self.valid_card_payload()
        payload.update(
            {
                "card_id": "c1-card-disengagement-0001",
                "signal": "disengagement",
                "native_label": "do not call",
            }
        )
        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError,
            "native_disengagement_label_protected_intent",
        ):
            phase_c1.parse_evidence_card(payload)

    def test_one_pass_only_admits_that_signal_to_c2(self) -> None:
        search, source_ledger, review = self.validated_projection_inputs()
        projection = decision.project_phase_c1_admission(
            protocol=self.protocol, search_ledger=search,
            source_ledger=source_ledger, review_receipt=review,
        )
        self.assertEqual(projection.overall_decision, "proceed_partial_to_c2")
        self.assertEqual(projection.c2_eligible_signals, ("confusion",))

    def test_projection_binds_exact_canonical_input_hashes(self) -> None:
        search, source_ledger, review = self.coherent_inputs()
        for field, code in (
            ("protocol_sha256", "decision_protocol_hash_mismatch"),
            ("search_ledger_sha256", "decision_search_hash_mismatch"),
            ("source_evidence_ledger_sha256", "decision_source_hash_mismatch"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, code):
                    decision.project_phase_c1_admission(
                        protocol=self.protocol,
                        search_ledger=search,
                        source_ledger=source_ledger,
                        review_receipt=replace(review, **{field: "F" * 64}),
                    )

    def test_validator_produced_88_query_inputs_project_partial_and_preserve_inputs(self) -> None:
        search, source_ledger, review = self.validated_projection_inputs()
        before = (
            self.canonical_dataclass_bytes(self.protocol, "EmotionStatePhaseC1DiscoveryProtocolV1"),
            self.canonical_dataclass_bytes(search, "EmotionStatePhaseC1SearchLedgerV1"),
            self.canonical_dataclass_bytes(source_ledger, "EmotionStatePhaseC1SourceEvidenceLedgerV1"),
            repr((self.protocol, search, source_ledger, review)),
            (id(self.protocol), id(search), id(source_ledger), id(review)),
        )
        projection = decision.project_phase_c1_admission(
            protocol=self.protocol, search_ledger=search,
            source_ledger=source_ledger, review_receipt=review,
        )
        self.assertEqual(
            (projection.overall_decision, projection.c2_eligible_signals),
            ("proceed_partial_to_c2", ("confusion",)),
        )
        self.assertEqual(
            before,
            (
                self.canonical_dataclass_bytes(self.protocol, "EmotionStatePhaseC1DiscoveryProtocolV1"),
                self.canonical_dataclass_bytes(search, "EmotionStatePhaseC1SearchLedgerV1"),
                self.canonical_dataclass_bytes(source_ledger, "EmotionStatePhaseC1SourceEvidenceLedgerV1"),
                repr((self.protocol, search, source_ledger, review)),
                (id(self.protocol), id(search), id(source_ledger), id(review)),
            ),
        )

    def test_validator_produced_inputs_cover_all_four_overall_decisions(self) -> None:
        cases = (
            (
                EXPECTED_SIGNALS,
                (),
                "proceed_full_to_c2",
                EXPECTED_SIGNALS,
            ),
            (
                ("confusion",),
                (),
                "proceed_partial_to_c2",
                ("confusion",),
            ),
            (
                (),
                ("confusion",),
                "defer_c2",
                (),
            ),
            (
                (),
                (),
                "stop_c2",
                (),
            ),
        )
        for admissible, unresolved, expected, eligible in cases:
            with self.subTest(expected=expected):
                search, source_ledger, review = self.validated_projection_inputs(
                    admissible_signals=admissible,
                    unresolved_signals=unresolved,
                )
                self.assertEqual(len(search.query_records), 88)
                projection = decision.project_phase_c1_admission(
                    protocol=self.protocol,
                    search_ledger=search,
                    source_ledger=source_ledger,
                    review_receipt=review,
                )
                self.assertEqual(
                    (projection.overall_decision, projection.c2_eligible_signals),
                    (expected, eligible),
                )

    def test_validator_produced_unresolved_card_alone_blocks_signal_fail(self) -> None:
        search, source_ledger, review = self.validated_projection_inputs(
            admissible_signals=(),
            unresolved_signals=("confusion",),
        )
        projection = decision.project_phase_c1_admission(
            protocol=self.protocol,
            search_ledger=search,
            source_ledger=source_ledger,
            review_receipt=review,
        )
        confusion = next(
            row for row in projection.signal_decisions
            if row.signal == "confusion"
        )
        self.assertEqual(
            (
                confusion.decision,
                confusion.unresolved_card_count,
                confusion.annotation_fallback,
            ),
            ("defer", 1, "infeasible"),
        )

    def test_mandatory_unresolved_eligibility_precedes_alpha_rejection(self) -> None:
        expected_reason_by_case = {
            "license_status": "license_unresolved",
            "annotation_modality": "source_documentation_incomplete",
            "observer_method": "observer_method_unresolved",
            "adjudicated_only_human_label": "reliability_not_preadjudication",
        }
        for case, expected_reason in expected_reason_by_case.items():
            with self.subTest(case=case):
                search, source_ledger, review = self.validated_projection_inputs(
                    admissible_signals=("confusion",),
                    alpha_rejecting_unresolved_case=case,
                )
                self.assertEqual(len(search.query_records), 88)
                card = source_ledger.cards[0]
                self.assertEqual(card.reliability.upper_95_micros, 669_999)
                projection = decision.project_phase_c1_admission(
                    protocol=self.protocol,
                    search_ledger=search,
                    source_ledger=source_ledger,
                    review_receipt=review,
                )
                disposition = projection.candidate_dispositions[0]
                confusion = next(
                    row
                    for row in projection.signal_decisions
                    if row.signal == "confusion"
                )
                self.assertEqual(
                    (disposition.status, disposition.reason_codes),
                    ("unresolved", (expected_reason,)),
                )
                self.assertEqual(
                    (
                        confusion.decision,
                        confusion.unresolved_card_count,
                        projection.overall_decision,
                    ),
                    ("defer", 1, "defer_c2"),
                )

    def test_valid_feasible_preregistered_fallback_defers_and_never_passes(self) -> None:
        search, source_ledger = self.validated_fallback_inputs(("feasible",))
        assessment = source_ledger.fallback_assessments[0]
        result = decision.derive_signal_decision(
            "hesitation",
            (),
            {},
            search_ledger=search,
            source_ledger=source_ledger,
        )
        self.assertEqual(
            (
                assessment.preregistration_only,
                assessment.execution_authorized,
                result.annotation_fallback,
                result.decision,
                result.c2_eligible,
            ),
            (True, False, "feasible", "defer", False),
        )

    def test_valid_unresolved_fallback_defers(self) -> None:
        search, source_ledger = self.validated_fallback_inputs(
            ("unresolved",)
        )
        result = decision.derive_signal_decision(
            "hesitation",
            (),
            {},
            search_ledger=search,
            source_ledger=source_ledger,
        )
        self.assertEqual(
            (result.annotation_fallback, result.decision),
            ("unresolved", "defer"),
        )

    def test_missing_fallback_evidence_material_is_unresolved_and_defers(self) -> None:
        search, source_ledger = self.validated_fallback_inputs(
            ("missing_evidence",)
        )
        material = (
            source_ledger.fallback_assessments[0].material_evidence[0]
        )
        result = decision.derive_signal_decision(
            "hesitation",
            (),
            {},
            search_ledger=search,
            source_ledger=source_ledger,
        )
        self.assertEqual(material.material_evidence_document_ids, ())
        self.assertEqual(
            (material.status, result.annotation_fallback, result.decision),
            ("unresolved", "unresolved", "defer"),
        )

    def test_one_unresolved_fallback_material_among_infeasible_materials_defers(self) -> None:
        search, source_ledger = self.validated_fallback_inputs(
            ("infeasible", "unresolved")
        )
        assessment = source_ledger.fallback_assessments[0]
        result = decision.derive_signal_decision(
            "hesitation",
            (),
            {},
            search_ledger=search,
            source_ledger=source_ledger,
        )
        self.assertEqual(
            tuple(material.status for material in assessment.material_evidence),
            ("infeasible", "unresolved"),
        )
        self.assertEqual(
            (result.annotation_fallback, result.decision),
            ("unresolved", "defer"),
        )

    def test_cross_source_fallback_document_has_exact_decision_error(self) -> None:
        search, source_ledger = self.validated_fallback_inputs(
            ("feasible", "feasible")
        )
        assessment = source_ledger.fallback_assessments[0]
        wrong_source_document_id = (
            source_ledger.sources[1].documents[0].document_id
        )
        materials = (
            replace(
                assessment.material_evidence[0],
                material_evidence_document_ids=(
                    wrong_source_document_id,
                ),
            ),
            assessment.material_evidence[1],
        )
        assessments = (
            replace(assessment, material_evidence=materials),
            *source_ledger.fallback_assessments[1:],
        )
        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError,
            "fallback_fact_document_wrong_source",
        ):
            decision.derive_signal_decision(
                "hesitation",
                (),
                {},
                search_ledger=search,
                source_ledger=replace(
                    source_ledger,
                    fallback_assessments=assessments,
                ),
            )

    def test_each_search_guard_individually_blocks_signal_fail(self) -> None:
        search, source_ledger, _ = self.validated_projection_inputs(
            admissible_signals=()
        )
        baseline = decision.derive_signal_decision(
            "hesitation",
            (),
            {},
            search_ledger=search,
            source_ledger=source_ledger,
        )
        self.assertEqual(baseline.decision, "fail")
        query_index = next(
            index
            for index, query in enumerate(search.query_records)
            if query.signal == "hesitation"
        )
        query = search.query_records[query_index]

        incomplete_query = replace(
            query,
            status="incomplete",
            incomplete_reason="rate_limit_pressure",
            response_sha256=None,
            response_byte_count=None,
        )
        truncated_query = replace(
            query,
            result_count=1,
            truncated=True,
        )

        def with_query(
            replacement: phase_c1.PhaseC1QueryRecordV1,
        ) -> phase_c1.PhaseC1SearchLedgerV1:
            return replace(
                search,
                query_records=(
                    search.query_records[:query_index]
                    + (replacement,)
                    + search.query_records[query_index + 1 :]
                ),
            )

        cases: tuple[
            tuple[
                str,
                phase_c1.PhaseC1SearchLedgerV1,
                Callable[[phase_c1.PhaseC1SearchLedgerV1], bool],
            ],
            ...,
        ] = (
            (
                "search_query_incomplete",
                with_query(incomplete_query),
                lambda item: item.query_records[query_index].status
                == "incomplete",
            ),
            (
                "query_result_truncated",
                with_query(truncated_query),
                lambda item: item.query_records[query_index].truncated,
            ),
            (
                "candidate_overflow",
                replace(
                    search,
                    overflow_count_by_signal=MappingProxyType(
                        {
                            signal: (
                                1 if signal == "hesitation" else 0
                            )
                            for signal in EXPECTED_SIGNALS
                        }
                    ),
                ),
                lambda item: item.overflow_count_by_signal["hesitation"]
                == 1,
            ),
            (
                "fallback_material_overflow",
                replace(search, fallback_material_overflow_count=1),
                lambda item: item.fallback_material_overflow_count == 1,
            ),
            (
                "citation_budget_incomplete_backward_budget_reached",
                replace(
                    search,
                    backward_citation_stop_by_signal=MappingProxyType(
                        {
                            signal: (
                                "budget_reached"
                                if signal == "hesitation"
                                else "source_list_exhausted"
                            )
                            for signal in EXPECTED_SIGNALS
                        }
                    ),
                ),
                lambda item: item.backward_citation_stop_by_signal[
                    "hesitation"
                ]
                == "budget_reached",
            ),
            (
                "citation_budget_incomplete_forward_budget_reached",
                replace(
                    search,
                    forward_citation_stop_by_signal=MappingProxyType(
                        {
                            signal: (
                                "budget_reached"
                                if signal == "hesitation"
                                else "source_list_exhausted"
                            )
                            for signal in EXPECTED_SIGNALS
                        }
                    ),
                ),
                lambda item: item.forward_citation_stop_by_signal[
                    "hesitation"
                ]
                == "budget_reached",
            ),
            (
                "citation_budget_incomplete_backward_incomplete",
                replace(
                    search,
                    backward_citation_stop_by_signal=MappingProxyType(
                        {
                            signal: (
                                "incomplete"
                                if signal == "hesitation"
                                else "source_list_exhausted"
                            )
                            for signal in EXPECTED_SIGNALS
                        }
                    ),
                ),
                lambda item: item.backward_citation_stop_by_signal[
                    "hesitation"
                ]
                == "incomplete",
            ),
            (
                "citation_budget_incomplete_forward_incomplete",
                replace(
                    search,
                    forward_citation_stop_by_signal=MappingProxyType(
                        {
                            signal: (
                                "incomplete"
                                if signal == "hesitation"
                                else "source_list_exhausted"
                            )
                            for signal in EXPECTED_SIGNALS
                        }
                    ),
                ),
                lambda item: item.forward_citation_stop_by_signal[
                    "hesitation"
                ]
                == "incomplete",
            ),
        )
        for reason, guarded_search, cause_is_present in cases:
            with self.subTest(reason=reason):
                result = decision.derive_signal_decision(
                    "hesitation",
                    (),
                    {},
                    search_ledger=guarded_search,
                    source_ledger=source_ledger,
                )
                self.assertEqual(
                    (reason, cause_is_present(guarded_search), result.decision),
                    (reason, True, "defer"),
                )

    def test_coherent_review_verdict_findings_and_boundary_precede_projection(self) -> None:
        search, source_ledger, review = self.validated_projection_inputs()
        for mutation in (
            {"verdict": "pending"}, {"verdict": "blocked"},
            {"critical_findings": 1}, {"important_findings": 1},
            {"minor_findings": 1}, {"private_data_read": True},
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "decision_review_binding"):
                    decision.project_phase_c1_admission(
                        protocol=self.protocol, search_ledger=search,
                        source_ledger=source_ledger,
                        review_receipt=replace(review, **mutation),
                    )

    def test_candidate_requires_same_source_authoritative_public_definition(self) -> None:
        card = self.direct_card()
        missing_definition = replace(card, native_definition_document_id="c1-document-9999")
        with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "native_definition_document_missing"):
            decision.derive_candidate_disposition(self.source(), missing_definition, protocol=self.protocol)
        document = self.source().documents[0]
        non_authoritative_source = replace(
            self.source(), documents=(replace(document, authoritative=False),)
        )
        disposition = decision.derive_candidate_disposition(
            non_authoritative_source, card, protocol=self.protocol
        )
        self.assertEqual(
            (disposition.status, disposition.reason_codes),
            ("unresolved", ("authoritative_provenance_unverified",)),
        )

    def test_authoritative_direct_definition_does_not_require_lexical_signal_label(self) -> None:
        card = replace(
            self.direct_card(), native_label="perceived difficulty understanding"
        )
        self.assertEqual(
            decision.derive_candidate_disposition(
                self.source(), card, protocol=self.protocol
            ),
            decision.PhaseC1CandidateDispositionV1(
                card.card_id, "admissible", ()
            ),
        )

    def test_native_label_matching_frozen_excluded_proxy_is_rejected(self) -> None:
        card = replace(self.direct_card(), native_label="ambiguity")
        self.assertEqual(
            decision.derive_candidate_disposition(
                self.source(), card, protocol=self.protocol
            ),
            decision.PhaseC1CandidateDispositionV1(
                card.card_id, "rejected", ("proxy_construct",)
            ),
        )

    def test_candidate_source_id_and_fallback_document_lineage_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError, "source_reference_missing"
        ):
            decision.derive_candidate_disposition(
                replace(self.source(), source_id="c1-source-0002"),
                self.direct_card(),
                protocol=self.protocol,
            )
        source = self.source()
        material = phase_c1.PhaseC1FallbackMaterialEvidenceV1(
            source_id=source.source_id,
            status="unresolved",
            public_spontaneous_material_status="available",
            license_status="compatible",
            ethical_use_status="compatible",
            minimum_three_raters_status="feasible",
            material_evidence_document_ids=("c1-document-9999",),
            license_evidence_document_ids=("c1-document-0001",),
            ethical_use_evidence_document_ids=("c1-document-0001",),
            rater_feasibility_evidence_document_ids=("c1-document-0001",),
        )
        assessments = tuple(
            phase_c1.PhaseC1AnnotationFallbackAssessmentV1(
                signal=signal, status="unresolved", material_evidence=(material,),
                preregistration_only=True, execution_authorized=False,
                reason_codes=("annotation_fallback_unresolved",),
            )
            for signal in EXPECTED_SIGNALS
        )
        search = replace(
            self.search_ledger(),
            fallback_material_candidate_order=(source.source_id,),
        )
        source_ledger = replace(
            self.source_ledger(assessments=assessments), sources=(source,)
        )
        with self.assertRaisesRegex(
            phase_c1.PhaseC1ContractError, "fallback_fact_document_unknown"
        ):
            decision.derive_signal_decision(
                "hesitation", (), {},
                search_ledger=search, source_ledger=source_ledger,
            )

    def test_fallback_material_claim_and_disposition_coverage_fail_closed(self) -> None:
        source = self.source()
        material = phase_c1.PhaseC1FallbackMaterialEvidenceV1(
            source_id=source.source_id,
            status="infeasible",
            public_spontaneous_material_status="available",
            license_status="compatible",
            ethical_use_status="compatible",
            minimum_three_raters_status="feasible",
            material_evidence_document_ids=("c1-document-0001",),
            license_evidence_document_ids=("c1-document-0001",),
            ethical_use_evidence_document_ids=("c1-document-0001",),
            rater_feasibility_evidence_document_ids=("c1-document-0001",),
        )
        assessments = tuple(
            phase_c1.PhaseC1AnnotationFallbackAssessmentV1(
                signal=signal, status="feasible", material_evidence=(material,),
                preregistration_only=True, execution_authorized=False,
                reason_codes=("annotation_fallback_feasible",),
            )
            for signal in EXPECTED_SIGNALS
        )
        search = replace(self.search_ledger(), fallback_material_candidate_order=(source.source_id,))
        source_ledger = replace(self.source_ledger(assessments=assessments), sources=(source,))
        with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "fallback_material_status_mismatch"):
            decision.derive_signal_decision("hesitation", (), {}, search_ledger=search, source_ledger=source_ledger)
        admissible = self.direct_card()
        with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "candidate_card_missing_or_duplicate"):
            decision.derive_signal_decision(
                "confusion", (), {admissible.card_id: admissible},
                search_ledger=self.search_ledger(), source_ledger=self.source_ledger(),
            )

    def test_fail_guards_and_protected_intent_cover_reviewed_bypasses(self) -> None:
        payload = self.valid_card_payload()
        payload.update({"card_id": "c1-card-disengagement-0001", "signal": "disengagement"})
        for native_label in ("do not call", "please don't call again", "do—not_call", "DNC", "refused", "stop calling"):
            with self.subTest(native_label=native_label):
                payload["native_label"] = native_label
                with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "native_disengagement_label_protected_intent"):
                    phase_c1.parse_evidence_card(payload)
        search = replace(self.search_ledger(), overflow_count_by_signal=MappingProxyType({signal: 1 if signal == "hesitation" else 0 for signal in EXPECTED_SIGNALS}))
        result = decision.derive_signal_decision("hesitation", (), {}, search_ledger=search, source_ledger=self.source_ledger())
        self.assertEqual(result.decision, "defer")

    def test_incomplete_query_citation_and_unapproved_fallback_block_fail(self) -> None:
        incomplete = phase_c1.PhaseC1QueryRecordV1(
            query_id="c1-query-hesitation-openalex-01",
            query_kind="direct_label_source", channel_id="openalex",
            signal="hesitation", query_text="synthetic", status="incomplete",
            incomplete_reason="network_error", result_limit=25,
            response_sha256=None, response_byte_count=None,
            transport_receipt_sha256="A" * 64, result_count=0,
            returned_count=0, truncated=False, discovery_records=(),
        )
        search = replace(
            self.search_ledger(), query_records=(incomplete,),
            backward_citation_stop_by_signal=MappingProxyType(
                {signal: "budget_reached" if signal == "hesitation" else "source_list_exhausted" for signal in EXPECTED_SIGNALS}
            ),
        )
        self.assertEqual(
            decision.derive_signal_decision(
                "hesitation", (), {}, search_ledger=search,
                source_ledger=self.source_ledger(),
            ).decision,
            "defer",
        )
        unapproved = phase_c1.PhaseC1AnnotationFallbackAssessmentV1(
            signal="hesitation", status="infeasible", material_evidence=(),
            preregistration_only=False, execution_authorized=True,
            reason_codes=(),
        )
        assessments = (unapproved,) + tuple(
            phase_c1.PhaseC1AnnotationFallbackAssessmentV1(
                signal=signal, status="infeasible", material_evidence=(),
                preregistration_only=True, execution_authorized=False,
                reason_codes=(),
            )
            for signal in EXPECTED_SIGNALS[1:]
        )
        with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "fallback_authorization"):
            decision.derive_signal_decision(
                "hesitation", (), {}, search_ledger=self.search_ledger(),
                source_ledger=self.source_ledger(assessments=assessments),
            )

    def test_card_claim_mismatch_and_input_immutability_fail_closed(self) -> None:
        card = replace(self.direct_card(), claimed_status="unresolved", claimed_reason_codes=())
        search, source_ledger, review = self.coherent_inputs(
            search=self.search_ledger(candidate_signals=("confusion",)),
            source_ledger=self.source_ledger((card,)),
        )
        before = repr((self.protocol, search, source_ledger, review))
        with self.assertRaisesRegex(phase_c1.PhaseC1ContractError, "card_claim_mismatch"):
            decision.project_phase_c1_admission(
                protocol=self.protocol, search_ledger=search,
                source_ledger=source_ledger, review_receipt=review,
            )
        self.assertEqual(before, repr((self.protocol, search, source_ledger, review)))


class PhaseC1AggregateRunnerTests(_PhaseC1FixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.source_ledger_bytes_by_sha256: dict[str, bytes] = {}
        self.projected_aggregate_sha256s: set[str] = set()
        self.authority_bytes_by_sha256: dict[str, dict[str, bytes]] = {
            "protocol_bytes": {},
            "search_ledger_bytes": {},
            "source_ledger_bytes": {},
            "review_receipt_bytes": {},
        }
        self.protocol_bytes = self.protocol_path.read_bytes()
        self.protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        (
            self.search_bytes,
            self.one_pass_source_bytes,
            self.review_bytes_for_one_pass,
        ) = self.validated_input_bytes(admissible_signals=("confusion",))

    def build_result(self, **kwargs: object) -> dict[str, object]:
        source_ledger_bytes = kwargs["source_ledger_bytes"]
        self.assertIsInstance(source_ledger_bytes, bytes)
        result = runner.build_phase_c1_result(**kwargs)
        self.projected_aggregate_sha256s.add(
            result["aggregate_content_sha256"]
        )
        for argument_name in self.authority_bytes_by_sha256:
            authority_bytes = kwargs[argument_name]
            self.assertIsInstance(authority_bytes, bytes)
            self.authority_bytes_by_sha256[argument_name][
                phase_c1.sha256_bytes(authority_bytes)
            ] = authority_bytes
        self.source_ledger_bytes_by_sha256[
            phase_c1.sha256_bytes(source_ledger_bytes)
        ] = source_ledger_bytes
        return result

    def authoritative_input_bytes_for(
        self,
        payload: dict[str, object],
    ) -> dict[str, bytes]:
        result_fields = {
            "protocol_bytes": "protocol_sha256",
            "search_ledger_bytes": "search_ledger_sha256",
            "source_ledger_bytes": "source_evidence_ledger_sha256",
            "review_receipt_bytes": "source_review_receipt_sha256",
        }
        return {
            argument_name: self.authority_bytes_by_sha256[argument_name][
                payload[result_field]
            ]
            for argument_name, result_field in result_fields.items()
        }

    def source_ledger_bytes_for(
        self,
        payload: dict[str, object],
    ) -> bytes:
        digest = payload["source_evidence_ledger_sha256"]
        self.assertIsInstance(digest, str)
        return self.source_ledger_bytes_by_sha256[digest]

    def validate_result(self, payload: dict[str, object]) -> None:
        if (
            payload["aggregate_content_sha256"]
            not in self.projected_aggregate_sha256s
        ):
            self.validate_local_result(payload)
            return
        authority_bytes = self.authoritative_input_bytes_for(payload)
        runner.validate_phase_c1_result_payload(
            payload,
            **authority_bytes,
        )

    def render_result(self, payload: dict[str, object]) -> bytes:
        if (
            payload["aggregate_content_sha256"]
            not in self.projected_aggregate_sha256s
        ):
            return self.render_local_result(payload)
        authority_bytes = self.authoritative_input_bytes_for(payload)
        return runner.render_phase_c1_report(
            payload,
            **authority_bytes,
        )

    def validate_local_result(self, payload: dict[str, object]) -> None:
        runner._validate_phase_c1_result_local(
            payload,
            source_ledger_bytes=self.source_ledger_bytes_for(payload),
        )

    def render_local_result(self, payload: dict[str, object]) -> bytes:
        return runner._render_phase_c1_report_local(
            payload,
            source_ledger_bytes=self.source_ledger_bytes_for(payload),
        )

    def assert_projection_rejected(
        self,
        payload: dict[str, object],
        *,
        authority_bytes: dict[str, bytes],
    ) -> None:
        self.reself(payload)
        for validate in (
            runner.validate_phase_c1_result_payload,
            runner.render_phase_c1_report,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaises(runner.RunnerError):
                    validate(
                        copy.deepcopy(payload),
                        **authority_bytes,
                    )

    def valid_card_payload(self) -> dict[str, object]:
        payload = _PhaseC1FixtureMixin.valid_card_payload()
        reliability = payload["reliability"]
        self.assertIsInstance(reliability, dict)
        reliability["uncertain_or_unratable_rate_micros"] = None
        return payload

    @staticmethod
    def canonical_dataclass_bytes(
        value: object,
        schema_version: str,
    ) -> bytes:
        return PhaseC1DecisionTests.canonical_dataclass_bytes(
            value,
            schema_version,
        )

    def validated_input_bytes(
        self,
        *,
        admissible_signals: tuple[str, ...] = (),
        unresolved_signals: tuple[str, ...] = (),
    ) -> tuple[bytes, bytes, bytes]:
        search, source_ledger, review = (
            PhaseC1DecisionTests.validated_projection_inputs(
                self,
                admissible_signals=admissible_signals,
                unresolved_signals=unresolved_signals,
            )
        )
        return (
            self.canonical_dataclass_bytes(
                search,
                "EmotionStatePhaseC1SearchLedgerV1",
            ),
            self.canonical_dataclass_bytes(
                source_ledger,
                "EmotionStatePhaseC1SourceEvidenceLedgerV1",
            ),
            self.canonical_dataclass_bytes(
                review,
                "EmotionStatePhaseC1SourceReviewReceiptV1",
            ),
        )

    def valid_result(self) -> dict[str, object]:
        return self.build_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=self.search_bytes,
            source_ledger_bytes=self.one_pass_source_bytes,
            review_receipt_bytes=self.review_bytes_for_one_pass,
        )

    def deferred_result(self) -> dict[str, object]:
        search_bytes, source_bytes, review_bytes = self.validated_input_bytes(
            unresolved_signals=("confusion",)
        )
        return self.build_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=search_bytes,
            source_ledger_bytes=source_bytes,
            review_receipt_bytes=review_bytes,
        )

    def all_fail_result(self) -> dict[str, object]:
        search_bytes, source_bytes, review_bytes = self.validated_input_bytes()
        return self.build_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=search_bytes,
            source_ledger_bytes=source_bytes,
            review_receipt_bytes=review_bytes,
        )

    def full_pass_result(self) -> dict[str, object]:
        search_bytes, source_bytes, review_bytes = self.validated_input_bytes(
            admissible_signals=EXPECTED_SIGNALS,
        )
        return self.build_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=search_bytes,
            source_ledger_bytes=source_bytes,
            review_receipt_bytes=review_bytes,
        )

    def fallback_result(
        self,
        material_kinds: tuple[str, ...],
    ) -> dict[str, object]:
        search, source_ledger = (
            PhaseC1DecisionTests.validated_fallback_inputs(
                self,
                material_kinds,
            )
        )
        search_bytes = self.canonical_dataclass_bytes(
            search,
            "EmotionStatePhaseC1SearchLedgerV1",
        )
        source_ledger = replace(
            source_ledger,
            search_ledger_sha256=phase_c1.sha256_bytes(search_bytes),
        )
        source_bytes = self.canonical_dataclass_bytes(
            source_ledger,
            "EmotionStatePhaseC1SourceEvidenceLedgerV1",
        )
        search_payload = phase_c1.load_json_strict(
            search_bytes,
            source="search",
        )
        review_payload = {
            "schema_version": "EmotionStatePhaseC1SourceReviewReceiptV1",
            "protocol_sha256": phase_c1.sha256_bytes(self.protocol_bytes),
            "search_ledger_sha256": phase_c1.sha256_bytes(search_bytes),
            "source_evidence_ledger_sha256": phase_c1.sha256_bytes(
                source_bytes
            ),
            "transport_ledger_sha256": "D" * 64,
            "reviewed_transport_receipt_sha256s": list(
                phase_c1._review_transport_hashes(
                    search_payload,
                    source_ledger.sources,
                )
            ),
            "reviewed_document_sha256s": [
                document.cached_sha256
                for source in source_ledger.sources
                for document in source.documents
            ],
            "review_scope": (
                "all_transport_discovery_citation_source_cards_and_"
                "search_completeness"
            ),
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
        return self.build_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=search_bytes,
            source_ledger_bytes=source_bytes,
            review_receipt_bytes=phase_c1.canonical_json_bytes(
                review_payload
            ),
        )

    @staticmethod
    def reself(payload: dict[str, object]) -> None:
        payload["aggregate_content_sha256"] = ""
        encoded = (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        payload["aggregate_content_sha256"] = hashlib.sha256(
            encoded
        ).hexdigest().upper()

    @staticmethod
    def rehash_source_signature(
        payload: dict[str, object],
        entry: dict[str, object],
    ) -> None:
        old_digest = entry["source_signature_sha256"]
        signature = {
            key: value
            for key, value in entry.items()
            if key not in {"source_signature_sha256", "count"}
        }
        new_digest = phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(signature)
        )
        entry["source_signature_sha256"] = new_digest
        for item in payload["per_signal"]:
            for diagnostic in item["reliability_diagnostics"]:
                if diagnostic["source_signature_sha256"] == old_digest:
                    diagnostic["source_signature_sha256"] = new_digest
        payload["source_signature_counts"].sort(
            key=lambda item: item["source_signature_sha256"]
        )

    @staticmethod
    def reference_diagnostic_disposition(
        diagnostic: dict[str, object],
        signature: dict[str, object],
    ) -> tuple[str, tuple[str, ...]]:
        rejected: set[str] = set()
        unresolved: set[str] = set()
        if not diagnostic["definition_document_authoritative"]:
            unresolved.add("authoritative_provenance_unverified")
        if not diagnostic["definition_document_public_without_login"]:
            unresolved.add("access_unresolved")
        if diagnostic["native_label_is_excluded_proxy"]:
            rejected.add("proxy_construct")
        source_reason = {
            ("access_status", "login_required"): "access_requires_login",
            ("access_status", "restricted"): "access_restricted",
            ("license_status", "incompatible"): "license_incompatible",
            (
                "ethical_use_status",
                "incompatible",
            ): "ethical_use_incompatible",
            (
                "conversation_status",
                "acted_or_scripted",
            ): "acted_or_scripted",
            (
                "conversation_status",
                "mixed_unseparated",
            ): "mixed_unseparated_conversation",
        }
        for (field, value), reason in source_reason.items():
            if signature[field] == value:
                rejected.add(reason)
        source_unresolved = {
            "access_status": "access_unresolved",
            "license_status": "license_unresolved",
            "ethical_use_status": "ethical_use_unresolved",
            "conversation_status": "conversation_status_unresolved",
        }
        for field, reason in source_unresolved.items():
            if signature[field] == "unresolved":
                unresolved.add(reason)
        construct = diagnostic["construct_correspondence"]
        if construct == "proxy_construct":
            rejected.add("proxy_construct")
        elif construct == "target_absent":
            rejected.add("target_label_absent")
        elif construct != "direct_target_construct":
            unresolved.add("directness_unresolved")
        if diagnostic["annotation_modality"] == "unresolved":
            unresolved.add("source_documentation_incomplete")
        temporal = diagnostic["temporal_unit"]
        if temporal == "conversation":
            rejected.add("conversation_level_only")
        elif temporal == "other":
            rejected.add("temporal_unit_incompatible")
        elif temporal == "unresolved":
            unresolved.add("temporal_unit_unresolved")
        observer = diagnostic["observer_method"]
        if observer == "self_report":
            rejected.add("self_report_label")
        elif observer == "llm_generated":
            rejected.add("llm_generated_label")
        elif observer == "automated_proxy":
            rejected.add("proxy_construct")
        elif observer == "adjudicated_only_human_label":
            unresolved.add("reliability_not_preadjudication")
        elif observer == "unresolved":
            unresolved.add("observer_method_unresolved")
        raters = diagnostic["independent_rater_count"]
        if raters is None:
            unresolved.add("rater_count_unresolved")
        elif raters < 2:
            rejected.add("single_rater")
        ordered = lambda reasons: tuple(
            code for code in EXPECTED_REASON_CODE_ORDER if code in reasons
        )
        if rejected:
            return "rejected", ordered(rejected)
        if unresolved:
            return "unresolved", ordered(unresolved)

        reliability: set[str] = set()
        if not diagnostic["preadjudication"]:
            reliability.add("reliability_not_preadjudication")
        if not diagnostic["verifiable"]:
            reliability.add("reliability_unverifiable")
        rated = diagnostic["rated_unit_count"]
        positives = diagnostic["published_positive_count"]
        if rated is None:
            reliability.add("reliability_effective_sample_insufficient")
        if positives is None:
            reliability.update(
                {
                    "published_positive_count_missing",
                    "reliability_effective_sample_insufficient",
                }
            )
        elif positives < 93:
            reliability.update(
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
            reliability.add("reliability_interval_uncertain")
        if reliability or not diagnostic["effective_sample_sufficient"]:
            return "unresolved", ordered(reliability)
        point, lower, upper = intervals
        if point >= 800_000 and lower >= 670_000:
            return "admissible", ()
        if upper < 670_000:
            return "rejected", ("reliability_upper_below_0_67",)
        return "unresolved", ("reliability_interval_uncertain",)

    @staticmethod
    def reference_fail_ready(
        payload: dict[str, object],
        signal: str,
    ) -> bool:
        lanes = payload["search_lane_counts"]
        direct = lanes["direct_by_signal"][signal]
        fallback = lanes["fallback_material"]
        return (
            direct["query_counts"]["incomplete"] == 0
            and direct["query_counts"]["truncated"] == 0
            and fallback["query_counts"]["incomplete"] == 0
            and fallback["query_counts"]["truncated"] == 0
            and all(
                direct["citations"][direction]["stop_status"]
                in {"no_eligible_candidates", "source_list_exhausted"}
                for direction in ("backward", "forward")
            )
            and direct["discovery_disposition_counts"]["unresolved"] == 0
            and all(
                direct["citations"][direction]["disposition_counts"][
                    "unresolved"
                ]
                == 0
                for direction in ("backward", "forward")
            )
            and fallback["discovery_disposition_counts"]["unresolved"] == 0
            and direct["candidate_overflow_count"] == 0
            and fallback["candidate_overflow_count"] == 0
        )

    def align_local_card_witnesses(
        self,
        payload: dict[str, object],
    ) -> None:
        reason_counts = payload["reason_code_counts"]
        for item in payload["per_signal"]:
            for diagnostic in item["reliability_diagnostics"]:
                for reason in diagnostic["claimed_reason_codes"]:
                    reason_counts[reason] -= 1
        signatures = {
            entry["source_signature_sha256"]: entry
            for entry in payload["source_signature_counts"]
        }
        totals = {"admissible": 0, "rejected": 0, "unresolved": 0}
        passed: list[str] = []
        for item in payload["per_signal"]:
            admissible: list[str] = []
            rejected = 0
            unresolved = 0
            for diagnostic in item["reliability_diagnostics"]:
                status, reasons = self.reference_diagnostic_disposition(
                    diagnostic,
                    signatures[diagnostic["source_signature_sha256"]],
                )
                diagnostic["claimed_status"] = status
                diagnostic["claimed_reason_codes"] = list(reasons)
                for reason in reasons:
                    reason_counts[reason] += 1
                totals[status] += 1
                if status == "admissible":
                    admissible.append(diagnostic["evidence_card_sha256"])
                elif status == "rejected":
                    rejected += 1
                else:
                    unresolved += 1
            item["admissible_evidence_card_sha256s"] = admissible
            item["rejected_card_count"] = rejected
            item["unresolved_card_count"] = unresolved
            fail_ready = self.reference_fail_ready(
                payload,
                item["signal"],
            )
            decision_value = (
                "pass"
                if admissible
                else "defer"
                if (
                    unresolved > 0
                    or not fail_ready
                    or item["annotation_fallback"]
                    in {"feasible", "unresolved"}
                )
                else "fail"
            )
            item["decision"] = decision_value
            item["c2_eligible"] = decision_value == "pass"
            if decision_value == "pass":
                passed.append(item["signal"])
        payload["card_counts_by_status"] = totals
        payload["c2_eligible_signals"] = passed
        payload["overall_decision"] = (
            "proceed_full_to_c2"
            if len(passed) == 5
            else "proceed_partial_to_c2"
            if passed
            else "defer_c2"
            if any(
                item["decision"] == "defer"
                for item in payload["per_signal"]
            )
            else "stop_c2"
        )

    def realign_without_search_reasons(
        self,
        payload: dict[str, object],
    ) -> None:
        payload["reason_code_counts"] = {
            code: 0 for code in EXPECTED_REASON_CODE_ORDER
        }
        for item in payload["per_signal"]:
            for diagnostic in item["reliability_diagnostics"]:
                for reason in diagnostic["claimed_reason_codes"]:
                    payload["reason_code_counts"][reason] += 1
            if item["annotation_fallback"] == "feasible":
                payload["reason_code_counts"][
                    "annotation_fallback_feasible"
                ] += 1
            elif item["annotation_fallback"] == "unresolved":
                payload["reason_code_counts"][
                    "annotation_fallback_unresolved"
                ] += 1
        self.align_local_card_witnesses(payload)

    def add_unresolved_discovery_witness(
        self,
        payload: dict[str, object],
        *,
        signal: str,
        reason: str = "source_identity_unverified",
    ) -> None:
        payload["search_counts"]["returned_discovery_record_count"] += 1
        payload["search_counts"][
            "unresolved_discovery_record_count"
        ] += 1
        payload["search_lane_counts"]["direct_by_signal"][signal][
            "discovery_disposition_counts"
        ]["unresolved"] += 1
        payload["reason_code_counts"][reason] += 1
        item = next(
            item
            for item in payload["per_signal"]
            if item["signal"] == signal
        )
        if (
            payload["search_lane_counts"]["fallback_material"][
                "candidate_order_count"
            ]
            == 0
        ):
            if item["annotation_fallback"] != "unresolved":
                item["annotation_fallback"] = "unresolved"
                payload["reason_code_counts"][
                    "annotation_fallback_unresolved"
                ] += 1
        self.align_local_card_witnesses(payload)

    def assert_result_rejected(
        self,
        payload: dict[str, object],
        code: str,
    ) -> None:
        self.reself(payload)
        for validate in (
            self.validate_result,
            self.render_result,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaisesRegex(runner.RunnerError, code):
                    validate(copy.deepcopy(payload))

    def rejected_alpha_result(self) -> dict[str, object]:
        payload = self.valid_result()
        item = payload["per_signal"][2]
        item["decision"] = "fail"
        item["admissible_evidence_card_sha256s"] = []
        item["rejected_card_count"] = 1
        item["c2_eligible"] = False
        diagnostic = item["reliability_diagnostics"][0]
        diagnostic.update(
            {
                "point_micros": -500_000,
                "lower_95_micros": -600_000,
                "upper_95_micros": -400_000,
            }
        )
        payload["card_counts_by_status"].update(
            {"admissible": 0, "rejected": 1}
        )
        payload["reason_code_counts"][
            "reliability_upper_below_0_67"
        ] = 0
        payload["overall_decision"] = "stop_c2"
        payload["c2_eligible_signals"] = []
        self.align_local_card_witnesses(payload)
        return payload

    def test_result_is_rowless_hash_bound_and_partial_when_one_signal_passes(
        self,
    ) -> None:
        before = (
            self.protocol_bytes,
            self.search_bytes,
            self.one_pass_source_bytes,
            self.review_bytes_for_one_pass,
        )
        result = self.valid_result()
        self.assertEqual(
            result["schema_version"],
            "EmotionStatePhaseC1AggregateResultV2",
        )
        self.assertEqual(set(result), EXPECTED_PHASE_C1_RESULT_FIELDS)
        self.assertEqual(
            phase_c1.PHASE_C1_RESULT_FIELDS,
            EXPECTED_PHASE_C1_RESULT_FIELDS,
        )
        self.assertEqual(result["overall_decision"], "proceed_partial_to_c2")
        self.assertEqual(result["target_signals"], list(EXPECTED_SIGNALS))
        self.assertEqual(result["c2_eligible_signals"], ["confusion"])
        self.assertFalse(result["runtime_approved"])
        self.assertFalse(result["boundary"]["model_evaluation_run"])
        self.assertNotIn("sources", result)
        self.assertNotIn("cards", result)
        self.assertEqual(
            result["protocol_sha256"],
            hashlib.sha256(self.protocol_bytes).hexdigest().upper(),
        )
        self.assertEqual(
            result["source_review_receipt_sha256"],
            hashlib.sha256(
                self.review_bytes_for_one_pass
            ).hexdigest().upper(),
        )
        self.assertEqual(
            result["search_counts"],
            {
                "direct_label_query_count": 80,
                "fallback_material_query_count": 8,
                "total_query_count": 88,
                "complete_query_count": 88,
                "incomplete_query_count": 0,
                "truncated_query_count": 0,
                "returned_discovery_record_count": 1,
                "retained_candidate_record_count": 1,
                "duplicate_discovery_record_count": 0,
                "excluded_discovery_record_count": 0,
                "unresolved_discovery_record_count": 0,
                "detailed_candidate_count": 1,
                "candidate_overflow_count": 0,
                "backward_citation_record_count": 0,
                "forward_citation_record_count": 0,
                "unresolved_citation_record_count": 0,
                "nonexhaustive_citation_stop_count": 0,
                "search_complete": True,
            },
        )
        self.assertEqual(
            result["source_counts"],
            {
                "source_count": 1,
                "document_count": 1,
                "existing_annotation_evidence_source_count": 1,
                "fallback_material_candidate_source_count": 1,
            },
        )
        self.assertEqual(
            result["card_counts_by_status"],
            {"admissible": 1, "rejected": 0, "unresolved": 0},
        )
        self.assertEqual(
            tuple(result["reason_code_counts"]),
            EXPECTED_REASON_CODE_ORDER,
        )
        self.assertTrue(
            all(value == 0 for value in result["reason_code_counts"].values())
        )
        confusion = next(
            item
            for item in result["per_signal"]
            if item["signal"] == "confusion"
        )
        self.assertEqual(
            set(confusion["reliability_diagnostics"][0]),
            EXPECTED_RELIABILITY_DIAGNOSTIC_FIELDS,
        )
        self.assertIsNone(
            confusion["reliability_diagnostics"][0][
                "uncertain_or_unratable_rate_micros"
            ]
        )
        self.assertEqual(
            before,
            (
                self.protocol_bytes,
                self.search_bytes,
                self.one_pass_source_bytes,
                self.review_bytes_for_one_pass,
            ),
        )
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("c1-source-", serialized)
        self.assertNotIn("c1-card-", serialized)

    def test_report_is_deterministic_lf_and_binds_exact_result(self) -> None:
        result = self.valid_result()
        first = self.render_result(result)
        second = self.render_result(copy.deepcopy(result))
        self.assertEqual(first, second)
        self.assertTrue(first.endswith(b"\n"))
        self.assertNotIn(b"\r", first)
        result_sha256 = phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(result)
        )
        self.assertIn(result_sha256.encode("ascii"), first)
        text = first.decode("utf-8")
        self.assertEqual(
            [
                line
                for line in text.splitlines()
                if line.startswith("#")
            ],
            [
                (
                    "# EMOTION-STATE-004 Phase C1 Operational-Signal "
                    "Evidence Admission"
                ),
                "## Aggregate",
                "## Per-Signal Decisions",
                "## C2 Eligibility",
                "## Reliability And Search Boundary",
                "## Interpretation",
                "## Limitations",
                "## Closed Boundary",
            ],
        )
        self.assertIn("unavailable", text)
        self.assertIn("No model evaluation was run.", text)
        self.assertIn("Runtime approval: false.", text)
        self.assertNotIn("https://", text)
        self.assertNotIn("c1-source-", text)
        self.assertNotIn("c1-card-", text)

    def test_fixed_tracked_input_paths_and_lexical_root_pin_are_exact(
        self,
    ) -> None:
        self.assertEqual(runner.ROOT, ROOT)
        self.assertEqual(
            runner.PROTOCOL_PATH,
            ROOT
            / "research"
            / "experiments"
            / "configs"
            / "emotion-state-004-phase-c1-discovery-protocol.json",
        )
        self.assertEqual(
            runner.SEARCH_LEDGER_PATH,
            ROOT
            / "research"
            / "sources"
            / "emotion_state"
            / "phase_c1_search_ledger.json",
        )
        self.assertEqual(
            runner.SOURCE_LEDGER_PATH,
            ROOT
            / "research"
            / "sources"
            / "emotion_state"
            / "phase_c1_source_evidence_ledger.json",
        )
        self.assertEqual(
            runner.SOURCE_REVIEW_PATH,
            ROOT
            / "research"
            / "sources"
            / "emotion_state"
            / "phase_c1_source_review_receipt.json",
        )
        root_key = os.path.normcase(os.path.abspath(os.fspath(ROOT)))
        matching_entries = [
            entry
            for entry in sys.path
            if os.path.normcase(os.path.abspath(entry or os.curdir))
            == root_key
        ]
        self.assertEqual(
            os.path.normcase(os.path.abspath(sys.path[0])),
            root_key,
        )
        self.assertEqual(len(matching_entries), 1)
        self.assertFalse(hasattr(runner, "SOURCE_CACHE_PATH"))

    def test_recursive_forbidden_content_rejects_before_render(self) -> None:
        for key in (
            "audio",
            "participant_id",
            "prediction",
            "probability",
            "transcript",
            "utterance",
        ):
            with self.subTest(key=key):
                payload = self.valid_result()
                payload["search_counts"][key] = "forbidden"
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "forbidden_content",
                ):
                    self.validate_result(payload)
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "forbidden_content",
                ):
                    self.render_result(payload)

    def test_result_rejects_runtime_and_decision_contradictions(self) -> None:
        runtime = self.valid_result()
        runtime["runtime_approved"] = True
        self.reself(runtime)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "runtime_approved",
        ):
            self.validate_result(runtime)

        eligible_defer = self.valid_result()
        confusion = eligible_defer["per_signal"][2]
        confusion["decision"] = "defer"
        confusion["admissible_evidence_card_sha256s"] = []
        confusion["unresolved_card_count"] = 1
        eligible_defer["card_counts_by_status"]["admissible"] = 0
        eligible_defer["card_counts_by_status"]["unresolved"] = 1
        eligible_defer["reason_code_counts"][
            "reliability_unverifiable"
        ] = 1
        eligible_defer["overall_decision"] = "defer_c2"
        self.reself(eligible_defer)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "per_signal",
        ):
            self.validate_result(eligible_defer)

        full = self.valid_result()
        full["overall_decision"] = "proceed_full_to_c2"
        self.reself(full)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "overall_decision",
        ):
            self.validate_result(full)

        partial = self.deferred_result()
        partial["overall_decision"] = "proceed_partial_to_c2"
        self.reself(partial)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "overall_decision",
        ):
            self.validate_result(partial)

        stopped = self.deferred_result()
        stopped["overall_decision"] = "stop_c2"
        self.reself(stopped)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "overall_decision",
        ):
            self.validate_result(stopped)

    def test_unresolved_or_feasible_signal_cannot_claim_fail(self) -> None:
        unresolved = self.deferred_result()
        unresolved["per_signal"][2]["decision"] = "fail"
        unresolved["overall_decision"] = "stop_c2"
        self.reself(unresolved)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "per_signal",
        ):
            self.validate_result(unresolved)

        feasible = self.all_fail_result()
        feasible["per_signal"][0]["annotation_fallback"] = "feasible"
        self.reself(feasible)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "per_signal",
        ):
            self.validate_result(feasible)

    def test_report_renderer_rejects_a_statement_contradicting_rows(
        self,
    ) -> None:
        payload = self.valid_result()
        payload["overall_decision"] = "proceed_full_to_c2"
        self.reself(payload)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "overall_decision",
        ):
            self.render_result(payload)

    def test_review_and_selfless_hash_mismatches_reject(self) -> None:
        review_payload = phase_c1.load_json_strict(
            self.review_bytes_for_one_pass,
            source="review",
        )
        self.assertIsInstance(review_payload, dict)
        review_payload["source_evidence_ledger_sha256"] = "E" * 64
        with self.assertRaisesRegex(
            runner.RunnerError,
            "review_hash_binding",
        ):
            runner.build_phase_c1_result(
                head_commit="a" * 40,
                validator_blob_id="b" * 40,
                protocol_bytes=self.protocol_bytes,
                search_ledger_bytes=self.search_bytes,
                source_ledger_bytes=self.one_pass_source_bytes,
                review_receipt_bytes=phase_c1.canonical_json_bytes(
                    review_payload
                ),
            )

        payload = self.valid_result()
        payload["aggregate_content_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            runner.RunnerError,
            "aggregate_content_sha256",
        ):
            self.validate_result(payload)

    def test_card_status_and_query_count_algebra_rejects(self) -> None:
        payload = self.valid_result()
        payload["card_counts_by_status"]["admissible"] += 1
        self.reself(payload)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "card_status_counts",
        ):
            self.validate_result(payload)

        for field, wrong in (
            ("direct_label_query_count", 79),
            ("fallback_material_query_count", 7),
            ("total_query_count", 87),
        ):
            with self.subTest(field=field):
                payload = self.valid_result()
                payload["search_counts"][field] = wrong
                self.reself(payload)
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "search_counts",
                ):
                    self.validate_result(payload)

    def test_protocol_caps_reject_impossible_aggregate_counts(self) -> None:
        mutations = (
            {
                "returned_discovery_record_count": 2_201,
                "retained_candidate_record_count": 2_201,
            },
            {"backward_citation_record_count": 26},
            {"forward_citation_record_count": 26},
            {"detailed_candidate_count": 111},
            {"candidate_overflow_count": 2},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                payload = self.valid_result()
                payload["search_counts"].update(mutation)
                if "detailed_candidate_count" in mutation:
                    payload["source_counts"].update(
                        {
                            "source_count": 111,
                            "document_count": 111,
                            "existing_annotation_evidence_source_count": 1,
                            "fallback_material_candidate_source_count": 1,
                        }
                    )
                self.reself(payload)
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "search_counts",
                ):
                    self.validate_result(payload)

    def test_per_signal_card_count_cannot_exceed_frozen_cap(self) -> None:
        payload = self.valid_result()
        item = payload["per_signal"][0]
        template = payload["per_signal"][2]["reliability_diagnostics"][0]
        item["reliability_diagnostics"] = []
        for ordinal in range(21):
            diagnostic = copy.deepcopy(template)
            diagnostic["evidence_card_sha256"] = hashlib.sha256(
                f"synthetic-card-{ordinal}".encode("ascii")
            ).hexdigest().upper()
            item["reliability_diagnostics"].append(diagnostic)
        item["rejected_card_count"] = 21
        payload["card_counts_by_status"]["rejected"] = 21
        payload["search_counts"].update(
            {
                "returned_discovery_record_count": 21,
                "retained_candidate_record_count": 21,
                "detailed_candidate_count": 21,
            }
        )
        payload["source_counts"].update(
            {
                "source_count": 21,
                "document_count": 21,
                "existing_annotation_evidence_source_count": 21,
            }
        )
        self.reself(payload)
        for validate in (
            self.validate_result,
            self.render_result,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "search_lane_counts",
                ):
                    validate(copy.deepcopy(payload))

    def test_card_totals_require_existing_annotation_sources(self) -> None:
        payload = self.valid_result()
        payload["source_counts"][
            "existing_annotation_evidence_source_count"
        ] = 0
        self.reself(payload)
        for validate in (
            self.validate_result,
            self.render_result,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "source_signature_counts",
                ):
                    validate(copy.deepcopy(payload))

    def test_source_document_count_respects_frozen_role_cap(self) -> None:
        payload = self.valid_result()
        payload["source_counts"]["document_count"] = 6
        self.reself(payload)
        for validate in (
            self.validate_result,
            self.render_result,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "source_counts",
                ):
                    validate(copy.deepcopy(payload))

    def test_negative_alpha_is_valid_for_rejected_diagnostic(self) -> None:
        payload = self.rejected_alpha_result()
        self.reself(payload)

        self.validate_result(payload)
        report = self.render_result(payload)
        self.assertIn(b"point_micros=-500000", report)
        self.assertIn(b"lower_95_micros=-600000", report)
        self.assertIn(b"upper_95_micros=-400000", report)

    def test_returned_records_are_capped_by_complete_queries(self) -> None:
        payload = self.valid_result()
        payload["search_counts"].update(
            {
                "complete_query_count": 0,
                "incomplete_query_count": 88,
                "search_complete": False,
            }
        )
        self.assert_result_rejected(payload, "search_counts")

    def test_unresolved_citation_cannot_supply_candidate_capacity(
        self,
    ) -> None:
        unresolved = self.valid_result()
        unresolved["search_counts"].update(
            {
                "returned_discovery_record_count": 0,
                "retained_candidate_record_count": 0,
                "backward_citation_record_count": 1,
                "unresolved_citation_record_count": 1,
            }
        )
        lane = unresolved["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]
        lane["discovery_disposition_counts"]["retained_candidate"] = 0
        lane["citations"]["backward"]["disposition_counts"][
            "unresolved"
        ] = 1
        unresolved["reason_code_counts"][
            "source_identity_unverified"
        ] = 1
        self.assert_result_rejected(unresolved, "search_counts")

        retained = self.valid_result()
        retained["search_counts"].update(
            {
                "returned_discovery_record_count": 0,
                "retained_candidate_record_count": 0,
                "backward_citation_record_count": 1,
            }
        )
        lane = retained["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]
        lane["discovery_disposition_counts"]["retained_candidate"] = 0
        lane["citations"]["backward"]["disposition_counts"][
            "retained_candidate"
        ] = 1
        self.reself(retained)
        self.validate_result(retained)
        self.render_result(retained)

    def test_positive_overflow_requires_a_saturated_candidate_lane(
        self,
    ) -> None:
        below_minimum = self.valid_result()
        below_minimum["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "retained_candidate_record_count": 2,
                "candidate_overflow_count": 1,
            }
        )
        lane = below_minimum["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]
        lane["candidate_overflow_count"] = 1
        lane["discovery_disposition_counts"]["retained_candidate"] = 2
        self.assert_result_rejected(below_minimum, "search_counts")

        no_saturated_lane = self.fallback_result(("infeasible",))
        no_saturated_lane["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "retained_candidate_record_count": 2,
                "candidate_overflow_count": 1,
            }
        )
        lane = no_saturated_lane["search_lane_counts"][
            "fallback_material"
        ]
        lane["candidate_overflow_count"] = 1
        lane["discovery_disposition_counts"]["retained_candidate"] = 2
        self.assert_result_rejected(no_saturated_lane, "search_counts")

    def test_every_source_requires_at_least_one_phase_c1_role(self) -> None:
        payload = self.valid_result()
        entry = payload["source_signature_counts"][0]
        entry["existing_annotation_evidence_role"] = False
        entry["fallback_material_candidate_role"] = False
        self.rehash_source_signature(payload, entry)
        payload["source_counts"].update(
            {
                "existing_annotation_evidence_source_count": 0,
                "fallback_material_candidate_source_count": 0,
            }
        )
        self.assert_result_rejected(
            payload,
            "source_counts",
        )

    def test_source_union_requires_direct_card_capacity(self) -> None:
        impossible = self.all_fail_result()
        impossible["search_counts"].update(
            {
                "returned_discovery_record_count": 11,
                "retained_candidate_record_count": 11,
                "detailed_candidate_count": 11,
            }
        )
        impossible["source_counts"].update(
            {
                "source_count": 11,
                "document_count": 11,
                "existing_annotation_evidence_source_count": 0,
                "fallback_material_candidate_source_count": 11,
            }
        )
        self.assert_result_rejected(impossible, "search_lane_counts")

        fallback_only_boundary = self.fallback_result(
            ("infeasible",) * 8
        )
        self.assertEqual(
            fallback_only_boundary["source_counts"],
            {
                "source_count": 8,
                "document_count": 8,
                "existing_annotation_evidence_source_count": 0,
                "fallback_material_candidate_source_count": 8,
            },
        )
        self.validate_result(fallback_only_boundary)
        self.render_result(fallback_only_boundary)

    def test_defer_requires_card_fallback_or_search_blocker(self) -> None:
        payload = self.valid_result()
        payload["per_signal"][0]["decision"] = "defer"
        self.assert_result_rejected(payload, "per_signal")

    def test_search_only_defer_requires_noninfeasible_fallback(self) -> None:
        impossible = self.all_fail_result()
        self.add_unresolved_discovery_witness(
            impossible,
            signal="hesitation",
        )
        impossible["per_signal"][0]["annotation_fallback"] = "infeasible"
        impossible["reason_code_counts"][
            "annotation_fallback_unresolved"
        ] = 0
        impossible["per_signal"][0]["decision"] = "fail"
        impossible["overall_decision"] = "stop_c2"
        self.assert_result_rejected(impossible, "per_signal")

        blocker_on_pass = self.valid_result()
        self.add_unresolved_discovery_witness(
            blocker_on_pass,
            signal="confusion",
        )
        self.reself(blocker_on_pass)
        self.validate_result(blocker_on_pass)
        self.render_result(blocker_on_pass)

    def test_aggregate_search_blocker_requires_noninfeasible_fallback(
        self,
    ) -> None:
        partial = self.valid_result()
        self.add_unresolved_discovery_witness(
            partial,
            signal="hesitation",
        )
        partial["per_signal"][0]["annotation_fallback"] = "infeasible"
        partial["reason_code_counts"][
            "annotation_fallback_unresolved"
        ] = 0
        self.assert_result_rejected(partial, "per_signal")

        full = self.full_pass_result()
        self.add_unresolved_discovery_witness(
            full,
            signal="hesitation",
        )
        full["per_signal"][0]["annotation_fallback"] = "infeasible"
        full["reason_code_counts"][
            "annotation_fallback_unresolved"
        ] = 0
        self.assert_result_rejected(full, "per_signal")

        no_blocker = self.all_fail_result()
        self.validate_result(no_blocker)
        self.render_result(no_blocker)

        blocker_with_unresolved_fallback = self.valid_result()
        self.add_unresolved_discovery_witness(
            blocker_with_unresolved_fallback,
            signal="confusion",
        )
        self.reself(blocker_with_unresolved_fallback)
        self.validate_result(
            blocker_with_unresolved_fallback
        )
        self.render_result(blocker_with_unresolved_fallback)

    def test_stop_rejects_every_aggregate_search_blocker(self) -> None:
        incomplete = self.all_fail_result()
        incomplete["search_counts"].update(
            {
                "complete_query_count": 87,
                "incomplete_query_count": 1,
                "search_complete": False,
            }
        )
        incomplete["search_lane_counts"]["direct_by_signal"][
            "hesitation"
        ]["query_counts"].update({"complete": 15, "incomplete": 1})

        unresolved_discovery = self.all_fail_result()
        unresolved_discovery["search_counts"].update(
            {
                "returned_discovery_record_count": 1,
                "unresolved_discovery_record_count": 1,
            }
        )
        unresolved_discovery["search_lane_counts"]["direct_by_signal"][
            "hesitation"
        ]["discovery_disposition_counts"]["unresolved"] = 1
        unresolved_discovery["reason_code_counts"][
            "source_identity_unverified"
        ] = 1

        unresolved_citation = self.all_fail_result()
        unresolved_citation["search_counts"].update(
            {
                "backward_citation_record_count": 1,
                "unresolved_citation_record_count": 1,
            }
        )
        unresolved_citation["search_lane_counts"]["direct_by_signal"][
            "hesitation"
        ]["citations"]["backward"]["disposition_counts"][
            "unresolved"
        ] = 1
        unresolved_citation["reason_code_counts"][
            "source_identity_unverified"
        ] = 1

        for name, payload in (
            ("incomplete_query", incomplete),
            ("unresolved_discovery", unresolved_discovery),
            ("unresolved_citation", unresolved_citation),
        ):
            with self.subTest(blocker=name):
                self.assert_result_rejected(payload, "per_signal")

    def test_empty_fallback_material_cannot_be_feasible_or_unresolved(
        self,
    ) -> None:
        for status, reason in (
            ("feasible", "annotation_fallback_feasible"),
            ("unresolved", "annotation_fallback_unresolved"),
        ):
            with self.subTest(status=status):
                payload = self.all_fail_result()
                payload["per_signal"][0].update(
                    {
                        "decision": "defer",
                        "annotation_fallback": status,
                    }
                )
                payload["reason_code_counts"][reason] = 1
                self.assert_result_rejected(payload, "per_signal")

    def test_fallback_reason_counts_equal_fallback_status_counts(self) -> None:
        for status, reason in (
            ("feasible", "annotation_fallback_feasible"),
            ("unresolved", "annotation_fallback_unresolved"),
        ):
            with self.subTest(status=status):
                payload = self.fallback_result(
                    (
                        "feasible"
                        if status == "feasible"
                        else "missing_evidence",
                    )
                )
                payload["reason_code_counts"][reason] = 0
                self.assert_result_rejected(
                    payload,
                    "reason_code_counts",
                )

    def test_exact_fallback_reason_counts_remain_valid(self) -> None:
        for status, reason in (
            ("feasible", "annotation_fallback_feasible"),
            ("unresolved", "annotation_fallback_unresolved"),
        ):
            with self.subTest(status=status):
                payload = self.fallback_result(
                    (
                        "feasible"
                        if status == "feasible"
                        else "missing_evidence",
                    )
                )
                self.reself(payload)
                self.validate_result(payload)
                self.render_result(payload)

    def test_reason_count_partitions_reject_impossible_aggregates(
        self,
    ) -> None:
        rejected_without_reason = self.rejected_alpha_result()
        rejected_without_reason["reason_code_counts"][
            "reliability_upper_below_0_67"
        ] = 0

        unresolved_without_reason = self.deferred_result()
        unresolved_without_reason["reason_code_counts"][
            "reliability_unverifiable"
        ] = 0

        rejection_reason_without_item = self.valid_result()
        rejection_reason_without_item["reason_code_counts"][
            "access_restricted"
        ] = 1

        search_meta_reason = self.valid_result()
        search_meta_reason["reason_code_counts"]["candidate_overflow"] = 1

        for name, payload in (
            ("rejected_without_reason", rejected_without_reason),
            ("unresolved_without_reason", unresolved_without_reason),
            ("rejection_reason_without_item", rejection_reason_without_item),
            ("search_meta_reason", search_meta_reason),
        ):
            with self.subTest(name=name):
                self.assert_result_rejected(payload, "reason_code_counts")





    def test_candidate_supply_reserves_retained_citations_before_reasons(
        self,
    ) -> None:
        reused = self.valid_result()
        reused["search_counts"].update(
            {
                "returned_discovery_record_count": 0,
                "retained_candidate_record_count": 0,
                "backward_citation_record_count": 1,
            }
        )
        lane = reused["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]
        lane["discovery_disposition_counts"]["retained_candidate"] = 0
        lane["citations"]["backward"]["disposition_counts"][
            "retained_candidate"
        ] = 1
        reused["reason_code_counts"]["access_restricted"] = 1
        self.assert_result_rejected(reused, "reason_code_counts")

        retained_and_excluded = self.valid_result()
        retained_and_excluded["search_counts"].update(
            {
                "returned_discovery_record_count": 0,
                "retained_candidate_record_count": 0,
                "backward_citation_record_count": 2,
            }
        )
        lane = retained_and_excluded["search_lane_counts"][
            "direct_by_signal"
        ]["confusion"]
        lane["discovery_disposition_counts"]["retained_candidate"] = 0
        lane["citations"]["backward"]["disposition_counts"].update(
            {"retained_candidate": 1, "excluded": 1}
        )
        retained_and_excluded["reason_code_counts"][
            "access_restricted"
        ] = 1
        self.reself(retained_and_excluded)
        self.validate_result(retained_and_excluded)
        self.render_result(retained_and_excluded)

        retained_and_duplicate = self.valid_result()
        retained_and_duplicate["search_counts"].update(
            {
                "returned_discovery_record_count": 0,
                "retained_candidate_record_count": 0,
                "backward_citation_record_count": 2,
            }
        )
        lane = retained_and_duplicate["search_lane_counts"][
            "direct_by_signal"
        ]["confusion"]
        lane["discovery_disposition_counts"]["retained_candidate"] = 0
        lane["citations"]["backward"]["disposition_counts"].update(
            {"retained_candidate": 1, "duplicate": 1}
        )
        self.reself(retained_and_duplicate)
        self.validate_result(retained_and_duplicate)
        self.render_result(retained_and_duplicate)

        excess_retained_discovery = self.valid_result()
        excess_retained_discovery["search_counts"].update(
            {
                "returned_discovery_record_count": 3,
                "retained_candidate_record_count": 3,
            }
        )
        self.assert_result_rejected(
            excess_retained_discovery,
            "search_lane_counts",
        )

    def test_cross_lane_retained_discovery_uses_global_candidate_union(
        self,
    ) -> None:
        search_payload = self.valid_search_ledger_payload()
        shared_source_id = "c1-source-0001"
        shared_identity = self.fixture_hash("shared-cross-lane-identity")
        for record_number, signal in enumerate(
            ("hesitation", "confusion"),
            start=1,
        ):
            query = next(
                item
                for item in search_payload["query_records"]
                if item["query_id"]
                == f"c1-query-{signal}-openalex-01"
            )
            discovery = self.discovery_record(
                query_id=query["query_id"],
                rank=1,
                record_number=record_number,
            )
            discovery.update(
                {
                    "candidate_source_id": shared_source_id,
                    "identity_sha256": shared_identity,
                }
            )
            query["discovery_records"] = [discovery]
            query["returned_count"] = 1
            query["result_count"] = 1
            search_payload["candidate_order_by_signal"][signal] = [
                shared_source_id
            ]

        search = phase_c1.validate_search_ledger(
            search_payload,
            protocol=self.protocol,
        )
        search_bytes = phase_c1.canonical_json_bytes(search_payload)
        source_payload = self.valid_source_evidence_ledger(search_bytes)
        source_payload["sources"] = [self.valid_source_payload()]
        source_payload["cards"] = []
        for signal in ("hesitation", "confusion"):
            card = self.valid_card_payload()
            card.update(
                {
                    "card_id": f"c1-card-{signal}-0001",
                    "signal": signal,
                    "native_label": signal,
                }
            )
            source_payload["cards"].append(card)
        for assessment in source_payload["fallback_assessments"]:
            assessment["status"] = "infeasible"
            assessment["reason_codes"] = []
        source_ledger = phase_c1.validate_source_evidence_ledger(
            source_payload,
            protocol=self.protocol,
            search_ledger_bytes=search_bytes,
        )
        source_bytes = phase_c1.canonical_json_bytes(source_payload)
        review_payload = {
            "schema_version": "EmotionStatePhaseC1SourceReviewReceiptV1",
            "protocol_sha256": hashlib.sha256(
                self.protocol_path.read_bytes()
            ).hexdigest().upper(),
            "search_ledger_sha256": phase_c1.sha256_bytes(search_bytes),
            "source_evidence_ledger_sha256": phase_c1.sha256_bytes(
                source_bytes
            ),
            "transport_ledger_sha256": "D" * 64,
            "reviewed_transport_receipt_sha256s": list(
                phase_c1._review_transport_hashes(
                    search_payload,
                    source_ledger.sources,
                )
            ),
            "reviewed_document_sha256s": [
                document.cached_sha256
                for source in source_ledger.sources
                for document in source.documents
            ],
            "review_scope": (
                "all_transport_discovery_citation_source_cards_and_"
                "search_completeness"
            ),
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
        review = phase_c1.validate_source_review_receipt(
            review_payload,
            protocol=self.protocol,
            search_ledger_bytes=search_bytes,
            source_evidence_ledger_bytes=source_bytes,
        )
        projection = decision.project_phase_c1_admission(
            protocol=self.protocol,
            search_ledger=search,
            source_ledger=source_ledger,
            review_receipt=review,
        )
        self.assertEqual(
            projection.c2_eligible_signals,
            ("hesitation", "confusion"),
        )

        result = self.build_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=search_bytes,
            source_ledger_bytes=source_bytes,
            review_receipt_bytes=phase_c1.canonical_json_bytes(
                review_payload
            ),
        )
        self.assertEqual(
            (
                result["search_counts"]["retained_candidate_record_count"],
                result["search_counts"]["detailed_candidate_count"],
            ),
            (2, 1),
        )
        self.validate_result(result)
        self.render_result(result)

        aggregate_only = self.valid_result()
        aggregate_only["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "retained_candidate_record_count": 2,
            }
        )
        self.assert_result_rejected(
            aggregate_only,
            "search_lane_counts",
        )

    def test_discovery_and_citation_duplicate_slack_requires_an_anchor(
        self,
    ) -> None:
        duplicate_only = self.all_fail_result()
        duplicate_only["search_counts"].update(
            {
                "returned_discovery_record_count": 1,
                "duplicate_discovery_record_count": 1,
            }
        )
        duplicate_only["search_lane_counts"]["direct_by_signal"][
            "hesitation"
        ]["discovery_disposition_counts"]["duplicate"] = 1
        self.assert_result_rejected(
            duplicate_only,
            "search_counts",
        )

        lone_resolved_citation = self.all_fail_result()
        lone_resolved_citation["search_counts"][
            "backward_citation_record_count"
        ] = 1
        lone_resolved_citation["search_lane_counts"][
            "direct_by_signal"
        ]["hesitation"]["citations"]["backward"][
            "disposition_counts"
        ]["duplicate"] = 1
        self.assert_result_rejected(
            lone_resolved_citation,
            "search_lane_counts",
        )

        anchored_duplicate = self.valid_result()
        anchored_duplicate["search_counts"][
            "backward_citation_record_count"
        ] = 1
        anchored_duplicate["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]["citations"]["backward"]["disposition_counts"]["duplicate"] = 1
        self.reself(anchored_duplicate)
        self.validate_result(anchored_duplicate)
        self.render_result(anchored_duplicate)

        retained_plus_excluded = self.valid_result()
        retained_plus_excluded["search_counts"][
            "backward_citation_record_count"
        ] = 1
        retained_plus_excluded["search_lane_counts"][
            "direct_by_signal"
        ]["confusion"]["citations"]["backward"]["disposition_counts"][
            "excluded"
        ] = 1
        retained_plus_excluded["reason_code_counts"][
            "access_restricted"
        ] = 1
        self.reself(retained_plus_excluded)
        self.validate_result(retained_plus_excluded)
        self.render_result(retained_plus_excluded)




    def test_observable_reliability_reason_thresholds_remain_reachable(
        self,
    ) -> None:
        alpha_below_upper_boundary = self.rejected_alpha_result()
        alpha_below_upper_boundary["per_signal"][2][
            "reliability_diagnostics"
        ][0].update(
            {
                "point_micros": 650_000,
                "lower_95_micros": 590_000,
                "upper_95_micros": 669_999,
            }
        )

        single_rater = self.rejected_alpha_result()
        single_rater["reason_code_counts"].update(
            {
                "reliability_upper_below_0_67": 0,
                "single_rater": 1,
            }
        )
        single_rater["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "independent_rater_count": 1,
                "effective_sample_sufficient": False,
                "point_micros": 840_000,
                "lower_95_micros": 700_000,
                "upper_95_micros": 900_000,
            }
        )

        missing_rater = self.deferred_result()
        missing_rater["reason_code_counts"].update(
            {
                "reliability_unverifiable": 0,
                "rater_count_unresolved": 1,
            }
        )
        missing_rater["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "independent_rater_count": None,
                "effective_sample_sufficient": False,
            }
        )

        incomplete_interval = self.deferred_result()
        incomplete_interval["reason_code_counts"].update(
            {
                "reliability_unverifiable": 0,
                "reliability_interval_uncertain": 1,
            }
        )
        incomplete_interval["per_signal"][2]["reliability_diagnostics"][0][
            "lower_95_micros"
        ] = None

        below_threshold = self.deferred_result()
        below_threshold["reason_code_counts"].update(
            {
                "reliability_unverifiable": 0,
                "reliability_effective_sample_insufficient": 1,
                "positive_support_below_93": 1,
            }
        )
        below_threshold["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "published_positive_count": 92,
                "effective_sample_sufficient": False,
            }
        )

        missing_positive = self.deferred_result()
        missing_positive["reason_code_counts"].update(
            {
                "reliability_unverifiable": 0,
                "reliability_effective_sample_insufficient": 1,
                "published_positive_count_missing": 1,
            }
        )
        missing_positive["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "published_positive_count": None,
                "effective_sample_sufficient": False,
            }
        )

        effective_only = self.deferred_result()
        effective_only["reason_code_counts"].update(
            {
                "reliability_unverifiable": 0,
                "reliability_effective_sample_insufficient": 1,
            }
        )
        effective_only["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "rated_unit_count": None,
                "effective_sample_sufficient": False,
            }
        )

        for name, payload in (
            ("alpha_below_upper_boundary", alpha_below_upper_boundary),
            ("single_rater", single_rater),
            ("missing_rater", missing_rater),
            ("incomplete_interval", incomplete_interval),
            ("below_threshold", below_threshold),
            ("missing_positive", missing_positive),
            ("effective_only", effective_only),
        ):
            with self.subTest(name=name):
                self.realign_without_search_reasons(payload)
                self.reself(payload)
                self.validate_result(payload)
                self.render_result(payload)

        alpha_at_boundary = self.rejected_alpha_result()
        alpha_at_boundary["per_signal"][2][
            "reliability_diagnostics"
        ][0].update(
            {
                "point_micros": 650_000,
                "lower_95_micros": 590_000,
                "upper_95_micros": 670_000,
            }
        )
        self.assert_result_rejected(
            alpha_at_boundary,
            "reliability_diagnostics",
        )







    def test_limitations_are_literal_ordered_and_rowless(self) -> None:
        mutations: tuple[
            Callable[[list[object]], None],
            ...,
        ] = (
            lambda values: values.__setitem__(0, "Changed."),
            lambda values: values.pop(),
            lambda values: values.append(values[-1]),
            lambda values: values.reverse(),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                payload = self.valid_result()
                limitations = payload["limitations"]
                self.assertIsInstance(limitations, list)
                mutate(limitations)
                self.reself(payload)
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "limitations",
                ):
                    self.validate_result(payload)

        payload = self.valid_result()
        self.assertEqual(
            payload["limitations"],
            list(EXPECTED_PHASE_C1_LIMITATIONS),
        )
        payload["limitations"][0] = [
            "row",
            {"participant_id": "synthetic-person"},
        ]
        self.reself(payload)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "forbidden_content",
        ):
            self.validate_result(payload)

    def test_closed_shapes_and_reliability_semantics_reject_mutations(
        self,
    ) -> None:
        payload = self.valid_result()
        payload["extra"] = False
        self.reself(payload)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "result_fields",
        ):
            self.validate_result(payload)

        payload = self.valid_result()
        diagnostic = payload["per_signal"][2]["reliability_diagnostics"][0]
        diagnostic["effective_sample_sufficient"] = False
        self.reself(payload)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "reliability_diagnostics",
        ):
            self.validate_result(payload)

        payload = self.valid_result()
        del payload["reason_code_counts"]["license_unresolved"]
        self.reself(payload)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "reason_code_counts",
        ):
            self.validate_result(payload)

    def test_admissible_diagnostic_must_pass_frozen_alpha_rule(
        self,
    ) -> None:
        mutations = (
            {"point_micros": 799_999},
            {"lower_95_micros": 669_999},
            {"point_micros": None},
            {"lower_95_micros": None},
            {"upper_95_micros": None},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                payload = self.valid_result()
                diagnostic = payload["per_signal"][2][
                    "reliability_diagnostics"
                ][0]
                diagnostic.update(mutation)
                self.reself(payload)
                for validate in (
                    self.validate_result,
                    self.render_result,
                ):
                    with self.subTest(validate=validate.__name__):
                        with self.assertRaisesRegex(
                            runner.RunnerError,
                            "reliability_diagnostics",
                        ):
                            validate(copy.deepcopy(payload))

    def test_v2_builder_exposes_bounded_rowless_witness_contract(self) -> None:
        result = self.valid_result()

        self.assertEqual(
            result["schema_version"],
            "EmotionStatePhaseC1AggregateResultV2",
        )
        self.assertEqual(set(result), EXPECTED_PHASE_C1_RESULT_FIELDS)
        self.assertIsInstance(result["search_lane_counts"], dict)
        self.assertIsInstance(result["source_signature_counts"], list)
        self.assertLessEqual(
            len(phase_c1.canonical_json_bytes(result)),
            512 * 1024,
        )
        self.assertIn(
            (
                "Sparse source signatures and per-card categorical "
                "diagnostics may fingerprint public source configurations."
            ),
            result["limitations"],
        )

    def test_v1_payload_is_rejected_even_after_self_hashing(self) -> None:
        payload = self.valid_result()
        payload["schema_version"] = "EmotionStatePhaseC1AggregateResultV1"
        self.assert_result_rejected(payload, "result_identity")

    def test_published_positive_count_cannot_exceed_rated_units(self) -> None:
        payload = self.deferred_result()
        payload["reason_code_counts"].update(
            {
                "reliability_unverifiable": 0,
                "reliability_effective_sample_insufficient": 1,
            }
        )
        payload["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "rated_unit_count": 50,
                "published_positive_count": 100,
                "effective_sample_sufficient": False,
            }
        )
        self.assert_result_rejected(
            payload,
            "reliability_diagnostics",
        )

    def test_rejected_card_status_is_rederived_from_local_facts(self) -> None:
        payload = self.rejected_alpha_result()
        payload["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "excluded_discovery_record_count": 1,
            }
        )
        payload["search_lane_counts"]["direct_by_signal"]["confusion"][
            "discovery_disposition_counts"
        ]["excluded"] = 1
        payload["reason_code_counts"].update(
            {
                "reliability_upper_below_0_67": 0,
                "single_rater": 1,
                "self_report_label": 1,
                "llm_generated_label": 1,
            }
        )
        payload["per_signal"][2]["reliability_diagnostics"][0].update(
            {
                "point_micros": 840_000,
                "lower_95_micros": 700_000,
                "upper_95_micros": 900_000,
                "independent_rater_count": 3,
            }
        )
        self.assert_result_rejected(
            payload,
            "reliability_diagnostics",
        )

    def test_lane_witness_rejects_record_stretch_and_fallback_anchor(
        self,
    ) -> None:
        stretched = self.valid_result()
        signature = stretched["source_signature_counts"][0]
        signature["direct_membership_by_signal"]["interest"] = True
        self.rehash_source_signature(stretched, signature)
        interest_lane = stretched["search_lane_counts"][
            "direct_by_signal"
        ]["interest"]
        interest_lane["candidate_order_count"] = 1
        interest_lane["discovery_disposition_counts"][
            "retained_candidate"
        ] = 1
        diagnostic = copy.deepcopy(
            stretched["per_signal"][2]["reliability_diagnostics"][0]
        )
        diagnostic["evidence_card_sha256"] = self.fixture_hash(
            "shared-interest-card"
        )
        diagnostic["source_signature_sha256"] = signature[
            "source_signature_sha256"
        ]
        stretched["per_signal"][3]["reliability_diagnostics"] = [
            diagnostic
        ]
        self.align_local_card_witnesses(stretched)
        self.assert_result_rejected(stretched, "search_lane_counts")

        shared = copy.deepcopy(stretched)
        shared["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "retained_candidate_record_count": 2,
            }
        )
        self.assert_result_rejected(
            shared,
            "evidence_card_binding",
        )

        fallback_only = self.all_fail_result()
        signature_payload = {
            "direct_membership_by_signal": {
                signal: False for signal in EXPECTED_SIGNALS
            },
            "fallback_material_membership": True,
            "existing_annotation_evidence_role": False,
            "fallback_material_candidate_role": True,
            "access_status": "public_no_login",
            "license_status": "compatible",
            "ethical_use_status": "compatible",
            "conversation_status": "spontaneous_conversation",
            "document_category_mask": 0b1000,
        }
        digest = phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(signature_payload)
        )
        fallback_only["source_signature_counts"] = [
            {
                "source_signature_sha256": digest,
                "count": 1,
                **signature_payload,
            }
        ]
        fallback_only["source_counts"].update(
            {
                "source_count": 1,
                "document_count": 1,
                "fallback_material_candidate_source_count": 1,
            }
        )
        fallback_only["search_counts"].update(
            {
                "returned_discovery_record_count": 1,
                "retained_candidate_record_count": 1,
                "detailed_candidate_count": 1,
                "backward_citation_record_count": 1,
            }
        )
        fallback_lane = fallback_only["search_lane_counts"][
            "fallback_material"
        ]
        fallback_lane["candidate_order_count"] = 1
        fallback_lane["discovery_disposition_counts"][
            "retained_candidate"
        ] = 1
        fallback_only["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]["citations"]["backward"]["disposition_counts"]["duplicate"] = 1
        self.assert_result_rejected(
            fallback_only,
            "search_lane_counts",
        )

    def test_source_signature_hash_role_mask_and_document_binding(
        self,
    ) -> None:
        payload = self.valid_result()
        entry = payload["source_signature_counts"][0]
        signature = {
            key: value
            for key, value in entry.items()
            if key not in {"source_signature_sha256", "count"}
        }
        expected_digest = phase_c1.sha256_bytes(
            phase_c1.canonical_json_bytes(signature)
        )
        self.assertEqual(entry["source_signature_sha256"], expected_digest)
        changed_count = {**entry, "count": 999}
        self.assertEqual(
            phase_c1.sha256_bytes(
                phase_c1.canonical_json_bytes(
                    {
                        key: value
                        for key, value in changed_count.items()
                        if key
                        not in {"source_signature_sha256", "count"}
                    }
                )
            ),
            expected_digest,
        )

        login_public = self.valid_result()
        entry = login_public["source_signature_counts"][0]
        entry["access_status"] = "login_required"
        self.rehash_source_signature(login_public, entry)
        self.assert_result_rejected(
            login_public,
            "source_signature_counts",
        )

        missing_role = self.valid_result()
        entry = missing_role["source_signature_counts"][0]
        entry["existing_annotation_evidence_role"] = False
        self.rehash_source_signature(missing_role, entry)
        self.assert_result_rejected(
            missing_role,
            "source_signature_counts",
        )

        empty_mask = self.valid_result()
        entry = empty_mask["source_signature_counts"][0]
        entry["document_category_mask"] = 0
        self.rehash_source_signature(empty_mask, entry)
        self.assert_result_rejected(
            empty_mask,
            "source_signature_counts",
        )

        wrong_document_category = self.valid_result()
        diagnostic = wrong_document_category["per_signal"][2][
            "reliability_diagnostics"
        ][0]
        diagnostic["definition_document_authoritative"] = False
        self.assert_result_rejected(
            wrong_document_category,
            "reliability_diagnostics",
        )

        unsorted = self.full_pass_result()
        unsorted["source_signature_counts"].reverse()
        self.assert_result_rejected(
            unsorted,
            "source_signature_counts",
        )

    def test_local_oracle_outcomes_and_decision_helper_independence(
        self,
    ) -> None:
        cases = (
            (
                "proxy",
                {},
                {"native_label_is_excluded_proxy": True},
                "rejected",
                ("proxy_construct",),
            ),
            (
                "license_unresolved",
                {"license_status": "unresolved"},
                {},
                "unresolved",
                ("license_unresolved",),
            ),
            (
                "self_report",
                {},
                {"observer_method": "self_report"},
                "rejected",
                ("self_report_label",),
            ),
            (
                "single_rater",
                {},
                {
                    "independent_rater_count": 1,
                    "effective_sample_sufficient": False,
                },
                "rejected",
                ("single_rater",),
            ),
            (
                "alpha_reject",
                {},
                {
                    "point_micros": 650_000,
                    "lower_95_micros": 590_000,
                    "upper_95_micros": 669_999,
                },
                "rejected",
                ("reliability_upper_below_0_67",),
            ),
            (
                "alpha_defer",
                {},
                {
                    "point_micros": 750_000,
                    "lower_95_micros": 650_000,
                    "upper_95_micros": 850_000,
                },
                "unresolved",
                ("reliability_interval_uncertain",),
            ),
            (
                "positive_support",
                {},
                {
                    "published_positive_count": 92,
                    "effective_sample_sufficient": False,
                },
                "unresolved",
                (
                    "reliability_effective_sample_insufficient",
                    "positive_support_below_93",
                ),
            ),
        )
        for (
            name,
            signature_updates,
            diagnostic_updates,
            expected_status,
            expected_reasons,
        ) in cases:
            with self.subTest(name=name):
                payload = self.valid_result()
                entry = payload["source_signature_counts"][0]
                entry.update(signature_updates)
                if signature_updates:
                    self.rehash_source_signature(payload, entry)
                diagnostic = payload["per_signal"][2][
                    "reliability_diagnostics"
                ][0]
                diagnostic.update(diagnostic_updates)
                actual = self.reference_diagnostic_disposition(
                    diagnostic,
                    entry,
                )
                self.assertEqual(
                    actual,
                    (expected_status, expected_reasons),
                )
                self.align_local_card_witnesses(payload)
                self.reself(payload)
                self.validate_result(payload)
                self.render_result(payload)

        payload = self.valid_result()
        with (
            mock.patch.object(
                decision,
                "derive_candidate_disposition",
                side_effect=AssertionError("decision helper called"),
            ),
            mock.patch.object(
                decision,
                "derive_reliability_status",
                side_effect=AssertionError("decision helper called"),
            ),
            mock.patch.object(
                decision,
                "derive_signal_decision",
                side_effect=AssertionError("decision helper called"),
            ),
        ):
            self.validate_local_result(payload)
            self.render_local_result(payload)

    def test_exact_residual_reconciliation_and_zero_search_meta(
        self,
    ) -> None:
        rejected_search = self.valid_result()
        rejected_search["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "excluded_discovery_record_count": 1,
            }
        )
        rejected_search["search_lane_counts"]["direct_by_signal"][
            "confusion"
        ]["discovery_disposition_counts"]["excluded"] = 1
        rejected_search["reason_code_counts"]["access_restricted"] = 1
        self.reself(rejected_search)
        self.validate_result(rejected_search)
        self.render_result(rejected_search)

        split = self.deferred_result()
        split["per_signal"][2]["annotation_fallback"] = "unresolved"
        split["reason_code_counts"]["annotation_fallback_unresolved"] = 1
        diagnostic = split["per_signal"][2][
            "reliability_diagnostics"
        ][0]
        diagnostic.update(
            {
                "verifiable": True,
                "rated_unit_count": None,
                "published_positive_count": 92,
                "effective_sample_sufficient": False,
            }
        )
        self.align_local_card_witnesses(split)
        split["search_counts"].update(
            {
                "returned_discovery_record_count": 2,
                "unresolved_discovery_record_count": 1,
            }
        )
        split["search_lane_counts"]["direct_by_signal"]["confusion"][
            "discovery_disposition_counts"
        ]["unresolved"] = 1
        split["reason_code_counts"]["source_identity_unverified"] = 1
        self.align_local_card_witnesses(split)
        self.reself(split)
        self.validate_result(split)
        self.render_result(split)

        missing_residual = copy.deepcopy(split)
        missing_residual["reason_code_counts"][
            "source_identity_unverified"
        ] = 0
        self.assert_result_rejected(
            missing_residual,
            "reason_code_counts",
        )

        for code in (
            "search_query_incomplete",
            "query_result_truncated",
            "candidate_overflow",
            "citation_budget_incomplete",
        ):
            with self.subTest(search_meta=code):
                invalid = self.valid_result()
                invalid["reason_code_counts"][code] = 1
                self.assert_result_rejected(
                    invalid,
                    "reason_code_counts",
                )

    def test_fail_ready_is_rederived_from_lane_facts(self) -> None:
        payload = self.all_fail_result()
        payload["search_counts"].update(
            {
                "complete_query_count": 87,
                "incomplete_query_count": 1,
                "search_complete": False,
            }
        )
        query_counts = payload["search_lane_counts"][
            "direct_by_signal"
        ]["hesitation"]["query_counts"]
        query_counts.update({"complete": 15, "incomplete": 1})
        payload["per_signal"][0]["annotation_fallback"] = "unresolved"
        payload["reason_code_counts"]["annotation_fallback_unresolved"] = 1
        self.align_local_card_witnesses(payload)
        self.reself(payload)
        self.validate_result(payload)
        self.render_result(payload)
        self.assertEqual(payload["per_signal"][0]["decision"], "defer")

        false_fail = copy.deepcopy(payload)
        false_fail["per_signal"][0].update(
            {
                "decision": "fail",
                "annotation_fallback": "infeasible",
                "c2_eligible": False,
            }
        )
        false_fail["reason_code_counts"][
            "annotation_fallback_unresolved"
        ] = 0
        false_fail["overall_decision"] = "stop_c2"
        self.assert_result_rejected(false_fail, "per_signal")

    def test_maximum_card_shape_size_is_measured_below_frozen_cap(
        self,
    ) -> None:
        payload = self.full_pass_result()
        source_payload = phase_c1.load_json_strict(
            self.source_ledger_bytes_for(payload),
            source="source_ledger",
        )
        self.assertIsInstance(source_payload, dict)
        source_cards = source_payload["cards"]
        self.assertIsInstance(source_cards, list)
        card_template_by_signal = {
            card["signal"]: card for card in source_cards
        }
        expanded_cards: list[dict[str, object]] = []
        card_hashes_by_signal: dict[str, list[str]] = {
            signal: [] for signal in EXPECTED_SIGNALS
        }
        for signal in EXPECTED_SIGNALS:
            for index in range(20):
                card = copy.deepcopy(card_template_by_signal[signal])
                card["card_id"] = f"c1-card-{signal}-{index + 1:04d}"
                phase_c1.parse_evidence_card(card)
                expanded_cards.append(card)
                card_hashes_by_signal[signal].append(
                    phase_c1.sha256_bytes(
                        phase_c1.canonical_json_bytes(card)
                    )
                )
        source_payload["cards"] = expanded_cards
        maximum_source_bytes = phase_c1.canonical_json_bytes(source_payload)
        maximum_source_sha256 = phase_c1.sha256_bytes(
            maximum_source_bytes
        )
        payload["source_evidence_ledger_sha256"] = maximum_source_sha256
        self.source_ledger_bytes_by_sha256[
            maximum_source_sha256
        ] = maximum_source_bytes
        for entry in payload["source_signature_counts"]:
            entry["count"] = 20
        payload["source_counts"].update(
            {
                "source_count": 100,
                "document_count": 100,
                "existing_annotation_evidence_source_count": 100,
                "fallback_material_candidate_source_count": 100,
            }
        )
        payload["search_counts"].update(
            {
                "returned_discovery_record_count": 100,
                "retained_candidate_record_count": 100,
                "detailed_candidate_count": 100,
            }
        )
        signatures_by_signal = {
            signal: next(
                entry["source_signature_sha256"]
                for entry in payload["source_signature_counts"]
                if entry["direct_membership_by_signal"][signal]
            )
            for signal in EXPECTED_SIGNALS
        }
        for item in payload["per_signal"]:
            signal = item["signal"]
            lane = payload["search_lane_counts"]["direct_by_signal"][
                signal
            ]
            lane["candidate_order_count"] = 20
            lane["discovery_disposition_counts"][
                "retained_candidate"
            ] = 20
            template = item["reliability_diagnostics"][0]
            diagnostics = []
            for index in range(20):
                diagnostic = copy.deepcopy(template)
                diagnostic["evidence_card_sha256"] = (
                    card_hashes_by_signal[signal][index]
                )
                diagnostic["source_signature_sha256"] = (
                    signatures_by_signal[signal]
                )
                diagnostics.append(diagnostic)
            item["reliability_diagnostics"] = diagnostics
        self.align_local_card_witnesses(payload)
        self.reself(payload)
        self.validate_result(payload)
        measured_size = len(phase_c1.canonical_json_bytes(payload))
        self.assertEqual(runner.MAX_AGGREGATE_RESULT_BYTES, 512 * 1024)
        self.assertLessEqual(
            measured_size,
            runner.MAX_AGGREGATE_RESULT_BYTES,
        )
        self.assertEqual(measured_size, 155_411)

        reordered = copy.deepcopy(payload)
        reordered_signal = reordered["per_signal"][0]
        reordered_signal["reliability_diagnostics"][0:2] = reversed(
            reordered_signal["reliability_diagnostics"][0:2]
        )
        reordered_signal["admissible_evidence_card_sha256s"][0:2] = reversed(
            reordered_signal["admissible_evidence_card_sha256s"][0:2]
        )
        self.reself(reordered)
        self.assert_result_rejected(
            reordered,
            "evidence_card_binding",
        )

    def test_fallback_material_status_counts_are_locally_witnessed(self) -> None:
        payload = self.fallback_result(("infeasible",))
        for item in payload["per_signal"]:
            self.assertEqual(
                item["fallback_material_status_counts"],
                {"feasible": 0, "infeasible": 1, "unresolved": 0},
            )

    def test_forged_all_infeasible_fallback_cannot_become_feasible(
        self,
    ) -> None:
        payload = self.fallback_result(("infeasible",))
        self.assertTrue(
            all(
                item["annotation_fallback"] == "infeasible"
                for item in payload["per_signal"]
            )
        )
        for item in payload["per_signal"]:
            item.update(
                {
                    "annotation_fallback": "feasible",
                    "decision": "defer",
                    "c2_eligible": False,
                }
            )
        payload["reason_code_counts"]["annotation_fallback_feasible"] = 5
        payload["overall_decision"] = "defer_c2"
        self.reself(payload)
        self.assert_result_rejected(payload, "per_signal")

    def test_lane_discovery_capacity_and_overflow_saturation_are_local(
        self,
    ) -> None:
        zero_complete = self.valid_result()
        zero_complete["search_counts"].update(
            {
                "complete_query_count": 72,
                "incomplete_query_count": 16,
                "search_complete": False,
            }
        )
        zero_complete["search_lane_counts"]["direct_by_signal"]["confusion"][
            "query_counts"
        ].update({"complete": 0, "incomplete": 16})
        self.reself(zero_complete)
        self.assert_result_rejected(zero_complete, "search_lane_counts")

        direct_unsaturated = self.all_fail_result()
        direct_counts = direct_unsaturated["search_counts"]
        direct_counts.update(
            {
                "returned_discovery_record_count": 20,
                "retained_candidate_record_count": 20,
                "detailed_candidate_count": 19,
                "candidate_overflow_count": 1,
            }
        )
        direct_lane = direct_unsaturated["search_lane_counts"][
            "direct_by_signal"
        ]["hesitation"]
        direct_lane.update(
            {
                "candidate_order_count": 19,
                "candidate_overflow_count": 1,
            }
        )
        direct_lane["discovery_disposition_counts"][
            "retained_candidate"
        ] = 20
        runner._validate_search_counts(direct_counts)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "search_lane_counts",
        ):
            runner._validate_search_lane_counts(
                direct_unsaturated["search_lane_counts"],
                search_counts=direct_counts,
            )

        fallback_unsaturated = self.all_fail_result()
        fallback_counts = fallback_unsaturated["search_counts"]
        fallback_counts.update(
            {
                "returned_discovery_record_count": 11,
                "retained_candidate_record_count": 11,
                "detailed_candidate_count": 10,
                "candidate_overflow_count": 1,
            }
        )
        direct_lane = fallback_unsaturated["search_lane_counts"][
            "direct_by_signal"
        ]["hesitation"]
        direct_lane["candidate_order_count"] = 1
        direct_lane["discovery_disposition_counts"][
            "retained_candidate"
        ] = 1
        fallback_lane = fallback_unsaturated["search_lane_counts"][
            "fallback_material"
        ]
        fallback_lane.update(
            {
                "candidate_order_count": 9,
                "candidate_overflow_count": 1,
            }
        )
        fallback_lane["discovery_disposition_counts"][
            "retained_candidate"
        ] = 10
        runner._validate_search_counts(fallback_counts)
        with self.assertRaisesRegex(
            runner.RunnerError,
            "search_lane_counts",
        ):
            runner._validate_search_lane_counts(
                fallback_unsaturated["search_lane_counts"],
                search_counts=fallback_counts,
            )

    def test_source_signature_reconciles_exact_document_count(self) -> None:
        payload = self.valid_result()
        self.assertEqual(payload["source_counts"]["document_count"], 1)
        payload["source_counts"]["document_count"] = 2
        self.reself(payload)
        self.assert_result_rejected(payload, "source_signature_counts")

    def test_actual_oversized_payload_rejects_before_render(self) -> None:
        payload = self.valid_result()
        payload["implementation_head"] = "a" * (
            runner.MAX_AGGREGATE_RESULT_BYTES + 1
        )
        self.assertGreater(
            len(phase_c1.canonical_json_bytes(payload)),
            runner.MAX_AGGREGATE_RESULT_BYTES,
        )
        for validate in (
            self.validate_result,
            self.render_result,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "result_size",
                ):
                    validate(copy.deepcopy(payload))

    def test_source_ledger_bytes_are_required_hash_bound_and_canonical(
        self,
    ) -> None:
        payload = self.valid_result()
        authority_bytes = self.authoritative_input_bytes_for(payload)
        for validate in (
            runner.validate_phase_c1_result_payload,
            runner.render_phase_c1_report,
        ):
            for missing in authority_bytes:
                with self.subTest(
                    validate=validate.__name__,
                    mutation=f"missing_{missing}",
                ):
                    incomplete = dict(authority_bytes)
                    del incomplete[missing]
                    with self.assertRaisesRegex(TypeError, missing):
                        validate(copy.deepcopy(payload), **incomplete)

            with self.subTest(validate=validate.__name__, mutation="wrong"):
                wrong = dict(authority_bytes)
                wrong["source_ledger_bytes"] = b"{}\n"
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "source_ledger_hash",
                ):
                    validate(
                        copy.deepcopy(payload),
                        **wrong,
                    )

            source_payload = phase_c1.load_json_strict(
                self.one_pass_source_bytes,
                source="source_ledger",
            )
            noncanonical = json.dumps(
                source_payload,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            noncanonical_result = copy.deepcopy(payload)
            noncanonical_result["source_evidence_ledger_sha256"] = (
                phase_c1.sha256_bytes(noncanonical)
            )
            self.reself(noncanonical_result)
            with self.subTest(
                validate=validate.__name__,
                mutation="noncanonical",
            ):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "source_ledger_canonical",
                ):
                    validate(
                        noncanonical_result,
                        **{
                            **authority_bytes,
                            "source_ledger_bytes": noncanonical,
                        },
                    )

            mutated_source_payload = copy.deepcopy(source_payload)
            mutated_card = mutated_source_payload["cards"][0]
            mutated_card["limitations"] = [
                *mutated_card["limitations"],
                "source-ledger-binding-mutation",
            ]
            phase_c1.parse_evidence_card(mutated_card)
            mutated_source_bytes = phase_c1.canonical_json_bytes(
                mutated_source_payload
            )
            mutated_source_result = copy.deepcopy(payload)
            mutated_source_result["source_evidence_ledger_sha256"] = (
                phase_c1.sha256_bytes(mutated_source_bytes)
            )
            self.reself(mutated_source_result)
            with self.subTest(
                validate=validate.__name__,
                mutation="full_card_hash",
            ):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "evidence_card_binding",
                ):
                    validate(
                        mutated_source_result,
                        **{
                            **authority_bytes,
                            "source_ledger_bytes": mutated_source_bytes,
                        },
                    )

    def test_cross_signal_card_hash_swap_rejects_against_source_bytes(
        self,
    ) -> None:
        search_bytes, source_bytes, review_bytes = self.validated_input_bytes(
            admissible_signals=EXPECTED_SIGNALS,
        )
        payload = runner.build_phase_c1_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            protocol_bytes=self.protocol_bytes,
            search_ledger_bytes=search_bytes,
            source_ledger_bytes=source_bytes,
            review_receipt_bytes=review_bytes,
        )
        hesitation = payload["per_signal"][0]
        frustration = payload["per_signal"][1]
        hesitation_hash = hesitation["reliability_diagnostics"][0][
            "evidence_card_sha256"
        ]
        frustration_hash = frustration["reliability_diagnostics"][0][
            "evidence_card_sha256"
        ]
        hesitation["reliability_diagnostics"][0][
            "evidence_card_sha256"
        ] = frustration_hash
        frustration["reliability_diagnostics"][0][
            "evidence_card_sha256"
        ] = hesitation_hash
        hesitation["admissible_evidence_card_sha256s"] = [
            frustration_hash
        ]
        frustration["admissible_evidence_card_sha256s"] = [
            hesitation_hash
        ]
        self.reself(payload)
        for validate in (
            runner.validate_phase_c1_result_payload,
            runner.render_phase_c1_report,
        ):
            with self.subTest(validate=validate.__name__):
                with self.assertRaisesRegex(
                    runner.RunnerError,
                    "evidence_card_binding",
                ):
                    validate(
                        copy.deepcopy(payload),
                        protocol_bytes=self.protocol_bytes,
                        search_ledger_bytes=search_bytes,
                        source_ledger_bytes=source_bytes,
                        review_receipt_bytes=review_bytes,
                    )

    def test_all_four_canonical_input_interfaces_are_required(self) -> None:
        expected = (
            "protocol_bytes",
            "search_ledger_bytes",
            "source_ledger_bytes",
            "review_receipt_bytes",
        )
        for validate in (
            runner.validate_phase_c1_result_payload,
            runner.render_phase_c1_report,
        ):
            with self.subTest(validate=validate.__name__):
                signature = inspect.signature(validate)
                keyword_only = tuple(
                    name
                    for name, parameter in signature.parameters.items()
                    if parameter.kind is inspect.Parameter.KEYWORD_ONLY
                )
                self.assertEqual(keyword_only, expected)
        validator_source = inspect.getsource(
            runner.validate_phase_c1_result_payload
        )
        renderer_source = inspect.getsource(runner.render_phase_c1_report)
        builder_source = inspect.getsource(runner.build_phase_c1_result)
        projection_source = inspect.getsource(
            runner._project_phase_c1_result
        )
        self.assertIn("_validate_phase_c1_result_local", validator_source)
        self.assertIn("_project_phase_c1_result", validator_source)
        self.assertIn("input_projection_binding", validator_source)
        self.assertIn("validate_phase_c1_result_payload", renderer_source)
        self.assertIn("_project_phase_c1_result", builder_source)
        self.assertIn("validate_phase_c1_result_payload", builder_source)
        self.assertNotIn(
            "validate_phase_c1_result_payload",
            projection_source,
        )

    def test_all_four_authority_inputs_are_hash_and_canonical_bound(
        self,
    ) -> None:
        payload = self.valid_result()
        authority_bytes = self.authoritative_input_bytes_for(payload)
        metadata = {
            "protocol_bytes": ("protocol_sha256", "protocol"),
            "search_ledger_bytes": (
                "search_ledger_sha256",
                "search_ledger",
            ),
            "source_ledger_bytes": (
                "source_evidence_ledger_sha256",
                "source_ledger",
            ),
            "review_receipt_bytes": (
                "source_review_receipt_sha256",
                "source_review",
            ),
        }
        for argument_name, (result_field, source) in metadata.items():
            for validate in (
                runner.validate_phase_c1_result_payload,
                runner.render_phase_c1_report,
            ):
                with self.subTest(
                    validate=validate.__name__,
                    argument=argument_name,
                    mutation="wrong_hash",
                ):
                    wrong = dict(authority_bytes)
                    wrong[argument_name] = b"{}\n"
                    with self.assertRaisesRegex(
                        runner.RunnerError,
                        f"{source}_hash",
                    ):
                        validate(copy.deepcopy(payload), **wrong)

                source_payload = phase_c1.load_json_strict(
                    authority_bytes[argument_name],
                    source=source,
                )
                noncanonical = json.dumps(
                    source_payload,
                    sort_keys=True,
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode("utf-8")
                noncanonical_result = copy.deepcopy(payload)
                noncanonical_result[result_field] = phase_c1.sha256_bytes(
                    noncanonical
                )
                self.reself(noncanonical_result)
                with self.subTest(
                    validate=validate.__name__,
                    argument=argument_name,
                    mutation="noncanonical",
                ):
                    noncanonical_authority = dict(authority_bytes)
                    noncanonical_authority[argument_name] = noncanonical
                    with self.assertRaisesRegex(
                        runner.RunnerError,
                        f"{source}_canonical",
                    ):
                        validate(
                            noncanonical_result,
                            **noncanonical_authority,
                        )

                wrong_schema_payload = copy.deepcopy(source_payload)
                wrong_schema_payload["schema_version"] = "WrongSchemaV1"
                wrong_schema = phase_c1.canonical_json_bytes(
                    wrong_schema_payload
                )
                wrong_schema_result = copy.deepcopy(payload)
                wrong_schema_result[result_field] = phase_c1.sha256_bytes(
                    wrong_schema
                )
                self.reself(wrong_schema_result)
                with self.subTest(
                    validate=validate.__name__,
                    argument=argument_name,
                    mutation="wrong_schema",
                ):
                    wrong_schema_authority = dict(authority_bytes)
                    wrong_schema_authority[argument_name] = wrong_schema
                    with self.assertRaises(runner.RunnerError):
                        validate(
                            wrong_schema_result,
                            **wrong_schema_authority,
                        )

    def test_four_canonical_inputs_block_coherent_semantic_rewrites(
        self,
    ) -> None:
        unresolved = self.deferred_result()
        unresolved_authority = self.authoritative_input_bytes_for(
            unresolved
        )
        confusion = unresolved["per_signal"][2]
        diagnostic = confusion["reliability_diagnostics"][0]
        diagnostic.update(
            {
                "claimed_status": "admissible",
                "claimed_reason_codes": [],
                "verifiable": True,
            }
        )
        confusion.update(
            {
                "decision": "pass",
                "admissible_evidence_card_sha256s": [
                    diagnostic["evidence_card_sha256"]
                ],
                "unresolved_card_count": 0,
                "c2_eligible": True,
            }
        )
        unresolved["card_counts_by_status"].update(
            {"admissible": 1, "unresolved": 0}
        )
        unresolved["reason_code_counts"]["reliability_unverifiable"] = 0
        unresolved["c2_eligible_signals"] = ["confusion"]
        unresolved["overall_decision"] = "proceed_partial_to_c2"
        with self.subTest(mutation="unresolved_card_to_c2_pass"):
            self.assert_projection_rejected(
                unresolved,
                authority_bytes=unresolved_authority,
            )

        blocked_review = self.valid_result()
        blocked_authority = self.authoritative_input_bytes_for(
            blocked_review
        )
        review_payload = phase_c1.load_json_strict(
            blocked_authority["review_receipt_bytes"],
            source="review",
        )
        review_payload.update(
            {
                "verdict": "blocked",
                "important_findings": 1,
            }
        )
        blocked_review_bytes = phase_c1.canonical_json_bytes(review_payload)
        blocked_review["source_review_receipt_sha256"] = (
            phase_c1.sha256_bytes(blocked_review_bytes)
        )
        blocked_authority["review_receipt_bytes"] = blocked_review_bytes
        with self.subTest(mutation="blocked_review_to_pass"):
            self.assert_projection_rejected(
                blocked_review,
                authority_bytes=blocked_authority,
            )

        rewritten_search = self.all_fail_result()
        rewritten_search_authority = self.authoritative_input_bytes_for(
            rewritten_search
        )
        rewritten_search["search_counts"].update(
            {
                "complete_query_count": 87,
                "incomplete_query_count": 1,
                "search_complete": False,
            }
        )
        rewritten_search["search_lane_counts"]["direct_by_signal"][
            "hesitation"
        ]["query_counts"].update(
            {"complete": 15, "incomplete": 1}
        )
        rewritten_search["per_signal"][0][
            "annotation_fallback"
        ] = "unresolved"
        rewritten_search["reason_code_counts"][
            "annotation_fallback_unresolved"
        ] = 1
        self.align_local_card_witnesses(rewritten_search)
        with self.subTest(mutation="search_facts_rewritten"):
            self.assert_projection_rejected(
                rewritten_search,
                authority_bytes=rewritten_search_authority,
            )

        incompatible_license = self.valid_result()
        incompatible_authority = self.authoritative_input_bytes_for(
            incompatible_license
        )
        incompatible_source = phase_c1.load_json_strict(
            incompatible_authority["source_ledger_bytes"],
            source="source",
        )
        incompatible_source["sources"][0]["license_status"] = "incompatible"
        incompatible_source_bytes = phase_c1.canonical_json_bytes(
            incompatible_source
        )
        incompatible_license["source_evidence_ledger_sha256"] = (
            phase_c1.sha256_bytes(incompatible_source_bytes)
        )
        incompatible_authority[
            "source_ledger_bytes"
        ] = incompatible_source_bytes
        with self.subTest(mutation="incompatible_license_to_pass"):
            self.assert_projection_rejected(
                incompatible_license,
                authority_bytes=incompatible_authority,
            )

        feasible_fallback = self.fallback_result(("infeasible",))
        feasible_authority = self.authoritative_input_bytes_for(
            feasible_fallback
        )
        for item in feasible_fallback["per_signal"]:
            item.update(
                {
                    "decision": "defer",
                    "annotation_fallback": "feasible",
                    "fallback_material_status_counts": {
                        "feasible": 1,
                        "infeasible": 0,
                        "unresolved": 0,
                    },
                    "c2_eligible": False,
                }
            )
        feasible_fallback["reason_code_counts"][
            "annotation_fallback_feasible"
        ] = len(EXPECTED_SIGNALS)
        feasible_fallback["overall_decision"] = "defer_c2"
        with self.subTest(mutation="infeasible_fallback_to_feasible"):
            self.assert_projection_rejected(
                feasible_fallback,
                authority_bytes=feasible_authority,
            )

        forged_source_links = self.valid_result()
        forged_source_authority = self.authoritative_input_bytes_for(
            forged_source_links
        )
        forged_source = phase_c1.load_json_strict(
            forged_source_authority["source_ledger_bytes"],
            source="source",
        )
        forged_source.update(
            {
                "protocol_sha256": "A" * 64,
                "search_ledger_sha256": "B" * 64,
            }
        )
        forged_source_bytes = phase_c1.canonical_json_bytes(forged_source)
        forged_source_links["source_evidence_ledger_sha256"] = (
            phase_c1.sha256_bytes(forged_source_bytes)
        )
        forged_source_authority["source_ledger_bytes"] = forged_source_bytes
        with self.subTest(mutation="source_link_hashes_rebound"):
            self.assert_projection_rejected(
                forged_source_links,
                authority_bytes=forged_source_authority,
            )

        rebound_result = self.valid_result()
        rebound_authority = self.authoritative_input_bytes_for(rebound_result)
        rebound_result.update(
            {
                "protocol_sha256": "A" * 64,
                "search_ledger_sha256": "B" * 64,
            }
        )
        with self.subTest(mutation="result_input_hashes_rebound"):
            self.assert_projection_rejected(
                rebound_result,
                authority_bytes=rebound_authority,
            )

    def test_normative_limitation_lists_are_exact_ten_item_contracts(
        self,
    ) -> None:
        plan_text = (
            ROOT
            / "docs"
            / "superpowers"
            / "plans"
            / (
                "2026-07-26-emotion-state-phase-c1-operational-signal-"
                "evidence-admission.md"
            )
        ).read_text(encoding="utf-8")
        plan_block = plan_text.split(
            "Canonical limitations use this exact order and wording:",
            1,
        )[1].split("- Every JSON byte authority uses:", 1)[0]
        self.assertEqual(
            plan_block.count('    "'),
            len(EXPECTED_PHASE_C1_LIMITATIONS),
        )
        for limitation in EXPECTED_PHASE_C1_LIMITATIONS:
            with self.subTest(document="plan", limitation=limitation):
                self.assertIn(f'"{limitation}"', plan_block)

        spec_text = (
            ROOT
            / "docs"
            / "superpowers"
            / "specs"
            / (
                "2026-07-26-emotion-state-phase-c1-operational-signal-"
                "evidence-admission-design.md"
            )
        ).read_text(encoding="utf-8")
        spec_block = spec_text.split(
            "## Risks And Limitations",
            1,
        )[1].split("## Explicit Exclusions", 1)[0]
        self.assertEqual(
            sum(
                line.startswith("- ")
                for line in spec_block.splitlines()
            ),
            len(EXPECTED_PHASE_C1_LIMITATIONS),
        )
        normalized_spec = " ".join(spec_block.split())
        for limitation in EXPECTED_PHASE_C1_LIMITATIONS:
            with self.subTest(document="spec", limitation=limitation):
                self.assertIn(limitation, normalized_spec)

    def test_retired_v1_solver_bodies_are_absent_and_scanner_is_nonvacuous(
        self,
    ) -> None:
        retired_names = frozenset(RETIRED_V1_TEST_METHOD_NAMES)
        self.assertEqual(len(retired_names), 13)
        synthetic_tree = ast.parse(
            "class SyntheticRetiredTests:\n"
            f"    def {RETIRED_V1_TEST_METHOD_NAMES[0]}(self):\n"
            "        pass\n"
        )
        synthetic_names = {
            node.name
            for node in ast.walk(synthetic_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertEqual(
            synthetic_names & retired_names,
            {RETIRED_V1_TEST_METHOD_NAMES[0]},
        )

        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        current_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertTrue(retired_names.isdisjoint(current_names))


def _phase_c1_publication_lock_contender(
    lock_path: str,
    result_queue: multiprocessing.queues.Queue[bool],
) -> None:
    """Attempt the production OS lock from a separate Windows/POSIX process."""
    handle = open(lock_path, "r+b")
    try:
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                result_queue.put(False)
                return
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                result_queue.put(False)
                return
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        result_queue.put(True)
    finally:
        handle.close()

class PhaseC1PublicationTransactionTests(
    _PhaseC1FixtureMixin,
    unittest.TestCase,
):
    """Temporary-root contract tests for the Task 9 publication protocol.

    These tests deliberately name the public transaction API before it exists.
    They must never use the repository candidate/canonical roots.
    """

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="emotion-state-c1-publication-",
        )
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp_root = Path(self.temporary_directory.name)
        self.protocol_bytes = self.protocol_path.read_bytes()
        self.protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        self.input_paths = {
            "protocol_path": (
                self.temp_root / "research" / "experiments" / "configs"
                / "emotion-state-004-phase-c1-discovery-protocol.json"
            ),
            "search_ledger_path": (
                self.temp_root / "research" / "sources" / "emotion_state"
                / "phase_c1_search_ledger.json"
            ),
            "source_ledger_path": (
                self.temp_root / "research" / "sources" / "emotion_state"
                / "phase_c1_source_evidence_ledger.json"
            ),
            "source_review_path": (
                self.temp_root / "research" / "sources" / "emotion_state"
                / "phase_c1_source_review_receipt.json"
            ),
        }
        self.seed_valid_tracked_inputs()
        (
            self.expected_candidate_result_bytes,
            self.expected_candidate_report_bytes,
        ) = self.derive_expected_pair_without_publication_helpers()

    def build_explicit_temp_runner_paths(
        self, root: Path,
    ) -> "runner.PhaseC1RunnerPaths":
        """Build every Task 9 path explicitly and pin it below ``root``."""
        candidate_root = root / ".tmp" / "emotion-state-004-phase-c1" / "candidate"
        canonical_root = (
            root / "research" / "experiments" / "generated"
            / "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission"
        )
        ignored_root = root / ".tmp" / "emotion-state-004-phase-c1"
        values = {
            "project_root": root,
            **self.input_paths,
            "ignored_root": ignored_root,
            "candidate_root": candidate_root,
            "candidate_receipt_path": ignored_root / "candidate-receipt.json",
            "candidate_receipt_stage_path": ignored_root / "candidate-receipt.stage",
            "candidate_validation_path": ignored_root / "candidate-validation.json",
            "candidate_validation_stage_path": (
                ignored_root / "candidate-validation.stage"
            ),
            "candidate_review_path": ignored_root / "candidate-review.json",
            "candidate_review_stage_path": (
                ignored_root / "candidate-review.stage"
            ),
            "publication_lock_path": ignored_root / "publication.lock",
            "publication_journal_path": ignored_root / "publication-journal.json",
            "publication_journal_stage_path": ignored_root / "publication-journal.stage",
            "candidate_stage_path": ignored_root / "candidate.stage",
            "canonical_stage_path": ignored_root / "canonical.stage",
            "canonical_root": canonical_root,
        }
        self.assertEqual(
            tuple(values),
            (
                "project_root", "protocol_path", "search_ledger_path",
                "source_ledger_path", "source_review_path", "ignored_root",
                "candidate_root", "candidate_receipt_path",
                "candidate_receipt_stage_path", "candidate_validation_path",
                "candidate_validation_stage_path", "candidate_review_path",
                "candidate_review_stage_path", "publication_lock_path",
                "publication_journal_path",
                "publication_journal_stage_path", "candidate_stage_path",
                "canonical_stage_path", "canonical_root",
            ),
        )
        resolved_root = root.resolve()
        for value in values.values():
            resolved = Path(value).resolve()
            self.assertTrue(resolved.is_relative_to(resolved_root), value)
        return runner.PhaseC1RunnerPaths(**values)

    def runner_context(
        self,
    ) -> tuple["runner.PhaseC1RunnerPaths", mock._patch, mock._patch]:
        """Patch fixed paths plus the private clean Git/validator-state seam."""
        paths = self.build_explicit_temp_runner_paths(self.temp_root)
        paths_patch = mock.patch.object(
            runner, "PRODUCTION_PATHS", paths, create=True,
        )
        head_patch = mock.patch.object(
            runner, "_current_repository_head", return_value="a" * 40,
            create=True,
        )
        self.validator_state_patch = mock.patch.object(
            runner,
            "_resolve_phase_c1_validator_state",
            return_value={
                "repository_head": "a" * 40,
                "validator_blob_id": "b" * 40,
                "is_clean": True,
            },
            create=True,
        )
        paths_patch.start()
        head_patch.start()
        self.validator_state_patch.start()
        return paths, paths_patch, head_patch

    def stop_runner_context(
        self,
        paths_patch: mock._patch,
        head_patch: mock._patch,
    ) -> None:
        self.validator_state_patch.stop()
        head_patch.stop()
        paths_patch.stop()

    def validator_context(self) -> mock._patch:
        return mock.patch.multiple(
            validator,
            ROOT=self.temp_root,
            PROTOCOL_PATH=self.input_paths["protocol_path"],
            SEARCH_LEDGER_PATH=self.input_paths["search_ledger_path"],
            SOURCE_LEDGER_PATH=self.input_paths["source_ledger_path"],
            SOURCE_REVIEW_PATH=self.input_paths["source_review_path"],
            CANDIDATE_ROOT=self.candidate_root,
            CANONICAL_ROOT=self.canonical_root,
        )

    @property
    def candidate_root(self) -> Path:
        return self.temp_root / ".tmp" / "emotion-state-004-phase-c1" / "candidate"

    @property
    def canonical_root(self) -> Path:
        return (
            self.temp_root / "research" / "experiments" / "generated"
            / "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission"
        )

    @property
    def ignored_root(self) -> Path:
        return self.temp_root / ".tmp" / "emotion-state-004-phase-c1"

    def seed_valid_tracked_inputs(self) -> None:
        authority = self.authority_bytes(admissible_signals=("confusion",))
        mapping = {
            "protocol_bytes": self.input_paths["protocol_path"],
            "search_ledger_bytes": self.input_paths["search_ledger_path"],
            "source_ledger_bytes": self.input_paths["source_ledger_path"],
            "review_receipt_bytes": self.input_paths["source_review_path"],
        }
        for name, path in mapping.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(authority[name])
        self.authority = authority

    def authority_bytes(self, *, admissible_signals: tuple[str, ...]) -> dict[str, bytes]:
        search, source_ledger, review = PhaseC1DecisionTests.validated_projection_inputs(
            self, admissible_signals=admissible_signals,
        )
        return {
            "protocol_bytes": self.protocol_bytes,
            "search_ledger_bytes": PhaseC1IndependentValidatorTests.canonical_dataclass_bytes(
                search, "EmotionStatePhaseC1SearchLedgerV1",
            ),
            "source_ledger_bytes": PhaseC1IndependentValidatorTests.canonical_dataclass_bytes(
                source_ledger, "EmotionStatePhaseC1SourceEvidenceLedgerV1",
            ),
            "review_receipt_bytes": PhaseC1IndependentValidatorTests.canonical_dataclass_bytes(
                review, "EmotionStatePhaseC1SourceReviewReceiptV1",
            ),
        }

    def derive_expected_pair_without_publication_helpers(self) -> tuple[bytes, bytes]:
        result = runner.build_phase_c1_result(
            head_commit="a" * 40,
            validator_blob_id="b" * 40,
            **self.authority,
        )
        return (
            phase_c1.canonical_json_bytes(result),
            runner.render_phase_c1_report(result, **self.authority),
        )

    def prepared_candidate(self) -> "runner.PreparedPhaseC1Publication":
        return runner.prepare_phase_c1_candidate(expected_head="a" * 40)

    def lock(
        self, prepared: "runner.PreparedPhaseC1Publication",
    ) -> ContextManager["runner.PhaseC1PublicationLockCapability"]:
        return runner.persistent_phase_c1_publication_lock(prepared)

    def assert_no_candidate_overwrite(self) -> None:
        self.assertFalse(self.candidate_root.exists())
        self.assertFalse(self.canonical_root.exists())

    def create_test_reparse(self, link: Path, target: Path) -> None:
        """Create a real reparse point without requiring Windows symlink privilege."""
        self.assertFalse(os.path.lexists(link))
        try:
            os.symlink(str(target.resolve()), link)
        except OSError as exc:
            if os.name != "nt" or getattr(exc, "winerror", None) != 1314:
                raise
            junction_target = target
            if not target.is_dir():
                junction_target = target.with_name(target.name + "-junction-target")
                junction_target.mkdir()
                (junction_target / "sentinel").write_bytes(target.read_bytes())
            result = subprocess.run(
                [
                    os.environ.get("COMSPEC", "cmd.exe"),
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(link),
                    str(junction_target),
                ],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=(
                    f"junction stdout={result.stdout!r} "
                    f"stderr={result.stderr!r}"
                ),
            )
        metadata = os.stat(link, follow_symlinks=False)
        self.assertTrue(
            stat.S_ISLNK(metadata.st_mode)
            or bool(getattr(metadata, "st_reparse_tag", 0)),
        )

    @staticmethod
    def snapshot_test_child(path: Path) -> tuple[object, ...]:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or bool(getattr(metadata, "st_reparse_tag", 0))
        ):
            return (
                metadata.st_mode,
                metadata.st_ino,
                "reparse",
                getattr(metadata, "st_reparse_tag", 0),
            )
        return (metadata.st_mode, metadata.st_ino, path.read_bytes())

    @contextlib.contextmanager
    def isolated_mutation_root(self) -> Iterator[None]:
        """Give every race mutation a new OS-owned root and no residual state."""
        saved_root = self.temp_root
        saved_paths = self.input_paths
        saved_authority = self.authority
        saved_result = self.expected_candidate_result_bytes
        saved_report = self.expected_candidate_report_bytes
        with tempfile.TemporaryDirectory(prefix="emotion-state-c1-race-") as name:
            self.temp_root = Path(name)
            self.input_paths = {
                "protocol_path": self.temp_root / "research" / "experiments"
                / "configs" / "emotion-state-004-phase-c1-discovery-protocol.json",
                "search_ledger_path": self.temp_root / "research" / "sources"
                / "emotion_state" / "phase_c1_search_ledger.json",
                "source_ledger_path": self.temp_root / "research" / "sources"
                / "emotion_state" / "phase_c1_source_evidence_ledger.json",
                "source_review_path": self.temp_root / "research" / "sources"
                / "emotion_state" / "phase_c1_source_review_receipt.json",
            }
            self.seed_valid_tracked_inputs()
            (
                self.expected_candidate_result_bytes,
                self.expected_candidate_report_bytes,
            ) = self.derive_expected_pair_without_publication_helpers()
            yield
        self.temp_root = saved_root
        self.input_paths = saved_paths
        self.authority = saved_authority
        self.expected_candidate_result_bytes = saved_result
        self.expected_candidate_report_bytes = saved_report

    def assert_recoverable_publication_state(
        self, paths: "runner.PhaseC1RunnerPaths",
    ) -> None:
        journal = self.ignored_root / "publication-journal.json"
        stage = self.ignored_root / "publication-journal.stage"
        self.assertFalse(
            stage.exists() and not journal.exists(),
            "a failed publication may not leave an unanchored journal stage",
        )
        if journal.exists():
            payload = phase_c1.load_json_strict(journal.read_bytes(), source="journal")
            self.assertIsInstance(payload, dict)
            self.assertIn(payload["status"], {
                "staging_candidate", "candidate_ready", "staging_canonical",
                "accepted",
            })
            if self.canonical_root.exists():
                self.assertIn(payload["status"], {
                    "staging_canonical", "accepted",
                })
                self.assertEqual(
                    (self.canonical_root / "result.json").read_bytes(),
                    self.expected_candidate_result_bytes,
                )
        else:
            self.assertFalse(self.canonical_root.exists())
        self.assertTrue(Path(getattr(paths, "ignored_root")).is_relative_to(self.temp_root))

    def assert_finalize_rejects_after(self, mutation: str) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            replaced_root: Path | None = None
            try:
                prepared = self.prepared_candidate()
                if mutation == "root_identity":
                    replacement = self.temp_root.with_name(self.temp_root.name + "-old")
                    self.temp_root.rename(replacement)
                    self.temp_root.mkdir()
                    replaced_root = replacement
                    with self.assertRaises(runner.RunnerError):
                        with self.lock(prepared):
                            pass
                    return
                with self.lock(prepared) as capability:
                    if mutation == "head":
                        with mock.patch.object(
                            runner, "_current_repository_head", return_value="c" * 40,
                        ):
                            with self.assertRaises(runner.RunnerError):
                                runner.finalize_phase_c1_publication(
                                    prepared, capability=capability,
                                )
                            return
                    if mutation in {
                        "protocol", "search", "source_ledger", "source_review",
                    }:
                        path = self.input_paths[
                            {
                                "protocol": "protocol_path",
                                "search": "search_ledger_path",
                                "source_ledger": "source_ledger_path",
                                "source_review": "source_review_path",
                            }[mutation]
                        ]
                        path.write_bytes(path.read_bytes() + b" ")
                    elif mutation == "input_link":
                        source = self.input_paths["search_ledger_path"]
                        target = source.with_name("search-target.json")
                        source.rename(target)
                        self.create_test_reparse(source, target)
                    elif mutation == "parent_identity":
                        parent = self.input_paths["protocol_path"].parent
                        old_parent = parent.with_name("configs-old")
                        parent.rename(old_parent)
                        parent.mkdir()
                        (parent / self.input_paths["protocol_path"].name).write_bytes(
                            self.authority["protocol_bytes"]
                        )
                    elif mutation == "unexpected_child":
                        self.ignored_root.mkdir(parents=True, exist_ok=True)
                        (self.ignored_root / "unexpected").write_bytes(b"x")
                    elif mutation == "candidate_exists":
                        self.candidate_root.mkdir(parents=True)
                        (self.candidate_root / "result.json").write_bytes(b"old")
                    elif mutation == "canonical_exists":
                        self.canonical_root.mkdir(parents=True)
                        (self.canonical_root / "result.json").write_bytes(b"old")
                    elif mutation == "candidate_stage_exists":
                        self.ignored_root.mkdir(parents=True, exist_ok=True)
                        (self.ignored_root / "candidate.stage").mkdir()
                    elif mutation == "canonical_stage_exists":
                        self.ignored_root.mkdir(parents=True, exist_ok=True)
                        (self.ignored_root / "canonical.stage").mkdir()
                    elif mutation == "receipt_stage_exists":
                        self.ignored_root.mkdir(parents=True, exist_ok=True)
                        (self.ignored_root / "candidate-receipt.stage").write_bytes(b"old")
                    elif mutation == "fake_capability":
                        capability = object()
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared, capability=capability,
                        )
                    if mutation == "canonical_exists":
                        self.assertEqual(
                            (self.canonical_root / "result.json").read_bytes(), b"old",
                        )
                    else:
                        self.assertFalse(self.canonical_root.exists())
            finally:
                self.stop_runner_context(paths_patch, head_patch)
                if replaced_root is not None and replaced_root.exists():
                    shutil.rmtree(replaced_root)

    def test_prepare_and_caller_locked_finalize_are_byte_exact(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            prepared = self.prepared_candidate()
            with self.lock(prepared) as capability:
                receipt = runner.finalize_phase_c1_publication(
                    prepared, capability=capability,
                )
        finally:
            self.stop_runner_context(paths_patch, head_patch)
        self.assertEqual(
            (self.candidate_root / "result.json").read_bytes(),
            self.expected_candidate_result_bytes,
        )
        self.assertEqual(
            (self.candidate_root / "report.md").read_bytes(),
            self.expected_candidate_report_bytes,
        )
        self.assertEqual(receipt.status, "candidate_ready")

    def test_publication_types_are_opaque_and_not_constructible(self) -> None:
        for type_name in (
            "PreparedPhaseC1Publication",
            "PhaseC1PublicationLockCapability",
        ):
            with self.subTest(type_name=type_name):
                publication_type = getattr(runner, type_name)
                self.assertEqual(publication_type.__slots__, ("__weakref__",))
                with self.assertRaises(TypeError):
                    publication_type()

    def test_wrong_fake_reused_and_collected_capabilities_reject(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            prepared = self.prepared_candidate()
            with self.lock(prepared) as capability:
                with self.assertRaises(runner.RunnerError):
                    runner.finalize_phase_c1_publication(
                        prepared, capability=object(),
                    )
                runner.finalize_phase_c1_publication(
                    prepared, capability=capability,
                )
            with self.assertRaises(runner.RunnerError):
                runner.finalize_phase_c1_publication(
                    prepared, capability=capability,
                )
            abandoned = self.prepared_candidate()
            reference = weakref.ref(abandoned)
            del abandoned
            gc.collect()
            self.assertIsNone(reference())
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_prepare_requires_clean_expected_head_validator_blob_state(self) -> None:
        for state in (
            {"repository_head": "a" * 40, "validator_blob_id": "b" * 40,
             "is_clean": False},
            {"repository_head": "a" * 40, "validator_blob_id": None,
             "is_clean": True},
            {"repository_head": "c" * 40, "validator_blob_id": "b" * 40,
             "is_clean": True},
        ):
            with self.subTest(state=state):
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    try:
                        with mock.patch.object(
                            runner, "_resolve_phase_c1_validator_state",
                            return_value=state,
                        ) as resolver:
                            with self.assertRaises(runner.RunnerError):
                                self.prepared_candidate()
                            resolver.assert_called_once_with("a" * 40)
                    finally:
                        self.stop_runner_context(paths_patch, head_patch)

    def test_capability_binding_weak_state_and_real_os_contender_reject(self) -> None:
        paths, paths_patch, head_patch = self.runner_context()
        try:
            first = self.prepared_candidate()
            second = self.prepared_candidate()
            with self.lock(first) as first_capability:
                with self.assertRaises(runner.RunnerError):
                    runner.finalize_phase_c1_publication(
                        second, capability=first_capability,
                    )
                with self.assertRaises(runner.RunnerError):
                    runner.finalize_phase_c1_publication(
                        first, capability=object(),
                    )
                context = multiprocessing.get_context("spawn")
                result_queue = context.Queue()
                contender = context.Process(
                    target=_phase_c1_publication_lock_contender,
                    args=(str(getattr(paths, "publication_lock_path")), result_queue),
                )
                contender.start()
                contender.join(timeout=10)
                self.assertFalse(contender.is_alive())
                self.assertEqual(contender.exitcode, 0)
                self.assertFalse(result_queue.get(timeout=2))
                result_queue.close()
                result_queue.join_thread()
            abandoned = second
            abandoned_reference = weakref.ref(abandoned)
            del abandoned
            del second
            gc.collect()
            self.assertIsNone(abandoned_reference())
            replacement = self.prepared_candidate()
            with self.lock(replacement) as replacement_capability:
                receipt = runner.finalize_phase_c1_publication(
                    replacement, capability=replacement_capability,
                )
            self.assertEqual(receipt.status, "candidate_ready")
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_finalize_rejects_input_head_root_policy_and_capability_races(self) -> None:
        mutations = (
            "head", "protocol", "search", "source_ledger", "source_review",
            "root_identity", "fake_capability", "candidate_exists",
            "canonical_exists", "candidate_stage_exists", "canonical_stage_exists",
            "receipt_stage_exists",
        )
        for name in mutations:
            with self.subTest(mutation=name):
                self.assert_finalize_rejects_after(name)

    def test_finalize_rejects_parent_identity_link_and_unexpected_child_races(self) -> None:
        for mutation in ("parent_identity", "input_link", "unexpected_child"):
            with self.subTest(mutation=mutation):
                self.assert_finalize_rejects_after(mutation)

    def test_canonical_accepts_only_reviewed_candidate_bytes(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            prepared = runner._prepare_phase_c1_acceptance(
                expected_head="a" * 40,
                candidate_receipt_name="candidate-receipt.json",
                candidate_validation_name="candidate-validation.json",
                candidate_review_name="candidate-review.json",
            )
            with self.lock(prepared) as capability:
                receipt = runner.finalize_phase_c1_publication(
                    prepared, capability=capability,
                )
        finally:
            self.stop_runner_context(paths_patch, head_patch)
        self.assertEqual(receipt.status, "accepted")
        self.assertEqual(
            (self.canonical_root / "result.json").read_bytes(),
            self.expected_candidate_result_bytes,
        )
        self.assertFalse(self.candidate_root.exists())

    def test_cli_accepts_only_the_two_exact_command_shapes(self) -> None:
        accepted = (
            ("prepare", "--mode", "candidate", "--expected-head", "a" * 40,
             "--receipt", "candidate-receipt.json"),
            ("accept", "--expected-head", "a" * 40,
             "--receipt", "candidate-receipt.json",
             "--validation", "candidate-validation.json",
             "--review", "candidate-review.json"),
        )
        for argv in accepted:
            with self.subTest(argv=argv):
                self.assertIsNotNone(runner.parse_cli_args(argv))
        rejected = (
            (), ("prepare",), ("accept",),
            ("prepare", "--mode", "canonical"),
            ("prepare", "--mode", "candidate", "--output", "elsewhere"),
            ("prepare", "--mode", "candidate", "--root", "elsewhere"),
            ("prepare", "--mode", "candidate", "--expected-head", "A" * 40,
             "--receipt", "candidate-receipt.json"),
            ("prepare", "--mode", "candidate", "--expected-head", "a" * 39,
             "--receipt", "candidate-receipt.json"),
            ("prepare", "--mode", "candidate", "--expected-head", "a" * 40,
             "--receipt", "nested/candidate-receipt.json"),
            ("accept", "--receipt", "../candidate-receipt.json"),
            ("accept", "--expected-head", "a" * 40,
             "--receipt", "candidate-receipt.json",
             "--validation", "candidate-validation.json"),
            ("accept", "--expected-head", "A" * 40,
             "--receipt", "candidate-receipt.json",
             "--validation", "candidate-validation.json",
             "--review", "candidate-review.json"),
            ("accept", "--expected-head", "a" * 40,
             "--receipt", "candidate-receipt.json",
             "--validation", "candidate-validation.json",
             "--review", "alternate-review.json"),
            ("accept", "--expected-head", "a" * 40,
             "--receipt", "candidate-receipt.json",
             "--validation", "nested/candidate-validation.json",
             "--review", "candidate-review.json"),
            ("accept", "--expected-head", "a" * 40,
             "--receipt", "candidate-receipt.json",
             "--validation", "candidate-validation.json",
             "--review", "candidate-review.json", "--unknown"),
            ("fetch",),
        )
        for argv in rejected:
            with self.subTest(argv=argv):
                with self.assertRaises(runner.RunnerError):
                    runner.parse_cli_args(argv)

    def test_real_runner_entrypoint_invalid_shape_exits_two_before_publication(
        self,
    ) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                os.fspath(ROOT / "scripts" / "run_emotion_state_004_phase_c1.py"),
                "prepare",
                "--mode",
                "canonical",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONDONTWRITEBYTECODE": "1",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_OPTIONAL_LOCKS": "0",
            },
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=30,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(
            completed.stderr,
            "EMOTION-STATE-004 Phase C1 publication failed: cli_arguments\n",
        )

    def test_invalid_cli_rejects_before_tracked_read_git_or_lock(self) -> None:
        invalid = (
            (), ("prepare", "--mode", "canonical"),
            ("prepare", "--mode", "candidate", "--expected-head", "A" * 40,
             "--receipt", "candidate-receipt.json"),
            ("accept", "--expected-head", "a" * 40, "--receipt", "../candidate-receipt.json",
             "--validation", "candidate-validation.json", "--review", "candidate-review.json"),
            ("accept", "--expected-head", "a" * 40, "--receipt", "candidate-receipt.json",
             "--validation", "candidate-validation.json", "--review", "candidate-review.json",
             "--root", "elsewhere"),
        )
        for argv in invalid:
            with self.subTest(argv=argv):
                read_spy = mock.Mock(side_effect=AssertionError("tracked read"))
                git_spy = mock.Mock(side_effect=AssertionError("git resolver"))
                lock_spy = mock.Mock(side_effect=AssertionError("lock"))
                with mock.patch.object(
                    runner, "_read_phase_c1_tracked_input_bytes", read_spy,
                ), mock.patch.object(
                    runner, "_resolve_phase_c1_validator_state", git_spy,
                ), mock.patch.object(
                    runner, "persistent_phase_c1_publication_lock", lock_spy,
                ):
                    with self.assertRaises(runner.RunnerError):
                        runner._run_phase_c1_publication_cli(argv)
                read_spy.assert_not_called()
                git_spy.assert_not_called()
                lock_spy.assert_not_called()

    def test_prepare_rejects_invalid_or_nonlive_expected_heads_before_reading(self) -> None:
        invalid_heads = ("A" * 40, "a" * 39, "g" * 40, "a" * 40)
        for expected_head in invalid_heads:
            with self.subTest(expected_head=expected_head), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                try:
                    live_head = "c" * 40 if expected_head == "a" * 40 else "a" * 40
                    with mock.patch.object(
                        runner, "_current_repository_head", return_value=live_head,
                    ), mock.patch.object(
                        runner, "_read_phase_c1_tracked_input_bytes",
                        side_effect=AssertionError("tracked read"),
                    ):
                        with self.assertRaises(runner.RunnerError):
                            runner.prepare_phase_c1_candidate(expected_head=expected_head)
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def create_candidate(self) -> object:
        prepared = self.prepared_candidate()
        with self.lock(prepared) as capability:
            return runner.finalize_phase_c1_publication(
                prepared, capability=capability,
            )

    def prepare_acceptance(self) -> "runner.PreparedPhaseC1Publication":
        return runner._prepare_phase_c1_acceptance(
            expected_head="a" * 40,
            candidate_receipt_name="candidate-receipt.json",
            candidate_validation_name="candidate-validation.json",
            candidate_review_name="candidate-review.json",
        )

    def seed_protected_source_research_children(
        self,
    ) -> dict[Path, tuple[bytes, tuple[int, int]]]:
        protected = {
            self.ignored_root / "source-cache" / "source.json": b"source-cache\n",
            self.ignored_root / "research" / "review.json": b"research\n",
        }
        snapshot: dict[Path, tuple[bytes, tuple[int, int]]] = {}
        for path, payload in protected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            metadata = path.stat()
            snapshot[path] = (payload, (metadata.st_dev, metadata.st_ino))
        return snapshot

    def assert_protected_children_unchanged(
        self, snapshot: dict[Path, tuple[bytes, tuple[int, int]]],
    ) -> None:
        for path, (payload, identity) in snapshot.items():
            self.assertEqual(path.read_bytes(), payload)
            metadata = path.stat()
            self.assertEqual((metadata.st_dev, metadata.st_ino), identity)

    def assert_valid_acceptance_control(self) -> None:
        with self.isolated_mutation_root():
            _paths, paths_patch, head_patch = self.runner_context()
            try:
                self.create_candidate()
                self.seed_valid_candidate_validation_and_review_receipts()
                prepared = self.prepare_acceptance()
                with self.lock(prepared) as capability:
                    receipt = runner.finalize_phase_c1_publication(
                        prepared, capability=capability,
                    )
                self.assertEqual(receipt.status, "accepted")
                self.assertEqual(
                    (self.canonical_root / "result.json").read_bytes(),
                    self.expected_candidate_result_bytes,
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    @staticmethod
    def _sha256(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def seed_valid_candidate_validation_and_review_receipts(self) -> None:
        """Write independently derived, canonical validation/review receipts."""
        candidate_receipt = phase_c1.load_json_strict(
            (self.ignored_root / "candidate-receipt.json").read_bytes(),
            source="candidate_receipt",
        )
        self.assertIsInstance(candidate_receipt, dict)
        result_bytes = (self.candidate_root / "result.json").read_bytes()
        report_bytes = (self.candidate_root / "report.md").read_bytes()
        validation = {
            "schema_version": "EmotionStatePhaseC1CandidateValidationV1",
            "checkpoint_id": runner.CHECKPOINT_ID,
            "implementation_head": candidate_receipt["implementation_head"],
            "candidate_transaction_id": candidate_receipt["transaction_id"],
            "candidate_result_sha256": self._sha256(result_bytes),
            "candidate_report_sha256": self._sha256(report_bytes),
            "protocol_sha256": candidate_receipt["protocol_sha256"],
            "search_ledger_sha256": candidate_receipt["search_ledger_sha256"],
            "source_evidence_ledger_sha256": candidate_receipt[
                "source_evidence_ledger_sha256"
            ],
            "source_review_receipt_sha256": candidate_receipt[
                "source_review_receipt_sha256"
            ],
            "validator_blob_id": candidate_receipt["validator_blob_id"],
            "verdict": "pass",
            "runtime_approved": False,
        }
        validation_bytes = phase_c1.canonical_json_bytes(validation)
        review = {
            "schema_version": "EmotionStatePhaseC1CandidateReviewV1",
            "checkpoint_id": runner.CHECKPOINT_ID,
            "candidate_transaction_id": candidate_receipt["transaction_id"],
            "implementation_head": candidate_receipt["implementation_head"],
            "candidate_result_sha256": self._sha256(result_bytes),
            "candidate_report_sha256": self._sha256(report_bytes),
            "candidate_validation_sha256": self._sha256(validation_bytes),
            "review_scope": (
                "all_candidate_inputs_decisions_pair_report_and_boundaries"
            ),
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
        self.validation_bytes = validation_bytes
        self.review_bytes = phase_c1.canonical_json_bytes(review)
        for path, payload in (
            (self.ignored_root / "candidate-validation.json", validation_bytes),
            (self.ignored_root / "candidate-review.json", self.review_bytes),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    def write_exact_journal(
        self,
        *,
        status: str,
        sequence: int = 0,
        previous: bytes | None = None,
        include_acceptance_hashes: bool = False,
    ) -> bytes:
        receipt_bytes = (self.ignored_root / "candidate-receipt.json").read_bytes()
        receipt = phase_c1.load_json_strict(receipt_bytes, source="candidate_receipt")
        self.assertIsInstance(receipt, dict)
        payload: dict[str, object] = {
            "schema_version": "EmotionStatePhaseC1PublicationJournalV1",
            "checkpoint_id": runner.CHECKPOINT_ID,
            "transaction_id": receipt["transaction_id"],
            "sequence": sequence,
            "previous_journal_sha256": (
                "0" * 64 if previous is None else self._sha256(previous)
            ),
            "status": status,
            "expected_head": "a" * 40,
            "implementation_head": receipt["implementation_head"],
            "validator_blob_id": receipt["validator_blob_id"],
            "protocol_sha256": receipt["protocol_sha256"],
            "search_ledger_sha256": receipt["search_ledger_sha256"],
            "source_evidence_ledger_sha256": receipt[
                "source_evidence_ledger_sha256"
            ],
            "source_review_receipt_sha256": receipt[
                "source_review_receipt_sha256"
            ],
            "result_sha256": receipt["result_sha256"],
            "report_sha256": receipt["report_sha256"],
            "candidate_receipt_sha256": self._sha256(receipt_bytes),
            "candidate_validation_sha256": (
                self._sha256(self.validation_bytes)
                if include_acceptance_hashes else None
            ),
            "candidate_review_sha256": (
                self._sha256(self.review_bytes)
                if include_acceptance_hashes else None
            ),
            "journal_content_sha256": "",
        }
        payload["journal_content_sha256"] = self._sha256(
            phase_c1.canonical_json_bytes(payload)
        )
        journal_bytes = phase_c1.canonical_json_bytes(payload)
        journal_path = self.ignored_root / "publication-journal.json"
        journal_path.write_bytes(journal_bytes)
        return journal_bytes

    def write_valid_journal_chain(self, *, final_status: str) -> tuple[bytes, bytes]:
        predecessor = self.write_exact_journal(status="staging_candidate")
        return predecessor, self.write_exact_journal(
            status=final_status,
            sequence=1,
            previous=predecessor,
            include_acceptance_hashes=final_status in {"staging_canonical", "accepted"},
        )

    def write_pair_directory(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / "result.json").write_bytes(self.expected_candidate_result_bytes)
        (path / "report.md").write_bytes(self.expected_candidate_report_bytes)

    def assert_pair_directory(self, path: Path) -> None:
        self.assertEqual((path / "result.json").read_bytes(), self.expected_candidate_result_bytes)
        self.assertEqual((path / "report.md").read_bytes(), self.expected_candidate_report_bytes)

    def test_candidate_validator_projects_and_rechecks_validation_receipt(self) -> None:
        git = PhaseC1IndependentValidatorTests.git
        git(self.temp_root, "init", "--quiet")
        git(self.temp_root, "config", "user.name", "Phase C1 Test")
        git(
            self.temp_root,
            "config",
            "user.email",
            "phase-c1-test@example.invalid",
        )
        validator_path = (
            self.temp_root
            / "scripts"
            / "validate_emotion_state_004_phase_c1.py"
        )
        validator_path.parent.mkdir(parents=True)
        validator_path.write_bytes(
            PhaseC1IndependentValidatorTests.closed_validator_import_source()
        )
        contracts_path = (
            self.temp_root
            / "scripts"
            / "emotion_state_phase_c1_contracts.py"
        )
        contracts_path.write_bytes(b"# synthetic contracts\n")
        git(self.temp_root, "add", ".")
        git(self.temp_root, "commit", "--quiet", "-m", "implementation")
        implementation_head = git(
            self.temp_root,
            "rev-parse",
            "HEAD",
        )
        validator_blob_id = git(
            self.temp_root,
            "rev-parse",
            (
                f"{implementation_head}:"
                "scripts/validate_emotion_state_004_phase_c1.py"
            ),
        )
        result = runner.build_phase_c1_result(
            head_commit=implementation_head,
            validator_blob_id=validator_blob_id,
            **self.authority,
        )
        self.expected_candidate_result_bytes = (
            phase_c1.canonical_json_bytes(result)
        )
        self.expected_candidate_report_bytes = (
            runner.render_phase_c1_report(
                result,
                **self.authority,
            )
        )
        paths = self.build_explicit_temp_runner_paths(self.temp_root)
        validator_state = {
            "repository_head": implementation_head,
            "validator_blob_id": validator_blob_id,
            "is_clean": True,
        }

        with mock.patch.object(
            runner,
            "PRODUCTION_PATHS",
            paths,
        ), mock.patch.object(
            runner,
            "_current_repository_head",
            return_value=implementation_head,
        ), mock.patch.object(
            runner,
            "_resolve_phase_c1_validator_state",
            return_value=validator_state,
        ), mock.patch.multiple(
            validator,
            ROOT=self.temp_root,
            PROTOCOL_PATH=self.input_paths["protocol_path"],
            SEARCH_LEDGER_PATH=self.input_paths["search_ledger_path"],
            SOURCE_LEDGER_PATH=self.input_paths["source_ledger_path"],
            SOURCE_REVIEW_PATH=self.input_paths["source_review_path"],
            VALIDATOR_PATH=validator_path,
            CONTRACTS_PATH=contracts_path,
            CANDIDATE_ROOT=self.candidate_root,
            CANONICAL_ROOT=self.canonical_root,
        ):
            prepared = runner.prepare_phase_c1_candidate(
                expected_head=implementation_head,
            )
            with runner.persistent_phase_c1_publication_lock(
                prepared,
            ) as capability:
                runner.finalize_phase_c1_publication(
                    prepared,
                    capability=capability,
                )
            self.seed_valid_candidate_validation_and_review_receipts()
            expected_validation_bytes = self.validation_bytes
            (self.ignored_root / "candidate-validation.json").unlink()
            (self.ignored_root / "candidate-review.json").unlink()

            class BinaryOnlyStdout:
                def __init__(self) -> None:
                    self.buffer = io.BytesIO()

                def write(self, value: object) -> int:
                    raise AssertionError("candidate --json must not use text stdout")

                def flush(self) -> None:
                    return None

            stdout = BinaryOnlyStdout()
            with mock.patch.object(sys, "stdout", stdout):
                self.assertEqual(validator.main(("candidate", "--json")), 0)
            self.assertEqual(stdout.buffer.getvalue(), expected_validation_bytes)
            self.assertFalse((self.ignored_root / "candidate-validation.json").exists())
            self.assertFalse((self.ignored_root / "candidate-review.json").exists())
            self.seed_valid_candidate_validation_and_review_receipts()
            self.assertEqual(validator.main(("candidate",)), 0)

    def test_candidate_validator_requires_exact_independent_review_binding(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        validator_patch = self.validator_context()
        validator_patch.start()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            receipt_path = self.ignored_root / "candidate-review.json"
            for mutation in (
                "missing", "reordered", "alternate_name", "wrong_hash",
                "critical", "important", "minor", "raw_rows", "private",
                "evaluation", "provider", "runtime", "noncanonical",
                "review_without_validation", "review_stage",
                "validation_missing", "validation_tamper", "validation_noncanonical",
            ):
                with self.subTest(mutation=mutation):
                    for extra_name in (
                        "alternate-review.json",
                        "candidate-review.stage",
                    ):
                        extra_path = self.ignored_root / extra_name
                        if extra_path.exists():
                            extra_path.unlink()
                    if not (self.ignored_root / "candidate-validation.json").exists():
                        (self.ignored_root / "candidate-validation.json").write_bytes(
                            self.validation_bytes
                        )
                    receipt_path.write_bytes(self.review_bytes)
                    if mutation == "missing":
                        receipt_path.unlink()
                    elif mutation == "alternate_name":
                        receipt_path.rename(
                            self.ignored_root / "alternate-review.json"
                        )
                    elif mutation == "review_without_validation":
                        (self.ignored_root / "candidate-validation.json").unlink()
                    elif mutation == "review_stage":
                        receipt_path.rename(
                            self.ignored_root / "candidate-review.stage"
                        )
                    elif mutation == "validation_missing":
                        (self.ignored_root / "candidate-validation.json").unlink()
                    elif mutation == "validation_tamper":
                        validation_path = self.ignored_root / "candidate-validation.json"
                        validation_path.write_bytes(validation_path.read_bytes() + b" ")
                    elif mutation == "validation_noncanonical":
                        validation_path = self.ignored_root / "candidate-validation.json"
                        validation_path.write_bytes(
                            validation_path.read_bytes().replace(b"\n", b"\r\n")
                        )
                    elif mutation == "noncanonical":
                        receipt_path.write_bytes(self.review_bytes.replace(b"\n", b"\r\n"))
                    elif mutation == "reordered":
                        payload = phase_c1.load_json_strict(
                            self.review_bytes, source="review",
                        )
                        self.assertIsInstance(payload, dict)
                        receipt_path.write_bytes(
                            json.dumps(payload, separators=(",", ":")).encode("utf-8")
                        )
                    else:
                        payload = phase_c1.load_json_strict(
                            self.review_bytes, source="review",
                        )
                        self.assertIsInstance(payload, dict)
                        if mutation == "wrong_hash":
                            payload["candidate_validation_sha256"] = "0" * 64
                        elif mutation in {"critical", "important", "minor"}:
                            payload[f"{mutation}_findings"] = 1
                        else:
                            boolean_field = {
                                "raw_rows": "raw_rows_read",
                                "private": "private_data_read",
                                "evaluation": "model_evaluation_run",
                                "provider": "provider_accessed",
                                "runtime": "runtime_modified",
                            }[mutation]
                            payload[boolean_field] = True
                        receipt_path.write_bytes(phase_c1.canonical_json_bytes(payload))
                    self.assertEqual(validator.main(("candidate",)), 1)
                    self.seed_valid_candidate_validation_and_review_receipts()
        finally:
            validator_patch.stop()
            self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_receipt_schema_and_status_mutations_reject(self) -> None:
        for mutation in (
            "schema_missing", "schema_replaced", "staging_candidate",
            "staging_canonical", "accepted", "unknown", "transaction",
            "head", "result_hash", "report_hash", "validator_blob",
        ):
            with self.subTest(mutation=mutation):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    validator_patch = self.validator_context()
                    validator_patch.start()
                    try:
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        receipt_path = self.ignored_root / "candidate-receipt.json"
                        payload = phase_c1.load_json_strict(
                            receipt_path.read_bytes(), source="candidate_receipt",
                        )
                        self.assertIsInstance(payload, dict)
                        if mutation == "schema_missing":
                            del payload["schema_version"]
                        elif mutation == "schema_replaced":
                            payload["schema_version"] = "OtherV1"
                        elif mutation in {
                            "staging_candidate", "staging_canonical", "accepted", "unknown",
                        }:
                            payload["status"] = mutation
                        else:
                            field = {
                                "transaction": "transaction_id",
                                "head": "implementation_head",
                                "result_hash": "result_sha256",
                                "report_hash": "report_sha256",
                                "validator_blob": "validator_blob_id",
                            }[mutation]
                            payload[field] = "0" * len(str(payload[field]))
                        receipt_path.write_bytes(phase_c1.canonical_json_bytes(payload))
                        self.assertEqual(validator.main(("candidate",)), 1)
                        with self.assertRaises(runner.RunnerError):
                            self.prepare_acceptance()
                    finally:
                        validator_patch.stop()
                        self.stop_runner_context(paths_patch, head_patch)

    def test_unresolved_candidate_receipt_and_validation_stages_reject_without_deletion(self) -> None:
        for name in (
            "candidate-receipt.json", "candidate-validation.json", "candidate-review.json",
        ):
            with self.subTest(name=name), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                validator_patch = self.validator_context()
                validator_patch.start()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    final_path = self.ignored_root / name
                    stage_path = final_path.with_suffix(".stage")
                    final_bytes = final_path.read_bytes()
                    stage_path.write_bytes(final_bytes)
                    staged = stage_path.read_bytes()
                    self.assertEqual(validator.main(("candidate",)), 1)
                    with self.assertRaises(runner.RunnerError):
                        self.prepare_acceptance()
                    self.assertEqual(stage_path.read_bytes(), staged)
                    self.assertEqual(final_path.read_bytes(), final_bytes)
                finally:
                    validator_patch.stop()
                    self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_receipt_has_exact_closed_shape_and_content_transaction_id(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            receipt_bytes = (self.ignored_root / "candidate-receipt.json").read_bytes()
            receipt = phase_c1.load_json_strict(receipt_bytes, source="candidate_receipt")
            self.assertIsInstance(receipt, dict)
            self.assertEqual(set(receipt), {
                "schema_version", "checkpoint_id", "transaction_id", "status",
                "implementation_head", "validator_blob_id", "protocol_sha256",
                "search_ledger_sha256", "source_evidence_ledger_sha256",
                "source_review_receipt_sha256", "result_sha256", "report_sha256",
            })
            self.assertEqual(receipt["schema_version"], "EmotionStatePhaseC1CandidateReceiptV1")
            self.assertEqual(receipt["status"], "candidate_ready")
            for value in receipt.values():
                self.assertIsInstance(value, str)
                self.assertTrue(value.isascii())
            content = copy.deepcopy(receipt)
            content["transaction_id"] = ""
            self.assertEqual(
                receipt["transaction_id"],
                self._sha256(phase_c1.canonical_json_bytes(content))[:32],
            )
            self.assertRegex(receipt["transaction_id"], r"^[0-9a-f]{32}$")
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_pair_tamper_after_validation_blocks_acceptance_without_rewrite(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            report_path = self.candidate_root / "report.md"
            report_path.write_bytes(report_path.read_bytes() + b"tampered\n")
            tampered = report_path.read_bytes()
            with self.assertRaises(runner.RunnerError):
                self.prepare_acceptance()
            self.assertEqual(report_path.read_bytes(), tampered)
            self.assertFalse(self.canonical_root.exists())
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_validation_and_review_schema_verdict_runtime_and_binding_mutations_reject(self) -> None:
        mutations = (
            ("validation", "schema_version", "OtherV1"),
            ("validation", "verdict", "fail"),
            ("validation", "runtime_approved", True),
            ("validation", "candidate_transaction_id", "0" * 32),
            ("validation", "implementation_head", "0" * 40),
            ("validation", "candidate_result_sha256", "0" * 64),
            ("validation", "candidate_report_sha256", "0" * 64),
            ("validation", "protocol_sha256", "0" * 64),
            ("validation", "search_ledger_sha256", "0" * 64),
            ("validation", "source_evidence_ledger_sha256", "0" * 64),
            ("validation", "source_review_receipt_sha256", "0" * 64),
            ("validation", "validator_blob_id", "0" * 40),
            ("review", "schema_version", "OtherV1"),
            ("review", "candidate_transaction_id", "0" * 32),
            ("review", "implementation_head", "0" * 40),
            ("review", "candidate_result_sha256", "0" * 64),
            ("review", "candidate_report_sha256", "0" * 64),
            ("review", "candidate_validation_sha256", "0" * 64),
            ("review", "review_scope", "other_scope"),
            ("review", "verdict", "rejected"),
        )
        for receipt_kind, field, value in mutations:
            with self.subTest(receipt=receipt_kind, field=field):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    validator_patch = self.validator_context()
                    validator_patch.start()
                    try:
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        path = self.ignored_root / f"candidate-{receipt_kind}.json"
                        payload = phase_c1.load_json_strict(path.read_bytes(), source=receipt_kind)
                        self.assertIsInstance(payload, dict)
                        payload[field] = value
                        path.write_bytes(phase_c1.canonical_json_bytes(payload))
                        if receipt_kind == "validation":
                            review_path = self.ignored_root / "candidate-review.json"
                            review = phase_c1.load_json_strict(
                                review_path.read_bytes(), source="review",
                            )
                            self.assertIsInstance(review, dict)
                            review["candidate_validation_sha256"] = self._sha256(
                                path.read_bytes(),
                            )
                            review_path.write_bytes(phase_c1.canonical_json_bytes(review))
                        self.assertEqual(validator.main(("candidate",)), 1)
                        with self.assertRaises(runner.RunnerError):
                            self.prepare_acceptance()
                    finally:
                        validator_patch.stop()
                        self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_lane_recovers_after_candidate_and_receipt_rename_crashes(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            receipt_path = self.ignored_root / "candidate-receipt.json"
            original = receipt_path.read_bytes()
            for crash in ("candidate_rename", "receipt_rename"):
                with self.subTest(crash=crash):
                    self.write_exact_journal(status="staging_candidate")
                    if crash == "candidate_rename":
                        receipt_path.unlink()
                    prepared = self.prepared_candidate()
                    with self.lock(prepared) as capability:
                        recovered = runner.finalize_phase_c1_publication(
                            prepared, capability=capability,
                        )
                    self.assertEqual(recovered.status, "candidate_ready")
                    self.assertEqual(receipt_path.read_bytes(), original)
                    self.assertEqual(
                        phase_c1.load_json_strict(
                            (self.ignored_root / "publication-journal.json").read_bytes(),
                            source="journal",
                        )["status"],
                        "candidate_ready",
                    )
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_acceptance_lane_recovery_requires_validation_and_review(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            self.write_valid_journal_chain(final_status="staging_canonical")
            for missing in ("candidate-validation.json", "candidate-review.json"):
                with self.subTest(missing=missing):
                    path = self.ignored_root / missing
                    saved = path.read_bytes()
                    path.unlink()
                    with self.assertRaises(runner.RunnerError):
                        runner._prepare_phase_c1_acceptance(
                            expected_head="a" * 40,
                            candidate_receipt_name="candidate-receipt.json",
                            candidate_validation_name="candidate-validation.json",
                            candidate_review_name="candidate-review.json",
                        )
                    path.write_bytes(saved)
            prepared = runner._prepare_phase_c1_acceptance(
                expected_head="a" * 40,
                candidate_receipt_name="candidate-receipt.json",
                candidate_validation_name="candidate-validation.json",
                candidate_review_name="candidate-review.json",
            )
            with self.lock(prepared) as capability:
                receipt = runner.finalize_phase_c1_publication(
                    prepared, capability=capability,
                )
            self.assertEqual(receipt.status, "accepted")
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_journal_fields_self_hash_status_and_predecessor_fail_closed(self) -> None:
        required = {
            "schema_version", "checkpoint_id", "transaction_id", "sequence",
            "previous_journal_sha256", "status", "expected_head",
            "implementation_head", "validator_blob_id", "protocol_sha256",
            "search_ledger_sha256", "source_evidence_ledger_sha256",
            "source_review_receipt_sha256", "result_sha256", "report_sha256",
            "candidate_receipt_sha256", "candidate_validation_sha256",
            "candidate_review_sha256", "journal_content_sha256",
        }
        for mutation in ("field", "self_hash", "status", "predecessor", "stage"):
            with self.subTest(mutation=mutation):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    try:
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        prepared = self.prepare_acceptance()
                        with self.lock(prepared) as capability:
                            runner.finalize_phase_c1_publication(prepared, capability=capability)
                        journal_path = self.ignored_root / "publication-journal.json"
                        valid = journal_path.read_bytes()
                        self.assertEqual(
                            set(phase_c1.load_json_strict(valid, source="journal")), required,
                        )
                        if mutation == "stage":
                            (self.ignored_root / "publication-journal.stage").write_bytes(
                                b"invalid\n"
                            )
                        else:
                            payload = phase_c1.load_json_strict(valid, source="journal")
                            self.assertIsInstance(payload, dict)
                            if mutation == "field":
                                del payload["result_sha256"]
                            elif mutation == "self_hash":
                                payload["journal_content_sha256"] = "0" * 64
                            elif mutation == "status":
                                payload["status"] = "unknown"
                            else:
                                payload["previous_journal_sha256"] = "F" * 64
                            journal_path.write_bytes(phase_c1.canonical_json_bytes(payload))
                        with self.assertRaisesRegex(runner.RunnerError, "journal"):
                            self.prepare_acceptance()
                        self.assertEqual(
                            (self.canonical_root / "result.json").read_bytes(),
                            self.expected_candidate_result_bytes,
                        )
                    finally:
                        self.stop_runner_context(paths_patch, head_patch)

    def test_each_accepted_journal_invariant_rejects_from_a_fresh_valid_canonical_baseline(self) -> None:
        mutations = (
            "negative_sequence", "nonmonotonic", "null_candidate_receipt",
            "null_validation", "null_review", "wrong_predecessor", "wrong_status",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    try:
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        prepared = self.prepare_acceptance()
                        with self.lock(prepared) as capability:
                            runner.finalize_phase_c1_publication(prepared, capability=capability)
                        journal_path = self.ignored_root / "publication-journal.json"
                        accepted = journal_path.read_bytes()
                        control = self.prepare_acceptance()
                        with self.lock(control) as capability:
                            control_receipt = runner.finalize_phase_c1_publication(
                                control, capability=capability,
                            )
                        self.assertEqual(control_receipt.status, "accepted")
                        self.assertEqual(journal_path.read_bytes(), accepted)
                        payload = phase_c1.load_json_strict(accepted, source="accepted")
                        self.assertIsInstance(payload, dict)
                        if mutation == "negative_sequence":
                            payload["sequence"] = -1
                        elif mutation == "nonmonotonic":
                            payload["sequence"] = 0
                        elif mutation == "null_candidate_receipt":
                            payload["candidate_receipt_sha256"] = None
                        elif mutation == "null_validation":
                            payload["candidate_validation_sha256"] = None
                        elif mutation == "null_review":
                            payload["candidate_review_sha256"] = None
                        elif mutation == "wrong_predecessor":
                            payload["previous_journal_sha256"] = "0" * 64
                        else:
                            payload["status"] = "candidate_ready"
                        payload["journal_content_sha256"] = ""
                        payload["journal_content_sha256"] = self._sha256(
                            phase_c1.canonical_json_bytes(payload),
                        )
                        journal_path.write_bytes(phase_c1.canonical_json_bytes(payload))
                        with self.assertRaises(runner.RunnerError):
                            self.prepare_acceptance()
                        self.assert_pair_directory(self.canonical_root)
                    finally:
                        self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_cleanup_recovery_survives_each_allowlisted_deletion(self) -> None:
        cleanup_targets = (
            "candidate", "candidate-receipt.json", "candidate-validation.json",
            "candidate-review.json",
        )
        self.assert_valid_acceptance_control()
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            candidate_snapshot = {
                "result.json": (self.candidate_root / "result.json").read_bytes(),
                "report.md": (self.candidate_root / "report.md").read_bytes(),
            }
            receipt_snapshot = {
                "candidate-receipt.json": (
                    self.ignored_root / "candidate-receipt.json"
                ).read_bytes(),
                "candidate-validation.json": self.validation_bytes,
                "candidate-review.json": self.review_bytes,
            }
            prepared = runner._prepare_phase_c1_acceptance(
                expected_head="a" * 40,
                candidate_receipt_name="candidate-receipt.json",
                candidate_validation_name="candidate-validation.json",
                candidate_review_name="candidate-review.json",
            )
            with self.lock(prepared) as capability:
                runner.finalize_phase_c1_publication(prepared, capability=capability)
            journal_path = self.ignored_root / "publication-journal.json"
            journal_bytes = journal_path.read_bytes()
            canonical_bytes = (self.canonical_root / "result.json").read_bytes()
            for retained in range(1 << len(cleanup_targets)):
                with self.subTest(retained=retained):
                    if self.candidate_root.exists():
                        for child in self.candidate_root.iterdir():
                            child.unlink()
                        self.candidate_root.rmdir()
                    self.candidate_root.mkdir(parents=True)
                    for name, payload in candidate_snapshot.items():
                        (self.candidate_root / name).write_bytes(payload)
                    for name, payload in receipt_snapshot.items():
                        (self.ignored_root / name).write_bytes(payload)
                    for index, target in enumerate(cleanup_targets):
                        if not retained & (1 << index):
                            path = (
                                self.candidate_root
                                if target == "candidate"
                                else self.ignored_root / target
                            )
                            if path.is_dir():
                                for child in path.iterdir():
                                    child.unlink()
                                path.rmdir()
                            else:
                                path.unlink()
                    recovery = runner._prepare_phase_c1_acceptance(
                        expected_head="a" * 40,
                        candidate_receipt_name="candidate-receipt.json",
                        candidate_validation_name="candidate-validation.json",
                        candidate_review_name="candidate-review.json",
                    )
                    with self.lock(recovery) as capability:
                        runner.finalize_phase_c1_publication(
                            recovery, capability=capability,
                        )
                    self.assertEqual(journal_path.read_bytes(), journal_bytes)
                    self.assertEqual(
                        (self.canonical_root / "result.json").read_bytes(),
                        canonical_bytes,
                    )
                    self.assertFalse(self.candidate_root.exists())
                    for target in cleanup_targets[1:]:
                        self.assertFalse((self.ignored_root / target).exists())
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_recovery_rows_remove_only_verified_stages_and_preserve_candidate_ready(self) -> None:
        rows = ("candidate_stage", "canonical_stage", "journal_stage", "candidate_ready")
        for row in rows:
            with self.subTest(row=row):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    try:
                        protected = self.seed_protected_source_research_children()
                        if row == "candidate_stage":
                            self.write_pair_directory(self.ignored_root / "candidate.stage")
                            prepared = self.prepared_candidate()
                            with self.lock(prepared) as capability:
                                receipt = runner.finalize_phase_c1_publication(
                                    prepared, capability=capability,
                                )
                            self.assertEqual(receipt.status, "candidate_ready")
                            self.assertFalse((self.ignored_root / "candidate.stage").exists())
                            self.assert_pair_directory(self.candidate_root)
                            self.assert_protected_children_unchanged(protected)
                            continue
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        if row == "canonical_stage":
                            self.write_pair_directory(self.ignored_root / "canonical.stage")
                            self.write_valid_journal_chain(final_status="staging_canonical")
                        elif row == "journal_stage":
                            predecessor = self.write_exact_journal(status="candidate_ready")
                            transition = self.write_exact_journal(
                                status="staging_canonical", sequence=1,
                                previous=predecessor, include_acceptance_hashes=True,
                            )
                            (self.ignored_root / "publication-journal.json").write_bytes(predecessor)
                            (self.ignored_root / "publication-journal.stage").write_bytes(transition)
                        else:
                            self.write_exact_journal(status="candidate_ready")
                            candidate_before = {
                                name: (self.candidate_root / name).read_bytes()
                                for name in ("result.json", "report.md")
                            }
                        prepared = self.prepare_acceptance()
                        if row == "candidate_ready":
                            self.assertEqual(
                                (self.candidate_root / "result.json").read_bytes(),
                                candidate_before["result.json"],
                            )
                            self.assertEqual(
                                (self.candidate_root / "report.md").read_bytes(),
                                candidate_before["report.md"],
                            )
                        with self.lock(prepared) as capability:
                            receipt = runner.finalize_phase_c1_publication(
                                prepared, capability=capability,
                            )
                        self.assertEqual(receipt.status, "accepted")
                        self.assertFalse((self.ignored_root / "canonical.stage").exists())
                        self.assertFalse((self.ignored_root / "publication-journal.stage").exists())
                        self.assert_pair_directory(self.canonical_root)
                        self.assert_protected_children_unchanged(protected)
                    finally:
                        self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_recovery_handles_each_optional_receipt_absence_with_durable_hashes(self) -> None:
        receipt_names = (
            "candidate-receipt.json", "candidate-validation.json", "candidate-review.json",
        )
        for retained_mask in range(1 << len(receipt_names)):
            with self.subTest(retained_mask=retained_mask):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    try:
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        snapshot = {
                            name: (self.ignored_root / name).read_bytes()
                            for name in receipt_names
                        }
                        prepared = self.prepare_acceptance()
                        with self.lock(prepared) as capability:
                            runner.finalize_phase_c1_publication(prepared, capability=capability)
                        journal_path = self.ignored_root / "publication-journal.json"
                        journal_before = journal_path.read_bytes()
                        journal = phase_c1.load_json_strict(journal_before, source="accepted")
                        self.assertIsInstance(journal, dict)
                        for field in (
                            "candidate_receipt_sha256", "candidate_validation_sha256",
                            "candidate_review_sha256",
                        ):
                            self.assertRegex(str(journal[field]), r"^[0-9a-f]{64}$")
                        for index, name in enumerate(receipt_names):
                            path = self.ignored_root / name
                            if retained_mask & (1 << index):
                                path.write_bytes(snapshot[name])
                            else:
                                self.assertFalse(path.exists())
                        recovery = self.prepare_acceptance()
                        with self.lock(recovery) as capability:
                            receipt = runner.finalize_phase_c1_publication(
                                recovery, capability=capability,
                            )
                        self.assertEqual(receipt.status, "accepted")
                        self.assertEqual(journal_path.read_bytes(), journal_before)
                        for name in receipt_names:
                            self.assertFalse((self.ignored_root / name).exists())
                    finally:
                        self.stop_runner_context(paths_patch, head_patch)

    def test_journal_stage_pairings_block_except_verified_staging_canonical_recovery(self) -> None:
        rows = ("mismatched_stage", "changed_predecessor", "staging_canonical_without_root")
        for row in rows:
            with self.subTest(row=row):
                self.assert_valid_acceptance_control()
                with self.isolated_mutation_root():
                    _paths, paths_patch, head_patch = self.runner_context()
                    try:
                        protected = self.seed_protected_source_research_children()
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        predecessor = self.write_exact_journal(status="candidate_ready")
                        if row == "staging_canonical_without_root":
                            self.write_exact_journal(
                                status="staging_canonical", sequence=1,
                                previous=predecessor, include_acceptance_hashes=True,
                            )
                            prepared = self.prepare_acceptance()
                            with self.lock(prepared) as capability:
                                receipt = runner.finalize_phase_c1_publication(
                                    prepared, capability=capability,
                                )
                            self.assertEqual(receipt.status, "accepted")
                            self.assert_pair_directory(self.canonical_root)
                            self.assert_protected_children_unchanged(protected)
                            continue
                        if row == "changed_predecessor":
                            alternate_predecessor = self.write_exact_journal(
                                status="candidate_ready",
                            )
                            alternate_payload = phase_c1.load_json_strict(
                                alternate_predecessor, source="alternate_predecessor",
                            )
                            self.assertIsInstance(alternate_payload, dict)
                            alternate_payload["expected_head"] = "c" * 40
                            alternate_payload["journal_content_sha256"] = ""
                            alternate_payload["journal_content_sha256"] = self._sha256(
                                phase_c1.canonical_json_bytes(alternate_payload),
                            )
                            alternate_predecessor = phase_c1.canonical_json_bytes(
                                alternate_payload,
                            )
                            staged_transition = self.write_exact_journal(
                                status="staging_canonical", sequence=1,
                                previous=alternate_predecessor,
                                include_acceptance_hashes=True,
                            )
                            (self.ignored_root / "publication-journal.json").write_bytes(predecessor)
                            (self.ignored_root / "publication-journal.stage").write_bytes(
                                staged_transition,
                            )
                            before = (predecessor, staged_transition)
                        else:
                            (self.ignored_root / "publication-journal.stage").write_bytes(b"invalid\n")
                            before = (
                                (self.ignored_root / "publication-journal.json").read_bytes(),
                                b"invalid\n",
                            )
                        with self.assertRaises(runner.RunnerError):
                            self.prepare_acceptance()
                        self.assertEqual(
                            (self.ignored_root / "publication-journal.json").read_bytes(), before[0],
                        )
                        self.assertEqual(
                            (self.ignored_root / "publication-journal.stage").read_bytes(), before[1],
                        )
                        self.assert_protected_children_unchanged(protected)
                    finally:
                        self.stop_runner_context(paths_patch, head_patch)

    def test_transaction_preserves_allowed_source_research_children(self) -> None:
        protected = {
            self.ignored_root / "source-cache" / "source.json": b"source-cache\n",
            self.ignored_root / "research" / "review.json": b"research\n",
        }
        identities: dict[Path, tuple[int, int]] = {}
        for path, payload in protected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            metadata = path.stat()
            identities[path] = (metadata.st_dev, metadata.st_ino)
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            prepared = runner._prepare_phase_c1_acceptance(
                expected_head="a" * 40,
                candidate_receipt_name="candidate-receipt.json",
                candidate_validation_name="candidate-validation.json",
                candidate_review_name="candidate-review.json",
            )
            with self.lock(prepared) as capability:
                runner.finalize_phase_c1_publication(
                    prepared, capability=capability,
                )
            recovery = runner._prepare_phase_c1_acceptance(
                expected_head="a" * 40,
                candidate_receipt_name="candidate-receipt.json",
                candidate_validation_name="candidate-validation.json",
                candidate_review_name="candidate-review.json",
            )
            with self.lock(recovery) as capability:
                runner.finalize_phase_c1_publication(
                    recovery, capability=capability,
                )
            for path, payload in protected.items():
                self.assertEqual(path.read_bytes(), payload)
                metadata = path.stat()
                self.assertEqual((metadata.st_dev, metadata.st_ino), identities[path])
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_narrow_writer_fsync_rename_receipt_and_journal_errors_retry(self) -> None:
        operations = (
            ("candidate_result_create", "_create_new_phase_c1_file", False, "candidate_result", 1, None, None),
            ("candidate_report_create", "_create_new_phase_c1_file", False, "candidate_report", 1, None, None),
            ("candidate_result_fsync", "_fsync_phase_c1_open_file", False, "candidate_result", 1, None, None),
            ("candidate_report_fsync", "_fsync_phase_c1_open_file", False, "candidate_report", 1, None, None),
            ("candidate_stage_fsync", "_fsync_phase_c1_directory", False, "candidate_stage", 1, None, None),
            ("candidate_rename", "_validate_and_rename_phase_c1_directory", False, "candidate_root", 1, None, None),
            ("staging_candidate_journal_root_fsync", "_fsync_phase_c1_directory", False, "ignored_root", 1, None, None),
            ("candidate_parent_fsync", "_fsync_phase_c1_directory", False, "ignored_root", 2, None, None),
            ("receipt_stage_create", "_create_new_phase_c1_file", False, "receipt_stage", 1, None, None),
            ("receipt_stage_fsync", "_fsync_phase_c1_open_file", False, "receipt_stage", 1, None, None),
            ("receipt_rename", "_rename_phase_c1_file_no_overwrite", False, "receipt", 1, None, None),
            ("receipt_parent_fsync", "_fsync_phase_c1_directory", False, "ignored_root", 3, None, None),
            ("journal_stage_create", "_create_new_phase_c1_file", False, "journal_stage", 1, None, None),
            ("journal_stage_fsync", "_fsync_phase_c1_open_file", False, "journal_stage", 1, None, None),
            ("journal_replace", "_replace_phase_c1_file", False, "journal", 1, None, None),
            ("candidate_ready_journal_root_fsync", "_fsync_phase_c1_directory", False, "ignored_root", 4, None, None),
            ("canonical_result_create", "_create_new_phase_c1_file", True, "canonical_result", 1, None, None),
            ("canonical_report_create", "_create_new_phase_c1_file", True, "canonical_report", 1, None, None),
            ("canonical_result_fsync", "_fsync_phase_c1_open_file", True, "canonical_result", 1, None, None),
            ("canonical_report_fsync", "_fsync_phase_c1_open_file", True, "canonical_report", 1, None, None),
            ("canonical_stage_fsync", "_fsync_phase_c1_directory", True, "canonical_stage", 1, None, None),
            ("staging_canonical_journal_root_fsync", "_fsync_phase_c1_directory", True, "ignored_root", 1, "staging_canonical", "journal_durability"),
            ("canonical_rename", "_validate_and_rename_phase_c1_directory", True, "canonical_root", 1, None, None),
            ("canonical_parent_fsync", "_fsync_phase_c1_directory", True, "canonical_parent", 1, None, None),
            ("accepted_journal_root_fsync", "_fsync_phase_c1_directory", True, "ignored_root", 2, "accepted", "journal_durability"),
        )
        for (
            label,
            helper_name,
            acceptance,
            target_key,
            occurrence,
            expected_journal_status,
            expected_journal_phase,
        ) in operations:
            with self.subTest(label=label), self.isolated_mutation_root():
                paths, paths_patch, head_patch = self.runner_context()
                try:
                    protected = self.seed_protected_source_research_children()
                    if acceptance:
                        self.create_candidate()
                        self.seed_valid_candidate_validation_and_review_receipts()
                        prepared = self.prepare_acceptance()
                        expected_status = "accepted"
                    else:
                        prepared = self.prepared_candidate()
                        expected_status = "candidate_ready"
                    target_paths = {
                        "candidate_result": paths.candidate_stage_path / "result.json",
                        "candidate_report": paths.candidate_stage_path / "report.md",
                        "candidate_stage": paths.candidate_stage_path,
                        "candidate_root": paths.candidate_root,
                        "ignored_root": paths.ignored_root,
                        "receipt_stage": paths.candidate_receipt_stage_path,
                        "receipt": paths.candidate_receipt_path,
                        "journal_stage": paths.publication_journal_stage_path,
                        "journal": paths.publication_journal_path,
                        "canonical_result": paths.canonical_stage_path / "result.json",
                        "canonical_report": paths.canonical_stage_path / "report.md",
                        "canonical_stage": paths.canonical_stage_path,
                        "canonical_root": paths.canonical_root,
                        "canonical_parent": paths.canonical_root.parent,
                    }
                    target_path = target_paths[target_key].resolve()
                    original = getattr(runner, helper_name)
                    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
                    journal_durability_phase: tuple[str, str] | None = None

                    def operation_paths(args: tuple[object, ...]) -> tuple[Path, ...]:
                        paths_seen: list[Path] = []
                        for value in args:
                            if isinstance(value, Path):
                                paths_seen.append(value)
                            elif isinstance(getattr(value, "name", None), str):
                                paths_seen.append(Path(value.name))
                        return tuple(paths_seen)

                    def delegate_until_exact_target(*args: object, **kwargs: object) -> object:
                        nonlocal journal_durability_phase
                        calls.append((args, kwargs))
                        matching = [
                            path for path in operation_paths(args)
                            if path.resolve() == target_path
                        ]
                        target_calls = len([entry for entry in calls if any(
                            path.resolve() == target_path for path in operation_paths(entry[0])
                        )])
                        if matching and expected_journal_status is not None:
                            journal = paths.publication_journal_path
                            self.assertTrue(journal.is_file())
                            payload = phase_c1.load_json_strict(
                                journal.read_bytes(), source="journal_durability_fsync",
                            )
                            self.assertIsInstance(payload, dict)
                            if target_calls == occurrence:
                                self.assertEqual(
                                    journal_durability_phase,
                                    (
                                        expected_journal_status,
                                        expected_journal_phase,
                                    ),
                                )
                                self.assertEqual(
                                    payload["status"], expected_journal_status,
                                )
                            journal_durability_phase = None
                        if target_calls == occurrence and matching:
                            raise OSError(label)
                        return original(*args, **kwargs)

                    def record_journal_durability_transition(
                        *args: object, **kwargs: object,
                    ) -> object:
                        nonlocal journal_durability_phase
                        result = journal_replace_original(*args, **kwargs)
                        if any(
                            path.resolve() == paths.publication_journal_path.resolve()
                            for path in operation_paths(args)
                        ):
                            payload = phase_c1.load_json_strict(
                                paths.publication_journal_path.read_bytes(),
                                source="journal_durability_transition",
                            )
                            self.assertIsInstance(payload, dict)
                            journal_durability_phase = (
                                str(payload["status"]), "journal_durability",
                            )
                        return result

                    def record_cleanup_phase(*args: object, **kwargs: object) -> object:
                        nonlocal journal_durability_phase
                        journal = paths.publication_journal_path
                        self.assertTrue(journal.is_file())
                        payload = phase_c1.load_json_strict(
                            journal.read_bytes(), source="journal_cleanup_phase",
                        )
                        self.assertIsInstance(payload, dict)
                        journal_durability_phase = (str(payload["status"]), "cleanup")
                        return cleanup_original(*args, **kwargs)

                    with contextlib.ExitStack() as stack:
                        if expected_journal_status is not None:
                            journal_replace_original = getattr(
                                runner, "_replace_phase_c1_file",
                            )
                            stack.enter_context(mock.patch.object(
                                runner,
                                "_replace_phase_c1_file",
                                side_effect=record_journal_durability_transition,
                            ))
                            cleanup_original = getattr(
                                runner, "_delete_verified_phase_c1_cleanup_target",
                            )
                            stack.enter_context(mock.patch.object(
                                runner,
                                "_delete_verified_phase_c1_cleanup_target",
                                side_effect=record_cleanup_phase,
                            ))
                        stack.enter_context(mock.patch.object(
                            runner, helper_name, side_effect=delegate_until_exact_target,
                        ))
                        with self.lock(prepared) as capability:
                            with self.assertRaises(runner.RunnerError):
                                runner.finalize_phase_c1_publication(
                                    prepared, capability=capability,
                                )
                    self.assertTrue(calls)
                    matching_calls = [
                        entry for entry in calls if any(
                            path.resolve() == target_path for path in operation_paths(entry[0])
                        )
                    ]
                    self.assertGreaterEqual(len(matching_calls), occurrence)
                    self.assert_recoverable_publication_state(paths)
                    self.assert_protected_children_unchanged(protected)
                    if acceptance:
                        recovered = self.prepare_acceptance()
                    else:
                        recovered = self.prepared_candidate()
                    with self.lock(recovered) as capability:
                        receipt = runner.finalize_phase_c1_publication(
                            recovered, capability=capability,
                        )
                    self.assertEqual(receipt.status, expected_status)
                    self.assert_protected_children_unchanged(protected)
                    self.assertIsNotNone(original)
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_verified_cleanup_deletes_in_order_and_retries_each_real_delete(self) -> None:
        ordered = (
            "candidate_root", "candidate_receipt", "candidate_validation", "candidate_review",
        )
        target_basenames = {
            "candidate_root": "candidate",
            "candidate_receipt": "candidate-receipt.json",
            "candidate_validation": "candidate-validation.json",
            "candidate_review": "candidate-review.json",
        }
        for target_name in ordered:
            with self.subTest(target=target_name), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    prepared = self.prepare_acceptance()
                    original = getattr(runner, "_delete_verified_phase_c1_cleanup_target")
                    deleted: list[Path] = []

                    def delete_then_interrupt(*args: object, **kwargs: object) -> object:
                        target = Path(args[-1])
                        result = original(*args, **kwargs)
                        deleted.append(target)
                        if target.name == target_basenames[target_name]:
                            raise OSError(target_name)
                        return result

                    with mock.patch.object(
                        runner,
                        "_delete_verified_phase_c1_cleanup_target",
                        side_effect=delete_then_interrupt,
                    ), self.lock(prepared) as capability:
                        with self.assertRaises(runner.RunnerError):
                            runner.finalize_phase_c1_publication(
                                prepared, capability=capability,
                            )
                    expected_prefix = [
                        target_basenames[name]
                        for name in ordered[:ordered.index(target_name) + 1]
                    ]
                    self.assertEqual([path.name for path in deleted], expected_prefix)
                    journal_before_retry = (
                        self.ignored_root / "publication-journal.json"
                    ).read_bytes()
                    recovery = self.prepare_acceptance()
                    with self.lock(recovery) as capability:
                        receipt = runner.finalize_phase_c1_publication(
                            recovery, capability=capability,
                        )
                    self.assertEqual(receipt.status, "accepted")
                    self.assertEqual(
                        (self.ignored_root / "publication-journal.json").read_bytes(),
                        journal_before_retry,
                    )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_durable_operations_use_the_narrow_helpers_in_order(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            ordered_helpers = (
                "_create_new_phase_c1_file",
                "_fsync_phase_c1_open_file",
                "_fsync_phase_c1_directory",
                "_validate_and_rename_phase_c1_directory",
                "_rename_phase_c1_file_no_overwrite",
                "_replace_phase_c1_file",
                "_validate_phase_c1_pair_at_path",
                "_validate_phase_c1_candidate_receipt_at_path",
                "_delete_verified_phase_c1_cleanup_target",
            )
            events: list[tuple[str, str, str | None]] = []
            with contextlib.ExitStack() as stack:
                for helper_name in ordered_helpers:
                    original = getattr(runner, helper_name)

                    def record_then_operate(
                        *args: object,
                        _original: Callable[..., object] = original,
                        _name: str = helper_name,
                        **kwargs: object,
                    ) -> object:
                        path = next((
                            str(value.resolve()) for value in args
                            if isinstance(value, Path)
                        ), next((
                            str(Path(value.name).resolve()) for value in args
                            if isinstance(getattr(value, "name", None), str)
                        ), ""))
                        status = None
                        for value in args:
                            if isinstance(value, dict) and "status" in value:
                                status = str(value["status"])
                            elif isinstance(value, bytes) and b'"status"' in value:
                                parsed = phase_c1.load_json_strict(value, source="journal_event")
                                if isinstance(parsed, dict):
                                    status = str(parsed.get("status"))
                        if (
                            status is None
                            and _name == "_fsync_phase_c1_directory"
                            and path.replace("\\", "/").endswith(
                                "/emotion-state-004-phase-c1",
                            )
                        ):
                            journal_path = (
                                self.ignored_root / "publication-journal.json"
                            )
                            self.assertTrue(journal_path.is_file())
                            journal = phase_c1.load_json_strict(
                                journal_path.read_bytes(), source="journal_fsync_event",
                            )
                            self.assertIsInstance(journal, dict)
                            status = str(journal["status"])
                        events.append((_name, path, status))
                        return _original(*args, **kwargs)

                    stack.enter_context(mock.patch.object(
                        runner, helper_name, side_effect=record_then_operate,
                    ))
                prepared = self.prepared_candidate()
                with self.lock(prepared) as capability:
                    candidate_receipt = runner.finalize_phase_c1_publication(
                        prepared, capability=capability,
                    )
                self.seed_valid_candidate_validation_and_review_receipts()
                acceptance = self.prepare_acceptance()
                with self.lock(acceptance) as capability:
                    accepted_receipt = runner.finalize_phase_c1_publication(
                        acceptance, capability=capability,
                    )
            self.assertEqual(candidate_receipt.status, "candidate_ready")
            self.assertEqual(accepted_receipt.status, "accepted")
            def event_index(operation: str, suffix: str, occurrence: int = 1) -> int:
                matches = [
                    index for index, (name, path, _status) in enumerate(events)
                    if name == operation and path.replace("\\", "/").endswith(suffix)
                ]
                self.assertGreaterEqual(len(matches), occurrence, (operation, suffix))
                return matches[occurrence - 1]

            result_create = event_index("_create_new_phase_c1_file", "/candidate.stage/result.json")
            result_sync = event_index("_fsync_phase_c1_open_file", "/candidate.stage/result.json")
            report_create = event_index("_create_new_phase_c1_file", "/candidate.stage/report.md")
            report_sync = event_index("_fsync_phase_c1_open_file", "/candidate.stage/report.md")
            stage_sync = event_index("_fsync_phase_c1_directory", "/candidate.stage")
            rename = event_index("_validate_and_rename_phase_c1_directory", "/candidate")
            parent_sync = event_index("_fsync_phase_c1_directory", "/emotion-state-004-phase-c1", 2)
            candidate_validate = event_index("_validate_phase_c1_pair_at_path", "/candidate")
            receipt_create = event_index("_create_new_phase_c1_file", "/candidate-receipt.stage")
            receipt_sync = event_index("_fsync_phase_c1_open_file", "/candidate-receipt.stage")
            receipt_rename = event_index("_rename_phase_c1_file_no_overwrite", "/candidate-receipt.json")
            receipt_parent_sync = event_index("_fsync_phase_c1_directory", "/emotion-state-004-phase-c1", 3)
            receipt_validate = event_index(
                "_validate_phase_c1_candidate_receipt_at_path",
                "/candidate-receipt.json",
            )
            canonical_result_create = event_index("_create_new_phase_c1_file", "/canonical.stage/result.json")
            canonical_report_create = event_index("_create_new_phase_c1_file", "/canonical.stage/report.md")
            canonical_result_sync = event_index("_fsync_phase_c1_open_file", "/canonical.stage/result.json")
            canonical_report_sync = event_index("_fsync_phase_c1_open_file", "/canonical.stage/report.md")
            canonical_stage_sync = event_index("_fsync_phase_c1_directory", "/canonical.stage")
            canonical_rename = event_index("_validate_and_rename_phase_c1_directory", "/EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission")
            canonical_parent_sync = event_index("_fsync_phase_c1_directory", "/generated")
            canonical_validate = event_index("_validate_phase_c1_pair_at_path", "/EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission")
            self.assertLess(result_create, result_sync)
            self.assertLess(result_sync, report_create)
            self.assertLess(report_create, report_sync)
            self.assertLess(report_sync, stage_sync)
            self.assertLess(stage_sync, rename)
            self.assertLess(rename, parent_sync)
            self.assertLess(parent_sync, candidate_validate)
            self.assertLess(candidate_validate, receipt_create)
            self.assertLess(receipt_create, receipt_sync)
            self.assertLess(receipt_sync, receipt_rename)
            self.assertLess(receipt_rename, receipt_parent_sync)
            self.assertLess(receipt_parent_sync, receipt_validate)
            self.assertLess(canonical_result_create, canonical_report_create)
            self.assertLess(canonical_result_create, canonical_result_sync)
            self.assertLess(canonical_result_sync, canonical_report_create)
            self.assertLess(canonical_report_create, canonical_report_sync)
            self.assertLess(canonical_report_sync, canonical_stage_sync)
            self.assertLess(canonical_stage_sync, canonical_rename)
            self.assertLess(canonical_rename, canonical_parent_sync)
            self.assertLess(canonical_parent_sync, canonical_validate)
            journal_stage_events = [
                (index, status) for index, (name, path, status) in enumerate(events)
                if name == "_create_new_phase_c1_file"
                and path.replace("\\", "/").endswith("/publication-journal.stage")
            ]
            self.assertEqual(
                [status for _index, status in journal_stage_events],
                ["staging_candidate", "candidate_ready", "staging_canonical", "accepted"],
            )
            journal_stage_syncs = [
                index for index, (name, path, _status) in enumerate(events)
                if name == "_fsync_phase_c1_open_file"
                and path.replace("\\", "/").endswith("/publication-journal.stage")
            ]
            journal_replaces = [
                index for index, (name, path, _status) in enumerate(events)
                if name == "_replace_phase_c1_file"
                and path.replace("\\", "/").endswith("/publication-journal.json")
            ]
            ignored_root_syncs = [
                (index, status) for index, (name, path, status) in enumerate(events)
                if name == "_fsync_phase_c1_directory"
                and path.replace("\\", "/").endswith("/emotion-state-004-phase-c1")
            ]
            self.assertGreaterEqual(len(journal_stage_syncs), 4)
            self.assertGreaterEqual(len(journal_replaces), 4)
            self.assertGreaterEqual(len(ignored_root_syncs), 6)
            self.assertEqual(
                [status for _index, status in ignored_root_syncs[:6]],
                [
                    "staging_candidate",
                    "staging_candidate",
                    "staging_candidate",
                    "candidate_ready",
                    "staging_canonical",
                    "accepted",
                ],
            )
            journal_root_sync_positions = (0, 3, 4, 5)
            for ordinal, (stage_index, _status) in enumerate(journal_stage_events):
                self.assertLess(stage_index, journal_stage_syncs[ordinal])
                self.assertLess(journal_stage_syncs[ordinal], journal_replaces[ordinal])
                self.assertLess(
                    journal_replaces[ordinal],
                    ignored_root_syncs[journal_root_sync_positions[ordinal]][0],
                )
            self.assertLess(ignored_root_syncs[0][0], result_create)
            self.assertLess(receipt_validate, journal_stage_events[1][0])
            self.assertLess(ignored_root_syncs[3][0], journal_stage_events[2][0])
            self.assertLess(ignored_root_syncs[4][0], canonical_result_create)
            accepted_stage_index = journal_stage_events[3][0]
            self.assertLess(canonical_validate, accepted_stage_index)
            cleanup_events = [
                (index, path) for index, (name, path, _status) in enumerate(events)
                if name == "_delete_verified_phase_c1_cleanup_target"
            ]
            self.assertEqual(
                [Path(path).name for _index, path in cleanup_events],
                ["candidate", "candidate-receipt.json", "candidate-validation.json", "candidate-review.json"],
            )
            self.assertGreater(cleanup_events[0][0], ignored_root_syncs[5][0])
            self.assertFalse(self.candidate_root.exists())
            self.assertFalse((self.ignored_root / "candidate.stage").exists())
            self.assertFalse((self.ignored_root / "canonical.stage").exists())
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_cleanup_rejects_a_link_without_deleting_its_target(self) -> None:
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            prepared = runner._prepare_phase_c1_acceptance(
                expected_head="a" * 40,
                candidate_receipt_name="candidate-receipt.json",
                candidate_validation_name="candidate-validation.json",
                candidate_review_name="candidate-review.json",
            )
            with self.lock(prepared) as capability:
                runner.finalize_phase_c1_publication(prepared, capability=capability)
            outside = self.temp_root / "outside-candidate-receipt.json"
            outside.write_bytes(b"do-not-delete")
            self.create_test_reparse(
                self.ignored_root / "candidate-receipt.json",
                outside,
            )
            with self.assertRaises(runner.RunnerError):
                runner._prepare_phase_c1_acceptance(
                    expected_head="a" * 40,
                    candidate_receipt_name="candidate-receipt.json",
                    candidate_validation_name="candidate-validation.json",
                    candidate_review_name="candidate-review.json",
                )
            self.assertEqual(outside.read_bytes(), b"do-not-delete")
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_ready_missing_candidate_root_rejects_without_rewrite(self) -> None:
        """A ready journal may revalidate a candidate, never reconstruct one."""
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            journal_path = self.ignored_root / "publication-journal.json"
            receipt_path = self.ignored_root / "candidate-receipt.json"
            journal_before = journal_path.read_bytes()
            receipt_before = receipt_path.read_bytes()
            shutil.rmtree(self.candidate_root)

            prepared = self.prepared_candidate()
            with self.lock(prepared) as capability:
                with self.assertRaises(runner.RunnerError):
                    runner.finalize_phase_c1_publication(
                        prepared, capability=capability,
                    )

            self.assertFalse(self.candidate_root.exists())
            self.assertEqual(journal_path.read_bytes(), journal_before)
            self.assertEqual(receipt_path.read_bytes(), receipt_before)
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_missing_canonical_rejects_without_republication(self) -> None:
        """An accepted journal is not authority to recreate a missing canonical pair."""
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            candidate_snapshot = {
                child.name: child.read_bytes() for child in self.candidate_root.iterdir()
            }
            receipt_snapshot = {
                name: (self.ignored_root / name).read_bytes()
                for name in (
                    "candidate-receipt.json",
                    "candidate-validation.json",
                    "candidate-review.json",
                )
            }
            prepared = self.prepare_acceptance()
            with self.lock(prepared) as capability:
                runner.finalize_phase_c1_publication(prepared, capability=capability)
            journal_path = self.ignored_root / "publication-journal.json"
            journal_before = journal_path.read_bytes()
            shutil.rmtree(self.canonical_root)
            self.candidate_root.mkdir()
            for name, payload in candidate_snapshot.items():
                (self.candidate_root / name).write_bytes(payload)
            for name, payload in receipt_snapshot.items():
                (self.ignored_root / name).write_bytes(payload)

            with self.assertRaises(runner.RunnerError):
                recovery = self.prepare_acceptance()
                with self.lock(recovery) as capability:
                    runner.finalize_phase_c1_publication(
                        recovery, capability=capability,
                    )

            self.assertFalse(self.canonical_root.exists())
            self.assertEqual(journal_path.read_bytes(), journal_before)
            self.assertEqual(
                {child.name: child.read_bytes() for child in self.candidate_root.iterdir()},
                candidate_snapshot,
            )
            for name, payload in receipt_snapshot.items():
                self.assertEqual((self.ignored_root / name).read_bytes(), payload)
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_acceptance_rejects_staging_candidate_without_rewrite(self) -> None:
        """Acceptance may begin only from a ready candidate journal transition."""
        _paths, paths_patch, head_patch = self.runner_context()
        try:
            self.create_candidate()
            self.seed_valid_candidate_validation_and_review_receipts()
            journal_before = self.write_exact_journal(status="staging_candidate")
            candidate_before = {
                child.name: child.read_bytes() for child in self.candidate_root.iterdir()
            }

            with self.assertRaises(runner.RunnerError):
                prepared = self.prepare_acceptance()
                with self.lock(prepared) as capability:
                    runner.finalize_phase_c1_publication(
                        prepared, capability=capability,
                    )

            self.assertEqual(
                (self.ignored_root / "publication-journal.json").read_bytes(),
                journal_before,
            )
            self.assertFalse(self.canonical_root.exists())
            self.assertEqual(
                {child.name: child.read_bytes() for child in self.candidate_root.iterdir()},
                candidate_before,
            )
        finally:
            self.stop_runner_context(paths_patch, head_patch)

    def test_journal_transition_matrix_rejects_illegal_edges(self) -> None:
        """Journal status is a constrained state machine, not a free enum."""
        cases = (
            ("candidate_ready", "staging_candidate", False),
            ("candidate_ready", "staging_canonical", False),
            ("staging_candidate", "accepted", True),
            ("accepted", "staging_canonical", True),
        )
        for source, target, acceptance_state in cases:
            with self.subTest(source=source, target=target), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    # Prepare only from the valid candidate-ready baseline.
                    # The synthetic source journal below is the sole transition
                    # fixture, so its invalidity cannot short-circuit preparation.
                    prepared = (
                        self.prepare_acceptance()
                        if acceptance_state
                        else self.prepared_candidate()
                    )
                    if source == "accepted":
                        _predecessor, current = self.write_valid_journal_chain(
                            final_status="accepted",
                        )
                    else:
                        current = self.write_exact_journal(status=source)
                    state = runner._state_for(prepared)
                    journal_path = self.ignored_root / "publication-journal.json"
                    with self.assertRaises(runner.RunnerError):
                        runner._advance_journal(state, status=target, current=current)
                    self.assertEqual(journal_path.read_bytes(), current)
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_cleanup_rechecks_every_retained_target_before_deletion(self) -> None:
        """Accepted cleanup is allowed only for byte-verified transaction artifacts."""
        mutations = (
            "candidate_pair_tamper",
            "candidate_unknown_child",
            "candidate_receipt_tamper",
            "candidate_validation_tamper",
            "candidate_review_tamper",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    candidate_snapshot = {
                        child.name: child.read_bytes()
                        for child in self.candidate_root.iterdir()
                    }
                    receipt_snapshot = {
                        name: (self.ignored_root / name).read_bytes()
                        for name in (
                            "candidate-receipt.json",
                            "candidate-validation.json",
                            "candidate-review.json",
                        )
                    }
                    prepared = self.prepare_acceptance()
                    with self.lock(prepared) as capability:
                        runner.finalize_phase_c1_publication(
                            prepared, capability=capability,
                        )
                    journal_path = self.ignored_root / "publication-journal.json"
                    journal_before = journal_path.read_bytes()
                    self.candidate_root.mkdir()
                    for name, payload in candidate_snapshot.items():
                        (self.candidate_root / name).write_bytes(payload)
                    for name, payload in receipt_snapshot.items():
                        (self.ignored_root / name).write_bytes(payload)
                    if mutation == "candidate_pair_tamper":
                        (self.candidate_root / "report.md").write_bytes(b"tampered\n")
                    elif mutation == "candidate_unknown_child":
                        (self.candidate_root / "unexpected").write_bytes(b"unexpected\n")
                    elif mutation == "candidate_receipt_tamper":
                        (self.ignored_root / "candidate-receipt.json").write_bytes(
                            b"tampered\n",
                        )
                    elif mutation == "candidate_validation_tamper":
                        (self.ignored_root / "candidate-validation.json").write_bytes(
                            b"tampered\n",
                        )
                    else:
                        (self.ignored_root / "candidate-review.json").write_bytes(
                            b"tampered\n",
                        )
                    candidate_before = {
                        child.name: child.read_bytes()
                        for child in self.candidate_root.iterdir()
                    }
                    receipts_before = {
                        name: (self.ignored_root / name).read_bytes()
                        for name in receipt_snapshot
                    }

                    with self.assertRaises(runner.RunnerError):
                        recovery = self.prepare_acceptance()
                        with self.lock(recovery) as capability:
                            runner.finalize_phase_c1_publication(
                                recovery, capability=capability,
                            )

                    self.assertEqual(journal_path.read_bytes(), journal_before)
                    self.assertEqual(
                        {child.name: child.read_bytes() for child in self.candidate_root.iterdir()},
                        candidate_before,
                    )
                    for name, payload in receipts_before.items():
                        self.assertEqual((self.ignored_root / name).read_bytes(), payload)
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    @unittest.skipUnless(os.name == "nt", "Windows directory durability contract")
    def test_windows_directory_fsync_uses_fail_closed_backend(self) -> None:
        """Windows directory fsync must not silently become a successful no-op."""
        # This is the owned test root, never a repository publication path. A
        # mock-only dispatch assertion would not prove that the Win32 backend
        # can acquire and flush a real directory handle.
        runner._flush_phase_c1_windows_directory(self.temp_root)

        backend = mock.Mock()
        with mock.patch.object(
            runner, "_flush_phase_c1_windows_directory", backend, create=True,
        ):
            runner._fsync_phase_c1_directory(self.temp_root)
        backend.assert_called_once_with(self.temp_root)

        with mock.patch.object(
            runner,
            "_flush_phase_c1_windows_directory",
            side_effect=OSError("directory flush failed"),
            create=True,
        ):
            with self.assertRaisesRegex(runner.RunnerError, "directory_fsync"):
                runner._fsync_phase_c1_directory(self.temp_root)

    def test_canonical_unknown_child_reparse_and_pair_mismatch_block_without_deletion(self) -> None:
        for mutation in ("unknown_child", "reparse", "pair_mismatch", "disallowed_status"):
            with self.subTest(mutation=mutation), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    self.canonical_root.mkdir(parents=True)
                    (self.canonical_root / "result.json").write_bytes(
                        self.expected_candidate_result_bytes,
                    )
                    (self.canonical_root / "report.md").write_bytes(
                        self.expected_candidate_report_bytes,
                    )
                    self.write_valid_journal_chain(final_status="staging_canonical")
                    outside: Path | None = None
                    if mutation == "unknown_child":
                        (self.canonical_root / "unexpected").write_bytes(b"x")
                    elif mutation == "reparse":
                        outside = self.temp_root / "outside-canonical-child"
                        outside.write_bytes(b"outside")
                        self.create_test_reparse(
                            self.canonical_root / "linked",
                            outside,
                        )
                    elif mutation == "pair_mismatch":
                        (self.canonical_root / "report.md").write_bytes(b"tampered\n")
                    else:
                        journal_path = self.ignored_root / "publication-journal.json"
                        journal = phase_c1.load_json_strict(
                            journal_path.read_bytes(), source="staging_canonical",
                        )
                        self.assertIsInstance(journal, dict)
                        before_status = copy.deepcopy(journal)
                        journal["status"] = "candidate_ready"
                        journal["journal_content_sha256"] = ""
                        journal["journal_content_sha256"] = self._sha256(
                            phase_c1.canonical_json_bytes(journal),
                        )
                        self.assertEqual(
                            {key: value for key, value in journal.items()
                             if key not in {"status", "journal_content_sha256"}},
                            {key: value for key, value in before_status.items()
                             if key not in {"status", "journal_content_sha256"}},
                        )
                        journal_path.write_bytes(phase_c1.canonical_json_bytes(journal))
                    canonical_snapshot = {
                        path.name: self.snapshot_test_child(path)
                        for path in self.canonical_root.iterdir()
                    }
                    outside_snapshot = None if outside is None else (
                        outside.lstat().st_ino, outside.read_bytes(),
                    )
                    with self.assertRaises(runner.RunnerError):
                        self.prepare_acceptance()
                    after_snapshot = {
                        path.name: self.snapshot_test_child(path)
                        for path in self.canonical_root.iterdir()
                    }
                    self.assertEqual(after_snapshot, canonical_snapshot)
                    if outside is not None:
                        self.assertEqual(
                            (outside.lstat().st_ino, outside.read_bytes()), outside_snapshot,
                        )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_canonical_parent_reparse_between_prepare_and_finalize_rejects_before_outside_write(
        self,
    ) -> None:
        """A canonical target parent may never redirect a fixed-path publish."""
        with self.isolated_mutation_root():
            _paths, paths_patch, head_patch = self.runner_context()
            saved_parent: Path | None = None
            try:
                self.create_candidate()
                self.seed_valid_candidate_validation_and_review_receipts()
                prepared = self.prepare_acceptance()
                candidate_journal = (
                    self.ignored_root / "publication-journal.json"
                ).read_bytes()
                candidate_result = (
                    self.candidate_root / "result.json"
                ).read_bytes()
                candidate_report = (
                    self.candidate_root / "report.md"
                ).read_bytes()
                candidate_receipt = (
                    self.ignored_root / "candidate-receipt.json"
                ).read_bytes()
                parent = self.canonical_root.parent
                saved_parent = parent.with_name("generated-saved")
                outside = self.temp_root / "outside-generated"
                os.replace(parent, saved_parent)
                outside.mkdir()
                self.create_test_reparse(parent, outside)

                with self.lock(prepared) as capability:
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                self.assertFalse(
                    (outside / self.canonical_root.name).exists(),
                )
                self.assertFalse(self.canonical_root.exists())
                self.assertFalse(
                    (self.ignored_root / "canonical.stage").exists(),
                )
                self.assertEqual(
                    (self.ignored_root / "publication-journal.json").read_bytes(),
                    candidate_journal,
                )
                self.assertEqual(
                    (self.candidate_root / "result.json").read_bytes(),
                    candidate_result,
                )
                self.assertEqual(
                    (self.candidate_root / "report.md").read_bytes(),
                    candidate_report,
                )
                self.assertEqual(
                    (self.ignored_root / "candidate-receipt.json").read_bytes(),
                    candidate_receipt,
                )
            finally:
                parent = self.canonical_root.parent
                if saved_parent is not None and os.path.lexists(parent):
                    os.rmdir(parent)
                if saved_parent is not None and saved_parent.exists():
                    os.replace(saved_parent, parent)
                self.stop_runner_context(paths_patch, head_patch)

    def test_held_destination_parent_authority_prevents_path_redirection(
        self,
    ) -> None:
        """The rename destination is the held directory, never a replaced path."""
        with self.isolated_mutation_root():
            destination_parent = self.temp_root / "destination"
            destination_parent.mkdir()
            saved_parent = self.temp_root / "destination-saved"
            outside_parent = self.temp_root / "outside-destination"
            outside_parent.mkdir()
            stage = self.temp_root / "canonical.stage"
            stage.mkdir()
            (stage / "result.json").write_bytes(b"result\n")
            (stage / "report.md").write_bytes(b"report\n")
            target = destination_parent / "canonical"
            attempted = False
            blocked = False
            swapped = False

            try:
                with runner._held_phase_c1_directory_authority(
                    destination_parent,
                ) as authority:
                    real_verify = (
                        runner._verify_held_phase_c1_directory_authority
                    )

                    def attempt_path_redirection(
                        active_authority: object,
                    ) -> None:
                        nonlocal attempted, blocked, swapped
                        real_verify(active_authority)
                        if attempted:
                            return
                        attempted = True
                        try:
                            os.replace(destination_parent, saved_parent)
                        except OSError:
                            blocked = True
                            return
                        swapped = True
                        if os.name == "nt":
                            self.create_test_reparse(
                                destination_parent,
                                outside_parent,
                            )
                        else:
                            os.symlink(
                                outside_parent,
                                destination_parent,
                                target_is_directory=True,
                            )

                    with mock.patch.object(
                        runner,
                        "_verify_held_phase_c1_directory_authority",
                        side_effect=attempt_path_redirection,
                    ):
                        if os.name == "nt":
                            runner._rename_phase_c1_directory_no_overwrite(
                                target,
                                stage,
                                authority=authority,
                            )
                        else:
                            with self.assertRaises(runner.RunnerError):
                                runner._rename_phase_c1_directory_no_overwrite(
                                    target,
                                    stage,
                                    authority=authority,
                                )

                self.assertTrue(attempted)
                self.assertFalse((outside_parent / target.name).exists())
                if os.name == "nt":
                    self.assertTrue(blocked)
                    self.assertFalse(swapped)
                    self.assertTrue(target.is_dir())
                    self.assertFalse(stage.exists())
                else:
                    self.assertFalse(blocked)
                    self.assertTrue(swapped)
                    self.assertTrue((saved_parent / target.name).is_dir())
                    self.assertFalse(stage.exists())
            finally:
                if swapped and os.path.lexists(destination_parent):
                    if destination_parent.is_symlink():
                        destination_parent.unlink()
                    else:
                        os.rmdir(destination_parent)
                if swapped and saved_parent.exists():
                    os.replace(saved_parent, destination_parent)

    def test_authority_rename_is_atomic_no_overwrite_at_actual_seam(
        self,
    ) -> None:
        """A target raced into existence survives the actual rename attempt."""
        with self.isolated_mutation_root():
            destination_parent = self.temp_root / "destination"
            destination_parent.mkdir()
            stage = self.temp_root / "candidate.stage"
            stage.mkdir()
            result_bytes = b"result\n"
            report_bytes = b"report\n"
            (stage / "result.json").write_bytes(result_bytes)
            (stage / "report.md").write_bytes(report_bytes)
            target = destination_parent / "candidate"
            raced_bytes = b"raced target\n"
            raced_identity: tuple[int, int] | None = None

            with runner._held_phase_c1_directory_authority(
                destination_parent,
            ) as authority:
                real_rename = runner._rename_phase_c1_directory_at_authority

                def create_target_at_rename_seam(
                    source: Path,
                    destination_name: str,
                    *,
                    authority: object,
                ) -> None:
                    nonlocal raced_identity
                    target.write_bytes(raced_bytes)
                    metadata = target.lstat()
                    raced_identity = (metadata.st_dev, metadata.st_ino)
                    real_rename(
                        source,
                        destination_name,
                        authority=authority,
                    )

                with mock.patch.object(
                    runner,
                    "_rename_phase_c1_directory_at_authority",
                    side_effect=create_target_at_rename_seam,
                ):
                    with self.assertRaises(runner.RunnerError) as raised:
                        runner._rename_phase_c1_directory_no_overwrite(
                            target,
                            stage,
                            authority=authority,
                        )

            self.assertEqual(raised.exception.code, "target_exists")
            self.assertIsNotNone(raced_identity)
            metadata = target.lstat()
            self.assertEqual(
                (metadata.st_dev, metadata.st_ino),
                raced_identity,
            )
            self.assertEqual(target.read_bytes(), raced_bytes)
            self.assertEqual(
                (stage / "result.json").read_bytes(),
                result_bytes,
            )
            self.assertEqual(
                (stage / "report.md").read_bytes(),
                report_bytes,
            )

    def test_journal_commit_binds_held_stage_and_predecessor_at_actual_seam(
        self,
    ) -> None:
        """Journal replacement is bound to both verified file identities."""
        for mutation in ("stage", "predecessor"):
            with self.subTest(mutation=mutation), self.isolated_mutation_root():
                parent = self.temp_root / "publication"
                parent.mkdir()
                journal = parent / "publication-journal.json"
                stage = parent / "publication-journal.stage"
                prior_bytes = b"prior journal\n"
                next_bytes = b"next journal\n"
                journal.write_bytes(prior_bytes)
                stage.write_bytes(next_bytes)
                prior_identity = (
                    journal.lstat().st_dev,
                    journal.lstat().st_ino,
                )
                moved = parent / f"{mutation}-moved"
                replacement_bytes = f"raced {mutation}\n".encode("ascii")
                attempted = False
                blocked = False
                swapped = False

                with runner._held_phase_c1_directory_authority(
                    parent,
                ) as parent_authority, runner._held_phase_c1_regular_file_authority(
                    stage,
                    expected_bytes=next_bytes,
                ) as stage_authority, runner._held_phase_c1_regular_file_authority(
                    journal,
                    expected_bytes=prior_bytes,
                ) as predecessor_authority:
                    real_commit = (
                        runner._commit_phase_c1_regular_file_at_authority
                    )

                    def replace_entry_at_commit_seam(
                        active_stage: object,
                        destination_name: str,
                        *,
                        parent_authority: object,
                        replace: bool,
                        predecessor_authority: object | None,
                    ) -> None:
                        nonlocal attempted, blocked, swapped
                        attempted = True
                        raced_path = stage if mutation == "stage" else journal
                        try:
                            os.replace(raced_path, moved)
                        except OSError:
                            blocked = True
                        else:
                            swapped = True
                            raced_path.write_bytes(replacement_bytes)
                        try:
                            real_commit(
                                active_stage,
                                destination_name,
                                parent_authority=parent_authority,
                                replace=replace,
                                predecessor_authority=predecessor_authority,
                            )
                        finally:
                            if swapped:
                                raced_path.unlink(missing_ok=True)
                                os.replace(moved, raced_path)

                    with mock.patch.object(
                        runner,
                        "_commit_phase_c1_regular_file_at_authority",
                        side_effect=replace_entry_at_commit_seam,
                    ):
                        if os.name == "nt":
                            runner._publish_phase_c1_journal_stage_at_authority(
                                journal,
                                stage,
                                expected_payload=next_bytes,
                                parent_authority=parent_authority,
                                stage_authority=stage_authority,
                                predecessor_authority=predecessor_authority,
                            )
                        else:
                            with self.assertRaises(runner.RunnerError):
                                runner._publish_phase_c1_journal_stage_at_authority(
                                    journal,
                                    stage,
                                    expected_payload=next_bytes,
                                    parent_authority=parent_authority,
                                    stage_authority=stage_authority,
                                    predecessor_authority=predecessor_authority,
                                )

                self.assertTrue(attempted)
                if os.name == "nt":
                    self.assertTrue(blocked)
                    self.assertFalse(swapped)
                    self.assertEqual(journal.read_bytes(), next_bytes)
                    self.assertFalse(stage.exists())
                else:
                    self.assertFalse(blocked)
                    self.assertTrue(swapped)
                    self.assertEqual(journal.read_bytes(), prior_bytes)
                    self.assertEqual(
                        (journal.lstat().st_dev, journal.lstat().st_ino),
                        prior_identity,
                    )
                    self.assertEqual(stage.read_bytes(), next_bytes)

    def test_receipt_commit_binds_held_stage_at_actual_seam(
        self,
    ) -> None:
        """A swapped verified receipt stage cannot become the final receipt."""
        with self.isolated_mutation_root():
            parent = self.temp_root / "publication"
            parent.mkdir()
            receipt = parent / "candidate-receipt.json"
            stage = parent / "candidate-receipt.stage"
            receipt_bytes = b"candidate receipt\n"
            replacement_bytes = b"raced receipt stage\n"
            stage.write_bytes(receipt_bytes)
            stage_identity = (stage.lstat().st_dev, stage.lstat().st_ino)
            moved = parent / "candidate-receipt.original-stage"
            attempted = False
            blocked = False
            swapped = False

            with runner._held_phase_c1_directory_authority(
                parent,
            ) as parent_authority, runner._held_phase_c1_regular_file_authority(
                stage,
                expected_bytes=receipt_bytes,
            ) as stage_authority:
                real_commit = runner._commit_phase_c1_regular_file_at_authority

                def replace_stage_at_commit_seam(
                    active_stage: object,
                    destination_name: str,
                    *,
                    parent_authority: object,
                    replace: bool,
                    predecessor_authority: object | None,
                ) -> None:
                    nonlocal attempted, blocked, swapped
                    attempted = True
                    try:
                        os.replace(stage, moved)
                    except OSError:
                        blocked = True
                    else:
                        swapped = True
                        stage.write_bytes(replacement_bytes)
                    try:
                        real_commit(
                            active_stage,
                            destination_name,
                            parent_authority=parent_authority,
                            replace=replace,
                            predecessor_authority=predecessor_authority,
                        )
                    finally:
                        if swapped:
                            stage.unlink(missing_ok=True)
                            os.replace(moved, stage)

                with mock.patch.object(
                    runner,
                    "_commit_phase_c1_regular_file_at_authority",
                    side_effect=replace_stage_at_commit_seam,
                ):
                    if os.name == "nt":
                        runner._publish_phase_c1_receipt_stage_at_authority(
                            receipt,
                            stage,
                            expected_payload=receipt_bytes,
                            parent_authority=parent_authority,
                            stage_authority=stage_authority,
                        )
                    else:
                        with self.assertRaises(runner.RunnerError):
                            runner._publish_phase_c1_receipt_stage_at_authority(
                                receipt,
                                stage,
                                expected_payload=receipt_bytes,
                                parent_authority=parent_authority,
                                stage_authority=stage_authority,
                            )

            self.assertTrue(attempted)
            if os.name == "nt":
                self.assertTrue(blocked)
                self.assertFalse(swapped)
                self.assertEqual(receipt.read_bytes(), receipt_bytes)
                self.assertFalse(stage.exists())
            else:
                self.assertFalse(blocked)
                self.assertTrue(swapped)
                self.assertFalse(receipt.exists())
                self.assertEqual(stage.read_bytes(), receipt_bytes)
                self.assertEqual(
                    (stage.lstat().st_dev, stage.lstat().st_ino),
                    stage_identity,
                )

    def test_receipt_commit_is_atomic_no_overwrite_at_actual_seam(
        self,
    ) -> None:
        """A raced final receipt survives and the verified stage remains valid."""
        with self.isolated_mutation_root():
            parent = self.temp_root / "publication"
            parent.mkdir()
            receipt = parent / "candidate-receipt.json"
            stage = parent / "candidate-receipt.stage"
            receipt_bytes = b"candidate receipt\n"
            raced_bytes = b"raced final receipt\n"
            stage.write_bytes(receipt_bytes)
            raced_identity: tuple[int, int] | None = None

            with runner._held_phase_c1_directory_authority(
                parent,
            ) as parent_authority, runner._held_phase_c1_regular_file_authority(
                stage,
                expected_bytes=receipt_bytes,
            ) as stage_authority:
                real_commit = runner._commit_phase_c1_regular_file_at_authority

                def create_final_at_commit_seam(
                    active_stage: object,
                    destination_name: str,
                    *,
                    parent_authority: object,
                    replace: bool,
                    predecessor_authority: object | None,
                ) -> None:
                    nonlocal raced_identity
                    receipt.write_bytes(raced_bytes)
                    metadata = receipt.lstat()
                    raced_identity = (metadata.st_dev, metadata.st_ino)
                    real_commit(
                        active_stage,
                        destination_name,
                        parent_authority=parent_authority,
                        replace=replace,
                        predecessor_authority=predecessor_authority,
                    )

                with mock.patch.object(
                    runner,
                    "_commit_phase_c1_regular_file_at_authority",
                    side_effect=create_final_at_commit_seam,
                ):
                    with self.assertRaises(runner.RunnerError) as raised:
                        runner._publish_phase_c1_receipt_stage_at_authority(
                            receipt,
                            stage,
                            expected_payload=receipt_bytes,
                            parent_authority=parent_authority,
                            stage_authority=stage_authority,
                        )

            self.assertEqual(raised.exception.code, "target_exists")
            self.assertIsNotNone(raced_identity)
            metadata = receipt.lstat()
            self.assertEqual(
                (metadata.st_dev, metadata.st_ino),
                raced_identity,
            )
            self.assertEqual(receipt.read_bytes(), raced_bytes)
            self.assertEqual(stage.read_bytes(), receipt_bytes)

    def test_finalize_holds_ignored_root_authority_before_any_transaction_write(
        self,
    ) -> None:
        """Journal, receipt, and pair mutations share one held root authority."""
        with self.isolated_mutation_root():
            _paths, paths_patch, head_patch = self.runner_context()
            saved_root: Path | None = None
            swapped = False
            try:
                prepared = self.prepared_candidate()
                outside = self.temp_root / "outside-publication"
                outside.mkdir()
                saved_root = self.ignored_root.with_name(
                    "emotion-state-004-phase-c1-saved",
                )
                attempted = False
                blocked = False
                real_verify = (
                    runner._verify_held_phase_c1_directory_authority
                )

                def attempt_ignored_root_redirection(
                    authority: object,
                ) -> None:
                    nonlocal attempted, blocked, swapped
                    real_verify(authority)
                    if attempted or authority.path != self.ignored_root:
                        return
                    attempted = True
                    self.assertFalse(
                        (self.ignored_root / "publication-journal.json").exists(),
                    )
                    self.assertFalse(
                        (self.ignored_root / "candidate-receipt.json").exists(),
                    )
                    self.assertFalse(self.candidate_root.exists())
                    try:
                        os.replace(self.ignored_root, saved_root)
                    except OSError:
                        blocked = True
                        return
                    swapped = True
                    if os.name == "nt":
                        self.create_test_reparse(self.ignored_root, outside)
                    else:
                        os.symlink(
                            outside,
                            self.ignored_root,
                            target_is_directory=True,
                        )

                with self.lock(prepared) as capability, mock.patch.object(
                    runner,
                    "_verify_held_phase_c1_directory_authority",
                    side_effect=attempt_ignored_root_redirection,
                ):
                    if os.name == "nt":
                        receipt = runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )
                        self.assertEqual(receipt.status, "candidate_ready")
                    else:
                        with self.assertRaises(runner.RunnerError):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                self.assertTrue(attempted)
                self.assertFalse(
                    (
                        outside / "publication-journal.json"
                    ).exists(),
                )
                self.assertFalse(
                    (outside / "candidate-receipt.json").exists(),
                )
                self.assertFalse((outside / "candidate").exists())
                if os.name == "nt":
                    self.assertTrue(blocked)
                    self.assertFalse(swapped)
                else:
                    self.assertFalse(blocked)
                    self.assertTrue(swapped)
            finally:
                if saved_root is not None and os.path.lexists(self.ignored_root):
                    if self.ignored_root.is_symlink():
                        self.ignored_root.unlink()
                    elif swapped:
                        os.rmdir(self.ignored_root)
                if (
                    saved_root is not None
                    and saved_root.exists()
                    and not self.ignored_root.exists()
                ):
                    os.replace(saved_root, self.ignored_root)
                self.stop_runner_context(paths_patch, head_patch)

    def test_post_prepare_receipt_changes_reject_before_canonical_acceptance(
        self,
    ) -> None:
        """Acceptance must re-read both independent receipts under its lock."""
        mutations = (
            ("candidate-validation.json", "tamper"),
            ("candidate-validation.json", "delete"),
            ("candidate-review.json", "tamper"),
            ("candidate-review.json", "delete"),
        )
        for name, mutation in mutations:
            with self.subTest(name=name, mutation=mutation), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    candidate_journal = (
                        self.ignored_root / "publication-journal.json"
                    ).read_bytes()
                    candidate_result = (
                        self.candidate_root / "result.json"
                    ).read_bytes()
                    candidate_report = (
                        self.candidate_root / "report.md"
                    ).read_bytes()
                    candidate_receipt = (
                        self.ignored_root / "candidate-receipt.json"
                    ).read_bytes()
                    prepared = self.prepare_acceptance()
                    receipt_path = self.ignored_root / name
                    if mutation == "tamper":
                        receipt_path.write_bytes(b"tampered\n")
                    else:
                        receipt_path.unlink()

                    with self.lock(prepared) as capability:
                        with self.assertRaises(runner.RunnerError):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    self.assertFalse(self.canonical_root.exists())
                    self.assertFalse(
                        (self.ignored_root / "canonical.stage").exists(),
                    )
                    self.assertEqual(
                        (self.ignored_root / "publication-journal.json").read_bytes(),
                        candidate_journal,
                    )
                    self.assertEqual(
                        (self.candidate_root / "result.json").read_bytes(),
                        candidate_result,
                    )
                    self.assertEqual(
                        (self.candidate_root / "report.md").read_bytes(),
                        candidate_report,
                    )
                    self.assertEqual(
                        (self.ignored_root / "candidate-receipt.json").read_bytes(),
                        candidate_receipt,
                    )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_unjournaled_byte_exact_candidate_root_is_not_adopted(self) -> None:
        """Only a verified staging journal can authorize candidate recovery."""
        with self.isolated_mutation_root():
            _paths, paths_patch, head_patch = self.runner_context()
            try:
                self.candidate_root.mkdir(parents=True)
                (self.candidate_root / "result.json").write_bytes(
                    self.expected_candidate_result_bytes,
                )
                (self.candidate_root / "report.md").write_bytes(
                    self.expected_candidate_report_bytes,
                )
                original_result = (self.candidate_root / "result.json").read_bytes()
                original_report = (self.candidate_root / "report.md").read_bytes()
                prepared = self.prepared_candidate()

                with self.lock(prepared) as capability:
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                self.assertEqual(
                    (self.candidate_root / "result.json").read_bytes(),
                    original_result,
                )
                self.assertEqual(
                    (self.candidate_root / "report.md").read_bytes(),
                    original_report,
                )
                self.assertFalse(
                    (self.ignored_root / "publication-journal.json").exists(),
                )
                self.assertFalse(
                    (self.ignored_root / "candidate-receipt.json").exists(),
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_pair_stage_link_at_first_child_create_never_writes_link_target(
        self,
    ) -> None:
        """A replaced pair stage must not redirect either pair child."""
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            redirected = self.temp_root / "redirected-pair-stage"
            redirected.mkdir()
            replaced = False
            try:
                prepared = self.prepared_candidate()
                original_create = runner._create_new_phase_c1_file

                def replace_pair_stage_before_first_child(
                    path: Path,
                    payload: bytes,
                ) -> object:
                    nonlocal replaced
                    candidate_path = Path(path)
                    if (
                        not replaced
                        and candidate_path.parent == paths.candidate_stage_path
                    ):
                        replaced = True
                        shutil.rmtree(paths.candidate_stage_path)
                        self.create_test_reparse(
                            paths.candidate_stage_path,
                            redirected,
                        )
                    return original_create(path, payload)

                with mock.patch.object(
                    runner,
                    "_create_new_phase_c1_file",
                    side_effect=replace_pair_stage_before_first_child,
                ), self.lock(prepared) as capability:
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                self.assertTrue(replaced)
                self.assertFalse((redirected / "result.json").exists())
                self.assertFalse((redirected / "report.md").exists())
            finally:
                if os.path.lexists(paths.candidate_stage_path):
                    metadata = paths.candidate_stage_path.lstat()
                    if stat.S_ISLNK(metadata.st_mode):
                        paths.candidate_stage_path.unlink()
                    else:
                        os.rmdir(paths.candidate_stage_path)
                self.stop_runner_context(paths_patch, head_patch)

    def test_cleanup_receipt_changed_at_delete_start_is_retained(
        self,
    ) -> None:
        """Cleanup must re-bind each receipt at the delete boundary."""
        receipt_names = (
            "candidate-receipt.json",
            "candidate-validation.json",
            "candidate-review.json",
        )
        for receipt_name in receipt_names:
            with self.subTest(receipt_name=receipt_name), self.isolated_mutation_root():
                _paths, paths_patch, head_patch = self.runner_context()
                changed = b"changed-at-cleanup-boundary\n"
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    prepared = self.prepare_acceptance()
                    target = self.ignored_root / receipt_name
                    original_delete = (
                        runner._delete_verified_phase_c1_cleanup_target
                    )
                    mutated = False

                    def change_receipt_at_delete_start(
                        paths: object,
                        deleting: Path,
                        **kwargs: object,
                    ) -> object:
                        nonlocal mutated
                        if Path(deleting) == target:
                            mutated = True
                            target.write_bytes(changed)
                        return original_delete(paths, deleting, **kwargs)

                    with mock.patch.object(
                        runner,
                        "_delete_verified_phase_c1_cleanup_target",
                        side_effect=change_receipt_at_delete_start,
                    ), self.lock(prepared) as capability:
                        with self.assertRaises(runner.RunnerError):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    self.assertTrue(mutated)
                    self.assertTrue(target.is_file())
                    self.assertEqual(target.read_bytes(), changed)
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_committed_file_swap_during_parent_flush_preserves_a_valid_state(
        self,
    ) -> None:
        """Parent flush cannot validate a substituted committed journal or receipt."""
        for artifact in ("journal", "receipt"):
            with self.subTest(artifact=artifact), self.isolated_mutation_root():
                paths, paths_patch, head_patch = self.runner_context()
                moved = self.ignored_root / f"{artifact}-moved"
                replacement = f"substituted {artifact}\n".encode("ascii")
                attempted = False
                blocked = False
                swapped = False
                prior_journal: bytes | None = None
                try:
                    prepared = self.prepared_candidate()
                    state = runner._state_for(prepared)
                    expected_receipt = state.candidate_receipt_bytes
                    original_fsync = runner._fsync_phase_c1_directory

                    def swap_committed_file_at_parent_flush(
                        path: Path,
                        *args: object,
                        **kwargs: object,
                    ) -> object:
                        nonlocal attempted, blocked, swapped, prior_journal
                        candidate_path = Path(path)
                        journal = paths.publication_journal_path
                        receipt = paths.candidate_receipt_path
                        if candidate_path == paths.ignored_root and journal.is_file():
                            journal_payload = phase_c1.load_json_strict(
                                journal.read_bytes(), source="flush_journal",
                            )
                            self.assertIsInstance(journal_payload, dict)
                            status = journal_payload["status"]
                            if status == "staging_candidate":
                                prior_journal = journal.read_bytes()
                            target = (
                                journal
                                if artifact == "journal" and status == "candidate_ready"
                                else receipt
                                if artifact == "receipt" and receipt.is_file()
                                else None
                            )
                            if target is not None and not attempted:
                                attempted = True
                                try:
                                    os.replace(target, moved)
                                except OSError:
                                    blocked = True
                                else:
                                    swapped = True
                                    target.write_bytes(replacement)
                        return original_fsync(path, *args, **kwargs)

                    with mock.patch.object(
                        runner,
                        "_fsync_phase_c1_directory",
                        side_effect=swap_committed_file_at_parent_flush,
                    ), self.lock(prepared) as capability:
                        with self.assertRaises(runner.RunnerError):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    self.assertTrue(attempted)
                    if blocked:
                        self.assertFalse(swapped)
                        self.assertTrue(paths.candidate_root.is_dir())
                        self.assertEqual(
                            paths.candidate_receipt_path.read_bytes(),
                            expected_receipt,
                        )
                        journal_payload = phase_c1.load_json_strict(
                            paths.publication_journal_path.read_bytes(),
                            source="blocked_journal",
                        )
                        self.assertEqual(journal_payload["status"], "candidate_ready")
                    else:
                        self.assertTrue(swapped)
                        self.assertFalse(blocked)
                        self.assertTrue(paths.candidate_root.is_dir())
                        if artifact == "journal":
                            self.assertIsNotNone(prior_journal)
                            self.assertNotEqual(
                                paths.publication_journal_path.read_bytes(),
                                replacement,
                            )
                        else:
                            receipt_path = paths.candidate_receipt_path
                            self.assertNotEqual(
                                receipt_path.read_bytes(),
                                replacement,
                            )
                            self.assertEqual(
                                paths.publication_journal_path.read_bytes(),
                                prior_journal,
                            )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_all_19_runner_paths_reject_topology_mutation_before_external_access(
        self,
    ) -> None:
        expected_fields = (
            "project_root",
            "protocol_path",
            "search_ledger_path",
            "source_ledger_path",
            "source_review_path",
            "ignored_root",
            "candidate_root",
            "candidate_receipt_path",
            "candidate_receipt_stage_path",
            "candidate_validation_path",
            "candidate_validation_stage_path",
            "candidate_review_path",
            "candidate_review_stage_path",
            "publication_lock_path",
            "publication_journal_path",
            "publication_journal_stage_path",
            "candidate_stage_path",
            "canonical_stage_path",
            "canonical_root",
        )
        self.assertEqual(
            tuple(field.name for field in fields(runner.PhaseC1RunnerPaths)),
            expected_fields,
        )
        for field_name in expected_fields:
            with (
                self.subTest(field=field_name),
                self.isolated_mutation_root(),
            ):
                valid_paths = self.build_explicit_temp_runner_paths(
                    self.temp_root,
                )
                if field_name == "project_root":
                    wrong_path = self.temp_root / "alternate-project"
                    wrong_path.mkdir()
                else:
                    wrong_path = (
                        self.temp_root
                        / "wrong-topology"
                        / field_name
                    )
                mutated_paths = replace(
                    valid_paths,
                    **{field_name: wrong_path},
                )
                external_accesses: list[str] = []

                def observe_repository_head() -> str:
                    external_accesses.append("repository_head")
                    return "a" * 40

                def observe_validator_state(
                    expected_head: str,
                ) -> dict[str, object]:
                    external_accesses.append("validator_state")
                    return {
                        "repository_head": expected_head,
                        "validator_blob_id": None,
                        "is_clean": False,
                    }

                with mock.patch.object(
                    runner,
                    "PRODUCTION_PATHS",
                    mutated_paths,
                ), mock.patch.object(
                    runner,
                    "_current_repository_head",
                    side_effect=observe_repository_head,
                ), mock.patch.object(
                    runner,
                    "_resolve_phase_c1_validator_state",
                    side_effect=observe_validator_state,
                ):
                    with self.assertRaises(runner.RunnerError):
                        runner.prepare_phase_c1_candidate(
                            expected_head="a" * 40,
                        )

                self.assertEqual(
                    external_accesses,
                    [],
                    msg=(
                        f"{field_name} topology mutation reached external "
                        f"access: {external_accesses}"
                    ),
                )

    @unittest.skipUnless(os.name == "posix", "POSIX authority regression")
    def test_posix_verified_stage_delete_retains_replacement_at_mutation_seam(
        self,
    ) -> None:
        for artifact in ("pair", "journal"):
            with (
                self.subTest(artifact=artifact),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                moved = self.temp_root / f"validated-{artifact}-stage"
                changed_result = b"replacement-result\n"
                changed_report = b"replacement-report\n"
                changed_journal = b"replacement-journal\n"
                mutated = False
                publication_error: runner.RunnerError | None = None
                try:
                    if artifact == "pair":
                        prepared = self.prepared_candidate()
                        target = paths.candidate_stage_path
                        self.write_pair_directory(target)
                    else:
                        self.create_candidate()
                        prepared = self.prepared_candidate()
                        predecessor = self.write_exact_journal(
                            status="staging_candidate",
                        )
                        transition = self.write_exact_journal(
                            status="candidate_ready",
                            sequence=1,
                            previous=predecessor,
                        )
                        paths.publication_journal_path.write_bytes(
                            predecessor,
                        )
                        target = paths.publication_journal_stage_path
                        target.write_bytes(transition)

                    original_delete = runner._delete_verified_stage

                    def substitute_validated_stage(
                        path: Path,
                        **kwargs: object,
                    ) -> None:
                        nonlocal mutated
                        deleting = Path(path)
                        if deleting == target and not mutated:
                            mutated = True
                            os.replace(deleting, moved)
                            if artifact == "pair":
                                deleting.mkdir()
                                (deleting / "result.json").write_bytes(
                                    changed_result,
                                )
                                (deleting / "report.md").write_bytes(
                                    changed_report,
                                )
                            else:
                                deleting.write_bytes(changed_journal)
                        original_delete(deleting, **kwargs)

                    with mock.patch.object(
                        runner,
                        "_delete_verified_stage",
                        side_effect=substitute_validated_stage,
                    ), self.lock(prepared) as capability:
                        try:
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )
                        except runner.RunnerError as exc:
                            publication_error = exc

                    self.assertTrue(
                        mutated,
                        msg=f"{artifact} deletion seam was not exercised",
                    )
                    if artifact == "pair":
                        self.assertTrue(
                            target.is_dir(),
                            msg=(
                                "validated pair-stage replacement was "
                                "deleted"
                            ),
                        )
                        self.assertEqual(
                            (target / "result.json").read_bytes(),
                            changed_result,
                        )
                        self.assertEqual(
                            (target / "report.md").read_bytes(),
                            changed_report,
                        )
                    else:
                        self.assertTrue(
                            target.is_file(),
                            msg=(
                                "validated journal-stage replacement was "
                                "deleted"
                            ),
                        )
                        self.assertEqual(
                            target.read_bytes(),
                            changed_journal,
                        )
                    self.assertIsNotNone(
                        publication_error,
                        msg=(
                            f"{artifact} replacement was accepted after "
                            "validated-stage substitution"
                        ),
                    )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    @unittest.skipUnless(os.name == "posix", "POSIX authority regression")
    def test_posix_pair_stage_rebind_before_authority_cannot_redirect_first_child(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            moved = self.temp_root / "created-stage-before-rebind"
            attempted = False
            swapped = False
            publication_error: runner.RunnerError | None = None
            try:
                prepared = self.prepared_candidate()
                original_verify = (
                    runner._verify_held_phase_c1_directory_authority
                )

                def substitute_stage_after_creation(
                    authority: object,
                ) -> None:
                    nonlocal attempted, swapped
                    original_verify(authority)
                    stage = paths.candidate_stage_path
                    if (
                        not attempted
                        and getattr(authority, "path", None)
                        == paths.ignored_root
                        and stage.is_dir()
                        and not any(stage.iterdir())
                        and not paths.candidate_root.exists()
                    ):
                        attempted = True
                        os.replace(stage, moved)
                        stage.mkdir()
                        swapped = True

                with mock.patch.object(
                    runner,
                    "_verify_held_phase_c1_directory_authority",
                    side_effect=substitute_stage_after_creation,
                ), self.lock(prepared) as capability:
                    try:
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )
                    except runner.RunnerError as exc:
                        publication_error = exc

                self.assertTrue(
                    attempted,
                    msg="stage substitution seam was not exercised",
                )
                self.assertTrue(swapped)
                self.assertIsNotNone(
                    publication_error,
                    msg=(
                        "replacement stage received first-child writes "
                        "before authority acquisition"
                    ),
                )
                self.assertFalse(paths.candidate_root.exists())
                self.assertTrue(paths.candidate_stage_path.is_dir())
                self.assertFalse(
                    (paths.candidate_stage_path / "result.json").exists(),
                    msg="result.json was redirected into the replacement",
                )
                self.assertFalse(
                    (paths.candidate_stage_path / "report.md").exists(),
                    msg="report.md was redirected into the replacement",
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_valid_initial_sequence_zero_journal_stage_recovers_to_candidate_ready(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            publication_error: runner.RunnerError | None = None
            receipt: runner.PhaseC1PublicationReceipt | None = None
            try:
                prepared = self.prepared_candidate()
                state = runner._state_for(prepared)
                initial_stage = runner._journal_payload(
                    state,
                    status="staging_candidate",
                    sequence=0,
                    previous=None,
                )
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                paths.publication_journal_stage_path.write_bytes(
                    initial_stage,
                )
                self.assertFalse(paths.publication_journal_path.exists())

                with self.lock(prepared) as capability:
                    try:
                        receipt = runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )
                    except runner.RunnerError as exc:
                        publication_error = exc

                self.assertIsNone(
                    publication_error,
                    msg=(
                        "valid initial sequence-0 journal stage wedged "
                        "recovery: "
                        f"{getattr(publication_error, 'code', None)}"
                    ),
                )
                self.assertIsNotNone(receipt)
                assert receipt is not None
                self.assertEqual(receipt.status, "candidate_ready")
                self.assertFalse(
                    paths.publication_journal_stage_path.exists(),
                )
                final_journal = phase_c1.load_json_strict(
                    paths.publication_journal_path.read_bytes(),
                    source="recovered_initial_journal",
                )
                self.assertIsInstance(final_journal, dict)
                self.assertEqual(
                    final_journal["status"],
                    "candidate_ready",
                )
                self.assert_pair_directory(paths.candidate_root)
                self.assertEqual(
                    paths.candidate_receipt_path.read_bytes(),
                    state.candidate_receipt_bytes,
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_invalid_initial_sequence_zero_journal_stage_is_retained_fail_closed(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            try:
                prepared = self.prepared_candidate()
                state = runner._state_for(prepared)
                valid_stage = runner._journal_payload(
                    state,
                    status="staging_candidate",
                    sequence=0,
                    previous=None,
                )
                invalid_payload = phase_c1.load_json_strict(
                    valid_stage,
                    source="valid_initial_journal_stage",
                )
                self.assertIsInstance(invalid_payload, dict)
                invalid_payload["journal_content_sha256"] = "0" * 64
                invalid_stage = phase_c1.canonical_json_bytes(
                    invalid_payload,
                )
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                paths.publication_journal_stage_path.write_bytes(
                    invalid_stage,
                )

                with self.lock(prepared) as capability:
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                self.assertEqual(
                    paths.publication_journal_stage_path.read_bytes(),
                    invalid_stage,
                )
                self.assertFalse(paths.publication_journal_path.exists())
                self.assertFalse(paths.candidate_root.exists())
                self.assertFalse(paths.candidate_receipt_path.exists())
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_every_publication_file_create_uses_its_held_parent_authority(
        self,
    ) -> None:
        records: list[tuple[str, str, str | None]] = []
        original_create = runner._create_new_phase_c1_file
        scenario = ""

        def record_create(path: Path, payload: bytes) -> object:
            authority = getattr(
                runner._PHASE_C1_FILE_CREATE_CONTEXT,
                "parent_authority",
                None,
            )
            target = Path(path)
            records.append(
                (
                    scenario,
                    target.relative_to(self.temp_root).as_posix(),
                    (
                        None
                        if authority is None
                        else Path(authority.path)
                        .relative_to(self.temp_root)
                        .as_posix()
                    ),
                )
            )
            return original_create(target, payload)

        for lane in ("first_and_acceptance", "candidate_stage_recovery"):
            with self.subTest(lane=lane), self.isolated_mutation_root():
                paths, paths_patch, head_patch = self.runner_context()
                scenario = lane
                try:
                    with mock.patch.object(
                        runner,
                        "_create_new_phase_c1_file",
                        side_effect=record_create,
                    ):
                        if lane == "candidate_stage_recovery":
                            self.write_pair_directory(
                                paths.candidate_stage_path,
                            )
                            prepared = self.prepared_candidate()
                            with self.lock(prepared) as capability:
                                receipt = runner.finalize_phase_c1_publication(
                                    prepared,
                                    capability=capability,
                                )
                            self.assertEqual(
                                receipt.status,
                                "candidate_ready",
                            )
                        else:
                            self.create_candidate()
                            self.seed_valid_candidate_validation_and_review_receipts()
                            prepared = self.prepare_acceptance()
                            with self.lock(prepared) as capability:
                                receipt = runner.finalize_phase_c1_publication(
                                    prepared,
                                    capability=capability,
                                )
                            self.assertEqual(receipt.status, "accepted")
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

        observed_roles = {
            path.rsplit("/", 1)[-1]
            if not path.endswith((
                "candidate.stage/result.json",
                "candidate.stage/report.md",
                "canonical.stage/result.json",
                "canonical.stage/report.md",
            ))
            else "/".join(path.split("/")[-2:])
            for _lane, path, _authority in records
        }
        self.assertTrue(
            {
                "publication.lock",
                "publication-journal.stage",
                "candidate-receipt.stage",
                "candidate.stage/result.json",
                "candidate.stage/report.md",
                "canonical.stage/result.json",
                "canonical.stage/report.md",
            }.issubset(observed_roles),
            msg=f"incomplete publication-create coverage: {records}",
        )
        unbound = tuple(
            (lane, path, authority)
            for lane, path, authority in records
            if authority != Path(path).parent.as_posix()
        )
        self.assertEqual(
            unbound,
            (),
            msg=(
                "fixed publication creates reached a raw pathname "
                f"fallback: {unbound}"
            ),
        )

    def test_publication_create_and_lock_open_call_sites_are_authority_bound(
        self,
    ) -> None:
        source = Path(runner.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        def call_name(call: ast.Call) -> str | None:
            if isinstance(call.func, ast.Name):
                return call.func.id
            if isinstance(call.func, ast.Attribute):
                return call.func.attr
            return None

        def has_bound_creation_context(call: ast.Call) -> bool:
            if any(
                keyword.arg == "parent_authority"
                for keyword in call.keywords
            ):
                return True
            current: ast.AST | None = call
            while current in parents:
                current = parents[current]
                if not isinstance(current, ast.With):
                    continue
                for item in current.items:
                    expression = item.context_expr
                    if (
                        isinstance(expression, ast.Call)
                        and call_name(expression)
                        == "_phase_c1_bound_child_creation"
                    ):
                        return True
            return False

        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if (
                call_name(node) == "_create_new_phase_c1_file"
                and not has_bound_creation_context(node)
            ):
                violations.append(
                    f"unbound_create@{node.lineno}"
                )
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "open"
                and len(node.args) >= 2
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "lock_path"
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "r+b"
            ):
                violations.append(
                    f"raw_existing_lock_open@{node.lineno}"
                )
        self.assertEqual(
            violations,
            [],
            msg=(
                "publication create/open call sites retain raw pathname "
                f"fallbacks: {violations}"
            ),
        )

    @unittest.skipUnless(os.name == "posix", "POSIX lock authority regression")
    def test_posix_existing_lock_swap_cannot_lock_decoy_inode(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            attempted = False
            opened_by: str | None = None
            opened_flags: int | None = None
            opened_dir_fd: int | None = None
            lock_error: runner.RunnerError | None = None
            capability_yielded = False
            try:
                prepared = self.prepared_candidate()
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                lock_bytes = b"phase-c1-publication-lock\n"
                paths.publication_lock_path.write_bytes(lock_bytes)
                moved = self.temp_root / "original-publication-lock"
                decoy = self.temp_root / "decoy-publication-lock"
                decoy.write_bytes(lock_bytes)
                decoy_identity = (
                    decoy.lstat().st_dev,
                    decoy.lstat().st_ino,
                )
                original_builtin_open = open
                original_os_open = os.open

                def substitute_lock() -> None:
                    nonlocal attempted
                    if attempted:
                        return
                    attempted = True
                    os.replace(paths.publication_lock_path, moved)
                    os.replace(decoy, paths.publication_lock_path)
                    current = paths.publication_lock_path.lstat()
                    self.assertEqual(
                        (current.st_dev, current.st_ino),
                        decoy_identity,
                    )

                def observed_builtin_open(
                    file: object,
                    mode: str = "r",
                    *args: object,
                    **kwargs: object,
                ) -> object:
                    nonlocal opened_by
                    if (
                        mode == "r+b"
                        and isinstance(file, (str, bytes, os.PathLike))
                        and Path(file) == paths.publication_lock_path
                    ):
                        opened_by = "builtins.open"
                        substitute_lock()
                    return original_builtin_open(
                        file,
                        mode,
                        *args,
                        **kwargs,
                    )

                def observed_os_open(
                    file: object,
                    flags: int,
                    mode: int = 0o777,
                    *,
                    dir_fd: int | None = None,
                ) -> int:
                    nonlocal opened_by, opened_flags, opened_dir_fd
                    text = (
                        os.fsdecode(file)
                        if isinstance(file, (str, bytes, os.PathLike))
                        else ""
                    )
                    if (
                        Path(text) == paths.publication_lock_path
                        or (
                            text == paths.publication_lock_path.name
                            and dir_fd is not None
                        )
                    ):
                        opened_by = "os.open"
                        opened_flags = flags
                        opened_dir_fd = dir_fd
                        substitute_lock()
                    return original_os_open(
                        file,
                        flags,
                        mode,
                        dir_fd=dir_fd,
                    )

                with mock.patch(
                    "builtins.open",
                    side_effect=observed_builtin_open,
                ), mock.patch.object(
                    os,
                    "open",
                    side_effect=observed_os_open,
                ):
                    try:
                        with self.lock(prepared):
                            capability_yielded = True
                    except runner.RunnerError as exc:
                        lock_error = exc

                violations: list[str] = []
                if not attempted:
                    violations.append("swap seam was not exercised")
                if lock_error is None:
                    violations.append("swapped decoy lock was accepted")
                if capability_yielded:
                    violations.append("capability was issued for decoy lock")
                if opened_by != "os.open":
                    violations.append(
                        f"existing lock used {opened_by!r}"
                    )
                if opened_dir_fd is None:
                    violations.append("existing lock open lacked dir_fd")
                nofollow = getattr(os, "O_NOFOLLOW", 0)
                if (
                    not nofollow
                    or opened_flags is None
                    or not opened_flags & nofollow
                ):
                    violations.append(
                        "existing lock open lacked O_NOFOLLOW"
                    )
                self.assertEqual(
                    violations,
                    [],
                    msg=(
                        "existing publication.lock was not held-parent "
                        f"bound: {violations}"
                    ),
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_candidate_cleanup_restarts_after_each_child_unlink(
        self,
    ) -> None:
        for crash_child in ("result.json", "report.md"):
            with (
                self.subTest(crash_child=crash_child),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                crashed = False
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    prepared = self.prepare_acceptance()
                    original_delete = (
                        runner._delete_held_phase_c1_regular_file
                    )

                    def crash_after_child_unlink(
                        authority: object,
                        *,
                        parent_authority: object,
                    ) -> None:
                        nonlocal crashed
                        target = Path(authority.path)
                        original_delete(
                            authority,
                            parent_authority=parent_authority,
                        )
                        if (
                            not crashed
                            and target.parent == paths.candidate_root
                            and target.name == crash_child
                        ):
                            crashed = True
                            raise runner.RunnerError(
                                "synthetic_child_unlink_crash"
                            )

                    with mock.patch.object(
                        runner,
                        "_delete_held_phase_c1_regular_file",
                        side_effect=crash_after_child_unlink,
                    ), self.lock(prepared) as capability:
                        with self.assertRaisesRegex(
                            runner.RunnerError,
                            "synthetic_child_unlink_crash",
                        ):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    self.assertTrue(crashed)
                    expected_children = (
                        {"report.md"}
                        if crash_child == "result.json"
                        else set()
                    )
                    self.assertEqual(
                        {
                            child.name
                            for child in paths.candidate_root.iterdir()
                        },
                        expected_children,
                    )
                    journal = phase_c1.load_json_strict(
                        paths.publication_journal_path.read_bytes(),
                        source="accepted_cleanup_crash_journal",
                    )
                    self.assertEqual(journal["status"], "accepted")

                    restart_error: runner.RunnerError | None = None
                    receipt: runner.PhaseC1PublicationReceipt | None = None
                    try:
                        recovery = self.prepare_acceptance()
                        with self.lock(recovery) as capability:
                            receipt = runner.finalize_phase_c1_publication(
                                recovery,
                                capability=capability,
                            )
                    except runner.RunnerError as exc:
                        restart_error = exc
                    self.assertIsNone(
                        restart_error,
                        msg=(
                            "accepted candidate cleanup wedged after "
                            f"{crash_child} unlink: "
                            f"{getattr(restart_error, 'code', None)}"
                        ),
                    )
                    self.assertIsNotNone(receipt)
                    assert receipt is not None
                    self.assertEqual(receipt.status, "accepted")
                    self.assertFalse(paths.candidate_root.exists())
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_stage_cleanup_restarts_after_each_child_unlink(
        self,
    ) -> None:
        for crash_child in ("result.json", "report.md"):
            with (
                self.subTest(crash_child=crash_child),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                crashed = False
                try:
                    prepared = self.prepared_candidate()
                    state = runner._state_for(prepared)
                    paths.ignored_root.mkdir(parents=True, exist_ok=True)
                    paths.publication_journal_path.write_bytes(
                        runner._journal_payload(
                            state,
                            status="staging_candidate",
                            sequence=0,
                            previous=None,
                        )
                    )
                    self.write_pair_directory(
                        paths.candidate_stage_path,
                    )
                    original_delete = (
                        runner._delete_held_phase_c1_regular_file
                    )

                    def crash_after_child_unlink(
                        authority: object,
                        *,
                        parent_authority: object,
                    ) -> None:
                        nonlocal crashed
                        target = Path(authority.path)
                        original_delete(
                            authority,
                            parent_authority=parent_authority,
                        )
                        if (
                            not crashed
                            and target.parent
                            == paths.candidate_stage_path
                            and target.name == crash_child
                        ):
                            crashed = True
                            raise runner.RunnerError(
                                "synthetic_stage_child_unlink_crash"
                            )

                    with mock.patch.object(
                        runner,
                        "_delete_held_phase_c1_regular_file",
                        side_effect=crash_after_child_unlink,
                    ), self.lock(prepared) as capability:
                        with self.assertRaisesRegex(
                            runner.RunnerError,
                            "synthetic_stage_child_unlink_crash",
                        ):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    self.assertTrue(crashed)
                    expected_children = (
                        {"report.md"}
                        if crash_child == "result.json"
                        else set()
                    )
                    self.assertEqual(
                        {
                            child.name
                            for child in paths.candidate_stage_path.iterdir()
                        },
                        expected_children,
                    )
                    restart_error: runner.RunnerError | None = None
                    receipt: runner.PhaseC1PublicationReceipt | None = None
                    try:
                        recovery = self.prepared_candidate()
                        with self.lock(recovery) as capability:
                            receipt = runner.finalize_phase_c1_publication(
                                recovery,
                                capability=capability,
                            )
                    except runner.RunnerError as exc:
                        restart_error = exc
                    self.assertIsNone(
                        restart_error,
                        msg=(
                            "candidate-stage cleanup wedged after "
                            f"{crash_child} unlink: "
                            f"{getattr(restart_error, 'code', None)}"
                        ),
                    )
                    self.assertIsNotNone(receipt)
                    assert receipt is not None
                    self.assertEqual(receipt.status, "candidate_ready")
                    self.assertFalse(
                        paths.candidate_stage_path.exists(),
                    )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_accepted_candidate_cleanup_prefix_matrix_is_exact(
        self,
    ) -> None:
        rows = (
            ("complete", True),
            ("report_only", True),
            ("empty", True),
            ("absent", True),
            ("wrong_bytes", False),
            ("result_only", False),
            ("extra_child", False),
            ("invalid_journal", False),
        )
        for row, should_recover in rows:
            with (
                self.subTest(row=row),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                try:
                    self.create_candidate()
                    self.seed_valid_candidate_validation_and_review_receipts()
                    prepared = self.prepare_acceptance()
                    with mock.patch.object(
                        runner,
                        "_cleanup_accepted",
                        side_effect=runner.RunnerError(
                            "synthetic_pre_cleanup_crash"
                        ),
                    ), self.lock(prepared) as capability:
                        with self.assertRaisesRegex(
                            runner.RunnerError,
                            "synthetic_pre_cleanup_crash",
                        ):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    result_path = paths.candidate_root / "result.json"
                    report_path = paths.candidate_root / "report.md"
                    if row == "report_only":
                        result_path.unlink()
                    elif row == "empty":
                        result_path.unlink()
                        report_path.unlink()
                    elif row == "absent":
                        result_path.unlink()
                        report_path.unlink()
                        paths.candidate_root.rmdir()
                    elif row == "wrong_bytes":
                        report_path.write_bytes(b"wrong-report\n")
                    elif row == "result_only":
                        report_path.unlink()
                    elif row == "extra_child":
                        (paths.candidate_root / "extra").write_bytes(
                            b"extra\n"
                        )
                    elif row == "invalid_journal":
                        journal = phase_c1.load_json_strict(
                            paths.publication_journal_path.read_bytes(),
                            source="accepted_journal",
                        )
                        journal["journal_content_sha256"] = "0" * 64
                        paths.publication_journal_path.write_bytes(
                            phase_c1.canonical_json_bytes(journal)
                        )

                    def snapshot_candidate() -> (
                        tuple[tuple[str, bytes], ...] | None
                    ):
                        if not paths.candidate_root.exists():
                            return None
                        return tuple(
                            sorted(
                                (
                                    child.name,
                                    child.read_bytes(),
                                )
                                for child in paths.candidate_root.iterdir()
                            )
                        )

                    candidate_before = snapshot_candidate()
                    journal_before = (
                        paths.publication_journal_path.read_bytes()
                    )
                    recovery_error: runner.RunnerError | None = None
                    receipt: runner.PhaseC1PublicationReceipt | None = None
                    try:
                        recovery = self.prepare_acceptance()
                        with self.lock(recovery) as capability:
                            receipt = runner.finalize_phase_c1_publication(
                                recovery,
                                capability=capability,
                            )
                    except runner.RunnerError as exc:
                        recovery_error = exc

                    if should_recover:
                        self.assertIsNone(
                            recovery_error,
                            msg=(
                                "valid accepted-cleanup prefix wedged: "
                                f"{row}: "
                                f"{getattr(recovery_error, 'code', None)}"
                            ),
                        )
                        self.assertIsNotNone(receipt)
                        self.assertFalse(
                            paths.candidate_root.exists(),
                        )
                    else:
                        self.assertIsNotNone(
                            recovery_error,
                            msg=(
                                "invalid accepted-cleanup prefix was "
                                f"accepted: {row}"
                            ),
                        )
                        self.assertEqual(
                            snapshot_candidate(),
                            candidate_before,
                        )
                        self.assertEqual(
                            paths.publication_journal_path.read_bytes(),
                            journal_before,
                        )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_candidate_stage_cleanup_prefix_matrix_is_exact(
        self,
    ) -> None:
        rows = (
            ("complete", True),
            ("report_only", True),
            ("empty", True),
            ("absent", True),
            ("wrong_bytes", False),
            ("result_only", True),
            ("extra_child", False),
            ("invalid_journal", False),
        )
        for row, should_recover in rows:
            with (
                self.subTest(row=row),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                try:
                    prepared = self.prepared_candidate()
                    state = runner._state_for(prepared)
                    paths.ignored_root.mkdir(parents=True, exist_ok=True)
                    journal_bytes = runner._journal_payload(
                        state,
                        status="staging_candidate",
                        sequence=0,
                        previous=None,
                    )
                    paths.publication_journal_path.write_bytes(
                        journal_bytes,
                    )
                    if row != "absent":
                        paths.candidate_stage_path.mkdir()
                        if row in {
                            "complete",
                            "wrong_bytes",
                            "extra_child",
                            "invalid_journal",
                        }:
                            (
                                paths.candidate_stage_path / "result.json"
                            ).write_bytes(state.result_bytes)
                            (
                                paths.candidate_stage_path / "report.md"
                            ).write_bytes(state.report_bytes)
                        elif row == "report_only":
                            (
                                paths.candidate_stage_path / "report.md"
                            ).write_bytes(state.report_bytes)
                        elif row == "result_only":
                            (
                                paths.candidate_stage_path / "result.json"
                            ).write_bytes(state.result_bytes)
                    if row == "wrong_bytes":
                        (
                            paths.candidate_stage_path / "report.md"
                        ).write_bytes(b"wrong-report\n")
                    elif row == "extra_child":
                        (
                            paths.candidate_stage_path / "extra"
                        ).write_bytes(b"extra\n")
                    elif row == "invalid_journal":
                        journal = phase_c1.load_json_strict(
                            journal_bytes,
                            source="staging_candidate_journal",
                        )
                        journal["journal_content_sha256"] = "0" * 64
                        paths.publication_journal_path.write_bytes(
                            phase_c1.canonical_json_bytes(journal)
                        )

                    def snapshot_stage() -> (
                        tuple[tuple[str, bytes], ...] | None
                    ):
                        if not paths.candidate_stage_path.exists():
                            return None
                        return tuple(
                            sorted(
                                (
                                    child.name,
                                    child.read_bytes(),
                                )
                                for child
                                in paths.candidate_stage_path.iterdir()
                            )
                        )

                    stage_before = snapshot_stage()
                    journal_before = (
                        paths.publication_journal_path.read_bytes()
                    )
                    publication_error: runner.RunnerError | None = None
                    receipt: runner.PhaseC1PublicationReceipt | None = None
                    try:
                        with self.lock(prepared) as capability:
                            receipt = runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )
                    except runner.RunnerError as exc:
                        publication_error = exc

                    if should_recover:
                        self.assertIsNone(
                            publication_error,
                            msg=(
                                "valid candidate-stage cleanup prefix "
                                f"wedged: {row}: "
                                f"{getattr(publication_error, 'code', None)}"
                            ),
                        )
                        self.assertIsNotNone(receipt)
                        self.assertFalse(
                            paths.candidate_stage_path.exists(),
                        )
                    else:
                        self.assertIsNotNone(
                            publication_error,
                            msg=(
                                "invalid candidate-stage cleanup prefix "
                                f"was accepted: {row}"
                            ),
                        )
                        self.assertEqual(
                            snapshot_stage(),
                            stage_before,
                        )
                        self.assertEqual(
                            paths.publication_journal_path.read_bytes(),
                            journal_before,
                        )
                        self.assertFalse(paths.candidate_root.exists())
                        self.assertFalse(
                            paths.candidate_receipt_path.exists(),
                        )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_receipt_cleanup_has_only_single_file_held_delete_boundaries(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            events: list[tuple[str, Path]] = []
            try:
                self.create_candidate()
                self.seed_valid_candidate_validation_and_review_receipts()
                prepared = self.prepare_acceptance()
                original_delete = (
                    runner._delete_held_phase_c1_regular_file
                )

                def record_delete(
                    authority: object,
                    *,
                    parent_authority: object,
                ) -> None:
                    target = Path(authority.path)
                    if target.parent == paths.ignored_root:
                        events.append(
                            (target.name, Path(parent_authority.path))
                        )
                    original_delete(
                        authority,
                        parent_authority=parent_authority,
                    )

                with mock.patch.object(
                    runner,
                    "_delete_held_phase_c1_regular_file",
                    side_effect=record_delete,
                ), self.lock(prepared) as capability:
                    receipt = runner.finalize_phase_c1_publication(
                        prepared,
                        capability=capability,
                    )
                self.assertEqual(receipt.status, "accepted")
                self.assertEqual(
                    events,
                    [
                        (
                            "candidate-receipt.json",
                            paths.ignored_root,
                        ),
                        (
                            "candidate-validation.json",
                            paths.ignored_root,
                        ),
                        (
                            "candidate-review.json",
                            paths.ignored_root,
                        ),
                    ],
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_unjournaled_complete_candidate_stage_commits_before_cleanup(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            interrupted = False
            committed_journal: bytes | None = None
            try:
                prepared = self.prepared_candidate()
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                self.write_pair_directory(paths.candidate_stage_path)
                original_advance = runner._advance_journal

                def interrupt_after_initial_commit(
                    state: object,
                    *,
                    status: str,
                    current: bytes | None,
                    root_authority: object,
                ) -> bytes:
                    nonlocal interrupted, committed_journal
                    payload = original_advance(
                        state,
                        status=status,
                        current=current,
                        root_authority=root_authority,
                    )
                    if (
                        not interrupted
                        and status == "staging_candidate"
                        and current is None
                    ):
                        interrupted = True
                        committed_journal = payload
                        raise runner.RunnerError(
                            "synthetic_post_journal_commit_crash"
                        )
                    return payload

                with mock.patch.object(
                    runner,
                    "_advance_journal",
                    side_effect=interrupt_after_initial_commit,
                ), self.lock(prepared) as capability:
                    with self.assertRaisesRegex(
                        runner.RunnerError,
                        "synthetic_post_journal_commit_crash",
                    ):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                self.assertTrue(interrupted)
                self.assertIsNotNone(committed_journal)
                self.assertTrue(paths.publication_journal_path.is_file())
                self.assertEqual(
                    paths.publication_journal_path.read_bytes(),
                    committed_journal,
                )
                committed = phase_c1.load_json_strict(
                    paths.publication_journal_path.read_bytes(),
                    source="unjournaled_stage_initial_commit",
                )
                self.assertIsInstance(committed, dict)
                self.assertEqual(committed["status"], "staging_candidate")
                self.assertEqual(committed["sequence"], 0)
                self.assertEqual(
                    committed["previous_journal_sha256"],
                    "0" * 64,
                )
                stage_snapshot = (
                    None
                    if not paths.candidate_stage_path.is_dir()
                    else tuple(
                        sorted(
                            (
                                child.name,
                                child.read_bytes(),
                            )
                            for child in paths.candidate_stage_path.iterdir()
                        )
                    )
                )
                self.assertEqual(
                    stage_snapshot,
                    (
                        ("report.md", self.expected_candidate_report_bytes),
                        (
                            "result.json",
                            self.expected_candidate_result_bytes,
                        ),
                    ),
                    msg=(
                        "the durable staging_candidate commit occurred "
                        "after cleanup had already started"
                    ),
                )

                recovery = self.prepared_candidate()
                with self.lock(recovery) as capability:
                    receipt = runner.finalize_phase_c1_publication(
                        recovery,
                        capability=capability,
                    )
                self.assertEqual(receipt.status, "candidate_ready")
                self.assertFalse(paths.candidate_stage_path.exists())
                self.assert_pair_directory(paths.candidate_root)
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_unjournaled_candidate_stage_unlink_crashes_retry_from_journal(
        self,
    ) -> None:
        for crash_child in ("result.json", "report.md"):
            with (
                self.subTest(crash_child=crash_child),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                crashed = False
                try:
                    prepared = self.prepared_candidate()
                    paths.ignored_root.mkdir(parents=True, exist_ok=True)
                    self.write_pair_directory(paths.candidate_stage_path)
                    original_delete = (
                        runner._delete_held_phase_c1_regular_file
                    )

                    def crash_after_stage_child_unlink(
                        authority: object,
                        *,
                        parent_authority: object,
                    ) -> None:
                        nonlocal crashed
                        target = Path(authority.path)
                        original_delete(
                            authority,
                            parent_authority=parent_authority,
                        )
                        if (
                            not crashed
                            and target.parent
                            == paths.candidate_stage_path
                            and target.name == crash_child
                        ):
                            crashed = True
                            raise runner.RunnerError(
                                "synthetic_unjournaled_stage_unlink_crash"
                            )

                    with mock.patch.object(
                        runner,
                        "_delete_held_phase_c1_regular_file",
                        side_effect=crash_after_stage_child_unlink,
                    ), self.lock(prepared) as capability:
                        with self.assertRaisesRegex(
                            runner.RunnerError,
                            "synthetic_unjournaled_stage_unlink_crash",
                        ):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    self.assertTrue(crashed)
                    self.assertTrue(paths.candidate_stage_path.is_dir())
                    expected_children = (
                        {"report.md"}
                        if crash_child == "result.json"
                        else set()
                    )
                    self.assertEqual(
                        {
                            child.name
                            for child
                            in paths.candidate_stage_path.iterdir()
                        },
                        expected_children,
                    )
                    self.assertTrue(
                        paths.publication_journal_path.is_file(),
                        msg=(
                            "candidate-stage child unlink occurred before "
                            "a durable staging_candidate journal"
                        ),
                    )
                    journal_bytes = (
                        paths.publication_journal_path.read_bytes()
                    )
                    journal = phase_c1.load_json_strict(
                        journal_bytes,
                        source="unjournaled_stage_unlink_crash",
                    )
                    self.assertIsInstance(journal, dict)
                    self.assertEqual(journal["status"], "staging_candidate")
                    self.assertEqual(journal["sequence"], 0)
                    self.assertEqual(
                        journal["previous_journal_sha256"],
                        "0" * 64,
                    )

                    recovery = self.prepared_candidate()
                    with self.lock(recovery) as capability:
                        receipt = runner.finalize_phase_c1_publication(
                            recovery,
                            capability=capability,
                        )
                    self.assertEqual(receipt.status, "candidate_ready")
                    self.assertFalse(paths.candidate_stage_path.exists())
                    self.assert_pair_directory(paths.candidate_root)
                    final_journal = phase_c1.load_json_strict(
                        paths.publication_journal_path.read_bytes(),
                        source="unjournaled_stage_unlink_recovery",
                    )
                    self.assertIsInstance(final_journal, dict)
                    self.assertEqual(
                        final_journal["status"],
                        "candidate_ready",
                    )
                    self.assertEqual(final_journal["sequence"], 1)
                    self.assertEqual(
                        final_journal["previous_journal_sha256"],
                        self._sha256(journal_bytes),
                    )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_unjournaled_candidate_stage_journal_failures_precede_cleanup(
        self,
    ) -> None:
        rows = (
            ("journal_stage_create", "_create_new_phase_c1_file"),
            ("journal_commit", "_replace_phase_c1_file"),
        )
        for label, helper_name in rows:
            with (
                self.subTest(label=label),
                self.isolated_mutation_root(),
            ):
                paths, paths_patch, head_patch = self.runner_context()
                deleted_stage_children: list[str] = []
                try:
                    prepared = self.prepared_candidate()
                    paths.ignored_root.mkdir(parents=True, exist_ok=True)
                    self.write_pair_directory(paths.candidate_stage_path)
                    original_delete = (
                        runner._delete_held_phase_c1_regular_file
                    )
                    original_faulted_helper = getattr(
                        runner,
                        helper_name,
                    )

                    def record_stage_child_delete(
                        authority: object,
                        *,
                        parent_authority: object,
                    ) -> None:
                        target = Path(authority.path)
                        if target.parent == paths.candidate_stage_path:
                            deleted_stage_children.append(target.name)
                        original_delete(
                            authority,
                            parent_authority=parent_authority,
                        )

                    def fail_initial_journal_operation(
                        *args: object,
                        **kwargs: object,
                    ) -> object:
                        target = Path(args[0])
                        expected_target = (
                            paths.publication_journal_stage_path
                            if helper_name == "_create_new_phase_c1_file"
                            else paths.publication_journal_path
                        )
                        if target == expected_target:
                            raise OSError(label)
                        return original_faulted_helper(*args, **kwargs)

                    with self.lock(prepared) as capability, mock.patch.object(
                        runner,
                        "_delete_held_phase_c1_regular_file",
                        side_effect=record_stage_child_delete,
                    ), mock.patch.object(
                        runner,
                        helper_name,
                        side_effect=fail_initial_journal_operation,
                    ):
                        with self.assertRaises(runner.RunnerError):
                            runner.finalize_phase_c1_publication(
                                prepared,
                                capability=capability,
                            )

                    stage_snapshot = (
                        None
                        if not paths.candidate_stage_path.is_dir()
                        else tuple(
                            sorted(
                                (
                                    child.name,
                                    child.read_bytes(),
                                )
                                for child
                                in paths.candidate_stage_path.iterdir()
                            )
                        )
                    )
                    violations: list[str] = []
                    if deleted_stage_children:
                        violations.append(
                            "cleanup preceded journal failure: "
                            + ",".join(deleted_stage_children)
                        )
                    if stage_snapshot != (
                        (
                            "report.md",
                            self.expected_candidate_report_bytes,
                        ),
                        (
                            "result.json",
                            self.expected_candidate_result_bytes,
                        ),
                    ):
                        violations.append(
                            f"complete stage not retained: {stage_snapshot!r}"
                        )
                    if paths.publication_journal_path.exists():
                        violations.append("journal unexpectedly committed")
                    if paths.publication_journal_stage_path.exists():
                        violations.append("journal stage was not rolled back")
                    if paths.candidate_root.exists():
                        violations.append("candidate root unexpectedly exists")
                    if paths.candidate_receipt_path.exists():
                        violations.append(
                            "candidate receipt unexpectedly exists"
                        )
                    self.assertEqual(
                        violations,
                        [],
                        msg=(
                            "journal failure did not precede all candidate "
                            f"stage cleanup: {label}: {violations}"
                        ),
                    )
                finally:
                    self.stop_runner_context(paths_patch, head_patch)

    def test_journaled_result_only_candidate_stage_retries_to_candidate_ready(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            try:
                prepared = self.prepared_candidate()
                state = runner._state_for(prepared)
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                journal_bytes = runner._journal_payload(
                    state,
                    status="staging_candidate",
                    sequence=0,
                    previous=None,
                )
                paths.publication_journal_path.write_bytes(journal_bytes)
                paths.candidate_stage_path.mkdir()
                (
                    paths.candidate_stage_path / "result.json"
                ).write_bytes(state.result_bytes)

                publication_error: runner.RunnerError | None = None
                receipt: runner.PhaseC1PublicationReceipt | None = None
                try:
                    with self.lock(prepared) as capability:
                        receipt = runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )
                except runner.RunnerError as exc:
                    publication_error = exc

                self.assertIsNone(
                    publication_error,
                    msg=(
                        "verified staging_candidate journal did not "
                        "authorize the exact result-only creation prefix: "
                        f"{getattr(publication_error, 'code', None)}"
                    ),
                )
                self.assertIsNotNone(receipt)
                assert receipt is not None
                self.assertEqual(receipt.status, "candidate_ready")
                self.assertFalse(paths.candidate_stage_path.exists())
                self.assert_pair_directory(paths.candidate_root)
                self.assertEqual(
                    paths.candidate_receipt_path.read_bytes(),
                    state.candidate_receipt_bytes,
                )
                final_journal = phase_c1.load_json_strict(
                    paths.publication_journal_path.read_bytes(),
                    source="journaled_result_only_recovery",
                )
                self.assertIsInstance(final_journal, dict)
                self.assertEqual(
                    final_journal["schema_version"],
                    "EmotionStatePhaseC1PublicationJournalV1",
                )
                self.assertEqual(
                    final_journal["status"],
                    "candidate_ready",
                )
                self.assertEqual(final_journal["sequence"], 1)
                self.assertEqual(
                    final_journal["previous_journal_sha256"],
                    self._sha256(journal_bytes),
                )
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_unjournaled_result_only_candidate_stage_remains_fail_closed(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            try:
                prepared = self.prepared_candidate()
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                paths.candidate_stage_path.mkdir()
                (
                    paths.candidate_stage_path / "result.json"
                ).write_bytes(self.expected_candidate_result_bytes)
                before = tuple(
                    (
                        child.name,
                        child.read_bytes(),
                    )
                    for child in paths.candidate_stage_path.iterdir()
                )

                with self.lock(prepared) as capability:
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                after = tuple(
                    (
                        child.name,
                        child.read_bytes(),
                    )
                    for child in paths.candidate_stage_path.iterdir()
                )
                self.assertEqual(after, before)
                self.assertFalse(paths.publication_journal_path.exists())
                self.assertFalse(
                    paths.publication_journal_stage_path.exists(),
                )
                self.assertFalse(paths.candidate_root.exists())
                self.assertFalse(paths.candidate_receipt_path.exists())
            finally:
                self.stop_runner_context(paths_patch, head_patch)

    def test_unjournaled_report_only_candidate_stage_remains_fail_closed(
        self,
    ) -> None:
        with self.isolated_mutation_root():
            paths, paths_patch, head_patch = self.runner_context()
            try:
                prepared = self.prepared_candidate()
                paths.ignored_root.mkdir(parents=True, exist_ok=True)
                paths.candidate_stage_path.mkdir()
                (
                    paths.candidate_stage_path / "report.md"
                ).write_bytes(self.expected_candidate_report_bytes)
                before = tuple(
                    (
                        child.name,
                        child.read_bytes(),
                    )
                    for child in paths.candidate_stage_path.iterdir()
                )

                with self.lock(prepared) as capability:
                    with self.assertRaises(runner.RunnerError):
                        runner.finalize_phase_c1_publication(
                            prepared,
                            capability=capability,
                        )

                after = tuple(
                    (
                        child.name,
                        child.read_bytes(),
                    )
                    for child in paths.candidate_stage_path.iterdir()
                )
                self.assertEqual(after, before)
                self.assertFalse(paths.publication_journal_path.exists())
                self.assertFalse(
                    paths.publication_journal_stage_path.exists(),
                )
                self.assertFalse(paths.candidate_root.exists())
                self.assertFalse(paths.candidate_receipt_path.exists())
            finally:
                self.stop_runner_context(paths_patch, head_patch)


class PhaseC1IndependentValidatorTests(
    _PhaseC1FixtureMixin,
    unittest.TestCase,
):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="emotion-state-c1-validator-",
        )
        self.addCleanup(self.temporary_directory.cleanup)
        self.temp_root = Path(self.temporary_directory.name)
        self.protocol_bytes = self.protocol_path.read_bytes()
        self.protocol = phase_c1.validate_discovery_protocol(
            self.valid_protocol_payload()
        )
        self.input_paths = {
            "PROTOCOL_PATH": (
                self.temp_root
                / "research"
                / "experiments"
                / "configs"
                / "emotion-state-004-phase-c1-discovery-protocol.json"
            ),
            "SEARCH_LEDGER_PATH": (
                self.temp_root
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_search_ledger.json"
            ),
            "SOURCE_LEDGER_PATH": (
                self.temp_root
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_source_evidence_ledger.json"
            ),
            "SOURCE_REVIEW_PATH": (
                self.temp_root
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_source_review_receipt.json"
            ),
        }
        self.candidate_root = (
            self.temp_root
            / ".tmp"
            / "emotion-state-004-phase-c1"
            / "candidate"
        )
        self.canonical_root = (
            self.temp_root
            / "research"
            / "experiments"
            / "generated"
            / (
                "EMOTION-STATE-004-phase-c1-operational-signal-"
                "evidence-admission"
            )
        )
        self.paths_patch = mock.patch.multiple(
            validator,
            ROOT=self.temp_root,
            CANDIDATE_ROOT=self.candidate_root,
            CANONICAL_ROOT=self.canonical_root,
            **self.input_paths,
        )
        self.paths_patch.start()
        self.addCleanup(self.paths_patch.stop)
        self.seed_authority(
            self.authority_bytes(admissible_signals=("confusion",))
        )

    @staticmethod
    def canonical_dataclass_bytes(
        value: object,
        schema_version: str,
    ) -> bytes:
        return PhaseC1DecisionTests.canonical_dataclass_bytes(
            value,
            schema_version,
        )

    @staticmethod
    def closed_validator_import_source() -> bytes:
        return (
            b"from __future__ import annotations\n"
            b"import ast\n"
            b"import ctypes\n"
            b"import json\n"
            b"import os\n"
            b"import re\n"
            b"import stat\n"
            b"import subprocess\n"
            b"import sys\n"
            b"import threading\n"
            b"from collections.abc import Mapping, Sequence\n"
            b"from ctypes import wintypes\n"
            b"from dataclasses import fields, is_dataclass\n"
            b"from pathlib import Path\n"
            b"from typing import Any, Final\n"
            b"from scripts import "
            b"emotion_state_phase_c1_contracts as phase_c1\n"
            b"kernel32 = ctypes.WinDLL("
            b"'kernel32', use_last_error=True)\n"
            b"get_information = "
            b"kernel32.GetFileInformationByHandle\n"
            b"kernel32 = ctypes.WinDLL("
            b"'kernel32', use_last_error=True)\n"
            b"create_file = kernel32.CreateFileW\n"
            b"kernel32 = ctypes.WinDLL("
            b"'kernel32', use_last_error=True)\n"
            b"close_handle = kernel32.CloseHandle\n"
            b"def _drain_git_pipe(\n"
            b"    stream: Any,\n"
            b"    *,\n"
            b"    maximum_bytes: int,\n"
            b"    chunks: list[bytes],\n"
            b"    overflow: threading.Event,\n"
            b"    errors: list[BaseException],\n"
            b"    process: subprocess.Popen[bytes],\n"
            b"):\n"
            b"    process.kill()\n"
            b"    process.kill()\n"
            b"def _git(repository_root, *arguments):\n"
            b"    command = [\n"
            b"        'git',\n"
            b"        '--no-replace-objects',\n"
            b"        '--no-lazy-fetch',\n"
            b"        *arguments,\n"
            b"    ]\n"
            b"    process = subprocess.Popen(\n"
            b"        command,\n"
            b"        cwd=repository_root,\n"
            b"        stdin=subprocess.DEVNULL,\n"
            b"        stdout=subprocess.PIPE,\n"
            b"        stderr=subprocess.PIPE,\n"
            b"        shell=False,\n"
            b"        close_fds=True,\n"
            b"        env=_git_environment(),\n"
            b"    )\n"
            b"    if process.stdout is None or process.stderr is None:\n"
            b"        process.kill()\n"
            b"    stdout_thread = threading.Thread(\n"
            b"        target=_drain_git_pipe,\n"
            b"        kwargs={\n"
            b"            'stream': process.stdout,\n"
            b"            'maximum_bytes': maximum_output_bytes,\n"
            b"            'chunks': stdout_chunks,\n"
            b"            'overflow': overflow,\n"
            b"            'errors': drain_errors,\n"
            b"            'process': process,\n"
            b"        },\n"
            b"        daemon=True,\n"
            b"    )\n"
            b"    stderr_thread = threading.Thread(\n"
            b"        target=_drain_git_pipe,\n"
            b"        kwargs={\n"
            b"            'stream': process.stderr,\n"
            b"            'maximum_bytes': maximum_output_bytes,\n"
            b"            'chunks': stderr_chunks,\n"
            b"            'overflow': overflow,\n"
            b"            'errors': drain_errors,\n"
            b"            'process': process,\n"
            b"        },\n"
            b"        daemon=True,\n"
            b"    )\n"
            b"    stdout_thread.start()\n"
            b"    stderr_thread.start()\n"
            b"    returncode = process.wait(timeout=15)\n"
            b"    process.kill()\n"
            b"    returncode = process.wait(timeout=2)\n"
            b"    process.kill()\n"
            b"    stdout_thread.join(timeout=2)\n"
            b"    stderr_thread.join(timeout=2)\n"
            b"    if stdout_thread.is_alive() or stderr_thread.is_alive():\n"
            b"        process.kill()\n"
            b"        stdout_thread.join(timeout=2)\n"
            b"        stderr_thread.join(timeout=2)\n"
            b"    process.stdout.close()\n"
            b"    process.stderr.close()\n"
            b"    if (\n"
            b"        timed_out\n"
            b"        or stdout_thread.is_alive()\n"
            b"        or stderr_thread.is_alive()\n"
            b"    ):\n"
            b"        pass\n"
            b"def main(argv: Sequence[str] | None = None):\n"
            b"    arguments = sys.argv[1:] if argv is None else argv\n"
            b"    payload = None\n"
            b"    sys.stdout.buffer.write("
            b"phase_c1.canonical_json_bytes(payload))\n"
            b"_git(repository_root, 'rev-parse', '--verify', "
            b"'HEAD^{commit}')\n"
            b"_git(repository_root, 'rev-parse', '--verify', "
            b"f'{commit}^{{commit}}')\n"
            b"_git(repository_root, 'ls-tree', '-z', commit, '--', "
            b"_literal_pathspec(relative_path))\n"
            b"_git(repository_root, 'ls-files', '--stage', '-z', "
            b"'--', _literal_pathspec(relative_path))\n"
            b"_git(repository_root, 'cat-file', '-s', object_id, "
            b"maximum_output_bytes=128)\n"
            b"_git(repository_root, 'cat-file', 'blob', object_id, "
            b"maximum_output_bytes=maximum_bytes)\n"
            b"_git(repository_root, 'log', '--format=%H', "
            b"'--diff-filter=A', '--no-renames', head, '--', "
            b"_literal_pathspec(relative_path))\n"
            b"_git(repository_root, 'diff-tree', '--no-commit-id', "
            b"'--name-status', '-r', '-z', '--no-renames', "
            b"pair_commit, '--')\n"
            b"_git(repository_root, 'merge-base', '--is-ancestor', "
            b"ancestor, descendant, expected_codes=(0, 1))\n"
            b"_git(requested, 'rev-parse', '--show-toplevel')\n"
            b"_git(repository, 'rev-list', '--parents', '-n', '1', "
            b"pair_commit)\n"
        )

    def authority_bytes(
        self,
        *,
        admissible_signals: tuple[str, ...] = (),
        unresolved_signals: tuple[str, ...] = (),
    ) -> dict[str, bytes]:
        search, source_ledger, review = (
            PhaseC1DecisionTests.validated_projection_inputs(
                self,
                admissible_signals=admissible_signals,
                unresolved_signals=unresolved_signals,
            )
        )
        return {
            "protocol_bytes": self.protocol_bytes,
            "search_ledger_bytes": self.canonical_dataclass_bytes(
                search,
                "EmotionStatePhaseC1SearchLedgerV1",
            ),
            "source_ledger_bytes": self.canonical_dataclass_bytes(
                source_ledger,
                "EmotionStatePhaseC1SourceEvidenceLedgerV1",
            ),
            "review_receipt_bytes": self.canonical_dataclass_bytes(
                review,
                "EmotionStatePhaseC1SourceReviewReceiptV1",
            ),
        }

    def seed_authority(self, authority: dict[str, bytes]) -> None:
        mapping = {
            "protocol_bytes": self.input_paths["PROTOCOL_PATH"],
            "search_ledger_bytes": self.input_paths["SEARCH_LEDGER_PATH"],
            "source_ledger_bytes": self.input_paths["SOURCE_LEDGER_PATH"],
            "review_receipt_bytes": self.input_paths["SOURCE_REVIEW_PATH"],
        }
        for name, path in mapping.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(authority[name])

    @staticmethod
    def reself(payload: dict[str, object]) -> None:
        PhaseC1AggregateRunnerTests.reself(payload)

    def build_pair(
        self,
        authority: dict[str, bytes] | None = None,
        *,
        head_commit: str = "a" * 40,
        validator_blob_id: str = "b" * 40,
    ) -> tuple[dict[str, object], bytes, bytes]:
        if authority is None:
            authority = self.authority_bytes(
                admissible_signals=("confusion",)
            )
        result = runner.build_phase_c1_result(
            head_commit=head_commit,
            validator_blob_id=validator_blob_id,
            **authority,
        )
        result_bytes = phase_c1.canonical_json_bytes(result)
        report_bytes = runner.render_phase_c1_report(result, **authority)
        return result, result_bytes, report_bytes

    def parsed_authority(
        self,
        authority: dict[str, bytes],
    ) -> tuple[
        phase_c1.PhaseC1ProtocolV1,
        phase_c1.PhaseC1SearchLedgerV1,
        phase_c1.PhaseC1SourceEvidenceLedgerV1,
        phase_c1.PhaseC1SourceReviewReceiptV1,
    ]:
        protocol_payload = phase_c1.load_json_strict(
            authority["protocol_bytes"],
            source="protocol",
        )
        protocol = phase_c1.validate_discovery_protocol(protocol_payload)
        search_payload = phase_c1.load_json_strict(
            authority["search_ledger_bytes"],
            source="search",
        )
        search = phase_c1.validate_search_ledger(
            search_payload,
            protocol=protocol,
        )
        source_payload = phase_c1.load_json_strict(
            authority["source_ledger_bytes"],
            source="source",
        )
        source_ledger = phase_c1.validate_source_evidence_ledger(
            source_payload,
            protocol=protocol,
            search_ledger_bytes=authority["search_ledger_bytes"],
        )
        review_payload = phase_c1.load_json_strict(
            authority["review_receipt_bytes"],
            source="review",
        )
        review = phase_c1.validate_source_review_receipt(
            review_payload,
            protocol=protocol,
            search_ledger_bytes=authority["search_ledger_bytes"],
            source_evidence_ledger_bytes=authority["source_ledger_bytes"],
        )
        return protocol, search, source_ledger, review

    def test_validator_ast_allows_only_the_exact_contract_dependency(
        self,
    ) -> None:
        allowed = self.closed_validator_import_source()
        actual_validator_bytes = Path(validator.__file__).read_bytes()
        validator._validate_validator_dependency_ast(allowed)
        rejected = (
            (
                b"from . import "
                b"emotion_state_phase_c1_decision as hidden\n"
            ),
            (
                b"from .emotion_state_phase_c1_decision "
                b"import decide as hidden\n"
            ),
            (
                b"import scripts.emotion_state_phase_c1_decision "
                b"as hidden\n"
            ),
            (
                b"from scripts import "
                b"run_emotion_state_004_phase_c1 as hidden\n"
            ),
            (
                b"import importlib\n"
                b"importlib.import_module("
                b"'scripts.emotion_state_phase_c1_decision')\n"
            ),
            (
                b"__import__('scripts.run_emotion_state_004_phase_c1')\n"
            ),
            (
                b"producer = "
                b"'scripts.emotion_state_phase_c1_decision'\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as contracts\n"
            ),
            (
                b"import scripts.emotion_state_phase_c1_contracts "
                b"as phase_c1\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"from scripts import unrelated as hidden\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"exec('from ' + 'scripts import ' + "
                b"'run_emotion_state_004_phase_c1')\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"eval('_' + '_import__' + "
                b"'(' + repr('scripts' + "
                b"'.run_emotion_state_004_phase_c1') + ')')\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"compile('import ' + 'scripts' + "
                b"'.run_emotion_state_004_phase_c1', "
                b"'<dynamic>', 'exec')\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"hidden = __import__\n"
                b"hidden('scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"import builtins as safe\n"
                b"hidden = getattr(safe, '__im' + 'port__')\n"
                b"hidden('scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                b"from scripts import "
                b"emotion_state_phase_c1_contracts as phase_c1\n"
                b"from builtins import exec as hidden\n"
                b"hidden('import ' + 'scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                allowed
                + b"hidden = globals()['__builtins__']["
                b"''.join(['__im', 'port__'])]\n"
                b"hidden('scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                allowed
                + b"hidden = getattr("
                b"globals()['__builtins__'], "
                b"''.join(['__im', 'port__']))\n"
                b"hidden('scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                allowed
                + b"hidden = locals()['__builtins__']["
                b"''.join(['ex', 'ec'])]\n"
            ),
            (
                allowed
                + b"hidden = vars(__builtins__)["
                b"''.join(['ev', 'al'])]\n"
            ),
            (
                allowed
                + b"setattr(object(), 'loader', "
                b"globals()['__builtins__'])\n"
            ),
            (
                allowed
                + b"delattr(object(), 'loader')\n"
            ),
            (
                allowed
                + b"hidden = sys.modules["
                b"'scripts' + "
                b"'.run_emotion_state_004_phase_c1']\n"
            ),
            (
                allowed
                + b"hidden = getattr(sys, 'mod' + 'ules')["
                b"'scripts' + "
                b"'.run_emotion_state_004_phase_c1']\n"
            ),
            (
                allowed
                + b"ctypes.PyDLL(None)\n"
            ),
            (
                allowed
                + b"import runpy\n"
                b"runpy.run_module('scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                allowed
                + b"ctypes.cdll.LoadLibrary('outside')\n"
            ),
            (
                allowed
                + b"ctypes.windll.LoadLibrary('outside')\n"
            ),
            (
                allowed
                + b"ctypes.pydll.LoadLibrary('outside')\n"
            ),
            (
                allowed
                + b"ctypes.oledll.LoadLibrary('outside')\n"
            ),
            (
                allowed
                + b"ctypes._dlopen('outside', 0)\n"
            ),
            (
                allowed
                + b"ctypes.LibraryLoader(object)\n"
            ),
            (
                allowed
                + b"ctypes.LoadLibrary('outside')\n"
            ),
            (
                allowed
                + b"hidden = sys._getframe().f_builtins["
                b"''.join(['__im', 'port__'])]\n"
                b"hidden('scripts' + "
                b"'.run_emotion_state_004_phase_c1')\n"
            ),
            (
                allowed
                + b"os.system('outside')\n"
            ),
            (
                allowed
                + b"subprocess.Popen(['outside'])\n"
            ),
            (
                actual_validator_bytes
                + b"\nx = os\n"
                + b"x.system('outside')\n"
            ),
            (
                actual_validator_bytes
                + b"\nsp = subprocess\n"
                + b"sp.Popen(['outside'])\n"
            ),
            (
                actual_validator_bytes
                + b"\nc = ctypes\n"
                + b"c.cdll.LoadLibrary('outside')\n"
            ),
            (
                actual_validator_bytes
                + b"\ns = sys\n"
                + b"s._getframe()\n"
            ),
            (
                actual_validator_bytes
                + b"\nsys.stdout.write('outside')\n"
            ),
            (
                actual_validator_bytes
                + b"\nsys.stdout.buffer.write(b'outside')\n"
            ),
            (
                actual_validator_bytes
                + b"\nsys.stdout.buffer.write("
                + b"phase_c1.canonical_json_bytes({}))\n"
            ),
            (
                actual_validator_bytes
                + b"\nsys.stdout.buffer.write("
                + b"phase_c1.canonical_json_bytes(payload))\n"
            ),
            (
                actual_validator_bytes
                + b"\nstdout_alias = sys.stdout\n"
            ),
            (
                actual_validator_bytes
                + b"\njson.__builtins__\n"
            ),
            (
                actual_validator_bytes
                + b"\njson.decoder.__builtins__\n"
            ),
            (
                actual_validator_bytes
                + b"\nthreading._sys.modules\n"
            ),
            (
                actual_validator_bytes
                + b"\nprint.__self__.__import__('outside')\n"
            ),
            (
                actual_validator_bytes
                + b"\ntry:\n"
                + b"    raise RuntimeError('outside')\n"
                + b"except RuntimeError as exception:\n"
                + b"    exception.__traceback__.tb_frame.f_builtins\n"
            ),
            (
                actual_validator_bytes
                + b"\nos.stat.__self__.system('outside')\n"
            ),
            (
                actual_validator_bytes
                + b"\nsubprocess.Popen[bytes].__origin__\n"
            ),
            (
                actual_validator_bytes
                + b"\nsubprocess.Popen[bytes](['outside'])\n"
            ),
            (
                actual_validator_bytes
                + b"\nctypes.WinDLL("
                + b"'kernel32', use_last_error=True"
                + b").WinExec('outside', 0)\n"
            ),
            (
                actual_validator_bytes
                + b"\nos.path.__builtins__\n"
            ),
            (
                actual_validator_bytes
                + b"\nos.path.sys.modules\n"
            ),
            (
                actual_validator_bytes
                + b"\nphase_c1.__builtins__\n"
            ),
            (
                actual_validator_bytes
                + b"\nphase_c1.load_json_strict.__builtins__\n"
            ),
            (
                actual_validator_bytes
                + b"\nast.literal_eval('0')\n"
            ),
            (
                actual_validator_bytes
                + b"\nast.Load()\n"
            ),
            (
                actual_validator_bytes
                + b"\njson.loads('{}')\n"
            ),
            (
                actual_validator_bytes
                + b"\nre.search('x', 'x')\n"
            ),
            (
                actual_validator_bytes
                + b"\nstat.filemode(0)\n"
            ),
            (
                actual_validator_bytes
                + b"\nthreading.Timer(0, print)\n"
            ),
            (
                actual_validator_bytes
                + b"\nwintypes.WORD\n"
            ),
            (
                actual_validator_bytes
                + b"\nphase_c1.unapproved\n"
            ),
            (
                actual_validator_bytes
                + b"\njson = object()\n"
                + b"json.dumps({})\n"
            ),
            (
                actual_validator_bytes
                + b"\nloader = kernel32\n"
            ),
            (
                actual_validator_bytes
                + b"\nkernel32.WinExec('outside', 0)\n"
            ),
            (
                actual_validator_bytes.replace(
                    (
                        b"kernel32 = ctypes.WinDLL("
                        b"\"kernel32\", use_last_error=True)"
                    ),
                    (
                        b"loader = ctypes.WinDLL("
                        b"\"kernel32\", use_last_error=True)"
                    ),
                    1,
                )
            ),
            (
                actual_validator_bytes
                + b"\n__loader__.load_module('scripts' + '.x')\n"
            ),
            (
                actual_validator_bytes
                + b"\n__spec__.loader.load_module('scripts' + '.x')\n"
            ),
            (
                actual_validator_bytes
                + b"\nhelp('scripts' + '.x')\n"
            ),
            (
                actual_validator_bytes
                + b"\nquit()\n"
            ),
            (
                actual_validator_bytes
                + b"\nsecond = type(process)(['outside'])\n"
            ),
            (
                actual_validator_bytes
                + b"\nprocess.pid\n"
            ),
            (
                actual_validator_bytes
                + b"\nprocess = object()\n"
            ),
            (
                actual_validator_bytes.replace(
                    b"    try:\n"
                    b"        process = subprocess.Popen(\n",
                    b"    command[:] = ['git', 'status']\n"
                    b"    try:\n"
                    b"        process = subprocess.Popen(\n",
                    1,
                )
            ),
            (
                actual_validator_bytes
                + b"\ncommand_alias = command\n"
            ),
            (
                actual_validator_bytes
                + b"\n_git("
                + b"ROOT, '-c', "
                + b"'alias.x=!python -c \"print(1)\"', 'x')\n"
            ),
            (
                actual_validator_bytes
                + b"\ngit_alias = _git\n"
            ),
            (
                actual_validator_bytes.replace(
                    b'        "HEAD^{commit}",\n',
                    b'        "HEAD",\n',
                    1,
                )
            ),
            (
                actual_validator_bytes
                + b"\nPath = object\n"
            ),
            (
                actual_validator_bytes
                + b"\nMapping = object\n"
            ),
            (
                actual_validator_bytes
                + b"\nfields = object\n"
            ),
            (
                actual_validator_bytes
                + b"\ndel Final\n"
            ),
            (
                actual_validator_bytes.replace(
                    b"    command = [\n",
                    b"    arguments = ('status',)\n"
                    b"    command = [\n",
                    1,
                )
            ),
            (
                actual_validator_bytes.replace(
                    b"    command = [\n",
                    b"    del arguments\n"
                    b"    command = [\n",
                    1,
                )
            ),
        )
        for source in rejected:
            with self.subTest(source=source):
                with self.assertRaises(validator.ValidationError):
                    validator._validate_validator_dependency_ast(source)

        validator._validate_validator_dependency_ast(actual_validator_bytes)
        tree = ast.parse(actual_validator_bytes.decode("utf-8"))
        forbidden_names = {
            "PhaseC1RunnerPaths",
            "PRODUCTION_PATHS",
            "_project_phase_c1_result",
            "build_phase_c1_result",
            "render_phase_c1_report",
        }
        used_names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
        } | {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
        }
        self.assertTrue(forbidden_names.isdisjoint(used_names))

    def test_validator_has_no_user_defined_mutable_container_globals(
        self,
    ) -> None:
        interpreter_metadata = {
            "__annotations__",
            "__builtins__",
        }

        def mutable_names() -> set[str]:
            return {
                name
                for name, value in vars(validator).items()
                if name not in interpreter_metadata
                and isinstance(value, (dict, list, set))
            }

        self.assertEqual(mutable_names(), set())
        with mock.patch.object(validator, "_CACHE", {}, create=True):
            self.assertEqual(mutable_names(), {"_CACHE"})

    def test_validator_ast_rejects_all_protected_binding_forms(
        self,
    ) -> None:
        source = Path(validator.__file__).read_bytes()

        def replace_last(old: bytes, new: bytes) -> bytes:
            prefix, separator, suffix = source.rpartition(old)
            self.assertEqual(separator, old)
            return prefix + new + suffix

        rejected = (
            (
                source
                + b"\nrecovered = stdout_thread._kwargs['process']\n"
                + b"type(recovered)(['outside'])\n"
            ),
            source + b"\nstream_alias = process.stdout\n",
            source + b"\nprocess = object()\n",
            source + b"\ndel process\n",
            source + b"\ndef command():\n    pass\n",
            source + b"\nclass Path:\n    pass\n",
            source + b"\nasync def fields():\n    pass\n",
            source + b"\n(lambda process: process)(None)\n",
            source + b"\ndef helper(Mapping):\n    pass\n",
            (
                source
                + b"\ntry:\n"
                + b"    raise RuntimeError('outside')\n"
                + b"except RuntimeError as arguments:\n"
                + b"    pass\n"
            ),
            source.replace(
                b"        *arguments,\n"
                b"    ]\n",
                b"        *arguments,\n"
                b"    ]\n"
                b"    match object():\n"
                b"        case command:\n"
                b"            pass\n",
                1,
            ),
            source + b"\nmatch []:\n    case [*stdout_thread]:\n        pass\n",
            (
                source
                + b"\nmatch {}:\n"
                + b"    case {**stderr_thread}:\n"
                + b"        pass\n"
            ),
            source + b"\ndef helper():\n    global _git\n",
            (
                source
                + b"\ndef outer():\n"
                + b"    def inner():\n"
                + b"        nonlocal Path\n"
            ),
            source.replace(
                b"def _git(\n",
                b"@staticmethod\n"
                b"def _git(\n",
                1,
            ),
            replace_last(
                b"process.kill()",
                b"process.wait()",
            ),
            replace_last(
                b"stdout_thread.start()",
                b"stdout_thread.run()",
            ),
            replace_last(
                b"stderr_thread.start()",
                b"stderr_thread.run()",
            ),
            replace_last(
                b"stdout_thread.is_alive()",
                b"stdout_thread.join()",
            ),
            replace_last(
                b"process.wait(timeout=15)",
                b"process.communicate(timeout=15)",
            ),
        )
        for payload in rejected:
            with self.subTest(payload=payload):
                with self.assertRaises(validator.ValidationError):
                    validator._validate_validator_dependency_ast(payload)

    def test_validator_ast_rejects_drain_process_method_mutations(
        self,
    ) -> None:
        source = Path(validator.__file__).read_bytes()
        start = source.index(b"def _drain_git_pipe(")
        end = source.index(b"\ndef _git(", start)
        drain_source = source[start:end]
        marker = b"process.kill()"
        offsets: list[int] = []
        cursor = 0
        while True:
            offset = drain_source.find(marker, cursor)
            if offset == -1:
                break
            offsets.append(offset)
            cursor = offset + len(marker)
        self.assertEqual(len(offsets), 2)

        def mutate(offset: int, replacement: bytes) -> bytes:
            absolute = start + offset
            return (
                source[:absolute]
                + replacement
                + source[absolute + len(marker) :]
            )

        rejected = (
            mutate(offsets[0], b"process.wait()"),
            mutate(offsets[1], b"process.wait()"),
            mutate(offsets[0], b"process.wait(timeout=15)"),
        )
        for payload in rejected:
            with self.subTest(payload=payload):
                with self.assertRaises(validator.ValidationError):
                    validator._validate_validator_dependency_ast(payload)

    def test_validator_ast_rejects_drain_binding_forms(self) -> None:
        source = Path(validator.__file__).read_bytes()
        rejected = (
            source.replace(
                b"\ndef _git(",
                b"\n_drain_git_pipe = print\n\ndef _git(",
                1,
            ),
            source.replace(
                b"\ndef _git(",
                b"\nclass _drain_git_pipe:\n"
                b"    pass\n\n"
                b"def _git(",
                1,
            ),
            source.replace(
                b"def _drain_git_pipe(",
                b"@staticmethod\n"
                b"def _drain_git_pipe(",
                1,
            ),
        )
        for payload in rejected:
            with self.subTest(payload=payload):
                with self.assertRaises(validator.ValidationError):
                    validator._validate_validator_dependency_ast(payload)

    def test_validator_ast_rejects_hybrid_git_body_pairs(self) -> None:
        production = Path(validator.__file__).read_bytes()
        synthetic = self.closed_validator_import_source()

        def function_source(payload: bytes, name: str) -> bytes:
            text = payload.decode("utf-8")
            functions = [
                node
                for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef)
                and node.name == name
            ]
            self.assertEqual(len(functions), 1)
            function = functions[0]
            return "\n".join(
                text.splitlines()[
                    function.lineno - 1 : function.end_lineno
                ]
            ).encode("utf-8")

        production_git = function_source(production, "_git")
        production_drain = function_source(
            production,
            "_drain_git_pipe",
        )
        synthetic_git = function_source(synthetic, "_git")
        synthetic_drain = function_source(
            synthetic,
            "_drain_git_pipe",
        )
        rejected = (
            production.replace(
                production_drain,
                synthetic_drain,
                1,
            ),
            production.replace(
                production_git,
                synthetic_git,
                1,
            ),
            production.replace(
                production_drain,
                synthetic_drain,
                1,
            ).replace(
                production_git,
                synthetic_git,
                1,
            ),
        )
        for payload in rejected:
            with self.subTest(payload=payload):
                with self.assertRaises(validator.ValidationError):
                    validator._validate_validator_dependency_ast(payload)

    def test_runner_and_validator_pin_lexical_root_before_project_imports(
        self,
    ) -> None:
        for path in (
            Path(runner.__file__),
            Path(validator.__file__),
        ):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                project_import_offsets = tuple(
                    offset
                    for marker in (
                        "from scripts import ",
                        "from scripts.",
                        "import scripts.",
                    )
                    if (offset := text.find(marker)) >= 0
                )
                self.assertTrue(project_import_offsets)
                self.assertGreater(
                    min(project_import_offsets),
                    text.index("_IMPORT_ROOT ="),
                )
                self.assertGreater(
                    min(project_import_offsets),
                    text.index("sys.path.insert(0,"),
                )

    def test_validator_rederives_all_four_overall_decisions(self) -> None:
        cases = (
            (
                EXPECTED_SIGNALS,
                (),
                "proceed_full_to_c2",
                list(EXPECTED_SIGNALS),
            ),
            (
                ("confusion",),
                (),
                "proceed_partial_to_c2",
                ["confusion"],
            ),
            ((), ("confusion",), "defer_c2", []),
            ((), (), "stop_c2", []),
        )
        for admitted, unresolved, expected, eligible in cases:
            with self.subTest(expected=expected):
                parsed = self.parsed_authority(
                    self.authority_bytes(
                        admissible_signals=admitted,
                        unresolved_signals=unresolved,
                    )
                )
                projection = (
                    validator.derive_phase_c1_projection_independently(
                        protocol=parsed[0],
                        search_ledger=parsed[1],
                        source_ledger=parsed[2],
                        review_receipt=parsed[3],
                    )
                )
                self.assertEqual(
                    projection["overall_decision"],
                    expected,
                )
                self.assertEqual(
                    projection["c2_eligible_signals"],
                    eligible,
                )

    def test_independent_projection_is_pure_and_does_not_read_paths(
        self,
    ) -> None:
        parsed = self.parsed_authority(
            self.authority_bytes(admissible_signals=("confusion",))
        )
        with mock.patch(
            "builtins.open",
            side_effect=AssertionError("projection opened a path"),
        ), mock.patch.object(
            validator.subprocess,
            "run",
            side_effect=AssertionError("projection invoked Git"),
        ):
            projection = (
                validator.derive_phase_c1_projection_independently(
                    protocol=parsed[0],
                    search_ledger=parsed[1],
                    source_ledger=parsed[2],
                    review_receipt=parsed[3],
                )
            )
        self.assertEqual(
            projection["overall_decision"],
            "proceed_partial_to_c2",
        )

    def test_validator_pair_projection_matches_all_four_fixture_outcomes(
        self,
    ) -> None:
        cases = (
            (EXPECTED_SIGNALS, (), "proceed_full_to_c2"),
            (("confusion",), (), "proceed_partial_to_c2"),
            ((), ("confusion",), "defer_c2"),
            ((), (), "stop_c2"),
        )
        for admitted, unresolved, expected in cases:
            with self.subTest(expected=expected):
                authority = self.authority_bytes(
                    admissible_signals=admitted,
                    unresolved_signals=unresolved,
                )
                self.seed_authority(authority)
                _payload, result_bytes, report_bytes = self.build_pair(
                    authority
                )
                validated = validator.validate_pair_bytes(
                    result_bytes,
                    report_bytes,
                )
                self.assertEqual(validated["overall_decision"], expected)

    def test_projection_independently_rejects_derived_search_rewrites(
        self,
    ) -> None:
        parsed = self.parsed_authority(
            self.authority_bytes(admissible_signals=("confusion",))
        )
        search = parsed[1]
        mutations = (
            (
                "search_complete",
                replace(
                    search,
                    search_complete=not search.search_complete,
                ),
            ),
            (
                "fail_ready",
                replace(
                    search,
                    fail_ready_by_signal=MappingProxyType(
                        {
                            **dict(search.fail_ready_by_signal),
                            "hesitation": not search.fail_ready_by_signal[
                                "hesitation"
                            ],
                        }
                    ),
                ),
            ),
            (
                "overflow",
                replace(
                    search,
                    overflow_count_by_signal=MappingProxyType(
                        {
                            **dict(search.overflow_count_by_signal),
                            "hesitation": 1,
                        }
                    ),
                ),
            ),
        )
        for name, mutation in mutations:
            with self.subTest(mutation=name):
                search_bytes = self.canonical_dataclass_bytes(
                    mutation,
                    "EmotionStatePhaseC1SearchLedgerV1",
                )
                source_ledger = replace(
                    parsed[2],
                    search_ledger_sha256=phase_c1.sha256_bytes(
                        search_bytes
                    ),
                )
                source_bytes = self.canonical_dataclass_bytes(
                    source_ledger,
                    "EmotionStatePhaseC1SourceEvidenceLedgerV1",
                )
                review = replace(
                    parsed[3],
                    search_ledger_sha256=phase_c1.sha256_bytes(
                        search_bytes
                    ),
                    source_evidence_ledger_sha256=phase_c1.sha256_bytes(
                        source_bytes
                    ),
                )
                with self.assertRaises(validator.ValidationError):
                    validator.derive_phase_c1_projection_independently(
                        protocol=parsed[0],
                        search_ledger=mutation,
                        source_ledger=source_ledger,
                        review_receipt=review,
                    )

    def test_inputs_and_pair_bind_all_four_canonical_authorities(
        self,
    ) -> None:
        loaded = validator.validate_phase_c1_inputs()
        self.assertEqual(
            loaded["input_sha256s"],
            {
                "protocol_sha256": phase_c1.sha256_bytes(
                    self.protocol_bytes
                ),
                "search_ledger_sha256": phase_c1.sha256_bytes(
                    self.input_paths["SEARCH_LEDGER_PATH"].read_bytes()
                ),
                "source_evidence_ledger_sha256": phase_c1.sha256_bytes(
                    self.input_paths["SOURCE_LEDGER_PATH"].read_bytes()
                ),
                "source_review_receipt_sha256": phase_c1.sha256_bytes(
                    self.input_paths["SOURCE_REVIEW_PATH"].read_bytes()
                ),
            },
        )
        _payload, result_bytes, report_bytes = self.build_pair()
        self.assertEqual(
            validator.validate_pair_bytes(
                result_bytes,
                report_bytes,
            )["overall_decision"],
            "proceed_partial_to_c2",
        )
        for path_key in (
            "PROTOCOL_PATH",
            "SEARCH_LEDGER_PATH",
            "SOURCE_LEDGER_PATH",
            "SOURCE_REVIEW_PATH",
        ):
            with self.subTest(path=path_key):
                path = self.input_paths[path_key]
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                try:
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_pair_bytes(
                            result_bytes,
                            report_bytes,
                        )
                finally:
                    path.write_bytes(original)

    def test_coherent_result_and_report_mutation_still_rejects(self) -> None:
        payload, result_bytes, report_bytes = self.build_pair()
        validator.validate_pair_bytes(result_bytes, report_bytes)
        per_signal = payload["per_signal"]
        self.assertIsInstance(per_signal, list)
        hesitation = per_signal[0]
        self.assertIsInstance(hesitation, dict)
        hesitation.update(
            {
                "decision": "pass",
                "c2_eligible": True,
            }
        )
        payload["c2_eligible_signals"] = ["hesitation", "confusion"]
        payload["overall_decision"] = "proceed_partial_to_c2"
        self.reself(payload)
        mutated_result = phase_c1.canonical_json_bytes(payload)
        mutated_report = validator.render_expected_report_independently(
            payload
        )
        with self.assertRaises(validator.ValidationError):
            validator.validate_pair_bytes(
                mutated_result,
                mutated_report,
            )

    def test_pair_reader_is_allowlisted_bounded_and_no_follow(self) -> None:
        _payload, result_bytes, report_bytes = self.build_pair()
        self.candidate_root.mkdir(parents=True)
        (self.candidate_root / "result.json").write_bytes(result_bytes)
        (self.candidate_root / "report.md").write_bytes(report_bytes)
        self.assertEqual(
            validator.read_allowlisted_phase_c1_pair(
                self.candidate_root
            ),
            (result_bytes, report_bytes),
        )
        rejected_roots = (
            self.temp_root / "elsewhere",
            (
                os.fspath(self.candidate_root.parent)
                + os.sep
                + "."
                + os.sep
                + self.candidate_root.name
            ),
            (
                os.fspath(self.candidate_root)
                + os.sep
                + ".."
                + os.sep
                + self.candidate_root.name
            ),
        )
        for rejected in rejected_roots:
            with self.subTest(root=rejected):
                with self.assertRaises(validator.ValidationError):
                    validator.read_allowlisted_phase_c1_pair(rejected)
        extra = self.candidate_root / "extra.json"
        extra.write_bytes(b"{}")
        with self.assertRaises(validator.ValidationError):
            validator.read_allowlisted_phase_c1_pair(
                self.candidate_root
            )
        extra.unlink()
        (self.candidate_root / "result.json").write_bytes(
            b"x" * (validator.MAX_PAIR_FILE_BYTES + 1)
        )
        with self.assertRaises(validator.ValidationError):
            validator.read_allowlisted_phase_c1_pair(
                self.candidate_root
            )

    def test_pair_reader_rejects_reparse_and_descriptor_races(
        self,
    ) -> None:
        _payload, result_bytes, report_bytes = self.build_pair()
        self.candidate_root.mkdir(parents=True)
        result_path = self.candidate_root / "result.json"
        report_path = self.candidate_root / "report.md"
        result_path.write_bytes(result_bytes)
        report_path.write_bytes(report_bytes)
        real_lstat = os.lstat

        def linked_result(path: object) -> os.stat_result:
            metadata = real_lstat(path)
            if Path(path) == result_path:
                return mock.Mock(
                    **{
                        **{
                            name: getattr(metadata, name)
                            for name in (
                                "st_mode",
                                "st_dev",
                                "st_ino",
                                "st_size",
                                "st_mtime_ns",
                            )
                        },
                        "st_file_attributes": (
                            getattr(metadata, "st_file_attributes", 0)
                            | validator.REPARSE_POINT
                        ),
                    }
                )
            return metadata

        with mock.patch.object(validator.os, "lstat", side_effect=linked_result):
            with self.assertRaises(validator.ValidationError):
                validator.read_allowlisted_phase_c1_pair(
                    self.candidate_root
                )
        with mock.patch.object(
            validator,
            "_metadata_identity",
            side_effect=[
                (1, 1, 1, 1, 1),
                (2, 2, 2, 2, 2),
            ],
        ):
            with self.assertRaises(validator.ValidationError):
                validator.read_allowlisted_phase_c1_pair(
                    self.candidate_root
                )

    def test_tracked_reader_anchors_every_input_and_binding_parent(
        self,
    ) -> None:
        validator_path = (
            self.temp_root
            / "scripts"
            / "validate_emotion_state_004_phase_c1.py"
        )
        contracts_path = (
            self.temp_root
            / "scripts"
            / "emotion_state_phase_c1_contracts.py"
        )
        validator_path.parent.mkdir(parents=True, exist_ok=True)
        tracked_paths = (
            ("protocol", self.input_paths["PROTOCOL_PATH"]),
            ("search", self.input_paths["SEARCH_LEDGER_PATH"]),
            ("source", self.input_paths["SOURCE_LEDGER_PATH"]),
            ("review", self.input_paths["SOURCE_REVIEW_PATH"]),
            ("validator", validator_path),
            ("contracts", contracts_path),
        )
        for label, target in tracked_paths:
            with self.subTest(label=label):
                original_bytes = f"ORIGINAL {label}\n".encode("ascii")
                outside_bytes = f"OUTSIDE {label}\n".encode("ascii")
                target.write_bytes(original_bytes)
                parent = target.parent
                saved = parent.with_name(f"{parent.name}-{label}-saved")
                outside = parent.with_name(
                    f"{parent.name}-{label}-outside"
                )
                outside.mkdir()
                (outside / target.name).write_bytes(outside_bytes)
                state = {
                    "attempted": False,
                    "blocked": False,
                    "swapped": False,
                }

                def swap_parent() -> None:
                    state["attempted"] = True
                    try:
                        os.replace(parent, saved)
                    except OSError:
                        state["blocked"] = True
                        return
                    try:
                        os.replace(outside, parent)
                    except OSError:
                        os.replace(saved, parent)
                        state["blocked"] = True
                        return
                    state["swapped"] = True

                def restore_parent() -> None:
                    if state["swapped"]:
                        os.replace(parent, outside)
                        os.replace(saved, parent)
                        state["swapped"] = False

                real_safe_lstat = validator._safe_lstat
                real_child_metadata = (
                    validator._AnchoredDirectory.child_metadata
                )
                real_anchor_validate = validator._AnchoredDirectory.validate

                def raced_safe_lstat(
                    path: Path,
                    *,
                    missing_code: str,
                ) -> os.stat_result:
                    current = Path(path)
                    if current == target and not state["attempted"]:
                        swap_parent()
                    elif current == parent and state["swapped"]:
                        restore_parent()
                    return real_safe_lstat(
                        path,
                        missing_code=missing_code,
                    )

                def raced_child_metadata(
                    anchor: object,
                    name: str,
                ) -> os.stat_result:
                    if (
                        anchor.target == parent
                        and name == target.name
                        and not state["attempted"]
                    ):
                        swap_parent()
                    return real_child_metadata(anchor, name)

                def restore_then_validate(anchor: object) -> None:
                    if anchor.target == parent:
                        restore_parent()
                    real_anchor_validate(anchor)

                payload: bytes | None = None
                try:
                    with mock.patch.object(
                        validator,
                        "_safe_lstat",
                        side_effect=raced_safe_lstat,
                    ), mock.patch.object(
                        validator._AnchoredDirectory,
                        "child_metadata",
                        autospec=True,
                        side_effect=raced_child_metadata,
                    ), mock.patch.object(
                        validator._AnchoredDirectory,
                        "validate",
                        autospec=True,
                        side_effect=restore_then_validate,
                    ):
                        try:
                            payload = validator._read_exact_tracked_file(
                                target
                            )
                        except validator.ValidationError:
                            payload = None
                finally:
                    restore_parent()
                self.assertTrue(state["attempted"])
                if payload is not None:
                    self.assertEqual(payload, original_bytes)
                    self.assertNotEqual(payload, outside_bytes)

    def test_pair_reader_anchors_original_root_across_swap_and_restore(
        self,
    ) -> None:
        original_result = b"ORIGINAL result\n"
        original_report = b"ORIGINAL report\n"
        outside_result = b"OUTSIDE result\n"
        outside_report = b"OUTSIDE report\n"
        self.candidate_root.mkdir(parents=True)
        (self.candidate_root / "result.json").write_bytes(original_result)
        (self.candidate_root / "report.md").write_bytes(original_report)
        outside = self.candidate_root.with_name("candidate-outside")
        outside.mkdir()
        (outside / "result.json").write_bytes(outside_result)
        (outside / "report.md").write_bytes(outside_report)
        saved = self.candidate_root.with_name("candidate-original")
        state = {
            "attempted": False,
            "blocked": False,
            "swapped": False,
        }
        real_children = validator._AnchoredDirectory.bounded_children
        real_validate = validator._AnchoredDirectory.validate

        def swap_before_enumeration(
            anchor: object,
            maximum_children: int,
        ) -> tuple[str, ...]:
            state["attempted"] = True
            try:
                os.replace(self.candidate_root, saved)
            except OSError:
                state["blocked"] = True
                return real_children(anchor, maximum_children)
            try:
                os.replace(outside, self.candidate_root)
            except OSError:
                os.replace(saved, self.candidate_root)
                state["blocked"] = True
                return real_children(anchor, maximum_children)
            state["swapped"] = True
            return real_children(anchor, maximum_children)

        def restore_before_final_validation(anchor: object) -> None:
            if state["swapped"]:
                os.replace(self.candidate_root, outside)
                os.replace(saved, self.candidate_root)
                state["swapped"] = False
            real_validate(anchor)

        pair: tuple[bytes, bytes] | None = None
        try:
            with mock.patch.object(
                validator._AnchoredDirectory,
                "bounded_children",
                autospec=True,
                side_effect=swap_before_enumeration,
            ), mock.patch.object(
                validator._AnchoredDirectory,
                "validate",
                autospec=True,
                side_effect=restore_before_final_validation,
            ):
                try:
                    pair = validator.read_allowlisted_phase_c1_pair(
                        self.candidate_root
                    )
                except validator.ValidationError:
                    pair = None
        finally:
            if state["swapped"]:
                os.replace(self.candidate_root, outside)
                os.replace(saved, self.candidate_root)
                state["swapped"] = False
            elif saved.exists() and not self.candidate_root.exists():
                os.replace(saved, self.candidate_root)
        self.assertTrue(state["attempted"])
        if pair is not None:
            self.assertEqual(pair, (original_result, original_report))
            self.assertNotEqual(pair, (outside_result, outside_report))

    def test_pair_reader_stops_child_enumeration_after_third_entry(
        self,
    ) -> None:
        self.candidate_root.mkdir(parents=True)
        (self.candidate_root / "result.json").write_bytes(b"result\n")
        (self.candidate_root / "report.md").write_bytes(b"report\n")
        for index in range(10):
            (self.candidate_root / f"extra-{index:02d}").write_bytes(b"x")
        real_scandir = os.scandir
        next_calls = 0

        class CountingScandir:
            def __init__(self, path: object) -> None:
                self.inner = real_scandir(path)

            def __enter__(self) -> CountingScandir:
                self.inner.__enter__()
                return self

            def __exit__(self, *args: object) -> object:
                return self.inner.__exit__(*args)

            def __iter__(self) -> CountingScandir:
                return self

            def __next__(self) -> os.DirEntry[str]:
                nonlocal next_calls
                entry = next(self.inner)
                next_calls += 1
                return entry

        with mock.patch.object(
            validator.os,
            "scandir",
            side_effect=CountingScandir,
        ):
            with self.assertRaises(validator.ValidationError):
                validator.read_allowlisted_phase_c1_pair(
                    self.candidate_root
                )
        self.assertEqual(next_calls, 3)

    def test_cli_accepts_only_exact_sections_and_has_stable_output(
        self,
    ) -> None:
        sections = (
            "inputs",
            "projection",
            "candidate",
            "canonical",
            "checkpoint",
        )
        for section in sections:
            with self.subTest(section=section):
                self.assertEqual(
                    validator.parse_cli_args((section,)),
                    section,
                )
        for argv in (
            (),
            ("fetch",),
            ("INPUTS",),
            ("candidate", "--root", "elsewhere"),
            ("checkpoint", "--json"),
        ):
            with self.subTest(argv=argv):
                with self.assertRaises(validator.CliUsageError):
                    validator.parse_cli_args(argv)
        with mock.patch.object(
            validator,
            "_run_section",
            return_value=None,
        ):
            with mock.patch("sys.stdout") as stdout:
                self.assertEqual(validator.main(["inputs"]), 0)
                stdout.write.assert_any_call("inputs:pass")
        with mock.patch.object(
            validator,
            "_run_section",
            side_effect=validator.ValidationError("synthetic"),
        ):
            with mock.patch("sys.stderr") as stderr:
                self.assertEqual(validator.main(["inputs"]), 1)
                message = "".join(
                    str(call.args[0])
                    for call in stderr.write.call_args_list
                    if call.args
                )
                self.assertTrue(
                    message.startswith(
                        "EMOTION-STATE-004 Phase C1 validation failed:"
                    )
                )
                self.assertNotIn("Traceback", message)

    def test_cli_rejects_two_thousand_level_json_without_traceback(
        self,
    ) -> None:
        deeply_nested = (
            (b"[" * 2000)
            + b"0"
            + (b"]" * 2000)
            + b"\n"
        )
        self.input_paths["PROTOCOL_PATH"].write_bytes(deeply_nested)
        with mock.patch("sys.stderr") as stderr:
            self.assertEqual(validator.main(["inputs"]), 1)
            message = "".join(
                str(call.args[0])
                for call in stderr.write.call_args_list
                if call.args
            )
        self.assertTrue(
            message.startswith(
                "EMOTION-STATE-004 Phase C1 validation failed:"
            )
        )
        self.assertNotIn("Traceback", message)

    @staticmethod
    def git(
        root: Path,
        *arguments: str,
        check: bool = True,
    ) -> str:
        completed = subprocess.run(
            ["git", "-C", os.fspath(root), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env={
                **os.environ,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_OPTIONAL_LOCKS": "0",
            },
        )
        if check and completed.returncode != 0:
            raise AssertionError(
                f"git {' '.join(arguments)} failed: {completed.stderr}"
            )
        return completed.stdout.strip()

    def synthetic_lineage_repository(
        self,
        mutation: str | None = None,
    ) -> Path:
        repository = self.temp_root / f"lineage-{mutation or 'valid'}"
        repository.mkdir()
        self.git(repository, "init", "--quiet")
        self.git(repository, "config", "user.name", "Phase C1 Test")
        self.git(
            repository,
            "config",
            "user.email",
            "phase-c1-test@example.invalid",
        )
        authority = self.authority_bytes(
            admissible_signals=("confusion",)
        )
        paths = {
            "protocol_bytes": (
                repository
                / "research"
                / "experiments"
                / "configs"
                / "emotion-state-004-phase-c1-discovery-protocol.json"
            ),
            "search_ledger_bytes": (
                repository
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_search_ledger.json"
            ),
            "source_ledger_bytes": (
                repository
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_source_evidence_ledger.json"
            ),
            "review_receipt_bytes": (
                repository
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_source_review_receipt.json"
            ),
        }
        for name, path in paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(authority[name])
        validator_path = (
            repository
            / "scripts"
            / "validate_emotion_state_004_phase_c1.py"
        )
        validator_path.parent.mkdir(parents=True)
        validator_path.write_bytes(self.closed_validator_import_source())
        contracts_path = (
            repository
            / "scripts"
            / "emotion_state_phase_c1_contracts.py"
        )
        contracts_path.write_bytes(b"# synthetic contracts\n")
        self.git(repository, "add", ".")
        self.git(repository, "commit", "--quiet", "-m", "implementation")
        implementation_head = self.git(repository, "rev-parse", "HEAD")
        validator_blob = self.git(
            repository,
            "rev-parse",
            (
                f"{implementation_head}:"
                "scripts/validate_emotion_state_004_phase_c1.py"
            ),
        )
        if mutation == "intervening_parent":
            note = repository / "docs" / "note.md"
            note.parent.mkdir()
            note.write_text("intervening\n", encoding="utf-8", newline="\n")
            self.git(repository, "add", "docs/note.md")
            self.git(repository, "commit", "--quiet", "-m", "intervening")
        if mutation == "merge_pair":
            base_branch = self.git(
                repository,
                "symbolic-ref",
                "--short",
                "HEAD",
            )
            self.git(repository, "checkout", "--quiet", "-b", "side")
            self.git(
                repository,
                "commit",
                "--quiet",
                "--allow-empty",
                "-m",
                "side parent",
            )
            self.git(repository, "checkout", "--quiet", base_branch)
            self.git(
                repository,
                "merge",
                "--quiet",
                "--no-commit",
                "--no-ff",
                "side",
            )
        result, result_bytes, report_bytes = self.build_pair(
            authority,
            head_commit=(
                "0" * 40
                if mutation == "wrong_implementation_head"
                else implementation_head
            ),
            validator_blob_id=validator_blob,
        )
        canonical = (
            repository
            / "research"
            / "experiments"
            / "generated"
            / (
                "EMOTION-STATE-004-phase-c1-operational-signal-"
                "evidence-admission"
            )
        )
        canonical.mkdir(parents=True)
        (canonical / "result.json").write_bytes(result_bytes)
        if mutation == "split_pair":
            self.git(repository, "add", os.fspath(canonical / "result.json"))
            self.git(repository, "commit", "--quiet", "-m", "result only")
        (canonical / "report.md").write_bytes(report_bytes)
        if mutation in {
            "precommit_one_staged",
            "precommit_both_staged",
        }:
            candidate = (
                repository
                / ".tmp"
                / "emotion-state-004-phase-c1"
                / "candidate"
            )
            candidate.mkdir(parents=True)
            (candidate / "result.json").write_bytes(result_bytes)
            (candidate / "report.md").write_bytes(report_bytes)
            self.git(
                repository,
                "add",
                os.fspath(canonical / "result.json"),
            )
            if mutation == "precommit_both_staged":
                self.git(
                    repository,
                    "add",
                    os.fspath(canonical / "report.md"),
                )
            return repository
        if mutation == "extra_pair_path":
            extra = repository / "extra.txt"
            extra.write_text("extra\n", encoding="utf-8", newline="\n")
        self.git(repository, "add", ".")
        self.git(repository, "commit", "--quiet", "-m", "pair")
        if mutation == "result_blob_drift":
            result["overall_decision"] = "stop_c2"
            self.reself(result)
            (canonical / "result.json").write_bytes(
                phase_c1.canonical_json_bytes(result)
            )
            self.git(repository, "add", os.fspath(canonical / "result.json"))
            self.git(repository, "commit", "--quiet", "-m", "drift result")
        if mutation == "input_rebound":
            paths["protocol_bytes"].write_bytes(
                paths["protocol_bytes"].read_bytes() + b" "
            )
            self.git(repository, "add", os.fspath(paths["protocol_bytes"]))
            self.git(repository, "commit", "--quiet", "-m", "rebind input")
        if mutation == "validator_rebound":
            validator_path.write_bytes(b"# rebound validator\n")
            self.git(repository, "add", os.fspath(validator_path))
            self.git(repository, "commit", "--quiet", "-m", "rebind validator")
        if mutation == "validator_worktree_dirty":
            validator_path.write_bytes(b"# dirty validator\n")
        if mutation == "contracts_rebound":
            contracts_path.write_bytes(b"# rebound contracts\n")
            self.git(repository, "add", os.fspath(contracts_path))
            self.git(
                repository,
                "commit",
                "--quiet",
                "-m",
                "rebind contracts",
            )
        if mutation == "contracts_worktree_dirty":
            contracts_path.write_bytes(b"# dirty contracts\n")
        if mutation == "pair_mode_drift":
            self.git(
                repository,
                "update-index",
                "--chmod=+x",
                os.fspath(canonical / "report.md"),
            )
            self.git(repository, "commit", "--quiet", "-m", "drift mode")
        if mutation == "pair_index_mode_staged":
            self.git(
                repository,
                "update-index",
                "--chmod=+x",
                os.fspath(canonical / "report.md"),
            )
        if mutation == "pair_index_deleted":
            self.git(
                repository,
                "rm",
                "--cached",
                "--quiet",
                os.fspath(canonical / "report.md"),
            )
        if mutation == "doc_descendant":
            note = repository / "docs" / "closeout.md"
            note.parent.mkdir(exist_ok=True)
            note.write_text("closeout\n", encoding="utf-8", newline="\n")
            self.git(repository, "add", "docs/closeout.md")
            self.git(repository, "commit", "--quiet", "-m", "closeout")
        return repository

    def patch_repository_paths(
        self,
        repository: Path,
    ) -> mock._patch:
        return mock.patch.multiple(
            validator,
            create=True,
            ROOT=repository,
            PROTOCOL_PATH=(
                repository
                / "research"
                / "experiments"
                / "configs"
                / "emotion-state-004-phase-c1-discovery-protocol.json"
            ),
            SEARCH_LEDGER_PATH=(
                repository
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_search_ledger.json"
            ),
            SOURCE_LEDGER_PATH=(
                repository
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_source_evidence_ledger.json"
            ),
            SOURCE_REVIEW_PATH=(
                repository
                / "research"
                / "sources"
                / "emotion_state"
                / "phase_c1_source_review_receipt.json"
            ),
            VALIDATOR_PATH=(
                repository
                / "scripts"
                / "validate_emotion_state_004_phase_c1.py"
            ),
            CONTRACTS_PATH=(
                repository
                / "scripts"
                / "emotion_state_phase_c1_contracts.py"
            ),
            CANDIDATE_ROOT=(
                repository
                / ".tmp"
                / "emotion-state-004-phase-c1"
                / "candidate"
            ),
            CANONICAL_ROOT=(
                repository
                / "research"
                / "experiments"
                / "generated"
                / (
                    "EMOTION-STATE-004-phase-c1-operational-signal-"
                    "evidence-admission"
                )
            ),
        )

    def test_precommit_rejects_one_or_both_staged_canonical_files(
        self,
    ) -> None:
        for mutation in (
            "precommit_one_staged",
            "precommit_both_staged",
        ):
            with self.subTest(mutation=mutation):
                repository = self.synthetic_lineage_repository(mutation)
                candidate = (
                    repository
                    / ".tmp"
                    / "emotion-state-004-phase-c1"
                    / "candidate"
                )
                with self.patch_repository_paths(repository):
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_phase_c1_pair(candidate)

    def test_git_cleans_up_after_thread_setup_failures(self) -> None:
        scenarios = (
            ("first_constructor", 0, None, ()),
            ("second_constructor", 1, None, ()),
            ("first_start", None, 0, ()),
            ("second_start", None, 1, (0,)),
        )
        for (
            label,
            failing_constructor,
            failing_start,
            expected_joined,
        ) in scenarios:
            with self.subTest(label=label):
                process = mock.Mock()
                process.stdout = mock.Mock()
                process.stderr = mock.Mock()
                process.wait.return_value = -1
                threads = (mock.Mock(), mock.Mock())
                for thread in threads:
                    thread.is_alive.return_value = False
                if failing_start is not None:
                    threads[failing_start].start.side_effect = RuntimeError(
                        label
                    )

                thread_results: list[object] = list(threads)
                if failing_constructor is not None:
                    thread_results[failing_constructor] = RuntimeError(label)

                with mock.patch.object(
                    validator.subprocess,
                    "Popen",
                    return_value=process,
                ), mock.patch.object(
                    validator.threading,
                    "Thread",
                    side_effect=thread_results,
                ):
                    with self.assertRaisesRegex(
                        validator.ValidationError,
                        "git_execution",
                    ):
                        validator._git(self.temp_root, "status")

                process.kill.assert_called_once_with()
                process.wait.assert_called_once_with(timeout=2)
                process.stdout.close.assert_called_once_with()
                process.stderr.close.assert_called_once_with()
                for index, thread in enumerate(threads):
                    if index in expected_joined:
                        thread.join.assert_called_once_with(timeout=2)
                    else:
                        thread.join.assert_not_called()

    def test_git_reaps_after_initial_wait_error(self) -> None:
        process = mock.Mock()
        process.stdout = mock.Mock()
        process.stderr = mock.Mock()
        process.wait.side_effect = (OSError("initial wait"), -1)
        threads = (mock.Mock(), mock.Mock())
        for thread in threads:
            thread.is_alive.return_value = False

        with mock.patch.object(
            validator.subprocess,
            "Popen",
            return_value=process,
        ), mock.patch.object(
            validator.threading,
            "Thread",
            side_effect=threads,
        ):
            with self.assertRaisesRegex(
                validator.ValidationError,
                "git_execution",
            ):
                validator._git(self.temp_root, "status")

        self.assertEqual(
            process.wait.call_args_list,
            [
                mock.call(timeout=15),
                mock.call(timeout=2),
            ],
        )
        process.kill.assert_called_once_with()
        process.stdout.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()
        for thread in threads:
            thread.join.assert_called_once_with(timeout=2)

    def test_git_capture_is_bounded_for_large_blobs_and_stderr(
        self,
    ) -> None:
        repository = self.temp_root / "bounded-git"
        repository.mkdir()
        self.git(repository, "init", "--quiet")
        large_blob = repository / "large.bin"
        large_blob.write_bytes(b"x" * (4 * 1024 * 1024))
        object_id = self.git(
            repository,
            "hash-object",
            "-w",
            os.fspath(large_blob),
        )
        with mock.patch.object(
            validator.subprocess,
            "run",
            side_effect=AssertionError("unbounded subprocess.run used"),
        ):
            with self.assertRaises(validator.ValidationError):
                validator._blob_bytes(
                    repository,
                    object_id,
                    maximum_bytes=1024,
                )
        with self.assertRaises(validator.ValidationError):
            validator._git(
                repository,
                "cat-file",
                "blob",
                "z" * 4096,
                expected_codes=(128,),
                maximum_output_bytes=1024,
            )

    def test_repository_alternates_reject_before_git_and_worktrees_pass(
        self,
    ) -> None:
        donor = self.temp_root / "alternates-donor"
        donor.mkdir()
        self.git(donor, "init", "--quiet")
        donor_object_directory = donor / ".git" / "objects"

        consumer = self.temp_root / "alternates-consumer"
        consumer.mkdir()
        self.git(consumer, "init", "--quiet")
        alternates = consumer / ".git" / "objects" / "info" / "alternates"
        alternates.parent.mkdir(parents=True, exist_ok=True)
        alternates.write_text(
            os.fspath(donor_object_directory) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        with mock.patch.object(validator, "ROOT", consumer):
            with mock.patch.object(
                validator,
                "_git",
                side_effect=AssertionError("Git ran before alternates check"),
            ):
                with self.assertRaises(validator.ValidationError):
                    validator._verify_repository_root(consumer)

        primary = self.temp_root / "worktree-primary"
        primary.mkdir()
        self.git(primary, "init", "--quiet")
        self.git(primary, "config", "user.name", "Phase C1 Test")
        self.git(
            primary,
            "config",
            "user.email",
            "phase-c1-test@example.invalid",
        )
        marker = primary / "marker.txt"
        marker.write_text("marker\n", encoding="utf-8", newline="\n")
        self.git(primary, "add", "marker.txt")
        self.git(primary, "commit", "--quiet", "-m", "worktree base")
        worktree = self.temp_root / "linked-worktree"
        self.git(
            primary,
            "worktree",
            "add",
            "--quiet",
            "--detach",
            os.fspath(worktree),
        )
        expected_head = self.git(worktree, "rev-parse", "HEAD")
        with mock.patch.object(validator, "ROOT", worktree):
            verified_root, live_head = validator._verify_repository_root(
                worktree
            )
        self.assertEqual(verified_root, worktree)
        self.assertEqual(live_head, expected_head)

    def test_checkpoint_lineage_rejects_non_pair_parent_or_descendant_rebinding(
        self,
    ) -> None:
        valid = self.synthetic_lineage_repository()
        with self.patch_repository_paths(valid):
            validator.validate_checkpoint_lineage(valid)
        descendant = self.synthetic_lineage_repository("doc_descendant")
        with self.patch_repository_paths(descendant):
            validator.validate_checkpoint_lineage(descendant)
        for mutation in (
            "wrong_implementation_head",
            "intervening_parent",
            "merge_pair",
            "split_pair",
            "extra_pair_path",
            "result_blob_drift",
            "input_rebound",
            "validator_rebound",
            "validator_worktree_dirty",
            "contracts_rebound",
            "contracts_worktree_dirty",
            "pair_mode_drift",
            "pair_index_mode_staged",
            "pair_index_deleted",
        ):
            with self.subTest(mutation=mutation):
                repository = self.synthetic_lineage_repository(mutation)
                with self.patch_repository_paths(repository):
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_checkpoint_lineage(repository)

    def test_candidate_json_rejects_self_consistent_uncommitted_head_and_validator_blob(
        self,
    ) -> None:
        for mutation in (
            "implementation_head",
            "validator_blob_id",
        ):
            with self.subTest(mutation=mutation):
                repository = self.synthetic_lineage_repository(
                    f"candidate_{mutation}",
                )
                canonical = (
                    repository
                    / "research"
                    / "experiments"
                    / "generated"
                    / (
                        "EMOTION-STATE-004-phase-c1-operational-signal-"
                        "evidence-admission"
                    )
                )
                committed_result = phase_c1.load_json_strict(
                    (canonical / "result.json").read_bytes(),
                    source="committed_result",
                )
                self.assertIsInstance(committed_result, dict)
                implementation_head = committed_result[
                    "implementation_head"
                ]
                validator_blob_id = committed_result["validator_blob_id"]
                self.assertIsInstance(implementation_head, str)
                self.assertIsInstance(validator_blob_id, str)
                self.git(
                    repository,
                    "reset",
                    "--hard",
                    implementation_head,
                )

                authority = self.authority_bytes(
                    admissible_signals=("confusion",),
                )
                candidate_head = (
                    "0" * 40
                    if mutation == "implementation_head"
                    else implementation_head
                )
                candidate_validator_blob = (
                    "0" * 40
                    if mutation == "validator_blob_id"
                    else validator_blob_id
                )
                (
                    _result,
                    result_bytes,
                    report_bytes,
                ) = self.build_pair(
                    authority,
                    head_commit=candidate_head,
                    validator_blob_id=candidate_validator_blob,
                )
                candidate_root = (
                    repository
                    / ".tmp"
                    / "emotion-state-004-phase-c1"
                    / "candidate"
                )
                candidate_root.mkdir(parents=True)
                (candidate_root / "result.json").write_bytes(
                    result_bytes,
                )
                (candidate_root / "report.md").write_bytes(
                    report_bytes,
                )

                candidate_receipt: dict[str, object] = {
                    "schema_version": (
                        "EmotionStatePhaseC1CandidateReceiptV1"
                    ),
                    "checkpoint_id": validator.CHECKPOINT_ID,
                    "transaction_id": "",
                    "status": "candidate_ready",
                    "implementation_head": candidate_head,
                    "validator_blob_id": candidate_validator_blob,
                    "protocol_sha256": hashlib.sha256(
                        authority["protocol_bytes"],
                    ).hexdigest(),
                    "search_ledger_sha256": hashlib.sha256(
                        authority["search_ledger_bytes"],
                    ).hexdigest(),
                    "source_evidence_ledger_sha256": hashlib.sha256(
                        authority["source_ledger_bytes"],
                    ).hexdigest(),
                    "source_review_receipt_sha256": hashlib.sha256(
                        authority["review_receipt_bytes"],
                    ).hexdigest(),
                    "result_sha256": hashlib.sha256(
                        result_bytes,
                    ).hexdigest(),
                    "report_sha256": hashlib.sha256(
                        report_bytes,
                    ).hexdigest(),
                }
                candidate_receipt["transaction_id"] = hashlib.sha256(
                    phase_c1.canonical_json_bytes(candidate_receipt),
                ).hexdigest()[:32]
                receipt_path = (
                    candidate_root.parent / "candidate-receipt.json"
                )
                receipt_path.write_bytes(
                    phase_c1.canonical_json_bytes(candidate_receipt),
                )

                class BinaryOnlyStdout:
                    def __init__(self) -> None:
                        self.buffer = io.BytesIO()

                    def write(self, value: object) -> int:
                        raise AssertionError(
                            "candidate --json must not use text stdout"
                        )

                    def flush(self) -> None:
                        return None

                stdout = BinaryOnlyStdout()
                with self.patch_repository_paths(repository), mock.patch.object(
                    sys,
                    "stdout",
                    stdout,
                ), mock.patch.object(sys, "stderr"):
                    exit_code = validator.main(
                        ("candidate", "--json"),
                    )

                self.assertEqual(
                    exit_code,
                    1,
                    msg=(
                        "candidate --json accepted self-consistent "
                        f"uncommitted {mutation}"
                    ),
                )
                self.assertEqual(
                    stdout.buffer.getvalue(),
                    b"",
                    msg=(
                        "candidate --json emitted a pass receipt for "
                        f"uncommitted {mutation}"
                    ),
                )


class PhaseC1Task10ReviewProcedureTests(unittest.TestCase):
    """Execute the frozen Task 10 review procedure only in a synthetic root."""

    _PLAN_PATH = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / (
            "2026-07-26-emotion-state-phase-c1-operational-signal-"
            "evidence-admission.md"
        )
    )
    _SYNTHETIC_VALIDATION_SHA256 = (
        "0f666497c55c617de0c1dc988883de9906a28cb8d7c024a7e8b83926a1ca263e"
    )
    _CANDIDATE_RECEIPT_FIELDS = frozenset(
        {
            "schema_version",
            "checkpoint_id",
            "transaction_id",
            "status",
            "implementation_head",
            "validator_blob_id",
            "protocol_sha256",
            "search_ledger_sha256",
            "source_evidence_ledger_sha256",
            "source_review_receipt_sha256",
            "result_sha256",
            "report_sha256",
        }
    )
    _VALIDATION_RECEIPT_FIELDS = frozenset(
        {
            "schema_version",
            "checkpoint_id",
            "implementation_head",
            "candidate_transaction_id",
            "candidate_result_sha256",
            "candidate_report_sha256",
            "protocol_sha256",
            "search_ledger_sha256",
            "source_evidence_ledger_sha256",
            "source_review_receipt_sha256",
            "validator_blob_id",
            "verdict",
            "runtime_approved",
        }
    )

    @classmethod
    def _step_6_review_block(cls) -> str:
        task_10 = cls._PLAN_PATH.read_text(encoding="utf-8").split(
            "- [ ] **Step 6: Independently review the candidate**",
            1,
        )[1]
        start = task_10.index('$ErrorActionPreference = "Stop"')
        end = task_10.index("\n```", start)
        return task_10[start:end]

    def test_step_6_review_block_writes_lowercase_canonical_receipt(self) -> None:
        """A raw Get-FileHash value must not enter the canonical review receipt."""
        powershell = (
            Path(os.environ.get("WINDIR", r"C:\Windows"))
            / "System32"
            / "WindowsPowerShell"
            / "v1.0"
            / "powershell.exe"
        )
        if not powershell.is_file():
            self.skipTest("Windows PowerShell 5.1 executable is unavailable")
        version = subprocess.run(
            [
                os.fspath(powershell),
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "$PSVersionTable.PSVersion.ToString()",
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        if version.returncode != 0 or not version.stdout.strip().startswith("5.1."):
            self.skipTest("Windows PowerShell 5.1 is unavailable")

        with tempfile.TemporaryDirectory(
            prefix="emotion-state-c1-task-10-review-procedure-",
        ) as temp_directory:
            synthetic_root = Path(temp_directory)
            ignored_root = synthetic_root / ".tmp" / "emotion-state-004-phase-c1"
            ignored_root.mkdir(parents=True)
            candidate_receipt = {
                "schema_version": "EmotionStatePhaseC1CandidateReceiptV1",
                "checkpoint_id": (
                    "EMOTION-STATE-004-phase-c1-operational-signal-evidence-"
                    "admission"
                ),
                "transaction_id": "",
                "status": "candidate_ready",
                "implementation_head": "d" * 40,
                "validator_blob_id": "e" * 40,
                "protocol_sha256": "f" * 64,
                "search_ledger_sha256": "1" * 64,
                "source_evidence_ledger_sha256": "2" * 64,
                "source_review_receipt_sha256": "3" * 64,
                "report_sha256": "b" * 64,
                "result_sha256": "a" * 64,
            }
            candidate_receipt["transaction_id"] = hashlib.sha256(
                phase_c1.canonical_json_bytes(candidate_receipt),
            ).hexdigest()[:32]
            candidate_receipt_bytes = phase_c1.canonical_json_bytes(candidate_receipt)
            self.assertEqual(set(candidate_receipt), self._CANDIDATE_RECEIPT_FIELDS)
            self.assertEqual(
                validator._canonical_candidate_receipt(candidate_receipt_bytes),
                candidate_receipt,
            )
            (ignored_root / "candidate-receipt.json").write_bytes(candidate_receipt_bytes)
            validation_payload = {
                "schema_version": "EmotionStatePhaseC1CandidateValidationV1",
                "checkpoint_id": candidate_receipt["checkpoint_id"],
                "implementation_head": candidate_receipt["implementation_head"],
                "candidate_transaction_id": candidate_receipt["transaction_id"],
                "candidate_result_sha256": candidate_receipt["result_sha256"],
                "candidate_report_sha256": candidate_receipt["report_sha256"],
                "protocol_sha256": candidate_receipt["protocol_sha256"],
                "search_ledger_sha256": candidate_receipt["search_ledger_sha256"],
                "source_evidence_ledger_sha256": candidate_receipt[
                    "source_evidence_ledger_sha256"
                ],
                "source_review_receipt_sha256": candidate_receipt[
                    "source_review_receipt_sha256"
                ],
                "validator_blob_id": candidate_receipt["validator_blob_id"],
                "verdict": "pass",
                "runtime_approved": False,
            }
            validation_bytes = phase_c1.canonical_json_bytes(validation_payload)
            (ignored_root / "candidate-validation.json").write_bytes(validation_bytes)
            validation_payload = phase_c1.load_json_strict(
                validation_bytes,
                source="synthetic_candidate_validation",
            )
            self.assertIsInstance(validation_payload, dict)
            self.assertEqual(set(validation_payload), self._VALIDATION_RECEIPT_FIELDS)
            self.assertEqual(
                phase_c1.canonical_json_bytes(validation_payload),
                validation_bytes,
            )
            self.assertEqual(
                hashlib.sha256(validation_bytes).hexdigest(),
                self._SYNTHETIC_VALIDATION_SHA256,
            )
            procedure_path = synthetic_root / "task-10-step-6.ps1"
            procedure_path.write_text(
                self._step_6_review_block(), encoding="utf-8", newline="\n",
            )
            completed = subprocess.run(
                [
                    os.fspath(powershell),
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    os.fspath(procedure_path),
                ],
                cwd=synthetic_root,
                capture_output=True,
                check=False,
                text=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                msg=(
                    "the extracted Task 10 Step 6 procedure failed: "
                    f"stdout={completed.stdout!r}; stderr={completed.stderr!r}"
                ),
            )
            review_stage = ignored_root / "candidate-review.stage"
            review_path = ignored_root / "candidate-review.json"
            self.assertFalse(review_stage.exists())
            self.assertTrue(review_path.is_file())
            expected_payload = {
                "candidate_report_sha256": "b" * 64,
                "candidate_result_sha256": "a" * 64,
                "candidate_transaction_id": candidate_receipt["transaction_id"],
                "candidate_validation_sha256": self._SYNTHETIC_VALIDATION_SHA256,
                "checkpoint_id": (
                    "EMOTION-STATE-004-phase-c1-operational-signal-evidence-"
                    "admission"
                ),
                "critical_findings": 0,
                "implementation_head": "d" * 40,
                "important_findings": 0,
                "minor_findings": 0,
                "model_evaluation_run": False,
                "private_data_read": False,
                "provider_accessed": False,
                "raw_rows_read": False,
                "review_scope": (
                    "all_candidate_inputs_decisions_pair_report_and_boundaries"
                ),
                "runtime_modified": False,
                "schema_version": "EmotionStatePhaseC1CandidateReviewV1",
                "verdict": "admitted",
            }
            expected_bytes = (
                json.dumps(expected_payload, ensure_ascii=True, indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8")
            actual_bytes = review_path.read_bytes()
            self.assertEqual(actual_bytes, expected_bytes)
            self.assertEqual(
                json.loads(actual_bytes)["candidate_validation_sha256"],
                self._SYNTHETIC_VALIDATION_SHA256,
            )


class PhaseC1CloseoutDocumentationTests(unittest.TestCase):
    """Keep the C1 closeout anchored to the accepted canonical checkpoint."""

    _CLOSEOUT_PATHS = (
        ROOT
        / "research"
        / "experiments"
        / "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission.md",
        ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md",
        ROOT / "docs" / "thesis" / "ROADMAP.md",
        ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md",
        ROOT / "docs" / "product" / "COMMANDS.md",
    )
    _COMMON_ANCHORS = (
        "Canonical status: accepted",
        "Overall decision: defer_c2",
        "hesitation=defer",
        "frustration=defer",
        "confusion=defer",
        "interest=defer",
        "disengagement=defer",
        "C2-eligible signals: none",
        "queries=88; sources=0; cards=0",
        "2540A1BA430F78B9F660BA466F6CFD7099CFFCAA6F1C1D1AC373F4BA1D4D2CCD",
        "A6FCAA50123E4D67FF92D36E9755B4ED7C82306FCAA50B72ED26A478361365DB",
        "81FB1301287F0E3E8FA0E21840B1B596028509C11FAAC75D6D6F8914051D0B58",
        "4B489D77BFC948B84F8A6BC73A30DC1068138D6ABD2A563EB7FD43BFE9224E11",
        "3B8D9F874990C9C2FBE1664FE1155392984D278FFB4F5E9BB74913469F8D0336",
        "8F9B8D1EB088CC7025F77F34FF83928C53DA2112A0A0D300E59DD5C7A7C3D637",
        "15B5285A8B18E9E8C5A36A71CBB8202EF0F72370C91F9CB8AD80271F8BF38CDD",
        "d1f78f321f4d01512944dfa7499d819cb10d7a5c",
        "Source review: admitted (C0/I0/M0)",
        "Candidate review: admitted (C0/I0/M0)",
        "No private data, dataset/annotation rows, audio, or transcripts were read.",
        (
            "No provider access, call, simulation, model evaluation, "
            "runtime modification/activation, or Phase B lockbox access occurred."
        ),
    )

    def test_closeout_documents_bind_the_accepted_canonical_outcome(self) -> None:
        """Every closeout surface must carry the same accepted checkpoint anchors."""
        for path in self._CLOSEOUT_PATHS:
            text = " ".join(path.read_text(encoding="utf-8").split())
            for anchor in self._COMMON_ANCHORS:
                with self.subTest(path=path, anchor=anchor):
                    self.assertIn(anchor, text)

    def test_command_map_exposes_only_read_only_c1_validation(self) -> None:
        """The C1 command section cannot preserve a reusable accept operation."""
        commands = (ROOT / "docs" / "product" / "COMMANDS.md").read_text(
            encoding="utf-8",
        )
        heading = "## EMOTION-STATE-004 Phase C1 Evidence Admission"
        self.assertIn(heading, commands)
        section = commands.split(heading, 1)[1].split("\n## ", 1)[0]
        self.assertIn(
            "python scripts/validate_emotion_state_004_phase_c1.py checkpoint",
            section,
        )
        command_blocks = "\n".join(
            re.findall(r"```(?:powershell)?\\n(.*?)```", section, flags=re.DOTALL),
        ).lower()
        self.assertNotIn("run_emotion_state_004_phase_c1.py accept", command_blocks)
        self.assertNotIn("fetch", command_blocks)
        self.assertNotIn("provider", command_blocks)
        self.assertNotIn("simulation", command_blocks)
        self.assertNotIn("runtime", command_blocks)

    def test_closeout_docs_reject_stale_and_unauthorized_claims(self) -> None:
        """Closeout records a defer only; it cannot claim C2 or runtime authority."""
        forbidden = (
            "source discovery not run",
            "customer emotion was inferred",
            "authorizes C2",
            "runtime is authorized",
            "production ready",
        )
        for path in self._CLOSEOUT_PATHS:
            text = path.read_text(encoding="utf-8").lower()
            for phrase in forbidden:
                with self.subTest(path=path, phrase=phrase):
                    self.assertNotIn(phrase.lower(), text)


if __name__ == "__main__":
    unittest.main()
