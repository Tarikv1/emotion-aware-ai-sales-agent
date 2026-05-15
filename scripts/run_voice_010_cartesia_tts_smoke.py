#!/usr/bin/env python3
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

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


VOICE_MILESTONE = "VOICE-010"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-010-cartesia-tts-smoke.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-010-cartesia-tts-smoke.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-010-cartesia-tts-smoke-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated"


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
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


def load_campaign(campaign_id: str, cases_path: Path) -> dict:
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, campaign_id)
    campaign["_case_file"] = cases_path
    return campaign


def redacted_request_preview(provider: dict, transcript: str, language: str) -> dict:
    return {
        "method": "POST",
        "url": provider["endpoint_url"],
        "headers": {
            "Authorization": "Bearer <redacted>",
            "Cartesia-Version": provider["api_version"],
            "Content-Type": "application/json",
        },
        "body": {
            "model_id": provider["model_id"],
            "transcript": transcript,
            "voice": {
                "mode": "id",
                "id": f"<redacted-env:{provider['voice_id_env_var']}>",
            },
            "output_format": provider["default_output_format"],
            "language": language,
            "generation_config": provider["generation_config"],
            "save": provider["save"],
        },
    }


def live_request_body(provider: dict, transcript: str, language: str, voice_id: str) -> dict:
    body = redacted_request_preview(provider, transcript, language)["body"]
    body["voice"]["id"] = voice_id
    return body


def read_error_body(error: urllib.error.HTTPError) -> str:
    try:
        raw = error.read(2048)
    except Exception:
        raw = b""
    text = raw.decode("utf-8", errors="replace").strip()
    return " ".join(text.split())[:500]


def call_cartesia_bytes(
    provider: dict,
    transcript: str,
    language: str,
    audio_path: Path,
    api_key: str,
    voice_id: str,
    timeout_seconds: float,
) -> dict:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    maybe_remove(audio_path)
    body = live_request_body(provider, transcript, language, voice_id)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        provider["endpoint_url"],
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Cartesia-Version": provider["api_version"],
            "Content-Type": "application/json",
        },
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            first_chunk = response.read(4096)
            time_to_first_audio_byte_ms = elapsed_ms(start)
            rest = response.read()
            total_latency_ms = elapsed_ms(start)
            audio_bytes = first_chunk + rest
            audio_path.write_bytes(audio_bytes)
            audio_created = audio_path.exists() and audio_path.stat().st_size > 44
            if not audio_created:
                maybe_remove(audio_path)
            return {
                "api_call_made": True,
                "fallback_used": not audio_created,
                "fallback_reason": None if audio_created else "cartesia-returned-empty-audio",
                "audio_file_created": audio_created,
                "audio_output_path": project_relative_string(audio_path) if audio_created else None,
                "audio_byte_size": audio_path.stat().st_size if audio_created else 0,
                "http_status": response.status,
                "response_content_type": response.headers.get("Content-Type"),
                "time_to_first_audio_byte_ms": time_to_first_audio_byte_ms,
                "total_provider_latency_ms": total_latency_ms,
                "provider_error": None,
            }
    except urllib.error.HTTPError as error:
        maybe_remove(audio_path)
        return {
            "api_call_made": True,
            "fallback_used": True,
            "fallback_reason": "cartesia-http-error",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": error.code,
            "response_content_type": error.headers.get("Content-Type") if error.headers else None,
            "time_to_first_audio_byte_ms": None,
            "total_provider_latency_ms": elapsed_ms(start),
            "provider_error": read_error_body(error),
        }
    except Exception as error:
        maybe_remove(audio_path)
        return {
            "api_call_made": True,
            "fallback_used": True,
            "fallback_reason": "cartesia-request-failed",
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": None,
            "response_content_type": None,
            "time_to_first_audio_byte_ms": None,
            "total_provider_latency_ms": elapsed_ms(start),
            "provider_error": str(error).splitlines()[0][:500],
        }


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


def build_cartesia_result(
    provider: dict,
    case: dict,
    decision: dict,
    audio_path: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict:
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    voice_id = None if force_key_missing else os.environ.get(provider["voice_id_env_var"])
    can_call_live = live and bool(api_key) and bool(voice_id)
    preview = redacted_request_preview(provider, decision["agent_response"], case["language"])

    if can_call_live:
        live_result = call_cartesia_bytes(
            provider=provider,
            transcript=decision["agent_response"],
            language=case["language"],
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
        fallback_used = live_result["fallback_used"]
        fallback = "text-only-tts-packet" if fallback_used else None
        generated_text_sent = True
    else:
        maybe_remove(audio_path)
        live_result = {
            "api_call_made": False,
            "fallback_used": True,
            "fallback_reason": fallback_reason(live, force_key_missing, api_key, voice_id),
            "audio_file_created": False,
            "audio_output_path": None,
            "audio_byte_size": 0,
            "http_status": None,
            "response_content_type": None,
            "time_to_first_audio_byte_ms": None,
            "total_provider_latency_ms": 0,
            "provider_error": None,
        }
        fallback_used = True
        fallback = "text-only-tts-packet"
        generated_text_sent = False

    return {
        "voice_milestone": VOICE_MILESTONE,
        "provider_id": provider["provider_id"],
        "endpoint_type": provider["endpoint_type"],
        "model_id": provider["model_id"],
        "language": case["language"],
        "live_call_requested": live,
        "api_key_env_var": provider["api_key_env_var"],
        "voice_id_env_var": provider["voice_id_env_var"],
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
        "fallback_provider": fallback,
        **live_result,
    }


def run_case(
    case: dict,
    provider: dict,
    runtime_cases_path: Path,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict:
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
    cartesia_result = build_cartesia_result(
        provider=provider,
        case=case,
        decision=decision,
        audio_path=audio_path,
        live=live,
        force_key_missing=force_key_missing,
        timeout_seconds=timeout_seconds,
    )
    final_provider = provider["provider_id"] if cartesia_result["audio_file_created"] else "dry-run"
    voice_packet = build_voice_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["transcript"],
        silence_count=0,
        decision=decision,
        provider=final_provider,
        voice_name="Cartesia Sonic 3 synthetic test voice" if final_provider != "dry-run" else None,
        audio_output_path=audio_path if cartesia_result["audio_file_created"] else None,
    )

    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "voice_packet": voice_packet,
        "cartesia_tts": cartesia_result,
    }


def summarize(cases: list[dict], live: bool, timeout_seconds: float) -> dict:
    languages = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1
    return {
        "case_count": len(cases),
        "languages": languages,
        "live_call_requested": live,
        "api_calls_made": sum(1 for case in cases if case["cartesia_tts"]["api_call_made"]),
        "audio_files_created": sum(1 for case in cases if case["cartesia_tts"]["audio_file_created"]),
        "fallback_count": sum(1 for case in cases if case["cartesia_tts"]["fallback_used"]),
        "customer_audio_uploaded": False,
        "synthetic_prompts_only": True,
        "timeout_seconds": timeout_seconds,
        "response_language_matches": sum(
            1 for case in cases if case["voice_packet"]["decision"]["response_language"] == case["language"]
        ),
        "tts_text_matches_decision": sum(
            1 for case in cases if case["voice_packet"]["tts_text"] == case["voice_packet"]["decision"]["agent_response"]
        ),
        "max_time_to_first_audio_byte_ms": max(
            (
                case["cartesia_tts"]["time_to_first_audio_byte_ms"]
                for case in cases
                if case["cartesia_tts"]["time_to_first_audio_byte_ms"] is not None
            ),
            default=None,
        ),
        "max_total_provider_latency_ms": max(
            case["cartesia_tts"]["total_provider_latency_ms"] for case in cases
        ),
    }


def render_report(payload: dict) -> str:
    summary = payload["summary"]
    provider = payload["provider"]
    lines = [
        "# VOICE-010 Cartesia TTS Smoke Report",
        "",
        "This report was generated by `scripts/run_voice_010_cartesia_tts_smoke.py`.",
        "",
    ]
    if summary["api_calls_made"] == 0:
        lines.extend(["No API calls were made.", ""])
    else:
        lines.extend([f"Provider API calls made: `{summary['api_calls_made']}`.", ""])
    lines.extend(
        [
            "No customer audio was uploaded.",
            "",
            "VOICE-010 defaults to dry-run mode. A live Cartesia request requires `--live`, `CARTESIA_API_KEY`, and `CARTESIA_VOICE_ID`.",
            "",
            "## Guardrails",
            "",
            f"- Provider: `{provider['provider_id']}`",
            f"- Endpoint type: `{provider['endpoint_type']}`",
            f"- Model: `{provider['model_id']}`",
            f"- API version: `{provider['api_version']}`",
            f"- API key env var: `{provider['api_key_env_var']}`",
            f"- Voice ID env var: `{provider['voice_id_env_var']}`",
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
            f"- API calls made: `{summary['api_calls_made']}`",
            f"- Audio files created: `{summary['audio_files_created']}`",
            f"- Fallback count: `{summary['fallback_count']}`",
            f"- Response-language matches: `{summary['response_language_matches']} / {summary['case_count']}`",
            f"- TTS text matches decision: `{summary['tts_text_matches_decision']} / {summary['case_count']}`",
            f"- Max time to first audio byte: `{summary['max_time_to_first_audio_byte_ms']}`",
            f"- Max total provider latency: `{summary['max_total_provider_latency_ms']} ms`",
            "",
            "## Case Results",
            "",
        ]
    )
    for case in payload["cases"]:
        cartesia = case["cartesia_tts"]
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- API call made: `{cartesia['api_call_made']}`",
                f"- Generated text sent to provider: `{cartesia['generated_text_sent_to_provider']}`",
                f"- Audio file created: `{cartesia['audio_file_created']}`",
                f"- Audio path: `{cartesia['audio_output_path'] or 'not created'}`",
                f"- Audio bytes: `{cartesia['audio_byte_size']}`",
                f"- HTTP status: `{cartesia['http_status']}`",
                f"- Time to first audio byte: `{cartesia['time_to_first_audio_byte_ms']}`",
                f"- Total provider latency: `{cartesia['total_provider_latency_ms']} ms`",
                f"- Fallback provider: `{cartesia['fallback_provider'] or 'not used'}`",
                f"- Fallback reason: `{cartesia['fallback_reason'] or 'not needed'}`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-010 guarded Cartesia Sonic 3 TTS smoke test.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-010 Cartesia case file.")
    parser.add_argument("--runtime-cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper runtime case file.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live Cartesia API calls when env gates are satisfied.")
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
        raise SystemExit("VOICE-010 paths could not be resolved.")

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
        "summary": summarize(cases, args.live, args.timeout_seconds),
        "cases": cases,
    }
    write_json(out_path, result)
    write_text(report_path, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
