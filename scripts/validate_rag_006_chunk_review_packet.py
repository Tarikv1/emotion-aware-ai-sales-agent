#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_chunk_review_packet.py"
RUNNER = ROOT / "scripts" / "run_rag_006_chunk_review_packet.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-006-chunk-review-packet.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_006_CHUNK_REVIEW_PACKET.md"
TMP_DIR = ROOT / ".tmp" / "rag-006-validation"
TMP_RAG005 = TMP_DIR / "rag005-result.json"
TMP_MANIFEST = TMP_DIR / "rag004-result.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "RAG-006-chunk-review-packet"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_inputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_id": "RAG-004-source-manifest-normalization",
        "source_manifest": {
            "sources": [
                {
                    "source_id": "rag004-source-001",
                    "canonical_title": "Cognism Hub/Scripts",
                    "raw_titles": ["Cognism Hub/Scripts"],
                    "topic_ids": ["cold_calling"],
                },
                {
                    "source_id": "rag004-source-002",
                    "canonical_title": "How to Speak So That People Want to Listen",
                    "raw_titles": ["Julian Treasure"],
                    "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
                },
            ]
        },
    }
    rag005 = {
        "normalization_id": "RAG-005-chunk-normalization",
        "summary": {
            "chunk_candidate_count": 4,
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
        "chunk_candidates": [
            {
                "chunk_candidate_id": "rag005-chunk-001",
                "source_title": "Cognism Cold Calling Scripts",
                "source_ids": [],
                "topic_ids": ["cold_calling"],
                "original_topic_id": "cold_calling",
                "principle": "Mirroring Pain",
                "application": "Reflect the customer's wording before asking a follow-up.",
                "when_not_to_use": "Do not parrot every phrase.",
                "source_excerpt_present": True,
                "review_status": "needs_human_review",
                "review_flags": ["source_mapping_required", "quote_review_required"],
            },
            {
                "chunk_candidate_id": "rag005-chunk-002",
                "source_title": "Cognism Cold Calling Scripts",
                "source_ids": [],
                "topic_ids": ["cold_calling"],
                "original_topic_id": "cold_calling",
                "principle": "Honesty Anchor",
                "application": "Admit the cold-call context early.",
                "when_not_to_use": "Do not use as fake intimacy.",
                "source_excerpt_present": False,
                "review_status": "needs_human_review",
                "review_flags": ["source_mapping_required"],
            },
            {
                "chunk_candidate_id": "rag005-chunk-003",
                "source_title": "How to Speak So That People Want to Listen",
                "source_ids": ["rag004-source-002"],
                "topic_ids": ["active_listening_human_like_sales_communication"],
                "original_topic_id": "delivery",
                "principle": "Acoustic Triggers",
                "application": "Use vocal delivery to reduce guardedness.",
                "when_not_to_use": "Do not overperform emotion.",
                "source_excerpt_present": False,
                "review_status": "needs_human_review",
                "review_flags": ["topic_mapping_required"],
            },
            {
                "chunk_candidate_id": "rag005-chunk-004",
                "source_title": "How to Speak So That People Want to Listen",
                "source_ids": ["rag004-source-002"],
                "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
                "original_topic_id": "speech_tone_prosody_human_like_voice_behavior",
                "principle": "Vocal Variety",
                "application": "Use measured pace and pitch variation.",
                "when_not_to_use": "Do not change protected campaign text.",
                "source_excerpt_present": False,
                "review_status": "needs_human_review",
                "review_flags": ["human_review_required"],
            },
        ],
    }
    TMP_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    TMP_RAG005.write_text(json.dumps(rag005, indent=2), encoding="utf-8")


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


def validate_module_contract() -> None:
    assert_condition(MODULE.exists(), "RAG-006 chunk review packet module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_chunk_review_packet import (  # noqa: PLC0415
        RAG_CHUNK_REVIEW_PACKET_ID,
        build_review_packet,
        render_review_packet_report,
    )

    assert_condition(RAG_CHUNK_REVIEW_PACKET_ID == EXPECTED_ID, RAG_CHUNK_REVIEW_PACKET_ID)
    write_fixture_inputs()
    payload = build_review_packet(TMP_RAG005, TMP_MANIFEST)
    report = render_review_packet_report(payload)
    summary = payload["summary"]
    queues = payload["review_queues"]

    assert_condition(payload["review_packet_id"] == EXPECTED_ID, payload)
    assert_condition(summary["chunk_candidate_count"] == 4, summary)
    assert_condition(summary["source_mapping_queue_count"] == 1, summary)
    assert_condition(summary["source_mapping_chunk_count"] == 2, summary)
    assert_condition(summary["topic_mapping_queue_count"] == 1, summary)
    assert_condition(summary["quote_review_queue_count"] == 1, summary)
    assert_condition(summary["first_slice_candidate_count"] == 1, summary)
    assert_condition(summary["auto_promoted_chunk_count"] == 0, summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["external_provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)

    source_queue = queues["source_mapping_queue"]
    assert_condition(source_queue[0]["source_title"] == "Cognism Cold Calling Scripts", source_queue)
    assert_condition(source_queue[0]["chunk_ids"] == ["rag005-chunk-001", "rag005-chunk-002"], source_queue)
    assert_condition(source_queue[0]["candidate_source_suggestions"][0]["source_id"] == "rag004-source-001", source_queue)
    assert_condition(queues["topic_mapping_queue"][0]["chunk_id"] == "rag005-chunk-003", queues["topic_mapping_queue"])
    assert_condition(queues["quote_review_queue"][0]["chunk_id"] == "rag005-chunk-001", queues["quote_review_queue"])
    assert_condition(payload["first_slice_candidates"][0]["chunk_id"] == "rag005-chunk-004", payload["first_slice_candidates"])
    payload_text = json.dumps(payload)
    assert_condition("This excerpt should not be carried forward" not in payload_text, payload)
    assert_condition('"source_excerpt_text":' not in payload_text, payload)
    assert_condition("Runtime retrieval remains disabled" in report, report)
    assert_condition("No chunks are promoted" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-006 chunk review packet runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-006 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-006 product doc is missing.")
    write_fixture_inputs()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--rag005-result",
            str(TMP_RAG005),
            "--source-manifest",
            str(TMP_MANIFEST),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-006 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-006 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition(payload["summary"]["source_mapping_queue_count"] == 1, payload["summary"])
    assert_condition("rag005-chunk-004" in report_text, report_text)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-006 chunk review packet validation passed.")


if __name__ == "__main__":
    main()
