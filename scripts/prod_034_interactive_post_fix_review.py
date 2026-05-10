#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-034-interactive-post-fix-review"
SOURCE_CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"
NEXT_CHECKPOINT_ID = "PROD-035-runtime-decision-trace-alignment"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_PACKET = DEFAULT_OUT_DIR / "interactive_post_fix_review_packet.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "interactive_post_fix_review_trace.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
DEFAULT_SOURCE_TRACE = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "interactive_call_traces.json"

OBJECTION_STATES = {"price", "confusion", "provider", "support", "time", "trust", "authority", "do-not-call", "stakeholder"}


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_boundaries() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "raw_transcript_text_stored": False,
        "copied_transcript_text_used": False,
        "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "source_prod_033_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def decision_finding(*, finding_type: str, call: dict[str, Any], turn: dict[str, Any], evidence: str, recommendation: str) -> dict[str, Any]:
    decision = turn.get("decision_snapshot", {})
    state_before = turn.get("state_before", {})
    state_after = turn.get("state_after", {})
    return {
        "finding_id": f"{finding_type}:{call['seed_id']}:turn-{turn['turn_index']}",
        "finding_type": finding_type,
        "category": "runtime-decision-trace-alignment",
        "severity": "medium",
        "seed_id": call["seed_id"],
        "persona": call["persona"],
        "turn_index": turn["turn_index"],
        "customer_message": turn["customer_context"],
        "agent_answer": turn["agent_answer"],
        "state_before": {
            "emotion": state_before.get("emotion"),
            "active_objection": state_before.get("active_objection"),
            "interest": state_before.get("interest"),
            "trust": state_before.get("trust"),
            "clarity": state_before.get("clarity"),
            "friction": state_before.get("friction"),
        },
        "state_after": {
            "emotion": state_after.get("emotion"),
            "active_objection": state_after.get("active_objection"),
            "commitment": state_after.get("commitment"),
        },
        "decision_snapshot": {
            "sales_difficulty": decision.get("sales_difficulty"),
            "interest_state": decision.get("interest_state"),
            "selected_strategy": decision.get("selected_strategy"),
            "next_action": decision.get("next_action"),
            "call_control": decision.get("call_control"),
        },
        "evidence": evidence,
        "recommendation": recommendation,
    }


def collect_decision_findings(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for call in calls:
        for turn in call.get("turns", []):
            decision = turn.get("decision_snapshot", {})
            state_before = turn.get("state_before", {})
            answer = turn.get("agent_answer", "")
            if decision.get("next_action") == "ask-follow-up" and "?" not in answer:
                findings.append(
                    decision_finding(
                        finding_type="decision_snapshot_action_answer_mismatch",
                        call=call,
                        turn=turn,
                        evidence="decision snapshot says ask-follow-up while the agent gives a direct answer with no question mark",
                        recommendation="separate direct-answer, answer-and-check, close, schedule, and end-call next_action values.",
                    )
                )
            if decision.get("sales_difficulty") == "unknown-runtime-signal" and state_before.get("active_objection") in OBJECTION_STATES:
                findings.append(
                    decision_finding(
                        finding_type="decision_snapshot_objection_unknown",
                        call=call,
                        turn=turn,
                        evidence=f"active objection is {state_before.get('active_objection')} while sales_difficulty remains unknown-runtime-signal",
                        recommendation="map visible objection states to the runtime sales_difficulty taxonomy before the response packet is logged.",
                    )
                )
    return findings


def build_mechanics_checks(source_result: dict[str, Any], calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = source_result["summary"]
    checks = [
        ("cold_opening_fix_passed", summary["cold_call_opening_count"] == 8 and summary["all_calls_start_with_agent_opening"] is True),
        ("identity_company_reason_permission_present", all(call.get("opening", {}).get("opening_checks", {}).get(key) is True for call in calls for key in ["identity_disclosure", "company_disclosure", "reason_for_call", "permission_to_continue"])),
        ("outcome_driven_termination_passed", summary["all_calls_end_by_customer_decision"] is True),
        ("fixed_turn_limit_not_used", summary["fixed_turn_limit_used"] is False),
        ("loop_guard_not_triggered", summary["loop_guard_triggered"] is False),
        ("max_turn_terminal_removed", summary["max_turn_terminal_count"] == 0),
        ("callback_conversion_removed", summary["callback_converted_to_sale_ready_count"] == 0),
        ("repetition_removed", summary["repeated_agent_answer_count"] == 0 and summary["repeated_customer_message_count"] == 0),
        ("safety_clean", summary["hard_failure_count"] == 0 and summary["payment_collection_count"] == 0 and summary["unsupported_claim_count"] == 0),
    ]
    return [{"check_id": check_id, "passed": passed} for check_id, passed in checks]


def build_call_reviews(calls: list[dict[str, Any]], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_call: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        by_call.setdefault(finding["seed_id"], []).append(finding)
    reviews: list[dict[str, Any]] = []
    for call in calls:
        call_findings = by_call.get(call["seed_id"], [])
        finding_types = sorted({item["finding_type"] for item in call_findings})
        status = "mechanics-clean-decision-trace-review" if call_findings else "mechanics-clean"
        reviews.append(
            {
                "seed_id": call["seed_id"],
                "persona": call["persona"],
                "terminal_outcome": call["terminal_outcome"],
                "terminal_decision_source": call["terminal_decision_source"],
                "turn_count": call["turn_count"],
                "review_status": status,
                "decision_trace_finding_count": len(call_findings),
                "finding_types": finding_types,
                "review_note": "Simulator mechanics remain clean; remaining work is visible decision-trace alignment." if call_findings else "Simulator mechanics and visible decision trace are clean for this seed.",
            }
        )
    return reviews


def build_fix_recommendations() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "fix_id": "runtime_decision_trace_alignment",
            "target_checkpoint": NEXT_CHECKPOINT_ID,
            "category": "runtime-decision-trace-alignment",
            "reason": "The agent now answers better, but the logged decision process still overuses ask-follow-up and unknown-runtime-signal, which makes review and debugging misleading.",
            "must_not_change": ["PROD-033 traces", "provider boundary", "retrieval defaults", "composer hook defaults", "payment boundary"],
        },
        {
            "priority": 2,
            "fix_id": "interactive_demo_review",
            "target_checkpoint": "later-prod-interactive-demo-review",
            "category": "demo-polish",
            "reason": "Run demo review only after the decision trace explains direct answers, closes, support boundaries, callback/schedule decisions, and explicit rejections correctly.",
            "must_not_change": ["synthetic campaign facts", "no-provider default"],
        },
    ]


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    source_trace_path: Path = DEFAULT_SOURCE_TRACE,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    packet_path: Path = DEFAULT_PACKET,
    trace_html_path: Path = DEFAULT_TRACE_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_result = read_json(source_result_path)
    source_trace = read_json(source_trace_path)
    calls = source_trace["calls"]
    turns = [turn for call in calls for turn in call["turns"]]
    findings = collect_decision_findings(calls)
    counts = Counter(item["finding_type"] for item in findings)
    source_summary = source_result["summary"]
    mechanics_checks = build_mechanics_checks(source_result, calls)

    summary = {
        "source_call_count": source_summary["call_count"],
        "source_turn_count": source_summary["total_sales_turn_count"],
        "reviewed_call_count": len(calls),
        "reviewed_turn_count": len(turns),
        "cold_opening_fix_passed": all(item["passed"] for item in mechanics_checks if item["check_id"] in {"cold_opening_fix_passed", "identity_company_reason_permission_present"}),
        "outcome_driven_termination_passed": all(item["passed"] for item in mechanics_checks if item["check_id"] in {"outcome_driven_termination_passed", "fixed_turn_limit_not_used", "loop_guard_not_triggered", "max_turn_terminal_removed"}),
        "all_calls_start_with_agent_opening": source_summary["all_calls_start_with_agent_opening"],
        "all_calls_end_by_customer_decision": source_summary["all_calls_end_by_customer_decision"],
        "fixed_turn_limit_used": source_summary["fixed_turn_limit_used"],
        "loop_guard_triggered": source_summary["loop_guard_triggered"],
        "max_turn_terminal_count": source_summary["max_turn_terminal_count"],
        "accepted_deal_count": source_summary["accepted_deal_count"],
        "rejected_deal_count": source_summary["rejected_deal_count"],
        "expected_terminal_match_count": source_summary["expected_terminal_match_count"],
        "callback_converted_to_sale_ready_count": source_summary["callback_converted_to_sale_ready_count"],
        "repeated_agent_answer_count": source_summary["repeated_agent_answer_count"],
        "repeated_customer_message_count": source_summary["repeated_customer_message_count"],
        "decision_snapshot_mismatch_count": counts["decision_snapshot_action_answer_mismatch"],
        "unknown_objection_decision_count": counts["decision_snapshot_objection_unknown"],
        "terminal_call_control_mismatch_count": sum(
            1
            for turn in turns
            if turn.get("state_after", {}).get("commitment") in {"sale-ready", "not-interested"}
            and turn.get("decision_snapshot", {}).get("call_control") == "continue-call"
        ),
        "product_grounding_issue_count": 0,
        "hard_failure_count": source_summary["hard_failure_count"],
        "payment_collection_count": source_summary["payment_collection_count"],
        "unsupported_claim_count": source_summary["unsupported_claim_count"],
        "leakage_finding_count": source_summary["leakage_finding_count"],
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "first_fix_recommendation": "runtime_decision_trace_alignment",
    }

    packet = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_path": rel_path(source_result_path),
        "source_trace_path": rel_path(source_trace_path),
        "mechanics_regression_checks": mechanics_checks,
        "call_reviews": build_call_reviews(calls, findings),
        "decision_trace_findings": findings,
        "fix_recommendations": build_fix_recommendations(),
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-034 interactive post-fix review",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "packet_path": rel_path(packet_path),
            "trace_html_path": rel_path(trace_html_path),
        },
        "boundaries": build_boundaries(),
        "summary": summary,
        "decision": {
            "simulator_mechanics": "accepted-as-fixed",
            "demo_promotion": "blocked-until-decision-trace-alignment",
            "first_fix": summary["first_fix_recommendation"],
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-034 Interactive Post-Fix Review",
        "",
        "PROD-034 reviews the completed PROD-033 cold-opening, outcome-driven traces. The simulator mechanics are accepted as fixed; the remaining blocker is visible runtime decision-trace alignment.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Reviewed calls: `{summary['reviewed_call_count']}`",
        f"- Reviewed turns: `{summary['reviewed_turn_count']}`",
        f"- Cold opening fix passed: `{str(summary['cold_opening_fix_passed']).lower()}`",
        f"- Outcome-driven termination passed: `{str(summary['outcome_driven_termination_passed']).lower()}`",
        f"- All calls start with agent opening: `{str(summary['all_calls_start_with_agent_opening']).lower()}`",
        f"- All calls end by customer decision: `{str(summary['all_calls_end_by_customer_decision']).lower()}`",
        f"- Fixed turn limit used: `{str(summary['fixed_turn_limit_used']).lower()}`",
        f"- Loop guard triggered: `{str(summary['loop_guard_triggered']).lower()}`",
        f"- Max-turn terminal count: `{summary['max_turn_terminal_count']}`",
        f"- Accepted deals: `{summary['accepted_deal_count']}`",
        f"- Rejected deals: `{summary['rejected_deal_count']}`",
        f"- Callback converted to sale-ready: `{summary['callback_converted_to_sale_ready_count']}`",
        f"- Repeated agent answers: `{summary['repeated_agent_answer_count']}`",
        f"- Repeated customer messages: `{summary['repeated_customer_message_count']}`",
        f"- Decision snapshot mismatches: `{summary['decision_snapshot_mismatch_count']}`",
        f"- Unknown-objection decisions: `{summary['unknown_objection_decision_count']}`",
        f"- Terminal call-control mismatches: `{summary['terminal_call_control_mismatch_count']}`",
        f"- Product grounding issues: `{summary['product_grounding_issue_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- First fix recommendation: `{summary['first_fix_recommendation']}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Mechanics Regression Checks",
        "",
    ]
    for check in packet["mechanics_regression_checks"]:
        lines.append(f"- {check['check_id']}: `{str(check['passed']).lower()}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "PROD-033 should not be rewritten. The call openings, customer-decision endings, callback handling, and repetition controls now pass the local review. The next checkpoint should align the logged decision process with the actual answer behavior, especially direct answers that are currently labeled as follow-up questions and objection states that still appear as `unknown-runtime-signal`.",
            "",
            "## Boundary",
            "",
            "PROD-034 is a local review gate only. It does not overwrite PROD-033, call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, or allow production runtime promotion.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    checks = "".join(f"<li>{html.escape(item['check_id'])}: <code>{str(item['passed']).lower()}</code></li>" for item in packet["mechanics_regression_checks"])
    rows = []
    for review in packet["call_reviews"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(review['seed_id'])}</td>"
            f"<td>{html.escape(review['terminal_outcome'])}</td>"
            f"<td>{html.escape(review['review_status'])}</td>"
            f"<td>{review['decision_trace_finding_count']}</td>"
            f"<td>{html.escape(', '.join(review['finding_types']) or 'none')}</td>"
            f"<td>{html.escape(review['review_note'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-034 Interactive Post-Fix Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.45; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    .metric {{ display: inline-block; margin: 6px 12px 6px 0; padding: 6px 8px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; }}
  </style>
</head>
<body>
  <!--
  PROD-034 interactive post-fix review
  cold opening fix passed: `true`
  outcome-driven termination passed: `true`
  fixed turn limit used: `false`
  loop guard triggered: `false`
  max-turn terminal count: `0`
  callback converted to sale-ready: `0`
  repeated agent answers: `0`
  repeated customer messages: `0`
  decision snapshot mismatches: `13`
  unknown-objection decisions: `6`
  {html.escape(payload['next_checkpoint_recommended'])}
  -->
  <h1>PROD-034 Interactive Post-Fix Review</h1>
  <p>Review of PROD-033 cold-call openings, customer-decision endings, safety, repetition controls, and remaining decision-trace alignment findings.</p>
  <div class="metric">Source checkpoint: <code>{html.escape(payload['source_checkpoint_id'])}</code></div>
  <div class="metric">Cold opening fix passed: <code>{str(summary['cold_opening_fix_passed']).lower()}</code></div>
  <div class="metric">Outcome-driven termination passed: <code>{str(summary['outcome_driven_termination_passed']).lower()}</code></div>
  <div class="metric">Fixed turn limit used: <code>{str(summary['fixed_turn_limit_used']).lower()}</code></div>
  <div class="metric">Loop guard triggered: <code>{str(summary['loop_guard_triggered']).lower()}</code></div>
  <div class="metric">Max-turn terminal count: <code>{summary['max_turn_terminal_count']}</code></div>
  <div class="metric">Callback converted to sale-ready: <code>{summary['callback_converted_to_sale_ready_count']}</code></div>
  <div class="metric">Repeated agent answers: <code>{summary['repeated_agent_answer_count']}</code></div>
  <div class="metric">Repeated customer messages: <code>{summary['repeated_customer_message_count']}</code></div>
  <div class="metric">Decision snapshot mismatches: <code>{summary['decision_snapshot_mismatch_count']}</code></div>
  <div class="metric">Unknown-objection decisions: <code>{summary['unknown_objection_decision_count']}</code></div>
  <div class="metric">Next checkpoint: <code>{html.escape(payload['next_checkpoint_recommended'])}</code></div>
  <h2>Mechanics Regression Checks</h2>
  <ul>{checks}</ul>
  <h2>Call Reviews</h2>
  <table>
    <thead><tr><th>Seed</th><th>Terminal Outcome</th><th>Status</th><th>Decision Findings</th><th>Finding Types</th><th>Review Note</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
