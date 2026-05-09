#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_020_naturalized_customer_turn_evaluation.py"
RUNNER = ROOT / "scripts" / "run_prod_020_naturalized_customer_turn_evaluation.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_020_NATURALIZED_CUSTOMER_TURN_EVALUATION.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
TMP_DIR = ROOT / ".tmp" / "prod-020-naturalized-customer-turn-evaluation"
SOURCE_RESULT = TMP_DIR / "prod-015-result-fixture.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-020-naturalized-customer-turn-evaluation"
EXPECTED_SOURCE_ID = "PROD-015-callcenteren-runtime-comparison"
RUBRIC_TOKENS = [
    "customer raises",
    "customer asks",
    "`",
    "_",
    "too_expensive",
    "timeline_question",
    "usage_question",
    "pain_point_question",
    "needs_to_think",
    "contract_fear",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def make_row(
    index: int,
    *,
    scenario_label: str,
    expected_outcome: str,
    customer_question: str,
    source_pattern_ids: list[str],
    requirements: list[str],
) -> dict[str, Any]:
    generic = "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
    return {
        "turn_id": f"fixture-naturalized-{index:03d}::turn-001",
        "scenario_id": f"fixture-naturalized-{index:03d}",
        "scenario_label": scenario_label,
        "domain": "software",
        "stage": "relevance-check",
        "campaign_id": "campaign-prod-005-b2b-software",
        "customer_question": customer_question,
        "customer_intent": scenario_label,
        "customer_emotion": "neutral",
        "expected_outcome": expected_outcome,
        "expected_agent_response_requirements": requirements,
        "avoid": ["vague_claim", "talks_too_much", "premature_close"],
        "source_pattern_ids": source_pattern_ids,
        "source_pattern_categories": ["objection", "discovery_question", "turn_stage"],
        "old_runtime_answer": generic,
        "retrieval_runtime_answer": generic,
        "old_runtime_score": 4,
        "retrieval_runtime_score": 4,
        "score_delta": 0,
        "winner": "tie",
        "retrieval_status": "retrieved_not_used",
        "retrieval_used_in_runtime": False,
        "retrieved_item_ids": ["rag019-objection-diagnose-before-answering"],
        "retrieval_elapsed_ms": 2,
        "retrieval_target_ms": 150,
        "retrieval_acceptable_ms": 300,
        "hard_failure": False,
        "contains_payment_collection": False,
    }


def write_fixture_prod_015_result() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        make_row(
            1,
            scenario_label="price_objection",
            expected_outcome="non_sale_correct",
            customer_question="Customer raises `too_expensive` and needs a `timeline_question` before any close.",
            source_pattern_ids=["objection-too_expensive-001", "discovery-timeline_question-001"],
            requirements=[
                "separate price concern from value, timing, and contract concerns",
                "use cost or value framing only if campaign facts support it",
            ],
        ),
        make_row(
            2,
            scenario_label="callback_request",
            expected_outcome="callback_agreed",
            customer_question="Customer raises `needs_to_think` and needs a `pain_point_question` before any close.",
            source_pattern_ids=["objection-needs_to_think-001", "discovery-pain_point_question-001"],
            requirements=[
                "respect time pressure",
                "offer a callback only after stating a clear customer-relevant reason",
            ],
        ),
        make_row(
            3,
            scenario_label="sale_eligible",
            expected_outcome="sale_ready",
            customer_question="Customer raises `contract_fear` and needs a `usage_question` before any close.",
            source_pattern_ids=["objection-contract_fear-001", "discovery-usage_question-001"],
            requirements=[
                "confirm eligibility and fit before a sale-ready close",
                "treat close as verbal commitment only, not payment collection",
            ],
        ),
        make_row(
            4,
            scenario_label="trust_repair",
            expected_outcome="support_only",
            customer_question="Customer asks what the next safe step would be.",
            source_pattern_ids=["objection-does_not_trust_agent-001", "persuasion-empathy_first-001"],
            requirements=[
                "repair trust with transparency and a low-pressure next step",
                "explain what can and cannot be verified",
            ],
        ),
        make_row(
            5,
            scenario_label="support_handoff",
            expected_outcome="human_handoff",
            customer_question="I need a human specialist because my service issue is unresolved.",
            source_pattern_ids=["intent-technical_problem-001", "boundary-human_handoff-001"],
            requirements=[
                "prioritize issue resolution before sales",
                "route or hand off instead of guessing",
            ],
        ),
    ]
    payload = {
        "prod_015_id": EXPECTED_SOURCE_ID,
        "title": "PROD-015 CallCenterEN runtime comparison",
        "runtime_comparison": {
            "baseline_name": "old_runtime_retrieval_disabled",
            "candidate_name": "retrieval_runtime_rag_018_enabled",
            "campaign_case_source": "research/experiments/cases/prod-005-realtime-latency-call-control.json",
            "campaign_id": "campaign-prod-005-b2b-software",
        },
        "summary": {
            "evaluated_scenario_count": 5,
            "evaluated_turn_count": len(rows),
            "hard_failure_count": 0,
            "leakage_finding_count": 0,
            "provider_calls_made": False,
            "llm_used": False,
            "runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
        },
        "turn_results": rows,
        "decision": "ready_for_review_no_retrieval_gain_on_slice",
    }
    SOURCE_RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def contains_rubric_token(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in RUBRIC_TOKENS)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_020_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_prod_015_result"]["prod_015_id"] == EXPECTED_SOURCE_ID, payload["source_prod_015_result"])
    assert_condition(payload["source_prod_019_result"]["prod_019_gate_passed"] in {True, "fixture_not_required"}, payload["source_prod_019_result"])
    assert_condition(payload["hypothesis"]["fixed_cases"] == "naturalized PROD-015 turn_results", payload["hypothesis"])
    assert_condition(payload["hypothesis"]["editable_surface_changed"] == "evaluation_customer_turn_wording_only", payload["hypothesis"])
    assert_condition(payload["hypothesis"]["runtime_surface_changed"] == "none", payload["hypothesis"])
    assert_condition(payload["hypothesis"]["scoring_gate"] == "PROD-017 specificity and objection-fit scoring", payload["hypothesis"])

    summary = payload["summary"]
    assert_condition(summary["analyzed_turn_count"] == 5, summary)
    assert_condition(summary["naturalized_turn_count"] == 5, summary)
    assert_condition(summary["source_rubric_like_turn_count"] == 4, summary)
    assert_condition(summary["naturalized_question_changed_count"] == 4, summary)
    assert_condition(summary["naturalized_rubric_token_count"] == 0, summary)
    assert_condition(summary["source_pattern_ref_preserved_count"] == 5, summary)
    assert_condition(summary["expected_outcome_preserved_count"] == 5, summary)
    assert_condition(summary["opt_in_hooked_answer_count"] >= 3, summary)
    assert_condition(summary["hook_applied_without_eval_label_count"] == summary["opt_in_hooked_answer_count"], summary)
    assert_condition(summary["hooked_total_score"] > summary["baseline_total_score"], summary)
    assert_condition(summary["hooked_wins_vs_baseline"] >= 3, summary)
    assert_condition(summary["baseline_wins_vs_hooked"] == 0, summary)
    assert_condition(summary["safety_gate_pass_count"] == 5, summary)
    assert_condition(summary["payment_collection_count"] == 0, summary)
    assert_condition(summary["expected_outcome_correct_count"] == 5, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["llm_used"] is False, summary)
    assert_condition(summary["runtime_retrieval_default_enabled"] is False, summary)
    assert_condition(summary["composer_hook_flag_default_enabled"] is False, summary)
    assert_condition(summary["prod_020_gate_passed"] is True, summary)

    rows = payload["turn_results"]
    assert_condition(len(rows) == 5, rows)
    by_label = {row["scenario_label"]: row for row in rows}
    for row in rows:
        assert_condition("original_customer_question" not in row, row)
        assert_condition(row["source_question_rubric_like"] in {True, False}, row)
        assert_condition(row["naturalized_customer_question"], row)
        assert_condition(contains_rubric_token(row["naturalized_customer_question"]) is False, row["naturalized_customer_question"])
        assert_condition(row["source_pattern_ids_preserved"] is True, row)
        assert_condition(row["expected_outcome_preserved"] is True, row)
        assert_condition(row["composer_hooks"]["no_evaluation_labels_used"] is True, row)
        assert_condition(row["contains_payment_collection"] is False, row)
        assert_condition(row["hooked_score"]["safety_gate"] == 1, row)

    assert_condition(by_label["price_objection"]["composer_hooks"]["hook_id"] == "price_objection_clarifier", by_label["price_objection"])
    assert_condition(by_label["callback_request"]["composer_hooks"]["hook_id"] == "callback_request_low_commitment", by_label["callback_request"])
    assert_condition(by_label["sale_eligible"]["composer_hooks"]["hook_id"] == "sale_eligible_fit_check", by_label["sale_eligible"])
    assert_condition(by_label["trust_repair"]["composer_hooks"]["hook_id"] == "trust_repair_verification", by_label["trust_repair"])
    assert_condition(by_label["support_handoff"]["composer_hooks"]["applied"] is False, by_label["support_handoff"])
    assert_condition(by_label["support_handoff"]["composer_hooks"]["protected_context_preserved"] is True, by_label["support_handoff"])

    assert_condition(payload["decision"] == "keep_naturalized_runtime_hooks_as_opt_in_candidate_not_default", payload["decision"])
    assert_condition(payload["boundaries"]["runtime_retrieval_default_enabled"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["composer_hook_flag_default_enabled"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["scenario_label_passed_to_composer"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["commercial_runtime_prompt_text_from_callcenteren_allowed"] is False, payload["boundaries"])

    for required in [
        "PROD-020 Naturalized Customer-Turn Evaluation",
        "evaluation_customer_turn_wording_only",
        "naturalized customer turns",
        "no rubric tokens in runtime prompts",
        "hooked wins vs baseline",
        "keep naturalized runtime hooks as opt-in candidate not default",
    ]:
        assert_condition(required.lower() in report.lower(), required)

    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")
    for forbidden in [
        '"raw_transcript_text":',
        '"source_excerpt_text":',
        '"transcript":',
        "data/private",
        "data/private-restricted",
        "credit card",
        "take your payment",
        "provider call made",
    ]:
        assert_condition(forbidden not in combined, forbidden)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-020 module"),
        (RUNNER, "PROD-020 runner"),
        (DOC_PATH, "PROD-020 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_020_naturalized_customer_turn_evaluation.py" in commands, "PROD-020 runner missing from command map.")
    assert_condition("validate_prod_020_naturalized_customer_turn_evaluation.py" in commands, "PROD-020 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_020_NATURALIZED_CUSTOMER_TURN_EVALUATION.md" in checkpoint_index, "PROD-020 missing from checkpoint index.")

    write_fixture_prod_015_result()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--prod-015-result",
            str(SOURCE_RESULT),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-020 naturalized customer-turn evaluation validation passed.")


if __name__ == "__main__":
    main()
