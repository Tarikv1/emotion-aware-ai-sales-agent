#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_voice_delivery_quote_clearance_decision_slice.py"
RUNNER = ROOT / "scripts" / "run_rag_016b_voice_delivery_decision_slice.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-016b-voice-delivery-decision-slice.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_016B_VOICE_DELIVERY_DECISION_SLICE.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-016B-voice-delivery-decision-slice" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-016B-voice-delivery-decision-slice" / "report.md"

EXPECTED_ID = "RAG-016B-voice-delivery-quote-clearance-decision-slice"
EXPECTED_ACCEPTED_COUNT = 19
EXPECTED_CHUNK_IDS = {
    "rag005-chunk-090",
    "rag005-chunk-092",
    "rag005-chunk-093",
    "rag005-chunk-094",
    "rag005-chunk-096",
    "rag005-chunk-100",
    "rag005-chunk-102",
    "rag005-chunk-103",
    "rag005-chunk-104",
    "rag005-chunk-105",
    "rag005-chunk-106",
    "rag005-chunk-107",
    "rag005-chunk-108",
    "rag005-chunk-109",
    "rag005-chunk-111",
    "rag005-chunk-112",
    "rag005-chunk-113",
    "rag005-chunk-115",
    "rag005-chunk-119",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    items = payload["accepted_quote_clearance_items"]
    combined_text = json.dumps(payload, sort_keys=True).lower() + "\n" + report.lower()

    assert_condition(payload["voice_delivery_decision_slice_id"] == EXPECTED_ID, payload)
    assert_condition(summary["accepted_voice_delivery_item_count"] == EXPECTED_ACCEPTED_COUNT, summary)
    assert_condition(summary["accepted_quote_clearance_item_count"] == EXPECTED_ACCEPTED_COUNT, summary)
    assert_condition(summary["voice_delivery_remaining_after_rag016b"] == 0, summary)
    assert_condition(summary["source_mapping_pending_chunk_count_from_rag015"] == 58, summary)
    assert_condition(summary["source_mapping_pending_group_count_from_rag015"] == 43, summary)
    assert_condition(summary["source_mapping_latent_quote_followup_count_from_rag015"] == 21, summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["retrieval_eligible_now"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["private_customer_data_used"] is False, summary)
    assert_condition(summary["reads_data_private"] is False, summary)

    assert_condition(boundaries["runtime_retrieval_enabled"] is False, boundaries)
    assert_condition(boundaries["retrieval_eligible_now"] is False, boundaries)
    assert_condition(boundaries["source_mapping_blockers_excluded_from_runtime_registry"] is True, boundaries)
    assert_condition(boundaries["latent_quote_followups_excluded_from_runtime_registry"] is True, boundaries)

    item_chunk_ids = {item["chunk_id"] for item in items}
    assert_condition(item_chunk_ids == EXPECTED_CHUNK_IDS, sorted(item_chunk_ids))
    for item in items:
        assert_condition(item["lane"] == "voice_delivery", item)
        assert_condition(item["voice_or_prosody_advisory_only"] is True, item)
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
        assert_condition(item["manual_review_clearance"]["source_excerpt_text_copied"] is False, item)
        assert_condition(item["hard_limits"]["hidden_emotion_inference_allowed"] is False, item)
        assert_condition(item["hard_limits"]["protected_trait_inference_allowed"] is False, item)
        assert_condition(item["hard_limits"]["pressure_or_urgency_escalation_allowed"] is False, item)
        assert_condition(item["hard_limits"]["protected_text_change_allowed"] is False, item)

    forbidden_phrases = [
        "customer is anxious",
        "customer is angry",
        "customer feels",
        "pressure the customer",
        "create urgency",
        "data/private",
    ]
    for phrase in forbidden_phrases:
        assert_condition(phrase not in combined_text, phrase)
    assert_condition('"source_excerpt_text":' not in combined_text, combined_text)
    assert_condition("advisory-only" in combined_text, report)


def main() -> None:
    assert_condition(MODULE.exists(), "RAG-016B module is missing.")
    assert_condition(RUNNER.exists(), "RAG-016B runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-016B case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-016B product doc is missing.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("RAG-016B voice-delivery decision slice validation passed.")


if __name__ == "__main__":
    main()
