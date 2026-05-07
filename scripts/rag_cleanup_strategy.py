from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_CLEANUP_STRATEGY_ID = "RAG-013-cleanup-strategy"
RAG012_ACCEPTED_CLEANUP_ID = "RAG-012-accepted-cleanup"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
RAG006_REVIEW_PACKET_ID = "RAG-006-chunk-review-packet"
NEXT_CHECKPOINT_ID = "RAG-014-source-mapped-quote-followup"
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
        raise ValueError(f"RAG-013 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-013 path is restricted: {path_value}")
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
    rag012_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    rag006_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> None:
    if rag012_payload.get("accepted_cleanup_id") != RAG012_ACCEPTED_CLEANUP_ID:
        raise ValueError("RAG-013 requires the RAG-012 accepted cleanup artifact.")
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-013 requires the RAG-009 all-source review coverage artifact.")
    if rag006_payload.get("review_packet_id") != RAG006_REVIEW_PACKET_ID:
        raise ValueError("RAG-013 requires the RAG-006 chunk review packet.")
    if case_payload.get("cleanup_strategy_id") != RAG_CLEANUP_STRATEGY_ID:
        raise ValueError("RAG-013 case ID does not match.")
    if case_payload.get("recommended_next_checkpoint") != NEXT_CHECKPOINT_ID:
        raise ValueError("RAG-013 case must recommend the source-mapped quote follow-up checkpoint.")
    for context, payload in (
        ("RAG-012 input", rag012_payload),
        ("RAG-009 input", rag009_payload),
        ("RAG-006 input", rag006_payload),
        ("RAG-013 case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _chunk_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("chunk_id", "")).strip() for row in rows if str(row.get("chunk_id", "")).strip()}


def _accepted_source_mapping_ids(rag012_payload: dict[str, Any]) -> set[str]:
    return _chunk_ids(rag012_payload.get("accepted_source_mappings", []))


def _accepted_quote_ids(rag012_payload: dict[str, Any]) -> set[str]:
    return _chunk_ids(rag012_payload.get("accepted_quote_clearance_items", []))


def _topic_lane(topic_ids: list[str], detail: dict[str, Any]) -> str:
    joined = " ".join(topic_ids).lower()
    if detail.get("voice_or_prosody_advisory_only") is True or "speech_tone_prosody" in joined:
        return "voice_delivery"
    if "ethical_persuasion" in joined:
        return "ethical_persuasion"
    if "emotion" in joined:
        return "emotional_intelligence"
    return "response_wording"


def _best_source_suggestion(group: dict[str, Any]) -> dict[str, Any] | None:
    suggestions = group.get("candidate_source_suggestions", [])
    if not isinstance(suggestions, list) or not suggestions:
        return None
    return max((dict(suggestion) for suggestion in suggestions), key=lambda item: float(item.get("score", 0.0)))


def build_source_mapped_quote_followups(rag012_payload: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for mapping in rag012_payload.get("accepted_source_mappings", []):
        if mapping.get("quote_clearance_follow_up_required") is not True:
            continue
        cards.append(
            {
                "chunk_id": str(mapping.get("chunk_id", "")),
                "source_title": str(mapping.get("source_title", "")),
                "topic_ids": [str(topic_id) for topic_id in mapping.get("topic_ids", [])],
                "accepted_source_ids": [str(source_id) for source_id in mapping.get("accepted_source_ids", [])],
                "accepted_canonical_title": str(mapping.get("accepted_canonical_title", "")),
                "cleanup_lane": "source_mapped_quote_followup",
                "review_action": "create_project_owned_paraphrase_or_reject",
                "reason": "Source mapping is accepted, but quote dependency is still unresolved.",
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    return cards


def build_source_mapping_batches(
    rag006_payload: dict[str, Any],
    accepted_source_mapping_ids: set[str],
    *,
    max_groups: int,
) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    for group in rag006_payload.get("review_queues", {}).get("source_mapping_queue", []):
        remaining_chunk_ids = [
            str(chunk_id)
            for chunk_id in group.get("chunk_ids", [])
            if str(chunk_id).strip() and str(chunk_id).strip() not in accepted_source_mapping_ids
        ]
        if not remaining_chunk_ids:
            continue
        suggestion = _best_source_suggestion(group)
        if suggestion:
            candidate_source_id = str(suggestion.get("source_id", ""))
            candidate_canonical_title = str(suggestion.get("canonical_title", ""))
            candidate_score = float(suggestion.get("score", 0.0))
            review_mode = "candidate_source_mapping_review"
        else:
            candidate_source_id = ""
            candidate_canonical_title = ""
            candidate_score = 0.0
            review_mode = "source_metadata_creation_or_manual_mapping_review"
        batches.append(
            {
                "source_title": str(group.get("source_title", "")),
                "remaining_chunk_ids": remaining_chunk_ids,
                "remaining_chunk_count": len(remaining_chunk_ids),
                "topic_ids": [str(topic_id) for topic_id in group.get("topic_ids", [])],
                "review_mode": review_mode,
                "candidate_source_id": candidate_source_id,
                "candidate_canonical_title": candidate_canonical_title,
                "candidate_score": candidate_score,
                "review_action": "map_to_existing_source_or_create_reviewed_source",
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    batches.sort(key=lambda item: (-int(item["remaining_chunk_count"]), item["source_title"].lower()))
    return batches[:max_groups]


def build_remaining_quote_clearance_examples(
    rag009_payload: dict[str, Any],
    accepted_quote_ids: set[str],
    *,
    max_examples: int,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    details = _chunk_details_by_id(rag009_payload)
    examples: list[dict[str, Any]] = []
    lane_counts: Counter[str] = Counter()
    for row in rag009_payload.get("review_queues", {}).get("quote_clearance_queue", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if not chunk_id or chunk_id in accepted_quote_ids:
            continue
        detail = details.get(chunk_id, {})
        topic_ids = [str(topic_id) for topic_id in row.get("topic_ids", detail.get("topic_ids", []))]
        lane = _topic_lane(topic_ids, detail)
        lane_counts[lane] += 1
        if len(examples) >= max_examples:
            continue
        examples.append(
            {
                "chunk_id": chunk_id,
                "source_title": str(row.get("source_title", detail.get("source_title", ""))),
                "source_ids": [str(source_id) for source_id in row.get("source_ids", detail.get("source_ids", []))],
                "topic_ids": topic_ids,
                "cleanup_lane": lane,
                "review_action": "create_project_owned_paraphrase_or_reject",
                "voice_or_prosody_advisory_only": bool(detail.get("voice_or_prosody_advisory_only", False)),
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    return examples, lane_counts


def _remaining_source_mapping_rows(rag009_payload: dict[str, Any], accepted_source_mapping_ids: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in rag009_payload.get("review_queues", {}).get("source_mapping_queue", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id and chunk_id not in accepted_source_mapping_ids:
            rows.append(dict(row))
    return rows


def _remaining_quote_rows(rag009_payload: dict[str, Any], accepted_quote_ids: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in rag009_payload.get("review_queues", {}).get("quote_clearance_queue", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id and chunk_id not in accepted_quote_ids:
            rows.append(dict(row))
    return rows


def _latent_quote_followup_count(
    rag009_payload: dict[str, Any],
    remaining_source_mapping_rows: list[dict[str, Any]],
) -> int:
    details = _chunk_details_by_id(rag009_payload)
    count = 0
    for row in remaining_source_mapping_rows:
        detail = details.get(str(row.get("chunk_id", "")).strip(), {})
        if detail.get("quote_dependency_present") is True or detail.get("quoted_text_copied") is True:
            count += 1
    return count


def build_strategy_stages(
    *,
    followup_count: int,
    source_mapping_count: int,
    quote_clearance_count: int,
    latent_followup_count: int,
) -> list[dict[str, Any]]:
    return [
        {
            "checkpoint_id": NEXT_CHECKPOINT_ID,
            "cleanup_lane": "source_mapped_quote_followup",
            "target_chunk_count": followup_count,
            "objective": "Clear or reject the quote dependencies created by RAG-012 accepted source mappings.",
            "why_first": "This is the smallest bounded cleanup set and it prevents metadata-cleaned chunks from being mistaken for runtime-ready knowledge.",
            "runtime_retrieval_enabled": False,
        },
        {
            "checkpoint_id": "RAG-015-source-mapping-batches",
            "cleanup_lane": "source_mapping",
            "target_chunk_count": source_mapping_count,
            "objective": "Review remaining source-title groups and map them to existing or newly reviewed source records.",
            "why_second": "One reviewed source decision can unlock multiple chunks, but it can also create quote-clearance follow-up work.",
            "runtime_retrieval_enabled": False,
        },
        {
            "checkpoint_id": "RAG-016-quote-clearance-batches",
            "cleanup_lane": "quote_clearance",
            "target_chunk_count": quote_clearance_count + latent_followup_count,
            "objective": "Rewrite or reject remaining quote-dependent candidates as project-owned rules.",
            "why_third": "Quote clearance requires human wording and safety review after source metadata is known.",
            "runtime_retrieval_enabled": False,
        },
        {
            "checkpoint_id": "RAG-017-clean-candidate-reaudit",
            "cleanup_lane": "pre_runtime_audit",
            "target_chunk_count": 0,
            "objective": "Re-audit clean candidates before any runtime-off retrieval harness is considered.",
            "why_final": "The project needs one clean accounting pass before retrieval policy can consume new knowledge.",
            "runtime_retrieval_enabled": False,
        },
    ]


def build_cleanup_strategy(
    rag012_result_path: Path | str,
    rag009_result_path: Path | str,
    rag006_packet_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag012_path = resolve_project_path(rag012_result_path, root_path)
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    rag006_path = resolve_project_path(rag006_packet_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag012_payload = load_json(rag012_path)
    rag009_payload = load_json(rag009_path)
    rag006_payload = load_json(rag006_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag012_payload, rag009_payload, rag006_payload, case_payload)

    accepted_source_ids = _accepted_source_mapping_ids(rag012_payload)
    accepted_quote_ids = _accepted_quote_ids(rag012_payload)
    remaining_source_rows = _remaining_source_mapping_rows(rag009_payload, accepted_source_ids)
    remaining_quote_rows = _remaining_quote_rows(rag009_payload, accepted_quote_ids)
    source_followups = build_source_mapped_quote_followups(rag012_payload)
    max_groups = int(case_payload.get("max_source_mapping_groups", 12))
    max_examples = int(case_payload.get("max_quote_clearance_examples", 12))
    source_batches = build_source_mapping_batches(rag006_payload, accepted_source_ids, max_groups=max_groups)
    quote_examples, quote_lane_counts = build_remaining_quote_clearance_examples(
        rag009_payload,
        accepted_quote_ids,
        max_examples=max_examples,
    )
    latent_followup_count = _latent_quote_followup_count(rag009_payload, remaining_source_rows)
    remaining_source_group_count = sum(
        1
        for group in rag006_payload.get("review_queues", {}).get("source_mapping_queue", [])
        if any(str(chunk_id).strip() not in accepted_source_ids for chunk_id in group.get("chunk_ids", []))
    )
    followup_count = len(source_followups)
    source_count = len(remaining_source_rows)
    quote_count = len(remaining_quote_rows)
    known_work_count = source_count + quote_count + followup_count
    summary = {
        "remaining_source_mapping_chunk_count": source_count,
        "remaining_source_mapping_group_count": remaining_source_group_count,
        "remaining_original_quote_clearance_count": quote_count,
        "quote_follow_up_from_accepted_source_mappings": followup_count,
        "known_cleanup_work_count_before_runtime": known_work_count,
        "latent_quote_followup_after_remaining_source_mapping": latent_followup_count,
        "cleanup_decisions_applied_now": 0,
        "auto_promoted_chunk_count": 0,
        "quote_clearance_lane_counts": dict(quote_lane_counts),
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
        "cleanup_strategy_id": RAG_CLEANUP_STRATEGY_ID,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "inputs": {
            "rag012_result_path": rel_path(rag012_path, root_path),
            "rag009_result_path": rel_path(rag009_path, root_path),
            "rag006_packet_path": rel_path(rag006_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "summary": summary,
        "strategy_stages": build_strategy_stages(
            followup_count=followup_count,
            source_mapping_count=source_count,
            quote_clearance_count=quote_count,
            latent_followup_count=latent_followup_count,
        ),
        "source_mapped_quote_followups": source_followups,
        "source_mapping_batches": source_batches,
        "quote_clearance_examples": quote_examples,
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
            "strategy_only_no_cleanup_mutation": True,
        },
    }


def render_cleanup_strategy_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-013 Cleanup Strategy",
        "",
        "RAG-013 partitions the remaining RAG cleanup work. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Recommended next checkpoint: `{payload['recommended_next_checkpoint']}`",
        f"- Remaining source-mapping chunks: `{summary['remaining_source_mapping_chunk_count']}`",
        f"- Remaining source-mapping groups: `{summary['remaining_source_mapping_group_count']}`",
        f"- Remaining original quote-clearance chunks: `{summary['remaining_original_quote_clearance_count']}`",
        f"- Quote follow-ups from accepted source mappings: `{summary['quote_follow_up_from_accepted_source_mappings']}`",
        f"- Known cleanup work count before runtime: `{summary['known_cleanup_work_count_before_runtime']}`",
        f"- Latent quote follow-up after remaining source mapping: `{summary['latent_quote_followup_after_remaining_source_mapping']}`",
        f"- Cleanup decisions applied now: `{summary['cleanup_decisions_applied_now']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Strategy Stages",
        "",
        "| Checkpoint | Lane | Target chunks | Objective |",
        "| --- | --- | ---: | --- |",
    ]
    for stage in payload.get("strategy_stages", []):
        objective = stage["objective"].replace("|", "/")
        lines.append(
            f"| `{stage['checkpoint_id']}` | `{stage['cleanup_lane']}` | `{stage['target_chunk_count']}` | {objective} |"
        )

    lines.extend(
        [
            "",
            "## RAG-014 Follow-Up Cards",
            "",
            "| Chunk ID | Accepted source | Action |",
            "| --- | --- | --- |",
        ]
    )
    for card in payload.get("source_mapped_quote_followups", []):
        source_ids = ", ".join(f"`{source_id}`" for source_id in card["accepted_source_ids"])
        lines.append(f"| `{card['chunk_id']}` | {source_ids} {card['accepted_canonical_title']} | {card['review_action']} |")

    lines.extend(
        [
            "",
            "## Source-Mapping Batch Preview",
            "",
            "| Source title | Remaining chunks | Review mode |",
            "| --- | ---: | --- |",
        ]
    )
    for group in payload.get("source_mapping_batches", []):
        title = group["source_title"].replace("|", "/")
        lines.append(f"| {title} | `{group['remaining_chunk_count']}` | `{group['review_mode']}` |")

    lines.extend(
        [
            "",
            "## Quote-Clearance Lane Counts",
            "",
        ]
    )
    for lane, count in sorted(summary.get("quote_clearance_lane_counts", {}).items()):
        lines.append(f"- `{lane}`: `{count}`")

    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No cleanup decisions are applied by this strategy packet.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data is used.",
            "- No source excerpt text is stored.",
            "",
        ]
    )
    return "\n".join(lines)
