#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from raw_audio_speech_features import write_synthetic_wav


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_RUNNER = ROOT / "scripts" / "run_voice_030b_local_speech_capture.py"
QUEUE_MODULE = ROOT / "scripts" / "private_speech_learning_queue.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030c-private-learning-queue.json"
TMP_DIR = ROOT / ".tmp" / "voice-030c-validation"
SOURCE_WAV = TMP_DIR / "source" / "voice-030c-source.wav"
SOURCE_WEBM = TMP_DIR / "source" / "voice-030c-source.webm"
PRIVATE_ROOT = ROOT / "data" / "private" / "voice-030c-validation"
QUEUE_MANIFEST = PRIVATE_ROOT / "derived" / "local-speech-learning-queue.jsonl"
FEATURES_DIR = PRIVATE_ROOT / "derived" / "audio-features"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def create_sources() -> None:
    write_synthetic_wav(
        SOURCE_WAV,
        {
            "sample_rate_hz": 16000,
            "segments": [
                {"kind": "tone", "duration_ms": 480, "frequency_hz": 220, "amplitude": 0.3},
                {"kind": "silence", "duration_ms": 240},
                {"kind": "tone", "duration_ms": 420, "frequency_hz": 260, "amplitude": 0.25},
                {"kind": "silence", "duration_ms": 220},
                {"kind": "tone", "duration_ms": 360, "frequency_hz": 240, "amplitude": 0.25},
            ],
        },
    )
    SOURCE_WEBM.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_WEBM.write_bytes(b"not-real-webm-but-extension-is-enough-for-queue-status")


def read_queue_records() -> list[dict[str, object]]:
    assert_condition(QUEUE_MANIFEST.exists(), "VOICE-030C private queue manifest was not created.")
    return [
        json.loads(line)
        for line in QUEUE_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def record_for(sample_id: str) -> dict[str, object]:
    matches = [record for record in read_queue_records() if record.get("sample_id") == sample_id]
    assert_condition(bool(matches), f"Missing queue record for {sample_id}.")
    return matches[-1]


def validate_wav_import_runs_private_analysis() -> None:
    completed = run_command(
        [
            sys.executable,
            str(CAPTURE_RUNNER),
            "--import-file",
            str(SOURCE_WAV),
            "--sample-id",
            "voice-030c-wav",
            "--language",
            "en",
            "--label",
            "voice 030c wav validation",
            "--private-root",
            str(PRIVATE_ROOT),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    assert_condition(payload["voice_milestone"] == "VOICE-030B", "Capture runner milestone should remain VOICE-030B.")
    queue_payload = payload.get("learning_queue")
    assert_condition(isinstance(queue_payload, dict), "Capture payload should include VOICE-030C learning_queue output.")
    assert_condition(queue_payload["voice_milestone"] == "VOICE-030C", "Queue payload milestone mismatch.")
    assert_condition(queue_payload["processing_status"] == "analyzed_needs_review", "WAV import should be analyzed.")
    assert_condition(queue_payload["privacy_boundary"]["provider_calls_made"] is False, "Queue must not call providers.")
    assert_condition(queue_payload["privacy_boundary"]["transcription_created"] is False, "Queue must not transcribe.")
    assert_condition(queue_payload["privacy_boundary"]["voice_cloning_used"] is False, "Queue must not clone voices.")
    assert_condition(queue_payload["privacy_boundary"]["runtime_profile_applied"] is False, "Queue must not apply runtime.")
    assert_condition(queue_payload["privacy_boundary"]["public_artifact_created"] is False, "Queue must not write public artifacts.")

    record = record_for("voice-030c-wav")
    assert_condition(record["processing_status"] == "analyzed_needs_review", "Queue manifest should record analyzed status.")
    assert_condition(record["speaker_context"]["native_language"] == "tr", "Queue should preserve Turkish-native context.")
    assert_condition(record["speaker_context"]["english_proficiency"] == "high", "Queue should record high English proficiency.")
    assert_condition(
        record["speaker_context"]["pronunciation_learning"] == "use_selectively_for_natural_delivery_not_identity_clone",
        "Queue should learn pronunciation/delivery selectively without identity cloning.",
    )
    assert_condition("timing" in record["speaker_context"]["learn_from"], "Queue should learn timing/rhythm signals.")
    assert_condition(
        "clear_english_delivery_patterns" in record["speaker_context"]["learn_from"],
        "Queue should learn from clear English delivery patterns.",
    )
    assert_condition(
        "do_not_clone_or_overfit_to_one_speaker_identity" in record["speaker_context"]["guardrails"],
        "Queue should guard against voice identity cloning/overfitting.",
    )

    features_path = ROOT / str(record["derived_feature_relative_path"])
    assert_condition(features_path.exists(), "Private derived feature file was not created.")
    assert_condition(features_path.is_relative_to(PRIVATE_ROOT), "Derived feature output must stay under private root.")
    feature_payload = json.loads(features_path.read_text(encoding="utf-8"))
    assert_condition(feature_payload["voice_milestone"] == "VOICE-030C", "Feature payload milestone mismatch.")
    assert_condition(feature_payload["sample_id"] == "voice-030c-wav", "Feature payload sample mismatch.")
    assert_condition(feature_payload["features"]["pause_count"] >= 2, "Feature payload should include WAV pause analysis.")
    signal_policy = feature_payload["learning_signal_policy"]
    assert_condition(
        signal_policy["long_formulation_pauses"] == "expected_in_owner_samples_not_agent_target",
        "Long owner formulation pauses should not become an agent target.",
    )
    for diagnostic_key in ["pause_ratio", "average_pause_ms", "longest_pause_ms", "silence_seconds"]:
        assert_condition(
            diagnostic_key in signal_policy["diagnostic_only_features"],
            f"{diagnostic_key} should be diagnostic-only.",
        )
        assert_condition(
            diagnostic_key not in feature_payload["runtime_learning_candidates"],
            f"{diagnostic_key} must not be a runtime learning candidate.",
        )
    assert_condition(
        "speech_burst_count" in feature_payload["runtime_learning_candidates"],
        "Speech burst count can remain a reviewable rhythm candidate.",
    )
    assert_condition(feature_payload["privacy_boundary"]["runtime_profile_applied"] is False, "Features must not apply runtime.")


def validate_non_wav_import_is_queued_for_conversion() -> None:
    completed = run_command(
        [
            sys.executable,
            str(CAPTURE_RUNNER),
            "--import-file",
            str(SOURCE_WEBM),
            "--sample-id",
            "voice-030c-webm",
            "--language",
            "en",
            "--label",
            "voice 030c webm validation",
            "--private-root",
            str(PRIVATE_ROOT),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    queue_payload = payload.get("learning_queue")
    assert_condition(queue_payload["processing_status"] == "needs_local_conversion", "WebM import should need conversion.")
    assert_condition(queue_payload["derived_feature_relative_path"] is None, "Non-WAV input should not create features.")
    record = record_for("voice-030c-webm")
    assert_condition(record["processing_status"] == "needs_local_conversion", "Queue manifest should record conversion status.")
    assert_condition(record["derived_feature_relative_path"] is None, "Queue record should not point to missing features.")


def validate_no_public_artifacts_or_raw_private_export() -> None:
    assert_condition(QUEUE_MODULE.exists(), "VOICE-030C queue module is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-030C case file is missing.")
    queue_text = QUEUE_MANIFEST.read_text(encoding="utf-8")
    assert_condition("voice-030c-validation/raw-audio" not in queue_text.replace("\\", "/"), "Queue should avoid raw private paths.")
    generated_dir = ROOT / "research" / "experiments" / "generated" / "VOICE-030C-private-learning-queue"
    assert_condition(not generated_dir.exists(), "VOICE-030C should not create public generated artifacts.")


def main() -> None:
    create_sources()
    validate_wav_import_runs_private_analysis()
    validate_non_wav_import_is_queued_for_conversion()
    validate_no_public_artifacts_or_raw_private_export()
    print("VOICE-030C private learning queue validation passed.")


if __name__ == "__main__":
    main()
