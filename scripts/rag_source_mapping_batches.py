from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RAG_SOURCE_MAPPING_BATCHES_ID = "RAG-015-source-mapping-batches"
RAG014_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID = "RAG-014-source-mapped-quote-followup"
RAG013_CLEANUP_STRATEGY_ID = "RAG-013-cleanup-strategy"
RAG006_REVIEW_PACKET_ID = "RAG-006-chunk-review-packet"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
NEXT_CHECKPOINT_ID = "RAG-016-quote-clearance-batches"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


PRIORITY_ORDER = {
    "batch_1_high_impact_groups": 1,
    "batch_2_medium_groups": 2,
    "batch_3_suggested_singletons": 3,
    "batch_4_unsuggested_singletons": 4,
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
        raise ValueError(f"RAG-015 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-015 path is restricted: {path_value}")
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
    rag014_payload: dict[str, Any],
    rag013_payload: dict[str, Any],
    rag006_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> None:
    if rag014_payload.get("source_mapped_quote_followup_id") != RAG014_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID:
        raise ValueError("RAG-015 requires the RAG-014 source-mapped quote follow-up artifact.")
    if rag014_payload.get("summary", {}).get("source_mapped_quote_followups_remaining_after_review") != 0:
        raise ValueError("RAG-015 requires RAG-014 to clear all source-mapped quote follow-ups first.")
    if rag013_payload.get("cleanup_strategy_id") != RAG013_CLEANUP_STRATEGY_ID:
        raise ValueError("RAG-015 requires the RAG-013 cleanup strategy artifact.")
    if rag006_payload.get("review_packet_id") != RAG006_REVIEW_PACKET_ID:
        raise ValueError("RAG-015 requires the RAG-006 chunk review packet.")
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-015 requires the RAG-009 all-source review coverage artifact.")
    if case_payload.get("source_mapping_batches_id") != RAG_SOURCE_MAPPING_BATCHES_ID:
        raise ValueError("RAG-015 case ID does not match.")
    for context, payload in (
        ("RAG-014 input", rag014_payload),
        ("RAG-013 input", rag013_payload),
        ("RAG-006 input", rag006_payload),
        ("RAG-009 input", rag009_payload),
        ("RAG-015 case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _resolved_source_mapping_ids_from_rag014(rag014_payload: dict[str, Any]) -> set[str]:
    resolved: set[str] = set()
    for collection_key in ("accepted_quote_clearance_items", "rejected_followup_items"):
        for item in rag014_payload.get(collection_key, []):
            if item.get("source_mapping_resolved") is True:
                chunk_id = str(item.get("chunk_id", "")).strip()
                if chunk_id:
                    resolved.add(chunk_id)
    return resolved


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _priority_batch(remaining_chunk_count: int, suggestion_count: int) -> str:
    if remaining_chunk_count >= 3:
        return "batch_1_high_impact_groups"
    if remaining_chunk_count == 2:
        return "batch_2_medium_groups"
    if suggestion_count > 0:
        return "batch_3_suggested_singletons"
    return "batch_4_unsuggested_singletons"


def _review_mode(suggestion_count: int) -> str:
    if suggestion_count > 0:
        return "candidate_source_mapping_review"
    return "source_metadata_creation_or_manual_mapping_review"


def _quote_followup_chunk_ids(remaining_chunk_ids: list[str], details_by_id: dict[str, dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for chunk_id in remaining_chunk_ids:
        detail = details_by_id.get(chunk_id, {})
        if detail.get("quote_dependency_present") is True or detail.get("quoted_text_copied") is True:
            ids.append(chunk_id)
    return ids


def build_review_groups(
    rag006_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    resolved_source_mapping_ids: set[str],
) -> list[dict[str, Any]]:
    details_by_id = _chunk_details_by_id(rag009_payload)
    review_groups: list[dict[str, Any]] = []
    for group in rag006_payload.get("review_queues", {}).get("source_mapping_queue", []):
        remaining_chunk_ids = [
            str(chunk_id)
            for chunk_id in group.get("chunk_ids", [])
            if str(chunk_id).strip() and str(chunk_id).strip() not in resolved_source_mapping_ids
        ]
        if not remaining_chunk_ids:
            continue
        suggestions = [dict(suggestion) for suggestion in group.get("candidate_source_suggestions", [])]
        suggestion_count = len(suggestions)
        priority = _priority_batch(len(remaining_chunk_ids), suggestion_count)
        quote_followup_ids = _quote_followup_chunk_ids(remaining_chunk_ids, details_by_id)
        review_groups.append(
            {
                "priority_batch": priority,
                "source_title": str(group.get("source_title", "")),
                "remaining_chunk_ids": remaining_chunk_ids,
                "remaining_chunk_count": len(remaining_chunk_ids),
                "topic_ids": [str(topic_id) for topic_id in group.get("topic_ids", [])],
                "candidate_source_suggestions": suggestions,
                "candidate_source_suggestion_count": suggestion_count,
                "review_mode": _review_mode(suggestion_count),
                "review_action": "human_review_source_mapping_before_reclassification",
                "latent_quote_followup_chunk_ids": quote_followup_ids,
                "latent_quote_followup_chunk_count": len(quote_followup_ids),
                "auto_apply_allowed": False,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    review_groups.sort(
        key=lambda item: (
            PRIORITY_ORDER[item["priority_batch"]],
            -int(item["remaining_chunk_count"]),
            str(item["source_title"]).lower(),
        )
    )
    return review_groups


def build_priority_batches(review_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups_by_priority: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in review_groups:
        groups_by_priority[str(group["priority_batch"])].append(group)
    batches: list[dict[str, Any]] = []
    for batch_id in sorted(groups_by_priority, key=lambda value: PRIORITY_ORDER[value]):
        groups = groups_by_priority[batch_id]
        batches.append(
            {
                "batch_id": batch_id,
                "group_count": len(groups),
                "chunk_count": sum(int(group["remaining_chunk_count"]) for group in groups),
                "latent_quote_followup_chunk_count": sum(int(group["latent_quote_followup_chunk_count"]) for group in groups),
                "candidate_source_suggestion_group_count": sum(
                    1 for group in groups if int(group["candidate_source_suggestion_count"]) > 0
                ),
                "objective": _batch_objective(batch_id),
                "runtime_retrieval_enabled": False,
            }
        )
    return batches


def _batch_objective(batch_id: str) -> str:
    objectives = {
        "batch_1_high_impact_groups": "Review larger source-title groups first because one source decision can unblock multiple chunks.",
        "batch_2_medium_groups": "Review two-chunk groups after larger groups to reduce blocker count efficiently.",
        "batch_3_suggested_singletons": "Review singleton chunks with candidate source suggestions before unsuggested singletons.",
        "batch_4_unsuggested_singletons": "Manually map or create source metadata for singleton chunks without source suggestions.",
    }
    return objectives[batch_id]


def build_source_mapping_batches(
    rag014_result_path: Path | str,
    rag013_result_path: Path | str,
    rag006_packet_path: Path | str,
    rag009_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag014_path = resolve_project_path(rag014_result_path, root_path)
    rag013_path = resolve_project_path(rag013_result_path, root_path)
    rag006_path = resolve_project_path(rag006_packet_path, root_path)
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag014_payload = load_json(rag014_path)
    rag013_payload = load_json(rag013_path)
    rag006_payload = load_json(rag006_path)
    rag009_payload = load_json(rag009_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag014_payload, rag013_payload, rag006_payload, rag009_payload, case_payload)

    resolved_ids = _resolved_source_mapping_ids_from_rag014(rag014_payload)
    review_groups = build_review_groups(rag006_payload, rag009_payload, resolved_ids)
    source_mapping_group_count = len(review_groups)
    source_mapping_chunk_count = sum(int(group["remaining_chunk_count"]) for group in review_groups)
    expected_groups = int(rag013_payload.get("summary", {}).get("remaining_source_mapping_group_count", source_mapping_group_count))
    expected_chunks = int(rag013_payload.get("summary", {}).get("remaining_source_mapping_chunk_count", source_mapping_chunk_count))
    if source_mapping_group_count != expected_groups or source_mapping_chunk_count != expected_chunks:
        raise ValueError(
            "RAG-015 source-mapping counts do not match RAG-013 strategy: "
            f"groups={source_mapping_group_count}/{expected_groups}, chunks={source_mapping_chunk_count}/{expected_chunks}"
        )

    batch_counter = Counter(group["priority_batch"] for group in review_groups)
    suggestion_group_count = sum(1 for group in review_groups if int(group["candidate_source_suggestion_count"]) > 0)
    suggestion_count = sum(int(group["candidate_source_suggestion_count"]) for group in review_groups)
    latent_quote_count = sum(int(group["latent_quote_followup_chunk_count"]) for group in review_groups)
    summary = {
        "source_mapping_group_count": source_mapping_group_count,
        "source_mapping_chunk_count": source_mapping_chunk_count,
        "high_impact_group_count": batch_counter["batch_1_high_impact_groups"],
        "medium_group_count": batch_counter["batch_2_medium_groups"],
        "singleton_group_count": batch_counter["batch_3_suggested_singletons"] + batch_counter["batch_4_unsuggested_singletons"],
        "candidate_source_suggestion_group_count": suggestion_group_count,
        "candidate_source_suggestion_count": suggestion_count,
        "latent_quote_followup_after_source_mapping": latent_quote_count,
        "cleanup_decisions_applied_now": 0,
        "source_mapping_blockers_resolved_now": 0,
        "source_mapping_blockers_remaining_after_rag015": source_mapping_chunk_count,
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
        "source_mapping_batches_id": RAG_SOURCE_MAPPING_BATCHES_ID,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "inputs": {
            "rag014_result_path": rel_path(rag014_path, root_path),
            "rag013_result_path": rel_path(rag013_path, root_path),
            "rag006_packet_path": rel_path(rag006_path, root_path),
            "rag009_result_path": rel_path(rag009_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "summary": summary,
        "priority_batches": build_priority_batches(review_groups),
        "source_mapping_review_groups": review_groups,
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
            "source_mapping_decisions_applied": False,
            "runtime_integration_gate_required_before_use": True,
        },
    }


def render_source_mapping_batches_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-015 Source-Mapping Batches",
        "",
        "RAG-015 organizes the remaining source-mapping review work. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Source-mapping groups: `{summary['source_mapping_group_count']}`",
        f"- Source-mapping chunks: `{summary['source_mapping_chunk_count']}`",
        f"- High-impact groups: `{summary['high_impact_group_count']}`",
        f"- Medium groups: `{summary['medium_group_count']}`",
        f"- Singleton groups: `{summary['singleton_group_count']}`",
        f"- Candidate source suggestion groups: `{summary['candidate_source_suggestion_group_count']}`",
        f"- Candidate source suggestions: `{summary['candidate_source_suggestion_count']}`",
        f"- Latent quote follow-ups after source mapping: `{summary['latent_quote_followup_after_source_mapping']}`",
        f"- Cleanup decisions applied now: `{summary['cleanup_decisions_applied_now']}`",
        f"- Source-mapping blockers resolved now: `{summary['source_mapping_blockers_resolved_now']}`",
        f"- Source-mapping blockers remaining: `{summary['source_mapping_blockers_remaining_after_rag015']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Priority Batches",
        "",
        "| Batch | Groups | Chunks | Latent quote follow-ups | Objective |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for batch in payload.get("priority_batches", []):
        objective = batch["objective"].replace("|", "/")
        lines.append(
            f"| `{batch['batch_id']}` | `{batch['group_count']}` | `{batch['chunk_count']}` | "
            f"`{batch['latent_quote_followup_chunk_count']}` | {objective} |"
        )

    lines.extend(
        [
            "",
            "## Source-Mapping Review Groups",
            "",
            "| Batch | Source title | Chunks | Suggestions | Latent quote follow-ups |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for group in payload.get("source_mapping_review_groups", []):
        title = group["source_title"].replace("|", "/")
        lines.append(
            f"| `{group['priority_batch']}` | {title} | `{group['remaining_chunk_count']}` | "
            f"`{group['candidate_source_suggestion_count']}` | `{group['latent_quote_followup_chunk_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- RAG-015 is a batch packet only.",
            "- Human source review is still required before source mapping can be accepted.",
            "- Candidate source suggestions are review hints only and are not auto-applied.",
            "- Larger groups are reviewed first because one source decision can unblock multiple chunks.",
            "- Source mapping may create additional quote-clearance follow-up work.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No source-mapping decisions are applied.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data is used.",
            "- No source excerpt text is stored.",
            "- A later runtime integration gate is required before any runtime use.",
            "",
        ]
    )
    return "\n".join(lines)
