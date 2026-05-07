#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

from local_voice_config import LOCAL_VOICE_IDS_PATH, local_voice_candidate_for_provider, local_voice_id_for_provider
from prosody_naturalness import apply_prosody_naturalness
from provider_prosody_rendering import render_provider_variant, validate_variant
from runtime_voice_delivery import build_interaction_segments, build_realistic_segments, build_spoken_segments
from speech_interaction import apply_speech_interaction
from speech_realism import apply_speech_realism
from spoken_text_normalization import apply_spoken_text_normalization
from tts_provider_clients import (
    call_elevenlabs_stream,
    fallback_reason,
    normalize_language,
    project_relative_string,
    redacted_request_preview,
)


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-027"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-027-interaction-prosody-live-ab.json"
DEFAULT_RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-027-interaction-prosody-live-ab"
DEFAULT_OUT = DEFAULT_RUN_DIR / "results.json"
DEFAULT_REPORT_OUT = DEFAULT_RUN_DIR / "report.md"
DEFAULT_AUDIO_DIR = DEFAULT_RUN_DIR / "audio"


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


def selected_languages(language_arg: str) -> set[str]:
    if language_arg == "both":
        return {"de", "en"}
    return {language_arg}


def provider_from_config(config: dict[str, Any]) -> dict[str, Any]:
    provider = dict(config["provider"])
    provider.setdefault("provider_id", "elevenlabs-stream")
    provider.setdefault("endpoint_type", "tts-http-stream")
    provider.setdefault("endpoint_url_template", "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream")
    provider.setdefault("default_voice_id_env_var", "ELEVENLABS_VOICE_ID")
    provider.setdefault(
        "language_voice_id_env_vars",
        {
            "de": "ELEVENLABS_VOICE_ID_DE",
            "en": "ELEVENLABS_VOICE_ID_EN",
        },
    )
    provider.setdefault("enable_logging", False)
    return provider


def campaign_by_id(campaigns: list[dict[str, Any]], campaign_id: str) -> dict[str, Any]:
    for campaign in campaigns:
        if campaign.get("campaign_id") == campaign_id:
            return campaign
    raise KeyError(f"Campaign not found: {campaign_id}")


def candidate_for_language(candidates: list[dict[str, Any]], language: str) -> dict[str, Any]:
    normalized = normalize_language(language)
    for candidate in candidates:
        if normalize_language(candidate.get("language")) == normalized:
            return candidate
    raise KeyError(f"Voice candidate not found for language: {language}")


def filter_scripts(scripts: list[dict[str, Any]], language_arg: str, limit_scripts: int | None) -> list[dict[str, Any]]:
    languages = selected_languages(language_arg)
    selected = [script for script in scripts if normalize_language(script.get("language")) in languages]
    if limit_scripts is not None:
        return selected[: max(0, limit_scripts)]
    return selected


def variant_campaign(campaign: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    adjusted = deepcopy(campaign)

    realism_profile = dict(adjusted.get("speech_realism", {}))
    realism_profile["enabled"] = bool(variant.get("speech_realism_enabled", True))
    if not realism_profile["enabled"]:
        realism_profile["filler_frequency"] = "off"
        realism_profile["max_bundles_per_response"] = 0
        realism_profile["allow_thinking_fillers"] = False
    adjusted["speech_realism"] = realism_profile

    interaction_profile = dict(adjusted.get("speech_interaction", {}))
    interaction_profile["enabled"] = bool(variant.get("speech_interaction_enabled", True))
    if not interaction_profile["enabled"]:
        interaction_profile["max_markers_per_response"] = 0
        interaction_profile["allow_backchannels"] = False
        interaction_profile["allow_latency_acknowledgement"] = False
        interaction_profile["allow_sales_pace_variation"] = False
    adjusted["speech_interaction"] = interaction_profile
    return adjusted


def audio_filename(language: str, variant_id: str, script_id: str, extension: str) -> str:
    safe_variant = "".join(char if char.isalnum() or char in "-_" else "-" for char in variant_id)
    safe_script = "".join(char if char.isalnum() or char in "-_" else "-" for char in script_id)
    return f"VOICE-027-{normalize_language(language)}-{safe_variant}-{safe_script}.{extension}"


def offline_result(reason: str, audio_path: Path) -> dict[str, Any]:
    del audio_path
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


def resolve_candidate_voice(
    provider: dict[str, Any],
    candidate: dict[str, Any],
    language: str,
    local_voice_config: Path,
    force_key_missing: bool,
) -> tuple[str | None, str | None, bool]:
    if force_key_missing:
        return None, candidate.get("local_voice_config_key"), False

    voice_id, voice_source = local_voice_candidate_for_provider(
        provider,
        candidate["candidate_id"],
        language,
        local_voice_config,
    )
    if voice_id:
        return voice_id, voice_source or candidate.get("local_voice_config_key"), True

    voice_id, voice_source = local_voice_id_for_provider(provider, language, local_voice_config)
    if voice_id:
        return voice_id, voice_source or candidate.get("fallback_voice_config_key"), True

    return None, candidate.get("local_voice_config_key"), False


def voice_settings_for_provider(provider: dict[str, Any], provider_rendering: dict[str, Any]) -> dict[str, Any]:
    settings = dict(provider.get("base_voice_settings", {}))
    settings.update(provider_rendering.get("voice_settings", {}))
    if provider.get("provider_key") == "elevenlabs":
        base_speed = float(provider.get("base_voice_settings", {}).get("speed", 1.0))
        rendered_speed = float(settings.get("speed", base_speed))
        settings["speed"] = round(min(1.1, max(1.04, rendered_speed if rendered_speed != 1.0 else base_speed)), 3)
    return settings


def build_provider_result_shape(script: dict[str, Any], campaign: dict[str, Any], prosody: dict[str, Any], language: str) -> dict[str, Any]:
    return {
        "case_id": script["script_id"],
        "case_title": script["script_title"],
        "campaign_id": campaign.get("campaign_id"),
        "language": language,
        "prosody_naturalness": prosody,
    }


def validate_pipeline(
    spoken_text_normalization: dict[str, Any],
    speech_realism: dict[str, Any],
    speech_interaction: dict[str, Any],
    prosody: dict[str, Any],
    provider_rendering: dict[str, Any],
) -> dict[str, Any]:
    provider_validation = validate_variant(provider_rendering)
    protected_segment_change_count = (
        len(spoken_text_normalization["validation"].get("protected_segment_changes", []))
        + len(speech_realism["validation"].get("protected_segment_changes", []))
        + len(speech_interaction["validation"].get("protected_segment_changes", []))
        + len(speech_interaction["validation"].get("protected_marker_violations", []))
        + len(prosody["validation"].get("protected_segment_changes", []))
        + len(provider_validation.get("protected_segment_changes", []))
    )
    unsafe_agreement_marker_count = len(speech_interaction["validation"].get("unsafe_agreement_markers", []))
    passed = (
        spoken_text_normalization["validation"]["passed"]
        and speech_realism["validation"]["passed"]
        and speech_interaction["validation"]["passed"]
        and prosody["validation"]["passed"]
        and provider_validation["passed"]
        and protected_segment_change_count == 0
        and unsafe_agreement_marker_count == 0
    )
    return {
        "validator": "VOICE-027 A/B voice delivery pipeline check",
        "passed": passed,
        "spoken_text_normalization_passed": spoken_text_normalization["validation"]["passed"],
        "speech_realism_passed": speech_realism["validation"]["passed"],
        "speech_interaction_passed": speech_interaction["validation"]["passed"],
        "prosody_passed": prosody["validation"]["passed"],
        "provider_rendering_passed": provider_validation["passed"],
        "provider_rendering_validation": provider_validation,
        "protected_segment_change_count": protected_segment_change_count,
        "unsafe_agreement_marker_count": unsafe_agreement_marker_count,
        "notes": (
            "A/B pipeline preserved protected text, avoided unsafe agreement, and rendered provider-safe TTS input."
            if passed
            else "A/B pipeline failed a protected-text, unsafe-agreement, or provider-rendering check."
        ),
    }


def run_script_variant(
    provider: dict[str, Any],
    candidate: dict[str, Any],
    campaign: dict[str, Any],
    script: dict[str, Any],
    variant: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    local_voice_config: Path,
) -> dict[str, Any]:
    language = normalize_language(script.get("language") or campaign.get("language"))
    variant_id = variant["variant_id"]
    seed = f"{VOICE_MILESTONE}:{script['script_id']}:{variant_id}"
    adjusted_campaign = variant_campaign(campaign, variant)
    source_segments = deepcopy(script["segments"])

    spoken_text_normalization = apply_spoken_text_normalization(
        adjusted_campaign,
        source_segments,
        language=language,
        seed=seed,
    )
    spoken_segments = build_spoken_segments(source_segments, spoken_text_normalization)
    speech_realism = apply_speech_realism(
        adjusted_campaign,
        spoken_segments,
        language=language,
        seed=seed,
        customer_state=script.get("customer_context"),
    )
    realistic_segments = build_realistic_segments(spoken_segments, speech_realism)
    speech_interaction = apply_speech_interaction(
        campaign=adjusted_campaign,
        segments=realistic_segments,
        language=language,
        seed=seed,
        customer_state=script.get("customer_context"),
    )
    interaction_segments = build_interaction_segments(realistic_segments, speech_interaction)
    prosody = apply_prosody_naturalness(adjusted_campaign, interaction_segments, language=language, seed=seed)
    provider_result_shape = build_provider_result_shape(script, adjusted_campaign, prosody, language)
    provider_rendering = render_provider_variant(provider_result_shape, provider)
    provider_rendering_validation = validate_variant(provider_rendering)
    voice_settings = voice_settings_for_provider(provider, provider_rendering)

    voice_id, voice_source, voice_id_present = resolve_candidate_voice(
        provider=provider,
        candidate=candidate,
        language=language,
        local_voice_config=local_voice_config,
        force_key_missing=force_key_missing,
    )
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    audio_path = audio_dir / audio_filename(language, variant_id, script["script_id"], provider["audio_extension"])
    request_preview = redacted_request_preview(
        provider=provider,
        provider_key="elevenlabs",
        language=language,
        text=provider_rendering["rendered_text"],
        voice_settings=voice_settings,
        voice_env_var=voice_source or candidate["local_voice_config_key"],
    )

    can_call_live = live and bool(api_key) and bool(voice_id)
    if can_call_live:
        provider_call_result = call_elevenlabs_stream(
            provider=provider,
            text=provider_rendering["rendered_text"],
            language=language,
            voice_settings=voice_settings,
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
        generated_text_sent = provider_call_result["api_call_made"]
    else:
        provider_call_result = offline_result(
            fallback_reason(live, force_key_missing, api_key, voice_id, "elevenlabs"),
            audio_path,
        )
        generated_text_sent = False

    validation = validate_pipeline(
        spoken_text_normalization,
        speech_realism,
        speech_interaction,
        prosody,
        provider_rendering,
    )
    marker_types: dict[str, int] = {}
    for marker in speech_interaction["interaction_markers"]:
        marker_type = marker.get("marker_type", "unknown")
        marker_types[marker_type] = marker_types.get(marker_type, 0) + 1

    return {
        "voice_milestone": VOICE_MILESTONE,
        "provider_key": "elevenlabs",
        "provider_name": provider["provider_name"],
        "model_id": provider["model_id"],
        "voice_candidate_id": candidate["candidate_id"],
        "voice_candidate_label": candidate["label"],
        "voice_candidate_version": candidate["version"],
        "voice_id_source": voice_source or candidate["local_voice_config_key"],
        "voice_id_present": voice_id_present,
        "voice_id_value_logged": False,
        "script_id": script["script_id"],
        "script_title": script["script_title"],
        "campaign_id": campaign["campaign_id"],
        "language": language,
        "variant_id": variant_id,
        "variant_label": variant["label"],
        "speech_realism_enabled": bool(variant.get("speech_realism_enabled", True)),
        "speech_interaction_enabled": bool(variant.get("speech_interaction_enabled", True)),
        "speech_realism_bundle_count": speech_realism["bundle_count"],
        "speech_interaction_marker_count": speech_interaction["marker_count"],
        "speech_interaction_marker_types": marker_types,
        "spoken_text_normalization_count": spoken_text_normalization["normalization_count"],
        "prosody_cue_count": prosody["cue_count"],
        "prosody_cue_counts": prosody["cue_counts"],
        "api_key_env_var": provider["api_key_env_var"],
        "api_key_present": bool(api_key),
        "api_key_value_logged": False,
        "customer_audio_uploaded": False,
        "private_audio_used": False,
        "generated_text_sent_to_provider": generated_text_sent,
        "synthetic_prompt_only": True,
        "voice_cloning_used": False,
        "custom_voice_used": voice_id_present,
        "timeout_seconds": timeout_seconds,
        "tts_input_text": provider_rendering["rendered_text"],
        "tts_input_chars": len(provider_rendering["rendered_text"]),
        "voice_settings": voice_settings,
        "request_preview": request_preview,
        "audio_filename": audio_path.name,
        "spoken_text_normalization": spoken_text_normalization,
        "speech_realism": speech_realism,
        "speech_interaction": speech_interaction,
        "prosody": prosody,
        "provider_rendering": provider_rendering,
        "provider_rendering_validation": provider_rendering_validation,
        "validation": validation,
        **provider_call_result,
    }


def run_comparison(
    config: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    language_arg: str,
    limit_scripts: int | None,
    local_voice_config: Path,
) -> list[dict[str, Any]]:
    provider = provider_from_config(config)
    scripts = filter_scripts(config["listening_scripts"], language_arg, limit_scripts)
    campaigns = config["campaigns"]
    candidates = config["voice_candidates"]
    results = []
    for script in scripts:
        language = normalize_language(script.get("language"))
        campaign = campaign_by_id(campaigns, script["campaign_id"])
        candidate = candidate_for_language(candidates, language)
        for variant in config["variants"]:
            results.append(
                run_script_variant(
                    provider=provider,
                    candidate=candidate,
                    campaign=campaign,
                    script=script,
                    variant=variant,
                    audio_dir=audio_dir,
                    live=live,
                    force_key_missing=force_key_missing,
                    timeout_seconds=timeout_seconds,
                    local_voice_config=local_voice_config,
                )
            )
    return results


def summarize(
    config: dict[str, Any],
    results: list[dict[str, Any]],
    live: bool,
    timeout_seconds: float,
    language_arg: str,
    limit_scripts: int | None,
) -> dict[str, Any]:
    languages: dict[str, int] = {}
    marker_types: dict[str, int] = {}
    for result in results:
        languages[result["language"]] = languages.get(result["language"], 0) + 1
        for marker_type, count in result["speech_interaction_marker_types"].items():
            marker_types[marker_type] = marker_types.get(marker_type, 0) + count

    scripts = filter_scripts(config["listening_scripts"], language_arg, limit_scripts)
    variants = config["variants"]
    return {
        "script_count": len(scripts),
        "variant_count": len(variants),
        "result_count": len(results),
        "languages": dict(sorted(languages.items())),
        "live_call_requested": live,
        "api_calls_made": sum(1 for result in results if result["api_call_made"]),
        "audio_files_created": sum(1 for result in results if result["audio_file_created"]),
        "fallback_count": sum(1 for result in results if result["fallback_used"]),
        "customer_audio_uploaded": False,
        "private_audio_used": False,
        "synthetic_prompts_only": True,
        "voice_cloning_used": False,
        "raw_voice_ids_logged": False,
        "timeout_seconds": timeout_seconds,
        "speech_interaction_marker_types": marker_types,
        "with_voice_026_marker_count": sum(
            result["speech_interaction_marker_count"] for result in results if result["variant_id"] == "with_voice_026"
        ),
        "voice_025_baseline_marker_count": sum(
            result["speech_interaction_marker_count"] for result in results if result["variant_id"] == "voice_025_baseline"
        ),
        "speech_realism_bundle_count": sum(result["speech_realism_bundle_count"] for result in results),
        "unsafe_agreement_marker_count": sum(result["validation"]["unsafe_agreement_marker_count"] for result in results),
        "protected_segment_change_count": sum(result["validation"]["protected_segment_change_count"] for result in results),
        "provider_rendering_failed_count": sum(1 for result in results if not result["provider_rendering_validation"]["passed"]),
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
        "# VOICE-027 Interaction Prosody Live A/B Report",
        "",
        "This report was generated by `scripts/run_voice_027_interaction_prosody_live_ab.py`.",
        "",
        "Live mode requires `--live`, `ELEVENLABS_API_KEY`, local voice IDs in ignored config, and a bounded timeout. Default mode is dry-run and makes no provider calls.",
        "",
        "API keys and raw voice IDs are not written to this report. Customer/private audio is never uploaded or used by this checkpoint.",
        "",
        "VOICE-027 isolates VOICE-026 interaction prosody by comparing the current VOICE-025 baseline against the same pipeline with lookup acknowledgements, neutral backchannels, and bounded sales-pace cues enabled.",
        "",
        "## Summary",
        "",
        f"- Scripts: `{summary['script_count']}`",
        f"- Variants: `{summary['variant_count']}`",
        f"- Results: `{summary['result_count']}`",
        f"- German results: `{summary['languages'].get('de', 0)}`",
        f"- English results: `{summary['languages'].get('en', 0)}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- With VOICE-026 marker count: `{summary['with_voice_026_marker_count']}`",
        f"- VOICE-025 baseline marker count: `{summary['voice_025_baseline_marker_count']}`",
        f"- Marker types: `{summary['speech_interaction_marker_types']}`",
        f"- Unsafe agreement markers: `{summary['unsafe_agreement_marker_count']}`",
        f"- Protected segment changes: `{summary['protected_segment_change_count']}`",
        f"- Raw voice IDs logged: `{summary['raw_voice_ids_logged']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Private audio used: `{summary['private_audio_used']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        f"- Max time to first audio: `{summary['max_time_to_first_audio_ms']}`",
        f"- Max total provider latency: `{summary['max_total_provider_latency_ms']} ms`",
        "",
        "## Listening Order",
        "",
        "For each script, listen to `voice_025_baseline` first and `with_voice_026` second. The voice stays the same; the comparison isolates the VOICE-026 interaction-prosody layer.",
        "",
        "## Results",
    ]

    for result in payload["results"]:
        lines.extend(
            [
                "",
                f"### {result['language']} / {result['script_id']} / {result['variant_id']}",
                "",
                f"- Candidate: `{result['voice_candidate_label']}`",
                f"- Voice ID source: `{result['voice_id_source']}`",
                f"- Voice ID present: `{result['voice_id_present']}`",
                f"- Speech-realism bundles: `{result['speech_realism_bundle_count']}`",
                f"- Interaction markers: `{result['speech_interaction_marker_count']}`",
                f"- Interaction marker types: `{result['speech_interaction_marker_types']}`",
                f"- Spoken normalizations: `{result['spoken_text_normalization_count']}`",
                f"- Prosody cues: `{result['prosody_cue_count']}`",
                f"- Audio created: `{result['audio_file_created']}`",
                f"- Audio path: `{result['audio_output_path'] or 'not created'}`",
                f"- API call made: `{result['api_call_made']}`",
                f"- Fallback reason: `{result['fallback_reason'] or 'not needed'}`",
                f"- Time to first audio: `{result['time_to_first_audio_ms']}`",
                f"- Total latency: `{result['total_provider_latency_ms']} ms`",
                f"- TTS input: {result['tts_input_text']}",
            ]
        )

    lines.extend(["", "## Listening Rubric", ""])
    for criterion in payload["quality_rubric"]["criteria"]:
        lines.append(f"- {criterion}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This checkpoint uses synthetic text only.",
            "- It does not upload customer audio or private call-center data.",
            "- It does not clone voices.",
            "- It does not claim audio quality until Tarik listens and records ratings.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(
    cases_path: Path,
    audio_dir: Path,
    out_path: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    language_arg: str,
    limit_scripts: int | None,
    local_voice_config: Path,
) -> dict[str, Any]:
    config = load_json(cases_path)
    results = run_comparison(
        config=config,
        audio_dir=audio_dir,
        live=live,
        force_key_missing=force_key_missing,
        timeout_seconds=timeout_seconds,
        language_arg=language_arg,
        limit_scripts=limit_scripts,
        local_voice_config=local_voice_config,
    )
    return {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": config["experiment_scope"],
        "case_file": project_relative_string(cases_path),
        "output_run_dir": project_relative_string(out_path.parent),
        "provider": provider_from_config(config),
        "voice_candidates": config["voice_candidates"],
        "variants": config["variants"],
        "campaigns": config["campaigns"],
        "listening_scripts": filter_scripts(config["listening_scripts"], language_arg, limit_scripts),
        "safety_gate": config["safety_gate"],
        "quality_rubric": config["quality_rubric"],
        "expected": config["expected"],
        "summary": summarize(config, results, live, timeout_seconds, language_arg, limit_scripts),
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(result["api_call_made"] for result in results),
            "requires_api_key": live and not force_key_missing,
            "api_key_location": "environment-only",
            "voice_id_location": "ignored local config or explicit environment override",
            "raw_voice_ids_logged": False,
            "customer_audio_uploaded": False,
            "private_audio_used": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-027 interaction-prosody live-capable A/B listening harness.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-027 case/config file.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--local-voice-config", default=str(LOCAL_VOICE_IDS_PATH), help="Ignored local voice ID config path.")
    parser.add_argument("--language", choices=["en", "de", "both"], default="both", help="Language subset to compare.")
    parser.add_argument("--limit-scripts", type=int, default=None, help="Limit selected listening scripts.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live ElevenLabs provider API calls when gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore provider env vars to validate missing-key fallback.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")

    cases_path = resolve_project_path(args.cases)
    audio_dir = resolve_project_path(args.audio_dir)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    local_voice_config = resolve_project_path(args.local_voice_config)
    if cases_path is None or audio_dir is None or out_path is None or report_path is None or local_voice_config is None:
        raise SystemExit("Cases, audio, output, report, and local voice config paths are required.")

    payload = build_payload(
        cases_path=cases_path,
        audio_dir=audio_dir,
        out_path=out_path,
        live=args.live,
        force_key_missing=args.force_key_missing,
        timeout_seconds=args.timeout_seconds,
        language_arg=args.language,
        limit_scripts=args.limit_scripts,
        local_voice_config=local_voice_config,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
