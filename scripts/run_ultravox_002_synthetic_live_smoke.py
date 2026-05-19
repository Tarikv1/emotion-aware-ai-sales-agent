#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "ultravox-002-synthetic-live-smoke.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-002" / "ULTRAVOX-002-synthetic-live-smoke.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-002" / "ULTRAVOX-002-synthetic-live-smoke-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-002" / "audio"
DEFAULT_ENV_FILE = ROOT / "runtime" / "config" / "local" / "ultravox.env"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def resolve_project_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def project_relative_string(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def maybe_remove(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


def load_env_file(path: Path, *, force_key_missing: bool) -> dict[str, str]:
    loaded: dict[str, str] = {}
    if force_key_missing or not path.exists():
        return loaded
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and value and os.environ.get(key) is None:
            os.environ[key] = value
            loaded[key] = value
    return loaded


def redact_secret_text(text: str | None) -> str | None:
    if text is None:
        return None
    return SECRET_PATTERN.sub("<redacted-secret>", text)


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        raw = error.read(4096)
    except Exception:
        raw = b""
    text = raw.decode("utf-8", errors="replace").strip()
    return redact_secret_text(" ".join(text.split())[:800]) or ""


def redacted_create_call_preview(provider: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    body = {
        "model": provider["model"],
        "recordingEnabled": False,
        "firstSpeaker": "FIRST_SPEAKER_AGENT",
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": provider["input_sample_rate"],
                "outputSampleRate": provider["output_sample_rate"],
                "clientBufferSizeMs": provider["client_buffer_size_ms"],
                "dataMessages": {
                    "callStarted": True,
                    "transcript": True,
                    "callEvent": True,
                    "debug": False,
                },
            }
        },
        "maxDuration": f"{case['max_duration_seconds']}s",
        "systemPrompt": case["system_prompt"],
        "firstSpeakerSettings": {
            "agent": {
                "text": case["agent_first_text"],
                "delay": "0s",
                "uninterruptible": False,
            }
        },
    }
    voice_value = resolve_voice_value(provider)
    if voice_value:
        body["voice"] = f"<redacted-env:{provider['voice_env_var']}>"
    return {
        "method": "POST",
        "url": provider["create_call_url"],
        "headers": {
            "X-API-Key": "<redacted>",
            "Content-Type": "application/json",
        },
        "body": body,
    }


def live_create_call_body(provider: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    body = redacted_create_call_preview(provider, case)["body"]
    voice_value = resolve_voice_value(provider)
    if voice_value:
        body["voice"] = voice_value
    else:
        body.pop("voice", None)
    body["metadata"] = {
        "project": "emotion-aware-ai-sales-agent",
        "milestone": "ULTRAVOX-002",
        "synthetic": "true",
        "customerAudio": "false",
    }
    return body


def resolve_voice_value(provider: dict[str, Any]) -> str | None:
    env_var = provider.get("voice_env_var")
    if not env_var:
        return None
    value = os.environ.get(env_var, "").strip()
    return value or None


def create_call(provider: dict[str, Any], case: dict[str, Any], api_key: str, timeout_seconds: float) -> dict[str, Any]:
    body = live_create_call_body(provider, case)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        provider["create_call_url"],
        data=data,
        method="POST",
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_body = json.loads(response.read().decode("utf-8"))
            return {
                "api_call_made": True,
                "http_status": response.status,
                "latency_ms": elapsed_ms(start),
                "call_id": response_body.get("callId") or response_body.get("call_id") or response_body.get("id"),
                "join_url": response_body.get("joinUrl") or response_body.get("join_url"),
                "provider_error": None,
            }
    except urllib.error.HTTPError as error:
        return {
            "api_call_made": True,
            "http_status": error.code,
            "latency_ms": elapsed_ms(start),
            "call_id": None,
            "join_url": None,
            "provider_error": read_error_body(error),
        }
    except Exception as error:
        return {
            "api_call_made": True,
            "http_status": None,
            "latency_ms": elapsed_ms(start),
            "call_id": None,
            "join_url": None,
            "provider_error": redact_secret_text(str(error).splitlines()[0][:800]),
        }


def delete_call(
    provider: dict[str, Any],
    call_id: str | None,
    api_key: str,
    timeout_seconds: float,
    retries: int = 4,
    sleep_seconds: float = 3.0,
) -> dict[str, Any]:
    if not call_id:
        return {
            "delete_attempted": False,
            "delete_api_call_made": False,
            "delete_attempt_count": 0,
            "delete_http_status": None,
            "delete_latency_ms": 0,
            "deleted": False,
            "delete_error": "missing-call-id",
        }
    url = provider["delete_call_url_template"].replace("{call_id}", call_id)
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            method="DELETE",
            headers={
                "X-API-Key": api_key,
            },
        )
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return {
                    "delete_attempted": True,
                    "delete_api_call_made": True,
                    "delete_attempt_count": attempt,
                    "delete_http_status": response.status,
                    "delete_latency_ms": elapsed_ms(start),
                    "deleted": 200 <= response.status < 300,
                    "delete_error": None,
                }
        except urllib.error.HTTPError as error:
            result = {
                "delete_attempted": True,
                "delete_api_call_made": True,
                "delete_attempt_count": attempt,
                "delete_http_status": error.code,
                "delete_latency_ms": elapsed_ms(start),
                "deleted": False,
                "delete_error": read_error_body(error),
            }
            if error.code != 425 or attempt == retries:
                return result
            time.sleep(sleep_seconds)
        except Exception as error:
            return {
                "delete_attempted": True,
                "delete_api_call_made": True,
                "delete_attempt_count": attempt,
                "delete_http_status": None,
                "delete_latency_ms": elapsed_ms(start),
                "deleted": False,
                "delete_error": redact_secret_text(str(error).splitlines()[0][:800]),
            }
    return {
        "delete_attempted": True,
        "delete_api_call_made": False,
        "delete_attempt_count": 0,
        "delete_http_status": None,
        "delete_latency_ms": 0,
        "deleted": False,
        "delete_error": "delete-not-attempted",
    }


def join_host(join_url: str | None) -> str | None:
    if not join_url:
        return None
    return urlparse(join_url).netloc


def call_id_suffix(call_id: str | None) -> str | None:
    if not call_id:
        return None
    return call_id[-8:]


def write_pcm_wav(audio_path: Path, audio_bytes: bytes, sample_rate: int) -> bool:
    maybe_remove(audio_path)
    if not audio_bytes:
        return False
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(audio_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_bytes)
    created = audio_path.exists() and audio_path.stat().st_size > 44
    if not created:
        maybe_remove(audio_path)
    return created


def listen_for_agent_audio(join_url: str, audio_path: Path, sample_rate: int, timeout_seconds: float) -> dict[str, Any]:
    try:
        import websocket  # type: ignore
    except Exception as error:
        return {
            "websocket_connection_attempted": False,
            "websocket_connected": False,
            "websocket_error": f"missing-websocket-client-package: {str(error).splitlines()[0][:400]}",
            "time_to_first_audio_byte_ms": None,
            "total_listen_latency_ms": 0,
            "audio_bytes_received": 0,
            "audio_file_created": False,
            "audio_output_path": None,
            "binary_message_count": 0,
            "text_message_count": 0,
            "text_event_types": [],
        }

    maybe_remove(audio_path)
    start = time.perf_counter()
    ws = None
    audio_parts: list[bytes] = []
    first_audio_ms = None
    binary_message_count = 0
    text_message_count = 0
    text_event_types: list[str] = []
    websocket_error = None
    connected = False

    try:
        ws = websocket.create_connection(join_url, timeout=timeout_seconds)
        connected = True
        deadline = time.perf_counter() + timeout_seconds
        while time.perf_counter() < deadline:
            remaining = max(0.1, min(1.0, deadline - time.perf_counter()))
            ws.settimeout(remaining)
            raw = ws.recv()
            if isinstance(raw, bytes):
                if raw:
                    if first_audio_ms is None:
                        first_audio_ms = elapsed_ms(start)
                    audio_parts.append(raw)
                    binary_message_count += 1
                    if sum(len(part) for part in audio_parts) >= sample_rate:
                        break
            else:
                text_message_count += 1
                try:
                    event = json.loads(raw)
                    event_type = event.get("type") or event.get("event") or event.get("message")
                    if event_type and event_type not in text_event_types:
                        text_event_types.append(str(event_type)[:80])
                except Exception:
                    if "non-json-text" not in text_event_types:
                        text_event_types.append("non-json-text")
    except Exception as error:
        websocket_error = redact_secret_text(str(error).splitlines()[0][:800])
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    audio_bytes = b"".join(audio_parts)
    audio_file_created = write_pcm_wav(audio_path, audio_bytes, sample_rate)
    return {
        "websocket_connection_attempted": True,
        "websocket_connected": connected,
        "websocket_error": websocket_error,
        "time_to_first_audio_byte_ms": first_audio_ms,
        "total_listen_latency_ms": elapsed_ms(start),
        "audio_bytes_received": len(audio_bytes),
        "audio_file_created": audio_file_created,
        "audio_output_path": project_relative_string(audio_path) if audio_file_created else None,
        "binary_message_count": binary_message_count,
        "text_message_count": text_message_count,
        "text_event_types": text_event_types,
    }


def fallback_result(reason: str, provider: dict[str, Any], case: dict[str, Any], timeout_seconds: float, env_file: Path) -> dict[str, Any]:
    return {
        "evaluation_milestone": "ULTRAVOX-002",
        "mode": "fallback",
        "provider": provider_summary(provider, env_file),
        "case": case_summary(case),
        "summary": {
            "live_call_requested": False,
            "approved_live_test": True,
            "create_call_api_calls_made": 0,
            "delete_call_api_calls_made": 0,
            "websocket_connections_attempted": 0,
            "audio_uploaded": False,
            "customer_audio_uploaded": False,
            "synthetic_prompt_only": True,
            "voice_cloning_used": False,
            "provider_owned_business_logic": False,
            "durable_provider_agent_created": False,
            "runtime_behavior_changed": False,
            "opens_prod_102": False,
            "audio_file_created": False,
            "fallback_used": True,
            "fallback_reason": reason,
            "timeout_seconds": timeout_seconds,
        },
        "request_preview": redacted_create_call_preview(provider, case),
        "create_call": {
            "attempted": False,
            "api_call_made": False,
            "http_status": None,
            "latency_ms": 0,
            "call_id_suffix": None,
            "join_url_received": False,
            "join_url_host": None,
            "provider_error": None,
        },
        "websocket": {
            "websocket_connection_attempted": False,
            "websocket_connected": False,
            "websocket_error": None,
            "time_to_first_audio_byte_ms": None,
            "total_listen_latency_ms": 0,
            "audio_bytes_received": 0,
            "audio_file_created": False,
            "audio_output_path": None,
            "binary_message_count": 0,
            "text_message_count": 0,
            "text_event_types": [],
        },
        "delete_call": {
            "delete_attempted": False,
            "delete_api_call_made": False,
            "delete_attempt_count": 0,
            "delete_http_status": None,
            "delete_latency_ms": 0,
            "deleted": False,
            "delete_error": None,
        },
    }


def provider_summary(provider: dict[str, Any], env_file: Path) -> dict[str, Any]:
    voice_configured = resolve_voice_value(provider) is not None
    return {
        "provider_id": provider["provider_id"],
        "endpoint_type": provider["endpoint_type"],
        "model": provider["model"],
        "voice_env_var": provider.get("voice_env_var"),
        "voice_value_logged": False,
        "voice_configured": voice_configured,
        "voice_selection": "env-voice-id-or-name" if voice_configured else "ultravox-default",
        "api_key_env_var": provider["api_key_env_var"],
        "env_file": project_relative_string(env_file),
        "api_key_value_logged": False,
        "join_url_value_logged": False,
        "input_sample_rate": provider["input_sample_rate"],
        "output_sample_rate": provider["output_sample_rate"],
    }


def case_summary(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "agent_first_text": case["agent_first_text"],
        "customer_transcript": case["customer_transcript"],
        "success_criteria": case["success_criteria"],
    }


def run_live_smoke(
    payload: dict[str, Any],
    env_file: Path,
    force_key_missing: bool,
    timeout_seconds: float,
    audio_dir: Path,
) -> dict[str, Any]:
    provider = payload["provider"]
    case = payload["synthetic_case"]
    loaded_env = load_env_file(env_file, force_key_missing=force_key_missing)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])

    if force_key_missing:
        return fallback_result("forced-key-missing", provider, case, timeout_seconds, env_file)
    if not api_key:
        return fallback_result("missing-ultravox-api-key", provider, case, timeout_seconds, env_file)

    create = create_call(provider, case, api_key, timeout_seconds)
    audio_path = audio_dir / "ULTRAVOX-002-agent-first-audio.wav"
    websocket_result = {
        "websocket_connection_attempted": False,
        "websocket_connected": False,
        "websocket_error": "join-url-not-received",
        "time_to_first_audio_byte_ms": None,
        "total_listen_latency_ms": 0,
        "audio_bytes_received": 0,
        "audio_file_created": False,
        "audio_output_path": None,
        "binary_message_count": 0,
        "text_message_count": 0,
        "text_event_types": [],
    }
    if create["join_url"]:
        websocket_result = listen_for_agent_audio(
            create["join_url"],
            audio_path,
            int(provider["output_sample_rate"]),
            timeout_seconds,
        )
    delete = delete_call(provider, create["call_id"], api_key, timeout_seconds)

    create_summary = {
        "attempted": True,
        "api_call_made": create["api_call_made"],
        "http_status": create["http_status"],
        "latency_ms": create["latency_ms"],
        "call_id_suffix": call_id_suffix(create["call_id"]),
        "join_url_received": bool(create["join_url"]),
        "join_url_host": join_host(create["join_url"]),
        "provider_error": create["provider_error"],
    }
    fallback_used = not (
        create_summary["http_status"] and 200 <= int(create_summary["http_status"]) < 300 and websocket_result["audio_bytes_received"] > 0
    )
    fallback_reason = None
    if fallback_used:
        if create_summary["provider_error"]:
            fallback_reason = "create-call-provider-error"
        elif not create_summary["join_url_received"]:
            fallback_reason = "missing-join-url"
        elif websocket_result["websocket_error"]:
            fallback_reason = "websocket-error"
        elif websocket_result["audio_bytes_received"] == 0:
            fallback_reason = "no-agent-audio-received"
        else:
            fallback_reason = "unknown-live-smoke-fallback"

    return {
        "evaluation_milestone": "ULTRAVOX-002",
        "mode": "live",
        "provider": provider_summary(provider, env_file),
        "case": case_summary(case),
        "summary": {
            "live_call_requested": True,
            "approved_live_test": payload["approved_live_test"]["approved_by_user"],
            "create_call_api_calls_made": 1 if create["api_call_made"] else 0,
            "delete_call_api_calls_made": 1 if delete["delete_api_call_made"] else 0,
            "websocket_connections_attempted": 1 if websocket_result["websocket_connection_attempted"] else 0,
            "audio_uploaded": False,
            "customer_audio_uploaded": False,
            "synthetic_prompt_only": True,
            "voice_cloning_used": False,
            "provider_owned_business_logic": False,
            "durable_provider_agent_created": False,
            "runtime_behavior_changed": False,
            "opens_prod_102": payload["approved_live_test"]["opens_prod_102"],
            "audio_file_created": websocket_result["audio_file_created"],
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "timeout_seconds": timeout_seconds,
        },
        "request_preview": redacted_create_call_preview(provider, case),
        "create_call": create_summary,
        "websocket": websocket_result,
        "delete_call": delete,
        "loaded_env_vars": sorted(loaded_env.keys()),
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    create = result["create_call"]
    websocket_result = result["websocket"]
    delete = result["delete_call"]
    lines = [
        "# ULTRAVOX-002 Synthetic Live Smoke Report",
        "",
        "This report was generated by `scripts/run_ultravox_002_synthetic_live_smoke.py`.",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Live call requested: `{str(summary['live_call_requested']).lower()}`",
        f"- Approved live test: `{str(summary['approved_live_test']).lower()}`",
        f"- Create-call API calls made: `{summary['create_call_api_calls_made']}`",
        f"- WebSocket connections attempted: `{summary['websocket_connections_attempted']}`",
        f"- Delete-call API calls made: `{summary['delete_call_api_calls_made']}`",
        f"- Customer audio uploaded: `{str(summary['customer_audio_uploaded']).lower()}`",
        f"- Synthetic prompt only: `{str(summary['synthetic_prompt_only']).lower()}`",
        f"- Voice cloning used: `{str(summary['voice_cloning_used']).lower()}`",
        f"- Durable provider agent created: `{str(summary['durable_provider_agent_created']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Opens PROD-102: `{str(summary['opens_prod_102']).lower()}`",
        f"- Fallback used: `{str(summary['fallback_used']).lower()}`",
        f"- Fallback reason: `{summary['fallback_reason']}`",
        "",
        "## Provider",
        "",
        f"- Provider: `{result['provider']['provider_id']}`",
        f"- Endpoint type: `{result['provider']['endpoint_type']}`",
        f"- Model: `{result['provider']['model']}`",
        f"- Voice selection: `{result['provider']['voice_selection']}`",
        f"- Voice env var: `{result['provider']['voice_env_var']}`",
        f"- Voice value logged: `{str(result['provider']['voice_value_logged']).lower()}`",
        f"- API key env var: `{result['provider']['api_key_env_var']}`",
        f"- Env file: `{result['provider']['env_file']}`",
        f"- API key value logged: `{str(result['provider']['api_key_value_logged']).lower()}`",
        f"- Join URL value logged: `{str(result['provider']['join_url_value_logged']).lower()}`",
        "",
        "## Create Call",
        "",
        f"- Attempted: `{str(create['attempted']).lower()}`",
        f"- HTTP status: `{create['http_status']}`",
        f"- Latency ms: `{create['latency_ms']}`",
        f"- Call ID suffix: `{create['call_id_suffix']}`",
        f"- Join URL received: `{str(create['join_url_received']).lower()}`",
        f"- Join URL host: `{create['join_url_host']}`",
        f"- Provider error: `{create['provider_error']}`",
        "",
        "## WebSocket",
        "",
        f"- Connection attempted: `{str(websocket_result['websocket_connection_attempted']).lower()}`",
        f"- Connected: `{str(websocket_result['websocket_connected']).lower()}`",
        f"- Time to first audio byte ms: `{websocket_result['time_to_first_audio_byte_ms']}`",
        f"- Total listen latency ms: `{websocket_result['total_listen_latency_ms']}`",
        f"- Audio bytes received: `{websocket_result['audio_bytes_received']}`",
        f"- Audio file created: `{str(websocket_result['audio_file_created']).lower()}`",
        f"- Audio output path: `{websocket_result['audio_output_path']}`",
        f"- Binary message count: `{websocket_result['binary_message_count']}`",
        f"- Text message count: `{websocket_result['text_message_count']}`",
        f"- Text event types: `{', '.join(websocket_result['text_event_types']) if websocket_result['text_event_types'] else 'none'}`",
        f"- WebSocket error: `{websocket_result['websocket_error']}`",
        "",
        "## Delete Call",
        "",
        f"- Delete attempted: `{str(delete['delete_attempted']).lower()}`",
        f"- HTTP status: `{delete['delete_http_status']}`",
        f"- Latency ms: `{delete['delete_latency_ms']}`",
        f"- Attempt count: `{delete['delete_attempt_count']}`",
        f"- Deleted: `{str(delete['deleted']).lower()}`",
        f"- Delete error: `{delete['delete_error']}`",
        "",
        "## Boundary",
        "",
        "This smoke test is agent-first. It does not upload customer audio and does not test customer speech understanding. A later test must use synthetic audio input if the goal is full speech-to-speech latency measurement.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ULTRAVOX-002 synthetic live smoke with env-only key handling.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Path to ULTRAVOX-002 case JSON.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON result.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Ignored env file containing ULTRAVOX_API_KEY.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Ignored output dir for synthetic provider audio.")
    parser.add_argument("--live", action="store_true", help="Make the approved synthetic provider call.")
    parser.add_argument("--force-key-missing", action="store_true", help="Exercise fallback without reading any key.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Bound provider and WebSocket waits.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(resolve_project_path(args.cases))
    env_file = resolve_project_path(args.env_file)
    timeout_seconds = min(max(args.timeout_seconds, 1.0), 10.0)
    if not args.live:
        result = fallback_result("dry-run-mode", payload["provider"], payload["synthetic_case"], timeout_seconds, env_file)
    else:
        result = run_live_smoke(
            payload,
            env_file=env_file,
            force_key_missing=args.force_key_missing,
            timeout_seconds=timeout_seconds,
            audio_dir=resolve_project_path(args.audio_dir),
        )

    serialized = json.dumps(result, ensure_ascii=False)
    if SECRET_PATTERN.search(serialized):
        raise SystemExit("Refusing to write result because a secret-like token appeared in output.")

    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    write_json(out_path, result)
    write_text(report_path, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
