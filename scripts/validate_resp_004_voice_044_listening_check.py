#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_resp_004_voice_044_listening_check.py"
DOC_PATH = ROOT / "docs" / "product" / "RESP_004_VOICE_044_LISTENING_CHECK.md"
TMP_DIR = ROOT / ".tmp" / "resp-004-voice-044-listening-check-validation"
TMP_JSON = TMP_DIR / "result.json"
TMP_REPORT = TMP_DIR / "report.md"
TMP_AUDIO_DIR = TMP_DIR / "audio"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|ELEVENLABS_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)

SECRET_VALUES = {
    "ELEVENLABS_API_KEY": "TEST_ELEVENLABS_VALUE_MUST_NOT_APPEAR",
    "CARTESIA_API_KEY": "TEST_CARTESIA_VALUE_MUST_NOT_APPEAR",
    "ELEVENLABS_VOICE_ID_DE": "test-eleven-de-voice-id-must-not-appear",
    "ELEVENLABS_VOICE_ID_EN": "test-eleven-en-voice-id-must-not-appear",
    "CARTESIA_VOICE_ID_DE": "test-cartesia-de-voice-id-must-not-appear",
    "CARTESIA_VOICE_ID_EN": "test-cartesia-en-voice-id-must-not-appear",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(SECRET_VALUES)
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=60)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dry_run_payload(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    assert_condition(payload["experiment_id"] == "RESP-004-voice-044-listening-check", payload)
    assert_condition(payload["source_runtime_tts_delivery_id"] == "RESP-003-runtime-live-tts", payload)
    assert_condition(payload["source_voice_milestone"] == "VOICE-044", payload)
    assert_condition(summary["case_count"] == 2, summary)
    assert_condition(summary["english_case_count"] == 1, summary)
    assert_condition(summary["german_case_count"] == 1, summary)
    assert_condition(summary["live_call_requested"] is False, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["fallback_count"] == 2, summary)
    assert_condition(summary["baseline_polish_applied_count"] == 2, summary)
    assert_condition(summary["baseline_polish_validation_passed"] is True, summary)
    assert_condition(summary["private_pattern_profile_applied_count"] == 0, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)
    assert_condition(summary["human_listening_review_recorded"] is False, summary)

    languages = {case["language"] for case in payload["cases"]}
    assert_condition(languages == {"de", "en"}, languages)
    source_case_ids = {case["source_case_id"] for case in payload["cases"]}
    assert_condition(source_case_ids == {"voice-044-en-fast-filler-cleanup", "voice-044-de-connector-cleanup"}, source_case_ids)

    for case in payload["cases"]:
        assert_condition(case["runtime_voice_delivery_id"] == "RESP-002-runtime-voice-delivery", case)
        assert_condition(case["runtime_tts_delivery_id"] == "RESP-003-runtime-live-tts", case)
        assert_condition(case["voice_milestone"] == "VOICE-044", case)
        assert_condition(case["voice_baseline_delivery_polish"]["applied"] is True, case)
        assert_condition(case["voice_baseline_delivery_polish"]["validation"]["passed"] is True, case)
        assert_condition(case["voice_private_pattern_profile"]["applied"] is False, case)
        assert_condition(case["tts_delivery"]["api_call_made"] is False, case)
        assert_condition(case["tts_delivery"]["audio_file_created"] is False, case)
        assert_condition(case["tts_delivery"]["fallback_reason"] == "dry-run-mode", case)
        assert_condition(case["tts_delivery"]["generated_text_sent_to_provider"] is False, case)
        assert_condition(case["tts_delivery"]["customer_audio_uploaded"] is False, case)
        assert_condition(case["tts_delivery"]["voice_cloning_used"] is False, case)
        assert_condition(case["tts_delivery"]["api_key_value_logged"] is False, case)
        assert_condition(case["tts_delivery"]["voice_id_value_logged"] is False, case)
        assert_condition(case["quality_review"]["human_listening_review_required"] is True, case)
        assert_condition(case["quality_review"]["quality_claim_allowed"] is False, case)
        assert_condition("<redacted" in json.dumps(case["tts_delivery"]["request_preview"], ensure_ascii=False), case)
        if case["language"] == "en":
            assert_condition("I'll keep this practical. You're right to ask." in case["tts_delivery"]["tts_input_text"], case)
            assert_condition(", so, you're right to ask" not in case["tts_delivery"]["tts_input_text"], case)
        if case["language"] == "de":
            assert_condition("also wenn's" in case["tts_delivery"]["tts_input_text"], case)
            assert_condition("Also, Wenn's" not in case["tts_delivery"]["tts_input_text"], case)


def validate_forced_missing_key() -> None:
    out_path = TMP_DIR / "forced-missing-result.json"
    report_path = TMP_DIR / "forced-missing-report.md"
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--live",
            "--force-key-missing",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(out_path),
            "--report-out",
            str(report_path),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = load_json(out_path)
    summary = payload["summary"]
    assert_condition(summary["live_call_requested"] is True, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["fallback_count"] == 2, summary)
    for case in payload["cases"]:
        assert_condition(case["tts_delivery"]["fallback_reason"] == "forced-key-missing", case)
        assert_condition(case["tts_delivery"]["generated_text_sent_to_provider"] is False, case)


def main() -> None:
    assert_condition(DOC_PATH.exists(), "RESP-004 product doc is missing.")
    assert_condition(RUNNER.exists(), "RESP-004 listening-check runner is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    assert_condition(TMP_JSON.exists(), "RESP-004 JSON result was not created.")
    assert_condition(TMP_REPORT.exists(), "RESP-004 Markdown report was not created.")

    payload = load_json(TMP_JSON)
    validate_dry_run_payload(payload)
    first_payload_text = TMP_JSON.read_text(encoding="utf-8")
    completed_again = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed_again.returncode == 0, completed_again.stderr)
    assert_condition(first_payload_text == TMP_JSON.read_text(encoding="utf-8"), "Dry-run output should be deterministic.")

    validate_forced_missing_key()
    report_text = TMP_REPORT.read_text(encoding="utf-8")
    combined_output = json.dumps(load_json(TMP_JSON), ensure_ascii=False) + report_text + completed.stdout + completed.stderr
    assert_condition("RESP-004" in report_text, "Report should identify RESP-004.")
    assert_condition("RESP-003 remains the TTS bridge" in report_text, "Report should preserve RESP-003 as the bridge.")
    for value in SECRET_VALUES.values():
        assert_condition(value not in combined_output, f"Secret test value leaked: {value}")
    match = SECRET_PATTERN.search(combined_output)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in RESP-004 output: {match.group(0)!r}")
    print("RESP-004 VOICE-044 listening check validation passed.")


if __name__ == "__main__":
    main()
