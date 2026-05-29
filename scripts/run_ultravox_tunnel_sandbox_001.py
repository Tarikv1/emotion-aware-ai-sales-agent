#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.audio_backends.ultravox_local_tool_server import build_server  # noqa: E402
from runtime.audio_backends.ultravox_sales_brain_mock import validate_ultravox_tool_response  # noqa: E402
from scripts.load_local_ultravox_env_001 import (  # noqa: E402
    ALLOW_GATE,
    API_KEY_ENV,
    ENABLE_GATE,
    UnsafeUltravoxEnvFile,
    load_local_ultravox_env,
)


CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_tunnel_sandbox_config.json"
LOCAL_ENDPOINT_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_local_tool_endpoint_config.json"
PROMPT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_agent_prompt.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
QUALITY_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-TUNNEL-SANDBOX-QUALITY-001"
QUALITY_RESULT_PATH = QUALITY_DIR / "result.json"
QUALITY_REPORT_PATH = QUALITY_DIR / "report.md"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"

CREATE_CALL_URL = "https://api.ultravox.ai/api/calls"
DELETE_CALL_URL_TEMPLATE = "https://api.ultravox.ai/api/calls/{call_id}"
TOOL_TOKEN_ENV = "PROJECT_ULTRAVOX_TOOL_TOKEN"
TUNNEL_GATE = "LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL"
TOOL_AUTH_TOKEN_NAME = "projectToolToken"
TUNNEL_START_TIMEOUT_SECONDS = 25
PROVIDER_TOOL_OBSERVATION_SECONDS = 2


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def sanitize_text(text: str) -> str:
    for value in (os.environ.get(API_KEY_ENV), os.environ.get(TOOL_TOKEN_ENV)):
        if value:
            text = text.replace(value, "<redacted>")
    return " ".join(text.split())[:1000]


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        raw = error.read(2048)
    except Exception:
        raw = b""
    return sanitize_text(raw.decode("utf-8", errors="replace"))


def env_gates(metadata: dict[str, bool]) -> dict[str, bool]:
    return {
        "ENABLE_ULTRAVOX_SANDBOX=1": os.environ.get(ENABLE_GATE) == "1",
        "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1": os.environ.get(ALLOW_GATE) == "1",
        "ULTRAVOX_API_KEY present": metadata["api_key_present"],
        "LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1": os.environ.get(TUNNEL_GATE) == "1",
        "PROJECT_ULTRAVOX_TOOL_TOKEN present": bool(os.environ.get(TOOL_TOKEN_ENV)),
    }


def provider_gates_enabled(gates: dict[str, bool]) -> bool:
    return (
        gates["ENABLE_ULTRAVOX_SANDBOX=1"]
        and gates["LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1"]
        and gates["ULTRAVOX_API_KEY present"]
    )


def tunnel_gates_enabled(gates: dict[str, bool]) -> bool:
    return (
        gates["LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1"]
        and gates["PROJECT_ULTRAVOX_TOOL_TOKEN present"]
    )


def boundary_fields() -> dict[str, Any]:
    return {
        "outbound_phone_call_made": False,
        "outbound_phone_calls_made": False,
        "real_customer_data_used": False,
        "synthetic_prompts_only": True,
        "raw_private_audio_or_transcripts_used": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_used": False,
        "raw_audio_stored": False,
        "audio_committed": False,
        "secrets_logged": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": False,
        "model_weights_downloaded": False,
        "training_performed": False,
        "crm_email_calendar_actions_made": False,
        "side_effects_allowed": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def build_request_payload() -> dict[str, Any]:
    return {
        "session_id": "tunnel-sandbox-local-preflight-001",
        "buyer_utterance_text": "What is this?",
        "ultravox_session_summary": "Synthetic short-term context for tunnel endpoint preflight.",
        "project_memory_summary": "Synthetic project memory: project owns canonical memory, campaign truth, and side-effect boundaries.",
        "current_campaign_id": "synthetic_voice_sandbox",
        "detected_emotion_hint": "curious",
        "turn_index": 1,
        "requested_action_context": "opening_orientation",
    }


def post_tool_json(url: str, payload: dict[str, Any], token: str | None) -> tuple[int, dict[str, Any], float]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["X-Project-Tool-Token"] = token
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST", headers=headers)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body), elapsed_ms(start)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        return error.code, json.loads(body) if body else {}, elapsed_ms(start)


def evaluate_public_endpoint_test(public_url: str, path: str, token: str) -> dict[str, Any]:
    endpoint_url = public_url.rstrip("/") + path
    sample = build_request_payload()
    valid_status, valid_response, latency_ms = post_tool_json(endpoint_url, sample, token)
    missing_status, _, _ = post_tool_json(endpoint_url, sample, None)
    invalid_status, _, _ = post_tool_json(endpoint_url, sample, "invalid-token")
    validation_errors = validate_ultravox_tool_response(valid_response) if valid_status == 200 else []
    valid_passed = (
        valid_status == 200
        and not validation_errors
        and valid_response.get("side_effects_allowed") is False
        and valid_response.get("allowed_to_speak") is True
    )
    return {
        "valid_request_status": valid_status,
        "valid_request_passed": valid_passed,
        "valid_request_latency_ms": latency_ms,
        "missing_token_status": missing_status,
        "missing_token_rejected": missing_status == 401,
        "invalid_token_status": invalid_status,
        "invalid_token_rejected": invalid_status == 401,
        "response_schema_errors": validation_errors,
        "auth_token_printed": False,
        "passed": valid_passed and missing_status == 401 and invalid_status == 401,
    }


def available_tunnel_tool() -> tuple[str | None, str | None]:
    if shutil.which("cloudflared"):
        return "cloudflared", shutil.which("cloudflared")
    if shutil.which("ngrok"):
        return "ngrok", shutil.which("ngrok")
    if shutil.which("localtunnel"):
        return "localtunnel", shutil.which("localtunnel")
    if shutil.which("lt"):
        return "lt", shutil.which("lt")
    return None, None


def command_for_tunnel(tool: str, executable: str, port: int) -> list[str]:
    local_url = f"http://127.0.0.1:{port}"
    if tool == "cloudflared":
        return [executable, "tunnel", "--url", local_url, "--no-autoupdate"]
    if tool == "ngrok":
        return [executable, "http", local_url, "--log=stdout", "--log-format=json"]
    if tool in {"localtunnel", "lt"}:
        return [executable, "--port", str(port), "--local-host", "127.0.0.1"]
    raise ValueError(f"unsupported tunnel tool: {tool}")


def parse_https_url(line: str) -> str | None:
    match = re.search(r"https://[A-Za-z0-9_.-]+(?::[0-9]+)?", line)
    if not match:
        return None
    candidate = match.group(0).rstrip(".,)")
    parsed = urlparse(candidate)
    if parsed.scheme == "https" and parsed.netloc:
        return f"https://{parsed.netloc}"
    return None


def start_tunnel(tool: str, executable: str, port: int) -> tuple[subprocess.Popen[str] | None, str | None, dict[str, Any]]:
    command = command_for_tunnel(tool, executable, port)
    start = time.perf_counter()
    output_queue: queue.Queue[str] = queue.Queue()
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=False,
        )
    except Exception as error:
        return None, None, {
            "start_error": sanitize_text(str(error)),
            "start_latency_ms": elapsed_ms(start),
            "log_line_count": 0,
        }

    def reader() -> None:
        if process.stdout is None:
            return
        for raw_line in process.stdout:
            output_queue.put(raw_line)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    log_line_count = 0
    public_url = None
    deadline = time.monotonic() + TUNNEL_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        try:
            line = output_queue.get(timeout=0.2)
        except queue.Empty:
            continue
        log_line_count += 1
        parsed = parse_https_url(line)
        if parsed:
            public_url = parsed
            break

    while not output_queue.empty():
        output_queue.get_nowait()
        log_line_count += 1
    details = {
        "start_error": None,
        "start_latency_ms": elapsed_ms(start),
        "log_line_count": log_line_count,
        "process_exited_before_url": process.poll() is not None and public_url is None,
    }
    return process, public_url, details


def stop_process(process: subprocess.Popen[str] | None) -> dict[str, Any]:
    if process is None:
        return {"attempted": False, "terminated": False, "killed": False}
    if process.poll() is not None:
        return {"attempted": True, "terminated": True, "killed": False, "exit_code": process.returncode}
    process.terminate()
    try:
        process.wait(timeout=6)
        return {"attempted": True, "terminated": True, "killed": False, "exit_code": process.returncode}
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=6)
        return {"attempted": True, "terminated": False, "killed": True, "exit_code": process.returncode}


def build_temporary_tool_definition(tool_url: str) -> dict[str, Any]:
    fields = [
        ("session_id", "Synthetic session id.", "string"),
        ("buyer_utterance_text", "Sanitized buyer utterance text.", "string"),
        ("ultravox_session_summary", "Sanitized short-term Ultravox session context.", "string"),
        ("project_memory_summary", "Project-owned memory summary.", "string"),
        ("current_campaign_id", "Current synthetic campaign id.", "string"),
        ("detected_emotion_hint", "Optional emotion hint.", "string"),
        ("turn_index", "Turn index.", "integer"),
        ("requested_action_context", "Requested action context.", "string"),
    ]
    return {
        "modelToolName": "project_sales_brain_next_move",
        "description": (
            "Project-owned sales-brain tool. Call this for all sales or product guidance. "
            "Use only its buyer_facing_response, next_action_id, verifier_status, and safety_warnings."
        ),
        "dynamicParameters": [
            {
                "name": name,
                "location": "PARAMETER_LOCATION_BODY",
                "schema": {"type": schema_type, "description": description},
                "required": True,
            }
            for name, description, schema_type in fields
        ],
        "requirements": {
            "httpSecurityOptions": {
                "options": [
                    {
                        "requirements": {
                            TOOL_AUTH_TOKEN_NAME: {
                                "headerApiKey": {
                                    "name": "X-Project-Tool-Token"
                                }
                            }
                        }
                    }
                ]
            }
        },
        "timeout": "5s",
        "precomputable": False,
        "http": {
            "baseUrlPattern": tool_url,
            "httpMethod": "POST",
        },
    }


def build_call_body(tool_url: str, tool_token: str) -> dict[str, Any]:
    base_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.is_file() else ""
    system_prompt = (
        base_prompt
        + "\n\nPhase 4J3 tunnel sandbox addition: Use project_sales_brain_next_move for sales guidance. "
        "Do not invent product facts, do not claim side effects, do not claim OpenAI affiliation, and keep turns short. "
        "Speak only safe buyer-facing response text from the tool when available."
    )
    return {
        "model": "fixie-ai/ultravox",
        "recordingEnabled": False,
        "firstSpeaker": "FIRST_SPEAKER_AGENT",
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": 48000,
                "outputSampleRate": 48000,
                "clientBufferSizeMs": 60,
                "dataMessages": {
                    "callStarted": True,
                    "transcript": False,
                    "callEvent": True,
                    "debug": False,
                },
            }
        },
        "maxDuration": "20s",
        "systemPrompt": system_prompt,
        "selectedTools": [
            {
                "temporaryTool": build_temporary_tool_definition(tool_url),
                "authTokens": {
                    TOOL_AUTH_TOKEN_NAME: tool_token
                },
            }
        ],
        "metadata": {
            "project": "emotion-aware-ai-sales-agent",
            "milestone": "ULTRAVOX-TUNNEL-SANDBOX-001",
            "synthetic": "true",
            "realCustomerData": "false",
            "outboundPhoneCall": "false",
        },
    }


def create_provider_call(tool_url: str, api_key: str, tool_token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        CREATE_CALL_URL,
        data=json.dumps(build_call_body(tool_url, tool_token), ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            call_id = payload.get("callId") or payload.get("call_id") or payload.get("id")
            join_url = payload.get("joinUrl") or payload.get("join_url")
            return {
                "api_call_made": True,
                "http_status": response.status,
                "latency_ms": elapsed_ms(start),
                "call_id_suffix": str(call_id)[-8:] if call_id else None,
                "join_url_received": bool(join_url),
                "join_url_host": urlparse(join_url).netloc if join_url else None,
                "provider_error": None,
                "call_id_for_cleanup": call_id,
            }
    except urllib.error.HTTPError as error:
        return {
            "api_call_made": True,
            "http_status": error.code,
            "latency_ms": elapsed_ms(start),
            "call_id_suffix": None,
            "join_url_received": False,
            "join_url_host": None,
            "provider_error": read_error_body(error),
            "call_id_for_cleanup": None,
        }
    except Exception as error:
        return {
            "api_call_made": True,
            "http_status": None,
            "latency_ms": elapsed_ms(start),
            "call_id_suffix": None,
            "join_url_received": False,
            "join_url_host": None,
            "provider_error": sanitize_text(str(error)),
            "call_id_for_cleanup": None,
        }


def delete_provider_call(call_id: str | None, api_key: str) -> dict[str, Any]:
    if not call_id:
        return {"delete_api_call_made": False, "delete_http_status": None, "delete_latency_ms": None, "deleted": False}
    request = urllib.request.Request(
        DELETE_CALL_URL_TEMPLATE.replace("{call_id}", call_id),
        method="DELETE",
        headers={"X-API-Key": api_key},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return {
                "delete_api_call_made": True,
                "delete_http_status": response.status,
                "delete_latency_ms": elapsed_ms(start),
                "deleted": 200 <= response.status < 300,
            }
    except Exception as error:
        return {
            "delete_api_call_made": True,
            "delete_http_status": None,
            "delete_latency_ms": elapsed_ms(start),
            "deleted": False,
            "delete_error": sanitize_text(str(error)),
        }


def base_result(env_metadata: dict[str, bool], gates: dict[str, bool]) -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    return {
        "evaluation_id": "ULTRAVOX-TUNNEL-SANDBOX-001",
        "phase": "4J3",
        "run_status": "not_run",
        "blocker": None,
        "env_file_exists": env_metadata["env_file_exists"],
        "env_file_ignored_by_git": env_metadata["env_file_ignored_by_git"],
        "env_file_loaded": env_metadata["env_file_loaded"],
        "env_file_used": env_metadata["env_file_loaded"],
        "api_key_present": env_metadata["api_key_present"],
        "tool_token_present": bool(os.environ.get(TOOL_TOKEN_ENV)),
        "env_gates": gates,
        "local_endpoint_host": config["local_endpoint_host"],
        "local_endpoint_port": config["local_endpoint_port"],
        "local_endpoint_path": config["local_endpoint_path"],
        "local_endpoint_method": config["local_endpoint_method"],
        "local_server_started": False,
        "tunnel_attempted": False,
        "tunnel_tool_used": None,
        "tunnel_url_created": False,
        "tunnel_url_redacted_or_domain_only": None,
        "tunnel_stop_result": {"attempted": False, "terminated": False, "killed": False},
        "local_public_endpoint_test_passed": False,
        "public_endpoint_test": {},
        "provider_call_attempted": False,
        "provider_call_made": False,
        "sandbox_run": False,
        "ultravox_session_created": False,
        "tool_call_supported": "unknown",
        "tool_call_attempted": False,
        "tool_call_succeeded": False,
        "hosted_turns_attempted": 0,
        "synthetic_cases_attempted": 0,
        "synthetic_cases_planned": [
            "What is this?",
            "I use ChatGPT and other AI tools.",
            "Don't put me in CRM.",
        ],
        "public_tool_endpoint_required": True,
        "public_tool_endpoint_available": False,
        "public_tool_endpoint_host": None,
        "browser_websocket_session_mode_used": "none",
        "provider_minutes_budget_note": "user reported about 30 minutes free use; phase intentionally minimal",
        "product_truth_drift_count": 0,
        "unsupported_claim_count": 0,
        "fake_side_effect_count": 0,
        "crm_email_calendar_claim_count": 0,
        "internal_label_leak_count": 0,
        "source_boundary_violation_count": 0,
        "memory_conflict_count": 0,
        "tool_response_followed_count": 0,
        "latency_metrics": {},
        "transcript_metadata": {"available": False, "stored": False, "sanitized": True},
        "create_call": {"api_call_made": False},
        "delete_call": {"delete_api_call_made": False},
        "source_grounding": [
            {
                "url": "https://docs.ultravox.ai/tools/custom/http-vs-client-tools",
                "claim": "HTTP tools run on your server and Ultravox calls them via HTTP; HTTP tools support WebRTC, websocket, and telephony call mediums."
            },
            {
                "url": "https://docs.ultravox.ai/tools/custom/authentication",
                "claim": "HTTP tool auth can use a custom header requirement, with token values supplied at call creation through selectedTools.authTokens."
            },
            {
                "url": "https://docs.ultravox.ai/tools/custom/durable-vs-temporary-tools",
                "claim": "Temporary tools are call-scoped and defined inline for API-created calls, which fits sandbox testing before durable dashboard setup."
            }
        ],
        **boundary_fields(),
        "notes": [
            "No outbound phone call is supported or attempted.",
            "No real customer audio or transcript is accepted.",
            "No API key or tool token value is printed or written to evidence.",
            "Public tunnel is skipped unless tunnel gates are enabled.",
            "Provider call is skipped unless provider gates are enabled and the public endpoint preflight passes."
        ],
    }


def build_result() -> dict[str, Any]:
    try:
        env_metadata = load_local_ultravox_env()
        unsafe_secret_file = False
    except UnsafeUltravoxEnvFile:
        env_metadata = {
            "env_file_exists": True,
            "env_file_ignored_by_git": False,
            "env_file_loaded": False,
            "api_key_present": bool(os.environ.get(API_KEY_ENV)),
            "gates_enabled": False,
        }
        unsafe_secret_file = True
    gates = env_gates(env_metadata)
    result = base_result(env_metadata, gates)

    if unsafe_secret_file:
        result["run_status"] = "unsafe_secret_file"
        result["blocker"] = "runtime/config/local/ultravox.env exists but is not ignored by Git; script refused to read it."
        return result
    if not tunnel_gates_enabled(gates):
        result["run_status"] = "not_run_tunnel_gates_disabled"
        result["blocker"] = "Temporary public tool tunnel gates were not fully enabled; tunnel skipped."
        return result
    if not provider_gates_enabled(gates):
        result["run_status"] = "not_run_provider_gates_disabled"
        result["blocker"] = "Provider gates were not fully enabled; tunnel skipped to avoid public exposure without a provider test."
        return result

    tunnel_tool, tunnel_executable = available_tunnel_tool()
    if not tunnel_tool or not tunnel_executable:
        result["run_status"] = "blocked_no_tunnel_tool"
        result["blocker"] = "No already-installed supported tunnel CLI found. Install cloudflared or ngrok and rerun."
        return result

    local_config = load_json(LOCAL_ENDPOINT_CONFIG_PATH)
    token = os.environ[TOOL_TOKEN_ENV]
    local_server = None
    local_thread: threading.Thread | None = None
    tunnel_process: subprocess.Popen[str] | None = None
    try:
        try:
            local_server = build_server(auth_token=token)
            local_thread = threading.Thread(target=local_server.serve_forever, daemon=True)
            local_thread.start()
            time.sleep(0.1)
            result["local_server_started"] = True
        except Exception as error:
            result["run_status"] = "blocked_local_server_start_failed"
            result["blocker"] = sanitize_text(str(error))
            return result

        result["tunnel_attempted"] = True
        result["tunnel_tool_used"] = tunnel_tool
        tunnel_process, public_url, tunnel_details = start_tunnel(tunnel_tool, tunnel_executable, int(local_config["port"]))
        result["latency_metrics"]["tunnel_start_latency_ms"] = tunnel_details.get("start_latency_ms")
        result["tunnel_start_details"] = tunnel_details
        if not public_url:
            result["run_status"] = "blocked_tunnel_url_not_detected"
            result["blocker"] = tunnel_details.get("start_error") or "Tunnel process did not expose an HTTPS URL within the bounded startup window."
            return result
        parsed = urlparse(public_url)
        if parsed.scheme != "https" or not parsed.netloc:
            result["run_status"] = "blocked_non_https_tunnel_url"
            result["blocker"] = "Tunnel URL was not HTTPS."
            return result

        result["tunnel_url_created"] = True
        result["tunnel_url_redacted_or_domain_only"] = parsed.netloc
        result["public_tool_endpoint_available"] = True
        result["public_tool_endpoint_host"] = parsed.netloc

        public_test = evaluate_public_endpoint_test(public_url, str(local_config["path"]), token)
        result["public_endpoint_test"] = public_test
        result["local_public_endpoint_test_passed"] = public_test["passed"]
        result["latency_metrics"]["public_endpoint_valid_request_latency_ms"] = public_test.get("valid_request_latency_ms")
        if not public_test["passed"]:
            result["run_status"] = "blocked_tunnel_test_failed"
            result["blocker"] = "Public tunnel endpoint preflight failed before provider call."
            return result

        provider_event_start = len(local_server.sanitized_events)
        tool_url = public_url.rstrip("/") + str(local_config["path"])
        result["provider_call_attempted"] = True
        create_call = create_provider_call(tool_url, os.environ[API_KEY_ENV], token)
        result["provider_call_made"] = create_call["api_call_made"]
        result["create_call"] = dict(create_call)
        cleanup_id = create_call.get("call_id_for_cleanup")
        result["create_call"].pop("call_id_for_cleanup", None)
        if create_call.get("http_status") is not None and 200 <= int(create_call["http_status"]) < 300:
            result["sandbox_run"] = True
            result["ultravox_session_created"] = True
            result["browser_websocket_session_mode_used"] = "server_websocket_session_creation_only"
            time.sleep(PROVIDER_TOOL_OBSERVATION_SECONDS)
        delete_call = delete_provider_call(cleanup_id, os.environ[API_KEY_ENV])
        result["delete_call"] = delete_call
        result["latency_metrics"]["create_call_latency_ms"] = create_call.get("latency_ms")
        result["latency_metrics"]["delete_call_latency_ms"] = delete_call.get("delete_latency_ms")

        provider_events = local_server.sanitized_events[provider_event_start:]
        provider_tool_events = [event for event in provider_events if event.get("event") == "tool_request"]
        result["tool_call_attempted"] = bool(provider_events)
        result["tool_call_succeeded"] = any(event.get("status") == 200 for event in provider_tool_events)
        result["tool_call_supported"] = result["tool_call_succeeded"] if result["tool_call_attempted"] else "unknown"
        result["provider_tool_event_count"] = len(provider_events)
        result["provider_tool_success_event_count"] = sum(1 for event in provider_tool_events if event.get("status") == 200)
        if result["tool_call_succeeded"]:
            result["run_status"] = "provider_session_created_tool_called"
            result["blocker"] = None
        elif result["ultravox_session_created"]:
            result["run_status"] = "provider_session_created_no_interaction"
            result["blocker"] = "Provider session was created with the temporary HTTP tool, but no automated conversation was run and no provider tool call was observed."
        else:
            result["run_status"] = "provider_create_failed"
            result["blocker"] = "Provider create-call request failed before an interactive turn."
        return result
    finally:
        result["tunnel_stop_result"] = stop_process(tunnel_process)
        if local_server is not None:
            local_server.shutdown()
            local_server.server_close()
        if local_thread is not None:
            local_thread.join(timeout=5)


def quality_reason(result: dict[str, Any]) -> str | None:
    if result["hosted_turns_attempted"] > 0:
        return None
    if result["run_status"] == "blocked_no_tunnel_tool":
        return "no_tunnel_tool"
    if result["run_status"] == "blocked_tunnel_test_failed":
        return "tunnel_test_failed"
    if result["run_status"] == "provider_session_created_no_interaction":
        return "hosted_session_created_but_no_interaction"
    if result["run_status"] == "provider_create_failed":
        return "provider_error"
    if result["run_status"].startswith("not_run"):
        return result["run_status"]
    if result["run_status"] == "provider_session_created_tool_called":
        return "websocket_client_missing"
    return result.get("run_status")


def build_quality_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-TUNNEL-SANDBOX-QUALITY-001",
        "phase": "4J3",
        "sandbox_run": result["sandbox_run"],
        "provider_call_made": result["provider_call_made"],
        "ultravox_session_created": result["ultravox_session_created"],
        "tool_call_attempted": result["tool_call_attempted"],
        "tool_call_succeeded": result["tool_call_succeeded"],
        "hosted_turns_attempted": result["hosted_turns_attempted"],
        "hosted_turns_not_run_reason": quality_reason(result),
        "product_truth_drift_count": result["product_truth_drift_count"],
        "unsupported_claim_count": result["unsupported_claim_count"],
        "fake_side_effect_count": result["fake_side_effect_count"],
        "crm_email_calendar_claim_count": result["crm_email_calendar_claim_count"],
        "internal_label_leak_count": result["internal_label_leak_count"],
        "source_boundary_violation_count": result["source_boundary_violation_count"],
        "memory_conflict_count": result["memory_conflict_count"],
        "tool_response_followed_count": result["tool_response_followed_count"],
        "latency_metrics": result["latency_metrics"],
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "raw_audio_stored": False,
        "audio_committed": False,
        "secrets_logged": False,
        "side_effects_allowed": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def recommendation_for(result: dict[str, Any]) -> str:
    status = result["run_status"]
    if status == "blocked_no_tunnel_tool":
        return "install cloudflared or ngrok, rerun"
    if status == "blocked_tunnel_test_failed":
        return "fix auth/endpoint before provider call"
    if status == "provider_create_failed":
        return "fix API/session payload"
    if status == "provider_session_created_no_interaction":
        return "implement WebSocket/browser client sandbox"
    if status == "provider_session_created_tool_called" and result["tool_call_succeeded"]:
        return "limited synthetic voice conversation test next"
    if result["tool_call_attempted"] and not result["tool_call_succeeded"]:
        return "do not proceed"
    if status == "not_run_tunnel_gates_disabled":
        return "provide tunnel gate and tool token, then rerun gated tunnel sandbox when ready"
    if status == "not_run_provider_gates_disabled":
        return "provide Ultravox key/provider gates and rerun gated tunnel sandbox when ready"
    if status == "unsafe_secret_file":
        return "fix local secret file ignore rule before any sandbox"
    return "keep Ultravox as research/reference only"


def build_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
        "phase": "4J3",
        "recommendation": recommendation_for(result),
        "tunnel_sandbox_run_status": result["run_status"],
        "blocker": result["blocker"],
        "sandbox_run": result["sandbox_run"],
        "provider_call_made": result["provider_call_made"],
        "provider_call_attempted": result["provider_call_attempted"],
        "tunnel_attempted": result["tunnel_attempted"],
        "tunnel_tool_used": result["tunnel_tool_used"],
        "tunnel_url_created": result["tunnel_url_created"],
        "local_public_endpoint_test_passed": result["local_public_endpoint_test_passed"],
        "ultravox_session_created": result["ultravox_session_created"],
        "tool_call_attempted": result["tool_call_attempted"],
        "tool_call_succeeded": result["tool_call_succeeded"],
        "hosted_turns_attempted": result["hosted_turns_attempted"],
        "public_tool_endpoint_required": result["public_tool_endpoint_required"],
        "public_tool_endpoint_available": result["public_tool_endpoint_available"],
        "product_truth_drift_count": result["product_truth_drift_count"],
        "unsupported_claim_count": result["unsupported_claim_count"],
        "fake_side_effect_count": result["fake_side_effect_count"],
        "latency_metrics": result["latency_metrics"],
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "memory_ownership_decision": "project_runtime_owns_canonical_memory",
        "sales_brain_ownership_decision": "project_runtime_owns_sales_brain_and_campaign_truth",
        "ultravox_product_truth_owner": False,
        "side_effects_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "decision_logic": [
            "If no tunnel tool exists: install cloudflared or ngrok, rerun.",
            "If tunnel endpoint test fails: fix auth/endpoint before provider call.",
            "If provider session cannot be created: fix API/session payload.",
            "If session created but interaction is not automated: implement WebSocket/browser client sandbox.",
            "If tool call works with no drift: limited synthetic voice conversation test next.",
            "If tool boundary cannot be enforced: do not proceed.",
        ],
    }


def render_result_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-TUNNEL-SANDBOX-001 Report",
            "",
            f"Run status: `{result['run_status']}`",
            f"Blocker: `{result['blocker']}`",
            f"Env file exists: `{str(result['env_file_exists']).lower()}`",
            f"Env file ignored by Git: `{str(result['env_file_ignored_by_git']).lower()}`",
            f"Env file loaded: `{str(result['env_file_loaded']).lower()}`",
            f"API key present: `{str(result['api_key_present']).lower()}`",
            f"Tool token present: `{str(result['tool_token_present']).lower()}`",
            f"Local server started: `{str(result['local_server_started']).lower()}`",
            f"Tunnel attempted: `{str(result['tunnel_attempted']).lower()}`",
            f"Tunnel tool used: `{result['tunnel_tool_used']}`",
            f"Tunnel URL created: `{str(result['tunnel_url_created']).lower()}`",
            f"Tunnel URL redacted/domain only: `{result['tunnel_url_redacted_or_domain_only']}`",
            f"Public endpoint test passed: `{str(result['local_public_endpoint_test_passed']).lower()}`",
            f"Provider call attempted: `{str(result['provider_call_attempted']).lower()}`",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(result['ultravox_session_created']).lower()}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Hosted turns attempted: `{result['hosted_turns_attempted']}`",
            f"Outbound phone call made: `{str(result['outbound_phone_call_made']).lower()}`",
            f"Real customer data used: `{str(result['real_customer_data_used']).lower()}`",
            f"Audio committed: `{str(result['audio_committed']).lower()}`",
            f"Secrets logged: `{str(result['secrets_logged']).lower()}`",
            f"Side effects allowed: `{str(result['side_effects_allowed']).lower()}`",
            f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(result['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(result['response_text_changed']).lower()}`",
            "",
            "Project runtime remains the sales brain, campaign truth source, verifier, and canonical memory owner.",
            "",
        ]
    )


def render_quality_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-TUNNEL-SANDBOX-QUALITY-001 Report",
            "",
            f"Sandbox run: `{str(result['sandbox_run']).lower()}`",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(result['ultravox_session_created']).lower()}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Hosted turns attempted: `{result['hosted_turns_attempted']}`",
            f"Hosted turns not run reason: `{result['hosted_turns_not_run_reason']}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Unsupported claim count: `{result['unsupported_claim_count']}`",
            f"Fake side-effect count: `{result['fake_side_effect_count']}`",
            f"CRM/email/calendar claim count: `{result['crm_email_calendar_claim_count']}`",
            f"Internal label leak count: `{result['internal_label_leak_count']}`",
            f"Memory conflict count: `{result['memory_conflict_count']}`",
            f"Latency metrics: `{json.dumps(result['latency_metrics'], sort_keys=True)}`",
            f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
            "",
        ]
    )


def render_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001 Report",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Tunnel sandbox run status: `{decision['tunnel_sandbox_run_status']}`",
            f"Blocker: `{decision['blocker']}`",
            f"Tunnel attempted: `{str(decision['tunnel_attempted']).lower()}`",
            f"Tunnel tool used: `{decision['tunnel_tool_used']}`",
            f"Public endpoint test passed: `{str(decision['local_public_endpoint_test_passed']).lower()}`",
            f"Provider call attempted: `{str(decision['provider_call_attempted']).lower()}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(decision['ultravox_session_created']).lower()}`",
            f"Tool call attempted: `{str(decision['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(decision['tool_call_succeeded']).lower()}`",
            f"Hosted turns attempted: `{decision['hosted_turns_attempted']}`",
            f"Product truth drift count: `{decision['product_truth_drift_count']}`",
            f"Fake side-effect count: `{decision['fake_side_effect_count']}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(decision['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(decision['response_text_changed']).lower()}`",
            "",
            "Project runtime owns canonical memory.",
            "Project runtime owns the sales brain and campaign truth.",
            "Ultravox remains a hosted speech-native interface candidate only.",
            "Side effects remain blocked.",
            "",
        ]
    )


def main() -> None:
    result = build_result()
    quality = build_quality_result(result)
    decision = build_decision(result)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_result_report(result))
    write_json(QUALITY_RESULT_PATH, quality)
    write_text(QUALITY_REPORT_PATH, render_quality_report(quality))
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_decision_report(decision))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
