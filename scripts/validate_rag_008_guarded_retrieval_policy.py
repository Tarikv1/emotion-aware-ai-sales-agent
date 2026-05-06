#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_guarded_retrieval_policy.py"
RUNNER = ROOT / "scripts" / "run_rag_008_guarded_retrieval_policy.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-008-guarded-retrieval-policy.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_008_GUARDED_RETRIEVAL_POLICY.md"
TMP_DIR = ROOT / ".tmp" / "rag-008-validation"
TMP_RAG007 = TMP_DIR / "rag007-result.json"
TMP_CASE = TMP_DIR / "case.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"
EXPECTED_ID = "RAG-008-guarded-retrieval-policy"
EXPECTED_RAG007_ID = "RAG-007-reviewed-first-slice"
EXPECTED_KNOWLEDGE_IDS = {
    "rag007-response-yes-and-objection-framing",
    "rag007-response-declarative-clarity",
    "rag007-response-empathy-echo",
    "rag007-response-prep-structure",
    "rag007-response-3-2-1-structure",
    "rag007-voice-yes-and-posture",
    "rag007-voice-tone-mismatch-uncertainty",
    "rag007-voice-trustworthy-not-forced-friendly",
    "rag007-voice-bounded-vocal-toolbox",
}
BLOCKED_CASE_IDS = {
    "customer_refusal_blocks",
    "protected_script_blocks",
    "human_escalation_blocks",
    "pressure_sensitive_blocks",
    "private_data_request_blocks",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def reviewed_item(
    knowledge_id: str,
    lane: str,
    source_chunk_id: str,
    source_id: str,
    project_rule: str,
    safe_application: str,
    do_not_use_when: str,
    guardrail_notes: str,
) -> dict[str, Any]:
    return {
        "knowledge_id": knowledge_id,
        "lane": lane,
        "source_chunk_ids": [source_chunk_id],
        "source_ids": [source_id],
        "source_titles": [f"Reviewed source {source_id}"],
        "source_metadata": {
            source_id: {
                "source_id": source_id,
                "canonical_title": f"Reviewed source {source_id}",
                "metadata_status": "needs_human_review",
                "rights_status": "needs_review",
            }
        },
        "topic_ids": [lane],
        "review_verdict": "manual_first_slice_paraphrased",
        "quote_dependency_resolved": True,
        "manual_review_clearance": {
            "selected_from_first_slice_candidates": True,
            "selected_from_quote_queue": True,
            "quote_clearance_required": True,
            "quote_clearance_resolution": "project_owned_paraphrase_no_source_excerpt_text",
            "source_excerpt_text_copied": False,
            "runtime_use_allowed": False,
        },
        "project_rule": project_rule,
        "safe_application": safe_application,
        "do_not_use_when": do_not_use_when,
        "guardrail_notes": guardrail_notes,
        "rag006_locations": ["quote_review_queue"],
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
    }


def write_fixture_inputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    knowledge_items = [
        reviewed_item(
            "rag007-response-yes-and-objection-framing",
            "response_wording",
            "rag005-chunk-017",
            "rag004-source-086",
            "Acknowledge the customer's price or timing concern before moving to a useful next step.",
            "Use for ordinary objections about price, timing, complexity, or uncertainty.",
            "Do not use for refusals, do-not-call requests, or false compliance claims.",
            "Compliance language, refusal handling, and campaign facts override this rule.",
        ),
        reviewed_item(
            "rag007-response-declarative-clarity",
            "response_wording",
            "rag005-chunk-020",
            "rag004-source-016",
            "Use short declarative statements when clarity matters.",
            "Use to reduce rambling in explanations and next-step summaries.",
            "Do not make the agent clipped, dismissive, or aggressive.",
            "This shapes freeform wording only and cannot shorten required disclosures.",
        ),
        reviewed_item(
            "rag007-response-empathy-echo",
            "response_wording",
            "rag005-chunk-022",
            "rag004-source-002",
            "Reflect a customer's concern sparingly before responding.",
            "Use when the customer expresses frustration, confusion, or hesitation.",
            "Do not repeat profanity, private details, or every phrase.",
            "The echo is not an emotion diagnosis and cannot override explicit intent.",
        ),
        reviewed_item(
            "rag007-response-prep-structure",
            "response_wording",
            "rag005-chunk-024",
            "rag004-source-013",
            "For a persuasive explanation, state the point, reason, example, and point.",
            "Use for medium-length answers that need a reason and concrete example.",
            "Do not use for simple yes/no answers or urgent refusal handling.",
            "Examples must be campaign-approved and truthful.",
        ),
        reviewed_item(
            "rag007-response-3-2-1-structure",
            "response_wording",
            "rag005-chunk-025",
            "rag004-source-032",
            "Constrain broad answers into three points, two options, or one takeaway.",
            "Use when a broad question could sprawl and needs a concise structure.",
            "Do not use when numbering would sound evasive.",
            "Numbering cannot remove mandatory disclosures or escalation language.",
        ),
        reviewed_item(
            "rag007-voice-yes-and-posture",
            "voice_delivery",
            "rag005-chunk-091",
            "rag004-source-087",
            "Use a non-defensive delivery posture when acknowledging objections.",
            "Use for ordinary resistance where the agent can acknowledge and continue.",
            "Do not sound agreeable when correcting false claims or honoring refusal.",
            "Delivery guidance only; it does not change guarded text.",
        ),
        reviewed_item(
            "rag007-voice-tone-mismatch-uncertainty",
            "voice_delivery",
            "rag005-chunk-098",
            "rag004-source-063",
            "If words and vocal delivery appear misaligned, treat that as uncertainty and ask a gentle clarification.",
            "Use when a customer sounds hesitant, strained, or unsure and clarification reduces pressure.",
            "Do not override consent, refusal, factual statements, compliance, or stated preferences.",
            "Tone is only a weak signal; never claim hidden emotion certainty.",
        ),
        reviewed_item(
            "rag007-voice-trustworthy-not-forced-friendly",
            "voice_delivery",
            "rag005-chunk-099",
            "rag004-source-085",
            "Prefer trustworthy, straightforward, moderately warm delivery over forced friendliness.",
            "Use as a default delivery target across B2B and B2C sales campaigns.",
            "Do not use exaggerated cheer or overfamiliar phrasing in serious contexts.",
            "Campaign persona can adjust warmth, but trust and clarity remain default.",
        ),
        reviewed_item(
            "rag007-voice-bounded-vocal-toolbox",
            "voice_delivery",
            "rag005-chunk-101",
            "rag004-source-042",
            "Use controlled pace, pitch, volume, warmth, and silence to support clarity.",
            "Use for TTS delivery metadata and human-review rubrics for freeform responses.",
            "Do not imitate a source speaker identity, accent, or theatrical performance.",
            "Protected scripts and compliance text must stay exact.",
        ),
    ]
    rag007 = {
        "reviewed_slice_id": EXPECTED_RAG007_ID,
        "summary": {
            "knowledge_item_count": len(knowledge_items),
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
            "private_customer_data_used": False,
        },
        "knowledge_items": knowledge_items,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "retrieval_eligible_now": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
        },
    }
    cases = {
        "retrieval_policy_id": EXPECTED_ID,
        "title": "Guarded retrieval policy dry-run cases",
        "runtime_retrieval_enabled": False,
        "retrieval_used_in_runtime": False,
        "chunk_import_enabled": False,
        "max_results": 3,
        "query_cases": [
            {
                "case_id": "ordinary_objection_yes_and",
                "query": "The customer is worried about price and timing. Acknowledge the concern and continue without pressure.",
                "lane_filter": "response_wording",
                "context_flags": ["ordinary_objection"],
                "expected_behavior": "retrieve",
                "expected_knowledge_ids": ["rag007-response-yes-and-objection-framing"],
            },
            {
                "case_id": "broad_question_structure",
                "query": "The customer asks for a broad explanation. Keep it concise with three points, two options, or a point reason example.",
                "lane_filter": "response_wording",
                "context_flags": ["broad_question"],
                "expected_behavior": "retrieve",
                "expected_knowledge_ids": [
                    "rag007-response-3-2-1-structure",
                    "rag007-response-prep-structure",
                ],
            },
            {
                "case_id": "tone_uncertainty_clarification",
                "query": "The customer says sure but sounds hesitant and uncertain. Use a gentle clarification.",
                "lane_filter": "voice_delivery",
                "context_flags": ["tone_uncertainty"],
                "expected_behavior": "retrieve",
                "expected_knowledge_ids": ["rag007-voice-tone-mismatch-uncertainty"],
            },
            {
                "case_id": "customer_refusal_blocks",
                "query": "The customer says no and asks us to stop calling.",
                "lane_filter": "any",
                "context_flags": ["customer_refusal", "do_not_call"],
                "expected_behavior": "block",
            },
            {
                "case_id": "protected_script_blocks",
                "query": "The next sentence is a required disclosure and protected campaign script.",
                "lane_filter": "any",
                "context_flags": ["protected_script", "required_disclosure"],
                "expected_behavior": "block",
            },
            {
                "case_id": "human_escalation_blocks",
                "query": "The customer asks for a human manager.",
                "lane_filter": "any",
                "context_flags": ["human_escalation"],
                "expected_behavior": "block",
            },
            {
                "case_id": "pressure_sensitive_blocks",
                "query": "The agent wants urgency language to push the customer past hesitation.",
                "lane_filter": "any",
                "context_flags": ["pressure_sensitive"],
                "expected_behavior": "block",
            },
            {
                "case_id": "private_data_request_blocks",
                "query": "Retrieve guidance from data/private customer recordings.",
                "lane_filter": "any",
                "context_flags": ["private_data_requested"],
                "expected_behavior": "block",
            },
        ],
    }
    TMP_RAG007.write_text(json.dumps(rag007, indent=2), encoding="utf-8")
    TMP_CASE.write_text(json.dumps(cases, indent=2), encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], report: str) -> None:
    summary = payload["summary"]
    boundaries = payload["boundaries"]
    case_results = payload["case_results"]
    combined_text = json.dumps(payload, sort_keys=True) + "\n" + report

    assert_condition(payload["retrieval_policy_id"] == EXPECTED_ID, payload)
    assert_condition(payload["inputs"]["rag007_reviewed_slice_id"] == EXPECTED_RAG007_ID, payload["inputs"])
    assert_condition(summary["query_case_count"] == 8, summary)
    assert_condition(summary["retrieval_case_count"] == 3, summary)
    assert_condition(summary["blocked_case_count"] == 5, summary)
    assert_condition(summary["retrieved_item_count"] >= 3, summary)
    assert_condition(summary["runtime_retrieval_enabled"] is False, summary)
    assert_condition(summary["retrieval_used_in_runtime"] is False, summary)
    assert_condition(summary["chunk_import_enabled"] is False, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["notebooklm_api_used"] is False, summary)
    assert_condition(summary["private_customer_data_used"] is False, summary)
    assert_condition(summary["reads_data_private"] is False, summary)
    assert_condition(summary["source_excerpt_text_stored"] is False, summary)
    assert_condition(summary["only_reviewed_rag007_used"] is True, summary)
    assert_condition(boundaries["runtime_retrieval_enabled"] is False, boundaries)
    assert_condition(boundaries["retrieval_used_in_runtime"] is False, boundaries)
    assert_condition(boundaries["chunk_import_enabled"] is False, boundaries)
    assert_condition(boundaries["auto_promote_allowed"] is False, boundaries)
    assert_condition(boundaries["source_excerpt_text_stored"] is False, boundaries)
    assert_condition(boundaries["provider_calls_allowed"] is False, boundaries)
    assert_condition(boundaries["notebooklm_api_allowed"] is False, boundaries)
    assert_condition(boundaries["private_customer_data_allowed"] is False, boundaries)
    assert_condition(boundaries["reads_data_private"] is False, boundaries)
    assert_condition(boundaries["only_reviewed_rag007_used"] is True, boundaries)

    assert_condition('"source_excerpt_text":' not in combined_text, combined_text)
    assert_condition("data/private" not in combined_text.replace("\\", "/"), combined_text)
    assert_condition("insurance" not in combined_text.lower(), combined_text)

    results_by_id = {case["case_id"]: case for case in case_results}
    assert_condition(set(results_by_id) == {
        "ordinary_objection_yes_and",
        "broad_question_structure",
        "tone_uncertainty_clarification",
        "customer_refusal_blocks",
        "protected_script_blocks",
        "human_escalation_blocks",
        "pressure_sensitive_blocks",
        "private_data_request_blocks",
    }, sorted(results_by_id))

    for case_id in BLOCKED_CASE_IDS:
        case = results_by_id[case_id]
        assert_condition(case["retrieval_decision"] == "blocked", case)
        assert_condition(case["retrieved_items"] == [], case)
        assert_condition(isinstance(case.get("block_reason"), str) and case["block_reason"], case)

    ordinary = results_by_id["ordinary_objection_yes_and"]
    ordinary_ids = {item["knowledge_id"] for item in ordinary["retrieved_items"]}
    assert_condition("rag007-response-yes-and-objection-framing" in ordinary_ids, ordinary)

    broad = results_by_id["broad_question_structure"]
    broad_ids = {item["knowledge_id"] for item in broad["retrieved_items"]}
    assert_condition("rag007-response-3-2-1-structure" in broad_ids, broad)
    assert_condition("rag007-response-prep-structure" in broad_ids, broad)

    tone = results_by_id["tone_uncertainty_clarification"]
    tone_ids = {item["knowledge_id"] for item in tone["retrieved_items"]}
    assert_condition(tone_ids == {"rag007-voice-tone-mismatch-uncertainty"}, tone)
    tone_text = json.dumps(tone).lower()
    assert_condition("weak signal" in tone_text, tone)
    assert_condition("emotion certainty" in tone_text, tone)
    assert_condition("advisory" in tone_text, tone)

    for case in case_results:
        for item in case["retrieved_items"]:
            assert_condition(item["knowledge_id"] in EXPECTED_KNOWLEDGE_IDS, item)
            assert_condition(item["runtime_use_allowed"] is False, item)
            assert_condition(item["retrieval_used_in_runtime"] is False, item)
            assert_condition(item["source_ids"], item)
            assert_condition(item["source_chunk_ids"], item)
            assert_condition(item["citation_trace"], item)
            assert_condition(item["match_reasons"], item)
            assert_condition("source_excerpt" not in json.dumps(item).lower(), item)

    report_text = report.lower()
    assert_condition("runtime retrieval remains disabled" in report_text, report)
    assert_condition("blocked cases" in report_text, report)
    assert_condition("retrieved cases" in report_text, report)


def validate_module_contract() -> None:
    assert_condition(MODULE.exists(), "RAG-008 guarded retrieval policy module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_guarded_retrieval_policy import (  # noqa: PLC0415
        RAG_GUARDED_RETRIEVAL_POLICY_ID,
        build_guarded_retrieval_policy,
        render_guarded_retrieval_policy_report,
    )

    assert_condition(RAG_GUARDED_RETRIEVAL_POLICY_ID == EXPECTED_ID, RAG_GUARDED_RETRIEVAL_POLICY_ID)
    write_fixture_inputs()
    payload = build_guarded_retrieval_policy(TMP_RAG007, TMP_CASE, root=ROOT)
    report = render_guarded_retrieval_policy_report(payload)
    validate_payload(payload, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-008 guarded retrieval policy runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-008 guarded retrieval policy case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-008 guarded retrieval policy product doc is missing.")
    write_fixture_inputs()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--rag007-result",
            str(TMP_RAG007),
            "--case",
            str(TMP_CASE),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-008 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-008 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-008 guarded retrieval policy validation passed.")


if __name__ == "__main__":
    main()
