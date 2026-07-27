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
from urllib.parse import parse_qsl, urlsplit


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
        or "\\" in url
    ):
        raise PhaseC1ContractError(code)
    if port is not None and not 1 <= port <= 65535:
        raise PhaseC1ContractError(code)
    lowered = hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(lowered)
    except ValueError:
        pass
    else:
        raise PhaseC1ContractError(code)
    _public_dns_hostname(hostname, code=code)
    if any(segment in {".", ".."} for segment in parsed.path.split("/")):
        raise PhaseC1ContractError(code)
    for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
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
