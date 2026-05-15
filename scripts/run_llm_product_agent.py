#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

from run_product_simulation import (
    initial_call_state,
    load_simulation_spec,
    render_prompt,
    update_call_state,
)
from product_agent_output_contract import (
    call_control_prompt_block,
    normalize_final_outcome,
    normalize_turn_output,
    strategy_taxonomy_prompt_block,
)


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_cases_and_campaigns(path: Path) -> tuple[list[dict], list[dict]]:
    campaigns, cases, _has_campaign_wrapper = load_simulation_spec(path)
    return cases, campaigns


def planned_model_call_count(cases: list[dict]) -> int:
    return sum(len(case.get("turns", [])) + 1 for case in cases)


def log_progress(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, file=sys.stderr, flush=True)


def missing_api_key_message(env_name: str) -> str:
    return (
        f"Missing {env_name}. Set {env_name} to run the LLM product agent. "
        "The runner did not call a live model."
    )


def parse_json_object(text: str) -> dict:
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1)
    else:
        first = stripped.find("{")
        last = stripped.rfind("}")
        if first != -1 and last != -1 and first < last:
            stripped = stripped[first : last + 1]
    return json.loads(stripped)


def call_chat_completion(
    prompt: str,
    api_key: str,
    model: str,
    base_url: str,
    timeout: int,
    temperature: float,
) -> dict:
    response = requests.post(
        base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    return parse_json_object(content)


def render_final_prompt(case: dict, campaign: dict, turn_outputs: list[dict]) -> str:
    transcript = [
        {
            "stage": turn["stage"],
            "agent_question": turn["agent_question"],
            "lead_answer": turn["lead_answer"],
            "candidate_turn_output": output,
        }
        for turn, output in zip(case["turns"], turn_outputs)
    ]
    return "\n".join(
        [
            "You are evaluating the final outcome of a constrained sales qualification call.",
            "",
            "Use the campaign context, lead profile, conversation transcript, and candidate turn outputs.",
            "Return only JSON with the exact final CallOutcome shape.",
            "",
            strategy_taxonomy_prompt_block(),
            "",
            call_control_prompt_block(),
            "",
            "Final outcome consistency rules:",
            "",
            "- If interest_state is needs-human, call_status must be escalated.",
            "- If interest_state is interested and no appointment time is confirmed, call_status should be ready-for-scheduling.",
            "- Do not mark appointment_scheduled true without a clear appointment time.",
            "- Use rapport for respectful human handoff or de-escalation; use inquiry for claim, fit, or comparison clarification.",
            "",
            "Campaign context:",
            "",
            json.dumps(campaign, indent=2, ensure_ascii=False),
            "",
            "Case:",
            "",
            json.dumps(
                {
                    "case_id": case["case_id"],
                    "case_title": case["case_title"],
                    "scenario_goal": case["scenario_goal"],
                    "lead_profile": case["lead_profile"],
                    "guardrail_notes": case.get("guardrail_notes", []),
                },
                indent=2,
                ensure_ascii=False,
            ),
            "",
            "Conversation and turn outputs:",
            "",
            json.dumps(transcript, indent=2, ensure_ascii=False),
            "",
            "Return only JSON:",
            "",
            "{",
            '  "call_status": "completed|escalated|ready-for-scheduling|needs-follow-up",',
            '  "interest_state": "interested|maybe-interested|not-interested|needs-human|do-not-call",',
            '  "selected_strategy": "rapport|inquiry|evidence-or-benefit|emotional-appeal|direct-ask-or-commitment",',
            '  "appointment_scheduled": false,',
            '  "appointment_time": null,',
            '  "escalation_reason": null,',
            '  "call_summary": "brief summary",',
            '  "next_action": "brief next action",',
            '  "call_control": "continue-call|bridge-then-continue|transfer-or-escalate|end-call|schedule-and-end"',
            "}",
        ]
    )


def build_final_outcome(raw_outcome: dict) -> dict:
    return normalize_final_outcome({
        "call_status": raw_outcome.get("call_status"),
        "interest_state": raw_outcome.get("interest_state"),
        "selected_strategy": raw_outcome.get("selected_strategy"),
        "appointment_scheduled": bool(raw_outcome.get("appointment_scheduled")),
        "appointment_time": raw_outcome.get("appointment_time"),
        "escalation_reason": raw_outcome.get("escalation_reason"),
        "call_summary": raw_outcome.get("call_summary"),
        "next_action": raw_outcome.get("next_action"),
        "call_control": raw_outcome.get("call_control"),
    })


def score_case(case: dict, turn_outputs: list[dict], final_outcome: dict) -> dict:
    turn_scores = []
    for turn, output in zip(case["turns"], turn_outputs):
        turn_scores.append(
            {
                "stage": turn["stage"],
                "emotion_match": output.get("detected_emotion") == turn["emotion_label"],
                "interest_state_match": output.get("interest_state") == turn["expected_state_after_turn"],
                "strategy_match": output.get("selected_strategy") == turn["strategy_label"],
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


def aggregate(results: list[dict]) -> dict:
    turn_total = 0
    emotion = 0
    interest = 0
    strategy = 0
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

    final_total = len(results)
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


def run_case(
    case: dict,
    campaign: dict,
    template: str,
    api_key: str,
    model: str,
    base_url: str,
    timeout: int,
    temperature: float,
    quiet: bool = False,
) -> dict:
    state = initial_call_state(case)
    turn_outputs = []
    for index, turn in enumerate(case["turns"], start=1):
        log_progress(f"  Turn {index}/{len(case['turns'])}: {turn['stage']}", quiet)
        prompt = render_prompt(template, case, turn, state, campaign)
        output = normalize_turn_output(call_chat_completion(prompt, api_key, model, base_url, timeout, temperature))
        turn_outputs.append(output)
        state = update_call_state(state, turn, output, case["expected_outcome"])

    log_progress("  Final outcome", quiet)
    final_prompt = render_final_prompt(case, campaign, turn_outputs)
    final_outcome = build_final_outcome(call_chat_completion(final_prompt, api_key, model, base_url, timeout, temperature))
    scores = score_case(case, turn_outputs, final_outcome)
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case.get("campaign_id") or campaign["campaign_id"],
        "turn_outputs": turn_outputs,
        "final_outcome": final_outcome,
        "scores": scores,
    }


def render_report(results: list[dict], summary: dict, run_label: str, model: str) -> str:
    lines = [
        f"# {run_label} LLM Agent Results",
        "",
        "This report was generated by `scripts/run_llm_product_agent.py`.",
        "",
        f"- Model: `{model}`",
        "- Live model execution: `run`",
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
                f"- Campaign: `{result['campaign_id']}`",
                f"- Final call status match: `{final['call_status_match']}`",
                f"- Final interest state match: `{final['interest_state_match']}`",
                f"- Final selected strategy match: `{final['selected_strategy_match']}`",
                f"- Final appointment scheduled match: `{final['appointment_scheduled_match']}`",
                "",
                "Final candidate outcome:",
                "",
                "```json",
                json.dumps(result["final_outcome"], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def report_title_for(path: Path) -> str:
    stem = path.stem
    if stem.startswith("prod-"):
        return "-".join(stem.split("-", maxsplit=2)[:2]).upper()
    return stem.upper()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a live LLM product agent on product qualification cases.")
    parser.add_argument("--cases", required=True, help="Path to the JSON simulation case file.")
    parser.add_argument("--out", required=True, help="Path to write detailed JSON results.")
    parser.add_argument("--report-out", required=True, help="Path to write markdown summary report.")
    parser.add_argument("--prompt", default="runtime/prompts/product-qualification-agent.txt")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--limit", type=int, help="Optional max number of cases to run.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output.")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(missing_api_key_message(args.api_key_env))

    cases_path = Path(args.cases)
    cases, campaigns = load_cases_and_campaigns(cases_path)
    if args.limit:
        cases = cases[: args.limit]

    campaign_lookup = {campaign["campaign_id"]: campaign for campaign in campaigns}
    template = load_text(Path(args.prompt))
    results = []
    log_progress(
        f"Running {len(cases)} cases with {planned_model_call_count(cases)} model calls using {args.model}.",
        args.quiet,
    )
    for case_index, case in enumerate(cases, start=1):
        campaign_id = case.get("campaign_id") or campaigns[0]["campaign_id"]
        campaign = campaign_lookup[campaign_id]
        log_progress(f"Case {case_index}/{len(cases)}: {case['case_id']} ({campaign_id})", args.quiet)
        results.append(
            run_case(
                case,
                campaign,
                template,
                api_key,
                args.model,
                args.base_url,
                args.timeout,
                args.temperature,
                args.quiet,
            )
        )

    summary = aggregate(results)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"model": args.model, "summary": summary, "results": results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results, summary, report_title_for(cases_path), args.model), encoding="utf-8")
    log_progress(f"Wrote results to {out_path}", args.quiet)
    log_progress(f"Wrote report to {report_path}", args.quiet)


if __name__ == "__main__":
    main()
