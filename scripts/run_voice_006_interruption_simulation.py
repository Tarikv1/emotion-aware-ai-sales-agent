#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from generate_voice_response import resolve_project_path
from run_browser_speech_demo import DEFAULT_CASES_PATH, build_browser_decision_packet
from voice_interruption_policy import classify_interruption_candidate, interruption_policy_metadata


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-006"
DEFAULT_RESULTS_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-006-interruption-results.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-006-interruption-report.md"
CURRENT_AGENT_RESPONSE = (
    "That makes sense. Is your bigger concern the monthly price, the contract terms, "
    "or whether reviewing options is worth your time?"
)
GERMAN_AGENT_RESPONSE = (
    "Das verstehe ich. Geht es Ihnen eher um den monatlichen Preis, die Vertragsbedingungen "
    "oder darum, ob sich ein kurzer Vergleich ueberhaupt lohnt?"
)

INTERRUPTION_CASES = [
    {
        "case_id": "VOICE-006-C01",
        "case_title": "English background noise must not stop the agent",
        "language": "en",
        "audio_event_type": "background-noise",
        "transcript": "",
        "agent_response": CURRENT_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C02",
        "case_title": "English likely echo must not stop the agent",
        "language": "en",
        "audio_event_type": "speech-interim",
        "transcript": "Is your bigger concern the monthly price",
        "agent_response": CURRENT_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C03",
        "case_title": "English short ambiguous interruption asks clarification",
        "language": "en",
        "audio_event_type": "speech-final",
        "transcript": "Huh?",
        "agent_response": CURRENT_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C04",
        "case_title": "English clear customer question becomes a new turn",
        "language": "en",
        "audio_event_type": "speech-final",
        "transcript": "What does that mean?",
        "agent_response": CURRENT_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C05",
        "case_title": "English stop request interrupts and ends call",
        "language": "en",
        "audio_event_type": "speech-final",
        "transcript": "Stop calling me.",
        "agent_response": CURRENT_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C06",
        "case_title": "English human request interrupts and escalates",
        "language": "en",
        "audio_event_type": "speech-final",
        "transcript": "Please have a real person call me.",
        "agent_response": CURRENT_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C07",
        "case_title": "German short ambiguous interruption asks clarification",
        "language": "de",
        "audio_event_type": "speech-final",
        "transcript": "Wie bitte?",
        "agent_response": GERMAN_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C08",
        "case_title": "German clear customer question becomes a new turn",
        "language": "de",
        "audio_event_type": "speech-final",
        "transcript": "Was bedeutet das?",
        "agent_response": GERMAN_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C09",
        "case_title": "German refusal interrupts and ends call",
        "language": "de",
        "audio_event_type": "speech-final",
        "transcript": "Rufen Sie mich bitte nicht mehr an.",
        "agent_response": GERMAN_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C10",
        "case_title": "German human request interrupts and escalates",
        "language": "de",
        "audio_event_type": "speech-final",
        "transcript": "Bitte eine echte Person anrufen.",
        "agent_response": GERMAN_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C11",
        "case_title": "German short acknowledgement does not stop the agent",
        "language": "de",
        "audio_event_type": "speech-final",
        "transcript": "Verstanden.",
        "agent_response": GERMAN_AGENT_RESPONSE,
    },
    {
        "case_id": "VOICE-006-C12",
        "case_title": "German likely echo must not stop the agent",
        "language": "de",
        "audio_event_type": "speech-interim",
        "transcript": "monatlichen Preis die Vertragsbedingungen",
        "agent_response": GERMAN_AGENT_RESPONSE,
    },
]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_case(case: dict, cases_path: Path) -> dict:
    interruption_decision = classify_interruption_candidate(
        transcript=case["transcript"],
        agent_response=case["agent_response"],
        audio_event_type=case["audio_event_type"],
        agent_is_speaking=True,
        language_hint=case["language"],
    )
    voice_packet = None
    if interruption_decision["send_to_agent_core"]:
        voice_packet = build_browser_decision_packet(
            transcript=case["transcript"],
            campaign_id="campaign-prod-005-b2c-telecom",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=cases_path,
        )
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "language": case["language"],
        "audio_event_type": case["audio_event_type"],
        "transcript": case["transcript"],
        "agent_response_under_playback": case["agent_response"],
        "interruption_decision": interruption_decision,
        "voice_packet": voice_packet,
    }


def summarize(cases: list[dict]) -> dict:
    languages = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1
    return {
        "case_count": len(cases),
        "languages": languages,
        "confirmed_interruptions": sum(1 for case in cases if case["interruption_decision"]["interruption_confirmed"]),
        "false_interruptions_blocked": sum(
            1
            for case in cases
            if case["interruption_decision"]["interruption_type"] in {"noise_or_no_transcript", "likely_echo"}
            and not case["interruption_decision"]["interruption_confirmed"]
        ),
        "clarification_cases": sum(
            1
            for case in cases
            if case["interruption_decision"]["agent_speech_action"] == "pause-and-ask-clarification"
        ),
        "sent_to_agent_core": sum(1 for case in cases if case["interruption_decision"]["send_to_agent_core"]),
    }


def render_report(payload: dict) -> str:
    lines = [
        "# VOICE-006 Safe Interruption Report",
        "",
        "This report was generated by `scripts/run_voice_006_interruption_simulation.py`.",
        "",
        "The same interruption policy is tested for English and German. This is one multilingual product behavior, not two separate products.",
        "",
        "Raw audio alone does not cancel agent speech.",
        "",
        "Short ambiguous interruption asks clarification instead of being sent directly to the sales core.",
        "",
        "Likely echo is ignored so the agent does not interrupt itself.",
        "",
        "## Summary",
        "",
        f"- Cases: `{payload['summary']['case_count']}`",
        f"- English cases: `{payload['summary']['languages'].get('en', 0)}`",
        f"- German cases: `{payload['summary']['languages'].get('de', 0)}`",
        f"- Confirmed interruptions: `{payload['summary']['confirmed_interruptions']}`",
        f"- False interruptions blocked: `{payload['summary']['false_interruptions_blocked']}`",
        f"- Clarification cases: `{payload['summary']['clarification_cases']}`",
        f"- Sent to agent core: `{payload['summary']['sent_to_agent_core']}`",
        "",
        "## Case Results",
        "",
    ]
    for case in payload["cases"]:
        decision = case["interruption_decision"]
        call_control = None
        if case["voice_packet"] is not None:
            call_control = case["voice_packet"]["response_packet"]["decision"]["call_control"]
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Interruption type: `{decision['interruption_type']}`",
                f"- Confirmed: `{decision['interruption_confirmed']}`",
                f"- Agent speech action: `{decision['agent_speech_action']}`",
                f"- Send to agent core: `{decision['send_to_agent_core']}`",
                f"- Call control: `{call_control or 'not sent'}`",
                f"- Rationale: {decision['rationale']}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-006 safe interruption simulation.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    parser.add_argument("--out", default=str(DEFAULT_RESULTS_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    cases = [run_case(case, cases_path) for case in INTERRUPTION_CASES]
    payload = {
        "voice_milestone": VOICE_MILESTONE,
        "policy": interruption_policy_metadata(),
        "server_started": False,
        "requires_api_key": False,
        "summary": summarize(cases),
        "cases": cases,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
