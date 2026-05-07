#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_runtime_knowledge_registry.py"
RUNNER = ROOT / "scripts" / "run_rag_017_runtime_knowledge_registry.py"
DOC_PATH = ROOT / "docs" / "product" / "RAG_017_RUNTIME_KNOWLEDGE_REGISTRY.md"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-017-runtime-knowledge-registry" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-017-runtime-knowledge-registry" / "report.md"

EXPECTED_ID = "RAG-017-runtime-knowledge-registry"
EXPECTED_INCLUDED_ARTIFACTS = {
    "RAG-007-reviewed-first-slice",
    "RAG-010-reviewed-expansion-slice",
    "RAG-012-accepted-cleanup",
    "RAG-014-source-mapped-quote-followup",
    "RAG-016A-quote-clearance-decision-slice",
    "RAG-016B-voice-delivery-quote-clearance-decision-slice",
}
BLOCKED_CHUNK_IDS = {"rag005-chunk-001", "rag005-chunk-002", "rag005-chunk-004"}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    items = payload["registry_items"]
    item_ids = {item["registry_id"] for item in items}
    chunk_ids = {chunk_id for item in items for chunk_id in item["source_chunk_ids"]}
    combined_text = json.dumps(payload, sort_keys=True).lower() + "\n" + report.lower()

    assert_condition(payload["runtime_knowledge_registry_id"] == EXPECTED_ID, payload)
    assert_condition(set(payload["included_artifacts"]) == EXPECTED_INCLUDED_ARTIFACTS, payload["included_artifacts"])
    assert_condition(summary["registry_item_count"] == 59, summary)
    assert_condition(summary["voice_delivery_item_count"] >= 25, summary)
    assert_condition(summary["runtime_retrieval_enabled_by_default"] is False, summary)
    assert_condition(summary["retrieval_used_in_runtime"] is False, summary)
    assert_condition(summary["source_mapping_blocker_chunk_count_excluded"] == 58, summary)
    assert_condition(summary["source_mapping_blocker_group_count_excluded"] == 43, summary)
    assert_condition(summary["latent_quote_followup_count_excluded"] == 21, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["private_customer_data_used"] is False, summary)

    assert_condition(boundaries["default_runtime_retrieval_enabled"] is False, boundaries)
    assert_condition(boundaries["requires_explicit_runtime_enablement"] is True, boundaries)
    assert_condition(boundaries["external_vector_db_used"] is False, boundaries)
    assert_condition(boundaries["embedding_provider_used"] is False, boundaries)
    assert_condition(boundaries["private_data_allowed"] is False, boundaries)

    assert_condition("rag007-response-yes-and-objection-framing" in item_ids, "RAG-007 item missing.")
    assert_condition("rag010-response-impact-bridge" in item_ids, "RAG-010 item missing.")
    assert_condition("rag012-guardrail-anti-manipulation" in item_ids, "RAG-012 item missing.")
    assert_condition("rag014-response-consent-based-schedule-confirmation" in item_ids, "RAG-014 item missing.")
    assert_condition("rag016a-response-autonomy-reminder" in item_ids, "RAG-016A item missing.")
    assert_condition("rag016b-voice-no-hidden-emotion-claims" in item_ids, "RAG-016B item missing.")
    assert_condition(not BLOCKED_CHUNK_IDS.intersection(chunk_ids), sorted(BLOCKED_CHUNK_IDS.intersection(chunk_ids)))

    for item in items:
        assert_condition(item["runtime_registry_eligible"] is True, item)
        assert_condition(item["retrieval_scope"] == "advisory_only", item)
        assert_condition(item["retrieval_used_in_runtime"] is False, item)
        assert_condition(item["protected_text_change_allowed"] is False, item)
        assert_condition(item["source_chunk_ids"], item)
        assert_condition(item["source_ids"], item)
        assert_condition(item["citation_trace"], item)
        assert_condition("source_excerpt" not in json.dumps(item).lower(), item)
        if item["lane"] == "voice_delivery":
            assert_condition(item["voice_or_prosody_advisory_only"] is True, item)
            assert_condition(item["hard_limits"]["hidden_emotion_inference_allowed"] is False, item)

    for phrase in ("data/private", '"source_excerpt_text":', "retrieval_used_in_runtime\": true"):
        assert_condition(phrase not in combined_text, phrase)
    assert_condition("opt-in" in combined_text, report)


def main() -> None:
    assert_condition(MODULE.exists(), "RAG-017 module is missing.")
    assert_condition(RUNNER.exists(), "RAG-017 runner is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-017 product doc is missing.")

    completed = run_command([sys.executable, str(RUNNER), "--out", str(RESULT_PATH), "--report-out", str(REPORT_PATH)])
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("RAG-017 runtime knowledge registry validation passed.")


if __name__ == "__main__":
    main()
