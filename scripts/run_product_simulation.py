#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ALLOWED_EMOTIONS = {"positive", "neutral", "skeptical-or-negative"}
ALLOWED_INTEREST_STATES = {"interested", "maybe-interested", "not-interested", "needs-human", "do-not-call"}
ALLOWED_STRATEGIES = {
    "rapport",
    "inquiry",
    "evidence-or-benefit",
    "emotional-appeal",
    "direct-ask-or-commitment",
}
ALLOWED_CALL_STATUSES = {"completed", "escalated", "ready-for-scheduling", "needs-follow-up"}
SIMULATION_TIMESTAMP = "2026-04-29T00:00:00Z"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(load_text(path))


def as_code(value) -> str:
    if value is None:
        return "`null`"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    return f"`{value}`"


def case_context(case: dict) -> str:
    profile = case["lead_profile"]
    return "\n".join(
        [
            f"case_id: {case['case_id']}",
            f"case_title: {case['case_title']}",
            f"scenario_goal: {case['scenario_goal']}",
            f"lead_role: {profile['role']}",
            f"company_context: {profile['company_context']}",
            f"starting_attitude: {profile['starting_attitude']}",
        ]
    )


def infer_next_action(turn: dict, is_last_turn: bool, outcome: dict) -> str:
    state = turn["expected_state_after_turn"]
    stage = turn["stage"]
    status = outcome["call_status"]

    if state == "do-not-call":
        return "suppress-contact"
    if state == "needs-human":
        return "escalate"
    if state == "not-interested":
        return "close-politely"
    if stage == "scheduling" and outcome["appointment_scheduled"]:
        return "confirm-scheduling"
    if state == "interested" and not outcome["appointment_scheduled"]:
        return "offer-scheduling" if status == "ready-for-scheduling" else "create-follow-up-task"
    if is_last_turn and status == "needs-follow-up":
        return "create-follow-up-task"
    if "ask" in turn["expected_agent_action"]:
        return "ask-follow-up"
    return "continue"


def reference_turn_output(turn: dict, is_last_turn: bool, outcome: dict) -> dict:
    return {
        "stage": turn["stage"],
        "detected_emotion": turn["emotion_label"],
        "interest_state": turn["expected_state_after_turn"],
        "selected_strategy": turn["strategy_label"],
        "next_action": infer_next_action(turn, is_last_turn, outcome),
        "agent_response": turn["expected_agent_action"],
        "confidence": 0.8,
        "rationale": "Reference output derived from the case-set expected labels.",
    }


def reference_call_outcome(case: dict) -> dict:
    outcome = dict(case["expected_outcome"])
    outcome["call_summary"] = (
        f"{case['case_title']}: {case['scenario_goal']} "
        f"Final state is {outcome['interest_state']} with next action: {outcome['next_action']}."
    )
    return outcome


def lead_contact_status(outcome: dict) -> str:
    interest_state = outcome["interest_state"]
    if interest_state == "do-not-call":
        return "do-not-call"
    if outcome.get("appointment_scheduled"):
        return "appointment-scheduled"
    if interest_state == "interested":
        return "qualified"
    if interest_state == "maybe-interested":
        return "called"
    if interest_state == "needs-human":
        return "needs-human"
    if interest_state == "not-interested":
        return "not-interested"
    return "called"


def normalized_answer_for(turn: dict) -> dict:
    return {
        "stage": turn["stage"],
        "expected_state_after_answer": turn["expected_state_after_turn"],
    }


def initial_call_state(case: dict) -> dict:
    return {
        "lead_profile": case["lead_profile"],
        "conversation_so_far": [],
        "current_stage": "not-started",
        "current_interest_state": "unknown",
        "current_emotion_label": "unknown",
        "current_strategy": "none",
        "appointment_status": "not-offered",
        "appointment_time": None,
        "escalation_flags": [],
        "suppression_requested": False,
    }


def appointment_status_for(turn: dict, outcome: dict) -> str:
    if turn["stage"] == "scheduling" and outcome.get("appointment_scheduled"):
        return "confirmed"
    if turn["expected_state_after_turn"] == "interested":
        return "offered-or-ready"
    return "not-offered"


def escalation_flags_for(turn: dict, outcome: dict) -> list[str]:
    flags = []
    if turn["expected_state_after_turn"] == "needs-human":
        reason = outcome.get("escalation_reason") or "needs human review"
        flags.append(reason)
    return flags


def update_call_state(state: dict, turn: dict, reference: dict, outcome: dict) -> dict:
    updated = dict(state)
    updated["conversation_so_far"] = [
        *state["conversation_so_far"],
        {
            "stage": turn["stage"],
            "agent_question": turn["agent_question"],
            "lead_answer": turn["lead_answer"],
            "detected_emotion": reference["detected_emotion"],
            "interest_state": reference["interest_state"],
            "selected_strategy": reference["selected_strategy"],
            "next_action": reference["next_action"],
        },
    ]
    updated["current_stage"] = turn["stage"]
    updated["current_interest_state"] = reference["interest_state"]
    updated["current_emotion_label"] = reference["detected_emotion"]
    updated["current_strategy"] = reference["selected_strategy"]
    updated["appointment_status"] = appointment_status_for(turn, outcome)
    if outcome.get("appointment_scheduled") and outcome.get("appointment_time"):
        updated["appointment_time"] = outcome["appointment_time"]
    updated["escalation_flags"] = [*state["escalation_flags"], *escalation_flags_for(turn, outcome)]
    updated["suppression_requested"] = state["suppression_requested"] or reference["interest_state"] == "do-not-call"
    return updated


def build_database_records(cases: list[dict], source_cases_path: Path) -> dict:
    records = {
        "metadata": {
            "source": "product-synthetic",
            "source_case_file": source_cases_path.as_posix(),
            "generated_by": "scripts/run_product_simulation.py",
            "generated_at": SIMULATION_TIMESTAMP,
            "record_mode": "reference-simulation",
            "privacy_note": "Synthetic simulation records only. Do not store real customer data in this repository.",
        },
        "leads": [],
        "call_sessions": [],
        "qualification_answers": [],
        "turn_decisions": [],
        "call_outcomes": [],
        "appointments": [],
        "escalations": [],
    }

    for case_index, case in enumerate(cases, start=1):
        outcome = reference_call_outcome(case)
        profile = case["lead_profile"]
        lead_id = f"lead-{case['case_id'].lower()}"
        call_id = f"call-{case['case_id'].lower()}"
        outcome_id = f"outcome-{case['case_id'].lower()}"

        records["leads"].append(
            {
                "lead_id": lead_id,
                "full_name": f"Synthetic Lead {case_index:02d}",
                "phone_number": None,
                "email": None,
                "company_name": profile["company_context"],
                "role_title": profile["role"],
                "source": "product-synthetic-simulation",
                "region": None,
                "language": "en",
                "contact_status": lead_contact_status(outcome),
                "consent_status": "unknown",
                "do_not_call": outcome["interest_state"] == "do-not-call",
                "do_not_call_reason": outcome["next_action"] if outcome["interest_state"] == "do-not-call" else None,
                "preferred_contact_time": None,
                "owner_user_id": None,
                "created_at": SIMULATION_TIMESTAMP,
                "updated_at": SIMULATION_TIMESTAMP,
            }
        )

        state = initial_call_state(case)
        for turn_index, turn in enumerate(case["turns"], start=1):
            reference = reference_turn_output(turn, turn_index == len(case["turns"]), case["expected_outcome"])
            answer_id = f"answer-{case['case_id'].lower()}-{turn_index:02d}"
            decision_id = f"decision-{case['case_id'].lower()}-{turn_index:02d}"

            records["qualification_answers"].append(
                {
                    "answer_id": answer_id,
                    "call_id": call_id,
                    "lead_id": lead_id,
                    "stage": turn["stage"],
                    "question_text": turn["agent_question"],
                    "answer_text": turn["lead_answer"],
                    "normalized_answer": normalized_answer_for(turn),
                    "detected_emotion": reference["detected_emotion"],
                    "interest_state_after_answer": reference["interest_state"],
                    "selected_strategy": reference["selected_strategy"],
                    "confidence": reference["confidence"],
                    "created_at": SIMULATION_TIMESTAMP,
                }
            )

            records["turn_decisions"].append(
                {
                    "decision_id": decision_id,
                    "call_id": call_id,
                    "lead_id": lead_id,
                    "turn_index": turn_index,
                    "stage": reference["stage"],
                    "detected_emotion": reference["detected_emotion"],
                    "interest_state": reference["interest_state"],
                    "selected_strategy": reference["selected_strategy"],
                    "next_action": reference["next_action"],
                    "agent_response": reference["agent_response"],
                    "confidence": reference["confidence"],
                    "rationale": reference["rationale"],
                    "guardrail_flags": case.get("guardrail_notes", []) if turn_index == len(case["turns"]) else [],
                    "created_at": SIMULATION_TIMESTAMP,
                }
            )
            state = update_call_state(state, turn, reference, case["expected_outcome"])

        records["call_sessions"].append(
            {
                "call_id": call_id,
                "lead_id": lead_id,
                "channel": "simulation",
                "started_at": SIMULATION_TIMESTAMP,
                "ended_at": SIMULATION_TIMESTAMP,
                "call_status": outcome["call_status"],
                "current_stage": state["current_stage"],
                "current_interest_state": state["current_interest_state"],
                "current_emotion_label": state["current_emotion_label"],
                "current_strategy": state["current_strategy"],
                "confidence": 0.8,
                "transcript_storage_mode": "structured-synthetic",
                "transcript_text": None,
                "call_summary": outcome["call_summary"],
                "created_by": "simulation-runner",
                "created_at": SIMULATION_TIMESTAMP,
            }
        )

        records["call_outcomes"].append(
            {
                "outcome_id": outcome_id,
                "call_id": call_id,
                "lead_id": lead_id,
                "call_status": outcome["call_status"],
                "interest_state": outcome["interest_state"],
                "selected_strategy": outcome["selected_strategy"],
                "appointment_scheduled": outcome["appointment_scheduled"],
                "appointment_time": outcome["appointment_time"],
                "escalation_reason": outcome["escalation_reason"],
                "call_summary": outcome["call_summary"],
                "next_action": outcome["next_action"],
                "created_at": SIMULATION_TIMESTAMP,
            }
        )

        if outcome.get("appointment_scheduled"):
            records["appointments"].append(
                {
                    "appointment_id": f"appointment-{case['case_id'].lower()}",
                    "lead_id": lead_id,
                    "call_id": call_id,
                    "scheduled_time": outcome["appointment_time"],
                    "timezone": None,
                    "assigned_sales_agent_id": None,
                    "appointment_status": "confirmed",
                    "confirmation_text": outcome["next_action"],
                    "calendar_event_id": None,
                    "created_at": SIMULATION_TIMESTAMP,
                    "updated_at": SIMULATION_TIMESTAMP,
                }
            )

        if outcome.get("escalation_reason"):
            records["escalations"].append(
                {
                    "escalation_id": f"escalation-{case['case_id'].lower()}",
                    "lead_id": lead_id,
                    "call_id": call_id,
                    "escalation_reason": outcome["escalation_reason"],
                    "severity": "medium",
                    "assigned_to": None,
                    "status": "open",
                    "notes": outcome["next_action"],
                    "created_at": SIMULATION_TIMESTAMP,
                    "resolved_at": None,
                }
            )

    return records


def validate_cases(cases: list[dict]) -> list[str]:
    errors = []
    seen_ids = set()

    for case in cases:
        case_id = case.get("case_id", "<missing>")
        if case_id in seen_ids:
            errors.append(f"{case_id}: duplicate case_id")
        seen_ids.add(case_id)

        if not case.get("turns"):
            errors.append(f"{case_id}: missing turns")

        outcome = case.get("expected_outcome", {})
        if outcome.get("interest_state") not in ALLOWED_INTEREST_STATES:
            errors.append(f"{case_id}: invalid final interest_state {outcome.get('interest_state')!r}")
        if outcome.get("selected_strategy") not in ALLOWED_STRATEGIES:
            errors.append(f"{case_id}: invalid final selected_strategy {outcome.get('selected_strategy')!r}")
        if outcome.get("call_status") not in ALLOWED_CALL_STATUSES:
            errors.append(f"{case_id}: invalid call_status {outcome.get('call_status')!r}")
        if outcome.get("appointment_scheduled") and not outcome.get("appointment_time"):
            errors.append(f"{case_id}: scheduled appointment is missing appointment_time")

        for index, turn in enumerate(case.get("turns", []), start=1):
            prefix = f"{case_id} turn {index}"
            if turn.get("emotion_label") not in ALLOWED_EMOTIONS:
                errors.append(f"{prefix}: invalid emotion_label {turn.get('emotion_label')!r}")
            if turn.get("expected_state_after_turn") not in ALLOWED_INTEREST_STATES:
                errors.append(f"{prefix}: invalid expected_state_after_turn {turn.get('expected_state_after_turn')!r}")
            if turn.get("strategy_label") not in ALLOWED_STRATEGIES:
                errors.append(f"{prefix}: invalid strategy_label {turn.get('strategy_label')!r}")

    return errors


def render_prompt(template: str, case: dict, turn: dict, state: dict) -> str:
    return template.format(
        case_context=case_context(case),
        accumulated_call_state=json.dumps(state, indent=2),
        agent_question=turn["agent_question"],
        lead_answer=turn["lead_answer"],
        stage=turn["stage"],
    )


def build_case_section(case: dict, template: str) -> str:
    lines = [
        f"## {case['case_id']}: {case['case_title']}",
        "",
        f"- Scenario goal: {case['scenario_goal']}",
        f"- Lead role: `{case['lead_profile']['role']}`",
        f"- Company context: {case['lead_profile']['company_context']}",
        f"- Starting attitude: `{case['lead_profile']['starting_attitude']}`",
        "",
    ]

    outcome = case["expected_outcome"]
    state = initial_call_state(case)
    for index, turn in enumerate(case["turns"], start=1):
        reference = reference_turn_output(turn, index == len(case["turns"]), outcome)
        prompt = render_prompt(template, case, turn, state)
        lines.extend(
            [
                f"### Turn {index}: `{turn['stage']}`",
                "",
                "Rendered prompt:",
                "",
                "```text",
                prompt.rstrip(),
                "```",
                "",
                "Reference structured output:",
                "",
                "```json",
                json.dumps(reference, indent=2),
                "```",
                "",
                "Candidate structured output:",
                "",
                "```json",
                "",
                "```",
                "",
                "Turn checks:",
                "",
                "- Emotion match:",
                "- Interest-state match:",
                "- Strategy match:",
                "- Guardrail issue:",
                "",
            ]
        )
        state = update_call_state(state, turn, reference, outcome)

    lines.extend(
        [
            "### Reference Final CallOutcome",
            "",
            "```json",
            json.dumps(reference_call_outcome(case), indent=2),
            "```",
            "",
            "Candidate Final CallOutcome:",
            "",
            "```json",
            "",
            "```",
            "",
            "Final checks:",
            "",
            f"- Expected call status: {as_code(outcome['call_status'])}",
            f"- Expected interest state: {as_code(outcome['interest_state'])}",
            f"- Expected selected strategy: {as_code(outcome['selected_strategy'])}",
            f"- Expected appointment scheduled: {as_code(outcome['appointment_scheduled'])}",
            f"- Expected appointment time: {as_code(outcome['appointment_time'])}",
            f"- Expected escalation reason: {as_code(outcome['escalation_reason'])}",
            "- Final outcome match:",
            "- Scheduling trigger correct:",
            "- Escalation trigger correct:",
            "- Guardrail issue:",
            "",
        ]
    )

    if case.get("guardrail_notes"):
        lines.extend(["Guardrail notes:", ""])
        lines.extend(f"- {note}" for note in case["guardrail_notes"])
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Render a product qualification simulation evaluation packet.")
    parser.add_argument("--cases", required=True, help="Path to the JSON simulation case file.")
    parser.add_argument("--out", required=True, help="Path to the markdown output file.")
    parser.add_argument(
        "--prompt",
        default="packages/prompts/product-qualification-agent.txt",
        help="Path to the product qualification agent prompt template.",
    )
    parser.add_argument(
        "--export-records",
        help="Optional path to write database-shaped synthetic simulation records as JSON.",
    )
    args = parser.parse_args()

    cases_path = Path(args.cases)
    out_path = Path(args.out)
    prompt_path = Path(args.prompt)

    cases = load_json(cases_path)
    errors = validate_cases(cases)
    if errors:
        raise SystemExit("Case validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    template = load_text(prompt_path)
    header = [
        f"# Product Qualification Simulation Run: {cases_path.stem}",
        "",
        "This file was generated by `scripts/run_product_simulation.py`.",
        "",
        f"- Source case file: `{cases_path.as_posix()}`",
        f"- Prompt template: `{prompt_path.as_posix()}`",
        f"- Cases: {len(cases)}",
        "- Source label: `product-synthetic`",
        "- Live model execution: `not-run`",
        "",
        "Use this packet to run the qualification agent turn by turn and compare candidate JSON outputs against the reference labels.",
        "",
    ]
    sections = [build_case_section(case, template) for case in cases]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(header + sections), encoding="utf-8")

    if args.export_records:
        records_path = Path(args.export_records)
        records = build_database_records(cases, cases_path)
        records_path.parent.mkdir(parents=True, exist_ok=True)
        records_path.write_text(json.dumps(records, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
