from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RAG_QUOTE_CLEARANCE_BATCHES_ID = "RAG-016-quote-clearance-batches"
RAG015_SOURCE_MAPPING_BATCHES_ID = "RAG-015-source-mapping-batches"
RAG013_CLEANUP_STRATEGY_ID = "RAG-013-cleanup-strategy"
RAG012_ACCEPTED_CLEANUP_ID = "RAG-012-accepted-cleanup"
RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
NEXT_CHECKPOINT_ID = "RAG-016A-quote-clearance-decision-slice"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


BATCH_ORDER = {
    "batch_1_ethical_persuasion_response_wording": 1,
    "batch_2_speech_prosody_advisory": 2,
    "batch_3_emotion_recognition_delivery_advisory": 3,
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
        raise ValueError(f"RAG-016 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-016 path is restricted: {path_value}")
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
    rag015_payload: dict[str, Any],
    rag013_payload: dict[str, Any],
    rag012_payload: dict[str, Any],
    rag009_payload: dict[str, Any],
    case_payload: dict[str, Any],
) -> None:
    if rag015_payload.get("source_mapping_batches_id") != RAG015_SOURCE_MAPPING_BATCHES_ID:
        raise ValueError("RAG-016 requires the RAG-015 source-mapping batches artifact.")
    if rag015_payload.get("recommended_next_checkpoint") != RAG_QUOTE_CLEARANCE_BATCHES_ID:
        raise ValueError("RAG-016 requires RAG-015 to recommend quote-clearance batches next.")
    if rag015_payload.get("summary", {}).get("cleanup_decisions_applied_now") != 0:
        raise ValueError("RAG-016 requires RAG-015 to be a no-decision batch packet.")
    if rag015_payload.get("summary", {}).get("source_mapping_blockers_resolved_now") != 0:
        raise ValueError("RAG-016 requires RAG-015 to resolve no source-mapping blockers.")
    if rag013_payload.get("cleanup_strategy_id") != RAG013_CLEANUP_STRATEGY_ID:
        raise ValueError("RAG-016 requires the RAG-013 cleanup strategy artifact.")
    if rag012_payload.get("accepted_cleanup_id") != RAG012_ACCEPTED_CLEANUP_ID:
        raise ValueError("RAG-016 requires the RAG-012 accepted cleanup artifact.")
    if rag009_payload.get("review_coverage_id") != RAG009_ALL_SOURCE_REVIEW_COVERAGE_ID:
        raise ValueError("RAG-016 requires the RAG-009 all-source review coverage artifact.")
    if case_payload.get("quote_clearance_batches_id") != RAG_QUOTE_CLEARANCE_BATCHES_ID:
        raise ValueError("RAG-016 case ID does not match.")
    if case_payload.get("recommended_next_checkpoint") != NEXT_CHECKPOINT_ID:
        raise ValueError("RAG-016 case must recommend the quote-clearance decision slice next.")
    for context, payload in (
        ("RAG-015 input", rag015_payload),
        ("RAG-013 input", rag013_payload),
        ("RAG-012 input", rag012_payload),
        ("RAG-009 input", rag009_payload),
        ("RAG-016 case", case_payload),
    ):
        _runtime_boundaries_are_disabled(payload, context=context)


def _chunk_details_by_id(rag009_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for row in rag009_payload.get("chunk_coverage", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            details[chunk_id] = dict(row)
    return details


def _accepted_quote_ids(rag012_payload: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for row in rag012_payload.get("accepted_quote_clearance_items", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id:
            ids.add(chunk_id)
    return ids


def _topic_ids(row: dict[str, Any], detail: dict[str, Any]) -> list[str]:
    values = row.get("topic_ids", detail.get("topic_ids", []))
    return [str(topic_id) for topic_id in values]


def _source_ids(row: dict[str, Any], detail: dict[str, Any]) -> list[str]:
    values = row.get("source_ids", detail.get("source_ids", []))
    return [str(source_id) for source_id in values]


def _batch_for(topic_ids: list[str], detail: dict[str, Any]) -> tuple[str, str, str, str]:
    joined = " ".join(topic_ids).lower()
    if "speech_tone_prosody" in joined:
        return (
            "batch_2_speech_prosody_advisory",
            "voice_delivery",
            "speech_prosody_advisory",
            "Advisory-only voice/prosody guidance; do not infer hidden emotion, protected traits, consent, refusal, urgency, or buying intent.",
        )
    if "emotion_recognition" in joined or detail.get("voice_or_prosody_advisory_only") is True:
        return (
            "batch_3_emotion_recognition_delivery_advisory",
            "voice_delivery",
            "emotion_recognition_delivery_advisory",
            "Advisory-only signal and dataset guidance; do not treat acoustic or multimodal cues as proof of inner state or purchase intent.",
        )
    return (
        "batch_1_ethical_persuasion_response_wording",
        "ethical_persuasion",
        "low_pressure_response_wording",
        "Rewrite as project-owned, consent-aware, low-pressure sales guidance or reject the candidate.",
    )


def _remaining_quote_rows(rag009_payload: dict[str, Any], accepted_quote_ids: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in rag009_payload.get("review_queues", {}).get("quote_clearance_queue", []):
        chunk_id = str(row.get("chunk_id", "")).strip()
        if chunk_id and chunk_id not in accepted_quote_ids:
            rows.append(dict(row))
    return rows


def build_quote_clearance_cards(
    rag009_payload: dict[str, Any],
    accepted_quote_ids: set[str],
) -> list[dict[str, Any]]:
    details_by_id = _chunk_details_by_id(rag009_payload)
    cards: list[dict[str, Any]] = []
    for row in _remaining_quote_rows(rag009_payload, accepted_quote_ids):
        chunk_id = str(row.get("chunk_id", "")).strip()
        detail = details_by_id.get(chunk_id, {})
        topic_ids = _topic_ids(row, detail)
        batch_id, lane, review_focus, review_guardrail = _batch_for(topic_ids, detail)
        cards.append(
            {
                "chunk_id": chunk_id,
                "priority_batch": batch_id,
                "cleanup_lane": lane,
                "review_focus": review_focus,
                "source_title": str(row.get("source_title", detail.get("source_title", ""))),
                "source_ids": _source_ids(row, detail),
                "topic_ids": topic_ids,
                "status_reasons": [str(reason) for reason in row.get("status_reasons", detail.get("status_reasons", []))],
                "review_action": "create_project_owned_paraphrase_or_reject",
                "review_guardrail": review_guardrail,
                "quote_dependency_present": True,
                "quote_clearance_resolved_now": False,
                "voice_or_prosody_advisory_only": lane == "voice_delivery",
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    cards.sort(
        key=lambda item: (
            BATCH_ORDER[str(item["priority_batch"])],
            str(item["source_title"]).lower(),
            str(item["chunk_id"]),
        )
    )
    return cards


def build_priority_batches(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        grouped[str(card["priority_batch"])].append(card)
    batches: list[dict[str, Any]] = []
    for batch_id in sorted(grouped, key=lambda value: BATCH_ORDER[value]):
        batch_cards = grouped[batch_id]
        source_titles = {str(card["source_title"]) for card in batch_cards}
        batches.append(
            {
                "batch_id": batch_id,
                "cleanup_lane": str(batch_cards[0]["cleanup_lane"]) if batch_cards else "",
                "review_focus": str(batch_cards[0]["review_focus"]) if batch_cards else "",
                "chunk_count": len(batch_cards),
                "source_title_group_count": len(source_titles),
                "objective": _batch_objective(batch_id),
                "cleanup_decisions_applied_now": 0,
                "runtime_retrieval_enabled": False,
            }
        )
    return batches


def _batch_objective(batch_id: str) -> str:
    objectives = {
        "batch_1_ethical_persuasion_response_wording": "Review persuasion and behavioral-science candidates as low-pressure response wording or reject them.",
        "batch_2_speech_prosody_advisory": "Review speaking, tone, cadence, and prosody candidates as advisory-only delivery implications.",
        "batch_3_emotion_recognition_delivery_advisory": "Review emotion-recognition and dataset candidates as limitations-aware delivery guidance only.",
    }
    return objectives[batch_id]


def build_source_title_groups(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        groups[(str(card["priority_batch"]), str(card["source_title"]))].append(card)
    output: list[dict[str, Any]] = []
    for (batch_id, source_title), group_cards in groups.items():
        source_ids = sorted({source_id for card in group_cards for source_id in card.get("source_ids", [])})
        topic_ids = sorted({topic_id for card in group_cards for topic_id in card.get("topic_ids", [])})
        output.append(
            {
                "priority_batch": batch_id,
                "source_title": source_title,
                "chunk_ids": [str(card["chunk_id"]) for card in group_cards],
                "chunk_count": len(group_cards),
                "source_ids": source_ids,
                "topic_ids": topic_ids,
                "review_action": "create_project_owned_paraphrase_or_reject",
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        )
    output.sort(
        key=lambda item: (
            BATCH_ORDER[str(item["priority_batch"])],
            -int(item["chunk_count"]),
            str(item["source_title"]).lower(),
        )
    )
    return output


def build_quote_clearance_batches(
    rag015_result_path: Path | str,
    rag013_result_path: Path | str,
    rag012_result_path: Path | str,
    rag009_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag015_path = resolve_project_path(rag015_result_path, root_path)
    rag013_path = resolve_project_path(rag013_result_path, root_path)
    rag012_path = resolve_project_path(rag012_result_path, root_path)
    rag009_path = resolve_project_path(rag009_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag015_payload = load_json(rag015_path)
    rag013_payload = load_json(rag013_path)
    rag012_payload = load_json(rag012_path)
    rag009_payload = load_json(rag009_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag015_payload, rag013_payload, rag012_payload, rag009_payload, case_payload)

    accepted_quote_ids = _accepted_quote_ids(rag012_payload)
    cards = build_quote_clearance_cards(rag009_payload, accepted_quote_ids)
    expected_quote_count = int(rag013_payload.get("summary", {}).get("remaining_original_quote_clearance_count", len(cards)))
    if len(cards) != expected_quote_count:
        raise ValueError(
            "RAG-016 quote-clearance counts do not match RAG-013 strategy: "
            f"chunks={len(cards)}/{expected_quote_count}"
        )

    lane_counter = Counter(str(card["cleanup_lane"]) for card in cards)
    focus_counter = Counter(str(card["review_focus"]) for card in cards)
    batch_counter = Counter(str(card["priority_batch"]) for card in cards)
    summary = {
        "quote_clearance_chunk_count": len(cards),
        "quote_clearance_batch_count": len(batch_counter),
        "quote_clearance_source_title_group_count": len({str(card["source_title"]) for card in cards}),
        "ethical_persuasion_chunk_count": lane_counter["ethical_persuasion"],
        "voice_delivery_chunk_count": lane_counter["voice_delivery"],
        "speech_prosody_advisory_chunk_count": focus_counter["speech_prosody_advisory"],
        "emotion_recognition_delivery_chunk_count": focus_counter["emotion_recognition_delivery_advisory"],
        "cleanup_decisions_applied_now": 0,
        "quote_clearance_blockers_resolved_now": 0,
        "quote_clearance_blockers_remaining_after_rag016": len(cards),
        "source_mapping_pending_chunk_count_from_rag015": int(
            rag015_payload.get("summary", {}).get("source_mapping_chunk_count", 0)
        ),
        "source_mapping_pending_group_count_from_rag015": int(
            rag015_payload.get("summary", {}).get("source_mapping_group_count", 0)
        ),
        "source_mapping_latent_quote_followup_count_from_rag015": int(
            rag015_payload.get("summary", {}).get("latent_quote_followup_after_source_mapping", 0)
        ),
        "known_unresolved_cleanup_work_after_rag016": int(
            rag015_payload.get("summary", {}).get("source_mapping_chunk_count", 0)
        )
        + len(cards),
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
    expected_lanes = rag013_payload.get("summary", {}).get("quote_clearance_lane_counts", {})
    if expected_lanes:
        for lane, expected_count in expected_lanes.items():
            if int(lane_counter[str(lane)]) != int(expected_count):
                raise ValueError(f"RAG-016 lane count mismatch for {lane}: {lane_counter[str(lane)]}/{expected_count}")

    return {
        "quote_clearance_batches_id": RAG_QUOTE_CLEARANCE_BATCHES_ID,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "inputs": {
            "rag015_result_path": rel_path(rag015_path, root_path),
            "rag013_result_path": rel_path(rag013_path, root_path),
            "rag012_result_path": rel_path(rag012_path, root_path),
            "rag009_result_path": rel_path(rag009_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "summary": summary,
        "priority_batches": build_priority_batches(cards),
        "source_title_groups": build_source_title_groups(cards),
        "quote_clearance_review_cards": cards,
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
            "quote_clearance_decisions_applied": False,
            "runtime_integration_gate_required_before_use": True,
        },
    }


def render_quote_clearance_batches_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-016 Quote-Clearance Batches",
        "",
        "RAG-016 organizes the remaining original quote-clearance review work. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Recommended next checkpoint: `{payload['recommended_next_checkpoint']}`",
        f"- Quote-clearance chunks: `{summary['quote_clearance_chunk_count']}`",
        f"- Quote-clearance batches: `{summary['quote_clearance_batch_count']}`",
        f"- Source-title groups: `{summary['quote_clearance_source_title_group_count']}`",
        f"- Ethical-persuasion chunks: `{summary['ethical_persuasion_chunk_count']}`",
        f"- Voice-delivery chunks: `{summary['voice_delivery_chunk_count']}`",
        f"- Speech/prosody advisory chunks: `{summary['speech_prosody_advisory_chunk_count']}`",
        f"- Emotion-recognition delivery chunks: `{summary['emotion_recognition_delivery_chunk_count']}`",
        f"- Source-mapping chunks still pending from RAG-015: `{summary['source_mapping_pending_chunk_count_from_rag015']}`",
        f"- Source-mapping groups still pending from RAG-015: `{summary['source_mapping_pending_group_count_from_rag015']}`",
        f"- Latent quote follow-ups behind source mapping: `{summary['source_mapping_latent_quote_followup_count_from_rag015']}`",
        f"- Cleanup decisions applied now: `{summary['cleanup_decisions_applied_now']}`",
        f"- Quote-clearance blockers resolved now: `{summary['quote_clearance_blockers_resolved_now']}`",
        f"- Quote-clearance blockers remaining: `{summary['quote_clearance_blockers_remaining_after_rag016']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Priority Batches",
        "",
        "| Batch | Lane | Focus | Chunks | Source groups | Objective |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for batch in payload.get("priority_batches", []):
        objective = str(batch["objective"]).replace("|", "/")
        lines.append(
            f"| `{batch['batch_id']}` | `{batch['cleanup_lane']}` | `{batch['review_focus']}` | "
            f"`{batch['chunk_count']}` | `{batch['source_title_group_count']}` | {objective} |"
        )

    lines.extend(
        [
            "",
            "## Source-Title Groups",
            "",
            "| Batch | Source title | Chunks | Topics |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for group in payload.get("source_title_groups", []):
        title = str(group["source_title"]).replace("|", "/")
        topics = ", ".join(f"`{topic_id}`" for topic_id in group.get("topic_ids", []))
        lines.append(f"| `{group['priority_batch']}` | {title} | `{group['chunk_count']}` | {topics} |")

    lines.extend(
        [
            "",
            "## Review Cards",
            "",
            "| Batch | Chunk ID | Source title | Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for card in payload.get("quote_clearance_review_cards", []):
        title = str(card["source_title"]).replace("|", "/")
        lines.append(f"| `{card['priority_batch']}` | `{card['chunk_id']}` | {title} | `{card['review_action']}` |")

    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- RAG-016 is a batch packet only.",
            "- Human wording review is still required before quote clearance can be accepted.",
            "- Ethical-persuasion items must become low-pressure project-owned guidance or be rejected.",
            "- Voice/prosody and emotion-recognition items are advisory-only.",
            "- Voice-delivery items cannot infer hidden emotion, protected traits, consent, refusal, urgency, or buying intent.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No chunks are auto-promoted.",
            "- No quote-clearance decisions are applied.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data is used.",
            "- No source excerpt text is stored.",
            "- A later runtime integration gate is required before any runtime use.",
            "",
        ]
    )
    return "\n".join(lines)
