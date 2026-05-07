from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


RAG_VOICE_DELIVERY_DECISION_SLICE_ID = "RAG-016B-voice-delivery-quote-clearance-decision-slice"
RAG016A_QUOTE_CLEARANCE_DECISION_SLICE_ID = "RAG-016A-quote-clearance-decision-slice"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))

COMMON_HARD_LIMITS = {
    "hidden_emotion_inference_allowed": False,
    "protected_trait_inference_allowed": False,
    "manipulation_allowed": False,
    "pressure_or_urgency_escalation_allowed": False,
    "protected_text_change_allowed": False,
}

ACCEPTED_RULES_BY_CHUNK_ID: dict[str, dict[str, str]] = {
    "rag005-chunk-090": {
        "knowledge_id": "rag016b-voice-clear-open-close",
        "project_rule": "Make openings and closings clear enough that the customer can follow the turn without extra cognitive load.",
        "safe_application": "Use as delivery guidance for short explanations, summaries, and transitions.",
        "do_not_use_when": "Do not add theatrical framing, long pauses, or extra wording to required scripts.",
        "guardrail_notes": "Clear delivery supports comprehension only; it cannot change campaign text or imply certainty.",
    },
    "rag005-chunk-092": {
        "knowledge_id": "rag016b-voice-calm-accountability",
        "project_rule": "Use calm, accountable delivery when acknowledging an issue or next step.",
        "safe_application": "Use for corrections, handoffs, and short ownership statements that the campaign permits.",
        "do_not_use_when": "Do not imitate a military, motivational, or dominant speaking style.",
        "guardrail_notes": "Delivery must stay professional and non-coercive.",
    },
    "rag005-chunk-093": {
        "knowledge_id": "rag016b-voice-signpost-structure",
        "project_rule": "Use simple vocal signposting so the customer can hear when the agent is moving from context to question or next step.",
        "safe_application": "Use for multi-part answers and short option comparisons.",
        "do_not_use_when": "Do not use signposting to bury limitations, pricing, or disclosure details.",
        "guardrail_notes": "Structure cannot remove mandatory text or human-escalation language.",
    },
    "rag005-chunk-094": {
        "knowledge_id": "rag016b-voice-brand-trust-clarity",
        "project_rule": "Prefer trustworthy, plain delivery over exaggerated warmth or entertainment.",
        "safe_application": "Use as a default voice target for regulated, serious, or unfamiliar sales contexts.",
        "do_not_use_when": "Do not make the agent sound falsely familiar or emotionally intimate.",
        "guardrail_notes": "Brand voice can tune warmth, but trust and clarity stay primary.",
    },
    "rag005-chunk-096": {
        "knowledge_id": "rag016b-voice-pause-for-comprehension",
        "project_rule": "Use brief pauses only where they help the customer process a high-value point.",
        "safe_application": "Use around concise summaries, confirmed next steps, or complex approved facts.",
        "do_not_use_when": "Do not pause to manufacture drama, pressure, or suspense.",
        "guardrail_notes": "Pauses are delivery metadata and never a persuasion loophole.",
    },
    "rag005-chunk-100": {
        "knowledge_id": "rag016b-voice-spontaneous-not-scriptless",
        "project_rule": "Sound natural by varying rhythm lightly while keeping the approved message intact.",
        "safe_application": "Use for freeform but guarded responses that have already passed text validation.",
        "do_not_use_when": "Do not improvise protected scripts, disclosures, prices, or promises.",
        "guardrail_notes": "Naturalness cannot loosen factual or compliance boundaries.",
    },
    "rag005-chunk-102": {
        "knowledge_id": "rag016b-voice-listening-forward",
        "project_rule": "Use delivery that sounds attentive and forward-moving, not performatively sympathetic.",
        "safe_application": "Use when acknowledging a customer concern before asking one useful question.",
        "do_not_use_when": "Do not over-empathize, diagnose feelings, or keep probing after refusal.",
        "guardrail_notes": "Listening cues are weak context only and must follow explicit customer words.",
    },
    "rag005-chunk-103": {
        "knowledge_id": "rag016b-voice-emphasis-sparingly",
        "project_rule": "Emphasize only the smallest number of words needed for comprehension.",
        "safe_application": "Use for one key term in a short answer, callback confirmation, or option comparison.",
        "do_not_use_when": "Do not emphasize savings, risk, scarcity, authority, or urgency beyond approved facts.",
        "guardrail_notes": "Emphasis must improve clarity, not push compliance.",
    },
    "rag005-chunk-104": {
        "knowledge_id": "rag016b-voice-question-shape",
        "project_rule": "Render genuine questions with an open, non-interrogative shape.",
        "safe_application": "Use for discovery, fit checks, and consent checks where the customer can decline.",
        "do_not_use_when": "Do not make questions sound like traps, tests, or forced choices.",
        "guardrail_notes": "Question delivery must preserve customer agency.",
    },
    "rag005-chunk-105": {
        "knowledge_id": "rag016b-voice-concise-turn-taking",
        "project_rule": "Keep delivery concise enough to invite customer turn-taking.",
        "safe_application": "Use when the response should create room for correction, no, or a follow-up question.",
        "do_not_use_when": "Do not use speed or density to prevent interruption or objections.",
        "guardrail_notes": "Turn-taking matters more than monologue control.",
    },
    "rag005-chunk-106": {
        "knowledge_id": "rag016b-voice-no-acoustic-certainty",
        "project_rule": "Treat acoustic signals as uncertain delivery context, not as proof of emotion, truthfulness, or buying intent.",
        "safe_application": "Use to choose slower pace, simpler wording, or a gentle clarification.",
        "do_not_use_when": "Do not infer consent, refusal, urgency, deception, or inner state from audio features.",
        "guardrail_notes": "Explicit customer words and policy decisions override acoustic cues.",
    },
    "rag005-chunk-107": {
        "knowledge_id": "rag016b-voice-no-hidden-emotion-claims",
        "project_rule": "Use multimodal uncertainty only to lower pressure or clarify; never claim to know the customer's internal state.",
        "safe_application": "Use when delivery metadata should become calmer, slower, or more tentative.",
        "do_not_use_when": "Do not label the customer, score their inner state, or personalize pressure from inferred affect.",
        "guardrail_notes": "Emotion-aware behavior must stay observable, tentative, and correctable.",
    },
    "rag005-chunk-108": {
        "knowledge_id": "rag016b-voice-dataset-limits",
        "project_rule": "Treat dataset-derived speech categories as development context, not live customer labels.",
        "safe_application": "Use to remind runtime code that training labels do not authorize live emotion claims.",
        "do_not_use_when": "Do not map a live caller to a dataset class for sales personalization.",
        "guardrail_notes": "Dataset labels never override consent, refusal, or campaign rules.",
    },
    "rag005-chunk-109": {
        "knowledge_id": "rag016b-voice-domain-shift-caution",
        "project_rule": "Assume speech and conversation datasets may not match live sales-call conditions.",
        "safe_application": "Use to keep confidence conservative when audio quality, language, or context differs.",
        "do_not_use_when": "Do not generalize dataset behavior into protected-trait or purchase-intent assumptions.",
        "guardrail_notes": "Domain shift is a reason to ask simpler clarifying questions, not to profile.",
    },
    "rag005-chunk-111": {
        "knowledge_id": "rag016b-voice-observable-only",
        "project_rule": "Respond only to observable words, silence, interruptions, and explicit preferences.",
        "safe_application": "Use when choosing between clarification, handoff, pause, or concise answer.",
        "do_not_use_when": "Do not treat demographic, identity, or accent guesses as personalization inputs.",
        "guardrail_notes": "Customer-stated preferences are valid; inferred identity traits are not.",
    },
    "rag005-chunk-112": {
        "knowledge_id": "rag016b-voice-low-confidence-fallback",
        "project_rule": "When affect or intent confidence is low, fall back to neutral wording and optional human escalation.",
        "safe_application": "Use when signals conflict or the customer may need more room.",
        "do_not_use_when": "Do not compensate for low confidence by becoming more persuasive or urgent.",
        "guardrail_notes": "Low confidence narrows the action set; it does not expand it.",
    },
    "rag005-chunk-113": {
        "knowledge_id": "rag016b-voice-consent-first-adaptation",
        "project_rule": "Adapt delivery from explicit consent, explicit preference, and campaign context before any inferred signal.",
        "safe_application": "Use when the customer asks to slow down, repeat, switch language, or talk to a human.",
        "do_not_use_when": "Do not continue adaptive persuasion after no, stop, or do-not-call language.",
        "guardrail_notes": "Consent and refusal are policy-owned, not style-owned.",
    },
    "rag005-chunk-115": {
        "knowledge_id": "rag016b-voice-prosocial-pressure-limit",
        "project_rule": "Use helpful, prosocial framing only when it preserves the customer's freedom to decline.",
        "safe_application": "Use for optional summaries, education, or handoff suggestions.",
        "do_not_use_when": "Do not convert helpfulness into obligation, guilt, or moral pressure.",
        "guardrail_notes": "Helpfulness must reduce pressure and preserve choice.",
    },
    "rag005-chunk-119": {
        "knowledge_id": "rag016b-voice-cross-modal-humility",
        "project_rule": "Treat cross-modal signals as fallible context for delivery humility.",
        "safe_application": "Use when text and audio appear mismatched and the safest response is a gentle check-in.",
        "do_not_use_when": "Do not infer hidden motives, urgency, or readiness to buy from signal mismatch.",
        "guardrail_notes": "Signal mismatch justifies caution, not certainty.",
    },
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
        raise ValueError(f"RAG-016B path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-016B path is restricted: {path_value}")
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


def validate_inputs(rag016a_payload: dict[str, Any], case_payload: dict[str, Any]) -> None:
    if rag016a_payload.get("quote_clearance_decision_slice_id") != RAG016A_QUOTE_CLEARANCE_DECISION_SLICE_ID:
        raise ValueError("RAG-016B requires the RAG-016A decision slice.")
    if rag016a_payload.get("recommended_next_checkpoint") != RAG_VOICE_DELIVERY_DECISION_SLICE_ID:
        raise ValueError("RAG-016A must recommend RAG-016B as the next checkpoint.")
    if case_payload.get("voice_delivery_decision_slice_id") != RAG_VOICE_DELIVERY_DECISION_SLICE_ID:
        raise ValueError("RAG-016B case ID does not match.")
    _runtime_boundaries_are_disabled(rag016a_payload, context="RAG-016A input")
    _runtime_boundaries_are_disabled(case_payload, context="RAG-016B case")


def _remaining_cards_by_id(rag016a_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    for card in rag016a_payload.get("remaining_quote_clearance_cards", []):
        chunk_id = str(card.get("chunk_id", "")).strip()
        if chunk_id:
            cards[chunk_id] = dict(card)
    return cards


def _id_set(case_payload: dict[str, Any], key: str) -> set[str]:
    return {str(value).strip() for value in case_payload.get(key, []) if str(value).strip()}


def _validate_review_scope(cards_by_id: dict[str, dict[str, Any]], accepted_ids: set[str]) -> None:
    card_ids = set(cards_by_id)
    missing = card_ids.difference(accepted_ids)
    unexpected = accepted_ids.difference(card_ids)
    if missing:
        raise ValueError(f"RAG-016B voice cards missing review decisions: {sorted(missing)}")
    if unexpected:
        raise ValueError(f"RAG-016B review decisions reference unknown chunks: {sorted(unexpected)}")
    if accepted_ids != set(ACCEPTED_RULES_BY_CHUNK_ID):
        raise ValueError("RAG-016B must accept exactly the reviewed voice-delivery candidate set.")


def build_accepted_voice_items(cards_by_id: dict[str, dict[str, Any]], accepted_ids: set[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for chunk_id in sorted(accepted_ids):
        card = cards_by_id[chunk_id]
        rule = ACCEPTED_RULES_BY_CHUNK_ID[chunk_id]
        if str(card.get("cleanup_lane", "")) != "voice_delivery":
            raise ValueError(f"RAG-016B can only accept voice-delivery cards: {chunk_id}")
        items.append(
            {
                "knowledge_id": rule["knowledge_id"],
                "chunk_id": chunk_id,
                "lane": "voice_delivery",
                "source_ids": [str(source_id) for source_id in card.get("source_ids", [])],
                "source_title": str(card.get("source_title", "")),
                "topic_ids": [str(topic_id) for topic_id in card.get("topic_ids", [])],
                "priority_batch": str(card.get("priority_batch", "")),
                "review_focus": str(card.get("review_focus", "")),
                "review_verdict": "manual_voice_delivery_quote_clearance_paraphrased",
                "quote_dependency_resolved": True,
                "human_acceptance_recorded": True,
                "project_rule": rule["project_rule"],
                "safe_application": rule["safe_application"],
                "do_not_use_when": rule["do_not_use_when"],
                "guardrail_notes": rule["guardrail_notes"],
                "voice_or_prosody_advisory_only": True,
                "hard_limits": dict(COMMON_HARD_LIMITS),
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
                "manual_review_clearance": {
                    "quote_clearance_resolution": "project_owned_voice_delivery_paraphrase_accepted",
                    "source_excerpt_text_copied": False,
                    "runtime_use_allowed": False,
                },
            }
        )
    return items


def build_voice_delivery_decision_slice(
    rag016a_result_path: Path | str,
    case_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag016a_path = resolve_project_path(rag016a_result_path, root_path)
    case_config_path = resolve_project_path(case_path, root_path)
    rag016a_payload = load_json(rag016a_path)
    case_payload = load_json(case_config_path)
    validate_inputs(rag016a_payload, case_payload)

    cards_by_id = _remaining_cards_by_id(rag016a_payload)
    accepted_ids = _id_set(case_payload, "accepted_quote_clearance_chunk_ids")
    _validate_review_scope(cards_by_id, accepted_ids)
    accepted_items = build_accepted_voice_items(cards_by_id, accepted_ids)
    priority_counts = Counter(item["priority_batch"] for item in accepted_items)
    source_pending_count = int(rag016a_payload.get("summary", {}).get("source_mapping_pending_chunk_count_from_rag015", 0))
    source_pending_group_count = int(rag016a_payload.get("summary", {}).get("source_mapping_pending_group_count_from_rag015", 0))
    latent_followup_count = int(rag016a_payload.get("summary", {}).get("source_mapping_latent_quote_followup_count_from_rag015", 0))
    summary = {
        "accepted_quote_clearance_item_count": len(accepted_items),
        "accepted_voice_delivery_item_count": len(accepted_items),
        "speech_prosody_advisory_item_count": priority_counts["batch_2_speech_prosody_advisory"],
        "emotion_recognition_delivery_advisory_item_count": priority_counts["batch_3_emotion_recognition_delivery_advisory"],
        "voice_delivery_remaining_after_rag016b": 0,
        "quote_clearance_blockers_remaining_after_rag016b": 0,
        "source_mapping_pending_chunk_count_from_rag015": source_pending_count,
        "source_mapping_pending_group_count_from_rag015": source_pending_group_count,
        "source_mapping_latent_quote_followup_count_from_rag015": latent_followup_count,
        "known_unresolved_cleanup_work_after_rag016b": source_pending_count,
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
        "voice_delivery_decision_slice_id": RAG_VOICE_DELIVERY_DECISION_SLICE_ID,
        "inputs": {
            "rag016a_result_path": rel_path(rag016a_path, root_path),
            "case_path": rel_path(case_config_path, root_path),
        },
        "acceptance": {
            "accepted_by": str(case_payload.get("accepted_by", "project_owner_current_session")),
            "acceptance_scope": "Remaining RAG-016A voice-delivery quote-clearance cards.",
            "prior_artifacts_mutated": False,
        },
        "summary": summary,
        "accepted_quote_clearance_items": accepted_items,
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
            "source_mapping_blockers_excluded_from_runtime_registry": True,
            "latent_quote_followups_excluded_from_runtime_registry": True,
            "runtime_registry_gate_required_before_use": True,
        },
    }


def render_voice_delivery_decision_slice_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-016B Voice-Delivery Decision Slice",
        "",
        "RAG-016B accepts the remaining voice/prosody candidates as project-owned advisory-only delivery rules. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Accepted voice-delivery items: `{summary['accepted_voice_delivery_item_count']}`",
        f"- Speech/prosody advisory items: `{summary['speech_prosody_advisory_item_count']}`",
        f"- Emotion-recognition delivery advisory items: `{summary['emotion_recognition_delivery_advisory_item_count']}`",
        f"- Voice-delivery remaining: `{summary['voice_delivery_remaining_after_rag016b']}`",
        f"- Source-mapping chunks still excluded: `{summary['source_mapping_pending_chunk_count_from_rag015']}`",
        f"- Source-mapping groups still excluded: `{summary['source_mapping_pending_group_count_from_rag015']}`",
        f"- Latent quote follow-ups still excluded: `{summary['source_mapping_latent_quote_followup_count_from_rag015']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        "",
        "## Accepted Advisory Rules",
        "",
        "| Knowledge ID | Chunk ID | Rule |",
        "| --- | --- | --- |",
    ]
    for item in payload.get("accepted_quote_clearance_items", []):
        rule = str(item["project_rule"]).replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['chunk_id']}` | {rule} |")

    lines.extend(
        [
            "",
            "## Hard Limits",
            "",
            "- Advisory-only voice and prosody guidance.",
            "- No hidden emotion inference.",
            "- No protected-class or identity profiling.",
            "- No manipulation, pressure, or urgency escalation.",
            "- No changes to protected campaign, disclosure, refusal, or handoff text.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled until RAG-017/RAG-018 opt-in runtime integration.",
            "- The unresolved RAG-015 source-mapping blockers and latent quote follow-ups stay excluded.",
            "- No source excerpt text, private customer data, provider calls, or NotebookLM API calls are used.",
            "",
        ]
    )
    return "\n".join(lines)
