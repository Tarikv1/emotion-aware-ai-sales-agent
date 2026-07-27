from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass

from scripts import emotion_state_phase_c1_contracts as phase_c1


@dataclass(frozen=True, slots=True)
class PhaseC1CandidateDispositionV1:
    card_id: str
    status: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseC1SignalDecisionV1:
    signal: str
    decision: str
    admissible_card_ids: tuple[str, ...]
    rejected_card_count: int
    unresolved_card_count: int
    annotation_fallback: str
    c2_eligible: bool


@dataclass(frozen=True, slots=True)
class PhaseC1AdmissionProjectionV1:
    candidate_dispositions: tuple[PhaseC1CandidateDispositionV1, ...]
    signal_decisions: tuple[PhaseC1SignalDecisionV1, ...]
    overall_decision: str
    c2_eligible_signals: tuple[str, ...]


def _ordered_reasons(
    protocol: phase_c1.PhaseC1ProtocolV1,
    reasons: set[str],
) -> tuple[str, ...]:
    return tuple(code for code in protocol.reason_code_order if code in reasons)


def _require_protocol(protocol: phase_c1.PhaseC1ProtocolV1) -> None:
    protocol_bytes = _canonical_dataclass_bytes(
        protocol, "EmotionStatePhaseC1DiscoveryProtocolV1"
    )
    phase_c1.validate_discovery_protocol(
        phase_c1.load_json_strict(protocol_bytes, source="protocol")
    )
    if (
        protocol.target_signals != phase_c1.TARGET_SIGNALS
        or protocol.candidate_status_order
        != ("admissible", "rejected", "unresolved")
        or protocol.signal_decision_order != ("pass", "defer", "fail")
        or protocol.overall_decision_order
        != (
            "proceed_full_to_c2",
            "proceed_partial_to_c2",
            "defer_c2",
            "stop_c2",
        )
    ):
        raise phase_c1.PhaseC1ContractError("decision_protocol")


def _json_value(value: object) -> object:
    if is_dataclass(value):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def _canonical_dataclass_bytes(value: object, schema_version: str) -> bytes:
    payload = _json_value(value)
    if not isinstance(payload, dict):
        raise phase_c1.PhaseC1ContractError("decision_payload")
    return phase_c1.canonical_json_bytes(
        {"schema_version": schema_version, **payload}
    )


def _reliability_rule(
    protocol: phase_c1.PhaseC1ProtocolV1,
    metric_id: str,
) -> Mapping[str, int | str] | None:
    for rule in protocol.reliability_rules:
        if rule.get("metric_id") == metric_id:
            return rule
    return None


def derive_reliability_status(
    evidence: phase_c1.PhaseC1ReliabilityEvidenceV1,
    *,
    independent_rater_count: int | None,
    protocol: phase_c1.PhaseC1ProtocolV1,
) -> tuple[str, tuple[str, ...]]:
    """Derive the frozen alpha gate without reading or mutating external state."""
    _require_protocol(protocol)
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
    elif rated is not None and rated < positives:
        raise phase_c1.PhaseC1ContractError("positive_count_exceeds_rated_units")
    elif positives < int(protocol.positive_support_rule["minimum_published_positive_count"]):
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

    effective_sample_sufficient = not {
        "rater_count_unresolved",
        "reliability_effective_sample_insufficient",
        "published_positive_count_missing",
        "positive_support_below_93",
    }.intersection(reasons)
    if (
        not evidence.verifiable
        or not evidence.preadjudication
        or rule is None
        or not effective_sample_sufficient
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


def derive_candidate_disposition(
    source: phase_c1.PhaseC1SourceReceiptV1,
    card: phase_c1.PhaseC1EvidenceCardV1,
    *,
    protocol: phase_c1.PhaseC1ProtocolV1,
) -> PhaseC1CandidateDispositionV1:
    _require_protocol(protocol)
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
        raise phase_c1.PhaseC1ContractError("native_definition_document_missing")
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
        raise phase_c1.PhaseC1ContractError("signal_construct_order")
    if card.native_label in construct["excluded_proxies"]:
        rejected.add("proxy_construct")
    if source.source_id != card.source_id:
        raise phase_c1.PhaseC1ContractError("source_reference_missing")
    if source.access_status == "login_required":
        rejected.add("access_requires_login")
    elif source.access_status == "restricted":
        rejected.add("access_restricted")
    elif source.access_status == "unresolved":
        unresolved.add("access_unresolved")
    if source.license_status == "incompatible":
        rejected.add("license_incompatible")
    elif source.license_status == "unresolved":
        unresolved.add("license_unresolved")
    if source.ethical_use_status == "incompatible":
        rejected.add("ethical_use_incompatible")
    elif source.ethical_use_status == "unresolved":
        unresolved.add("ethical_use_unresolved")
    if source.conversation_status == "acted_or_scripted":
        rejected.add("acted_or_scripted")
    elif source.conversation_status == "mixed_unseparated":
        rejected.add("mixed_unseparated_conversation")
    elif source.conversation_status == "unresolved":
        unresolved.add("conversation_status_unresolved")
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

    reliability_status, reliability_reasons = derive_reliability_status(
        card.reliability,
        independent_rater_count=card.independent_rater_count,
        protocol=protocol,
    )
    for reason in reliability_reasons:
        if reason == "reliability_upper_below_0_67":
            rejected.add(reason)
        else:
            unresolved.add(reason)
    if rejected:
        return PhaseC1CandidateDispositionV1(
            card.card_id, "rejected", _ordered_reasons(protocol, rejected)
        )
    if unresolved:
        return PhaseC1CandidateDispositionV1(
            card.card_id, "unresolved", _ordered_reasons(protocol, unresolved)
        )
    if reliability_status == "pass":
        return PhaseC1CandidateDispositionV1(card.card_id, "admissible", ())
    if reliability_status == "rejected":
        return PhaseC1CandidateDispositionV1(
            card.card_id,
            "rejected",
            ("reliability_upper_below_0_67",),
        )
    return PhaseC1CandidateDispositionV1(
        card.card_id, "unresolved", _ordered_reasons(protocol, set(reliability_reasons))
    )


def _derived_material_status(
    material: phase_c1.PhaseC1FallbackMaterialEvidenceV1,
    source: phase_c1.PhaseC1SourceReceiptV1,
    all_document_ids: set[str],
) -> str:
    source_document_ids = {document.document_id for document in source.documents}
    document_groups = (
        material.material_evidence_document_ids,
        material.license_evidence_document_ids,
        material.ethical_use_evidence_document_ids,
        material.rater_feasibility_evidence_document_ids,
    )
    for documents in document_groups:
        if any(document not in all_document_ids for document in documents):
            raise phase_c1.PhaseC1ContractError("fallback_fact_document_unknown")
        if any(document not in source_document_ids for document in documents):
            raise phase_c1.PhaseC1ContractError(
                "fallback_fact_document_wrong_source"
            )
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
        and any(value in {"unavailable", "incompatible", "infeasible"} for value in facts)
    ):
        return "infeasible"
    return "unresolved"


def _fallback_status(
    signal: str,
    *,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
) -> str:
    assessments = source_ledger.fallback_assessments
    if tuple(item.signal for item in assessments) != phase_c1.TARGET_SIGNALS:
        raise phase_c1.PhaseC1ContractError("fallback_signal_missing")
    assessment = assessments[phase_c1.TARGET_SIGNALS.index(signal)]
    if not assessment.preregistration_only or assessment.execution_authorized:
        raise phase_c1.PhaseC1ContractError("fallback_authorization")
    expected_order = search_ledger.fallback_material_candidate_order
    if tuple(item.source_id for item in assessment.material_evidence) != expected_order:
        raise phase_c1.PhaseC1ContractError("fallback_material_order_mismatch")
    sources = {source.source_id: source for source in source_ledger.sources}
    all_document_ids = {
        document.document_id
        for source in source_ledger.sources
        for document in source.documents
    }
    statuses: list[str] = []
    for material in assessment.material_evidence:
        source = sources.get(material.source_id)
        if source is None or "fallback_material_candidate" not in source.phase_c1_roles:
            raise phase_c1.PhaseC1ContractError("source_reference_missing")
        material_status = _derived_material_status(
            material, source, all_document_ids
        )
        if material.status != material_status:
            raise phase_c1.PhaseC1ContractError(
                "fallback_material_status_mismatch"
            )
        statuses.append(material_status)
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
        raise phase_c1.PhaseC1ContractError("fallback_reason_mismatch")
    return derived


def derive_signal_decision(
    signal: str,
    dispositions: tuple[PhaseC1CandidateDispositionV1, ...],
    cards: Mapping[str, phase_c1.PhaseC1EvidenceCardV1],
    *,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
) -> PhaseC1SignalDecisionV1:
    if signal not in phase_c1.TARGET_SIGNALS:
        raise phase_c1.PhaseC1ContractError("card_signal_not_in_protocol")
    card_ids = tuple(item.card_id for item in dispositions)
    if (
        card_ids != tuple(cards)
        or len(set(card_ids)) != len(card_ids)
        or any(card_id not in cards for card_id in card_ids)
    ):
        raise phase_c1.PhaseC1ContractError("candidate_card_missing_or_duplicate")
    selected = tuple(item for item in dispositions if cards[item.card_id].signal == signal)
    if any(item.status not in ("admissible", "rejected", "unresolved") for item in selected):
        raise phase_c1.PhaseC1ContractError("candidate_status")
    admissible = tuple(item.card_id for item in selected if item.status == "admissible")
    unresolved = sum(item.status == "unresolved" for item in selected)
    rejected = sum(item.status == "rejected" for item in selected)
    fallback = _fallback_status(
        signal, search_ledger=search_ledger, source_ledger=source_ledger
    )
    fail_guard_blocked = (
        search_ledger.overflow_count_by_signal[signal] > 0
        or search_ledger.fallback_material_overflow_count > 0
        or any(
            query.status != "complete" or query.truncated
            for query in search_ledger.query_records
            if query.signal == signal or query.query_kind == "fallback_material"
        )
        or search_ledger.backward_citation_stop_by_signal[signal]
        in {"budget_reached", "incomplete"}
        or search_ledger.forward_citation_stop_by_signal[signal]
        in {"budget_reached", "incomplete"}
    )
    if admissible:
        result = "pass"
    elif (
        unresolved
        or fail_guard_blocked
        or not search_ledger.fail_ready_by_signal[signal]
        or fallback in {"feasible", "unresolved"}
    ):
        result = "defer"
    else:
        result = "fail"
    return PhaseC1SignalDecisionV1(
        signal, result, admissible, rejected, unresolved, fallback, result == "pass"
    )


def _require_review(
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
    review_receipt: phase_c1.PhaseC1SourceReviewReceiptV1,
) -> None:
    _require_protocol(protocol)
    protocol_bytes = _canonical_dataclass_bytes(
        protocol, "EmotionStatePhaseC1DiscoveryProtocolV1"
    )
    protocol_sha256 = phase_c1.sha256_bytes(protocol_bytes)
    if (
        review_receipt.protocol_sha256 != protocol_sha256
        or search_ledger.protocol_sha256 != protocol_sha256
        or source_ledger.protocol_sha256 != protocol_sha256
    ):
        raise phase_c1.PhaseC1ContractError("decision_protocol_hash_mismatch")
    search_bytes = _canonical_dataclass_bytes(
        search_ledger, "EmotionStatePhaseC1SearchLedgerV1"
    )
    search_sha256 = phase_c1.sha256_bytes(search_bytes)
    if (
        review_receipt.search_ledger_sha256 != search_sha256
        or source_ledger.search_ledger_sha256 != search_sha256
    ):
        raise phase_c1.PhaseC1ContractError("decision_search_hash_mismatch")
    source_bytes = _canonical_dataclass_bytes(
        source_ledger, "EmotionStatePhaseC1SourceEvidenceLedgerV1"
    )
    if review_receipt.source_evidence_ledger_sha256 != phase_c1.sha256_bytes(source_bytes):
        raise phase_c1.PhaseC1ContractError("decision_source_hash_mismatch")
    if (
        review_receipt.verdict != "admitted"
        or any(
            (
                review_receipt.critical_findings,
                review_receipt.important_findings,
                review_receipt.minor_findings,
            )
        )
        or any(
            (
                review_receipt.raw_rows_read,
                review_receipt.private_data_read,
                review_receipt.model_evaluation_run,
                review_receipt.provider_accessed,
                review_receipt.runtime_modified,
            )
        )
    ):
        raise phase_c1.PhaseC1ContractError("decision_review_binding")


def project_phase_c1_admission(
    *,
    protocol: phase_c1.PhaseC1ProtocolV1,
    search_ledger: phase_c1.PhaseC1SearchLedgerV1,
    source_ledger: phase_c1.PhaseC1SourceEvidenceLedgerV1,
    review_receipt: phase_c1.PhaseC1SourceReviewReceiptV1,
) -> PhaseC1AdmissionProjectionV1:
    _require_review(protocol, search_ledger, source_ledger, review_receipt)
    sources = {source.source_id: source for source in source_ledger.sources}
    cards = {card.card_id: card for card in source_ledger.cards}
    if len(cards) != len(source_ledger.cards):
        raise phase_c1.PhaseC1ContractError("candidate_card_missing_or_duplicate")
    expected_pairs = tuple(
        (signal, source_id)
        for signal in protocol.target_signals
        for source_id in search_ledger.candidate_order_by_signal[signal]
    )
    actual_pairs = tuple((card.signal, card.source_id) for card in source_ledger.cards)
    if actual_pairs != expected_pairs:
        raise phase_c1.PhaseC1ContractError("candidate_card_missing_or_duplicate")
    dispositions: list[PhaseC1CandidateDispositionV1] = []
    for card in source_ledger.cards:
        source = sources.get(card.source_id)
        if source is None:
            raise phase_c1.PhaseC1ContractError("source_reference_missing")
        disposition = derive_candidate_disposition(source, card, protocol=protocol)
        if (
            card.claimed_status != disposition.status
            or card.claimed_reason_codes != disposition.reason_codes
        ):
            raise phase_c1.PhaseC1ContractError("card_claim_mismatch")
        dispositions.append(disposition)
    decision_rows = tuple(
        derive_signal_decision(
            signal, tuple(dispositions), cards,
            search_ledger=search_ledger, source_ledger=source_ledger,
        )
        for signal in protocol.target_signals
    )
    decisions = tuple(item.decision for item in decision_rows)
    if all(value == "pass" for value in decisions):
        overall = "proceed_full_to_c2"
    elif any(value == "pass" for value in decisions):
        overall = "proceed_partial_to_c2"
    elif any(value == "defer" for value in decisions):
        overall = "defer_c2"
    else:
        overall = "stop_c2"
    eligible = tuple(item.signal for item in decision_rows if item.c2_eligible)
    return PhaseC1AdmissionProjectionV1(tuple(dispositions), decision_rows, overall, eligible)
