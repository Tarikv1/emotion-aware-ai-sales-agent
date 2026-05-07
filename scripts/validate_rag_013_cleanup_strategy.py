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
MODULE = ROOT / "scripts" / "rag_cleanup_strategy.py"
RUNNER = ROOT / "scripts" / "run_rag_013_cleanup_strategy.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-013-cleanup-strategy.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_013_CLEANUP_STRATEGY.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-013-cleanup-strategy" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-013-cleanup-strategy" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-013-validation"
EXPECTED_ID = "RAG-013-cleanup-strategy"
EXPECTED_NEXT_CHECKPOINT = "RAG-014-source-mapped-quote-followup"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def source_row(chunk_id: str, source_title: str) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": source_title,
        "source_ids": [],
        "topic_ids": ["cold_calling"],
        "status_reasons": ["source_mapping_required"],
        "review_action": "map_to_rag004_source_or_create_reviewed_source",
    }


def quote_row(chunk_id: str, source_id: str, topic_id: str) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": f"Quote source {source_id}",
        "source_ids": [source_id],
        "topic_ids": [topic_id],
        "status_reasons": ["quote_clearance_required"],
        "review_action": "replace_quote_dependency_with_project_owned_paraphrase",
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rag012 = {
        "accepted_cleanup_id": "RAG-012-accepted-cleanup",
        "summary": {
            "accepted_source_mapping_chunk_count": 1,
            "accepted_quote_clearance_item_count": 1,
            "quote_clearance_follow_up_required_from_source_mappings": 1,
            "source_mapping_blockers_remaining_after_acceptance": 2,
            "quote_clearance_blockers_remaining_after_acceptance": 2,
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
        "accepted_source_mappings": [
            {
                "chunk_id": "rag005-chunk-901",
                "source_title": "Accepted source",
                "topic_ids": ["cold_calling"],
                "accepted_source_ids": ["rag004-source-901"],
                "accepted_canonical_title": "Accepted Canonical Source",
                "source_mapping_resolved": True,
                "quote_dependency_resolved": False,
                "quote_clearance_follow_up_required": True,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        ],
        "accepted_quote_clearance_items": [
            {
                "knowledge_id": "rag012-fixture-rule",
                "chunk_id": "rag005-chunk-904",
                "lane": "response_wording",
                "source_ids": ["rag004-source-904"],
                "quote_dependency_resolved": True,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
                "project_rule": "Fixture safe paraphrase.",
            }
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
            "blocked_source_mapping_count": 3,
            "blocked_quote_clearance_count": 3,
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
        "review_queues": {
            "source_mapping_queue": [
                source_row("rag005-chunk-901", "Accepted source"),
                source_row("rag005-chunk-902", "Remaining source A"),
                source_row("rag005-chunk-903", "Remaining source A"),
            ],
            "quote_clearance_queue": [
                quote_row("rag005-chunk-904", "rag004-source-904", "consultative_selling_discovery"),
                quote_row("rag005-chunk-905", "rag004-source-905", "speech_tone_prosody_human_like_voice_behavior"),
                quote_row("rag005-chunk-906", "rag004-source-906", "ethical_persuasion_persuasive_dialogue"),
            ],
        },
        "chunk_coverage": [
            {
                **source_row("rag005-chunk-901", "Accepted source"),
                "quote_dependency_present": True,
                "quoted_text_copied": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **source_row("rag005-chunk-902", "Remaining source A"),
                "quote_dependency_present": True,
                "quoted_text_copied": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **source_row("rag005-chunk-903", "Remaining source A"),
                "quote_dependency_present": False,
                "quoted_text_copied": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **quote_row("rag005-chunk-904", "rag004-source-904", "consultative_selling_discovery"),
                "quote_dependency_present": True,
                "quoted_text_copied": False,
                "voice_or_prosody_advisory_only": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **quote_row("rag005-chunk-905", "rag004-source-905", "speech_tone_prosody_human_like_voice_behavior"),
                "quote_dependency_present": True,
                "quoted_text_copied": False,
                "voice_or_prosody_advisory_only": True,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **quote_row("rag005-chunk-906", "rag004-source-906", "ethical_persuasion_persuasive_dialogue"),
                "quote_dependency_present": True,
                "quoted_text_copied": False,
                "voice_or_prosody_advisory_only": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
        ],
    }
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "summary": {
            "source_mapping_queue_count": 2,
            "source_mapping_chunk_count": 3,
            "quote_review_queue_count": 3,
            "auto_promoted_chunk_count": 0,
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
            "external_provider_calls_made": False,
            "notebooklm_api_used": False,
            "private_customer_data_used": False,
        },
        "review_queues": {
            "source_mapping_queue": [
                {
                    "source_title": "Accepted source",
                    "chunk_ids": ["rag005-chunk-901"],
                    "topic_ids": ["cold_calling"],
                    "chunk_count": 1,
                    "candidate_source_suggestions": [
                        {"source_id": "rag004-source-901", "canonical_title": "Accepted Canonical Source", "score": 0.71}
                    ],
                    "auto_mapped": False,
                },
                {
                    "source_title": "Remaining source A",
                    "chunk_ids": ["rag005-chunk-902", "rag005-chunk-903"],
                    "topic_ids": ["cold_calling"],
                    "chunk_count": 2,
                    "candidate_source_suggestions": [],
                    "auto_mapped": False,
                },
            ]
        },
    }
    case = {
        "cleanup_strategy_id": EXPECTED_ID,
        "recommended_next_checkpoint": EXPECTED_NEXT_CHECKPOINT,
        "max_source_mapping_groups": 5,
        "max_quote_clearance_examples": 5,
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
    }
    paths = {
        "rag012": TMP_DIR / "rag012-result.json",
        "rag009": TMP_DIR / "rag009-result.json",
        "rag006": TMP_DIR / "rag006-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag012"].write_text(json.dumps(rag012, indent=2), encoding="utf-8")
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["rag006"].write_text(json.dumps(rag006, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-013 cleanup strategy module is missing.")
    spec = importlib.util.spec_from_file_location("rag_cleanup_strategy", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-013 module spec.")
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-013 text found: {term}")


def validate_payload(
    payload: dict[str, Any],
    *,
    expected_source_remaining: int,
    expected_quote_remaining: int,
    expected_followups: int,
) -> None:
    assert_condition(payload.get("cleanup_strategy_id") == EXPECTED_ID, "Unexpected RAG-013 ID.")
    summary = payload.get("summary", {})
    assert_condition(summary.get("remaining_source_mapping_chunk_count") == expected_source_remaining, summary)
    assert_condition(summary.get("remaining_original_quote_clearance_count") == expected_quote_remaining, summary)
    assert_condition(summary.get("quote_follow_up_from_accepted_source_mappings") == expected_followups, summary)
    assert_condition(
        summary.get("known_cleanup_work_count_before_runtime")
        == expected_source_remaining + expected_quote_remaining + expected_followups,
        summary,
    )
    assert_condition(summary.get("cleanup_decisions_applied_now") == 0, summary)
    assert_condition(summary.get("auto_promoted_chunk_count") == 0, summary)
    assert_condition(payload.get("recommended_next_checkpoint") == EXPECTED_NEXT_CHECKPOINT, payload)
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

    stages = payload.get("strategy_stages", [])
    assert_condition(stages and stages[0]["checkpoint_id"] == EXPECTED_NEXT_CHECKPOINT, stages)
    assert_condition(stages[0]["cleanup_lane"] == "source_mapped_quote_followup", stages[0])
    for card in payload.get("source_mapped_quote_followups", []):
        assert_condition(card["runtime_eligible_now"] is False, card)
        assert_condition(card["retrieval_eligible_now"] is False, card)
        assert_condition(card["review_action"] == "create_project_owned_paraphrase_or_reject", card)
    for group in payload.get("source_mapping_batches", []):
        assert_condition(group["runtime_eligible_now"] is False, group)
        assert_condition(group["retrieval_eligible_now"] is False, group)
        assert_condition(group["remaining_chunk_count"] >= 1, group)
    for item in payload.get("quote_clearance_examples", []):
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(module.RAG_CLEANUP_STRATEGY_ID == EXPECTED_ID, "Unexpected RAG-013 module ID.")
    assert_condition(hasattr(module, "build_cleanup_strategy"), "Missing builder function.")
    assert_condition(hasattr(module, "render_cleanup_strategy_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_cleanup_strategy(paths["rag012"], paths["rag009"], paths["rag006"], paths["case"], root=ROOT)
    validate_payload(payload, expected_source_remaining=2, expected_quote_remaining=2, expected_followups=1)
    report = module.render_cleanup_strategy_report(payload)
    assert_condition("RAG-013 Cleanup Strategy" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-013 cleanup strategy runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-013 cleanup strategy case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-013 cleanup strategy product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
        "--rag012-result",
        str(paths["rag012"]),
        "--rag009-result",
        str(paths["rag009"]),
        "--rag006-packet",
        str(paths["rag006"]),
        "--case",
        str(paths["case"]),
        "--out",
        str(paths["result"]),
        "--report-out",
        str(paths["report"]),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    validate_payload(json.loads(paths["result"].read_text(encoding="utf-8")), expected_source_remaining=2, expected_quote_remaining=2, expected_followups=1)
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-013 Cleanup Strategy" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("known cleanup work count before runtime is `93`" in doc_text, "Product doc should record official work count.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-013 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-013 report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    validate_payload(payload, expected_source_remaining=58, expected_quote_remaining=30, expected_followups=5)
    summary = payload["summary"]
    assert_condition(summary.get("known_cleanup_work_count_before_runtime") == 93, summary)
    assert_condition(summary.get("remaining_source_mapping_group_count") == 43, summary)
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-013 cleanup strategy validation passed.")


if __name__ == "__main__":
    main()
