#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_voice_010_cartesia_tts_smoke.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-010-cartesia-tts-smoke.json"
OUT_JSON = ROOT / "research" / "experiments" / "generated" / "VOICE-010-cartesia-tts-smoke.json"
REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-010-cartesia-tts-smoke-report.md"


SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def safe_env() -> dict:
    env = os.environ.copy()
    env.pop("CARTESIA_API_KEY", None)
    env.pop("CARTESIA_VOICE_ID", None)
    return env


def run_smoke(*extra_args: str) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(OUT_JSON),
            "--report-out",
            str(REPORT_OUT),
            *extra_args,
        ],
        cwd=ROOT,
        env=safe_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def validate_payload(payload: dict, *, live_requested: bool) -> None:
    assert_condition(payload["voice_milestone"] == "VOICE-010", "Unexpected milestone.")
    assert_condition(payload["provider"]["provider_id"] == "cartesia-sonic-3", "VOICE-010 must target Cartesia Sonic 3.")
    assert_condition(payload["provider"]["endpoint_type"] == "tts-bytes", "VOICE-010 should use the guarded bytes endpoint first.")
    assert_condition(payload["provider"]["api_key_env_var"] == "CARTESIA_API_KEY", "Cartesia key must be environment-only.")
    assert_condition(payload["provider"]["voice_id_env_var"] == "CARTESIA_VOICE_ID", "Cartesia voice ID must be environment-only.")
    assert_condition(payload["provider"]["api_key_value_logged"] is False, "API key value must never be logged.")
    assert_condition(payload["provider"]["voice_id_value_logged"] is False, "Voice ID value should not be logged.")
    assert_condition(payload["summary"]["case_count"] == 2, "Expected one German and one English Cartesia case.")
    assert_condition(payload["summary"]["languages"] == {"de": 1, "en": 1}, "Expected German and English coverage.")
    assert_condition(payload["summary"]["live_call_requested"] is live_requested, "Unexpected live-call mode.")
    assert_condition(payload["summary"]["api_calls_made"] == 0, "Validator must not make provider API calls.")
    assert_condition(payload["summary"]["audio_files_created"] == 0, "No-key validation should not create audio.")
    assert_condition(payload["summary"]["fallback_count"] == 2, "No-key validation should fall back for both cases.")
    assert_condition(payload["summary"]["response_language_matches"] == 2, "Both responses should preserve language.")
    assert_condition(payload["summary"]["tts_text_matches_decision"] == 2, "TTS text must match agent response.")
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, "VOICE-010 must not upload customer audio.")
    assert_condition(payload["summary"]["synthetic_prompts_only"] is True, "VOICE-010 must use synthetic prompts only.")
    assert_condition(payload["summary"]["timeout_seconds"] <= 10, "Timeout should stay bounded for smoke tests.")

    for case in payload["cases"]:
        cartesia = case["cartesia_tts"]
        packet = case["voice_packet"]
        assert_condition(packet["tts_text"] == packet["decision"]["agent_response"], f"{case['case_id']} TTS text mismatch.")
        assert_condition(packet["campaign"]["language"] == case["language"], f"{case['case_id']} campaign language mismatch.")
        assert_condition(packet["decision"]["response_language"] == case["language"], f"{case['case_id']} response language mismatch.")
        assert_condition(cartesia["provider_id"] == "cartesia-sonic-3", f"{case['case_id']} provider mismatch.")
        assert_condition(cartesia["model_id"] == "sonic-3", f"{case['case_id']} model mismatch.")
        assert_condition(cartesia["language"] == case["language"], f"{case['case_id']} language mismatch.")
        assert_condition(cartesia["api_call_made"] is False, f"{case['case_id']} should not call Cartesia during validation.")
        assert_condition(cartesia["audio_file_created"] is False, f"{case['case_id']} should not create audio during validation.")
        assert_condition(cartesia["fallback_used"] is True, f"{case['case_id']} should use fallback.")
        assert_condition(cartesia["fallback_provider"] == "text-only-tts-packet", f"{case['case_id']} fallback mismatch.")
        assert_condition(cartesia["api_key_value_logged"] is False, f"{case['case_id']} API key value should not be logged.")
        assert_condition(cartesia["voice_id_value_logged"] is False, f"{case['case_id']} voice ID value should not be logged.")
        assert_condition(cartesia["customer_audio_uploaded"] is False, f"{case['case_id']} should not upload customer audio.")
        assert_condition(cartesia["generated_text_sent_to_provider"] is False, f"{case['case_id']} should not send text in validation.")
        assert_condition(cartesia["timeout_seconds"] <= 10, f"{case['case_id']} timeout too high.")
        assert_condition(cartesia["request_preview"]["headers"]["Authorization"] == "Bearer <redacted>", f"{case['case_id']} auth preview not redacted.")
        assert_condition(cartesia["request_preview"]["body"]["voice"]["id"] == "<redacted-env:CARTESIA_VOICE_ID>", f"{case['case_id']} voice preview not redacted.")
        if live_requested:
            assert_condition(
                cartesia["fallback_reason"] in {"missing-cartesia-api-key", "missing-cartesia-voice-id", "forced-key-missing"},
                f"{case['case_id']} should explain live fallback.",
            )
        else:
            assert_condition(cartesia["fallback_reason"] == "dry-run-mode", f"{case['case_id']} should stay dry-run.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "VOICE-010 Cartesia smoke script is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-010 Cartesia case file is missing.")

    live_missing_key_payload = run_smoke("--live", "--force-key-missing")
    validate_payload(live_missing_key_payload, live_requested=True)

    dry_run_payload = run_smoke()
    validate_payload(dry_run_payload, live_requested=False)
    assert_condition(dry_run_payload == json.loads(OUT_JSON.read_text(encoding="utf-8")), "Stdout and JSON artifact should match.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-010 report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No API calls were made" in report_text, "Report should state no API calls for validation mode.")
    assert_condition("No customer audio was uploaded" in report_text, "Report should state no customer audio upload.")
    assert_condition("CARTESIA_API_KEY" in report_text, "Report should document key env var.")
    assert_condition("CARTESIA_VOICE_ID" in report_text, "Report should document voice env var.")
    assert_condition("German cases: `1`" in report_text, "Report should include German count.")
    assert_condition("English cases: `1`" in report_text, "Report should include English count.")
    assert_condition("text-only-tts-packet" in report_text, "Report should document fallback.")
    assert_condition("timeout" in report_text.lower(), "Report should document timeout guardrails.")

    serialized = json.dumps(dry_run_payload) + json.dumps(live_missing_key_payload) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-010 Cartesia TTS smoke validation passed.")


if __name__ == "__main__":
    main()
