from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_REVIEWED_EXPANSION_SLICE_ID = "RAG-010-reviewed-expansion-slice"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))

REVIEWED_EXPANSION_RULES: list[dict[str, Any]] = [
    {
        "knowledge_id": "rag010-response-impact-bridge",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-029"],
        "project_rule": "When a customer describes an operational issue, ask one neutral question that connects the issue to business impact the customer can confirm.",
        "safe_application": "Use when discovery needs to move from a surface problem to measurable impact, such as lost time, missed work, rework, churn risk, customer experience, or internal cost.",
        "do_not_use_when": "Do not invent PR risk, retention risk, financial loss, executive urgency, or any high-stakes consequence the customer has not stated or the campaign has not approved.",
        "guardrail_notes": "Impact discovery must stay low-pressure and evidence-seeking. Campaign facts, compliance text, refusal handling, and human escalation override this wording rule.",
    },
    {
        "knowledge_id": "rag010-response-so-what-clarifier",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-030"],
        "project_rule": "After a customer names a problem, ask one respectful impact clarifier so the agent understands why the issue matters before proposing a next step.",
        "safe_application": "Use when the customer gives a vague or operational answer and the agent needs the business or personal consequence in the customer's own terms.",
        "do_not_use_when": "Do not interrogate, challenge, or repeat impact questions after the customer has answered, declined, or asked for a direct factual response.",
        "guardrail_notes": "The clarifier must sound curious, not confrontational. It cannot turn weak pain into fabricated urgency or override a customer's refusal.",
    },
    {
        "knowledge_id": "rag010-response-real-timing-check",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-031"],
        "project_rule": "Ask about the customer's real timing, decision window, or deadline to understand priority without creating urgency.",
        "safe_application": "Use after a need or impact is identified and the next useful step depends on whether the buyer has a real timing constraint.",
        "do_not_use_when": "Do not manufacture scarcity, imply a deadline exists, or push for a meeting when the buyer is still clarifying the problem or has declined.",
        "guardrail_notes": "Timing qualification is for fit and prioritization only. It cannot become pressure, scarcity, or a reason to ignore hesitation.",
    },
    {
        "knowledge_id": "rag010-voice-cadence-as-weak-context",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-036"],
        "project_rule": "Treat customer speech pace as a weak context cue for response pacing or a gentle check-in, not as proof of hidden emotion or intent.",
        "safe_application": "Use to slow down, simplify, or ask a low-pressure clarification when fast, hesitant, or uneven speech suggests the customer may need more room.",
        "do_not_use_when": "Do not infer hidden emotion, urgency, stress, consent, refusal, truthfulness, or buying intent from cadence alone.",
        "guardrail_notes": "This is advisory delivery guidance only. It must not alter protected text, override explicit customer words, or personalize based on sensitive traits.",
        "voice_or_prosody_advisory_only": True,
    },
]

SELECTED_CHUNK_IDS = tuple(rule["source_chunk_ids"][0] for rule in REVIEWED_EXPANSION_RULES)
RULE_BY_CHUNK_ID = {rule["source_chunk_ids"][0]: rule for rule in REVIEWED_EXPANSION_RULES}


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
        raise ValueError(f"RAG-010 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-010 path is restricted: {path_value}")
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
        "notebooklm_api_used",
        "private_customer_data_used",
        "reads_data_private",
    ):
        if summary.get(key) is True:
            raise ValueError(f"{context} enables forbidden runtime boundary: {key}")


def _selected_chunk_ids_from_case(case_config: dict[str, Any]) -> list[str]:
    selected = [str(value) for value in case_config.get("selected_chunk_ids", [])]
    if set(selected) != set(SELECTED_CHUNK_IDS):
        raise ValueError(
            "RAG-010 case must select exactly the reviewed expansion chunk IDs: "
            f"{sorted(SELECTED_CHUNK_IDS)}"
        )
    return selected


def _candidate_rows(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for candidate in rag009_payload.get("next_promotion_candidates", []):
        chunk_id = str(candidate.get("chunk_id", "")).strip()
        if chunk_id:
            rows[chunk_id] = dict(candidate)
    if rows:
        return rows
    for candidate in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(candidate.get("chunk_id", "")).strip()
        if chunk_id and candidate.get("status") == "candidate_next_manual_review":
            rows[chunk_id] = dict(candidate)
    return rows


def _validate_candidate(chunk_id: str, row: dict[str, Any]) -> None:
    if row.get("status") != "candidate_next_manual_review":
        raise ValueError(f"RAG-010 selected chunk is not a clean RAG-009 candidate: {chunk_id}")
    if row.get("runtime_use_allowed") is True or row.get("retrieval_used_in_runtime") is True:
        raise ValueError(f"RAG-010 selected chunk has runtime use enabled: {chunk_id}")
    if row.get("quote_dependency_present") is True or row.get("quoted_text_copied") is True:
        raise ValueError(f"RAG-010 selected chunk still has quote dependency: {chunk_id}")
    if not row.get("source_ids"):
        raise ValueError(f"RAG-010 selected chunk has no source IDs: {chunk_id}")


def _knowledge_item(rule: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    chunk_id = rule["source_chunk_ids"][0]
    source_ids = [str(value) for value in candidate.get("source_ids", []) if str(value).strip()]
    topic_ids = [str(value) for value in candidate.get("topic_ids", []) if str(value).strip()]
    advisory_only = bool(rule.get("voice_or_prosody_advisory_only", False))
    return {
        "knowledge_id": rule["knowledge_id"],
        "lane": rule["lane"],
        "source_chunk_ids": [chunk_id],
        "source_ids": source_ids,
        "source_titles": [str(candidate.get("source_title", ""))],
        "topic_ids": topic_ids,
        "original_candidate_principle": str(candidate.get("principle", "")),
        "review_verdict": "manual_expansion_slice_paraphrased",
        "quote_dependency_resolved": True,
        "manual_review_clearance": {
            "selected_from_rag009_next_promotion_candidates": True,
            "quote_clearance_required": False,
            "quote_clearance_resolution": "not_required_clean_rag009_candidate",
            "source_excerpt_text_copied": False,
            "runtime_use_allowed": False,
            "clearance_note": "Manual RAG-010 review accepted a project-owned paraphrase from a clean RAG-009 next-promotion candidate.",
        },
        "project_rule": rule["project_rule"],
        "safe_application": rule["safe_application"],
        "do_not_use_when": rule["do_not_use_when"],
        "guardrail_notes": rule["guardrail_notes"],
        "voice_or_prosody_advisory_only": advisory_only,
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
    }


def build_reviewed_expansion_slice(
    rag009_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag009_payload = load_json(rag009_path)
    case_config = load_json(case_config_path)
    if case_config.get("reviewed_expansion_slice_id") != RAG_REVIEWED_EXPANSION_SLICE_ID:
        raise ValueError("RAG-010 case ID does not match the reviewed expansion slice ID.")
    _runtime_boundaries_are_disabled(rag009_payload, context="RAG-009 input")
    _runtime_boundaries_are_disabled(case_config, context="RAG-010 case")
    selected_chunk_ids = _selected_chunk_ids_from_case(case_config)
    candidate_rows = _candidate_rows(rag009_payload)

    knowledge_items: list[dict[str, Any]] = []
    for chunk_id in selected_chunk_ids:
        candidate = candidate_rows.get(chunk_id)
        if candidate is None:
            raise KeyError(f"RAG-010 selected chunk is missing from RAG-009 next-promotion candidates: {chunk_id}")
        _validate_candidate(chunk_id, candidate)
        knowledge_items.append(_knowledge_item(RULE_BY_CHUNK_ID[chunk_id], candidate))

    lane_counts = Counter(item["lane"] for item in knowledge_items)
    advisory_count = sum(1 for item in knowledge_items if item["voice_or_prosody_advisory_only"])
    summary = {
        "selected_chunk_count": len(selected_chunk_ids),
        "knowledge_item_count": len(knowledge_items),
        "lane_counts": {
            "response_wording": lane_counts["response_wording"],
            "voice_delivery": lane_counts["voice_delivery"],
        },
        "voice_or_prosody_advisory_item_count": advisory_count,
        "rejected_candidate_count": 0,
        "auto_promoted_chunk_count": 0,
        "runtime_retrieval_enabled": False,
        "retrieval_eligible_now": False,
        "chunk_import_enabled": False,
        "source_excerpt_text_stored": False,
        "external_provider_calls_made": False,
        "notebooklm_api_used": False,
        "private_customer_data_used": False,
        "source_metadata_final": False,
    }
    return {
        "reviewed_expansion_slice_id": RAG_REVIEWED_EXPANSION_SLICE_ID,
        "inputs": {
            "rag009_result_path": rel_path(rag009_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "summary": summary,
        "knowledge_items": knowledge_items,
        "review_decisions": {
            "promoted_chunk_ids": selected_chunk_ids,
            "rejected_chunk_ids": [],
            "decision_note": "All four clean RAG-009 next-promotion candidates were accepted as project-owned paraphrases for offline review artifacts only.",
        },
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
            "retrieval_policy_required_before_runtime_use": True,
        },
    }


def render_reviewed_expansion_slice_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-010 Reviewed Expansion Slice",
        "",
        "RAG-010 manually reviews the four clean RAG-009 next-promotion candidates. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Selected chunks: `{summary['selected_chunk_count']}`",
        f"- Knowledge items: `{summary['knowledge_item_count']}`",
        f"- Response wording items: `{summary['lane_counts']['response_wording']}`",
        f"- Voice delivery items: `{summary['lane_counts']['voice_delivery']}`",
        f"- Voice/prosody advisory items: `{summary['voice_or_prosody_advisory_item_count']}`",
        f"- Rejected candidates: `{summary['rejected_candidate_count']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Retrieval eligible now: `{summary['retrieval_eligible_now']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Reviewed Items",
        "",
        "| Knowledge ID | Lane | Source Chunk | Rule |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["knowledge_items"]:
        rule = item["project_rule"].replace("|", "/")
        lines.append(
            f"| `{item['knowledge_id']}` | `{item['lane']}` | `{item['source_chunk_ids'][0]}` | {rule} |"
        )
    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- All items are project-owned paraphrases.",
            "- Clean RAG-009 candidates do not require quote clearance.",
            "- Operational impact, timing, and follow-up questions must stay neutral and evidence-seeking.",
            "- Speech cadence is a weak delivery/context cue only; it cannot prove hidden emotion, intent, truthfulness, urgency, consent, or refusal.",
            "- Campaign guardrails, customer refusal, compliance text, and human escalation override every reviewed item.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer inputs are used.",
            "- No source excerpt text is stored.",
            "",
        ]
    )
    return "\n".join(lines)
