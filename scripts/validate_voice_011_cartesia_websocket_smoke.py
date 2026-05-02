#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_voice_011_cartesia_websocket_smoke.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-011-cartesia-websocket-smoke.json"
OUT_JSON = ROOT / ".tmp" / "VOICE-011-cartesia-websocket-smoke-validation.json"
REPORT_OUT = ROOT / ".tmp" / "VOICE-011-cartesia-websocket-smoke-validation-report.md"


SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
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
    for name in [
        "CARTESIA_API_KEY",
        "CARTESIA_VOICE_ID",
        "CARTESIA_VOICE_ID_DE",
        "CARTESIA_VOICE_ID_EN",
    ]:
        env.pop(name, None)
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
    assert_condition(payload["voice_milestone"] == "VOICE-011", "Unexpected milestone.")
    provider = payload["provider"]
    assert_condition(provider["provider_id"] == "cartesia-sonic-3-websocket", "Unexpected provider.")
    assert_condition(provider["endpoint_type"] == "tts-websocket", "VOICE-011 must use the WebSocket endpoint.")
    assert_condition(provider["api_key_env_var"] == "CARTESIA_API_KEY", "Cartesia key must be environment-only.")
    assert_condition(provider["default_voice_id_env_var"] == "CARTESIA_VOICE_ID", "Default voice ID env var mismatch.")
    assert_condition(provider["language_voice_id_env_vars"] == {"de": "CARTESIA_VOICE_ID_DE", "en": "CARTESIA_VOICE_ID_EN"}, "Language voice ID env vars mismatch.")
    assert_condition(provider["api_key_value_logged"] is False, "API key value must never be logged.")
    assert_condition(provider["voice_id_value_logged"] is False, "Voice ID value must never be logged.")

    summary = payload["summary"]
    assert_condition(summary["case_count"] == 4, "Expected four longer WebSocket quality cases.")
    assert_condition(summary["languages"] == {"de": 2, "en": 2}, "Expected two German and two English cases.")
    assert_condition(summary["live_call_requested"] is live_requested, "Unexpected live-call mode.")
    assert_condition(summary["websocket_connections_attempted"] == 0, "Validator must not connect to Cartesia.")
    assert_condition(summary["api_calls_made"] == 0, "Validator must not make provider calls.")
    assert_condition(summary["audio_files_created"] == 0, "No-key validation should not create audio.")
    assert_condition(summary["fallback_count"] == 4, "No-key validation should fall back for every case.")
    assert_condition(summary["customer_audio_uploaded"] is False, "VOICE-011 must not upload customer audio.")
    assert_condition(summary["synthetic_prompts_only"] is True, "VOICE-011 must use synthetic prompts only.")
    assert_condition(summary["timeout_seconds"] <= 10, "Timeout should stay bounded.")
    assert_condition(summary["response_language_matches"] == 4, "Agent decisions should preserve case language.")
    assert_condition(summary["quality_script_languages_match"] == 4, "Quality scripts should preserve language labels.")
    assert_condition(summary["audio_quality_human_rated"] is False, "Dry-run validation should not claim audio quality ratings.")

    for case in payload["cases"]:
        stream = case["cartesia_websocket"]
        packet = case["voice_packet"]
        assert_condition(case["quality_review"]["human_rating_required"] is True, f"{case['case_id']} should require human listening review.")
        assert_condition(case["quality_review"]["rating_recorded"] is False, f"{case['case_id']} should not have dry-run ratings.")
        assert_condition(packet["decision"]["response_language"] == case["language"], f"{case['case_id']} response language mismatch.")
        assert_condition(stream["provider_id"] == "cartesia-sonic-3-websocket", f"{case['case_id']} provider mismatch.")
        assert_condition(stream["model_id"] == "sonic-3", f"{case['case_id']} model mismatch.")
        assert_condition(stream["language"] == case["language"], f"{case['case_id']} language mismatch.")
        assert_condition(stream["websocket_connection_attempted"] is False, f"{case['case_id']} should not connect during validation.")
        assert_condition(stream["api_call_made"] is False, f"{case['case_id']} should not call provider during validation.")
        assert_condition(stream["audio_file_created"] is False, f"{case['case_id']} should not create audio during validation.")
        assert_condition(stream["fallback_used"] is True, f"{case['case_id']} should use fallback.")
        assert_condition(stream["fallback_provider"] == "text-only-tts-packet", f"{case['case_id']} fallback mismatch.")
        assert_condition(stream["api_key_value_logged"] is False, f"{case['case_id']} API key value should not be logged.")
        assert_condition(stream["voice_id_value_logged"] is False, f"{case['case_id']} voice ID value should not be logged.")
        assert_condition(stream["customer_audio_uploaded"] is False, f"{case['case_id']} should not upload customer audio.")
        assert_condition(stream["generated_text_sent_to_provider"] is False, f"{case['case_id']} should not send text during validation.")
        assert_condition(stream["timeout_seconds"] <= 10, f"{case['case_id']} timeout too high.")
        assert_condition(stream["request_preview"]["headers"]["X-API-Key"] == "<redacted>", f"{case['case_id']} API key preview not redacted.")
        assert_condition(stream["request_preview"]["voice"]["id"].startswith("<redacted-env:"), f"{case['case_id']} voice preview not redacted.")
        assert_condition(len(stream["transcript_chunks"]) >= 2, f"{case['case_id']} should test chunked input.")
        assert_condition(stream["output_format"]["container"] == "raw", f"{case['case_id']} should use raw WebSocket audio.")
        assert_condition(stream["output_format"]["encoding"] == "pcm_s16le", f"{case['case_id']} should use PCM output.")
        if live_requested:
            assert_condition(
                stream["fallback_reason"] in {"forced-key-missing", "missing-cartesia-api-key", "missing-cartesia-voice-id"},
                f"{case['case_id']} should explain live fallback.",
            )
        else:
            assert_condition(stream["fallback_reason"] == "dry-run-mode", f"{case['case_id']} should stay dry-run.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "VOICE-011 Cartesia WebSocket smoke script is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-011 Cartesia WebSocket case file is missing.")

    live_missing_key_payload = run_smoke("--live", "--force-key-missing")
    validate_payload(live_missing_key_payload, live_requested=True)

    dry_run_payload = run_smoke()
    validate_payload(dry_run_payload, live_requested=False)
    assert_condition(dry_run_payload == json.loads(OUT_JSON.read_text(encoding="utf-8")), "Stdout and JSON artifact should match.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-011 validation report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No WebSocket connections were attempted" in report_text, "Report should state no WebSocket connections for validation.")
    assert_condition("No customer audio was uploaded" in report_text, "Report should state no customer audio upload.")
    assert_condition("CARTESIA_API_KEY" in report_text, "Report should document key env var.")
    assert_condition("CARTESIA_VOICE_ID_DE" in report_text, "Report should document German voice env var.")
    assert_condition("CARTESIA_VOICE_ID_EN" in report_text, "Report should document English voice env var.")
    assert_condition("Human listening review required" in report_text, "Report should keep quality claims human-rated.")
    assert_condition("text-only-tts-packet" in report_text, "Report should document fallback.")
    assert_condition("timeout" in report_text.lower(), "Report should document timeout guardrails.")

    serialized = json.dumps(dry_run_payload) + json.dumps(live_missing_key_payload) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-011 Cartesia WebSocket smoke validation passed.")


if __name__ == "__main__":
    main()
