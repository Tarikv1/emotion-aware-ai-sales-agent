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
MODULE = ROOT / "scripts" / "rag_accepted_cleanup.py"
RUNNER = ROOT / "scripts" / "run_rag_012_accepted_cleanup.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-012-accepted-cleanup.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_012_ACCEPTED_CLEANUP.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-012-accepted-cleanup" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-012-accepted-cleanup" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-012-validation"
EXPECTED_ID = "RAG-012-accepted-cleanup"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def quote_card(chunk_id: str, source_id: str, principle: str) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": f"Quote source {source_id}",
        "source_ids": [source_id],
        "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
        "original_topic_id": "speech_tone_prosody_human_like_voice_behavior",
        "principle": principle,
        "application": "Original review card application that must be rewritten.",
        "when_not_to_use": "Original review card guardrail that must be rewritten.",
        "voice_or_prosody_advisory_only": True,
        "rewrite_action": "create_project_owned_paraphrase_or_keep_blocked",
        "human_acceptance_required": True,
        "quote_dependency_resolved_now": False,
        "source_excerpt_text_copied": False,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def chunk_row(chunk_id: str, status: str, source_title: str, *, source_ids: list[str] | None = None) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "status": status,
        "source_title": source_title,
        "source_ids": source_ids or [],
        "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
        "original_topic_id": "speech_tone_prosody_human_like_voice_behavior",
        "principle": f"Fixture principle for {chunk_id}",
        "application": "Fixture application.",
        "when_not_to_use": "Fixture guardrail.",
        "quote_dependency_present": status == "blocked_quote_clearance",
        "quoted_text_copied": False,
        "voice_or_prosody_advisory_only": status == "blocked_quote_clearance",
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rag011 = {
        "blocker_cleanup_packet_id": "RAG-011-blocker-cleanup-packet",
        "summary": {
            "source_mapping_blocker_count": 2,
            "source_mapping_candidate_group_count": 1,
            "source_mapping_candidate_chunk_count": 2,
            "quote_clearance_blocker_count": 2,
            "quote_clearance_review_card_count": 2,
            "potential_blocker_reduction_after_human_acceptance": 4,
            "blockers_resolved_now": 0,
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
        "source_mapping_candidates": [
            {
                "source_title": "Fixture high-confidence source",
                "chunk_ids": ["rag005-chunk-901", "rag005-chunk-902"],
                "chunk_count": 2,
                "topic_ids": ["cold_calling"],
                "candidate_source_id": "rag004-source-901",
                "candidate_canonical_title": "Fixture Canonical Source",
                "candidate_score": 0.66,
                "score_threshold": 0.55,
                "human_acceptance_required": True,
                "auto_apply_allowed": False,
                "review_action": "human_confirm_source_mapping_before_chunk_reclassification",
            }
        ],
        "quote_clearance_cards": [
            quote_card("rag005-chunk-903", "rag004-source-903", "Purposeful Pausing for Highlight"),
            quote_card("rag005-chunk-904", "rag004-source-904", "Match, Mirror, and Lead"),
        ],
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_used_in_runtime": False,
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
            "source_count": 4,
            "chunk_candidate_count": 4,
            "blocked_source_mapping_count": 2,
            "blocked_quote_clearance_count": 2,
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
            chunk_row("rag005-chunk-901", "blocked_source_mapping", "Fixture high-confidence source"),
            chunk_row("rag005-chunk-902", "blocked_source_mapping", "Fixture high-confidence source"),
            chunk_row("rag005-chunk-903", "blocked_quote_clearance", "Quote source rag004-source-903", source_ids=["rag004-source-903"]),
            chunk_row("rag005-chunk-904", "blocked_quote_clearance", "Quote source rag004-source-904", source_ids=["rag004-source-904"]),
        ],
    }
    case = {
        "accepted_cleanup_id": EXPECTED_ID,
        "accepted_by": "project_owner_current_session",
        "accepted_source_mapping_chunk_ids": ["rag005-chunk-901", "rag005-chunk-902"],
        "accepted_quote_clearance_chunk_ids": ["rag005-chunk-903", "rag005-chunk-904"],
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
    }
    paths = {
        "rag011": TMP_DIR / "rag011-result.json",
        "rag009": TMP_DIR / "rag009-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag011"].write_text(json.dumps(rag011, indent=2), encoding="utf-8")
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-012 accepted cleanup module is missing.")
    spec = importlib.util.spec_from_file_location("rag_accepted_cleanup", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-012 module spec.")
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-012 text found: {term}")


def validate_payload(payload: dict[str, Any], *, expected_total: int) -> None:
    assert_condition(payload.get("accepted_cleanup_id") == EXPECTED_ID, "Unexpected RAG-012 ID.")
    summary = payload.get("summary", {})
    assert_condition(summary.get("accepted_cleanup_decision_count") == expected_total, summary)
    assert_condition(summary.get("blockers_resolved_in_prior_artifacts") == 0, summary)
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

    mappings = payload.get("accepted_source_mappings", [])
    quote_items = payload.get("accepted_quote_clearance_items", [])
    assert_condition(summary.get("accepted_source_mapping_chunk_count") == len(mappings), summary)
    assert_condition(summary.get("accepted_quote_clearance_item_count") == len(quote_items), summary)
    assert_condition(len(mappings) + len(quote_items) == expected_total, payload)

    for mapping in mappings:
        assert_condition(mapping["review_verdict"] == "source_mapping_accepted", mapping)
        assert_condition(mapping["runtime_eligible_now"] is False, mapping)
        assert_condition(mapping["retrieval_eligible_now"] is False, mapping)
        assert_condition(mapping["quote_dependency_resolved"] is False, mapping)
        assert_condition(mapping["source_mapping_resolved"] is True, mapping)
        assert_condition(mapping["accepted_source_ids"], mapping)

    for item in quote_items:
        assert_condition(item["review_verdict"] == "manual_quote_clearance_paraphrased", item)
        assert_condition(item["quote_dependency_resolved"] is True, item)
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
        assert_condition(item["project_rule"], item)
        assert_condition(item["safe_application"], item)
        assert_condition(item["do_not_use_when"], item)
        assert_condition(item["guardrail_notes"], item)
        assert_condition("source_excerpt" not in item, item)
        assert_condition("source_excerpt_text" not in item, item)

    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(module.RAG_ACCEPTED_CLEANUP_ID == EXPECTED_ID, "Unexpected RAG-012 module ID.")
    assert_condition(hasattr(module, "build_accepted_cleanup"), "Missing builder function.")
    assert_condition(hasattr(module, "render_accepted_cleanup_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_accepted_cleanup(paths["rag011"], paths["rag009"], paths["case"], root=ROOT)
    validate_payload(payload, expected_total=4)
    report = module.render_accepted_cleanup_report(payload)
    assert_condition("RAG-012 Accepted Cleanup" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-012 accepted cleanup runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-012 accepted cleanup case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-012 accepted cleanup product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
        "--rag011-result",
        str(paths["rag011"]),
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
    validate_payload(json.loads(paths["result"].read_text(encoding="utf-8")), expected_total=4)
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-012 Accepted Cleanup" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("17 accepted cleanup decisions" in doc_text, "Product doc should record official cleanup count.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-012 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-012 report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    validate_payload(payload, expected_total=17)
    summary = payload["summary"]
    assert_condition(summary.get("accepted_source_mapping_chunk_count") == 5, summary)
    assert_condition(summary.get("accepted_quote_clearance_item_count") == 12, summary)
    assert_condition(summary.get("source_mapping_blockers_remaining_after_acceptance") == 58, summary)
    assert_condition(summary.get("quote_clearance_blockers_remaining_after_acceptance") == 30, summary)
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-012 accepted cleanup validation passed.")


if __name__ == "__main__":
    main()
