#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_012_speech_naturalness.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-012-speech-naturalness.json"
TMP_DIR = ROOT / ".tmp" / "voice-012-validation"
TMP_JSON = TMP_DIR / "VOICE-012-speech-naturalness.json"
TMP_REPORT = TMP_DIR / "VOICE-012-speech-naturalness-report.md"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9])"
)

FILLERS_BY_LANGUAGE = {
    "en": {"um", "uh", "hm", "you know", "like"},
    "de": {"ähm", "äh", "hm", "also"},
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def find_segment(packet: dict, segment_id: str) -> dict:
    for segment in packet["output_segments"]:
        if segment["segment_id"] == segment_id:
            return segment
    raise AssertionError(f"Segment not found in output: {segment_id}")


def validate_result(result: dict) -> None:
    packet = result["speech_naturalness"]
    expected = result["expected"]
    language = result["language"]
    filler_count = packet["filler_count"]

    assert_condition(packet["validation"]["passed"] is True, f"{result['case_id']} failed packet validation.")
    assert_condition(
        expected["min_fillers"] <= filler_count <= expected["max_fillers"],
        f"{result['case_id']} filler count {filler_count} outside expected range {expected}.",
    )

    for protected_segment_id in expected.get("protected_segment_ids_unchanged", []):
        segment = find_segment(packet, protected_segment_id)
        assert_condition(
            segment["text_before"] == segment["text_after"],
            f"{result['case_id']} protected segment changed: {protected_segment_id}",
        )
        assert_condition(
            segment["filler_inserted"] is None,
            f"{result['case_id']} inserted filler into protected segment: {protected_segment_id}",
        )
        assert_condition(
            segment["protected_reason"] is not None,
            f"{result['case_id']} expected protected reason for {protected_segment_id}",
        )

    for segment in packet["output_segments"]:
        if segment["protected_reason"] is not None:
            assert_condition(
                segment["filler_inserted"] is None,
                f"{result['case_id']} inserted filler into protected segment {segment['segment_id']}.",
            )
            assert_condition(
                segment["text_before"] == segment["text_after"],
                f"{result['case_id']} changed protected segment {segment['segment_id']}.",
            )
        if segment["filler_inserted"] is not None:
            assert_condition(
                segment["eligible_for_fillers"] is True,
                f"{result['case_id']} inserted filler into ineligible segment {segment['segment_id']}.",
            )
            assert_condition(
                segment["filler_inserted"] in FILLERS_BY_LANGUAGE[language],
                f"{result['case_id']} used wrong-language filler {segment['filler_inserted']!r}.",
            )


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-012 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-012 case file is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    assert_condition(TMP_JSON.exists(), "VOICE-012 validation JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-012 validation report was not created.")

    payload = json.loads(TMP_JSON.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 8, summary)
    assert_condition(summary["languages"]["de"] == 4, summary)
    assert_condition(summary["languages"]["en"] == 4, summary)
    assert_condition(summary["validation_failed"] == 0, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["requires_api_key"] is False, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)

    for result in payload["results"]:
        validate_result(result)

    c07 = next(result for result in payload["results"] if result["case_id"] == "VOICE-012-C07")
    assert_condition(c07["speech_naturalness"]["profile"]["enabled"] is False, "C07 profile should be disabled.")
    assert_condition(c07["speech_naturalness"]["filler_count"] == 0, "Disabled profile should insert no fillers.")

    output_text = json.dumps(payload, ensure_ascii=False) + TMP_REPORT.read_text(encoding="utf-8") + completed.stdout
    match = SECRET_PATTERN.search(output_text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-012 output: {match.group(0)!r}")
    print("VOICE-012 speech naturalness validation passed.")


if __name__ == "__main__":
    main()
