#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from raw_audio_speech_features import write_synthetic_wav


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_030b_local_speech_capture.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030b-local-speech-capture.json"
TMP_DIR = ROOT / ".tmp" / "voice-030b-validation"
SOURCE_WAV = TMP_DIR / "source" / "tarik-validation-source.wav"
DEFAULT_PRIVATE_ROOT = ROOT / "data" / "private" / "tarik-speech-samples"
PRIVATE_ROOT = ROOT / "data" / "private" / "voice-030b-validation"
RAW_AUDIO_DIR = PRIVATE_ROOT / "raw-audio"
MANIFEST_PATH = PRIVATE_ROOT / "derived" / "local-speech-capture-manifest.jsonl"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def create_source_wav() -> None:
    write_synthetic_wav(
        SOURCE_WAV,
        {
            "sample_rate_hz": 16000,
            "segments": [
                {"kind": "tone", "duration_ms": 500, "frequency_hz": 220, "amplitude": 0.3},
                {"kind": "silence", "duration_ms": 220},
                {"kind": "tone", "duration_ms": 500, "frequency_hz": 260, "amplitude": 0.25},
            ],
        },
    )


def load_latest_manifest_record() -> dict[str, object]:
    assert_condition(MANIFEST_PATH.exists(), "Private capture manifest was not created.")
    records = [
        json.loads(line)
        for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matching = [record for record in records if record.get("sample_id") == "validation-import"]
    assert_condition(bool(matching), "Validation import record is missing from the private manifest.")
    return matching[-1]


def validate_import_to_private_raw_audio() -> None:
    assert_condition(RUNNER.exists(), "VOICE-030B local speech capture runner is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-030B case file is missing.")
    create_source_wav()

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--import-file",
            str(SOURCE_WAV),
            "--sample-id",
            "validation-import",
            "--language",
            "en",
            "--label",
            "validator synthetic import",
            "--private-root",
            str(PRIVATE_ROOT),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)

    assert_condition(payload["voice_milestone"] == "VOICE-030B", "Unexpected milestone.")
    assert_condition(payload["mode"] == "import_file", "Import mode should be recorded.")
    assert_condition(payload["privacy_boundary"]["provider_calls_made"] is False, "Capture must not call providers.")
    assert_condition(payload["privacy_boundary"]["transcription_created"] is False, "Capture must not transcribe audio.")
    assert_condition(payload["privacy_boundary"]["voice_cloning_used"] is False, "Capture must not clone voices.")
    assert_condition(payload["privacy_boundary"]["runtime_profile_applied"] is False, "Capture must not apply runtime settings.")
    assert_condition(payload["privacy_boundary"]["stored_under_data_private"] is True, "Sample must be stored under data/private.")
    assert_condition(payload["privacy_boundary"]["public_artifact_created"] is False, "Capture must not write public artifacts.")
    assert_condition(payload["sample"]["sample_id"] == "validation-import", "Sample ID should be stable for validation.")
    assert_condition(payload["sample"]["language"] == "en", "Language metadata should be preserved.")
    assert_condition(payload["sample"]["file_extension"] == ".wav", "Imported WAV extension should be preserved.")

    target_relative = str(payload["sample"]["stored_relative_path"])
    assert_condition(
        target_relative.replace("\\", "/").startswith("data/private/voice-030b-validation/raw-audio/"),
        "Stored path should be project-relative under the private raw-audio folder.",
    )
    target_path = ROOT / target_relative
    assert_condition(target_path.exists(), "Imported audio file was not written.")
    assert_condition(target_path.read_bytes() == SOURCE_WAV.read_bytes(), "Imported audio bytes should be copied unchanged.")

    record = load_latest_manifest_record()
    assert_condition(record["sample_id"] == "validation-import", "Manifest sample ID mismatch.")
    assert_condition(record["source_kind"] == "import_file", "Manifest source kind mismatch.")
    assert_condition(record["stored_relative_path"] == target_relative, "Manifest path should match runner output.")


def validate_localhost_dry_run() -> None:
    completed = run_command([sys.executable, str(RUNNER), "--serve", "--dry-run", "--print-json"])
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    assert_condition(payload["voice_milestone"] == "VOICE-030B", "Unexpected dry-run milestone.")
    assert_condition(payload["mode"] == "serve_dry_run", "Dry-run mode should be explicit.")
    assert_condition(payload["server"]["host"] == "127.0.0.1", "Recorder must bind to localhost only.")
    assert_condition(payload["server"]["provider_calls_made"] is False, "Recorder server must not call providers.")
    assert_condition(payload["privacy_boundary"]["stores_uploads_under_data_private"] is True, "Uploads must stay private.")
    assert_condition(payload["privacy_boundary"]["public_artifact_created"] is False, "Dry-run must not write public artifacts.")
    assert_condition(
        payload["sample"]["raw_audio_dir"] == (DEFAULT_PRIVATE_ROOT / "raw-audio").relative_to(ROOT).as_posix(),
        "Default recorder target should be data/private/tarik-speech-samples/raw-audio.",
    )


def validate_browser_recorder_prefers_wav() -> None:
    script_text = RUNNER.read_text(encoding="utf-8")
    assert_condition("function encodeWav" in script_text, "Browser recorder should include a local WAV encoder.")
    assert_condition("audio/wav" in script_text, "Browser recorder should upload WAV audio by default.")
    assert_condition("AudioContext" in script_text, "Browser recorder should use Web Audio for local PCM capture.")
    assert_condition("getChannelData" in script_text, "Browser recorder should extract PCM samples before WAV encoding.")
    assert_condition("new MediaRecorder" not in script_text, "Browser recorder should not default to WebM MediaRecorder capture.")
    assert_condition(
        "audio/webm;codecs=opus" not in script_text,
        "Browser recorder should not prefer WebM/Opus when WAV analysis is the next local step.",
    )


def main() -> None:
    validate_import_to_private_raw_audio()
    validate_localhost_dry_run()
    validate_browser_recorder_prefers_wav()
    print("VOICE-030B local speech capture validation passed.")


if __name__ == "__main__":
    main()
