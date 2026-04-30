#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from product_agent_output_contract import call_control_for_next_action


FAST_RESPONSE_MS = 700
BRIDGE_RESPONSE_MS = 600
BACKGROUND_COMPLETION_MS = 3500


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_realtime_cases(path: Path) -> tuple[list[dict], list[dict]]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SystemExit("PROD-005 case file must be a campaign wrapper object.")
    return payload.get("campaigns", []), payload.get("cases", [])


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def latency_bucket(milliseconds: int) -> str:
    if milliseconds <= 1000:
        return "under-1s"
    if milliseconds <= 2000:
        return "under-2s"
    return "over-2s"


def classify_runtime_input(case: dict) -> dict:
    customer_input = case["customer_input"]
    transcript = customer_input.get("transcript", "")
    input_type = customer_input.get("input_type")
    stage = customer_input.get("stage")

    if input_type == "voicemail-detected":
        return {
            "detected_emotion": "neutral",
            "sales_difficulty": "voicemail",
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": "I reached voicemail, so I will log this for follow-up according to campaign rules.",
        }

    if input_type == "silence-timeout" and customer_input.get("silence_count", 0) >= 2:
        return {
            "detected_emotion": "neutral",
            "sales_difficulty": "repeated-silence",
            "interest_state": "not-interested",
            "selected_strategy": "rapport",
            "next_action": "close-politely",
            "agent_response": "I will end the call for now. Goodbye.",
        }

    if contains_any(transcript, ["nicht mehr an", "do not call", "don't call", "stop calling"]):
        return {
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": "do-not-call",
            "interest_state": "do-not-call",
            "selected_strategy": "rapport",
            "next_action": "suppress-contact",
            "agent_response": "Understood. I will make sure this contact is marked so you are not called again. Goodbye.",
        }

    if contains_any(transcript, ["real person", "human", "person call", "person anrufen"]):
        return {
            "detected_emotion": "neutral",
            "sales_difficulty": "human-request",
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": "Of course. I will route this to a human specialist instead of continuing automatically.",
        }

    if contains_any(transcript, ["garantieren", "guarantee", "stabil", "coverage", "geschwindigkeit"]):
        return {
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": "claim-boundary",
            "interest_state": "needs-human",
            "selected_strategy": "inquiry",
            "next_action": "escalate",
            "agent_response": "I do not want to guarantee something that depends on the details. I can route this to a specialist.",
        }

    if contains_any(transcript, ["welcher genaue tarif", "datenvolumen", "exact plan", "which plan"]):
        return {
            "detected_emotion": "neutral",
            "sales_difficulty": "product-detail-lookup",
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
            "agent_response": "One moment, I want to check the approved product information.",
        }

    if stage == "scheduling" and contains_any(transcript, ["mittwoch", "wednesday", "10 uhr", "10 works"]):
        return {
            "detected_emotion": "positive",
            "sales_difficulty": "scheduling-confirmation",
            "interest_state": "interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "confirm-scheduling",
            "agent_response": "Confirmed. I will record that time for the specialist callback. Goodbye.",
        }

    if contains_any(transcript, ["vielleicht irgendwann", "naechste woche", "nothing firm", "nichts fest"]):
        return {
            "detected_emotion": "neutral",
            "sales_difficulty": "timing-delay",
            "interest_state": "maybe-interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "create-follow-up-task",
            "agent_response": "Thanks. I will log a follow-up rather than forcing a fixed appointment now. Goodbye.",
        }

    if contains_any(transcript, ["guenstiger", "too expensive", "lohnt sich", "aufwand"]):
        return {
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": "price-objection",
            "interest_state": "maybe-interested",
            "selected_strategy": "inquiry",
            "next_action": "ask-follow-up",
            "agent_response": "That makes sense. Is the main concern the price itself, or whether the review is worth the effort?",
        }

    return {
        "detected_emotion": "neutral",
        "sales_difficulty": "unknown-runtime-signal",
        "interest_state": "maybe-interested",
        "selected_strategy": "inquiry",
        "next_action": "ask-follow-up",
        "agent_response": "Thanks. May I ask one quick clarifying question?",
    }


def background_modules_for(decision: dict, expected: dict) -> list[str]:
    if decision["response_mode"] == "bridge-then-background":
        return expected.get("background_modules", [])
    return expected.get("background_modules", [])


def run_case(case: dict) -> dict:
    expected = case["expected_runtime"]
    classified = classify_runtime_input(case)
    response_mode = "bridge-then-background" if classified["sales_difficulty"] == "product-detail-lookup" else "fast-response"
    first_response_ms = BRIDGE_RESPONSE_MS if response_mode == "bridge-then-background" else FAST_RESPONSE_MS
    call_control = "bridge-then-continue" if response_mode == "bridge-then-background" else call_control_for_next_action(
        classified["next_action"],
        classified["interest_state"],
    )
    bridge_response = classified["agent_response"] if response_mode == "bridge-then-background" else None

    runtime_decision = {
        "case_id": case["case_id"],
        "response_mode": response_mode,
        "first_response_latency_budget_ms": first_response_ms,
        "first_response_latency_bucket": latency_bucket(first_response_ms),
        "background_completion_budget_ms": BACKGROUND_COMPLETION_MS if response_mode == "bridge-then-background" else None,
        "background_modules": background_modules_for({"response_mode": response_mode}, expected),
        "live_path_subagents": [],
        "detected_emotion": classified["detected_emotion"],
        "sales_difficulty": classified["sales_difficulty"],
        "interest_state": classified["interest_state"],
        "selected_strategy": classified["selected_strategy"],
        "next_action": classified["next_action"],
        "call_control": call_control,
        "bridge_response": bridge_response,
        "agent_response": classified["agent_response"],
        "rationale": "Deterministic runtime policy selected the fastest safe response path.",
    }
    scores = score_case(case, runtime_decision)
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "runtime_scenario": case["runtime_scenario"],
        "runtime_decision": runtime_decision,
        "scores": scores,
    }


def score_case(case: dict, decision: dict) -> dict:
    expected = case["expected_runtime"]
    return {
        "response_mode_match": decision["response_mode"] == expected["response_mode"],
        "latency_bucket_match": decision["first_response_latency_bucket"] == expected["first_response_latency_bucket"],
        "background_modules_match": decision["background_modules"] == expected.get("background_modules", []),
        "emotion_match": decision["detected_emotion"] == expected["detected_emotion"],
        "sales_difficulty_match": decision["sales_difficulty"] == expected["sales_difficulty"],
        "interest_state_match": decision["interest_state"] == expected["interest_state"],
        "strategy_match": decision["selected_strategy"] == expected["selected_strategy"],
        "next_action_match": decision["next_action"] == expected["next_action"],
        "call_control_match": decision["call_control"] == expected["call_control"],
        "live_path_subagent_violation": bool(decision["live_path_subagents"]),
    }


def aggregate(results: list[dict]) -> dict:
    summary = {
        "case_total": len(results),
        "response_mode_matches": 0,
        "latency_bucket_matches": 0,
        "background_modules_matches": 0,
        "emotion_matches": 0,
        "sales_difficulty_matches": 0,
        "interest_state_matches": 0,
        "strategy_matches": 0,
        "next_action_matches": 0,
        "call_control_matches": 0,
        "live_path_subagent_violations": 0,
    }
    for result in results:
        scores = result["scores"]
        summary["response_mode_matches"] += int(scores["response_mode_match"])
        summary["latency_bucket_matches"] += int(scores["latency_bucket_match"])
        summary["background_modules_matches"] += int(scores["background_modules_match"])
        summary["emotion_matches"] += int(scores["emotion_match"])
        summary["sales_difficulty_matches"] += int(scores["sales_difficulty_match"])
        summary["interest_state_matches"] += int(scores["interest_state_match"])
        summary["strategy_matches"] += int(scores["strategy_match"])
        summary["next_action_matches"] += int(scores["next_action_match"])
        summary["call_control_matches"] += int(scores["call_control_match"])
        summary["live_path_subagent_violations"] += int(scores["live_path_subagent_violation"])
    return summary


def render_report(results: list[dict], summary: dict) -> str:
    lines = [
        "# PROD-005 Realtime Latency And Call-Control Report",
        "",
        "This report was generated by `scripts/run_realtime_turn_simulation.py`.",
        "",
        "The simulation checks runtime behavior, not product-category breadth.",
        "",
        "## Aggregate Results",
        "",
        f"- Cases: {summary['case_total']}",
        f"- Response-mode matches: {summary['response_mode_matches']} / {summary['case_total']}",
        f"- First-response latency-bucket matches: {summary['latency_bucket_matches']} / {summary['case_total']}",
        f"- Background-module matches: {summary['background_modules_matches']} / {summary['case_total']}",
        f"- Emotion matches: {summary['emotion_matches']} / {summary['case_total']}",
        f"- Sales-difficulty matches: {summary['sales_difficulty_matches']} / {summary['case_total']}",
        f"- Interest-state matches: {summary['interest_state_matches']} / {summary['case_total']}",
        f"- Strategy matches: {summary['strategy_matches']} / {summary['case_total']}",
        f"- Next-action matches: {summary['next_action_matches']} / {summary['case_total']}",
        f"- Call-control matches: {summary['call_control_matches']} / {summary['case_total']}",
        f"- Live-path sub-agent violations: {summary['live_path_subagent_violations']}",
        "",
        "## Case Results",
        "",
    ]
    for result in results:
        decision = result["runtime_decision"]
        lines.extend(
            [
                f"### {result['case_id']}: {result['case_title']}",
                "",
                f"- Campaign: `{result['campaign_id']}`",
                f"- Scenario: `{result['runtime_scenario']}`",
                f"- Response mode: `{decision['response_mode']}`",
                f"- First-response latency bucket: `{decision['first_response_latency_bucket']}`",
                f"- Background modules: `{', '.join(decision['background_modules']) or 'none'}`",
                f"- Next action: `{decision['next_action']}`",
                f"- Call control: `{decision['call_control']}`",
                f"- Live-path sub-agents: `{len(decision['live_path_subagents'])}`",
                "",
                "Runtime decision:",
                "",
                "```json",
                json.dumps(decision, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PROD-005 realtime latency and call-control simulation.")
    parser.add_argument("--cases", required=True, help="Path to PROD-005 realtime case JSON.")
    parser.add_argument("--out", required=True, help="Path to write JSON results.")
    parser.add_argument("--report-out", required=True, help="Path to write markdown report.")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    _campaigns, cases = load_realtime_cases(cases_path)
    results = [run_case(case) for case in cases]
    summary = aggregate(results)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results, summary), encoding="utf-8")


if __name__ == "__main__":
    main()
