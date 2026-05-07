#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import uuid
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
RUNNER = SCRIPT_DIR / "run_voice_032_local_audio_conversion.py"
MODULE = SCRIPT_DIR / "private_audio_conversion.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-032-local-audio-conversion.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_032_LOCAL_AUDIO_CONVERSION.md"
TMP_DIR = ROOT / ".tmp" / "voice-032-validation"
BASE_PRIVATE_ROOT = ROOT / "data" / "private" / "voice-032-validation" / f"run-{uuid.uuid4().hex}"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def write_fake_ogg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"OggS voice-032 synthetic whatsapp fixture")


def write_fake_converter(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "import math",
                "import struct",
                "import sys",
                "import wave",
                "from pathlib import Path",
                "out = Path(sys.argv[-1])",
                "out.parent.mkdir(parents=True, exist_ok=True)",
                "sample_rate = 16000",
                "frames = []",
                "for index in range(sample_rate // 2):",
                "    value = int(12000 * math.sin(2 * math.pi * 440 * index / sample_rate))",
                "    frames.append(struct.pack('<h', value))",
                "with wave.open(str(out), 'wb') as handle:",
                "    handle.setnchannels(1)",
                "    handle.setsampwidth(2)",
                "    handle.setframerate(sample_rate)",
                "    handle.writeframes(b''.join(frames))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def load_json_output(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got stdout={completed.stdout!r} stderr={completed.stderr!r}") from exc


def fixture_paths(name: str) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    private_root = BASE_PRIVATE_ROOT / name
    whatsapp_dir = private_root / "whatsapp-voice-notes"
    converted_dir = private_root / "converted-audio"
    manifest = private_root / "derived" / "local-audio-conversion-manifest.jsonl"
    report = private_root / "derived" / "local-audio-conversion-report.md"
    queue = private_root / "derived" / "local-speech-learning-queue.jsonl"
    features_dir = private_root / "derived" / "audio-features"
    return private_root, whatsapp_dir, converted_dir, manifest, report, queue, features_dir


def validate_required_files() -> None:
    for path in [RUNNER, MODULE, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-032 file is missing: {path.relative_to(ROOT)}")


def validate_missing_converter_status() -> None:
    private_root, whatsapp_dir, _converted_dir, _manifest, report, _queue, _features_dir = fixture_paths("missing")
    write_fake_ogg(whatsapp_dir / "voice-note-a.ogg")
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--ffmpeg-command",
            "definitely-missing-voice-032-ffmpeg",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_output(completed)
    assert_condition(payload["voice_milestone"] == "VOICE-032", "Unexpected milestone.")
    assert_condition(payload["source_extension_focus"] == ".ogg", "VOICE-032 should be OGG-first.")
    assert_condition(payload["summary"]["converter_missing_count"] == 1, payload["summary"])
    record = payload["records"][0]
    assert_condition(record["source_extension"] == ".ogg", record)
    assert_condition(record["conversion_status"] == "converter_missing_needs_local_ffmpeg", record)
    assert_condition(record["converted_relative_path"] is None, record)
    assert_condition(payload["privacy_boundary"]["provider_calls_made"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["transcription_created"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["voice_cloning_used"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["runtime_profile_applied"] is False, payload["privacy_boundary"])
    assert_condition(report.exists(), "VOICE-032 private report should be written.")
    assert_condition("ffmpeg" in report.read_text(encoding="utf-8").lower(), "Report should explain missing ffmpeg.")


def validate_successful_ogg_conversion_and_queue() -> None:
    private_root, whatsapp_dir, _converted_dir, manifest, _report, queue, features_dir = fixture_paths("success")
    fake_converter = TMP_DIR / "fake_ffmpeg.py"
    write_fake_converter(fake_converter)
    write_fake_ogg(whatsapp_dir / "voice-note-b.ogg")
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--ffmpeg-command",
            sys.executable,
            str(fake_converter),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_output(completed)
    assert_condition(payload["summary"]["converted_count"] == 1, payload["summary"])
    record = payload["records"][0]
    assert_condition(record["conversion_status"] == "converted_and_queued", record)
    assert_condition(record["source_kind"] == "whatsapp_voice_note", record)
    assert_condition(record["converted_relative_path"].endswith(".wav"), record)
    assert_condition(record["learning_queue"]["processing_status"] == "analyzed_needs_review", record)

    converted_path = ROOT / record["converted_relative_path"]
    assert_condition(converted_path.exists(), "Converted WAV file should exist under private data.")
    with wave.open(str(converted_path), "rb") as handle:
        assert_condition(handle.getframerate() == 16000, "Converted WAV should use 16 kHz.")
        assert_condition(handle.getnchannels() == 1, "Converted WAV should be mono.")

    assert_condition(manifest.exists(), "Conversion manifest should exist under private data.")
    assert_condition(queue.exists(), "VOICE-030C queue should receive converted WAV record.")
    assert_condition(any(features_dir.glob("*.json")), "Converted WAV should produce private feature JSON.")
    combined = manifest.read_text(encoding="utf-8") + queue.read_text(encoding="utf-8")
    assert_condition("voice-note-b.ogg" in combined, "Private manifest should retain source filename locally.")
    assert_condition("provider_calls_made" in combined, "Privacy boundary should be recorded.")


def validate_unsupported_extension_deferred() -> None:
    private_root, whatsapp_dir, _converted_dir, _manifest, _report, _queue, _features_dir = fixture_paths("unsupported")
    whatsapp_dir.mkdir(parents=True, exist_ok=True)
    (whatsapp_dir / "unsupported.m4a").write_bytes(b"not the current whatsapp ogg target")
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--include-unsupported",
            "--ffmpeg-command",
            "definitely-missing-voice-032-ffmpeg",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_output(completed)
    assert_condition(payload["summary"]["unsupported_count"] == 1, payload["summary"])
    assert_condition(payload["records"][0]["conversion_status"] == "unsupported_extension_deferred", payload["records"])


def validate_private_boundary_refusals() -> None:
    private_root, _whatsapp_dir, _converted_dir, _manifest, _report, _queue, _features_dir = fixture_paths("boundary")
    outside_input = ROOT / ".tmp" / "voice-032-outside-input"
    outside_input.mkdir(parents=True, exist_ok=True)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--input-dir",
            str(outside_input),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode != 0, "VOICE-032 should refuse input outside data/private.")
    assert_condition("data/private" in (completed.stderr + completed.stdout), "Refusal should mention data/private.")

    outside_output = ROOT / ".tmp" / "voice-032-outside-output"
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--converted-dir",
            str(outside_output),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode != 0, "VOICE-032 should refuse output outside data/private.")
    assert_condition("data/private" in (completed.stderr + completed.stdout), "Refusal should mention data/private.")


def validate_no_public_generated_private_artifact() -> None:
    public_dir = ROOT / "research" / "experiments" / "generated" / "VOICE-032-local-audio-conversion"
    assert_condition(not public_dir.exists(), "VOICE-032 should not create public generated artifacts from private audio.")


def main() -> None:
    validate_required_files()
    validate_missing_converter_status()
    validate_successful_ogg_conversion_and_queue()
    validate_unsupported_extension_deferred()
    validate_private_boundary_refusals()
    validate_no_public_generated_private_artifact()
    print("VOICE-032 local audio conversion validation passed.")


if __name__ == "__main__":
    main()
