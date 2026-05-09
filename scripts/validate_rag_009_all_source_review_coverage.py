#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_all_source_review_coverage.py"
RUNNER = ROOT / "scripts" / "run_rag_009_all_source_review_coverage.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-009-all-source-review-coverage.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md"
TMP_DIR = ROOT / ".tmp" / "rag-009-validation"
EXPECTED_ID = "RAG-009-all-source-review-coverage"
EXPECTED_SOURCE_IDS = {
    "rag004-source-001",
    "rag004-source-002",
    "rag004-source-003",
    "rag004-source-004",
}
EXPECTED_CHUNK_IDS = {
    "rag005-chunk-001",
    "rag005-chunk-002",
    "rag005-chunk-003",
    "rag005-chunk-004",
    "rag005-chunk-005",
    "rag005-chunk-006",
}
FIXTURE_REPORT_PATH = (
    "research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge/imports/"
    + "fixture.md"
)


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def chunk(
    chunk_id: str,
    source_title: str,
    source_ids: list[str],
    topic_ids: list[str],
    review_flags: list[str],
    source_excerpt_present: bool,
    principle: str,
    application: str,
    lane: str,
) -> dict[str, Any]:
    return {
        "chunk_candidate_id": chunk_id,
        "stable_key": f"stable-{chunk_id}",
        "source_title": source_title,
        "source_ids": source_ids,
        "source_mapping_status": "mapped" if source_ids else "needs_review",
        "topic_ids": topic_ids,
        "original_topic_id": topic_ids[0] if topic_ids else "",
        "language": "English",
        "sales_stage": "Review",
        "principle": principle,
        "application": application,
        "when_not_to_use": "Do not use when customer refusal, required disclosure, or human escalation applies.",
        "example_phrases": ["not copied into RAG-009 outputs"],
        "emotional_cues": ["review only"],
        "compliance_notes": "Campaign guardrails override this candidate.",
        "evidence_type": lane,
        "confidence": "0.90",
        "citation_note": "fixture",
        "source_excerpt_present": source_excerpt_present,
        "source_excerpt_text_stored": False,
        "report_name": "Fixture report.md",
        "report_path": FIXTURE_REPORT_PATH,
        "review_status": "needs_human_review",
        "review_flags": review_flags,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    source_manifest = {
        "source_manifest_id": "RAG-004-source-manifest-normalization",
        "summary": {
            "source_count": 4,
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "raw_source_text_stored": False,
            "private_customer_data_used": False,
        },
        "source_manifest": {
            "sources": [
                source("rag004-source-001", "Mapped voice source", ["speech_tone_prosody_human_like_voice_behavior"]),
                source("rag004-source-002", "Mapped objection source", ["objection_handling"]),
                source("rag004-source-003", "Mapped compliance-risk source", ["ethical_persuasion_persuasive_dialogue"]),
                source("rag004-source-004", "Unused but accounted source", ["cold_calling"]),
            ]
        },
    }
    chunk_candidates = [
        chunk(
            "rag005-chunk-001",
            "Mapped voice source",
            ["rag004-source-001"],
            ["speech_tone_prosody_human_like_voice_behavior"],
            [],
            False,
            "Bounded vocal clarity",
            "Use delivery cues as advisory metadata.",
            "voice_delivery",
        ),
        chunk(
            "rag005-chunk-002",
            "Mapped objection source",
            ["rag004-source-002"],
            ["objection_handling"],
            ["quote_review_required"],
            True,
            "Objection acknowledgement",
            "Acknowledge normal objections without pressure.",
            "response_wording",
        ),
        chunk(
            "rag005-chunk-003",
            "Unknown source",
            [],
            ["cold_calling"],
            ["source_mapping_required"],
            False,
            "Needs source mapping",
            "Blocked until a source is mapped.",
            "response_wording",
        ),
        chunk(
            "rag005-chunk-004",
            "Mapped objection source",
            ["rag004-source-002"],
            ["off_taxonomy"],
            ["topic_mapping_required"],
            False,
            "Needs topic mapping",
            "Blocked until topic mapping is reviewed.",
            "response_wording",
        ),
        chunk(
            "rag005-chunk-005",
            "Mapped compliance-risk source",
            ["rag004-source-003"],
            ["ethical_persuasion_persuasive_dialogue"],
            [],
            False,
            "False certainty claim",
            "Infer the customer's hidden emotion with certainty.",
            "emotion_detection",
        ),
        chunk(
            "rag005-chunk-006",
            "Mapped compliance-risk source",
            ["rag004-source-003"],
            ["ethical_persuasion_persuasive_dialogue"],
            [],
            False,
            "Pressure tactic",
            "Create urgency to push past hesitation.",
            "response_wording",
        ),
    ]
    rag005 = {
        "chunk_normalization_id": "RAG-005-chunk-normalization",
        "summary": {
            "chunk_candidate_count": len(chunk_candidates),
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
            "private_customer_data_used": False,
        },
        "chunk_candidates": chunk_candidates,
    }
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "summary": {
            "chunk_candidate_count": len(chunk_candidates),
            "auto_promoted_chunk_count": 0,
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
        },
        "review_queues": {
            "source_mapping_queue": [{"source_title": "Unknown source", "chunk_ids": ["rag005-chunk-003"], "chunk_count": 1}],
            "topic_mapping_queue": [{"chunk_id": "rag005-chunk-004"}],
            "quote_review_queue": [{"chunk_id": "rag005-chunk-002", "source_excerpt_present": True}],
        },
        "first_slice_candidates": [{"chunk_id": "rag005-chunk-001"}],
    }
    rag007 = {
        "reviewed_slice_id": "RAG-007-reviewed-first-slice",
        "summary": {
            "knowledge_item_count": 1,
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
        },
        "knowledge_items": [
            {
                "knowledge_id": "rag007-voice-bounded-vocal-toolbox",
                "lane": "voice_delivery",
                "source_chunk_ids": ["rag005-chunk-001"],
                "source_ids": ["rag004-source-001"],
                "review_verdict": "manual_first_slice_paraphrased",
                "quote_dependency_resolved": True,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        ],
    }
    case_config = {
        "review_coverage_id": EXPECTED_ID,
        "title": "All-source RAG review coverage gate fixture",
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
        "max_next_promotion_candidates": 10,
        "reject_patterns": [
            "hidden emotion with certainty",
            "push past hesitation",
        ],
        "review_lanes": [
            "reviewed_rag007",
            "candidate_next_manual_review",
            "blocked_source_mapping",
            "blocked_topic_mapping",
            "blocked_quote_clearance",
            "rejected_safety",
            "deferred_review",
        ],
    }
    paths = {
        "rag004": TMP_DIR / "rag004.json",
        "rag005": TMP_DIR / "rag005.json",
        "rag006": TMP_DIR / "rag006.json",
        "rag007": TMP_DIR / "rag007.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    payloads = {
        "rag004": source_manifest,
        "rag005": rag005,
        "rag006": rag006,
        "rag007": rag007,
        "case": case_config,
    }
    for key, payload in payloads.items():
        paths[key].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return paths


def source(source_id: str, title: str, topic_ids: list[str]) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "canonical_title": title,
        "raw_titles": [title],
        "topic_ids": topic_ids,
        "topic_labels": topic_ids,
        "report_names": ["Fixture report.md"],
        "report_paths": [FIXTURE_REPORT_PATH],
        "source_type_guess": "article_or_video",
        "language_guess": "English",
        "source_type": "needs_review",
        "language": "English",
        "rights_status": "needs_review",
        "metadata_status": "needs_human_review",
        "notebooklm_status": "imported_report_reference",
        "use_status": "candidate",
        "raw_source_text_stored": False,
        "secret_like_detected": False,
    }


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


def validate_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    source_coverage = payload["source_coverage"]
    chunk_coverage = payload["chunk_coverage"]
    chunks_by_id = {item["chunk_id"]: item for item in chunk_coverage}
    sources_by_id = {item["source_id"]: item for item in source_coverage}
    combined_text = json.dumps(payload, sort_keys=True) + "\n" + report

    assert_condition(payload["review_coverage_id"] == EXPECTED_ID, payload)
    assert_condition(summary["source_count"] == 4, summary)
    assert_condition(summary["chunk_candidate_count"] == 6, summary)
    assert_condition(summary["reviewed_rag007_chunk_count"] == 1, summary)
    assert_condition(summary["blocked_source_mapping_count"] == 1, summary)
    assert_condition(summary["blocked_topic_mapping_count"] == 1, summary)
    assert_condition(summary["blocked_quote_clearance_count"] == 1, summary)
    assert_condition(summary["rejected_safety_count"] == 2, summary)
    assert_condition(summary["next_promotion_candidate_count"] == 0, summary)
    assert_condition(summary["all_rag004_sources_accounted_for"] is True, summary)
    assert_condition(summary["all_rag005_chunks_accounted_for"] is True, summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["retrieval_used_in_runtime"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["private_customer_data_used"] is False, summary)
    assert_condition(summary["reads_data_private"] is False, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(boundaries["runtime_retrieval_enabled"] is False, boundaries)
    assert_condition(boundaries["retrieval_used_in_runtime"] is False, boundaries)
    assert_condition(boundaries["chunk_import_enabled"] is False, boundaries)
    assert_condition(boundaries["auto_promote_allowed"] is False, boundaries)
    assert_condition(boundaries["provider_calls_allowed"] is False, boundaries)
    assert_condition(boundaries["notebooklm_api_allowed"] is False, boundaries)
    assert_condition(boundaries["private_customer_data_allowed"] is False, boundaries)
    assert_condition(boundaries["reads_data_private"] is False, boundaries)
    assert_condition(boundaries["source_excerpt_text_stored"] is False, boundaries)

    assert_condition(set(sources_by_id) == EXPECTED_SOURCE_IDS, sorted(sources_by_id))
    assert_condition(set(chunks_by_id) == EXPECTED_CHUNK_IDS, sorted(chunks_by_id))
    assert_condition(len(source_coverage) == len(sources_by_id), source_coverage)
    assert_condition(len(chunk_coverage) == len(chunks_by_id), chunk_coverage)

    assert_condition(chunks_by_id["rag005-chunk-001"]["status"] == "reviewed_rag007", chunks_by_id["rag005-chunk-001"])
    assert_condition(chunks_by_id["rag005-chunk-002"]["status"] == "blocked_quote_clearance", chunks_by_id["rag005-chunk-002"])
    assert_condition(chunks_by_id["rag005-chunk-003"]["status"] == "blocked_source_mapping", chunks_by_id["rag005-chunk-003"])
    assert_condition(chunks_by_id["rag005-chunk-004"]["status"] == "blocked_topic_mapping", chunks_by_id["rag005-chunk-004"])
    assert_condition(chunks_by_id["rag005-chunk-005"]["status"] == "rejected_safety", chunks_by_id["rag005-chunk-005"])
    assert_condition(chunks_by_id["rag005-chunk-006"]["status"] == "rejected_safety", chunks_by_id["rag005-chunk-006"])
    assert_condition(payload["next_promotion_candidates"] == [], payload["next_promotion_candidates"])
    assert_condition(set(payload["promotion_ledger"]) >= {"reviewed_rag007", "blocked_quote_clearance", "blocked_source_mapping", "blocked_topic_mapping", "rejected_safety"}, payload["promotion_ledger"])

    assert_condition('"source_excerpt":' not in combined_text, combined_text)
    assert_condition('"source_excerpt_text":' not in combined_text, combined_text)
    assert_condition("data/private" not in combined_text.replace("\\", "/"), combined_text)
    assert_condition('"runtime_retrieval_enabled": true' not in combined_text.lower(), combined_text)
    assert_condition('"chunk_import_enabled": true' not in combined_text.lower(), combined_text)

    report_text = report.lower()
    assert_condition("all-source review coverage" in report_text, report)
    assert_condition("runtime retrieval remains disabled" in report_text, report)
    assert_condition("blocked review queues" in report_text, report)
    assert_condition("next promotion candidates" in report_text, report)


def validate_module_contract() -> None:
    assert_condition(MODULE.exists(), "RAG-009 all-source review coverage module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_all_source_review_coverage import (  # noqa: PLC0415
        RAG_ALL_SOURCE_REVIEW_COVERAGE_ID,
        build_all_source_review_coverage,
        render_all_source_review_coverage_report,
    )

    assert_condition(RAG_ALL_SOURCE_REVIEW_COVERAGE_ID == EXPECTED_ID, RAG_ALL_SOURCE_REVIEW_COVERAGE_ID)
    paths = write_fixture_inputs()
    payload = build_all_source_review_coverage(paths["rag004"], paths["rag005"], paths["rag006"], paths["rag007"], paths["case"], root=ROOT)
    report = render_all_source_review_coverage_report(payload)
    validate_payload(payload, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-009 all-source review coverage runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-009 all-source review coverage case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-009 all-source review coverage product doc is missing.")
    paths = write_fixture_inputs()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--rag004-result",
            str(paths["rag004"]),
            "--rag005-result",
            str(paths["rag005"]),
            "--rag006-packet",
            str(paths["rag006"]),
            "--rag007-result",
            str(paths["rag007"]),
            "--case",
            str(paths["case"]),
            "--out",
            str(paths["result"]),
            "--report-out",
            str(paths["report"]),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(paths["result"].exists(), "RAG-009 JSON result was not created.")
    assert_condition(paths["report"].exists(), "RAG-009 Markdown report was not created.")
    payload = load_json(paths["result"])
    report = paths["report"].read_text(encoding="utf-8")
    validate_payload(payload, report)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-009 all-source review coverage validation passed.")


if __name__ == "__main__":
    main()
