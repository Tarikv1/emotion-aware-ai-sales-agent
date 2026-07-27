from __future__ import annotations

import copy
import hashlib
import json
import unittest
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Callable

import scripts.emotion_state_phase_c1_contracts as phase_c1


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SIGNALS = (
    "hesitation",
    "frustration",
    "confusion",
    "interest",
    "disengagement",
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

Protocol frozen; source discovery not run.

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
        for rule in EXPECTED_GITATTRIBUTES_RULES:
            self.assertEqual(attribute_lines.count(rule), 1)
        self.assertFalse(
            any(
                "emotion-state-004-phase-c1" in line and "*" in line
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

    def test_discovery_endpoint_registry_entry_remains_exactly_plan_only(
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

- Type: planned public scholarly/dataset discovery metadata
- Sources:
  - https://api.openalex.org/works
  - https://api.crossref.org/works
  - https://zenodo.org/api/records
  - https://huggingface.co/api/datasets
- Project use: Phase C1 discovery seed only.
- Current status: not accessed; plan only.
- Thesis caution: discovery-service results are not authoritative source evidence and cannot admit a signal."""
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
        )
        for host in rejected_hosts:
            with self.subTest(host=host):
                payload = self.valid_transport_receipt()
                payload["requested_url"] = _https(f"{host}/source")
                with self.assertRaises(phase_c1.PhaseC1ContractError):
                    phase_c1.parse_transport_receipt(payload)

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


if __name__ == "__main__":
    unittest.main()
