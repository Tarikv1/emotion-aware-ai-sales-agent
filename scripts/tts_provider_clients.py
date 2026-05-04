#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave
from pathlib import Path
from typing import Any

from local_voice_config import local_voice_id_for_provider


ROOT = Path(__file__).resolve().parents[1]


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def maybe_remove(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"
    lowered = language.lower()
    if lowered.startswith("de"):
        return "de"
    return "en"


def voice_env_for_language(provider: dict[str, Any], language: str) -> str:
    return provider.get("language_voice_id_env_vars", {}).get(normalize_language(language)) or provider[
        "default_voice_id_env_var"
    ]


def resolve_voice_id(provider: dict[str, Any], language: str, force_key_missing: bool) -> tuple[str | None, str]:
    language_env = voice_env_for_language(provider, language)
    if force_key_missing:
        return None, language_env
    language_voice = os.environ.get(language_env)
    if language_voice:
        return language_voice, language_env
    default_env = provider["default_voice_id_env_var"]
    default_voice = os.environ.get(default_env)
    if default_voice:
        return default_voice, default_env
    local_voice, local_source = local_voice_id_for_provider(provider, language)
    if local_voice:
        return local_voice, local_source or language_env
    return None, language_env


def fallback_reason(live: bool, force_key_missing: bool, api_key: str | None, voice_id: str | None, provider_key: str) -> str:
    if not live:
        return "dry-run-mode"
    if force_key_missing:
        return "forced-key-missing"
    if not api_key:
        return f"missing-{provider_key}-api-key"
    if not voice_id:
        return f"missing-{provider_key}-voice-id"
    return "live-call-not-attempted"


def elevenlabs_endpoint_url(provider: dict[str, Any], voice_id: str, redacted: bool = False, voice_env_var: str | None = None) -> str:
    rendered_voice = f"<redacted-env:{voice_env_var}>" if redacted else urllib.parse.quote(voice_id, safe="")
    base_url = provider["endpoint_url_template"].format(voice_id=rendered_voice)
    query = {
        "output_format": provider["default_output_format"],
        "enable_logging": str(bool(provider.get("enable_logging", False))).lower(),
    }
    return f"{base_url}?{urllib.parse.urlencode(query)}"


def cartesia_websocket_url(provider: dict[str, Any]) -> str:
    query = urllib.parse.urlencode({"cartesia_version": provider["api_version"]})
    return f"{provider['endpoint_url']}?{query}"


def redacted_request_preview(
    provider: dict[str, Any],
    provider_key: str,
    language: str,
    text: str,
    voice_settings: dict[str, Any],
    voice_env_var: str,
) -> dict[str, Any]:
    if provider_key == "elevenlabs":
        return {
            "method": "POST",
            "url": elevenlabs_endpoint_url(provider, "<redacted>", redacted=True, voice_env_var=voice_env_var),
            "headers": {
                "xi-api-key": "<redacted>",
                "Content-Type": "application/json",
            },
            "body": {
                "text": text,
                "model_id": provider["model_id"],
                "language_code": normalize_language(language),
                "voice_settings": voice_settings,
            },
        }
    return {
        "url": cartesia_websocket_url(provider),
        "headers": {
            "X-API-Key": "<redacted>",
            "Cartesia-Version": provider["api_version"],
        },
        "model_id": provider["model_id"],
        "voice": {
            "mode": "id",
            "id": f"<redacted-env:{voice_env_var}>",
        },
        "language": normalize_language(language),
        "transcript": text,
        "output_format": provider["default_output_format"],
        "add_timestamps": provider.get("add_timestamps", True),
        "context_id": "<generated-per-call>",
        "streaming_input_chunks": 1,
    }


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        raw = error.read(4096)
    except Exception:
        raw = b""
    text = raw.decode("utf-8", errors="replace").strip()
    try:
        payload = json.loads(text)
        detail = payload.get("detail")
        if isinstance(detail, dict):
            detail.pop("request_id", None)
            return json.dumps({"detail": detail}, separators=(",", ":"), ensure_ascii=False)[:700]
    except Exception:
        pass
    return " ".join(text.split())[:700]


def parse_provider_error(error_text: str | None) -> dict[str, Any]:
    if not error_text:
        return {"type": None, "code": None, "message": None}
    try:
        payload = json.loads(error_text)
        detail = payload.get("detail")
        if isinstance(detail, dict):
            return {
                "type": detail.get("type"),
                "code": detail.get("code"),
                "message": detail.get("message"),
            }
    except Exception:
        pass
    return {"type": "unparsed-provider-error", "code": None, "message": error_text[:300]}


def call_elevenlabs_stream(
    provider: dict[str, Any],
    text: str,
    language: str,
    voice_settings: dict[str, Any],
    audio_path: Path,
    api_key: str,
    voice_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    maybe_remove(audio_path)
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "text": text,
        "model_id": provider["model_id"],
        "language_code": normalize_language(language),
        "voice_settings": voice_settings,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        elevenlabs_endpoint_url(provider, voice_id),
        data=data,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        },
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            first_chunk = response.read(4096)
            time_to_first_audio_ms = elapsed_ms(start)
            rest = response.read()
            total_latency_ms = elapsed_ms(start)
            audio_bytes = first_chunk + rest
            audio_path.write_bytes(audio_bytes)
            audio_created = audio_path.exists() and audio_path.stat().st_size > 0
            if not audio_created:
                maybe_remove(audio_path)
            return {
                "api_call_made": True,
                "fallback_used": not audio_created,
                "fallback_reason": None if audio_created else "elevenlabs-returned-empty-audio",
                "audio_file_created": audio_created,
                "audio_output_path": project_relative_string(audio_path) if audio_created else None,
                "audio_byte_size": audio_path.stat().st_size if audio_created else 0,
                "http_status": response.status,
                "response_content_type": response.headers.get("Content-Type"),
                "request_id_present": bool(response.headers.get("request-id")),
                "time_to_first_audio_ms": time_to_first_audio_ms,
                "total_provider_latency_ms": total_latency_ms,
                "provider_error": None,
                "provider_error_summary": {"type": None, "code": None, "message": None},
            }
    except urllib.error.HTTPError as error:
        maybe_remove(audio_path)
        provider_error = read_error_body(error)
        return {
            "api_call_made": True,
            "fallback_used": True,
            "fallback_reason": "elevenlabs-http-error",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": error.code,
            "response_content_type": error.headers.get("Content-Type") if error.headers else None,
            "request_id_present": bool(error.headers.get("request-id")) if error.headers else False,
            "time_to_first_audio_ms": None,
            "total_provider_latency_ms": elapsed_ms(start),
            "provider_error": provider_error,
            "provider_error_summary": parse_provider_error(provider_error),
        }
    except Exception as error:
        maybe_remove(audio_path)
        provider_error = str(error).splitlines()[0][:700]
        return {
            "api_call_made": True,
            "fallback_used": True,
            "fallback_reason": "elevenlabs-request-failed",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": None,
            "response_content_type": None,
            "request_id_present": False,
            "time_to_first_audio_ms": None,
            "total_provider_latency_ms": elapsed_ms(start),
            "provider_error": provider_error,
            "provider_error_summary": parse_provider_error(provider_error),
        }


def write_pcm_wav(audio_path: Path, audio_bytes: bytes, output_format: dict[str, Any]) -> bool:
    maybe_remove(audio_path)
    if not audio_bytes:
        return False
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    sample_width = 2 if output_format["encoding"] == "pcm_s16le" else 4
    with wave.open(str(audio_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(sample_width)
        wav.setframerate(int(output_format["sample_rate"]))
        wav.writeframes(audio_bytes)
    created = audio_path.exists() and audio_path.stat().st_size > 44
    if not created:
        maybe_remove(audio_path)
    return created


def decode_audio_chunk(message: dict[str, Any]) -> bytes:
    data = message.get("data")
    if not data:
        return b""
    try:
        return base64.b64decode(data)
    except Exception:
        return b""


def call_cartesia_websocket(
    provider: dict[str, Any],
    text: str,
    language: str,
    audio_path: Path,
    api_key: str,
    voice_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    try:
        import websocket  # type: ignore
    except Exception as error:
        maybe_remove(audio_path)
        return {
            "websocket_connection_attempted": False,
            "api_call_made": False,
            "fallback_used": True,
            "fallback_reason": "missing-websocket-client-package",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": None,
            "response_content_type": None,
            "request_id_present": False,
            "connection_established_ms": None,
            "time_to_first_audio_ms": None,
            "total_provider_latency_ms": 0,
            "audio_chunk_count": 0,
            "timestamp_event_count": 0,
            "done_received": False,
            "provider_error": str(error).splitlines()[0][:500],
            "provider_error_summary": {
                "type": "missing-websocket-client-package",
                "code": None,
                "message": str(error).splitlines()[0][:300],
            },
        }

    context_id = str(uuid.uuid4())
    start = time.perf_counter()
    ws = None
    audio_parts: list[bytes] = []
    audio_chunk_count = 0
    timestamp_event_count = 0
    first_audio_ms = None
    done_received = False
    provider_error = None
    try:
        ws = websocket.create_connection(
            cartesia_websocket_url(provider),
            header=[
                f"X-API-Key: {api_key}",
                f"Cartesia-Version: {provider['api_version']}",
            ],
            timeout=timeout_seconds,
        )
        connection_established_ms = elapsed_ms(start)
        ws.send(
            json.dumps(
                {
                    "model_id": provider["model_id"],
                    "transcript": text,
                    "voice": {"mode": "id", "id": voice_id},
                    "language": normalize_language(language),
                    "context_id": context_id,
                    "output_format": provider["default_output_format"],
                    "add_timestamps": provider.get("add_timestamps", True),
                    "continue": False,
                },
                ensure_ascii=False,
            )
        )
        deadline = time.perf_counter() + timeout_seconds
        while time.perf_counter() < deadline:
            remaining = max(0.1, min(1.0, deadline - time.perf_counter()))
            ws.settimeout(remaining)
            raw = ws.recv()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            message = json.loads(raw)
            message_type = message.get("type")
            if message_type == "chunk":
                chunk_bytes = decode_audio_chunk(message)
                if chunk_bytes:
                    if first_audio_ms is None:
                        first_audio_ms = elapsed_ms(start)
                    audio_parts.append(chunk_bytes)
                    audio_chunk_count += 1
            elif message_type in {"timestamps", "phoneme_timestamps"}:
                timestamp_event_count += 1
            elif message_type == "done" or message.get("done") is True:
                done_received = True
                break
            elif message_type == "error":
                provider_error = " ".join(str(message.get("message") or message.get("title") or message).split())[:500]
                break
        total_latency_ms = elapsed_ms(start)
        audio_created = write_pcm_wav(audio_path, b"".join(audio_parts), provider["default_output_format"])
        return {
            "websocket_connection_attempted": True,
            "api_call_made": True,
            "fallback_used": not audio_created,
            "fallback_reason": None if audio_created else provider_error or "cartesia-websocket-returned-no-audio",
            "audio_file_created": audio_created,
            "audio_output_path": project_relative_string(audio_path) if audio_created else None,
            "audio_byte_size": audio_path.stat().st_size if audio_created else 0,
            "http_status": None,
            "response_content_type": None,
            "request_id_present": False,
            "connection_established_ms": connection_established_ms,
            "time_to_first_audio_ms": first_audio_ms,
            "total_provider_latency_ms": total_latency_ms,
            "audio_chunk_count": audio_chunk_count,
            "timestamp_event_count": timestamp_event_count,
            "done_received": done_received,
            "provider_error": provider_error,
            "provider_error_summary": {"type": None, "code": None, "message": provider_error},
        }
    except Exception as error:
        maybe_remove(audio_path)
        provider_error = str(error).splitlines()[0][:500]
        return {
            "websocket_connection_attempted": True,
            "api_call_made": True,
            "fallback_used": True,
            "fallback_reason": "cartesia-websocket-request-failed",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": None,
            "response_content_type": None,
            "request_id_present": False,
            "connection_established_ms": elapsed_ms(start),
            "time_to_first_audio_ms": first_audio_ms,
            "total_provider_latency_ms": elapsed_ms(start),
            "audio_chunk_count": audio_chunk_count,
            "timestamp_event_count": timestamp_event_count,
            "done_received": done_received,
            "provider_error": provider_error,
            "provider_error_summary": {
                "type": "cartesia-websocket-request-failed",
                "code": None,
                "message": provider_error,
            },
        }
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
