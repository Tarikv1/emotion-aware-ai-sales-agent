#!/usr/bin/env python3
import argparse
import json
import time
from pathlib import Path

from generate_voice_response import (
    DEFAULT_CASES_PATH,
    build_voice_packet,
    project_relative_string,
    resolve_project_path,
    synthesize_with_windows_sapi,
)
from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-008"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-008-local-tts-smoke.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-008-local-tts-smoke-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated"


SMOKE_CASES = [
    {
        "case_id": "VOICE-008-C01",
        "case_title": "German local TTS smoke",
        "language": "de",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "stage": "relevance-check",
        "transcript": "Nur wenn Sie garantieren koennen, dass es stabil ist.",
        "audio_filename": "VOICE-008-C01-de-local-tts.wav",
    },
    {
        "case_id": "VOICE-008-C02",
        "case_title": "English local TTS smoke",
        "language": "en",
        "campaign_id": "campaign-prod-005-b2b-software",
        "stage": "relevance-check",
        "transcript": "Can you guarantee the performance will be better?",
        "audio_filename": "VOICE-008-C02-en-local-tts.wav",
    },
]


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def load_campaign(campaign_id: str, cases_path: Path) -> dict:
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, campaign_id)
    campaign["_case_file"] = cases_path
    return campaign


def maybe_remove(path: Path) -> None:
    if path.exists():
        try:
            path.unlink()
        except PermissionError:
            pass


def clean_fallback_reason(reason: str) -> str:
    first_line = " ".join(reason.splitlines()[0].split())
    if "No voice installed on the system" in reason:
        return "Windows SAPI is available, but no usable local voice is installed or allowed by the current security setting."
    return first_line or "Local TTS synthesis was unavailable."


def run_case(case: dict, cases_path: Path, audio_dir: Path, force_fallback: bool) -> dict:
    campaign = load_campaign(case["campaign_id"], cases_path)
    turn_case = build_turn_case(
        case["campaign_id"],
        case["stage"],
        case["transcript"],
        "speech-final",
        0,
    )
    decision = run_turn_decision(turn_case, campaign)
    audio_path = audio_dir / case["audio_filename"]
    maybe_remove(audio_path)

    fallback_reason = None
    audio_created = False
    generation_start = time.perf_counter()
    if force_fallback:
        fallback_reason = "Forced fallback requested for deterministic dry-run validation."
    else:
        try:
            synthesize_with_windows_sapi(decision["agent_response"], audio_path, voice_name=None)
            audio_created = audio_path.exists() and audio_path.stat().st_size > 44
            if not audio_created:
                fallback_reason = "Windows SAPI did not create a playable WAV."
        except SystemExit as exc:
            fallback_reason = clean_fallback_reason(str(exc))
            maybe_remove(audio_path)
    generation_latency_ms = elapsed_ms(generation_start)

    final_provider = "windows-sapi" if audio_created else "dry-run"
    voice_packet = build_voice_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["transcript"],
        silence_count=0,
        decision=decision,
        provider=final_provider,
        voice_name=None,
        audio_output_path=audio_path if audio_created else None,
    )

    audio_relative = project_relative_string(audio_path) if audio_created else None
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "voice_packet": voice_packet,
        "local_tts": {
            "voice_milestone": VOICE_MILESTONE,
            "provider_attempted": "windows-sapi",
            "final_provider": final_provider,
            "fallback_provider": "dry-run",
            "fallback_used": not audio_created,
            "fallback_reason": fallback_reason,
            "audio_file_created": audio_created,
            "audio_output_path": audio_relative,
            "audio_byte_size": audio_path.stat().st_size if audio_created else 0,
            "generation_latency_ms": generation_latency_ms,
            "requires_api_key": False,
            "api_calls_made": False,
            "cloud_provider_used": False,
            "customer_audio_uploaded": False,
            "synthetic_voice_only": True,
            "consent_boundary": "synthetic-test-voice-only",
        },
    }


def summarize(cases: list[dict]) -> dict:
    languages = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1
    return {
        "case_count": len(cases),
        "languages": languages,
        "provider_attempted": "windows-sapi",
        "api_calls_made": False,
        "requires_api_key": False,
        "cloud_provider_used": False,
        "customer_audio_uploaded": False,
        "synthetic_voice_only": True,
        "audio_file_success_count": sum(1 for case in cases if case["local_tts"]["audio_file_created"]),
        "fallback_count": sum(1 for case in cases if case["local_tts"]["fallback_used"]),
        "fallback_safe_count": sum(
            1
            for case in cases
            if case["local_tts"]["fallback_provider"] == "dry-run"
            and case["local_tts"]["requires_api_key"] is False
        ),
        "response_language_matches": sum(
            1
            for case in cases
            if case["voice_packet"]["decision"]["response_language"] == case["language"]
        ),
        "tts_text_matches_decision": sum(
            1
            for case in cases
            if case["voice_packet"]["tts_text"] == case["voice_packet"]["decision"]["agent_response"]
        ),
        "max_generation_latency_ms": max((case["local_tts"]["generation_latency_ms"] for case in cases), default=0),
    }


def render_report(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-008 Local TTS Smoke Report",
        "",
        "This report was generated by `scripts/run_voice_008_local_tts_smoke.py`.",
        "",
        "No API calls were made.",
        "",
        "No customer audio was uploaded.",
        "",
        "VOICE-008 attempts local Windows SAPI TTS and falls back to dry-run fallback metadata when local audio generation is unavailable.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- German cases: `{summary['languages'].get('de', 0)}`",
        f"- English cases: `{summary['languages'].get('en', 0)}`",
        f"- Provider attempted: `{summary['provider_attempted']}`",
        f"- Audio files created: `{summary['audio_file_success_count']}`",
        f"- Dry-run fallback count: `{summary['fallback_count']}`",
        f"- Response-language matches: `{summary['response_language_matches']} / {summary['case_count']}`",
        f"- TTS text matches decision: `{summary['tts_text_matches_decision']} / {summary['case_count']}`",
        f"- Max local TTS generation latency: `{summary['max_generation_latency_ms']} ms`",
        "",
        "## Case Results",
        "",
    ]
    for case in payload["cases"]:
        local_tts = case["local_tts"]
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- Final provider: `{local_tts['final_provider']}`",
                f"- Audio file created: `{local_tts['audio_file_created']}`",
                f"- Audio path: `{local_tts['audio_output_path'] or 'not created'}`",
                f"- Audio bytes: `{local_tts['audio_byte_size']}`",
                f"- Fallback used: `{local_tts['fallback_used']}`",
                f"- Fallback reason: {local_tts['fallback_reason'] or 'not needed'}",
                f"- Generation latency: `{local_tts['generation_latency_ms']} ms`",
                "",
            ]
        )
    return "\n".join(lines)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-008 local TTS smoke test with dry-run fallback.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated WAV files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--force-fallback", action="store_true", help="Skip local TTS synthesis and validate fallback path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    audio_dir = resolve_project_path(args.audio_dir)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    if cases_path is None or audio_dir is None or out_path is None or report_path is None:
        raise SystemExit("VOICE-008 paths could not be resolved.")

    cases = [run_case(case, cases_path, audio_dir, args.force_fallback) for case in SMOKE_CASES]
    payload = {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": "local no-key TTS audio smoke test with dry-run fallback",
        "case_file": project_relative_string(cases_path),
        "audio_dir": project_relative_string(audio_dir),
        "summary": summarize(cases),
        "cases": cases,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
