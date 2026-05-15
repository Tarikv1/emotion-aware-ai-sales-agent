#!/usr/bin/env python3
from __future__ import annotations

import json
from copy import deepcopy
from typing import Any


RAG_INTAKE_ID = "RAG-001-notebooklm-source-intake-bridge"

TOPIC_TAXONOMY = [
    {
        "topic_id": "cold_calling",
        "label": "Cold calling",
        "aliases": ["cold calling", "outbound calling", "opening calls"],
        "description": "Opening, permission, relevance framing, and early-call trust for outbound sales.",
    },
    {
        "topic_id": "closing_techniques",
        "label": "Closing techniques",
        "aliases": ["closing", "commitment", "next step"],
        "description": "Low-pressure commitment, appointment setting, and next-step language.",
    },
    {
        "topic_id": "objection_handling",
        "label": "Objection handling",
        "aliases": ["price objection", "timing objection", "status quo", "brushoff"],
        "description": "Safe responses to price, trust, timing, authority, fit, and send-info objections.",
    },
    {
        "topic_id": "consultative_selling_discovery",
        "label": "Consultative selling and discovery",
        "aliases": ["consultative selling", "discovery", "qualification"],
        "description": "Need discovery, qualification, problem framing, and useful follow-up questions.",
    },
    {
        "topic_id": "emotional_intelligence",
        "label": "Emotional intelligence",
        "aliases": ["empathy", "emotional adaptation", "rapport"],
        "description": "Emotion-aware tone, de-escalation, empathy, trust preservation, and boundaries.",
    },
    {
        "topic_id": "active_listening_human_like_sales_communication",
        "label": "Active listening and human-like sales communication",
        "aliases": ["active listening", "human-like communication", "backchannels", "conversation flow"],
        "description": "Listening markers, paraphrasing, conversational flow, acknowledgements, and natural phrasing.",
    },
    {
        "topic_id": "negotiation_german_english_sales_calls_telefonakquise",
        "label": "Negotiation, English/German sales calls, and Telefonakquise",
        "aliases": ["negotiation", "English sales calls", "German sales calls", "Telefonakquise"],
        "description": "Negotiation patterns, bilingual call conventions, and German outbound-call language.",
    },
    {
        "topic_id": "ethical_persuasion_persuasive_dialogue",
        "label": "Persuasion, ethical persuasion, and persuasive dialogue",
        "aliases": ["persuasion", "ethical persuasion", "persuasive dialogue"],
        "description": "Persuasive structure that stays honest, non-coercive, and campaign-safe.",
    },
    {
        "topic_id": "speech_tone_prosody_human_like_voice_behavior",
        "label": "Speech, tone, prosody, and human-like voice behavior",
        "aliases": ["speech", "tone", "prosody", "voice behavior", "human-like voice"],
        "description": "Pacing, emphasis, pause behavior, pitch motion, and voice naturalness.",
    },
    {
        "topic_id": "emotion_recognition_speech_emotion_persuasion_datasets",
        "label": "Emotion recognition, speech emotion datasets, and persuasion datasets",
        "aliases": ["emotion recognition", "speech emotion datasets", "persuasion datasets"],
        "description": "Datasets and evaluation references for emotion, persuasion, and speech behavior.",
    },
]

ALLOWED_TOPIC_IDS = {topic["topic_id"] for topic in TOPIC_TAXONOMY}
ALLOWED_SOURCE_TYPES = {"youtube", "website", "book", "pdf", "paper", "audio", "notebooklm_note", "source_slot"}
ALLOWED_NOTEBOOKLM_STATUS = {"not_added_yet", "added", "extracted", "failed", "notebooklm_not_required"}
ALLOWED_RIGHTS_STATUS = {
    "pending_review",
    "metadata_only",
    "public",
    "licensed",
    "owned",
    "permission_granted",
    "unknown_review_required",
}
FORBIDDEN_RAW_TEXT_KEYS = {
    "raw_text",
    "raw_source_text",
    "full_text",
    "full_source_text",
    "verbatim_transcript",
    "raw_transcript",
    "copied_article",
    "copied_chapter",
}
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "topic_ids",
    "source_type",
    "title",
    "language",
    "rights_status",
    "notebooklm_status",
    "use_status",
}
REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "topic_ids",
    "source_ids",
    "language",
    "sales_stage",
    "principle",
    "application",
    "when_not_to_use",
    "example_phrases",
    "emotional_cues",
    "compliance_notes",
    "evidence_type",
    "confidence",
    "citation_note",
}


def get_topic_taxonomy() -> list[dict[str, Any]]:
    return deepcopy(TOPIC_TAXONOMY)


def source_id_for(topic: dict[str, Any], index: int) -> str:
    return f"rag001-slot-{index:02d}-{topic['topic_id']}"


def build_source_manifest_template() -> dict[str, Any]:
    sources = []
    for index, topic in enumerate(TOPIC_TAXONOMY, start=1):
        sources.append(
            {
                "source_id": source_id_for(topic, index),
                "topic_ids": [topic["topic_id"]],
                "source_type": "source_slot",
                "title": f"{topic['label']} source slot",
                "creator_or_author": "",
                "url": "",
                "isbn_or_publisher_note": "",
                "language": "mixed",
                "rights_status": "pending_review",
                "notebooklm_status": "not_added_yet",
                "use_status": "candidate",
                "notes": "Replace this slot with a real source metadata record before extraction.",
            }
        )
    return {
        "manifest_id": "rag-001-source-manifest-template",
        "rag_intake_id": RAG_INTAKE_ID,
        "version": 1,
        "workflow_role": "NotebookLM extraction helper input, not permanent product memory",
        "source_policy": {
            "store_metadata_only": True,
            "store_raw_source_text": False,
            "allow_private_customer_data": False,
            "allow_unsourced_chunks": False,
            "max_source_excerpt_words": 60,
        },
        "topics": get_topic_taxonomy(),
        "sources": sources,
    }


def make_issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def find_forbidden_raw_text_keys(payload: Any, path: str = "$") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_path = f"{path}.{key}"
            if key in FORBIDDEN_RAW_TEXT_KEYS:
                issues.append(make_issue("raw_source_text_field", next_path, "Raw source text fields are not allowed."))
            issues.extend(find_forbidden_raw_text_keys(value, next_path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            issues.extend(find_forbidden_raw_text_keys(item, f"{path}[{index}]"))
    return issues


def validate_source_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    issues.extend(find_forbidden_raw_text_keys(manifest))

    sources = manifest.get("sources")
    if not isinstance(sources, list):
        sources = []
        issues.append(make_issue("missing_sources", "sources", "Manifest must contain a sources list."))

    seen_source_ids: set[str] = set()
    covered_topics: set[str] = set()
    for index, source in enumerate(sources):
        path = f"sources[{index}]"
        if not isinstance(source, dict):
            issues.append(make_issue("invalid_source_record", path, "Each source must be an object."))
            continue
        missing_fields = sorted(REQUIRED_SOURCE_FIELDS - set(source))
        for field in missing_fields:
            issues.append(make_issue("missing_source_field", f"{path}.{field}", "Required source metadata is missing."))

        source_id = str(source.get("source_id", "")).strip()
        if not source_id:
            issues.append(make_issue("empty_source_id", f"{path}.source_id", "source_id must be non-empty."))
        elif source_id in seen_source_ids:
            issues.append(make_issue("duplicate_source_id", f"{path}.source_id", "source_id must be unique."))
        seen_source_ids.add(source_id)

        source_type = str(source.get("source_type", "")).strip()
        if source_type not in ALLOWED_SOURCE_TYPES:
            issues.append(make_issue("invalid_source_type", f"{path}.source_type", "source_type is not in the allowed set."))

        topic_ids = source.get("topic_ids")
        if not isinstance(topic_ids, list) or not topic_ids:
            issues.append(make_issue("missing_topic_ids", f"{path}.topic_ids", "Each source needs at least one topic_id."))
        else:
            for topic_id in topic_ids:
                if topic_id not in ALLOWED_TOPIC_IDS:
                    issues.append(make_issue("invalid_topic_id", f"{path}.topic_ids", f"Unknown topic_id: {topic_id}"))
                else:
                    covered_topics.add(topic_id)

        if str(source.get("rights_status", "")).strip() not in ALLOWED_RIGHTS_STATUS:
            issues.append(make_issue("invalid_rights_status", f"{path}.rights_status", "rights_status requires review."))
        if str(source.get("notebooklm_status", "")).strip() not in ALLOWED_NOTEBOOKLM_STATUS:
            issues.append(
                make_issue("invalid_notebooklm_status", f"{path}.notebooklm_status", "notebooklm_status is invalid.")
            )
        if source_type != "source_slot" and not (str(source.get("url", "")).strip() or str(source.get("isbn_or_publisher_note", "")).strip()):
            issues.append(make_issue("missing_source_locator", path, "Real sources need a URL, ISBN, or publisher note."))

    topics_without_source_slots = sorted(ALLOWED_TOPIC_IDS - covered_topics)
    all_topic_slots_present = not topics_without_source_slots
    raw_source_text_stored = any(issue["code"] == "raw_source_text_field" for issue in issues)
    passed = not issues and all_topic_slots_present
    return {
        "passed": passed,
        "manifest_id": manifest.get("manifest_id"),
        "source_count": len(sources),
        "topic_count": len(TOPIC_TAXONOMY),
        "covered_topic_count": len(covered_topics),
        "all_topic_slots_present": all_topic_slots_present,
        "topics_without_source_slots": topics_without_source_slots,
        "raw_source_text_stored": raw_source_text_stored,
        "issues": issues,
    }


def build_notebooklm_extraction_prompt(manifest: dict[str, Any]) -> str:
    topics = manifest.get("topics") or get_topic_taxonomy()
    topic_lines = "\n".join(f"- `{topic['topic_id']}`: {topic['label']}" for topic in topics)
    schema = {
        "chunk_id": "stable-id",
        "topic_ids": ["one_or_more_topic_ids"],
        "source_ids": ["source_id_from_manifest"],
        "language": "en|de|mixed",
        "sales_stage": ["opening|relevance-check|objection|qualification|closing|handoff|voice-delivery"],
        "principle": "short paraphrased lesson",
        "application": "when the sales agent should use this",
        "when_not_to_use": "boundaries and unsafe situations",
        "example_phrases": {"en": "short safe phrase", "de": "short safe phrase"},
        "emotional_cues": ["skeptical", "curious"],
        "compliance_notes": "guardrails, claim limits, or escalation notes",
        "evidence_type": "book|website|youtube|dataset|paper|mixed|synthetic_schema_demo",
        "confidence": "low|medium|high",
        "citation_note": "which source and section/video moment supports the paraphrase",
        "source_excerpt": "optional short quote, maximum 60 words, blank preferred",
    }
    return "\n".join(
        [
            "# NotebookLM Extraction Prompt For RAG-001",
            "",
            "NotebookLM is an extraction helper, not permanent product memory.",
            "Use the sources in the current notebook to produce source-tracked, paraphrased RAG chunks for the Emotion Aware AI Sales Agent.",
            "",
            "Do not copy long passages. Do not paste transcripts, book sections, article bodies, or raw source text.",
            "Every chunk must cite one or more `source_ids` from the manifest. If a lesson cannot be source-tracked, omit it.",
            "Prefer practical, reusable sales-agent guidance over motivational quotes.",
            "Flag pressure, deception, unsupported claims, fear tactics, medical/legal/coverage claims, and sensitive-data collection risks.",
            "",
            "Topics:",
            topic_lines,
            "",
            "Return a JSON array. Each object must follow this schema:",
            "",
            "```json",
            json.dumps(schema, indent=2),
            "```",
            "",
            "Quality bar:",
            "- one idea per chunk",
            "- paraphrased principle, not copied text",
            "- clear when-to-use and when-not-to-use",
            "- English and German phrase examples when the source supports both, otherwise use the source language only",
            "- no private customer data",
            "- no claims that the source does not support",
        ]
    )


def word_count(text: str) -> int:
    return len([word for word in str(text).split() if word.strip()])


def validate_notebooklm_chunks(chunks: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    issues.extend(find_forbidden_raw_text_keys(chunks))
    sources_by_id = {source["source_id"]: source for source in manifest.get("sources", []) if isinstance(source, dict) and source.get("source_id")}

    chunks_with_sources = 0
    for index, chunk in enumerate(chunks):
        path = f"chunks[{index}]"
        if not isinstance(chunk, dict):
            issues.append(make_issue("invalid_chunk_record", path, "Each chunk must be an object."))
            continue
        missing_fields = sorted(REQUIRED_CHUNK_FIELDS - set(chunk))
        for field in missing_fields:
            issues.append(make_issue("missing_chunk_field", f"{path}.{field}", "Required chunk field is missing."))

        topic_ids = chunk.get("topic_ids")
        if not isinstance(topic_ids, list) or not topic_ids:
            issues.append(make_issue("missing_chunk_topics", f"{path}.topic_ids", "Chunk needs at least one topic_id."))
        else:
            for topic_id in topic_ids:
                if topic_id not in ALLOWED_TOPIC_IDS:
                    issues.append(make_issue("invalid_chunk_topic_id", f"{path}.topic_ids", f"Unknown topic_id: {topic_id}"))

        source_ids = chunk.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            issues.append(make_issue("missing_chunk_sources", f"{path}.source_ids", "Chunk needs at least one source_id."))
        else:
            known_source_count = 0
            for source_id in source_ids:
                if source_id not in sources_by_id:
                    issues.append(make_issue("unknown_source_id", f"{path}.source_ids", f"Unknown source_id: {source_id}"))
                else:
                    known_source_count += 1
            if known_source_count:
                chunks_with_sources += 1

        source_excerpt = str(chunk.get("source_excerpt", "") or "")
        if word_count(source_excerpt) > int(manifest.get("source_policy", {}).get("max_source_excerpt_words", 60)):
            issues.append(make_issue("source_excerpt_too_long", f"{path}.source_excerpt", "source_excerpt exceeds the maximum word limit."))
        if not isinstance(chunk.get("example_phrases"), dict):
            issues.append(make_issue("invalid_example_phrases", f"{path}.example_phrases", "example_phrases must be an object keyed by language."))
        if str(chunk.get("confidence", "")).strip() not in {"low", "medium", "high"}:
            issues.append(make_issue("invalid_confidence", f"{path}.confidence", "confidence must be low, medium, or high."))

    raw_source_text_stored = any(issue["code"] == "raw_source_text_field" for issue in issues)
    return {
        "passed": not issues,
        "chunk_count": len(chunks),
        "chunks_with_sources": chunks_with_sources,
        "raw_source_text_stored": raw_source_text_stored,
        "issues": issues,
    }


def build_retrieval_text(chunk: dict[str, Any]) -> str:
    phrases = chunk.get("example_phrases", {})
    phrase_text = " ".join(str(value) for value in phrases.values()) if isinstance(phrases, dict) else ""
    parts = [
        chunk.get("principle", ""),
        chunk.get("application", ""),
        chunk.get("when_not_to_use", ""),
        phrase_text,
        chunk.get("compliance_notes", ""),
    ]
    return " ".join(str(part).strip() for part in parts if str(part).strip())


def build_knowledge_base(chunks: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    source_index = {source["source_id"]: deepcopy(source) for source in manifest.get("sources", []) if isinstance(source, dict)}
    chunk_records = []
    topic_index: dict[str, dict[str, Any]] = {
        topic["topic_id"]: {"chunk_ids": [], "source_ids": []} for topic in TOPIC_TAXONOMY
    }
    all_chunks_source_tracked = True
    for chunk in chunks:
        source_ids = list(chunk.get("source_ids", []))
        if not source_ids or any(source_id not in source_index for source_id in source_ids):
            all_chunks_source_tracked = False
        record = deepcopy(chunk)
        record["retrieval_text"] = build_retrieval_text(chunk)
        chunk_records.append(record)
        for topic_id in chunk.get("topic_ids", []):
            if topic_id not in topic_index:
                continue
            topic_index[topic_id]["chunk_ids"].append(chunk.get("chunk_id"))
            for source_id in source_ids:
                if source_id not in topic_index[topic_id]["source_ids"]:
                    topic_index[topic_id]["source_ids"].append(source_id)

    return {
        "knowledge_base_id": "RAG-001-source-tracked-knowledge-base-preview",
        "rag_intake_id": RAG_INTAKE_ID,
        "summary": {
            "topic_count": len(TOPIC_TAXONOMY),
            "source_count": len(source_index),
            "chunk_count": len(chunk_records),
            "embedding_created": False,
            "runtime_retrieval_enabled": False,
        },
        "source_traceability": {
            "all_chunks_source_tracked": all_chunks_source_tracked,
            "source_ids": sorted(source_index),
        },
        "topic_index": topic_index,
        "source_index": source_index,
        "chunks": chunk_records,
    }
