#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from generate_voice_response import synthesize_with_windows_sapi  # noqa: E402


DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "ultravox-003-synthetic-audio-turn.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-003" / "ULTRAVOX-003-synthetic-audio-turn.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-003" / "ULTRAVOX-003-synthetic-audio-turn-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-003" / "audio"
DEFAULT_ENV_FILE = ROOT / "runtime" / "config" / "local" / "ultravox.env"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
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


def resolve_voice_value(provider: dict[str, Any]) -> str | None:
    env_var = provider.get("voice_env_var")
    if not env_var:
        return None
    value = os.environ.get(env_var, "").strip()
    return value or None


def create_call_body(provider: dict[str, Any], case: dict[str, Any], *, redacted: bool) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": provider["model"],
        "recordingEnabled": False,
        "firstSpeaker": "FIRST_SPEAKER_USER",
        "transcriptOptional": False,
        "initialOutputMedium": "MESSAGE_MEDIUM_VOICE",
        "languageHint": case["language"],
        "joinTimeout": f"{case['join_timeout_seconds']}s",
        "maxDuration": f"{case['max_duration_seconds']}s",
        "systemPrompt": case["system_prompt"],
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
                    "userStartedSpeaking": True,
                    "userStoppedSpeaking": True,
                },
            }
        },
        "metadata": {
            "project": "emotion-aware-ai-sales-agent",
            "milestone": "ULTRAVOX-003",
            "syntheticCustomerAudio": "true",
            "realCustomerAudio": "false",
        },
    }
    voice_value = resolve_voice_value(provider)
    if voice_value:
        body["voice"] = f"<redacted-env:{provider['voice_env_var']}>" if redacted else voice_value
    return body


def redacted_request_preview(provider: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": provider["create_call_url"],
        "headers": {
            "X-API-Key": "<redacted>",
            "Content-Type": "application/json",
        },
        "body": create_call_body(provider, case, redacted=True),
    }


def create_call(provider: dict[str, Any], case: dict[str, Any], api_key: str, timeout_seconds: float) -> dict[str, Any]:
    data = json.dumps(create_call_body(provider, case, redacted=False), ensure_ascii=False).encode("utf-8")
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
    retries: int = 5,
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
        request = urllib.request.Request(url, method="DELETE", headers={"X-API-Key": api_key})
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
    raise AssertionError("unreachable")


def call_id_suffix(call_id: str | None) -> str | None:
    return call_id[-8:] if call_id else None


def join_host(join_url: str | None) -> str | None:
    return urlparse(join_url).netloc if join_url else None


def synthesize_with_windows_sapi_com(text: str, audio_path: Path) -> None:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["ULTRAVOX_003_TEXT"] = text
    env["ULTRAVOX_003_OUT"] = str(audio_path)
    command = r"""
$ErrorActionPreference = 'Stop'
$voice = New-Object -ComObject SAPI.SpVoice
$stream = New-Object -ComObject SAPI.SpFileStream
try {
  $stream.Open($env:ULTRAVOX_003_OUT, 3, $false)
  $voice.AudioOutputStream = $stream
  [void]$voice.Speak($env:ULTRAVOX_003_TEXT, 0)
}
finally {
  if ($stream) {
    $stream.Close()
  }
}
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("Windows SAPI COM fallback requires PowerShell on Windows.") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        maybe_remove(audio_path)
        raise SystemExit(
            f"Windows SAPI COM fallback did not create a playable WAV in this environment: {message}"
        ) from exc

    if not audio_path.exists() or audio_path.stat().st_size <= 44:
        maybe_remove(audio_path)
        raise SystemExit("Windows SAPI COM fallback did not create a playable WAV in this environment.")


def synthesize_customer_wav(case: dict[str, Any], audio_dir: Path) -> dict[str, Any]:
    wav_path = audio_dir / "ULTRAVOX-003-synthetic-customer-input.wav"
    maybe_remove(wav_path)
    audio_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    backend = "windows-sapi-system-speech"
    primary_error = None
    fallback_fixture_error = None
    try:
        synthesize_with_windows_sapi(case["customer_text"], wav_path, voice_name=None)
    except SystemExit as error:
        primary_error = str(error).splitlines()[0][:800]
        maybe_remove(wav_path)
        backend = "windows-sapi-com-fallback"
        try:
            synthesize_with_windows_sapi_com(case["customer_text"], wav_path)
        except SystemExit as fallback_error:
            fallback_fixture_error = str(fallback_error).splitlines()[0][:800]
            maybe_remove(wav_path)
            fixture = case.get("fallback_input_audio_fixture")
            fixture_path = resolve_project_path(fixture) if fixture else None
            if fixture_path and fixture_path.exists() and fixture_path.stat().st_size > 44:
                backend = "ultravox-002-synthetic-audio-fixture-fallback"
                shutil.copyfile(fixture_path, wav_path)
            else:
                return {
                    "synthesis_attempted": True,
                    "synthesis_succeeded": False,
                    "synthesis_latency_ms": elapsed_ms(start),
                    "synthesis_backend": backend,
                    "primary_synthesis_error": primary_error,
                    "fallback_synthesis_error": fallback_fixture_error,
                    "fixture_source_path": project_relative_string(fixture_path) if fixture_path else None,
                    "fixture_used": False,
                    "input_text_matches_case": False,
                    "wav_path": None,
                    "wav_byte_size": 0,
                    "synthesis_error": "local-speech-synthesis-and-fixture-fallback-failed",
                    "pcm_sample_rate": 48000,
                    "pcm_byte_size": 0,
                }
    return {
        "synthesis_attempted": True,
        "synthesis_succeeded": wav_path.exists() and wav_path.stat().st_size > 44,
        "synthesis_latency_ms": elapsed_ms(start),
        "synthesis_backend": backend,
        "primary_synthesis_error": primary_error,
        "fallback_synthesis_error": fallback_fixture_error,
        "fixture_source_path": case.get("fallback_input_audio_fixture") if backend.startswith("ultravox-002") else None,
        "fixture_used": backend.startswith("ultravox-002"),
        "input_text_matches_case": not backend.startswith("ultravox-002"),
        "wav_path": project_relative_string(wav_path),
        "wav_byte_size": wav_path.stat().st_size if wav_path.exists() else 0,
        "synthesis_error": None,
        "pcm_sample_rate": 48000,
        "pcm_byte_size": 0,
    }


def wav_to_pcm_s16le_mono_48k(wav_path: Path, target_rate: int) -> bytes:
    with wave.open(str(wav_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        source_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width == 1:
        audio = (np.frombuffer(frames, dtype=np.uint8).astype(np.int16) - 128) << 8
    elif sample_width == 2:
        audio = np.frombuffer(frames, dtype="<i2").astype(np.float32)
    elif sample_width == 4:
        audio = (np.frombuffer(frames, dtype="<i4").astype(np.float32) / 65536.0)
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width}")

    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)

    if source_rate != target_rate and len(audio) > 1:
        old_x = np.linspace(0.0, 1.0, num=len(audio), endpoint=False)
        new_len = max(1, int(round(len(audio) * target_rate / source_rate)))
        new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
        audio = np.interp(new_x, old_x, audio)

    pcm = np.clip(audio, -32768, 32767).astype("<i2")
    return pcm.tobytes()


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


def parse_text_event(raw: str) -> tuple[str | None, str | None]:
    try:
        event = json.loads(raw)
    except Exception:
        return "non-json-text", None
    event_type = event.get("type") or event.get("event") or event.get("message")
    text = None
    if event_type == "transcript" or "transcript" in event:
        transcript = event.get("transcript")
        if isinstance(transcript, str):
            text = transcript
        elif isinstance(transcript, dict):
            text = transcript.get("text") or transcript.get("transcript")
        text = text or event.get("text")
    return str(event_type)[:80] if event_type else "unknown-text-event", text


def stream_synthetic_turn(
    join_url: str,
    pcm: bytes,
    audio_path: Path,
    sample_rate: int,
    chunk_ms: int,
    trailing_silence_ms: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    try:
        import websocket  # type: ignore
    except Exception as error:
        return {
            "websocket_connection_attempted": False,
            "websocket_connected": False,
            "websocket_error": f"missing-websocket-client-package: {str(error).splitlines()[0][:400]}",
            "customer_audio_bytes_sent": 0,
            "time_to_first_transcript_ms": None,
            "first_transcript_text": None,
            "time_to_first_agent_audio_byte_ms": None,
            "total_turn_latency_ms": 0,
            "agent_audio_bytes_received": 0,
            "agent_audio_file_created": False,
            "agent_audio_output_path": None,
            "binary_message_count": 0,
            "text_message_count": 0,
            "text_event_types": [],
        }

    maybe_remove(audio_path)
    start = time.perf_counter()
    ws = None
    audio_parts: list[bytes] = []
    first_transcript_ms = None
    first_transcript_text = None
    first_agent_audio_ms = None
    binary_message_count = 0
    text_message_count = 0
    text_event_types: list[str] = []
    websocket_error = None
    connected = False
    bytes_sent = 0

    chunk_size = max(2, int(sample_rate * 2 * chunk_ms / 1000))
    chunk_size -= chunk_size % 2
    silence = b"\x00" * int(sample_rate * 2 * trailing_silence_ms / 1000)

    try:
        ws = websocket.create_connection(join_url, timeout=timeout_seconds)
        connected = True
        stream = pcm + silence
        for offset in range(0, len(stream), chunk_size):
            chunk = stream[offset : offset + chunk_size]
            ws.send_binary(chunk)
            bytes_sent += len(chunk)
            time.sleep(chunk_ms / 1000)

        deadline = time.perf_counter() + timeout_seconds
        while time.perf_counter() < deadline:
            remaining = max(0.1, min(1.0, deadline - time.perf_counter()))
            ws.settimeout(remaining)
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if isinstance(raw, bytes):
                if raw:
                    if first_agent_audio_ms is None:
                        first_agent_audio_ms = elapsed_ms(start)
                    audio_parts.append(raw)
                    binary_message_count += 1
                    if sum(len(part) for part in audio_parts) >= sample_rate:
                        break
            else:
                text_message_count += 1
                event_type, text = parse_text_event(raw)
                if event_type and event_type not in text_event_types:
                    text_event_types.append(event_type)
                if text and first_transcript_ms is None:
                    first_transcript_ms = elapsed_ms(start)
                    first_transcript_text = " ".join(text.split())[:240]
    except Exception as error:
        websocket_error = redact_secret_text(str(error).splitlines()[0][:800])
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    audio_bytes = b"".join(audio_parts)
    audio_created = write_pcm_wav(audio_path, audio_bytes, sample_rate)
    return {
        "websocket_connection_attempted": True,
        "websocket_connected": connected,
        "websocket_error": websocket_error,
        "customer_audio_bytes_sent": bytes_sent,
        "time_to_first_transcript_ms": first_transcript_ms,
        "first_transcript_text": first_transcript_text,
        "time_to_first_agent_audio_byte_ms": first_agent_audio_ms,
        "total_turn_latency_ms": elapsed_ms(start),
        "agent_audio_bytes_received": len(audio_bytes),
        "agent_audio_file_created": audio_created,
        "agent_audio_output_path": project_relative_string(audio_path) if audio_created else None,
        "binary_message_count": binary_message_count,
        "text_message_count": text_message_count,
        "text_event_types": text_event_types,
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


def fallback_result(
    reason: str,
    provider: dict[str, Any],
    case: dict[str, Any],
    timeout_seconds: float,
    env_file: Path,
    *,
    live_requested: bool = False,
) -> dict[str, Any]:
    return {
        "evaluation_milestone": "ULTRAVOX-003",
        "mode": "fallback",
        "provider": provider_summary(provider, env_file),
        "case": case_summary(case),
        "summary": summary_block(live_requested, False, False, reason, timeout_seconds),
        "request_preview": redacted_request_preview(provider, case),
        "synthetic_input_audio": empty_synthetic_audio(reason),
        "create_call": empty_create_call(),
        "websocket": empty_websocket(),
        "delete_call": empty_delete_call(),
    }


def empty_synthetic_audio(reason: str | None = None) -> dict[str, Any]:
    return {
        "synthesis_attempted": False,
        "synthesis_succeeded": False,
        "synthesis_latency_ms": 0,
        "wav_path": None,
        "wav_byte_size": 0,
        "synthesis_error": reason,
        "pcm_sample_rate": 48000,
        "pcm_byte_size": 0,
    }


def empty_create_call() -> dict[str, Any]:
    return {
        "attempted": False,
        "api_call_made": False,
        "http_status": None,
        "latency_ms": 0,
        "call_id_suffix": None,
        "join_url_received": False,
        "join_url_host": None,
        "provider_error": None,
    }


def empty_websocket() -> dict[str, Any]:
    return {
        "websocket_connection_attempted": False,
        "websocket_connected": False,
        "websocket_error": None,
        "customer_audio_bytes_sent": 0,
        "time_to_first_transcript_ms": None,
        "first_transcript_text": None,
        "time_to_first_agent_audio_byte_ms": None,
        "total_turn_latency_ms": 0,
        "agent_audio_bytes_received": 0,
        "agent_audio_file_created": False,
        "agent_audio_output_path": None,
        "binary_message_count": 0,
        "text_message_count": 0,
        "text_event_types": [],
    }


def empty_delete_call() -> dict[str, Any]:
    return {
        "delete_attempted": False,
        "delete_api_call_made": False,
        "delete_attempt_count": 0,
        "delete_http_status": None,
        "delete_latency_ms": 0,
        "deleted": False,
        "delete_error": None,
    }


def summary_block(
    live: bool,
    provider_called: bool,
    audio_created: bool,
    fallback_reason: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        "live_call_requested": live,
        "approved_live_test": True,
        "create_call_api_calls_made": 1 if provider_called else 0,
        "delete_call_api_calls_made": 0,
        "websocket_connections_attempted": 0,
        "real_customer_audio_uploaded": False,
        "synthetic_customer_audio_uploaded": False,
        "synthetic_prompt_only": True,
        "voice_cloning_used": False,
        "provider_owned_business_logic": False,
        "durable_provider_agent_created": False,
        "runtime_behavior_changed": False,
        "opens_prod_102": False,
        "agent_audio_file_created": audio_created,
        "fallback_used": fallback_reason is not None,
        "fallback_reason": fallback_reason,
        "timeout_seconds": timeout_seconds,
    }


def case_summary(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "customer_text": case["customer_text"],
        "success_criteria": case["success_criteria"],
    }


def run_live_turn(payload: dict[str, Any], env_file: Path, force_key_missing: bool, timeout_seconds: float, audio_dir: Path) -> dict[str, Any]:
    provider = payload["provider"]
    case = payload["synthetic_case"]
    loaded_env = load_env_file(env_file, force_key_missing=force_key_missing)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])

    if force_key_missing:
        return fallback_result("forced-key-missing", provider, case, timeout_seconds, env_file, live_requested=True)
    if not api_key:
        return fallback_result("missing-ultravox-api-key", provider, case, timeout_seconds, env_file, live_requested=True)

    synthetic_audio = synthesize_customer_wav(case, audio_dir)
    if not synthetic_audio["synthesis_succeeded"] or not synthetic_audio["wav_path"]:
        result = fallback_result(
            "synthetic-audio-generation-failed",
            provider,
            case,
            timeout_seconds,
            env_file,
            live_requested=True,
        )
        result["synthetic_input_audio"] = synthetic_audio
        return result

    pcm = wav_to_pcm_s16le_mono_48k(ROOT / synthetic_audio["wav_path"], int(provider["input_sample_rate"]))
    synthetic_audio["pcm_sample_rate"] = int(provider["input_sample_rate"])
    synthetic_audio["pcm_byte_size"] = len(pcm)

    create = create_call(provider, case, api_key, timeout_seconds)
    websocket_result = empty_websocket()
    if create["join_url"]:
        websocket_result = stream_synthetic_turn(
            create["join_url"],
            pcm,
            audio_dir / "ULTRAVOX-003-agent-response-audio.wav",
            int(provider["output_sample_rate"]),
            int(case["audio_chunk_ms"]),
            int(case["trailing_silence_ms"]),
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
    fallback_reason = None
    if create_summary["provider_error"]:
        fallback_reason = "create-call-provider-error"
    elif not create_summary["join_url_received"]:
        fallback_reason = "missing-join-url"
    elif websocket_result["websocket_error"]:
        fallback_reason = "websocket-error"
    elif websocket_result["agent_audio_bytes_received"] == 0 and websocket_result["first_transcript_text"] is None:
        fallback_reason = "no-transcript-or-agent-audio-received"

    summary = summary_block(True, create["api_call_made"], websocket_result["agent_audio_file_created"], fallback_reason, timeout_seconds)
    summary["delete_call_api_calls_made"] = 1 if delete["delete_api_call_made"] else 0
    summary["websocket_connections_attempted"] = 1 if websocket_result["websocket_connection_attempted"] else 0
    summary["synthetic_customer_audio_uploaded"] = websocket_result["customer_audio_bytes_sent"] > 0

    return {
        "evaluation_milestone": "ULTRAVOX-003",
        "mode": "live",
        "provider": provider_summary(provider, env_file),
        "case": case_summary(case),
        "summary": summary,
        "request_preview": redacted_request_preview(provider, case),
        "synthetic_input_audio": synthetic_audio,
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
    synthetic = result["synthetic_input_audio"]
    lines = [
        "# ULTRAVOX-003 Synthetic Audio Turn Report",
        "",
        "This report was generated by `scripts/run_ultravox_003_synthetic_audio_turn.py`.",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Live call requested: `{str(summary['live_call_requested']).lower()}`",
        f"- Approved live test: `{str(summary['approved_live_test']).lower()}`",
        f"- Create-call API calls made: `{summary['create_call_api_calls_made']}`",
        f"- WebSocket connections attempted: `{summary['websocket_connections_attempted']}`",
        f"- Delete-call API calls made: `{summary['delete_call_api_calls_made']}`",
        f"- Real customer audio uploaded: `{str(summary['real_customer_audio_uploaded']).lower()}`",
        f"- Synthetic customer audio uploaded: `{str(summary['synthetic_customer_audio_uploaded']).lower()}`",
        f"- Voice cloning used: `{str(summary['voice_cloning_used']).lower()}`",
        f"- Runtime behavior changed: `{str(summary['runtime_behavior_changed']).lower()}`",
        f"- Opens PROD-102: `{str(summary['opens_prod_102']).lower()}`",
        f"- Fallback used: `{str(summary['fallback_used']).lower()}`",
        f"- Fallback reason: `{summary['fallback_reason']}`",
        "",
        "## Synthetic Input Audio",
        "",
        f"- Text: `{result['case']['customer_text']}`",
        f"- WAV path: `{synthetic['wav_path']}`",
        f"- WAV bytes: `{synthetic['wav_byte_size']}`",
        f"- Synthesis backend: `{synthetic.get('synthesis_backend')}`",
        f"- Fixture used: `{str(synthetic.get('fixture_used', False)).lower()}`",
        f"- Fixture source path: `{synthetic.get('fixture_source_path')}`",
        f"- Input text matches case: `{str(synthetic.get('input_text_matches_case', True)).lower()}`",
        f"- PCM sample rate: `{synthetic['pcm_sample_rate']}`",
        f"- PCM bytes sent candidate: `{synthetic['pcm_byte_size']}`",
        f"- Synthesis latency ms: `{synthetic['synthesis_latency_ms']}`",
        f"- Synthesis error: `{synthetic['synthesis_error']}`",
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
        "## WebSocket Turn",
        "",
        f"- Connection attempted: `{str(websocket_result['websocket_connection_attempted']).lower()}`",
        f"- Connected: `{str(websocket_result['websocket_connected']).lower()}`",
        f"- Synthetic customer bytes sent: `{websocket_result['customer_audio_bytes_sent']}`",
        f"- Time to first transcript ms: `{websocket_result['time_to_first_transcript_ms']}`",
        f"- First transcript text: `{websocket_result['first_transcript_text']}`",
        f"- Time to first agent audio byte ms: `{websocket_result['time_to_first_agent_audio_byte_ms']}`",
        f"- Total turn latency ms: `{websocket_result['total_turn_latency_ms']}`",
        f"- Agent audio bytes received: `{websocket_result['agent_audio_bytes_received']}`",
        f"- Agent audio file created: `{str(websocket_result['agent_audio_file_created']).lower()}`",
        f"- Agent audio output path: `{websocket_result['agent_audio_output_path']}`",
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
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ULTRAVOX-003 synthetic customer-audio live turn.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Path to ULTRAVOX-003 case JSON.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON result.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Ignored env file containing ULTRAVOX_API_KEY.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Ignored output dir for synthetic input and agent audio.")
    parser.add_argument("--live", action="store_true", help="Make the approved synthetic provider call.")
    parser.add_argument("--force-key-missing", action="store_true", help="Exercise fallback without reading any key.")
    parser.add_argument("--timeout-seconds", type=float, default=10.0, help="Bound provider and WebSocket waits.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(resolve_project_path(args.cases))
    env_file = resolve_project_path(args.env_file)
    timeout_seconds = min(max(args.timeout_seconds, 1.0), 12.0)
    if not args.live:
        result = fallback_result("dry-run-mode", payload["provider"], payload["synthetic_case"], timeout_seconds, env_file)
    else:
        result = run_live_turn(
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
