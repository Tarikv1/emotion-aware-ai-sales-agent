#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_035_connected_speech.py"
MODULE = ROOT / "scripts" / "voice_connected_speech.py"
RUNTIME_RUNNER = ROOT / "scripts" / "generate_runtime_voice_delivery.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-035-connected-speech-phrase-flow.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_035_CONNECTED_SPEECH_PHRASE_FLOW.md"
TMP_DIR = ROOT / ".tmp" / "voice-035-validation"
RESULT_PATH = TMP_DIR / "runtime-result.json"
REPORT_PATH = TMP_DIR / "runtime-report.md"
VOICE_035_OUT_DIR = TMP_DIR / "runner"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got {completed.stdout!r}") from exc


def run_runtime(
    *,
    campaign: str,
    transcript: str,
    candidate_response: str | None = None,
) -> dict:
    args = [
        sys.executable,
        str(RUNTIME_RUNNER),
        "--campaign",
        campaign,
        "--stage",
        "relevance-check",
        "--transcript",
        transcript,
        "--cases",
        str(CASES_PATH),
        "--provider",
        "elevenlabs",
        "--out",
        str(RESULT_PATH),
        "--report-out",
        str(REPORT_PATH),
    ]
    if candidate_response:
        args.extend(["--candidate-response", candidate_response])
    completed = run_command(args)
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return parse_stdout_json(completed)


def validate_required_files() -> None:
    for path in [RUNNER, MODULE, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-035 file is missing: {path.relative_to(ROOT)}")


def validate_german_runtime_phrase_flow() -> None:
    payload = run_runtime(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
    )
    delivery = payload["voice_delivery"]
    connected = delivery["voice_connected_speech"]
    provider = connected["connected_provider_rendering"]
    rendered = provider["rendered_text"]

    assert_condition(connected["voice_milestone"] == "VOICE-035", connected)
    assert_condition(connected["language"] == "de", connected)
    assert_condition(connected["validation"]["passed"] is True, connected["validation"])
    assert_condition(delivery["validation"]["voice_connected_speech_passed"] is True, delivery["validation"])
    assert_condition(connected["flow_join_count"] >= 1, connected)
    assert_condition("Das verstehe ich, also geht's" in rendered, rendered)
    assert_condition("Also, Geht's" not in rendered, rendered)
    assert_condition(". <break" not in rendered, rendered)
    assert_condition(provider["voice_settings"]["speed"] >= 1.09, provider["voice_settings"])
    assert_condition(provider["voice_settings"]["speed"] <= 1.16, provider["voice_settings"])
    assert_condition(delivery["final_response_unchanged"] is True, delivery)
    assert_condition(delivery["provider_calls_made"] is False, delivery)
    assert_condition(delivery["customer_audio_uploaded"] is False, delivery)
    assert_condition(delivery["voice_cloning_used"] is False, delivery)


def validate_english_runtime_phrase_flow() -> None:
    payload = run_runtime(
        campaign="campaign-prod-005-b2b-software",
        transcript="That sounds expensive.",
        candidate_response=(
            "I will keep this simple. You are right to ask. It is only useful if there is a practical next step."
        ),
    )
    delivery = payload["voice_delivery"]
    connected = delivery["voice_connected_speech"]
    provider = connected["connected_provider_rendering"]
    rendered = provider["rendered_text"].lower()

    assert_condition(connected["language"] == "en", connected)
    assert_condition(connected["validation"]["passed"] is True, connected["validation"])
    assert_condition(delivery["validation"]["voice_connected_speech_passed"] is True, delivery["validation"])
    assert_condition(connected["flow_join_count"] >= 2, connected)
    assert_condition("i'll keep this simple, well" in rendered, provider["rendered_text"])
    assert_condition("right to ask, and it's" in rendered, provider["rendered_text"])
    assert_condition("simple. <break" not in rendered, provider["rendered_text"])
    assert_condition(provider["voice_settings"]["speed"] >= 1.07, provider["voice_settings"])
    assert_condition(provider["voice_settings"]["speed"] <= 1.15, provider["voice_settings"])


def validate_protected_text_unchanged() -> None:
    payload = run_runtime(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Rufen Sie mich bitte nicht mehr an.",
    )
    delivery = payload["voice_delivery"]
    connected = delivery["voice_connected_speech"]
    provider = connected["connected_provider_rendering"]

    assert_condition(delivery["segments"][0]["segment_type"] == "do_not_call", delivery["segments"])
    assert_condition(connected["flow_join_count"] == 0, connected)
    assert_condition(connected["validation"]["protected_segment_text_changes"] == [], connected["validation"])
    assert_condition(provider["rendered_text"] == payload["final_response"], provider)
    assert_condition(provider["voice_settings"].get("speed", 1.0) == 1.0, provider["voice_settings"])


def validate_standalone_runner() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--out-dir",
            str(VOICE_035_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = parse_stdout_json(completed)
    assert_condition(payload["voice_milestone"] == "VOICE-035", payload)
    assert_condition(payload["summary"]["case_count"] >= 3, payload["summary"])
    assert_condition(payload["summary"]["validation_passed"] == payload["summary"]["case_count"], payload["summary"])
    assert_condition(payload["summary"]["flow_join_cases"] >= 2, payload["summary"])
    assert_condition(payload["summary"]["provider_calls_made"] is False, payload["summary"])
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, payload["summary"])
    assert_condition(payload["summary"]["voice_cloning_used"] is False, payload["summary"])
    assert_condition((VOICE_035_OUT_DIR / "results.json").exists(), "VOICE-035 runner did not write JSON.")
    assert_condition((VOICE_035_OUT_DIR / "report.md").exists(), "VOICE-035 runner did not write report.")


def main() -> None:
    validate_required_files()
    validate_german_runtime_phrase_flow()
    validate_english_runtime_phrase_flow()
    validate_protected_text_unchanged()
    validate_standalone_runner()
    print("VOICE-035 connected speech validation passed.")


if __name__ == "__main__":
    main()
