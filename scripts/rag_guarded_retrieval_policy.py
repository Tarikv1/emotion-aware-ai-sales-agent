from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


RAG_GUARDED_RETRIEVAL_POLICY_ID = "RAG-008-guarded-retrieval-policy"
RAG007_REVIEWED_SLICE_ID = "RAG-007-reviewed-first-slice"
RAG017_RUNTIME_REGISTRY_ID = "RAG-017-runtime-knowledge-registry"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
BLOCKING_CONTEXT_FLAGS = {
    "customer_refusal": "customer_refusal_overrides_retrieval",
    "do_not_call": "do_not_call_overrides_retrieval",
    "protected_script": "protected_script_text_must_not_change",
    "required_disclosure": "required_disclosure_text_must_not_change",
    "human_escalation": "human_escalation_overrides_retrieval",
    "pressure_sensitive": "pressure_sensitive_context_blocks_style_retrieval",
    "private_data_requested": "private_data_request_blocks_retrieval",
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "or",
    "that",
    "the",
    "this",
    "to",
    "use",
    "when",
    "with",
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


def _resolve_input_path(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    if _contains_private_path_parts(resolved):
        raise ValueError("RAG-008 input path is restricted.")
    return resolved


def load_json(path: Path | str) -> dict[str, Any]:
    json_path = Path(path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def searchable_text(item: dict[str, Any]) -> str:
    return " ".join(
        str(item.get(field, ""))
        for field in (
            "advisory_rule_text",
            "project_rule",
            "safe_application",
            "do_not_use",
            "do_not_use_when",
            "guardrails",
            "guardrail_notes",
        )
    )


def validate_rag007_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("reviewed_slice_id") != RAG007_REVIEWED_SLICE_ID:
        raise ValueError("RAG-008 can only read the RAG-007 reviewed first slice.")
    items = payload.get("knowledge_items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("RAG-007 reviewed slice has no knowledge_items.")
    for item in items:
        if item.get("review_verdict") != "manual_first_slice_paraphrased":
            raise ValueError(f"Unreviewed RAG item is not eligible: {item.get('knowledge_id')}")
        if item.get("runtime_eligible_now") is True or item.get("retrieval_eligible_now") is True:
            raise ValueError(f"RAG-008 requires non-runtime RAG-007 items: {item.get('knowledge_id')}")
        if not item.get("source_ids") or not item.get("source_chunk_ids"):
            raise ValueError(f"RAG-007 item is missing citation fields: {item.get('knowledge_id')}")
    return items


def validate_registry_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("runtime_knowledge_registry_id") != RAG017_RUNTIME_REGISTRY_ID:
        raise ValueError("RAG-008 requires the RAG-017 runtime knowledge registry.")
    summary = payload.get("summary", {})
    boundaries = payload.get("boundaries", {})
    if summary.get("runtime_retrieval_enabled_by_default") is True:
        raise ValueError("RAG-017 registry cannot enable runtime retrieval by default.")
    if summary.get("retrieval_used_in_runtime") is True or boundaries.get("retrieval_used_in_runtime") is True:
        raise ValueError("RAG-017 registry artifact cannot mark runtime retrieval as used.")
    items = payload.get("registry_items", [])
    if not isinstance(items, list) or not items:
        raise ValueError("RAG-017 registry has no registry_items.")
    for item in items:
        item_id = item.get("registry_id") or item.get("knowledge_id")
        if item.get("runtime_registry_eligible") is not True:
            raise ValueError(f"Registry item is not eligible: {item_id}")
        if item.get("retrieval_scope") != "advisory_only":
            raise ValueError(f"Registry item is not advisory-only: {item_id}")
        if item.get("retrieval_used_in_runtime") is True:
            raise ValueError(f"Registry item already marks runtime use: {item_id}")
        if item.get("protected_text_change_allowed") is True:
            raise ValueError(f"Registry item can change protected text: {item_id}")
        if not item.get("source_ids") or not item.get("source_chunk_ids") or not item.get("citation_trace"):
            raise ValueError(f"Registry item is missing trace fields: {item_id}")
    return items


def first_block_reason(context_flags: list[str]) -> str | None:
    for flag in context_flags:
        if flag in BLOCKING_CONTEXT_FLAGS:
            return BLOCKING_CONTEXT_FLAGS[flag]
    return None


def lane_allowed(item_lane: str, lane_filter: str) -> bool:
    return lane_filter == "any" or item_lane == lane_filter


def build_candidate(item: dict[str, Any], query_tokens: set[str], item_tokens: set[str], score: int) -> dict[str, Any]:
    overlap = sorted(query_tokens & item_tokens)
    knowledge_id = str(item.get("registry_id") or item.get("knowledge_id", ""))
    source_ids = [str(source_id) for source_id in item.get("source_ids", []) if source_id]
    source_chunk_ids = [str(chunk_id) for chunk_id in item.get("source_chunk_ids", []) if chunk_id]
    citation_trace = item.get("citation_trace") or [
        {"source_id": source_id, "source_chunk_ids": source_chunk_ids}
        for source_id in source_ids
    ]
    return {
        "knowledge_id": knowledge_id,
        "registry_id": knowledge_id,
        "lane": item["lane"],
        "source_chunk_ids": source_chunk_ids,
        "source_ids": source_ids,
        "project_rule": item.get("advisory_rule_text") or item.get("project_rule", ""),
        "guardrail_notes": item.get("guardrails") or item.get("guardrail_notes", ""),
        "match_reasons": [f"keyword_overlap:{token}" for token in overlap[:8]] or ["lane_filter_match"],
        "match_score": score,
        "citation_trace": citation_trace,
        "retrieval_scope": "advisory_only",
        "voice_delivery_advisory_only": item.get("lane") == "voice_delivery" or bool(item.get("voice_or_prosody_advisory_only")),
        "protected_text_change_allowed": False,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def retrieve_for_case(case: dict[str, Any], items: list[dict[str, Any]], max_results: int) -> dict[str, Any]:
    case_id = str(case.get("case_id", ""))
    lane_filter = str(case.get("lane_filter", "any"))
    context_flags = [str(flag) for flag in case.get("context_flags", []) if flag]
    block_reason = first_block_reason(context_flags)
    if block_reason:
        return {
            "case_id": case_id,
            "lane_filter": lane_filter,
            "context_flags": context_flags,
            "retrieval_decision": "blocked",
            "block_reason": block_reason,
            "retrieved_items": [],
        }

    query_tokens = tokens(str(case.get("query", "")))
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for item in items:
        if not lane_allowed(str(item.get("lane", "")), lane_filter):
            continue
        item_tokens = tokens(searchable_text(item))
        score = len(query_tokens & item_tokens)
        if score <= 0:
            continue
        candidate = build_candidate(item, query_tokens, item_tokens, score)
        scored.append((score, str(item.get("knowledge_id", "")), candidate))

    scored.sort(key=lambda row: (-row[0], row[1]))
    retrieved_items = [candidate for _, _, candidate in scored[:max_results]]
    return {
        "case_id": case_id,
        "lane_filter": lane_filter,
        "context_flags": context_flags,
        "retrieval_decision": "candidate_packet_created" if retrieved_items else "no_match",
        "block_reason": "",
        "retrieved_items": retrieved_items,
    }


def build_guarded_retrieval_policy(
    registry_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    registry_path = _resolve_input_path(registry_result_path, root_path)
    cases_path = _resolve_input_path(case_path, root_path)
    registry_payload = load_json(registry_path)
    case_payload = load_json(cases_path)
    items = validate_registry_payload(registry_payload)
    max_results = int(case_payload.get("max_results", 3))
    query_cases = case_payload.get("query_cases", [])
    if not isinstance(query_cases, list) or not query_cases:
        raise ValueError("RAG-008 case file must contain query_cases.")

    case_results = [retrieve_for_case(case, items, max_results) for case in query_cases]
    decision_counts = Counter(result["retrieval_decision"] for result in case_results)
    retrieved_item_count = sum(len(result["retrieved_items"]) for result in case_results)
    retrieved_knowledge_ids = sorted(
        {
            item["knowledge_id"]
            for result in case_results
            for item in result["retrieved_items"]
        }
    )
    summary = {
        "query_case_count": len(case_results),
        "retrieval_case_count": sum(1 for result in case_results if result["retrieved_items"]),
        "blocked_case_count": decision_counts["blocked"],
        "retrieved_item_count": retrieved_item_count,
        "unique_retrieved_knowledge_count": len(retrieved_knowledge_ids),
        "runtime_retrieval_enabled_by_default": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promoted_chunk_count": 0,
        "provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
        "reads_data_private": False,
        "source_excerpt_text_stored": False,
        "only_runtime_registry_used": True,
    }
    return {
        "retrieval_policy_id": RAG_GUARDED_RETRIEVAL_POLICY_ID,
        "inputs": {
            "registry_result_path": rel_path(registry_path, root_path),
            "case_path": rel_path(cases_path, root_path),
            "registry_id": registry_payload.get("runtime_knowledge_registry_id", ""),
        },
        "summary": summary,
        "policy": {
            "max_results": max_results,
            "matching": "deterministic_keyword_overlap",
            "hard_block_flags": dict(BLOCKING_CONTEXT_FLAGS),
            "voice_delivery_scope": "advisory_only",
            "runtime_use_allowed": False,
        },
        "retrieved_knowledge_ids": retrieved_knowledge_ids,
        "case_results": case_results,
        "boundaries": {
            "default_runtime_retrieval_enabled": False,
            "retrieval_used_in_runtime": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
            "only_runtime_registry_used": True,
            "explicit_runtime_enablement_required_before_live_use": True,
        },
    }


def render_guarded_retrieval_policy_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-008 Guarded Retrieval Policy",
        "",
        "RAG-008 creates a dry-run retrieval packet over the RAG-017 runtime knowledge registry. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Query cases: `{summary['query_case_count']}`",
        f"- Retrieved cases: `{summary['retrieval_case_count']}`",
        f"- Blocked cases: `{summary['blocked_case_count']}`",
        f"- Retrieved item packets: `{summary['retrieved_item_count']}`",
        f"- Runtime retrieval enabled by default: `{summary['runtime_retrieval_enabled_by_default']}`",
        f"- Retrieval used in runtime: `{summary['retrieval_used_in_runtime']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        f"- Only runtime registry used: `{summary['only_runtime_registry_used']}`",
        "",
        "## Retrieved Cases",
        "",
        "| Case | Retrieved Knowledge |",
        "| --- | --- |",
    ]
    for result in payload["case_results"]:
        if not result["retrieved_items"]:
            continue
        knowledge_ids = ", ".join(f"`{item['knowledge_id']}`" for item in result["retrieved_items"])
        lines.append(f"| `{result['case_id']}` | {knowledge_ids} |")

    lines.extend(["", "## Blocked Cases", "", "| Case | Block Reason |", "| --- | --- |"])
    for result in payload["case_results"]:
        if result["retrieval_decision"] != "blocked":
            continue
        lines.append(f"| `{result['case_id']}` | `{result['block_reason']}` |")

    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Candidate packets are not used by the runtime sales agent.",
            "- Chunk import remains disabled.",
            "- Voice-delivery items are advisory only.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer inputs are used.",
            "- No source excerpt text is stored.",
            "",
        ]
    )
    return "\n".join(lines)
