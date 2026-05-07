#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_source_mapped_quote_followup.py"
RUNNER = ROOT / "scripts" / "run_rag_014_source_mapped_quote_followup.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-014-source-mapped-quote-followup.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_014_SOURCE_MAPPED_QUOTE_FOLLOWUP.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-014-source-mapped-quote-followup" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-014-source-mapped-quote-followup" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-014-validation"
EXPECTED_ID = "RAG-014-source-mapped-quote-followup"
EXPECTED_RAG013_ID = "RAG-013-cleanup-strategy"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def followup_card(
    chunk_id: str,
    source_title: str,
    source_id: str,
    canonical_title: str,
    topic_id: str,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": source_title,
        "topic_ids": [topic_id],
        "accepted_source_ids": [source_id],
        "accepted_canonical_title": canonical_title,
        "cleanup_lane": "source_mapped_quote_followup",
        "review_action": "create_project_owned_paraphrase_or_reject",
        "reason": "Source mapping is accepted, but quote dependency is still unresolved.",
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
    }


def chunk_detail(
    chunk_id: str,
    source_title: str,
    principle: str,
    application: str,
    when_not_to_use: str,
    topic_id: str,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "status": "blocked_source_mapping",
        "source_title": source_title,
        "source_ids": [],
        "topic_ids": [topic_id],
        "original_topic_id": topic_id,
        "principle": principle,
        "application": application,
        "when_not_to_use": when_not_to_use,
        "quote_dependency_present": True,
        "quoted_text_copied": False,
        "voice_or_prosody_advisory_only": False,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rag013 = {
        "cleanup_strategy_id": EXPECTED_RAG013_ID,
        "recommended_next_checkpoint": EXPECTED_ID,
        "summary": {
            "quote_follow_up_from_accepted_source_mappings": 2,
            "cleanup_decisions_applied_now": 0,
            "auto_promoted_chunk_count": 0,
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
            "provider_calls_made": False,
            "notebooklm_api_used": False,
            "private_customer_data_used": False,
            "reads_data_private": False,
        },
        "source_mapped_quote_followups": [
            followup_card(
                "rag005-chunk-003",
                "Cognism Cold Calling Scripts",
                "rag004-source-028",
                "Cognism Hub/Scripts",
                "cold_calling",
            ),
            followup_card(
                "rag005-chunk-005",
                "Sell Better - Jason Bay",
                "rag004-source-051",
                "Jason Bay (Sell Better)",
                "cold_calling",
            ),
        ],
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "notebooklm_api_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
        },
    }
    rag009 = {
        "review_coverage_id": "RAG-009-all-source-review-coverage",
        "summary": {
            "auto_promoted_chunk_count": 0,
            "runtime_retrieval_enabled": False,
            "retrieval_used_in_runtime": False,
            "chunk_import_enabled": False,
            "provider_calls_made": False,
            "notebooklm_api_used": False,
            "private_customer_data_used": False,
            "reads_data_private": False,
            "source_excerpt_text_stored": False,
        },
        "chunk_coverage": [
            chunk_detail(
                "rag005-chunk-003",
                "Cognism Cold Calling Scripts",
                "Mirroring Pain",
                "Original application that must be rewritten safely.",
                "Original guardrail that must be rewritten safely.",
                "cold_calling",
            ),
            chunk_detail(
                "rag005-chunk-005",
                "Sell Better - Jason Bay",
                "Rep Talk-Time Dominance",
                "Original control-oriented application that must be rejected.",
                "Original guardrail.",
                "cold_calling",
            ),
        ],
    }
    case = {
        "source_mapped_quote_followup_id": EXPECTED_ID,
        "title": "RAG source-mapped quote follow-up",
        "accepted_by": "project_owner_current_session",
        "default_rag013_result": "research/experiments/generated/RAG-013-cleanup-strategy/result.json",
        "default_rag009_result": "research/experiments/generated/RAG-009-all-source-review-coverage/result.json",
        "accepted_followup_chunk_ids": ["rag005-chunk-003"],
        "rejected_followup_chunk_ids": ["rag005-chunk-005"],
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
        "metadata_only": True,
    }
    paths = {
        "rag013": TMP_DIR / "rag013-result.json",
        "rag009": TMP_DIR / "rag009-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag013"].write_text(json.dumps(rag013, indent=2), encoding="utf-8")
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-014 source-mapped quote follow-up module is missing.")
    spec = importlib.util.spec_from_file_location("rag_source_mapped_quote_followup", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-014 module spec.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_no_forbidden_text(payload_text: str) -> None:
    forbidden_terms = [
        '"runtime_retrieval_enabled": true',
        '"chunk_import_enabled": true',
        '"retrieval_used_in_runtime": true',
        '"runtime_use_allowed": true',
        '"runtime_eligible_now": true',
        '"retrieval_eligible_now": true',
        '"auto_promote_allowed": true',
        '"provider_calls_made": true',
        '"notebooklm_api_used": true',
        '"private_customer_data_used": true',
        '"reads_data_private": true',
        '"source_excerpt":',
        '"source_excerpt_text":',
        "data/private",
    ]
    lowered = payload_text.lower()
    for term in forbidden_terms:
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-014 text found: {term}")


def validate_payload(
    payload: dict[str, Any],
    *,
    expected_candidates: int,
    expected_accepted: int,
    expected_rejected: int,
) -> None:
    assert_condition(payload.get("source_mapped_quote_followup_id") == EXPECTED_ID, "Unexpected RAG-014 ID.")
    summary = payload.get("summary", {})
    assert_condition(summary.get("followup_candidate_count") == expected_candidates, summary)
    assert_condition(summary.get("accepted_followup_count") == expected_accepted, summary)
    assert_condition(summary.get("rejected_followup_count") == expected_rejected, summary)
    assert_condition(summary.get("accepted_quote_clearance_item_count") == expected_accepted, summary)
    assert_condition(summary.get("source_mapped_quote_followups_remaining_after_review") == 0, summary)
    assert_condition(summary.get("cleanup_decisions_applied_now") == expected_candidates, summary)
    assert_condition(summary.get("auto_promoted_chunk_count") == 0, summary)
    for key in (
        "runtime_retrieval_enabled",
        "retrieval_eligible_now",
        "chunk_import_enabled",
        "source_excerpt_text_stored",
        "provider_calls_made",
        "notebooklm_api_used",
        "private_customer_data_used",
        "reads_data_private",
    ):
        assert_condition(summary.get(key) is False, {key: summary.get(key)})

    accepted_items = payload.get("accepted_quote_clearance_items", [])
    rejected_items = payload.get("rejected_followup_items", [])
    assert_condition(len(accepted_items) == expected_accepted, accepted_items)
    assert_condition(len(rejected_items) == expected_rejected, rejected_items)

    for item in accepted_items:
        assert_condition(item["review_verdict"] == "manual_source_mapped_quote_clearance_paraphrased", item)
        assert_condition(item["quote_dependency_resolved"] is True, item)
        assert_condition(item["source_mapping_resolved"] is True, item)
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
        assert_condition(item["project_rule"], item)
        assert_condition(item["safe_application"], item)
        assert_condition(item["do_not_use_when"], item)
        assert_condition(item["guardrail_notes"], item)
        assert_condition("source_excerpt" not in item, item)
        assert_condition("source_excerpt_text" not in item, item)

    for item in rejected_items:
        assert_condition(item["review_verdict"].startswith("rejected_"), item)
        assert_condition(item["followup_resolved_by_rejection"] is True, item)
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
        assert_condition(item["rejection_reason"], item)
        assert_condition("source_excerpt" not in item, item)
        assert_condition("source_excerpt_text" not in item, item)

    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(module.RAG_SOURCE_MAPPED_QUOTE_FOLLOWUP_ID == EXPECTED_ID, "Unexpected RAG-014 module ID.")
    assert_condition(hasattr(module, "build_source_mapped_quote_followup"), "Missing builder function.")
    assert_condition(hasattr(module, "render_source_mapped_quote_followup_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_source_mapped_quote_followup(paths["rag013"], paths["rag009"], paths["case"], root=ROOT)
    validate_payload(payload, expected_candidates=2, expected_accepted=1, expected_rejected=1)
    report = module.render_source_mapped_quote_followup_report(payload)
    assert_condition("RAG-014 Source-Mapped Quote Follow-Up" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-014 source-mapped quote follow-up runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-014 source-mapped quote follow-up case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-014 source-mapped quote follow-up product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
        "--rag013-result",
        str(paths["rag013"]),
        "--rag009-result",
        str(paths["rag009"]),
        "--case",
        str(paths["case"]),
        "--out",
        str(paths["result"]),
        "--report-out",
        str(paths["report"]),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    validate_payload(json.loads(paths["result"].read_text(encoding="utf-8")), expected_candidates=2, expected_accepted=1, expected_rejected=1)
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-014 Source-Mapped Quote Follow-Up" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("5 follow-up candidates" in doc_text, "Product doc should record official candidate count.")
    assert_condition("4 accepted project-owned paraphrases" in doc_text, "Product doc should record official acceptance count.")
    assert_condition("1 rejected pressure/control candidate" in doc_text, "Product doc should record official rejection count.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-014 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-014 report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    validate_payload(payload, expected_candidates=5, expected_accepted=4, expected_rejected=1)
    accepted_ids = {item["chunk_id"] for item in payload.get("accepted_quote_clearance_items", [])}
    rejected_ids = {item["chunk_id"] for item in payload.get("rejected_followup_items", [])}
    assert_condition(
        accepted_ids == {"rag005-chunk-003", "rag005-chunk-006", "rag005-chunk-081", "rag005-chunk-084"},
        accepted_ids,
    )
    assert_condition(rejected_ids == {"rag005-chunk-005"}, rejected_ids)
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-014 source-mapped quote follow-up validation passed.")


if __name__ == "__main__":
    main()
