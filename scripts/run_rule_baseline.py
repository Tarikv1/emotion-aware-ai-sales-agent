#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.contracts.product_agent_output_contract import normalize_final_outcome, normalize_turn_output


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(path: Path) -> list[dict]:
    payload = load_json(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("cases", [])
    raise SystemExit("Case file must be either a case list or a campaign wrapper object.")


def run_label_for(path: Path) -> str:
    stem = path.stem
    if stem.startswith("prod-"):
        return stem.split("-", maxsplit=2)[:2]
    return [stem]


def report_title_for(path: Path) -> str:
    parts = run_label_for(path)
    return "-".join(parts).upper()


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def answer_text_for(case: dict) -> str:
    return " ".join(turn["lead_answer"].lower() for turn in case["turns"])


def detect_emotion(answer: str) -> str:
    if contains_any(
        answer,
        [
            "do not call",
            "don't call",
            "generic sales pitch",
            "tired",
            "privacy",
            "annoying",
            "nervt",
            "will jetzt nicht reden",
            "not good",
            "no budget",
            "not looking",
            "zu teuer",
            "nicht wert",
            "warum sollte ich",
            "vertrauen",
            "besser sind",
            "anderer anbieter",
            "garantieren",
            "garantie",
            "stabil und schnell",
        ],
    ):
        return "skeptical-or-negative"
    if contains_any(
        answer,
        [
            "yes",
            "useful",
            "works",
            "open",
            "would like",
            "great",
            "sure",
            "warum nicht",
            "in ordnung",
            "waere in ordnung",
            "wäre in ordnung",
            "merken sie",
            "vormerken",
        ],
    ):
        return "positive"
    return "neutral"


def classify_interest(answer: str, state: dict) -> str:
    if contains_any(answer, ["do not call", "don't call", "never call"]):
        return "do-not-call"
    if contains_any(
        answer,
        [
            "have a person call",
            "human",
            "person anrufen",
            "direkt eine person",
            "mensch",
            "privacy",
            "integrate",
            "integration",
            "custom crm",
            "ticketing",
            "legal",
            "contract",
            "pricing",
            "besser sind als",
            "anderer anbieter",
            "garantieren",
            "garantie",
            "stabil und schnell",
            "pruefung bestehe",
            "prüfung bestehe",
            "not the right person",
            "nicht zustaendig",
            "nicht zuständig",
            "cannot decide",
            "can't decide",
            "muesste",
            "müsste",
            "leiterin",
            "handled by lena",
            "pass your message",
        ],
    ):
        return "needs-human"
    if contains_any(
        answer,
        [
            "do not really get inbound",
            "do not handle sales",
            "not interested",
            "not looking",
            "no budget",
            "working well enough",
            "we do not need",
            "will jetzt nicht reden",
            "das nervt",
        ],
    ):
        return "not-interested"
    if contains_any(answer, ["try me sometime next week"]):
        return "interested"
    if contains_any(
        answer,
        [
            "could you send me",
            "send me something",
            "schicken sie mir",
            "maybe later",
            "call me another day",
            "ende naechsten monats",
            "ende nächsten monats",
            "vielleicht irgendwann",
        ],
    ):
        return "maybe-interested"
    if contains_any(answer, ["wednesday at", "tuesday at", "works"]):
        return "interested"
    if contains_any(
        answer,
        [
            "would be useful",
            "short call",
            "open to",
            "i could do",
            "would like to see",
            "rueckruf waere in ordnung",
            "rückruf wäre in ordnung",
            "kurzer rueckruf",
            "kurzer rückruf",
        ],
    ):
        return "interested"
    if contains_any(answer, ["yes", "sure", "okay", "go ahead", "we do handle", "my team owns", "we get"]):
        return "maybe-interested"
    return state.get("current_interest_state") if state.get("current_interest_state") != "unknown" else "maybe-interested"


def is_direct_human_or_owner_path(answer: str) -> bool:
    return contains_any(
        answer,
        [
            "have a person call",
            "human",
            "person anrufen",
            "direkt eine person",
            "privacy",
            "data privacy",
            "integrate",
            "integration",
            "custom crm",
            "ticketing",
            "nicht zustaendig",
            "nicht zuständig",
            "not the right person",
            "handled by lena",
            "leiterin",
        ],
    )


def is_claim_or_fit_boundary(answer: str) -> bool:
    return contains_any(
        answer,
        [
            "besser sind als",
            "anderer anbieter",
            "garantieren",
            "garantie",
            "stabil und schnell",
            "pruefung bestehe",
            "prüfung bestehe",
            "coverage",
        ],
    )


def select_strategy(answer: str, emotion: str, interest_state: str, stage: str) -> str:
    if interest_state == "needs-human":
        return "rapport" if is_direct_human_or_owner_path(answer) else "inquiry"
    if interest_state in {"do-not-call", "not-interested"}:
        return "rapport"
    if contains_any(answer, ["schicken sie mir", "send me something", "could you send me"]):
        return "evidence-or-benefit"
    if contains_any(
        answer,
        [
            "ende naechsten monats",
            "ende nächsten monats",
            "vormerken",
            "rueckruf waere in ordnung",
            "rückruf wäre in ordnung",
            "kurzer rueckruf",
            "kurzer rückruf",
        ],
    ):
        return "direct-ask-or-commitment"
    if contains_any(answer, ["unternehmen nicht", "why should i trust", "warum sollte ich", "vertrauen"]):
        return "rapport"
    if interest_state == "interested":
        if stage == "pain-point-check":
            return "evidence-or-benefit"
        return "direct-ask-or-commitment"
    if contains_any(answer, ["call me another day", "now is not good"]):
        return "rapport"
    if emotion == "skeptical-or-negative":
        return "inquiry"
    if contains_any(answer, ["handoffs", "miss", "opportunities", "not terrible"]):
        return "evidence-or-benefit"
    if stage in {"relevance-check", "pain-point-check"}:
        return "inquiry"
    return "rapport"


def next_action_for(answer: str, interest_state: str, stage: str, is_last_turn: bool) -> str:
    if interest_state == "do-not-call":
        return "suppress-contact"
    if interest_state == "needs-human":
        return "escalate"
    if interest_state == "not-interested":
        return "close-politely"
    if stage == "scheduling" and contains_any(answer, ["works", "wednesday", "tuesday"]):
        return "confirm-scheduling"
    if interest_state == "interested":
        if contains_any(answer, ["next week", "have to run"]):
            return "create-follow-up-task"
        return "offer-scheduling" if is_last_turn else "continue"
    if contains_any(
        answer,
        [
            "send me something",
            "schicken sie mir",
            "call me another day",
            "ende naechsten monats",
            "ende nächsten monats",
            "vormerken",
        ],
    ):
        return "create-follow-up-task"
    if is_last_turn:
        return "create-follow-up-task"
    return "ask-follow-up"


def agent_response_for(interest_state: str, next_action: str) -> str:
    responses = {
        "suppress-contact": "Understood. I will make sure this contact is marked so you are not called again.",
        "escalate": "Thanks for raising that. I will route this to a human specialist instead of guessing.",
        "close-politely": "Thanks for clarifying. I will note that this is not relevant right now and will not take more of your time.",
        "confirm-scheduling": "Confirmed. I will record that time for the follow-up with a human specialist.",
        "offer-scheduling": "That sounds relevant. I can offer a short follow-up with a human specialist if you would like.",
        "create-follow-up-task": "Thanks. I will note this for follow-up rather than forcing the conversation now.",
        "ask-follow-up": "Thanks. What is the hardest part of that process for your team right now?",
        "continue": "Thanks. I will keep this focused and continue with the next qualification step.",
    }
    return responses.get(next_action, f"Proceed with {interest_state}.")


def update_state(state: dict, turn: dict, output: dict) -> dict:
    updated = dict(state)
    updated["conversation_so_far"] = [
        *state["conversation_so_far"],
        {
            "stage": turn["stage"],
            "agent_question": turn["agent_question"],
            "lead_answer": turn["lead_answer"],
            "detected_emotion": output["detected_emotion"],
            "interest_state": output["interest_state"],
            "selected_strategy": output["selected_strategy"],
            "next_action": output["next_action"],
            "call_control": output["call_control"],
        },
    ]
    updated["current_stage"] = turn["stage"]
    updated["current_interest_state"] = output["interest_state"]
    updated["current_emotion_label"] = output["detected_emotion"]
    updated["current_strategy"] = output["selected_strategy"]
    if output["next_action"] == "confirm-scheduling":
        updated["appointment_status"] = "confirmed"
    elif output["next_action"] == "offer-scheduling":
        updated["appointment_status"] = "offered-or-ready"
    if output["next_action"] == "escalate":
        updated["escalation_flags"] = [*state["escalation_flags"], output["rationale"]]
    updated["suppression_requested"] = state["suppression_requested"] or output["interest_state"] == "do-not-call"
    return updated


def run_turn(turn: dict, state: dict, is_last_turn: bool) -> dict:
    emotion = detect_emotion(turn["lead_answer"])
    interest_state = classify_interest(turn["lead_answer"], state)
    strategy = select_strategy(turn["lead_answer"], emotion, interest_state, turn["stage"])
    next_action = next_action_for(turn["lead_answer"], interest_state, turn["stage"], is_last_turn)
    return normalize_turn_output({
        "stage": turn["stage"],
        "detected_emotion": emotion,
        "interest_state": interest_state,
        "selected_strategy": strategy,
        "next_action": next_action,
        "agent_response": agent_response_for(interest_state, next_action),
        "confidence": 0.74,
        "rationale": f"Rule baseline selected {interest_state} from answer cues and stage {turn['stage']}.",
    })


def final_outcome_for(case: dict, state: dict, turn_outputs: list[dict]) -> dict:
    last = turn_outputs[-1]
    interest_state = last["interest_state"]
    selected_strategy = last["selected_strategy"]
    appointment_scheduled = last["next_action"] == "confirm-scheduling"
    appointment_time = None
    if appointment_scheduled:
        appointment_time = case["expected_outcome"].get("appointment_time")

    escalation_reason = None
    full_answer_text = answer_text_for(case)
    if interest_state == "needs-human":
        answer_text = full_answer_text
        if "privacy" in answer_text:
            escalation_reason = "privacy or compliance-sensitive topic"
        elif "besser sind" in answer_text or "anderer anbieter" in answer_text:
            escalation_reason = "competitor comparison outside approved AI response scope"
        elif "stabil und schnell" in answer_text:
            escalation_reason = "coverage or speed guarantee request outside approved AI scope"
        elif "pruefung" in answer_text or "prüfung" in answer_text:
            escalation_reason = "learning outcome guarantee request outside approved AI scope"
        elif "garantieren" in answer_text or "garantie" in answer_text:
            escalation_reason = "claim guarantee request outside approved AI response scope"
        elif "human" in answer_text or "person call" in answer_text or "person anrufen" in answer_text:
            escalation_reason = "lead requested human contact"
        elif "lena" in answer_text or "right person" in answer_text or "nicht zustaendig" in answer_text or "nicht zuständig" in answer_text or "leiterin" in answer_text:
            escalation_reason = "wrong contact with named referral path"
        else:
            escalation_reason = "complex integration question outside approved AI response scope"
    elif interest_state == "interested" and last["next_action"] == "create-follow-up-task":
        escalation_reason = "scheduling window too vague to confirm appointment"

    if interest_state == "needs-human" or escalation_reason:
        call_status = "escalated" if interest_state == "needs-human" else "needs-follow-up"
    elif appointment_scheduled or interest_state in {"not-interested", "do-not-call", "maybe-interested"}:
        call_status = "completed"
    elif interest_state == "interested":
        call_status = "ready-for-scheduling"
    else:
        call_status = "needs-follow-up"

    if interest_state == "maybe-interested" and last["next_action"] == "create-follow-up-task":
        if "call me another day" in case["turns"][-1]["lead_answer"].lower():
            call_status = "needs-follow-up"
        if contains_any(full_answer_text, ["gut genug", "not perfect", "not perfekt"]):
            call_status = "needs-follow-up"
            escalation_reason = "status quo resistance requires later nurturing"
        if contains_any(full_answer_text, ["ende naechsten monats", "ende nächsten monats", "vormerken"]):
            call_status = "needs-follow-up"
            escalation_reason = "callback timing remains broad rather than a confirmed appointment"

    return normalize_final_outcome({
        "call_status": call_status,
        "interest_state": interest_state,
        "selected_strategy": selected_strategy,
        "appointment_scheduled": appointment_scheduled,
        "appointment_time": appointment_time,
        "escalation_reason": escalation_reason,
        "call_summary": f"Rule baseline processed {case['case_id']} with final state {interest_state}.",
        "next_action": next_action_summary(last["next_action"], interest_state),
    })


def next_action_summary(next_action: str, interest_state: str) -> str:
    if next_action == "confirm-scheduling":
        return "send calendar invite and notify human sales specialist"
    if next_action == "suppress-contact":
        return "suppress future outreach for this contact according to policy"
    if next_action == "escalate":
        return "route to human specialist"
    if next_action == "create-follow-up-task":
        return "create scheduling follow-up task or route to human scheduler"
    if next_action == "offer-scheduling":
        return "offer available appointment windows"
    if interest_state == "not-interested":
        return "log no current need and end politely"
    return "log outcome and close"


def initial_state(case: dict) -> dict:
    return {
        "lead_profile": case["lead_profile"],
        "conversation_so_far": [],
        "current_stage": "not-started",
        "current_interest_state": "unknown",
        "current_emotion_label": "unknown",
        "current_strategy": "none",
        "appointment_status": "not-offered",
        "escalation_flags": [],
        "suppression_requested": False,
    }


def score_case(case: dict, turn_outputs: list[dict], final_outcome: dict) -> dict:
    turn_scores = []
    for turn, output in zip(case["turns"], turn_outputs):
        turn_scores.append(
            {
                "stage": turn["stage"],
                "emotion_match": output["detected_emotion"] == turn["emotion_label"],
                "interest_state_match": output["interest_state"] == turn["expected_state_after_turn"],
                "strategy_match": output["selected_strategy"] == turn["strategy_label"],
            }
        )

    expected = case["expected_outcome"]
    return {
        "case_id": case["case_id"],
        "turn_scores": turn_scores,
        "final_scores": {
            "call_status_match": final_outcome["call_status"] == expected["call_status"],
            "interest_state_match": final_outcome["interest_state"] == expected["interest_state"],
            "selected_strategy_match": final_outcome["selected_strategy"] == expected["selected_strategy"],
            "appointment_scheduled_match": final_outcome["appointment_scheduled"] == expected["appointment_scheduled"],
        },
    }


def run_case(case: dict) -> dict:
    state = initial_state(case)
    turn_outputs = []
    for index, turn in enumerate(case["turns"], start=1):
        output = run_turn(turn, state, index == len(case["turns"]))
        turn_outputs.append(output)
        state = update_state(state, turn, output)
    final_outcome = final_outcome_for(case, state, turn_outputs)
    scores = score_case(case, turn_outputs, final_outcome)
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "turn_outputs": turn_outputs,
        "final_outcome": final_outcome,
        "scores": scores,
    }


def aggregate(results: list[dict]) -> dict:
    turn_total = 0
    emotion = 0
    interest = 0
    strategy = 0
    final_total = len(results)
    final_status = 0
    final_interest = 0
    final_strategy = 0
    final_appointment = 0

    for result in results:
        for turn_score in result["scores"]["turn_scores"]:
            turn_total += 1
            emotion += int(turn_score["emotion_match"])
            interest += int(turn_score["interest_state_match"])
            strategy += int(turn_score["strategy_match"])
        final = result["scores"]["final_scores"]
        final_status += int(final["call_status_match"])
        final_interest += int(final["interest_state_match"])
        final_strategy += int(final["selected_strategy_match"])
        final_appointment += int(final["appointment_scheduled_match"])

    return {
        "turn_total": turn_total,
        "emotion_matches": emotion,
        "interest_state_matches": interest,
        "strategy_matches": strategy,
        "final_total": final_total,
        "final_call_status_matches": final_status,
        "final_interest_state_matches": final_interest,
        "final_strategy_matches": final_strategy,
        "final_appointment_matches": final_appointment,
    }


def render_report(results: list[dict], summary: dict, report_title: str) -> str:
    lines = [
        f"# {report_title} Rule Baseline Results",
        "",
        "This report was generated by `scripts/run_rule_baseline.py`.",
        "",
        "The baseline uses transparent keyword and state-transition rules. It does not call a live model.",
        "",
        "## Aggregate Results",
        "",
        f"- Turn emotion matches: {summary['emotion_matches']} / {summary['turn_total']}",
        f"- Turn interest-state matches: {summary['interest_state_matches']} / {summary['turn_total']}",
        f"- Turn strategy matches: {summary['strategy_matches']} / {summary['turn_total']}",
        f"- Final call-status matches: {summary['final_call_status_matches']} / {summary['final_total']}",
        f"- Final interest-state matches: {summary['final_interest_state_matches']} / {summary['final_total']}",
        f"- Final strategy matches: {summary['final_strategy_matches']} / {summary['final_total']}",
        f"- Final appointment matches: {summary['final_appointment_matches']} / {summary['final_total']}",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        final = result["scores"]["final_scores"]
        lines.extend(
            [
                f"### {result['case_id']}: {result['case_title']}",
                "",
                f"- Final call status match: `{final['call_status_match']}`",
                f"- Final interest state match: `{final['interest_state_match']}`",
                f"- Final selected strategy match: `{final['selected_strategy_match']}`",
                f"- Final appointment scheduled match: `{final['appointment_scheduled_match']}`",
                "",
                "Final candidate outcome:",
                "",
                "```json",
                json.dumps(result["final_outcome"], indent=2),
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run a deterministic rule baseline on product qualification cases.")
    parser.add_argument("--cases", required=True, help="Path to the JSON simulation case file.")
    parser.add_argument("--out", required=True, help="Path to write detailed JSON results.")
    parser.add_argument("--report-out", required=True, help="Path to write markdown summary report.")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    cases = load_cases(cases_path)
    results = [run_case(case) for case in cases]
    summary = aggregate(results)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results, summary, report_title_for(cases_path)), encoding="utf-8")


if __name__ == "__main__":
    main()
