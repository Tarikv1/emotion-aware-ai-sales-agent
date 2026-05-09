#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_buyer_trust_conversation_repair.py"
RUNNER = ROOT / "scripts" / "run_rag_021_buyer_trust_conversation_repair.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-021-buyer-trust-conversation-repair.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_021_BUYER_TRUST_CONVERSATION_REPAIR.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-021-buyer-trust-conversation-repair" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-021-buyer-trust-conversation-repair" / "report.md"

EXPECTED_ID = "RAG-021-buyer-trust-conversation-repair"
EXPECTED_SOURCE_COUNT = 10
EXPECTED_ITEM_COUNT = 16
EXPECTED_TOPIC_COUNT = 8
EXPECTED_REQUIRED_IDS = {
    "rag021-value-map-before-pitch",
    "rag021-value-basics-before-emotional-value",
    "rag021-trust-diagnose-ability-benevolence-integrity",
    "rag021-trust-repair-admit-limits",
    "rag021-autonomy-supportive-choice-frame",
    "rag021-reactance-control-language-limit",
    "rag021-cognitive-load-one-decision",
    "rag021-plain-language-buyer-summary",
    "rag021-conversation-repair-invite-correction",
    "rag021-emotion-regulation-slow-reframe",
    "rag021-implementation-intention-consented-next-step",
    "rag021-ai-transparency-human-handoff",
}
EXPECTED_TOPIC_GROUPS = {
    "b2b_value_mapping",
    "trust_repair",
    "autonomy_and_reactance",
    "cognitive_load_and_clarity",
    "conversation_repair",
    "emotion_regulation_support",
    "action_commitment_design",
    "ai_transparency_and_handoff",
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
    topics = set(payload["covered_deep_dive_topics"])
    combined_text = json.dumps(payload, sort_keys=True).lower() + "\n" + report.lower()

    assert_condition(payload["buyer_trust_conversation_repair_id"] == EXPECTED_ID, payload)
    assert_condition(summary["source_count"] == EXPECTED_SOURCE_COUNT, summary)
    assert_condition(summary["knowledge_item_count"] == EXPECTED_ITEM_COUNT, summary)
    assert_condition(summary["covered_deep_dive_topic_count"] == EXPECTED_TOPIC_COUNT, summary)
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
    assert_condition(boundaries["runtime_registry_gate_required_before_use"] is True, boundaries)

    for source in payload["source_registry"]:
        assert_condition(source["url"].startswith("https://"), source)
        assert_condition(source["reuse_label"] in {"adapted pattern", "summarized fact", "inspiration only"}, source)
        assert_condition(source["checked_date"] == "2026-05-08", source)

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
        assert_condition(item["hard_limits"]["unvalidated_emotion_classifier_runtime_use_allowed"] is False, item)

    forbidden = [
        "data/private",
        '"source_excerpt_text": true',
        '"source_excerpt":',
        "copied script text",
        "customer is anxious",
        "customer is angry",
        "pressure the customer",
        "fake urgency",
        "hidden emotion inference allowed",
    ]
    normalized_text = combined_text.replace("\\", "/")
    for phrase in forbidden:
        assert_condition(phrase not in normalized_text, phrase)
    assert_condition("advisory-only" in combined_text, report)
    assert_condition("trust repair" in combined_text, report)
    assert_condition("conversation repair" in combined_text, report)
    assert_condition("runtime retrieval enabled: `false`" in combined_text, report)
    assert_condition("registry rebuild" in combined_text, "RAG-021 registry gate missing.")


def main() -> None:
    assert_condition(MODULE.exists(), "RAG-021 module is missing.")
    assert_condition(RUNNER.exists(), "RAG-021 runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-021 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-021 product doc is missing.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("RAG-021 buyer trust conversation repair validation passed.")


if __name__ == "__main__":
    main()
