from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_ACCEPTED_CLEANUP_ID = "RAG-012-accepted-cleanup"
RAG011_BLOCKER_CLEANUP_PACKET_ID = "RAG-011-blocker-cleanup-packet"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


QUOTE_REWRITE_RULES_BY_CHUNK_ID: dict[str, dict[str, Any]] = {
    "rag005-chunk-018": {
        "knowledge_id": "rag012-response-empathy-echo",
        "lane": "response_wording",
        "project_rule": "When a customer sounds hesitant, concerned, or uncertain, reflect the concern as a tentative observation and invite correction.",
        "safe_application": "Use a short empathy echo before the next question, such as naming that something may sound uncertain or important, then let the customer confirm or correct it.",
        "do_not_use_when": "Do not diagnose emotion, tell the customer what they feel, or keep probing after they decline to discuss it.",
        "guardrail_notes": "Customer words override vocal guesses. Treat emotion cues as weak context only.",
        "voice_or_prosody_advisory_only": True,
    },
    "rag005-chunk-019": {
        "knowledge_id": "rag012-voice-purposeful-pause",
        "lane": "voice_delivery",
        "project_rule": "Use a brief pause around a high-value sentence only when it helps the customer process the point.",
        "safe_application": "Use for important next-step, impact, or summary statements after the agent has earned the right to slow down.",
        "do_not_use_when": "Do not add repeated pauses to normal information exchange, compliance text, or urgent customer questions.",
        "guardrail_notes": "Pauses are delivery metadata only and must not change protected wording.",
        "voice_or_prosody_advisory_only": True,
    },
    "rag005-chunk-021": {
        "knowledge_id": "rag012-voice-warm-volume",
        "lane": "voice_delivery",
        "project_rule": "Prefer clear, warm vocal energy over raw loudness when the agent needs to sound confident.",
        "safe_application": "Use provider settings or delivery hints that preserve clarity without clipping, shouting, or harsh emphasis.",
        "do_not_use_when": "Do not push loudness for objections, pricing, disclosures, or emotionally sensitive topics.",
        "guardrail_notes": "This is a TTS rendering constraint, not a claim about human vocal anatomy.",
        "voice_or_prosody_advisory_only": True,
    },
    "rag005-chunk-023": {
        "knowledge_id": "rag012-voice-declarative-statements",
        "lane": "voice_delivery",
        "project_rule": "Render clear statements with declarative confidence while keeping genuine questions open and non-interrogative.",
        "safe_application": "Use on concise summaries, next-step statements, and factual confirmations that the campaign allows.",
        "do_not_use_when": "Do not use a forceful declarative tone for discovery questions, uncertain claims, compliance text, or customer disagreement.",
        "guardrail_notes": "Confidence in delivery cannot upgrade weak facts into certainty.",
        "voice_or_prosody_advisory_only": True,
    },
    "rag005-chunk-026": {
        "knowledge_id": "rag012-voice-energy-match-and-lead",
        "lane": "voice_delivery",
        "project_rule": "Start near the customer's pace and energy, then gently guide the call toward a calm professional rhythm.",
        "safe_application": "Use when the customer is quiet, fast, or cautious and the agent needs to avoid sounding mismatched.",
        "do_not_use_when": "Do not mirror hostility, panic, yelling, accents, dialects, protected traits, or refusal language.",
        "guardrail_notes": "Matching is about pace and intensity only; it cannot become mimicry or emotion certainty.",
        "voice_or_prosody_advisory_only": True,
    },
    "rag005-chunk-027": {
        "knowledge_id": "rag012-voice-pace-variation",
        "lane": "voice_delivery",
        "project_rule": "Vary response pace so routine context stays efficient and important or complex points slow down.",
        "safe_application": "Use a moderate pace for setup context and a slower pace for price, risk, next steps, and customer-confirmed impact.",
        "do_not_use_when": "Do not rush disclosures, pricing, consent, callback details, or anything the customer asks to repeat.",
        "guardrail_notes": "Pacing must improve comprehension, not create pressure.",
        "voice_or_prosody_advisory_only": True,
    },
    "rag005-chunk-063": {
        "knowledge_id": "rag012-response-low-pressure-visual-followup",
        "lane": "response_wording",
        "project_rule": "When a customer resists an immediate explanation but has not refused contact, offer a low-pressure campaign-approved follow-up asset.",
        "safe_application": "Use for a short video, visual summary, or written explainer only when the campaign supports it and the customer can choose whether to review it later.",
        "do_not_use_when": "Do not offer further contact after an explicit no-contact request, do-not-call signal, or compliance block.",
        "guardrail_notes": "Follow-up must reduce pressure and preserve consent; it cannot be a workaround for refusal.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-071": {
        "knowledge_id": "rag012-response-switching-friction",
        "lane": "response_wording",
        "project_rule": "Acknowledge the customer's prior investment before discussing whether future value justifies a change.",
        "safe_application": "Use when a customer hesitates because the current tool, provider, or process already took time, money, or effort to set up.",
        "do_not_use_when": "Do not shame past decisions, exaggerate hidden costs, or imply the customer was wrong to choose their current path.",
        "guardrail_notes": "The agent may compare future tradeoffs only with campaign-approved facts and customer-confirmed pain.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-072": {
        "knowledge_id": "rag012-response-explicit-preference-adaptation",
        "lane": "response_wording",
        "project_rule": "Adapt explanation style to the customer's explicitly stated professional priorities and preferences.",
        "safe_application": "Use customer-provided signals such as wanting numbers, simplicity, risk reduction, speed, service quality, or a human callback.",
        "do_not_use_when": "Do not infer or use sensitive demographics, protected traits, private psychology, or manipulative personality labels.",
        "guardrail_notes": "Personalization must stay transparent, professional, and based on the conversation or campaign profile.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-073": {
        "knowledge_id": "rag012-response-voluntary-micro-commitment",
        "lane": "response_wording",
        "project_rule": "Ask for small, voluntary confirmations before larger next steps.",
        "safe_application": "Use to confirm one problem, one priority, or one acceptable next step before moving to scheduling or handoff.",
        "do_not_use_when": "Do not trap customers with gotcha logic, false agreement chains, or commitments they did not freely choose.",
        "guardrail_notes": "The customer must be able to say no, correct the agent, or choose a different next step.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-074": {
        "knowledge_id": "rag012-guardrail-anti-manipulation",
        "lane": "safety_guardrail",
        "project_rule": "Block sales tactics that rely on trickery, emotional coercion, shame, gaslighting, or repeated pressure.",
        "safe_application": "Use as a universal negative constraint before response wording, objection handling, retrieval, or follow-up suggestions.",
        "do_not_use_when": "Do not make this configurable per campaign unless a stricter policy replaces it.",
        "guardrail_notes": "This guardrail overrides persuasion tactics, voice style, campaign goals, and conversion pressure.",
        "voice_or_prosody_advisory_only": False,
    },
    "rag005-chunk-076": {
        "knowledge_id": "rag012-response-transparent-choice-architecture",
        "lane": "response_wording",
        "project_rule": "When multiple campaign-approved options exist, present the tradeoffs plainly so the customer can choose.",
        "safe_application": "Use simple comparisons that explain who each option fits, what it costs, and what the customer gives up.",
        "do_not_use_when": "Do not hide alternatives, invent decoy choices, bury costs, or create confusing tiers to push a target option.",
        "guardrail_notes": "Choice design must improve clarity and consent, not manipulate preference.",
        "voice_or_prosody_advisory_only": False,
    },
}


QUOTE_REWRITE_RULES_BY_PRINCIPLE: dict[str, dict[str, Any]] = {
    "Purposeful Pausing for Highlight": QUOTE_REWRITE_RULES_BY_CHUNK_ID["rag005-chunk-019"],
    "Match, Mirror, and Lead": QUOTE_REWRITE_RULES_BY_CHUNK_ID["rag005-chunk-026"],
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
        raise ValueError(f"RAG-012 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-012 path is restricted: {path_value}")
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


def validate_inputs(rag011_payload: dict[str, Any], rag009_payload: dict[str, Any], case_payload: dict[str, Any]) -> None:
    if rag011_payload.get("blocker_cleanup_packet_id") != RAG011_BLOCKER_CLEANUP_PACKET_ID:
        raise ValueError("RAG-012 requires the RAG-011 blocker cleanup packet.")
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-012 requires the RAG-009 all-source review coverage artifact.")
    if case_payload.get("accepted_cleanup_id") != RAG_ACCEPTED_CLEANUP_ID:
        raise ValueError("RAG-012 case ID does not match.")
    for context, payload in (
        ("RAG-011 input", rag011_payload),
        ("RAG-009 input", rag009_payload),
        ("RAG-012 case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _accepted_id_set(case_payload: dict[str, Any], key: str) -> set[str]:
    return {str(value).strip() for value in case_payload.get(key, []) if str(value).strip()}


def build_accepted_source_mappings(
    rag011_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    accepted_chunk_ids = _accepted_id_set(case_payload, "accepted_source_mapping_chunk_ids")
    details = _chunk_details_by_id(rag009_payload)
    mappings: list[dict[str, Any]] = []
    for group in rag011_payload.get("source_mapping_candidates", []):
        group_chunk_ids = [str(chunk_id) for chunk_id in group.get("chunk_ids", []) if str(chunk_id).strip()]
        for chunk_id in group_chunk_ids:
            if chunk_id not in accepted_chunk_ids:
                continue
            detail = details.get(chunk_id, {})
            mappings.append(
                {
                    "chunk_id": chunk_id,
                    "source_title": str(group.get("source_title", detail.get("source_title", ""))),
                    "original_status": str(detail.get("status", "blocked_source_mapping")),
                    "topic_ids": [str(topic_id) for topic_id in group.get("topic_ids", detail.get("topic_ids", []))],
                    "accepted_source_ids": [str(group.get("candidate_source_id", ""))],
                    "accepted_canonical_title": str(group.get("candidate_canonical_title", "")),
                    "candidate_score": float(group.get("candidate_score", 0.0)),
                    "source_mapping_resolved": True,
                    "quote_dependency_resolved": False,
                    "quote_clearance_follow_up_required": bool(
                        detail.get("quote_dependency_present", False) or detail.get("quoted_text_copied", False)
                    ),
                    "review_verdict": "source_mapping_accepted",
                    "human_acceptance_recorded": True,
                    "runtime_eligible_now": False,
                    "retrieval_eligible_now": False,
                }
            )
    missing = sorted(accepted_chunk_ids.difference({mapping["chunk_id"] for mapping in mappings}))
    if missing:
        raise ValueError(f"RAG-012 accepted source-mapping chunks were not present in RAG-011: {missing}")
    return mappings


def _rewrite_rule_for_card(card: dict[str, Any]) -> dict[str, Any]:
    chunk_id = str(card.get("chunk_id", "")).strip()
    principle = str(card.get("principle", "")).strip()
    rule = QUOTE_REWRITE_RULES_BY_CHUNK_ID.get(chunk_id) or QUOTE_REWRITE_RULES_BY_PRINCIPLE.get(principle)
    if rule is None:
        raise ValueError(f"RAG-012 has no project-owned quote-clearance rewrite for chunk: {chunk_id}")
    return dict(rule)


def build_accepted_quote_clearance_items(
    rag011_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    accepted_chunk_ids = _accepted_id_set(case_payload, "accepted_quote_clearance_chunk_ids")
    items: list[dict[str, Any]] = []
    for card in rag011_payload.get("quote_clearance_cards", []):
        chunk_id = str(card.get("chunk_id", "")).strip()
        if chunk_id not in accepted_chunk_ids:
            continue
        rewrite = _rewrite_rule_for_card(card)
        items.append(
            {
                "knowledge_id": str(rewrite["knowledge_id"]),
                "chunk_id": chunk_id,
                "lane": str(rewrite["lane"]),
                "source_ids": [str(source_id) for source_id in card.get("source_ids", [])],
                "source_title": str(card.get("source_title", "")),
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", [])],
                "original_candidate_principle": str(card.get("principle", "")),
                "review_verdict": "manual_quote_clearance_paraphrased",
                "quote_dependency_resolved": True,
                "human_acceptance_recorded": True,
                "project_rule": str(rewrite["project_rule"]),
                "safe_application": str(rewrite["safe_application"]),
                "do_not_use_when": str(rewrite["do_not_use_when"]),
                "guardrail_notes": str(rewrite["guardrail_notes"]),
                "voice_or_prosody_advisory_only": bool(rewrite["voice_or_prosody_advisory_only"]),
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
                "manual_review_clearance": {
                    "quote_clearance_resolution": "project_owned_paraphrase_accepted",
                    "source_excerpt_text_copied": False,
                    "runtime_use_allowed": False,
                },
            }
        )
    missing = sorted(accepted_chunk_ids.difference({item["chunk_id"] for item in items}))
    if missing:
        raise ValueError(f"RAG-012 accepted quote-clearance chunks were not present in RAG-011: {missing}")
    return items


def build_accepted_cleanup(
    rag011_result_path: Path | str,
    rag009_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag011_path = resolve_project_path(rag011_result_path, root_path)
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag011_payload = load_json(rag011_path)
    rag009_payload = load_json(rag009_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag011_payload, rag009_payload, case_payload)

    accepted_source_mappings = build_accepted_source_mappings(rag011_payload, rag009_payload, case_payload)
    accepted_quote_items = build_accepted_quote_clearance_items(rag011_payload, case_payload)
    lane_counts = Counter(item["lane"] for item in accepted_quote_items)
    source_mapping_blocker_count = int(rag011_payload.get("summary", {}).get("source_mapping_blocker_count", 0))
    quote_clearance_blocker_count = int(rag011_payload.get("summary", {}).get("quote_clearance_blocker_count", 0))
    quote_follow_up_count = sum(1 for item in accepted_source_mappings if item["quote_clearance_follow_up_required"])
    accepted_source_count = len(accepted_source_mappings)
    accepted_quote_count = len(accepted_quote_items)
    accepted_total = accepted_source_count + accepted_quote_count
    summary = {
        "source_mapping_blocker_count_before": source_mapping_blocker_count,
        "quote_clearance_blocker_count_before": quote_clearance_blocker_count,
        "accepted_source_mapping_chunk_count": accepted_source_count,
        "accepted_source_mapping_group_count": len(rag011_payload.get("source_mapping_candidates", [])),
        "accepted_quote_clearance_item_count": accepted_quote_count,
        "accepted_cleanup_decision_count": accepted_total,
        "quote_clearance_follow_up_required_from_source_mappings": quote_follow_up_count,
        "source_mapping_blockers_remaining_after_acceptance": max(source_mapping_blocker_count - accepted_source_count, 0),
        "quote_clearance_blockers_remaining_after_acceptance": max(quote_clearance_blocker_count - accepted_quote_count, 0),
        "primary_review_blockers_remaining_after_acceptance": max(source_mapping_blocker_count - accepted_source_count, 0)
        + max(quote_clearance_blocker_count - accepted_quote_count, 0),
        "blockers_resolved_in_prior_artifacts": 0,
        "blockers_resolved_by_rag012_acceptance": accepted_total,
        "auto_promoted_chunk_count": 0,
        "lane_counts": {
            "response_wording": lane_counts["response_wording"],
            "voice_delivery": lane_counts["voice_delivery"],
            "safety_guardrail": lane_counts["safety_guardrail"],
        },
        "voice_or_prosody_advisory_item_count": sum(
            1 for item in accepted_quote_items if item["voice_or_prosody_advisory_only"]
        ),
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
        "accepted_cleanup_id": RAG_ACCEPTED_CLEANUP_ID,
        "inputs": {
            "rag011_result_path": rel_path(rag011_path, root_path),
            "rag009_result_path": rel_path(rag009_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "acceptance": {
            "accepted_by": str(case_payload.get("accepted_by", "project_owner_current_session")),
            "acceptance_scope": "RAG-011 source-mapping proposals and quote-clearance cards listed in the RAG-012 case file.",
            "prior_artifacts_mutated": False,
        },
        "summary": summary,
        "accepted_source_mappings": accepted_source_mappings,
        "accepted_quote_clearance_items": accepted_quote_items,
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


def render_accepted_cleanup_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-012 Accepted Cleanup",
        "",
        "RAG-012 records the human-accepted cleanup decisions from RAG-011. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Accepted cleanup decisions: `{summary['accepted_cleanup_decision_count']}`",
        f"- Accepted source-mapping chunks: `{summary['accepted_source_mapping_chunk_count']}`",
        f"- Accepted quote-clearance items: `{summary['accepted_quote_clearance_item_count']}`",
        f"- Source-mapping blockers remaining after acceptance: `{summary['source_mapping_blockers_remaining_after_acceptance']}`",
        f"- Quote-clearance blockers remaining after acceptance: `{summary['quote_clearance_blockers_remaining_after_acceptance']}`",
        f"- Quote-clearance follow-up required from accepted source mappings: `{summary['quote_clearance_follow_up_required_from_source_mappings']}`",
        f"- Blockers resolved in prior artifacts: `{summary['blockers_resolved_in_prior_artifacts']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Accepted Source Mappings",
        "",
        "| Chunk ID | Accepted source | Score | Follow-up |",
        "| --- | --- | ---: | --- |",
    ]
    for item in payload.get("accepted_source_mappings", []):
        source_ids = ", ".join(f"`{source_id}`" for source_id in item["accepted_source_ids"])
        follow_up = "quote clearance" if item["quote_clearance_follow_up_required"] else "none"
        lines.append(
            f"| `{item['chunk_id']}` | {source_ids} {item['accepted_canonical_title']} | `{item['candidate_score']:.3f}` | {follow_up} |"
        )

    lines.extend(
        [
            "",
            "## Accepted Quote-Clearance Rewrites",
            "",
            "| Knowledge ID | Lane | Chunk ID | Rule |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload.get("accepted_quote_clearance_items", []):
        rule = item["project_rule"].replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['lane']}` | `{item['chunk_id']}` | {rule} |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- Accepted source mappings resolve source metadata only; quote-clearance follow-up may still be required.",
            "- Accepted quote-clearance items are project-owned paraphrases.",
            "- Voice and prosody items are advisory delivery guidance only.",
            "- Persuasion guidance is constrained by consent, campaign facts, compliance, refusal handling, and anti-manipulation guardrails.",
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
