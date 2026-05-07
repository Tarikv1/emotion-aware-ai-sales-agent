#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_chunk_normalization.py"
RUNNER = ROOT / "scripts" / "run_rag_005_chunk_normalization.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-005-chunk-normalization.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_005_CHUNK_NORMALIZATION.md"
TMP_DIR = ROOT / ".tmp" / "rag-005-validation"
TMP_IMPORTS = TMP_DIR / "imports"
TMP_MANIFEST = TMP_DIR / "rag004-result.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "RAG-005-chunk-normalization"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_inputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_IMPORTS.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_id": "RAG-004-source-manifest-normalization",
        "source_manifest": {
            "sources": [
                {
                    "source_id": "rag004-source-001",
                    "canonical_title": "30MPC Perfect Script Masterclass",
                    "raw_titles": ["30MPC Perfect Script Masterclass"],
                    "topic_ids": ["cold_calling"],
                },
                {
                    "source_id": "rag004-source-002",
                    "canonical_title": "24 Techniques for Closing the Sale",
                    "raw_titles": ["24 Techniques for Closing the Sale"],
                    "topic_ids": ["closing_techniques"],
                },
            ]
        },
    }
    TMP_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (TMP_IMPORTS / "cold-calling.md").write_text(
        """# Cold calling report

## RAG-Ready Extraction Appendix

{
  "chunk_id": "COLD_001",
  "source_title": "30MPC Perfect Script Masterclass",
  "topic_id": "cold_calling",
  "language": "English",
  "sales_stage": "Opener",
  "principle": "Tailored permission opener",
  "application": "Use after a real trigger was researched.",
  "when_not_to_use": "Do not fabricate context.",
  "example_phrase": "I noticed the role you are hiring for.",
  "emotional_cues": "curious, guarded",
  "compliance_notes": "Use only factual public context.",
  "evidence_type": "youtube transcript",
  "confidence": "High",
  "citation_note": "30MPC transcript",
  "source_excerpt": "This excerpt should not be carried forward."
}

END: COMPLETE
""",
        encoding="utf-8",
    )
    (TMP_IMPORTS / "closing.md").write_text(
        """# Closing report

## RAG-Ready Extraction Appendix

Row,Content
Chunk ID,CHUNK_001
Source Title,24 Techniques for Closing the Sale
Topic ID,closing_techniques
Language,English
Sales Stage,Pre-Closing
Principle,The Approach Close
Application,Ask for a decision process commitment.
When Not To Use,Do not imply purchase commitment.
Example Phrase,Just look and judge for yourself.
Emotional Cues,guarded
Compliance Notes,Keep the next step optional.
Evidence Type,book
Confidence,High
Citation Note,Brian Tracy
Source Excerpt Present,true

END: COMPLETE
""",
        encoding="utf-8",
    )


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
    assert_condition(MODULE.exists(), "RAG-005 chunk normalization module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_chunk_normalization import (  # noqa: PLC0415
        RAG_CHUNK_NORMALIZATION_ID,
        normalize_chunks,
        render_chunk_report,
    )

    assert_condition(RAG_CHUNK_NORMALIZATION_ID == EXPECTED_ID, RAG_CHUNK_NORMALIZATION_ID)
    write_fixture_inputs()
    payload = normalize_chunks(TMP_IMPORTS, TMP_MANIFEST)
    report = render_chunk_report(payload)
    summary = payload["summary"]
    chunks = payload["chunk_candidates"]

    assert_condition(payload["normalization_id"] == EXPECTED_ID, payload)
    assert_condition(summary["report_count"] == 2, summary)
    assert_condition(summary["chunk_candidate_count"] == 2, summary)
    assert_condition(summary["mapped_chunk_count"] == 2, summary)
    assert_condition(summary["chunks_requiring_review_count"] == 2, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["external_provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(all(chunk["review_status"] == "needs_human_review" for chunk in chunks), chunks)
    assert_condition(chunks[0]["source_ids"] == ["rag004-source-001"], chunks[0])
    assert_condition(chunks[0]["source_excerpt_present"] is True, chunks[0])
    assert_condition("source_excerpt" not in chunks[0], chunks[0])
    assert_condition(chunks[1]["source_ids"] == ["rag004-source-002"], chunks[1])
    assert_condition(chunks[1]["source_excerpt_present"] is True, chunks[1])
    assert_condition("RAG-005 Chunk Normalization" in report, report)
    assert_condition("Runtime retrieval remains disabled" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-005 chunk normalization runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-005 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-005 product doc is missing.")
    write_fixture_inputs()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--imports-dir",
            str(TMP_IMPORTS),
            "--source-manifest",
            str(TMP_MANIFEST),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-005 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-005 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition(payload["summary"]["chunk_candidate_count"] == 2, payload["summary"])
    assert_condition(payload["summary"]["mapped_chunk_count"] == 2, payload["summary"])
    assert_condition("rag005-chunk-001" in report_text, report_text)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-005 chunk normalization validation passed.")


if __name__ == "__main__":
    main()
