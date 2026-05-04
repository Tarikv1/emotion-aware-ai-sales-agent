#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_voice_023_speech_realism.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-023-speech-realism.json"
RESULTS_PATH = ROOT / "research" / "experiments" / "generated" / "VOICE-023-speech-realism.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "VOICE-023-speech-realism-report.md"
RUNTIME_PATH = ROOT / "scripts" / "runtime_voice_delivery.py"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def output_by_segment(packet: dict[str, Any], segment_id: str) -> dict[str, Any]:
    for segment in packet["output_segments"]:
        if segment["segment_id"] == segment_id:
            return segment
    raise AssertionError(f"Missing output segment: {segment_id}")


def validate_case(result: dict[str, Any]) -> None:
    packet = result["speech_realism"]
    expected = result["expected"]
    assert_condition(packet["validation"]["passed"] is True, f"{result['case_id']} speech realism validation failed.")
    assert_condition(
        expected["min_bundle_count"] <= packet["bundle_count"] <= expected["max_bundle_count"],
        f"{result['case_id']} bundle count outside expected range.",
    )
    assert_condition(packet["provider_calls_made"] is False, f"{result['case_id']} must not call providers.")
    assert_condition(packet["customer_audio_uploaded"] is False, f"{result['case_id']} must not upload audio.")
    assert_condition(packet["voice_cloning_used"] is False, f"{result['case_id']} must not use voice cloning.")

    bundle_types = {bundle["bundle_type"] for bundle in packet["speech_bundles"]}
    for bundle_type in expected.get("required_bundle_types", []):
        assert_condition(bundle_type in bundle_types, f"{result['case_id']} missing bundle type: {bundle_type}")

    fillers = {bundle.get("filler") for bundle in packet["speech_bundles"] if bundle.get("filler")}
    allowed_fillers = set(expected.get("allowed_fillers", []))
    if allowed_fillers:
        assert_condition(bool(fillers), f"{result['case_id']} expected at least one filler.")
        assert_condition(fillers <= allowed_fillers, f"{result['case_id']} used unexpected filler: {fillers}")

    tts_text_padded = f" {packet['tts_text'].lower()} "
    for forbidden in expected.get("forbidden_fragments", []):
        assert_condition(forbidden.lower() not in tts_text_padded, f"{result['case_id']} contains forbidden fragment: {forbidden}")

    input_by_id = {segment["segment_id"]: segment for segment in packet["input_segments"]}
    for segment_id in expected.get("protected_segment_ids_unchanged", []):
        output_segment = output_by_segment(packet, segment_id)
        assert_condition(
            input_by_id[segment_id]["text"] == output_segment["text_after"],
            f"{result['case_id']} changed protected segment {segment_id}.",
        )
        assert_condition(
            not output_segment["bundles"],
            f"{result['case_id']} added realism bundles to protected segment {segment_id}.",
        )


def main() -> None:
    assert_condition(RUNNER_PATH.exists(), "VOICE-023 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-023 case file is missing.")

    completed = run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(RESULTS_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"VOICE-023 runner failed: {completed.stderr or completed.stdout}")
    assert_condition(RESULTS_PATH.exists(), "VOICE-023 results were not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-023 report was not created.")

    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert_condition(payload["summary"]["case_count"] == 5, "VOICE-023 should cover five cases.")
    assert_condition(payload["summary"]["languages"] == {"de": 3, "en": 2}, "VOICE-023 should cover English and German.")
    assert_condition(payload["summary"]["provider_calls_made"] is False, "VOICE-023 must be offline.")
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, "VOICE-023 must not upload audio.")
    assert_condition(payload["summary"]["voice_cloning_used"] is False, "VOICE-023 must not use voice cloning.")
    assert_condition(payload["summary"]["protected_segment_change_count"] == 0, "VOICE-023 changed protected text.")
    assert_condition(payload["summary"]["validation_failed"] == 0, "VOICE-023 has failed validations.")

    for result in payload["results"]:
        validate_case(result)

    runtime_text = RUNTIME_PATH.read_text(encoding="utf-8")
    assert_condition("apply_speech_realism" in runtime_text, "Runtime voice delivery must call the VOICE-023 speech realism layer.")
    assert_condition('"speech_realism"' in runtime_text, "Runtime voice delivery must expose the speech_realism packet.")

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("protected campaign" in report_text.lower(), "VOICE-023 report should document protected text boundary.")
    assert_condition("provider calls made: `false`" in report_text.lower(), "VOICE-023 report should document offline provider boundary.")

    print("VOICE-023 speech realism validation passed.")


if __name__ == "__main__":
    main()
