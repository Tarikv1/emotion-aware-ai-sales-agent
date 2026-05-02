#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-017"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-017-live-ab-audio.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-017-live-ab-audio.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-017-live-ab-audio-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated"


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def resolve_project_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
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
    return None, language_env


def selected_provider_keys(provider_arg: str) -> list[str]:
    if provider_arg == "both":
        return ["elevenlabs", "cartesia"]
    return [provider_arg]


def selected_source_cases(source_payload: dict[str, Any], selected_ids: list[str], limit: int | None) -> list[dict[str, Any]]:
    cases_by_id = {case["case_id"]: case for case in source_payload["cases"]}
    cases = [cases_by_id[case_id] for case_id in selected_ids]
    if limit is not None:
        return cases[: max(0, limit)]
    return cases


def find_provider_variant(source_case: dict[str, Any], provider_key: str) -> dict[str, Any]:
    for variant in source_case["provider_variants"]:
        if variant["provider_key"] == provider_key:
            return variant
    raise KeyError(f"Provider variant not found: {source_case['case_id']} {provider_key}")


def audio_filename(case_index: int, language: str, provider_key: str, variant_kind: str, extension: str) -> str:
    return f"VOICE-017-C{case_index:02d}-{language}-{provider_key}-{variant_kind}.{extension}"


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
            "provider_error_summary": {"type": "missing-websocket-client-package", "code": None, "message": str(error).splitlines()[0][:300]},
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
            "provider_error_summary": {"type": "cartesia-websocket-request-failed", "code": None, "message": provider_error},
        }
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def offline_result(reason: str) -> dict[str, Any]:
    return {
        "api_call_made": False,
        "fallback_used": True,
        "fallback_reason": reason,
        "audio_file_created": False,
        "audio_output_path": None,
        "audio_byte_size": 0,
        "http_status": None,
        "response_content_type": None,
        "request_id_present": False,
        "time_to_first_audio_ms": None,
        "total_provider_latency_ms": 0,
        "provider_error": None,
        "provider_error_summary": {"type": None, "code": None, "message": None},
    }


def run_ab_result(
    provider: dict[str, Any],
    provider_key: str,
    case: dict[str, Any],
    provider_variant: dict[str, Any],
    case_index: int,
    variant_kind: str,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    language = normalize_language(case["language"])
    text = case["plain_text"] if variant_kind == "plain" else provider_variant["rendered_text"]
    if provider_key == "elevenlabs":
        voice_settings = dict(provider.get("base_voice_settings", {}))
        if variant_kind == "prosody":
            voice_settings.update(provider_variant.get("voice_settings") or {})
    else:
        voice_settings = {}

    voice_id, voice_env_var = resolve_voice_id(provider, language, force_key_missing)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    can_call_live = live and bool(api_key) and bool(voice_id)
    filename = audio_filename(case_index, language, provider_key, variant_kind, provider["audio_extension"])
    audio_path = audio_dir / filename
    request_preview = redacted_request_preview(provider, provider_key, language, text, voice_settings, voice_env_var)

    if can_call_live:
        if provider_key == "elevenlabs":
            provider_result = call_elevenlabs_stream(
                provider=provider,
                text=text,
                language=language,
                voice_settings=voice_settings,
                audio_path=audio_path,
                api_key=api_key or "",
                voice_id=voice_id or "",
                timeout_seconds=timeout_seconds,
            )
        else:
            provider_result = call_cartesia_websocket(
                provider=provider,
                text=text,
                language=language,
                audio_path=audio_path,
                api_key=api_key or "",
                voice_id=voice_id or "",
                timeout_seconds=timeout_seconds,
            )
        generated_text_sent = provider_result["api_call_made"]
    else:
        maybe_remove(audio_path)
        provider_result = offline_result(fallback_reason(live, force_key_missing, api_key, voice_id, provider_key))
        generated_text_sent = False

    return {
        "provider_key": provider_key,
        "provider_id": provider["provider_id"],
        "provider_name": provider["provider_name"],
        "endpoint_type": provider["endpoint_type"],
        "model_id": provider["model_id"],
        "variant_kind": variant_kind,
        "language": language,
        "source_case_id": case["case_id"],
        "api_key_env_var": provider["api_key_env_var"],
        "selected_voice_id_env_var": voice_env_var,
        "api_key_present": bool(api_key),
        "voice_id_present": bool(voice_id),
        "api_key_value_logged": False,
        "voice_id_value_logged": False,
        "customer_audio_uploaded": False,
        "generated_text_sent_to_provider": generated_text_sent,
        "synthetic_prompt_only": True,
        "voice_clone_used": False,
        "custom_voice_used": False,
        "timeout_seconds": timeout_seconds,
        "tts_input_text": text,
        "tts_input_chars": len(text),
        "voice_settings": voice_settings,
        "request_preview": request_preview,
        "audio_filename": filename,
        **provider_result,
    }


def run_case(
    case: dict[str, Any],
    providers: dict[str, Any],
    provider_keys: list[str],
    case_index: int,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    results = []
    for provider_key in provider_keys:
        provider = providers[provider_key]
        provider_variant = next(variant for variant in case["provider_variants"] if variant["provider_key"] == provider_key)
        for variant_kind in ["plain", "prosody"]:
            results.append(
                run_ab_result(
                    provider=provider,
                    provider_key=provider_key,
                    case=case,
                    provider_variant=provider_variant,
                    case_index=case_index,
                    variant_kind=variant_kind,
                    audio_dir=audio_dir,
                    live=live,
                    force_key_missing=force_key_missing,
                    timeout_seconds=timeout_seconds,
                )
            )
    return {
        "case_id": f"VOICE-017-C{case_index:02d}",
        "source_case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "language": normalize_language(case["language"]),
        "plain_text": case["plain_text"],
        "prosody_cue_count": case["prosody_cue_count"],
        "prosody_cue_counts": case["prosody_cue_counts"],
        "ab_results": results,
        "quality_review": {
            "human_rating_required": True,
            "human_ratings_recorded": False,
            "quality_claim_allowed": False,
            "criteria": [
                "naturalness",
                "clarity",
                "language pronunciation",
                "sales-call pacing",
                "low muffling or artifacts",
                "emotional appropriateness without overacting",
                "trustworthiness",
                "plain vs prosody preference",
            ],
        },
    }


def summarize(cases: list[dict[str, Any]], provider_keys: list[str], live: bool, timeout_seconds: float) -> dict[str, Any]:
    results = [result for case in cases for result in case["ab_results"]]
    languages: dict[str, int] = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1
    return {
        "case_count": len(cases),
        "languages": languages,
        "provider_count": len(provider_keys),
        "providers": provider_keys,
        "ab_variant_count": len(results),
        "plain_variant_count": sum(1 for result in results if result["variant_kind"] == "plain"),
        "prosody_variant_count": sum(1 for result in results if result["variant_kind"] == "prosody"),
        "live_call_requested": live,
        "api_calls_made": sum(1 for result in results if result["api_call_made"]),
        "audio_files_created": sum(1 for result in results if result["audio_file_created"]),
        "fallback_count": sum(1 for result in results if result["fallback_used"]),
        "customer_audio_uploaded": False,
        "synthetic_prompts_only": True,
        "voice_cloning_used": False,
        "timeout_seconds": timeout_seconds,
        "human_ratings_recorded": False,
        "quality_claim_allowed": False,
        "max_time_to_first_audio_ms": max(
            (result["time_to_first_audio_ms"] for result in results if result["time_to_first_audio_ms"] is not None),
            default=None,
        ),
        "max_total_provider_latency_ms": max((result["total_provider_latency_ms"] for result in results), default=0),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-017 Live A/B Audio Report",
        "",
        "This report was generated by `scripts/run_voice_017_live_ab_audio.py`.",
        "",
        "Default mode is dry-run. Live mode requires `--live`, provider-specific environment variables, and a bounded timeout.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- German cases: `{summary['languages'].get('de', 0)}`",
        f"- English cases: `{summary['languages'].get('en', 0)}`",
        f"- Providers: `{', '.join(summary['providers'])}`",
        f"- A/B variants: `{summary['ab_variant_count']}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Human ratings recorded: `{summary['human_ratings_recorded']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        f"- Max time to first audio: `{summary['max_time_to_first_audio_ms']}`",
        f"- Max total provider latency: `{summary['max_total_provider_latency_ms']} ms`",
        "",
        "## Case Results",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                "",
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Source case: `{case['source_case_id']}`",
                f"- Language: `{case['language']}`",
                f"- Prosody cues: `{case['prosody_cue_count']}`",
            ]
        )
        for result in case["ab_results"]:
            lines.extend(
                [
                    f"- `{result['provider_key']}` `{result['variant_kind']}`:",
                    f"  audio created: `{result['audio_file_created']}`",
                    f"  audio path: `{result['audio_output_path'] or 'not created'}`",
                    f"  API call made: `{result['api_call_made']}`",
                    f"  fallback reason: `{result['fallback_reason'] or 'not needed'}`",
                    f"  time to first audio: `{result['time_to_first_audio_ms']}`",
                    f"  total latency: `{result['total_provider_latency_ms']} ms`",
                ]
            )
    return "\n".join(lines) + "\n"


def build_payload(
    cases_path: Path,
    provider_arg: str,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    limit: int | None,
) -> dict[str, Any]:
    config = load_json(cases_path)
    source_path = resolve_project_path(config["source_artifact"])
    if source_path is None:
        raise SystemExit("VOICE-017 source artifact could not be resolved.")
    source_payload = load_json(source_path)
    provider_keys = selected_provider_keys(provider_arg)
    cases = selected_source_cases(source_payload, config["selected_source_case_ids"], limit)
    results = [
        run_case(
            case=case,
            providers=config["providers"],
            provider_keys=provider_keys,
            case_index=index,
            audio_dir=audio_dir,
            live=live,
            force_key_missing=force_key_missing,
            timeout_seconds=timeout_seconds,
        )
        for index, case in enumerate(cases, start=1)
    ]
    return {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": config["experiment_scope"],
        "case_file": project_relative_string(cases_path),
        "source_artifact": project_relative_string(source_path),
        "selected_source_case_ids": [case["case_id"] for case in cases],
        "selected_provider_arg": provider_arg,
        "providers": {key: config["providers"][key] for key in provider_keys},
        "safety_gate": config["safety_gate"],
        "quality_rubric": config["quality_rubric"],
        "summary": summarize(results, provider_keys, live, timeout_seconds),
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(result["api_call_made"] for case in results for result in case["ab_results"]),
            "requires_api_key": live and not force_key_missing,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
        },
        "cases": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-017 guarded plain-vs-prosody live-capable TTS A/B harness.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-017 case/config file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia", "both"], default="both", help="Provider to render/call.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of selected source cases.")
    parser.add_argument("--live", action="store_true", help="Allow live provider API calls when env gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore provider env vars to validate missing-key fallback.")
    parser.add_argument("--allow-both-live", action="store_true", help="Allow live calls to both providers in one run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")
    if args.live and args.provider == "both" and not args.allow_both_live:
        raise SystemExit("--live with --provider both requires --allow-both-live to avoid accidental double-provider calls.")

    cases_path = resolve_project_path(args.cases)
    audio_dir = resolve_project_path(args.audio_dir)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    if cases_path is None or audio_dir is None or out_path is None or report_path is None:
        raise SystemExit("Cases, audio, output, and report paths are required.")

    payload = build_payload(
        cases_path=cases_path,
        provider_arg=args.provider,
        audio_dir=audio_dir,
        live=args.live,
        force_key_missing=args.force_key_missing,
        timeout_seconds=args.timeout_seconds,
        limit=args.limit,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
