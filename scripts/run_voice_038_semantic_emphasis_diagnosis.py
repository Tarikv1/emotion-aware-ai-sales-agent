#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.providers.tts_provider_clients import (
    call_elevenlabs_stream,
    fallback_reason,
    maybe_remove,
    normalize_language,
    project_relative_string,
    redacted_request_preview,
    resolve_voice_id,
)


VOICE_MILESTONE = "VOICE-038"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-038-semantic-emphasis-diagnosis.json"
DEFAULT_RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-038-semantic-emphasis-diagnosis"
DEFAULT_OUT = DEFAULT_RUN_DIR / "results.json"
DEFAULT_REPORT_OUT = DEFAULT_RUN_DIR / "report.md"
DEFAULT_AUDIO_DIR = DEFAULT_RUN_DIR / "audio"
FRAGILE_CLAUSE = "whether reviewing options is worth your time"


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


def provider_from_config(config: dict[str, Any]) -> dict[str, Any]:
    provider = dict(config["provider"])
    provider.setdefault("provider_key", "elevenlabs")
    provider.setdefault("provider_id", "elevenlabs-stream")
    provider.setdefault("provider_name", "ElevenLabs")
    provider.setdefault("endpoint_type", "tts-http-stream")
    provider.setdefault("endpoint_url_template", "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream")
    provider.setdefault("model_id", "eleven_flash_v2_5")
    provider.setdefault("api_key_env_var", "ELEVENLABS_API_KEY")
    provider.setdefault("default_voice_id_env_var", "ELEVENLABS_VOICE_ID")
    provider.setdefault(
        "language_voice_id_env_vars",
        {
            "de": "ELEVENLABS_VOICE_ID_DE",
            "en": "ELEVENLABS_VOICE_ID_EN",
        },
    )
    provider.setdefault("default_output_format", "mp3_44100_128")
    provider.setdefault("audio_extension", "mp3")
    provider.setdefault("enable_logging", False)
    provider.setdefault(
        "base_voice_settings",
        {
            "stability": 0.56,
            "similarity_boost": 0.75,
            "style": 0.08,
            "use_speaker_boost": True,
            "speed": 1.07,
        },
    )
    return provider


def voice_settings_for_variant(provider: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    settings = dict(provider["base_voice_settings"])
    settings.update(variant.get("voice_settings", {}))
    settings["stability"] = round(min(0.7, max(0.5, float(settings.get("stability", 0.56)))), 3)
    settings["style"] = round(min(0.2, max(0.0, float(settings.get("style", 0.08)))), 3)
    settings["speed"] = round(min(1.1, max(1.03, float(settings.get("speed", 1.07)))), 3)
    return settings


def safe_filename_part(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value).strip("-") or "variant"


def audio_filename(variant_id: str, extension: str) -> str:
    return f"VOICE-038-en-{safe_filename_part(variant_id)}.{extension}"


def offline_result(reason: str, audio_path: Path) -> dict[str, Any]:
    maybe_remove(audio_path)
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


def validate_variant_result(variant: dict[str, Any], text: str, voice_settings: dict[str, Any]) -> dict[str, Any]:
    has_markdown_emphasis = "**" in text or "__" in text
    has_fake_emphasis_tag = "[emphasis]" in text.lower() or "<emphasis" in text.lower()
    passed = (
        normalize_language(variant.get("language", "en")) == "en"
        and bool(text.strip())
        and not has_markdown_emphasis
        and not has_fake_emphasis_tag
        and 0.5 <= float(voice_settings["stability"]) <= 0.7
        and 0.0 <= float(voice_settings["style"]) <= 0.2
        and 1.03 <= float(voice_settings["speed"]) <= 1.1
    )
    return {
        "validator": "VOICE-038 semantic emphasis diagnosis safety check",
        "passed": passed,
        "english_only": normalize_language(variant.get("language", "en")) == "en",
        "non_empty_text": bool(text.strip()),
        "markdown_emphasis_blocked": not has_markdown_emphasis,
        "fake_emphasis_tags_blocked": not has_fake_emphasis_tag,
        "bounded_voice_settings": (
            0.5 <= float(voice_settings["stability"]) <= 0.7
            and 0.0 <= float(voice_settings["style"]) <= 0.2
            and 1.03 <= float(voice_settings["speed"]) <= 1.1
        ),
    }


def run_variant(
    provider: dict[str, Any],
    voice_candidate: dict[str, Any],
    script: dict[str, Any],
    variant: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    language = normalize_language(script.get("language"))
    text = variant["tts_input_text"]
    voice_settings = voice_settings_for_variant(provider, variant)
    voice_id, voice_source = resolve_voice_id(provider, language, force_key_missing)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    audio_path = audio_dir / audio_filename(variant["variant_id"], provider["audio_extension"])
    request_preview = redacted_request_preview(
        provider=provider,
        provider_key=provider["provider_key"],
        language=language,
        text=text,
        voice_settings=voice_settings,
        voice_env_var=voice_source,
    )
    can_call_live = live and bool(api_key) and bool(voice_id)
    if can_call_live:
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
        generated_text_sent = provider_result["api_call_made"]
    else:
        provider_result = offline_result(
            fallback_reason(live, force_key_missing, api_key, voice_id, provider["provider_key"]),
            audio_path,
        )
        generated_text_sent = False

    diagnosis_tags = list(variant.get("diagnosis_tags", []))
    return {
        "voice_milestone": VOICE_MILESTONE,
        "provider_key": provider["provider_key"],
        "provider_name": provider["provider_name"],
        "model_id": provider["model_id"],
        "voice_candidate_id": voice_candidate["candidate_id"],
        "voice_candidate_label": voice_candidate["label"],
        "voice_candidate_status": voice_candidate["status"],
        "voice_id_source": voice_source,
        "voice_id_present": bool(voice_id),
        "voice_id_value_logged": False,
        "script_id": script["script_id"],
        "script_title": script["script_title"],
        "language": language,
        "variant_id": variant["variant_id"],
        "variant_label": variant["label"],
        "hypothesis": variant["hypothesis"],
        "diagnosis_tags": diagnosis_tags,
        "fragile_clause_target": FRAGILE_CLAUSE,
        "keeps_fragile_clause": FRAGILE_CLAUSE in text,
        "replaces_fragile_clause": FRAGILE_CLAUSE not in text,
        "uses_break_tags": "<break" in text,
        "api_key_env_var": provider["api_key_env_var"],
        "api_key_present": bool(api_key),
        "api_key_value_logged": False,
        "customer_audio_uploaded": False,
        "private_audio_used": False,
        "generated_text_sent_to_provider": generated_text_sent,
        "synthetic_prompt_only": True,
        "voice_cloning_used": False,
        "timeout_seconds": timeout_seconds,
        "tts_input_text": text,
        "tts_input_chars": len(text),
        "voice_settings": voice_settings,
        "request_preview": request_preview,
        "audio_filename": audio_path.name,
        "validation": validate_variant_result(variant, text, voice_settings),
        **provider_result,
    }


def run_diagnosis(
    config: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    provider = provider_from_config(config)
    script = config["listening_script"]
    voice_candidate = config["voice_candidate"]
    return [
        run_variant(
            provider=provider,
            voice_candidate=voice_candidate,
            script=script,
            variant=variant,
            audio_dir=audio_dir,
            live=live,
            force_key_missing=force_key_missing,
            timeout_seconds=timeout_seconds,
        )
        for variant in config["variants"]
    ]


def summarize(config: dict[str, Any], results: list[dict[str, Any]], live: bool, timeout_seconds: float) -> dict[str, Any]:
    languages: dict[str, int] = {}
    diagnosis_tags: dict[str, int] = {}
    for result in results:
        languages[result["language"]] = languages.get(result["language"], 0) + 1
        for tag in result["diagnosis_tags"]:
            diagnosis_tags[tag] = diagnosis_tags.get(tag, 0) + 1
    return {
        "script_count": 1,
        "variant_count": len(config["variants"]),
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
        "diagnosis_tags": dict(sorted(diagnosis_tags.items())),
        "fragile_clause_variants": sum(1 for result in results if result["keeps_fragile_clause"]),
        "replacement_clause_variants": sum(1 for result in results if result["replaces_fragile_clause"]),
        "break_tag_variant_count": sum(1 for result in results if result["uses_break_tags"]),
        "validation_passed": sum(1 for result in results if result["validation"]["passed"]),
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
        "# VOICE-038 Semantic Emphasis Diagnosis Report",
        "",
        "This report was generated by `scripts/run_voice_038_semantic_emphasis_diagnosis.py`.",
        "",
        "VOICE-038 is a listening diagnosis for the current preferred English ElevenLabs voice. It does not change the runtime agent yet.",
        "",
        "The target failure is semantic emphasis and phrase rhythm around: `whether reviewing options is worth your time`.",
        "",
        "Live mode requires `--live`, `ELEVENLABS_API_KEY`, an English voice ID in the current shell or ignored local config, and a bounded timeout.",
        "",
        "API keys and raw voice IDs are not written to this report. Customer/private audio is never uploaded or used by this checkpoint.",
        "",
        "## Summary",
        "",
        f"- Variants: `{summary['variant_count']}`",
        f"- Results: `{summary['result_count']}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Fragile-clause variants: `{summary['fragile_clause_variants']}`",
        f"- Replacement-clause variants: `{summary['replacement_clause_variants']}`",
        f"- Break-tag variants: `{summary['break_tag_variant_count']}`",
        f"- Validation passed: `{summary['validation_passed']} / {summary['result_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Private audio used: `{summary['private_audio_used']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Raw voice IDs logged: `{summary['raw_voice_ids_logged']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Listening Order",
        "",
        "Listen in the report order. Use the same preferred English voice for every variant. Pick the variant where the phrase sounds least forced, least over-emphasized, and most sales-trustworthy.",
        "",
        "## Results",
    ]
    for result in payload["results"]:
        lines.extend(
            [
                "",
                f"### {result['variant_id']}: {result['variant_label']}",
                "",
                f"- Hypothesis: {result['hypothesis']}",
                f"- Diagnosis tags: `{result['diagnosis_tags']}`",
                f"- Keeps fragile clause: `{result['keeps_fragile_clause']}`",
                f"- Uses break tags: `{result['uses_break_tags']}`",
                f"- Voice ID source: `{result['voice_id_source']}`",
                f"- Voice ID present: `{result['voice_id_present']}`",
                f"- Audio created: `{result['audio_file_created']}`",
                f"- Audio path: `{result['audio_output_path'] or 'not created'}`",
                f"- API call made: `{result['api_call_made']}`",
                f"- Fallback reason: `{result['fallback_reason'] or 'not needed'}`",
                f"- Stability: `{result['voice_settings']['stability']}`",
                f"- Style: `{result['voice_settings']['style']}`",
                f"- Speed: `{result['voice_settings']['speed']}`",
                f"- TTS input: {result['tts_input_text']}",
            ]
        )
    lines.extend(["", "## Human Listening Review", ""])
    for criterion in payload["quality_rubric"]["criteria"]:
        lines.append(f"- {criterion}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Synthetic English text only.",
            "- No customer audio.",
            "- No private call-center data.",
            "- No voice cloning.",
            "- No quality claim until Tarik listens.",
            "- No runtime behavior change until a winning variant is selected.",
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
) -> dict[str, Any]:
    config = load_json(cases_path)
    results = run_diagnosis(
        config=config,
        audio_dir=audio_dir,
        live=live,
        force_key_missing=force_key_missing,
        timeout_seconds=timeout_seconds,
    )
    return {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": config["experiment_scope"],
        "case_file": project_relative_string(cases_path),
        "output_run_dir": project_relative_string(out_path.parent),
        "provider": provider_from_config(config),
        "voice_candidate": config["voice_candidate"],
        "listening_script": config["listening_script"],
        "variants": config["variants"],
        "safety_gate": config["safety_gate"],
        "quality_rubric": config["quality_rubric"],
        "expected": config["expected"],
        "summary": summarize(config, results, live, timeout_seconds),
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(result["api_call_made"] for result in results),
            "requires_api_key": live and not force_key_missing,
            "api_key_location": "environment-only",
            "voice_id_location": "environment or ignored local config",
            "raw_voice_ids_logged": False,
            "customer_audio_uploaded": False,
            "private_audio_used": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
            "runtime_behavior_changed": False,
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-038 semantic-emphasis/rhythm diagnosis for the preferred English voice.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-038 case/config file.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
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
    if cases_path is None or audio_dir is None or out_path is None or report_path is None:
        raise SystemExit("Cases, audio, output, and report paths are required.")
    payload = build_payload(
        cases_path=cases_path,
        audio_dir=audio_dir,
        out_path=out_path,
        live=args.live,
        force_key_missing=args.force_key_missing,
        timeout_seconds=args.timeout_seconds,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
