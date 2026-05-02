#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "generate_runtime_tts_delivery.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
TMP_DIR = ROOT / ".tmp" / "resp-003-validation"
RESULT_PATH = TMP_DIR / "RESP-003-runtime-live-tts-result.json"
REPORT_PATH = TMP_DIR / "RESP-003-runtime-live-tts-report.md"
AUDIO_DIR = TMP_DIR / "audio"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def run_resp_003(transcript: str, extra_args: list[str] | None = None) -> dict:
    args = [
        sys.executable,
        str(RUNNER),
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--transcript",
        transcript,
        "--cases",
        str(CASES_PATH),
        "--provider",
        "elevenlabs",
        "--audio-dir",
        str(AUDIO_DIR),
        "--out",
        str(RESULT_PATH),
        "--report-out",
        str(REPORT_PATH),
    ]
    if extra_args:
        args.extend(extra_args)
    completed = run_command(args)
    assert_condition(completed.returncode == 0, completed.stderr)
    return parse_stdout_json(completed)


def validate_common_payload(payload: dict) -> None:
    delivery = payload["tts_delivery"]
    assert_condition(payload["runtime_tts_delivery_id"] == "RESP-003-runtime-live-tts", payload)
    assert_condition(payload["runtime_voice_delivery_id"] == "RESP-002-runtime-voice-delivery", payload)
    assert_condition(delivery["source_runtime_voice_delivery_id"] == "RESP-002-runtime-voice-delivery", delivery)
    assert_condition(delivery["api_key_value_logged"] is False, delivery)
    assert_condition(delivery["voice_id_value_logged"] is False, delivery)
    assert_condition(delivery["customer_audio_uploaded"] is False, delivery)
    assert_condition(delivery["voice_cloning_used"] is False, delivery)
    assert_condition(delivery["synthetic_prompt_only"] is True, delivery)
    assert_condition(delivery["timeout_seconds"] <= 10, delivery)
    assert_condition(delivery["validation"]["passed"] is True, delivery["validation"])
    assert_condition(delivery["asset_log"]["run_boundary"]["api_key_location"] == "environment-only", delivery["asset_log"])
    assert_condition(delivery["asset_log"]["inputs"]["customer_audio_uploaded"] is False, delivery["asset_log"])
    assert_condition(delivery["asset_log"]["inputs"]["voice_cloning_used"] is False, delivery["asset_log"])
    assert_condition(delivery["asset_log"]["review"]["human_listening_review"] is False, delivery["asset_log"])


def validate_default_dry_run(payload: dict) -> None:
    delivery = payload["tts_delivery"]
    assert_condition(delivery["live_call_requested"] is False, delivery)
    assert_condition(delivery["provider_calls_made"] is False, delivery)
    assert_condition(delivery["generated_text_sent_to_provider"] is False, delivery)
    assert_condition(delivery["audio_file_created"] is False, delivery)
    assert_condition(delivery["fallback_used"] is True, delivery)
    assert_condition(delivery["fallback_reason"] == "dry-run-mode", delivery)
    assert_condition(delivery["tts_input_source"] == "provider_rendered_text", delivery)
    assert_condition("<redacted>" in json.dumps(delivery["request_preview"], ensure_ascii=False), delivery["request_preview"])


def validate_missing_key_live_fallback(payload: dict) -> None:
    delivery = payload["tts_delivery"]
    assert_condition(delivery["live_call_requested"] is True, delivery)
    assert_condition(delivery["provider_calls_made"] is False, delivery)
    assert_condition(delivery["generated_text_sent_to_provider"] is False, delivery)
    assert_condition(delivery["fallback_reason"] == "forced-key-missing", delivery)
    assert_condition(delivery["audio_file_created"] is False, delivery)


def validate_protected_text(payload: dict) -> None:
    delivery = payload["tts_delivery"]
    assert_condition(payload["voice_delivery"]["segments"][0]["segment_type"] == "do_not_call", payload["voice_delivery"])
    assert_condition(delivery["tts_input_source"] == "final_response", delivery)
    assert_condition(delivery["tts_input_text"] == payload["final_response"], delivery)
    assert_condition(delivery["provider_rendering_used"] is False, delivery)


def assert_no_secret_text(text: str, label: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in {label}: {match.group(0)!r}")


def main() -> None:
    assert_condition(RUNNER.exists(), "RESP-003 runner script is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    freeform_payload = run_resp_003("Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.")
    validate_common_payload(freeform_payload)
    validate_default_dry_run(freeform_payload)

    missing_key_payload = run_resp_003(
        "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
        ["--live", "--force-key-missing"],
    )
    validate_common_payload(missing_key_payload)
    validate_missing_key_live_fallback(missing_key_payload)

    protected_payload = run_resp_003("Rufen Sie mich bitte nicht mehr an.")
    validate_common_payload(protected_payload)
    validate_protected_text(protected_payload)

    assert_condition(RESULT_PATH.exists(), "RESP-003 JSON result file was not created.")
    assert_condition(REPORT_PATH.exists(), "RESP-003 Markdown report was not created.")
    assert_no_secret_text(
        RESULT_PATH.read_text(encoding="utf-8")
        + REPORT_PATH.read_text(encoding="utf-8")
        + json.dumps(freeform_payload, ensure_ascii=False),
        "RESP-003 artifacts",
    )
    print("RESP-003 runtime live TTS validation passed.")


if __name__ == "__main__":
    main()
