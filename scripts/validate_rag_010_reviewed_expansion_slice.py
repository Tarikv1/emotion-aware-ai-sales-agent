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
MODULE = ROOT / "scripts" / "rag_reviewed_expansion_slice.py"
RUNNER = ROOT / "scripts" / "run_rag_010_reviewed_expansion_slice.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-010-reviewed-expansion-slice.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_010_REVIEWED_EXPANSION_SLICE.md"
OFFICIAL_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-010-reviewed-expansion-slice" / "result.json"
OFFICIAL_REPORT = ROOT / "research" / "experiments" / "generated" / "RAG-010-reviewed-expansion-slice" / "report.md"
TMP_DIR = ROOT / ".tmp" / "rag-010-validation"
EXPECTED_ID = "RAG-010-reviewed-expansion-slice"
EXPECTED_CHUNK_IDS = {
    "rag005-chunk-029",
    "rag005-chunk-030",
    "rag005-chunk-031",
    "rag005-chunk-036",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def fixture_candidate(
    chunk_id: str,
    source_id: str,
    principle: str,
    application: str,
    *,
    voice_or_prosody_advisory_only: bool = False,
) -> dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "source_title": f"Fixture source {source_id}",
        "source_ids": [source_id],
        "topic_ids": ["consultative_selling_discovery"],
        "original_topic_id": "consultative_selling_discovery",
        "principle": principle,
        "application": application,
        "when_not_to_use": "Do not use when the customer has refused or when facts are unknown.",
        "review_flags": ["human_review_required"],
        "rag006_locations": [],
        "quote_dependency_present": False,
        "quoted_text_copied": False,
        "status": "candidate_next_manual_review",
        "status_reasons": ["clean_candidate_for_manual_review"],
        "voice_or_prosody_advisory_only": voice_or_prosody_advisory_only,
        "runtime_use_allowed": False,
        "retrieval_used_in_runtime": False,
    }


def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [
        fixture_candidate(
            "rag005-chunk-029",
            "rag004-source-007",
            "Level 3 Executive Problem",
            "Move from operational issue to business consequence without exaggerating risk.",
        ),
        fixture_candidate(
            "rag005-chunk-030",
            "rag004-source-072",
            "So What Gap",
            "Ask one respectful impact question after the customer describes a problem.",
        ),
        fixture_candidate(
            "rag005-chunk-031",
            "rag004-source-074",
            "Deadline Qualification",
            "Ask about real timing without manufacturing urgency.",
        ),
        fixture_candidate(
            "rag005-chunk-036",
            "rag004-source-073",
            "Cadence Detection",
            "Use buyer speech pace only as weak delivery context.",
            voice_or_prosody_advisory_only=True,
        ),
    ]
    compact_candidates = [
        {
            "chunk_id": candidate["chunk_id"],
            "source_ids": candidate["source_ids"],
            "topic_ids": candidate["topic_ids"],
            "principle": candidate["principle"],
            "application": candidate["application"],
            "voice_or_prosody_advisory_only": candidate["voice_or_prosody_advisory_only"],
            "runtime_use_allowed": False,
        }
        for candidate in candidates
    ]
    rag009 = {
        "review_coverage_id": "RAG-009-all-source-review-coverage",
        "summary": {
            "source_count": 4,
            "chunk_candidate_count": 4,
            "next_promotion_candidate_count": 4,
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
        "next_promotion_candidates": compact_candidates,
        "chunk_coverage": candidates,
    }
    case = {
        "reviewed_expansion_slice_id": EXPECTED_ID,
        "selected_chunk_ids": sorted(EXPECTED_CHUNK_IDS),
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "auto_promotion_enabled": False,
    }
    paths = {
        "rag009": TMP_DIR / "rag009-result.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    paths["rag009"].write_text(json.dumps(rag009, indent=2), encoding="utf-8")
    paths["case"].write_text(json.dumps(case, indent=2), encoding="utf-8")
    return paths


def load_module() -> Any:
    assert_condition(MODULE.exists(), "RAG-010 reviewed expansion slice module is missing.")
    spec = importlib.util.spec_from_file_location("rag_reviewed_expansion_slice", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load RAG-010 module spec.")
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
        assert_condition(term.lower() not in lowered, f"Forbidden RAG-010 text found: {term}")


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("reviewed_expansion_slice_id") == EXPECTED_ID, "Unexpected RAG-010 ID.")
    summary = payload.get("summary", {})
    assert_condition(summary.get("selected_chunk_count") == 4, summary)
    assert_condition(summary.get("knowledge_item_count") == 4, summary)
    assert_condition(summary.get("lane_counts", {}).get("response_wording") == 3, summary)
    assert_condition(summary.get("lane_counts", {}).get("voice_delivery") == 1, summary)
    assert_condition(summary.get("rejected_candidate_count") == 0, summary)
    assert_condition(summary.get("auto_promoted_chunk_count") == 0, summary)
    for key in (
        "runtime_retrieval_enabled",
        "retrieval_eligible_now",
        "chunk_import_enabled",
        "source_excerpt_text_stored",
        "external_provider_calls_made",
        "notebooklm_api_used",
        "private_customer_data_used",
    ):
        assert_condition(summary.get(key) is False, {key: summary.get(key)})

    items = payload.get("knowledge_items", [])
    assert_condition(len(items) == 4, items)
    chunk_ids = {item["source_chunk_ids"][0] for item in items}
    assert_condition(chunk_ids == EXPECTED_CHUNK_IDS, chunk_ids)
    knowledge_ids = {item["knowledge_id"] for item in items}
    assert_condition(len(knowledge_ids) == 4, knowledge_ids)
    assert_condition(
        "rag010-voice-cadence-as-weak-context" in knowledge_ids,
        knowledge_ids,
    )
    for item in items:
        assert_condition(item["review_verdict"] == "manual_expansion_slice_paraphrased", item)
        assert_condition(item["runtime_eligible_now"] is False, item)
        assert_condition(item["retrieval_eligible_now"] is False, item)
        assert_condition(item["manual_review_clearance"]["runtime_use_allowed"] is False, item)
        assert_condition(item["manual_review_clearance"]["source_excerpt_text_copied"] is False, item)
        assert_condition(item["quote_dependency_resolved"] is True, item)
        assert_condition("project_rule" in item and item["project_rule"], item)
        assert_condition("safe_application" in item and item["safe_application"], item)
        assert_condition("do_not_use_when" in item and item["do_not_use_when"], item)
        assert_condition("guardrail_notes" in item and item["guardrail_notes"], item)
        assert_condition("source_excerpt" not in item, item)
        assert_condition("source_excerpt_text" not in item, item)
        if item["knowledge_id"] == "rag010-voice-cadence-as-weak-context":
            assert_condition(item["lane"] == "voice_delivery", item)
            assert_condition(item["voice_or_prosody_advisory_only"] is True, item)
            combined = " ".join(
                str(item[key])
                for key in ("project_rule", "safe_application", "do_not_use_when", "guardrail_notes")
            ).lower()
            assert_condition("hidden emotion" in combined, item)
            assert_condition("weak" in combined, item)

    assert_no_forbidden_text(json.dumps(payload, ensure_ascii=False).lower())


def validate_module_contract() -> None:
    module = load_module()
    assert_condition(
        module.RAG_REVIEWED_EXPANSION_SLICE_ID == EXPECTED_ID,
        "Unexpected RAG-010 module ID.",
    )
    assert_condition(hasattr(module, "build_reviewed_expansion_slice"), "Missing builder function.")
    assert_condition(hasattr(module, "render_reviewed_expansion_slice_report"), "Missing report renderer.")
    paths = write_fixture_inputs()
    payload = module.build_reviewed_expansion_slice(paths["rag009"], paths["case"], root=ROOT)
    validate_payload(payload)
    report = module.render_reviewed_expansion_slice_report(payload)
    assert_condition("RAG-010 Reviewed Expansion Slice" in report, report[:200])
    assert_condition("Runtime retrieval remains disabled" in report, report[:400])
    assert_condition("rag010-response-impact-bridge" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-010 reviewed expansion slice runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-010 reviewed expansion slice case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-010 reviewed expansion slice product doc is missing.")
    paths = write_fixture_inputs()
    command = [
        sys.executable,
        str(RUNNER),
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
    validate_payload(json.loads(paths["result"].read_text(encoding="utf-8")))
    report_text = paths["report"].read_text(encoding="utf-8")
    assert_condition("RAG-010 Reviewed Expansion Slice" in report_text, report_text[:200])
    assert_no_forbidden_text(paths["result"].read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(report_text.lower())
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    assert_condition("Runtime retrieval remains disabled" in doc_text, doc_text[:400])
    assert_condition("rag005-chunk-036" in doc_text, "Product doc should mention cadence candidate.")


def validate_official_artifacts_if_present() -> None:
    if not OFFICIAL_RESULT.exists() and not OFFICIAL_REPORT.exists():
        return
    assert_condition(OFFICIAL_RESULT.exists(), "Official RAG-010 result is missing.")
    assert_condition(OFFICIAL_REPORT.exists(), "Official RAG-010 report is missing.")
    validate_payload(json.loads(OFFICIAL_RESULT.read_text(encoding="utf-8")))
    assert_no_forbidden_text(OFFICIAL_RESULT.read_text(encoding="utf-8").lower())
    assert_no_forbidden_text(OFFICIAL_REPORT.read_text(encoding="utf-8").lower())


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    validate_official_artifacts_if_present()
    print("RAG-010 reviewed expansion slice validation passed.")


if __name__ == "__main__":
    main()
