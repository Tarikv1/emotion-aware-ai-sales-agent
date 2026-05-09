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
RUNNER = ROOT / "scripts" / "run_voice_042_private_pattern_live_ab.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-042-private-pattern-live-ab.json"
TMP_DIR = ROOT / ".tmp" / "voice-042-private-pattern-live-ab-validation"
TMP_JSON = TMP_DIR / "result.json"
TMP_REPORT = TMP_DIR / "report.md"
TMP_AUDIO_DIR = TMP_DIR / "audio"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)

SECRET_VALUES = {
    "ELEVENLABS_API_KEY": "TEST_ELEVENLABS_VALUE_MUST_NOT_APPEAR",
    "ELEVENLABS_VOICE_ID_EN": "test-eleven-en-voice-id-must-not-appear",
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


def assert_no_secrets(text: str) -> None:
    for value in SECRET_VALUES.values():
        assert_condition(value not in text, f"Secret test value leaked: {value}")
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-042 output: {match.group(0)!r}")


def validate_payload(payload: dict[str, Any], *, live_requested: bool, fallback_reason: str) -> None:
    summary = payload["summary"]
    assert_condition(payload["experiment_id"] == "VOICE-042-private-pattern-live-ab", payload)
    assert_condition(summary["case_count"] == 1, summary)
    assert_condition(summary["ab_variant_count"] == 2, summary)
    assert_condition(summary["baseline_variant_count"] == 1, summary)
    assert_condition(summary["profiled_variant_count"] == 1, summary)
    assert_condition(summary["live_call_requested"] is live_requested, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["raw_audio_read"] is False, summary)
    assert_condition(summary["transcription_created"] is False, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)
    assert_condition(summary["human_listening_review_recorded"] is False, summary)
    assert_condition(summary["provider_count"] == 1, summary)
    assert_condition(summary["providers"] == ["elevenlabs"], summary)

    case = payload["cases"][0]
    assert_condition(case["language"] == "en", case)
    assert_condition(len(case["ab_results"]) == 2, case)
    variants = {result["variant_kind"]: result for result in case["ab_results"]}
    assert_condition(set(variants) == {"baseline_shaped_runtime", "private_pattern_profile"}, variants)
    baseline = variants["baseline_shaped_runtime"]
    profiled = variants["private_pattern_profile"]

    assert_condition(baseline["voice_private_pattern_profile"]["applied"] is False, baseline)
    assert_condition(profiled["voice_private_pattern_profile"]["applied"] is True, profiled)
    assert_condition(baseline["final_response"] == case["final_response"], baseline)
    assert_condition(profiled["final_response"] == case["final_response"], profiled)
    assert_condition(baseline["tts_input_text"] == profiled["tts_input_text"], case)
    assert_condition(baseline["voice_settings"]["style"] == 0.0, baseline["voice_settings"])
    assert_condition(profiled["voice_settings"]["style"] == 0.06, profiled["voice_settings"])
    assert_condition(profiled["voice_settings"]["stability"] < baseline["voice_settings"]["stability"], (baseline, profiled))
    assert_condition(profiled["generated_text_sent_to_provider"] is False, profiled)

    for result in case["ab_results"]:
        assert_condition(result["provider_key"] == "elevenlabs", result)
        assert_condition(result["customer_audio_uploaded"] is False, result)
        assert_condition(result["voice_cloning_used"] is False, result)
        assert_condition(result["api_key_value_logged"] is False, result)
        assert_condition(result["voice_id_value_logged"] is False, result)
        assert_condition(result["synthetic_prompt_only"] is True, result)
        assert_condition(result["fallback_reason"] == fallback_reason, result)
        assert_condition("<redacted" in json.dumps(result["request_preview"], ensure_ascii=False), result)


def validate_dry_run() -> None:
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
    assert_condition(TMP_JSON.exists(), "VOICE-042 JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-042 report was not created.")
    payload = load_json(TMP_JSON)
    validate_payload(payload, live_requested=False, fallback_reason="dry-run-mode")
    assert_no_secrets(TMP_JSON.read_text(encoding="utf-8") + TMP_REPORT.read_text(encoding="utf-8") + completed.stdout + completed.stderr)


def validate_live_limit_guard() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--live",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(TMP_DIR / "unguarded-live.json"),
            "--report-out",
            str(TMP_DIR / "unguarded-live.md"),
        ]
    )
    assert_condition(completed.returncode != 0, "VOICE-042 live mode should require --limit-cases.")
    assert_condition("--live requires --limit-cases" in (completed.stdout + completed.stderr), completed)


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
            "--limit-cases",
            "1",
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
    validate_payload(payload, live_requested=True, fallback_reason="forced-key-missing")
    assert_condition(payload["summary"]["api_calls_made"] == 0, payload["summary"])
    assert_condition(payload["summary"]["audio_files_created"] == 0, payload["summary"])
    assert_condition(payload["summary"]["fallback_count"] == 2, payload["summary"])
    assert_no_secrets(out_path.read_text(encoding="utf-8") + report_path.read_text(encoding="utf-8") + completed.stdout + completed.stderr)


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-042 runner is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-042 case file is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    validate_dry_run()
    validate_live_limit_guard()
    validate_forced_missing_key()
    print("VOICE-042 private pattern live A/B validation passed.")


if __name__ == "__main__":
    main()
