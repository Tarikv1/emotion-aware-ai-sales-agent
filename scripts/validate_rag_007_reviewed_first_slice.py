#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_reviewed_first_slice.py"
RUNNER = ROOT / "scripts" / "run_rag_007_reviewed_first_slice.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-007-reviewed-first-slice.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_007_REVIEWED_FIRST_SLICE.md"
TMP_DIR = ROOT / ".tmp" / "rag-007-validation"
TMP_RAG006 = TMP_DIR / "rag006-result.json"
TMP_RAG005 = TMP_DIR / "rag005-result.json"
TMP_MANIFEST = TMP_DIR / "rag004-result.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"
EXPECTED_ID = "RAG-007-reviewed-first-slice"
EXPECTED_CHUNK_IDS = {
    "rag005-chunk-017",
    "rag005-chunk-020",
    "rag005-chunk-022",
    "rag005-chunk-024",
    "rag005-chunk-025",
    "rag005-chunk-091",
    "rag005-chunk-098",
    "rag005-chunk-099",
    "rag005-chunk-101",
}
PRESSURE_CHUNK_IDS = {
    "rag005-chunk-071",
    "rag005-chunk-075",
    "rag005-chunk-076",
    "rag005-chunk-077",
    "rag005-chunk-087",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_inputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    source_ids = [
        "rag004-source-086",
        "rag004-source-016",
        "rag004-source-002",
        "rag004-source-013",
        "rag004-source-032",
        "rag004-source-087",
        "rag004-source-063",
        "rag004-source-085",
        "rag004-source-042",
        "rag004-source-075",
    ]
    manifest = {
        "manifest_id": "RAG-004-source-manifest-normalization",
        "source_manifest": {
            "sources": [
                {
                    "source_id": source_id,
                    "canonical_title": f"Reviewed source {source_id}",
                    "metadata_status": "needs_human_review",
                    "rights_status": "needs_review",
                }
                for source_id in source_ids
            ]
        },
    }
    selected_chunks = [
        (
            "rag005-chunk-017",
            "rag004-source-086",
            "response_wording",
            "Plain-language permission check",
            "Ask for permission before continuing and keep the wording short.",
            "Do not use when the prospect has already clearly opted out.",
        ),
        (
            "rag005-chunk-020",
            "rag004-source-016",
            "response_wording",
            "Specific problem reflection",
            "Reflect the prospect's stated problem before introducing a next step.",
            "Do not infer a hidden motive from sparse wording.",
        ),
        (
            "rag005-chunk-022",
            "rag004-source-002",
            "voice_delivery",
            "Warm pacing",
            "Use a measured pace and grounded tone when the buyer sounds guarded.",
            "Do not slow down so much that the call feels theatrical.",
        ),
        (
            "rag005-chunk-024",
            "rag004-source-013",
            "response_wording",
            "Concrete next step",
            "Offer one concrete next step instead of multiple competing choices.",
            "Do not push a meeting when a clarification question is more appropriate.",
        ),
        (
            "rag005-chunk-025",
            "rag004-source-032",
            "voice_delivery",
            "Low-pressure emphasis",
            "Emphasize the useful detail, not the close, when offering help.",
            "Do not use emphasis to make uncertainty sound like certainty.",
        ),
        (
            "rag005-chunk-091",
            "rag004-source-087",
            "response_wording",
            "Objection acknowledgment",
            "Acknowledge the objection before asking one diagnostic follow-up.",
            "Do not debate the objection before understanding it.",
        ),
        (
            "rag005-chunk-098",
            "rag004-source-063",
            "response_wording",
            "Uncertainty and override",
            "Name uncertainty, ask a clarification question, and make override explicit when the signal is ambiguous.",
            "Do not present inferred emotion certainty as fact.",
        ),
        (
            "rag005-chunk-099",
            "rag004-source-085",
            "voice_delivery",
            "Breath before repair",
            "Pause briefly before repairing a misunderstanding.",
            "Do not add a pause that makes the response feel scripted.",
        ),
        (
            "rag005-chunk-101",
            "rag004-source-042",
            "response_wording",
            "Respectful close",
            "Close the loop with a respectful option when the buyer declines.",
            "Do not reopen the pitch after a clear no.",
        ),
    ]
    chunks = [
        {
            "chunk_candidate_id": chunk_id,
            "source_title": f"Reviewed source {source_id}",
            "source_ids": [source_id],
            "topic_ids": [lane],
            "original_topic_id": lane,
            "principle": principle,
            "application": application,
            "when_not_to_use": when_not_to_use,
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_status": "needs_human_review",
            "review_flags": ["quote_review_required"],
        }
        for chunk_id, source_id, lane, principle, application, when_not_to_use in selected_chunks
    ]
    chunks.append(
        {
            "chunk_candidate_id": "rag005-chunk-075",
            "source_title": "Reviewed source rag004-source-075",
            "source_ids": ["rag004-source-075"],
            "topic_ids": ["pressure_tactics"],
            "original_topic_id": "pressure_tactics",
            "principle": "Pressure close",
            "application": "Push past hesitation with urgency.",
            "when_not_to_use": "Do not use in ethical product conversations.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_status": "needs_human_review",
            "review_flags": ["quote_review_required"],
        }
    )
    rag005 = {
        "normalization_id": "RAG-005-chunk-normalization",
        "summary": {
            "chunk_candidate_count": len(chunks),
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
        "chunk_candidates": chunks,
    }
    quote_review_queue = [
        {
            "chunk_id": chunk["chunk_candidate_id"],
            "source_ids": chunk["source_ids"],
            "topic_ids": chunk["topic_ids"],
            "principle": chunk["principle"],
            "application": chunk["application"],
            "when_not_to_use": chunk["when_not_to_use"],
            "source_excerpt_present": True,
            "review_action": "verify_quote_or_replace_with_paraphrase",
        }
        for chunk in chunks
    ]
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "summary": {
            "chunk_candidate_count": len(chunks),
            "source_mapping_queue_count": 0,
            "source_mapping_chunk_count": 0,
            "topic_mapping_queue_count": 0,
            "quote_review_queue_count": len(quote_review_queue),
            "first_slice_candidate_count": 1,
            "auto_promoted_chunk_count": 0,
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
        "review_queues": {
            "source_mapping_queue": [],
            "topic_mapping_queue": [],
            "quote_review_queue": quote_review_queue,
        },
        "first_slice_candidates": [quote_review_queue[0]],
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
        },
    }
    TMP_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    TMP_RAG005.write_text(json.dumps(rag005, indent=2), encoding="utf-8")
    TMP_RAG006.write_text(json.dumps(rag006, indent=2), encoding="utf-8")


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


def _payload_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def validate_reviewed_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    items = payload["knowledge_items"]
    assert_condition(isinstance(items, list), "Reviewed first slice knowledge items must be a list.")
    item_ids = [item["source_chunk_ids"][0] for item in items]
    all_source_chunk_ids = {
        chunk_id
        for item in items
        for chunk_id in item.get("source_chunk_ids", [])
    }
    payload_text = _payload_text(payload)
    combined_text = payload_text + "\n" + report
    report_text = report.lower()

    assert_condition(payload["reviewed_slice_id"] == EXPECTED_ID, payload)
    assert_condition(summary["selected_chunk_count"] == len(EXPECTED_CHUNK_IDS), summary)
    assert_condition(summary["knowledge_item_count"] == len(EXPECTED_CHUNK_IDS), summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["retrieval_eligible_now"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["auto_promoted_chunk_count"] == 0, summary)
    assert_condition(summary["external_provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["private_customer_data_used"] is False, summary)
    assert_condition(boundaries["runtime_retrieval_enabled"] is False, boundaries)
    assert_condition(boundaries["retrieval_eligible_now"] is False, boundaries)
    assert_condition(boundaries["chunk_import_enabled"] is False, boundaries)
    assert_condition(boundaries["auto_promote_allowed"] is False, boundaries)
    assert_condition(boundaries["source_excerpt_text_stored"] is False, boundaries)
    assert_condition(boundaries["provider_calls_allowed"] is False, boundaries)
    assert_condition(boundaries["notebooklm_api_allowed"] is False, boundaries)
    assert_condition(boundaries["private_customer_data_allowed"] is False, boundaries)
    assert_condition(boundaries["reads_data_private"] is False, boundaries)

    assert_condition(item_ids == sorted(EXPECTED_CHUNK_IDS), item_ids)
    assert_condition(set(item_ids) == EXPECTED_CHUNK_IDS, item_ids)
    assert_condition(len(item_ids) == len(set(item_ids)), item_ids)
    assert_condition(all_source_chunk_ids == EXPECTED_CHUNK_IDS, sorted(all_source_chunk_ids))
    assert_condition(not (all_source_chunk_ids & PRESSURE_CHUNK_IDS), sorted(all_source_chunk_ids))
    assert_condition('"source_excerpt_text":' not in combined_text, combined_text)
    assert_condition("quote_review_required" not in combined_text, combined_text)
    assert_condition("data/private" not in combined_text.replace("\\", "/"), combined_text)
    assert_condition("insurance" not in combined_text.lower(), combined_text)

    lanes = {str(item["lane"]) for item in items}
    assert_condition({"response_wording", "voice_delivery"} <= lanes, lanes)
    for item in items:
        assert_condition(len(item["source_chunk_ids"]) == 1, item)
        assert_condition(item.get("runtime_eligible_now") is False, item)
        assert_condition(item.get("retrieval_eligible_now") is False, item)
        assert_condition(item.get("review_verdict") == "manual_first_slice_paraphrased", item)

    chunk_098 = next(item for item in items if item["source_chunk_ids"][0] == "rag005-chunk-098")
    chunk_098_text = json.dumps(chunk_098).lower()
    assert_condition("uncertainty" in chunk_098_text, chunk_098)
    assert_condition("clarification" in chunk_098_text or "clarify" in chunk_098_text, chunk_098)
    assert_condition("override explicit" in chunk_098_text, chunk_098)
    assert_condition("emotion certainty" not in chunk_098_text, chunk_098)
    assert_condition("runtime retrieval remains disabled" in report_text, report)
    assert_condition("response wording" in report_text, report)
    assert_condition("voice delivery" in report_text, report)


def validate_module_contract() -> None:
    assert_condition(MODULE.exists(), "RAG-007 reviewed first slice module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_reviewed_first_slice import (  # noqa: PLC0415
        RAG_REVIEWED_FIRST_SLICE_ID,
        SELECTED_CHUNK_IDS,
        build_reviewed_first_slice,
        render_reviewed_first_slice_report,
    )

    assert_condition(RAG_REVIEWED_FIRST_SLICE_ID == EXPECTED_ID, RAG_REVIEWED_FIRST_SLICE_ID)
    assert_condition(set(SELECTED_CHUNK_IDS) == EXPECTED_CHUNK_IDS, SELECTED_CHUNK_IDS)
    assert_condition(list(SELECTED_CHUNK_IDS) == sorted(EXPECTED_CHUNK_IDS), SELECTED_CHUNK_IDS)
    write_fixture_inputs()
    payload = build_reviewed_first_slice(TMP_RAG006, TMP_RAG005, TMP_MANIFEST, root=ROOT)
    report = render_reviewed_first_slice_report(payload)
    validate_reviewed_payload(payload, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-007 reviewed first slice runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-007 reviewed first slice case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-007 reviewed first slice product doc is missing.")
    write_fixture_inputs()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--rag006-packet",
            str(TMP_RAG006),
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
    assert_condition(RESULT_PATH.exists(), "RAG-007 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-007 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition(len(payload["knowledge_items"]) == len(EXPECTED_CHUNK_IDS), payload)
    assert_condition("rag005-chunk-098" in report, report)
    assert_condition("Runtime retrieval remains disabled" in report, report)
    validate_reviewed_payload(payload, report)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-007 reviewed first slice validation passed.")


if __name__ == "__main__":
    main()
