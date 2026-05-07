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
MODULE = ROOT / "scripts" / "rag_blocker_cleanup_packet.py"
RUNNER = ROOT / "scripts" / "run_rag_011_blocker_cleanup_packet.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-011-blocker-cleanup-packet.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_011_BLOCKER_CLEANUP_PACKET.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-011-blocker-cleanup-packet" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-011-blocker-cleanup-packet" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-011-validation"
EXPECTED_ID = "RAG-011-blocker-cleanup-packet"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def source_mapping_row(chunk_id: str, source_title: str) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": source_title,
        "source_ids": [],
        "topic_ids": ["consultative_selling_discovery"],
        "status_reasons": ["source_mapping_required"],
        "review_action": "map_to_rag004_source_or_create_reviewed_source",
    }


def quote_row(chunk_id: str, source_id: str, principle: str) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": f"Quote source {source_id}",
        "source_ids": [source_id],
        "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
        "status_reasons": ["quote_clearance_required"],
        "review_action": "replace_quote_dependency_with_project_owned_paraphrase",
        "principle": principle,
        "application": "Create a safe project-owned paraphrase before any future promotion.",
        "when_not_to_use": "Do not use until quote dependency is cleared by human review.",
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "summary": {
            "source_mapping_chunk_count": 3,
            "quote_review_queue_count": 3,
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
                    "source_title": "High confidence source",
                    "chunk_ids": ["rag005-chunk-201", "rag005-chunk-202"],
                    "topic_ids": ["consultative_selling_discovery"],
                    "chunk_count": 2,
                    "candidate_source_suggestions": [
                        {
                            "source_id": "rag004-source-201",
                            "canonical_title": "High Confidence Source",
                            "score": 0.72,
                            "review_only": True,
                        }
                    ],
                    "review_action": "map_to_existing_source_or_create_source_candidate",
                    "auto_mapped": False,
                },
                {
                    "source_title": "Low confidence source",
                    "chunk_ids": ["rag005-chunk-203"],
                    "topic_ids": ["objection_handling"],
                    "chunk_count": 1,
                    "candidate_source_suggestions": [
                        {
                            "source_id": "rag004-source-203",
                            "canonical_title": "Low Confidence Source",
                            "score": 0.41,
                            "review_only": True,
                        }
                    ],
                    "review_action": "map_to_existing_source_or_create_source_candidate",
                    "auto_mapped": False,
                },
            ],
            "topic_mapping_queue": [],
            "quote_review_queue": [],
        },
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
    }
    quote_rows = [
        quote_row("rag005-chunk-301", "rag004-source-301", "Quote Card One"),
        quote_row("rag005-chunk-302", "rag004-source-302", "Quote Card Two"),
        quote_row("rag005-chunk-303", "rag004-source-303", "Quote Card Three"),
    ]
    rag009 = {
        "review_coverage_id": "RAG-009-all-source-review-coverage",
        "summary": {
            "source_count": 6,
            "chunk_candidate_count": 6,
            "blocked_source_mapping_count": 3,
            "blocked_quote_clearance_count": 3,
            "auto_promoted_chunk_count": 0,
            "all_rag004_sources_accounted_for": True,
            "all_rag005_chunks_accounted_for": True,
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
                source_mapping_row("rag005-chunk-201", "High confidence source"),
                source_mapping_row("rag005-chunk-202", "High confidence source"),
                source_mapping_row("rag005-chunk-203", "Low confidence source"),
            ],
            "topic_mapping_queue": [],
            "quote_clearance_queue": [
                {key: value for key, value in row.items() if key in {"chunk_id", "source_title", "source_ids", "topic_ids", "status_reasons", "review_action"}}
                for row in quote_rows
            ],
            "safety_rejection_queue": [],
            "deferred_review_queue": [],
        },
        "chunk_coverage": [
            {
                **source_mapping_row("rag005-chunk-201", "High confidence source"),
                "original_topic_id": "consultative_selling_discovery",
                "principle": "Mapped one",
                "application": "Needs source mapping.",
                "when_not_to_use": "Do not use before mapping.",
                "review_flags": ["source_mapping_required"],
                "rag006_locations": ["source_mapping_queue"],
                "quote_dependency_present": False,
                "quoted_text_copied": False,
                "status": "blocked_source_mapping",
                "voice_or_prosody_advisory_only": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **source_mapping_row("rag005-chunk-202", "High confidence source"),
                "original_topic_id": "consultative_selling_discovery",
                "principle": "Mapped two",
                "application": "Needs source mapping.",
                "when_not_to_use": "Do not use before mapping.",
                "review_flags": ["source_mapping_required"],
                "rag006_locations": ["source_mapping_queue"],
                "quote_dependency_present": False,
                "quoted_text_copied": False,
                "status": "blocked_source_mapping",
                "voice_or_prosody_advisory_only": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            {
                **source_mapping_row("rag005-chunk-203", "Low confidence source"),
                "original_topic_id": "objection_handling",
                "principle": "Low score",
                "application": "Needs source mapping.",
                "when_not_to_use": "Do not use before mapping.",
                "review_flags": ["source_mapping_required"],
                "rag006_locations": ["source_mapping_queue"],
                "quote_dependency_present": False,
                "quoted_text_copied": False,
                "status": "blocked_source_mapping",
                "voice_or_prosody_advisory_only": False,
                "runtime_use_allowed": False,
                "retrieval_used_in_runtime": False,
            },
            *[
                {
                    **row,
                    "original_topic_id": "speech_tone_prosody_human_like_voice_behavior",
                    "review_flags": ["quote_review_required"],
                    "rag006_locations": ["quote_review_queue"],
                    "quote_dependency_present": True,
                    "quoted_text_copied": False,
                    "status": "blocked_quote_clearance",
                    "voice_or_prosody_advisory_only": True,
                    "runtime_use_allowed": False,
                    "retrieval_used_in_runtime": False,
                }
                for row in quote_rows
            ],
        ],
    }
    case = {
        "blocker_cleanup_packet_id": EXPECTED_ID,
        "min_source_suggestion_score": 0.55,
        "max_quote_clearance_cards": 2,
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
    }
    paths = {
        "rag009": TMP_DIR / "rag009-result.json",
        "rag006": TMP_DIR / "rag006-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["rag006"].write_text(json.dumps(rag006, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-011 blocker cleanup module is missing.")
    spec = importlib.util.spec_from_file_location("rag_blocker_cleanup_packet", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-011 module spec.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_no_forbidden_text(payload_text: str) -> None:
    forbidden_terms = [
        '"runtime_retrieval_enabled": true',
        '"chunk_import_enabled": true',
        '"retrieval_used_in_runtime": true',
        '"runtime_use_allowed": true',
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-011 text found: {term}")


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("blocker_cleanup_packet_id") == EXPECTED_ID, "Unexpected RAG-011 ID.")
    summary = payload.get("summary", {})
    assert_condition(summary.get("source_mapping_blocker_count") == 3, summary)
    assert_condition(summary.get("source_mapping_candidate_group_count") == 1, summary)
    assert_condition(summary.get("source_mapping_candidate_chunk_count") == 2, summary)
    assert_condition(summary.get("quote_clearance_blocker_count") == 3, summary)
    assert_condition(summary.get("quote_clearance_review_card_count") == 2, summary)
    assert_condition(summary.get("blockers_resolved_now") == 0, summary)
    assert_condition(summary.get("auto_promoted_chunk_count") == 0, summary)
    for key in (
        "runtime_retrieval_enabled",
        "retrieval_used_in_runtime",
        "chunk_import_enabled",
        "provider_calls_made",
        "notebooklm_api_used",
        "private_customer_data_used",
        "reads_data_private",
        "source_excerpt_text_stored",
    ):
        assert_condition(summary.get(key) is False, {key: summary.get(key)})

    proposals = payload.get("source_mapping_candidates", [])
    assert_condition(len(proposals) == 1, proposals)
    proposal = proposals[0]
    assert_condition(proposal["source_title"] == "High confidence source", proposal)
    assert_condition(proposal["candidate_source_id"] == "rag004-source-201", proposal)
    assert_condition(proposal["candidate_score"] >= 0.55, proposal)
    assert_condition(proposal["chunk_ids"] == ["rag005-chunk-201", "rag005-chunk-202"], proposal)
    assert_condition(proposal["human_acceptance_required"] is True, proposal)
    assert_condition(proposal["auto_apply_allowed"] is False, proposal)

    cards = payload.get("quote_clearance_cards", [])
    assert_condition(len(cards) == 2, cards)
    assert_condition([card["chunk_id"] for card in cards] == ["rag005-chunk-301", "rag005-chunk-302"], cards)
    for card in cards:
        assert_condition(card["human_acceptance_required"] is True, card)
        assert_condition(card["quote_dependency_resolved_now"] is False, card)
        assert_condition(card["runtime_use_allowed"] is False, card)
        assert_condition(card["source_excerpt_text_copied"] is False, card)
        assert_condition("source_excerpt" not in card, card)
        assert_condition("source_excerpt_text" not in card, card)

    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(
        module.RAG_BLOCKER_CLEANUP_PACKET_ID == EXPECTED_ID,
        "Unexpected RAG-011 module ID.",
    )
    assert_condition(hasattr(module, "build_blocker_cleanup_packet"), "Missing builder function.")
    assert_condition(hasattr(module, "render_blocker_cleanup_packet_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_blocker_cleanup_packet(paths["rag009"], paths["rag006"], paths["case"], root=ROOT)
    validate_payload(payload)
    report = module.render_blocker_cleanup_packet_report(payload)
    assert_condition("RAG-011 Blocker Cleanup Packet" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])
    assert_condition("High confidence source" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-011 blocker cleanup runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-011 blocker cleanup case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-011 blocker cleanup product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
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
    validate_payload(json.loads(paths["result"].read_text(encoding="utf-8")))
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-011 Blocker Cleanup Packet" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("blockers_resolved_now" in doc_text, "Product doc should document non-mutation boundary.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-011 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-011 report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    summary = payload.get("summary", {})
    assert_condition(summary.get("source_mapping_blocker_count") == 63, summary)
    assert_condition(summary.get("quote_clearance_blocker_count") == 42, summary)
    assert_condition(summary.get("blockers_resolved_now") == 0, summary)
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-011 blocker cleanup packet validation passed.")


if __name__ == "__main__":
    main()
