from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from types import MappingProxyType
from typing import Final
from urllib.parse import parse_qsl, unquote_to_bytes, urlsplit


class PhaseC1ContractError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise PhaseC1ContractError("json_nonfinite")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PhaseC1ContractError("json_duplicate_key")
        result[key] = value
    return result


def load_json_strict(data: bytes, *, source: str) -> object:
    try:
        return json.loads(
            data.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PhaseC1ContractError(f"{source}_json") from exc


@dataclass(frozen=True, slots=True)
class PhaseC1ProtocolV1:
    checkpoint_id: str
    protocol_id: str
    target_signals: tuple[str, ...]
    signal_constructs: tuple[Mapping[str, object], ...]
    construct_correspondence_order: tuple[str, ...]
    observer_method_order: tuple[str, ...]
    annotation_modality_order: tuple[str, ...]
    temporal_unit_order: tuple[str, ...]
    source_channels: tuple[Mapping[str, object], ...]
    query_templates: tuple[str, ...]
    expected_seed_query_count: int
    fallback_material_query_templates: tuple[str, ...]
    expected_fallback_material_query_count: int
    expected_total_query_count: int
    max_detailed_candidates_per_signal: int
    max_detailed_fallback_material_candidates: int
    citation_hop_depth: int
    max_backward_citations_per_signal: int
    max_forward_citations_per_signal: int
    max_response_bytes_by_transport_purpose: Mapping[str, int]
    allowed_response_content_types_by_transport_purpose: Mapping[
        str,
        tuple[str, ...],
    ]
    max_total_source_cache_bytes: int
    allowed_url_schemes: tuple[str, ...]
    seed_discovery_domains: tuple[str, ...]
    blocked_browser_modes: tuple[str, ...]
    candidate_status_order: tuple[str, ...]
    signal_decision_order: tuple[str, ...]
    overall_decision_order: tuple[str, ...]
    reason_code_order: tuple[str, ...]
    reliability_scale: int
    reliability_rules: tuple[Mapping[str, int | str], ...]
    positive_support_rule: Mapping[str, int | str]
    annotation_fallback_protocol: Mapping[str, object]
    failure_guards: Mapping[str, bool]
    canonical_json: Mapping[str, bool | int | str]


@dataclass(frozen=True, slots=True)
class PhaseC1TransportReceiptV1:
    receipt_id: str
    purpose: str
    request_key: str
    retrieved_at_utc: str
    requested_url: str
    final_url: str | None
    outcome: str
    incomplete_reason: str | None
    http_status_code: int | None
    redirect_hop_count: int
    redirect_chain: tuple[str, ...]
    response_sha256: str | None
    response_byte_count: int | None
    response_content_type: str | None


@dataclass(frozen=True, slots=True)
class PhaseC1TransportReceiptLedgerV1:
    protocol_sha256: str
    receipts: tuple[PhaseC1TransportReceiptV1, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1DiscoveryRecordV1:
    discovery_record_id: str
    query_id: str
    rank: int
    identity_sha256: str
    disposition: str
    candidate_source_id: str | None
    duplicate_of_discovery_record_id: str | None
    reason_code: str | None
    documentation_transport_receipt_sha256s: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1QueryRecordV1:
    query_id: str
    query_kind: str
    channel_id: str
    signal: str | None
    query_text: str
    status: str
    incomplete_reason: str | None
    result_limit: int
    response_sha256: str | None
    response_byte_count: int | None
    transport_receipt_sha256: str
    result_count: int
    returned_count: int
    truncated: bool
    discovery_records: tuple[PhaseC1DiscoveryRecordV1, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1CitationRecordV1:
    citation_record_id: str
    signal: str
    direction: str
    rank: int
    parent_source_id: str
    parent_source_document_sha256: str
    transport_receipt_sha256: str
    identity_sha256: str
    disposition: str
    candidate_source_id: str | None
    duplicate_of_record_id: str | None
    reason_code: str | None
    documentation_transport_receipt_sha256s: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1SearchLedgerV1:
    protocol_sha256: str
    query_records: tuple[PhaseC1QueryRecordV1, ...]
    citation_records: tuple[PhaseC1CitationRecordV1, ...]
    candidate_order_by_signal: Mapping[str, tuple[str, ...]]
    overflow_count_by_signal: Mapping[str, int]
    fallback_material_candidate_order: tuple[str, ...]
    fallback_material_overflow_count: int
    backward_citation_count_by_signal: Mapping[str, int]
    forward_citation_count_by_signal: Mapping[str, int]
    backward_citation_stop_by_signal: Mapping[str, str]
    forward_citation_stop_by_signal: Mapping[str, str]
    citation_transport_receipt_sha256s_by_signal: Mapping[
        str,
        Mapping[str, tuple[str, ...]],
    ]
    fail_ready_by_signal: Mapping[str, bool]
    search_complete: bool


TARGET_SIGNALS: Final = (
    "hesitation",
    "frustration",
    "confusion",
    "interest",
    "disengagement",
)
TRANSPORT_PURPOSES: Final = (
    "seed_query",
    "citation_discovery",
    "authoritative_document",
)
TRANSPORT_OUTCOMES: Final = ("complete", "incomplete")
TRANSPORT_INCOMPLETE_REASONS: Final = (
    "authentication_required",
    "captcha_or_antibot",
    "terms_or_cost",
    "private_address_or_redirect",
    "unapproved_redirect",
    "rate_limit_pressure",
    "network_error",
    "response_too_large",
    "cache_budget_exhausted",
    "invalid_response",
    "source_documentation_incomplete",
)

_FROZEN_PROTOCOL_SHA256: Final = (
    "2540A1BA430F78B9F660BA466F6CFD7099CFFCAA6F1C1D1AC373F4BA1D4D2CCD"
)
_CHECKPOINT_ID: Final = (
    "EMOTION-STATE-004-phase-c1-operational-signal-evidence-admission"
)
_PROTOCOL_ID: Final = "emotion-state-phase-c1-discovery-v1"
_PROTOCOL_SCHEMA: Final = "EmotionStatePhaseC1DiscoveryProtocolV1"
_RECEIPT_SCHEMA: Final = "EmotionStatePhaseC1TransportReceiptV1"
_LEDGER_SCHEMA: Final = "EmotionStatePhaseC1TransportReceiptLedgerV1"
_SHA256_RE: Final = re.compile(r"^[0-9A-F]{64}$")
_RECEIPT_ID_RE: Final = re.compile(r"^c1-transport-[0-9]{4}$")
_TIMESTAMP_RE: Final = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_SEED_REQUEST_RE: Final = re.compile(
    r"^c1-query-(?:"
    r"(?:hesitation|frustration|confusion|interest|disengagement)-"
    r"(?:openalex|crossref|zenodo|huggingface)-0[1-4]"
    r"|fallback-material-(?:openalex|crossref|zenodo|huggingface)-0[1-2]"
    r")$"
)
_CITATION_REQUEST_RE: Final = re.compile(
    r"^c1-citation-transport-"
    r"(?:hesitation|frustration|confusion|interest|disengagement)-"
    r"(?:backward|forward)-0[1-5]$"
)
_DOCUMENT_REQUEST_RE: Final = re.compile(
    r"^c1-document-[0-9]{4}$"
)
_BLOCKED_QUERY_PARAMETER_RE: Final = re.compile(
    r"(?:token|key|secret|password|auth|authorization|session|cookie)",
    re.IGNORECASE,
)
_FORBIDDEN_PAYLOAD_QUERY_NAMES: Final = frozenset(
    {
        "audio",
        "customer_id",
        "feature",
        "model_metric",
        "participant_id",
        "prediction",
        "probability",
        "transcript",
        "utterance",
    }
)
_PUBLIC_DNS_LABEL_RE: Final = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
_NUMERIC_HOST_COMPONENT_RE: Final = re.compile(
    r"^(?:[0-9]+|0x[0-9a-f]+)$"
)
_SPECIAL_USE_HOST_SUFFIXES: Final = frozenset(
    {
        "example",
        "home.arpa",
        "internal",
        "invalid",
        "lan",
        "local",
        "localdomain",
        "localhost",
        "onion",
        "test",
    }
)
_CONTENT_TYPE_RE: Final = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$"
)
_TOP_LEVEL_PROTOCOL_FIELDS: Final = frozenset(
    {
        "schema_version",
        "checkpoint_id",
        "protocol_id",
        "target_signals",
        "signal_constructs",
        "construct_correspondence_order",
        "observer_method_order",
        "annotation_modality_order",
        "temporal_unit_order",
        "source_channels",
        "query_templates",
        "expected_seed_query_count",
        "fallback_material_query_templates",
        "expected_fallback_material_query_count",
        "expected_total_query_count",
        "max_detailed_candidates_per_signal",
        "max_detailed_fallback_material_candidates",
        "citation_hop_depth",
        "max_backward_citations_per_signal",
        "max_forward_citations_per_signal",
        "max_response_bytes_by_transport_purpose",
        "allowed_response_content_types_by_transport_purpose",
        "max_total_source_cache_bytes",
        "allowed_url_schemes",
        "seed_discovery_domains",
        "blocked_browser_modes",
        "candidate_status_order",
        "signal_decision_order",
        "overall_decision_order",
        "reason_code_order",
        "reliability_scale",
        "reliability_rules",
        "positive_support_rule",
        "annotation_fallback_protocol",
        "failure_guards",
        "canonical_json",
    }
)
_RECEIPT_FIELDS: Final = frozenset(
    {
        "schema_version",
        "receipt_id",
        "purpose",
        "request_key",
        "retrieved_at_utc",
        "requested_url",
        "final_url",
        "outcome",
        "incomplete_reason",
        "http_status_code",
        "redirect_hop_count",
        "redirect_chain",
        "response_sha256",
        "response_byte_count",
        "response_content_type",
    }
)
_LEDGER_FIELDS: Final = frozenset(
    {"schema_version", "protocol_sha256", "receipts"}
)
_PROTOCOL_INTEGER_FIELDS: Final = (
    "expected_seed_query_count",
    "expected_fallback_material_query_count",
    "expected_total_query_count",
    "max_detailed_candidates_per_signal",
    "max_detailed_fallback_material_candidates",
    "citation_hop_depth",
    "max_backward_citations_per_signal",
    "max_forward_citations_per_signal",
    "max_total_source_cache_bytes",
    "reliability_scale",
)


def _mapping(value: object, *, code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PhaseC1ContractError(code)
    if not all(isinstance(key, str) for key in value):
        raise PhaseC1ContractError(code)
    return value


def _exact_fields(
    value: Mapping[str, object],
    expected: frozenset[str],
    *,
    code: str,
) -> None:
    if frozenset(value) != expected:
        raise PhaseC1ContractError(code)


def _string(value: object, *, code: str, maximum: int = 512) -> str:
    if not isinstance(value, str):
        raise PhaseC1ContractError(code)
    if not value or len(value) > maximum:
        raise PhaseC1ContractError(code)
    if unicodedata.normalize("NFC", value) != value:
        raise PhaseC1ContractError(code)
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise PhaseC1ContractError(code)
    return value


def _integer(
    value: object,
    *,
    code: str,
    minimum: int,
    maximum: int | None = None,
) -> int:
    if type(value) is not int:
        raise PhaseC1ContractError(code)
    if value < minimum or (maximum is not None and value > maximum):
        raise PhaseC1ContractError(code)
    return value


def _sequence(value: object, *, code: str) -> list[object]:
    if not isinstance(value, list):
        raise PhaseC1ContractError(code)
    return value


def _string_tuple(value: object, *, code: str) -> tuple[str, ...]:
    items = _sequence(value, code=code)
    result = tuple(_string(item, code=code) for item in items)
    if len(set(result)) != len(result):
        raise PhaseC1ContractError(code)
    return result


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _validate_protocol_shape(payload: Mapping[str, object]) -> None:
    _exact_fields(
        payload,
        _TOP_LEVEL_PROTOCOL_FIELDS,
        code="protocol_fields",
    )
    if payload["schema_version"] != _PROTOCOL_SCHEMA:
        raise PhaseC1ContractError("protocol_schema")
    if payload["checkpoint_id"] != _CHECKPOINT_ID:
        raise PhaseC1ContractError("protocol_checkpoint")
    if payload["protocol_id"] != _PROTOCOL_ID:
        raise PhaseC1ContractError("protocol_id")

    if tuple(_string_tuple(payload["target_signals"], code="target_signals")) != TARGET_SIGNALS:
        raise PhaseC1ContractError("target_signals")

    for field in _PROTOCOL_INTEGER_FIELDS:
        _integer(payload[field], code=f"protocol_{field}", minimum=1)

    signal_constructs = _sequence(
        payload["signal_constructs"],
        code="signal_constructs",
    )
    if len(signal_constructs) != len(TARGET_SIGNALS):
        raise PhaseC1ContractError("signal_constructs")
    for expected_signal, raw_construct in zip(
        TARGET_SIGNALS,
        signal_constructs,
        strict=True,
    ):
        construct = _mapping(raw_construct, code="signal_construct")
        _exact_fields(
            construct,
            frozenset(
                {
                    "signal",
                    "observer_construct",
                    "direct_label_requirement",
                    "excluded_proxies",
                }
            ),
            code="signal_construct_fields",
        )
        if construct["signal"] != expected_signal:
            raise PhaseC1ContractError("signal_construct_order")
        _string(construct["observer_construct"], code="observer_construct")
        _string(
            construct["direct_label_requirement"],
            code="direct_label_requirement",
        )
        if not _string_tuple(
            construct["excluded_proxies"],
            code="excluded_proxies",
        ):
            raise PhaseC1ContractError("excluded_proxies")

    for field in (
        "construct_correspondence_order",
        "observer_method_order",
        "annotation_modality_order",
        "temporal_unit_order",
        "query_templates",
        "fallback_material_query_templates",
        "allowed_url_schemes",
        "seed_discovery_domains",
        "blocked_browser_modes",
        "candidate_status_order",
        "signal_decision_order",
        "overall_decision_order",
        "reason_code_order",
    ):
        if not _string_tuple(payload[field], code=f"protocol_{field}"):
            raise PhaseC1ContractError(f"protocol_{field}")

    channels = _sequence(payload["source_channels"], code="source_channels")
    expected_channels = (
        ("openalex", "https://api.openalex.org/works"),
        ("crossref", "https://api.crossref.org/works"),
        ("zenodo", "https://zenodo.org/api/records"),
        ("huggingface", "https://huggingface.co/api/datasets"),
    )
    if len(channels) != len(expected_channels):
        raise PhaseC1ContractError("source_channels")
    for raw_channel, (channel_id, endpoint) in zip(
        channels,
        expected_channels,
        strict=True,
    ):
        channel = _mapping(raw_channel, code="source_channel")
        _exact_fields(
            channel,
            frozenset(
                {
                    "channel_id",
                    "endpoint",
                    "query_parameter",
                    "limit_parameter",
                    "result_limit",
                    "authority_role",
                }
            ),
            code="source_channel_fields",
        )
        if (
            channel["channel_id"] != channel_id
            or channel["endpoint"] != endpoint
            or channel["authority_role"] != "discovery_only"
        ):
            raise PhaseC1ContractError("source_channel_value")
        _public_https_url(channel["endpoint"], code="source_channel_url")
        _string(channel["query_parameter"], code="source_channel_query")
        _string(channel["limit_parameter"], code="source_channel_limit")
        if _integer(
            channel["result_limit"],
            code="source_channel_result_limit",
            minimum=1,
        ) != 25:
            raise PhaseC1ContractError("source_channel_result_limit")

    caps = _mapping(
        payload["max_response_bytes_by_transport_purpose"],
        code="transport_caps",
    )
    _exact_fields(
        caps,
        frozenset(TRANSPORT_PURPOSES),
        code="transport_cap_fields",
    )
    for value in caps.values():
        _integer(value, code="transport_cap", minimum=1)

    content_types = _mapping(
        payload["allowed_response_content_types_by_transport_purpose"],
        code="transport_content_types",
    )
    _exact_fields(
        content_types,
        frozenset(TRANSPORT_PURPOSES),
        code="transport_content_type_fields",
    )
    for purpose in TRANSPORT_PURPOSES:
        values = _string_tuple(
            content_types[purpose],
            code="transport_content_types",
        )
        if not values:
            raise PhaseC1ContractError("transport_content_types")
        for value in values:
            _content_type(value)

    rules = _sequence(payload["reliability_rules"], code="reliability_rules")
    if len(rules) != 1:
        raise PhaseC1ContractError("reliability_rules")
    rule = _mapping(rules[0], code="reliability_rule")
    _exact_fields(
        rule,
        frozenset(
            {
                "metric_id",
                "pass_point_min_micros",
                "pass_lower_95_min_micros",
                "reject_upper_95_max_exclusive_micros",
                "unverifiable_disposition",
                "insufficient_effective_sample_disposition",
            }
        ),
        code="reliability_rule_fields",
    )
    if rule["metric_id"] != "krippendorff_alpha":
        raise PhaseC1ContractError("reliability_metric")
    for field in (
        "pass_point_min_micros",
        "pass_lower_95_min_micros",
        "reject_upper_95_max_exclusive_micros",
    ):
        _integer(rule[field], code="reliability_threshold", minimum=0)

    positive = _mapping(
        payload["positive_support_rule"],
        code="positive_support_rule",
    )
    _exact_fields(
        positive,
        frozenset(
            {
                "method",
                "estimand",
                "trial_unit",
                "worst_case_probability_micros",
                "z_micros",
                "max_half_width_micros",
                "minimum_published_positive_count",
            }
        ),
        code="positive_support_fields",
    )
    for field in ("method", "estimand", "trial_unit"):
        _string(positive[field], code="positive_support_string")
    for field in (
        "worst_case_probability_micros",
        "z_micros",
        "max_half_width_micros",
        "minimum_published_positive_count",
    ):
        _integer(positive[field], code="positive_support_integer", minimum=1)

    fallback = _mapping(
        payload["annotation_fallback_protocol"],
        code="annotation_fallback",
    )
    _exact_fields(
        fallback,
        frozenset(
            {
                "execution_authorized",
                "requires_separate_checkpoint",
                "material_scope",
                "minimum_independent_raters_per_segment",
                "labels",
                "signals_independent",
                "signal_cooccurrence_allowed",
                "bounded_context_frozen_before_annotation",
                "annotators_blinded_to_model_outputs",
                "annotators_blinded_to_sales_decisions",
                "annotators_blinded_to_other_raters",
                "training_and_pilot_excluded_from_later_evaluation",
                "codebook_revision_phase",
                "raw_disagreement_preserved",
                "majority_vote_as_ground_truth_allowed",
                "llm_labels_allowed",
                "private_conversations_allowed",
                "customer_calls_allowed",
                "protected_characteristic_inference_allowed",
                "speaker_and_conversation_ids_use",
                "sample_size_method",
            }
        ),
        code="annotation_fallback_fields",
    )
    for field, value in fallback.items():
        if field == "minimum_independent_raters_per_segment":
            _integer(value, code="annotation_fallback_raters", minimum=1)
        elif field == "labels":
            _string_tuple(value, code="annotation_fallback_labels")
        elif field in {
            "material_scope",
            "codebook_revision_phase",
            "speaker_and_conversation_ids_use",
            "sample_size_method",
        }:
            _string(value, code="annotation_fallback_string")
        elif type(value) is not bool:
            raise PhaseC1ContractError("annotation_fallback_boolean")

    guards = _mapping(payload["failure_guards"], code="failure_guards")
    if not guards or not all(type(value) is bool for value in guards.values()):
        raise PhaseC1ContractError("failure_guards")

    canonical = _mapping(payload["canonical_json"], code="canonical_json")
    _exact_fields(
        canonical,
        frozenset(
            {
                "encoding",
                "indent",
                "sort_keys",
                "ensure_ascii",
                "allow_nan",
                "terminal_lf",
            }
        ),
        code="canonical_json_fields",
    )
    if type(canonical["indent"]) is not int:
        raise PhaseC1ContractError("canonical_json_indent")
    for field in ("sort_keys", "ensure_ascii", "allow_nan", "terminal_lf"):
        if type(canonical[field]) is not bool:
            raise PhaseC1ContractError("canonical_json_boolean")


def validate_discovery_protocol(payload: object) -> PhaseC1ProtocolV1:
    protocol = _mapping(payload, code="protocol_object")
    _validate_protocol_shape(protocol)
    try:
        canonical = canonical_json_bytes(protocol)
    except (TypeError, ValueError) as exc:
        raise PhaseC1ContractError("protocol_json") from exc
    if sha256_bytes(canonical) != _FROZEN_PROTOCOL_SHA256:
        raise PhaseC1ContractError("protocol_exact")

    frozen = _freeze(protocol)
    if not isinstance(frozen, Mapping):
        raise PhaseC1ContractError("protocol_freeze")
    return PhaseC1ProtocolV1(
        checkpoint_id=protocol["checkpoint_id"],
        protocol_id=protocol["protocol_id"],
        target_signals=frozen["target_signals"],
        signal_constructs=frozen["signal_constructs"],
        construct_correspondence_order=frozen["construct_correspondence_order"],
        observer_method_order=frozen["observer_method_order"],
        annotation_modality_order=frozen["annotation_modality_order"],
        temporal_unit_order=frozen["temporal_unit_order"],
        source_channels=frozen["source_channels"],
        query_templates=frozen["query_templates"],
        expected_seed_query_count=protocol["expected_seed_query_count"],
        fallback_material_query_templates=frozen[
            "fallback_material_query_templates"
        ],
        expected_fallback_material_query_count=protocol[
            "expected_fallback_material_query_count"
        ],
        expected_total_query_count=protocol["expected_total_query_count"],
        max_detailed_candidates_per_signal=protocol[
            "max_detailed_candidates_per_signal"
        ],
        max_detailed_fallback_material_candidates=protocol[
            "max_detailed_fallback_material_candidates"
        ],
        citation_hop_depth=protocol["citation_hop_depth"],
        max_backward_citations_per_signal=protocol[
            "max_backward_citations_per_signal"
        ],
        max_forward_citations_per_signal=protocol[
            "max_forward_citations_per_signal"
        ],
        max_response_bytes_by_transport_purpose=frozen[
            "max_response_bytes_by_transport_purpose"
        ],
        allowed_response_content_types_by_transport_purpose=frozen[
            "allowed_response_content_types_by_transport_purpose"
        ],
        max_total_source_cache_bytes=protocol["max_total_source_cache_bytes"],
        allowed_url_schemes=frozen["allowed_url_schemes"],
        seed_discovery_domains=frozen["seed_discovery_domains"],
        blocked_browser_modes=frozen["blocked_browser_modes"],
        candidate_status_order=frozen["candidate_status_order"],
        signal_decision_order=frozen["signal_decision_order"],
        overall_decision_order=frozen["overall_decision_order"],
        reason_code_order=frozen["reason_code_order"],
        reliability_scale=protocol["reliability_scale"],
        reliability_rules=frozen["reliability_rules"],
        positive_support_rule=frozen["positive_support_rule"],
        annotation_fallback_protocol=frozen["annotation_fallback_protocol"],
        failure_guards=frozen["failure_guards"],
        canonical_json=frozen["canonical_json"],
    )


def expected_phase_c1_queries(
    protocol: PhaseC1ProtocolV1,
) -> tuple[tuple[str, str, str, str | None, str], ...]:
    rows: list[tuple[str, str, str, str | None, str]] = []
    for signal in protocol.target_signals:
        for channel in protocol.source_channels:
            channel_id = str(channel["channel_id"])
            for index, template in enumerate(
                protocol.query_templates,
                start=1,
            ):
                query_id = f"c1-query-{signal}-{channel_id}-{index:02d}"
                rows.append(
                    (
                        query_id,
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
            rows.append(
                (
                    f"c1-query-fallback-material-{channel_id}-{index:02d}",
                    "fallback_material",
                    channel_id,
                    None,
                    template,
                )
            )
    return tuple(rows)


def _public_dns_hostname(hostname: str, *, code: str) -> str:
    if hostname.endswith(".."):
        raise PhaseC1ContractError(code)
    normalized = unicodedata.normalize("NFC", hostname)
    if normalized.endswith("."):
        normalized = normalized[:-1]
    try:
        ascii_hostname = normalized.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise PhaseC1ContractError(code) from exc
    if (
        not ascii_hostname
        or len(ascii_hostname) > 253
        or "." not in ascii_hostname
    ):
        raise PhaseC1ContractError(code)
    labels = ascii_hostname.split(".")
    if (
        any(_PUBLIC_DNS_LABEL_RE.fullmatch(label) is None for label in labels)
        or all(
            _NUMERIC_HOST_COMPONENT_RE.fullmatch(label) is not None
            for label in labels
        )
    ):
        raise PhaseC1ContractError(code)
    if any(
        ascii_hostname == suffix
        or ascii_hostname.endswith(f".{suffix}")
        for suffix in _SPECIAL_USE_HOST_SUFFIXES
    ):
        raise PhaseC1ContractError(code)
    return ascii_hostname


def _public_https_url(value: object, *, code: str) -> str:
    url = _string(value, code=code, maximum=2048)
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise PhaseC1ContractError(code) from exc
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise PhaseC1ContractError(code)
    decoded_url = url
    for _ in range(len(url) + 1):
        if re.search(r"%(?![0-9A-Fa-f]{2})|%(?:2[fF]|5[cC])", decoded_url):
            raise PhaseC1ContractError(code)
        try:
            next_decoded_url = unquote_to_bytes(decoded_url).decode("utf-8", "strict")
        except UnicodeDecodeError as exc:
            raise PhaseC1ContractError(code) from exc
        if any(unicodedata.category(character) == "Cc" for character in next_decoded_url):
            raise PhaseC1ContractError(code)
        if next_decoded_url == decoded_url:
            break
        decoded_url = next_decoded_url
    else:
        raise PhaseC1ContractError(code)
    try:
        decoded = urlsplit(decoded_url)
        decoded_hostname = decoded.hostname
        decoded_port = decoded.port
    except ValueError as exc:
        raise PhaseC1ContractError(code) from exc
    if (
        decoded.scheme != "https"
        or not decoded.netloc
        or decoded_hostname is None
        or decoded.username is not None
        or decoded.password is not None
        or decoded.fragment
        or "\\" in decoded_url
    ):
        raise PhaseC1ContractError(code)
    if port is not None and not 1 <= port <= 65535:
        raise PhaseC1ContractError(code)
    if decoded_port is not None and not 1 <= decoded_port <= 65535:
        raise PhaseC1ContractError(code)
    lowered = hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(lowered)
    except ValueError:
        pass
    else:
        raise PhaseC1ContractError(code)
    _public_dns_hostname(hostname, code=code)
    _public_dns_hostname(decoded_hostname, code=code)
    if any(segment in {".", ".."} for segment in decoded.path.split("/")):
        raise PhaseC1ContractError(code)
    for key, _ in parse_qsl(decoded.query, keep_blank_values=True):
        normalized_key = unicodedata.normalize("NFC", key).casefold()
        if (
            normalized_key in _FORBIDDEN_PAYLOAD_QUERY_NAMES
            or _BLOCKED_QUERY_PARAMETER_RE.search(normalized_key)
        ):
            raise PhaseC1ContractError(code)
    return url


def _content_type(value: object) -> str:
    content_type = _string(value, code="transport_content_type")
    if (
        content_type != content_type.lower()
        or _CONTENT_TYPE_RE.fullmatch(content_type) is None
    ):
        raise PhaseC1ContractError("transport_content_type")
    return content_type


def _optional_hash(value: object) -> str | None:
    if value is None:
        return None
    digest = _string(value, code="transport_sha256")
    if _SHA256_RE.fullmatch(digest) is None:
        raise PhaseC1ContractError("transport_sha256")
    return digest


def _optional_integer(
    value: object,
    *,
    code: str,
    minimum: int,
    maximum: int | None = None,
) -> int | None:
    if value is None:
        return None
    return _integer(value, code=code, minimum=minimum, maximum=maximum)


def _request_key(value: object, *, purpose: str) -> str:
    request_key = _string(value, code="transport_request_key")
    pattern = {
        "seed_query": _SEED_REQUEST_RE,
        "citation_discovery": _CITATION_REQUEST_RE,
        "authoritative_document": _DOCUMENT_REQUEST_RE,
    }[purpose]
    if pattern.fullmatch(request_key) is None:
        raise PhaseC1ContractError("transport_request_key")
    return request_key


def parse_transport_receipt(payload: object) -> PhaseC1TransportReceiptV1:
    raw = _mapping(payload, code="transport_receipt_object")
    _exact_fields(raw, _RECEIPT_FIELDS, code="transport_receipt_fields")
    if raw["schema_version"] != _RECEIPT_SCHEMA:
        raise PhaseC1ContractError("transport_receipt_schema")

    receipt_id = _string(raw["receipt_id"], code="transport_receipt_id")
    if _RECEIPT_ID_RE.fullmatch(receipt_id) is None:
        raise PhaseC1ContractError("transport_receipt_id")

    purpose = _string(raw["purpose"], code="transport_purpose")
    if purpose not in TRANSPORT_PURPOSES:
        raise PhaseC1ContractError("transport_purpose")
    request_key = _request_key(raw["request_key"], purpose=purpose)

    retrieved_at_utc = _string(
        raw["retrieved_at_utc"],
        code="transport_timestamp",
    )
    if _TIMESTAMP_RE.fullmatch(retrieved_at_utc) is None:
        raise PhaseC1ContractError("transport_timestamp")
    try:
        datetime.strptime(retrieved_at_utc, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise PhaseC1ContractError("transport_timestamp") from exc

    requested_url = _public_https_url(
        raw["requested_url"],
        code="transport_requested_url",
    )
    final_url = (
        None
        if raw["final_url"] is None
        else _public_https_url(
            raw["final_url"],
            code="transport_final_url",
        )
    )

    outcome = _string(raw["outcome"], code="transport_outcome")
    if outcome not in TRANSPORT_OUTCOMES:
        raise PhaseC1ContractError("transport_outcome")
    incomplete_reason = raw["incomplete_reason"]
    if incomplete_reason is not None:
        incomplete_reason = _string(
            incomplete_reason,
            code="transport_incomplete_reason",
        )
        if incomplete_reason not in TRANSPORT_INCOMPLETE_REASONS:
            raise PhaseC1ContractError("transport_incomplete_reason")

    http_status_code = _optional_integer(
        raw["http_status_code"],
        code="transport_http_status",
        minimum=100,
        maximum=599,
    )
    redirect_hop_count = _integer(
        raw["redirect_hop_count"],
        code="transport_redirect_count",
        minimum=0,
        maximum=3,
    )
    redirect_chain = tuple(
        _public_https_url(item, code="transport_redirect_url")
        for item in _sequence(
            raw["redirect_chain"],
            code="transport_redirect_chain",
        )
    )
    if len(redirect_chain) != redirect_hop_count:
        raise PhaseC1ContractError("transport_redirect_count")

    response_sha256 = _optional_hash(raw["response_sha256"])
    response_byte_count = _optional_integer(
        raw["response_byte_count"],
        code="transport_response_bytes",
        minimum=1,
    )
    if (response_sha256 is None) != (response_byte_count is None):
        raise PhaseC1ContractError("transport_response_pair")
    response_content_type = (
        None
        if raw["response_content_type"] is None
        else _content_type(raw["response_content_type"])
    )

    if outcome == "complete":
        if (
            incomplete_reason is not None
            or final_url is None
            or http_status_code is None
            or not 200 <= http_status_code <= 299
            or response_sha256 is None
            or response_byte_count is None
            or response_content_type is None
        ):
            raise PhaseC1ContractError("transport_complete")
    elif incomplete_reason is None:
        raise PhaseC1ContractError("transport_incomplete")

    return PhaseC1TransportReceiptV1(
        receipt_id=receipt_id,
        purpose=purpose,
        request_key=request_key,
        retrieved_at_utc=retrieved_at_utc,
        requested_url=requested_url,
        final_url=final_url,
        outcome=outcome,
        incomplete_reason=incomplete_reason,
        http_status_code=http_status_code,
        redirect_hop_count=redirect_hop_count,
        redirect_chain=redirect_chain,
        response_sha256=response_sha256,
        response_byte_count=response_byte_count,
        response_content_type=response_content_type,
    )


def _thaw_protocol_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            key: _thaw_protocol_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_thaw_protocol_value(item) for item in value]
    return value


def _validated_transport_protocol(
    protocol: object,
) -> PhaseC1ProtocolV1:
    if not isinstance(protocol, PhaseC1ProtocolV1):
        raise PhaseC1ContractError("transport_protocol")
    payload = {
        "schema_version": _PROTOCOL_SCHEMA,
        **{
            field.name: _thaw_protocol_value(
                getattr(protocol, field.name)
            )
            for field in fields(PhaseC1ProtocolV1)
        },
    }
    try:
        return validate_discovery_protocol(payload)
    except PhaseC1ContractError as exc:
        raise PhaseC1ContractError("transport_protocol") from exc


def validate_transport_receipt_ledger(
    payload: object,
    *,
    protocol: PhaseC1ProtocolV1,
) -> PhaseC1TransportReceiptLedgerV1:
    protocol = _validated_transport_protocol(protocol)
    raw = _mapping(payload, code="transport_ledger_object")
    _exact_fields(raw, _LEDGER_FIELDS, code="transport_ledger_fields")
    if raw["schema_version"] != _LEDGER_SCHEMA:
        raise PhaseC1ContractError("transport_ledger_schema")
    protocol_sha256 = _string(
        raw["protocol_sha256"],
        code="transport_protocol_sha256",
    )
    if (
        _SHA256_RE.fullmatch(protocol_sha256) is None
        or protocol_sha256 != _FROZEN_PROTOCOL_SHA256
    ):
        raise PhaseC1ContractError("transport_protocol_sha256")

    receipts = tuple(
        parse_transport_receipt(item)
        for item in _sequence(raw["receipts"], code="transport_receipts")
    )
    receipt_ids = tuple(item.receipt_id for item in receipts)
    request_keys = tuple(item.request_key for item in receipts)
    if receipt_ids != tuple(sorted(receipt_ids)):
        raise PhaseC1ContractError("transport_receipt_order")
    if len(set(receipt_ids)) != len(receipt_ids):
        raise PhaseC1ContractError("transport_duplicate_receipt_id")
    if len(set(request_keys)) != len(request_keys):
        raise PhaseC1ContractError("transport_duplicate_request_key")

    response_sizes: dict[str, int] = {}
    for receipt in receipts:
        if receipt.response_byte_count is not None:
            cap = protocol.max_response_bytes_by_transport_purpose[
                receipt.purpose
            ]
            if receipt.response_byte_count > cap:
                raise PhaseC1ContractError("transport_response_cap")
        if (
            receipt.response_content_type is not None
            and receipt.response_content_type
            not in protocol.allowed_response_content_types_by_transport_purpose[
                receipt.purpose
            ]
        ):
            raise PhaseC1ContractError("transport_content_type_purpose")
        if receipt.response_sha256 is not None:
            previous = response_sizes.setdefault(
                receipt.response_sha256,
                receipt.response_byte_count,
            )
            if previous != receipt.response_byte_count:
                raise PhaseC1ContractError("transport_hash_size")
    if sum(response_sizes.values()) > protocol.max_total_source_cache_bytes:
        raise PhaseC1ContractError("transport_cache_cap")

    return PhaseC1TransportReceiptLedgerV1(
        protocol_sha256=protocol_sha256,
        receipts=receipts,
    )


@dataclass(frozen=True, slots=True)
class PhaseC1DocumentReceiptV1:
    document_id: str
    role: str
    authoritative_url: str
    publisher_domain: str
    retrieved_at_utc: str
    cached_sha256: str
    content_type: str
    byte_count: int
    authoritative: bool
    public_without_login: bool
    transport_receipt_sha256: str


@dataclass(frozen=True, slots=True)
class PhaseC1SourceReceiptV1:
    source_id: str
    title: str
    source_kind: str
    phase_c1_roles: tuple[str, ...]
    version: str
    documents: tuple[PhaseC1DocumentReceiptV1, ...]
    access_status: str
    license_status: str
    license_identifier: str
    ethical_use_status: str
    conversation_status: str
    domain: str
    languages: tuple[str, ...]
    population_scope: str
    modalities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1ReliabilityEvidenceV1:
    metric_id: str
    point_micros: int | None
    lower_95_micros: int | None
    upper_95_micros: int | None
    rated_unit_count: int | None
    published_positive_count: int | None
    preadjudication: bool
    verifiable: bool
    uncertain_or_unratable_rate_micros: int | None
    class_prevalence_micros: int | None
    positive_agreement_micros: int | None
    negative_agreement_micros: int | None
    preadjudication_disagreement_micros: int | None


@dataclass(frozen=True, slots=True)
class PhaseC1EvidenceCardV1:
    card_id: str
    source_id: str
    signal: str
    native_label: str
    native_definition_document_id: str
    native_definition_locator: str
    native_definition_excerpt_sha256: str
    annotation_modality: str
    construct_correspondence: str
    temporal_unit: str
    bounded_context_description: str
    observer_method: str
    independent_rater_count: int | None
    reliability: PhaseC1ReliabilityEvidenceV1
    claimed_status: str
    claimed_reason_codes: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1FallbackMaterialEvidenceV1:
    source_id: str
    status: str
    public_spontaneous_material_status: str
    license_status: str
    ethical_use_status: str
    minimum_three_raters_status: str
    material_evidence_document_ids: tuple[str, ...]
    license_evidence_document_ids: tuple[str, ...]
    ethical_use_evidence_document_ids: tuple[str, ...]
    rater_feasibility_evidence_document_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1AnnotationFallbackAssessmentV1:
    signal: str
    status: str
    material_evidence: tuple[PhaseC1FallbackMaterialEvidenceV1, ...]
    preregistration_only: bool
    execution_authorized: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1SourceEvidenceLedgerV1:
    protocol_sha256: str
    search_ledger_sha256: str
    sources: tuple[PhaseC1SourceReceiptV1, ...]
    cards: tuple[PhaseC1EvidenceCardV1, ...]
    fallback_assessments: tuple[PhaseC1AnnotationFallbackAssessmentV1, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1SourceReviewReceiptV1:
    protocol_sha256: str
    search_ledger_sha256: str
    source_evidence_ledger_sha256: str
    transport_ledger_sha256: str
    reviewed_transport_receipt_sha256s: tuple[str, ...]
    reviewed_document_sha256s: tuple[str, ...]
    review_scope: str
    verdict: str
    critical_findings: int
    important_findings: int
    minor_findings: int
    raw_rows_read: bool
    private_data_read: bool
    model_evaluation_run: bool
    provider_accessed: bool
    runtime_modified: bool


DOCUMENT_ROLES: Final = (
    "academic_paper",
    "annotation_manual",
    "corpus_page",
    "license",
    "reliability_report",
)
SOURCE_KINDS: Final = ("academic_corpus", "public_dataset")
SOURCE_ROLES: Final = (
    "existing_annotation_evidence",
    "fallback_material_candidate",
)
ACCESS_STATUSES: Final = (
    "public_no_login",
    "login_required",
    "restricted",
    "unresolved",
)
LICENSE_STATUSES: Final = ("compatible", "incompatible", "unresolved")
ETHICAL_USE_STATUSES: Final = ("compatible", "incompatible", "unresolved")
CONVERSATION_STATUSES: Final = (
    "spontaneous_conversation",
    "acted_or_scripted",
    "mixed_unseparated",
    "unresolved",
)
ANNOTATION_FALLBACK_STATUSES: Final = ("feasible", "infeasible", "unresolved")
FALLBACK_MATERIAL_STATUSES: Final = ("available", "unavailable", "unresolved")
FALLBACK_RATER_STATUSES: Final = ("feasible", "infeasible", "unresolved")
SOURCE_REVIEW_VERDICTS: Final = ("pending", "blocked", "admitted")
CONSTRUCT_CORRESPONDENCE_VALUES: Final = (
    "direct_target_construct",
    "proxy_construct",
    "target_absent",
    "unresolved",
)
OBSERVER_METHODS: Final = (
    "independent_human_observer",
    "adjudicated_only_human_label",
    "self_report",
    "llm_generated",
    "automated_proxy",
    "unresolved",
)
ANNOTATION_MODALITIES: Final = (
    "audio_only",
    "audio_visual",
    "transcript_only",
    "mixed",
    "unresolved",
)
TEMPORAL_UNITS: Final = ("turn", "bounded_segment", "conversation", "other", "unresolved")
SOURCE_MODALITIES: Final = ("audio", "video", "transcript")
BOUNDED_CONTEXT_VALUES: Final = (
    "single_turn",
    "turn_with_adjacent_context",
    "bounded_segment_within_conversation",
)
_REASON_CODES: Final = (
    "access_requires_login", "access_restricted", "license_incompatible",
    "ethical_use_incompatible", "acted_or_scripted", "mixed_unseparated_conversation",
    "proxy_construct", "target_label_absent", "conversation_level_only",
    "temporal_unit_incompatible", "single_rater", "self_report_label",
    "llm_generated_label", "reliability_upper_below_0_67", "source_identity_unverified",
    "authoritative_provenance_unverified", "access_unresolved", "license_unresolved",
    "ethical_use_unresolved", "conversation_status_unresolved", "directness_unresolved",
    "temporal_unit_unresolved", "observer_method_unresolved", "rater_count_unresolved",
    "reliability_metric_unapproved", "reliability_not_preadjudication",
    "reliability_unverifiable", "reliability_effective_sample_insufficient",
    "positive_support_below_93", "reliability_interval_uncertain",
    "published_positive_count_missing", "source_documentation_incomplete",
    "raw_annotation_rows_required", "search_query_incomplete", "query_result_truncated",
    "candidate_overflow", "citation_budget_incomplete", "annotation_fallback_feasible",
    "annotation_fallback_unresolved",
)
QUERY_STATUSES: Final = ("complete", "incomplete")
QUERY_KINDS: Final = ("direct_label_source", "fallback_material")
QUERY_INCOMPLETE_REASONS: Final = (
    "authentication_required",
    "captcha_or_antibot",
    "terms_or_cost",
    "private_address_or_redirect",
    "unapproved_redirect",
    "rate_limit_pressure",
    "network_error",
    "response_too_large",
    "cache_budget_exhausted",
    "invalid_response",
)
DISCOVERY_DISPOSITIONS: Final = (
    "retained_candidate",
    "duplicate",
    "excluded",
    "unresolved",
)
CITATION_DIRECTIONS: Final = ("backward", "forward")
CITATION_STOP_STATUSES: Final = (
    "no_eligible_candidates",
    "source_list_exhausted",
    "budget_reached",
    "incomplete",
)

_SOURCE_ID_RE: Final = re.compile(r"^c1-source-[0-9]{4}$")
_DOCUMENT_ID_RE: Final = re.compile(r"^c1-document-[0-9]{4}$")
_CARD_ID_RE: Final = re.compile(
    r"^c1-card-(?:hesitation|frustration|confusion|interest|disengagement)-[0-9]{4}$"
)
_LANGUAGE_TAG_RE: Final = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
_SOURCE_FIELDS: Final = frozenset(field.name for field in fields(PhaseC1SourceReceiptV1))
_DOCUMENT_FIELDS: Final = frozenset(field.name for field in fields(PhaseC1DocumentReceiptV1))
_RELIABILITY_FIELDS: Final = frozenset(field.name for field in fields(PhaseC1ReliabilityEvidenceV1))
_CARD_FIELDS: Final = frozenset(field.name for field in fields(PhaseC1EvidenceCardV1))
_FALLBACK_MATERIAL_FIELDS: Final = frozenset(field.name for field in fields(PhaseC1FallbackMaterialEvidenceV1))
_FALLBACK_FIELDS: Final = frozenset(field.name for field in fields(PhaseC1AnnotationFallbackAssessmentV1))
_SOURCE_LEDGER_FIELDS: Final = frozenset(
    {"schema_version", *(field.name for field in fields(PhaseC1SourceEvidenceLedgerV1))}
)
_SOURCE_REVIEW_FIELDS: Final = frozenset(
    {"schema_version", *(field.name for field in fields(PhaseC1SourceReviewReceiptV1))}
)
_SOURCE_LEDGER_SCHEMA: Final = "EmotionStatePhaseC1SourceEvidenceLedgerV1"
_SOURCE_REVIEW_SCHEMA: Final = "EmotionStatePhaseC1SourceReviewReceiptV1"
_SOURCE_REVIEW_SCOPE: Final = (
    "all_transport_discovery_citation_source_cards_and_search_completeness"
)
_SEARCH_LEDGER_SCHEMA: Final = "EmotionStatePhaseC1SearchLedgerV1"
_DISCOVERY_ID_RE: Final = re.compile(r"^c1-discovery-[0-9]{4}$")
_CITATION_ID_RE: Final = re.compile(
    r"^c1-citation-"
    r"(hesitation|frustration|confusion|interest|disengagement)-"
    r"(backward|forward)-([0-9]{2})$"
)
_SEARCH_LEDGER_FIELDS: Final = frozenset(
    {
        "schema_version",
        *(field.name for field in fields(PhaseC1SearchLedgerV1)),
    }
)
_QUERY_FIELDS: Final = frozenset(
    field.name for field in fields(PhaseC1QueryRecordV1)
)
_DISCOVERY_FIELDS: Final = frozenset(
    field.name for field in fields(PhaseC1DiscoveryRecordV1)
)
_CITATION_FIELDS: Final = frozenset(
    field.name for field in fields(PhaseC1CitationRecordV1)
)
_SEARCH_FORBIDDEN_KEYS: Final = frozenset(
    {
        "abstract",
        "author",
        "author_name",
        "author_names",
        "body",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "header",
        "headers",
        "html",
        "local_path",
        "participant",
        "participant_id",
        "path",
        "raw_snippet",
        "snippet",
        "title",
    }
)
_AUTHORITATIVE_DOCUMENT_CONTENT_TYPES: Final = (
    "application/json",
    "application/pdf",
    "application/xml",
    "text/html",
    "text/plain",
    "text/xml",
)


def _forbidden_content(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if (
                isinstance(key, str)
                and unicodedata.normalize("NFC", key).casefold()
                in _FORBIDDEN_PAYLOAD_QUERY_NAMES
            ):
                raise PhaseC1ContractError("forbidden_content")
            _forbidden_content(item)
    elif isinstance(value, list):
        for item in value:
            _forbidden_content(item)


def _hash(value: object, *, code: str) -> str:
    digest = _string(value, code=code, maximum=64)
    if _SHA256_RE.fullmatch(digest) is None:
        raise PhaseC1ContractError(code)
    return digest


def _timestamp(value: object, *, code: str) -> str:
    timestamp = _string(value, code=code)
    if _TIMESTAMP_RE.fullmatch(timestamp) is None:
        raise PhaseC1ContractError(code)
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise PhaseC1ContractError(code) from exc
    return timestamp


def _enum(value: object, values: tuple[str, ...], *, code: str) -> str:
    result = _string(value, code=code)
    if result not in values:
        raise PhaseC1ContractError(code)
    return result


def _ordered_tuple(
    value: object,
    values: tuple[str, ...],
    *,
    code: str,
    nonempty: bool = False,
) -> tuple[str, ...]:
    result = _string_tuple(value, code=code)
    if nonempty and not result:
        raise PhaseC1ContractError(code)
    try:
        positions = tuple(values.index(item) for item in result)
    except ValueError as exc:
        raise PhaseC1ContractError(code) from exc
    if positions != tuple(sorted(positions)):
        raise PhaseC1ContractError(code)
    return result


def _optional_millionths(value: object, *, code: str) -> int | None:
    return _optional_integer(
        value,
        code=code,
        minimum=-1_000_000,
        maximum=1_000_000,
    )


def _document_receipt(payload: object) -> PhaseC1DocumentReceiptV1:
    raw = _mapping(payload, code="document_object")
    _exact_fields(raw, _DOCUMENT_FIELDS, code="document_fields")
    document_id = _string(raw["document_id"], code="document_id")
    if _DOCUMENT_ID_RE.fullmatch(document_id) is None:
        raise PhaseC1ContractError("document_id")
    role = _enum(raw["role"], DOCUMENT_ROLES, code="document_role_unknown")
    authoritative_url = _public_https_url(raw["authoritative_url"], code="document_url")
    publisher_domain = _public_dns_hostname(
        _string(raw["publisher_domain"], code="document_publisher_domain"),
        code="document_publisher_domain",
    )
    retrieved_at_utc = _timestamp(raw["retrieved_at_utc"], code="document_timestamp")
    cached_sha256 = _hash(raw["cached_sha256"], code="document_hash_malformed")
    content_type = _content_type(raw["content_type"])
    if content_type not in _AUTHORITATIVE_DOCUMENT_CONTENT_TYPES:
        raise PhaseC1ContractError("document_content_type")
    byte_count = _integer(
        raw["byte_count"], code="document_byte_count", minimum=1, maximum=20_000_000
    )
    if type(raw["authoritative"]) is not bool:
        raise PhaseC1ContractError("document_authoritative")
    if type(raw["public_without_login"]) is not bool:
        raise PhaseC1ContractError("document_public_without_login")
    transport_receipt_sha256 = _hash(
        raw["transport_receipt_sha256"], code="document_transport_receipt_missing"
    )
    return PhaseC1DocumentReceiptV1(
        document_id=document_id,
        role=role,
        authoritative_url=authoritative_url,
        publisher_domain=publisher_domain,
        retrieved_at_utc=retrieved_at_utc,
        cached_sha256=cached_sha256,
        content_type=content_type,
        byte_count=byte_count,
        authoritative=raw["authoritative"],
        public_without_login=raw["public_without_login"],
        transport_receipt_sha256=transport_receipt_sha256,
    )


def parse_source_receipt(payload: object) -> PhaseC1SourceReceiptV1:
    _forbidden_content(payload)
    raw = _mapping(payload, code="source_object")
    _exact_fields(raw, _SOURCE_FIELDS, code="source_fields")
    source_id = _string(raw["source_id"], code="source_id_mismatch")
    if _SOURCE_ID_RE.fullmatch(source_id) is None:
        raise PhaseC1ContractError("source_id_mismatch")
    documents = tuple(_document_receipt(item) for item in _sequence(raw["documents"], code="source_documents"))
    if not documents:
        raise PhaseC1ContractError("source_documents")
    roles = tuple(item.role for item in documents)
    if roles != tuple(sorted(roles, key=DOCUMENT_ROLES.index)):
        raise PhaseC1ContractError("document_role_order")
    if len({item.document_id for item in documents}) != len(documents):
        raise PhaseC1ContractError("duplicate_document_id")
    if len({item.cached_sha256 for item in documents}) != len(documents):
        raise PhaseC1ContractError("duplicate_document_hash")
    if len(set(roles)) != len(roles):
        raise PhaseC1ContractError("document_role_duplicate")
    access_status = _enum(raw["access_status"], ACCESS_STATUSES, code="source_access_status")
    if access_status == "login_required" and any(item.public_without_login for item in documents):
        raise PhaseC1ContractError("login_claim_with_public_document")
    languages = _string_tuple(raw["languages"], code="source_languages")
    if not languages or any(_LANGUAGE_TAG_RE.fullmatch(item) is None or len(item) > 35 for item in languages):
        raise PhaseC1ContractError("source_languages")
    return PhaseC1SourceReceiptV1(
        source_id=source_id,
        title=_string(raw["title"], code="source_title"),
        source_kind=_enum(raw["source_kind"], SOURCE_KINDS, code="source_kind"),
        phase_c1_roles=_ordered_tuple(raw["phase_c1_roles"], SOURCE_ROLES, code="source_role_missing_or_unknown", nonempty=True),
        version=_string(raw["version"], code="source_version", maximum=128),
        documents=documents,
        access_status=access_status,
        license_status=_enum(raw["license_status"], LICENSE_STATUSES, code="source_license_status"),
        license_identifier=_string(raw["license_identifier"], code="source_license_identifier", maximum=128),
        ethical_use_status=_enum(raw["ethical_use_status"], ETHICAL_USE_STATUSES, code="source_ethical_use_status"),
        conversation_status=_enum(raw["conversation_status"], CONVERSATION_STATUSES, code="source_conversation_status"),
        domain=_string(raw["domain"], code="source_domain"),
        languages=languages,
        population_scope=_string(raw["population_scope"], code="source_population_scope"),
        modalities=_ordered_tuple(raw["modalities"], SOURCE_MODALITIES, code="source_modalities", nonempty=True),
    )


def _reliability(payload: object) -> PhaseC1ReliabilityEvidenceV1:
    raw = _mapping(payload, code="reliability_object")
    _exact_fields(raw, _RELIABILITY_FIELDS, code="reliability_fields")
    metric_id = _string(raw["metric_id"], code="metric_not_allowlisted")
    if metric_id != "krippendorff_alpha":
        raise PhaseC1ContractError("metric_not_allowlisted")
    point = _optional_millionths(raw["point_micros"], code="reliability_point")
    lower = _optional_millionths(raw["lower_95_micros"], code="reliability_lower")
    upper = _optional_millionths(raw["upper_95_micros"], code="reliability_upper")
    if (
        (lower is not None and point is not None and lower > point)
        or (point is not None and upper is not None and point > upper)
        or (lower is not None and upper is not None and lower > upper)
    ):
        raise PhaseC1ContractError("alpha_interval_not_ordered")
    rated = _optional_integer(raw["rated_unit_count"], code="rated_unit_count", minimum=1)
    positives = _optional_integer(raw["published_positive_count"], code="positive_count_boolean", minimum=1)
    if rated is not None and positives is not None and positives > rated:
        raise PhaseC1ContractError("positive_count_exceeds_rated_units")
    rate_fields = (
        "uncertain_or_unratable_rate_micros", "class_prevalence_micros",
        "positive_agreement_micros", "negative_agreement_micros",
        "preadjudication_disagreement_micros",
    )
    if any(type(raw[field]) is bool for field in rate_fields):
        raise PhaseC1ContractError("secondary_diagnostic_boolean")
    rates = tuple(_optional_integer(raw[field], code="secondary_diagnostic_out_of_range", minimum=0, maximum=1_000_000) for field in rate_fields)
    if type(raw["preadjudication"]) is not bool or type(raw["verifiable"]) is not bool:
        raise PhaseC1ContractError("reliability_boolean")
    return PhaseC1ReliabilityEvidenceV1(
        metric_id, point, lower, upper, rated, positives, raw["preadjudication"], raw["verifiable"], *rates
    )


def parse_evidence_card(payload: object) -> PhaseC1EvidenceCardV1:
    _forbidden_content(payload)
    raw = _mapping(payload, code="card_object")
    _exact_fields(raw, _CARD_FIELDS, code="card_fields")
    card_id = _string(raw["card_id"], code="card_id")
    if _CARD_ID_RE.fullmatch(card_id) is None:
        raise PhaseC1ContractError("card_id")
    signal = _enum(raw["signal"], TARGET_SIGNALS, code="card_signal_not_in_protocol")
    if not card_id.startswith(f"c1-card-{signal}-"):
        raise PhaseC1ContractError("card_signal_not_in_protocol")
    construct = _enum(raw["construct_correspondence"], CONSTRUCT_CORRESPONDENCE_VALUES, code="construct_correspondence")
    modality = _enum(raw["annotation_modality"], ANNOTATION_MODALITIES, code="annotation_modality_unknown")
    temporal = _enum(raw["temporal_unit"], TEMPORAL_UNITS, code="temporal_unit")
    observer = _enum(raw["observer_method"], OBSERVER_METHODS, code="observer_method_unknown")
    rater_count = _optional_integer(raw["independent_rater_count"], code="independent_rater_count", minimum=1)
    reliability = _reliability(raw["reliability"])
    claimed_status = _enum(raw["claimed_status"], ("admissible", "rejected", "unresolved"), code="claimed_status")
    reasons = _ordered_tuple(raw["claimed_reason_codes"], _REASON_CODES, code="reason_codes_unsorted")
    limitations = tuple(
        _string(item, code="limitations")
        for item in _sequence(raw["limitations"], code="limitations")
    )
    if len(set(limitations)) != len(limitations):
        raise PhaseC1ContractError("limitation_duplicate")
    if claimed_status == "admissible":
        if construct != "direct_target_construct":
            raise PhaseC1ContractError("proxy_card_claimed_admissible")
        if modality == "unresolved":
            raise PhaseC1ContractError("annotation_modality_unresolved_claimed_admissible")
        if observer == "self_report":
            raise PhaseC1ContractError("self_report_claimed_admissible")
        if observer != "independent_human_observer":
            raise PhaseC1ContractError("observer_method_claimed_admissible")
        if temporal == "conversation":
            raise PhaseC1ContractError("conversation_card_claimed_admissible")
        if temporal not in ("turn", "bounded_segment"):
            raise PhaseC1ContractError("temporal_unit_claimed_admissible")
        if rater_count is None or rater_count < 2:
            raise PhaseC1ContractError("single_rater_claimed_admissible")
        if not reliability.preadjudication:
            raise PhaseC1ContractError("admissible_reliability_postadjudication")
    source_id = _string(raw["source_id"], code="source_reference_missing")
    if _SOURCE_ID_RE.fullmatch(source_id) is None:
        raise PhaseC1ContractError("source_reference_missing")
    return PhaseC1EvidenceCardV1(
        card_id=card_id, source_id=source_id, signal=signal,
        native_label=_string(raw["native_label"], code="native_label", maximum=128),
        native_definition_document_id=_string(raw["native_definition_document_id"], code="native_definition_document_missing"),
        native_definition_locator=_string(raw["native_definition_locator"], code="native_definition_locator_unbounded", maximum=512),
        native_definition_excerpt_sha256=_hash(raw["native_definition_excerpt_sha256"], code="native_definition_hash_malformed"),
        annotation_modality=modality, construct_correspondence=construct, temporal_unit=temporal,
        bounded_context_description=_enum(raw["bounded_context_description"], BOUNDED_CONTEXT_VALUES, code="bounded_context_description"),
        observer_method=observer, independent_rater_count=rater_count, reliability=reliability,
        claimed_status=claimed_status, claimed_reason_codes=reasons, limitations=limitations,
    )


def _document_ids(value: object, *, code: str) -> tuple[str, ...]:
    result = _string_tuple(value, code=code)
    if any(_DOCUMENT_ID_RE.fullmatch(item) is None for item in result):
        raise PhaseC1ContractError(code)
    return result


def _fallback_material(payload: object) -> PhaseC1FallbackMaterialEvidenceV1:
    raw = _mapping(payload, code="fallback_material_object")
    _exact_fields(raw, _FALLBACK_MATERIAL_FIELDS, code="fallback_material_fields")
    source_id = _string(raw["source_id"], code="source_reference_missing")
    if _SOURCE_ID_RE.fullmatch(source_id) is None:
        raise PhaseC1ContractError("source_reference_missing")
    return PhaseC1FallbackMaterialEvidenceV1(
        source_id=source_id,
        status=_enum(raw["status"], ANNOTATION_FALLBACK_STATUSES, code="fallback_material_status_mismatch"),
        public_spontaneous_material_status=_enum(raw["public_spontaneous_material_status"], FALLBACK_MATERIAL_STATUSES, code="fallback_material_status_mismatch"),
        license_status=_enum(raw["license_status"], LICENSE_STATUSES, code="fallback_material_status_mismatch"),
        ethical_use_status=_enum(raw["ethical_use_status"], ETHICAL_USE_STATUSES, code="fallback_material_status_mismatch"),
        minimum_three_raters_status=_enum(raw["minimum_three_raters_status"], FALLBACK_RATER_STATUSES, code="fallback_material_status_mismatch"),
        material_evidence_document_ids=_document_ids(raw["material_evidence_document_ids"], code="fallback_fact_document_unknown"),
        license_evidence_document_ids=_document_ids(raw["license_evidence_document_ids"], code="fallback_fact_document_unknown"),
        ethical_use_evidence_document_ids=_document_ids(raw["ethical_use_evidence_document_ids"], code="fallback_fact_document_unknown"),
        rater_feasibility_evidence_document_ids=_document_ids(raw["rater_feasibility_evidence_document_ids"], code="fallback_fact_document_unknown"),
    )


def parse_annotation_fallback_assessment(
    payload: object,
) -> PhaseC1AnnotationFallbackAssessmentV1:
    _forbidden_content(payload)
    raw = _mapping(payload, code="fallback_object")
    _exact_fields(raw, _FALLBACK_FIELDS, code="fallback_fields")
    signal = _enum(raw["signal"], TARGET_SIGNALS, code="fallback_signal_missing")
    if type(raw["preregistration_only"]) is not bool or type(raw["execution_authorized"]) is not bool:
        raise PhaseC1ContractError("fallback_boolean")
    if not raw["preregistration_only"] or raw["execution_authorized"]:
        raise PhaseC1ContractError("fallback_authorization")
    return PhaseC1AnnotationFallbackAssessmentV1(
        signal=signal,
        status=_enum(raw["status"], ANNOTATION_FALLBACK_STATUSES, code="fallback_status_unknown"),
        material_evidence=tuple(_fallback_material(item) for item in _sequence(raw["material_evidence"], code="fallback_material_evidence")),
        preregistration_only=raw["preregistration_only"],
        execution_authorized=raw["execution_authorized"],
        reason_codes=_ordered_tuple(raw["reason_codes"], _REASON_CODES, code="reason_codes_unsorted"),
    )


def _search_forbidden_content(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if (
                isinstance(key, str)
                and unicodedata.normalize("NFC", key).casefold()
                in _SEARCH_FORBIDDEN_KEYS
            ):
                raise PhaseC1ContractError("forbidden_search_content")
            _search_forbidden_content(item)
    elif isinstance(value, list):
        for item in value:
            _search_forbidden_content(item)


def _documentation_transport_hashes(
    value: object,
) -> tuple[str, ...]:
    raw = _sequence(value, code="documentation_transport_hashes")
    if len(raw) > 5:
        raise PhaseC1ContractError("documentation_transport_hashes")
    result = tuple(
        _hash(item, code="documentation_transport_hashes")
        for item in raw
    )
    if len(set(result)) != len(result):
        raise PhaseC1ContractError("documentation_transport_hashes")
    return result


def _optional_search_string(value: object, *, code: str) -> str | None:
    if value is None:
        return None
    return _string(value, code=code)


def _candidate_source_id(value: object, *, code: str) -> str:
    source_id = _string(value, code=code)
    if _SOURCE_ID_RE.fullmatch(source_id) is None:
        raise PhaseC1ContractError(code)
    return source_id


def _validate_disposition_fields(
    *,
    disposition: str,
    candidate_source_id: str | None,
    duplicate_reference: str | None,
    reason_code: str | None,
    documentation_hashes: tuple[str, ...],
    field_code: str,
    reason_code_error: str,
) -> None:
    rejection_reasons = frozenset(_REASON_CODES[:14])
    unresolved_reasons = frozenset(_REASON_CODES[14:])
    if disposition == "retained_candidate":
        if not documentation_hashes:
            raise PhaseC1ContractError("documentation_transport_hashes")
        if (
            candidate_source_id is None
            or duplicate_reference is not None
            or reason_code is not None
        ):
            raise PhaseC1ContractError(field_code)
        return
    if disposition == "duplicate":
        if (
            candidate_source_id is not None
            or duplicate_reference is None
            or reason_code is not None
            or documentation_hashes
        ):
            raise PhaseC1ContractError(field_code)
        return
    if disposition == "excluded":
        if not documentation_hashes:
            raise PhaseC1ContractError("documentation_transport_hashes")
        if (
            candidate_source_id is not None
            or duplicate_reference is not None
        ):
            raise PhaseC1ContractError(field_code)
        if reason_code not in rejection_reasons:
            raise PhaseC1ContractError(reason_code_error)
        return
    if (
        candidate_source_id is not None
        or duplicate_reference is not None
        or reason_code not in unresolved_reasons
    ):
        raise PhaseC1ContractError(
            reason_code_error
            if reason_code is not None
            else field_code
        )


def parse_discovery_record(payload: object) -> PhaseC1DiscoveryRecordV1:
    _search_forbidden_content(payload)
    raw = _mapping(payload, code="discovery_object")
    _exact_fields(raw, _DISCOVERY_FIELDS, code="discovery_fields")
    discovery_record_id = _string(
        raw["discovery_record_id"],
        code="discovery_record_id",
    )
    if _DISCOVERY_ID_RE.fullmatch(discovery_record_id) is None:
        raise PhaseC1ContractError("discovery_record_id")
    query_id = _string(raw["query_id"], code="discovery_query_id")
    rank = _integer(raw["rank"], code="discovery_rank", minimum=1, maximum=25)
    identity_sha256 = _hash(
        raw["identity_sha256"],
        code="discovery_identity_sha256",
    )
    disposition = _enum(
        raw["disposition"],
        DISCOVERY_DISPOSITIONS,
        code="discovery_disposition",
    )
    candidate_source_id = (
        None
        if raw["candidate_source_id"] is None
        else _candidate_source_id(
            raw["candidate_source_id"],
            code="discovery_candidate_source_id",
        )
    )
    duplicate_reference = _optional_search_string(
        raw["duplicate_of_discovery_record_id"],
        code="discovery_duplicate_reference",
    )
    if (
        duplicate_reference is not None
        and _DISCOVERY_ID_RE.fullmatch(duplicate_reference) is None
    ):
        raise PhaseC1ContractError("discovery_duplicate_reference")
    reason_code = _optional_search_string(
        raw["reason_code"],
        code="discovery_reason_partition",
    )
    documentation_hashes = _documentation_transport_hashes(
        raw["documentation_transport_receipt_sha256s"]
    )
    _validate_disposition_fields(
        disposition=disposition,
        candidate_source_id=candidate_source_id,
        duplicate_reference=duplicate_reference,
        reason_code=reason_code,
        documentation_hashes=documentation_hashes,
        field_code="discovery_disposition_fields",
        reason_code_error="discovery_reason_partition",
    )
    return PhaseC1DiscoveryRecordV1(
        discovery_record_id=discovery_record_id,
        query_id=query_id,
        rank=rank,
        identity_sha256=identity_sha256,
        disposition=disposition,
        candidate_source_id=candidate_source_id,
        duplicate_of_discovery_record_id=duplicate_reference,
        reason_code=reason_code,
        documentation_transport_receipt_sha256s=documentation_hashes,
    )


def parse_citation_record(payload: object) -> PhaseC1CitationRecordV1:
    _search_forbidden_content(payload)
    raw = _mapping(payload, code="citation_object")
    _exact_fields(raw, _CITATION_FIELDS, code="citation_fields")
    citation_record_id = _string(
        raw["citation_record_id"],
        code="citation_record_id",
    )
    match = _CITATION_ID_RE.fullmatch(citation_record_id)
    if match is None:
        raise PhaseC1ContractError("citation_record_id")
    signal = _enum(raw["signal"], TARGET_SIGNALS, code="citation_signal")
    direction = _enum(
        raw["direction"],
        CITATION_DIRECTIONS,
        code="citation_direction",
    )
    rank = _integer(raw["rank"], code="citation_rank", minimum=1, maximum=5)
    if (
        match.group(1) != signal
        or match.group(2) != direction
        or int(match.group(3)) != rank
    ):
        raise PhaseC1ContractError("citation_record_id")
    parent_source_id = _candidate_source_id(
        raw["parent_source_id"],
        code="citation_parent_source_id",
    )
    parent_document_hash = _hash(
        raw["parent_source_document_sha256"],
        code="citation_parent_document_sha256",
    )
    transport_hash = _hash(
        raw["transport_receipt_sha256"],
        code="citation_transport_receipt_sha256",
    )
    identity_hash = _hash(
        raw["identity_sha256"],
        code="citation_identity_sha256",
    )
    disposition = _enum(
        raw["disposition"],
        DISCOVERY_DISPOSITIONS,
        code="citation_disposition",
    )
    candidate_source_id = (
        None
        if raw["candidate_source_id"] is None
        else _candidate_source_id(
            raw["candidate_source_id"],
            code="citation_candidate_source_id",
        )
    )
    duplicate_reference = _optional_search_string(
        raw["duplicate_of_record_id"],
        code="citation_duplicate_reference",
    )
    if (
        duplicate_reference is not None
        and _DISCOVERY_ID_RE.fullmatch(duplicate_reference) is None
        and _CITATION_ID_RE.fullmatch(duplicate_reference) is None
    ):
        raise PhaseC1ContractError("citation_duplicate_reference")
    reason_code = _optional_search_string(
        raw["reason_code"],
        code="citation_reason_partition",
    )
    documentation_hashes = _documentation_transport_hashes(
        raw["documentation_transport_receipt_sha256s"]
    )
    _validate_disposition_fields(
        disposition=disposition,
        candidate_source_id=candidate_source_id,
        duplicate_reference=duplicate_reference,
        reason_code=reason_code,
        documentation_hashes=documentation_hashes,
        field_code="citation_disposition_fields",
        reason_code_error="citation_reason_partition",
    )
    return PhaseC1CitationRecordV1(
        citation_record_id=citation_record_id,
        signal=signal,
        direction=direction,
        rank=rank,
        parent_source_id=parent_source_id,
        parent_source_document_sha256=parent_document_hash,
        transport_receipt_sha256=transport_hash,
        identity_sha256=identity_hash,
        disposition=disposition,
        candidate_source_id=candidate_source_id,
        duplicate_of_record_id=duplicate_reference,
        reason_code=reason_code,
        documentation_transport_receipt_sha256s=documentation_hashes,
    )


def _query_record(
    payload: object,
    *,
    expected: tuple[str, str, str, str | None, str],
    seed_response_cap: int,
) -> PhaseC1QueryRecordV1:
    raw = _mapping(payload, code="query_object")
    _exact_fields(raw, _QUERY_FIELDS, code="query_fields")
    query_id = _string(raw["query_id"], code="search_query_grid")
    query_kind = _enum(raw["query_kind"], QUERY_KINDS, code="query_kind")
    channel_id = _string(raw["channel_id"], code="query_channel")
    signal = (
        None
        if raw["signal"] is None
        else _enum(raw["signal"], TARGET_SIGNALS, code="query_signal")
    )
    query_text = _string(raw["query_text"], code="query_text")
    if (
        query_id,
        query_kind,
        channel_id,
        signal,
        query_text,
    ) != expected:
        raise PhaseC1ContractError("search_query_grid")
    status = _enum(raw["status"], QUERY_STATUSES, code="query_status")
    incomplete_reason = _optional_search_string(
        raw["incomplete_reason"],
        code="query_incomplete_reason",
    )
    if (
        incomplete_reason is not None
        and incomplete_reason not in QUERY_INCOMPLETE_REASONS
    ):
        raise PhaseC1ContractError("query_incomplete_reason")
    result_limit = _integer(
        raw["result_limit"],
        code="query_result_limit",
        minimum=25,
        maximum=25,
    )
    response_sha256 = (
        None
        if raw["response_sha256"] is None
        else _hash(raw["response_sha256"], code="query_response_hash")
    )
    response_byte_count = _optional_integer(
        raw["response_byte_count"],
        code="query_response_bytes",
        minimum=1,
        maximum=seed_response_cap,
    )
    if (response_sha256 is None) != (response_byte_count is None):
        raise PhaseC1ContractError("query_response_pair")
    transport_receipt_sha256 = _hash(
        raw["transport_receipt_sha256"],
        code="query_transport_receipt_sha256",
    )
    result_count = _integer(
        raw["result_count"],
        code="query_result_reconciliation",
        minimum=0,
    )
    returned_count = _integer(
        raw["returned_count"],
        code="query_result_reconciliation",
        minimum=0,
    )
    if returned_count > 25:
        raise PhaseC1ContractError("query_returned_cap")
    if returned_count > result_count:
        raise PhaseC1ContractError("query_result_reconciliation")
    if type(raw["truncated"]) is not bool:
        raise PhaseC1ContractError("query_truncated")
    truncated = raw["truncated"]
    discovery_payloads = _sequence(
        raw["discovery_records"],
        code="query_result_reconciliation",
    )
    if len(discovery_payloads) > 25:
        raise PhaseC1ContractError("query_returned_cap")
    if status == "incomplete" and (
        result_count != 0
        or returned_count != 0
        or truncated
        or discovery_payloads
    ):
        raise PhaseC1ContractError("query_incomplete")
    if len(discovery_payloads) != returned_count:
        raise PhaseC1ContractError("query_result_reconciliation")
    discovery_records = tuple(
        parse_discovery_record(item) for item in discovery_payloads
    )
    if tuple(item.rank for item in discovery_records) != tuple(
        range(1, returned_count + 1)
    ):
        raise PhaseC1ContractError("discovery_rank")
    if any(item.query_id != query_id for item in discovery_records):
        raise PhaseC1ContractError("discovery_query_id")
    if status == "complete":
        if (
            incomplete_reason is not None
            or response_sha256 is None
            or response_byte_count is None
        ):
            raise PhaseC1ContractError("query_complete")
        if truncated != (result_count > returned_count):
            raise PhaseC1ContractError("query_truncated")
    else:
        if incomplete_reason is None:
            raise PhaseC1ContractError("query_incomplete_reason")
    return PhaseC1QueryRecordV1(
        query_id=query_id,
        query_kind=query_kind,
        channel_id=channel_id,
        signal=signal,
        query_text=query_text,
        status=status,
        incomplete_reason=incomplete_reason,
        result_limit=result_limit,
        response_sha256=response_sha256,
        response_byte_count=response_byte_count,
        transport_receipt_sha256=transport_receipt_sha256,
        result_count=result_count,
        returned_count=returned_count,
        truncated=truncated,
        discovery_records=discovery_records,
    )


def _exact_signal_mapping(
    value: object,
    *,
    code: str,
) -> Mapping[str, object]:
    result = _mapping(value, code=code)
    if frozenset(result) != frozenset(TARGET_SIGNALS):
        raise PhaseC1ContractError(code)
    return result


def _candidate_order_mapping(
    value: object,
) -> Mapping[str, tuple[str, ...]]:
    raw = _exact_signal_mapping(value, code="search_signal_order")
    result: dict[str, tuple[str, ...]] = {}
    for signal in TARGET_SIGNALS:
        source_ids = _string_tuple(
            raw[signal],
            code="search_candidate_order",
        )
        if any(_SOURCE_ID_RE.fullmatch(item) is None for item in source_ids):
            raise PhaseC1ContractError("search_candidate_order")
        result[signal] = source_ids
    return MappingProxyType(result)


def _nonnegative_signal_counts(
    value: object,
    *,
    code: str,
    maximum: int | None = None,
) -> Mapping[str, int]:
    raw = _exact_signal_mapping(value, code=code)
    result = {
        signal: _integer(
            raw[signal],
            code=code,
            minimum=0,
            maximum=maximum,
        )
        for signal in TARGET_SIGNALS
    }
    return MappingProxyType(result)


def _citation_stops(
    value: object,
) -> Mapping[str, str]:
    raw = _exact_signal_mapping(value, code="citation_stop_map")
    result = {
        signal: _enum(
            raw[signal],
            CITATION_STOP_STATUSES,
            code="citation_stop_map",
        )
        for signal in TARGET_SIGNALS
    }
    return MappingProxyType(result)


def _citation_attempt_hashes(
    value: object,
    *,
    protocol: PhaseC1ProtocolV1,
) -> Mapping[str, Mapping[str, tuple[str, ...]]]:
    raw = _exact_signal_mapping(
        value,
        code="citation_attempt_signal_map",
    )
    result: dict[str, Mapping[str, tuple[str, ...]]] = {}
    caps = {
        "backward": protocol.max_backward_citations_per_signal,
        "forward": protocol.max_forward_citations_per_signal,
    }
    for signal in TARGET_SIGNALS:
        directions = _mapping(
            raw[signal],
            code="citation_attempt_fields",
        )
        _exact_fields(
            directions,
            frozenset(CITATION_DIRECTIONS),
            code="citation_attempt_fields",
        )
        parsed_directions: dict[str, tuple[str, ...]] = {}
        for direction in CITATION_DIRECTIONS:
            attempts = tuple(
                _hash(item, code="citation_transport_attempts")
                for item in _sequence(
                    directions[direction],
                    code="citation_transport_attempts",
                )
            )
            if (
                len(attempts) > caps[direction]
                or len(set(attempts)) != len(attempts)
            ):
                raise PhaseC1ContractError("citation_transport_attempts")
            parsed_directions[direction] = attempts
        result[signal] = MappingProxyType(parsed_directions)
    return MappingProxyType(result)


def _claimed_fail_ready(
    value: object,
) -> Mapping[str, bool]:
    raw = _exact_signal_mapping(value, code="search_fail_ready")
    result: dict[str, bool] = {}
    for signal in TARGET_SIGNALS:
        if type(raw[signal]) is not bool:
            raise PhaseC1ContractError("search_fail_ready")
        result[signal] = raw[signal]
    return MappingProxyType(result)


def _first_unique_candidates(
    values: list[str],
) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def validate_search_ledger(
    payload: object,
    *,
    protocol: PhaseC1ProtocolV1,
) -> PhaseC1SearchLedgerV1:
    protocol = _validated_transport_protocol(protocol)
    _search_forbidden_content(payload)
    raw = _mapping(payload, code="search_ledger_object")
    _exact_fields(raw, _SEARCH_LEDGER_FIELDS, code="search_ledger_fields")
    if raw["schema_version"] != _SEARCH_LEDGER_SCHEMA:
        raise PhaseC1ContractError("search_ledger_schema")
    protocol_sha256 = _hash(
        raw["protocol_sha256"],
        code="search_protocol_sha256",
    )
    if protocol_sha256 != _FROZEN_PROTOCOL_SHA256:
        raise PhaseC1ContractError("search_protocol_sha256")

    expected_queries = expected_phase_c1_queries(protocol)
    query_payloads = _sequence(
        raw["query_records"],
        code="search_query_grid",
    )
    if len(query_payloads) != len(expected_queries):
        raise PhaseC1ContractError("search_query_grid")
    query_records = tuple(
        _query_record(
            item,
            expected=expected,
            seed_response_cap=protocol.max_response_bytes_by_transport_purpose[
                "seed_query"
            ],
        )
        for item, expected in zip(
            query_payloads,
            expected_queries,
            strict=True,
        )
    )
    query_transport_hashes = tuple(
        item.transport_receipt_sha256 for item in query_records
    )
    if len(set(query_transport_hashes)) != len(query_transport_hashes):
        raise PhaseC1ContractError("duplicate_query_transport_receipt")

    seen_record_ids: set[str] = set()
    identity_by_record_id: dict[str, str] = {}
    seen_identity_lanes: set[tuple[str, str]] = set()
    identity_by_candidate_source_id: dict[str, str] = {}
    for query in query_records:
        identity_lane = (
            "fallback_material"
            if query.query_kind == "fallback_material"
            else query.signal
        )
        for discovery in query.discovery_records:
            if discovery.discovery_record_id in seen_record_ids:
                raise PhaseC1ContractError(
                    "duplicate_discovery_record_id"
                )
            if (
                discovery.disposition == "duplicate"
                and discovery.duplicate_of_discovery_record_id
                not in seen_record_ids
            ):
                raise PhaseC1ContractError(
                    "discovery_duplicate_reference"
                )
            if (
                discovery.disposition == "duplicate"
                and identity_by_record_id[
                    discovery.duplicate_of_discovery_record_id
                ]
                != discovery.identity_sha256
            ):
                raise PhaseC1ContractError(
                    "discovery_duplicate_identity"
                )
            if (
                (identity_lane, discovery.identity_sha256)
                in seen_identity_lanes
                and discovery.disposition != "duplicate"
            ):
                raise PhaseC1ContractError(
                    "duplicate_identity_unaccounted"
                )
            if discovery.candidate_source_id is not None:
                previous_identity = identity_by_candidate_source_id.setdefault(
                    discovery.candidate_source_id,
                    discovery.identity_sha256,
                )
                if previous_identity != discovery.identity_sha256:
                    raise PhaseC1ContractError(
                        "candidate_source_identity"
                    )
            seen_record_ids.add(discovery.discovery_record_id)
            identity_by_record_id[
                discovery.discovery_record_id
            ] = discovery.identity_sha256
            seen_identity_lanes.add(
                (identity_lane, discovery.identity_sha256)
            )

    citation_records = tuple(
        parse_citation_record(item)
        for item in _sequence(
            raw["citation_records"],
            code="citation_records",
        )
    )
    citation_sort_keys = tuple(
        (
            TARGET_SIGNALS.index(item.signal),
            CITATION_DIRECTIONS.index(item.direction),
            item.rank,
        )
        for item in citation_records
    )
    if citation_sort_keys != tuple(sorted(citation_sort_keys)):
        raise PhaseC1ContractError("citation_order")
    for signal in TARGET_SIGNALS:
        for direction in CITATION_DIRECTIONS:
            group = tuple(
                item
                for item in citation_records
                if item.signal == signal and item.direction == direction
            )
            cap = (
                protocol.max_backward_citations_per_signal
                if direction == "backward"
                else protocol.max_forward_citations_per_signal
            )
            if len(group) > cap:
                raise PhaseC1ContractError("citation_cap")
            if tuple(item.rank for item in group) != tuple(
                range(1, len(group) + 1)
            ):
                raise PhaseC1ContractError("citation_rank")
    for citation in citation_records:
        if citation.citation_record_id in seen_record_ids:
            raise PhaseC1ContractError("duplicate_citation_record_id")
        if (
            citation.disposition == "duplicate"
            and citation.duplicate_of_record_id not in seen_record_ids
        ):
            raise PhaseC1ContractError("citation_duplicate_reference")
        if (
            citation.disposition == "duplicate"
            and identity_by_record_id[citation.duplicate_of_record_id]
            != citation.identity_sha256
        ):
            raise PhaseC1ContractError("citation_duplicate_identity")
        if (
            (citation.signal, citation.identity_sha256)
            in seen_identity_lanes
            and citation.disposition != "duplicate"
        ):
            raise PhaseC1ContractError("duplicate_identity_unaccounted")
        if citation.candidate_source_id is not None:
            previous_identity = identity_by_candidate_source_id.setdefault(
                citation.candidate_source_id,
                citation.identity_sha256,
            )
            if previous_identity != citation.identity_sha256:
                raise PhaseC1ContractError("candidate_source_identity")
        seen_record_ids.add(citation.citation_record_id)
        identity_by_record_id[
            citation.citation_record_id
        ] = citation.identity_sha256
        seen_identity_lanes.add(
            (citation.signal, citation.identity_sha256)
        )

    candidate_order = _candidate_order_mapping(
        raw["candidate_order_by_signal"]
    )
    overflow_counts = _nonnegative_signal_counts(
        raw["overflow_count_by_signal"],
        code="search_candidate_overflow",
    )
    fallback_order = _string_tuple(
        raw["fallback_material_candidate_order"],
        code="fallback_material_order_mismatch",
    )
    if any(_SOURCE_ID_RE.fullmatch(item) is None for item in fallback_order):
        raise PhaseC1ContractError("fallback_material_order_mismatch")
    fallback_overflow = _integer(
        raw["fallback_material_overflow_count"],
        code="fallback_material_overflow_mismatch",
        minimum=0,
    )
    backward_counts = _nonnegative_signal_counts(
        raw["backward_citation_count_by_signal"],
        code="citation_count_map",
        maximum=protocol.max_backward_citations_per_signal,
    )
    forward_counts = _nonnegative_signal_counts(
        raw["forward_citation_count_by_signal"],
        code="citation_count_map",
        maximum=protocol.max_forward_citations_per_signal,
    )
    backward_stops = _citation_stops(
        raw["backward_citation_stop_by_signal"]
    )
    forward_stops = _citation_stops(
        raw["forward_citation_stop_by_signal"]
    )
    citation_attempts = _citation_attempt_hashes(
        raw["citation_transport_receipt_sha256s_by_signal"],
        protocol=protocol,
    )
    flattened_citation_attempts = tuple(
        attempt
        for signal in TARGET_SIGNALS
        for direction in CITATION_DIRECTIONS
        for attempt in citation_attempts[signal][direction]
    )
    if len(set(flattened_citation_attempts)) != len(
        flattened_citation_attempts
    ):
        raise PhaseC1ContractError("citation_transport_attempts")
    if set(query_transport_hashes).intersection(
        flattened_citation_attempts
    ):
        raise PhaseC1ContractError("transport_receipt_authority")
    documentation_transport_hashes = {
        digest
        for query in query_records
        for discovery in query.discovery_records
        for digest in discovery.documentation_transport_receipt_sha256s
    }
    documentation_transport_hashes.update(
        digest
        for citation in citation_records
        for digest in citation.documentation_transport_receipt_sha256s
    )
    if documentation_transport_hashes.intersection(
        set(query_transport_hashes).union(flattened_citation_attempts)
    ):
        raise PhaseC1ContractError("transport_receipt_authority")
    claimed_fail_ready = _claimed_fail_ready(
        raw["fail_ready_by_signal"]
    )
    if type(raw["search_complete"]) is not bool:
        raise PhaseC1ContractError("search_complete")
    claimed_search_complete = raw["search_complete"]

    for signal in TARGET_SIGNALS:
        for direction, counts, stops in (
            ("backward", backward_counts, backward_stops),
            ("forward", forward_counts, forward_stops),
        ):
            actual_count = sum(
                item.signal == signal and item.direction == direction
                for item in citation_records
            )
            if counts[signal] != actual_count:
                raise PhaseC1ContractError("citation_count_mismatch")
            stop = stops[signal]
            cap = (
                protocol.max_backward_citations_per_signal
                if direction == "backward"
                else protocol.max_forward_citations_per_signal
            )
            if (
                (stop == "no_eligible_candidates" and actual_count != 0)
                or (stop == "budget_reached" and actual_count != cap)
            ):
                raise PhaseC1ContractError("citation_stop_count")
    for citation in citation_records:
        if (
            citation.transport_receipt_sha256
            not in citation_attempts[citation.signal][citation.direction]
        ):
            raise PhaseC1ContractError(
                "citation_transport_attempt_missing"
            )

    direct_candidates: dict[str, list[str]] = {
        signal: [] for signal in TARGET_SIGNALS
    }
    fallback_candidates: list[str] = []
    unresolved_by_signal = {
        signal: False for signal in TARGET_SIGNALS
    }
    fallback_unresolved = False
    for query in query_records:
        for discovery in query.discovery_records:
            if discovery.disposition == "retained_candidate":
                if query.query_kind == "fallback_material":
                    fallback_candidates.append(
                        discovery.candidate_source_id
                    )
                else:
                    direct_candidates[query.signal].append(
                        discovery.candidate_source_id
                    )
            elif discovery.disposition == "unresolved":
                if query.query_kind == "fallback_material":
                    fallback_unresolved = True
                else:
                    unresolved_by_signal[query.signal] = True
    for direction in CITATION_DIRECTIONS:
        for signal in TARGET_SIGNALS:
            for citation in citation_records:
                if (
                    citation.signal == signal
                    and citation.direction == direction
                ):
                    if citation.disposition == "retained_candidate":
                        direct_candidates[signal].append(
                            citation.candidate_source_id
                        )
                    elif citation.disposition == "unresolved":
                        unresolved_by_signal[signal] = True

    derived_candidate_order: dict[str, tuple[str, ...]] = {}
    derived_overflow: dict[str, int] = {}
    for signal in TARGET_SIGNALS:
        unique = _first_unique_candidates(direct_candidates[signal])
        derived_candidate_order[signal] = unique[
            : protocol.max_detailed_candidates_per_signal
        ]
        derived_overflow[signal] = max(
            0,
            len(unique) - protocol.max_detailed_candidates_per_signal,
        )
    unique_fallback = _first_unique_candidates(fallback_candidates)
    derived_fallback_order = unique_fallback[
        : protocol.max_detailed_fallback_material_candidates
    ]
    derived_fallback_overflow = max(
        0,
        len(unique_fallback)
        - protocol.max_detailed_fallback_material_candidates,
    )

    exhaustive_stops = frozenset(
        {"no_eligible_candidates", "source_list_exhausted"}
    )
    derived_fail_ready: dict[str, bool] = {}
    fallback_queries_ready = all(
        query.status == "complete" and not query.truncated
        for query in query_records
        if query.query_kind == "fallback_material"
    )
    for signal in TARGET_SIGNALS:
        direct_queries_ready = all(
            query.status == "complete" and not query.truncated
            for query in query_records
            if query.signal == signal
        )
        derived_fail_ready[signal] = (
            direct_queries_ready
            and fallback_queries_ready
            and backward_stops[signal] in exhaustive_stops
            and forward_stops[signal] in exhaustive_stops
            and not unresolved_by_signal[signal]
            and not fallback_unresolved
            and derived_overflow[signal] == 0
            and derived_fallback_overflow == 0
        )
        if (
            claimed_fail_ready[signal]
            and (
                overflow_counts[signal] > 0
                or fallback_overflow > 0
                or backward_stops[signal] not in exhaustive_stops
                or forward_stops[signal] not in exhaustive_stops
            )
        ):
            raise PhaseC1ContractError("search_fail_ready")

    if candidate_order != derived_candidate_order:
        raise PhaseC1ContractError("search_candidate_order")
    if dict(overflow_counts) != derived_overflow:
        raise PhaseC1ContractError("search_candidate_overflow")
    if fallback_order != derived_fallback_order:
        raise PhaseC1ContractError("fallback_material_order_mismatch")
    if fallback_overflow != derived_fallback_overflow:
        raise PhaseC1ContractError(
            "fallback_material_overflow_mismatch"
        )
    if dict(claimed_fail_ready) != derived_fail_ready:
        raise PhaseC1ContractError("search_fail_ready")

    derived_search_complete = (
        all(
            query.status == "complete" and not query.truncated
            for query in query_records
        )
        and all(
            backward_stops[signal] in exhaustive_stops
            and forward_stops[signal] in exhaustive_stops
            for signal in TARGET_SIGNALS
        )
    )
    if claimed_search_complete != derived_search_complete:
        raise PhaseC1ContractError("search_complete")

    return PhaseC1SearchLedgerV1(
        protocol_sha256=protocol_sha256,
        query_records=query_records,
        citation_records=citation_records,
        candidate_order_by_signal=MappingProxyType(
            derived_candidate_order
        ),
        overflow_count_by_signal=MappingProxyType(derived_overflow),
        fallback_material_candidate_order=derived_fallback_order,
        fallback_material_overflow_count=derived_fallback_overflow,
        backward_citation_count_by_signal=backward_counts,
        forward_citation_count_by_signal=forward_counts,
        backward_citation_stop_by_signal=backward_stops,
        forward_citation_stop_by_signal=forward_stops,
        citation_transport_receipt_sha256s_by_signal=citation_attempts,
        fail_ready_by_signal=MappingProxyType(derived_fail_ready),
        search_complete=derived_search_complete,
    )


def _search_orders(search: Mapping[str, object]) -> tuple[
    Mapping[str, tuple[str, ...]], tuple[str, ...], Mapping[str, bool]
]:
    candidates = _mapping(search.get("candidate_order_by_signal"), code="search_candidate_order")
    fail_ready = _mapping(search.get("fail_ready_by_signal"), code="search_fail_ready")
    if frozenset(candidates) != frozenset(TARGET_SIGNALS) or frozenset(fail_ready) != frozenset(TARGET_SIGNALS):
        raise PhaseC1ContractError("search_signal_order")
    parsed_candidates: dict[str, tuple[str, ...]] = {}
    parsed_fail_ready: dict[str, bool] = {}
    for signal in TARGET_SIGNALS:
        source_ids = _string_tuple(candidates[signal], code="search_candidate_order")
        if any(_SOURCE_ID_RE.fullmatch(item) is None for item in source_ids):
            raise PhaseC1ContractError("search_candidate_order")
        parsed_candidates[signal] = source_ids
        if type(fail_ready[signal]) is not bool:
            raise PhaseC1ContractError("search_fail_ready")
        parsed_fail_ready[signal] = fail_ready[signal]
    fallback = _string_tuple(search.get("fallback_material_candidate_order"), code="fallback_material_order_mismatch")
    if any(_SOURCE_ID_RE.fullmatch(item) is None for item in fallback):
        raise PhaseC1ContractError("fallback_material_order_mismatch")
    return MappingProxyType(parsed_candidates), fallback, MappingProxyType(parsed_fail_ready)


def _first_occurrence(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _material_status(item: PhaseC1FallbackMaterialEvidenceV1) -> str:
    facts = (
        (item.public_spontaneous_material_status, item.material_evidence_document_ids),
        (item.license_status, item.license_evidence_document_ids),
        (item.ethical_use_status, item.ethical_use_evidence_document_ids),
        (item.minimum_three_raters_status, item.rater_feasibility_evidence_document_ids),
    )
    if (
        item.public_spontaneous_material_status == "available"
        and item.license_status == "compatible"
        and item.ethical_use_status == "compatible"
        and item.minimum_three_raters_status == "feasible"
        and all(documents for _, documents in facts)
    ):
        return "feasible"
    unresolved = {"unresolved"}
    blockers = {"unavailable", "incompatible", "infeasible"}
    if (
        not any(value in unresolved for value, _ in facts)
        and any(value in blockers for value, _ in facts)
        and all(documents for _, documents in facts)
    ):
        return "infeasible"
    return "unresolved"


def validate_source_evidence_ledger(
    payload: object,
    *,
    protocol: PhaseC1ProtocolV1,
    search_ledger_bytes: bytes,
) -> PhaseC1SourceEvidenceLedgerV1:
    protocol = _validated_transport_protocol(protocol)
    _forbidden_content(payload)
    raw = _mapping(payload, code="source_ledger_object")
    _exact_fields(raw, _SOURCE_LEDGER_FIELDS, code="source_ledger_fields")
    if raw["schema_version"] != _SOURCE_LEDGER_SCHEMA:
        raise PhaseC1ContractError("source_ledger_schema")
    protocol_sha256 = _hash(raw["protocol_sha256"], code="source_protocol_sha256")
    if protocol_sha256 != _FROZEN_PROTOCOL_SHA256:
        raise PhaseC1ContractError("source_protocol_sha256")
    search_ledger_sha256 = _hash(raw["search_ledger_sha256"], code="fallback_search_hash_mismatch")
    if search_ledger_sha256 != sha256_bytes(search_ledger_bytes):
        raise PhaseC1ContractError("fallback_search_hash_mismatch")
    search = _mapping(load_json_strict(search_ledger_bytes, source="search_ledger"), code="search_ledger_object")
    candidates, fallback_order, fail_ready = _search_orders(search)
    sources = tuple(parse_source_receipt(item) for item in _sequence(raw["sources"], code="source_ledger_sources"))
    document_ids = tuple(
        document.document_id for source in sources for document in source.documents
    )
    if len(set(document_ids)) != len(document_ids):
        raise PhaseC1ContractError("duplicate_document_id")
    document_hashes = tuple(
        document.cached_sha256 for source in sources for document in source.documents
    )
    if len(set(document_hashes)) != len(document_hashes):
        raise PhaseC1ContractError("duplicate_document_hash")
    expected_source_ids = _first_occurrence(
        tuple(source_id for signal in TARGET_SIGNALS for source_id in candidates[signal])
        + fallback_order
    )
    if len({item.source_id for item in sources}) != len(sources):
        raise PhaseC1ContractError("source_id_mismatch")
    by_source = {item.source_id: item for item in sources}
    all_document_ids = {
        document.document_id for source in sources for document in source.documents
    }
    cards = tuple(parse_evidence_card(item) for item in _sequence(raw["cards"], code="source_ledger_cards"))
    assessments = tuple(parse_annotation_fallback_assessment(item) for item in _sequence(raw["fallback_assessments"], code="fallback_assessments"))
    referenced_source_ids = tuple(card.source_id for card in cards) + tuple(
        material.source_id
        for assessment in assessments
        for material in assessment.material_evidence
    )
    if any(source_id not in by_source for source_id in referenced_source_ids):
        raise PhaseC1ContractError("source_reference_missing")
    if tuple(item.source_id for item in sources) != expected_source_ids:
        raise PhaseC1ContractError("source_order")
    expected_pairs = tuple((signal, source_id) for signal in TARGET_SIGNALS for source_id in candidates[signal])
    actual_pairs = tuple((card.signal, card.source_id) for card in cards)
    if any(pair not in expected_pairs for pair in actual_pairs):
        raise PhaseC1ContractError("card_outside_candidate_pair")
    if actual_pairs != expected_pairs:
        raise PhaseC1ContractError("candidate_card_missing_or_duplicate")
    if len({card.card_id for card in cards}) != len(cards):
        raise PhaseC1ContractError("candidate_card_missing_or_duplicate")
    for card in cards:
        source = by_source.get(card.source_id)
        if source is None:
            raise PhaseC1ContractError("source_reference_missing")
        if "existing_annotation_evidence" not in source.phase_c1_roles:
            raise PhaseC1ContractError("source_role_missing_or_unknown")
        if card.native_definition_document_id not in {document.document_id for document in source.documents}:
            raise PhaseC1ContractError("native_definition_document_missing")
        if card.claimed_status == "admissible" and source.conversation_status == "acted_or_scripted":
            raise PhaseC1ContractError("acted_source_claimed_admissible")
        if card.claimed_status == "admissible" and source.conversation_status != "spontaneous_conversation":
            raise PhaseC1ContractError("conversation_card_claimed_admissible")
    if tuple(item.signal for item in assessments) != TARGET_SIGNALS:
        raise PhaseC1ContractError("fallback_signal_missing")
    for assessment in assessments:
        if tuple(item.source_id for item in assessment.material_evidence) != fallback_order:
            raise PhaseC1ContractError("fallback_material_order_mismatch")
        material_statuses: list[str] = []
        for material in assessment.material_evidence:
            source = by_source.get(material.source_id)
            if source is None:
                raise PhaseC1ContractError("source_reference_missing")
            if "fallback_material_candidate" not in source.phase_c1_roles:
                raise PhaseC1ContractError("source_role_missing_or_unknown")
            source_document_ids = {document.document_id for document in source.documents}
            for documents in (
                material.material_evidence_document_ids, material.license_evidence_document_ids,
                material.ethical_use_evidence_document_ids, material.rater_feasibility_evidence_document_ids,
            ):
                if any(document_id not in all_document_ids for document_id in documents):
                    raise PhaseC1ContractError("fallback_fact_document_unknown")
                if any(document_id not in source_document_ids for document_id in documents):
                    raise PhaseC1ContractError("fallback_fact_document_wrong_source")
            known_facts = (
                material.public_spontaneous_material_status,
                material.license_status,
                material.ethical_use_status,
                material.minimum_three_raters_status,
            )
            fact_documents = (
                material.material_evidence_document_ids,
                material.license_evidence_document_ids,
                material.ethical_use_evidence_document_ids,
                material.rater_feasibility_evidence_document_ids,
            )
            if material.status != "unresolved" and any(
                fact != "unresolved" and not documents
                for fact, documents in zip(known_facts, fact_documents, strict=True)
            ):
                raise PhaseC1ContractError("fallback_fact_evidence_missing")
            actual = _material_status(material)
            if material.status != actual:
                raise PhaseC1ContractError("fallback_material_status_mismatch")
            material_statuses.append(actual)
        expected_status = (
            "feasible" if "feasible" in material_statuses
            else "infeasible" if fail_ready[assessment.signal] and (not material_statuses or all(status == "infeasible" for status in material_statuses))
            else "unresolved"
        )
        expected_reasons = (
            ("annotation_fallback_feasible",) if expected_status == "feasible"
            else () if expected_status == "infeasible"
            else ("annotation_fallback_unresolved",)
        )
        if assessment.status != expected_status or assessment.reason_codes != expected_reasons:
            raise PhaseC1ContractError("fallback_reason_mismatch")
    return PhaseC1SourceEvidenceLedgerV1(protocol_sha256, search_ledger_sha256, sources, cards, assessments)


def _review_transport_hashes(
    search: Mapping[str, object],
    sources: tuple[PhaseC1SourceReceiptV1, ...],
) -> tuple[str, ...]:
    query_hashes: list[str] = []
    discovery_document_hashes: list[str] = []
    citation_hashes: list[str] = []
    citation_document_hashes: list[str] = []
    for query in _sequence(search.get("query_records"), code="reviewed_transport_hash_mismatch"):
        record = _mapping(query, code="reviewed_transport_hash_mismatch")
        query_hashes.append(_hash(record.get("transport_receipt_sha256"), code="reviewed_transport_hash_mismatch"))
        for discovery in _sequence(record.get("discovery_records"), code="reviewed_transport_hash_mismatch"):
            detail = _mapping(discovery, code="reviewed_transport_hash_mismatch")
            discovery_document_hashes.extend(_hash(item, code="reviewed_transport_hash_mismatch") for item in _sequence(detail.get("documentation_transport_receipt_sha256s"), code="reviewed_transport_hash_mismatch"))
    for citation in _sequence(search.get("citation_records"), code="reviewed_transport_hash_mismatch"):
        record = _mapping(citation, code="reviewed_transport_hash_mismatch")
        citation_hashes.append(_hash(record.get("transport_receipt_sha256"), code="reviewed_transport_hash_mismatch"))
        citation_document_hashes.extend(_hash(item, code="reviewed_transport_hash_mismatch") for item in _sequence(record.get("documentation_transport_receipt_sha256s"), code="reviewed_transport_hash_mismatch"))
    source_document_hashes = [
        document.transport_receipt_sha256
        for source in sources
        for document in source.documents
    ]
    return _first_occurrence(tuple(
        query_hashes
        + discovery_document_hashes
        + citation_hashes
        + citation_document_hashes
        + source_document_hashes
    ))


def validate_source_review_receipt(
    payload: object,
    *,
    protocol: PhaseC1ProtocolV1,
    search_ledger_bytes: bytes,
    source_evidence_ledger_bytes: bytes,
) -> PhaseC1SourceReviewReceiptV1:
    protocol = _validated_transport_protocol(protocol)
    _forbidden_content(payload)
    raw = _mapping(payload, code="source_review_object")
    _exact_fields(raw, _SOURCE_REVIEW_FIELDS, code="source_review_fields")
    if raw["schema_version"] != _SOURCE_REVIEW_SCHEMA:
        raise PhaseC1ContractError("source_review_schema")
    protocol_sha256 = _hash(raw["protocol_sha256"], code="review_protocol_sha256")
    search_ledger_sha256 = _hash(raw["search_ledger_sha256"], code="review_search_ledger_sha256")
    source_evidence_ledger_sha256 = _hash(raw["source_evidence_ledger_sha256"], code="review_source_ledger_sha256")
    if (
        protocol_sha256 != _FROZEN_PROTOCOL_SHA256
        or search_ledger_sha256 != sha256_bytes(search_ledger_bytes)
        or source_evidence_ledger_sha256 != sha256_bytes(source_evidence_ledger_bytes)
    ):
        raise PhaseC1ContractError("review_hash_binding")
    source_payload = load_json_strict(source_evidence_ledger_bytes, source="source_ledger")
    source_ledger = validate_source_evidence_ledger(
        source_payload, protocol=protocol, search_ledger_bytes=search_ledger_bytes
    )
    search = _mapping(load_json_strict(search_ledger_bytes, source="search_ledger"), code="search_ledger_object")
    transport_ledger_sha256 = _hash(raw["transport_ledger_sha256"], code="review_transport_ledger_sha256")
    reviewed_transport = tuple(_hash(item, code="reviewed_transport_hash_mismatch") for item in _sequence(raw["reviewed_transport_receipt_sha256s"], code="reviewed_transport_hash_mismatch"))
    reviewed_documents = tuple(_hash(item, code="reviewed_document_hash_omitted") for item in _sequence(raw["reviewed_document_sha256s"], code="reviewed_document_hash_omitted"))
    expected_documents = tuple(document.cached_sha256 for source in source_ledger.sources for document in source.documents)
    if reviewed_documents != expected_documents:
        raise PhaseC1ContractError("reviewed_document_hash_omitted")
    if reviewed_transport != _review_transport_hashes(search, source_ledger.sources):
        raise PhaseC1ContractError("reviewed_transport_hash_mismatch")
    review_scope = _string(raw["review_scope"], code="review_scope")
    if review_scope != _SOURCE_REVIEW_SCOPE:
        raise PhaseC1ContractError("review_scope")
    verdict = _enum(raw["verdict"], SOURCE_REVIEW_VERDICTS, code="review_verdict")
    counts = tuple(_integer(raw[field], code="review_findings", minimum=0) for field in ("critical_findings", "important_findings", "minor_findings"))
    boundary_values = tuple(raw[field] for field in ("raw_rows_read", "private_data_read", "model_evaluation_run", "provider_accessed", "runtime_modified"))
    if any(type(value) is not bool for value in boundary_values):
        raise PhaseC1ContractError("review_boundary_boolean")
    if verdict == "admitted" and any(counts):
        raise PhaseC1ContractError("review_admitted_with_findings")
    if verdict == "admitted" and any(boundary_values):
        raise PhaseC1ContractError("review_admitted_with_boundary_violation")
    if any(boundary_values) and verdict != "blocked":
        raise PhaseC1ContractError("review_boundary_violation")
    return PhaseC1SourceReviewReceiptV1(
        protocol_sha256, search_ledger_sha256, source_evidence_ledger_sha256,
        transport_ledger_sha256, reviewed_transport, reviewed_documents,
        review_scope, verdict, *counts, *boundary_values,
    )
