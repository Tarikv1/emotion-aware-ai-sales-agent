#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_composer_hook_test.py"
RUNNER = ROOT / "scripts" / "run_prod_018_callcenteren_composer_hook_test.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_018_CALLCENTEREN_COMPOSER_HOOK_TEST.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
TMP_DIR = ROOT / ".tmp" / "prod-018-callcenteren-composer-hook-test"
SOURCE_RESULT = TMP_DIR / "prod-015-result-fixture.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-018-callcenteren-composer-hook-test"
EXPECTED_SOURCE_ID = "PROD-015-callcenteren-runtime-comparison"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def make_row(
    index: int,
    *,
    scenario_label: str,
    expected_outcome: str,
    customer_question: str,
    requirements: list[str],
    old_answer: str,
    retrieval_answer: str,
    retrieval_status: str = "retrieved_not_used",
    retrieval_used: bool = False,
) -> dict[str, Any]:
    return {
        "turn_id": f"fixture-composer-hook-{index:03d}::turn-001",
        "scenario_id": f"fixture-composer-hook-{index:03d}",
        "scenario_label": scenario_label,
        "domain": "software" if index % 2 else "telecom",
        "expected_outcome": expected_outcome,
        "customer_question": customer_question,
        "expected_agent_response_requirements": requirements,
        "avoid": ["vague_claim", "talks_too_much", "premature_close"],
        "old_runtime_answer": old_answer,
        "retrieval_runtime_answer": retrieval_answer,
        "old_runtime_score": 4,
        "retrieval_runtime_score": 4,
        "score_delta": 0,
        "winner": "tie",
        "retrieval_status": retrieval_status,
        "retrieval_used_in_runtime": retrieval_used,
        "retrieved_item_ids": ["rag019-objection-diagnose-before-answering"],
        "retrieval_elapsed_ms": 2,
        "retrieval_target_ms": 150,
        "retrieval_acceptable_ms": 300,
        "hard_failure": False,
        "contains_payment_collection": False,
        "decision_trace": {
            "retrieval_runtime": {
                "retrieval_status": retrieval_status,
                "retrieval_used_in_runtime": retrieval_used,
                "retrieved_item_ids": ["rag019-objection-diagnose-before-answering"],
                "advisory_hints": [
                    {
                        "item_id": "rag019-objection-diagnose-before-answering",
                        "lane": "response_wording",
                        "hint": "Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.",
                        "match_score": 4,
                    }
                ],
                "final_response": retrieval_answer,
            }
        },
    }


def write_fixture_prod_015_result() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    generic = "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
    rows = [
        make_row(
            1,
            scenario_label="price_objection",
            expected_outcome="non_sale_correct",
            customer_question="Customer raises `too_expensive` and needs a `timeline_question` before any close.",
            requirements=[
                "separate price concern from value, timing, and contract concerns",
                "use cost or value framing only if campaign facts support it",
            ],
            old_answer=generic,
            retrieval_answer=generic,
        ),
        make_row(
            2,
            scenario_label="support_handoff",
            expected_outcome="human_handoff",
            customer_question="I need a human specialist because my service issue is unresolved.",
            requirements=[
                "prioritize issue resolution before sales",
                "route or hand off instead of guessing",
                "avoid unsupported troubleshooting or product claims",
            ],
            old_answer=generic,
            retrieval_answer=generic,
        ),
        make_row(
            3,
            scenario_label="cancellation_boundary",
            expected_outcome="end_call",
            customer_question="No thanks, I am not interested and I do not want a sales push.",
            requirements=[
                "stop selling until the boundary or cancellation reason is understood",
                "confirm whether the customer wants no further sales discussion",
                "avoid pressure, scarcity, or retention claims",
            ],
            old_answer=generic,
            retrieval_answer=generic,
        ),
        make_row(
            4,
            scenario_label="sale_eligible",
            expected_outcome="sale_ready",
            customer_question="I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.",
            requirements=[
                "acknowledge the customer's stated state without labeling their emotion as fact",
                "ask one focused discovery or clarification question before any close attempt",
                "avoid vague_claim, talks_too_much, premature_close",
            ],
            old_answer=generic,
            retrieval_answer="That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?",
            retrieval_status="influenced",
            retrieval_used=True,
        ),
    ]
    payload = {
        "prod_015_id": EXPECTED_SOURCE_ID,
        "title": "PROD-015 CallCenterEN runtime comparison",
        "runtime_comparison": {
            "baseline_name": "old_runtime_retrieval_disabled",
            "candidate_name": "retrieval_runtime_rag_018_enabled",
            "campaign_id": "campaign-prod-005-b2b-software",
            "stratified_slice": True,
        },
        "summary": {
            "evaluated_scenario_count": 4,
            "evaluated_turn_count": len(rows),
            "hard_failure_count": 0,
            "leakage_finding_count": 0,
            "old_runtime_total_score": 16,
            "retrieval_runtime_total_score": 16,
            "retrieval_turn_wins": 0,
            "old_runtime_turn_wins": 0,
            "tie_turns": len(rows),
            "provider_calls_made": False,
            "llm_used": False,
            "runtime_behavior_changed": False,
            "runtime_retrieval_default_enabled": False,
        },
        "turn_results": rows,
        "decision": "ready_for_review_no_retrieval_gain_on_slice",
    }
    SOURCE_RESULT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_018_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_prod_015_result"]["prod_015_id"] == EXPECTED_SOURCE_ID, payload["source_prod_015_result"])
    assert_condition(payload["hypothesis"]["fixed_cases"] == "unchanged PROD-015 turn_results", payload["hypothesis"])
    assert_condition(payload["hypothesis"]["editable_surface_changed"] == "offline_composer_hook_only", payload["hypothesis"])

    hook_ids = {item["hook_id"] for item in payload["hook_set"]}
    for required in [
        "price_objection_clarifier",
        "support_handoff_router",
        "cancellation_boundary_stop",
        "callback_request_low_commitment",
        "trust_repair_verification",
        "sale_eligible_fit_check",
    ]:
        assert_condition(required in hook_ids, hook_ids)

    summary = payload["summary"]
    assert_condition(summary["analyzed_turn_count"] == 4, summary)
    assert_condition(summary["eligible_hook_turn_count"] == 3, summary)
    assert_condition(summary["hooked_answer_count"] == 3, summary)
    assert_condition(summary["preserved_existing_influenced_count"] == 1, summary)
    assert_condition(summary["hooked_total_score"] > summary["current_retrieval_total_score"], summary)
    assert_condition(summary["hooked_wins_vs_current"] == 3, summary)
    assert_condition(summary["hooked_wins_vs_old"] == 4, summary)
    assert_condition(summary["hooked_old_wins"] == 0, summary)
    assert_condition(summary["hooked_ties_vs_old"] == 0, summary)
    assert_condition(summary["safety_gate_pass_count"] == 4, summary)
    assert_condition(summary["payment_collection_count"] == 0, summary)
    assert_condition(summary["non_sale_correctness"] == 1.0, summary)
    assert_condition(summary["safe_close_correctness"] == 1.0, summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["runtime_retrieval_default_enabled"] is False, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["prod_018_gate_passed"] is True, summary)

    rows = payload["turn_results"]
    assert_condition(len(rows) == 4, rows)
    for row in rows:
        assert_condition(row["hooked_score"]["safety_gate"] == 1, row)
        assert_condition(row["contains_payment_collection"] is False, row)
        assert_condition(row["hooked_answer"], row)

    price = [row for row in rows if row["scenario_label"] == "price_objection"][0]
    assert_condition(price["hook_applied"] is True, price)
    assert_condition("cost" in price["hooked_answer"].lower() or "price" in price["hooked_answer"].lower(), price)
    assert_condition(price["hooked_winner_vs_current"] == "hooked", price)

    support = [row for row in rows if row["scenario_label"] == "support_handoff"][0]
    assert_condition("route" in support["hooked_answer"].lower() and "specialist" in support["hooked_answer"].lower(), support)

    cancellation = [row for row in rows if row["scenario_label"] == "cancellation_boundary"][0]
    assert_condition("stop" in cancellation["hooked_answer"].lower() and "sales" in cancellation["hooked_answer"].lower(), cancellation)

    preserved = [row for row in rows if row["scenario_label"] == "sale_eligible"][0]
    assert_condition(preserved["hook_applied"] is False, preserved)
    assert_condition(preserved["preserved_existing_influenced"] is True, preserved)

    assert_condition(payload["decision"] == "keep_composer_hooks_for_runtime_candidate_not_default", payload["decision"])
    assert_condition(payload["boundaries"]["runtime_behavior_changed"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["provider_calls_made"] is False, payload["boundaries"])

    for required in [
        "PROD-018 CallCenterEN Composer Hook Test",
        "offline composer hook only",
        "hooked wins vs current",
        "price objection clarifier",
        "support handoff router",
        "cancellation boundary stop",
        "keep composer hooks for runtime candidate not default",
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
        (MODULE, "PROD-018 module"),
        (RUNNER, "PROD-018 runner"),
        (DOC_PATH, "PROD-018 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_018_callcenteren_composer_hook_test.py" in commands, "PROD-018 runner missing from command map.")
    assert_condition("validate_prod_018_callcenteren_composer_hook_test.py" in commands, "PROD-018 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_018_CALLCENTEREN_COMPOSER_HOOK_TEST.md" in checkpoint_index, "PROD-018 missing from checkpoint index.")

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
    print("PROD-018 CallCenterEN composer hook test validation passed.")


if __name__ == "__main__":
    main()
