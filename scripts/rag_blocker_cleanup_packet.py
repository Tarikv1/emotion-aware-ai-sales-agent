from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RAG_BLOCKER_CLEANUP_PACKET_ID = "RAG-011-blocker-cleanup-packet"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
RAG006_REVIEW_PACKET_ID = "RAG-006-chunk-review-packet"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


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
        raise ValueError(f"RAG-011 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-011 path is restricted: {path_value}")
    return resolved


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _runtime_boundaries_are_disabled(payload: dict[str, Any], *, context: str) -> None:
    summary = payload.get("summary", payload)
    for key in (
        "runtime_retrieval_enabled",
        "retrieval_used_in_runtime",
        "chunk_import_enabled",
        "provider_calls_made",
        "external_provider_calls_made",
        "notebooklm_api_used",
        "private_customer_data_used",
        "reads_data_private",
    ):
        if summary.get(key) is True:
            raise ValueError(f"{context} enables forbidden runtime boundary: {key}")


def validate_inputs(rag009_payload: dict[str, Any], rag006_payload: dict[str, Any], case_payload: dict[str, Any]) -> None:
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-011 requires the RAG-009 all-source review coverage artifact.")
    if rag006_payload.get("review_packet_id") != RAG006_REVIEW_PACKET_ID:
        raise ValueError("RAG-011 requires the RAG-006 chunk review packet.")
    if case_payload.get("blocker_cleanup_packet_id") != RAG_BLOCKER_CLEANUP_PACKET_ID:
        raise ValueError("RAG-011 case ID does not match.")
    for context, payload in (
        ("RAG-009 input", rag009_payload),
        ("RAG-006 input", rag006_payload),
        ("RAG-011 case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _best_source_suggestion(item: dict[str, Any]) -> dict[str, Any] | None:
    suggestions = item.get("candidate_source_suggestions", [])
    if not isinstance(suggestions, list) or not suggestions:
        return None
    sorted_suggestions = sorted(
        (dict(suggestion) for suggestion in suggestions),
        key=lambda suggestion: float(suggestion.get("score", 0.0)),
        reverse=True,
    )
    return sorted_suggestions[0]


def build_source_mapping_candidates(
    rag006_payload: dict[str, Any],
    *,
    min_source_suggestion_score: float,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in rag006_payload.get("review_queues", {}).get("source_mapping_queue", []):
        suggestion = _best_source_suggestion(item)
        if not suggestion:
            continue
        score = float(suggestion.get("score", 0.0))
        if score < min_source_suggestion_score:
            continue
        chunk_ids = [str(chunk_id) for chunk_id in item.get("chunk_ids", []) if str(chunk_id).strip()]
        candidates.append(
            {
                "source_title": str(item.get("source_title", "")),
                "chunk_ids": chunk_ids,
                "chunk_count": len(chunk_ids),
                "topic_ids": [str(topic_id) for topic_id in item.get("topic_ids", [])],
                "candidate_source_id": str(suggestion.get("source_id", "")),
                "candidate_canonical_title": str(suggestion.get("canonical_title", "")),
                "candidate_score": score,
                "score_threshold": min_source_suggestion_score,
                "human_acceptance_required": True,
                "auto_apply_allowed": False,
                "review_action": "human_confirm_source_mapping_before_chunk_reclassification",
            }
        )
    return candidates


def _quote_card(queue_row: dict[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    chunk_id = str(queue_row.get("chunk_id", "") or detail.get("chunk_id", ""))
    return {
        "chunk_id": chunk_id,
        "source_title": str(detail.get("source_title") or queue_row.get("source_title", "")),
        "source_ids": [str(source_id) for source_id in detail.get("source_ids", queue_row.get("source_ids", []))],
        "topic_ids": [str(topic_id) for topic_id in detail.get("topic_ids", queue_row.get("topic_ids", []))],
        "original_topic_id": str(detail.get("original_topic_id", "")),
        "principle": str(detail.get("principle", "")),
        "application": str(detail.get("application", "")),
        "when_not_to_use": str(detail.get("when_not_to_use", "")),
        "voice_or_prosody_advisory_only": bool(detail.get("voice_or_prosody_advisory_only", False)),
        "rewrite_action": "create_project_owned_paraphrase_or_keep_blocked",
        "human_acceptance_required": True,
        "quote_dependency_resolved_now": False,
        "source_excerpt_text_copied": False,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def build_quote_clearance_cards(
    rag009_payload: dict[str, Any],
    *,
    max_quote_clearance_cards: int,
) -> list[dict[str, Any]]:
    details = _chunk_details_by_id(rag009_payload)
    cards: list[dict[str, Any]] = []
    for queue_row in rag009_payload.get("review_queues", {}).get("quote_clearance_queue", []):
        if len(cards) >= max_quote_clearance_cards:
            break
        chunk_id = str(queue_row.get("chunk_id", "")).strip()
        detail = details.get(chunk_id, dict(queue_row))
        cards.append(_quote_card(queue_row, detail))
    return cards


def build_blocker_cleanup_packet(
    rag009_result_path: Path | str,
    rag006_packet_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    rag006_path = resolve_project_path(rag006_packet_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag009_payload = load_json(rag009_path)
    rag006_payload = load_json(rag006_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag009_payload, rag006_payload, case_payload)

    min_score = float(case_payload.get("min_source_suggestion_score", 0.55))
    max_quote_cards = int(case_payload.get("max_quote_clearance_cards", 12))
    source_mapping_candidates = build_source_mapping_candidates(
        rag006_payload,
        min_source_suggestion_score=min_score,
    )
    quote_clearance_cards = build_quote_clearance_cards(
        rag009_payload,
        max_quote_clearance_cards=max_quote_cards,
    )

    rag009_summary = rag009_payload.get("summary", {})
    source_mapping_blocker_count = int(
        rag009_summary.get(
            "blocked_source_mapping_count",
            len(rag009_payload.get("review_queues", {}).get("source_mapping_queue", [])),
        )
    )
    quote_clearance_blocker_count = int(
        rag009_summary.get(
            "blocked_quote_clearance_count",
            len(rag009_payload.get("review_queues", {}).get("quote_clearance_queue", [])),
        )
    )
    source_mapping_candidate_chunk_count = sum(item["chunk_count"] for item in source_mapping_candidates)
    potential_reduction = source_mapping_candidate_chunk_count + len(quote_clearance_cards)
    summary = {
        "source_mapping_blocker_count": source_mapping_blocker_count,
        "source_mapping_candidate_group_count": len(source_mapping_candidates),
        "source_mapping_candidate_chunk_count": source_mapping_candidate_chunk_count,
        "quote_clearance_blocker_count": quote_clearance_blocker_count,
        "quote_clearance_review_card_count": len(quote_clearance_cards),
        "potential_blocker_reduction_after_human_acceptance": potential_reduction,
        "blockers_resolved_now": 0,
        "auto_promoted_chunk_count": 0,
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
        "reads_data_private": False,
        "source_excerpt_text_stored": False,
    }
    return {
        "blocker_cleanup_packet_id": RAG_BLOCKER_CLEANUP_PACKET_ID,
        "inputs": {
            "rag009_result_path": rel_path(rag009_path, root_path),
            "rag006_packet_path": rel_path(rag006_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "case_config": {
            "min_source_suggestion_score": min_score,
            "max_quote_clearance_cards": max_quote_cards,
        },
        "summary": summary,
        "source_mapping_candidates": source_mapping_candidates,
        "quote_clearance_cards": quote_clearance_cards,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_used_in_runtime": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
            "human_acceptance_required_before_reclassification": True,
        },
    }


def render_blocker_cleanup_packet_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-011 Blocker Cleanup Packet",
        "",
        "RAG-011 narrows source-mapping and quote-clearance cleanup work. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Source-mapping blockers: `{summary['source_mapping_blocker_count']}`",
        f"- Source-mapping candidate groups: `{summary['source_mapping_candidate_group_count']}`",
        f"- Source-mapping candidate chunks: `{summary['source_mapping_candidate_chunk_count']}`",
        f"- Quote-clearance blockers: `{summary['quote_clearance_blocker_count']}`",
        f"- Quote-clearance review cards: `{summary['quote_clearance_review_card_count']}`",
        f"- Potential blocker reduction after human acceptance: `{summary['potential_blocker_reduction_after_human_acceptance']}`",
        f"- Blockers resolved now: `{summary['blockers_resolved_now']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Source Mapping Candidates",
        "",
        "| Source title | Candidate source | Score | Chunks |",
        "| --- | --- | ---: | --- |",
    ]
    for item in payload.get("source_mapping_candidates", []):
        chunk_ids = ", ".join(f"`{chunk_id}`" for chunk_id in item["chunk_ids"])
        title = item["source_title"].replace("|", "/")
        candidate = f"`{item['candidate_source_id']}` {item['candidate_canonical_title']}".replace("|", "/")
        lines.append(f"| {title} | {candidate} | `{item['candidate_score']:.3f}` | {chunk_ids} |")

    lines.extend(
        [
            "",
            "## Quote Clearance Cards",
            "",
            "| Chunk ID | Source IDs | Principle |",
            "| --- | --- | --- |",
        ]
    )
    for card in payload.get("quote_clearance_cards", []):
        source_ids = ", ".join(f"`{source_id}`" for source_id in card["source_ids"])
        principle = card["principle"].replace("|", "/")
        lines.append(f"| `{card['chunk_id']}` | {source_ids} | {principle} |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- Source mappings are proposals only and require human acceptance.",
            "- Quote-clearance cards require project-owned paraphrases or they stay blocked.",
            "- This packet reports possible cleanup work; it does not reclassify chunks.",
            "- No source excerpt text is copied into the packet.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data is used.",
            "- `blockers_resolved_now` remains `0` until a later human-accepted cleanup checkpoint.",
            "",
        ]
    )
    return "\n".join(lines)
