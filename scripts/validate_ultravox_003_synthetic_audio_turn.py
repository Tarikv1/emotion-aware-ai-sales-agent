#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_ultravox_003_synthetic_audio_turn.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "ultravox-003-synthetic-audio-turn.json"
ENV_FILE = ROOT / "runtime" / "config" / "local" / "ultravox.env"
TMP_DIR = ROOT / ".tmp" / "ULTRAVOX-003"
OUT_JSON = TMP_DIR / "ULTRAVOX-003-synthetic-audio-turn.json"
REPORT_OUT = TMP_DIR / "ULTRAVOX-003-synthetic-audio-turn-report.md"
TMP_AUDIO_DIR = TMP_DIR / "audio"

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
    env.pop("ULTRAVOX_VOICE_ID_OR_NAME", None)
    return env


def run_turn(*extra_args: str) -> dict:
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
            "--audio-dir",
            str(TMP_AUDIO_DIR),
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
    assert_condition(payload["evaluation_milestone"] == "ULTRAVOX-003", "Unexpected milestone.")
    provider = payload["provider"]
    summary = payload["summary"]
    request_preview = payload["request_preview"]
    synthetic = payload["synthetic_input_audio"]
    create = payload["create_call"]
    websocket = payload["websocket"]
    delete = payload["delete_call"]

    assert_condition(provider["provider_id"] == "ultravox-hosted-api", "Unexpected provider.")
    assert_condition(provider["endpoint_type"] == "server-websocket", "Unexpected endpoint type.")
    assert_condition(provider["model"] == "fixie-ai/ultravox", "Unexpected model.")
    assert_condition(provider["api_key_env_var"] == "ULTRAVOX_API_KEY", "Unexpected API key env var.")
    assert_condition(provider["voice_env_var"] == "ULTRAVOX_VOICE_ID_OR_NAME", "Unexpected voice env var.")
    assert_condition(provider["voice_value_logged"] is False, "Voice value must not be logged.")
    assert_condition(provider["voice_selection"] == "ultravox-default", "Validation should not read voice env values.")
    assert_condition(provider["env_file"] == "runtime/config/local/ultravox.env", "Unexpected env file.")
    assert_condition(provider["api_key_value_logged"] is False, "API key value must not be logged.")
    assert_condition(provider["join_url_value_logged"] is False, "Join URL value must not be logged.")
    assert_condition(provider["input_sample_rate"] == 48000, "Unexpected input sample rate.")
    assert_condition(provider["output_sample_rate"] == 48000, "Unexpected output sample rate.")

    assert_condition(summary["live_call_requested"] is live_requested, "Unexpected live mode.")
    assert_condition(summary["approved_live_test"] is True, "Live approval should be recorded.")
    assert_condition(summary["create_call_api_calls_made"] == 0, "Validator must not create UltraVox calls.")
    assert_condition(summary["delete_call_api_calls_made"] == 0, "Validator must not delete provider calls.")
    assert_condition(summary["websocket_connections_attempted"] == 0, "Validator must not open WebSockets.")
    assert_condition(summary["real_customer_audio_uploaded"] is False, "Real customer audio must not upload.")
    assert_condition(summary["synthetic_customer_audio_uploaded"] is False, "Fallback validation must not upload audio.")
    assert_condition(summary["synthetic_prompt_only"] is True, "Synthetic boundary missing.")
    assert_condition(summary["voice_cloning_used"] is False, "Voice cloning must stay blocked.")
    assert_condition(summary["provider_owned_business_logic"] is False, "Provider must not own business logic.")
    assert_condition(summary["durable_provider_agent_created"] is False, "No durable provider agent should be created.")
    assert_condition(summary["runtime_behavior_changed"] is False, "Runtime behavior must not change.")
    assert_condition(summary["opens_prod_102"] is False, "ULTRAVOX-003 must not open PROD-102.")
    assert_condition(summary["fallback_used"] is True, "Validation should stay in fallback.")
    assert_condition(summary["fallback_reason"] == expected_fallback, "Unexpected fallback reason.")
    assert_condition(summary["timeout_seconds"] <= 12, "Timeout should stay bounded.")

    body = request_preview["body"]
    assert_condition(request_preview["headers"]["X-API-Key"] == "<redacted>", "Request preview should redact API key.")
    assert_condition(body["recordingEnabled"] is False, "Recording should be disabled.")
    assert_condition(body["firstSpeaker"] == "FIRST_SPEAKER_USER", "Synthetic audio turn should be user-first.")
    assert_condition(body["transcriptOptional"] is False, "Transcript should not be optional for this test.")
    assert_condition(body["initialOutputMedium"] == "MESSAGE_MEDIUM_VOICE", "Turn should request voice output.")
    assert_condition(body["languageHint"] == "en", "Unexpected language hint.")
    assert_condition(body["medium"]["serverWebSocket"]["inputSampleRate"] == 48000, "Unexpected request input sample rate.")
    assert_condition(body["medium"]["serverWebSocket"]["outputSampleRate"] == 48000, "Unexpected request output sample rate.")
    assert_condition(body["medium"]["serverWebSocket"]["dataMessages"]["transcript"] is True, "Transcript events should be enabled.")
    assert_condition(body["metadata"]["syntheticCustomerAudio"] == "true", "Synthetic-audio metadata missing.")
    assert_condition(body["metadata"]["realCustomerAudio"] == "false", "Real-customer metadata must stay false.")
    assert_condition("voice" not in body, "Default-voice validation should omit raw voice.")

    assert_condition(synthetic["synthesis_attempted"] is False, "Validator must not synthesize audio in fallback.")
    assert_condition(synthetic["pcm_byte_size"] == 0, "Validator must not prepare PCM in fallback.")
    assert_condition(create["api_call_made"] is False, "Validator must not call create.")
    assert_condition(create["join_url_received"] is False, "Validator must not receive a join URL.")
    assert_condition(create["join_url_host"] is None, "Validator must not log join URL host without a call.")
    assert_condition(websocket["websocket_connection_attempted"] is False, "Validator must not open WebSocket.")
    assert_condition(websocket["customer_audio_bytes_sent"] == 0, "Validator must not send synthetic audio.")
    assert_condition(websocket["agent_audio_file_created"] is False, "Validator must not create agent audio.")
    assert_condition(delete["delete_api_call_made"] is False, "Validator must not delete provider calls.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "ULTRAVOX-003 runner is missing.")
    assert_condition(CASES_PATH.exists(), "ULTRAVOX-003 case file is missing.")

    dry_run = run_turn()
    validate_payload(dry_run, live_requested=False, expected_fallback="dry-run-mode")

    missing_key = run_turn("--live", "--force-key-missing")
    validate_payload(missing_key, live_requested=True, expected_fallback="forced-key-missing")

    assert_condition(OUT_JSON.exists(), "Expected ULTRAVOX-003 JSON artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected ULTRAVOX-003 Markdown artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("ULTRAVOX-003 Synthetic Audio Turn Report" in report_text, "Report title missing.")
    assert_condition("Real customer audio uploaded: `false`" in report_text, "Report should state no real customer audio.")
    assert_condition("Synthetic customer audio uploaded: `false`" in report_text, "Fallback report should state no synthetic upload.")
    assert_condition("API key value logged: `false`" in report_text, "Report should state no API key logging.")
    assert_condition("Voice value logged: `false`" in report_text, "Report should state no voice value logging.")
    assert_condition("Join URL value logged: `false`" in report_text, "Report should state no join URL logging.")

    serialized = json.dumps(dry_run) + json.dumps(missing_key) + report_text
    assert_no_secret_patterns(serialized)
    print("ULTRAVOX-003 synthetic audio turn validation passed.")


if __name__ == "__main__":
    main()
