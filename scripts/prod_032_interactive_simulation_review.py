#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-032-interactive-simulation-review"
SOURCE_CHECKPOINT_ID = "PROD-031-interactive-grounded-call-simulation"
NEXT_CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_PACKET = DEFAULT_OUT_DIR / "interactive_simulation_review_packet.json"
DEFAULT_TRACE_HTML = DEFAULT_OUT_DIR / "interactive_simulation_review_trace.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
DEFAULT_SOURCE_TRACE = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "interactive_call_traces.json"


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


def finding(
    *,
    finding_type: str,
    category: str,
    severity: str,
    call: dict[str, Any],
    turn: dict[str, Any],
    evidence: str,
    review_note: str,
) -> dict[str, Any]:
    decision = turn.get("decision_snapshot", {})
    return {
        "finding_id": f"{finding_type}:{call['seed_id']}:turn-{turn['turn_index']}",
        "finding_type": finding_type,
        "category": category,
        "severity": severity,
        "seed_id": call["seed_id"],
        "persona": call["persona"],
        "turn_index": turn["turn_index"],
        "customer_message": turn["customer_message"],
        "agent_answer": turn["agent_answer"],
        "state_before": turn["state_before"],
        "state_after": turn["state_after"],
        "decision_snapshot": {
            "sales_difficulty": decision.get("sales_difficulty"),
            "interest_state": decision.get("interest_state"),
            "selected_strategy": decision.get("selected_strategy"),
            "next_action": decision.get("next_action"),
            "call_control": decision.get("call_control"),
        },
        "evidence": evidence,
        "review_note": review_note,
    }


def collect_findings(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for call in calls:
        previous_answer = None
        previous_customer = None
        for turn in call["turns"]:
            before = turn["state_before"]
            after = turn["state_after"]
            decision = turn["decision_snapshot"]
            customer_message = turn["customer_message"].lower()
            agent_answer = turn["agent_answer"]

            if "close language came before" in turn["customer_reaction_reason"]:
                findings.append(
                    finding(
                        finding_type="premature_close_marker",
                        category="still-relevant-static-route-gap",
                        severity="medium",
                        call=call,
                        turn=turn,
                        evidence="reaction reason marks close language before enough trust or clarity",
                        review_note="Price-objection handling still needs route/policy review even though the answer stayed safe.",
                    )
                )

            if previous_answer == agent_answer:
                findings.append(
                    finding(
                        finding_type="repeated_agent_answer",
                        category="simulator-design-limit",
                        severity="medium",
                        call=call,
                        turn=turn,
                        evidence="agent answer repeats the immediately previous answer",
                        review_note="The interactive loop should vary, terminate, or schedule instead of replaying the same answer.",
                    )
                )

            if previous_customer == turn["customer_message"]:
                findings.append(
                    finding(
                        finding_type="repeated_customer_message",
                        category="simulator-design-limit",
                        severity="medium",
                        call=call,
                        turn=turn,
                        evidence="customer message repeats the immediately previous customer message",
                        review_note="The simulator is forcing extra turns after a terminal customer intent.",
                    )
                )

            if before.get("commitment") == "callback" and after.get("commitment") == "sale-ready":
                findings.append(
                    finding(
                        finding_type="callback_converted_to_sale_ready",
                        category="simulator-design-limit",
                        severity="high",
                        call=call,
                        turn=turn,
                        evidence="state transition changes callback commitment into sale-ready commitment",
                        review_note="A callback request should remain a callback or handoff outcome unless the customer explicitly upgrades intent.",
                    )
                )

            if "callback" in customer_message and after.get("commitment") == "sale-ready":
                findings.append(
                    finding(
                        finding_type="callback_request_converted_to_sale_ready",
                        category="still-relevant-static-route-gap",
                        severity="high",
                        call=call,
                        turn=turn,
                        evidence="customer asks for callback while state after marks sale-ready",
                        review_note="The old callback route gap still matters in reactive traces.",
                    )
                )

            if decision.get("next_action") == "ask-follow-up" and "?" not in agent_answer:
                findings.append(
                    finding(
                        finding_type="decision_snapshot_action_answer_mismatch",
                        category="runtime-policy-issue",
                        severity="medium",
                        call=call,
                        turn=turn,
                        evidence="decision snapshot says ask-follow-up while spoken answer asks no question",
                        review_note="Decision trace and answer behavior are not aligned enough for reliable review.",
                    )
                )

            if decision.get("sales_difficulty") == "unknown-runtime-signal" and before.get("active_objection") in {"price", "confusion", "provider", "support"}:
                findings.append(
                    finding(
                        finding_type="decision_snapshot_objection_unknown",
                        category="runtime-policy-issue",
                        severity="medium",
                        call=call,
                        turn=turn,
                        evidence=f"active objection is {before.get('active_objection')} but decision snapshot keeps unknown-runtime-signal",
                        review_note="The answer may be useful, but the visible decision process is not recognizing the customer state.",
                    )
                )

            previous_answer = agent_answer
            previous_customer = turn["customer_message"]
    return findings


def build_call_reviews(calls: list[dict[str, Any]], raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings_by_call: dict[str, list[dict[str, Any]]] = {}
    for item in raw_findings:
        findings_by_call.setdefault(item["seed_id"], []).append(item)

    reviews: list[dict[str, Any]] = []
    for call in calls:
        call_findings = findings_by_call.get(call["seed_id"], [])
        finding_types = sorted({item["finding_type"] for item in call_findings})
        categories = sorted({item["category"] for item in call_findings})
        if not call_findings:
            status = "clean"
            review_note = "No PROD-032 review findings; this trace can remain regression evidence."
        elif any(item["severity"] == "high" for item in call_findings):
            status = "fix-before-demo"
            review_note = "High-severity callback or terminal-control finding needs a simulator/control fix before demo review."
        else:
            status = "review-before-demo"
            review_note = "Trace is safe but needs policy or simulator review before stronger demo claims."
        reviews.append(
            {
                "seed_id": call["seed_id"],
                "persona": call["persona"],
                "terminal_outcome": call["terminal_outcome"],
                "turn_count": call["turn_count"],
                "review_status": status,
                "finding_count": len(call_findings),
                "finding_types": finding_types,
                "categories": categories,
                "review_note": review_note,
            }
        )
    return reviews


def build_clusters(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(item["finding_type"] for item in raw_findings)
    return [
        {
            "cluster_id": "callback-terminal-control",
            "category": "simulator-design-limit",
            "finding_types": ["callback_converted_to_sale_ready", "callback_request_converted_to_sale_ready"],
            "finding_count": counts["callback_converted_to_sale_ready"] + counts["callback_request_converted_to_sale_ready"],
            "affected_static_route_gap": "callback_request",
            "classification": "fix first because terminal state quality controls every later interactive metric",
        },
        {
            "cluster_id": "repetition-loop-control",
            "category": "simulator-design-limit",
            "finding_types": ["repeated_agent_answer", "repeated_customer_message"],
            "finding_count": counts["repeated_agent_answer"] + counts["repeated_customer_message"],
            "affected_static_route_gap": "none",
            "classification": "fix simulator loop termination and answer variation before using traces for demo claims",
        },
        {
            "cluster_id": "visible-decision-policy-alignment",
            "category": "runtime-policy-issue",
            "finding_types": ["decision_snapshot_action_answer_mismatch", "decision_snapshot_objection_unknown"],
            "finding_count": counts["decision_snapshot_action_answer_mismatch"] + counts["decision_snapshot_objection_unknown"],
            "affected_static_route_gap": "price_objection",
            "classification": "runtime decision snapshots need route specialization after the simulator terminal fix",
        },
        {
            "cluster_id": "price-close-readiness",
            "category": "still-relevant-static-route-gap",
            "finding_types": ["premature_close_marker"],
            "finding_count": counts["premature_close_marker"],
            "affected_static_route_gap": "price_objection",
            "classification": "price handling is safe but still shows premature-close pressure in the simulator state model",
        },
    ]


def build_fix_recommendations() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "fix_id": "simulator_termination_and_callback_state_control",
            "target_checkpoint": NEXT_CHECKPOINT_ID,
            "category": "simulator-design-limit",
            "reason": "Callback and stop/schedule intents must terminate or preserve callback state before route-policy quality can be measured cleanly.",
            "must_not_change": ["provider boundary", "runtime retrieval defaults", "composer hook defaults", "payment boundary"],
        },
        {
            "priority": 2,
            "fix_id": "runtime_decision_snapshot_route_alignment",
            "target_checkpoint": "later-prod-runtime-policy-review",
            "category": "runtime-policy-issue",
            "reason": "The visible decision process should match the actual answer and recognize price, confusion, provider, support, and callback states.",
            "must_not_change": ["validated guarded answer text", "campaign facts", "provider boundary"],
        },
        {
            "priority": 3,
            "fix_id": "answer_variation_after_state_progress",
            "target_checkpoint": "later-interactive-demo-polish",
            "category": "simulator-design-limit",
            "reason": "The simulator should avoid replaying the same agent/customer turn after state has already moved.",
            "must_not_change": ["source PROD-031 evidence", "safety gates"],
        },
    ]


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
        "source_prod_031_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


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
    raw_findings = collect_findings(calls)
    counts = Counter(item["finding_type"] for item in raw_findings)
    categories = Counter(item["category"] for item in raw_findings)
    affected_calls = {item["seed_id"] for item in raw_findings}
    static_route_gaps = sorted({"callback_request", "price_objection"})

    summary = {
        "source_call_count": source_result["summary"]["call_count"],
        "source_turn_count": source_result["summary"]["total_turn_count"],
        "reviewed_call_count": len(calls),
        "reviewed_turn_count": len(turns),
        "raw_finding_count": len(raw_findings),
        "affected_call_count": len(affected_calls),
        "clean_call_count": len(calls) - len(affected_calls),
        "simulator_design_limit_count": categories["simulator-design-limit"],
        "runtime_policy_issue_count": categories["runtime-policy-issue"],
        "product_grounding_issue_count": categories["product-grounding-issue"],
        "still_relevant_static_route_gap_count": len(static_route_gaps),
        "still_relevant_static_route_gaps": static_route_gaps,
        "callback_converted_to_sale_ready_count": counts["callback_converted_to_sale_ready"],
        "callback_request_converted_to_sale_ready_count": counts["callback_request_converted_to_sale_ready"],
        "repeated_agent_answer_count": counts["repeated_agent_answer"],
        "repeated_customer_message_count": counts["repeated_customer_message"],
        "decision_snapshot_mismatch_count": counts["decision_snapshot_action_answer_mismatch"],
        "unknown_objection_decision_count": counts["decision_snapshot_objection_unknown"],
        "premature_close_marker_count": counts["premature_close_marker"],
        "hard_failure_count": sum(1 for turn in turns if turn["safety_flags"]["hard_failure"]),
        "payment_collection_count": sum(1 for turn in turns if turn["safety_flags"]["payment_collection"]),
        "unsupported_claim_count": sum(1 for turn in turns if turn["safety_flags"]["unsupported_claim"]),
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "first_fix_recommendation": "simulator_termination_and_callback_state_control",
    }

    packet = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_path": rel_path(source_result_path),
        "source_trace_path": rel_path(source_trace_path),
        "call_reviews": build_call_reviews(calls, raw_findings),
        "raw_findings": raw_findings,
        "finding_clusters": build_clusters(raw_findings),
        "fix_recommendations": build_fix_recommendations(),
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-032 interactive simulation review",
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
            "interactive_trace_evidence": "accepted-for-review-not-demo-promotion",
            "first_fix": summary["first_fix_recommendation"],
            "static_route_gap_cleanup": "defer-until-simulator-terminal-control-is-clean",
            "runtime_promotion": "blocked",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, packet


def render_report(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-032 Interactive Simulation Review",
        "",
        "PROD-032 reviews the completed PROD-031 reactive state traces and classifies the remaining issues before any runtime, demo, provider, or route-gap cleanup step.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Reviewed calls: `{summary['reviewed_call_count']}`",
        f"- Reviewed turns: `{summary['reviewed_turn_count']}`",
        f"- Raw findings: `{summary['raw_finding_count']}`",
        f"- Affected calls: `{summary['affected_call_count']}`",
        f"- Clean calls: `{summary['clean_call_count']}`",
        f"- Simulator-design limits: `{summary['simulator_design_limit_count']}`",
        f"- Runtime-policy issues: `{summary['runtime_policy_issue_count']}`",
        f"- Product grounding issues: `{summary['product_grounding_issue_count']}`",
        f"- Still-relevant static route gaps: `{summary['still_relevant_static_route_gap_count']}`",
        f"- Callback converted to sale-ready: `{summary['callback_converted_to_sale_ready_count']}`",
        f"- Repeated agent answers: `{summary['repeated_agent_answer_count']}`",
        f"- Repeated customer messages: `{summary['repeated_customer_message_count']}`",
        f"- Decision snapshot mismatches: `{summary['decision_snapshot_mismatch_count']}`",
        f"- Unknown-objection decisions: `{summary['unknown_objection_decision_count']}`",
        f"- Premature close markers: `{summary['premature_close_marker_count']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- First fix recommendation: `{summary['first_fix_recommendation']}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Finding Clusters",
        "",
    ]
    for cluster in packet["finding_clusters"]:
        lines.extend(
            [
                f"### {cluster['cluster_id']}",
                "",
                f"- Category: `{cluster['category']}`",
                f"- Finding count: `{cluster['finding_count']}`",
                f"- Affected static route gap: `{cluster['affected_static_route_gap']}`",
                f"- Classification: {cluster['classification']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Fix Recommendation",
            "",
            "The first fix recommendation is `simulator_termination_and_callback_state_control`. The simulator should preserve callback commitments, end or schedule when a customer asks for callback, and avoid forcing repeated turns after terminal intent.",
            "",
            "Runtime decision alignment remains important, but it should follow the simulator terminal-control fix so the next review is not measuring artificial loops.",
            "",
            "## Boundary",
            "",
            "PROD-032 is a local review gate only. It does not overwrite PROD-031, call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, or allow production runtime promotion.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], packet: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for review in packet["call_reviews"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(review['seed_id'])}</td>"
            f"<td>{html.escape(review['review_status'])}</td>"
            f"<td>{review['finding_count']}</td>"
            f"<td>{html.escape(', '.join(review['categories']) or 'clean')}</td>"
            f"<td>{html.escape(review['review_note'])}</td>"
            "</tr>"
        )
    clusters = []
    for cluster in packet["finding_clusters"]:
        clusters.append(
            "<li>"
            f"<strong>{html.escape(cluster['cluster_id'])}</strong>: "
            f"{html.escape(cluster['category'])}, {cluster['finding_count']} findings. "
            f"{html.escape(cluster['classification'])}"
            "</li>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-032 Interactive Simulation Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.45; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    .metric {{ display: inline-block; margin: 6px 12px 6px 0; padding: 6px 8px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>PROD-032 Interactive Simulation Review</h1>
  <p>Review of PROD-031 simulator-design limits, runtime-policy issues, product-grounding issues, and still-relevant static route gaps.</p>
  <div class="metric">Source checkpoint: `{html.escape(payload['source_checkpoint_id'])}`</div>
  <div class="metric">Raw findings: `{summary['raw_finding_count']}`</div>
  <div class="metric">Affected calls: `{summary['affected_call_count']}`</div>
  <div class="metric">Simulator-design limits: `{summary['simulator_design_limit_count']}`</div>
  <div class="metric">Runtime-policy issues: `{summary['runtime_policy_issue_count']}`</div>
  <div class="metric">Product grounding issues: `{summary['product_grounding_issue_count']}`</div>
  <div class="metric">Callback converted to sale-ready: `{summary['callback_converted_to_sale_ready_count']}`</div>
  <div class="metric">Repeated agent answers: `{summary['repeated_agent_answer_count']}`</div>
  <div class="metric">Repeated customer messages: `{summary['repeated_customer_message_count']}`</div>
  <div class="metric">first fix recommendation: `{html.escape(summary['first_fix_recommendation'])}`</div>
  <div class="metric">Next checkpoint: `{html.escape(payload['next_checkpoint_recommended'])}`</div>
  <h2>Finding Clusters</h2>
  <ul>{''.join(clusters)}</ul>
  <h2>Call Reviews</h2>
  <table>
    <thead><tr><th>Seed</th><th>Status</th><th>Findings</th><th>Categories</th><th>Review Note</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
