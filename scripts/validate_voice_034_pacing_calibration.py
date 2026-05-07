#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_034_pacing_calibration.py"
MODULE = ROOT / "scripts" / "voice_pacing_calibration.py"
RUNTIME_RUNNER = ROOT / "scripts" / "generate_runtime_voice_delivery.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-034-pacing-calibration-v2.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_034_PACING_CALIBRATION_V2.md"
TMP_DIR = ROOT / ".tmp" / "voice-034-validation"
RESULT_PATH = TMP_DIR / "runtime-result.json"
REPORT_PATH = TMP_DIR / "runtime-report.md"
VOICE_034_OUT_DIR = TMP_DIR / "runner"


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
    provider: str = "elevenlabs",
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
        provider,
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


def break_ms_values(text: str) -> list[int]:
    values = []
    for match in re.finditer(r"<break\s+time=\"(?P<value>[0-9.]+)(?P<unit>ms|s)\"\s*/?>", text, flags=re.IGNORECASE):
        value = float(match.group("value"))
        unit = match.group("unit").lower()
        values.append(int(round(value * 1000)) if unit == "s" else int(round(value)))
    return values


def validate_required_files() -> None:
    for path in [RUNNER, MODULE, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-034 file is missing: {path.relative_to(ROOT)}")


def validate_german_runtime_gap_tightening() -> None:
    payload = run_runtime(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
    )
    delivery = payload["voice_delivery"]
    calibration = delivery["voice_pacing_calibration"]
    provider = delivery["provider_rendering"]

    assert_condition(calibration["voice_milestone"] == "VOICE-034", calibration)
    assert_condition(calibration["language"] == "de", calibration)
    assert_condition(calibration["validation"]["passed"] is True, calibration["validation"])
    assert_condition(calibration["german_word_gap_reduction_applied"] is True, calibration)
    assert_condition(calibration["tuned_segment_count"] >= 1, calibration)
    assert_condition(provider["pacing_calibrated"] is True, provider)
    assert_condition(calibration["average_speed_ratio"] >= 1.09, calibration)
    assert_condition(calibration["average_speed_ratio"] <= 1.16, calibration)
    calibrated_settings = calibration["calibrated_provider_rendering"]["voice_settings"]
    assert_condition(calibrated_settings["speed"] >= 1.09, calibrated_settings)
    assert_condition(calibrated_settings["speed"] <= 1.16, calibrated_settings)
    if delivery["voice_listening_calibration"]["german_connected_speech_relaxed"]:
        assert_condition(provider["voice_settings"]["speed"] >= 1.03, provider["voice_settings"])
        assert_condition(provider["voice_settings"]["speed"] <= 1.08, provider["voice_settings"])
    else:
        assert_condition(provider["voice_settings"]["speed"] >= 1.09, provider["voice_settings"])
        assert_condition(provider["voice_settings"]["speed"] <= 1.16, provider["voice_settings"])
    assert_condition(provider["provider_tag_count"] <= calibration["source_provider_tag_count"], calibration)
    assert_condition(
        calibration["average_break_duration_after_ms"] <= calibration["average_break_duration_before_ms"],
        calibration,
    )
    assert_condition(
        all(value <= 210 for value in break_ms_values(provider["rendered_text"])),
        provider["rendered_text"],
    )
    assert_condition(delivery["final_response_unchanged"] is True, delivery)
    assert_condition(delivery["provider_calls_made"] is False, delivery)
    assert_condition(delivery["customer_audio_uploaded"] is False, delivery)
    assert_condition(delivery["voice_cloning_used"] is False, delivery)


def validate_english_runtime_sales_pace() -> None:
    payload = run_runtime(
        campaign="campaign-prod-005-b2b-software",
        transcript="That sounds expensive.",
        candidate_response=(
            "I will keep this simple. You are right to ask. It is only useful if there is a practical next step."
        ),
    )
    calibration = payload["voice_delivery"]["voice_pacing_calibration"]
    provider = payload["voice_delivery"]["provider_rendering"]
    assert_condition(calibration["language"] == "en", calibration)
    assert_condition(calibration["validation"]["passed"] is True, calibration["validation"])
    assert_condition(calibration["german_word_gap_reduction_applied"] is False, calibration)
    assert_condition(provider["voice_settings"]["speed"] >= 1.07, provider["voice_settings"])
    assert_condition(provider["voice_settings"]["speed"] <= 1.15, provider["voice_settings"])
    assert_condition(provider["pacing_calibrated"] is True, provider)


def validate_protected_text_unchanged() -> None:
    payload = run_runtime(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Rufen Sie mich bitte nicht mehr an.",
    )
    delivery = payload["voice_delivery"]
    calibration = delivery["voice_pacing_calibration"]
    provider = delivery["provider_rendering"]
    assert_condition(delivery["segments"][0]["segment_type"] == "do_not_call", delivery["segments"])
    assert_condition(calibration["tuned_segment_count"] == 0, calibration)
    assert_condition(calibration["validation"]["protected_segment_text_changes"] == [], calibration["validation"])
    assert_condition(provider["rendered_text"] == payload["final_response"], provider)
    assert_condition(provider["voice_settings"].get("speed", 1.0) == 1.0, provider["voice_settings"])


def validate_standalone_runner() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--out-dir",
            str(VOICE_034_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = parse_stdout_json(completed)
    assert_condition(payload["voice_milestone"] == "VOICE-034", payload)
    assert_condition(payload["summary"]["case_count"] >= 3, payload["summary"])
    assert_condition(payload["summary"]["validation_passed"] == payload["summary"]["case_count"], payload["summary"])
    assert_condition(payload["summary"]["german_cases"] >= 1, payload["summary"])
    assert_condition(payload["summary"]["provider_calls_made"] is False, payload["summary"])
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, payload["summary"])
    assert_condition(payload["summary"]["voice_cloning_used"] is False, payload["summary"])
    assert_condition((VOICE_034_OUT_DIR / "results.json").exists(), "VOICE-034 runner did not write JSON.")
    assert_condition((VOICE_034_OUT_DIR / "report.md").exists(), "VOICE-034 runner did not write report.")


def main() -> None:
    validate_required_files()
    validate_german_runtime_gap_tightening()
    validate_english_runtime_sales_pace()
    validate_protected_text_unchanged()
    validate_standalone_runner()
    print("VOICE-034 pacing calibration validation passed.")


if __name__ == "__main__":
    main()
