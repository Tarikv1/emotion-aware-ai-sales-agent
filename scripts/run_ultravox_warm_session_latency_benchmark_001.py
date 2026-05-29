#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
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
from scripts.run_ultravox_websocket_audio_sandbox_001 import (  # noqa: E402
    boundary_fields,
    read_input_audio,
    read_manual_audio_inputs,
    send_audio_bytes,
)
from scripts.run_ultravox_websocket_text_sandbox_001 import (  # noqa: E402
    coerce_tool_payload,
    count_quality_flags,
    expected_tool_responses,
)


CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_warm_session_latency_config.json"
PROMPT_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_sandbox_agent_prompt.md"
MANUAL_AUDIO_INPUT_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-MANUAL-AUDIO-INPUTS-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WARM-SESSION-LATENCY-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

WEBSOCKET_CONNECT_TIMEOUT_SECONDS = 10
PRE_TURN_LISTEN_SECONDS = 1.0
PER_TURN_LISTEN_SECONDS = 12.0
FINAL_LISTEN_SECONDS = 3.0
SOCKET_RECV_TIMEOUT_SECONDS = 0.5
MAX_RECORDED_MESSAGES = 120
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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sanitize_for_evidence(value: Any) -> str:
    text = sanitize_text(str(value))
    text = SENSITIVE_URL_PATTERN.sub("<provider-url-redacted>", text)
    return text[:500]


def normalize_type(value: Any) -> str:
    raw = str(value or "")
    if not raw:
        return ""
    raw = raw.replace("-", "_")
    raw = re.sub(r"(?<!^)([A-Z])", r"_\1", raw)
    return raw.lower()


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


def build_call_body(tool_url: str, tool_token: str, config: dict[str, Any]) -> dict[str, Any]:
    base_prompt = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.is_file() else ""
    system_prompt = (
        base_prompt
        + "\n\nPhase 4J7 warm-session latency benchmark addition: this is prepared manual synthetic/non-customer local audio only, not a phone call, microphone test, CRM, email, calendar, or live runtime test. "
        "Use project_sales_brain_next_move for every product or sales answer. "
        "When the tool gives a buyer_facing_response and verifier_status is passed, speak only that safe buyer-facing response. "
        "If tool output is missing, ask a short clarification rather than inventing product facts. "
        "Keep responses short so warm-turn latency can be measured."
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
        "maxDuration": "90s",
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
            "milestone": "ULTRAVOX-WARM-SESSION-LATENCY-001",
            "synthetic": "true",
            "realCustomerData": "false",
            "outboundPhoneCall": "false",
            "audioInput": "true",
            "manualAudioInput": "true",
            "warmSessionLatencyBenchmark": "true",
            "liveWiring": "false",
        },
    }


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read(2048).decode("utf-8", errors="replace")
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
            "errorMessage": "Project tool request failed in synthetic warm-session latency benchmark.",
        }
    ws.send(json.dumps(message, ensure_ascii=False))
    return True


def mark_event_time(turn: dict[str, Any], time_key: str, latency_key: str | None, origin_perf: float | None, event_perf: float | None = None) -> None:
    if turn.get(time_key) is None:
        event_perf = event_perf if event_perf is not None else time.perf_counter()
        turn[time_key] = now_iso()
        if latency_key and origin_perf is not None:
            turn[latency_key] = round(event_perf - origin_perf, 3)


def sync_turn_tool_events(turn: dict[str, Any] | None, local_server: Any | None, send_end_perf: float | None) -> None:
    if turn is None or local_server is None:
        return
    start_index = int(turn.get("_local_event_start", 0) or 0)
    events = [
        event
        for event in local_server.sanitized_events[start_index:]
        if isinstance(event, dict) and event.get("event") in {"tool_request", "auth_rejected"}
    ]
    turn["local_http_tool_request_count"] = len(events)
    if events:
        event_perf = time.perf_counter()
        mark_event_time(turn, "first_tool_request_time", "user_turn_end_to_first_tool_request_seconds", send_end_perf, event_perf)
        if any(event.get("event") == "tool_request" for event in events):
            mark_event_time(turn, "tool_response_time", None, None, event_perf)
            if turn.get("_tool_response_perf") is None:
                turn["_tool_response_perf"] = event_perf


def handle_transcript_payload(result: dict[str, Any], turn: dict[str, Any] | None, payload: dict[str, Any], send_end_perf: float | None) -> None:
    role = str(payload.get("role") or "").lower()
    text = sanitize_for_evidence(payload.get("text") or payload.get("delta") or "")
    final = payload.get("final") is True
    if role == "agent":
        result["agent_transcript_count"] += 1
        if text:
            result["agent_response_texts_sanitized"].append(text)
            if turn is not None:
                if turn.get("user_transcript_observed") is not True and turn.get("first_tool_request_time") is None:
                    turn["pre_user_agent_transcript_texts_sanitized"].append(text)
                    return
                turn["agent_transcript_texts_sanitized"].append(text)
                turn["agent_response_observed_after_send"] = True
                mark_event_time(turn, "first_agent_transcript_time", None, None)
    elif role == "user":
        result["user_transcript_count"] += 1
        if turn is not None:
            turn["user_transcript_observed"] = True
            if text and not turn.get("transcript_text_sanitized"):
                turn["transcript_text_sanitized"] = text
            mark_event_time(turn, "first_user_transcript_time", "user_turn_end_to_first_transcript_seconds", send_end_perf)
            if final and text:
                turn["final_user_transcript_time"] = now_iso()
    if final and text:
        result["final_transcripts_sanitized"].append(
            {
                "role": role or "unknown",
                "medium": sanitize_for_evidence(payload.get("medium") or ""),
                "text": text,
                "ordinal": payload.get("ordinal"),
            }
        )


def handle_tool_invocation(ws: Any, message_type: str, result: dict[str, Any], turn: dict[str, Any] | None, payload: dict[str, Any], local_url: str, token: str, send_end_perf: float | None) -> None:
    if message_type == "client_tool_invocation":
        result["client_tool_invocation_count"] += 1
    else:
        result["data_connection_tool_invocation_count"] += 1
    invocation_id = str(payload.get("invocationId") or payload.get("invocation_id") or "")
    tool_name = str(payload.get("toolName") or payload.get("tool_name") or "")
    fallback_index = int(turn.get("turn_index", 1)) if turn is not None else max(1, result["client_tool_invocation_count"] + result["data_connection_tool_invocation_count"])
    fallback_text = str(turn.get("expected_spoken_content") or "What is this?") if turn is not None else "What is this?"
    if turn is not None:
        mark_event_time(turn, "first_tool_request_time", "user_turn_end_to_first_tool_request_seconds", send_end_perf)
    if tool_name and tool_name != "project_sales_brain_next_move":
        status = 400
        latency_ms = None
        tool_response = {"error": "unexpected_tool_name", "tool_name": sanitize_for_evidence(tool_name)}
    else:
        tool_payload = coerce_tool_payload(payload.get("parameters"), fallback_text, fallback_index)
        status, tool_response, latency_ms = post_tool_json(local_url, tool_payload, token)
        result["latency_metrics"].setdefault("client_tool_local_call_latency_ms", []).append(latency_ms)
    if turn is not None:
        mark_event_time(turn, "tool_response_time", None, None)
        turn["tool_response_status"] = status
        turn["tool_response_latency_ms"] = latency_ms
        turn["expected_tool_response_buyer_facing_response"] = sanitize_for_evidence(tool_response.get("buyer_facing_response", ""))
    if invocation_id and send_tool_result(ws, message_type, invocation_id, status, tool_response):
        result["tool_result_sent_count"] += 1
        result["tool_responses_sanitized"].append(
            {
                "turn_index": fallback_index,
                "status": status,
                "buyer_facing_response": sanitize_for_evidence(tool_response.get("buyer_facing_response", "")),
                "verifier_status": tool_response.get("verifier_status"),
                "side_effects_allowed": tool_response.get("side_effects_allowed"),
            }
        )


def handle_data_message(ws: Any, message: str, result: dict[str, Any], local_url: str, token: str, *, turn: dict[str, Any] | None, send_end_perf: float | None) -> None:
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
        handle_transcript_payload(result, turn, payload, send_end_perf)
    elif message_type in {"client_tool_invocation", "data_connection_tool_invocation"}:
        handle_tool_invocation(ws, message_type, result, turn, payload, local_url, token, send_end_perf)


def listen_for_messages(
    ws: Any,
    seconds: float,
    result: dict[str, Any],
    local_url: str,
    token: str,
    *,
    turn: dict[str, Any] | None,
    send_end_perf: float | None,
    local_server: Any | None,
) -> None:
    deadline = time.monotonic() + seconds
    sync_turn_tool_events(turn, local_server, send_end_perf)
    while time.monotonic() < deadline:
        try:
            message = ws.recv()
        except Exception as error:
            error_type = type(error).__name__
            if "Timeout" in error_type:
                sync_turn_tool_events(turn, local_server, send_end_perf)
                continue
            result["websocket_receive_errors"].append(sanitize_for_evidence(error))
            break
        if isinstance(message, bytes):
            if message:
                result["agent_audio_chunks_received"] += 1
                result["agent_audio_bytes_received"] += len(message)
                if turn is None:
                    result["pre_or_post_turn_agent_audio_chunks"] += 1
                    result["pre_or_post_turn_agent_audio_bytes"] += len(message)
                else:
                    event_perf = time.perf_counter()
                    if turn.get("user_transcript_observed") is not True and turn.get("first_tool_request_time") is None:
                        turn["pre_user_agent_audio_chunks"] += 1
                        turn["pre_user_agent_audio_bytes"] += len(message)
                        result["pre_or_post_turn_agent_audio_chunks"] += 1
                        result["pre_or_post_turn_agent_audio_bytes"] += len(message)
                        continue
                    mark_event_time(turn, "first_agent_audio_time", "user_turn_end_to_first_agent_audio_seconds", send_end_perf, event_perf)
                    if turn.get("_tool_response_perf") is not None and turn.get("tool_response_to_first_agent_audio_seconds") is None:
                        turn["tool_response_to_first_agent_audio_seconds"] = round(event_perf - float(turn["_tool_response_perf"]), 3)
                    elif turn.get("tool_response_time") and turn.get("tool_response_to_first_agent_audio_seconds") is None:
                        turn["tool_response_to_first_agent_audio_seconds"] = None
                    turn["final_agent_audio_time"] = now_iso()
                    turn["agent_audio_chunks"] += 1
                    turn["agent_audio_bytes"] += len(message)
                    turn["agent_audio_observed_after_send"] = True
            continue
        handle_data_message(ws, str(message), result, local_url, token, turn=turn, send_end_perf=send_end_perf)
        if turn is not None and turn.get("tool_response_time") and turn.get("_tool_response_perf") is None:
            turn["_tool_response_perf"] = time.perf_counter()
        sync_turn_tool_events(turn, local_server, send_end_perf)


def build_turns(config: dict[str, Any], manual_input_result: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], bool]:
    prepared_files = [item for item in manual_input_result.get("prepared_files", []) if isinstance(item, dict) and item.get("path")]
    by_case_id = {str(item.get("case_id")): item for item in prepared_files}
    sequence = list(config.get("audio_turn_sequence", []))[: int(config["max_audio_turns"])]
    turns: list[dict[str, Any]] = []
    input_paths: list[str] = []
    repeated = False
    for index, spec in enumerate(sequence, start=1):
        case_id = str(spec.get("case_id") or "")
        prepared = by_case_id.get(case_id)
        if prepared is None and prepared_files:
            prepared = prepared_files[(index - 1) % len(prepared_files)]
            repeated = index > len(prepared_files)
        if prepared is None:
            continue
        path_text = str(prepared.get("path"))
        input_paths.append(path_text)
        expected_text = str(spec.get("expected_spoken_content") or prepared.get("expected_spoken_content") or "")
        measured = index > int(config["warmup_turn_count"])
        turns.append(
            {
                "turn_index": index,
                "input_audio_case_id": str(prepared.get("case_id") or case_id),
                "expected_spoken_content": expected_text,
                "input_audio_path": path_text,
                "input_audio_duration_seconds": None,
                "input_audio_metadata": {},
                "warmup_turn": not measured,
                "measured_turn": measured,
                "send_audio_start_time": None,
                "send_audio_end_time": None,
                "first_user_transcript_time": None,
                "final_user_transcript_time": None,
                "first_tool_request_time": None,
                "tool_response_time": None,
                "first_agent_transcript_time": None,
                "first_agent_audio_time": None,
                "final_agent_audio_time": None,
                "user_turn_end_to_first_transcript_seconds": None,
                "user_turn_end_to_first_tool_request_seconds": None,
                "tool_response_to_first_agent_audio_seconds": None,
                "user_turn_end_to_first_agent_audio_seconds": None,
                "agent_audio_chunks": 0,
                "agent_audio_bytes": 0,
                "pre_user_agent_audio_chunks": 0,
                "pre_user_agent_audio_bytes": 0,
                "local_http_tool_request_count": 0,
                "transcript_text_sanitized": None,
                "agent_transcript_texts_sanitized": [],
                "pre_user_agent_transcript_texts_sanitized": [],
                "expected_tool_response_buyer_facing_response": None,
                "tool_response_status": None,
                "tool_response_latency_ms": None,
                "tool_response_followed": "unknown",
                "fake_side_effect_detected": False,
                "product_truth_drift_detected": False,
                "boundary_respected": "unknown",
                "sent": False,
                "completed": False,
                "user_transcript_observed": False,
                "agent_response_observed_after_send": False,
                "agent_audio_observed_after_send": False,
                "_local_event_start": 0,
                "_tool_response_perf": None,
            }
        )
        if index > len(prepared_files):
            repeated = True
    return turns, input_paths, repeated or len(prepared_files) < len(sequence)


def base_result(env_metadata: dict[str, bool], gates: dict[str, bool], config: dict[str, Any], manual_input_result: dict[str, Any]) -> dict[str, Any]:
    turns, input_paths, repeated = build_turns(config, manual_input_result)
    prepared_count = int(manual_input_result.get("prepared_case_count", 0) or 0)
    expected_texts = [str(turn.get("expected_spoken_content") or "") for turn in turns]
    result = {
        "evaluation_id": "ULTRAVOX-WARM-SESSION-LATENCY-001",
        "phase": "4J7",
        "benchmark_id": config["benchmark_id"],
        "run_status": "not_run",
        "blocker": None,
        "config_path": rel(CONFIG_PATH),
        "manual_audio_input_result_path": rel(MANUAL_AUDIO_INPUT_RESULT_PATH),
        "env_file_exists": env_metadata["env_file_exists"],
        "env_file_ignored": env_metadata["env_file_ignored_by_git"],
        "env_file_loaded": env_metadata["env_file_loaded"],
        "api_key_present": env_metadata["api_key_present"],
        "tool_token_present": bool(os.environ.get(TOOL_TOKEN_ENV)),
        "env_gates": gates,
        "websocket_dependency_available": websocket_dependency_available(),
        "provider_calls_allowed_by_default": bool(config["provider_calls_allowed_by_default"]),
        "existing_audio_only": bool(config["existing_audio_only"]),
        "no_new_audio_generation": bool(config["no_new_audio_generation"]),
        "no_microphone": bool(config["no_microphone"]),
        "no_outbound_phone": bool(config["no_outbound_phone"]),
        "prepared_audio_available": prepared_count >= 2 and len(turns) >= int(config["max_audio_turns"]),
        "prepared_audio_inputs_count": prepared_count,
        "manual_audio_conversion_succeeded": manual_input_result.get("conversion_succeeded") is True,
        "manual_audio_converter_used": manual_input_result.get("converter_used"),
        "input_audio_files": input_paths,
        "repeated_synthetic_inputs_used": repeated,
        "repeated_synthetic_inputs_note": config.get("repeated_synthetic_inputs_note"),
        "local_endpoint_host": config["local_endpoint_host"],
        "local_endpoint_port": int(config["local_endpoint_port"]),
        "local_endpoint_path": config["local_endpoint_path"],
        "websocket_mode": config["websocket_mode"],
        "input_sample_rate": int(config["input_sample_rate"]),
        "output_sample_rate": int(config["output_sample_rate"]),
        "input_audio_format": config["input_audio_format"],
        "max_hosted_sessions": int(config["max_hosted_sessions"]),
        "max_audio_turns": int(config["max_audio_turns"]),
        "warmup_turn_count": int(config["warmup_turn_count"]),
        "measured_turn_count_configured": int(config["measured_turn_count"]),
        "turns": turns,
        "expected_tool_responses_sanitized": expected_tool_responses(expected_texts),
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
        "audio_turns_attempted": 0,
        "audio_turns_completed": 0,
        "hosted_turns_attempted": 0,
        "measured_warm_turn_count": 0,
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
        "pre_or_post_turn_agent_audio_chunks": 0,
        "pre_or_post_turn_agent_audio_bytes": 0,
        "agent_audio_files_written_under_local_artifacts": [],
        "output_audio_duration_seconds": None,
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
        "project_sales_brain_owner": "project_runtime",
        "canonical_memory_owner": "project_runtime",
        "ultravox_product_truth_owner": False,
        "final_elevenlabs_replacement_claimed": False,
        "no_final_elevenlabs_replacement_claim": True,
        "measurement_note": "Per-turn latency uses client-observed receive times after each prepared audio send finishes; it does not store raw provider audio in public evidence.",
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
                "claim": "HTTP tools keep project sales logic outside Ultravox.",
            },
        ],
        **boundary_fields(),
    }
    result["raw_audio_stored_public"] = False
    return result


def response_followed(turn: dict[str, Any]) -> bool | str:
    expected = str(turn.get("expected_tool_response_buyer_facing_response") or "").strip().lower()
    if not expected:
        status, response = handle_request(
            {
                "session_id": "warm-session-latency-expected",
                "buyer_utterance_text": str(turn.get("expected_spoken_content") or "What is this?"),
                "ultravox_session_summary": "Synthetic warm-session latency benchmark.",
                "project_memory_summary": "Project runtime owns canonical memory, campaign truth, and side-effect boundaries.",
                "current_campaign_id": "synthetic_voice_sandbox",
                "detected_emotion_hint": "boundary_setting" if "crm" in str(turn.get("expected_spoken_content", "")).lower() else "curious",
                "turn_index": int(turn.get("turn_index", 1)),
                "requested_action_context": "contact_boundary" if "crm" in str(turn.get("expected_spoken_content", "")).lower() else "opening_orientation",
            }
        )
        if status == 200:
            expected = str(response.get("buyer_facing_response") or "").strip().lower()
            turn["expected_tool_response_buyer_facing_response"] = sanitize_for_evidence(response.get("buyer_facing_response", ""))
    actual = "\n".join(str(text) for text in turn.get("agent_transcript_texts_sanitized", [])).strip().lower()
    if not actual:
        return "unknown"
    if not expected:
        return "unknown"
    return expected in actual or actual in expected


def finalize_turns(result: dict[str, Any]) -> None:
    for turn in result["turns"]:
        flags = count_quality_flags([str(text) for text in turn.get("agent_transcript_texts_sanitized", [])])
        turn["fake_side_effect_detected"] = flags["fake_side_effect_count"] > 0
        turn["product_truth_drift_detected"] = flags["product_truth_drift_count"] > 0
        followed = response_followed(turn)
        turn["tool_response_followed"] = followed
        if turn["fake_side_effect_detected"] or turn["product_truth_drift_detected"]:
            turn["boundary_respected"] = False
        elif turn.get("local_http_tool_request_count", 0) > 0 and followed is not False:
            turn["boundary_respected"] = True
        else:
            turn["boundary_respected"] = "unknown"
        turn["completed"] = bool(turn.get("user_transcript_observed") and turn.get("agent_audio_chunks", 0) > 0)


def scrub_internal_turn_fields(result: dict[str, Any]) -> None:
    cleaned = []
    for turn in result["turns"]:
        cleaned.append({key: value for key, value in turn.items() if not key.startswith("_")})
    result["turns"] = cleaned


def finalize_counts(result: dict[str, Any], local_server: Any | None, provider_event_start: int) -> None:
    provider_events = []
    if local_server is not None:
        provider_events = local_server.sanitized_events[provider_event_start:]
    http_events = [event for event in provider_events if event.get("event") in {"tool_request", "auth_rejected"}]
    success_events = [event for event in provider_events if event.get("event") == "tool_request" and event.get("status") == 200]
    result["local_http_tool_request_count"] = len(http_events)
    result["http_tool_endpoint_request_count"] = len(http_events)
    result["provider_tool_success_event_count"] = len(success_events)
    finalize_turns(result)
    result["audio_turns_completed"] = len([turn for turn in result["turns"] if turn.get("completed")])
    result["measured_warm_turn_count"] = len(
        [
            turn
            for turn in result["turns"]
            if turn.get("measured_turn") is True and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))
        ]
    )
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
    if result["blocker"]:
        scrub_internal_turn_fields(result)
        return
    if result["websocket_connected"] and result["audio_turns_attempted"] > 0 and result["user_transcript_count"] == 0:
        result["run_status"] = "websocket_audio_no_user_transcript"
        result["blocker"] = "Manual audio was sent, but no user transcript was observed."
    elif result["websocket_connected"] and result["user_transcript_count"] > 0 and not result["tool_call_attempted"]:
        result["run_status"] = "websocket_audio_no_tool_invocation"
        result["blocker"] = "Manual audio produced a user transcript, but no project tool call was observed."
    elif result["websocket_connected"] and result["measured_warm_turn_count"] > 0:
        result["run_status"] = "warm_session_latency_measured"
    elif result["websocket_connected"]:
        result["run_status"] = "warm_session_latency_inconclusive"
        result["blocker"] = "WebSocket connected, but no measured warm turn produced agent audio."
    elif result["ultravox_session_created"] and not result["websocket_connected"]:
        result["run_status"] = "websocket_connect_failed"
        result["blocker"] = "Provider session was created, but the WebSocket join failed before manual audio turns."
    elif result["provider_call_made"] and not result["ultravox_session_created"]:
        result["run_status"] = "provider_create_failed"
        result["blocker"] = "Provider create-call request failed before WebSocket join."
    scrub_internal_turn_fields(result)


def run_websocket_audio_turns(join_url: str, result: dict[str, Any], local_url: str, token: str, config: dict[str, Any], local_server: Any, provider_event_start: int) -> None:
    if not websocket_dependency_available():
        result["run_status"] = "blocked_websocket_dependency_missing"
        result["blocker"] = "Python websocket-client package is not available locally."
        return
    ws = None
    start = time.perf_counter()
    try:
        ws = websocket_client.create_connection(join_url, timeout=WEBSOCKET_CONNECT_TIMEOUT_SECONDS)  # type: ignore[union-attr]
        ws.settimeout(SOCKET_RECV_TIMEOUT_SECONDS)
        result["websocket_connected"] = True
        result["latency_metrics"]["websocket_connect_latency_ms"] = elapsed_ms(start)
        ping_timestamp = time.time()
        ws.send(json.dumps({"type": "ping", "timestamp": ping_timestamp}))
        result["ping_sent"] = True
        listen_for_messages(ws, PRE_TURN_LISTEN_SECONDS, result, local_url, token, turn=None, send_end_perf=None, local_server=local_server)

        for turn in result["turns"]:
            if int(turn["turn_index"]) > int(config["max_audio_turns"]):
                break
            path = ROOT / str(turn["input_audio_path"])
            audio, duration_seconds, audio_metadata = read_input_audio(path, int(config["input_sample_rate"]))
            turn["_local_event_start"] = len(local_server.sanitized_events)
            turn["input_audio_duration_seconds"] = duration_seconds
            turn["input_audio_metadata"] = audio_metadata
            turn["sent"] = True
            result["audio_turns_attempted"] += 1
            result["hosted_turns_attempted"] += 1
            before_user = result["user_transcript_count"]
            turn["send_audio_start_time"] = now_iso()
            send_audio_bytes(ws, audio, int(config["input_sample_rate"]))
            send_end_perf = time.perf_counter()
            turn["send_audio_end_time"] = now_iso()
            listen_for_messages(ws, PER_TURN_LISTEN_SECONDS, result, local_url, token, turn=turn, send_end_perf=send_end_perf, local_server=local_server)
            sync_turn_tool_events(turn, local_server, send_end_perf)
            after_user = result["user_transcript_count"]
            if int(turn["turn_index"]) == 1 and after_user <= before_user:
                result["run_status"] = "websocket_audio_no_user_transcript"
                result["blocker"] = "No user transcript appeared after the first manual audio turn; stopped to avoid wasting provider minutes."
                break
            if int(turn["turn_index"]) == 1 and int(turn.get("agent_audio_chunks", 0) or 0) <= 0:
                result["run_status"] = "websocket_audio_no_agent_audio"
                result["blocker"] = "No agent audio appeared after the first manual audio turn; stopped to avoid wasting provider minutes."
                break
            if after_user > before_user and int(turn.get("local_http_tool_request_count", 0) or 0) <= 0:
                result["run_status"] = "websocket_audio_no_tool_invocation"
                result["blocker"] = "A user transcript appeared, but no project HTTP tool endpoint request was observed after the relevant prompt."
                break
        listen_for_messages(ws, FINAL_LISTEN_SECONDS, result, local_url, token, turn=None, send_end_perf=None, local_server=local_server)
    except Exception as error:
        result["websocket_errors"].append(sanitize_for_evidence(error))
        if result["websocket_connected"]:
            result["blocker"] = "WebSocket connected, but manual audio exchange failed."
            result["run_status"] = "websocket_audio_exchange_failed"
        else:
            result["blocker"] = "Could not join Ultravox session via returned joinUrl."
            result["run_status"] = "websocket_connect_failed"
    finally:
        if ws is not None:
            try:
                ws.close()
                result["websocket_closed"] = True
            except Exception as error:
                result["websocket_close_error"] = sanitize_for_evidence(error)


def build_result() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    manual_input_result = read_manual_audio_inputs()
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
    result = base_result(env_metadata, gates, config, manual_input_result)
    if unsafe_secret_file:
        result["run_status"] = "unsafe_secret_file"
        result["blocker"] = "runtime/config/local/ultravox.env exists but is not ignored by Git; script refused to read it."
        return result
    if result["prepared_audio_available"] is not True:
        result["run_status"] = "prepared_manual_audio_missing"
        result["blocker"] = "Prepared manual audio inputs are missing or incomplete."
        return result
    if not websocket_dependency_available():
        result["run_status"] = "blocked_websocket_dependency_missing"
        result["blocker"] = "Python websocket-client package is not available locally."
        return result
    for path_text in result["input_audio_files"]:
        path = ROOT / str(path_text)
        if not path.is_file():
            result["run_status"] = "prepared_manual_audio_missing"
            result["blocker"] = f"Prepared manual input audio is missing: {path_text}"
            return result

    discovery = discover_tunnel_tools()
    add_tunnel_discovery(result, discovery)
    if discovery.get("selected_preferred_tool") != "ngrok" and config.get("use_ngrok_tunnel") is True:
        result["run_status"] = "blocked_ngrok_not_selected"
        result["blocker"] = "Config requires ngrok for this benchmark, but ngrok was not selected."
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
            result["blocker"] = "No already-installed supported tunnel CLI found for warm-session benchmark."
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
        else:
            scrub_internal_turn_fields(result)
        if local_thread is not None:
            local_thread.join(timeout=5)


def warm_latencies(result: dict[str, Any]) -> list[float]:
    return [
        float(turn["user_turn_end_to_first_agent_audio_seconds"])
        for turn in result.get("turns", [])
        if isinstance(turn, dict)
        and turn.get("measured_turn") is True
        and isinstance(turn.get("user_turn_end_to_first_agent_audio_seconds"), (int, float))
    ]


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[midpoint], 3)
    return round((ordered[midpoint - 1] + ordered[midpoint]) / 2.0, 3)


def percentile_nearest(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return round(ordered[index], 3)


def recommendation_for(result: dict[str, Any]) -> str:
    if result.get("prepared_audio_available") is not True:
        return "prepare manual audio inputs"
    if result.get("session_created") is not True or result.get("websocket_connected") is not True:
        return "fix session/WebSocket before more provider usage"
    if result.get("tool_boundary_enforced") is not True:
        return "do not proceed"
    latencies = warm_latencies(result)
    p50 = median(latencies)
    if p50 is not None and p50 <= 2.0:
        return "limited synthetic voice conversation evaluation next"
    if p50 is not None and p50 <= 3.0:
        return "thesis-demo synthetic voice evaluation next"
    if p50 is not None and p50 > 5.0:
        return "keep Ultravox as architecture candidate, investigate provider settings/voice/session configuration before more usage"
    if p50 is not None:
        return "test voice/session settings and warm-run repeat once"
    return "benchmark inconclusive"


def render_report(result: dict[str, Any]) -> str:
    latencies = warm_latencies(result)
    p50 = median(latencies)
    p90 = percentile_nearest(latencies, 90.0) if len(latencies) >= 2 else None
    return "\n".join(
        [
            "# ULTRAVOX-WARM-SESSION-LATENCY-001",
            "",
            f"Run status: `{result['run_status']}`",
            f"Blocker: `{result['blocker']}`",
            "",
            "## Gates",
            f"Env file ignored: `{str(result['env_file_ignored']).lower()}`",
            f"API key present: `{str(result['api_key_present']).lower()}`",
            f"Tool token present: `{str(result['tool_token_present']).lower()}`",
            f"Prepared audio available: `{str(result['prepared_audio_available']).lower()}`",
            f"Prepared audio input count: `{result['prepared_audio_inputs_count']}`",
            f"Repeated synthetic inputs used: `{str(result['repeated_synthetic_inputs_used']).lower()}`",
            "",
            "## Hosted Session",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Session created: `{str(result['session_created']).lower()}`",
            f"WebSocket connected: `{str(result['websocket_connected']).lower()}`",
            f"Audio turns attempted: `{result['audio_turns_attempted']}`",
            f"Audio turns completed: `{result['audio_turns_completed']}`",
            f"Warm measured turn count: `{result['measured_warm_turn_count']}`",
            "",
            "## Latency",
            f"Warm p50 first-agent-audio latency seconds: `{p50}`",
            f"Warm p90 first-agent-audio latency seconds: `{p90}`",
            f"Measured warm latencies seconds: `{latencies}`",
            result["measurement_note"],
            "",
            "## Tool Boundary",
            f"Local HTTP tool request count: `{result['local_http_tool_request_count']}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Tool boundary enforced: `{str(result['tool_boundary_enforced']).lower()}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Fake side effect count: `{result['fake_side_effect_count']}`",
            f"CRM/email/calendar claim count: `{result['crm_email_calendar_claim_count']}`",
            "",
            "## Boundaries",
            f"No new audio generated: `{str(result['no_new_audio_generation']).lower()}`",
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


def main() -> None:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
