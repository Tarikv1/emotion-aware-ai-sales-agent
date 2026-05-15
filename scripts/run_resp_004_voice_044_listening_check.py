#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases
from runtime.voice.runtime_tts_delivery import attach_runtime_tts_delivery
from runtime.voice.runtime_voice_delivery import attach_runtime_voice_delivery
from runtime.providers.tts_provider_clients import project_relative_string


EXPERIMENT_ID = "RESP-004-voice-044-listening-check"
DEFAULT_CAMPAIGN_CASES = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_FOCUS_CASES = ROOT / "research" / "experiments" / "cases" / "voice-044-baseline-delivery-polish.json"
DEFAULT_CASE_IDS = ["voice-044-en-fast-filler-cleanup", "voice-044-de-connector-cleanup"]
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_OUT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT_OUT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_AUDIO_DIR = DEFAULT_OUT_DIR / "audio"


def resolve_path(path_text: str | None, default: Path) -> Path:
    if not path_text:
        return default
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_cases(focus_cases_path: Path, case_ids: list[str]) -> list[dict[str, Any]]:
    payload = load_json(focus_cases_path)
    by_id = {case["case_id"]: case for case in payload["cases"]}
    missing = [case_id for case_id in case_ids if case_id not in by_id]
    if missing:
        known = ", ".join(sorted(by_id))
        raise SystemExit(f"Unknown case id(s): {', '.join(missing)}. Known cases: {known}")
    return [by_id[case_id] for case_id in case_ids]


def build_case_packet(
    case: dict[str, Any],
    campaign: dict[str, Any],
    provider: str,
    live: bool,
    force_key_missing: bool,
    audio_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    guarded_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type=case.get("input_type", "speech-final"),
        transcript=case.get("transcript", ""),
        silence_count=int(case.get("silence_count", 0)),
        candidate_response_override=case["candidate_response"],
    )
    voice_packet = attach_runtime_voice_delivery(
        guarded_packet,
        campaign,
        provider_key=provider,
        seed=f"{case['case_id']}:resp-004-voice-044-listening-check",
    )
    return attach_runtime_tts_delivery(
        voice_packet,
        provider_key=provider,
        live=live,
        force_key_missing=force_key_missing,
        audio_dir=audio_dir,
        timeout_seconds=timeout_seconds,
        command_name="scripts/run_resp_004_voice_044_listening_check.py",
    )


def quality_review() -> dict[str, Any]:
    return {
        "human_listening_review_required": True,
        "human_listening_review_recorded": False,
        "quality_claim_allowed": False,
        "criteria": [
            "naturalness",
            "trust-repair rhythm",
            "German connector clarity",
            "English phrase flow",
            "sales-call pacing",
            "AI-obviousness",
            "protected text preservation",
            "whether VOICE-044 is good enough before returning to RAG-018",
        ],
    }


def compact_tts_delivery(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider_key": delivery["provider_key"],
        "provider_id": delivery["provider_id"],
        "provider_name": delivery["provider_name"],
        "endpoint_type": delivery["endpoint_type"],
        "model_id": delivery["model_id"],
        "language": delivery["language"],
        "live_call_requested": delivery["live_call_requested"],
        "requires_api_key": delivery["requires_api_key"],
        "api_key_env_var": delivery["api_key_env_var"],
        "selected_voice_id_env_var": delivery["selected_voice_id_env_var"],
        "api_key_present": delivery["api_key_present"],
        "voice_id_present": delivery["voice_id_present"],
        "api_key_value_logged": delivery["api_key_value_logged"],
        "voice_id_value_logged": delivery["voice_id_value_logged"],
        "api_call_made": delivery["provider_calls_made"],
        "generated_text_sent_to_provider": delivery["generated_text_sent_to_provider"],
        "audio_file_created": delivery["audio_file_created"],
        "audio_output_path": delivery["audio_output_path"],
        "audio_byte_size": delivery["audio_byte_size"],
        "fallback_used": delivery["fallback_used"],
        "fallback_reason": delivery["fallback_reason"],
        "customer_audio_uploaded": delivery["customer_audio_uploaded"],
        "voice_cloning_used": delivery["voice_cloning_used"],
        "synthetic_prompt_only": delivery["synthetic_prompt_only"],
        "tts_input_source": delivery["tts_input_source"],
        "tts_input_text": delivery["tts_input_text"],
        "provider_rendering_used": delivery["provider_rendering_used"],
        "voice_settings": delivery["voice_settings"],
        "request_preview": delivery["request_preview"],
        "timeout_seconds": delivery["timeout_seconds"],
        "time_to_first_audio_ms": delivery["time_to_first_audio_ms"],
        "total_provider_latency_ms": delivery["total_provider_latency_ms"],
        "provider_error_summary": delivery["provider_error_summary"],
        "asset_log": delivery["asset_log"],
        "validation": delivery["validation"],
    }


def run_case(
    case: dict[str, Any],
    *,
    campaign: dict[str, Any],
    cases_path: Path,
    provider: str,
    live: bool,
    force_key_missing: bool,
    audio_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    packet = build_case_packet(case, campaign, provider, live, force_key_missing, audio_dir, timeout_seconds)
    voice_delivery = packet["voice_delivery"]
    tts_delivery = packet["tts_delivery"]
    polish = voice_delivery["voice_baseline_delivery_polish"]
    profile = voice_delivery["voice_private_pattern_profile"]
    return {
        "case_id": case["case_id"].replace("voice-044", "resp-004-voice-044"),
        "source_case_id": case["case_id"],
        "title": case["title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "source_cases": project_relative_string(cases_path),
        "transcript": case["transcript"],
        "final_response": packet["final_response"],
        "runtime_voice_delivery_id": packet["runtime_voice_delivery_id"],
        "runtime_tts_delivery_id": packet["runtime_tts_delivery_id"],
        "voice_milestone": "VOICE-044",
        "voice_baseline_delivery_polish": {
            "enabled": polish["enabled"],
            "applied": polish["applied"],
            "adjustment_count": polish["adjustment_count"],
            "adjustments": polish["adjustments"],
            "validation": polish["validation"],
            "runtime_boundary": polish["runtime_boundary"],
        },
        "voice_private_pattern_profile": {
            "enabled": profile["enabled"],
            "applied": profile["applied"],
            "blocked_reason": profile["blocked_reason"],
            "validation": profile["validation"],
            "runtime_boundary": profile["runtime_boundary"],
        },
        "provider_rendering": {
            "rendered_text": voice_delivery["provider_rendering"]["rendered_text"],
            "provider_tag_count": voice_delivery["provider_rendering"]["provider_tag_count"],
            "protected_segment_provider_tag_count": voice_delivery["provider_rendering"]["protected_segment_provider_tag_count"],
            "voice_settings": voice_delivery["provider_rendering"].get("voice_settings") or {},
        },
        "tts_delivery": compact_tts_delivery(tts_delivery),
        "quality_review": quality_review(),
    }


def build_summary(cases: list[dict[str, Any]], provider: str, live: bool, timeout_seconds: float) -> dict[str, Any]:
    return {
        "case_count": len(cases),
        "english_case_count": sum(1 for case in cases if case["language"] == "en"),
        "german_case_count": sum(1 for case in cases if case["language"] == "de"),
        "providers": [provider],
        "live_call_requested": live,
        "api_calls_made": sum(1 for case in cases if case["tts_delivery"]["api_call_made"]),
        "audio_files_created": sum(1 for case in cases if case["tts_delivery"]["audio_file_created"]),
        "fallback_count": sum(1 for case in cases if case["tts_delivery"]["fallback_used"]),
        "baseline_polish_applied_count": sum(1 for case in cases if case["voice_baseline_delivery_polish"]["applied"]),
        "baseline_polish_validation_passed": all(
            case["voice_baseline_delivery_polish"]["validation"]["passed"] for case in cases
        ),
        "private_pattern_profile_applied_count": sum(
            1 for case in cases if case["voice_private_pattern_profile"]["applied"]
        ),
        "customer_audio_uploaded": any(case["tts_delivery"]["customer_audio_uploaded"] for case in cases),
        "voice_cloning_used": any(case["tts_delivery"]["voice_cloning_used"] for case in cases),
        "synthetic_prompts_only": all(case["tts_delivery"]["synthetic_prompt_only"] for case in cases),
        "timeout_seconds": timeout_seconds,
        "human_listening_review_recorded": False,
        "quality_claim_allowed": False,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RESP-004 VOICE-044 Listening Check Report",
        "",
        "This report was generated by `scripts/run_resp_004_voice_044_listening_check.py`.",
        "",
        "RESP-004 is a separate listening-check checkpoint for the VOICE-044 polished baseline. RESP-003 remains the TTS bridge; RESP-004 owns this test's scope, evidence, and review gate.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- English cases: `{summary['english_case_count']}`",
        f"- German cases: `{summary['german_case_count']}`",
        f"- Provider: `{', '.join(summary['providers'])}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- VOICE-044 validation passed: `{summary['baseline_polish_validation_passed']}`",
        f"- VOICE-041 profile applications: `{summary['private_pattern_profile_applied_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Human listening review recorded: `{summary['human_listening_review_recorded']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Cases",
    ]
    for case in payload["cases"]:
        tts = case["tts_delivery"]
        polish = case["voice_baseline_delivery_polish"]
        lines.extend(
            [
                "",
                f"### {case['case_id']}",
                "",
                f"- Source case: `{case['source_case_id']}`",
                f"- Title: `{case['title']}`",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- VOICE-044 applied: `{polish['applied']}`",
                f"- VOICE-044 adjustments: `{polish['adjustment_count']}`",
                f"- TTS bridge: `{case['runtime_tts_delivery_id']}`",
                f"- TTS input source: `{tts['tts_input_source']}`",
                f"- API call made: `{tts['api_call_made']}`",
                f"- Audio file created: `{tts['audio_file_created']}`",
                f"- Audio path: `{tts['audio_output_path'] or 'not created'}`",
                f"- Fallback reason: `{tts['fallback_reason'] or 'not needed'}`",
                "",
                "TTS input:",
                "",
                tts["tts_input_text"],
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Dry-run by default.",
            "- Live calls require `--live`, provider key, voice ID, and bounded timeout.",
            "- No customer audio upload.",
            "- No raw private audio read.",
            "- No transcription.",
            "- No voice cloning.",
            "- API keys and raw voice IDs are never written to JSON, Markdown, stdout, or logs.",
            "- No audio quality claim is allowed until Tarik records a human listening review.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RESP-004 live-capable VOICE-044 polished-baseline listening check.")
    parser.add_argument("--cases", default=str(DEFAULT_CAMPAIGN_CASES), help="Campaign wrapper case file.")
    parser.add_argument("--focus-cases", default=str(DEFAULT_FOCUS_CASES), help="VOICE-044 focus case file.")
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        help="VOICE-044 focus case id to include. Defaults to the English/German VOICE-044 artifact cases.",
    )
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs", help="TTS provider to prepare or call.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live provider API calls when env gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore provider env vars to validate missing-key fallback.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")

    case_ids = args.case_ids or DEFAULT_CASE_IDS
    cases_path = resolve_path(args.cases, DEFAULT_CAMPAIGN_CASES)
    focus_cases_path = resolve_path(args.focus_cases, DEFAULT_FOCUS_CASES)
    audio_dir = resolve_path(args.audio_dir, DEFAULT_AUDIO_DIR)
    out_path = resolve_path(args.out, DEFAULT_OUT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT_OUT)
    campaigns, _cases = load_realtime_cases(cases_path)
    results: list[dict[str, Any]] = []
    for case in selected_cases(focus_cases_path, case_ids):
        campaign = find_campaign(campaigns, case["campaign_id"])
        results.append(
            run_case(
                case,
                campaign=campaign,
                cases_path=cases_path,
                provider=args.provider,
                live=args.live,
                force_key_missing=args.force_key_missing,
                audio_dir=audio_dir,
                timeout_seconds=args.timeout_seconds,
            )
        )
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "checkpoint_title": "RESP-004 VOICE-044 polished-baseline listening check",
        "case_file": project_relative_string(cases_path),
        "focus_case_file": project_relative_string(focus_cases_path),
        "source_runtime_tts_delivery_id": "RESP-003-runtime-live-tts",
        "source_voice_milestone": "VOICE-044",
        "provider": args.provider,
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(case["tts_delivery"]["api_call_made"] for case in results),
            "requires_api_key": args.live and not args.force_key_missing,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
            "resp_003_preserved_as_bridge": True,
        },
        "summary": build_summary(results, args.provider, args.live, args.timeout_seconds),
        "cases": results,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
