#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_ultravox_002_synthetic_live_smoke.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "ultravox-002-synthetic-live-smoke.json"
ENV_FILE = ROOT / "runtime" / "config" / "local" / "ultravox.env"
OUT_JSON = ROOT / ".tmp" / "ULTRAVOX-002" / "ULTRAVOX-002-synthetic-live-smoke.json"
REPORT_OUT = ROOT / ".tmp" / "ULTRAVOX-002" / "ULTRAVOX-002-synthetic-live-smoke-report.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
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
    env.pop("ULTRAVOX_API_KEY", None)
    return env


def run_smoke(*extra_args: str) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--cases",
            str(CASES_PATH),
            "--env-file",
            str(ENV_FILE),
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


def validate_payload(payload: dict, *, live_requested: bool, expected_fallback: str) -> None:
    assert_condition(payload["evaluation_milestone"] == "ULTRAVOX-002", "Unexpected milestone.")
    provider = payload["provider"]
    summary = payload["summary"]
    request_preview = payload["request_preview"]
    create = payload["create_call"]
    websocket = payload["websocket"]
    delete = payload["delete_call"]

    assert_condition(provider["provider_id"] == "ultravox-hosted-api", "Unexpected provider.")
    assert_condition(provider["endpoint_type"] == "server-websocket", "Unexpected endpoint type.")
    assert_condition(provider["api_key_env_var"] == "ULTRAVOX_API_KEY", "Unexpected API key env var.")
    assert_condition(provider["voice_env_var"] == "ULTRAVOX_VOICE_ID_OR_NAME", "Unexpected voice env var.")
    assert_condition(provider["voice_value_logged"] is False, "Voice value must not be logged.")
    assert_condition(provider["voice_selection"] in {"ultravox-default", "env-voice-id-or-name"}, "Unexpected voice selection.")
    assert_condition(provider["env_file"] == "runtime/config/local/ultravox.env", "Unexpected env file.")
    assert_condition(provider["api_key_value_logged"] is False, "API key value must not be logged.")
    assert_condition(provider["join_url_value_logged"] is False, "Join URL value must not be logged.")

    assert_condition(summary["live_call_requested"] is live_requested, "Unexpected live mode.")
    assert_condition(summary["approved_live_test"] is True, "Live approval should be recorded.")
    assert_condition(summary["customer_audio_uploaded"] is False, "Customer audio must not upload.")
    assert_condition(summary["audio_uploaded"] is False, "No input audio should upload in validation.")
    assert_condition(summary["synthetic_prompt_only"] is True, "Synthetic prompt boundary missing.")
    assert_condition(summary["voice_cloning_used"] is False, "Voice cloning must stay blocked.")
    assert_condition(summary["provider_owned_business_logic"] is False, "Provider must not own business logic.")
    assert_condition(summary["durable_provider_agent_created"] is False, "No durable provider agent should be created.")
    assert_condition(summary["runtime_behavior_changed"] is False, "Runtime behavior must not change.")
    assert_condition(summary["opens_prod_102"] is False, "ULTRAVOX-002 must not open PROD-102.")
    assert_condition(summary["fallback_used"] is True, "Validation should stay in fallback.")
    assert_condition(summary["fallback_reason"] == expected_fallback, "Unexpected fallback reason.")
    assert_condition(summary["timeout_seconds"] <= 10, "Timeout should stay bounded.")

    assert_condition(request_preview["headers"]["X-API-Key"] == "<redacted>", "Request preview should redact API key.")
    assert_condition(request_preview["body"]["recordingEnabled"] is False, "Recording should be disabled.")
    assert_condition(request_preview["body"]["firstSpeaker"] == "FIRST_SPEAKER_AGENT", "Smoke should be agent-first.")
    assert_condition(request_preview["body"]["initialOutputMedium"] == "MESSAGE_MEDIUM_VOICE", "Smoke should request voice output.")
    if provider["voice_selection"] == "ultravox-default":
        assert_condition("voice" not in request_preview["body"], "Default-voice mode should omit voice.")
    else:
        assert_condition(request_preview["body"]["voice"].startswith("<redacted-env:"), "Voice preview should redact env value.")

    assert_condition(create["api_call_made"] is False, "Validator must not create an UltraVox call.")
    assert_condition(create["join_url_received"] is False, "Validator must not receive a join URL.")
    assert_condition(create["join_url_host"] is None, "Validator must not log join URL host without a call.")
    assert_condition(websocket["websocket_connection_attempted"] is False, "Validator must not open WebSocket.")
    assert_condition(websocket["audio_file_created"] is False, "Validator must not create audio.")
    assert_condition(delete["delete_api_call_made"] is False, "Validator must not delete provider calls.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "ULTRAVOX-002 smoke script is missing.")
    assert_condition(CASES_PATH.exists(), "ULTRAVOX-002 case file is missing.")
    assert_condition(ENV_FILE.exists(), "ULTRAVOX env file is missing.")

    dry_run = run_smoke()
    validate_payload(dry_run, live_requested=False, expected_fallback="dry-run-mode")

    missing_key = run_smoke("--live", "--force-key-missing")
    validate_payload(missing_key, live_requested=False, expected_fallback="forced-key-missing")

    assert_condition(OUT_JSON.exists(), "Expected ULTRAVOX-002 JSON artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected ULTRAVOX-002 Markdown artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("ULTRAVOX-002 Synthetic Live Smoke Report" in report_text, "Report title missing.")
    assert_condition("Customer audio uploaded: `false`" in report_text, "Report should state no customer audio upload.")
    assert_condition("API key value logged: `false`" in report_text, "Report should state no API key logging.")
    assert_condition("Voice value logged: `false`" in report_text, "Report should state no voice value logging.")
    assert_condition("Join URL value logged: `false`" in report_text, "Report should state no join URL logging.")
    assert_condition("does not test customer speech understanding" in report_text, "Report should state the bounded limitation.")

    serialized = json.dumps(dry_run) + json.dumps(missing_key) + report_text
    assert_no_secret_patterns(serialized)
    print("ULTRAVOX-002 synthetic live smoke validation passed.")


if __name__ == "__main__":
    main()
