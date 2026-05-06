from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_REVIEWED_FIRST_SLICE_ID = "RAG-007-reviewed-first-slice"

SELECTED_KNOWLEDGE_RULES: list[dict[str, Any]] = [
    {
        "knowledge_id": "rag007-response-yes-and-objection-framing",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-017"],
        "project_rule": "Acknowledge the customer's concern before moving to a useful next step; do not use agreement language to blur factual or compliance boundaries.",
        "safe_application": "Use when the customer raises a normal objection such as price, timing, complexity, or uncertainty and the agent can acknowledge the concern without validating a false claim.",
        "do_not_use_when": "Do not use when the customer states an incorrect fact, legal claim, medical claim, pricing detail, contract term, refusal, or do-not-call request; correct or honor that boundary directly.",
        "guardrail_notes": "Campaign facts, compliance language, refusal handling, human escalation, and do-not-call policy override this wording rule.",
    },
    {
        "knowledge_id": "rag007-response-declarative-clarity",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-020"],
        "project_rule": "Use short declarative statements when clarity matters, especially after an objection or broad question.",
        "safe_application": "Use to reduce rambling in explanations, next-step summaries, and concise value statements.",
        "do_not_use_when": "Do not make the agent sound clipped, robotic, dismissive, or aggressive; keep warmth and natural transitions.",
        "guardrail_notes": "This rule shapes freeform wording only and must not shorten required disclosures or campaign scripts.",
    },
    {
        "knowledge_id": "rag007-response-empathy-echo",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-022"],
        "project_rule": "Reflect a customer's key concern or emotional phrase sparingly before responding, so the reply shows listening without mechanical repetition.",
        "safe_application": "Use when the customer expresses frustration, confusion, hesitation, or a specific concern that should be acknowledged before the next question or explanation.",
        "do_not_use_when": "Do not repeat profanity, insults, private details, or the same phrase on every turn.",
        "guardrail_notes": "The echo is not an emotion diagnosis and must not override explicit customer intent.",
    },
    {
        "knowledge_id": "rag007-response-prep-structure",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-024"],
        "project_rule": "For a persuasive explanation, state the point, give the reason, add one concrete example, and return to the point.",
        "safe_application": "Use for medium-length answers where the customer needs a clear reason to continue or compare an option.",
        "do_not_use_when": "Do not use for simple yes/no answers, pleasantries, required compliance text, or urgent refusal handling.",
        "guardrail_notes": "Examples must be campaign-approved and truthful; the structure cannot invent claims or guarantees.",
    },
    {
        "knowledge_id": "rag007-response-3-2-1-structure",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-025"],
        "project_rule": "When an answer could sprawl, constrain it into a small numbered structure such as three points, two options, or one key takeaway.",
        "safe_application": "Use when the customer asks a broad or unexpected question and the agent needs a concise, organized response.",
        "do_not_use_when": "Do not use when the customer asked for one direct factual answer or when numbering would sound evasive.",
        "guardrail_notes": "Numbered structure cannot remove mandatory disclosures, uncertainty statements, or escalation language.",
    },
    {
        "knowledge_id": "rag007-voice-yes-and-posture",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-091"],
        "project_rule": "Use a non-defensive delivery posture when acknowledging objections; the voice should sound constructive rather than argumentative.",
        "safe_application": "Use to guide delivery tone for ordinary resistance where the agent can acknowledge and continue.",
        "do_not_use_when": "Do not sound agreeable when correcting a false claim, honoring a refusal, or delivering a compliance boundary.",
        "guardrail_notes": "This is delivery guidance only; it does not change the guarded text.",
    },
    {
        "knowledge_id": "rag007-voice-tone-mismatch-uncertainty",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-098"],
        "project_rule": "If words and vocal delivery appear misaligned, treat that as uncertainty and ask a gentle clarification instead of assuming hidden emotion or intent.",
        "safe_application": "Use when a customer says something positive or neutral but sounds hesitant, strained, or unsure, and a clarification would reduce pressure.",
        "do_not_use_when": "Do not override explicit consent, refusal, factual statements, compliance boundaries, or customer-stated preferences.",
        "guardrail_notes": "The agent must not claim it knows the customer's real emotion from tone; tone is only a weak signal for choosing a low-pressure clarification.",
    },
    {
        "knowledge_id": "rag007-voice-trustworthy-not-forced-friendly",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-099"],
        "project_rule": "Prefer a trustworthy, straightforward, moderately warm delivery over forced friendliness or entertainment.",
        "safe_application": "Use as the default delivery target across serious B2B and B2C sales campaigns.",
        "do_not_use_when": "Do not use exaggerated cheer, jokes, or overfamiliar phrasing in high-stakes or regulated contexts.",
        "guardrail_notes": "Campaign persona can adjust warmth, but trust and clarity remain the default delivery priority.",
    },
    {
        "knowledge_id": "rag007-voice-bounded-vocal-toolbox",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-101"],
        "project_rule": "Use controlled variation in pace, pitch, volume, warmth, and silence to support clarity and engagement.",
        "safe_application": "Use to guide TTS delivery metadata and human-review rubrics for freeform sales responses.",
        "do_not_use_when": "Do not imitate a source speaker's identity, accent, personal style, or theatrical performance.",
        "guardrail_notes": "Protected campaign scripts and compliance text must stay exact even when delivery metadata changes.",
    },
]

SELECTED_CHUNK_IDS = tuple(rule["source_chunk_ids"][0] for rule in SELECTED_KNOWLEDGE_RULES)
PRESSURE_TACTIC_CHUNK_IDS = {
    "rag005-chunk-071",
    "rag005-chunk-075",
    "rag005-chunk-076",
    "rag005-chunk-077",
    "rag005-chunk-087",
}

PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))
FORBIDDEN_ITEM_FIELDS = {
    "review_flags",
    "quote_review_required",
    "source_excerpt_text",
    "source_excerpt_text_stored",
}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _resolve_input_path(path: Path | str, root: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    parts = tuple(part.lower() for part in resolved.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                raise ValueError("RAG-007 input path is restricted.")
    return resolved


def load_json(path: Path | str) -> dict[str, Any]:
    json_path = Path(path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def load_manifest_sources(path: Path | str) -> dict[str, dict[str, Any]]:
    payload = load_json(path)
    manifest = payload.get("source_manifest", payload)
    sources: dict[str, dict[str, Any]] = {}
    for source in manifest.get("sources", []):
        source_id = source.get("source_id")
        if not source_id:
            continue
        sources[str(source_id)] = dict(source)
    return sources


def index_rag005_chunks(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(chunk.get("chunk_candidate_id", "")): chunk
        for chunk in payload.get("chunk_candidates", [])
        if chunk.get("chunk_candidate_id")
    }


def rag006_chunk_locations(payload: dict[str, Any]) -> dict[str, list[str]]:
    locations: dict[str, set[str]] = {}

    def add(chunk_id: Any, location: str) -> None:
        value = str(chunk_id or "")
        if value:
            locations.setdefault(value, set()).add(location)

    for item in payload.get("first_slice_candidates", []):
        add(item.get("chunk_id") or item.get("chunk_candidate_id"), "first_slice_candidates")

    review_queues = payload.get("review_queues", {})
    for queue_name in ("quote_review_queue", "topic_mapping_queue"):
        for item in review_queues.get(queue_name, []):
            add(item.get("chunk_id") or item.get("chunk_candidate_id"), queue_name)

    for item in review_queues.get("source_mapping_queue", []):
        for chunk_id in item.get("chunk_ids", []):
            add(chunk_id, "source_mapping_queue")
        add(item.get("chunk_id") or item.get("chunk_candidate_id"), "source_mapping_queue")

    return {chunk_id: sorted(values) for chunk_id, values in locations.items()}


def source_metadata_for(
    source_id: str,
    sources: dict[str, dict[str, Any]],
    *,
    chunk_id: str | None = None,
) -> dict[str, Any]:
    if source_id not in sources:
        chunk_detail = f" for chunk {chunk_id}" if chunk_id else ""
        raise ValueError(f"Missing RAG-004 source_id {source_id}{chunk_detail}.")
    source = sources[source_id]
    return {
        "source_id": source_id,
        "canonical_title": source.get("canonical_title", ""),
        "metadata_status": source.get("metadata_status", ""),
        "rights_status": source.get("rights_status", ""),
    }


def _source_title(source_id: str, chunk: dict[str, Any], sources: dict[str, dict[str, Any]]) -> str:
    source = sources.get(source_id, {})
    return str(source.get("canonical_title") or chunk.get("source_title") or source_id)


def build_knowledge_item(
    rule: dict[str, Any],
    rag005_chunks: dict[str, dict[str, Any]],
    rag006_locations: dict[str, list[str]],
    sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    chunk_ids = list(rule["source_chunk_ids"])
    if len(chunk_ids) != 1:
        raise ValueError(f"Expected exactly one source chunk for {rule['knowledge_id']}.")
    chunk_id = chunk_ids[0]
    if chunk_id in PRESSURE_TACTIC_CHUNK_IDS:
        raise ValueError(f"Pressure tactic chunk is not eligible: {chunk_id}")
    if chunk_id not in rag005_chunks:
        raise KeyError(f"Selected chunk missing from RAG-005: {chunk_id}")
    if chunk_id not in rag006_locations:
        raise KeyError(f"Selected chunk missing from RAG-006: {chunk_id}")

    locations = rag006_locations[chunk_id]
    blocked_locations = {"source_mapping_queue", "topic_mapping_queue"} & set(locations)
    if blocked_locations:
        raise ValueError(
            f"Selected chunk still needs review before RAG-007: {chunk_id}; "
            f"blocked_locations={sorted(blocked_locations)}"
        )

    chunk = rag005_chunks[chunk_id]
    source_ids = []
    for source_id in chunk.get("source_ids", []):
        if not source_id:
            continue
        source_id_value = str(source_id).strip()
        if source_id_value:
            source_ids.append(source_id_value)
    if not source_ids:
        raise ValueError(f"Selected chunk has no source IDs: {chunk_id}")
    for source_id in source_ids:
        if source_id not in sources:
            raise ValueError(f"Missing RAG-004 source_id {source_id} for chunk {chunk_id}.")

    return {
        "knowledge_id": rule["knowledge_id"],
        "lane": rule["lane"],
        "source_chunk_ids": [chunk_id],
        "source_ids": source_ids,
        "source_titles": [_source_title(source_id, chunk, sources) for source_id in source_ids],
        "source_metadata": {
            source_id: source_metadata_for(source_id, sources, chunk_id=chunk_id)
            for source_id in source_ids
        },
        "topic_ids": list(chunk.get("topic_ids", [])),
        "review_verdict": "manual_first_slice_paraphrased",
        "quote_dependency_resolved": True,
        "project_rule": rule["project_rule"],
        "safe_application": rule["safe_application"],
        "do_not_use_when": rule["do_not_use_when"],
        "guardrail_notes": rule["guardrail_notes"],
        "rag006_locations": sorted(set(locations)),
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
    }


def build_reviewed_first_slice(
    rag006_packet_path: Path | str,
    rag005_result_path: Path | str,
    source_manifest_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag006_path = _resolve_input_path(rag006_packet_path, root_path)
    rag005_path = _resolve_input_path(rag005_result_path, root_path)
    manifest_path = _resolve_input_path(source_manifest_path, root_path)

    rag006_payload = load_json(rag006_path)
    rag005_payload = load_json(rag005_path)
    sources = load_manifest_sources(manifest_path)
    rag005_chunks = index_rag005_chunks(rag005_payload)
    locations = rag006_chunk_locations(rag006_payload)
    knowledge_items = [
        build_knowledge_item(rule, rag005_chunks, locations, sources)
        for rule in SELECTED_KNOWLEDGE_RULES
    ]
    lane_counts = Counter(item["lane"] for item in knowledge_items)

    summary = {
        "selected_chunk_count": len(SELECTED_CHUNK_IDS),
        "knowledge_item_count": len(knowledge_items),
        "lane_counts": {
            "response_wording": lane_counts["response_wording"],
            "voice_delivery": lane_counts["voice_delivery"],
        },
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
        "reviewed_slice_id": RAG_REVIEWED_FIRST_SLICE_ID,
        "inputs": {
            "rag006_packet_path": rel_path(rag006_path, root_path),
            "rag005_result_path": rel_path(rag005_path, root_path),
            "source_manifest_path": rel_path(manifest_path, root_path),
        },
        "summary": summary,
        "knowledge_items": knowledge_items,
        "excluded_categories": {
            "pressure_tactic_chunk_ids": sorted(PRESSURE_TACTIC_CHUNK_IDS),
            "reason": "Pressure, scarcity, threat, and demographic-personalization tactics are excluded from this first reviewed slice.",
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


def render_reviewed_first_slice_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-007 Reviewed First Slice",
        "",
        "RAG-007 creates a manually reviewed, paraphrased first knowledge slice. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Selected chunks: `{summary['selected_chunk_count']}`",
        f"- Knowledge items: `{summary['knowledge_item_count']}`",
        f"- Response wording items: `{summary['lane_counts']['response_wording']}`",
        f"- Voice delivery items: `{summary['lane_counts']['voice_delivery']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Retrieval eligible now: `{summary['retrieval_eligible_now']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        f"- Source metadata final: `{summary['source_metadata_final']}`",
        "",
        "## Response wording",
        "",
        "| Knowledge ID | Source Chunk | Rule |",
        "| --- | --- | --- |",
    ]
    for item in payload["knowledge_items"]:
        if item["lane"] != "response_wording":
            continue
        rule = item["project_rule"].replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['source_chunk_ids'][0]}` | {rule} |")

    lines.extend(["", "## Voice delivery", "", "| Knowledge ID | Source Chunk | Rule |", "| --- | --- | --- |"])
    for item in payload["knowledge_items"]:
        if item["lane"] != "voice_delivery":
            continue
        rule = item["project_rule"].replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['source_chunk_ids'][0]}` | {rule} |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- All items are project-owned paraphrases.",
            "- Quote-dependent source text is not copied forward.",
            "- Campaign guardrails, customer refusal, compliance text, and human escalation override every item.",
            "- Tone mismatch is treated as uncertainty that can justify a gentle clarification, not as a certain hidden state.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer inputs are used.",
            "",
        ]
    )
    return "\n".join(lines)
