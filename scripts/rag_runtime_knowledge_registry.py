from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_RUNTIME_KNOWLEDGE_REGISTRY_ID = "RAG-017-runtime-knowledge-registry"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))

DEFAULT_INCLUDED_ARTIFACT_KEYS = (
    "RAG-007-reviewed-first-slice",
    "RAG-010-reviewed-expansion-slice",
    "RAG-012-accepted-cleanup",
    "RAG-014-source-mapped-quote-followup",
    "RAG-016A-quote-clearance-decision-slice",
    "RAG-016B-voice-delivery-quote-clearance-decision-slice",
    "RAG-019-sales-communication-source-expansion",
)

ARTIFACT_ID_KEYS = (
    "reviewed_slice_id",
    "reviewed_expansion_slice_id",
    "accepted_cleanup_id",
    "source_mapped_quote_followup_id",
    "quote_clearance_decision_slice_id",
    "voice_delivery_decision_slice_id",
    "sales_communication_source_expansion_id",
)

COMMON_HARD_LIMITS = {
    "hidden_emotion_inference_allowed": False,
    "protected_trait_inference_allowed": False,
    "manipulation_allowed": False,
    "pressure_or_urgency_escalation_allowed": False,
    "protected_text_change_allowed": False,
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
        raise ValueError(f"RAG-017 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-017 path is restricted: {path_value}")
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


def artifact_id(payload: dict[str, Any]) -> str:
    for key in ARTIFACT_ID_KEYS:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    raise ValueError("RAG-017 input artifact has no recognized ID.")


def _artifact_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ("knowledge_items", "accepted_quote_clearance_items"):
        for item in payload.get(key, []):
            items.append(dict(item))
    return items


def _source_chunk_ids(item: dict[str, Any]) -> list[str]:
    chunk_ids = [str(value).strip() for value in item.get("source_chunk_ids", []) if str(value).strip()]
    chunk_id = str(item.get("chunk_id", "")).strip()
    if chunk_id and chunk_id not in chunk_ids:
        chunk_ids.append(chunk_id)
    return chunk_ids


def _source_ids(item: dict[str, Any]) -> list[str]:
    return [str(value).strip() for value in item.get("source_ids", []) if str(value).strip()]


def _source_urls(item: dict[str, Any]) -> list[str]:
    return [str(value).strip() for value in item.get("source_urls", []) if str(value).strip()]


def _trace_source_title(item: dict[str, Any]) -> str:
    source_titles = item.get("source_titles", [])
    if source_titles:
        return str(source_titles[0])
    return str(item.get("source_title", ""))


def _voice_item(item: dict[str, Any]) -> bool:
    return str(item.get("lane", "")) == "voice_delivery" or bool(item.get("voice_or_prosody_advisory_only", False))


def normalize_registry_item(item: dict[str, Any], source_artifact_id: str) -> dict[str, Any]:
    registry_id = str(item.get("knowledge_id", "")).strip()
    if not registry_id:
        raise ValueError(f"RAG-017 item from {source_artifact_id} is missing knowledge_id.")
    source_chunk_ids = _source_chunk_ids(item)
    source_ids = _source_ids(item)
    source_urls = _source_urls(item)
    if not source_chunk_ids or not source_ids:
        raise ValueError(f"RAG-017 item is missing trace fields: {registry_id}")
    lane = str(item.get("lane", "")).strip()
    voice_item = _voice_item(item)
    hard_limits = dict(COMMON_HARD_LIMITS)
    hard_limits.update(dict(item.get("hard_limits", {})))
    return {
        "registry_id": registry_id,
        "knowledge_id": registry_id,
        "source_artifact_id": source_artifact_id,
        "lane": lane,
        "category": lane,
        "advisory_rule_text": str(item.get("project_rule", "")),
        "safe_application": str(item.get("safe_application", "")),
        "do_not_use": str(item.get("do_not_use_when", "")),
        "guardrails": str(item.get("guardrail_notes", "")),
        "source_chunk_ids": source_chunk_ids,
        "source_ids": source_ids,
        "topic_ids": [str(value) for value in item.get("topic_ids", []) if str(value).strip()],
        "trace_metadata": {
            "source_artifact_id": source_artifact_id,
            "review_verdict": str(item.get("review_verdict", "")),
            "quote_dependency_resolved": bool(item.get("quote_dependency_resolved", True)),
            "source_title": _trace_source_title(item),
            "source_urls": source_urls,
        },
        "citation_trace": [
            {
                "source_id": source_id,
                "source_chunk_ids": source_chunk_ids,
                "artifact_id": source_artifact_id,
                **({"source_url": source_urls[index]} if index < len(source_urls) else {}),
            }
            for index, source_id in enumerate(source_ids)
        ],
        "runtime_registry_eligible": True,
        "retrieval_scope": "advisory_only",
        "retrieval_used_in_runtime": False,
        "protected_text_change_allowed": False,
        "voice_or_prosody_advisory_only": voice_item,
        "hard_limits": hard_limits,
    }


def build_runtime_knowledge_registry(
    artifact_paths: dict[str, Path | str],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    resolved_paths = {
        key: resolve_project_path(path, root_path)
        for key, path in artifact_paths.items()
    }
    payloads = {key: load_json(path) for key, path in resolved_paths.items()}
    included_artifacts: list[str] = []
    registry_items: list[dict[str, Any]] = []

    for key in DEFAULT_INCLUDED_ARTIFACT_KEYS:
        payload = payloads.get(key)
        if payload is None:
            raise ValueError(f"RAG-017 missing required artifact: {key}")
        _runtime_boundaries_are_disabled(payload, context=key)
        current_artifact_id = artifact_id(payload)
        if current_artifact_id != key:
            raise ValueError(f"RAG-017 artifact mismatch: expected {key}, got {current_artifact_id}")
        included_artifacts.append(current_artifact_id)
        for item in _artifact_items(payload):
            registry_items.append(normalize_registry_item(item, current_artifact_id))

    registry_ids = [item["registry_id"] for item in registry_items]
    duplicates = sorted({item_id for item_id in registry_ids if registry_ids.count(item_id) > 1})
    if duplicates:
        raise ValueError(f"RAG-017 duplicate registry IDs: {duplicates}")

    lane_counts = Counter(item["lane"] for item in registry_items)
    voice_count = sum(1 for item in registry_items if item["voice_or_prosody_advisory_only"])
    rag016b = payloads["RAG-016B-voice-delivery-quote-clearance-decision-slice"]
    rag016b_summary = rag016b.get("summary", {})
    summary = {
        "registry_item_count": len(registry_items),
        "lane_counts": dict(lane_counts),
        "voice_delivery_item_count": voice_count,
        "runtime_retrieval_enabled_by_default": False,
        "retrieval_used_in_runtime": False,
        "source_mapping_blocker_chunk_count_excluded": int(rag016b_summary.get("source_mapping_pending_chunk_count_from_rag015", 0)),
        "source_mapping_blocker_group_count_excluded": int(rag016b_summary.get("source_mapping_pending_group_count_from_rag015", 0)),
        "latent_quote_followup_count_excluded": int(rag016b_summary.get("source_mapping_latent_quote_followup_count_from_rag015", 0)),
        "source_excerpt_text_stored": False,
        "provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
        "reads_data_private": False,
        "external_vector_db_used": False,
        "embedding_provider_used": False,
    }
    return {
        "runtime_knowledge_registry_id": RAG_RUNTIME_KNOWLEDGE_REGISTRY_ID,
        "inputs": {key: rel_path(path, root_path) for key, path in resolved_paths.items()},
        "included_artifacts": included_artifacts,
        "summary": summary,
        "registry_items": registry_items,
        "excluded_runtime_sources": {
            "source_mapping_blocker_chunk_count": summary["source_mapping_blocker_chunk_count_excluded"],
            "source_mapping_blocker_group_count": summary["source_mapping_blocker_group_count_excluded"],
            "latent_quote_followup_count": summary["latent_quote_followup_count_excluded"],
            "reason": "Unresolved source-mapping blockers and latent quote follow-ups are not registry items.",
        },
        "boundaries": {
            "default_runtime_retrieval_enabled": False,
            "requires_explicit_runtime_enablement": True,
            "retrieval_used_in_runtime": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_data_allowed": False,
            "reads_data_private": False,
            "external_vector_db_used": False,
            "embedding_provider_used": False,
        },
    }


def render_runtime_knowledge_registry_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-017 Runtime Knowledge Registry",
        "",
        "RAG-017 creates a local opt-in registry from already accepted project-owned RAG slices. Runtime retrieval is disabled by default.",
        "",
        "## Summary",
        "",
        f"- Registry items: `{summary['registry_item_count']}`",
        f"- Voice-delivery advisory items: `{summary['voice_delivery_item_count']}`",
        f"- Runtime retrieval enabled by default: `{summary['runtime_retrieval_enabled_by_default']}`",
        f"- Source-mapping blocker chunks excluded: `{summary['source_mapping_blocker_chunk_count_excluded']}`",
        f"- Source-mapping blocker groups excluded: `{summary['source_mapping_blocker_group_count_excluded']}`",
        f"- Latent quote follow-ups excluded: `{summary['latent_quote_followup_count_excluded']}`",
        "",
        "## Included Artifacts",
        "",
    ]
    for artifact in payload["included_artifacts"]:
        lines.append(f"- `{artifact}`")

    lines.extend(
        [
            "",
            "## Runtime Boundary",
            "",
            "- Registry lookup is deterministic keyword matching only.",
            "- No external vector DB, embedding provider, provider call, NotebookLM API call, or private-data read is used.",
            "- Runtime use requires explicit opt-in from the guarded response path.",
            "- Retrieved items remain advisory-only and cannot alter protected text.",
            "",
            "## Exclusions",
            "",
            "- Unresolved source-mapping blockers stay out of the registry.",
            "- Latent quote follow-ups stay out of the registry.",
            "- Source excerpt text is not stored.",
            "",
        ]
    )
    return "\n".join(lines)
