#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_voice_008_local_tts_smoke.py"
OUT_JSON = ROOT / "research" / "experiments" / "generated" / "VOICE-008-local-tts-smoke.json"
REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-008-local-tts-smoke-report.md"


SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def run_smoke(*extra_args: str) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out",
            str(OUT_JSON),
            "--report-out",
            str(REPORT_OUT),
            *extra_args,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def validate_payload(payload: dict, *, forced_fallback: bool) -> None:
    assert_condition(payload["voice_milestone"] == "VOICE-008", "Unexpected milestone.")
    assert_condition(payload["summary"]["case_count"] == 2, "Expected one German and one English TTS case.")
    assert_condition(payload["summary"]["languages"] == {"de": 1, "en": 1}, "Expected German and English coverage.")
    assert_condition(payload["summary"]["api_calls_made"] is False, "VOICE-008 must not call APIs.")
    assert_condition(payload["summary"]["requires_api_key"] is False, "VOICE-008 must not require API keys.")
    assert_condition(payload["summary"]["cloud_provider_used"] is False, "VOICE-008 must not use cloud providers.")
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, "VOICE-008 must not upload customer audio.")
    assert_condition(payload["summary"]["synthetic_voice_only"] is True, "VOICE-008 must stay synthetic voice only.")
    assert_condition(payload["summary"]["response_language_matches"] == 2, "Both cases should preserve response language.")
    assert_condition(payload["summary"]["tts_text_matches_decision"] == 2, "TTS text must match approved agent response.")
    assert_condition(payload["summary"]["fallback_safe_count"] == 2, "Both cases should have safe fallback metadata.")
    assert_condition(payload["summary"]["provider_attempted"] == "windows-sapi", "VOICE-008 should attempt Windows SAPI.")
    if forced_fallback:
        assert_condition(payload["summary"]["audio_file_success_count"] == 0, "Forced fallback should not create audio.")
        assert_condition(payload["summary"]["fallback_count"] == 2, "Forced fallback should use dry-run for both cases.")
    else:
        assert_condition(
            payload["summary"]["audio_file_success_count"] + payload["summary"]["fallback_count"] == 2,
            "Every case should either create audio or fall back safely.",
        )

    for case in payload["cases"]:
        expected_language = case["language"]
        packet = case["voice_packet"]
        assert_condition(packet["tts_text"] == packet["decision"]["agent_response"], f"{case['case_id']} TTS text mismatch.")
        assert_condition(packet["campaign"]["language"] == expected_language, f"{case['case_id']} campaign language mismatch.")
        assert_condition(packet["decision"]["campaign_language"] == expected_language, f"{case['case_id']} decision campaign language mismatch.")
        assert_condition(packet["decision"]["response_language"] == expected_language, f"{case['case_id']} response language mismatch.")
        assert_condition(case["local_tts"]["provider_attempted"] == "windows-sapi", f"{case['case_id']} should attempt Windows SAPI.")
        assert_condition(case["local_tts"]["fallback_provider"] == "dry-run", f"{case['case_id']} should declare dry-run fallback.")
        assert_condition(case["local_tts"]["requires_api_key"] is False, f"{case['case_id']} should not require an API key.")
        assert_condition(case["local_tts"]["cloud_provider_used"] is False, f"{case['case_id']} should not use cloud TTS.")
        assert_condition(case["local_tts"]["synthetic_voice_only"] is True, f"{case['case_id']} should stay synthetic.")
        assert_condition(case["local_tts"]["generation_latency_ms"] >= 0, f"{case['case_id']} missing latency.")
        if case["local_tts"]["audio_file_created"]:
            audio_path = ROOT / case["local_tts"]["audio_output_path"]
            assert_condition(audio_path.exists(), f"{case['case_id']} audio file is missing.")
            assert_condition(audio_path.stat().st_size == case["local_tts"]["audio_byte_size"], f"{case['case_id']} audio size mismatch.")
            assert_condition(case["local_tts"]["audio_byte_size"] > 44, f"{case['case_id']} WAV should contain audio bytes.")
            assert_condition(case["local_tts"]["final_provider"] == "windows-sapi", f"{case['case_id']} should report SAPI success.")
        else:
            assert_condition(case["local_tts"]["final_provider"] == "dry-run", f"{case['case_id']} fallback should be dry-run.")
            assert_condition(case["local_tts"]["fallback_used"] is True, f"{case['case_id']} should mark fallback.")
            assert_condition(case["local_tts"]["fallback_reason"], f"{case['case_id']} should explain fallback.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "VOICE-008 local TTS smoke script is missing.")

    forced_payload = run_smoke("--force-fallback")
    validate_payload(forced_payload, forced_fallback=True)

    normal_payload = run_smoke()
    validate_payload(normal_payload, forced_fallback=False)
    assert_condition(normal_payload == json.loads(OUT_JSON.read_text(encoding="utf-8")), "Stdout and JSON artifact should match.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-008 report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No API calls were made" in report_text, "Report should state no API calls.")
    assert_condition("No customer audio was uploaded" in report_text, "Report should state no audio upload.")
    assert_condition("German cases: `1`" in report_text, "Report should include German count.")
    assert_condition("English cases: `1`" in report_text, "Report should include English count.")
    assert_condition("dry-run fallback" in report_text.lower(), "Report should document fallback.")

    serialized = json.dumps(forced_payload) + json.dumps(normal_payload) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-008 local TTS smoke validation passed.")


if __name__ == "__main__":
    main()
