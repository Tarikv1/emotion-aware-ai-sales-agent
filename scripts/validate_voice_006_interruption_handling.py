#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMULATION_SCRIPT = ROOT / "scripts" / "run_voice_006_interruption_simulation.py"
VOICE_004_SCRIPT = ROOT / "scripts" / "run_browser_speech_demo.py"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
RESULTS_OUT = GENERATED_DIR / "VOICE-006-interruption-results.json"
REPORT_OUT = GENERATED_DIR / "VOICE-006-interruption-report.md"
HTML_OUT = GENERATED_DIR / "VOICE-006-browser-speech-demo.html"
METADATA_OUT = GENERATED_DIR / "VOICE-006-browser-speech-demo-metadata.json"


SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def parse_json_stdout(completed: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def case_by_id(payload: dict, case_id: str) -> dict:
    for case in payload["cases"]:
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"Missing case {case_id}")


def interruption(case: dict) -> dict:
    return case["interruption_decision"]


def main() -> None:
    assert_condition(SIMULATION_SCRIPT.exists(), "VOICE-006 interruption simulation script is missing.")
    assert_condition(VOICE_004_SCRIPT.exists(), "VOICE-004 browser speech demo script is missing.")

    completed = run_command(
        [
            sys.executable,
            str(SIMULATION_SCRIPT),
            "--out",
            str(RESULTS_OUT),
            "--report-out",
            str(REPORT_OUT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = parse_json_stdout(completed)
    assert_condition(RESULTS_OUT.exists(), "Expected VOICE-006 JSON results artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-006 Markdown report artifact.")
    assert_condition(payload == json.loads(RESULTS_OUT.read_text(encoding="utf-8")), "Stdout and file JSON should match.")
    assert_condition(payload["voice_milestone"] == "VOICE-006", "Unexpected milestone.")
    assert_condition(payload["requires_api_key"] is False, "VOICE-006 must stay no-key.")
    assert_condition(payload["server_started"] is False, "VOICE-006 validation should not start a server.")
    assert_condition(payload["summary"]["case_count"] >= 6, "Expected at least six interruption cases.")
    assert_condition(payload["summary"]["false_interruptions_blocked"] >= 2, "Noise and echo should be blocked.")
    assert_condition(payload["summary"]["clarification_cases"] >= 1, "Short ambiguous interruptions should clarify.")

    noise = interruption(case_by_id(payload, "VOICE-006-C01"))
    assert_condition(noise["interruption_type"] == "noise_or_no_transcript", "Noise should not become an interruption.")
    assert_condition(noise["interruption_confirmed"] is False, "Noise must not stop agent speech.")
    assert_condition(noise["agent_speech_action"] == "continue-speaking", "Noise should continue speech.")

    echo = interruption(case_by_id(payload, "VOICE-006-C02"))
    assert_condition(echo["interruption_type"] == "likely_echo", "Echo should be classified as echo.")
    assert_condition(echo["interruption_confirmed"] is False, "Echo must not stop agent speech.")
    assert_condition(echo["agent_speech_action"] == "continue-speaking", "Echo should continue speech.")

    short = interruption(case_by_id(payload, "VOICE-006-C03"))
    assert_condition(short["interruption_type"] == "short_ambiguous_interruption", "Short phrase should be ambiguous.")
    assert_condition(short["interruption_confirmed"] is True, "Short meaningful phrase should pause the agent.")
    assert_condition(short["agent_speech_action"] == "pause-and-ask-clarification", "Short phrase should ask clarification.")
    assert_condition(short["send_to_agent_core"] is False, "Short ambiguous phrase should not go straight to sales core.")
    assert_condition("unclear" in short["clarification_response"].lower() or "ask" in short["clarification_response"].lower(), "Clarification response should invite a question.")

    question = interruption(case_by_id(payload, "VOICE-006-C04"))
    assert_condition(question["interruption_type"] == "clear_customer_question", "Question should be clear interruption.")
    assert_condition(question["interruption_confirmed"] is True, "Question should stop current agent speech.")
    assert_condition(question["agent_speech_action"] == "cancel-agent-speech-and-process-turn", "Question should process as new turn.")
    assert_condition(question["send_to_agent_core"] is True, "Question should be sent to agent core.")

    stop_case = case_by_id(payload, "VOICE-006-C05")
    stop_decision = interruption(stop_case)
    assert_condition(stop_decision["interruption_type"] == "stop_or_refusal", "Stop/refusal should be detected.")
    assert_condition(stop_decision["agent_speech_action"] == "cancel-agent-speech-and-process-turn", "Stop should cancel and process.")
    assert_condition(stop_case["voice_packet"]["response_packet"]["decision"]["call_control"] == "end-call", "Stop request should end call.")

    human_case = case_by_id(payload, "VOICE-006-C06")
    human_decision = interruption(human_case)
    assert_condition(human_decision["interruption_type"] == "human_request", "Human request should be detected.")
    assert_condition(human_case["voice_packet"]["response_packet"]["decision"]["call_control"] == "transfer-or-escalate", "Human request should escalate.")

    html_run = run_command(
        [
            sys.executable,
            str(VOICE_004_SCRIPT),
            "--export-html",
            str(HTML_OUT),
            "--export-metadata",
            str(METADATA_OUT),
        ]
    )
    assert_condition(html_run.returncode == 0, html_run.stderr)
    html = HTML_OUT.read_text(encoding="utf-8")
    metadata = json.loads(METADATA_OUT.read_text(encoding="utf-8"))
    assert_condition(metadata["interruption_policy"]["voice_milestone"] == "VOICE-006", "Metadata should expose VOICE-006 policy.")
    assert_condition("interruptionState" in html, "Browser demo should expose interruption state.")
    assert_condition("classifyInterruptionCandidate" in html, "Browser demo should include interruption classifier.")
    assert_condition("pause-and-ask-clarification" in html, "Browser demo should support clarification action.")
    assert_condition("likely_echo" in html, "Browser demo should guard against echo.")
    assert_condition("speechSynthesis.cancel()" in html, "Browser demo should cancel only after confirmed interruption.")
    assert_condition("raw audio alone does not cancel" in html.lower(), "Browser copy should state raw audio alone does not cancel.")

    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("Raw audio alone does not cancel agent speech" in report_text, "Report should document raw-audio guardrail.")
    assert_condition("Short ambiguous interruption asks clarification" in report_text, "Report should document clarification layer.")
    assert_condition("likely echo" in report_text.lower(), "Report should document echo handling.")

    serialized = json.dumps(payload) + html + json.dumps(metadata) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-006 interruption handling validation passed.")


if __name__ == "__main__":
    main()
