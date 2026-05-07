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
MODULE = ROOT / "scripts" / "rag_source_mapping_batches.py"
RUNNER = ROOT / "scripts" / "run_rag_015_source_mapping_batches.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-015-source-mapping-batches.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_015_SOURCE_MAPPING_BATCHES.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-015-source-mapping-batches" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-015-source-mapping-batches" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-015-validation"
EXPECTED_ID = "RAG-015-source-mapping-batches"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def source_group(source_title: str, chunk_ids: list[str], *, suggestions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "source_title": source_title,
        "chunk_ids": chunk_ids,
        "topic_ids": ["cold_calling"],
        "chunk_count": len(chunk_ids),
        "candidate_source_suggestions": suggestions or [],
        "auto_mapped": False,
    }


def source_row(chunk_id: str, source_title: str, *, quote_dependency: bool) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "status": "blocked_source_mapping",
        "source_title": source_title,
        "source_ids": [],
        "topic_ids": ["cold_calling"],
        "status_reasons": ["source_mapping_required"],
        "quote_dependency_present": quote_dependency,
        "quoted_text_copied": False,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rag014 = {
        "source_mapped_quote_followup_id": "RAG-014-source-mapped-quote-followup",
        "summary": {
            "source_mapped_quote_followups_remaining_after_review": 0,
            "cleanup_decisions_applied_now": 2,
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
        "accepted_quote_clearance_items": [
            {
                "chunk_id": "rag005-chunk-001",
                "source_mapping_resolved": True,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
            }
        ],
        "rejected_followup_items": [
            {
                "chunk_id": "rag005-chunk-002",
                "source_mapping_resolved": True,
                "runtime_eligible_now": False,
                "retrieval_eligible_now": False,
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
    rag013 = {
        "cleanup_strategy_id": "RAG-013-cleanup-strategy",
        "summary": {
            "remaining_source_mapping_chunk_count": 6,
            "remaining_source_mapping_group_count": 3,
            "latent_quote_followup_after_remaining_source_mapping": 2,
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
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "summary": {
            "source_mapping_queue_count": 4,
            "source_mapping_chunk_count": 7,
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
                source_group("Already resolved source", ["rag005-chunk-001", "rag005-chunk-002"]),
                source_group("High impact source", ["rag005-chunk-003", "rag005-chunk-004", "rag005-chunk-005"]),
                source_group("Medium source", ["rag005-chunk-006", "rag005-chunk-007"]),
                source_group(
                    "Suggested singleton",
                    ["rag005-chunk-008"],
                    suggestions=[
                        {
                            "source_id": "rag004-source-008",
                            "canonical_title": "Suggested Source",
                            "score": 0.61,
                            "review_only": True,
                        }
                    ],
                ),
            ]
        },
    }
    rag009 = {
        "review_coverage_id": "RAG-009-all-source-review-coverage",
        "summary": {
            "blocked_source_mapping_count": 7,
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
                source_row("rag005-chunk-003", "High impact source", quote_dependency=True),
                source_row("rag005-chunk-004", "High impact source", quote_dependency=False),
                source_row("rag005-chunk-005", "High impact source", quote_dependency=False),
                source_row("rag005-chunk-006", "Medium source", quote_dependency=True),
                source_row("rag005-chunk-007", "Medium source", quote_dependency=False),
                source_row("rag005-chunk-008", "Suggested singleton", quote_dependency=False),
            ]
        },
        "chunk_coverage": [
            source_row("rag005-chunk-003", "High impact source", quote_dependency=True),
            source_row("rag005-chunk-004", "High impact source", quote_dependency=False),
            source_row("rag005-chunk-005", "High impact source", quote_dependency=False),
            source_row("rag005-chunk-006", "Medium source", quote_dependency=True),
            source_row("rag005-chunk-007", "Medium source", quote_dependency=False),
            source_row("rag005-chunk-008", "Suggested singleton", quote_dependency=False),
        ],
    }
    case = {
        "source_mapping_batches_id": EXPECTED_ID,
        "title": "RAG source-mapping batches",
        "default_rag014_result": "research/experiments/generated/RAG-014-source-mapped-quote-followup/result.json",
        "default_rag013_result": "research/experiments/generated/RAG-013-cleanup-strategy/result.json",
        "default_rag006_packet": "research/experiments/generated/RAG-006-chunk-review-packet/result.json",
        "default_rag009_result": "research/experiments/generated/RAG-009-all-source-review-coverage/result.json",
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
        "metadata_only": True,
    }
    paths = {
        "rag014": TMP_DIR / "rag014-result.json",
        "rag013": TMP_DIR / "rag013-result.json",
        "rag006": TMP_DIR / "rag006-result.json",
        "rag009": TMP_DIR / "rag009-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag014"].write_text(json.dumps(rag014, indent=2), encoding="utf-8")
    paths["rag013"].write_text(json.dumps(rag013, indent=2), encoding="utf-8")
    paths["rag006"].write_text(json.dumps(rag006, indent=2), encoding="utf-8")
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-015 source-mapping batches module is missing.")
    spec = importlib.util.spec_from_file_location("rag_source_mapping_batches", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-015 module spec.")
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-015 text found: {term}")


def validate_payload(
    payload: dict[str, Any],
    *,
    expected_groups: int,
    expected_chunks: int,
    expected_high: int,
    expected_medium: int,
    expected_singletons: int,
    expected_latent: int,
) -> None:
    assert_condition(payload.get("source_mapping_batches_id") == EXPECTED_ID, "Unexpected RAG-015 ID.")
    summary = payload.get("summary", {})
    assert_condition(summary.get("source_mapping_group_count") == expected_groups, summary)
    assert_condition(summary.get("source_mapping_chunk_count") == expected_chunks, summary)
    assert_condition(summary.get("high_impact_group_count") == expected_high, summary)
    assert_condition(summary.get("medium_group_count") == expected_medium, summary)
    assert_condition(summary.get("singleton_group_count") == expected_singletons, summary)
    assert_condition(summary.get("latent_quote_followup_after_source_mapping") == expected_latent, summary)
    assert_condition(summary.get("cleanup_decisions_applied_now") == 0, summary)
    assert_condition(summary.get("source_mapping_blockers_resolved_now") == 0, summary)
    assert_condition(summary.get("source_mapping_blockers_remaining_after_rag015") == expected_chunks, summary)
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

    groups = payload.get("source_mapping_review_groups", [])
    batches = payload.get("priority_batches", [])
    assert_condition(len(groups) == expected_groups, groups)
    assert_condition(sum(group["remaining_chunk_count"] for group in groups) == expected_chunks, groups)
    assert_condition(len(batches) >= 3, batches)
    for group in groups:
        assert_condition(group["runtime_eligible_now"] is False, group)
        assert_condition(group["retrieval_eligible_now"] is False, group)
        assert_condition(group["auto_apply_allowed"] is False, group)
        assert_condition(group["review_action"] == "human_review_source_mapping_before_reclassification", group)
        assert_condition(group["remaining_chunk_count"] >= 1, group)
    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(module.RAG_SOURCE_MAPPING_BATCHES_ID == EXPECTED_ID, "Unexpected RAG-015 module ID.")
    assert_condition(hasattr(module, "build_source_mapping_batches"), "Missing builder function.")
    assert_condition(hasattr(module, "render_source_mapping_batches_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_source_mapping_batches(
        paths["rag014"],
        paths["rag013"],
        paths["rag006"],
        paths["rag009"],
        paths["case"],
        root=ROOT,
    )
    validate_payload(
        payload,
        expected_groups=3,
        expected_chunks=6,
        expected_high=1,
        expected_medium=1,
        expected_singletons=1,
        expected_latent=2,
    )
    report = module.render_source_mapping_batches_report(payload)
    assert_condition("RAG-015 Source-Mapping Batches" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-015 source-mapping batches runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-015 source-mapping batches case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-015 source-mapping batches product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
        "--rag014-result",
        str(paths["rag014"]),
        "--rag013-result",
        str(paths["rag013"]),
        "--rag006-packet",
        str(paths["rag006"]),
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
    validate_payload(
        json.loads(paths["result"].read_text(encoding="utf-8")),
        expected_groups=3,
        expected_chunks=6,
        expected_high=1,
        expected_medium=1,
        expected_singletons=1,
        expected_latent=2,
    )
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-015 Source-Mapping Batches" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("58 remaining source-mapping chunks" in doc_text, "Product doc should record official chunk count.")
    assert_condition("43 source-title groups" in doc_text, "Product doc should record official group count.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-015 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-015 report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    validate_payload(
        payload,
        expected_groups=43,
        expected_chunks=58,
        expected_high=3,
        expected_medium=6,
        expected_singletons=34,
        expected_latent=21,
    )
    summary = payload["summary"]
    assert_condition(summary.get("candidate_source_suggestion_group_count") == 6, summary)
    assert_condition(summary.get("candidate_source_suggestion_count") == 7, summary)
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-015 source-mapping batches validation passed.")


if __name__ == "__main__":
    main()
