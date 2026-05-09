#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_HOOKS = ROOT / "scripts" / "runtime_composer_hooks.py"
MODULE = ROOT / "scripts" / "prod_019_guarded_runtime_composer_hooks.py"
RUNNER = ROOT / "scripts" / "run_prod_019_guarded_runtime_composer_hooks.py"
GUARDED_RESPONSE = ROOT / "scripts" / "generate_guarded_response.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_019_GUARDED_RUNTIME_COMPOSER_HOOKS.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
TMP_DIR = ROOT / ".tmp" / "prod-019-guarded-runtime-composer-hooks"
SOURCE_RESULT = TMP_DIR / "prod-015-result-fixture.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-019-guarded-runtime-composer-hooks"
EXPECTED_SOURCE_ID = "PROD-015-callcenteren-runtime-comparison"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert_condition(completed.returncode == 0, completed.stderr)
    return json.loads(completed.stdout)


def make_row(
    index: int,
    *,
    scenario_label: str,
    expected_outcome: str,
    stage: str,
    customer_question: str,
    requirements: list[str],
    retrieval_answer: str,
    retrieval_status: str = "retrieved_not_used",
    retrieval_used: bool = False,
) -> dict[str, Any]:
    generic = "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
    return {
        "turn_id": f"fixture-runtime-hook-{index:03d}::turn-001",
        "scenario_id": f"fixture-runtime-hook-{index:03d}",
        "scenario_label": scenario_label,
        "domain": "software",
        "stage": stage,
        "campaign_id": "campaign-prod-005-b2b-software",
        "expected_outcome": expected_outcome,
        "customer_question": customer_question,
        "expected_agent_response_requirements": requirements,
        "avoid": ["vague_claim", "talks_too_much", "premature_close"],
        "old_runtime_answer": generic,
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
    }


def write_fixture_prod_015_result() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    generic = "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"
    rows = [
        make_row(
            1,
            scenario_label="price_objection",
            expected_outcome="non_sale_correct",
            stage="relevance-check",
            customer_question="Customer raises too_expensive and needs a timeline_question before any close.",
            requirements=[
                "separate price concern from value, timing, and contract concerns",
                "use cost or value framing only if campaign facts support it",
            ],
            retrieval_answer=generic,
        ),
        make_row(
            2,
            scenario_label="callback_request",
            expected_outcome="callback_agreed",
            stage="relevance-check",
            customer_question="I need time to think, so do not rush me into a decision.",
            requirements=[
                "respect time pressure",
                "offer a callback only after stating a clear customer-relevant reason",
            ],
            retrieval_answer=generic,
        ),
        make_row(
            3,
            scenario_label="sale_eligible",
            expected_outcome="sale_ready",
            stage="relevance-check",
            customer_question="I am worried about being locked into something, so clarify the commitment before any close.",
            requirements=[
                "confirm eligibility and fit before a sale-ready close",
                "treat close as verbal commitment only, not payment collection",
            ],
            retrieval_answer=generic,
        ),
        make_row(
            4,
            scenario_label="support_handoff",
            expected_outcome="human_handoff",
            stage="product-detail-check",
            customer_question="I need a human specialist because my service issue is unresolved.",
            requirements=[
                "prioritize issue resolution before sales",
                "route or hand off instead of guessing",
            ],
            retrieval_answer="Of course. I will route this to a solutions specialist instead of continuing automatically.",
            retrieval_status="blocked",
        ),
        make_row(
            5,
            scenario_label="trust_repair",
            expected_outcome="support_only",
            stage="relevance-check",
            customer_question="I do not trust this call. How do I know this is legitimate?",
            requirements=[
                "repair trust with transparency and a low-pressure next step",
                "explain what can and cannot be verified",
            ],
            retrieval_answer="Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?",
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


def validate_cli_flag_behavior() -> None:
    base_args = [
        sys.executable,
        str(GUARDED_RESPONSE),
        "--campaign",
        "campaign-prod-005-b2b-software",
        "--stage",
        "relevance-check",
        "--transcript",
        "Customer raises too_expensive and needs a timeline_question before any close.",
        "--retrieval-enabled",
        "--retrieval-registry",
        "research/experiments/generated/RAG-017-runtime-knowledge-registry/result.json",
        "--retrieval-max-results",
        "4",
        "--retrieval-min-score",
        "1",
    ]
    default_payload = parse_stdout_json(run_command(base_args))
    assert_condition(default_payload["composer_hooks"]["enabled"] is False, default_payload.get("composer_hooks"))
    assert_condition(default_payload["composer_hooks"]["applied"] is False, default_payload.get("composer_hooks"))
    assert_condition(default_payload["retrieval"]["enabled"] is True, default_payload["retrieval"])
    assert_condition(default_payload["retrieval"]["retrieval_used_in_runtime"] is False, default_payload["retrieval"])
    assert_condition(
        default_payload["final_response"]
        == "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?",
        default_payload["final_response"],
    )

    hooked_payload = parse_stdout_json(run_command(base_args + ["--composer-hooks-enabled"]))
    hooks = hooked_payload["composer_hooks"]
    assert_condition(hooks["enabled"] is True, hooks)
    assert_condition(hooks["applied"] is True, hooks)
    assert_condition(hooks["hook_id"] == "price_objection_clarifier", hooks)
    assert_condition(hooks["no_evaluation_labels_used"] is True, hooks)
    assert_condition("transcript_signal" in hooks["hook_basis"], hooks)
    assert_condition("scenario_label" not in json.dumps(hooks).lower(), hooks)
    assert_condition("cost" in hooked_payload["final_response"].lower() or "price" in hooked_payload["final_response"].lower(), hooked_payload["final_response"])
    assert_condition(hooked_payload["final_response"] != default_payload["final_response"], hooked_payload["final_response"])
    assert_condition(hooked_payload["validation"]["passed"] is True, hooked_payload["validation"])

    no_retrieval_payload = parse_stdout_json(
        run_command(
            [
                sys.executable,
                str(GUARDED_RESPONSE),
                "--campaign",
                "campaign-prod-005-b2b-software",
                "--stage",
                "relevance-check",
                "--transcript",
                "Customer raises too_expensive and needs a timeline_question before any close.",
                "--composer-hooks-enabled",
            ]
        )
    )
    assert_condition(no_retrieval_payload["retrieval"]["enabled"] is False, no_retrieval_payload["retrieval"])
    assert_condition(no_retrieval_payload["composer_hooks"]["enabled"] is True, no_retrieval_payload["composer_hooks"])
    assert_condition(no_retrieval_payload["composer_hooks"]["applied"] is False, no_retrieval_payload["composer_hooks"])
    assert_condition(no_retrieval_payload["composer_hooks"]["blocked_reason"] == "retrieval_not_enabled", no_retrieval_payload["composer_hooks"])


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_019_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_prod_015_result"]["prod_015_id"] == EXPECTED_SOURCE_ID, payload["source_prod_015_result"])
    assert_condition(payload["hypothesis"]["fixed_cases"] == "unchanged PROD-015 turn_results", payload["hypothesis"])
    assert_condition(payload["hypothesis"]["editable_surface_changed"] == "guarded_runtime_composer_hook_flag_only", payload["hypothesis"])
    assert_condition(payload["source_prod_018_result"]["prod_018_gate_passed"] in {True, "fixture_not_required"}, payload["source_prod_018_result"])

    summary = payload["summary"]
    assert_condition(summary["analyzed_turn_count"] == 5, summary)
    assert_condition(summary["default_off_answer_drift_count"] == 0, summary)
    assert_condition(summary["opt_in_hooked_answer_count"] == 3, summary)
    assert_condition(summary["hook_applied_without_eval_label_count"] == 3, summary)
    assert_condition(summary["hooked_total_score"] > summary["current_retrieval_total_score"], summary)
    assert_condition(summary["hooked_wins_vs_current"] == 3, summary)
    assert_condition(summary["hooked_current_wins"] == 0, summary)
    assert_condition(summary["safety_gate_pass_count"] == 5, summary)
    assert_condition(summary["payment_collection_count"] == 0, summary)
    assert_condition(summary["non_sale_correctness"] == 1.0, summary)
    assert_condition(summary["safe_close_correctness"] == 1.0, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["llm_used"] is False, summary)
    assert_condition(summary["default_runtime_behavior_changed"] is False, summary)
    assert_condition(summary["runtime_retrieval_default_enabled"] is False, summary)
    assert_condition(summary["composer_hook_flag_default_enabled"] is False, summary)
    assert_condition(summary["prod_019_gate_passed"] is True, summary)

    rows = payload["turn_results"]
    assert_condition(len(rows) == 5, rows)
    for row in rows:
        assert_condition(row["default_off_answer_drift"] is False, row)
        assert_condition(row["hooked_score"]["safety_gate"] == 1, row)
        assert_condition(row["contains_payment_collection"] is False, row)
        assert_condition(row["composer_hooks"]["no_evaluation_labels_used"] is True, row)

    by_label = {row["scenario_label"]: row for row in rows}
    assert_condition(by_label["price_objection"]["composer_hooks"]["hook_id"] == "price_objection_clarifier", by_label["price_objection"])
    assert_condition("cost" in by_label["price_objection"]["hooked_answer"].lower() or "price" in by_label["price_objection"]["hooked_answer"].lower(), by_label["price_objection"])
    assert_condition(by_label["callback_request"]["composer_hooks"]["hook_id"] == "callback_request_low_commitment", by_label["callback_request"])
    assert_condition("callback" in by_label["callback_request"]["hooked_answer"].lower(), by_label["callback_request"])
    assert_condition(by_label["sale_eligible"]["composer_hooks"]["hook_id"] == "sale_eligible_fit_check", by_label["sale_eligible"])
    assert_condition("eligibility" in by_label["sale_eligible"]["hooked_answer"].lower(), by_label["sale_eligible"])
    assert_condition(by_label["support_handoff"]["composer_hooks"]["applied"] is False, by_label["support_handoff"])
    assert_condition(by_label["support_handoff"]["composer_hooks"]["protected_context_preserved"] is True, by_label["support_handoff"])
    assert_condition(by_label["trust_repair"]["composer_hooks"]["applied"] is False, by_label["trust_repair"])
    assert_condition(by_label["trust_repair"]["preserved_existing_influenced"] is True, by_label["trust_repair"])

    assert_condition(payload["decision"] == "keep_runtime_composer_hooks_opt_in_candidate_not_default", payload["decision"])
    assert_condition(payload["boundaries"]["runtime_retrieval_default_enabled"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["composer_hook_flag_default_enabled"] is False, payload["boundaries"])
    assert_condition(payload["boundaries"]["commercial_runtime_prompt_text_from_callcenteren_allowed"] is False, payload["boundaries"])

    for required in [
        "PROD-019 Guarded Runtime Composer Hooks",
        "guarded runtime composer hook flag only",
        "opt-in runtime composer hooks",
        "default-off behavior unchanged",
        "hooked wins vs current",
        "keep runtime composer hooks opt-in candidate not default",
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
        (RUNTIME_HOOKS, "runtime composer hook helper"),
        (MODULE, "PROD-019 module"),
        (RUNNER, "PROD-019 runner"),
        (DOC_PATH, "PROD-019 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_019_guarded_runtime_composer_hooks.py" in commands, "PROD-019 runner missing from command map.")
    assert_condition("validate_prod_019_guarded_runtime_composer_hooks.py" in commands, "PROD-019 validator missing from command map.")
    assert_condition("--composer-hooks-enabled" in commands, "Composer hook opt-in flag missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_019_GUARDED_RUNTIME_COMPOSER_HOOKS.md" in checkpoint_index, "PROD-019 missing from checkpoint index.")

    validate_cli_flag_behavior()
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
    print("PROD-019 guarded runtime composer hooks validation passed.")


if __name__ == "__main__":
    main()
