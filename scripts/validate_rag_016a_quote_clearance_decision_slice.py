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
MODULE = ROOT / "scripts" / "rag_quote_clearance_decision_slice.py"
RUNNER = ROOT / "scripts" / "run_rag_016a_quote_clearance_decision_slice.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-016a-quote-clearance-decision-slice.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_016A_QUOTE_CLEARANCE_DECISION_SLICE.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-016A-quote-clearance-decision-slice" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-016A-quote-clearance-decision-slice" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-016a-validation"
EXPECTED_ID = "RAG-016A-quote-clearance-decision-slice"
EXPECTED_NEXT_CHECKPOINT = "RAG-016B-voice-delivery-quote-clearance-decision-slice"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def review_card(
    chunk_id: str,
    batch_id: str,
    lane: str,
    source_title: str,
    source_id: str,
    topic_id: str,
    *,
    voice_advisory: bool = False,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "priority_batch": batch_id,
        "cleanup_lane": lane,
        "review_focus": "low_pressure_response_wording" if lane == "ethical_persuasion" else "speech_prosody_advisory",
        "source_title": source_title,
        "source_ids": [source_id],
        "topic_ids": [topic_id],
        "status_reasons": ["quote_clearance_required"],
        "review_action": "create_project_owned_paraphrase_or_reject",
        "review_guardrail": "Rewrite as project-owned guidance.",
        "quote_dependency_present": True,
        "quote_clearance_resolved_now": False,
        "voice_or_prosody_advisory_only": voice_advisory,
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
    }


def chunk_detail(chunk_id: str, source_title: str, principle: str, topic_id: str) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": source_title,
        "source_ids": [],
        "topic_ids": [topic_id],
        "principle": principle,
        "quote_dependency_present": True,
        "quoted_text_copied": False,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    accepted_a = review_card(
        "rag005-chunk-077",
        "batch_1_ethical_persuasion_response_wording",
        "ethical_persuasion",
        "Science Of Persuasion",
        "rag004-source-075",
        "ethical_persuasion_persuasive_dialogue",
    )
    accepted_b = review_card(
        "rag005-chunk-089",
        "batch_1_ethical_persuasion_response_wording",
        "ethical_persuasion",
        "The Ethics of Manipulation",
        "rag004-source-083",
        "ethical_persuasion_persuasive_dialogue",
    )
    pending_voice = review_card(
        "rag005-chunk-090",
        "batch_2_speech_prosody_advisory",
        "voice_delivery",
        "How to Speak | Patrick Winston",
        "rag004-source-042",
        "speech_tone_prosody_human_like_voice_behavior",
        voice_advisory=True,
    )
    rag016 = {
        "quote_clearance_batches_id": "RAG-016-quote-clearance-batches",
        "recommended_next_checkpoint": EXPECTED_ID,
        "summary": {
            "quote_clearance_chunk_count": 3,
            "quote_clearance_batch_count": 2,
            "ethical_persuasion_chunk_count": 2,
            "voice_delivery_chunk_count": 1,
            "speech_prosody_advisory_chunk_count": 1,
            "emotion_recognition_delivery_chunk_count": 0,
            "source_mapping_pending_chunk_count_from_rag015": 6,
            "source_mapping_pending_group_count_from_rag015": 3,
            "source_mapping_latent_quote_followup_count_from_rag015": 2,
            "cleanup_decisions_applied_now": 0,
            "quote_clearance_blockers_resolved_now": 0,
            "quote_clearance_blockers_remaining_after_rag016": 3,
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
        "quote_clearance_review_cards": [accepted_a, accepted_b, pending_voice],
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
            "quote_clearance_decisions_applied": False,
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
            chunk_detail("rag005-chunk-077", "Science Of Persuasion", "Reciprocity", "ethical_persuasion_persuasive_dialogue"),
            chunk_detail("rag005-chunk-089", "The Ethics of Manipulation", "Ethical Guardrails", "ethical_persuasion_persuasive_dialogue"),
            chunk_detail("rag005-chunk-090", "How to Speak | Patrick Winston", "Fixture voice principle", "speech_tone_prosody_human_like_voice_behavior"),
        ],
    }
    case = {
        "quote_clearance_decision_slice_id": EXPECTED_ID,
        "recommended_next_checkpoint": EXPECTED_NEXT_CHECKPOINT,
        "selected_priority_batch": "batch_1_ethical_persuasion_response_wording",
        "accepted_quote_clearance_chunk_ids": ["rag005-chunk-077", "rag005-chunk-089"],
        "rejected_quote_clearance_chunk_ids": [],
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
        "metadata_only": True,
    }
    paths = {
        "rag016": TMP_DIR / "rag016-result.json",
        "rag009": TMP_DIR / "rag009-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag016"].write_text(json.dumps(rag016, indent=2), encoding="utf-8")
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-016A quote-clearance decision slice module is missing.")
    spec = importlib.util.spec_from_file_location("rag_quote_clearance_decision_slice", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-016A module spec.")
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-016A text found: {term}")


def validate_payload(
    payload: dict[str, Any],
    *,
    expected_candidates: int,
    expected_accepted: int,
    expected_rejected: int,
    expected_remaining: int,
    expected_source_mapping_pending: int,
) -> None:
    assert_condition(payload.get("quote_clearance_decision_slice_id") == EXPECTED_ID, "Unexpected RAG-016A ID.")
    assert_condition(payload.get("recommended_next_checkpoint") == EXPECTED_NEXT_CHECKPOINT, payload)
    summary = payload.get("summary", {})
    assert_condition(summary.get("decision_candidate_count") == expected_candidates, summary)
    assert_condition(summary.get("accepted_quote_clearance_item_count") == expected_accepted, summary)
    assert_condition(summary.get("rejected_quote_clearance_item_count") == expected_rejected, summary)
    assert_condition(summary.get("quote_clearance_decisions_applied_now") == expected_accepted + expected_rejected, summary)
    assert_condition(summary.get("quote_clearance_blockers_resolved_now") == expected_accepted + expected_rejected, summary)
    assert_condition(summary.get("quote_clearance_blockers_remaining_after_rag016a") == expected_remaining, summary)
    assert_condition(summary.get("source_mapping_pending_chunk_count_from_rag015") == expected_source_mapping_pending, summary)
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
    rejected_items = payload.get("rejected_quote_clearance_items", [])
    remaining_cards = payload.get("remaining_quote_clearance_cards", [])
    assert_condition(len(accepted_items) == expected_accepted, accepted_items)
    assert_condition(len(rejected_items) == expected_rejected, rejected_items)
    assert_condition(len(remaining_cards) == expected_remaining, remaining_cards)
    for item in accepted_items:
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
    assert_condition(module.RAG_QUOTE_CLEARANCE_DECISION_SLICE_ID == EXPECTED_ID, "Unexpected RAG-016A module ID.")
    assert_condition(hasattr(module, "build_quote_clearance_decision_slice"), "Missing builder function.")
    assert_condition(hasattr(module, "render_quote_clearance_decision_slice_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_quote_clearance_decision_slice(paths["rag016"], paths["rag009"], paths["case"], root=ROOT)
    validate_payload(
        payload,
        expected_candidates=2,
        expected_accepted=2,
        expected_rejected=0,
        expected_remaining=1,
        expected_source_mapping_pending=6,
    )
    report = module.render_quote_clearance_decision_slice_report(payload)
    assert_condition("RAG-016A Quote-Clearance Decision Slice" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-016A quote-clearance decision slice runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-016A quote-clearance decision slice case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-016A quote-clearance decision slice product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
        "--rag016-result",
        str(paths["rag016"]),
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
        expected_candidates=2,
        expected_accepted=2,
        expected_rejected=0,
        expected_remaining=1,
        expected_source_mapping_pending=6,
    )
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-016A Quote-Clearance Decision Slice" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("11 accepted quote-clearance items" in doc_text, "Product doc should record official acceptance count.")
    assert_condition("19 remaining original quote-clearance blockers" in doc_text, "Product doc should record official remaining count.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-016A result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-016A report is missing.")
    payload = json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8"))
    validate_payload(
        payload,
        expected_candidates=11,
        expected_accepted=11,
        expected_rejected=0,
        expected_remaining=19,
        expected_source_mapping_pending=58,
    )
    summary = payload["summary"]
    assert_condition(summary.get("ethical_persuasion_remaining_after_rag016a") == 0, summary)
    assert_condition(summary.get("voice_delivery_remaining_after_rag016a") == 19, summary)
    assert_condition(summary.get("accepted_lane_counts", {}).get("response_wording") == 10, summary)
    assert_condition(summary.get("accepted_lane_counts", {}).get("safety_guardrail") == 1, summary)
    accepted_ids = {item["chunk_id"] for item in payload.get("accepted_quote_clearance_items", [])}
    assert_condition(
        accepted_ids
        == {
            "rag005-chunk-077",
            "rag005-chunk-078",
            "rag005-chunk-079",
            "rag005-chunk-080",
            "rag005-chunk-082",
            "rag005-chunk-083",
            "rag005-chunk-085",
            "rag005-chunk-086",
            "rag005-chunk-087",
            "rag005-chunk-088",
            "rag005-chunk-089",
        },
        accepted_ids,
    )
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-016A quote-clearance decision slice validation passed.")


if __name__ == "__main__":
    main()
