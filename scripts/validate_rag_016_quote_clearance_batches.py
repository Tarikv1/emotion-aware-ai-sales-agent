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
MODULE = ROOT / "scripts" / "rag_quote_clearance_batches.py"
RUNNER = ROOT / "scripts" / "run_rag_016_quote_clearance_batches.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-016-quote-clearance-batches.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_016_QUOTE_CLEARANCE_BATCHES.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-016-quote-clearance-batches" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-016-quote-clearance-batches" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-016-validation"
EXPECTED_ID = "RAG-016-quote-clearance-batches"
EXPECTED_NEXT_CHECKPOINT = "RAG-016A-quote-clearance-decision-slice"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def quote_row(chunk_id: str, source_id: str, topic_id: str, *, voice_advisory: bool = False) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": f"Quote source {source_id}",
        "source_ids": [source_id],
        "topic_ids": [topic_id],
        "status_reasons": ["quote_clearance_required"],
        "review_action": "replace_quote_dependency_with_project_owned_paraphrase",
        "quote_dependency_present": True,
        "quoted_text_copied": False,
        "voice_or_prosody_advisory_only": voice_advisory,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rag015 = {
        "source_mapping_batches_id": "RAG-015-source-mapping-batches",
        "recommended_next_checkpoint": EXPECTED_ID,
        "summary": {
            "source_mapping_group_count": 3,
            "source_mapping_chunk_count": 6,
            "latent_quote_followup_after_source_mapping": 2,
            "cleanup_decisions_applied_now": 0,
            "source_mapping_blockers_resolved_now": 0,
            "source_mapping_blockers_remaining_after_rag015": 6,
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
            "source_mapping_decisions_applied": False,
        },
    }
    rag013 = {
        "cleanup_strategy_id": "RAG-013-cleanup-strategy",
        "summary": {
            "remaining_source_mapping_chunk_count": 6,
            "remaining_source_mapping_group_count": 3,
            "remaining_original_quote_clearance_count": 3,
            "quote_follow_up_from_accepted_source_mappings": 1,
            "known_cleanup_work_count_before_runtime": 10,
            "latent_quote_followup_after_remaining_source_mapping": 2,
            "cleanup_decisions_applied_now": 0,
            "auto_promoted_chunk_count": 0,
            "quote_clearance_lane_counts": {
                "ethical_persuasion": 1,
                "voice_delivery": 2,
            },
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
    rag012 = {
        "accepted_cleanup_id": "RAG-012-accepted-cleanup",
        "summary": {
            "accepted_quote_clearance_item_count": 1,
            "quote_clearance_blockers_remaining_after_acceptance": 3,
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
                "quote_dependency_resolved": True,
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
    accepted_row = quote_row("rag005-chunk-001", "rag004-source-001", "consultative_selling_discovery")
    ethical_row = quote_row("rag005-chunk-002", "rag004-source-002", "ethical_persuasion_persuasive_dialogue")
    speech_row = quote_row(
        "rag005-chunk-003",
        "rag004-source-003",
        "speech_tone_prosody_human_like_voice_behavior",
        voice_advisory=True,
    )
    emotion_row = quote_row(
        "rag005-chunk-004",
        "rag004-source-004",
        "emotion_recognition_speech_emotion_persuasion_datasets",
        voice_advisory=True,
    )
    rag009 = {
        "review_coverage_id": "RAG-009-all-source-review-coverage",
        "summary": {
            "blocked_quote_clearance_count": 4,
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
            "quote_clearance_queue": [accepted_row, ethical_row, speech_row, emotion_row],
        },
        "chunk_coverage": [accepted_row, ethical_row, speech_row, emotion_row],
    }
    case = {
        "quote_clearance_batches_id": EXPECTED_ID,
        "recommended_next_checkpoint": EXPECTED_NEXT_CHECKPOINT,
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
        "metadata_only": True,
    }
    paths = {
        "rag015": TMP_DIR / "rag015-result.json",
        "rag013": TMP_DIR / "rag013-result.json",
        "rag012": TMP_DIR / "rag012-result.json",
        "rag009": TMP_DIR / "rag009-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag015"].write_text(json.dumps(rag015, indent=2), encoding="utf-8")
    paths["rag013"].write_text(json.dumps(rag013, indent=2), encoding="utf-8")
    paths["rag012"].write_text(json.dumps(rag012, indent=2), encoding="utf-8")
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-016 quote-clearance batches module is missing.")
    spec = importlib.util.spec_from_file_location("rag_quote_clearance_batches", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-016 module spec.")
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-016 text found: {term}")


def validate_payload(
    payload: dict[str, Any],
    *,
    expected_chunks: int,
    expected_ethical: int,
    expected_voice: int,
    expected_speech: int,
    expected_emotion: int,
    expected_source_mapping_pending: int,
    expected_source_mapping_groups: int,
) -> None:
    assert_condition(payload.get("quote_clearance_batches_id") == EXPECTED_ID, "Unexpected RAG-016 ID.")
    assert_condition(payload.get("recommended_next_checkpoint") == EXPECTED_NEXT_CHECKPOINT, payload)
    summary = payload.get("summary", {})
    assert_condition(summary.get("quote_clearance_chunk_count") == expected_chunks, summary)
    assert_condition(summary.get("ethical_persuasion_chunk_count") == expected_ethical, summary)
    assert_condition(summary.get("voice_delivery_chunk_count") == expected_voice, summary)
    assert_condition(summary.get("speech_prosody_advisory_chunk_count") == expected_speech, summary)
    assert_condition(summary.get("emotion_recognition_delivery_chunk_count") == expected_emotion, summary)
    assert_condition(summary.get("source_mapping_pending_chunk_count_from_rag015") == expected_source_mapping_pending, summary)
    assert_condition(summary.get("source_mapping_pending_group_count_from_rag015") == expected_source_mapping_groups, summary)
    assert_condition(summary.get("cleanup_decisions_applied_now") == 0, summary)
    assert_condition(summary.get("quote_clearance_blockers_resolved_now") == 0, summary)
    assert_condition(summary.get("quote_clearance_blockers_remaining_after_rag016") == expected_chunks, summary)
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

    batches = payload.get("priority_batches", [])
    cards = payload.get("quote_clearance_review_cards", [])
    assert_condition(len(batches) == 3, batches)
    assert_condition(len(cards) == expected_chunks, cards)
    assert_condition(sum(int(batch["chunk_count"]) for batch in batches) == expected_chunks, batches)
    assert_condition(any(batch["batch_id"] == "batch_1_ethical_persuasion_response_wording" for batch in batches), batches)
    assert_condition(any(batch["batch_id"] == "batch_2_speech_prosody_advisory" for batch in batches), batches)
    assert_condition(any(batch["batch_id"] == "batch_3_emotion_recognition_delivery_advisory" for batch in batches), batches)
    for card in cards:
        assert_condition(card["runtime_eligible_now"] is False, card)
        assert_condition(card["retrieval_eligible_now"] is False, card)
        assert_condition(card["quote_clearance_resolved_now"] is False, card)
        assert_condition(card["review_action"] == "create_project_owned_paraphrase_or_reject", card)
        assert_condition("source_excerpt" not in card, card)
        assert_condition("source_excerpt_text" not in card, card)
    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(module.RAG_QUOTE_CLEARANCE_BATCHES_ID == EXPECTED_ID, "Unexpected RAG-016 module ID.")
    assert_condition(hasattr(module, "build_quote_clearance_batches"), "Missing builder function.")
    assert_condition(hasattr(module, "render_quote_clearance_batches_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_quote_clearance_batches(
        paths["rag015"],
        paths["rag013"],
        paths["rag012"],
        paths["rag009"],
        paths["case"],
        root=ROOT,
    )
    validate_payload(
        payload,
        expected_chunks=3,
        expected_ethical=1,
        expected_voice=2,
        expected_speech=1,
        expected_emotion=1,
        expected_source_mapping_pending=6,
        expected_source_mapping_groups=3,
    )
    report = module.render_quote_clearance_batches_report(payload)
    assert_condition("RAG-016 Quote-Clearance Batches" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-016 quote-clearance batches runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-016 quote-clearance batches case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-016 quote-clearance batches product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
        "--rag015-result",
        str(paths["rag015"]),
        "--rag013-result",
        str(paths["rag013"]),
        "--rag012-result",
        str(paths["rag012"]),
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
        expected_chunks=3,
        expected_ethical=1,
        expected_voice=2,
        expected_speech=1,
        expected_emotion=1,
        expected_source_mapping_pending=6,
        expected_source_mapping_groups=3,
    )
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-016 Quote-Clearance Batches" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("30 remaining original quote-clearance chunks" in doc_text, "Product doc should record official chunk count.")
    assert_condition("19 voice-delivery chunks" in doc_text, "Product doc should record official voice count.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-016 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-016 report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    validate_payload(
        payload,
        expected_chunks=30,
        expected_ethical=11,
        expected_voice=19,
        expected_speech=10,
        expected_emotion=9,
        expected_source_mapping_pending=58,
        expected_source_mapping_groups=43,
    )
    summary = payload["summary"]
    assert_condition(summary.get("quote_clearance_batch_count") == 3, summary)
    assert_condition(summary.get("source_mapping_latent_quote_followup_count_from_rag015") == 21, summary)
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-016 quote-clearance batches validation passed.")


if __name__ == "__main__":
    main()
