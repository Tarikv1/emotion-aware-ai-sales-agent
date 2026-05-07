#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_sales_communication_source_expansion.py"
RUNNER = ROOT / "scripts" / "run_rag_019_sales_communication_source_expansion.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-019-sales-communication-source-expansion.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_019_SALES_COMMUNICATION_SOURCE_EXPANSION.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-019-sales-communication-source-expansion" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-019-sales-communication-source-expansion" / "report.md"

EXPECTED_ID = "RAG-019-sales-communication-source-expansion"
EXPECTED_SOURCE_COUNT = 25
EXPECTED_ITEM_COUNT = 31
EXPECTED_TOPIC_COUNT = 15
EXPECTED_REQUIRED_IDS = {
    "rag019-cold-call-permission-opener",
    "rag019-objection-price-value-gap",
    "rag019-closing-obtain-commitment-not-hard-close",
    "rag019-spin-consultative-question-flow",
    "rag019-psychology-loss-aversion-ethical-limit",
    "rag019-ei-labeling-with-tentative-language",
    "rag019-negotiation-calibrated-questions",
    "rag019-voice-delivery-clarity-over-performance",
    "rag019-conversation-barge-in-respect",
    "rag019-call-center-escalation-service-recovery",
    "rag019-storytelling-problem-solution-proof",
    "rag019-german-sales-formal-consent-first",
    "rag019-real-call-breakdowns-training-only",
    "rag019-ethics-ai-disclosure-truthful-claims",
}
EXPECTED_TOPIC_GROUPS = {
    "cold_calling",
    "objection_handling",
    "closing_techniques",
    "consultative_selling",
    "sales_psychology",
    "emotional_intelligence_in_sales",
    "negotiation",
    "voice_and_speech_delivery",
    "conversation_design",
    "call_center_communication",
    "persuasion_frameworks",
    "storytelling_for_sales",
    "german_sales_communication",
    "real_sales_call_breakdowns",
    "ethics_and_compliance",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    items = payload["knowledge_items"]
    item_ids = {item["knowledge_id"] for item in items}
    topics = set(payload["covered_requested_topics"])
    combined_text = json.dumps(payload, sort_keys=True).lower() + "\n" + report.lower()

    assert_condition(payload["sales_communication_source_expansion_id"] == EXPECTED_ID, payload)
    assert_condition(summary["source_count"] == EXPECTED_SOURCE_COUNT, summary)
    assert_condition(summary["knowledge_item_count"] == EXPECTED_ITEM_COUNT, summary)
    assert_condition(summary["covered_requested_topic_count"] == EXPECTED_TOPIC_COUNT, summary)
    assert_condition(topics == EXPECTED_TOPIC_GROUPS, topics)
    assert_condition(EXPECTED_REQUIRED_IDS.issubset(item_ids), sorted(EXPECTED_REQUIRED_IDS - item_ids))
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["retrieval_eligible_now"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["copied_scripts_stored"] is False, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["private_customer_data_used"] is False, summary)
    assert_condition(summary["reads_data_private"] is False, summary)
    assert_condition(summary["external_vector_db_used"] is False, summary)
    assert_condition(summary["embedding_provider_used"] is False, summary)

    assert_condition(boundaries["runtime_retrieval_enabled"] is False, boundaries)
    assert_condition(boundaries["auto_promote_allowed"] is False, boundaries)
    assert_condition(boundaries["source_excerpt_text_stored"] is False, boundaries)
    assert_condition(boundaries["copied_scripts_stored"] is False, boundaries)
    assert_condition(boundaries["private_customer_data_allowed"] is False, boundaries)
    assert_condition(boundaries["reads_data_private"] is False, boundaries)

    for source in payload["source_registry"]:
        assert_condition(source["url"].startswith("https://"), source)
        assert_condition(source["reuse_label"] in {"adapted pattern", "inspiration only"}, source)

    for item in items:
        assert_condition(item["source_ids"], item)
        assert_condition(item["source_chunk_ids"], item)
        assert_condition(item["source_urls"], item)
        assert_condition(item["source_titles"], item)
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
        assert_condition(item["manual_review_clearance"]["source_excerpt_text_copied"] is False, item)
        assert_condition(item["manual_review_clearance"]["copied_script_text_stored"] is False, item)
        assert_condition(item["hard_limits"]["hidden_emotion_inference_allowed"] is False, item)
        assert_condition(item["hard_limits"]["protected_trait_inference_allowed"] is False, item)
        assert_condition(item["hard_limits"]["manipulation_allowed"] is False, item)
        assert_condition(item["hard_limits"]["pressure_or_urgency_escalation_allowed"] is False, item)
        assert_condition(item["hard_limits"]["protected_text_change_allowed"] is False, item)

    forbidden = [
        "data/private",
        '"source_excerpt_text":',
        "copied script text",
        "customer is anxious",
        "customer is angry",
        "pressure the customer",
        "fake urgency",
    ]
    for phrase in forbidden:
        assert_condition(phrase not in combined_text.replace("\\", "/"), phrase)
    assert_condition("advisory-only" in combined_text, report)
    assert_condition("ai disclosure" in combined_text, "AI disclosure topic missing.")
    assert_condition("sie language" in combined_text, "German formal language topic missing.")


def main() -> None:
    assert_condition(MODULE.exists(), "RAG-019 module is missing.")
    assert_condition(RUNNER.exists(), "RAG-019 runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-019 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-019 product doc is missing.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("RAG-019 sales communication source expansion validation passed.")


if __name__ == "__main__":
    main()
