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

CALL_CONTROL_VALUES = (
    "continue-call",
    "bridge-then-continue",
    "transfer-or-escalate",
    "end-call",
    "schedule-and-end",
    "close-and-log-sale-ready",
)

CALL_CONTROL_DEFINITIONS = {
    "continue-call": "Keep the call open and continue the normal qualification flow.",
    "bridge-then-continue": "Say a short bridge response while slower lookup or verification runs.",
    "transfer-or-escalate": "Route to a human or specialist workflow instead of continuing autonomous qualification.",
    "end-call": "Say the appropriate closing sentence, update records, and hang up.",
    "schedule-and-end": "Confirm the appointment or callback, update records, and end the call politely.",
    "close-and-log-sale-ready": "Confirm a campaign-approved verbal commitment, log the sale-ready outcome, and end or hand off according to the campaign.",
}


def strategy_taxonomy_prompt_block() -> str:
    lines = ["Strategy taxonomy decision rules:"]
    for definition in STRATEGY_DEFINITIONS.values():
        lines.append(f"- {definition}")
    return "\n".join(lines)


def call_control_prompt_block() -> str:
    lines = ["Call-control decision rules:"]
    for value, definition in CALL_CONTROL_DEFINITIONS.items():
        lines.append(f"- `{value}`: {definition}")
    return "\n".join(lines)


def call_control_for_next_action(next_action: str | None, interest_state: str | None) -> str:
    action = (next_action or "").lower()

    if interest_state == "do-not-call" or action == "suppress-contact":
        return "end-call"
    if interest_state == "needs-human" or action == "escalate":
        return "transfer-or-escalate"
    if action == "confirm-scheduling":
        return "schedule-and-end"
    if action == "sale-ready-log":
        return "close-and-log-sale-ready"
    if action in {"close-politely", "create-follow-up-task"}:
        return "end-call"
    if action in {"continue", "ask-follow-up", "offer-scheduling"}:
        return "continue-call"
    if "route to human" in action or "human specialist" in action or "escalate" in action:
        return "transfer-or-escalate"
    if "calendar invite" in action or "appointment" in action:
        return "schedule-and-end"
    if "sale-ready" in action or "verbal commitment" in action:
        return "close-and-log-sale-ready"
    if "follow-up task" in action or "suppress future outreach" in action or "end politely" in action:
        return "end-call"
    return "continue-call"


def call_control_for_final_outcome(outcome: dict) -> str:
    if outcome.get("interest_state") == "do-not-call":
        return "end-call"
    if outcome.get("interest_state") == "needs-human" or outcome.get("call_status") == "escalated":
        return "transfer-or-escalate"
    if outcome.get("appointment_scheduled"):
        return "schedule-and-end"
    if outcome.get("call_status") == "sale-ready" or outcome.get("next_action") == "sale-ready-log":
        return "close-and-log-sale-ready"
    if outcome.get("call_status") == "ready-for-scheduling":
        return "continue-call"
    if outcome.get("call_status") in {"completed", "needs-follow-up"}:
        return "end-call"
    return call_control_for_next_action(outcome.get("next_action"), outcome.get("interest_state"))


def normalize_turn_output(raw_output: dict) -> dict:
    output = {
        "stage": raw_output.get("stage"),
        "detected_emotion": raw_output.get("detected_emotion"),
        "interest_state": raw_output.get("interest_state"),
        "selected_strategy": raw_output.get("selected_strategy"),
        "next_action": raw_output.get("next_action"),
        "call_control": raw_output.get("call_control"),
        "agent_response": raw_output.get("agent_response"),
        "confidence": raw_output.get("confidence"),
        "rationale": raw_output.get("rationale"),
    }

    if output["interest_state"] == "do-not-call":
        output["next_action"] = "suppress-contact"
    elif output["interest_state"] == "needs-human":
        output["next_action"] = "escalate"

    call_control = output.get("call_control")
    if call_control not in CALL_CONTROL_VALUES:
        output["call_control"] = call_control_for_next_action(output["next_action"], output["interest_state"])

    return output


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
        "call_control": raw_outcome.get("call_control"),
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

    if outcome["call_control"] not in CALL_CONTROL_VALUES:
        outcome["call_control"] = call_control_for_final_outcome(outcome)

    return outcome
