#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_knowledge_base.py"
RUNNER = ROOT / "scripts" / "run_rag_001_notebooklm_source_intake.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-001-notebooklm-source-intake-bridge.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_001_NOTEBOOKLM_SOURCE_INTAKE_BRIDGE.md"
TMP_DIR = ROOT / ".tmp" / "rag-001-validation"
RESULT_PATH = TMP_DIR / "RAG-001-result.json"
REPORT_PATH = TMP_DIR / "RAG-001-report.md"

EXPECTED_TOPICS = [
    "cold_calling",
    "closing_techniques",
    "objection_handling",
    "consultative_selling_discovery",
    "emotional_intelligence",
    "active_listening_human_like_sales_communication",
    "negotiation_german_english_sales_calls_telefonakquise",
    "ethical_persuasion_persuasive_dialogue",
    "speech_tone_prosody_human_like_voice_behavior",
    "emotion_recognition_speech_emotion_persuasion_datasets",
]

REQUIRED_CHUNK_FIELDS = [
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
]

SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|sk_car_[A-Za-z0-9_-]{20,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]|ELEVENLABS_API_KEY\s*=\s*[^\s]+",
    re.IGNORECASE,
)


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_secret_text(text: str, label: str) -> None:
    assert_condition(not SECRET_RE.search(text), f"Secret-like value leaked in {label}.")


def validate_module_contract() -> None:
    assert_condition(MODULE.exists(), "RAG-001 knowledge-base module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_knowledge_base import (  # noqa: PLC0415
        build_knowledge_base,
        build_notebooklm_extraction_prompt,
        build_source_manifest_template,
        get_topic_taxonomy,
        validate_notebooklm_chunks,
        validate_source_manifest,
    )

    taxonomy = get_topic_taxonomy()
    topic_ids = [topic["topic_id"] for topic in taxonomy]
    assert_condition(topic_ids == EXPECTED_TOPICS, topic_ids)
    assert_condition(len(taxonomy) == 10, taxonomy)
    assert_condition(any("Telefonakquise" in " ".join(topic.get("aliases", [])) for topic in taxonomy), taxonomy)

    manifest = build_source_manifest_template()
    manifest_report = validate_source_manifest(manifest)
    assert_condition(manifest_report["passed"] is True, manifest_report)
    assert_condition(manifest_report["source_count"] == 10, manifest_report)
    assert_condition(manifest_report["all_topic_slots_present"] is True, manifest_report)
    assert_condition(manifest_report["raw_source_text_stored"] is False, manifest_report)

    prompt = build_notebooklm_extraction_prompt(manifest)
    for topic_id in EXPECTED_TOPICS:
        assert_condition(topic_id in prompt, f"NotebookLM prompt missing topic {topic_id}")
    for field in REQUIRED_CHUNK_FIELDS:
        assert_condition(field in prompt, f"NotebookLM prompt missing schema field {field}")
    assert_condition("Do not copy long passages" in prompt, prompt)
    assert_condition("source_ids" in prompt and "citation_note" in prompt, prompt)

    invalid_manifest = json.loads(json.dumps(manifest))
    invalid_manifest["sources"][0]["topic_ids"] = ["not_a_real_topic"]
    invalid_report = validate_source_manifest(invalid_manifest)
    assert_condition(invalid_report["passed"] is False, invalid_report)
    assert_condition("invalid_topic_id" in {issue["code"] for issue in invalid_report["issues"]}, invalid_report)

    first_source_id = manifest["sources"][2]["source_id"]
    good_chunk = {
        "chunk_id": "rag001-demo-objection-001",
        "topic_ids": ["objection_handling", "ethical_persuasion_persuasive_dialogue"],
        "source_ids": [first_source_id],
        "language": "en",
        "sales_stage": ["relevance-check"],
        "principle": "Acknowledge the concern before proposing a low-risk next step.",
        "application": "Use when a prospect raises a price or effort concern but has not asked to stop.",
        "when_not_to_use": "Do not use after a do-not-call request, legal boundary, medical boundary, or human request.",
        "example_phrases": {
            "en": "That makes sense. No changes needed today; we can simply check whether a short review is useful.",
            "de": "Das verstehe ich. Heute muss nichts geaendert werden; wir pruefen nur kurz, ob ein Blick sinnvoll ist.",
        },
        "emotional_cues": ["skeptical", "price-sensitive"],
        "compliance_notes": "Keep the next step optional and avoid guarantees.",
        "evidence_type": "synthetic_schema_demo",
        "confidence": "medium",
        "citation_note": "Synthetic demo chunk for schema validation only.",
        "source_excerpt": "",
    }
    chunk_report = validate_notebooklm_chunks([good_chunk], manifest)
    assert_condition(chunk_report["passed"] is True, chunk_report)
    assert_condition(chunk_report["chunk_count"] == 1, chunk_report)
    assert_condition(chunk_report["chunks_with_sources"] == 1, chunk_report)

    bad_source_chunk = json.loads(json.dumps(good_chunk))
    bad_source_chunk["source_ids"] = ["missing-source"]
    bad_source_report = validate_notebooklm_chunks([bad_source_chunk], manifest)
    assert_condition(bad_source_report["passed"] is False, bad_source_report)
    assert_condition("unknown_source_id" in {issue["code"] for issue in bad_source_report["issues"]}, bad_source_report)

    long_excerpt_chunk = json.loads(json.dumps(good_chunk))
    long_excerpt_chunk["source_excerpt"] = "word " * 90
    long_excerpt_report = validate_notebooklm_chunks([long_excerpt_chunk], manifest)
    assert_condition(long_excerpt_report["passed"] is False, long_excerpt_report)
    assert_condition("source_excerpt_too_long" in {issue["code"] for issue in long_excerpt_report["issues"]}, long_excerpt_report)

    knowledge_base = build_knowledge_base([good_chunk], manifest)
    assert_condition(knowledge_base["summary"]["chunk_count"] == 1, knowledge_base)
    assert_condition(knowledge_base["summary"]["source_count"] == 10, knowledge_base)
    assert_condition(knowledge_base["source_traceability"]["all_chunks_source_tracked"] is True, knowledge_base)
    assert_condition("objection_handling" in knowledge_base["topic_index"], knowledge_base)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-001 runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-001 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-001 product doc is missing.")

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-001 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-001 Markdown report was not created.")

    payload = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_no_secret_text(json.dumps(payload, ensure_ascii=False) + report_text, "RAG-001 artifacts")

    assert_condition(payload["rag_intake_id"] == "RAG-001-notebooklm-source-intake-bridge", payload)
    summary = payload["summary"]
    assert_condition(summary["topic_count"] == 10, summary)
    assert_condition(summary["source_count"] == 10, summary)
    assert_condition(summary["chunk_count"] >= 2, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["external_provider_calls_made"] is False, summary)
    assert_condition(summary["raw_source_text_stored"] is False, summary)
    assert_condition(summary["customer_private_data_used"] is False, summary)
    assert_condition(summary["validation_passed"] is True, summary)
    assert_condition(summary["all_chunks_source_tracked"] is True, summary)
    assert_condition(summary["all_topics_have_source_slots"] is True, summary)

    prompt = payload["notebooklm_extraction_prompt"]
    assert_condition("NotebookLM is an extraction helper, not permanent product memory" in prompt, prompt)
    assert_condition("JSON array" in prompt and "source_ids" in prompt, prompt)
    assert_condition("youtube.com/watch" not in prompt.lower(), "RAG-001 should not preload unreviewed YouTube links.")

    knowledge_base = payload["knowledge_base"]
    assert_condition(knowledge_base["source_traceability"]["all_chunks_source_tracked"] is True, knowledge_base)
    assert_condition("speech_tone_prosody_human_like_voice_behavior" in knowledge_base["topic_index"], knowledge_base)
    assert_condition("RAG-001" in report_text, report_text)
    assert_condition("NotebookLM" in report_text and "not permanent memory" in report_text, report_text)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-001 NotebookLM source intake validation passed.")


if __name__ == "__main__":
    main()
