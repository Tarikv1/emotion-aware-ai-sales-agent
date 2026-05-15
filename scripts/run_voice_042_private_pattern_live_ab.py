#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from copy import deepcopy
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


EXPERIMENT_ID = "VOICE-042-private-pattern-live-ab"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-042-private-pattern-live-ab.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_OUT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT_OUT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_AUDIO_DIR = DEFAULT_OUT_DIR / "audio"


def resolve_path(path_text: str | None, default: Path) -> Path:
    if not path_text:
        return default
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact_tts_delivery(tts: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "runtime_tts_delivery_id",
        "source_runtime_voice_delivery_id",
        "provider_key",
        "provider_id",
        "provider_name",
        "endpoint_type",
        "model_id",
        "language",
        "live_call_requested",
        "requires_api_key",
        "api_key_env_var",
        "selected_voice_id_env_var",
        "api_key_present",
        "voice_id_present",
        "api_key_value_logged",
        "voice_id_value_logged",
        "customer_audio_uploaded",
        "generated_text_sent_to_provider",
        "synthetic_prompt_only",
        "voice_cloning_used",
        "timeout_seconds",
        "tts_input_source",
        "tts_input_text",
        "provider_rendering_used",
        "voice_settings",
        "request_preview",
        "provider_calls_made",
        "audio_file_created",
        "audio_output_path",
        "audio_byte_size",
        "fallback_used",
        "fallback_reason",
        "http_status",
        "response_content_type",
        "request_id_present",
        "time_to_first_audio_ms",
        "total_provider_latency_ms",
        "provider_error_summary",
        "validation",
        "asset_log",
    ]
    return {key: tts.get(key) for key in keys}


def campaign_for_variant(base_campaign: dict[str, Any], profile: dict[str, Any] | None) -> dict[str, Any]:
    campaign = deepcopy(base_campaign)
    campaign.pop("voice_private_pattern_profile", None)
    campaign.pop("private_speech_pattern_profile", None)
    if profile is not None:
        campaign["voice_private_pattern_profile"] = deepcopy(profile)
    return campaign


def build_variant_packet(
    case: dict[str, Any],
    campaign: dict[str, Any],
    *,
    provider_key: str,
    seed: str,
) -> dict[str, Any]:
    guarded_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type=case.get("input_type", "speech-final"),
        transcript=case.get("transcript", ""),
        silence_count=int(case.get("silence_count", 0)),
        candidate_response_override=case.get("candidate_response"),
    )
    return attach_runtime_voice_delivery(
        guarded_packet,
        campaign,
        provider_key=provider_key,
        seed=seed,
    )


def run_variant(
    case: dict[str, Any],
    base_campaign: dict[str, Any],
    *,
    profile: dict[str, Any] | None,
    variant_kind: str,
    provider_key: str,
    live: bool,
    force_key_missing: bool,
    audio_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    campaign = campaign_for_variant(base_campaign, profile)
    voice_packet = build_variant_packet(
        case,
        campaign,
        provider_key=provider_key,
        seed=f"{case['case_id']}:voice-042-shared-text",
    )
    tts_packet = attach_runtime_tts_delivery(
        voice_packet,
        provider_key=provider_key,
        live=live,
        force_key_missing=force_key_missing,
        audio_dir=audio_dir / variant_kind,
        timeout_seconds=timeout_seconds,
        command_name="scripts/run_voice_042_private_pattern_live_ab.py",
    )
    voice_delivery = tts_packet["voice_delivery"]
    profile_result = voice_delivery["voice_private_pattern_profile"]
    tts = tts_packet["tts_delivery"]
    return {
        "variant_kind": variant_kind,
        "source_checkpoint": (
            "RESP-002 shaped runtime without VOICE-041"
            if profile is None
            else "RESP-002 shaped runtime with accepted VOICE-041 private pattern profile"
        ),
        "provider_key": provider_key,
        "language": voice_delivery["language"],
        "final_response": tts_packet["final_response"],
        "voice_private_pattern_profile": {
            "enabled": profile_result["enabled"],
            "applied": profile_result["applied"],
            "blocked_reason": profile_result["blocked_reason"],
            "rhythm_density_action": profile_result["rhythm_density_action"],
            "presence_action": profile_result["presence_action"],
            "setting_adjustments": profile_result["setting_adjustments"],
            "validation": profile_result["validation"],
            "runtime_boundary": profile_result["runtime_boundary"],
        },
        **compact_tts_delivery(tts),
    }


def validate_case(case: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    expected = case.get("expected", {})
    variants = {result["variant_kind"]: result for result in results}
    baseline = variants["baseline_shaped_runtime"]
    profiled = variants["private_pattern_profile"]
    same_text = baseline["tts_input_text"] == profiled["tts_input_text"]
    runtime_ok = all(
        result["validation"]["passed"] is True
        and result["customer_audio_uploaded"] is False
        and result["voice_cloning_used"] is False
        and result["api_key_value_logged"] is False
        and result["voice_id_value_logged"] is False
        and result["synthetic_prompt_only"] is True
        for result in results
    )
    passed = all(
        [
            baseline["voice_private_pattern_profile"]["applied"] is bool(expected.get("baseline_profile_applied", False)),
            profiled["voice_private_pattern_profile"]["applied"] is bool(expected.get("profile_variant_applied", True)),
            same_text is bool(expected.get("same_tts_text", True)),
            profiled["voice_settings"].get("style") == expected.get("profile_style_after", 0.06),
            baseline["voice_settings"].get("style") != profiled["voice_settings"].get("style"),
            baseline["voice_settings"].get("stability") > profiled["voice_settings"].get("stability"),
            runtime_ok,
        ]
    )
    return {
        "passed": passed,
        "baseline_profile_applied": baseline["voice_private_pattern_profile"]["applied"],
        "profile_variant_applied": profiled["voice_private_pattern_profile"]["applied"],
        "same_tts_text": same_text,
        "style_changed": baseline["voice_settings"].get("style") != profiled["voice_settings"].get("style"),
        "stability_reduced": baseline["voice_settings"].get("stability") > profiled["voice_settings"].get("stability"),
        "runtime_boundary_passed": runtime_ok,
    }


def run_case(
    case: dict[str, Any],
    *,
    campaigns: list[dict[str, Any]],
    source_cases_path: Path,
    profile: dict[str, Any],
    provider_key: str,
    live: bool,
    force_key_missing: bool,
    audio_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    base_campaign = find_campaign(campaigns, case["campaign_id"])
    results = [
        run_variant(
            case,
            base_campaign,
            profile=None,
            variant_kind="baseline_shaped_runtime",
            provider_key=provider_key,
            live=live,
            force_key_missing=force_key_missing,
            audio_dir=audio_dir,
            timeout_seconds=timeout_seconds,
        ),
        run_variant(
            case,
            base_campaign,
            profile=profile,
            variant_kind="private_pattern_profile",
            provider_key=provider_key,
            live=live,
            force_key_missing=force_key_missing,
            audio_dir=audio_dir,
            timeout_seconds=timeout_seconds,
        ),
    ]
    validation = validate_case(case, results)
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "language": case["language"],
        "source_cases": project_relative_string(source_cases_path),
        "transcript": case["transcript"],
        "final_response": results[0]["final_response"],
        "baseline_tts_input_text": results[0]["tts_input_text"],
        "profiled_tts_input_text": results[1]["tts_input_text"],
        "ab_results": results,
        "validation": validation,
        "quality_review": {
            "human_listening_review_required": True,
            "human_listening_review_recorded": False,
            "quality_claim_allowed": False,
            "criteria": [
                "baseline shaped runtime vs VOICE-041 profile preference",
                "naturalness",
                "clarity",
                "sales-call pacing",
                "AI-obviousness",
                "emotional appropriateness without hidden-state claims",
                "trustworthiness",
                "whether style increase causes artifacts or overacting",
            ],
        },
    }


def build_summary(cases: list[dict[str, Any]], provider_key: str, live: bool, timeout_seconds: float) -> dict[str, Any]:
    results = [result for case in cases for result in case["ab_results"]]
    return {
        "case_count": len(cases),
        "ab_variant_count": len(results),
        "baseline_variant_count": sum(1 for result in results if result["variant_kind"] == "baseline_shaped_runtime"),
        "profiled_variant_count": sum(1 for result in results if result["variant_kind"] == "private_pattern_profile"),
        "provider_count": 1,
        "providers": [provider_key],
        "live_call_requested": live,
        "api_calls_made": sum(1 for result in results if result["provider_calls_made"]),
        "audio_files_created": sum(1 for result in results if result["audio_file_created"]),
        "fallback_count": sum(1 for result in results if result["fallback_used"]),
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "raw_audio_read": False,
        "transcription_created": False,
        "synthetic_prompts_only": True,
        "timeout_seconds": timeout_seconds,
        "human_listening_review_recorded": False,
        "quality_claim_allowed": False,
        "validation_passed": all(case["validation"]["passed"] for case in cases),
        "max_time_to_first_audio_ms": max(
            (result["time_to_first_audio_ms"] for result in results if result["time_to_first_audio_ms"] is not None),
            default=None,
        ),
        "max_total_provider_latency_ms": max((result["total_provider_latency_ms"] for result in results), default=0),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-042 Private Pattern Live A/B Report",
        "",
        "This report was generated by `scripts/run_voice_042_private_pattern_live_ab.py`.",
        "",
        "It compares baseline RESP-002 shaped runtime against the same text with accepted VOICE-041 private pattern provider settings. The variants keep the same TTS text so listening isolates provider setting impact.",
        "",
        "Default mode is dry-run. Live mode requires `--live`, `--limit-cases`, provider environment variables, and a bounded timeout.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- A/B variants: `{summary['ab_variant_count']}`",
        f"- Provider: `{', '.join(summary['providers'])}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Raw audio read: `{summary['raw_audio_read']}`",
        f"- Transcription created: `{summary['transcription_created']}`",
        f"- Validation passed: `{summary['validation_passed']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Case Results",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                "",
                f"### {case['case_id']}: {case['title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- Same TTS text: `{case['validation']['same_tts_text']}`",
                f"- Style changed: `{case['validation']['style_changed']}`",
                f"- Stability reduced: `{case['validation']['stability_reduced']}`",
                f"- Validation passed: `{case['validation']['passed']}`",
            ]
        )
        for result in case["ab_results"]:
            lines.extend(
                [
                    f"- `{result['variant_kind']}`:",
                    f"  profile applied: `{result['voice_private_pattern_profile']['applied']}`",
                    f"  voice settings: `{result['voice_settings']}`",
                    f"  audio created: `{result['audio_file_created']}`",
                    f"  audio path: `{result['audio_output_path'] or 'not created'}`",
                    f"  API call made: `{result['provider_calls_made']}`",
                    f"  fallback reason: `{result['fallback_reason'] or 'not needed'}`",
                    f"  total latency: `{result['total_provider_latency_ms']} ms`",
                ]
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "No audio quality claim is allowed until an accepted human listening review records the A/B pair as improved.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-042 private pattern profile live-capable A/B harness.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-042 case file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs", help="TTS provider to prepare or call.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live provider API calls when env gates are satisfied.")
    parser.add_argument("--limit-cases", type=int, help="Limit case count. Required with --live to bound provider calls.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore provider env vars to validate missing-key fallback.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")
    if args.live and args.limit_cases is None:
        raise SystemExit("--live requires --limit-cases to bound provider calls.")

    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    audio_dir = resolve_path(args.audio_dir, DEFAULT_AUDIO_DIR)
    out_path = resolve_path(args.out, DEFAULT_OUT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT_OUT)
    config = load_json(cases_path)
    source_cases_path = resolve_path(config["source_cases"], ROOT / config["source_cases"])
    campaigns, _source_cases = load_realtime_cases(source_cases_path)
    selected_cases = list(config["cases"])
    if args.limit_cases is not None:
        selected_cases = selected_cases[: args.limit_cases]

    cases = [
        run_case(
            case,
            campaigns=campaigns,
            source_cases_path=source_cases_path,
            profile=config["voice_private_pattern_profile"],
            provider_key=args.provider,
            live=args.live,
            force_key_missing=args.force_key_missing,
            audio_dir=audio_dir,
            timeout_seconds=args.timeout_seconds,
        )
        for case in selected_cases
    ]
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "case_file": project_relative_string(cases_path),
        "provider": args.provider,
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(result["provider_calls_made"] for case in cases for result in case["ab_results"]),
            "requires_api_key": args.live and not args.force_key_missing,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "raw_audio_read": False,
            "transcription_created": False,
            "quality_claim_allowed_without_human_rating": False,
        },
        "summary": build_summary(cases, args.provider, args.live, args.timeout_seconds),
        "cases": cases,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
