from __future__ import annotations

import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from rag_source_manifest_normalization import title_key


RAG_CHUNK_REVIEW_PACKET_ID = "RAG-006-chunk-review-packet"

SAFE_FIRST_SLICE_TOPIC_PRIORITY = [
    "objection_handling",
    "ethical_persuasion_persuasive_dialogue",
    "active_listening_human_like_sales_communication",
    "speech_tone_prosody_human_like_voice_behavior",
    "cold_calling",
]


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path | str) -> dict[str, Any]:
    json_path = Path(path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def load_manifest_sources(path: Path | str) -> list[dict[str, Any]]:
    payload = load_json(path)
    manifest = payload.get("source_manifest", payload)
    return list(manifest.get("sources", []))


def compact_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": chunk.get("chunk_candidate_id", ""),
        "source_title": chunk.get("source_title", ""),
        "source_ids": list(chunk.get("source_ids", [])),
        "topic_ids": list(chunk.get("topic_ids", [])),
        "original_topic_id": chunk.get("original_topic_id", ""),
        "principle": chunk.get("principle", ""),
        "application": chunk.get("application", ""),
        "when_not_to_use": chunk.get("when_not_to_use", ""),
        "review_flags": list(chunk.get("review_flags", [])),
    }


def token_set(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) >= 3}


def source_similarity(source_title: str, source: dict[str, Any]) -> float:
    source_key = title_key(source_title)
    title_values = [source.get("canonical_title", ""), *source.get("raw_titles", [])]
    best_score = 0.0
    for title in title_values:
        candidate_key = title_key(str(title))
        if not source_key or not candidate_key:
            continue
        ratio = SequenceMatcher(None, source_key, candidate_key).ratio()
        source_tokens = token_set(source_title)
        candidate_tokens = token_set(str(title))
        overlap = len(source_tokens & candidate_tokens) / max(1, len(source_tokens | candidate_tokens))
        best_score = max(best_score, round((ratio * 0.7) + (overlap * 0.3), 3))
    return best_score


def candidate_source_suggestions(source_title: str, sources: list[dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    suggestions = []
    for source in sources:
        score = source_similarity(source_title, source)
        if score < 0.45:
            continue
        suggestions.append(
            {
                "source_id": source.get("source_id", ""),
                "canonical_title": source.get("canonical_title", ""),
                "score": score,
                "review_only": True,
            }
        )
    suggestions.sort(key=lambda item: (-item["score"], item["source_id"]))
    return suggestions[:limit]


def build_source_mapping_queue(chunks: list[dict[str, Any]], sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        if "source_mapping_required" in chunk.get("review_flags", []) or not chunk.get("source_ids"):
            grouped[str(chunk.get("source_title", "") or "missing_source_title")].append(chunk)

    queue = []
    for source_title, group in grouped.items():
        topic_ids = sorted({topic_id for chunk in group for topic_id in chunk.get("topic_ids", [])})
        queue.append(
            {
                "source_title": source_title,
                "chunk_ids": [chunk.get("chunk_candidate_id", "") for chunk in group],
                "topic_ids": topic_ids,
                "chunk_count": len(group),
                "candidate_source_suggestions": candidate_source_suggestions(source_title, sources),
                "review_action": "map_to_existing_source_or_create_source_candidate",
                "auto_mapped": False,
            }
        )
    queue.sort(key=lambda item: (-item["chunk_count"], item["source_title"].lower()))
    return queue


def build_topic_mapping_queue(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for chunk in chunks:
        if "topic_mapping_required" not in chunk.get("review_flags", []):
            continue
        item = compact_chunk(chunk)
        item["review_action"] = "confirm_project_topic_or_create_taxonomy_note"
        queue.append(item)
    return queue


def build_quote_review_queue(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue = []
    for chunk in chunks:
        if not chunk.get("source_excerpt_present"):
            continue
        item = compact_chunk(chunk)
        item["source_excerpt_present"] = True
        item["review_action"] = "verify_quote_or_replace_with_paraphrase"
        queue.append(item)
    return queue


def first_slice_priority(chunk: dict[str, Any]) -> tuple[int, str]:
    topic_ids = chunk.get("topic_ids", [])
    priority = min(
        (SAFE_FIRST_SLICE_TOPIC_PRIORITY.index(topic_id) for topic_id in topic_ids if topic_id in SAFE_FIRST_SLICE_TOPIC_PRIORITY),
        default=len(SAFE_FIRST_SLICE_TOPIC_PRIORITY),
    )
    return priority, str(chunk.get("chunk_candidate_id", ""))


def build_first_slice_candidates(chunks: list[dict[str, Any]], *, limit: int = 20) -> list[dict[str, Any]]:
    candidates = []
    for chunk in chunks:
        flags = set(chunk.get("review_flags", []))
        if "source_mapping_required" in flags or "topic_mapping_required" in flags:
            continue
        if not chunk.get("source_ids"):
            continue
        item = compact_chunk(chunk)
        item["review_action"] = "human_review_for_possible_rag006_or_later_promotion"
        item["runtime_eligible_now"] = False
        candidates.append(item)
    candidates.sort(key=first_slice_priority)
    return candidates[:limit]


def build_review_packet(
    rag005_result_path: Path | str,
    source_manifest_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag005_path = Path(rag005_result_path)
    if not rag005_path.is_absolute():
        rag005_path = root_path / rag005_path
    manifest_path = Path(source_manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = root_path / manifest_path

    rag005_payload = load_json(rag005_path)
    sources = load_manifest_sources(manifest_path)
    chunks = list(rag005_payload.get("chunk_candidates", []))
    source_mapping_queue = build_source_mapping_queue(chunks, sources)
    topic_mapping_queue = build_topic_mapping_queue(chunks)
    quote_review_queue = build_quote_review_queue(chunks)
    first_slice_candidates = build_first_slice_candidates(chunks)

    source_mapping_chunk_count = sum(item["chunk_count"] for item in source_mapping_queue)
    summary = {
        "chunk_candidate_count": len(chunks),
        "source_mapping_queue_count": len(source_mapping_queue),
        "source_mapping_chunk_count": source_mapping_chunk_count,
        "topic_mapping_queue_count": len(topic_mapping_queue),
        "quote_review_queue_count": len(quote_review_queue),
        "first_slice_candidate_count": len(first_slice_candidates),
        "auto_promoted_chunk_count": 0,
        "runtime_retrieval_enabled": False,
        "chunk_import_enabled": False,
        "source_excerpt_text_stored": False,
        "external_provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
    }
    return {
        "review_packet_id": RAG_CHUNK_REVIEW_PACKET_ID,
        "rag005_result_path": rel_path(rag005_path, root_path),
        "source_manifest_path": rel_path(manifest_path, root_path),
        "summary": summary,
        "review_queues": {
            "source_mapping_queue": source_mapping_queue,
            "topic_mapping_queue": topic_mapping_queue,
            "quote_review_queue": quote_review_queue,
        },
        "first_slice_candidates": first_slice_candidates,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_suggestions_are_review_only": True,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "private_customer_data_allowed": False,
        },
    }


def render_review_packet_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-006 Chunk Review Packet",
        "",
        "This report turns RAG-005 candidates into human review queues before any runtime knowledge promotion.",
        "",
        "Runtime retrieval remains disabled. No chunks are promoted, imported, or used by the sales agent in this checkpoint.",
        "",
        "## Summary",
        "",
        f"- Chunk candidates reviewed: `{summary['chunk_candidate_count']}`",
        f"- Source-title review groups: `{summary['source_mapping_queue_count']}`",
        f"- Chunks needing source mapping: `{summary['source_mapping_chunk_count']}`",
        f"- Chunks needing topic mapping: `{summary['topic_mapping_queue_count']}`",
        f"- Chunks needing quote review: `{summary['quote_review_queue_count']}`",
        f"- First-slice review candidates: `{summary['first_slice_candidate_count']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Source Mapping Queue",
        "",
        "| Source Title | Chunk Count | Chunk IDs | Suggestions |",
        "| --- | ---: | --- | --- |",
    ]
    for item in payload["review_queues"]["source_mapping_queue"][:50]:
        chunk_ids = ", ".join(f"`{chunk_id}`" for chunk_id in item["chunk_ids"])
        suggestions = ", ".join(
            f"{suggestion['source_id']} ({suggestion['score']})"
            for suggestion in item["candidate_source_suggestions"]
        ) or "create_or_review_source"
        lines.append(f"| {item['source_title']} | {item['chunk_count']} | {chunk_ids} | {suggestions} |")

    lines.extend(
        [
            "",
            "## Topic Mapping Queue",
            "",
            "| Chunk ID | Original Topic | Current Topic IDs | Principle |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload["review_queues"]["topic_mapping_queue"][:50]:
        topic_ids = ", ".join(item["topic_ids"])
        principle = str(item["principle"]).replace("|", "/")[:120]
        lines.append(f"| `{item['chunk_id']}` | {item['original_topic_id']} | {topic_ids} | {principle} |")

    lines.extend(
        [
            "",
            "## First-Slice Review Candidates",
            "",
            "| Chunk ID | Topic IDs | Source IDs | Principle |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in payload["first_slice_candidates"]:
        topic_ids = ", ".join(item["topic_ids"])
        source_ids = ", ".join(item["source_ids"])
        principle = str(item["principle"]).replace("|", "/")[:120]
        lines.append(f"| `{item['chunk_id']}` | {topic_ids} | {source_ids} | {principle} |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- Treat source suggestions as review hints only, never automatic mappings.",
            "- Resolve source mappings before promotion.",
            "- Resolve topic mapping flags before promotion.",
            "- Review quote flags and replace source-excerpt dependence with paraphrased, cited knowledge.",
            "- Keep campaign guardrails above all RAG suggestions.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- No chunks are promoted.",
            "- No source excerpt text is stored.",
            "- No provider or NotebookLM API calls are made.",
            "",
        ]
    )
    return "\n".join(lines)
