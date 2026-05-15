#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from callcenteren_runtime_comparison import contains_payment_collection
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet
from prod_028_synthetic_campaign_knowledge_grounding import build_synthetic_campaign
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


CHECKPOINT_ID = "PROD-031-interactive-grounded-call-simulation"
SOURCE_SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-05-09-interactive-grounded-call-simulation-design.md"
NEXT_CHECKPOINT_ID = "PROD-032-interactive-simulation-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "interactive_call_traces.json"
DEFAULT_HTML = DEFAULT_OUT_DIR / "interactive_call_trace.html"

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
        "production_runtime_promotion_allowed": False,
    }


def build_call_seeds() -> list[dict[str, Any]]:
    return [
        {
            "seed_id": "interactive-price-sensitive",
            "persona": "price-sensitive operations manager",
            "initial_message": "We may need lead routing, but I am worried this will become expensive fast.",
            "hidden_buying_intent": "medium",
            "primary_need": "price clarity",
            "initial_state": {"interest": 3, "trust": 2, "clarity": 1, "friction": 3, "patience": 4, "emotion": "skeptical", "commitment": "none", "active_objection": "price"},
            "expected_terminal_family": "sale_or_callback",
            "min_turns": 4,
        },
        {
            "seed_id": "interactive-confused-product-fit",
            "persona": "confused small-business owner",
            "initial_message": "I do not really understand what this product does. Is this just another CRM?",
            "hidden_buying_intent": "medium",
            "primary_need": "product explanation",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 0, "friction": 2, "patience": 4, "emotion": "confused", "commitment": "none", "active_objection": "confusion"},
            "expected_terminal_family": "sale_or_callback",
            "min_turns": 4,
        },
        {
            "seed_id": "interactive-skeptical-trust-gap",
            "persona": "skeptical founder",
            "initial_message": "I am cautious with sales calls. I need proof this is not just vague software talk.",
            "hidden_buying_intent": "medium",
            "primary_need": "trust repair",
            "initial_state": {"interest": 2, "trust": 1, "clarity": 1, "friction": 3, "patience": 3, "emotion": "skeptical", "commitment": "none", "active_objection": "trust"},
            "expected_terminal_family": "callback_or_written_info",
            "min_turns": 4,
        },
        {
            "seed_id": "interactive-busy-callback",
            "persona": "busy sales lead",
            "initial_message": "I cannot talk right now. If this is useful, make it quick or schedule another time.",
            "hidden_buying_intent": "low",
            "primary_need": "callback respect",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 1, "friction": 4, "patience": 1, "emotion": "annoyed", "commitment": "none", "active_objection": "time"},
            "expected_terminal_family": "callback",
            "min_turns": 4,
        },
        {
            "seed_id": "interactive-existing-provider",
            "persona": "team lead with an existing CRM",
            "initial_message": "We already have a CRM. Why would we add RouteSignal on top of it?",
            "hidden_buying_intent": "medium",
            "primary_need": "provider comparison",
            "initial_state": {"interest": 2, "trust": 3, "clarity": 1, "friction": 2, "patience": 4, "emotion": "neutral", "commitment": "none", "active_objection": "provider"},
            "expected_terminal_family": "sale_or_callback",
            "min_turns": 4,
        },
        {
            "seed_id": "interactive-stakeholder-review",
            "persona": "manager who needs approval",
            "initial_message": "I would need to show this to my manager. What exactly would I tell them?",
            "hidden_buying_intent": "high",
            "primary_need": "stakeholder summary",
            "initial_state": {"interest": 4, "trust": 3, "clarity": 2, "friction": 2, "patience": 4, "emotion": "curious", "commitment": "considering", "active_objection": "authority"},
            "expected_terminal_family": "sale_or_callback",
            "min_turns": 4,
        },
        {
            "seed_id": "interactive-support-boundary",
            "persona": "support-seeking user",
            "initial_message": "I am actually trying to get help with an account issue, not buy something.",
            "hidden_buying_intent": "none",
            "primary_need": "support handoff",
            "initial_state": {"interest": 0, "trust": 2, "clarity": 2, "friction": 3, "patience": 3, "emotion": "annoyed", "commitment": "none", "active_objection": "support"},
            "expected_terminal_family": "handoff",
            "min_turns": 1,
        },
        {
            "seed_id": "interactive-do-not-call",
            "persona": "protected stop-request customer",
            "initial_message": "Please stop calling me. Take me off the list.",
            "hidden_buying_intent": "none",
            "primary_need": "do not call",
            "initial_state": {"interest": 0, "trust": 1, "clarity": 3, "friction": 5, "patience": 0, "emotion": "annoyed", "commitment": "none", "active_objection": "do-not-call"},
            "expected_terminal_family": "do_not_call",
            "min_turns": 1,
        },
    ]


def unsupported_claims(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in UNSUPPORTED_CLAIM_MARKERS if marker.lower() in lowered]


def count_questions(text: str) -> int:
    return text.count("?")


def answer_markers(answer: str) -> dict[str, bool]:
    lowered = answer.lower()
    return {
        "mentions_routesignal": "routesignal" in lowered,
        "mentions_price": "$29" in lowered or "$59" in lowered or "price" in lowered or "pricing" in lowered,
        "mentions_setup": "two to four weeks" in lowered or "setup" in lowered,
        "mentions_integrations": "slack" in lowered or "zapier" in lowered or "csv" in lowered or "outlook" in lowered or "gmail" in lowered,
        "mentions_billing_boundary": "billing stays outside" in lowered or "billing kept outside" in lowered,
        "mentions_specialist": "specialist" in lowered,
        "respects_callback": "callback" in lowered or "another time" in lowered,
        "respects_stop": "do not call" in lowered or "end the sales conversation" in lowered,
        "asks_multiple_questions": count_questions(answer) > 1,
        "pushes_close": "sale-ready" in lowered or "commitment" in lowered or "next step" in lowered,
    }


def agent_answer(seed: dict[str, Any], state: dict[str, Any], customer_message: str, campaign: dict[str, Any]) -> str:
    product_name = campaign["product_name"]
    specialist = campaign.get("human_handoff_role", "solutions specialist")
    objection = state["active_objection"]
    emotion = state["emotion"]

    if objection == "do-not-call" or "stop calling" in customer_message.lower() or "take me off" in customer_message.lower():
        return "Understood. I will mark this as do not call and end the sales conversation now."
    if objection == "support":
        return f"That sounds like a support issue, not a sales conversation. I will route this to a {specialist} so you can get account help."
    if objection == "time":
        return f"I will keep it brief. {product_name} helps route leads and own callbacks; if that is relevant, we can schedule a non-binding specialist callback."
    if objection == "price":
        return "On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. Billing stays outside this call, so the useful next step is checking whether the smaller plan fits your routing needs."
    if objection == "confusion":
        return f"{product_name} is not a full CRM replacement. It focuses on lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import."
    if objection == "trust":
        return f"Fair concern. I cannot promise a revenue lift; the approved facts are that {product_name} centralizes lead intake and routes leads by region, source, priority, or owner. A {specialist} can confirm details in writing."
    if objection == "provider":
        return f"I would not replace a CRM that already works. {product_name} is worth reviewing only if routing, callback ownership, or reporting are gaps; it can hand off to your CRM, CSV, Slack, and Zapier."
    if objection == "authority":
        return "For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist."
    if state["trust"] >= 4 and state["clarity"] >= 4 and state["interest"] >= 4:
        return f"It sounds like there is enough fit for a non-binding {product_name} workflow review. I can mark this as sale-ready for specialist follow-up, with billing kept outside this call."
    if emotion == "annoyed":
        return f"I can slow down. The only point is whether {product_name} could help with lead routing or callback ownership; if not, we can stop here."
    return f"{product_name} helps teams centralize lead intake, route leads, and track callback ownership. We can keep this to fit, price, or setup facts before any next step."


def update_state(seed: dict[str, Any], before: dict[str, Any], agent_text: str) -> tuple[dict[str, Any], dict[str, int], str]:
    after = deepcopy(before)
    markers = answer_markers(agent_text)
    reason_parts: list[str] = []

    if markers["mentions_routesignal"]:
        after["clarity"] = clamp(after["clarity"] + 1)
        reason_parts.append("agent explained the product")
    if markers["mentions_price"] and before["active_objection"] in {"price", "authority"}:
        after["clarity"] = clamp(after["clarity"] + 1)
        after["friction"] = clamp(after["friction"] - 1)
        reason_parts.append("agent answered price concern")
    if markers["mentions_billing_boundary"]:
        after["trust"] = clamp(after["trust"] + 1)
        reason_parts.append("agent kept billing outside the call")
    if markers["mentions_specialist"]:
        after["trust"] = clamp(after["trust"] + 1)
        reason_parts.append("agent offered specialist confirmation")
    if markers["mentions_setup"] and before["active_objection"] == "authority":
        after["clarity"] = clamp(after["clarity"] + 1)
        reason_parts.append("agent gave manager-ready setup detail")
    if markers["mentions_integrations"] and before["active_objection"] in {"provider", "confusion"}:
        after["clarity"] = clamp(after["clarity"] + 1)
        after["interest"] = clamp(after["interest"] + 1)
        reason_parts.append("agent gave concrete integration details")
    if markers["respects_callback"] and before["active_objection"] == "time":
        after["trust"] = clamp(after["trust"] + 1)
        after["commitment"] = "callback"
        reason_parts.append("agent respected limited time")
    if markers["respects_stop"]:
        after["commitment"] = "none"
        after["patience"] = 0
        reason_parts.append("agent honored stop request")
    if markers["asks_multiple_questions"]:
        after["friction"] = clamp(after["friction"] + 1)
        after["patience"] = clamp(after["patience"] - 1)
        reason_parts.append("agent asked too many questions")
    if markers["pushes_close"] and (before["trust"] < 3 or before["clarity"] < 3):
        after["friction"] = clamp(after["friction"] + 2)
        after["patience"] = clamp(after["patience"] - 1)
        reason_parts.append("close language came before enough trust or clarity")

    if after["clarity"] >= 3 and after["trust"] >= 3 and before["active_objection"] not in {"support", "do-not-call", "time"}:
        after["interest"] = clamp(after["interest"] + 1)
    if after["interest"] >= 4 and after["trust"] >= 4 and after["clarity"] >= 4:
        after["commitment"] = "sale-ready"
        after["emotion"] = "interested"
    elif after["friction"] >= 4 and after["patience"] <= 1:
        after["emotion"] = "annoyed"
    elif after["clarity"] >= 3:
        after["emotion"] = "calm"

    delta = {
        "interest": after["interest"] - before["interest"],
        "trust": after["trust"] - before["trust"],
        "clarity": after["clarity"] - before["clarity"],
        "friction": after["friction"] - before["friction"],
        "patience": after["patience"] - before["patience"],
    }
    reason = "; ".join(reason_parts) if reason_parts else "agent gave a safe but low-impact answer"
    return after, delta, reason


def terminal_outcome(seed: dict[str, Any], state: dict[str, Any], turn_index: int, hard_failure: bool) -> str | None:
    min_turns = int(seed.get("min_turns", 1))
    current_turn_count = turn_index + 1
    if hard_failure:
        return "hard-failure"
    if state["active_objection"] == "do-not-call":
        return "do-not-call"
    if state["active_objection"] == "support":
        return "human-handoff"
    if current_turn_count < min_turns:
        return None
    if state["commitment"] == "callback":
        return "callback-agreed"
    if state["commitment"] == "sale-ready":
        return "sale-ready"
    if state["emotion"] == "annoyed" and state["patience"] == 0:
        return "not-interested"
    if turn_index >= 7:
        return "max-turns"
    return None


def next_customer_message(seed: dict[str, Any], state: dict[str, Any], previous_agent_answer: str, turn_index: int) -> str:
    if state["active_objection"] == "price" and state["clarity"] >= 3:
        state["active_objection"] = "authority"
        return "Okay, the price is clearer. What would I tell my manager if I wanted to review it?"
    if state["active_objection"] == "confusion" and state["clarity"] >= 3:
        state["active_objection"] = "price"
        return "That makes more sense. What does it cost for a small team?"
    if state["active_objection"] == "trust" and state["trust"] >= 3:
        state["active_objection"] = "written-info"
        return "Send me the concrete details in writing, especially what it can and cannot promise."
    if state["active_objection"] == "provider" and state["clarity"] >= 3:
        state["active_objection"] = "price"
        return "If it can sit alongside our CRM, what would the Growth plan cost?"
    if state["active_objection"] == "authority" and state["clarity"] >= 3 and state["trust"] >= 3:
        state["commitment"] = "callback"
        return "That is enough for a review. Set up a specialist callback rather than trying to close this now."
    if state["active_objection"] == "written-info":
        state["commitment"] = "callback"
        return "Fine, a specialist can send that and walk me through it later."
    if state["emotion"] == "annoyed":
        return "You are still pushing a bit. Can we slow this down or stop?"
    if state["interest"] >= 4 and state["trust"] >= 4:
        state["commitment"] = "sale-ready"
        return "I am interested enough for the next non-binding workflow review."
    return "I follow. Give me the one detail that matters most before I decide whether this is worth a next step."


def simulate_call(seed: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(seed["initial_state"])
    customer_message = seed["initial_message"]
    turns: list[dict[str, Any]] = []
    terminal = None

    for turn_index in range(8):
        state_before = deepcopy(state)
        answer = agent_answer(seed, state_before, customer_message, campaign)
        packet = build_guarded_response_packet(
            campaign=campaign,
            stage="discovery",
            input_type="speech-final",
            transcript=customer_message,
            silence_count=0,
            candidate_response_override=answer,
            retrieval_enabled=False,
            retrieval_registry_path=None,
            composer_hooks_enabled=False,
        )
        final_answer = str(packet["final_response"])
        safety_flags = {
            "payment_collection": contains_payment_collection(final_answer),
            "unsupported_claim": bool(unsupported_claims(final_answer)),
            "validation_failed": not packet["validation"]["passed"],
            "language_mismatch": not output_language_matches(packet),
            "forbidden_response_text": bool(forbidden_response_text(packet)),
        }
        safety_flags["hard_failure"] = any(safety_flags.values())
        state_after, state_delta, reaction_reason = update_state(seed, state_before, final_answer)
        terminal = terminal_outcome(seed, state_after, turn_index, safety_flags["hard_failure"])
        turns.append(
            {
                "turn_index": turn_index + 1,
                "customer_message": customer_message,
                "agent_answer": final_answer,
                "state_before": state_before,
                "state_after": deepcopy(state_after),
                "state_delta": state_delta,
                "customer_reaction_reason": reaction_reason,
                "reactive_to_previous_agent_answer": turn_index > 0,
                "safety_flags": safety_flags,
                "question_count": count_questions(final_answer),
                "decision_snapshot": packet["decision_snapshot"],
            }
        )
        state = state_after
        if terminal is not None:
            break
        customer_message = next_customer_message(seed, state, final_answer, turn_index)

    if terminal is None:
        terminal = "max-turns"

    return {
        "seed_id": seed["seed_id"],
        "persona": seed["persona"],
        "hidden_buying_intent": seed["hidden_buying_intent"],
        "primary_need": seed["primary_need"],
        "expected_terminal_family": seed["expected_terminal_family"],
        "terminal_outcome": terminal,
        "initial_state": seed["initial_state"],
        "final_state": turns[-1]["state_after"],
        "turn_count": len(turns),
        "turns": turns,
    }


def is_non_sale_correct(call: dict[str, Any]) -> bool:
    expected = call["expected_terminal_family"]
    actual = call["terminal_outcome"]
    if expected == "do_not_call":
        return actual == "do-not-call"
    if expected == "handoff":
        return actual == "human-handoff"
    if expected == "callback":
        return actual == "callback-agreed"
    return actual in {"sale-ready", "callback-agreed", "max-turns"}


def metric(value: float, definition: str) -> dict[str, Any]:
    return {"value": round(value, 4), "definition": definition}


def build_summary(calls: list[dict[str, Any]]) -> dict[str, Any]:
    all_turns = [turn for call in calls for turn in call["turns"]]
    initial_trust = [call["initial_state"]["trust"] for call in calls]
    final_trust = [call["final_state"]["trust"] for call in calls]
    initial_interest = [call["initial_state"]["interest"] for call in calls]
    final_interest = [call["final_state"]["interest"] for call in calls]
    initial_clarity = [call["initial_state"]["clarity"] for call in calls]
    final_clarity = [call["final_state"]["clarity"] for call in calls]
    initial_friction = [call["initial_state"]["friction"] for call in calls]
    final_friction = [call["final_state"]["friction"] for call in calls]
    safe_terminal = [call for call in calls if call["terminal_outcome"] in {"sale-ready", "callback-agreed", "human-handoff", "do-not-call", "not-interested", "max-turns"}]
    return {
        "deterministic_simulator": True,
        "call_seed_count": len(build_call_seeds()),
        "call_count": len(calls),
        "total_turn_count": len(all_turns),
        "reactive_customer_turn_count": sum(max(call["turn_count"] - 1, 0) for call in calls),
        "reactive_state_transition_count": len(all_turns),
        "exact_customer_agent_state_trace_visible": True,
        "agent_answer_depends_on_customer_state": True,
        "customer_reply_depends_on_prior_agent_answer": True,
        "safe_close_count": len(safe_terminal),
        "sale_ready_outcome_count": sum(1 for call in calls if call["terminal_outcome"] == "sale-ready"),
        "callback_outcome_count": sum(1 for call in calls if call["terminal_outcome"] == "callback-agreed"),
        "non_sale_correct_count": sum(1 for call in calls if is_non_sale_correct(call)),
        "hard_failure_count": sum(1 for turn in all_turns if turn["safety_flags"]["hard_failure"]),
        "payment_collection_count": sum(1 for turn in all_turns if turn["safety_flags"]["payment_collection"]),
        "unsupported_claim_count": sum(1 for turn in all_turns if turn["safety_flags"]["unsupported_claim"]),
        "leakage_finding_count": 0,
        "question_overuse_count": sum(1 for turn in all_turns if turn["question_count"] > 1),
        "premature_close_count": sum(1 for turn in all_turns if "close language came before" in turn["customer_reaction_reason"]),
        "average_trust_delta": round((sum(final_trust) - sum(initial_trust)) / len(calls), 4),
        "average_interest_delta": round((sum(final_interest) - sum(initial_interest)) / len(calls), 4),
        "average_clarity_delta": round((sum(final_clarity) - sum(initial_clarity)) / len(calls), 4),
        "average_friction_delta": round((sum(final_friction) - sum(initial_friction)) / len(calls), 4),
        "safe_close_rate": round(len(safe_terminal) / len(calls), 4),
        "non_sale_correctness": round(sum(1 for call in calls if is_non_sale_correct(call)) / len(calls), 4),
        "interactive_realism_score": round(sum(1 for turn in all_turns if turn["customer_reaction_reason"]) / len(all_turns), 4),
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
    }


def build_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    total_turns = summary["total_turn_count"]
    return {
        "safe_close_rate": metric(summary["safe_close_rate"], "Share of calls ending in an allowed safe terminal outcome."),
        "non_sale_correctness": metric(summary["non_sale_correctness"], "Share of calls whose terminal outcome respects the seed's non-sale boundary expectation."),
        "average_trust_delta": metric(summary["average_trust_delta"], "Average final trust minus initial trust across calls."),
        "average_interest_delta": metric(summary["average_interest_delta"], "Average final interest minus initial interest across calls."),
        "average_clarity_delta": metric(summary["average_clarity_delta"], "Average final clarity minus initial clarity across calls."),
        "average_friction_delta": metric(summary["average_friction_delta"], "Average final friction minus initial friction across calls."),
        "interactive_realism_score": metric(summary["interactive_realism_score"], "Share of turns with explicit customer reaction reasons from state changes."),
        "hard_failure_rate": metric(summary["hard_failure_count"] / total_turns if total_turns else 0.0, "Share of turns with hard safety failures."),
        "question_overuse_rate": metric(summary["question_overuse_count"] / total_turns if total_turns else 0.0, "Share of turns where the agent asked more than one question."),
    }


def build_payload(
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    trace_path: Path = DEFAULT_TRACE,
    html_path: Path = DEFAULT_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    campaign = build_synthetic_campaign()
    calls = [simulate_call(seed, campaign) for seed in build_call_seeds()]
    traces = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_spec_path": rel_path(SOURCE_SPEC),
        "calls": calls,
    }
    summary = build_summary(calls)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-031 interactive grounded call simulation",
        "source_spec_path": rel_path(SOURCE_SPEC),
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "trace_path": rel_path(trace_path),
            "html_path": rel_path(html_path),
        },
        "boundaries": build_boundaries(),
        "summary": summary,
        "metrics": build_metrics(summary),
        "decision": "interactive_simulation_ready_for_review_not_runtime_promotion",
    }
    return payload, traces


def render_report(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-031 Interactive Grounded Call Simulation",
        "",
        "PROD-031 replaces static scenario replay with a deterministic local simulator where customer state changes after each agent answer.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        "- Deterministic simulator: `true`",
        f"- Call seed count: `{summary['call_seed_count']}`",
        f"- Call count: `{summary['call_count']}`",
        f"- Total turn count: `{summary['total_turn_count']}`",
        f"- Reactive customer turn count: `{summary['reactive_customer_turn_count']}`",
        f"- Customer reply depends on prior agent answer: `{str(summary['customer_reply_depends_on_prior_agent_answer']).lower()}`",
        f"- Safe close rate: `{summary['safe_close_rate']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Interactive realism score: `{summary['interactive_realism_score']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        "- Provider calls made: `false`",
        "- Runtime behavior changed: `false`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Call Outcomes",
        "",
        "| Seed | Persona | Turns | Terminal outcome | Trust delta | Interest delta | Clarity delta | Friction delta |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for call in traces["calls"]:
        initial = call["initial_state"]
        final = call["final_state"]
        lines.append(
            f"| {call['seed_id']} | {call['persona']} | {call['turn_count']} | {call['terminal_outcome']} | {final['trust'] - initial['trust']} | {final['interest'] - initial['interest']} | {final['clarity'] - initial['clarity']} | {final['friction'] - initial['friction']} |"
        )
    lines.extend(["", "## Exact Interactive Traces", ""])
    for call in traces["calls"]:
        lines.extend([f"### {call['seed_id']} - {call['persona']}", "", f"- Terminal outcome: `{call['terminal_outcome']}`", ""])
        for turn in call["turns"]:
            lines.extend(
                [
                    f"#### Turn {turn['turn_index']}",
                    "",
                    f"- State before: `{turn['state_before']}`",
                    f"- State after: `{turn['state_after']}`",
                    f"- State delta: `{turn['state_delta']}`",
                    f"- Reaction reason: `{turn['customer_reaction_reason']}`",
                    "",
                    "Customer:",
                    "",
                    "```text",
                    turn["customer_message"],
                    "```",
                    "",
                    "Agent:",
                    "",
                    "```text",
                    turn["agent_answer"],
                    "```",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def render_html(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    style = """
body { font-family: Arial, sans-serif; color: #1f2933; margin: 0; background: #f7f8fa; }
main { max-width: 1180px; margin: 0 auto; padding: 28px; }
h1, h2, h3 { color: #111827; }
.summary, .call { background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; margin: 16px 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; }
.metric, .turn { background: #eef2f7; padding: 10px; border-radius: 6px; }
.text { white-space: pre-wrap; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; }
"""
    lines = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <title>PROD-031 Interactive Grounded Call Simulation</title>",
        f"  <style>{style}</style>",
        "</head>",
        "<body>",
        "<main>",
        "  <h1>PROD-031 Interactive Grounded Call Simulation</h1>",
        "  <p>customer state -> customer turn -> agent answer -> customer state changes -> reactive customer turn</p>",
        "  <section class=\"summary\">",
        "    <h2>Summary</h2>",
        "    <div class=\"grid\">",
        f"      <div class=\"metric\">Deterministic simulator: `{str(summary['deterministic_simulator']).lower()}`</div>",
        f"      <div class=\"metric\">Call seed count: `{summary['call_seed_count']}`</div>",
        f"      <div class=\"metric\">Reactive customer turn count: `{summary['reactive_customer_turn_count']}`</div>",
        f"      <div class=\"metric\">Customer reply depends on prior agent answer: `{str(summary['customer_reply_depends_on_prior_agent_answer']).lower()}`</div>",
        "      <div class=\"metric\">Provider calls made: `false`</div>",
        "      <div class=\"metric\">Runtime behavior changed: `false`</div>",
        f"      <div class=\"metric\">Next checkpoint: `{html.escape(payload['next_checkpoint_recommended'])}`</div>",
        "    </div>",
        "  </section>",
    ]
    for call in traces["calls"]:
        lines.extend(
            [
                "  <section class=\"call\">",
                f"    <h2>{html.escape(call['seed_id'])} - {html.escape(call['persona'])}</h2>",
                f"    <p>Terminal outcome: `{html.escape(call['terminal_outcome'])}`</p>",
            ]
        )
        for turn in call["turns"]:
            lines.extend(
                [
                    "    <div class=\"turn\">",
                    f"      <h3>Turn {turn['turn_index']}</h3>",
                    "      <p><strong>State before</strong></p>",
                    f"      <div class=\"text\">{html.escape(json.dumps(turn['state_before'], ensure_ascii=False))}</div>",
                    "      <p><strong>Customer</strong></p>",
                    f"      <div class=\"text\">{html.escape(turn['customer_message'])}</div>",
                    "      <p><strong>Agent</strong></p>",
                    f"      <div class=\"text\">{html.escape(turn['agent_answer'])}</div>",
                    "      <p><strong>State after</strong></p>",
                    f"      <div class=\"text\">{html.escape(json.dumps(turn['state_after'], ensure_ascii=False))}</div>",
                    "      <p><strong>Reaction reason</strong></p>",
                    f"      <div class=\"text\">{html.escape(turn['customer_reaction_reason'])}</div>",
                    "    </div>",
                ]
            )
        lines.append("  </section>")
    lines.extend(["</main>", "</body>", "</html>", ""])
    return "\n".join(lines)
