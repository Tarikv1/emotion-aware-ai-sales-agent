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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODULE = ROOT / "scripts" / "rag_notebooklm_automation.py"
RUNNER = ROOT / "scripts" / "run_rag_002_notebooklm_extraction_automation.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-002-notebooklm-extraction-automation-bridge.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_002_NOTEBOOKLM_EXTRACTION_AUTOMATION_BRIDGE.md"
TMP_DIR = ROOT / ".tmp" / "rag-002-validation"
RESULT_PATH = TMP_DIR / "RAG-002-result.json"
REPORT_PATH = TMP_DIR / "RAG-002-report.md"

EXPECTED_AUTOMATION_ID = "RAG-002-notebooklm-extraction-automation-bridge"
EXPECTED_TOPIC_COUNT = 10
EXPECTED_PROMPTS_PER_TOPIC = 3
DEFAULT_PROMPT_CHAR_LIMIT = 4500
DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT = 10000

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
    assert_condition(MODULE.exists(), "RAG-002 NotebookLM automation module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from runtime.retrieval.knowledge_base import build_source_manifest_template  # noqa: PLC0415
    from rag_notebooklm_automation import (  # noqa: PLC0415
        RAG_AUTOMATION_ID,
        build_notebooklm_prompt_pack,
        validate_extraction_output,
        validate_prompt_pack,
    )

    assert_condition(RAG_AUTOMATION_ID == EXPECTED_AUTOMATION_ID, RAG_AUTOMATION_ID)

    manifest = build_source_manifest_template()
    prompt_pack = build_notebooklm_prompt_pack(manifest, prompt_char_limit=DEFAULT_PROMPT_CHAR_LIMIT)
    prompt_report = validate_prompt_pack(prompt_pack)

    assert_condition(prompt_report["passed"] is True, prompt_report)
    assert_condition(prompt_report["topic_count"] == EXPECTED_TOPIC_COUNT, prompt_report)
    assert_condition(prompt_report["prompt_count"] == EXPECTED_TOPIC_COUNT * EXPECTED_PROMPTS_PER_TOPIC, prompt_report)
    assert_condition(prompt_report["prompt_char_limit"] == DEFAULT_PROMPT_CHAR_LIMIT, prompt_report)
    assert_condition(prompt_report["chat_customization_char_limit"] == DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT, prompt_report)
    assert_condition(prompt_report["chat_customization_within_limit"] is True, prompt_report)
    assert_condition(prompt_report["all_topics_have_report_artifact_prompt"] is True, prompt_report)
    assert_condition(prompt_report["report_artifact_workflow_enabled"] is True, prompt_report)
    assert_condition(prompt_report["primary_prompts_include_readable_report"] is True, prompt_report)
    assert_condition(prompt_report["primary_prompts_include_json_block"] is True, prompt_report)
    assert_condition(prompt_report["all_prompts_within_limit"] is True, prompt_report)
    assert_condition(prompt_report["all_prompts_have_completion_marker"] is True, prompt_report)
    assert_condition(prompt_report["all_primary_prompts_are_exhaustive"] is True, prompt_report)
    assert_condition(prompt_report["manual_notebooklm_ui_required"] is True, prompt_report)
    assert_condition(prompt_report["notebooklm_api_used"] is False, prompt_report)

    chat_customization = prompt_pack["chat_customization"]
    assert_condition(len(chat_customization["text"]) <= DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT, chat_customization)
    assert_condition("Choose response length: Longer" in chat_customization["text"], chat_customization["text"])
    assert_condition("Do not collapse the tailored report into short JSON strings" in chat_customization["text"], chat_customization["text"])

    for topic_prompt in prompt_pack["topics"]:
        topic_id = topic_prompt["topic_id"]
        report_artifact = topic_prompt["prompts"]["report_artifact"]
        primary = topic_prompt["prompts"]["primary_report"]
        gap_check = topic_prompt["prompts"]["gap_check"]
        assert_condition(len(report_artifact["text"]) <= DEFAULT_PROMPT_CHAR_LIMIT, (topic_id, len(report_artifact["text"])))
        assert_condition(len(primary["text"]) <= DEFAULT_PROMPT_CHAR_LIMIT, (topic_id, len(primary["text"])))
        assert_condition(len(gap_check["text"]) <= DEFAULT_PROMPT_CHAR_LIMIT, (topic_id, len(gap_check["text"])))
        assert_condition("Create a NotebookLM report file" in report_artifact["text"], report_artifact["text"])
        assert_condition("Do not answer only in chat" in report_artifact["text"], report_artifact["text"])
        assert_condition("Export or copy the completed report file" in report_artifact["text"], report_artifact["text"])
        assert_condition("RAG-ready extraction appendix" in report_artifact["text"], report_artifact["text"])
        assert_condition("Do not give me a small sample batch" in primary["text"], primary["text"])
        assert_condition("END: COMPLETE" in primary["text"], primary["text"])
        assert_condition("NEED_CONTINUATION" in primary["text"], primary["text"])
        assert_condition("coverage_checklist" in primary["text"], primary["text"])
        assert_condition("PART A - TAILORED REPORT" in primary["text"], primary["text"])
        assert_condition("PART B - RAG JSON" in primary["text"], primary["text"])
        assert_condition("Return exactly one JSON object" not in primary["text"], primary["text"])
        assert_condition(topic_id in primary["text"], primary["text"])
        assert_condition(topic_id in gap_check["text"], gap_check["text"])
        assert_condition("find missing distinct items" in gap_check["text"], gap_check["text"])

    known_source_id = manifest["sources"][2]["source_id"]
    complete_output = {
        "topic_id": "objection_handling",
        "completion_status": "complete",
        "coverage_checklist": {
            "all_selected_sources_reviewed": True,
            "small_sample_batch": False,
            "no_more_distinct_items_found": True,
            "end_marker": "END: COMPLETE",
        },
        "chunks": [
            {
                "chunk_id": f"rag002-demo-objection-{index:03d}",
                "topic_ids": ["objection_handling"],
                "source_ids": [known_source_id],
                "language": "en",
                "sales_stage": ["objection"],
                "principle": f"Acknowledge objection pattern {index} before offering a low-pressure next step.",
                "application": "Use only when the prospect has not refused, asked to stop, or requested a human.",
                "when_not_to_use": "Do not use after a do-not-call request or when regulated advice is needed.",
                "example_phrases": {
                    "en": "That makes sense; we can simply check whether a short review is useful.",
                    "de": "Das verstehe ich; wir pruefen nur kurz, ob ein Blick sinnvoll ist.",
                },
                "emotional_cues": ["skeptical"],
                "compliance_notes": "Keep the next step optional and avoid guarantees.",
                "evidence_type": "synthetic_schema_demo",
                "confidence": "medium",
                "citation_note": "Synthetic RAG-002 validator example; replace with NotebookLM citations.",
                "source_excerpt": "",
            }
            for index in range(1, 9)
        ],
    }
    complete_report = validate_extraction_output(
        complete_output,
        manifest,
        topic_id="objection_handling",
        min_chunks_per_topic=8,
    )
    assert_condition(complete_report["passed"] is True, complete_report)
    assert_condition(complete_report["coverage_complete"] is True, complete_report)
    assert_condition(complete_report["small_sample_batch_detected"] is False, complete_report)

    tiny_output = json.loads(json.dumps(complete_output))
    tiny_output["chunks"] = tiny_output["chunks"][:2]
    tiny_report = validate_extraction_output(
        tiny_output,
        manifest,
        topic_id="objection_handling",
        min_chunks_per_topic=8,
    )
    assert_condition(tiny_report["passed"] is False, tiny_report)
    assert_condition("too_few_chunks_for_topic" in {issue["code"] for issue in tiny_report["issues"]}, tiny_report)

    incomplete_output = json.loads(json.dumps(complete_output))
    incomplete_output["completion_status"] = "partial"
    incomplete_output["coverage_checklist"]["end_marker"] = "NEED_CONTINUATION"
    incomplete_report = validate_extraction_output(
        incomplete_output,
        manifest,
        topic_id="objection_handling",
        min_chunks_per_topic=8,
    )
    assert_condition(incomplete_report["passed"] is False, incomplete_report)
    assert_condition("completion_status_not_complete" in {issue["code"] for issue in incomplete_report["issues"]}, incomplete_report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-002 runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-002 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-002 product doc is missing.")

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
            "--prompt-dir",
            str(TMP_DIR / "prompts"),
            "--import-dir",
            str(TMP_DIR / "imports"),
            "--prompt-char-limit",
            str(DEFAULT_PROMPT_CHAR_LIMIT),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-002 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-002 Markdown report was not created.")

    payload = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_no_secret_text(json.dumps(payload, ensure_ascii=False) + report_text, "RAG-002 artifacts")

    summary = payload["summary"]
    assert_condition(payload["rag_automation_id"] == EXPECTED_AUTOMATION_ID, payload)
    assert_condition(summary["topic_count"] == EXPECTED_TOPIC_COUNT, summary)
    assert_condition(summary["prompt_count"] == EXPECTED_TOPIC_COUNT * EXPECTED_PROMPTS_PER_TOPIC, summary)
    assert_condition(summary["prompt_char_limit"] == DEFAULT_PROMPT_CHAR_LIMIT, summary)
    assert_condition(summary["chat_customization_char_limit"] == DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT, summary)
    assert_condition(summary["chat_customization_within_limit"] is True, summary)
    assert_condition(summary["report_artifact_workflow_enabled"] is True, summary)
    assert_condition(summary["primary_prompts_include_readable_report"] is True, summary)
    assert_condition(summary["primary_prompts_include_json_block"] is True, summary)
    assert_condition(summary["all_prompts_within_limit"] is True, summary)
    assert_condition(summary["completion_gate_enabled"] is True, summary)
    assert_condition(summary["small_batch_rejection_enabled"] is True, summary)
    assert_condition(summary["manual_notebooklm_ui_required"] is True, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["external_provider_calls_made"] is False, summary)
    assert_condition(summary["raw_source_text_stored"] is False, summary)
    assert_condition(summary["customer_private_data_used"] is False, summary)
    assert_condition(summary["validation_passed"] is True, summary)

    prompt_pack = payload["prompt_pack"]
    assert_condition(len(prompt_pack["topics"]) == EXPECTED_TOPIC_COUNT, prompt_pack)
    assert_condition("objection_handling" in {topic["topic_id"] for topic in prompt_pack["topics"]}, prompt_pack)
    assert_condition("RAG-002" in report_text and "small sample batch" in report_text, report_text)
    assert_condition((TMP_DIR / "prompts" / "00-configure-chat-custom-instructions.md").exists(), "Configure Chat instructions were not written.")
    assert_condition((TMP_DIR / "prompts" / "01-cold-calling" / "01-create-report-file.md").exists(), "Report-file prompt was not written.")


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-002 NotebookLM extraction automation validation passed.")


if __name__ == "__main__":
    main()
