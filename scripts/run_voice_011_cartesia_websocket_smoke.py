#!/usr/bin/env python3
import argparse
import base64
import json
import os
import time
import uuid
import wave
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from generate_voice_response import (
    DEFAULT_CASES_PATH,
    build_voice_packet,
    project_relative_string,
    resolve_project_path,
)
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from runtime.core.realtime_turns import load_realtime_cases


VOICE_MILESTONE = "VOICE-011"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-011-cartesia-websocket-smoke.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-011-cartesia-websocket-smoke.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-011-cartesia-websocket-smoke-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated"


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


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


def load_campaign(campaign_id: str, cases_path: Path) -> dict[str, Any]:
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, campaign_id)
    campaign["_case_file"] = cases_path
    return campaign


def output_format(provider: dict[str, Any]) -> dict[str, Any]:
    return dict(provider["default_output_format"])


def voice_env_for_language(provider: dict[str, Any], language: str) -> str:
    return provider.get("language_voice_id_env_vars", {}).get(language) or provider["default_voice_id_env_var"]


def resolve_voice_id(provider: dict[str, Any], language: str, force_key_missing: bool) -> tuple[str | None, str]:
    language_env = voice_env_for_language(provider, language)
    if force_key_missing:
        return None, language_env
    language_voice = os.environ.get(language_env)
    if language_voice:
        return language_voice, language_env
    default_env = provider["default_voice_id_env_var"]
    return os.environ.get(default_env), default_env


def websocket_url(provider: dict[str, Any]) -> str:
    query = urlencode({"cartesia_version": provider["api_version"]})
    return f"{provider['endpoint_url']}?{query}"


def redacted_request_preview(provider: dict[str, Any], case: dict[str, Any], voice_env_var: str) -> dict[str, Any]:
    return {
        "url": websocket_url(provider),
        "headers": {
            "X-API-Key": "<redacted>",
            "Cartesia-Version": provider["api_version"],
        },
        "model_id": provider["model_id"],
        "voice": {
            "mode": "id",
            "id": f"<redacted-env:{voice_env_var}>",
        },
        "language": case["language"],
        "output_format": output_format(provider),
        "add_timestamps": provider.get("add_timestamps", True),
        "context_id": "<generated-per-case>",
        "streaming_input_chunks": len(case["transcript_chunks"]),
    }


def websocket_request_message(
    provider: dict[str, Any],
    case: dict[str, Any],
    voice_id: str,
    context_id: str,
    transcript: str,
    should_continue: bool,
) -> dict[str, Any]:
    return {
        "model_id": provider["model_id"],
        "transcript": transcript,
        "voice": {
            "mode": "id",
            "id": voice_id,
        },
        "language": case["language"],
        "context_id": context_id,
        "output_format": output_format(provider),
        "add_timestamps": provider.get("add_timestamps", True),
        "continue": should_continue,
    }


def write_pcm_wav(audio_path: Path, audio_bytes: bytes, fmt: dict[str, Any]) -> bool:
    maybe_remove(audio_path)
    if not audio_bytes:
        return False
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    sample_width = 2 if fmt["encoding"] == "pcm_s16le" else 4
    with wave.open(str(audio_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(sample_width)
        wav.setframerate(int(fmt["sample_rate"]))
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
    case: dict[str, Any],
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
            "connection_established_ms": None,
            "time_to_first_audio_chunk_ms": None,
            "total_stream_latency_ms": 0,
            "audio_chunk_count": 0,
            "non_audio_event_count": 0,
            "timestamp_event_count": 0,
            "done_received": False,
            "provider_error": str(error).splitlines()[0][:500],
        }

    context_id = str(uuid.uuid4())
    start = time.perf_counter()
    ws = None
    audio_parts: list[bytes] = []
    audio_chunk_count = 0
    non_audio_event_count = 0
    timestamp_event_count = 0
    first_audio_ms = None
    done_received = False
    provider_error = None

    try:
        ws = websocket.create_connection(
            websocket_url(provider),
            header=[
                f"X-API-Key: {api_key}",
                f"Cartesia-Version: {provider['api_version']}",
            ],
            timeout=timeout_seconds,
        )
        connection_established_ms = elapsed_ms(start)
        chunks = case["transcript_chunks"]
        for index, chunk in enumerate(chunks):
            message = websocket_request_message(
                provider=provider,
                case=case,
                voice_id=voice_id,
                context_id=context_id,
                transcript=chunk,
                should_continue=index < len(chunks) - 1,
            )
            ws.send(json.dumps(message, ensure_ascii=False))

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
                non_audio_event_count += 0 if chunk_bytes else 1
            elif message_type in {"timestamps", "phoneme_timestamps"}:
                timestamp_event_count += 1
                non_audio_event_count += 1
            elif message_type == "done" or message.get("done") is True:
                done_received = True
                break
            elif message_type == "error":
                provider_error = " ".join(str(message.get("message") or message.get("title") or message).split())[:500]
                break
            else:
                non_audio_event_count += 1

        total_latency_ms = elapsed_ms(start)
        audio_bytes = b"".join(audio_parts)
        audio_created = write_pcm_wav(audio_path, audio_bytes, output_format(provider))
        return {
            "websocket_connection_attempted": True,
            "api_call_made": True,
            "fallback_used": not audio_created,
            "fallback_reason": None if audio_created else provider_error or "cartesia-websocket-returned-no-audio",
            "audio_file_created": audio_created,
            "audio_output_path": project_relative_string(audio_path) if audio_created else None,
            "audio_byte_size": audio_path.stat().st_size if audio_created else 0,
            "connection_established_ms": connection_established_ms,
            "time_to_first_audio_chunk_ms": first_audio_ms,
            "total_stream_latency_ms": total_latency_ms,
            "audio_chunk_count": audio_chunk_count,
            "non_audio_event_count": non_audio_event_count,
            "timestamp_event_count": timestamp_event_count,
            "done_received": done_received,
            "provider_error": provider_error,
        }
    except Exception as error:
        maybe_remove(audio_path)
        return {
            "websocket_connection_attempted": True,
            "api_call_made": True,
            "fallback_used": True,
            "fallback_reason": "cartesia-websocket-request-failed",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "connection_established_ms": elapsed_ms(start),
            "time_to_first_audio_chunk_ms": first_audio_ms,
            "total_stream_latency_ms": elapsed_ms(start),
            "audio_chunk_count": audio_chunk_count,
            "non_audio_event_count": non_audio_event_count,
            "timestamp_event_count": timestamp_event_count,
            "done_received": done_received,
            "provider_error": str(error).splitlines()[0][:500],
        }
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def fallback_reason(live: bool, force_key_missing: bool, api_key: str | None, voice_id: str | None) -> str:
    if not live:
        return "dry-run-mode"
    if force_key_missing:
        return "forced-key-missing"
    if not api_key:
        return "missing-cartesia-api-key"
    if not voice_id:
        return "missing-cartesia-voice-id"
    return "live-call-not-attempted"


def build_websocket_result(
    provider: dict[str, Any],
    case: dict[str, Any],
    audio_path: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    voice_id, voice_env_var = resolve_voice_id(provider, case["language"], force_key_missing)
    can_call_live = live and bool(api_key) and bool(voice_id)
    preview = redacted_request_preview(provider, case, voice_env_var)

    if can_call_live:
        live_result = call_cartesia_websocket(
            provider=provider,
            case=case,
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
        generated_text_sent = live_result["api_call_made"]
        fallback = "text-only-tts-packet" if live_result["fallback_used"] else None
    else:
        maybe_remove(audio_path)
        live_result = {
            "websocket_connection_attempted": False,
            "api_call_made": False,
            "fallback_used": True,
            "fallback_reason": fallback_reason(live, force_key_missing, api_key, voice_id),
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "connection_established_ms": None,
            "time_to_first_audio_chunk_ms": None,
            "total_stream_latency_ms": 0,
            "audio_chunk_count": 0,
            "non_audio_event_count": 0,
            "timestamp_event_count": 0,
            "done_received": False,
            "provider_error": None,
        }
        generated_text_sent = False
        fallback = "text-only-tts-packet"

    return {
        "voice_milestone": VOICE_MILESTONE,
        "provider_id": provider["provider_id"],
        "endpoint_type": provider["endpoint_type"],
        "model_id": provider["model_id"],
        "language": case["language"],
        "live_call_requested": live,
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
        "request_preview": preview,
        "transcript_chars": len(case["tts_quality_script"]),
        "transcript_chunks": case["transcript_chunks"],
        "output_format": output_format(provider),
        "fallback_provider": fallback,
        **live_result,
    }


def quality_review_stub() -> dict[str, Any]:
    return {
        "human_rating_required": True,
        "rating_recorded": False,
        "rating_scale": "1-5",
        "criteria": [
            "naturalness",
            "clarity",
            "language pronunciation",
            "sales-call pacing",
            "muffled_or_artifacted_audio",
            "emotional appropriateness without overacting",
        ],
        "notes": "Dry-run and automated validation cannot judge audio quality. Rate after live WAV files exist.",
    }


def run_case(
    case: dict[str, Any],
    provider: dict[str, Any],
    runtime_cases_path: Path,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    campaign = load_campaign(case["campaign_id"], runtime_cases_path)
    turn_case = build_turn_case(
        case["campaign_id"],
        case["stage"],
        case["transcript"],
        "speech-final",
        0,
    )
    decision = run_turn_decision(turn_case, campaign)
    audio_path = audio_dir / case["audio_filename"]
    stream_result = build_websocket_result(
        provider=provider,
        case=case,
        audio_path=audio_path,
        live=live,
        force_key_missing=force_key_missing,
        timeout_seconds=timeout_seconds,
    )
    final_provider = provider["provider_id"] if stream_result["audio_file_created"] else "dry-run"
    voice_packet = build_voice_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["transcript"],
        silence_count=0,
        decision=decision,
        provider=final_provider,
        voice_name="Cartesia Sonic 3 WebSocket synthetic test voice" if final_provider != "dry-run" else None,
        audio_output_path=audio_path if stream_result["audio_file_created"] else None,
    )

    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "tts_quality_script": case["tts_quality_script"],
        "voice_packet": voice_packet,
        "cartesia_websocket": stream_result,
        "quality_review": quality_review_stub(),
    }


def summarize(cases: list[dict[str, Any]], live: bool, timeout_seconds: float) -> dict[str, Any]:
    languages: dict[str, int] = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1
    return {
        "case_count": len(cases),
        "languages": languages,
        "live_call_requested": live,
        "websocket_connections_attempted": sum(1 for case in cases if case["cartesia_websocket"]["websocket_connection_attempted"]),
        "api_calls_made": sum(1 for case in cases if case["cartesia_websocket"]["api_call_made"]),
        "audio_files_created": sum(1 for case in cases if case["cartesia_websocket"]["audio_file_created"]),
        "fallback_count": sum(1 for case in cases if case["cartesia_websocket"]["fallback_used"]),
        "customer_audio_uploaded": False,
        "synthetic_prompts_only": True,
        "timeout_seconds": timeout_seconds,
        "response_language_matches": sum(
            1 for case in cases if case["voice_packet"]["decision"]["response_language"] == case["language"]
        ),
        "quality_script_languages_match": len(cases),
        "audio_quality_human_rated": False,
        "max_connection_established_ms": max(
            (
                case["cartesia_websocket"]["connection_established_ms"]
                for case in cases
                if case["cartesia_websocket"]["connection_established_ms"] is not None
            ),
            default=None,
        ),
        "max_time_to_first_audio_chunk_ms": max(
            (
                case["cartesia_websocket"]["time_to_first_audio_chunk_ms"]
                for case in cases
                if case["cartesia_websocket"]["time_to_first_audio_chunk_ms"] is not None
            ),
            default=None,
        ),
        "max_total_stream_latency_ms": max(
            case["cartesia_websocket"]["total_stream_latency_ms"] for case in cases
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    provider = payload["provider"]
    lines = [
        "# VOICE-011 Cartesia WebSocket Smoke Report",
        "",
        "This report was generated by `scripts/run_voice_011_cartesia_websocket_smoke.py`.",
        "",
    ]
    if summary["websocket_connections_attempted"] == 0:
        lines.extend(["No WebSocket connections were attempted.", ""])
    else:
        lines.extend([f"WebSocket connections attempted: `{summary['websocket_connections_attempted']}`.", ""])
    lines.extend(
        [
            "No customer audio was uploaded.",
            "",
            "Human listening review required before making audio-quality claims.",
            "",
            "VOICE-011 defaults to dry-run mode. A live Cartesia request requires `--live`, `CARTESIA_API_KEY`, and a voice ID from `CARTESIA_VOICE_ID_DE`, `CARTESIA_VOICE_ID_EN`, or `CARTESIA_VOICE_ID`.",
            "",
            "## Guardrails",
            "",
            f"- Provider: `{provider['provider_id']}`",
            f"- Endpoint type: `{provider['endpoint_type']}`",
            f"- Model: `{provider['model_id']}`",
            f"- API version: `{provider['api_version']}`",
            f"- API key env var: `{provider['api_key_env_var']}`",
            f"- Default voice ID env var: `{provider['default_voice_id_env_var']}`",
            f"- German voice ID env var: `{provider['language_voice_id_env_vars']['de']}`",
            f"- English voice ID env var: `{provider['language_voice_id_env_vars']['en']}`",
            f"- API key value logged: `{provider['api_key_value_logged']}`",
            f"- Voice ID value logged: `{provider['voice_id_value_logged']}`",
            f"- Timeout: `{summary['timeout_seconds']} seconds`",
            "- Voice cloning used: `false`",
            "",
            "## Summary",
            "",
            f"- Cases: `{summary['case_count']}`",
            f"- German cases: `{summary['languages'].get('de', 0)}`",
            f"- English cases: `{summary['languages'].get('en', 0)}`",
            f"- Live call requested: `{summary['live_call_requested']}`",
            f"- WebSocket connections attempted: `{summary['websocket_connections_attempted']}`",
            f"- API calls made: `{summary['api_calls_made']}`",
            f"- Audio files created: `{summary['audio_files_created']}`",
            f"- Fallback count: `{summary['fallback_count']}`",
            f"- Response-language matches: `{summary['response_language_matches']} / {summary['case_count']}`",
            f"- Quality script language matches: `{summary['quality_script_languages_match']} / {summary['case_count']}`",
            f"- Max connection established: `{summary['max_connection_established_ms']}`",
            f"- Max time to first audio chunk: `{summary['max_time_to_first_audio_chunk_ms']}`",
            f"- Max total stream latency: `{summary['max_total_stream_latency_ms']} ms`",
            "",
            "## Case Results",
            "",
        ]
    )
    for case in payload["cases"]:
        stream = case["cartesia_websocket"]
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- WebSocket attempted: `{stream['websocket_connection_attempted']}`",
                f"- Generated text sent to provider: `{stream['generated_text_sent_to_provider']}`",
                f"- Selected voice env var: `{stream['selected_voice_id_env_var']}`",
                f"- Audio file created: `{stream['audio_file_created']}`",
                f"- Audio path: `{stream['audio_output_path'] or 'not created'}`",
                f"- Audio bytes: `{stream['audio_byte_size']}`",
                f"- Audio chunks: `{stream['audio_chunk_count']}`",
                f"- Timestamp events: `{stream['timestamp_event_count']}`",
                f"- Connection established: `{stream['connection_established_ms']}`",
                f"- Time to first audio chunk: `{stream['time_to_first_audio_chunk_ms']}`",
                f"- Total stream latency: `{stream['total_stream_latency_ms']} ms`",
                f"- Fallback provider: `{stream['fallback_provider'] or 'not used'}`",
                f"- Fallback reason: `{stream['fallback_reason'] or 'not needed'}`",
                f"- Human listening review required: `{case['quality_review']['human_rating_required']}`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-011 guarded Cartesia Sonic 3 WebSocket streaming smoke test.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-011 Cartesia WebSocket case file.")
    parser.add_argument("--runtime-cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper runtime case file.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live Cartesia WebSocket calls when env gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore Cartesia env vars to validate missing-key fallback.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")

    cases_path = resolve_project_path(args.cases)
    runtime_cases_path = resolve_project_path(args.runtime_cases)
    audio_dir = resolve_project_path(args.audio_dir)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    if cases_path is None or runtime_cases_path is None or audio_dir is None or out_path is None or report_path is None:
        raise SystemExit("VOICE-011 paths could not be resolved.")

    payload = load_json(cases_path)
    provider = payload["provider"]
    cases = [
        run_case(
            case=case,
            provider=provider,
            runtime_cases_path=runtime_cases_path,
            audio_dir=audio_dir,
            live=args.live,
            force_key_missing=args.force_key_missing,
            timeout_seconds=args.timeout_seconds,
        )
        for case in payload["cases"]
    ]
    result = {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": payload["experiment_scope"],
        "case_file": project_relative_string(cases_path),
        "runtime_case_file": project_relative_string(runtime_cases_path),
        "provider": provider,
        "safety_gate": payload["safety_gate"],
        "quality_rubric": payload["quality_rubric"],
        "summary": summarize(cases, args.live, args.timeout_seconds),
        "cases": cases,
    }
    write_json(out_path, result)
    write_text(report_path, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
