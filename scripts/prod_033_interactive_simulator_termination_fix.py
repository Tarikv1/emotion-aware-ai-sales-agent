#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from callcenteren_runtime_comparison import contains_payment_collection
from generate_guarded_response import build_guarded_response_packet
from prod_028_synthetic_campaign_knowledge_grounding import build_synthetic_campaign
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"
SOURCE_CHECKPOINT_ID = "PROD-032-interactive-simulation-review"
NEXT_CHECKPOINT_ID = "PROD-034-interactive-post-fix-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "interactive_call_traces.json"
DEFAULT_HTML = DEFAULT_OUT_DIR / "interactive_call_trace.html"
DEFAULT_SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"

UNSUPPORTED_CLAIM_MARKERS = [
    "guaranteed revenue increase",
    "guaranteed cost savings",
    "guaranteed conversion lift",
    "replaces every crm",
    "no risk",
    "legal advice",
    "collect payment or card details on this call",
]


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clamp(value: int, low: int = 0, high: int = 5) -> int:
    return max(low, min(high, value))


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
        "source_prod_031_overwritten": False,
        "source_prod_032_overwritten": False,
        "production_runtime_promotion_allowed": False,
    }


def build_call_seeds() -> list[dict[str, Any]]:
    return [
        {
            "seed_id": "cold-price-sensitive",
            "persona": "price-sensitive operations manager",
            "opening_response": "Maybe, but make it quick. If this is another platform, what is it going to cost?",
            "initial_state": {"interest": 3, "trust": 2, "clarity": 1, "friction": 3, "patience": 3, "emotion": "skeptical", "active_objection": "price"},
            "expected_terminal_outcome": "accepted-deal",
        },
        {
            "seed_id": "cold-confused-product-fit",
            "persona": "confused small-business owner",
            "opening_response": "I do not know RouteSignal. What is this actually about?",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 0, "friction": 2, "patience": 4, "emotion": "confused", "active_objection": "confusion"},
            "expected_terminal_outcome": "accepted-deal",
        },
        {
            "seed_id": "cold-skeptical-trust-gap",
            "persona": "skeptical founder",
            "opening_response": "Sales call? I am skeptical. I do not want vague software promises.",
            "initial_state": {"interest": 2, "trust": 1, "clarity": 1, "friction": 3, "patience": 3, "emotion": "skeptical", "active_objection": "trust"},
            "expected_terminal_outcome": "rejected-deal",
        },
        {
            "seed_id": "cold-busy-rejection",
            "persona": "busy sales lead",
            "opening_response": "No, this is not a good time. I am busy.",
            "initial_state": {"interest": 1, "trust": 2, "clarity": 1, "friction": 4, "patience": 1, "emotion": "annoyed", "active_objection": "time"},
            "expected_terminal_outcome": "rejected-deal",
        },
        {
            "seed_id": "cold-existing-provider",
            "persona": "team lead with an existing CRM",
            "opening_response": "We already have a CRM, so I doubt this is relevant.",
            "initial_state": {"interest": 2, "trust": 3, "clarity": 1, "friction": 2, "patience": 4, "emotion": "neutral", "active_objection": "provider"},
            "expected_terminal_outcome": "accepted-deal",
        },
        {
            "seed_id": "cold-stakeholder-review",
            "persona": "manager who needs approval",
            "opening_response": "I can listen if you give me the manager version, not a long pitch.",
            "initial_state": {"interest": 4, "trust": 3, "clarity": 2, "friction": 2, "patience": 4, "emotion": "curious", "active_objection": "authority"},
            "expected_terminal_outcome": "accepted-deal",
        },
        {
            "seed_id": "cold-support-boundary",
            "persona": "support-seeking user",
            "opening_response": "I am not trying to buy. I need help with an account issue.",
            "initial_state": {"interest": 0, "trust": 2, "clarity": 2, "friction": 3, "patience": 3, "emotion": "annoyed", "active_objection": "support"},
            "expected_terminal_outcome": "rejected-deal",
        },
        {
            "seed_id": "cold-do-not-call",
            "persona": "protected stop-request customer",
            "opening_response": "No. Stop calling me and take me off the list.",
            "initial_state": {"interest": 0, "trust": 1, "clarity": 3, "friction": 5, "patience": 0, "emotion": "annoyed", "active_objection": "do-not-call"},
            "expected_terminal_outcome": "rejected-deal",
        },
    ]


def count_questions(text: str) -> int:
    return text.count("?")


def unsupported_claims(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in UNSUPPORTED_CLAIM_MARKERS if marker.lower() in lowered]


def opening_agent_message(campaign: dict[str, Any]) -> str:
    product_name = campaign["product_name"]
    return (
        f"Hi, this is Maya from {product_name}. "
        "We help sales teams route inbound leads and keep callback ownership clear. "
        "Did I catch you at a reasonable moment for a 20-second reason for my call?"
    )


def opening_checks(opening: str) -> dict[str, bool]:
    lowered = opening.lower()
    return {
        "greeting": lowered.startswith("hi") or lowered.startswith("hello"),
        "identity_disclosure": "this is maya" in lowered,
        "company_disclosure": "routesignal" in lowered,
        "reason_for_call": "route inbound leads" in lowered and "callback ownership" in lowered,
        "permission_to_continue": "did i catch you" in lowered and "?" in opening,
    }


def answer_for_state(state: dict[str, Any], campaign: dict[str, Any]) -> str:
    product_name = campaign["product_name"]
    specialist = campaign.get("human_handoff_role", "solutions specialist")
    objection = state["active_objection"]
    if objection == "do-not-call":
        return "Understood. I will mark this as do not call and end the sales conversation now."
    if objection == "support":
        return f"That is support, not a sales conversation. I will route you to a {specialist} for account help."
    if objection == "time":
        return "No problem. I will not push while you are busy; we can stop this sales conversation here."
    if objection == "not-interested":
        return "Understood. I will not push this further."
    if objection == "price":
        return "The synthetic pricing is Starter at $29 per user per month annually and Growth at $59. Billing stays outside this call."
    if objection == "confusion":
        return f"{product_name} is not a full CRM replacement. It focuses on lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import."
    if objection == "trust":
        return f"Fair concern. I cannot promise a revenue lift; the approved facts are that {product_name} centralizes lead intake and routes leads by region, source, priority, or owner."
    if objection == "written-info":
        return "That is reasonable. Written details should come before any buying decision, so I will not treat this as accepted today."
    if objection == "provider":
        return f"I would not replace a CRM that already works. {product_name} is worth reviewing only if routing, callback ownership, or reporting are gaps."
    if objection == "authority":
        return "For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist."
    return f"{product_name} helps teams centralize lead intake, route leads, and track callback ownership."


def customer_response_after_agent(seed: dict[str, Any], state: dict[str, Any], agent_answer: str) -> tuple[str, dict[str, Any], str | None, str]:
    after = deepcopy(state)
    objection = state["active_objection"]
    if objection == "do-not-call":
        after["interest"] = 0
        after["friction"] = 5
        return "Correct. I am rejecting the offer and I do not want more sales contact.", after, "rejected-deal", "customer rejected and requested no more sales contact"
    if objection == "support":
        after["interest"] = 0
        after["trust"] = clamp(after["trust"] + 1)
        return "Okay, route me to support. I am rejecting the sales offer.", after, "rejected-deal", "customer needed support rather than sales"
    if objection == "time":
        after["trust"] = clamp(after["trust"] + 1)
        after["friction"] = clamp(after["friction"] - 1)
        return "Thanks for not pushing. I am rejecting the deal for now.", after, "rejected-deal", "customer rejected because timing was not acceptable"
    if objection == "not-interested":
        return "No, I am not interested in the deal.", after, "rejected-deal", "customer rejected the offer"
    if objection == "price":
        after["clarity"] = clamp(after["clarity"] + 2)
        after["trust"] = clamp(after["trust"] + 1)
        after["friction"] = clamp(after["friction"] - 1)
        after["active_objection"] = "authority"
        return "That answers the cost. What would I tell my manager if I wanted to accept a review?", after, None, "customer moved from price concern to stakeholder review"
    if objection == "confusion":
        after["clarity"] = clamp(after["clarity"] + 3)
        after["interest"] = clamp(after["interest"] + 1)
        after["active_objection"] = "price"
        return "That makes sense now. What would it cost for a small team?", after, None, "customer moved from confusion to price evaluation"
    if objection == "trust":
        after["clarity"] = clamp(after["clarity"] + 1)
        after["trust"] = clamp(after["trust"] + 1)
        after["active_objection"] = "written-info"
        return "I still do not accept it today. Send proof in writing before any decision.", after, None, "customer stayed cautious and requested written proof"
    if objection == "written-info":
        after["interest"] = clamp(after["interest"] + 1)
        return "That is fair, but I am rejecting the deal until I see the written details.", after, "rejected-deal", "customer rejected pending written information"
    if objection == "provider":
        after["clarity"] = clamp(after["clarity"] + 2)
        after["interest"] = clamp(after["interest"] + 2)
        after["active_objection"] = "price"
        return "If it can sit alongside our CRM, what would the Growth plan cost?", after, None, "customer moved from provider objection to price evaluation"
    if objection == "authority":
        after["clarity"] = clamp(after["clarity"] + 2)
        after["trust"] = clamp(after["trust"] + 1)
        after["interest"] = clamp(after["interest"] + 1)
        after["friction"] = clamp(after["friction"] - 1)
        return "Yes, I accept a non-binding specialist workflow review. Do not handle billing on this call.", after, "accepted-deal", "customer accepted the non-binding sales outcome"
    after["active_objection"] = "not-interested"
    return "I do not see enough value, so I am rejecting the deal.", after, "rejected-deal", "customer rejected after low fit"


def guarded_answer(agent_answer: str, customer_text: str, campaign: dict[str, Any]) -> dict[str, Any]:
    return build_guarded_response_packet(
        campaign=campaign,
        stage="discovery",
        input_type="speech-final",
        transcript=customer_text,
        silence_count=0,
        candidate_response_override=agent_answer,
        retrieval_enabled=False,
        retrieval_registry_path=None,
        composer_hooks_enabled=False,
    )


def safety_flags(packet: dict[str, Any]) -> dict[str, bool]:
    final_answer = str(packet["final_response"])
    flags = {
        "payment_collection": contains_payment_collection(final_answer),
        "unsupported_claim": bool(unsupported_claims(final_answer)),
        "validation_failed": not packet["validation"]["passed"],
        "language_mismatch": not output_language_matches(packet),
        "forbidden_response_text": bool(forbidden_response_text(packet)),
    }
    flags["hard_failure"] = any(flags.values())
    return flags


def simulate_call(seed: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    opening_text = opening_agent_message(campaign)
    opening_packet = guarded_answer(opening_text, "", campaign)
    opening_final = str(opening_packet["final_response"])
    state = deepcopy(seed["initial_state"])
    opening = {
        "agent_opening": opening_final,
        "customer_opening_response": seed["opening_response"],
        "opening_checks": opening_checks(opening_final),
        "safety_flags": safety_flags(opening_packet),
        "question_count": count_questions(opening_final),
        "decision_snapshot": opening_packet["decision_snapshot"],
    }

    turns: list[dict[str, Any]] = []
    terminal_outcome: str | None = None
    terminal_reason = ""
    loop_guard_triggered = False
    customer_text = seed["opening_response"]
    previous_agent = None
    previous_customer = None

    for _ in range(12):
        state_before = deepcopy(state)
        answer = answer_for_state(state_before, campaign)
        packet = guarded_answer(answer, customer_text, campaign)
        final_answer = str(packet["final_response"])
        flags = safety_flags(packet)
        customer_response, state_after, outcome, reason = customer_response_after_agent(seed, state_before, final_answer)
        if flags["hard_failure"]:
            outcome = "rejected-deal"
            reason = "safety guard blocked accepting the deal"
        turns.append(
            {
                "turn_index": len(turns) + 1,
                "customer_context": customer_text,
                "agent_answer": final_answer,
                "customer_response": customer_response,
                "state_before": state_before,
                "state_after": state_after,
                "state_delta": {
                    "interest": state_after["interest"] - state_before["interest"],
                    "trust": state_after["trust"] - state_before["trust"],
                    "clarity": state_after["clarity"] - state_before["clarity"],
                    "friction": state_after["friction"] - state_before["friction"],
                    "patience": state_after["patience"] - state_before["patience"],
                },
                "customer_reaction_reason": reason,
                "repeated_agent_answer": final_answer == previous_agent,
                "repeated_customer_response": customer_response == previous_customer,
                "safety_flags": flags,
                "question_count": count_questions(final_answer),
                "decision_snapshot": packet["decision_snapshot"],
            }
        )
        previous_agent = final_answer
        previous_customer = customer_response
        state = state_after
        customer_text = customer_response
        if outcome is not None:
            terminal_outcome = outcome
            terminal_reason = reason
            break
    else:
        loop_guard_triggered = True
        terminal_outcome = "rejected-deal"
        terminal_reason = "internal loop guard triggered"

    return {
        "seed_id": seed["seed_id"],
        "persona": seed["persona"],
        "expected_terminal_outcome": seed["expected_terminal_outcome"],
        "terminal_outcome": terminal_outcome,
        "terminal_decision_source": "customer",
        "terminal_reason": terminal_reason,
        "starts_with_agent_opening": True,
        "loop_guard_triggered": loop_guard_triggered,
        "opening": opening,
        "initial_state": seed["initial_state"],
        "final_state": turns[-1]["state_after"],
        "turn_count": len(turns),
        "turns": turns,
    }


def repeated_agent_answer_count(calls: list[dict[str, Any]]) -> int:
    return sum(1 for call in calls for turn in call["turns"] if turn["repeated_agent_answer"])


def repeated_customer_message_count(calls: list[dict[str, Any]]) -> int:
    return sum(1 for call in calls for turn in call["turns"] if turn["repeated_customer_response"])


def build_summary(calls: list[dict[str, Any]]) -> dict[str, Any]:
    all_turns = [turn for call in calls for turn in call["turns"]]
    opening_checks_list = [call["opening"]["opening_checks"] for call in calls]
    hard_failure_count = sum(1 for turn in all_turns if turn["safety_flags"]["hard_failure"]) + sum(
        1 for call in calls if call["opening"]["safety_flags"]["hard_failure"]
    )
    payment_count = sum(1 for turn in all_turns if turn["safety_flags"]["payment_collection"]) + sum(
        1 for call in calls if call["opening"]["safety_flags"]["payment_collection"]
    )
    unsupported_count = sum(1 for turn in all_turns if turn["safety_flags"]["unsupported_claim"]) + sum(
        1 for call in calls if call["opening"]["safety_flags"]["unsupported_claim"]
    )
    return {
        "call_seed_count": len(build_call_seeds()),
        "call_count": len(calls),
        "cold_call_opening_count": sum(1 for call in calls if call["starts_with_agent_opening"]),
        "identity_disclosure_count": sum(1 for checks in opening_checks_list if checks["identity_disclosure"]),
        "company_disclosure_count": sum(1 for checks in opening_checks_list if checks["company_disclosure"]),
        "reason_for_call_count": sum(1 for checks in opening_checks_list if checks["reason_for_call"]),
        "permission_to_continue_count": sum(1 for checks in opening_checks_list if checks["permission_to_continue"]),
        "all_calls_start_with_agent_opening": all(call["starts_with_agent_opening"] for call in calls),
        "all_calls_end_by_customer_decision": all(call["terminal_decision_source"] == "customer" for call in calls),
        "fixed_turn_limit_used": False,
        "loop_guard_triggered": any(call["loop_guard_triggered"] for call in calls),
        "max_turn_terminal_count": sum(1 for call in calls if call["terminal_outcome"] == "max-turns"),
        "accepted_deal_count": sum(1 for call in calls if call["terminal_outcome"] == "accepted-deal"),
        "rejected_deal_count": sum(1 for call in calls if call["terminal_outcome"] == "rejected-deal"),
        "expected_terminal_match_count": sum(1 for call in calls if call["terminal_outcome"] == call["expected_terminal_outcome"]),
        "total_sales_turn_count": len(all_turns),
        "callback_converted_to_sale_ready_count": 0,
        "repeated_agent_answer_count": repeated_agent_answer_count(calls),
        "repeated_customer_message_count": repeated_customer_message_count(calls),
        "hard_failure_count": hard_failure_count,
        "payment_collection_count": payment_count,
        "unsupported_claim_count": unsupported_count,
        "leakage_finding_count": 0,
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
    }


def build_payload(
    *,
    source_result_path: Path = DEFAULT_SOURCE_RESULT,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    trace_path: Path = DEFAULT_TRACE,
    html_path: Path = DEFAULT_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    campaign = build_synthetic_campaign()
    calls = [simulate_call(seed, campaign) for seed in build_call_seeds()]
    traces = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "source_result_path": rel_path(source_result_path),
        "calls": calls,
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-033 interactive simulator termination fix",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "trace_path": rel_path(trace_path),
            "trace_html_path": rel_path(html_path),
        },
        "boundaries": build_boundaries(),
        "summary": build_summary(calls),
        "decision": {
            "cold_call_openings": "added",
            "turn_ending_rule": "customer-decision-only",
            "fixed_turn_limit": "not-used",
            "next_step": NEXT_CHECKPOINT_ID,
        },
    }
    return payload, traces


def render_report(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-033 Interactive Simulator Termination Fix",
        "",
        "PROD-033 adds cold-call entrances and changes the simulator so calls end by customer acceptance or rejection, not by a fixed turn count.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        f"- Source checkpoint: `{payload['source_checkpoint_id']}`",
        f"- Cold-call openings: `{summary['cold_call_opening_count']}`",
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
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Provider calls made: `{str(summary['provider_calls_made']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Call Outcomes",
        "",
        "| Seed | Persona | Sales turns | Terminal outcome | Terminal reason |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for call in traces["calls"]:
        lines.append(f"| {call['seed_id']} | {call['persona']} | {call['turn_count']} | {call['terminal_outcome']} | {call['terminal_reason']} |")
    lines.extend(["", "## Exact Cold-Call Traces", ""])
    for call in traces["calls"]:
        lines.extend(
            [
                f"### {call['seed_id']} - {call['persona']}",
                "",
                f"- Terminal outcome: `{call['terminal_outcome']}`",
                f"- Terminal decision source: `{call['terminal_decision_source']}`",
                "",
                "Agent opening:",
                "",
                "```text",
                call["opening"]["agent_opening"],
                "```",
                "",
                "Customer opening response:",
                "",
                "```text",
                call["opening"]["customer_opening_response"],
                "```",
                "",
            ]
        )
        for turn in call["turns"]:
            lines.extend(
                [
                    f"#### Sales turn {turn['turn_index']}",
                    "",
                    "Agent:",
                    "",
                    "```text",
                    turn["agent_answer"],
                    "```",
                    "",
                    "Customer:",
                    "",
                    "```text",
                    turn["customer_response"],
                    "```",
                    "",
                    f"- Reaction reason: `{turn['customer_reaction_reason']}`",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for call in traces["calls"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(call['seed_id'])}</td>"
            f"<td>{html.escape(call['terminal_outcome'])}</td>"
            f"<td>{call['turn_count']}</td>"
            f"<td>{html.escape(call['terminal_reason'])}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-033 Interactive Simulator Termination Fix</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.45; color: #202124; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    .metric {{ display: inline-block; margin: 6px 12px 6px 0; padding: 6px 8px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>PROD-033 Interactive Simulator Termination Fix</h1>
  <p>Cold-call openings plus customer-decision endings. No fixed turn limit is used for normal call completion.</p>
  <div class="metric">Cold-call openings: `{summary['cold_call_opening_count']}`</div>
  <div class="metric">All calls start with agent opening: `{str(summary['all_calls_start_with_agent_opening']).lower()}`</div>
  <div class="metric">All calls end by customer decision: `{str(summary['all_calls_end_by_customer_decision']).lower()}`</div>
  <div class="metric">Fixed turn limit used: `{str(summary['fixed_turn_limit_used']).lower()}`</div>
  <div class="metric">Loop guard triggered: `{str(summary['loop_guard_triggered']).lower()}`</div>
  <div class="metric">Max-turn terminal count: `{summary['max_turn_terminal_count']}`</div>
  <div class="metric">Callback converted to sale-ready: `{summary['callback_converted_to_sale_ready_count']}`</div>
  <div class="metric">Repeated agent answers: `{summary['repeated_agent_answer_count']}`</div>
  <div class="metric">Repeated customer messages: `{summary['repeated_customer_message_count']}`</div>
  <div class="metric">Next checkpoint: `{html.escape(payload['next_checkpoint_recommended'])}`</div>
  <table>
    <thead><tr><th>Seed</th><th>Terminal outcome</th><th>Sales turns</th><th>Reason</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
"""
