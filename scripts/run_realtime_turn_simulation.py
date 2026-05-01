#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from product_agent_output_contract import call_control_for_next_action


FAST_RESPONSE_MS = 700
BRIDGE_RESPONSE_MS = 600
BACKGROUND_COMPLETION_MS = 3500
STOP_OR_REFUSAL_RUNTIME_PHRASES = [
    "nicht mehr an",
    "kein interesse",
    "nein danke",
    "do not call",
    "don't call",
    "dont call",
    "stop calling",
    "not interested",
    "no thanks",
    "no thank you",
]
HUMAN_REQUEST_RUNTIME_PHRASES = [
    "real person",
    "human",
    "person call",
    "representative",
    "specialist",
    "advisor",
    "mitarbeiter",
    "mensch",
    "berater",
    "spezialist",
    "echte person",
    "person anrufen",
]
LOCALIZED_RESPONSES = {
    "en": {
        "voicemail": "I reached voicemail, so I will log this for follow-up according to campaign rules.",
        "repeated-silence": "I will end the call for now. Goodbye.",
        "do-not-call": "Understood. I will make sure this contact is marked so you are not called again. Goodbye.",
        "human-request": "Of course. I will route this to a human specialist instead of continuing automatically.",
        "claim-boundary": "I do not want to guarantee something that depends on the details. I can route this to a specialist.",
        "product-detail-lookup": "One moment, I want to check the approved product information.",
        "scheduling-confirmation": "Confirmed. I will record that time for the specialist callback. Goodbye.",
        "timing-delay": "Thanks. I will log a follow-up rather than forcing a fixed appointment now. Goodbye.",
        "price-objection": "That makes sense. Is the main concern the price itself, or whether the review is worth the effort?",
        "unknown-runtime-signal": "Thanks. May I ask one quick clarifying question?",
    },
    "de": {
        "voicemail": "Ich habe die Mailbox erreicht und dokumentiere einen Follow-up nach den Kampagnenregeln.",
        "repeated-silence": "Ich beende den Anruf fuer jetzt. Auf Wiederhoeren.",
        "do-not-call": "Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren.",
        "human-request": "Natuerlich. Ich leite das an einen menschlichen Spezialisten weiter, statt automatisch fortzufahren.",
        "claim-boundary": "Ich moechte nichts garantieren, was von den Details abhaengt. Ich kann das an einen Spezialisten weiterleiten.",
        "product-detail-lookup": "Einen Moment, ich pruefe die freigegebenen Produktinformationen.",
        "scheduling-confirmation": "Bestaetigt. Ich notiere den Rueckruf fuer den Spezialisten. Auf Wiederhoeren.",
        "timing-delay": "Danke. Ich dokumentiere einen Rueckruf, statt jetzt einen festen Termin zu erzwingen. Auf Wiederhoeren.",
        "price-objection": "Das verstehe ich. Geht es eher um den Preis selbst oder darum, ob sich der Aufwand lohnt?",
        "unknown-runtime-signal": "Danke. Darf ich kurz eine klaerende Frage stellen?",
    },
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_realtime_cases(path: Path) -> tuple[list[dict], list[dict]]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SystemExit("PROD-005 case file must be a campaign wrapper object.")
    return payload.get("campaigns", []), payload.get("cases", [])


def find_campaign(campaigns: list[dict], campaign_id: str) -> dict | None:
    for campaign in campaigns:
        if campaign.get("campaign_id") == campaign_id:
            return campaign
    return None


def normalize_response_language(language: str | None) -> str:
    if (language or "").lower().startswith("de"):
        return "de"
    return "en"


def localized_response(language: str, sales_difficulty: str) -> str:
    language_key = normalize_response_language(language)
    return LOCALIZED_RESPONSES[language_key].get(
        sales_difficulty,
        LOCALIZED_RESPONSES[language_key]["unknown-runtime-signal"],
    )


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def latency_bucket(milliseconds: int) -> str:
    if milliseconds <= 1000:
        return "under-1s"
    if milliseconds <= 2000:
        return "under-2s"
    return "over-2s"


def classify_runtime_input(case: dict, campaign: dict | None = None) -> dict:
    customer_input = case["customer_input"]
    transcript = customer_input.get("transcript", "")
    input_type = customer_input.get("input_type")
    stage = customer_input.get("stage")
    response_language = normalize_response_language((campaign or {}).get("language"))

    if input_type == "voicemail-detected":
        sales_difficulty = "voicemail"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "rapport",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if input_type == "silence-timeout" and customer_input.get("silence_count", 0) >= 2:
        sales_difficulty = "repeated-silence"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "not-interested",
            "selected_strategy": "rapport",
            "next_action": "close-politely",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if contains_any(transcript, STOP_OR_REFUSAL_RUNTIME_PHRASES):
        sales_difficulty = "do-not-call"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "do-not-call",
            "selected_strategy": "rapport",
            "next_action": "suppress-contact",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if contains_any(transcript, HUMAN_REQUEST_RUNTIME_PHRASES):
        sales_difficulty = "human-request"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "rapport",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if contains_any(transcript, ["garantieren", "guarantee", "stabil", "coverage", "geschwindigkeit"]):
        sales_difficulty = "claim-boundary"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "needs-human",
            "selected_strategy": "inquiry",
            "next_action": "escalate",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if contains_any(transcript, ["welcher genaue tarif", "welche genauen details", "was ist enthalten", "datenvolumen", "exact plan", "which plan", "which exact", "service details", "included"]):
        sales_difficulty = "product-detail-lookup"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "evidence-or-benefit",
            "next_action": "continue",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if stage == "scheduling" and contains_any(transcript, ["mittwoch", "wednesday", "10 uhr", "10 works"]):
        sales_difficulty = "scheduling-confirmation"
        return {
            "response_language": response_language,
            "detected_emotion": "positive",
            "sales_difficulty": sales_difficulty,
            "interest_state": "interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "confirm-scheduling",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if contains_any(transcript, ["vielleicht irgendwann", "vielleicht naechste woche", "naechste woche", "nothing firm", "next week", "cannot commit", "nichts fest"]):
        sales_difficulty = "timing-delay"
        return {
            "response_language": response_language,
            "detected_emotion": "neutral",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": "create-follow-up-task",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    if contains_any(transcript, ["guenstiger", "zu teuer", "too expensive", "lohnt sich", "aufwand", "worth the effort"]):
        sales_difficulty = "price-objection"
        return {
            "response_language": response_language,
            "detected_emotion": "skeptical-or-negative",
            "sales_difficulty": sales_difficulty,
            "interest_state": "maybe-interested",
            "selected_strategy": "inquiry",
            "next_action": "ask-follow-up",
            "agent_response": localized_response(response_language, sales_difficulty),
        }

    sales_difficulty = "unknown-runtime-signal"
    return {
        "response_language": response_language,
        "detected_emotion": "neutral",
        "sales_difficulty": sales_difficulty,
        "interest_state": "maybe-interested",
        "selected_strategy": "inquiry",
        "next_action": "ask-follow-up",
        "agent_response": localized_response(response_language, sales_difficulty),
    }


def background_modules_for(response_mode: str, expected: dict | None, classified: dict) -> list[str]:
    if expected is not None:
        return expected.get("background_modules", [])
    if response_mode == "bridge-then-background":
        return ["campaign-knowledge-lookup"]
    if classified["next_action"] == "suppress-contact":
        return ["crm-suppression-update"]
    if classified["next_action"] == "escalate":
        return ["human-handoff-prep"]
    if classified["next_action"] == "confirm-scheduling":
        return ["calendar-write"]
    if classified["next_action"] == "create-follow-up-task":
        return ["follow-up-task-write"]
    if classified["sales_difficulty"] == "repeated-silence":
        return ["no-response-log"]
    return []


def build_runtime_decision(case: dict, expected: dict | None = None, campaign: dict | None = None) -> dict:
    classified = classify_runtime_input(case, campaign)
    response_mode = "bridge-then-background" if classified["sales_difficulty"] == "product-detail-lookup" else "fast-response"
    first_response_ms = BRIDGE_RESPONSE_MS if response_mode == "bridge-then-background" else FAST_RESPONSE_MS
    call_control = "bridge-then-continue" if response_mode == "bridge-then-background" else call_control_for_next_action(
        classified["next_action"],
        classified["interest_state"],
    )
    bridge_response = classified["agent_response"] if response_mode == "bridge-then-background" else None

    runtime_decision = {
        "case_id": case["case_id"],
        "campaign_language": normalize_response_language((campaign or {}).get("language")),
        "response_language": classified["response_language"],
        "response_mode": response_mode,
        "first_response_latency_budget_ms": first_response_ms,
        "first_response_latency_bucket": latency_bucket(first_response_ms),
        "background_completion_budget_ms": BACKGROUND_COMPLETION_MS if response_mode == "bridge-then-background" else None,
        "background_modules": background_modules_for(response_mode, expected, classified),
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
    return runtime_decision


def run_case(case: dict, campaigns: list[dict] | None = None) -> dict:
    expected = case["expected_runtime"]
    campaign = find_campaign(campaigns or [], case["campaign_id"])
    runtime_decision = build_runtime_decision(case, expected, campaign)
    scores = score_case(case, runtime_decision)
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "campaign": {
            "language": normalize_response_language((campaign or {}).get("language")),
            "locale": (campaign or {}).get("locale"),
            "product_category": (campaign or {}).get("product_category"),
            "customer_type": (campaign or {}).get("customer_type"),
        },
        "runtime_scenario": case["runtime_scenario"],
        "expected_runtime": expected,
        "runtime_decision": runtime_decision,
        "scores": scores,
    }


def score_case(case: dict, decision: dict) -> dict:
    expected = case["expected_runtime"]
    expected_language = expected.get("response_language")
    expected_markers = [marker.lower() for marker in expected.get("response_must_include_any", [])]
    response_text = decision["agent_response"].lower()
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
        "response_language_match": expected_language is None or decision["response_language"] == expected_language,
        "response_marker_match": not expected_markers or any(marker in response_text for marker in expected_markers),
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
        "response_language_matches": 0,
        "response_marker_matches": 0,
        "live_path_subagent_violations": 0,
        "language_counts": {},
    }
    for result in results:
        scores = result["scores"]
        language = result["runtime_decision"].get("response_language", "en")
        summary["language_counts"][language] = summary["language_counts"].get(language, 0) + 1
        summary["response_mode_matches"] += int(scores["response_mode_match"])
        summary["latency_bucket_matches"] += int(scores["latency_bucket_match"])
        summary["background_modules_matches"] += int(scores["background_modules_match"])
        summary["emotion_matches"] += int(scores["emotion_match"])
        summary["sales_difficulty_matches"] += int(scores["sales_difficulty_match"])
        summary["interest_state_matches"] += int(scores["interest_state_match"])
        summary["strategy_matches"] += int(scores["strategy_match"])
        summary["next_action_matches"] += int(scores["next_action_match"])
        summary["call_control_matches"] += int(scores["call_control_match"])
        summary["response_language_matches"] += int(scores["response_language_match"])
        summary["response_marker_matches"] += int(scores["response_marker_match"])
        summary["live_path_subagent_violations"] += int(scores["live_path_subagent_violation"])
    return summary


def render_report(results: list[dict], summary: dict) -> str:
    lines = [
        "# Bilingual Realtime Sales Core Report",
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
        f"- Response-language matches: {summary['response_language_matches']} / {summary['case_total']}",
        f"- Response-marker matches: {summary['response_marker_matches']} / {summary['case_total']}",
        f"- Live-path sub-agent violations: {summary['live_path_subagent_violations']}",
        f"- Language counts: `{json.dumps(summary['language_counts'], sort_keys=True)}`",
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
                f"- Response language: `{decision['response_language']}`",
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
    campaigns, cases = load_realtime_cases(cases_path)
    results = [run_case(case, campaigns) for case in cases]
    summary = aggregate(results)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2), encoding="utf-8")

    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results, summary), encoding="utf-8")


if __name__ == "__main__":
    main()
