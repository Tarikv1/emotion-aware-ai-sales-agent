#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from local_voice_config import LOCAL_VOICE_IDS_PATH, local_voice_candidate_for_provider
from tts_provider_clients import (
    call_elevenlabs_stream,
    fallback_reason,
    maybe_remove,
    normalize_language,
    project_relative_string,
    redacted_request_preview,
)


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-021"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-021-elevenlabs-custom-voice-comparison.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-021-custom-voice-comparison.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-021-custom-voice-comparison-report.md"
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


def selected_languages(language_arg: str) -> set[str]:
    if language_arg == "both":
        return {"de", "en"}
    return {language_arg}


def filter_candidates(candidates: list[dict[str, Any]], language_arg: str) -> list[dict[str, Any]]:
    languages = selected_languages(language_arg)
    return [candidate for candidate in candidates if normalize_language(candidate["language"]) in languages]


def filter_scripts(scripts: list[dict[str, Any]], language_arg: str, limit_scripts: int | None) -> list[dict[str, Any]]:
    languages = selected_languages(language_arg)
    selected = [script for script in scripts if normalize_language(script["language"]) in languages]
    if limit_scripts is not None:
        return selected[: max(0, limit_scripts)]
    return selected


def audio_filename(language: str, candidate_id: str, script_id: str, extension: str) -> str:
    safe_candidate = "".join(char if char.isalnum() or char in "-_" else "-" for char in candidate_id)
    safe_script = "".join(char if char.isalnum() or char in "-_" else "-" for char in script_id)
    return f"VOICE-021-{language}-{safe_candidate}-{safe_script}.{extension}"


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


def resolve_candidate_voice(
    provider: dict[str, Any],
    candidate: dict[str, Any],
    language: str,
    local_voice_config: Path,
    force_key_missing: bool,
) -> tuple[str | None, str | None, bool]:
    voice_id, voice_source = local_voice_candidate_for_provider(
        provider,
        candidate["candidate_id"],
        language,
        local_voice_config,
    )
    if force_key_missing:
        return None, voice_source or candidate["local_voice_config_key"], False
    return voice_id, voice_source or candidate["local_voice_config_key"], bool(voice_id)


def run_candidate_script(
    provider: dict[str, Any],
    candidate: dict[str, Any],
    script: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    local_voice_config: Path,
) -> dict[str, Any]:
    language = normalize_language(script["language"])
    voice_id, voice_source, voice_id_present = resolve_candidate_voice(
        provider,
        candidate,
        language,
        local_voice_config,
        force_key_missing,
    )
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    voice_settings = dict(provider.get("base_voice_settings", {}))
    audio_path = audio_dir / audio_filename(language, candidate["candidate_id"], script["script_id"], provider["audio_extension"])
    request_preview = redacted_request_preview(
        provider=provider,
        provider_key="elevenlabs",
        language=language,
        text=script["text"],
        voice_settings=voice_settings,
        voice_env_var=voice_source or candidate["local_voice_config_key"],
    )
    can_call_live = live and bool(api_key) and bool(voice_id)

    if can_call_live:
        provider_result = call_elevenlabs_stream(
            provider=provider,
            text=script["text"],
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
            fallback_reason(live, force_key_missing, api_key, voice_id, "elevenlabs"),
            audio_path,
        )
        generated_text_sent = False

    return {
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
        "language": language,
        "api_key_env_var": provider["api_key_env_var"],
        "api_key_present": bool(api_key),
        "api_key_value_logged": False,
        "customer_audio_uploaded": False,
        "generated_text_sent_to_provider": generated_text_sent,
        "synthetic_prompt_only": True,
        "voice_cloning_used": False,
        "custom_voice_used": voice_id_present,
        "timeout_seconds": timeout_seconds,
        "tts_input_text": script["text"],
        "tts_input_chars": len(script["text"]),
        "voice_settings": voice_settings,
        "request_preview": request_preview,
        "audio_filename": audio_path.name,
        **provider_result,
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
    candidates = filter_candidates(config["voice_candidates"], language_arg)
    scripts = filter_scripts(config["listening_scripts"], language_arg, limit_scripts)
    results = []
    for script in scripts:
        script_language = normalize_language(script["language"])
        for candidate in candidates:
            if normalize_language(candidate["language"]) != script_language:
                continue
            results.append(
                run_candidate_script(
                    provider=provider,
                    candidate=candidate,
                    script=script,
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
) -> dict[str, Any]:
    languages: dict[str, int] = {}
    for result in results:
        languages[result["language"]] = languages.get(result["language"], 0) + 1
    return {
        "candidate_count": len(filter_candidates(config["voice_candidates"], language_arg)),
        "script_count": len(filter_scripts(config["listening_scripts"], language_arg, None)),
        "comparison_group_count": len(
            [
                group
                for group in config["comparison_groups"]
                if normalize_language(group["language"]) in selected_languages(language_arg)
            ]
        ),
        "result_count": len(results),
        "languages": dict(sorted(languages.items())),
        "live_call_requested": live,
        "api_calls_made": sum(1 for result in results if result["api_call_made"]),
        "audio_files_created": sum(1 for result in results if result["audio_file_created"]),
        "fallback_count": sum(1 for result in results if result["fallback_used"]),
        "customer_audio_uploaded": False,
        "synthetic_prompts_only": True,
        "voice_cloning_used": False,
        "raw_voice_ids_logged": False,
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
        "# VOICE-021 ElevenLabs Custom Voice Comparison Report",
        "",
        "This report was generated by `scripts/run_voice_021_custom_voice_comparison.py`.",
        "",
        "Default mode is dry-run. Live mode requires `--live`, `ELEVENLABS_API_KEY`, local candidate voice IDs, and a bounded timeout.",
        "",
        "Raw voice IDs and API keys are not written to this report.",
        "",
        "## Summary",
        "",
        f"- Candidates: `{summary['candidate_count']}`",
        f"- Scripts: `{summary['script_count']}`",
        f"- Results: `{summary['result_count']}`",
        f"- German results: `{summary['languages'].get('de', 0)}`",
        f"- English results: `{summary['languages'].get('en', 0)}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Raw voice IDs logged: `{summary['raw_voice_ids_logged']}`",
        f"- Human ratings recorded: `{summary['human_ratings_recorded']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        f"- Max time to first audio: `{summary['max_time_to_first_audio_ms']}`",
        f"- Max total provider latency: `{summary['max_total_provider_latency_ms']} ms`",
        "",
        "## Comparison Groups",
        "",
    ]
    for group in payload["comparison_groups"]:
        lines.append(f"- `{group['group_id']}`: {group['question']}")

    lines.extend(["", "## Results"])
    for result in payload["results"]:
        lines.extend(
            [
                "",
                f"### {result['language']} / {result['voice_candidate_id']} / {result['script_id']}",
                "",
                f"- Candidate: `{result['voice_candidate_label']}`",
                f"- Version: `{result['voice_candidate_version']}`",
                f"- Voice ID source: `{result['voice_id_source']}`",
                f"- Voice ID present: `{result['voice_id_present']}`",
                f"- Script: `{result['script_title']}`",
                f"- Audio created: `{result['audio_file_created']}`",
                f"- Audio path: `{result['audio_output_path'] or 'not created'}`",
                f"- API call made: `{result['api_call_made']}`",
                f"- Fallback reason: `{result['fallback_reason'] or 'not needed'}`",
                f"- Time to first audio: `{result['time_to_first_audio_ms']}`",
                f"- Total latency: `{result['total_provider_latency_ms']} ms`",
            ]
        )
    lines.extend(
        [
            "",
            "## Listening Rubric",
            "",
        ]
    )
    for criterion in payload["quality_rubric"]["criteria"]:
        lines.append(f"- {criterion}")
    return "\n".join(lines) + "\n"


def build_payload(
    cases_path: Path,
    audio_dir: Path,
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
        "provider": provider_from_config(config),
        "voice_candidates": filter_candidates(config["voice_candidates"], language_arg),
        "listening_scripts": filter_scripts(config["listening_scripts"], language_arg, limit_scripts),
        "comparison_groups": [
            group
            for group in config["comparison_groups"]
            if normalize_language(group["language"]) in selected_languages(language_arg)
        ],
        "safety_gate": config["safety_gate"],
        "quality_rubric": config["quality_rubric"],
        "expected": config["expected"],
        "summary": summarize(config, results, live, timeout_seconds, language_arg),
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(result["api_call_made"] for result in results),
            "requires_api_key": live and not force_key_missing,
            "api_key_location": "environment-only",
            "voice_id_location": "ignored local config or explicit environment override",
            "raw_voice_ids_logged": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
        },
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-021 ElevenLabs custom voice comparison.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-021 case/config file.")
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
