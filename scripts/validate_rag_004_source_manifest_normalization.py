#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_source_manifest_normalization.py"
RUNNER = ROOT / "scripts" / "run_rag_004_source_manifest_normalization.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-004-source-manifest-normalization.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_004_SOURCE_MANIFEST_NORMALIZATION.md"
TMP_DIR = ROOT / ".tmp" / "rag-004-validation"
TMP_IMPORTS = TMP_DIR / "imports"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "RAG-004-source-manifest-normalization"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_imports() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_IMPORTS.mkdir(parents=True, exist_ok=True)
    cold_calling = """# Emotion Aware AI Sales Agent - Cold calling Source Extraction Report

## Source Coverage Table

| Source title | Source type | Language | Main contribution | Confidence | Citation note |
| --- | --- | --- | --- | --- | --- |
| 30MPC Cold Call Masterclass | youtube | en | tailored permission opener | high | public video transcript |
| Sales Scripter Cold Calling Training | youtube | en | casual disarming opener | high | public video transcript |

## RAG-ready extraction appendix

- stable chunk id: cold-calling-tailored-permission-001
- source title/id: 30MPC Cold Call Masterclass
- topic id: cold_calling

END: COMPLETE
"""
    objection = """# Emotion Aware AI Sales Agent - Objection Handling Source Extraction Report

## Source Coverage Table

Source Name/ID,Primary Topic,Substantive Contribution,Evidence Density
30MPC Cold Call Masterclass,Objection Handling,agree and incentivize objection handling,High
Cognism Blog Cold Calling Scripts,Objection Handling,mirroring and repetition,High

## RAG-ready extraction appendix

{
  "source_id": "Cognism Blog Cold Calling Scripts",
  "topic_id": "objection_handling",
  "citation_note": "Cognism Blog"
}

END: COMPLETE
"""
    (TMP_IMPORTS / "cold-calling.md").write_text(cold_calling, encoding="utf-8")
    (TMP_IMPORTS / "objection-handling.md").write_text(objection, encoding="utf-8")


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
    assert_condition(MODULE.exists(), "RAG-004 source manifest normalization module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_source_manifest_normalization import (  # noqa: PLC0415
        RAG_SOURCE_MANIFEST_ID,
        build_source_manifest,
        render_manifest_report,
    )

    assert_condition(RAG_SOURCE_MANIFEST_ID == EXPECTED_ID, RAG_SOURCE_MANIFEST_ID)
    write_fixture_imports()
    payload = build_source_manifest(TMP_IMPORTS)
    report = render_manifest_report(payload)
    summary = payload["summary"]
    sources = payload["source_manifest"]["sources"]

    assert_condition(payload["manifest_id"] == EXPECTED_ID, payload)
    assert_condition(summary["report_count"] == 2, summary)
    assert_condition(summary["source_count"] == 3, summary)
    assert_condition(summary["source_id_mapping_review_required"] is True, summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["external_provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["secret_like_source_count"] == 0, summary)
    assert_condition(all(source["source_id"].startswith("rag004-source-") for source in sources), sources)
    assert_condition(all(source["metadata_status"] == "needs_human_review" for source in sources), sources)
    assert_condition(all(source["rights_status"] == "needs_review" for source in sources), sources)
    assert_condition(all(source["raw_source_text_stored"] is False for source in sources), sources)
    assert_condition(
        {source["canonical_title"] for source in sources}
        == {
            "30MPC Cold Call Masterclass",
            "Sales Scripter Cold Calling Training",
            "Cognism Blog Cold Calling Scripts",
        },
        sources,
    )
    assert_condition("cold_calling" in sources[0]["topic_ids"] or "objection_handling" in sources[0]["topic_ids"], sources)
    assert_condition("RAG-004 Source Manifest Normalization" in report, report)
    assert_condition("Runtime retrieval remains disabled" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-004 source manifest normalization runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-004 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-004 product doc is missing.")
    write_fixture_imports()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--imports-dir",
            str(TMP_IMPORTS),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-004 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-004 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition(payload["summary"]["source_count"] == 3, payload["summary"])
    assert_condition(payload["summary"]["source_id_mapping_review_required"] is True, payload["summary"])
    assert_condition("rag004-source-001" in report_text, report_text)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-004 source manifest normalization validation passed.")


if __name__ == "__main__":
    main()
