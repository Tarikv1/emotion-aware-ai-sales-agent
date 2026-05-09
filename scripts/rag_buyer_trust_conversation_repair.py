from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_BUYER_TRUST_CONVERSATION_REPAIR_ID = "RAG-021-buyer-trust-conversation-repair"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
REQUIRED_TOPIC_COUNT = 8

COMMON_HARD_LIMITS = {
    "hidden_emotion_inference_allowed": False,
    "protected_trait_inference_allowed": False,
    "manipulation_allowed": False,
    "pressure_or_urgency_escalation_allowed": False,
    "protected_text_change_allowed": False,
    "biometric_emotion_recognition_allowed": False,
    "buyer_autonomy_override_allowed": False,
    "unvalidated_emotion_classifier_runtime_use_allowed": False,
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
        raise ValueError(f"RAG-021 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-021 path is restricted: {path_value}")
    return resolved


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _assert_runtime_boundaries_disabled(payload: dict[str, Any]) -> None:
    boundaries = payload.get("boundaries", {})
    for key in (
        "runtime_retrieval_enabled",
        "retrieval_eligible_now",
        "chunk_import_enabled",
        "auto_promote_allowed",
        "source_excerpt_text_stored",
        "copied_scripts_stored",
        "provider_calls_allowed",
        "notebooklm_api_allowed",
        "private_customer_data_allowed",
        "reads_data_private",
        "external_vector_db_used",
        "embedding_provider_used",
    ):
        if boundaries.get(key) is True or payload.get(key) is True:
            raise ValueError(f"RAG-021 enables forbidden boundary: {key}")


def _source_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = payload.get("source_registry", [])
    if not isinstance(sources, list) or not sources:
        raise ValueError("RAG-021 source_registry is required.")
    by_id: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_id = str(source.get("source_id", "")).strip()
        if not source_id:
            raise ValueError("RAG-021 source is missing source_id.")
        if source_id in by_id:
            raise ValueError(f"RAG-021 duplicate source_id: {source_id}")
        if not str(source.get("url", "")).startswith("https://"):
            raise ValueError(f"RAG-021 source must have https URL: {source_id}")
        by_id[source_id] = dict(source)
    return by_id


def _normalize_item(item: dict[str, Any], sources_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    knowledge_id = str(item.get("knowledge_id", "")).strip()
    chunk_id = str(item.get("chunk_id", "")).strip()
    lane = str(item.get("lane", "")).strip()
    source_ids = [str(source_id).strip() for source_id in item.get("source_ids", []) if str(source_id).strip()]
    if not knowledge_id or not chunk_id or not lane or not source_ids:
        raise ValueError(f"RAG-021 item missing required fields: {knowledge_id or item}")
    missing_sources = [source_id for source_id in source_ids if source_id not in sources_by_id]
    if missing_sources:
        raise ValueError(f"RAG-021 item references unknown sources: {knowledge_id} {missing_sources}")
    if "source_excerpt" in json.dumps(item, sort_keys=True).lower():
        raise ValueError(f"RAG-021 item stores forbidden source excerpt text: {knowledge_id}")

    source_urls = [str(sources_by_id[source_id]["url"]) for source_id in source_ids]
    source_titles = [str(sources_by_id[source_id]["title"]) for source_id in source_ids]
    hard_limits = dict(COMMON_HARD_LIMITS)
    hard_limits.update(dict(item.get("hard_limits", {})))
    return {
        **item,
        "source_chunk_ids": [chunk_id],
        "source_urls": source_urls,
        "source_titles": source_titles,
        "review_verdict": str(item.get("review_verdict", "manual_public_source_paraphrased")),
        "quote_dependency_resolved": bool(item.get("quote_dependency_resolved", True)),
        "human_acceptance_recorded": True,
        "voice_or_prosody_advisory_only": lane == "voice_delivery",
        "hard_limits": hard_limits,
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
        "manual_review_clearance": {
            "source_expansion_resolution": "project_owned_public_source_paraphrase_accepted",
            "source_excerpt_text_copied": False,
            "copied_script_text_stored": False,
            "runtime_use_allowed": False,
        },
    }


def build_buyer_trust_conversation_repair(case_path: Path | str, *, root: Path | None = None) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    resolved_case_path = resolve_project_path(case_path, root_path)
    case_payload = load_json(resolved_case_path)
    if case_payload.get("buyer_trust_conversation_repair_id") != RAG_BUYER_TRUST_CONVERSATION_REPAIR_ID:
        raise ValueError("RAG-021 case ID mismatch.")
    _assert_runtime_boundaries_disabled(case_payload)
    sources_by_id = _source_map(case_payload)
    items = [_normalize_item(dict(item), sources_by_id) for item in case_payload.get("knowledge_items", [])]
    if not items:
        raise ValueError("RAG-021 requires at least one knowledge item.")

    knowledge_ids = [item["knowledge_id"] for item in items]
    duplicates = sorted({item_id for item_id in knowledge_ids if knowledge_ids.count(item_id) > 1})
    if duplicates:
        raise ValueError(f"RAG-021 duplicate knowledge IDs: {duplicates}")

    covered_topics = [str(topic) for topic in case_payload.get("covered_deep_dive_topics", [])]
    if len(set(covered_topics)) < REQUIRED_TOPIC_COUNT:
        raise ValueError("RAG-021 does not cover all requested deep-dive topic groups.")

    lane_counts = Counter(item["lane"] for item in items)
    summary = {
        "source_count": len(sources_by_id),
        "knowledge_item_count": len(items),
        "covered_deep_dive_topic_count": len(set(covered_topics)),
        "lane_counts": dict(lane_counts),
        "runtime_retrieval_enabled": False,
        "retrieval_eligible_now": False,
        "chunk_import_enabled": False,
        "source_excerpt_text_stored": False,
        "copied_scripts_stored": False,
        "provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
        "reads_data_private": False,
        "external_vector_db_used": False,
        "embedding_provider_used": False,
    }
    return {
        "buyer_trust_conversation_repair_id": RAG_BUYER_TRUST_CONVERSATION_REPAIR_ID,
        "inputs": {
            "case_path": rel_path(resolved_case_path, root_path),
        },
        "acceptance": case_payload["acceptance"],
        "summary": summary,
        "covered_deep_dive_topics": covered_topics,
        "source_registry": list(sources_by_id.values()),
        "knowledge_items": items,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "copied_scripts_stored": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
            "external_vector_db_used": False,
            "embedding_provider_used": False,
            "runtime_registry_gate_required_before_use": True,
        },
    }


def render_buyer_trust_conversation_repair_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-021 Buyer Trust Conversation Repair",
        "",
        "RAG-021 adds public-source-backed, project-owned advisory rules for buyer value, trust repair, autonomy, clarity, conversation repair, emotion regulation support, and AI transparency. It stores paraphrases only.",
        "",
        "## Summary",
        "",
        f"- Sources reviewed: `{summary['source_count']}`",
        f"- Knowledge items accepted: `{summary['knowledge_item_count']}`",
        f"- Deep-dive topic groups covered: `{summary['covered_deep_dive_topic_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Source excerpt text stored: `{summary['source_excerpt_text_stored']}`",
        f"- Copied scripts stored: `{summary['copied_scripts_stored']}`",
        "",
        "## Covered Topic Groups",
        "",
    ]
    for topic in payload["covered_deep_dive_topics"]:
        lines.append(f"- `{topic}`")
    lines.extend(["", "## Sources", ""])
    for source in payload["source_registry"]:
        lines.append(f"- `{source['source_id']}` {source['title']} - {source['url']}")
    lines.extend(
        [
            "",
            "## Trust Repair And Conversation Repair",
            "",
            "- Trust objections should be diagnosed as ability, benevolence, or integrity gaps before answering.",
            "- Conversation repair should invite correction instead of assuming the buyer's hidden state.",
            "- Plain language and cognitive-load limits are part of persuasion quality, not cosmetic style.",
            "",
            "## Runtime Boundary",
            "",
            "- Items are advisory-only public-source paraphrases.",
            "- No source excerpts, copied scripts, private customer data, provider calls, embeddings, or vector database are used.",
            "- RAG-021 is not imported into the RAG-017 runtime registry in this pass.",
            "- Runtime use requires a separate registry rebuild and RAG-018 guarded-retrieval evaluation.",
            "- Compliance, refusal, protected text, and human escalation override every sales rule.",
            "",
        ]
    )
    return "\n".join(lines)
