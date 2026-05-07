#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_036_listening_calibration.py"
MODULE = ROOT / "scripts" / "voice_listening_calibration.py"
RUNTIME_TTS_RUNNER = ROOT / "scripts" / "generate_runtime_tts_delivery.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-036-listening-calibration.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_036_LISTENING_CALIBRATION.md"
TMP_DIR = ROOT / ".tmp" / "voice-036-validation"
VOICE_036_OUT_DIR = TMP_DIR / "runner"


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


def run_resp_003(
    *,
    campaign: str,
    transcript: str,
    candidate_response: str | None = None,
    out_name: str,
) -> dict:
    args = [
        sys.executable,
        str(RUNTIME_TTS_RUNNER),
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
        "--audio-dir",
        str(TMP_DIR / "audio"),
        "--out",
        str(TMP_DIR / f"{out_name}.json"),
        "--report-out",
        str(TMP_DIR / f"{out_name}.md"),
    ]
    if candidate_response:
        args.extend(["--candidate-response", candidate_response])
    completed = run_command(args)
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return parse_stdout_json(completed)


def validate_required_files() -> None:
    for path in [RUNNER, MODULE, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-036 file is missing: {path.relative_to(ROOT)}")


def validate_german_relaxed_connected_speech() -> None:
    payload = run_resp_003(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
        out_name="de-runtime",
    )
    delivery = payload["voice_delivery"]
    tts = payload["tts_delivery"]
    calibration = delivery["voice_listening_calibration"]
    provider = delivery["provider_rendering"]
    rendered = provider["rendered_text"]
    speed = float(provider["voice_settings"]["speed"])

    assert_condition(calibration["voice_milestone"] == "VOICE-036", calibration)
    assert_condition(calibration["language"] == "de", calibration)
    assert_condition(calibration["validation"]["passed"] is True, calibration["validation"])
    assert_condition(delivery["validation"]["voice_listening_calibration_passed"] is True, delivery["validation"])
    assert_condition(delivery["voice_connected_speech"]["flow_join_count"] >= 1, delivery["voice_connected_speech"])
    assert_condition(calibration["german_connected_speech_relaxed"] is True, calibration)
    assert_condition("Das verstehe ich, <break time=\"0.08s\" /> also geht's" in rendered, rendered)
    assert_condition(tts["tts_input_text"] == rendered, tts)
    assert_condition(0.97 <= speed <= 1.02, provider["voice_settings"])
    assert_condition(delivery["final_response_unchanged"] is True, delivery)
    assert_condition(delivery["provider_calls_made"] is False, delivery)
    assert_condition(tts["provider_calls_made"] is False, tts)
    assert_condition(tts["customer_audio_uploaded"] is False, tts)
    assert_condition(tts["voice_cloning_used"] is False, tts)


def validate_english_emphasis_guard() -> None:
    payload = run_resp_003(
        campaign="campaign-prod-005-b2b-software",
        transcript="That sounds expensive.",
        candidate_response=(
            "I will keep this simple. You are right to ask. It is only useful if there is a practical next step."
        ),
        out_name="en-runtime",
    )
    delivery = payload["voice_delivery"]
    calibration = delivery["voice_listening_calibration"]
    provider = delivery["provider_rendering"]
    rendered = provider["rendered_text"].lower()
    prosody_plan = delivery["prosody"]["prosody_plan"]
    emphasis_targets = [cue.get("target", "").lower() for cue in prosody_plan if cue.get("type") == "emphasis"]

    assert_condition(calibration["language"] == "en", calibration)
    assert_condition(calibration["validation"]["passed"] is True, calibration["validation"])
    assert_condition(calibration["emphasis_guard"]["blocked_emphasis_count"] >= 1, calibration)
    assert_condition("practical" not in emphasis_targets, prosody_plan)
    assert_condition(provider["unsupported_cue_counts"].get("emphasis", 0) == 0, provider["unsupported_cue_counts"])
    assert_condition("i'll keep this simple, well, you're right to ask, and it's" in rendered, provider["rendered_text"])
    assert_condition(1.07 <= float(provider["voice_settings"]["speed"]) <= 1.15, provider["voice_settings"])


def validate_protected_text_unchanged() -> None:
    payload = run_resp_003(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Rufen Sie mich bitte nicht mehr an.",
        out_name="protected-runtime",
    )
    delivery = payload["voice_delivery"]
    tts = payload["tts_delivery"]
    calibration = delivery["voice_listening_calibration"]
    provider = delivery["provider_rendering"]

    assert_condition(delivery["segments"][0]["segment_type"] == "do_not_call", delivery["segments"])
    assert_condition(calibration["listening_adjustment_count"] == 0, calibration)
    assert_condition(calibration["validation"]["protected_segment_text_changes"] == [], calibration["validation"])
    assert_condition(provider["rendered_text"] == payload["final_response"], provider)
    assert_condition(provider["voice_settings"].get("speed", 1.0) == 1.0, provider["voice_settings"])
    assert_condition(tts["tts_input_source"] == "final_response", tts)
    assert_condition(tts["tts_input_text"] == payload["final_response"], tts)


def validate_standalone_runner() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--out-dir",
            str(VOICE_036_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = parse_stdout_json(completed)
    assert_condition(payload["voice_milestone"] == "VOICE-036", payload)
    assert_condition(payload["summary"]["case_count"] >= 3, payload["summary"])
    assert_condition(payload["summary"]["validation_passed"] == payload["summary"]["case_count"], payload["summary"])
    assert_condition(payload["summary"]["german_relaxed_cases"] >= 1, payload["summary"])
    assert_condition(payload["summary"]["emphasis_blocked_cases"] >= 1, payload["summary"])
    assert_condition(payload["summary"]["provider_calls_made"] is False, payload["summary"])
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, payload["summary"])
    assert_condition(payload["summary"]["voice_cloning_used"] is False, payload["summary"])
    assert_condition((VOICE_036_OUT_DIR / "results.json").exists(), "VOICE-036 runner did not write JSON.")
    assert_condition((VOICE_036_OUT_DIR / "report.md").exists(), "VOICE-036 runner did not write report.")


def main() -> None:
    validate_required_files()
    validate_german_relaxed_connected_speech()
    validate_english_emphasis_guard()
    validate_protected_text_unchanged()
    validate_standalone_runner()
    print("VOICE-036 listening calibration validation passed.")


if __name__ == "__main__":
    main()
