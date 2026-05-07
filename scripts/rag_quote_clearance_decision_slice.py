from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_QUOTE_CLEARANCE_DECISION_SLICE_ID = "RAG-016A-quote-clearance-decision-slice"
RAG016_QUOTE_CLEARANCE_BATCHES_ID = "RAG-016-quote-clearance-batches"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
NEXT_CHECKPOINT_ID = "RAG-016B-voice-delivery-quote-clearance-decision-slice"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


ACCEPTED_RULES_BY_CHUNK_ID: dict[str, dict[str, Any]] = {
    "rag005-chunk-077": {
        "knowledge_id": "rag016a-response-no-strings-value",
        "lane": "response_wording",
        "project_rule": "Offer useful campaign-approved information without making it conditional on agreement or a next step.",
        "safe_application": "Use when a short checklist, explanation, or comparison can help the customer decide with less pressure.",
        "do_not_use_when": "Do not frame the value as a debt, favor, gift, obligation, bribe, or reason the customer should reciprocate.",
        "guardrail_notes": "Value-first behavior must support customer agency; it cannot create a social-obligation trap.",
    },
    "rag005-chunk-078": {
        "knowledge_id": "rag016a-response-choice-clarity",
        "lane": "response_wording",
        "project_rule": "Present the smallest useful set of campaign-approved options first, then offer full details when the customer asks.",
        "safe_application": "Use when too many tiers, add-ons, dates, or configurations would make the next choice harder to compare.",
        "do_not_use_when": "Do not hide relevant options, prices, limitations, compliance details, or requested customization details.",
        "guardrail_notes": "Choice simplification improves comprehension only when full information remains available.",
    },
    "rag005-chunk-079": {
        "knowledge_id": "rag016a-response-truthful-social-proof",
        "lane": "response_wording",
        "project_rule": "Use social proof only when it is truthful, relevant, and framed as context rather than pressure.",
        "safe_application": "Use campaign-approved examples from similar customers, segments, or use cases to reduce uncertainty.",
        "do_not_use_when": "Do not cite vague popularity, unrelated groups, inflated adoption claims, or herd pressure.",
        "guardrail_notes": "Social proof is weak context; it never replaces the customer's own fit, timing, or consent.",
    },
    "rag005-chunk-080": {
        "knowledge_id": "rag016a-response-goal-path-alignment",
        "lane": "response_wording",
        "project_rule": "With permission, compare a customer-stated goal with the current path and ask whether the gap is worth examining.",
        "safe_application": "Use only after the customer has stated both a desired outcome and a current constraint or tradeoff.",
        "do_not_use_when": "Do not shame, mock, corner, or imply hypocrisy; do not force a change narrative.",
        "guardrail_notes": "The agent may surface a possible mismatch, but the customer decides whether it matters.",
    },
    "rag005-chunk-082": {
        "knowledge_id": "rag016a-response-autonomy-reminder",
        "lane": "response_wording",
        "project_rule": "Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.",
        "safe_application": "Use when the customer is hesitant, resistant, or worried about being pushed.",
        "do_not_use_when": "Do not use autonomy language as reverse psychology or as a setup for renewed pressure.",
        "guardrail_notes": "Autonomy reminders are valid only when the agent actually honors the customer's choice.",
    },
    "rag005-chunk-083": {
        "knowledge_id": "rag016a-response-shared-business-objective",
        "lane": "response_wording",
        "project_rule": "Build rapport by naming a shared business objective the customer has already stated, not by fabricating personal similarity.",
        "safe_application": "Use to align on goals such as reducing risk, saving time, improving service, or clarifying cost.",
        "do_not_use_when": "Do not fake personal anecdotes, imply friendship, mine private details, or mimic identity traits.",
        "guardrail_notes": "An AI sales agent can align professionally without pretending to share human experiences.",
    },
    "rag005-chunk-085": {
        "knowledge_id": "rag016a-response-concise-benefit-set",
        "lane": "response_wording",
        "project_rule": "Keep benefit framing concise by naming only the few campaign-approved points that match the customer's stated priority.",
        "safe_application": "Use when summarizing fit after discovery or when the customer asks for the simplest explanation.",
        "do_not_use_when": "Do not remove critical compliance, price, safety, limitation, or eligibility information to keep the list short.",
        "guardrail_notes": "Concision is a comprehension aid, not a reason to omit material information.",
    },
    "rag005-chunk-086": {
        "knowledge_id": "rag016a-response-transparent-reference-point",
        "lane": "response_wording",
        "project_rule": "Use reference prices, benchmarks, or value metrics only when they are real, relevant, and clearly explained.",
        "safe_application": "Use campaign-approved market ranges, baseline costs, or customer-confirmed current spend as context.",
        "do_not_use_when": "Do not inflate a comparison, invent a list price, cherry-pick misleading benchmarks, or bury assumptions.",
        "guardrail_notes": "A reference point must clarify tradeoffs; it cannot manufacture perceived savings.",
    },
    "rag005-chunk-087": {
        "knowledge_id": "rag016a-response-truthful-authority-context",
        "lane": "response_wording",
        "project_rule": "Reference expertise, endorsements, or introductions only when the role, relationship, and evidence are truthful.",
        "safe_application": "Use verified campaign materials, legitimate referrals, or accurate specialist context to explain why information is credible.",
        "do_not_use_when": "Do not exaggerate credentials, invent third-party approval, imply unavailable expertise, or use fake titles.",
        "guardrail_notes": "Authority cues must improve evidence quality, not borrow trust through deception.",
    },
    "rag005-chunk-088": {
        "knowledge_id": "rag016a-response-stated-priority-reflection",
        "lane": "response_wording",
        "project_rule": "Tie impact to professional priorities the customer has explicitly stated, then invite correction.",
        "safe_application": "Use for customer-stated priorities such as reliability, workload, budget control, reputation, speed, or service quality.",
        "do_not_use_when": "Do not infer private values, identity, insecurity, ambition, or personal life goals from sparse signals.",
        "guardrail_notes": "Reflection stays professional and tentative; customer correction overrides the agent's framing.",
    },
    "rag005-chunk-089": {
        "knowledge_id": "rag016a-guardrail-rational-agency",
        "lane": "safety_guardrail",
        "project_rule": "Influence tactics must help the customer reason about fit and tradeoffs, not bypass judgment through trickery or coercion.",
        "safe_application": "Use as a universal guardrail before persuasion, objection handling, retrieval, voice delivery, and follow-up suggestions.",
        "do_not_use_when": "Do not make this guardrail weaker for aggressive campaign goals or conversion pressure.",
        "guardrail_notes": "Respect for rational agency overrides persuasion patterns, campaign targets, and voice style.",
    },
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
        raise ValueError(f"RAG-016A path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-016A path is restricted: {path_value}")
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
    rag016_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> None:
    if rag016_payload.get("quote_clearance_batches_id") != RAG016_QUOTE_CLEARANCE_BATCHES_ID:
        raise ValueError("RAG-016A requires the RAG-016 quote-clearance batches artifact.")
    if rag016_payload.get("recommended_next_checkpoint") != RAG_QUOTE_CLEARANCE_DECISION_SLICE_ID:
        raise ValueError("RAG-016A requires RAG-016 to recommend the decision slice next.")
    if rag016_payload.get("summary", {}).get("cleanup_decisions_applied_now") != 0:
        raise ValueError("RAG-016A requires RAG-016 to be a no-decision batch packet.")
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-016A requires the RAG-009 all-source review coverage artifact.")
    if case_payload.get("quote_clearance_decision_slice_id") != RAG_QUOTE_CLEARANCE_DECISION_SLICE_ID:
        raise ValueError("RAG-016A case ID does not match.")
    if case_payload.get("recommended_next_checkpoint") != NEXT_CHECKPOINT_ID:
        raise ValueError("RAG-016A case must recommend the voice-delivery quote-clearance decision slice next.")
    for context, payload in (
        ("RAG-016 input", rag016_payload),
        ("RAG-009 input", rag009_payload),
        ("RAG-016A case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _cards_by_id(rag016_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for card in rag016_payload.get("quote_clearance_review_cards", []):
        chunk_id = str(card.get("chunk_id", "")).strip()
        if chunk_id:
            cards[chunk_id] = dict(card)
    return cards


def _id_set(case_payload: dict[str, Any], key: str) -> set[str]:
    return {str(value).strip() for value in case_payload.get(key, []) if str(value).strip()}


def _selected_batch_cards(rag016_payload: dict[str, Any], selected_batch: str) -> list[dict[str, Any]]:
    return [
        dict(card)
        for card in rag016_payload.get("quote_clearance_review_cards", [])
        if str(card.get("priority_batch", "")) == selected_batch
    ]


def _validate_review_scope(
    rag016_payload: dict[str, Any],
    case_payload: dict[str, Any],
    accepted_ids: set[str],
    rejected_ids: set[str],
) -> None:
    selected_batch = str(case_payload.get("selected_priority_batch", "")).strip()
    selected_cards = _selected_batch_cards(rag016_payload, selected_batch)
    if not selected_cards:
        raise ValueError(f"RAG-016A selected priority batch has no cards: {selected_batch}")
    selected_ids = {str(card["chunk_id"]) for card in selected_cards}
    all_card_ids = set(_cards_by_id(rag016_payload))
    overlap = accepted_ids.intersection(rejected_ids)
    if overlap:
        raise ValueError(f"RAG-016A accepted and rejected ID sets overlap: {sorted(overlap)}")
    reviewed_ids = accepted_ids.union(rejected_ids)
    unexpected = reviewed_ids.difference(all_card_ids)
    if unexpected:
        raise ValueError(f"RAG-016A review decisions reference unknown quote-clearance chunks: {sorted(unexpected)}")
    outside_batch = reviewed_ids.difference(selected_ids)
    if outside_batch:
        raise ValueError(f"RAG-016A review decisions must stay inside selected batch: {sorted(outside_batch)}")
    missing = selected_ids.difference(reviewed_ids)
    if missing:
        raise ValueError(f"RAG-016A selected batch chunks missing review decisions: {sorted(missing)}")


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
            raise ValueError(f"RAG-016A accepted chunk is missing RAG-009 details: {chunk_id}")
        rewrite = ACCEPTED_RULES_BY_CHUNK_ID.get(chunk_id)
        if rewrite is None:
            raise ValueError(f"RAG-016A has no project-owned rewrite for chunk: {chunk_id}")
        items.append(
            {
                "knowledge_id": str(rewrite["knowledge_id"]),
                "chunk_id": chunk_id,
                "lane": str(rewrite["lane"]),
                "source_ids": [str(source_id) for source_id in card.get("source_ids", [])],
                "source_title": str(card.get("source_title", detail.get("source_title", ""))),
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", detail.get("topic_ids", []))],
                "priority_batch": str(card.get("priority_batch", "")),
                "original_candidate_principle": str(detail.get("principle", "")),
                "review_verdict": "manual_quote_clearance_paraphrased",
                "quote_dependency_resolved": True,
                "human_acceptance_recorded": True,
                "project_rule": str(rewrite["project_rule"]),
                "safe_application": str(rewrite["safe_application"]),
                "do_not_use_when": str(rewrite["do_not_use_when"]),
                "guardrail_notes": str(rewrite["guardrail_notes"]),
                "voice_or_prosody_advisory_only": False,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
                "manual_review_clearance": {
                    "quote_clearance_resolution": "project_owned_paraphrase_accepted",
                    "source_excerpt_text_copied": False,
                    "runtime_use_allowed": False,
                },
            }
        )
    return items


def build_rejected_quote_clearance_items(
    cards_by_id: dict[str, dict[str, Any]],
    details_by_id: dict[str, dict[str, Any]],
    rejected_ids: set[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for chunk_id in sorted(rejected_ids):
        card = cards_by_id[chunk_id]
        detail = details_by_id.get(chunk_id)
        if detail is None:
            raise ValueError(f"RAG-016A rejected chunk is missing RAG-009 details: {chunk_id}")
        items.append(
            {
                "chunk_id": chunk_id,
                "lane": str(card.get("cleanup_lane", "")),
                "source_ids": [str(source_id) for source_id in card.get("source_ids", [])],
                "source_title": str(card.get("source_title", detail.get("source_title", ""))),
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", detail.get("topic_ids", []))],
                "priority_batch": str(card.get("priority_batch", "")),
                "original_candidate_principle": str(detail.get("principle", "")),
                "review_verdict": "rejected_for_this_decision_slice",
                "rejection_reason": "No project-owned safe rewrite was accepted for this slice.",
                "quote_dependency_resolved": False,
                "project_owned_rule_created": False,
                "human_rejection_recorded": True,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    return items


def _remaining_cards(
    rag016_payload: dict[str, Any],
    accepted_ids: set[str],
    rejected_ids: set[str],
) -> list[dict[str, Any]]:
    resolved_ids = accepted_ids.union(rejected_ids)
    remaining: list[dict[str, Any]] = []
    for card in rag016_payload.get("quote_clearance_review_cards", []):
        chunk_id = str(card.get("chunk_id", "")).strip()
        if not chunk_id or chunk_id in resolved_ids:
            continue
        remaining.append(
            {
                "chunk_id": chunk_id,
                "priority_batch": str(card.get("priority_batch", "")),
                "cleanup_lane": str(card.get("cleanup_lane", "")),
                "review_focus": str(card.get("review_focus", "")),
                "source_title": str(card.get("source_title", "")),
                "source_ids": [str(source_id) for source_id in card.get("source_ids", [])],
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", [])],
                "review_action": "create_project_owned_paraphrase_or_reject",
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    return remaining


def build_quote_clearance_decision_slice(
    rag016_result_path: Path | str,
    rag009_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag016_path = resolve_project_path(rag016_result_path, root_path)
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag016_payload = load_json(rag016_path)
    rag009_payload = load_json(rag009_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag016_payload, rag009_payload, case_payload)

    accepted_ids = _id_set(case_payload, "accepted_quote_clearance_chunk_ids")
    rejected_ids = _id_set(case_payload, "rejected_quote_clearance_chunk_ids")
    _validate_review_scope(rag016_payload, case_payload, accepted_ids, rejected_ids)
    cards_by_id = _cards_by_id(rag016_payload)
    details_by_id = _chunk_details_by_id(rag009_payload)
    accepted_items = build_accepted_quote_clearance_items(cards_by_id, details_by_id, accepted_ids)
    rejected_items = build_rejected_quote_clearance_items(cards_by_id, details_by_id, rejected_ids)
    remaining_cards = _remaining_cards(rag016_payload, accepted_ids, rejected_ids)
    lane_counts = Counter(item["lane"] for item in accepted_items)
    remaining_lane_counts = Counter(card["cleanup_lane"] for card in remaining_cards)
    decision_count = len(accepted_items) + len(rejected_items)
    source_pending_count = int(rag016_payload.get("summary", {}).get("source_mapping_pending_chunk_count_from_rag015", 0))
    summary = {
        "selected_priority_batch": str(case_payload.get("selected_priority_batch", "")),
        "decision_candidate_count": decision_count,
        "accepted_quote_clearance_item_count": len(accepted_items),
        "rejected_quote_clearance_item_count": len(rejected_items),
        "quote_clearance_decisions_applied_now": decision_count,
        "quote_clearance_blockers_resolved_now": decision_count,
        "quote_clearance_blockers_remaining_after_rag016a": len(remaining_cards),
        "ethical_persuasion_remaining_after_rag016a": remaining_lane_counts["ethical_persuasion"],
        "voice_delivery_remaining_after_rag016a": remaining_lane_counts["voice_delivery"],
        "accepted_lane_counts": dict(lane_counts),
        "source_mapping_pending_chunk_count_from_rag015": source_pending_count,
        "source_mapping_pending_group_count_from_rag015": int(
            rag016_payload.get("summary", {}).get("source_mapping_pending_group_count_from_rag015", 0)
        ),
        "source_mapping_latent_quote_followup_count_from_rag015": int(
            rag016_payload.get("summary", {}).get("source_mapping_latent_quote_followup_count_from_rag015", 0)
        ),
        "known_unresolved_cleanup_work_after_rag016a": source_pending_count + len(remaining_cards),
        "auto_promoted_chunk_count": 0,
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
        "quote_clearance_decision_slice_id": RAG_QUOTE_CLEARANCE_DECISION_SLICE_ID,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "inputs": {
            "rag016_result_path": rel_path(rag016_path, root_path),
            "rag009_result_path": rel_path(rag009_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "acceptance": {
            "accepted_by": str(case_payload.get("accepted_by", "project_owner_current_session")),
            "acceptance_scope": "RAG-016 ethical-persuasion response-wording batch listed in the RAG-016A case file.",
            "prior_artifacts_mutated": False,
        },
        "summary": summary,
        "accepted_quote_clearance_items": accepted_items,
        "rejected_quote_clearance_items": rejected_items,
        "remaining_quote_clearance_cards": remaining_cards,
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


def render_quote_clearance_decision_slice_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-016A Quote-Clearance Decision Slice",
        "",
        "RAG-016A accepts the ethical-persuasion quote-clearance batch as project-owned guidance. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Recommended next checkpoint: `{payload['recommended_next_checkpoint']}`",
        f"- Selected priority batch: `{summary['selected_priority_batch']}`",
        f"- Decision candidates reviewed: `{summary['decision_candidate_count']}`",
        f"- Accepted quote-clearance items: `{summary['accepted_quote_clearance_item_count']}`",
        f"- Rejected quote-clearance items: `{summary['rejected_quote_clearance_item_count']}`",
        f"- Quote-clearance blockers remaining: `{summary['quote_clearance_blockers_remaining_after_rag016a']}`",
        f"- Ethical-persuasion blockers remaining: `{summary['ethical_persuasion_remaining_after_rag016a']}`",
        f"- Voice-delivery blockers remaining: `{summary['voice_delivery_remaining_after_rag016a']}`",
        f"- Source-mapping chunks still pending from RAG-015: `{summary['source_mapping_pending_chunk_count_from_rag015']}`",
        f"- Known unresolved cleanup work after RAG-016A: `{summary['known_unresolved_cleanup_work_after_rag016a']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Accepted Project-Owned Rules",
        "",
        "| Knowledge ID | Lane | Chunk ID | Rule |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload.get("accepted_quote_clearance_items", []):
        rule = str(item["project_rule"]).replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['lane']}` | `{item['chunk_id']}` | {rule} |")

    lines.extend(
        [
            "",
            "## Remaining Quote-Clearance Cards",
            "",
            "| Batch | Lane | Chunk ID | Source |",
            "| --- | --- | --- | --- |",
        ]
    )
    for card in payload.get("remaining_quote_clearance_cards", []):
        source = str(card["source_title"]).replace("|", "/")
        lines.append(f"| `{card['priority_batch']}` | `{card['cleanup_lane']}` | `{card['chunk_id']}` | {source} |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- Accepted items are project-owned paraphrases, not copied source text.",
            "- Ethical-persuasion guidance must stay low-pressure, consent-aware, truthful, and vertical-agnostic.",
            "- Voice-delivery quote-clearance cards remain pending for RAG-016B.",
            "- Accepted items are still not runtime-eligible.",
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
