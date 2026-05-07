#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_030d_private_feature_review.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030d-private-feature-review.json"
PRIVATE_ROOT = ROOT / "data" / "private" / "voice-030d-validation"
FEATURES_DIR = PRIVATE_ROOT / "derived" / "audio-features"
SUMMARY_PATH = PRIVATE_ROOT / "derived" / "review" / "voice-030d-feature-review-summary.json"
REPORT_PATH = PRIVATE_ROOT / "derived" / "review" / "voice-030d-feature-review-summary.md"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_feature(
    sample_id: str,
    *,
    duration_seconds: float,
    speech_burst_count: int,
    energy_variation: float,
    mean_speech_rms: float,
    pause_ratio: float,
    average_pause_ms: float,
) -> None:
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "voice_milestone": "VOICE-030C",
        "sample_id": sample_id,
        "language": "en",
        "features": {
            "duration_seconds": duration_seconds,
            "speech_burst_count": speech_burst_count,
            "energy_variation": energy_variation,
            "mean_speech_rms": mean_speech_rms,
            "pause_ratio": pause_ratio,
            "average_pause_ms": average_pause_ms,
            "longest_pause_ms": 1200,
            "silence_seconds": duration_seconds * pause_ratio,
        },
        "learning_signal_policy": {
            "long_formulation_pauses": "expected_in_owner_samples_not_agent_target",
            "diagnostic_only_features": [
                "pause_ratio",
                "average_pause_ms",
                "longest_pause_ms",
                "silence_seconds",
            ],
            "runtime_candidate_features": [
                "speech_burst_count",
                "energy_variation",
                "mean_speech_rms",
            ],
            "runtime_use_requires_human_review": True,
        },
        "runtime_learning_candidates": {
            "speech_burst_count": speech_burst_count,
            "energy_variation": energy_variation,
            "mean_speech_rms": mean_speech_rms,
        },
        "privacy_boundary": {
            "provider_calls_made": False,
            "transcription_created": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "public_artifact_created": False,
        },
    }
    (FEATURES_DIR / f"{sample_id}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def create_private_feature_fixtures() -> None:
    write_feature(
        "voice-030d-a",
        duration_seconds=6.0,
        speech_burst_count=8,
        energy_variation=0.21,
        mean_speech_rms=0.19,
        pause_ratio=0.42,
        average_pause_ms=980,
    )
    write_feature(
        "voice-030d-b",
        duration_seconds=9.0,
        speech_burst_count=11,
        energy_variation=0.29,
        mean_speech_rms=0.24,
        pause_ratio=0.51,
        average_pause_ms=1450,
    )


def validate_private_feature_review() -> None:
    assert_condition(RUNNER.exists(), "VOICE-030D runner is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-030D case file is missing.")
    create_private_feature_fixtures()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(PRIVATE_ROOT),
            "--allow-private-read",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    assert_condition(payload["voice_milestone"] == "VOICE-030D", "Unexpected milestone.")
    assert_condition(payload["summary"]["sample_count"] == 2, "Two private feature fixtures should be summarized.")
    assert_condition(payload["summary"]["language_counts"] == {"en": 2}, "Language counts should be aggregate only.")
    assert_condition(payload["summary"]["duration_seconds"]["min"] == 6.0, "Duration min should be context only.")
    assert_condition(payload["summary"]["duration_seconds"]["max"] == 9.0, "Duration max should be context only.")

    candidates = payload["runtime_candidate_summary"]
    assert_condition(candidates["speech_burst_count"]["avg"] == 9.5, "Speech burst count average mismatch.")
    assert_condition(candidates["energy_variation"]["avg"] == 0.25, "Energy variation average mismatch.")
    assert_condition(candidates["mean_speech_rms"]["avg"] == 0.215, "Mean speech RMS average mismatch.")

    diagnostic_only = payload["diagnostic_only_summary"]
    for key in ["pause_ratio", "average_pause_ms", "longest_pause_ms", "silence_seconds"]:
        assert_condition(key in diagnostic_only["excluded_from_runtime_learning"], f"{key} should be excluded.")
        assert_condition(key not in candidates, f"{key} must not appear in runtime candidates.")

    boundary = payload["privacy_boundary"]
    assert_condition(boundary["private_input_read"] is True, "Private features should be read only with opt-in.")
    assert_condition(boundary["provider_calls_made"] is False, "VOICE-030D must not call providers.")
    assert_condition(boundary["transcription_created"] is False, "VOICE-030D must not transcribe.")
    assert_condition(boundary["voice_cloning_used"] is False, "VOICE-030D must not clone voices.")
    assert_condition(boundary["runtime_profile_applied"] is False, "VOICE-030D must not apply runtime settings.")
    assert_condition(boundary["public_artifact_created"] is False, "VOICE-030D must not write public artifacts.")

    assert_condition(SUMMARY_PATH.exists(), "Private JSON review summary was not written.")
    assert_condition(REPORT_PATH.exists(), "Private Markdown review summary was not written.")
    combined = SUMMARY_PATH.read_text(encoding="utf-8") + REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("raw-audio" not in combined, "Review summary must not include raw audio paths.")
    assert_condition("pause_ratio" in combined, "Diagnostic-only policy should be visible for review.")
    generated_dir = ROOT / "research" / "experiments" / "generated" / "VOICE-030D-private-feature-review"
    assert_condition(not generated_dir.exists(), "VOICE-030D must not create public generated artifacts.")


def validate_private_read_guard() -> None:
    completed = run_command([sys.executable, str(RUNNER), "--private-root", str(PRIVATE_ROOT), "--print-json"])
    assert_condition(completed.returncode != 0, "VOICE-030D should require --allow-private-read.")
    combined = completed.stdout + completed.stderr
    assert_condition("--allow-private-read" in combined, "Private-read refusal should explain the required flag.")


def main() -> None:
    validate_private_feature_review()
    validate_private_read_guard()
    print("VOICE-030D private feature review validation passed.")


if __name__ == "__main__":
    main()
