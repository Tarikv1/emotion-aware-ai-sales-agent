#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_report_import_readiness.py"
RUNNER = ROOT / "scripts" / "run_rag_003_report_import_readiness.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-003-report-import-readiness.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_003_REPORT_IMPORT_READINESS.md"
TMP_DIR = ROOT / ".tmp" / "rag-003-validation"
TMP_IMPORTS = TMP_DIR / "imports"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_AUDIT_ID = "RAG-003-report-import-readiness"
EXPECTED_TOPIC_IDS = [
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


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_imports() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_IMPORTS.mkdir(parents=True, exist_ok=True)
    for index, topic_id in enumerate(EXPECTED_TOPIC_IDS, start=1):
        text = f"""# Emotion Aware AI Sales Agent - {topic_id} Source Extraction Report

## Source Coverage Table

All selected sources for `{topic_id}` were reviewed in this synthetic validator fixture.

## Executive Synthesis

This fixture exists only to test RAG-003 report-import readiness checks.

## RAG-ready extraction appendix

- stable chunk id: fixture-{topic_id}-001
- source title/id: rag001-slot-{index:02d}-{topic_id}
- topic id: {topic_id}
- language: mixed
- sales stage: opening
- principle: Keep sales guidance source-tracked and bounded.
- application: Use only after human review.
- when not to use: Do not use for regulated claims or private data.
- compliance notes: No private data, no provider calls, no raw source text.
- evidence type: synthetic_schema_demo
- confidence: medium
- citation note: Synthetic validator fixture.

END: COMPLETE
"""
        (TMP_IMPORTS / f"{index:02d}-{topic_id}.md").write_text(text, encoding="utf-8")


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
    assert_condition(MODULE.exists(), "RAG-003 report import readiness module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_report_import_readiness import (  # noqa: PLC0415
        RAG_REPORT_IMPORT_READINESS_ID,
        audit_import_directory,
        render_report,
    )

    assert_condition(RAG_REPORT_IMPORT_READINESS_ID == EXPECTED_AUDIT_ID, RAG_REPORT_IMPORT_READINESS_ID)
    write_fixture_imports()
    payload = audit_import_directory(TMP_IMPORTS)
    report = render_report(payload)

    assert_condition(payload["audit_id"] == EXPECTED_AUDIT_ID, payload)
    assert_condition(payload["summary"]["expected_topic_count"] == 10, payload["summary"])
    assert_condition(payload["summary"]["covered_topic_count"] == 10, payload["summary"])
    assert_condition(payload["summary"]["missing_topic_ids"] == [], payload["summary"])
    assert_condition(payload["summary"]["need_continuation_count"] == 0, payload["summary"])
    assert_condition(payload["summary"]["secret_like_report_count"] == 0, payload["summary"])
    assert_condition(payload["summary"]["all_reports_have_complete_marker"] is True, payload["summary"])
    assert_condition(payload["summary"]["all_reports_have_source_coverage"] is True, payload["summary"])
    assert_condition(payload["summary"]["all_reports_have_rag_appendix"] is True, payload["summary"])
    assert_condition(payload["summary"]["runtime_retrieval_enabled"] is False, payload["summary"])
    assert_condition(payload["summary"]["safe_to_auto_promote"] is False, payload["summary"])
    assert_condition("RAG-003 Report Import Readiness" in report, report)
    assert_condition("Runtime retrieval remains disabled" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-003 report import readiness runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-003 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-003 product doc is missing.")
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
    assert_condition(RESULT_PATH.exists(), "RAG-003 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-003 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition(payload["summary"]["covered_topic_count"] == 10, payload["summary"])
    assert_condition(payload["summary"]["source_id_mapping_required"] is False, payload["summary"])
    assert_condition(payload["summary"]["safe_to_auto_promote"] is False, payload["summary"])
    assert_condition("10 / 10" in report, report)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-003 report import readiness validation passed.")


if __name__ == "__main__":
    main()
