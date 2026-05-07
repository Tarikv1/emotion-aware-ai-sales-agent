#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_voice_013_elevenlabs_tts_smoke.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-013-elevenlabs-tts-smoke.json"
OUT_JSON = ROOT / ".tmp" / "VOICE-013-elevenlabs-tts-smoke-validation.json"
REPORT_OUT = ROOT / ".tmp" / "VOICE-013-elevenlabs-tts-smoke-validation-report.md"


SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|CARTESIA_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9]|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def safe_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in [
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID",
        "ELEVENLABS_VOICE_ID_DE",
        "ELEVENLABS_VOICE_ID_EN",
    ]:
        env.pop(key, None)
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
    assert_condition(payload["voice_milestone"] == "VOICE-013", "Unexpected milestone.")
    assert_condition(payload["provider"]["provider_id"] == "elevenlabs-stream", "VOICE-013 must target ElevenLabs.")
    assert_condition(payload["provider"]["endpoint_type"] == "tts-http-stream", "VOICE-013 should use HTTP streaming.")
    assert_condition(payload["provider"]["api_key_env_var"] == "ELEVENLABS_API_KEY", "ElevenLabs key must be environment-only.")
    assert_condition(
        payload["provider"]["language_voice_id_env_vars"] == {
            "de": "ELEVENLABS_VOICE_ID_DE",
            "en": "ELEVENLABS_VOICE_ID_EN",
        },
        "VOICE-013 should support language-specific voice IDs.",
    )
    assert_condition(payload["provider"]["default_voice_id_env_var"] == "ELEVENLABS_VOICE_ID", "Default voice ID env mismatch.")
    assert_condition(payload["provider"]["api_key_value_logged"] is False, "API key value must never be logged.")
    assert_condition(payload["provider"]["voice_id_value_logged"] is False, "Voice ID value should not be logged.")
    assert_condition(payload["provider"]["enable_logging"] is False, "VOICE-013 should request provider logging disabled.")
    assert_condition(payload["summary"]["case_count"] == 4, "Expected two German and two English ElevenLabs cases.")
    assert_condition(payload["summary"]["languages"] == {"de": 2, "en": 2}, "Expected German and English coverage.")
    assert_condition(payload["summary"]["live_call_requested"] is live_requested, "Unexpected live-call mode.")
    assert_condition(payload["summary"]["api_calls_made"] == 0, "Validator must not make provider API calls.")
    assert_condition(payload["summary"]["audio_files_created"] == 0, "No-key validation should not create audio.")
    assert_condition(payload["summary"]["fallback_count"] == 4, "No-key validation should fall back for all cases.")
    assert_condition(payload["summary"]["response_language_matches"] == 4, "Responses should preserve language.")
    assert_condition(payload["summary"]["quality_script_languages_match"] == 4, "Quality scripts should preserve language.")
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, "VOICE-013 must not upload customer audio.")
    assert_condition(payload["summary"]["synthetic_prompts_only"] is True, "VOICE-013 must use synthetic prompts only.")
    assert_condition(payload["summary"]["timeout_seconds"] <= 10, "Timeout should stay bounded for smoke tests.")

    for case in payload["cases"]:
        elevenlabs = case["elevenlabs_tts"]
        packet = case["voice_packet"]
        expected_env = "ELEVENLABS_VOICE_ID_DE" if case["language"] == "de" else "ELEVENLABS_VOICE_ID_EN"
        expected_local_source = f"local_voice_ids:elevenlabs.{case['language']}"
        selected_voice_source = elevenlabs["selected_voice_id_env_var"]
        allowed_voice_sources = {expected_env, expected_local_source}
        assert_condition(packet["campaign"]["language"] == case["language"], f"{case['case_id']} campaign language mismatch.")
        assert_condition(packet["decision"]["response_language"] == case["language"], f"{case['case_id']} response language mismatch.")
        assert_condition(elevenlabs["provider_id"] == "elevenlabs-stream", f"{case['case_id']} provider mismatch.")
        assert_condition(elevenlabs["model_id"] == "eleven_flash_v2_5", f"{case['case_id']} model mismatch.")
        assert_condition(elevenlabs["language"] == case["language"], f"{case['case_id']} language mismatch.")
        assert_condition(selected_voice_source in allowed_voice_sources, f"{case['case_id']} voice source mismatch.")
        assert_condition(elevenlabs["api_call_made"] is False, f"{case['case_id']} should not call ElevenLabs during validation.")
        assert_condition(elevenlabs["audio_file_created"] is False, f"{case['case_id']} should not create audio during validation.")
        assert_condition(elevenlabs["fallback_used"] is True, f"{case['case_id']} should use fallback.")
        assert_condition(elevenlabs["fallback_provider"] == "text-only-tts-packet", f"{case['case_id']} fallback mismatch.")
        assert_condition(elevenlabs["api_key_value_logged"] is False, f"{case['case_id']} API key value should not be logged.")
        assert_condition(elevenlabs["voice_id_value_logged"] is False, f"{case['case_id']} voice ID value should not be logged.")
        assert_condition(elevenlabs["customer_audio_uploaded"] is False, f"{case['case_id']} should not upload customer audio.")
        assert_condition(elevenlabs["generated_text_sent_to_provider"] is False, f"{case['case_id']} should not send text in validation.")
        assert_condition(elevenlabs["timeout_seconds"] <= 10, f"{case['case_id']} timeout too high.")
        assert_condition(elevenlabs["request_preview"]["headers"]["xi-api-key"] == "<redacted>", f"{case['case_id']} key preview not redacted.")
        assert_condition(
            f"<redacted-env:{selected_voice_source}>" in elevenlabs["request_preview"]["url"],
            f"{case['case_id']} voice URL preview not redacted.",
        )
        assert_condition(elevenlabs["request_preview"]["body"]["text"] == case["tts_quality_script"], f"{case['case_id']} text mismatch.")
        if live_requested:
            assert_condition(
                elevenlabs["fallback_reason"] in {
                    "missing-elevenlabs-api-key",
                    "missing-elevenlabs-voice-id",
                    "forced-key-missing",
                },
                f"{case['case_id']} should explain live fallback.",
            )
        else:
            assert_condition(elevenlabs["fallback_reason"] == "dry-run-mode", f"{case['case_id']} should stay dry-run.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "VOICE-013 ElevenLabs smoke script is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-013 ElevenLabs case file is missing.")

    live_missing_key_payload = run_smoke("--live", "--force-key-missing")
    validate_payload(live_missing_key_payload, live_requested=True)

    dry_run_payload = run_smoke()
    validate_payload(dry_run_payload, live_requested=False)
    assert_condition(dry_run_payload == json.loads(OUT_JSON.read_text(encoding="utf-8")), "Stdout and JSON artifact should match.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-013 report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No API calls were made" in report_text, "Report should state no API calls for validation mode.")
    assert_condition("No customer audio was uploaded" in report_text, "Report should state no customer audio upload.")
    assert_condition("ELEVENLABS_API_KEY" in report_text, "Report should document key env var.")
    assert_condition("ELEVENLABS_VOICE_ID_DE" in report_text, "Report should document German voice env var.")
    assert_condition("ELEVENLABS_VOICE_ID_EN" in report_text, "Report should document English voice env var.")
    assert_condition("German cases: `2`" in report_text, "Report should include German count.")
    assert_condition("English cases: `2`" in report_text, "Report should include English count.")
    assert_condition("text-only-tts-packet" in report_text, "Report should document fallback.")
    assert_condition("timeout" in report_text.lower(), "Report should document timeout guardrails.")

    serialized = json.dumps(dry_run_payload) + json.dumps(live_missing_key_payload) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-013 ElevenLabs TTS smoke validation passed.")


if __name__ == "__main__":
    main()
