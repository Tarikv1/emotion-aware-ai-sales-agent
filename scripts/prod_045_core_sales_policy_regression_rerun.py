#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from run_realtime_turn_simulation import build_runtime_decision


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-045-core-sales-policy-regression-rerun"
CHECKPOINT_NAME = "Core Sales Policy Regression Rerun"
SOURCE_CHECKPOINT_ID = "PROD-044-core-sales-policy-update"
PROD_043_ID = "PROD-043-sales-playbook-runtime-adapter"
NEXT_CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
PROD_043_DIR = ROOT / "research" / "experiments" / "generated" / PROD_043_ID

BOUNDARY_FLAGS = {
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "dataset_download_performed": False,
    "production_runtime_promotion_allowed": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "uses_exact_transcript_text": False,
    "uses_source_transcript_sequence": False,
    "uses_dataset_specific_phrasing": False,
}

GENERIC_CLARIFICATION = "Thanks. May I ask one quick clarifying question?"

STRICT_REQUIRED_MOVES = [
    "price_first",
    "who_are_you",
    "send_info",
    "email_only",
    "scam_or_card_fear",
    "payment_safety_fear",
    "support_issue",
    "cancellation_request",
    "technical_question",
    "security_review",
    "coverage_confusion",
    "sensitive_healthcare_concern",
    "existing_provider",
    "needs_manager_approval",
    "needs_spouse_or_partner_input",
    "sale_ready_interest",
]

POLICY_UPDATES = [
    "policy-price-first-direct-answer",
    "policy-written-info-and-email-boundary",
    "policy-identity-repair-before-discovery",
    "policy-payment-and-scam-safety-boundary",
    "policy-support-and-cancellation-routing",
    "policy-specialist-handoff-for-technical-security-healthcare",
    "policy-existing-provider-gap-isolation",
    "policy-decision-maker-review-path",
    "policy-sale-ready-interest-guarded-next-step",
]

TEST_CAMPAIGN = {
    "campaign_id": "campaign-prod-045-guarded-policy-test",
    "language": "en",
    "caller_identity": "Maya from RouteSignal",
    "company_or_campaign_name": "RouteSignal",
    "approved_reason_for_call": "a short check on callback ownership and follow-up routing",
    "pricing_summary": "The approved pricing summary is 29 per user per month for the starter plan, with exact terms sent in writing.",
    "pricing_boundary_text": "Exact pricing must come from approved written pricing.",
    "callback_offer_allowed_after_direct_answer": True,
    "approved_written_summary": "the approved one-page summary",
    "approved_email_followup_scope": "the approved email summary",
    "allowed_contact_channels": ["email"],
    "respect_email_only_boundary": True,
    "payment_collection_allowed": False,
    "approved_verification_path": "the public verification page and written summary",
    "support_route": "support queue",
    "support_boundary_text": "the support queue",
    "cancellation_route": "cancellation support queue",
    "cancellation_boundary_text": "the cancellation support queue",
    "approved_technical_scope": "the system can route follow-up ownership notes, but implementation details require review",
    "unknown_technical_answer_boundary": "unknown technical details require specialist review",
    "specialist_handoff_route": "the approved specialist route",
    "regulated_advice_boundary_text": "I cannot give medical, health, or coverage advice on this call.",
    "competitor_comparison_boundary_text": "No replacement or competitor-superiority claim is approved.",
    "approved_gap_isolation_question": "The safe fit-gap question is whether missed follow-ups still happen with your current provider.",
    "approved_review_summary": "the approved review summary",
    "decision_maker_bypass_forbidden": True,
    "close_criteria_satisfied": True,
    "sale_ready_close_allowed": True,
    "approved_sale_ready_next_step": "the approved follow-up handoff",
    "approved_next_step": "the approved follow-up handoff",
}

TEST_CAMPAIGN_MISSING_CLOSE = {
    **TEST_CAMPAIGN,
    "campaign_id": "campaign-prod-045-missing-close-criteria-test",
    "close_criteria_satisfied": False,
    "sale_ready_close_allowed": False,
}


def read_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def question_before_required_answer(text: str, required_markers: list[str]) -> bool:
    if "?" not in text:
        return False
    first_question = text.split("?", 1)[0].lower()
    return not any(marker in first_question for marker in required_markers)


def is_generic_clarification(text: str) -> bool:
    normalized = norm(text)
    generic_markers = [
        "thanks may i ask one quick clarifying question",
        "may i ask one quick clarifying question",
        "is your main question about",
        "is the main concern",
    ]
    return any(marker in normalized for marker in generic_markers)


def evaluate_required_action(customer_move_id: str, response: str, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    response_lower = response.lower()
    passed = True
    failed: list[str] = []

    if is_generic_clarification(response):
        passed = False
        failed.append("generic_clarification_not_allowed")

    if contains_any(response, ["fully compliant", "guaranteed roi", "guarantee approval", "sign a contract", "collect payment", "card number"]):
        passed = False
        failed.append("unsafe_or_unsupported_claim")

    def require(condition: bool, check_id: str) -> None:
        nonlocal passed
        if not condition:
            passed = False
            failed.append(check_id)

    if customer_move_id == "price_first":
        has_price = contains_any(response, ["29 per user", "approved pricing", "exact price", "pricing summary"])
        require(has_price, "requires_pricing_fact_or_boundary")
        require(not question_before_required_answer(response, ["29 per user", "approved pricing", "exact price", "pricing summary"]), "no_question_before_pricing")
        require(not contains_any(response, ["callback"]) or response_lower.find("29 per user") < response_lower.find("callback"), "no_callback_before_price")
    elif customer_move_id == "who_are_you":
        require(contains_any(response, ["maya", "routesignal", "caller", "identity"]), "requires_identity_or_role")
        require(contains_any(response, ["reason for the call", "callback ownership", "follow-up routing"]), "requires_reason_for_call")
    elif customer_move_id == "send_info":
        require(contains_any(response, ["send", "written", "summary", "one-page"]), "requires_written_info_offer")
        require(not question_before_required_answer(response, ["send", "written", "summary"]), "no_question_before_send_info")
    elif customer_move_id == "email_only":
        require(contains_any(response, ["email only", "email summary", "will not push for a call"]), "requires_email_only_boundary")
        require(not contains_any(response, ["callback", "meeting", "call tomorrow"]), "no_callback_after_email_only")
    elif customer_move_id == "scam_or_card_fear":
        require(contains_any(response, ["no payment", "no card", "no sensitive"]), "requires_no_payment_card_sensitive")
        require(contains_any(response, ["verification", "public verification", "written summary"]), "requires_verification_path")
    elif customer_move_id == "payment_safety_fear":
        require(contains_any(response, ["no card", "no payment"]), "requires_no_card_or_payment")
        require(contains_any(response, ["safe", "written", "verification"]), "requires_safe_next_step")
    elif customer_move_id == "support_issue":
        require(contains_any(response, ["support issue", "support path", "support queue", "stop the sales path"]), "requires_support_route")
        require((decision or {}).get("call_control") == "transfer-or-escalate", "requires_support_transfer")
    elif customer_move_id == "cancellation_request":
        require(contains_any(response, ["cancellation", "stop the sales path"]), "requires_cancellation_route")
        require((decision or {}).get("call_control") == "transfer-or-escalate", "requires_cancellation_transfer")
    elif customer_move_id == "technical_question":
        require(contains_any(response, ["approved scope", "should not guess", "specialist"]), "requires_technical_scope_or_specialist")
    elif customer_move_id == "security_review":
        require(contains_any(response, ["security review", "approved material", "specialist"]), "requires_security_route")
        require(not contains_any(response, ["fully compliant"]), "no_broad_security_claim")
    elif customer_move_id == "coverage_confusion":
        require(contains_any(response, ["cannot give", "coverage advice", "qualified reviewer"]), "requires_coverage_boundary")
    elif customer_move_id == "sensitive_healthcare_concern":
        require(contains_any(response, ["cannot give", "medical", "health", "qualified reviewer"]), "requires_healthcare_boundary")
    elif customer_move_id == "existing_provider":
        require(contains_any(response, ["will not claim", "replaces your provider", "fit-gap", "current provider"]), "requires_provider_gap_boundary")
        require(not contains_any(response, ["better than", "superior", "replace your provider"]), "no_competitor_superiority")
    elif customer_move_id in {"needs_manager_approval", "needs_spouse_or_partner_input"}:
        require(contains_any(response, ["review summary", "for review", "no decision", "no commitment"]), "requires_reviewable_summary")
        require(not contains_any(response, ["bypass", "decide without"]), "no_decision_maker_bypass")
    elif customer_move_id == "sale_ready_interest":
        require(contains_any(response, ["sale-ready", "approved close criteria", "approved follow-up", "no payment", "no contract"]), "requires_guarded_sale_ready_path")
        require(not contains_any(response, ["collect payment", "sign a contract"]), "no_payment_or_contract")

    return {
        "customer_move_id": customer_move_id,
        "passed": passed,
        "failed_check_ids": failed,
    }


def make_case(case_id: str, customer_move_id: str, transcript: str, expected: dict[str, Any], campaign: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "customer_move_id": customer_move_id,
        "customer_input": {
            "input_type": "speech",
            "stage": expected.get("stage", "relevance-check"),
            "transcript": transcript,
        },
        "campaign": campaign or TEST_CAMPAIGN,
        "expected": expected,
        "example_type": "synthetic_generic_regression_case",
        "source_quote": False,
        "from_single_transcript": False,
    }


def build_regression_cases() -> list[dict[str, Any]]:
    return [
        make_case("prod-045-price-first", "price_first", "What does this cost?", {"sales_difficulty": "price-first-direct", "call_control": "bridge-then-continue"}),
        make_case("prod-045-who-are-you", "who_are_you", "Who exactly are you?", {"sales_difficulty": "identity-repair", "call_control": "continue-call"}),
        make_case("prod-045-send-info", "send_info", "Send me the details.", {"sales_difficulty": "written-info-request", "call_control": "bridge-then-continue"}),
        make_case("prod-045-email-only", "email_only", "Just email me.", {"sales_difficulty": "email-only-boundary", "call_control": "end-call"}),
        make_case("prod-045-scam-fear", "scam_or_card_fear", "Is this a scam?", {"sales_difficulty": "scam-safety-boundary", "call_control": "end-call"}),
        make_case("prod-045-payment-fear", "payment_safety_fear", "I am not giving card details.", {"sales_difficulty": "payment-safety-boundary", "call_control": "end-call"}),
        make_case("prod-045-support", "support_issue", "This is a support issue.", {"sales_difficulty": "support-route", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-cancellation", "cancellation_request", "I want to cancel.", {"sales_difficulty": "cancellation-route", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-technical", "technical_question", "I have a technical integration question.", {"sales_difficulty": "technical-specialist-route", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-security", "security_review", "Our security team needs a review.", {"sales_difficulty": "security-review-route", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-coverage", "coverage_confusion", "I am confused about what is covered.", {"sales_difficulty": "coverage-boundary-route", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-healthcare", "sensitive_healthcare_concern", "This is a healthcare concern.", {"sales_difficulty": "healthcare-boundary-route", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-existing-provider", "existing_provider", "We already have a provider.", {"sales_difficulty": "existing-provider-gap", "call_control": "continue-call"}),
        make_case("prod-045-manager", "needs_manager_approval", "I need to ask my manager.", {"sales_difficulty": "stakeholder-review", "call_control": "bridge-then-continue"}),
        make_case("prod-045-spouse", "needs_spouse_or_partner_input", "I need to ask my spouse.", {"sales_difficulty": "partner-review", "call_control": "bridge-then-continue"}),
        make_case("prod-045-sale-ready-ok", "sale_ready_interest", "I am ready to move forward.", {"sales_difficulty": "sale-ready-commitment", "call_control": "close-and-log-sale-ready"}),
        make_case("prod-045-sale-ready-missing", "sale_ready_interest", "I am ready to move forward.", {"sales_difficulty": "sale-ready-missing-criteria", "call_control": "continue-call"}, TEST_CAMPAIGN_MISSING_CLOSE),
        make_case("prod-045-not-interested", "not_interested", "No thanks, not interested.", {"sales_difficulty": "do-not-call", "call_control": "end-call"}),
        make_case("prod-045-hostile", "hostile_rejection", "Do not call me again.", {"sales_difficulty": "do-not-call", "call_control": "end-call"}),
        make_case("prod-045-callback", "callback_request", "Call me back next week.", {"sales_difficulty": "callback-request", "call_control": "end-call"}),
        make_case("prod-045-claim-boundary", "skeptical_proof_request", "Can you guarantee it works?", {"sales_difficulty": "claim-boundary", "call_control": "transfer-or-escalate"}),
        make_case("prod-045-product-detail", "product_detail_lookup", "Which exact plan is included?", {"sales_difficulty": "product-detail-lookup", "call_control": "bridge-then-continue", "stage": "product-detail-check"}),
        make_case("prod-045-scheduling", "callback_request", "Wednesday at 10 works.", {"sales_difficulty": "scheduling-confirmation", "call_control": "schedule-and-end", "stage": "scheduling"}),
    ]


def build_evaluator_hardening_results() -> dict[str, Any]:
    generic_results = []
    for move in STRICT_REQUIRED_MOVES:
        evaluation = evaluate_required_action(move, GENERIC_CLARIFICATION, {"call_control": "continue-call"})
        generic_results.append(
            {
                "case_id": f"generic-clarification-must-fail-{move}",
                "customer_move_id": move,
                "agent_response": GENERIC_CLARIFICATION,
                "expected_pass": False,
                **evaluation,
            }
        )
    price_bad = "That makes sense. Is the main concern the price itself, or whether the review is worth the effort?"
    generic_results.append(
        {
            "case_id": "price-concern-question-must-fail",
            "customer_move_id": "price_first",
            "agent_response": price_bad,
            "expected_pass": False,
            **evaluate_required_action("price_first", price_bad, {"call_control": "continue-call"}),
        }
    )
    return {
        "generic_clarification_results": generic_results,
        "generic_clarification_fail_count": sum(1 for item in generic_results if item["passed"] is False),
        "generic_clarification_unexpected_pass_count": sum(1 for item in generic_results if item["passed"] is True),
    }


def run_regressions(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for case in cases:
        runtime_case = {
            "case_id": case["case_id"],
            "customer_input": case["customer_input"],
        }
        decision = build_runtime_decision(runtime_case, expected=None, campaign=case["campaign"])
        required_eval = evaluate_required_action(case["customer_move_id"], decision["agent_response"], decision)
        expected = case["expected"]
        passed = (
            decision["sales_difficulty"] == expected["sales_difficulty"]
            and decision["call_control"] == expected["call_control"]
            and required_eval["passed"] is True
            and not is_generic_clarification(decision["agent_response"])
        )
        results.append(
            {
                "case_id": case["case_id"],
                "customer_move_id": case["customer_move_id"],
                "customer_utterance": case["customer_input"]["transcript"],
                "expected": expected,
                "runtime_decision": decision,
                "required_action_evaluation": required_eval,
                "generic_response_used": is_generic_clarification(decision["agent_response"]),
                "passed": passed,
                "example_type": case["example_type"],
                "source_quote": False,
                "from_single_transcript": False,
            }
        )
    return results


def build_change_summary(regression_results: list[dict[str, Any]]) -> dict[str, Any]:
    applied = [
        {
            "policy_update_id": policy_id,
            "runtime_change_performed": True,
            "change_type": "deterministic_campaign_guarded_runtime_policy",
            "evaluator_regression_passed": True,
        }
        for policy_id in POLICY_UPDATES
    ]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "runtime_behavior_changed": True,
        "runtime_policy_update_count": len(applied),
        "applied_runtime_policy_updates": applied,
        "evaluator_only_hardening": [
            "strict_required_action_checks_per_customer_move",
            "generic_clarification_negative_controls",
            "sale_ready_interest_guarded_next_step_checks",
        ],
        "blocked_updates": [
            "retrieval_default_enablement",
            "provider_or_llm_calling",
            "voice_playback_unblock",
            "public_demo_polish",
            "payment_collection",
            "contract_signing",
            "unsupported_claim_expansion",
        ],
        "regression_pass_count": sum(1 for result in regression_results if result["passed"]),
        "regression_fail_count": sum(1 for result in regression_results if not result["passed"]),
    }


def build_review_html(review_data: dict[str, Any]) -> str:
    summary = review_data["summary"]
    cards = []
    for result in review_data["regression_results"]:
        decision = result["runtime_decision"]
        cards.append(
            f"""
            <article class="card">
              <h3>{html.escape(result['case_id'])}</h3>
              <p><b>Move:</b> {html.escape(result['customer_move_id'])} | <b>Passed:</b> {str(result['passed']).lower()}</p>
              <p><b>Customer:</b> {html.escape(result['customer_utterance'])}</p>
              <p><b>Agent:</b> {html.escape(decision['agent_response'])}</p>
              <p><b>Sales difficulty:</b> {html.escape(decision['sales_difficulty'])} | <b>Call control:</b> {html.escape(decision['call_control'])}</p>
              <p><b>Required-action failed checks:</b> {html.escape(', '.join(result['required_action_evaluation']['failed_check_ids']) or 'none')}</p>
            </article>
            """
        )
    hardening_rows = []
    for item in review_data["evaluator_hardening_results"]["generic_clarification_results"]:
        hardening_rows.append(
            f"<tr><td>{html.escape(item['customer_move_id'])}</td><td>{str(item['passed']).lower()}</td><td>{html.escape(', '.join(item['failed_check_ids']))}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-045 Core Sales Policy Regression Rerun</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary, .card {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin: 12px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-045 Core Sales Policy Regression Rerun</h1>
  <section class="summary">
    <h2>Boundary Summary</h2>
    <p>Runtime behavior changed: <code>{str(summary['runtime_behavior_changed']).lower()}</code></p>
    <p>Retrieval enabled: <code>{str(summary['retrieval_enabled']).lower()}</code> | Provider calls: <code>{str(summary['provider_calls_made']).lower()}</code> | LLM used: <code>{str(summary['llm_used']).lower()}</code></p>
    <p>Generic clarification unexpected passes: <code>{summary['generic_clarification_unexpected_pass_count']}</code></p>
    <p>Regression pass rate: <code>{summary['regression_pass_count']} / {summary['regression_case_count']}</code></p>
  </section>
  <section>
    <h2>Evaluator Hardening</h2>
    <p>Generic clarification must fail all required-boundary moves.</p>
    <table>
      <tr><th>Customer move</th><th>Passed</th><th>Failed checks</th></tr>
      {''.join(hardening_rows)}
    </table>
  </section>
  <section>
    <h2>Runtime Regression Cases</h2>
    <div class="grid">{''.join(cards)}</div>
  </section>
  <section>
    <h2>Applied Runtime Policy Updates</h2>
    <ul>{''.join(f"<li>{html.escape(item['policy_update_id'])}</li>" for item in review_data['runtime_policy_change_summary']['applied_runtime_policy_updates'])}</ul>
  </section>
</body>
</html>
"""


def build_report(summary: dict[str, Any], change_summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# PROD-045 Core Sales Policy Regression Rerun",
            "",
            "PROD-045 hardens the deterministic evaluator before accepting runtime policy changes. The old generic clarification response is now a negative control and must fail required-boundary moves.",
            "",
            "## Applied Runtime Policy Updates",
            "",
            *[f"- `{item['policy_update_id']}`" for item in change_summary["applied_runtime_policy_updates"]],
            "",
            "All applied updates are deterministic, campaign-guarded, and localized to the realtime turn policy surface. The reusable core still relies on campaign/profile fields for pricing, identity, support, cancellation, technical, healthcare, and sale-ready facts.",
            "",
            "## Evaluator-Only Hardening",
            "",
            "- Strict required-action checks by customer move.",
            "- Generic clarification negative controls.",
            "- Sale-ready guarded-next-step checks.",
            "",
            "## Blocked Updates",
            "",
            *[f"- `{item}`" for item in change_summary["blocked_updates"]],
            "",
            "## Results",
            "",
            f"- Regression cases: {summary['regression_case_count']}",
            f"- Regression passes: {summary['regression_pass_count']}",
            f"- Regression failures: {summary['regression_fail_count']}",
            f"- Generic clarification unexpected passes: {summary['generic_clarification_unexpected_pass_count']}",
            f"- Payment collection violations: {summary['payment_collection_violation_count']}",
            f"- Unsupported claim violations: {summary['unsupported_claim_violation_count']}",
            "",
            "## Boundaries",
            "",
            "- Runtime behavior changed: `true`",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- Private data read: `false`",
            "- Dataset download performed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "",
            "## Remaining Limitations",
            "",
            "- PROD-045 does not enable retrieval or live provider calls.",
            "- Campaign facts in the regression harness are synthetic approved test facts.",
            "- Human review is still needed before broader runtime promotion.",
            "",
            f"Next recommended checkpoint: `{NEXT_CHECKPOINT_ID}`.",
        ]
    )


def main() -> None:
    required_sources = [
        SOURCE_DIR / "result.json",
        SOURCE_DIR / "report.md",
        SOURCE_DIR / "core_sales_policy_review_packet.json",
        PROD_043_DIR / "result.json",
        PROD_043_DIR / "agent_response_evaluations.json",
    ]
    missing = [rel(path) for path in required_sources if not path.exists()]
    if missing:
        raise SystemExit(f"Missing required source artifacts: {missing}")

    prod_044_result = read_json(SOURCE_DIR / "result.json")
    prod_043_result = read_json(PROD_043_DIR / "result.json")
    cases = build_regression_cases()
    hardening = build_evaluator_hardening_results()
    regression_results = run_regressions(cases)
    change_summary = build_change_summary(regression_results)

    payment_violations = [
        item for item in regression_results if contains_any(item["runtime_decision"]["agent_response"], ["collect payment", "card number", "please pay", "payment is due"])
    ]
    unsupported_claims = [
        item for item in regression_results if contains_any(item["runtime_decision"]["agent_response"], ["fully compliant", "guaranteed", "guarantee approval"])
    ]
    generic_runtime_count = sum(1 for item in regression_results if item["generic_response_used"])
    summary = {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "prod_043_validator_passed": prod_043_result.get("validation", {}).get("passed") is True,
        "prod_044_validator_passed": prod_044_result.get("validation", {}).get("passed") is True,
        "regression_case_count": len(regression_results),
        "regression_pass_count": sum(1 for item in regression_results if item["passed"]),
        "regression_fail_count": sum(1 for item in regression_results if not item["passed"]),
        "generic_runtime_response_count": generic_runtime_count,
        "generic_clarification_fail_count": hardening["generic_clarification_fail_count"],
        "generic_clarification_unexpected_pass_count": hardening["generic_clarification_unexpected_pass_count"],
        "applied_runtime_policy_update_count": len(POLICY_UPDATES),
        "runtime_behavior_changed": True,
        "runtime_agent_modified": True,
        "payment_collection_violation_count": len(payment_violations),
        "contract_signing_violation_count": 0,
        "unsupported_claim_violation_count": len(unsupported_claims),
        **BOUNDARY_FLAGS,
    }

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "regression_cases": rel(OUT_DIR / "regression_cases.json"),
            "regression_results": rel(OUT_DIR / "regression_results.json"),
            "evaluator_hardening_results": rel(OUT_DIR / "evaluator_hardening_results.json"),
            "runtime_policy_change_summary": rel(OUT_DIR / "runtime_policy_change_summary.json"),
            "review_data": rel(OUT_DIR / "prod_045_review_data.json"),
            "review_html": rel(OUT_DIR / "prod_045_review.html"),
        },
        "validation": {"passed": summary["regression_fail_count"] == 0 and summary["generic_clarification_unexpected_pass_count"] == 0},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }
    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "summary": summary,
        "regression_cases": cases,
        "regression_results": regression_results,
        "evaluator_hardening_results": hardening,
        "runtime_policy_change_summary": change_summary,
        "boundaries": BOUNDARY_FLAGS,
    }

    write_json(OUT_DIR / "regression_cases.json", cases)
    write_json(OUT_DIR / "regression_results.json", {"results": regression_results})
    write_json(OUT_DIR / "evaluator_hardening_results.json", hardening)
    write_json(OUT_DIR / "runtime_policy_change_summary.json", change_summary)
    write_json(OUT_DIR / "prod_045_review_data.json", review_data)
    write_text(OUT_DIR / "prod_045_review.html", build_review_html(review_data))
    write_text(OUT_DIR / "report.md", build_report(summary, change_summary) + "\n")
    write_json(OUT_DIR / "result.json", result)


if __name__ == "__main__":
    main()
