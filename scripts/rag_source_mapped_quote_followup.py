from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID = "RAG-014-source-mapped-quote-followup"
RAG013_CLEANUP_STRATEGY_ID = "RAG-013-cleanup-strategy"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


ACCEPTED_FOLLOWUP_RULES_BY_CHUNK_ID: dict[str, dict[str, Any]] = {
    "rag005-chunk-003": {
        "knowledge_id": "rag014-response-neutral-pain-reflection",
        "lane": "response_wording",
        "project_rule": "When a customer names a problem, reflect one short neutral phrase back as a clarification question before moving deeper.",
        "safe_application": "Use once to verify the problem in the customer's words and invite elaboration only if they want to explain.",
        "do_not_use_when": "Do not parrot the customer, use repetitive mirroring, or keep probing after a short answer, correction, or refusal.",
        "guardrail_notes": "Reflection must clarify, not extract disclosure. The customer can correct the phrase or decline to expand.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-006": {
        "knowledge_id": "rag014-response-consent-based-schedule-confirmation",
        "lane": "response_wording",
        "project_rule": "After a customer voluntarily agrees to a meeting or callback, confirm the date, time, channel, and expected next step in one concise check.",
        "safe_application": "Use only after explicit agreement, and optionally ask whether a reminder or calendar invite is helpful.",
        "do_not_use_when": "Do not stack confirmations before consent, imply commitment that was not given, or maximize attendance through pressure.",
        "guardrail_notes": "Confirmation protects clarity and consent; it cannot become a compliance workaround or pressure loop.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-081": {
        "knowledge_id": "rag014-response-cost-of-inaction-check",
        "lane": "response_wording",
        "project_rule": "When a customer has confirmed a problem and prefers to wait, ask neutrally whether keeping the current path has a cost worth considering.",
        "safe_application": "Use as one cost-of-inaction check tied only to customer-confirmed facts and campaign-approved impacts.",
        "do_not_use_when": "Do not invent hidden costs, fear-monger, shame indecision, or use this when the customer sounds anxious or overwhelmed.",
        "guardrail_notes": "The agent may surface tradeoffs, but the customer owns the timing and can choose no next step.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-084": {
        "knowledge_id": "rag014-response-validate-prior-investment",
        "lane": "response_wording",
        "project_rule": "Validate the customer's prior effort before comparing future tradeoffs.",
        "safe_application": "Use when a customer has invested time, money, work, or reputation into a current tool, provider, or process.",
        "do_not_use_when": "Do not call their valuation irrational, dismiss the current setup, attack past decisions, or force a pivot.",
        "guardrail_notes": "After validation, compare only campaign-approved ROI, effort, risk, and fit tradeoffs.",
        "voice_or_prosody_advisory_only": False,
    },
}


REJECTED_FOLLOWUP_RULES_BY_CHUNK_ID: dict[str, dict[str, Any]] = {
    "rag005-chunk-005": {
        "review_verdict": "rejected_pressure_or_control_tactic",
        "rejection_reason": "Fixed rep talk-time dominance optimizes control over listening and does not fit a low-pressure, vertical-agnostic sales-agent core.",
        "rejection_category": "pressure_or_control_tactic",
        "replacement_guidance": "Favor customer-led listening, concise answers, and campaign-stage-specific discovery instead of a fixed agent talk-time target.",
    }
}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_project_path(path_value: Path | str, root: Path) -> Path:
    path = Path(path_value)
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    root_resolved = root.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"RAG-014 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-014 path is restricted: {path_value}")
    return resolved


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _runtime_boundaries_are_disabled(payload: dict[str, Any], *, context: str) -> None:
    summary = payload.get("summary", payload)
    boundaries = payload.get("boundaries", {})
    for key in (
        "runtime_retrieval_enabled",
        "retrieval_used_in_runtime",
        "runtime_use_allowed",
        "runtime_eligible_now",
        "retrieval_eligible_now",
        "chunk_import_enabled",
        "provider_calls_made",
        "external_provider_calls_made",
        "notebooklm_api_used",
        "private_customer_data_used",
        "reads_data_private",
        "auto_promote_allowed",
        "source_excerpt_text_stored",
    ):
        if summary.get(key) is True or boundaries.get(key) is True or payload.get(key) is True:
            raise ValueError(f"{context} enables forbidden runtime boundary: {key}")


def validate_inputs(
    rag013_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> None:
    if rag013_payload.get("cleanup_strategy_id") != RAG013_CLEANUP_STRATEGY_ID:
        raise ValueError("RAG-014 requires the RAG-013 cleanup strategy artifact.")
    if rag013_payload.get("recommended_next_checkpoint") != RAG_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID:
        raise ValueError("RAG-013 must recommend RAG-014 as the next checkpoint.")
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-014 requires the RAG-009 all-source review coverage artifact.")
    if case_payload.get("source_mapped_quote_followup_id") != RAG_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID:
        raise ValueError("RAG-014 case ID does not match.")
    for context, payload in (
        ("RAG-013 input", rag013_payload),
        ("RAG-009 input", rag009_payload),
        ("RAG-014 case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _followup_cards_by_id(rag013_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for card in rag013_payload.get("source_mapped_quote_followups", []):
        chunk_id = str(card.get("chunk_id", "")).strip()
        if chunk_id:
            cards[chunk_id] = dict(card)
    return cards


def _id_set(case_payload: dict[str, Any], key: str) -> set[str]:
    return {str(value).strip() for value in case_payload.get(key, []) if str(value).strip()}


def _validate_review_scope(cards_by_id: dict[str, dict[str, Any]], accepted_ids: set[str], rejected_ids: set[str]) -> None:
    overlap = accepted_ids.intersection(rejected_ids)
    if overlap:
        raise ValueError(f"RAG-014 accepted and rejected ID sets overlap: {sorted(overlap)}")
    card_ids = set(cards_by_id)
    reviewed_ids = accepted_ids.union(rejected_ids)
    missing = card_ids.difference(reviewed_ids)
    unexpected = reviewed_ids.difference(card_ids)
    if missing:
        raise ValueError(f"RAG-014 follow-up chunks missing review decisions: {sorted(missing)}")
    if unexpected:
        raise ValueError(f"RAG-014 review decisions reference unknown follow-up chunks: {sorted(unexpected)}")


def _source_ids(card: dict[str, Any]) -> list[str]:
    return [str(source_id) for source_id in card.get("accepted_source_ids", []) if str(source_id).strip()]


def build_accepted_quote_clearance_items(
    cards_by_id: dict[str, dict[str, Any]],
    details_by_id: dict[str, dict[str, Any]],
    accepted_ids: set[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for chunk_id in sorted(accepted_ids):
        card = cards_by_id[chunk_id]
        detail = details_by_id.get(chunk_id)
        if detail is None:
            raise ValueError(f"RAG-014 accepted follow-up chunk is missing RAG-009 details: {chunk_id}")
        rewrite = ACCEPTED_FOLLOWUP_RULES_BY_CHUNK_ID.get(chunk_id)
        if rewrite is None:
            raise ValueError(f"RAG-014 has no project-owned follow-up rewrite for chunk: {chunk_id}")
        items.append(
            {
                "knowledge_id": str(rewrite["knowledge_id"]),
                "chunk_id": chunk_id,
                "lane": str(rewrite["lane"]),
                "source_ids": _source_ids(card),
                "source_title": str(card.get("source_title", detail.get("source_title", ""))),
                "accepted_canonical_title": str(card.get("accepted_canonical_title", "")),
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", detail.get("topic_ids", []))],
                "original_candidate_principle": str(detail.get("principle", "")),
                "review_verdict": "manual_source_mapped_quote_clearance_paraphrased",
                "quote_dependency_resolved": True,
                "source_mapping_resolved": True,
                "source_mapped_followup_resolved": True,
                "human_acceptance_recorded": True,
                "project_rule": str(rewrite["project_rule"]),
                "safe_application": str(rewrite["safe_application"]),
                "do_not_use_when": str(rewrite["do_not_use_when"]),
                "guardrail_notes": str(rewrite["guardrail_notes"]),
                "voice_or_prosody_advisory_only": bool(rewrite["voice_or_prosody_advisory_only"]),
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
                "manual_review_clearance": {
                    "quote_clearance_resolution": "source_mapped_project_owned_paraphrase_accepted",
                    "source_excerpt_text_copied": False,
                    "runtime_use_allowed": False,
                },
            }
        )
    return items


def build_rejected_followup_items(
    cards_by_id: dict[str, dict[str, Any]],
    details_by_id: dict[str, dict[str, Any]],
    rejected_ids: set[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for chunk_id in sorted(rejected_ids):
        card = cards_by_id[chunk_id]
        detail = details_by_id.get(chunk_id)
        if detail is None:
            raise ValueError(f"RAG-014 rejected follow-up chunk is missing RAG-009 details: {chunk_id}")
        rejection = REJECTED_FOLLOWUP_RULES_BY_CHUNK_ID.get(chunk_id)
        if rejection is None:
            raise ValueError(f"RAG-014 has no rejection rule for follow-up chunk: {chunk_id}")
        items.append(
            {
                "chunk_id": chunk_id,
                "lane": "response_wording",
                "source_ids": _source_ids(card),
                "source_title": str(card.get("source_title", detail.get("source_title", ""))),
                "accepted_canonical_title": str(card.get("accepted_canonical_title", "")),
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", detail.get("topic_ids", []))],
                "original_candidate_principle": str(detail.get("principle", "")),
                "review_verdict": str(rejection["review_verdict"]),
                "rejection_category": str(rejection["rejection_category"]),
                "rejection_reason": str(rejection["rejection_reason"]),
                "replacement_guidance": str(rejection["replacement_guidance"]),
                "quote_dependency_resolved": False,
                "source_mapping_resolved": True,
                "followup_resolved_by_rejection": True,
                "project_owned_rule_created": False,
                "human_rejection_recorded": True,
                "voice_or_prosody_advisory_only": False,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    return items


def build_source_mapped_quote_followup(
    rag013_result_path: Path | str,
    rag009_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag013_path = resolve_project_path(rag013_result_path, root_path)
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag013_payload = load_json(rag013_path)
    rag009_payload = load_json(rag009_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag013_payload, rag009_payload, case_payload)

    cards_by_id = _followup_cards_by_id(rag013_payload)
    details_by_id = _chunk_details_by_id(rag009_payload)
    accepted_ids = _id_set(case_payload, "accepted_followup_chunk_ids")
    rejected_ids = _id_set(case_payload, "rejected_followup_chunk_ids")
    _validate_review_scope(cards_by_id, accepted_ids, rejected_ids)
    accepted_items = build_accepted_quote_clearance_items(cards_by_id, details_by_id, accepted_ids)
    rejected_items = build_rejected_followup_items(cards_by_id, details_by_id, rejected_ids)
    accepted_lane_counts = Counter(item["lane"] for item in accepted_items)
    followup_count = len(cards_by_id)
    accepted_count = len(accepted_items)
    rejected_count = len(rejected_items)
    summary = {
        "followup_candidate_count": followup_count,
        "accepted_followup_count": accepted_count,
        "rejected_followup_count": rejected_count,
        "accepted_quote_clearance_item_count": accepted_count,
        "rejected_quote_clearance_item_count": rejected_count,
        "source_mapped_quote_followups_cleared_by_acceptance": accepted_count,
        "source_mapped_quote_followups_rejected": rejected_count,
        "source_mapped_quote_followups_remaining_after_review": max(followup_count - accepted_count - rejected_count, 0),
        "cleanup_decisions_applied_now": accepted_count + rejected_count,
        "auto_promoted_chunk_count": 0,
        "accepted_lane_counts": dict(accepted_lane_counts),
        "runtime_retrieval_enabled": False,
        "retrieval_eligible_now": False,
        "chunk_import_enabled": False,
        "source_excerpt_text_stored": False,
        "provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
        "reads_data_private": False,
    }
    return {
        "source_mapped_quote_followup_id": RAG_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID,
        "inputs": {
            "rag013_result_path": rel_path(rag013_path, root_path),
            "rag009_result_path": rel_path(rag009_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "review": {
            "accepted_by": str(case_payload.get("accepted_by", "project_owner_current_session")),
            "review_scope": "RAG-013 source-mapped quote follow-up cards listed in the RAG-014 case file.",
            "prior_artifacts_mutated": False,
        },
        "summary": summary,
        "accepted_quote_clearance_items": accepted_items,
        "rejected_followup_items": rejected_items,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
            "runtime_integration_gate_required_before_use": True,
        },
    }


def render_source_mapped_quote_followup_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-014 Source-Mapped Quote Follow-Up",
        "",
        "RAG-014 clears the quote follow-ups created by RAG-012 accepted source mappings. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Follow-up candidates reviewed: `{summary['followup_candidate_count']}`",
        f"- Accepted project-owned paraphrases: `{summary['accepted_followup_count']}`",
        f"- Rejected follow-up candidates: `{summary['rejected_followup_count']}`",
        f"- Source-mapped quote follow-ups remaining: `{summary['source_mapped_quote_followups_remaining_after_review']}`",
        f"- Cleanup decisions applied now: `{summary['cleanup_decisions_applied_now']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Accepted Project-Owned Rules",
        "",
        "| Knowledge ID | Chunk ID | Source | Rule |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload.get("accepted_quote_clearance_items", []):
        source = item["source_title"].replace("|", "/")
        rule = item["project_rule"].replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['chunk_id']}` | {source} | {rule} |")

    lines.extend(
        [
            "",
            "## Rejected Follow-Up Candidates",
            "",
            "| Chunk ID | Source | Verdict | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("rejected_followup_items", []):
        source = item["source_title"].replace("|", "/")
        reason = item["rejection_reason"].replace("|", "/")
        lines.append(f"| `{item['chunk_id']}` | {source} | `{item['review_verdict']}` | {reason} |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- Accepted items are project-owned paraphrases, not copied source text.",
            "- The rejected talk-time dominance candidate is kept out because it optimizes control over listening.",
            "- Persuasion guidance must stay low-pressure, consent-based, campaign-factual, and vertical-agnostic.",
            "- Source mapping is resolved for these five chunks, but runtime admission still requires a later gate.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data is used.",
            "- No source excerpt text is stored.",
            "- A later runtime integration gate is required before any runtime use.",
            "",
        ]
    )
    return "\n".join(lines)
