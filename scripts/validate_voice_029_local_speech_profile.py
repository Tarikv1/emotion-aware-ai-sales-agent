#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_029_local_speech_profile.py"
INIT_RUNNER = ROOT / "scripts" / "init_personal_speech_learning_workspace.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-029-local-speech-profile-learning.json"
TMP_DIR = ROOT / ".tmp" / "voice-029-validation"
RESULT_PATH = TMP_DIR / "results.json"
REPORT_PATH = TMP_DIR / "report.md"

RAW_FIXTURE_FRAGMENTS = [
    "Example Person",
    "5550100",
    "this private detail should never appear",
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def load_payload() -> dict:
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def validate_synthetic_profile() -> None:
    assert_condition(RUNNER.exists(), "VOICE-029 runner is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-029 case file is missing.")
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
    assert_condition(RESULT_PATH.exists(), "VOICE-029 result JSON was not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-029 report was not created.")

    payload = load_payload()
    assert_condition(payload["voice_milestone"] == "VOICE-029", "Unexpected voice milestone.")
    assert_condition(payload["source_mode"] == "synthetic_fixture", "Default run should use synthetic fixtures.")
    assert_condition(payload["privacy_boundary"]["private_input_read"] is False, "Synthetic run must not read private input.")
    assert_condition(payload["privacy_boundary"]["raw_audio_read"] is False, "VOICE-029 must not read raw audio.")
    assert_condition(payload["privacy_boundary"]["provider_calls_made"] is False, "VOICE-029 must not call providers.")
    assert_condition(payload["privacy_boundary"]["voice_cloning_used"] is False, "VOICE-029 must not clone voices.")
    assert_condition(payload["privacy_boundary"]["raw_transcript_exported"] is False, "VOICE-029 must not export raw transcripts.")
    assert_condition(payload["privacy_boundary"]["human_review_required_before_runtime_use"] is True, "Runtime use must require review.")
    assert_condition(payload["summary"]["sample_count"] == 4, "Synthetic fixture should include four samples.")
    assert_condition(payload["summary"]["languages"] == {"de": 1, "en": 3}, "Expected English/German sample counts.")
    assert_condition(payload["summary"]["safe_public_artifact"] is True, "Synthetic output should be safe as public artifact.")

    english = payload["pattern_profile"]["languages"]["en"]
    german = payload["pattern_profile"]["languages"]["de"]
    assert_condition(english["filler_marker_count"] >= 2, "English fixture should detect filler markers.")
    assert_condition(english["repair_marker_count"] >= 2, "English fixture should detect repair/rephrase markers.")
    assert_condition(english["contraction_count"] >= 2, "English fixture should detect contractions.")
    assert_condition(german["filler_marker_count"] >= 1, "German fixture should detect German discourse markers.")
    assert_condition(payload["runtime_profile_proposal"]["apply_to_runtime_by_default"] is False, "Profile must not auto-apply.")
    assert_condition(payload["runtime_profile_proposal"]["requires_human_review"] is True, "Profile proposal must require review.")

    combined = RESULT_PATH.read_text(encoding="utf-8") + REPORT_PATH.read_text(encoding="utf-8")
    for fragment in RAW_FIXTURE_FRAGMENTS:
        assert_condition(fragment not in combined, f"Raw/private fixture fragment leaked into output: {fragment}")


def validate_private_guard() -> None:
    private_input = ROOT / "data" / "private" / "tarik-speech-samples" / "transcripts-redacted"
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
    assert_condition(completed.returncode != 0, "Private input should require explicit --allow-private-read.")
    assert_condition("--allow-private-read" in (completed.stderr + completed.stdout), "Missing private-read guidance.")


def validate_workspace_initializer() -> None:
    assert_condition(INIT_RUNNER.exists(), "VOICE-029 private workspace initializer is missing.")
    completed = run_command([sys.executable, str(INIT_RUNNER), "--dry-run"])
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    output = completed.stdout
    assert_condition("tarik-speech-samples" in output, "Initializer should point to Tarik speech sample workspace.")
    assert_condition("Raw/private contents read: false" in output, "Initializer must not read private contents.")
    assert_condition("raw-audio" in output and "transcripts-redacted" in output, "Initializer should list required folders.")


def main() -> None:
    validate_synthetic_profile()
    validate_private_guard()
    validate_workspace_initializer()
    print("VOICE-029 local speech profile validation passed.")


if __name__ == "__main__":
    main()
