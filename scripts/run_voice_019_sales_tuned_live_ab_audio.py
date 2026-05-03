#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from run_voice_017_live_ab_audio import (
    call_cartesia_websocket,
    call_elevenlabs_stream,
    fallback_reason,
    maybe_remove,
    normalize_language,
    project_relative_string,
    redacted_request_preview,
    resolve_voice_id,
    selected_provider_keys,
)


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-019"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-019-sales-tuned-live-ab-audio.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-019-sales-tuned-live-ab-audio.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-019-sales-tuned-live-ab-audio-report.md"
DEFAULT_AUDIO_DIR = ROOT / "research" / "experiments" / "generated"


def resolve_project_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_cases(source_payload: dict[str, Any], selected_ids: list[str], limit: int | None) -> list[dict[str, Any]]:
    cases_by_id = {case["case_id"]: case for case in source_payload["cases"]}
    cases = [cases_by_id[case_id] for case_id in selected_ids]
    if limit is not None:
        return cases[: max(0, limit)]
    return cases


def find_sales_variant(case: dict[str, Any], provider_key: str) -> dict[str, Any]:
    for variant in case["sales_voice_variants"]:
        if variant["provider_key"] == provider_key:
            return variant
    raise KeyError(f"Provider variant not found: {case['case_id']} {provider_key}")


def audio_filename(case_index: int, language: str, provider_key: str, variant_kind: str, extension: str) -> str:
    return f"VOICE-019-C{case_index:02d}-{language}-{provider_key}-{variant_kind}.{extension}"


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


def variant_input(
    source_case: dict[str, Any],
    sales_variant: dict[str, Any],
    provider: dict[str, Any],
    variant_kind: str,
) -> tuple[str, dict[str, Any], dict[str, Any], str]:
    if variant_kind == "prosody":
        return (
            sales_variant["source_rendered_text"],
            dict(provider.get("base_voice_settings", {})),
            {
                "average_speed_ratio": 1.0,
                "emotion_intents": [],
                "pitch_intents": [],
                "tuned_segment_count": 0,
            },
            "VOICE-017-style-prosody",
        )
    voice_settings = dict(provider.get("base_voice_settings", {}))
    voice_settings.update(sales_variant.get("voice_settings") or {})
    return (
        sales_variant["sales_tuned_text"],
        voice_settings,
        {
            "average_speed_ratio": sales_variant["average_speed_ratio"],
            "emotion_intents": sales_variant["emotion_intents"],
            "pitch_intents": sales_variant["pitch_intents"],
            "tuned_segment_count": sales_variant["tuned_segment_count"],
            "pause_compression_count": sales_variant["pause_compression_count"],
            "source_prosody_cue_count": source_case["prosody_cue_count"],
        },
        "VOICE-018",
    )


def run_ab_result(
    provider: dict[str, Any],
    provider_key: str,
    source_case: dict[str, Any],
    sales_variant: dict[str, Any],
    case_index: int,
    variant_kind: str,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    language = normalize_language(source_case["language"])
    text, voice_settings, sales_tuned_metadata, source_checkpoint = variant_input(
        source_case,
        sales_variant,
        provider,
        variant_kind,
    )
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
        "source_checkpoint": source_checkpoint,
        "language": language,
        "source_case_id": source_case["case_id"],
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
        "sales_tuned_metadata": sales_tuned_metadata,
        "request_preview": request_preview,
        "audio_filename": filename,
        **provider_result,
    }


def run_case(
    source_case: dict[str, Any],
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
        sales_variant = find_sales_variant(source_case, provider_key)
        for variant_kind in ["prosody", "sales_tuned"]:
            results.append(
                run_ab_result(
                    provider=provider,
                    provider_key=provider_key,
                    source_case=source_case,
                    sales_variant=sales_variant,
                    case_index=case_index,
                    variant_kind=variant_kind,
                    audio_dir=audio_dir,
                    live=live,
                    force_key_missing=force_key_missing,
                    timeout_seconds=timeout_seconds,
                )
            )
    return {
        "case_id": f"VOICE-019-C{case_index:02d}",
        "source_case_id": source_case["case_id"],
        "case_title": source_case["case_title"],
        "campaign_id": source_case["campaign_id"],
        "language": normalize_language(source_case["language"]),
        "prosody_cue_count": source_case["prosody_cue_count"],
        "prosody_cue_counts": source_case["prosody_cue_counts"],
        "ab_results": results,
        "quality_review": {
            "human_rating_required": True,
            "human_ratings_recorded": False,
            "quality_claim_allowed": False,
            "criteria": [
                "naturalness",
                "sales-call pacing",
                "pitch variation",
                "emotional appropriateness without overacting",
                "clarity",
                "language pronunciation",
                "AI-obviousness",
                "low muffling or artifacts",
                "trustworthiness",
                "prosody vs sales_tuned preference",
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
        "prosody_variant_count": sum(1 for result in results if result["variant_kind"] == "prosody"),
        "sales_tuned_variant_count": sum(1 for result in results if result["variant_kind"] == "sales_tuned"),
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
        "# VOICE-019 Sales-Tuned Live A/B Audio Report",
        "",
        "This report was generated by `scripts/run_voice_019_sales_tuned_live_ab_audio.py`.",
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
        f"- Prosody variants: `{summary['prosody_variant_count']}`",
        f"- Sales-tuned variants: `{summary['sales_tuned_variant_count']}`",
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
                f"- Source prosody cues: `{case['prosody_cue_count']}`",
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
                    f"  source checkpoint: `{result['source_checkpoint']}`",
                    f"  sales speed: `{result['sales_tuned_metadata'].get('average_speed_ratio', 1.0)}`",
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
    provider_config_path = resolve_project_path(config["provider_config_source"])
    if source_path is None or provider_config_path is None:
        raise SystemExit("VOICE-019 source artifacts could not be resolved.")
    source_payload = load_json(source_path)
    provider_config = load_json(provider_config_path)
    provider_keys = selected_provider_keys(provider_arg)
    cases = source_cases(source_payload, config["selected_source_case_ids"], limit)
    results = [
        run_case(
            source_case=case,
            providers=provider_config["providers"],
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
        "provider_config_source": project_relative_string(provider_config_path),
        "selected_source_case_ids": [case["case_id"] for case in cases],
        "selected_provider_arg": provider_arg,
        "providers": {key: provider_config["providers"][key] for key in provider_keys},
        "ab_variants": config["ab_variants"],
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
    parser = argparse.ArgumentParser(description="Run VOICE-019 guarded prosody-vs-sales-tuned live-capable TTS A/B harness.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-019 case/config file.")
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
