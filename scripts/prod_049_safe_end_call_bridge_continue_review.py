#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from prod_045_core_sales_policy_regression_rerun import TEST_CAMPAIGN
from run_realtime_turn_simulation import build_runtime_decision


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-049-safe-end-call-bridge-continue-review"
CHECKPOINT_NAME = "Safe End-Call Bridge Continue Review"
SOURCE_CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
NEXT_CHECKPOINT_ID = "PROD-050-safe-call-control-softening-regression"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

SOURCE_CALL_CONTROL_FINDINGS = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / SOURCE_CHECKPOINT_ID
    / "call_control_findings.json"
)

SOURCE_RESULTS = {
    "prod_048c": ROOT / "research" / "experiments" / "generated" / "PROD-048C-german-wording-feedback-patch" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json",
    "prod_045": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
}

BRIDGE_CANDIDATE_DIFFICULTIES = {
    "price-first-direct": {
        "candidate_reason": "The customer asked a non-refusal factual question; the agent can answer and then continue only if the customer stays engaged.",
        "future_test_goal": "Answer first, then ask one low-pressure qualification question.",
    },
    "written-info-request": {
        "candidate_reason": "The customer asked for written information; the agent can confirm the written path and optionally ask one tailoring question.",
        "future_test_goal": "Confirm written info, then continue only with an optional tailoring question.",
    },
    "stakeholder-review": {
        "candidate_reason": "The customer needs another reviewer; the agent can bridge to a review summary and ask one useful context question.",
        "future_test_goal": "Offer a review summary and ask one low-pressure context question.",
    },
    "partner-review": {
        "candidate_reason": "The customer needs partner review; the agent can bridge to a review summary without bypassing the partner.",
        "future_test_goal": "Offer a review summary and ask one low-pressure context question.",
    },
}

PROTECTED_REASONS = {
    "email-only-boundary": "Customer constrained the channel; continuing the phone call would weaken the email-only boundary.",
    "scam-safety-boundary": "Safety fear should not become continued sales without a separate consented continuation design.",
    "payment-safety-boundary": "Payment or card concern should close with safe written or verification information, not continued sales pressure.",
    "sale-ready-commitment": "Sale-ready handling is a terminal guarded close and must keep no-payment/no-contract boundaries.",
    "callback-request": "Customer asked for later contact; the safe action is to log the follow-up and end rather than continue.",
}

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "call_control_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
}

PROTECTED_BOUNDARY_SPECS = [
    {
        "case_id": "prod-049-support-boundary",
        "customer_move_id": "support_issue",
        "transcript": "This is a support issue.",
        "expected_call_control": "transfer-or-escalate",
    },
    {
        "case_id": "prod-049-cancellation-boundary",
        "customer_move_id": "cancellation_request",
        "transcript": "I want to cancel.",
        "expected_call_control": "transfer-or-escalate",
    },
    {
        "case_id": "prod-049-do-not-call-boundary",
        "customer_move_id": "do_not_call",
        "transcript": "Do not call me again.",
        "expected_call_control": "end-call",
    },
    {
        "case_id": "prod-049-human-request-boundary",
        "customer_move_id": "human_request",
        "transcript": "I want a human specialist.",
        "expected_call_control": "transfer-or-escalate",
    },
    {
        "case_id": "prod-049-email-only-boundary",
        "customer_move_id": "email_only",
        "transcript": "Just email me.",
        "expected_call_control": "end-call",
    },
    {
        "case_id": "prod-049-payment-safety-boundary",
        "customer_move_id": "payment_safety_fear",
        "transcript": "I am not giving card details.",
        "expected_call_control": "end-call",
    },
    {
        "case_id": "prod-049-scam-safety-boundary",
        "customer_move_id": "scam_or_card_fear",
        "transcript": "Is this a scam?",
        "expected_call_control": "end-call",
    },
    {
        "case_id": "prod-049-sale-ready-boundary",
        "customer_move_id": "sale_ready_interest",
        "transcript": "I am ready to move forward.",
        "expected_call_control": "close-and-log-sale-ready",
    },
]

FORBIDDEN_PRESSURE_MARKERS = [
    "payment now",
    "pay now",
    "card number",
    "sign now",
    "contract today",
    "must decide",
    "only available today",
    "ignore your cancellation",
    "keep selling",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def source_result_statuses() -> dict[str, bool]:
    return {key: read_json(path).get("validation", {}).get("passed") is True for key, path in SOURCE_RESULTS.items()}


def build_candidate_matrix() -> list[dict[str, Any]]:
    source_items = read_json(SOURCE_CALL_CONTROL_FINDINGS)["items"]
    matrix = []
    for item in source_items:
        sales_difficulty = item["sales_difficulty"]
        is_candidate = sales_difficulty in BRIDGE_CANDIDATE_DIFFICULTIES
        current_call_control = item["call_control"]
        candidate_meta = BRIDGE_CANDIDATE_DIFFICULTIES.get(sales_difficulty, {})
        matrix.append(
            {
                "finding_id": item["finding_id"],
                "language": item["language"],
                "case_id": item["case_id"],
                "sales_difficulty": sales_difficulty,
                "current_call_control": current_call_control,
                "bridge_then_continue_candidate": is_candidate,
                "candidate_call_control": "bridge-then-continue" if is_candidate else current_call_control,
                "candidate_reason": candidate_meta.get("candidate_reason"),
                "future_test_goal": candidate_meta.get("future_test_goal"),
                "exclusion_reason": None if is_candidate else PROTECTED_REASONS.get(sales_difficulty, "Not selected for this narrow call-control review."),
                "guardrail_preserved": True,
                "runtime_change_applied": False,
                "requires_future_regression": bool(is_candidate),
                "source_recommended_future_change": item["recommended_future_change"],
            }
        )
    return matrix


def runtime_decision_for(case_id: str, transcript: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": case_id,
            "customer_input": {
                "input_type": "speech",
                "stage": "relevance-check",
                "transcript": transcript,
            },
        },
        campaign=TEST_CAMPAIGN,
    )


def build_protected_boundary_results() -> list[dict[str, Any]]:
    results = []
    for spec in PROTECTED_BOUNDARY_SPECS:
        decision = runtime_decision_for(spec["case_id"], spec["transcript"])
        response = decision.get("agent_response", "").lower()
        pressure_hits = [marker for marker in FORBIDDEN_PRESSURE_MARKERS if marker in response]
        passed = (
            decision["call_control"] == spec["expected_call_control"]
            and decision["call_control"] != "bridge-then-continue"
            and not pressure_hits
        )
        results.append(
            {
                **spec,
                "runtime_decision": decision,
                "pressure_marker_hits": pressure_hits,
                "bridge_then_continue_forbidden": True,
                "passed": passed,
            }
        )
    return results


def build_review_packet(matrix: list[dict[str, Any]], boundary_results: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_items = [item for item in matrix if item["bridge_then_continue_candidate"]]
    protected_items = [item for item in matrix if not item["bridge_then_continue_candidate"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "review_basis": [
            rel(SOURCE_CALL_CONTROL_FINDINGS),
            *[rel(path) for path in SOURCE_RESULTS.values()],
        ],
        "decision": {
            "selected_non_refusal_cases_should_be_tested_as_bridge_then_continue": True,
            "runtime_change_applied": False,
            "do_not_change_support_cancellation_or_refusal_boundaries": True,
            "requires_future_regression_checkpoint_before_runtime_change": True,
            "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        },
        "selected_candidate_sales_difficulties": sorted(BRIDGE_CANDIDATE_DIFFICULTIES),
        "protected_sales_difficulties": sorted(PROTECTED_REASONS),
        "candidate_items": candidate_items,
        "protected_items": protected_items,
        "protected_boundary_results": boundary_results,
        "future_runtime_test_requirements": [
            "Keep support, cancellation, do-not-call, human request, email-only, payment fear, scam fear, sale-ready, and callback boundaries unchanged.",
            "Only test bridge-then-continue for price-first, written-info, stakeholder-review, and partner-review style non-refusal turns.",
            "The bridge response must answer or acknowledge the customer first before asking any question.",
            "The follow-up question must be optional, low pressure, and based on approved campaign fields.",
            "Payment collection, contract signing, unsupported claims, retrieval defaults, providers, voice playback, public demo use, and production promotion remain blocked.",
        ],
    }


def build_summary(matrix: list[dict[str, Any]], boundary_results: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_items = [item for item in matrix if item["bridge_then_continue_candidate"]]
    protected_items = [item for item in matrix if not item["bridge_then_continue_candidate"]]
    candidate_language_counts = Counter(item["language"] for item in candidate_items)
    protected_diff_counts = Counter(item["sales_difficulty"] for item in protected_items)
    summary = {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_statuses": source_result_statuses(),
        "source_call_control_finding_count": len(matrix),
        "bridge_then_continue_candidate_count": len(candidate_items),
        "protected_end_or_escalation_count": len(protected_items),
        "candidate_language_counts": {
            "en": candidate_language_counts.get("en", 0),
            "de": candidate_language_counts.get("de", 0),
        },
        "selected_sales_difficulty_count": len(BRIDGE_CANDIDATE_DIFFICULTIES),
        "protected_sales_difficulty_count": len(PROTECTED_REASONS),
        "protected_boundary_probe_count": len(boundary_results),
        "protected_boundary_pass_count": sum(1 for item in boundary_results if item["passed"]),
        "support_cancellation_do_not_call_softened": False,
        "email_only_softened": protected_diff_counts.get("email-only-boundary", 0) == 0,
        "payment_or_scam_softened": (
            protected_diff_counts.get("payment-safety-boundary", 0) == 0
            or protected_diff_counts.get("scam-safety-boundary", 0) == 0
        ),
        "sale_ready_softened": protected_diff_counts.get("sale-ready-commitment", 0) == 0,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }
    return summary


def build_report(summary: dict[str, Any], matrix: list[dict[str, Any]]) -> str:
    candidate_counts = Counter(item["sales_difficulty"] for item in matrix if item["bridge_then_continue_candidate"])
    protected_counts = Counter(item["sales_difficulty"] for item in matrix if not item["bridge_then_continue_candidate"])
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        f"- Checkpoint id: `{CHECKPOINT_ID}`",
        f"- Source checkpoint: `{SOURCE_CHECKPOINT_ID}`",
        f"- Source call-control findings: `{summary['source_call_control_finding_count']}`",
        f"- Bridge-then-continue candidates: `{summary['bridge_then_continue_candidate_count']}`",
        f"- Protected end/escalation cases: `{summary['protected_end_or_escalation_count']}`",
        f"- Protected boundary probes passed: `{summary['protected_boundary_pass_count']} / {summary['protected_boundary_probe_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Call-control behavior changed: `{str(summary['call_control_behavior_changed']).lower()}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- LLM used: `{str(summary['llm_used']).lower()}`",
        f"- Private data read: `{str(summary['private_data_read']).lower()}`",
        f"- Production runtime promotion allowed: `{str(summary['production_runtime_promotion_allowed']).lower()}`",
        "",
        "## Decision",
        "",
        "Selected non-refusal end-call cases should be tested as `bridge-then-continue` in a future regression checkpoint. This checkpoint does not apply that runtime change.",
        "",
        "## Candidate Groups",
        "",
    ]
    for difficulty, count in sorted(candidate_counts.items()):
        lines.append(f"- `{difficulty}`: `{count}` candidate finding(s)")
    lines.extend(["", "## Protected Groups", ""])
    for difficulty, count in sorted(protected_counts.items()):
        lines.append(f"- `{difficulty}`: `{count}` protected finding(s)")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Support, cancellation, do-not-call, human-request, email-only, payment/scam safety, sale-ready, and callback paths remain protected from this bridge-then-continue review.",
            "",
            f"Recommended next checkpoint: `{NEXT_CHECKPOINT_ID}`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_html(summary: dict[str, Any], matrix: list[dict[str, Any]], boundary_results: list[dict[str, Any]]) -> str:
    candidate_rows = []
    protected_rows = []
    for item in matrix:
        row = (
            "<tr>"
            f"<td>{html.escape(item['language'])}</td>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['current_call_control'])}</td>"
            f"<td>{html.escape(item['candidate_call_control'])}</td>"
            f"<td>{html.escape(item.get('candidate_reason') or item.get('exclusion_reason') or '')}</td>"
            "</tr>"
        )
        if item["bridge_then_continue_candidate"]:
            candidate_rows.append(row)
        else:
            protected_rows.append(row)
    boundary_rows = [
        (
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['expected_call_control'])}</td>"
            f"<td>{html.escape(item['runtime_decision']['call_control'])}</td>"
            f"<td>{'pass' if item['passed'] else 'fail'}</td>"
            "</tr>"
        )
        for item in boundary_results
    ]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-049 Safe End-Call Bridge Continue Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1f2933; }}
    h1, h2 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
    .summary {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #cbd5e1; padding: 10px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>PROD-049 Safe End-Call Bridge Continue Review</h1>
  <p>This local review decides which safe-but-abrupt end-call findings should be tested as bridge-then-continue later. Runtime behavior changed: false. Provider calls made: false. Production runtime promotion allowed: false.</p>
  <section class="summary">
    <div class="metric"><strong>Source findings</strong><br>{summary['source_call_control_finding_count']}</div>
    <div class="metric"><strong>Bridge candidates</strong><br>{summary['bridge_then_continue_candidate_count']}</div>
    <div class="metric"><strong>Protected cases</strong><br>{summary['protected_end_or_escalation_count']}</div>
  </section>
  <h2>Bridge-Then-Continue Candidates</h2>
  <table>
    <thead><tr><th>Language</th><th>Case</th><th>Sales difficulty</th><th>Current</th><th>Candidate</th><th>Reason</th></tr></thead>
    <tbody>{''.join(candidate_rows)}</tbody>
  </table>
  <h2>Protected End Or Escalation Cases</h2>
  <table>
    <thead><tr><th>Language</th><th>Case</th><th>Sales difficulty</th><th>Current</th><th>Candidate</th><th>Reason</th></tr></thead>
    <tbody>{''.join(protected_rows)}</tbody>
  </table>
  <h2>Protected Boundary Probes</h2>
  <table>
    <thead><tr><th>Case</th><th>Expected call control</th><th>Observed call control</th><th>Result</th></tr></thead>
    <tbody>{''.join(boundary_rows)}</tbody>
  </table>
</body>
</html>
"""


def build_payload() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    matrix = build_candidate_matrix()
    boundary_results = build_protected_boundary_results()
    packet = build_review_packet(matrix, boundary_results)
    summary = build_summary(matrix, boundary_results)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_id": NEXT_CHECKPOINT_ID,
        "validation": {
            "passed": all(summary["source_result_statuses"].values())
            and summary["source_call_control_finding_count"] == 45
            and summary["bridge_then_continue_candidate_count"] == 22
            and summary["protected_boundary_pass_count"] == summary["protected_boundary_probe_count"],
        },
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "candidate_matrix": rel(OUT_DIR / "bridge_continue_candidate_matrix.json"),
            "boundary_results": rel(OUT_DIR / "protected_boundary_results.json"),
            "review_packet": rel(OUT_DIR / "safe_end_call_review_packet.json"),
            "review_html": rel(OUT_DIR / "prod_049_review.html"),
        },
        "summary": summary,
    }
    return payload, packet, matrix, boundary_results


def main() -> None:
    payload, packet, matrix, boundary_results = build_payload()
    write_json(OUT_DIR / "bridge_continue_candidate_matrix.json", {"checkpoint_id": CHECKPOINT_ID, "items": matrix})
    write_json(OUT_DIR / "protected_boundary_results.json", {"checkpoint_id": CHECKPOINT_ID, "items": boundary_results})
    write_json(OUT_DIR / "safe_end_call_review_packet.json", packet)
    write_text(OUT_DIR / "report.md", build_report(payload["summary"], matrix))
    write_text(OUT_DIR / "prod_049_review.html", build_html(payload["summary"], matrix, boundary_results))
    write_json(OUT_DIR / "result.json", payload)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": payload["validation"], "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
