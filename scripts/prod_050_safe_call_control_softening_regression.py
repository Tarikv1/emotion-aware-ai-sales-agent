#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

from prod_045_core_sales_policy_regression_rerun import TEST_CAMPAIGN
from prod_046a_german_naturalized_policy_regression import GERMAN_CAMPAIGN
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.core.realtime_turns import build_runtime_decision


CHECKPOINT_ID = "PROD-050-safe-call-control-softening-regression"
CHECKPOINT_NAME = "Safe Call-Control Softening Regression"
SOURCE_CHECKPOINT_ID = "PROD-049-safe-end-call-bridge-continue-review"
NEXT_CHECKPOINT_ID = "PROD-051-safe-call-control-runtime-update"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

PROD_049_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
PROD_045_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun"
PROD_046D_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-046D-german-source-informed-wording-quality-guard"

SOURCE_FILES = {
    "prod_049_result": PROD_049_DIR / "result.json",
    "prod_049_matrix": PROD_049_DIR / "bridge_continue_candidate_matrix.json",
    "prod_048c_result": ROOT / "research" / "experiments" / "generated" / "PROD-048C-german-wording-feedback-patch" / "result.json",
    "prod_047_result": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046_result": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
    "prod_045_result": PROD_045_DIR / "result.json",
}

SELECTED_DIFFICULTIES = {
    "price-first-direct",
    "written-info-request",
    "stakeholder-review",
    "partner-review",
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
    ("prod-050-support-boundary", "support_issue", "This is a support issue.", "transfer-or-escalate"),
    ("prod-050-cancellation-boundary", "cancellation_request", "I want to cancel.", "transfer-or-escalate"),
    ("prod-050-do-not-call-boundary", "do_not_call", "Do not call me again.", "end-call"),
    ("prod-050-human-request-boundary", "human_request", "I want a human specialist.", "transfer-or-escalate"),
    ("prod-050-email-only-boundary", "email_only", "Just email me.", "end-call"),
    ("prod-050-payment-safety-boundary", "payment_safety_fear", "I am not giving card details.", "end-call"),
    ("prod-050-scam-safety-boundary", "scam_or_card_fear", "Is this a scam?", "end-call"),
    ("prod-050-sale-ready-boundary", "sale_ready_interest", "I am ready to move forward.", "close-and-log-sale-ready"),
    ("prod-050-callback-boundary", "callback_request", "Call me back later.", "end-call"),
]

PRESSURE_MARKERS = [
    "must decide",
    "only available today",
    "last chance",
    "forced appointment",
    "keep selling",
    "ignore your cancellation",
    "müssen sich entscheiden",
    "nur heute",
]
PAYMENT_COLLECTION_MARKERS = ["collect payment", "payment now", "pay now", "card number", "zahlung einziehen"]
CONTRACT_SIGNING_MARKERS = ["sign a contract", "contract today", " unterschreiben", "vertragsabschluss jetzt"]
UNSUPPORTED_CLAIM_MARKERS = ["guaranteed roi", "fully compliant", "guarantee approval", "garantierter erfolg"]
TERMINAL_CLOSING_MARKERS = ["leave it there", "belasse es dabei", "hang up", "end the call"]
LOW_PRESSURE_CONTINUATION_MARKERS = {
    "en": ["if useful", "if it helps", "so it is useful", "so it's useful", "so it is more useful", "so it's more useful", "no decision today"],
    "de": ["wenn es hilfreich ist", "wenn es hilft"],
}

PROPOSED_RESPONSE_TEXT = {
    ("price-first-direct", "en"): (
        "The starter plan is 29 per user per month, and I can send the exact terms in writing. "
        "If useful, I can briefly explain what is included before I send them. No payment or commitment on this call."
    ),
    ("price-first-direct", "de"): (
        "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich. "
        "Wenn es hilfreich ist, kann ich kurz einordnen, was darin enthalten ist."
    ),
    ("written-info-request", "en"): (
        "Of course, I can tailor the summary to your main point. Then I can send it over, so it is more useful to you."
    ),
    ("written-info-request", "de"): (
        "Ich sende Ihnen gern eine kurze Zusammenfassung per E-Mail. "
        "Wenn es hilfreich ist, kann ich sie kurz auf den wichtigsten Punkt für Sie zuschneiden."
    ),
    ("stakeholder-review", "en"): (
        "Of course, I can send your manager a short summary with the key points. No decision today."
    ),
    ("stakeholder-review", "de"): (
        "Ich sende Ihnen eine kurze Zusammenfassung für die prüfende Person. "
        "Wenn es hilfreich ist, kann ich die zwei wichtigsten Punkte direkt mit aufnehmen. "
        "Heute müssen Sie nichts entscheiden."
    ),
    ("partner-review", "en"): (
        "Of course, I can send your spouse a short summary with the key points. No decision today."
    ),
    ("partner-review", "de"): (
        "Ich sende Ihnen eine kurze Zusammenfassung für die mitentscheidende Person. "
        "Wenn es hilfreich ist, kann ich die zwei wichtigsten Punkte direkt mit aufnehmen. "
        "Heute müssen Sie nichts entscheiden."
    ),
}

LEGACY_BASELINE_RESPONSE_TEXT = {
    ("price-first-direct", "en"): (
        "The approved pricing summary is 29 per user per month for the starter plan, with exact terms sent in writing. "
        "No payment or commitment on this call."
    ),
    ("price-first-direct", "de"): "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich.",
    ("written-info-request", "en"): "I can send the approved one-page summary and leave it there.",
    ("written-info-request", "de"): "Ich sende Ihnen gern eine kurze Zusammenfassung per E-Mail und belasse es dabei.",
    ("stakeholder-review", "en"): "I can send the approved review summary for review. No decision or commitment from you today.",
    ("stakeholder-review", "de"): "Ich sende Ihnen eine kurze Zusammenfassung zur Prüfung. Heute müssen Sie nichts entscheiden.",
    ("partner-review", "en"): "I can send the approved review summary for review. No decision or commitment from you today.",
    ("partner-review", "de"): "Ich sende Ihnen eine kurze Zusammenfassung zur Prüfung. Heute müssen Sie nichts entscheiden.",
}


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


def source_statuses() -> dict[str, bool]:
    return {key: read_json(path).get("validation", {}).get("passed") is True for key, path in SOURCE_FILES.items() if key.endswith("_result")}


def current_case_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    english_cases = read_json(PROD_045_DIR / "regression_cases.json")
    for case in english_cases:
        index[case["case_id"]] = {
            "case_id": case["case_id"],
            "customer_move_id": case["customer_move_id"],
            "customer_input": case["customer_input"],
            "campaign": case["campaign"],
            "language": "en",
        }

    german_results = read_json(PROD_046D_DIR / "german_source_informed_results.json")["items"]
    for item in german_results:
        index[item["case_id"]] = {
            "case_id": item["case_id"],
            "customer_move_id": item["customer_move_id"],
            "customer_input": {
                "input_type": "speech",
                "stage": "relevance-check",
                "transcript": item["customer_utterance"],
            },
            "campaign": GERMAN_CAMPAIGN,
            "language": "de",
        }
    return index


def candidate_items() -> list[dict[str, Any]]:
    matrix = read_json(PROD_049_DIR / "bridge_continue_candidate_matrix.json")["items"]
    return [item for item in matrix if item["bridge_then_continue_candidate"] is True]


def build_cases() -> list[dict[str, Any]]:
    index = current_case_index()
    cases = []
    for source in candidate_items():
        base = index[source["case_id"]]
        cases.append(
            {
                "case_id": source["case_id"],
                "source_finding_id": source["finding_id"],
                "language": source["language"],
                "customer_move_id": base["customer_move_id"],
                "sales_difficulty": source["sales_difficulty"],
                "customer_input": base["customer_input"],
                "campaign": base["campaign"],
                "current_call_control": source["current_call_control"],
                "proposed_call_control": "bridge-then-continue",
                "example_type": "synthetic_softening_regression_case",
                "source_quote": False,
                "from_single_transcript": False,
            }
        )
    return cases


def proposed_response_for(current: dict[str, Any]) -> str:
    key = (current["sales_difficulty"], current["response_language"])
    return PROPOSED_RESPONSE_TEXT[key]


def legacy_baseline_decision(case: dict[str, Any]) -> dict[str, Any]:
    live_shape = build_runtime_decision(case, campaign=case["campaign"])
    baseline = deepcopy(live_shape)
    baseline["call_control"] = case["current_call_control"]
    baseline["next_action"] = "create-follow-up-task"
    baseline["background_modules"] = ["follow-up-task-write"]
    baseline["bridge_response"] = None
    baseline["agent_response"] = LEGACY_BASELINE_RESPONSE_TEXT[(case["sales_difficulty"], case["language"])]
    baseline["rationale"] = "PROD-050 frozen pre-PROD-051 baseline from the source call-control review."
    return baseline


def proposed_decision(current: dict[str, Any]) -> dict[str, Any]:
    proposed = deepcopy(current)
    proposed["call_control"] = "bridge-then-continue"
    proposed["agent_response"] = proposed_response_for(current)
    proposed["rationale"] = (
        "PROD-050 proposed softening: preserve the safe answer content, remove terminal phrasing, and continue only with a low-pressure optional next step."
    )
    proposed["response_text_change_applied"] = True
    proposed["runtime_change_applied"] = False
    return proposed


def contains_any(text: str, markers: list[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def answered_or_acknowledged(decision: dict[str, Any]) -> bool:
    response = decision["agent_response"].lower()
    difficulty = decision["sales_difficulty"]
    if difficulty == "price-first-direct":
        return contains_any(response, ["29", "price", "pricing", "preis", "euro", "kosten"])
    if difficulty == "written-info-request":
        return contains_any(response, ["send", "summary", "written", "sende", "zusammenfassung", "schriftlich"])
    if difficulty in {"stakeholder-review", "partner-review"}:
        return contains_any(response, ["summary", "review", "person", "zusammenfassung", "prüf", "person"])
    return False


def has_low_pressure_continuation(decision: dict[str, Any]) -> bool:
    response_language = decision["response_language"]
    return contains_any(decision["agent_response"], LOW_PRESSURE_CONTINUATION_MARKERS[response_language])


def evaluate_result(case: dict[str, Any]) -> dict[str, Any]:
    current = legacy_baseline_decision(case)
    proposed = proposed_decision(current)
    proposed_response = proposed["agent_response"]
    pressure_violation = contains_any(proposed_response, PRESSURE_MARKERS)
    payment_violation = contains_any(proposed_response, PAYMENT_COLLECTION_MARKERS)
    contract_violation = contains_any(proposed_response, CONTRACT_SIGNING_MARKERS)
    unsupported_violation = contains_any(proposed_response, UNSUPPORTED_CLAIM_MARKERS)
    current_answered = answered_or_acknowledged(current)
    proposed_answered = answered_or_acknowledged(proposed)
    low_pressure_continuation = has_low_pressure_continuation(proposed)
    terminal_closing_phrase = contains_any(proposed_response, TERMINAL_CLOSING_MARKERS)
    response_text_changed = proposed_response != current["agent_response"]
    passed = (
        current["sales_difficulty"] == case["sales_difficulty"]
        and current["call_control"] == "end-call"
        and proposed["call_control"] == "bridge-then-continue"
        and proposed["sales_difficulty"] == current["sales_difficulty"]
        and response_text_changed
        and current_answered
        and proposed_answered
        and low_pressure_continuation
        and not terminal_closing_phrase
        and not pressure_violation
        and not payment_violation
        and not contract_violation
        and not unsupported_violation
    )
    return {
        "case_id": case["case_id"],
        "source_finding_id": case["source_finding_id"],
        "language": case["language"],
        "customer_move_id": case["customer_move_id"],
        "sales_difficulty": case["sales_difficulty"],
        "customer_utterance": case["customer_input"]["transcript"],
        "current_runtime_decision": current,
        "proposed_runtime_decision": proposed,
        "current_answered_or_acknowledged": current_answered,
        "answered_or_acknowledged_before_continue": proposed_answered,
        "current_safe_answer_preserved": proposed_answered,
        "proposed_response_text_changed": response_text_changed,
        "low_pressure_continuation_prompt": low_pressure_continuation,
        "terminal_closing_phrase_in_proposed": terminal_closing_phrase,
        "pressure_violation": pressure_violation,
        "payment_collection_violation": payment_violation,
        "contract_signing_violation": contract_violation,
        "unsupported_claim_violation": unsupported_violation,
        "runtime_change_applied": False,
        "passed": passed,
    }


def boundary_case(case_id: str, move_id: str, transcript: str, expected_call_control: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "customer_move_id": move_id,
        "customer_input": {"input_type": "speech", "stage": "relevance-check", "transcript": transcript},
        "campaign": TEST_CAMPAIGN,
        "expected_call_control": expected_call_control,
    }


def proposed_boundary_decision(current: dict[str, Any]) -> dict[str, Any]:
    proposed = deepcopy(current)
    proposed["runtime_change_applied"] = False
    return proposed


def build_boundary_results() -> list[dict[str, Any]]:
    results = []
    for case_id, move_id, transcript, expected_call_control in PROTECTED_BOUNDARY_SPECS:
        case = boundary_case(case_id, move_id, transcript, expected_call_control)
        current = build_runtime_decision(case, campaign=TEST_CAMPAIGN)
        proposed = proposed_boundary_decision(current)
        passed = (
            current["call_control"] == expected_call_control
            and proposed["call_control"] == expected_call_control
            and proposed["call_control"] != "bridge-then-continue"
        )
        results.append(
            {
                "case_id": case_id,
                "customer_move_id": move_id,
                "customer_utterance": transcript,
                "expected_call_control": expected_call_control,
                "current_runtime_decision": current,
                "proposed_runtime_decision": proposed,
                "passed": passed,
            }
        )
    return results


def build_change_summary(results: list[dict[str, Any]], boundaries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "selected_sales_difficulties": sorted(SELECTED_DIFFICULTIES),
        "proposed_runtime_change": (
            "Map selected non-refusal safe end-call outcomes to bridge-then-continue and replace terminal safe-close "
            "phrasing with low-pressure optional continuation text while preserving approved answer content."
        ),
        "runtime_change_applied_by_this_checkpoint": False,
        "response_text_change_recommended": True,
        "call_control_definition_update_required": True,
        "protected_boundaries_preserved": all(item["passed"] for item in boundaries),
        "softening_regression_passed": all(item["passed"] for item in results),
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        "implementation_requirements_for_next_checkpoint": [
            "Change only selected price-first, written-info, stakeholder-review, and partner-review style outcomes.",
            "Apply the low-pressure continuation text together with the call-control mapping; do not set bridge-then-continue on terminal wording.",
            "Update the call-control definition if bridge-then-continue remains the chosen value for answer-then-continue cases rather than lookup-only cases.",
            "Do not change customer-move classification, retrieval defaults, provider calls, voice playback, or production promotion.",
            "Keep support, cancellation, do-not-call, human request, email-only, payment/scam safety, sale-ready, and callback request protections unchanged.",
            "Re-run historical validators and update only expectations that intentionally move from end-call to bridge-then-continue.",
        ],
    }


def build_summary(results: list[dict[str, Any]], boundaries: list[dict[str, Any]]) -> dict[str, Any]:
    difficulty_counts = Counter(item["sales_difficulty"] for item in results)
    summary = {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_statuses": source_statuses(),
        "source_bridge_candidate_count": len(candidate_items()),
        "softening_regression_case_count": len(results),
        "softening_regression_pass_count": sum(1 for item in results if item["passed"]),
        "softening_regression_fail_count": sum(1 for item in results if not item["passed"]),
        "selected_sales_difficulty_count": len(difficulty_counts),
        "selected_sales_difficulty_counts": dict(sorted(difficulty_counts.items())),
        "protected_boundary_probe_count": len(boundaries),
        "protected_boundary_pass_count": sum(1 for item in boundaries if item["passed"]),
        "current_runtime_unchanged_count": sum(1 for item in results if item["current_runtime_decision"]["call_control"] == "end-call"),
        "proposed_bridge_then_continue_count": sum(
            1 for item in results if item["proposed_runtime_decision"]["call_control"] == "bridge-then-continue"
        ),
        "current_safe_answer_preserved_count": sum(1 for item in results if item["current_safe_answer_preserved"]),
        "proposed_response_text_changed_count": sum(1 for item in results if item["proposed_response_text_changed"]),
        "low_pressure_continuation_prompt_count": sum(1 for item in results if item["low_pressure_continuation_prompt"]),
        "terminal_closing_phrase_in_proposed_count": sum(1 for item in results if item["terminal_closing_phrase_in_proposed"]),
        "pressure_violation_count": sum(1 for item in results if item["pressure_violation"]),
        "unsupported_claim_violation_count": sum(1 for item in results if item["unsupported_claim_violation"]),
        "payment_collection_violation_count": sum(1 for item in results if item["payment_collection_violation"]),
        "contract_signing_violation_count": sum(1 for item in results if item["contract_signing_violation"]),
        "support_cancellation_do_not_call_softened": False,
        "runtime_change_recommended": all(item["passed"] for item in results) and all(item["passed"] for item in boundaries),
        "runtime_change_applied_by_this_checkpoint": False,
        "response_text_change_recommended": True,
        "call_control_definition_update_required": True,
        "recommended_next_checkpoint": NEXT_CHECKPOINT_ID,
        **BOUNDARY_FLAGS,
    }
    return summary


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        f"- Checkpoint id: `{CHECKPOINT_ID}`",
        f"- Source checkpoint: `{SOURCE_CHECKPOINT_ID}`",
        f"- Softening regression cases: `{summary['softening_regression_case_count']}`",
        f"- Softening regression passes: `{summary['softening_regression_pass_count']}`",
        f"- Protected boundary probes: `{summary['protected_boundary_pass_count']} / {summary['protected_boundary_probe_count']}`",
        f"- Low-pressure continuation prompts: `{summary['low_pressure_continuation_prompt_count']}`",
        f"- Terminal closing phrases in proposed responses: `{summary['terminal_closing_phrase_in_proposed_count']}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Call-control behavior changed: `{str(summary['call_control_behavior_changed']).lower()}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- LLM used: `{str(summary['llm_used']).lower()}`",
        f"- Private data read: `{str(summary['private_data_read']).lower()}`",
        f"- Production runtime promotion allowed: `{str(summary['production_runtime_promotion_allowed']).lower()}`",
        "",
        "## Result",
        "",
        "The proposed `bridge-then-continue` softening passes for all selected non-refusal candidates by preserving approved answer content, replacing terminal safe-close phrasing with low-pressure optional continuation text, and preserving protected boundaries. This checkpoint does not apply the runtime change.",
        "",
        "## Selected Groups",
        "",
    ]
    for difficulty, count in summary["selected_sales_difficulty_counts"].items():
        lines.append(f"- `{difficulty}`: `{count}` proposed case(s)")
    lines.extend(
        [
            "",
            "## Next",
            "",
            f"Recommended next checkpoint: `{NEXT_CHECKPOINT_ID}`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_html(summary: dict[str, Any], results: list[dict[str, Any]], boundaries: list[dict[str, Any]]) -> str:
    result_rows = []
    for item in results:
        result_rows.append(
            "<tr>"
            f"<td>{html.escape(item['language'])}</td>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['sales_difficulty'])}</td>"
            f"<td>{html.escape(item['current_runtime_decision']['call_control'])}</td>"
            f"<td>{html.escape(item['proposed_runtime_decision']['call_control'])}</td>"
            f"<td>{html.escape(item['current_runtime_decision']['agent_response'])}</td>"
            f"<td>{html.escape(item['proposed_runtime_decision']['agent_response'])}</td>"
            f"<td>{str(item['passed']).lower()}</td>"
            "</tr>"
        )
    boundary_rows = []
    for item in boundaries:
        boundary_rows.append(
            "<tr>"
            f"<td>{html.escape(item['case_id'])}</td>"
            f"<td>{html.escape(item['expected_call_control'])}</td>"
            f"<td>{html.escape(item['proposed_runtime_decision']['call_control'])}</td>"
            f"<td>{str(item['passed']).lower()}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-050 Safe Call-Control Softening Regression</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #edf2f7; }}
  </style>
</head>
<body>
  <h1>PROD-050 Safe Call-Control Softening Regression</h1>
  <p>Runtime behavior changed: false. Call-control behavior changed: false. Provider calls made: false. Production runtime promotion allowed: false.</p>
  <p>The proposed bridge-then-continue mapping plus low-pressure continuation text passed {summary['softening_regression_pass_count']} of {summary['softening_regression_case_count']} selected non-refusal cases.</p>
  <h2>Softening Regression Cases</h2>
  <table>
    <thead><tr><th>Language</th><th>Case</th><th>Sales difficulty</th><th>Current</th><th>Proposed</th><th>Current response</th><th>Proposed response</th><th>Passed</th></tr></thead>
    <tbody>{''.join(result_rows)}</tbody>
  </table>
  <h2>Protected Boundary Probes</h2>
  <table>
    <thead><tr><th>Case</th><th>Expected</th><th>Proposed</th><th>Passed</th></tr></thead>
    <tbody>{''.join(boundary_rows)}</tbody>
  </table>
</body>
</html>
"""


def build_payload() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    cases = build_cases()
    results = [evaluate_result(case) for case in cases]
    boundaries = build_boundary_results()
    change_summary = build_change_summary(results, boundaries)
    summary = build_summary(results, boundaries)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_id": NEXT_CHECKPOINT_ID,
        "validation": {
            "passed": all(summary["source_result_statuses"].values())
            and summary["softening_regression_case_count"] == 22
            and summary["softening_regression_fail_count"] == 0
            and summary["protected_boundary_pass_count"] == summary["protected_boundary_probe_count"],
        },
        "outputs": {
            "result": rel(OUT_DIR / "result.json"),
            "report": rel(OUT_DIR / "report.md"),
            "cases": rel(OUT_DIR / "softening_regression_cases.json"),
            "results": rel(OUT_DIR / "softening_regression_results.json"),
            "boundary_results": rel(OUT_DIR / "protected_boundary_results.json"),
            "change_summary": rel(OUT_DIR / "proposed_runtime_change_summary.json"),
            "review_html": rel(OUT_DIR / "prod_050_review.html"),
        },
        "summary": summary,
    }
    return payload, cases, results, boundaries, change_summary


def main() -> None:
    payload, cases, results, boundaries, change_summary = build_payload()
    write_json(OUT_DIR / "softening_regression_cases.json", {"checkpoint_id": CHECKPOINT_ID, "items": cases})
    write_json(OUT_DIR / "softening_regression_results.json", {"checkpoint_id": CHECKPOINT_ID, "items": results})
    write_json(OUT_DIR / "protected_boundary_results.json", {"checkpoint_id": CHECKPOINT_ID, "items": boundaries})
    write_json(OUT_DIR / "proposed_runtime_change_summary.json", change_summary)
    write_text(OUT_DIR / "report.md", build_report(payload["summary"]))
    write_text(OUT_DIR / "prod_050_review.html", build_html(payload["summary"], results, boundaries))
    write_json(OUT_DIR / "result.json", payload)
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": payload["validation"], "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
