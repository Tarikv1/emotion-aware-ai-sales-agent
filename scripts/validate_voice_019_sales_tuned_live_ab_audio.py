#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_019_sales_tuned_live_ab_audio.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-019-sales-tuned-live-ab-audio.json"
TMP_DIR = ROOT / ".tmp" / "voice-019-validation"
TMP_JSON = TMP_DIR / "VOICE-019-sales-tuned-live-ab-audio.json"
TMP_REPORT = TMP_DIR / "VOICE-019-sales-tuned-live-ab-audio-report.md"

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


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(SECRET_VALUES)
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=30)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dry_run_payload(payload: dict) -> None:
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 4, summary)
    assert_condition(summary["languages"]["de"] == 2, summary)
    assert_condition(summary["languages"]["en"] == 2, summary)
    assert_condition(summary["provider_count"] == 2, summary)
    assert_condition(summary["ab_variant_count"] == 16, summary)
    assert_condition(summary["prosody_variant_count"] == 8, summary)
    assert_condition(summary["sales_tuned_variant_count"] == 8, summary)
    assert_condition(summary["live_call_requested"] is False, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["fallback_count"] == 16, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)

    for case in payload["cases"]:
        assert_condition(len(case["ab_results"]) == 4, f"{case['case_id']} should have four A/B provider results.")
        seen = {(result["provider_key"], result["variant_kind"]) for result in case["ab_results"]}
        assert_condition(
            seen == {
                ("cartesia", "prosody"),
                ("cartesia", "sales_tuned"),
                ("elevenlabs", "prosody"),
                ("elevenlabs", "sales_tuned"),
            },
            f"{case['case_id']} missing provider/variant result: {seen}",
        )
        for result in case["ab_results"]:
            assert_condition(result["api_call_made"] is False, result)
            assert_condition(result["audio_file_created"] is False, result)
            assert_condition(result["fallback_used"] is True, result)
            assert_condition(result["fallback_reason"] == "dry-run-mode", result)
            assert_condition(result["api_key_value_logged"] is False, result)
            assert_condition(result["voice_id_value_logged"] is False, result)
            assert_condition(result["customer_audio_uploaded"] is False, result)
            assert_condition(result["voice_clone_used"] is False, result)
            assert_condition(result["generated_text_sent_to_provider"] is False, result)
            assert_condition("<redacted" in json.dumps(result["request_preview"], ensure_ascii=False), result)
            if result["variant_kind"] == "sales_tuned":
                assert_condition(result["source_checkpoint"] == "VOICE-018", result)
                assert_condition(result["sales_tuned_metadata"]["average_speed_ratio"] >= 1.0, result)
                if result["provider_key"] == "cartesia":
                    assert_condition("<speed ratio=" in result["tts_input_text"], result["tts_input_text"])
                if result["provider_key"] == "elevenlabs":
                    assert_condition(result["voice_settings"].get("speed", 1.0) >= 1.0, result)
            else:
                assert_condition(result["source_checkpoint"] == "VOICE-017-style-prosody", result)


def validate_forced_missing_key(provider: str) -> None:
    out_path = TMP_DIR / f"VOICE-019-{provider}-forced-missing.json"
    report_path = TMP_DIR / f"VOICE-019-{provider}-forced-missing-report.md"
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--provider",
            provider,
            "--live",
            "--force-key-missing",
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
    assert_condition(summary["provider_count"] == 1, summary)
    assert_condition(summary["ab_variant_count"] == 8, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["fallback_count"] == 8, summary)
    for case in payload["cases"]:
        for result in case["ab_results"]:
            assert_condition(result["fallback_reason"] == "forced-key-missing", result)
            assert_condition(result["generated_text_sent_to_provider"] is False, result)


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-019 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-019 case file is missing.")
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
    assert_condition(TMP_JSON.exists(), "VOICE-019 validation JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-019 validation report was not created.")

    validate_dry_run_payload(load_json(TMP_JSON))
    first_payload_text = TMP_JSON.read_text(encoding="utf-8")
    completed_again = run_command(
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
    assert_condition(completed_again.returncode == 0, completed_again.stderr)
    assert_condition(first_payload_text == TMP_JSON.read_text(encoding="utf-8"), "VOICE-019 dry-run output should be deterministic.")

    validate_forced_missing_key("elevenlabs")
    validate_forced_missing_key("cartesia")

    combined_output = (
        json.dumps(load_json(TMP_JSON), ensure_ascii=False)
        + TMP_REPORT.read_text(encoding="utf-8")
        + completed.stdout
        + completed.stderr
    )
    for value in SECRET_VALUES.values():
        assert_condition(value not in combined_output, f"Secret test value leaked: {value}")
    match = SECRET_PATTERN.search(combined_output)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-019 output: {match.group(0)!r}")
    print("VOICE-019 sales-tuned live A/B audio validation passed.")


if __name__ == "__main__":
    main()
