#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_030_raw_audio_reader.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030-raw-audio-local-reader.json"
TMP_DIR = ROOT / ".tmp" / "voice-030-validation"
RESULT_PATH = TMP_DIR / "results.json"
REPORT_PATH = TMP_DIR / "report.md"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def validate_synthetic_raw_audio_reader() -> None:
    assert_condition(RUNNER.exists(), "VOICE-030 raw audio runner is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-030 case file is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--case",
            str(CASE_PATH),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    assert_condition(RESULT_PATH.exists(), "VOICE-030 result JSON was not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-030 report was not created.")

    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    assert_condition(payload["voice_milestone"] == "VOICE-030A", "Unexpected milestone.")
    assert_condition(payload["source_mode"] == "synthetic_audio_fixture", "Default run should use synthetic audio fixtures.")
    assert_condition(payload["privacy_boundary"]["private_input_read"] is False, "Synthetic run must not read private input.")
    assert_condition(payload["privacy_boundary"]["raw_audio_decoded"] is True, "Synthetic WAV audio should be decoded.")
    assert_condition(payload["privacy_boundary"]["raw_private_audio_decoded"] is False, "Synthetic run must not decode private audio.")
    assert_condition(payload["privacy_boundary"]["provider_calls_made"] is False, "VOICE-030 must not call providers.")
    assert_condition(payload["privacy_boundary"]["transcription_created"] is False, "VOICE-030A must not transcribe audio.")
    assert_condition(payload["privacy_boundary"]["voice_cloning_used"] is False, "VOICE-030 must not clone voices.")
    assert_condition(payload["privacy_boundary"]["runtime_profile_applied"] is False, "VOICE-030 must not auto-apply runtime settings.")
    assert_condition(payload["summary"]["audio_file_count"] == 2, "Synthetic run should analyze two files.")
    assert_condition(payload["summary"]["supported_file_count"] == 2, "Synthetic WAV files should be supported.")
    assert_condition(payload["summary"]["unsupported_file_count"] == 0, "Synthetic run should have no unsupported files.")
    assert_condition(payload["summary"]["languages"] == {"de": 1, "en": 1}, "Synthetic run should cover English and German.")
    assert_condition(payload["summary"]["total_pause_count"] >= 4, "Synthetic fixtures should include measurable pauses.")
    assert_condition(payload["summary"]["total_duration_seconds"] > 4.0, "Synthetic fixtures should have duration.")

    for result in payload["audio_results"]:
        features = result["features"]
        assert_condition(features["duration_seconds"] > 2.0, "Each fixture should be longer than two seconds.")
        assert_condition(features["pause_count"] >= 2, "Each fixture should contain at least two pauses.")
        assert_condition(features["speech_burst_count"] >= 3, "Each fixture should contain speech bursts.")
        assert_condition(0 < features["pause_ratio"] < 1, "Pause ratio should be bounded.")
        assert_condition(features["sample_rate_hz"] == 16000, "Synthetic fixture sample rate should be stable.")

    combined = RESULT_PATH.read_text(encoding="utf-8") + REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("data/private" not in combined.replace("\\", "/"), "Public artifact should not mention private file paths.")


def validate_private_read_guard() -> None:
    private_input = ROOT / "data" / "private" / "tarik-speech-samples" / "raw-audio"
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--input-dir",
            str(private_input),
            "--out",
            str(TMP_DIR / "leaky-public-output.json"),
        ]
    )
    combined = completed.stdout + completed.stderr
    assert_condition(completed.returncode != 0, "Private raw audio should require explicit --allow-private-read.")
    assert_condition("--allow-private-read" in combined, "Private-read refusal should explain the required flag.")


def main() -> None:
    validate_synthetic_raw_audio_reader()
    validate_private_read_guard()
    print("VOICE-030 raw audio reader validation passed.")


if __name__ == "__main__":
    main()
