#!/usr/bin/env python3

STRATEGY_DEFINITIONS = {
    "rapport": (
        "Use `rapport` when the safest move is respect, acknowledgment, trust-building, "
        "de-escalation, or a clean human handoff. Do not use it to keep pushing."
    ),
    "inquiry": (
        "Use `inquiry` when the agent should ask one clarifying question about value, fit, "
        "risk, comparison criteria, timing, or the decision path."
    ),
    "evidence-or-benefit": (
        "Use `evidence-or-benefit` when the lead asks for information or needs an approved, "
        "non-guaranteed benefit explanation. Do not invent proof."
    ),
    "emotional-appeal": (
        "Use `emotional-appeal` only for approved empathy or motivation. Do not use it for "
        "annoyed leads, fear pressure, guilt, or high-risk claims."
    ),
    "direct-ask-or-commitment": (
        "Use `direct-ask-or-commitment` when the lead is open to a concrete next step, "
        "callback window, appointment, or explicit non-binding specialist follow-up."
    ),
}


def strategy_taxonomy_prompt_block() -> str:
    lines = ["Strategy taxonomy decision rules:"]
    for definition in STRATEGY_DEFINITIONS.values():
        lines.append(f"- {definition}")
    return "\n".join(lines)


def normalize_final_outcome(raw_outcome: dict) -> dict:
    outcome = {
        "call_status": raw_outcome.get("call_status"),
        "interest_state": raw_outcome.get("interest_state"),
        "selected_strategy": raw_outcome.get("selected_strategy"),
        "appointment_scheduled": bool(raw_outcome.get("appointment_scheduled")),
        "appointment_time": raw_outcome.get("appointment_time"),
        "escalation_reason": raw_outcome.get("escalation_reason"),
        "call_summary": raw_outcome.get("call_summary"),
        "next_action": raw_outcome.get("next_action"),
    }

    interest_state = outcome["interest_state"]

    if interest_state == "needs-human":
        outcome["call_status"] = "escalated"
        if outcome["selected_strategy"] in {"direct-ask-or-commitment", "emotional-appeal"}:
            outcome["selected_strategy"] = "rapport"
        if not outcome["escalation_reason"]:
            outcome["escalation_reason"] = "human handoff required"

    if (
        interest_state == "interested"
        and not outcome["appointment_scheduled"]
        and outcome["call_status"] in {None, "completed"}
    ):
        outcome["call_status"] = "ready-for-scheduling"

    if interest_state == "do-not-call":
        outcome["call_status"] = "completed"
        outcome["appointment_scheduled"] = False
        outcome["appointment_time"] = None

    if not outcome["appointment_scheduled"]:
        outcome["appointment_time"] = None

    if outcome["appointment_scheduled"] and not outcome["appointment_time"]:
        outcome["call_status"] = "needs-follow-up"

    return outcome
