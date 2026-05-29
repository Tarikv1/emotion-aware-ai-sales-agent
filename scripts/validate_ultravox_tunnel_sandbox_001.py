#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_tunnel_sandbox_config.json"
LOCAL_ENDPOINT_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_endpoint_config.json"
SERVER_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_server.py"
ENV_PATH = ROOT / "runtime" / "config" / "local" / "ultravox.env"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001" / "report.md"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9])"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def git_ignored(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_no_secret(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    config = load_json(CONFIG_PATH)
    local_config = load_json(LOCAL_ENDPOINT_CONFIG_PATH)
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret(json.dumps(config) + json.dumps(local_config) + json.dumps(result) + report + SERVER_PATH.read_text(encoding="utf-8"))

    if ENV_PATH.exists() and not git_ignored(ENV_PATH):
        fail("runtime/config/local/ultravox.env exists but is not ignored by Git")
    if result.get("evaluation_id") != "ULTRAVOX-TUNNEL-SANDBOX-001":
        fail("unexpected tunnel sandbox evaluation_id")
    if result.get("phase") != "4J3":
        fail("tunnel sandbox must record phase 4J3")
    for key in (
        "explicit_cloudflared_path_present",
        "explicit_cloudflared_path_exists",
        "explicit_cloudflared_version_ok",
        "cloudflared_available",
        "cloudflared_dns_failed_before",
        "cloudflared_passed_before",
        "ngrok_available",
        "ngrok_version_ok",
        "ngrok_config_check_attempted",
        "ngrok_config_check_succeeded",
        "explicit_ngrok_path_present",
        "explicit_ngrok_path_exists",
        "explicit_ngrok_version_ok",
        "tunnel_preflight_only",
        "dns_success",
        "http_success",
        "auth_preflight_success",
        "valid_request_success",
        "missing_token_401",
        "invalid_token_401",
        "provider_call_gate_passed",
    ):
        if not isinstance(result.get(key), bool):
            fail(f"{key} must be a boolean")
    if result.get("explicit_cloudflared_path_present") and result.get("explicit_cloudflared_executable") in {"", None}:
        fail("explicit cloudflared path evidence must include a safe executable path or redacted marker")
    if result.get("cloudflared_dns_failed_before") and result.get("ngrok_available"):
        if result.get("selected_preferred_tool") != "ngrok":
            fail("ngrok must be the selected preferred tool after prior cloudflared DNS failure")
    if result.get("ngrok_auth_configured") not in {True, False, "unknown"}:
        fail("ngrok_auth_configured must be true, false, or unknown")
    if result.get("ngrok_available") and result.get("ngrok_config_check_attempted") is not True:
        fail("ngrok config check must be attempted when ngrok is available")
    if result.get("run_status") == "blocked_ngrok_auth_missing":
        if result.get("ngrok_auth_configured") is not False:
            fail("ngrok auth missing blocker must record ngrok_auth_configured false")
        if result.get("tunnel_attempted") is not False:
            fail("ngrok auth missing blocker must stop before tunnel attempt")
    if result.get("run_status") == "blocked_explicit_cloudflared_path_missing" and result.get("explicit_cloudflared_path_exists") is not False:
        fail("missing explicit cloudflared path blocker must record path_exists false")
    if result.get("run_status") == "blocked_tunnel_url_not_detected" and result.get("tunnel_attempted") is not True:
        fail("tunnel URL parsing blocker must follow a tunnel attempt")
    for key in ("dns_attempt_count", "http_attempt_count"):
        if not isinstance(result.get(key), int):
            fail(f"{key} must be an integer")
    for key in ("dns_first_success_seconds", "http_first_success_seconds"):
        if key not in result:
            fail(f"{key} must exist")
    if result.get("provider_call_attempted") and result.get("provider_call_gate_passed") is not True:
        fail("provider call must not be attempted unless DNS, HTTP, and auth preflight gates passed")
    if result.get("tunnel_preflight_only") and result.get("provider_call_attempted") is not False:
        fail("provider call must not be attempted in tunnel-preflight-only mode")
    if result.get("run_status") == "blocked_tunnel_dns_failed" and result.get("dns_success") is not False:
        fail("DNS failure status must record dns_success false")
    if result.get("run_status") == "blocked_tunnel_http_failed" and result.get("http_success") is not False:
        fail("HTTP failure status must record http_success false")
    if result.get("run_status") == "blocked_tunnel_auth_failed" and result.get("auth_preflight_success") is not False:
        fail("auth failure status must record auth_preflight_success false")
    if config.get("tunnel_allowed_by_default") is not False:
        fail("tunnel config must block tunnel by default")
    if local_config.get("auth_required") is not True:
        fail("local endpoint must require auth")
    if local_config.get("auth_header_name") != "X-Project-Tool-Token":
        fail("local endpoint auth header must remain X-Project-Tool-Token")

    gates = result.get("env_gates", {})
    tunnel_gates = gates.get("LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1") is True and gates.get("PROJECT_ULTRAVOX_TOOL_TOKEN present") is True
    provider_gates = (
        gates.get("ENABLE_ULTRAVOX_SANDBOX=1") is True
        and gates.get("LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1") is True
        and gates.get("ULTRAVOX_API_KEY present") is True
    )
    if result.get("tunnel_attempted") and not tunnel_gates:
        fail("tunnel must not be attempted unless tunnel gates are enabled")
    if result.get("provider_call_made") and not provider_gates:
        fail("provider call must not be made unless provider gates are enabled")
    if result.get("provider_call_made") and result.get("local_public_endpoint_test_passed") is not True:
        fail("provider call must not happen before public endpoint preflight passes")
    if result.get("provider_call_made") and not (result.get("dns_success") and result.get("http_success") and result.get("auth_preflight_success")):
        fail("provider call must not happen before DNS, HTTP, and auth preflight pass")
    if result.get("tunnel_url_created") and not result.get("tunnel_url_redacted_or_domain_only"):
        fail("tunnel evidence must store redacted/domain-only URL metadata")
    if result.get("tunnel_domain_only") != result.get("tunnel_url_redacted_or_domain_only"):
        fail("tunnel_domain_only must match redacted/domain-only tunnel URL evidence")
    if result.get("tunnel_url_redacted_or_domain_only") and str(result["tunnel_url_redacted_or_domain_only"]).startswith("https://"):
        fail("tunnel evidence must not store full public URL")

    for key in (
        "outbound_phone_call_made",
        "outbound_phone_calls_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "raw_audio_stored",
        "audio_committed",
        "secrets_logged",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "local_model_generation_made",
        "model_weights_downloaded",
        "training_performed",
        "crm_email_calendar_actions_made",
        "side_effects_allowed",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if result.get(key) is not False:
            fail(f"{key} must be false")
    for field in (
        "product_truth_drift_count",
        "unsupported_claim_count",
        "fake_side_effect_count",
        "crm_email_calendar_claim_count",
        "internal_label_leak_count",
        "source_boundary_violation_count",
        "memory_conflict_count",
    ):
        if result.get(field) != 0:
            fail(f"{field} must stay 0")
    if "Project runtime remains the sales brain" not in report:
        fail("report must state project sales brain ownership")
    print("ULTRAVOX tunnel sandbox validation passed.")


if __name__ == "__main__":
    main()
