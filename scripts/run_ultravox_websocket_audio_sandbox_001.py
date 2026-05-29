#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import websocket as websocket_client  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - dependency presence is evidence, not logic.
    websocket_client = None  # type: ignore[assignment]

from runtime.audio_backends.ultravox_local_tool_server import build_server, handle_request  # noqa: E402
from scripts.generate_ultravox_synthetic_audio_inputs_001 import (  # noqa: E402
    RESULT_PATH as AUDIO_INPUT_RESULT_PATH,
    generate_synthetic_audio_inputs,
    persist_result as persist_audio_input_result,
)
from scripts.load_local_ultravox_env_001 import (  # noqa: E402
    ALLOW_GATE,
    API_KEY_ENV,
    ENABLE_GATE,
    UnsafeUltravoxEnvFile,
    load_local_ultravox_env,
)
from scripts.probe_ultravox_tunnel_tools_001 import discover_tunnel_tools  # noqa: E402
from scripts.run_ultravox_tunnel_sandbox_001 import (  # noqa: E402
    CREATE_CALL_URL,
    DELETE_CALL_URL_TEMPLATE,
    TOOL_AUTH_TOKEN_NAME,
    TOOL_TOKEN_ENV,
    TUNNEL_GATE,
    add_tunnel_discovery,
    auth_preflight,
    build_temporary_tool_definition,
    elapsed_ms,
    post_tool_json,
    sanitize_text,
    start_tunnel,
    stop_process,
    tunnel_gates_enabled,
    wait_for_dns_ready,
    wait_for_http_ready,
)
from scripts.run_ultravox_websocket_text_sandbox_001 import (  # noqa: E402
    build_project_tool_payload,
    coerce_tool_payload,
    count_quality_flags,
    expected_tool_responses,
)


CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_websocket_audio_sandbox_config.json"
PROMPT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_agent_prompt.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
AGENT_AUDIO_DIR = ROOT / "local_artifacts" / "audio_outputs" / "ultravox" / "agent_outputs"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"

WEBSOCKET_CONNECT_TIMEOUT_SECONDS = 10
PRE_TURN_LISTEN_SECONDS = 2.0
PER_TURN_LISTEN_SECONDS = 10.0
FINAL_LISTEN_SECONDS = 4.0
SOCKET_RECV_TIMEOUT_SECONDS = 1.0
AUDIO_CHUNK_MS = 100
POST_TURN_SILENCE_SECONDS = 0.35
MAX_RECORDED_MESSAGES = 80
SENSITIVE_URL_PATTERN = re.compile(r"(?:wss|https)://[^\s\"']+")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sanitize_for_evidence(value: Any) -> str:
    text = sanitize_text(str(value))
    text = SENSITIVE_URL_PATTERN.sub("<provider-url-redacted>", text)
    return text[:500]


def env_gates(metadata: dict[str, bool]) -> dict[str, bool]:
    return {
        "ENABLE_ULTRAVOX_SANDBOX=1": os.environ.get(ENABLE_GATE) == "1",
        "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1": os.environ.get(ALLOW_GATE) == "1",
        "ULTRAVOX_API_KEY present": bool(os.environ.get(API_KEY_ENV)),
        "LOCAL_ULTRAVOX_ALLOW_PUBLIC_TOOL_TUNNEL=1": os.environ.get(TUNNEL_GATE) == "1",
        "PROJECT_ULTRAVOX_TOOL_TOKEN present": bool(os.environ.get(TOOL_TOKEN_ENV)),
        "env_file_loaded": metadata.get("env_file_loaded") is True,
    }


def provider_gates_enabled(gates: dict[str, bool]) -> bool:
    return (
        gates["ENABLE_ULTRAVOX_SANDBOX=1"]
        and gates["LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS=1"]
        and gates["ULTRAVOX_API_KEY present"]
    )


def websocket_dependency_available() -> bool:
    return websocket_client is not None


def normalize_type(value: Any) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    raw = raw.replace("-", "_")
    raw = re.sub(r"(?<!^)([A-Z])", r"_\1", raw)
    return raw.lower()


def boundary_fields() -> dict[str, Any]:
    return {
        "outbound_phone_call_made": False,
        "outbound_phone_calls_made": False,
        "real_customer_data_used": False,
        "synthetic_prompts_only": True,
        "raw_private_audio_or_transcripts_used": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_used": False,
        "raw_audio_stored_public": False,
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


def read_or_generate_audio_inputs() -> dict[str, Any]:
    if AUDIO_INPUT_RESULT_PATH.is_file():
        return load_json(AUDIO_INPUT_RESULT_PATH)
    result = generate_synthetic_audio_inputs()
    persist_audio_input_result(result)
    return result


def read_input_audio(path: Path, expected_sample_rate: int) -> tuple[bytes, float, dict[str, Any]]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frames = wav_file.getnframes()
        if channels != 1 or sample_width != 2 or sample_rate != expected_sample_rate:
            raise ValueError(f"Expected 48000 Hz 16-bit mono WAV; got {sample_rate} Hz, {sample_width} bytes, {channels} channels")
        audio = wav_file.readframes(frames)
    duration = round(frames / float(expected_sample_rate), 3) if expected_sample_rate else 0.0
    return audio, duration, {"sample_rate": sample_rate, "channels": channels, "sample_width_bytes": sample_width, "duration_seconds": duration}


def write_agent_audio_output(audio: bytes, sample_rate: int) -> dict[str, Any] | None:
    if not audio:
        return None
    AGENT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = AGENT_AUDIO_DIR / "ultravox_agent_output_001.wav"
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)
    duration_seconds = round(len(audio) / float(sample_rate * 2), 3) if sample_rate else None
    return {
        "path": rel(path),
        "sha256": sha256_bytes(audio),
        "bytes": len(audio),
        "duration_seconds": duration_seconds,
        "sample_rate": sample_rate,
    }


def build_call_body(tool_url: str, tool_token: str, config: dict[str, Any]) -> dict[str, Any]:
    base_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.is_file() else ""
    system_prompt = (
        base_prompt
        + "\n\nPhase 4J5 WebSocket audio sandbox addition: this is synthetic local audio only, not a phone call, microphone test, CRM, email, calendar, or live runtime test. "
        "Use project_sales_brain_next_move for every product or sales answer. "
        "When the tool gives a buyer_facing_response and verifier_status is passed, speak only that safe buyer-facing response. "
        "If tool output is missing, ask a short clarification rather than inventing product facts."
    )
    return {
        "model": "fixie-ai/ultravox",
        "recordingEnabled": False,
        "firstSpeaker": "FIRST_SPEAKER_AGENT",
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": int(config["input_sample_rate"]),
                "outputSampleRate": int(config["output_sample_rate"]),
                "clientBufferSizeMs": 60,
                "dataMessages": {
                    "callStarted": True,
                    "transcript": True,
                    "callEvent": True,
                    "debug": False,
                },
            }
        },
        "maxDuration": "45s",
        "systemPrompt": system_prompt,
        "selectedTools": [
            {
                "temporaryTool": build_temporary_tool_definition(tool_url),
                "authTokens": {
                    TOOL_AUTH_TOKEN_NAME: tool_token,
                },
            }
        ],
        "metadata": {
            "project": "emotion-aware-ai-sales-agent",
            "milestone": "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001",
            "synthetic": "true",
            "realCustomerData": "false",
            "outboundPhoneCall": "false",
            "audioInput": "true",
            "liveWiring": "false",
        },
    }


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8")
    except Exception:
        return ""


def create_provider_call(tool_url: str, api_key: str, tool_token: str, config: dict[str, Any]) -> tuple[dict[str, Any], str | None, str | None]:
    request = urllib.request.Request(
        CREATE_CALL_URL,
        data=json.dumps(build_call_body(tool_url, tool_token, config), ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
            call_id = payload.get("callId") or payload.get("call_id") or payload.get("id")
            join_url = payload.get("joinUrl") or payload.get("join_url")
            parsed = urlparse(str(join_url)) if join_url else None
            return (
                {
                    "api_call_made": True,
                    "http_status": response.status,
                    "latency_ms": elapsed_ms(start),
                    "call_id_suffix": str(call_id)[-8:] if call_id else None,
                    "join_url_received": bool(join_url),
                    "join_url_host": parsed.netloc if parsed and parsed.netloc else None,
                    "provider_error": None,
                },
                str(join_url) if join_url else None,
                str(call_id) if call_id else None,
            )
    except urllib.error.HTTPError as error:
        return (
            {
                "api_call_made": True,
                "http_status": error.code,
                "latency_ms": elapsed_ms(start),
                "call_id_suffix": None,
                "join_url_received": False,
                "join_url_host": None,
                "provider_error": sanitize_for_evidence(read_error_body(error) or str(error)),
            },
            None,
            None,
        )
    except Exception as error:
        return (
            {
                "api_call_made": True,
                "http_status": None,
                "latency_ms": elapsed_ms(start),
                "call_id_suffix": None,
                "join_url_received": False,
                "join_url_host": None,
                "provider_error": sanitize_for_evidence(error),
            },
            None,
            None,
        )


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
        with urllib.request.urlopen(request, timeout=10) as response:
            return {
                "delete_api_call_made": True,
                "delete_http_status": response.status,
                "delete_latency_ms": elapsed_ms(start),
                "deleted": 200 <= response.status < 300,
            }
    except Exception as error:
        return {
            "delete_api_call_made": True,
            "delete_http_status": getattr(error, "code", None),
            "delete_latency_ms": elapsed_ms(start),
            "deleted": False,
            "delete_error": sanitize_for_evidence(error),
        }


def send_tool_result(ws: Any, invocation_type: str, invocation_id: str, status: int, response: dict[str, Any]) -> bool:
    result_type = "data_connection_tool_result" if invocation_type == "data_connection_tool_invocation" else "client_tool_result"
    if status == 200:
        message = {
            "type": result_type,
            "invocationId": invocation_id,
            "result": json.dumps(response, ensure_ascii=False),
            "responseType": "tool-response",
            "agentReaction": "speaks",
            "errorType": None,
            "errorMessage": None,
        }
    else:
        message = {
            "type": result_type,
            "invocationId": invocation_id,
            "responseType": "tool-response",
            "agentReaction": "listens",
            "errorType": "implementation-error",
            "errorMessage": "Project tool request failed in synthetic audio sandbox.",
        }
    ws.send(json.dumps(message, ensure_ascii=False))
    return True


def mark_first_latency(result: dict[str, Any], key: str, origin: float | None) -> None:
    if origin is not None and result.get(key) is None:
        result[key] = round(time.perf_counter() - origin, 3)


def mark_turn_progress(result: dict[str, Any], payload: dict[str, Any], *, turn_origin: float | None) -> None:
    role = str(payload.get("role") or "").lower()
    text = sanitize_for_evidence(payload.get("text") or payload.get("delta") or "")
    if not text:
        return
    if role in {"user", "agent"}:
        mark_first_latency(result, "first_transcript_latency_seconds", turn_origin)
    for turn in result["synthetic_audio_turns_status"]:
        if role == "user" and turn.get("sent") and not turn.get("user_transcript_observed"):
            turn["user_transcript_observed"] = True
        if role == "agent" and turn.get("sent"):
            turn["agent_response_observed_after_send"] = True


def handle_data_message(ws: Any, message: str, result: dict[str, Any], local_url: str, token: str, *, turn_origin: float | None) -> None:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        result["non_json_message_count"] += 1
        return
    if not isinstance(payload, dict):
        result["non_object_message_count"] += 1
        return
    message_type = normalize_type(payload.get("type"))
    if message_type:
        result["message_type_counts"][message_type] = result["message_type_counts"].get(message_type, 0) + 1
    if len(result["received_message_types_sample"]) < MAX_RECORDED_MESSAGES:
        result["received_message_types_sample"].append(message_type or "unknown")

    if message_type == "call_started":
        result["call_started_received"] = True
    elif message_type == "state":
        state = sanitize_for_evidence(payload.get("state"))
        if state:
            result["state_messages_sanitized"].append(state)
    elif message_type == "pong":
        timestamp = payload.get("timestamp")
        if isinstance(timestamp, (int, float)):
            result["latency_metrics"]["ping_round_trip_ms"] = round((time.time() - float(timestamp)) * 1000, 3)
    elif message_type == "transcript":
        role = str(payload.get("role") or "").lower()
        text = sanitize_for_evidence(payload.get("text") or payload.get("delta") or "")
        final = payload.get("final") is True
        if role == "agent":
            result["agent_transcript_count"] += 1
            if text:
                result["agent_response_texts_sanitized"].append(text)
        elif role == "user":
            result["user_transcript_count"] += 1
        mark_turn_progress(result, payload, turn_origin=turn_origin)
        if final and text:
            result["final_transcripts_sanitized"].append(
                {
                    "role": role or "unknown",
                    "medium": sanitize_for_evidence(payload.get("medium") or ""),
                    "text": text,
                    "ordinal": payload.get("ordinal"),
                }
            )
    elif message_type in {"client_tool_invocation", "data_connection_tool_invocation"}:
        if message_type == "client_tool_invocation":
            result["client_tool_invocation_count"] += 1
        else:
            result["data_connection_tool_invocation_count"] += 1
        invocation_id = str(payload.get("invocationId") or payload.get("invocation_id") or "")
        tool_name = str(payload.get("toolName") or payload.get("tool_name") or "")
        fallback_index = max(1, result["client_tool_invocation_count"] + result["data_connection_tool_invocation_count"])
        fallback_text = result["synthetic_audio_turns"][min(fallback_index - 1, len(result["synthetic_audio_turns"]) - 1)] if result["synthetic_audio_turns"] else "What is this?"
        if tool_name and tool_name != "project_sales_brain_next_move":
            status = 400
            tool_response = {"error": "unexpected_tool_name", "tool_name": sanitize_for_evidence(tool_name)}
        else:
            tool_payload = coerce_tool_payload(payload.get("parameters"), fallback_text, fallback_index)
            status, tool_response, latency_ms = post_tool_json(local_url, tool_payload, token)
            result["latency_metrics"].setdefault("client_tool_local_call_latency_ms", []).append(latency_ms)
        if invocation_id and send_tool_result(ws, message_type, invocation_id, status, tool_response):
            result["tool_result_sent_count"] += 1
            result["tool_responses_sanitized"].append(
                {
                    "status": status,
                    "buyer_facing_response": sanitize_for_evidence(tool_response.get("buyer_facing_response", "")),
                    "verifier_status": tool_response.get("verifier_status"),
                    "side_effects_allowed": tool_response.get("side_effects_allowed"),
                }
            )


def listen_for_messages(
    ws: Any,
    seconds: float,
    result: dict[str, Any],
    local_url: str,
    token: str,
    *,
    agent_audio_parts: list[bytes],
    turn_origin: float | None,
) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            message = ws.recv()
        except Exception as error:
            error_type = type(error).__name__
            if "Timeout" in error_type:
                continue
            result["websocket_receive_errors"].append(sanitize_for_evidence(error))
            break
        if isinstance(message, bytes):
            if message:
                mark_first_latency(result, "first_agent_audio_latency_seconds", turn_origin)
                result["agent_audio_chunks_received"] += 1
                result["agent_audio_bytes_received"] += len(message)
                agent_audio_parts.append(message)
            continue
        handle_data_message(ws, str(message), result, local_url, token, turn_origin=turn_origin)


def send_audio_bytes(ws: Any, audio: bytes, sample_rate: int) -> None:
    bytes_per_second = sample_rate * 2
    chunk_size = max(2, int(bytes_per_second * AUDIO_CHUNK_MS / 1000))
    if chunk_size % 2:
        chunk_size += 1
    for offset in range(0, len(audio), chunk_size):
        chunk = audio[offset : offset + chunk_size]
        if chunk:
            ws.send_binary(chunk)
            time.sleep(min(AUDIO_CHUNK_MS / 1000.0, max(len(chunk) / float(bytes_per_second), 0.01)))
    silence = b"\x00" * int(bytes_per_second * POST_TURN_SILENCE_SECONDS)
    if silence:
        ws.send_binary(silence)


def current_provider_tool_request_count(local_server: Any, provider_event_start: int) -> int:
    events = local_server.sanitized_events[provider_event_start:]
    return len([event for event in events if event.get("event") in {"tool_request", "auth_rejected"}])


def run_websocket_audio_turns(join_url: str, result: dict[str, Any], local_url: str, token: str, config: dict[str, Any], local_server: Any, provider_event_start: int) -> None:
    if not websocket_dependency_available():
        result["run_status"] = "blocked_websocket_dependency_missing"
        result["blocker"] = "Python websocket-client package is not available locally."
        return
    ws = None
    agent_audio_parts: list[bytes] = []
    start = time.perf_counter()
    try:
        ws = websocket_client.create_connection(join_url, timeout=WEBSOCKET_CONNECT_TIMEOUT_SECONDS)  # type: ignore[union-attr]
        ws.settimeout(SOCKET_RECV_TIMEOUT_SECONDS)
        result["websocket_connected"] = True
        result["latency_metrics"]["websocket_connect_latency_ms"] = elapsed_ms(start)
        ping_timestamp = time.time()
        ws.send(json.dumps({"type": "ping", "timestamp": ping_timestamp}))
        result["ping_sent"] = True
        listen_for_messages(ws, PRE_TURN_LISTEN_SECONDS, result, local_url, token, agent_audio_parts=agent_audio_parts, turn_origin=None)

        for index, path_text in enumerate(result["input_audio_files"], start=1):
            if index > int(config["max_audio_turns"]):
                break
            path = ROOT / path_text
            audio, duration_seconds, audio_metadata = read_input_audio(path, int(config["input_sample_rate"]))
            status = result["synthetic_audio_turns_status"][index - 1]
            status["sent"] = True
            status["input_audio_duration_seconds"] = duration_seconds
            status["input_audio_metadata"] = audio_metadata
            result["synthetic_audio_turns_attempted"] += 1
            result["hosted_turns_attempted"] += 1
            turn_origin = time.perf_counter()
            before_user = result["user_transcript_count"]
            before_tool_requests = current_provider_tool_request_count(local_server, provider_event_start)
            send_audio_bytes(ws, audio, int(config["input_sample_rate"]))
            listen_for_messages(ws, PER_TURN_LISTEN_SECONDS, result, local_url, token, agent_audio_parts=agent_audio_parts, turn_origin=turn_origin)
            after_user = result["user_transcript_count"]
            after_tool_requests = current_provider_tool_request_count(local_server, provider_event_start)
            if after_user > before_user:
                status["user_transcript_observed"] = True
            if result["agent_audio_chunks_received"] > 0:
                status["agent_audio_observed_after_send"] = True
            if status.get("user_transcript_observed") or status.get("agent_response_observed_after_send") or status.get("agent_audio_observed_after_send"):
                status["completed"] = True
            if index == 1 and after_user <= before_user:
                result["run_status"] = "websocket_audio_no_user_transcript"
                result["blocker"] = "No user transcript appeared after the first synthetic audio turn; stopped to avoid wasting provider minutes."
                break
            if after_user > before_user and after_tool_requests <= before_tool_requests:
                result["run_status"] = "websocket_audio_no_tool_invocation"
                result["blocker"] = "A user transcript appeared, but no project HTTP tool endpoint request was observed after the relevant prompt."
                break
        listen_for_messages(ws, FINAL_LISTEN_SECONDS, result, local_url, token, agent_audio_parts=agent_audio_parts, turn_origin=None)
    except Exception as error:
        result["websocket_errors"].append(sanitize_for_evidence(error))
        if result["websocket_connected"]:
            result["blocker"] = "WebSocket connected, but synthetic audio exchange failed."
            result["run_status"] = "websocket_audio_exchange_failed"
        else:
            result["blocker"] = "Could not join Ultravox session via returned joinUrl."
            result["run_status"] = "websocket_connect_failed"
    finally:
        if agent_audio_parts:
            metadata = write_agent_audio_output(b"".join(agent_audio_parts), int(config["output_sample_rate"]))
            if metadata:
                result["agent_audio_files_written_under_local_artifacts"].append(metadata["path"])
                result["agent_audio_hashes"].append(metadata["sha256"])
                result["output_audio_duration_seconds"] = metadata["duration_seconds"]
                result["agent_audio_file_metadata"].append(metadata)
        if ws is not None:
            try:
                ws.close()
                result["websocket_closed"] = True
            except Exception as error:
                result["websocket_close_error"] = sanitize_for_evidence(error)


def base_result(env_metadata: dict[str, bool], gates: dict[str, bool], config: dict[str, Any], input_result: dict[str, Any]) -> dict[str, Any]:
    turns = list(config["synthetic_audio_turns"])[: int(config["max_audio_turns"])]
    input_paths = list(input_result.get("output_paths", []))[: int(config["max_audio_turns"])]
    return {
        "evaluation_id": "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001",
        "phase": "4J5",
        "phase_detail": "4J5",
        "run_status": "not_run",
        "blocker": None,
        "env_file_exists": env_metadata["env_file_exists"],
        "env_file_ignored": env_metadata["env_file_ignored_by_git"],
        "env_file_loaded": env_metadata["env_file_loaded"],
        "api_key_present": env_metadata["api_key_present"],
        "tool_token_present": bool(os.environ.get(TOOL_TOKEN_ENV)),
        "env_gates": gates,
        "websocket_dependency_available": websocket_dependency_available(),
        "audio_input_generation_succeeded": input_result.get("generation_succeeded") is True,
        "audio_input_result_path": rel(AUDIO_INPUT_RESULT_PATH),
        "input_audio_files": input_paths,
        "local_endpoint_host": config["local_endpoint_host"],
        "local_endpoint_port": int(config["local_endpoint_port"]),
        "local_endpoint_path": config["local_endpoint_path"],
        "websocket_mode": config["websocket_mode"],
        "input_sample_rate": int(config["input_sample_rate"]),
        "output_sample_rate": int(config["output_sample_rate"]),
        "input_audio_format": config["input_audio_format"],
        "output_audio_expected": bool(config["output_audio_expected"]),
        "max_hosted_sessions": int(config["max_hosted_sessions"]),
        "max_audio_turns": int(config["max_audio_turns"]),
        "synthetic_audio_only": bool(config["synthetic_audio_only"]),
        "synthetic_audio_turns": turns,
        "synthetic_audio_turns_status": [
            {
                "turn_index": index,
                "text": text,
                "sent": False,
                "completed": False,
                "user_transcript_observed": False,
                "agent_response_observed_after_send": False,
                "agent_audio_observed_after_send": False,
            }
            for index, text in enumerate(turns, start=1)
        ],
        "expected_tool_responses_sanitized": expected_tool_responses(turns),
        "selected_tunnel_tool": None,
        "selected_preferred_tool": None,
        "selected_tunnel_executable": None,
        "ngrok_available": False,
        "ngrok_version_ok": False,
        "ngrok_version": None,
        "ngrok_path_source": None,
        "ngrok_config_check_attempted": False,
        "ngrok_config_check_succeeded": False,
        "ngrok_config_path": None,
        "ngrok_auth_configured": "unknown",
        "cloudflared_available": False,
        "cloudflared_dns_failed_before": False,
        "explicit_cloudflared_path_present": False,
        "explicit_cloudflared_path_exists": False,
        "explicit_cloudflared_version_ok": False,
        "local_server_started": False,
        "tunnel_attempted": False,
        "tunnel_tool_used": None,
        "tunnel_url_created": False,
        "tunnel_domain_only": None,
        "tunnel_url_full_recorded": False,
        "dns_success": False,
        "dns_attempt_count": 0,
        "http_success": False,
        "http_attempt_count": 0,
        "auth_preflight_success": False,
        "valid_request_success": False,
        "missing_token_401": False,
        "invalid_token_401": False,
        "public_endpoint_preflight_passed": False,
        "local_public_endpoint_test_passed": False,
        "provider_call_gate_passed": False,
        "provider_call_attempted": False,
        "provider_call_made": False,
        "sandbox_run": False,
        "session_created": False,
        "ultravox_session_created": False,
        "join_url_received": False,
        "join_url_host": None,
        "join_url_full_recorded": False,
        "websocket_connected": False,
        "websocket_closed": False,
        "ping_sent": False,
        "call_started_received": False,
        "synthetic_audio_turns_attempted": 0,
        "synthetic_audio_turns_completed": 0,
        "hosted_turns_attempted": 0,
        "client_tool_invocation_count": 0,
        "data_connection_tool_invocation_count": 0,
        "local_http_tool_request_count": 0,
        "http_tool_endpoint_request_count": 0,
        "provider_tool_success_event_count": 0,
        "tool_result_sent_count": 0,
        "tool_call_attempted": False,
        "tool_call_succeeded": False,
        "tool_boundary_enforced": False,
        "agent_transcript_count": 0,
        "user_transcript_count": 0,
        "agent_audio_chunks_received": 0,
        "agent_audio_bytes_received": 0,
        "agent_audio_files_written_under_local_artifacts": [],
        "agent_audio_hashes": [],
        "agent_audio_file_metadata": [],
        "output_audio_duration_seconds": None,
        "first_agent_audio_latency_seconds": None,
        "first_transcript_latency_seconds": None,
        "final_transcripts_sanitized": [],
        "agent_response_texts_sanitized": [],
        "tool_responses_sanitized": [],
        "product_truth_drift_count": 0,
        "unsupported_claim_count": 0,
        "fake_side_effect_count": 0,
        "crm_email_calendar_claim_count": 0,
        "internal_label_leak_count": 0,
        "source_boundary_violation_count": 0,
        "memory_conflict_count": 0,
        "message_type_counts": {},
        "received_message_types_sample": [],
        "state_messages_sanitized": [],
        "non_json_message_count": 0,
        "non_object_message_count": 0,
        "websocket_errors": [],
        "websocket_receive_errors": [],
        "latency_metrics": {},
        "create_call": {"api_call_made": False},
        "delete_call": {"delete_api_call_made": False},
        "public_endpoint_test": {},
        "tunnel_start_details": {},
        "tunnel_stop_result": {"attempted": False, "terminated": False, "killed": False},
        "audio_sandbox_success_claimed": False,
        "source_grounding": [
            {
                "url": "https://docs.ultravox.ai/apps/websockets",
                "claim": "WebSocket calls use medium.serverWebSocket, 48000 Hz sample rates, and a returned joinUrl for server-to-server use.",
            },
            {
                "url": "https://docs.ultravox.ai/apps/datamessages",
                "claim": "Data messages include transcripts, state messages, call events, and tool invocation/result messages.",
            },
            {
                "url": "https://docs.ultravox.ai/tools/custom/http-vs-client-tools",
                "claim": "HTTP tools run on the project server and keep sales logic outside Ultravox.",
            },
        ],
        "project_sales_brain_owner": "project_runtime",
        "canonical_memory_owner": "project_runtime",
        "ultravox_product_truth_owner": False,
        **boundary_fields(),
    }


def finalize_counts(result: dict[str, Any], local_server: Any | None, provider_event_start: int) -> None:
    provider_events = []
    if local_server is not None:
        provider_events = local_server.sanitized_events[provider_event_start:]
    http_events = [event for event in provider_events if event.get("event") in {"tool_request", "auth_rejected"}]
    success_events = [event for event in provider_events if event.get("event") == "tool_request" and event.get("status") == 200]
    result["local_http_tool_request_count"] = len(http_events)
    result["http_tool_endpoint_request_count"] = len(http_events)
    result["provider_tool_success_event_count"] = len(success_events)
    result["synthetic_audio_turns_completed"] = len([turn for turn in result["synthetic_audio_turns_status"] if turn.get("completed")])
    flags = count_quality_flags(result["agent_response_texts_sanitized"])
    result.update(flags)
    result["tool_call_attempted"] = (
        result["client_tool_invocation_count"]
        + result["data_connection_tool_invocation_count"]
        + result["local_http_tool_request_count"]
    ) > 0
    result["tool_call_succeeded"] = result["provider_tool_success_event_count"] > 0 or result["tool_result_sent_count"] > 0
    result["tool_boundary_enforced"] = (
        result["tool_call_succeeded"]
        and result["product_truth_drift_count"] == 0
        and result["fake_side_effect_count"] == 0
        and result["internal_label_leak_count"] == 0
    )
    result["audio_sandbox_success_claimed"] = result["user_transcript_count"] > 0 or result["agent_audio_chunks_received"] > 0
    if result["blocker"]:
        return
    if result["websocket_connected"] and result["user_transcript_count"] == 0 and result["synthetic_audio_turns_attempted"] > 0:
        result["run_status"] = "websocket_audio_no_user_transcript"
        result["blocker"] = "Synthetic audio was sent, but no user transcript was observed."
    elif result["websocket_connected"] and result["user_transcript_count"] > 0 and not result["tool_call_attempted"]:
        result["run_status"] = "websocket_audio_no_tool_invocation"
        result["blocker"] = "Synthetic audio produced a user transcript, but no project tool call was observed."
    elif result["websocket_connected"] and result["tool_call_succeeded"] and result["agent_audio_chunks_received"] > 0:
        result["run_status"] = "websocket_audio_tool_boundary_agent_audio_observed"
    elif result["websocket_connected"] and result["tool_call_succeeded"]:
        result["run_status"] = "websocket_audio_tool_boundary_no_agent_audio"
        result["blocker"] = "Project tool call worked, but no binary agent audio was observed."
    elif result["ultravox_session_created"] and not result["websocket_connected"]:
        result["run_status"] = "websocket_connect_failed"
        result["blocker"] = "Provider session was created, but the WebSocket join failed before synthetic audio turns."
    elif result["provider_call_made"] and not result["ultravox_session_created"]:
        result["run_status"] = "provider_create_failed"
        result["blocker"] = "Provider create-call request failed before WebSocket join."


def build_result() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    input_result = read_or_generate_audio_inputs()
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
    result = base_result(env_metadata, gates, config, input_result)
    if unsafe_secret_file:
        result["run_status"] = "unsafe_secret_file"
        result["blocker"] = "runtime/config/local/ultravox.env exists but is not ignored by Git; script refused to read it."
        return result
    if input_result.get("generation_succeeded") is not True:
        result["run_status"] = "blocked_synthetic_audio_generation_failed"
        result["blocker"] = input_result.get("blocker") or "Synthetic audio input generation did not succeed."
        return result
    for path_text in result["input_audio_files"]:
        path = ROOT / path_text
        if not path.is_file():
            result["run_status"] = "blocked_synthetic_audio_missing"
            result["blocker"] = f"Synthetic input audio is missing: {path_text}"
            return result
    if not websocket_dependency_available():
        result["run_status"] = "blocked_websocket_dependency_missing"
        result["blocker"] = "Python websocket-client package is not available locally."
        return result
    discovery = discover_tunnel_tools()
    add_tunnel_discovery(result, discovery)
    if discovery.get("selected_preferred_tool") != "ngrok" and config.get("use_ngrok_tunnel") is True:
        result["run_status"] = "blocked_ngrok_not_selected"
        result["blocker"] = "Config requires ngrok for this sandbox, but ngrok was not selected."
        return result
    if not tunnel_gates_enabled(gates):
        result["run_status"] = "not_run_tunnel_gates_disabled"
        result["blocker"] = "Temporary public tool tunnel gates were not fully enabled; tunnel skipped."
        return result
    if not provider_gates_enabled(gates):
        result["run_status"] = "not_run_provider_gates_disabled"
        result["blocker"] = "Provider gates were not fully enabled; tunnel skipped to avoid public exposure without a provider test."
        return result
    if result["ngrok_auth_configured"] is False:
        result["run_status"] = "blocked_ngrok_auth_missing"
        result["blocker"] = "Ngrok is installed, but auth/config is missing or invalid; no tunnel or provider call attempted."
        return result

    token = os.environ[TOOL_TOKEN_ENV]
    local_server = None
    local_thread: threading.Thread | None = None
    tunnel_process = None
    cleanup_id = None
    provider_event_start = 0
    try:
        try:
            local_server = build_server(
                host=str(config["local_endpoint_host"]),
                port=int(config["local_endpoint_port"]),
                auth_token=token,
            )
            local_thread = threading.Thread(target=local_server.serve_forever, daemon=True)
            local_thread.start()
            time.sleep(0.1)
            result["local_server_started"] = True
        except Exception as error:
            result["run_status"] = "blocked_local_server_start_failed"
            result["blocker"] = sanitize_for_evidence(error)
            return result

        tunnel_tool = discovery["selected_tunnel_tool"]
        tunnel_executable = discovery["selected_tunnel_executable_for_run"]
        if not tunnel_tool or not tunnel_executable:
            result["run_status"] = "blocked_no_tunnel_tool"
            result["blocker"] = "No already-installed supported tunnel CLI found for WebSocket audio sandbox."
            return result
        result["tunnel_attempted"] = True
        result["tunnel_tool_used"] = tunnel_tool
        result["selected_tunnel_executable"] = tunnel_executable
        tunnel_process, public_url, tunnel_details = start_tunnel(tunnel_tool, tunnel_executable, int(config["local_endpoint_port"]))
        result["tunnel_start_details"] = tunnel_details
        result["latency_metrics"]["tunnel_start_latency_ms"] = tunnel_details.get("start_latency_ms")
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
        result["tunnel_domain_only"] = parsed.netloc
        result["tunnel_url_full_recorded"] = False

        dns_result = wait_for_dns_ready(parsed.netloc)
        result.update(dns_result)
        if not dns_result["dns_success"]:
            result["run_status"] = "blocked_tunnel_dns_failed"
            result["blocker"] = "Tunnel URL was created, but DNS readiness did not succeed before provider call."
            return result

        http_result = wait_for_http_ready(public_url, str(config["local_endpoint_path"]), token)
        result.update({key: value for key, value in http_result.items() if key != "http_attempts"})
        if not http_result["http_success"]:
            result["run_status"] = "blocked_tunnel_http_failed"
            result["blocker"] = "Tunnel DNS resolved, but HTTP readiness did not succeed before provider call."
            return result

        auth_result = auth_preflight(public_url, str(config["local_endpoint_path"]), token)
        result["public_endpoint_test"] = auth_result
        result["auth_preflight_success"] = auth_result["auth_preflight_success"]
        result["valid_request_success"] = auth_result["valid_request_success"]
        result["missing_token_401"] = auth_result["missing_token_401"]
        result["invalid_token_401"] = auth_result["invalid_token_401"]
        result["public_endpoint_preflight_passed"] = auth_result["passed"]
        result["local_public_endpoint_test_passed"] = auth_result["passed"]
        result["latency_metrics"]["public_endpoint_valid_request_latency_ms"] = auth_result.get("valid_request_latency_ms")
        if not auth_result["passed"]:
            result["run_status"] = "blocked_tunnel_auth_failed"
            result["blocker"] = "Tunnel HTTP readiness passed, but auth preflight failed before provider call."
            return result
        result["provider_call_gate_passed"] = True

        provider_event_start = len(local_server.sanitized_events)
        tool_url = public_url.rstrip("/") + str(config["local_endpoint_path"])
        local_url = f"http://{config['local_endpoint_host']}:{int(config['local_endpoint_port'])}{config['local_endpoint_path']}"
        result["provider_call_attempted"] = True
        create_call, join_url, cleanup_id = create_provider_call(tool_url, os.environ[API_KEY_ENV], token, config)
        result["provider_call_made"] = create_call["api_call_made"]
        result["create_call"] = create_call
        result["join_url_received"] = create_call.get("join_url_received") is True
        result["join_url_host"] = create_call.get("join_url_host")
        result["latency_metrics"]["create_call_latency_ms"] = create_call.get("latency_ms")
        if create_call.get("http_status") is not None and 200 <= int(create_call["http_status"]) < 300 and join_url:
            result["sandbox_run"] = True
            result["session_created"] = True
            result["ultravox_session_created"] = True
            run_websocket_audio_turns(join_url, result, local_url, token, config, local_server, provider_event_start)
        else:
            result["run_status"] = "provider_create_failed"
            result["blocker"] = "Provider create-call request failed before WebSocket join."
        return result
    finally:
        if cleanup_id:
            delete_call = delete_provider_call(cleanup_id, os.environ.get(API_KEY_ENV, ""))
            result["delete_call"] = delete_call
            result["latency_metrics"]["delete_call_latency_ms"] = delete_call.get("delete_latency_ms")
        result["tunnel_stop_result"] = stop_process(tunnel_process)
        if local_server is not None:
            finalize_counts(result, local_server, provider_event_start)
            local_server.shutdown()
            local_server.server_close()
        if local_thread is not None:
            local_thread.join(timeout=5)


def recommendation_for(result: dict[str, Any]) -> str:
    if result.get("audio_input_generation_succeeded") is not True:
        return "prepare local synthetic audio inputs manually"
    if result.get("websocket_connected") and result.get("user_transcript_count", 0) == 0 and result.get("synthetic_audio_turns_attempted", 0) > 0:
        return "fix audio format/chunking/sample rate"
    if result.get("user_transcript_count", 0) > 0 and not result.get("tool_call_attempted"):
        return "fix prompt/tool declaration for audio mode"
    if result.get("tool_boundary_enforced") and result.get("agent_audio_chunks_received", 0) > 0 and result.get("product_truth_drift_count", 0) == 0 and result.get("fake_side_effect_count", 0) == 0:
        return "manual listening review of agent audio next"
    if result.get("tool_call_attempted") and not result.get("tool_boundary_enforced"):
        return "do not proceed"
    if result.get("provider_call_made") and not result.get("session_created"):
        return "fix API/session payload"
    if result.get("run_status") and str(result["run_status"]).startswith("not_run"):
        return "provide gated sandbox env values and rerun"
    return "keep Ultravox as research only"


def build_interim_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
        "phase": "4J5",
        "recommendation": recommendation_for(result),
        "blocker": result.get("blocker"),
        "websocket_audio_sandbox_run_status": result.get("run_status"),
        "websocket_audio_quality_blocker_classification": None,
        "sandbox_run": result.get("sandbox_run"),
        "provider_call_made": result.get("provider_call_made"),
        "provider_call_attempted": result.get("provider_call_attempted"),
        "ultravox_session_created": result.get("session_created"),
        "session_created": result.get("session_created"),
        "join_url_received": result.get("join_url_received"),
        "websocket_connected": result.get("websocket_connected"),
        "synthetic_audio_generation_succeeded": result.get("audio_input_generation_succeeded"),
        "synthetic_audio_turns_attempted": result.get("synthetic_audio_turns_attempted"),
        "synthetic_audio_turns_completed": result.get("synthetic_audio_turns_completed"),
        "user_transcript_count": result.get("user_transcript_count"),
        "agent_transcript_count": result.get("agent_transcript_count"),
        "agent_audio_chunks_received": result.get("agent_audio_chunks_received"),
        "agent_audio_bytes_received": result.get("agent_audio_bytes_received"),
        "local_http_tool_request_count": result.get("local_http_tool_request_count"),
        "tool_call_attempted": result.get("tool_call_attempted"),
        "tool_call_succeeded": result.get("tool_call_succeeded"),
        "tool_boundary_enforced": result.get("tool_boundary_enforced"),
        "project_tool_called": result.get("tool_call_attempted"),
        "response_follows_project_tool": None,
        "first_agent_audio_latency_seconds": result.get("first_agent_audio_latency_seconds"),
        "first_transcript_latency_seconds": result.get("first_transcript_latency_seconds"),
        "product_truth_drift_count": result.get("product_truth_drift_count"),
        "unsupported_claim_count": result.get("unsupported_claim_count"),
        "fake_side_effect_count": result.get("fake_side_effect_count"),
        "crm_email_calendar_claim_count": result.get("crm_email_calendar_claim_count"),
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
            "If synthetic audio generation fails: prepare local synthetic audio inputs manually.",
            "If WebSocket connects but no user transcript appears: fix audio format/chunking/sample rate.",
            "If user transcript appears but the tool call does not: fix prompt/tool declaration for audio mode.",
            "If tool call works and agent audio returns: run manual listening review of agent audio next.",
            "If tool boundary works and quality seems promising: limited synthetic voice conversation evaluation can be considered next.",
            "If boundary fails: do not proceed.",
            "Always keep live wiring, production calls, and real customer data disallowed.",
        ],
    }


def render_result_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001",
            "",
            f"Run status: `{result['run_status']}`",
            f"Blocker: `{result['blocker']}`",
            "",
            "## Gates",
            f"Env file ignored: `{str(result['env_file_ignored']).lower()}`",
            f"API key present: `{str(result['api_key_present']).lower()}`",
            f"Tool token present: `{str(result['tool_token_present']).lower()}`",
            f"Synthetic audio generated: `{str(result['audio_input_generation_succeeded']).lower()}`",
            f"Public endpoint preflight passed: `{str(result['public_endpoint_preflight_passed']).lower()}`",
            "",
            "## Hosted Session",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(result['session_created']).lower()}`",
            f"Join URL received: `{str(result['join_url_received']).lower()}`",
            f"WebSocket connected: `{str(result['websocket_connected']).lower()}`",
            f"Audio turns attempted: `{result['synthetic_audio_turns_attempted']}`",
            f"Audio turns completed: `{result['synthetic_audio_turns_completed']}`",
            "",
            "## Audio And Transcript",
            f"User transcript count: `{result['user_transcript_count']}`",
            f"Agent transcript count: `{result['agent_transcript_count']}`",
            f"Agent audio chunks received: `{result['agent_audio_chunks_received']}`",
            f"Agent audio bytes received: `{result['agent_audio_bytes_received']}`",
            f"Output audio duration seconds: `{result['output_audio_duration_seconds']}`",
            f"First agent audio latency seconds: `{result['first_agent_audio_latency_seconds']}`",
            f"First transcript latency seconds: `{result['first_transcript_latency_seconds']}`",
            "",
            "## Tool Boundary",
            f"Local HTTP tool request count: `{result['local_http_tool_request_count']}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Unsupported claim count: `{result['unsupported_claim_count']}`",
            f"Fake side effect count: `{result['fake_side_effect_count']}`",
            f"CRM/email/calendar claim count: `{result['crm_email_calendar_claim_count']}`",
            "",
            "## Boundaries",
            f"Agent audio files written under local_artifacts: `{result['agent_audio_files_written_under_local_artifacts']}`",
            f"Raw audio stored public: `{str(result['raw_audio_stored_public']).lower()}`",
            f"Audio committed: `{str(result['audio_committed']).lower()}`",
            f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(result['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(result['response_text_changed']).lower()}`",
            "",
            f"Decision recommendation: `{recommendation_for(result)}`",
            "",
        ]
    )


def render_interim_decision_report(decision: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-HOSTED-FEASIBILITY-DECISION-001",
            "",
            f"Recommendation: `{decision['recommendation']}`",
            f"Blocker: `{decision['blocker']}`",
            f"WebSocket audio sandbox run status: `{decision['websocket_audio_sandbox_run_status']}`",
            f"WebSocket audio quality blocker classification: `{decision['websocket_audio_quality_blocker_classification']}`",
            f"Provider call made: `{str(decision['provider_call_made']).lower()}`",
            f"Ultravox session created: `{str(decision['ultravox_session_created']).lower()}`",
            f"Join URL received: `{str(decision['join_url_received']).lower()}`",
            f"WebSocket connected: `{str(decision['websocket_connected']).lower()}`",
            f"Synthetic audio generation succeeded: `{str(decision['synthetic_audio_generation_succeeded']).lower()}`",
            f"Synthetic audio turns attempted: `{decision['synthetic_audio_turns_attempted']}`",
            f"Synthetic audio turns completed: `{decision['synthetic_audio_turns_completed']}`",
            f"User transcript count: `{decision['user_transcript_count']}`",
            f"Agent transcript count: `{decision['agent_transcript_count']}`",
            f"Agent audio chunks received: `{decision['agent_audio_chunks_received']}`",
            f"Agent audio bytes received: `{decision['agent_audio_bytes_received']}`",
            f"Tool call attempted: `{str(decision['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(decision['tool_call_succeeded']).lower()}`",
            f"Tool boundary enforced: `{str(decision['tool_boundary_enforced']).lower()}`",
            f"Project tool called: `{str(decision['project_tool_called']).lower()}`",
            f"Response follows project tool: `{decision['response_follows_project_tool']}`",
            f"Local HTTP tool request count: `{decision['local_http_tool_request_count']}`",
            f"Product truth drift count: `{decision['product_truth_drift_count']}`",
            f"Fake side effect count: `{decision['fake_side_effect_count']}`",
            f"Live wiring allowed: `{str(decision['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(decision['production_call_allowed']).lower()}`",
            f"Real customer data allowed: `{str(decision['real_customer_data_allowed']).lower()}`",
            "",
            "Project runtime owns canonical memory.",
            "Project runtime owns the sales brain and campaign truth.",
            "",
        ]
    )


def main() -> None:
    result = build_result()
    decision = build_interim_decision(result)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_result_report(result))
    write_json(DECISION_RESULT_PATH, decision)
    write_text(DECISION_REPORT_PATH, render_interim_decision_report(decision))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
