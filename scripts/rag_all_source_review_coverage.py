from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RAG_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
RAG004_SOURCE_MANIFEST_ID = "RAG-004-source-manifest-normalization"
RAG005_CHUNK_NORMALIZATION_ID = "RAG-005-chunk-normalization"
RAG006_REVIEW_PACKET_ID = "RAG-006-chunk-review-packet"
RAG007_REVIEWED_SLICE_ID = "RAG-007-reviewed-first-slice"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
DEFAULT_REJECT_PATTERNS = [
    "hidden emotion with certainty",
    "guarantee hidden intent",
    "sensitive demographic",
    "protected attribute",
    "rewrite required disclosure",
    "ignore refusal",
    "push past hesitation",
    "pressure tactic",
    "create urgency",
    "creating time pressure",
    "time pressure",
    "scarcity",
    "threat",
    "ultimatum",
    "simulate human suffering",
    "lie about its identity",
]


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


def _resolve_input_path(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    if _contains_private_path_parts(resolved):
        raise ValueError("RAG-009 input path is restricted.")
    return resolved


def load_json(path: Path | str) -> dict[str, Any]:
    json_path = Path(path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def load_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = payload.get("source_manifest", payload)
    sources = manifest.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("RAG-004 payload must contain a source list.")
    return [dict(source) for source in sources]


def load_chunks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = payload.get("chunk_candidates", [])
    if not isinstance(chunks, list):
        raise ValueError("RAG-005 payload must contain chunk_candidates.")
    return [dict(chunk) for chunk in chunks]


def validate_inputs(
    rag004_payload: dict[str, Any],
    rag005_payload: dict[str, Any],
    rag006_payload: dict[str, Any],
    rag007_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> None:
    if case_payload.get("review_coverage_id") != RAG_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-009 case file has the wrong review_coverage_id.")
    if rag006_payload.get("review_packet_id") != RAG006_REVIEW_PACKET_ID:
        raise ValueError("RAG-009 requires the RAG-006 review packet.")
    if rag007_payload.get("reviewed_slice_id") != RAG007_REVIEWED_SLICE_ID:
        raise ValueError("RAG-009 requires the RAG-007 reviewed first slice.")
    for payload_name, payload in (
        ("RAG-004", rag004_payload),
        ("RAG-005", rag005_payload),
        ("RAG-006", rag006_payload),
        ("RAG-007", rag007_payload),
        ("RAG-009 case", case_payload),
    ):
        summary = payload.get("summary", payload)
        if summary.get("runtime_retrieval_enabled") is True:
            raise ValueError(f"{payload_name} cannot have runtime retrieval enabled.")
        if summary.get("chunk_import_enabled") is True:
            raise ValueError(f"{payload_name} cannot have chunk import enabled.")


def chunk_id_value(chunk: dict[str, Any]) -> str:
    return str(chunk.get("chunk_candidate_id") or chunk.get("chunk_id") or "")


def index_rag006_locations(payload: dict[str, Any]) -> dict[str, list[str]]:
    locations: dict[str, set[str]] = defaultdict(set)

    def add(value: Any, location: str) -> None:
        chunk_id = str(value or "")
        if chunk_id:
            locations[chunk_id].add(location)

    for item in payload.get("first_slice_candidates", []):
        add(item.get("chunk_id") or item.get("chunk_candidate_id"), "first_slice_candidates")

    review_queues = payload.get("review_queues", {})
    for item in review_queues.get("source_mapping_queue", []):
        for chunk_id in item.get("chunk_ids", []):
            add(chunk_id, "source_mapping_queue")
        add(item.get("chunk_id") or item.get("chunk_candidate_id"), "source_mapping_queue")

    for queue_name in ("topic_mapping_queue", "quote_review_queue"):
        for item in review_queues.get(queue_name, []):
            add(item.get("chunk_id") or item.get("chunk_candidate_id"), queue_name)

    return {chunk_id: sorted(values) for chunk_id, values in locations.items()}


def reviewed_chunk_ids(payload: dict[str, Any]) -> set[str]:
    chunk_ids: set[str] = set()
    for item in payload.get("knowledge_items", []):
        for chunk_id in item.get("source_chunk_ids", []):
            if chunk_id:
                chunk_ids.add(str(chunk_id))
    return chunk_ids


def text_for_safety_scan(chunk: dict[str, Any]) -> str:
    values = [
        str(chunk.get("principle", "")),
        str(chunk.get("application", "")),
        str(chunk.get("compliance_notes", "")),
        " ".join(str(value) for value in chunk.get("emotional_cues", [])),
    ]
    return " ".join(values).lower()


def reject_patterns(case_payload: dict[str, Any]) -> list[str]:
    configured = [str(pattern).lower() for pattern in case_payload.get("reject_patterns", []) if pattern]
    return sorted(set(configured + DEFAULT_REJECT_PATTERNS))


def safety_rejection_reasons(chunk: dict[str, Any], patterns: list[str]) -> list[str]:
    text = text_for_safety_scan(chunk)
    reasons = []
    for pattern in patterns:
        if pattern and pattern in text:
            reasons.append(f"reject_pattern:{pattern}")
    if re.search(r"\binfer\b.*\bhidden emotion\b", text):
        reasons.append("reject_pattern:hidden_emotion_certainty")
    if re.search(r"\b(create|creating)\b.*\burgency\b", text):
        reasons.append("reject_pattern:urgency_pressure")
    return sorted(set(reasons))


def determine_chunk_status(
    chunk: dict[str, Any],
    *,
    rag006_locations: list[str],
    reviewed_ids: set[str],
    patterns: list[str],
) -> tuple[str, list[str]]:
    chunk_id = chunk_id_value(chunk)
    flags = set(str(flag) for flag in chunk.get("review_flags", []))
    source_ids = [source_id for source_id in chunk.get("source_ids", []) if source_id]

    if chunk_id in reviewed_ids:
        return "reviewed_rag007", ["manual_reviewed_first_slice"]
    if "source_mapping_required" in flags or not source_ids or "source_mapping_queue" in rag006_locations:
        return "blocked_source_mapping", ["source_mapping_required"]
    if "topic_mapping_required" in flags or "topic_mapping_queue" in rag006_locations:
        return "blocked_topic_mapping", ["topic_mapping_required"]

    rejection_reasons = safety_rejection_reasons(chunk, patterns)
    if rejection_reasons:
        return "rejected_safety", rejection_reasons

    if "quote_review_required" in flags or chunk.get("source_excerpt_present") is True or "quote_review_queue" in rag006_locations:
        return "blocked_quote_clearance", ["quote_clearance_required"]

    return "candidate_next_manual_review", ["clean_candidate_for_manual_review"]


def compact_source(source: dict[str, Any], chunk_ids: list[str]) -> dict[str, Any]:
    return {
        "source_id": str(source.get("source_id", "")),
        "canonical_title": str(source.get("canonical_title", "")),
        "topic_ids": [str(topic_id) for topic_id in source.get("topic_ids", [])],
        "metadata_status": str(source.get("metadata_status", "")),
        "rights_status": str(source.get("rights_status", "")),
        "use_status": str(source.get("use_status", "")),
        "raw_source_text_stored": bool(source.get("raw_source_text_stored", False)),
        "secret_like_detected": bool(source.get("secret_like_detected", False)),
        "chunk_ids": chunk_ids,
        "chunk_count": len(chunk_ids),
        "review_action": "complete_metadata_review_before_runtime_use",
    }


def is_voice_or_prosody_chunk(chunk: dict[str, Any]) -> bool:
    text = " ".join(
        [
            " ".join(str(topic_id) for topic_id in chunk.get("topic_ids", [])),
            str(chunk.get("evidence_type", "")),
            str(chunk.get("principle", "")),
            str(chunk.get("application", "")),
        ]
    ).lower()
    return any(term in text for term in ("voice", "prosody", "tone", "vocal", "speech"))


def compact_chunk(
    chunk: dict[str, Any],
    *,
    status: str,
    status_reasons: list[str],
    locations: list[str],
) -> dict[str, Any]:
    source_ids = [str(source_id) for source_id in chunk.get("source_ids", []) if source_id]
    topic_ids = [str(topic_id) for topic_id in chunk.get("topic_ids", [])]
    item = {
        "chunk_id": chunk_id_value(chunk),
        "source_title": str(chunk.get("source_title", "")),
        "source_ids": source_ids,
        "topic_ids": topic_ids,
        "original_topic_id": str(chunk.get("original_topic_id", "")),
        "principle": str(chunk.get("principle", "")),
        "application": str(chunk.get("application", "")),
        "when_not_to_use": str(chunk.get("when_not_to_use", "")),
        "review_flags": [str(flag) for flag in chunk.get("review_flags", [])],
        "rag006_locations": locations,
        "quote_dependency_present": bool(chunk.get("source_excerpt_present", False)) or "quote_review_required" in chunk.get("review_flags", []),
        "quoted_text_copied": False,
        "status": status,
        "status_reasons": status_reasons,
        "voice_or_prosody_advisory_only": is_voice_or_prosody_chunk(chunk),
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }
    return item


def build_review_queues(chunk_coverage: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    queues = {
        "source_mapping_queue": [],
        "topic_mapping_queue": [],
        "quote_clearance_queue": [],
        "safety_rejection_queue": [],
        "deferred_review_queue": [],
    }
    queue_by_status = {
        "blocked_source_mapping": "source_mapping_queue",
        "blocked_topic_mapping": "topic_mapping_queue",
        "blocked_quote_clearance": "quote_clearance_queue",
        "rejected_safety": "safety_rejection_queue",
        "deferred_review": "deferred_review_queue",
    }
    for chunk in chunk_coverage:
        queue_name = queue_by_status.get(chunk["status"])
        if not queue_name:
            continue
        queues[queue_name].append(
            {
                "chunk_id": chunk["chunk_id"],
                "source_title": chunk["source_title"],
                "source_ids": chunk["source_ids"],
                "topic_ids": chunk["topic_ids"],
                "status_reasons": chunk["status_reasons"],
                "review_action": review_action_for_status(chunk["status"]),
            }
        )
    return queues


def review_action_for_status(status: str) -> str:
    return {
        "blocked_source_mapping": "map_to_rag004_source_or_create_reviewed_source",
        "blocked_topic_mapping": "confirm_approved_project_topic",
        "blocked_quote_clearance": "replace_quote_dependency_with_project_owned_paraphrase",
        "rejected_safety": "keep_out_of_promotion_unless_reversed_by_human_review",
        "deferred_review": "review_after_higher_priority_queues",
    }.get(status, "review_manually")


def build_promotion_ledger(chunk_coverage: list[dict[str, Any]]) -> dict[str, list[str]]:
    ledger: dict[str, list[str]] = defaultdict(list)
    for chunk in chunk_coverage:
        ledger[chunk["status"]].append(chunk["chunk_id"])
    return {status: sorted(chunk_ids) for status, chunk_ids in sorted(ledger.items())}


def build_all_source_review_coverage(
    rag004_result_path: Path | str,
    rag005_result_path: Path | str,
    rag006_packet_path: Path | str,
    rag007_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag004_path = _resolve_input_path(rag004_result_path, root_path)
    rag005_path = _resolve_input_path(rag005_result_path, root_path)
    rag006_path = _resolve_input_path(rag006_packet_path, root_path)
    rag007_path = _resolve_input_path(rag007_result_path, root_path)
    case_config_path = _resolve_input_path(case_path, root_path)

    rag004_payload = load_json(rag004_path)
    rag005_payload = load_json(rag005_path)
    rag006_payload = load_json(rag006_path)
    rag007_payload = load_json(rag007_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag004_payload, rag005_payload, rag006_payload, rag007_payload, case_payload)

    sources = load_sources(rag004_payload)
    chunks = load_chunks(rag005_payload)
    rag006_by_chunk = index_rag006_locations(rag006_payload)
    reviewed_ids = reviewed_chunk_ids(rag007_payload)
    patterns = reject_patterns(case_payload)

    chunks_by_source: dict[str, list[str]] = defaultdict(list)
    chunk_coverage = []
    for chunk in chunks:
        chunk_id = chunk_id_value(chunk)
        locations = rag006_by_chunk.get(chunk_id, [])
        status, status_reasons = determine_chunk_status(
            chunk,
            rag006_locations=locations,
            reviewed_ids=reviewed_ids,
            patterns=patterns,
        )
        coverage_item = compact_chunk(chunk, status=status, status_reasons=status_reasons, locations=locations)
        chunk_coverage.append(coverage_item)
        for source_id in coverage_item["source_ids"]:
            chunks_by_source[source_id].append(chunk_id)

    source_coverage = [
        compact_source(source, sorted(chunks_by_source.get(str(source.get("source_id", "")), [])))
        for source in sources
    ]
    chunk_coverage.sort(key=lambda item: item["chunk_id"])
    source_coverage.sort(key=lambda item: item["source_id"])

    status_counts = Counter(item["status"] for item in chunk_coverage)
    next_limit = int(case_payload.get("max_next_promotion_candidates", 25))
    next_promotion_candidates = [
        {
            "chunk_id": item["chunk_id"],
            "source_ids": item["source_ids"],
            "topic_ids": item["topic_ids"],
            "principle": item["principle"],
            "application": item["application"],
            "voice_or_prosody_advisory_only": item["voice_or_prosody_advisory_only"],
            "runtime_use_allowed": False,
        }
        for item in chunk_coverage
        if item["status"] == "candidate_next_manual_review"
    ][:next_limit]
    rag004_source_ids = {str(source.get("source_id", "")) for source in sources if source.get("source_id")}
    rag005_chunk_ids = {chunk_id_value(chunk) for chunk in chunks if chunk_id_value(chunk)}
    summary = {
        "source_count": len(source_coverage),
        "chunk_candidate_count": len(chunk_coverage),
        "reviewed_rag007_chunk_count": status_counts["reviewed_rag007"],
        "candidate_next_manual_review_count": status_counts["candidate_next_manual_review"],
        "blocked_source_mapping_count": status_counts["blocked_source_mapping"],
        "blocked_topic_mapping_count": status_counts["blocked_topic_mapping"],
        "blocked_quote_clearance_count": status_counts["blocked_quote_clearance"],
        "rejected_safety_count": status_counts["rejected_safety"],
        "deferred_review_count": status_counts["deferred_review"],
        "next_promotion_candidate_count": len(next_promotion_candidates),
        "auto_promoted_chunk_count": 0,
        "all_rag004_sources_accounted_for": len(rag004_source_ids) == len(source_coverage),
        "all_rag005_chunks_accounted_for": len(rag005_chunk_ids) == len(chunk_coverage),
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
        "review_coverage_id": RAG_ALL_SOURCE_REVIEW_COVERAGE_ID,
        "inputs": {
            "rag004_result_path": rel_path(rag004_path, root_path),
            "rag005_result_path": rel_path(rag005_path, root_path),
            "rag006_packet_path": rel_path(rag006_path, root_path),
            "rag007_result_path": rel_path(rag007_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "summary": summary,
        "source_coverage": source_coverage,
        "chunk_coverage": chunk_coverage,
        "review_queues": build_review_queues(chunk_coverage),
        "promotion_ledger": build_promotion_ledger(chunk_coverage),
        "next_promotion_candidates": next_promotion_candidates,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_used_in_runtime": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
            "source_excerpt_text_stored": False,
            "voice_prosody_advisory_only": True,
            "runtime_gate_required_before_live_use": True,
        },
    }


def render_all_source_review_coverage_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-009 All-Source Review Coverage",
        "",
        "RAG-009 creates all-source review coverage before runtime retrieval. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Sources accounted for: `{summary['source_count']}`",
        f"- Chunks accounted for: `{summary['chunk_candidate_count']}`",
        f"- Reviewed RAG-007 chunks: `{summary['reviewed_rag007_chunk_count']}`",
        f"- Next promotion candidates: `{summary['next_promotion_candidate_count']}`",
        f"- Blocked for source mapping: `{summary['blocked_source_mapping_count']}`",
        f"- Blocked for topic mapping: `{summary['blocked_topic_mapping_count']}`",
        f"- Blocked for quote clearance: `{summary['blocked_quote_clearance_count']}`",
        f"- Rejected for safety: `{summary['rejected_safety_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Blocked Review Queues",
        "",
        "| Queue | Count |",
        "| --- | ---: |",
    ]
    for queue_name, rows in payload["review_queues"].items():
        lines.append(f"| `{queue_name}` | `{len(rows)}` |")

    lines.extend(["", "## Next Promotion Candidates", "", "| Chunk ID | Topics | Sources | Principle |", "| --- | --- | --- | --- |"])
    for item in payload["next_promotion_candidates"]:
        topic_ids = ", ".join(item["topic_ids"])
        source_ids = ", ".join(item["source_ids"])
        principle = str(item["principle"]).replace("|", "/")[:120]
        lines.append(f"| `{item['chunk_id']}` | {topic_ids} | {source_ids} | {principle} |")
    if not payload["next_promotion_candidates"]:
        lines.append("| none | none | none | none |")

    lines.extend(
        [
            "",
            "## Coverage Rules",
            "",
            "- Every RAG-004 source appears once in source coverage.",
            "- Every RAG-005 chunk appears once in chunk coverage.",
            "- RAG-007 chunks stay reviewed but non-runtime.",
            "- Blocked chunks require human review before any later promotion.",
            "- Rejected chunks stay out of promotion unless Tarik explicitly reverses the decision.",
            "- Voice and prosody guidance remains advisory only.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data is used.",
            "- No source excerpt text is stored.",
            "",
        ]
    )
    return "\n".join(lines)
