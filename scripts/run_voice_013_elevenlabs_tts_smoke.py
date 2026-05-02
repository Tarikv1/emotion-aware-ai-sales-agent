#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from generate_voice_response import (
    DEFAULT_CASES_PATH,
    build_voice_packet,
    project_relative_string,
    resolve_project_path,
)
from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-013"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-013-elevenlabs-tts-smoke.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-013-elevenlabs-tts-smoke.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-013-elevenlabs-tts-smoke-report.md"
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


def endpoint_url(provider: dict[str, Any], voice_id: str, redacted: bool = False, voice_env_var: str | None = None) -> str:
    rendered_voice = f"<redacted-env:{voice_env_var}>" if redacted else urllib.parse.quote(voice_id, safe="")
    base_url = provider["endpoint_url_template"].format(voice_id=rendered_voice)
    query = {
        "output_format": provider["default_output_format"],
        "enable_logging": str(bool(provider.get("enable_logging", False))).lower(),
    }
    return f"{base_url}?{urllib.parse.urlencode(query)}"


def redacted_request_preview(provider: dict[str, Any], case: dict[str, Any], voice_env_var: str) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": endpoint_url(provider, "<redacted>", redacted=True, voice_env_var=voice_env_var),
        "headers": {
            "xi-api-key": "<redacted>",
            "Content-Type": "application/json",
        },
        "body": {
            "text": case["tts_quality_script"],
            "model_id": provider["model_id"],
            "language_code": normalize_language(case["language"]),
            "voice_settings": provider["voice_settings"],
        },
    }


def live_request_body(provider: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": case["tts_quality_script"],
        "model_id": provider["model_id"],
        "language_code": normalize_language(case["language"]),
        "voice_settings": provider["voice_settings"],
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
        return {
            "type": None,
            "code": None,
            "message": None,
        }
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
    return {
        "type": "unparsed-provider-error",
        "code": None,
        "message": error_text[:300],
    }


def call_elevenlabs_stream(
    provider: dict[str, Any],
    case: dict[str, Any],
    audio_path: Path,
    api_key: str,
    voice_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    maybe_remove(audio_path)
    body = live_request_body(provider, case)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint_url(provider, voice_id),
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
            time_to_first_audio_byte_ms = elapsed_ms(start)
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
                "time_to_first_audio_byte_ms": time_to_first_audio_byte_ms,
                "total_provider_latency_ms": total_latency_ms,
                "provider_error": None,
            }
    except urllib.error.HTTPError as error:
        maybe_remove(audio_path)
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
            "time_to_first_audio_byte_ms": None,
            "total_provider_latency_ms": elapsed_ms(start),
            "provider_error": read_error_body(error),
        }
    except Exception as error:
        maybe_remove(audio_path)
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
            "time_to_first_audio_byte_ms": None,
            "total_provider_latency_ms": elapsed_ms(start),
            "provider_error": str(error).splitlines()[0][:700],
        }


def fallback_reason(live: bool, force_key_missing: bool, api_key: str | None, voice_id: str | None) -> str:
    if not live:
        return "dry-run-mode"
    if force_key_missing:
        return "forced-key-missing"
    if not api_key:
        return "missing-elevenlabs-api-key"
    if not voice_id:
        return "missing-elevenlabs-voice-id"
    return "live-call-not-attempted"


def build_elevenlabs_result(
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
        live_result = call_elevenlabs_stream(
            provider=provider,
            case=case,
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
            "request_id_present": False,
            "time_to_first_audio_byte_ms": None,
            "total_provider_latency_ms": 0,
            "provider_error": None,
        }
        fallback_used = True
        fallback = "text-only-tts-packet"
        generated_text_sent = False

    provider_error_summary = parse_provider_error(live_result.get("provider_error"))

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
        "enable_logging": bool(provider.get("enable_logging", False)),
        "customer_audio_uploaded": False,
        "generated_text_sent_to_provider": generated_text_sent,
        "synthetic_prompt_only": True,
        "voice_clone_used": False,
        "custom_voice_used": False,
        "timeout_seconds": timeout_seconds,
        "request_preview": preview,
        "transcript_chars": len(case["tts_quality_script"]),
        "fallback_provider": fallback,
        "provider_error_summary": provider_error_summary,
        **live_result,
    }


def quality_script_language_matches(case: dict[str, Any]) -> bool:
    text = case["tts_quality_script"].lower()
    if case["language"] == "de":
        markers = ["ich", "ihnen", "rückruf", "fachberater", "unverbindlich", "garantie"]
        english_markers = ["the ", "workflow", "callback", "specialist"]
        return any(marker in text for marker in markers) and not any(marker in text for marker in english_markers)
    markers = ["the ", "workflow", "callback", "specialist", "performance"]
    german_markers = [" ich ", " ihnen ", "rückruf", "fachberater"]
    return any(marker in text for marker in markers) and not any(marker in text for marker in german_markers)


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
    elevenlabs_result = build_elevenlabs_result(
        provider=provider,
        case=case,
        audio_path=audio_path,
        live=live,
        force_key_missing=force_key_missing,
        timeout_seconds=timeout_seconds,
    )
    final_provider = provider["provider_id"] if elevenlabs_result["audio_file_created"] else "dry-run"
    voice_packet = build_voice_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["transcript"],
        silence_count=0,
        decision=decision,
        provider=final_provider,
        voice_name="ElevenLabs streaming synthetic test voice" if final_provider != "dry-run" else None,
        audio_output_path=audio_path if elevenlabs_result["audio_file_created"] else None,
    )

    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "tts_quality_script": case["tts_quality_script"],
        "voice_packet": voice_packet,
        "elevenlabs_tts": elevenlabs_result,
        "quality_review": {
            "human_rating_required": True,
            "human_rating_recorded": False,
            "quality_claim_allowed": False,
            "criteria": [
                "naturalness",
                "clarity",
                "language pronunciation",
                "sales-call pacing",
                "muffled_or_artifacted_audio",
                "emotional appropriateness without overacting",
                "trustworthiness",
            ],
        },
        "quality_script_language_match": quality_script_language_matches(case),
    }


def summarize(cases: list[dict[str, Any]], live: bool, timeout_seconds: float) -> dict[str, Any]:
    languages: dict[str, int] = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1
    return {
        "case_count": len(cases),
        "languages": languages,
        "live_call_requested": live,
        "api_calls_made": sum(1 for case in cases if case["elevenlabs_tts"]["api_call_made"]),
        "audio_files_created": sum(1 for case in cases if case["elevenlabs_tts"]["audio_file_created"]),
        "fallback_count": sum(1 for case in cases if case["elevenlabs_tts"]["fallback_used"]),
        "customer_audio_uploaded": False,
        "synthetic_prompts_only": True,
        "timeout_seconds": timeout_seconds,
        "response_language_matches": sum(
            1 for case in cases if case["voice_packet"]["decision"]["response_language"] == case["language"]
        ),
        "quality_script_languages_match": sum(1 for case in cases if case["quality_script_language_match"]),
        "audio_quality_human_rated": False,
        "enable_logging": any(case["elevenlabs_tts"]["enable_logging"] for case in cases),
        "max_time_to_first_audio_byte_ms": max(
            (
                case["elevenlabs_tts"]["time_to_first_audio_byte_ms"]
                for case in cases
                if case["elevenlabs_tts"]["time_to_first_audio_byte_ms"] is not None
            ),
            default=None,
        ),
        "max_total_provider_latency_ms": max(
            case["elevenlabs_tts"]["total_provider_latency_ms"] for case in cases
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    provider = payload["provider"]
    lines = [
        "# VOICE-013 ElevenLabs TTS Smoke Report",
        "",
        "This report was generated by `scripts/run_voice_013_elevenlabs_tts_smoke.py`.",
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
            "Human listening review required before making audio-quality claims.",
            "",
            "VOICE-013 defaults to dry-run mode. A live ElevenLabs request requires `--live`, `ELEVENLABS_API_KEY`, and a voice ID from `ELEVENLABS_VOICE_ID_DE`, `ELEVENLABS_VOICE_ID_EN`, or `ELEVENLABS_VOICE_ID`.",
            "",
            "## Guardrails",
            "",
            f"- Provider: `{provider['provider_id']}`",
            f"- Endpoint type: `{provider['endpoint_type']}`",
            f"- Model: `{provider['model_id']}`",
            f"- Output format: `{provider['default_output_format']}`",
            f"- API key env var: `{provider['api_key_env_var']}`",
            f"- Default voice ID env var: `{provider['default_voice_id_env_var']}`",
            f"- German voice ID env var: `{provider['language_voice_id_env_vars']['de']}`",
            f"- English voice ID env var: `{provider['language_voice_id_env_vars']['en']}`",
            f"- API key value logged: `{provider['api_key_value_logged']}`",
            f"- Voice ID value logged: `{provider['voice_id_value_logged']}`",
            f"- Enable logging: `{provider['enable_logging']}`",
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
            f"- Quality script language matches: `{summary['quality_script_languages_match']} / {summary['case_count']}`",
            f"- Max time to first audio byte: `{summary['max_time_to_first_audio_byte_ms']}`",
            f"- Max total provider latency: `{summary['max_total_provider_latency_ms']} ms`",
            "",
            "## Case Results",
            "",
        ]
    )
    for case in payload["cases"]:
        elevenlabs = case["elevenlabs_tts"]
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- API call made: `{elevenlabs['api_call_made']}`",
                f"- Generated text sent to provider: `{elevenlabs['generated_text_sent_to_provider']}`",
                f"- Selected voice env var: `{elevenlabs['selected_voice_id_env_var']}`",
                f"- Audio file created: `{elevenlabs['audio_file_created']}`",
                f"- Audio path: `{elevenlabs['audio_output_path'] or 'not created'}`",
                f"- Audio bytes: `{elevenlabs['audio_byte_size']}`",
                f"- HTTP status: `{elevenlabs['http_status']}`",
                f"- Response content type: `{elevenlabs['response_content_type']}`",
                f"- Time to first audio byte: `{elevenlabs['time_to_first_audio_byte_ms']}`",
                f"- Total provider latency: `{elevenlabs['total_provider_latency_ms']} ms`",
                f"- Fallback provider: `{elevenlabs['fallback_provider'] or 'not used'}`",
                f"- Fallback reason: `{elevenlabs['fallback_reason'] or 'not needed'}`",
                f"- Provider error code: `{elevenlabs['provider_error_summary']['code'] or 'none'}`",
                f"- Provider error message: `{elevenlabs['provider_error_summary']['message'] or 'none'}`",
                f"- Human listening review required: `{case['quality_review']['human_rating_required']}`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-013 guarded ElevenLabs streaming TTS smoke test.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-013 ElevenLabs case file.")
    parser.add_argument("--runtime-cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper runtime case file.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live ElevenLabs API calls when env gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore ElevenLabs env vars to validate missing-key fallback.")
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
        raise SystemExit("VOICE-013 paths could not be resolved.")

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
