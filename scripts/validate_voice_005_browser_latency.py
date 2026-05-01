#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOICE_004_SCRIPT = ROOT / "scripts" / "run_browser_speech_demo.py"
MEASURE_SCRIPT = ROOT / "scripts" / "measure_voice_005_latency.py"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
RESULTS_OUT = GENERATED_DIR / "VOICE-005-latency-results.json"
REPORT_OUT = GENERATED_DIR / "VOICE-005-latency-report.md"
PRICE_TRANSCRIPT = "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt."


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


def assert_latency_block(block: dict) -> None:
    assert_condition(block["voice_milestone"] == "VOICE-005", "Latency block should identify VOICE-005.")
    assert_condition(block["measurement_scope"] == "local-python-after-final-transcript", "Unexpected scope.")
    assert_condition(block["browser_asr_measured"] is False, "Browser ASR should not be claimed as measured.")
    assert_condition(block["browser_tts_playback_measured"] is False, "Browser TTS playback should not be claimed as measured.")
    assert_condition(block["requires_api_key"] is False, "Latency measurement should not require an API key.")
    assert_condition(block["server_started"] is False, "Validator should not start a long-running server.")
    assert_condition(block["target_first_response_ms"] == 2000, "Unexpected first response target.")
    assert_condition(block["total_decision_loop_ms"] >= 0, "Total latency must be non-negative.")
    assert_condition(block["total_decision_loop_ms"] <= 2000, "Local decision loop should stay under 2s in prototype.")
    assert_condition(block["observed_bucket"] in ["under-1s", "under-2s", "over-2s"], "Unexpected latency bucket.")
    assert_condition("realtime_decision_ms" in block["segments"], "Missing realtime decision segment.")
    assert_condition("guarded_response_ms" in block["segments"], "Missing RESP-001 segment.")
    assert_condition("voice_packet_build_ms" in block["segments"], "Missing voice packet segment.")


def main() -> None:
    assert_condition(VOICE_004_SCRIPT.exists(), "VOICE-004 browser speech demo script is missing.")
    assert_condition(MEASURE_SCRIPT.exists(), "VOICE-005 latency measurement script is missing.")

    decision_run = run_command(
        [
            sys.executable,
            str(VOICE_004_SCRIPT),
            "--decision-transcript",
            PRICE_TRANSCRIPT,
        ]
    )
    assert_condition(decision_run.returncode == 0, decision_run.stderr)
    decision_packet = parse_json_stdout(decision_run)
    assert_condition("latency_measurement" in decision_packet, "VOICE-004 packet must include latency_measurement.")
    assert_latency_block(decision_packet["latency_measurement"])
    assert_condition(
        decision_packet["response_packet"]["response_generation"]["response_generation_id"] == "RESP-001-local-guarded",
        "VOICE-005 must preserve RESP-001 integration.",
    )

    measure_run = run_command(
        [
            sys.executable,
            str(MEASURE_SCRIPT),
            "--out",
            str(RESULTS_OUT),
            "--report-out",
            str(REPORT_OUT),
        ]
    )
    assert_condition(measure_run.returncode == 0, measure_run.stderr)
    payload = parse_json_stdout(measure_run)
    assert_condition(RESULTS_OUT.exists(), "Expected VOICE-005 JSON results artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-005 Markdown report artifact.")
    assert_condition(payload == json.loads(RESULTS_OUT.read_text(encoding="utf-8")), "Stdout and file JSON should match.")
    assert_condition(payload["voice_milestone"] == "VOICE-005", "Unexpected measurement milestone.")
    assert_condition(payload["server_started"] is False, "VOICE-005 validator should use one-shot mode.")
    assert_condition(payload["summary"]["case_count"] >= 4, "Expected at least four latency cases.")
    assert_condition(payload["summary"]["over_2s_count"] == 0, "No local prototype case should exceed 2s.")
    assert_condition(payload["summary"]["max_total_decision_loop_ms"] <= 2000, "Max latency should stay under 2s.")

    case_ids = {case["case_id"] for case in payload["cases"]}
    for expected_case in ["VOICE-005-C01", "VOICE-005-C02", "VOICE-005-C03", "VOICE-005-C04"]:
        assert_condition(expected_case in case_ids, f"Missing latency case {expected_case}.")

    for case in payload["cases"]:
        assert_latency_block(case["packet"]["latency_measurement"])
        assert_condition(case["packet"]["latency_measurement"]["total_decision_loop_ms"] == case["total_decision_loop_ms"], "Case latency mismatch.")

    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No server was started" in report_text, "Report should state no server was started.")
    assert_condition("RESP-001" in report_text, "Report should mention RESP-001 segment measurement.")
    assert_condition("Browser ASR and browser TTS playback are not measured" in report_text, "Report should name exclusions.")

    serialized = json.dumps(decision_packet) + json.dumps(payload) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-005 browser latency validation passed.")


if __name__ == "__main__":
    main()
