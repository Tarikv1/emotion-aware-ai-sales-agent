#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
RUNNER = SCRIPT_DIR / "run_voice_033_private_sample_readiness.py"
MODULE = SCRIPT_DIR / "private_sample_readiness.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-033-private-sample-readiness.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_033_PRIVATE_SAMPLE_READINESS.md"
BASE_PRIVATE_ROOT = ROOT / "data" / "private" / "voice-033-validation" / f"run-{uuid.uuid4().hex}"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def touch_audio(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"voice-033 metadata-only fixture")


def create_fixture(
    name: str,
    *,
    analyzed_count: int,
    whatsapp_ogg_count: int = 0,
    raw_webm_count: int = 0,
    analysis_failed_count: int = 0,
    conversion_failed_count: int = 0,
) -> Path:
    private_root = BASE_PRIVATE_ROOT / name
    raw_dir = private_root / "raw-audio"
    converted_dir = private_root / "converted-audio"
    whatsapp_dir = private_root / "whatsapp-voice-notes"
    features_dir = private_root / "derived" / "audio-features"
    queue_path = private_root / "derived" / "local-speech-learning-queue.jsonl"
    conversion_manifest = private_root / "derived" / "local-audio-conversion-manifest.jsonl"

    for index in range(analyzed_count):
        touch_audio(converted_dir / f"ready-{index:03}.wav")
        write_json(
            features_dir / f"ready-{index:03}.json",
            {
                "voice_milestone": "VOICE-030C",
                "sample_id": f"ready-{index:03}",
                "language": "en" if index % 2 == 0 else "de",
                "source_kind": "whatsapp_voice_note_converted" if index % 3 == 0 else "localhost_browser_recorder",
            },
        )
        append_jsonl(
            queue_path,
            {
                "voice_milestone": "VOICE-030C",
                "sample_id": f"ready-{index:03}",
                "language": "en" if index % 2 == 0 else "de",
                "source_kind": "whatsapp_voice_note_converted" if index % 3 == 0 else "localhost_browser_recorder",
                "source_file_extension": ".wav",
                "processing_status": "analyzed_needs_review",
                "derived_feature_relative_path": f"data/private/voice-033-validation/{name}/derived/audio-features/ready-{index:03}.json",
            },
        )

    for index in range(whatsapp_ogg_count):
        touch_audio(whatsapp_dir / f"whatsapp-{index:03}.ogg")

    for index in range(raw_webm_count):
        touch_audio(raw_dir / f"legacy-{index:03}.webm")
        append_jsonl(
            queue_path,
            {
                "voice_milestone": "VOICE-030C",
                "sample_id": f"legacy-{index:03}",
                "language": "unknown",
                "source_kind": "localhost_browser_recorder",
                "source_file_extension": ".webm",
                "processing_status": "needs_local_conversion",
            },
        )

    for index in range(analysis_failed_count):
        touch_audio(raw_dir / f"failed-{index:03}.wav")
        append_jsonl(
            queue_path,
            {
                "voice_milestone": "VOICE-030C",
                "sample_id": f"failed-{index:03}",
                "language": "en",
                "source_kind": "import_file",
                "source_file_extension": ".wav",
                "processing_status": "analysis_failed_needs_review",
            },
        )

    for index in range(conversion_failed_count):
        append_jsonl(
            conversion_manifest,
            {
                "voice_milestone": "VOICE-032",
                "source_kind": "whatsapp_voice_note",
                "source_extension": ".ogg",
                "conversion_status": "conversion_failed_needs_review",
            },
        )

    return private_root


def load_json_stdout(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got stdout={completed.stdout!r} stderr={completed.stderr!r}") from exc


def validate_required_files() -> None:
    for path in [RUNNER, MODULE, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-033 file is missing: {path.relative_to(ROOT)}")


def validate_private_read_guard() -> None:
    private_root = create_fixture("guard", analyzed_count=1)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode != 0, "VOICE-033 should require --allow-private-metadata-read.")
    assert_condition(
        "--allow-private-metadata-read" in (completed.stderr + completed.stdout),
        "Private metadata refusal should explain the required flag.",
    )


def validate_not_enough_samples_status() -> None:
    private_root = create_fixture(
        "not-enough",
        analyzed_count=4,
        whatsapp_ogg_count=2,
        raw_webm_count=1,
        analysis_failed_count=1,
        conversion_failed_count=1,
    )
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--allow-private-metadata-read",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_stdout(completed)
    assert_condition(payload["voice_milestone"] == "VOICE-033", "Unexpected milestone.")
    assert_condition(payload["readiness_status"] == "not_enough_samples_yet", payload)
    assert_condition(payload["sample_inventory"]["analyzed_feature_files"] == 4, payload["sample_inventory"])
    assert_condition(payload["sample_inventory"]["whatsapp_ogg_waiting_conversion"] == 2, payload["sample_inventory"])
    assert_condition(payload["sample_inventory"]["other_non_wav_needing_conversion"] == 1, payload["sample_inventory"])
    assert_condition(payload["sample_inventory"]["analysis_failed_needs_review"] == 1, payload["sample_inventory"])
    assert_condition(payload["sample_inventory"]["conversion_failed_needs_review"] == 1, payload["sample_inventory"])
    assert_condition(payload["thresholds"]["first_review_min_analyzed_samples"] == 10, payload["thresholds"])
    assert_condition(payload["thresholds"]["stronger_pattern_review_min_analyzed_samples"] == 100, payload["thresholds"])
    assert_condition(payload["next_action"]["recommended_action"] == "collect_more_wav_samples", payload["next_action"])
    assert_condition(any("ffmpeg" in item.lower() for item in payload["recommendations"]), payload["recommendations"])
    assert_condition(payload["privacy_boundary"]["raw_audio_content_read"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["provider_calls_made"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["transcription_created"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["voice_cloning_used"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["runtime_profile_applied"] is False, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["public_artifact_created"] is False, payload["privacy_boundary"])

    report_path = private_root / "derived" / "readiness" / "voice-033-private-sample-readiness.md"
    result_path = private_root / "derived" / "readiness" / "voice-033-private-sample-readiness.json"
    assert_condition(report_path.exists(), "Private readiness report should be written.")
    assert_condition(result_path.exists(), "Private readiness JSON should be written.")
    report = report_path.read_text(encoding="utf-8")
    assert_condition("not_enough_samples_yet" in report, "Report should include readiness status.")


def validate_enough_for_first_review_status() -> None:
    private_root = create_fixture("first-review", analyzed_count=12)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--allow-private-metadata-read",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_stdout(completed)
    assert_condition(payload["readiness_status"] == "enough_for_first_review", payload)
    assert_condition(payload["next_action"]["recommended_action"] == "run_voice_030d_private_feature_review", payload["next_action"])
    assert_condition(payload["language_counts"] == {"de": 6, "en": 6}, payload["language_counts"])
    assert_condition(payload["source_counts"]["whatsapp_voice_note_converted"] == 4, payload["source_counts"])


def validate_enough_for_stronger_review_status() -> None:
    private_root = create_fixture("strong-review", analyzed_count=100)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(private_root),
            "--allow-private-metadata-read",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = load_json_stdout(completed)
    assert_condition(payload["readiness_status"] == "enough_for_stronger_pattern_review", payload)
    assert_condition(payload["next_action"]["recommended_action"] == "run_voice_030d_private_feature_review", payload["next_action"])


def validate_private_boundary_refusals() -> None:
    outside_root = ROOT / ".tmp" / "voice-033-outside-root"
    outside_root.mkdir(parents=True, exist_ok=True)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--private-root",
            str(outside_root),
            "--allow-private-metadata-read",
            "--print-json",
        ]
    )
    assert_condition(completed.returncode != 0, "VOICE-033 should refuse private roots outside data/private.")
    assert_condition("data/private" in (completed.stderr + completed.stdout), "Refusal should mention data/private.")


def validate_no_raw_audio_reads_in_module() -> None:
    module_text = MODULE.read_text(encoding="utf-8")
    forbidden_fragments = [".read_bytes(", "wave.open(", "AudioSegment", "subprocess.run("]
    for fragment in forbidden_fragments:
        assert_condition(fragment not in module_text, f"Readiness module should not inspect/convert audio content: {fragment}")


def main() -> None:
    validate_required_files()
    validate_private_read_guard()
    validate_not_enough_samples_status()
    validate_enough_for_first_review_status()
    validate_enough_for_stronger_review_status()
    validate_private_boundary_refusals()
    validate_no_raw_audio_reads_in_module()
    print("VOICE-033 private sample readiness validation passed.")


if __name__ == "__main__":
    main()
