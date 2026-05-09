#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from generate_guarded_response import build_guarded_response_packet
from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from runtime_tts_delivery import offline_provider_result, provider_for_key
from runtime_voice_delivery import attach_runtime_voice_delivery
from tts_provider_clients import (
    call_cartesia_websocket,
    call_elevenlabs_stream,
    fallback_reason,
    maybe_remove,
    project_relative_string,
    redacted_request_preview,
    resolve_voice_id,
)


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "RESP-006-german-runtime-version-ab-listening-check"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "resp-006-german-runtime-version-ab-listening-check.json"
DEFAULT_CAMPAIGN_CASES = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_OUT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT_OUT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_REVIEW_OUT = DEFAULT_OUT_DIR / "human-listening-review.md"
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


def audio_filename(case_id: str, language: str, provider_key: str, variant_kind: str, extension: str) -> str:
    return f"{case_id}-{language}-{provider_key}-{variant_kind}.{extension}"


def build_runtime_packet(case: dict[str, Any], campaign: dict[str, Any], provider_key: str) -> dict[str, Any]:
    guarded = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type=case.get("input_type", "speech-final"),
        transcript=case["question"],
        silence_count=int(case.get("silence_count", 0)),
        candidate_response_override=case["candidate_response"],
    )
    return attach_runtime_voice_delivery(
        guarded,
        campaign,
        provider_key=provider_key,
        seed=f"{case['case_id']}:resp-006-german-runtime-version-ab",
    )


def old_runtime_spec(packet: dict[str, Any], provider: dict[str, Any], provider_key: str) -> dict[str, Any]:
    return {
        "label": "Old runtime: plain guarded German response",
        "variant_kind": "old_plain_guarded",
        "source_checkpoint": "RESP-001 guarded final_response",
        "tts_input_source": "final_response",
        "tts_input_text": packet["final_response"],
        "provider_rendering_used": False,
        "voice_settings": dict(provider.get("base_voice_settings", {})) if provider_key == "elevenlabs" else {},
    }


def new_runtime_spec(packet: dict[str, Any]) -> dict[str, Any]:
    provider_rendering = packet["voice_delivery"]["provider_rendering"]
    rendered_text = provider_rendering["rendered_text"]
    return {
        "label": "New runtime: shaped provider-ready German response",
        "variant_kind": "new_shaped_runtime",
        "source_checkpoint": "RESP-002/VOICE-044 shaped runtime",
        "tts_input_source": "provider_rendered_text",
        "tts_input_text": rendered_text,
        "provider_rendering_used": True,
        "voice_settings": dict(provider_rendering.get("voice_settings") or {}),
    }


def run_variant(
    *,
    case: dict[str, Any],
    provider_key: str,
    spec: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    provider = provider_for_key(provider_key)
    language = case["language"]
    voice_id, voice_env_var = resolve_voice_id(provider, language, force_key_missing)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    can_call_live = live and bool(api_key) and bool(voice_id)
    audio_path = audio_dir / audio_filename(case["case_id"], language, provider_key, spec["variant_kind"], provider["audio_extension"])
    request_preview = redacted_request_preview(
        provider=provider,
        provider_key=provider_key,
        language=language,
        text=spec["tts_input_text"],
        voice_settings=spec["voice_settings"],
        voice_env_var=voice_env_var,
    )

    if can_call_live and provider_key == "elevenlabs":
        provider_result = call_elevenlabs_stream(
            provider=provider,
            text=spec["tts_input_text"],
            language=language,
            voice_settings=spec["voice_settings"],
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
    elif can_call_live and provider_key == "cartesia":
        provider_result = call_cartesia_websocket(
            provider=provider,
            text=spec["tts_input_text"],
            language=language,
            audio_path=audio_path,
            api_key=api_key or "",
            voice_id=voice_id or "",
            timeout_seconds=timeout_seconds,
        )
    else:
        maybe_remove(audio_path)
        provider_result = offline_provider_result(
            fallback_reason(live, force_key_missing, api_key, voice_id, provider_key),
            audio_path,
        )

    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "label": spec["label"],
        "variant_kind": spec["variant_kind"],
        "source_checkpoint": spec["source_checkpoint"],
        "provider_key": provider_key,
        "provider_id": provider["provider_id"],
        "provider_name": provider["provider_name"],
        "endpoint_type": provider["endpoint_type"],
        "model_id": provider["model_id"],
        "language": language,
        "api_key_env_var": provider["api_key_env_var"],
        "selected_voice_id_env_var": voice_env_var,
        "api_key_present": bool(api_key),
        "voice_id_present": bool(voice_id),
        "api_key_value_logged": False,
        "voice_id_value_logged": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "synthetic_prompt_only": True,
        "live_call_requested": live,
        "generated_text_sent_to_provider": provider_result["api_call_made"],
        "tts_input_source": spec["tts_input_source"],
        "tts_input_text": spec["tts_input_text"],
        "tts_input_chars": len(spec["tts_input_text"]),
        "provider_rendering_used": spec["provider_rendering_used"],
        "voice_settings": spec["voice_settings"],
        "request_preview": request_preview,
        "audio_filename": audio_path.name,
        "asset_log": {
            "asset_log_id": "RESP-006-generated-audio-asset-log",
            "asset_id": provider_result.get("audio_output_path") or "no-audio-created",
            "output_path": provider_result.get("audio_output_path") or "",
            "status": "needs review" if provider_result.get("audio_file_created") else "not created",
            "provider": provider_key,
            "provider_model": provider["model_id"],
            "provider_voice_env_var": voice_env_var,
            "language": language,
            "source_text_path": project_relative_string(DEFAULT_CASES),
            "input_source_status": "synthetic project-local German test case",
            "consent_rights": "No customer audio, no private audio, no voice cloning.",
            "review_decision": "needs human listening review",
        },
        **provider_result,
    }


def run_case(
    *,
    case: dict[str, Any],
    campaign: dict[str, Any],
    provider_key: str,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    provider = provider_for_key(provider_key)
    packet = build_runtime_packet(case, campaign, provider_key)
    specs = [old_runtime_spec(packet, provider, provider_key), new_runtime_spec(packet)]
    variants = [
        run_variant(
            case=case,
            provider_key=provider_key,
            spec=spec,
            audio_dir=audio_dir,
            live=live,
            force_key_missing=force_key_missing,
            timeout_seconds=timeout_seconds,
        )
        for spec in specs
    ]
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "question": case["question"],
        "final_response": packet["final_response"],
        "runtime_voice_delivery_id": packet["runtime_voice_delivery_id"],
        "provider_rendering_changed": packet["voice_delivery"]["provider_rendering"]["rendered_text"] != packet["final_response"],
        "review_focus": case.get("review_focus", []),
        "variants": variants,
        "quality_review": {
            "human_listening_review_required": True,
            "human_listening_review_recorded": False,
            "quality_claim_allowed": False,
            "criteria": [
                "German naturalness",
                "German formality",
                "more complex speaking flow",
                "sales-call pacing",
                "clarity",
                "AI-obviousness",
                "trustworthiness",
                "old runtime versus new runtime preference",
            ],
        },
    }


def build_summary(cases: list[dict[str, Any]], provider: str, live: bool, timeout_seconds: float) -> dict[str, Any]:
    variants = [variant for case in cases for variant in case["variants"]]
    questions = {case["question"] for case in cases}
    return {
        "case_count": len(cases),
        "german_case_count": sum(1 for case in cases if case["language"] == "de"),
        "variant_count": len(variants),
        "same_question_for_all_variants": len(questions) == 1 and all(
            variant["question"] in questions for variant in variants
        ),
        "old_runtime_variant_count": sum(1 for variant in variants if variant["variant_kind"] == "old_plain_guarded"),
        "new_runtime_variant_count": sum(1 for variant in variants if variant["variant_kind"] == "new_shaped_runtime"),
        "minimum_tts_input_chars": min((variant["tts_input_chars"] for variant in variants), default=0),
        "maximum_tts_input_chars": max((variant["tts_input_chars"] for variant in variants), default=0),
        "provider": provider,
        "live_call_requested": live,
        "api_calls_made": sum(1 for variant in variants if variant["api_call_made"]),
        "audio_files_created": sum(1 for variant in variants if variant["audio_file_created"]),
        "fallback_count": sum(1 for variant in variants if variant["fallback_used"]),
        "customer_audio_uploaded": any(variant["customer_audio_uploaded"] for variant in variants),
        "voice_cloning_used": any(variant["voice_cloning_used"] for variant in variants),
        "synthetic_prompts_only": all(variant["synthetic_prompt_only"] for variant in variants),
        "raw_secret_values_logged": any(
            variant["api_key_value_logged"] or variant["voice_id_value_logged"] for variant in variants
        ),
        "timeout_seconds": timeout_seconds,
        "human_listening_review_recorded": False,
        "quality_claim_allowed": False,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RESP-006 German Runtime Version A/B Listening Check",
        "",
        "This report compares one old runtime version and one newer runtime version answering the same German question.",
        "",
        "The answer is intentionally longer for more complex speaking, so pacing, transitions, formality, and AI-obviousness are easier to judge in Deutsch.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- German cases: `{summary['german_case_count']}`",
        f"- Variants: `{summary['variant_count']}`",
        f"- Same question for all variants: `{summary['same_question_for_all_variants']}`",
        f"- Provider: `{summary['provider']}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Variants",
    ]
    for case in payload["cases"]:
        lines.extend(["", f"### {case['case_id']}", "", f"Question: {case['question']}", ""])
        for variant in case["variants"]:
            lines.extend(
                [
                    f"#### {variant['variant_kind']}",
                    "",
                    f"- Label: `{variant['label']}`",
                    f"- Source checkpoint: `{variant['source_checkpoint']}`",
                    f"- Provider rendering used: `{variant['provider_rendering_used']}`",
                    f"- Audio created: `{variant['audio_file_created']}`",
                    f"- Audio path: `{variant['audio_output_path'] or 'not created'}`",
                    f"- Fallback reason: `{variant['fallback_reason'] or 'not needed'}`",
                    "",
                    "TTS input:",
                    "",
                    variant["tts_input_text"],
                    "",
                ]
            )
    lines.extend(
        [
            "## Boundary",
            "",
            "- Dry-run by default.",
            "- Live provider calls require `--live`, provider API key, selected German voice ID, and bounded timeout.",
            "- No customer audio upload.",
            "- No private raw audio read.",
            "- No transcription.",
            "- No voice cloning.",
            "- API keys and raw voice IDs are never written to artifacts.",
            "- No German voice-personality claim is allowed until Tarik records the listening review.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_review(payload: dict[str, Any]) -> str:
    case = payload["cases"][0]
    lines = [
        "# RESP-006 German Runtime Version A/B Human Listening Review",
        "",
        "Date: 2026-05-08",
        "",
        "Reviewer: Tarik",
        "",
        "## Input",
        "",
        f"- Question: {case['question']}",
        "- Purpose: compare old runtime versus newer shaped runtime on the same longer German answer.",
        "- Score each variant from `1` to `5` before deciding whether the English personality lanes survive in Deutsch.",
        "",
    ]
    for variant in case["variants"]:
        lines.extend(
            [
                f"## {variant['variant_kind']}",
                "",
                f"- Label: `{variant['label']}`",
                f"- Source checkpoint: `{variant['source_checkpoint']}`",
                f"- Audio path: `{variant['audio_output_path'] or 'not created in current dry-run'}`",
                "",
                "Text:",
                "",
                "```text",
                variant["tts_input_text"],
                "```",
                "",
                "Scores:",
                "",
                "- German naturalness:",
                "- German formality:",
                "- More complex speaking flow:",
                "- Sales-call pacing:",
                "- Clarity:",
                "- AI-obviousness:",
                "- Trustworthiness:",
                "- Overall preference:",
                "",
                "Notes:",
                "",
                "```text",
                "TODO",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            "```text",
            "TODO: choose old_plain_guarded, new_shaped_runtime, accept both as German personalities, revise both, or run live audio again.",
            "```",
            "",
            "Not allowed yet:",
            "",
            "```text",
            "Either German voice style is production-ready for all campaigns, providers, voices, or real leads.",
            "```",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RESP-006 German same-question old/new runtime listening check.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="RESP-006 case JSON.")
    parser.add_argument("--campaign-cases", default=str(DEFAULT_CAMPAIGN_CASES), help="Campaign wrapper case file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated audio files.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--review-out", default=str(DEFAULT_REVIEW_OUT), help="Path to write human review sheet.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--live", action="store_true", help="Allow live provider API calls when env gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Ignore provider env vars to validate missing-key fallback.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")

    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    campaign_cases_path = resolve_path(args.campaign_cases, DEFAULT_CAMPAIGN_CASES)
    audio_dir = resolve_path(args.audio_dir, DEFAULT_AUDIO_DIR)
    out_path = resolve_path(args.out, DEFAULT_OUT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT_OUT)
    review_path = resolve_path(args.review_out, DEFAULT_REVIEW_OUT)
    cases_payload = load_json(cases_path)
    campaigns, _cases = load_realtime_cases(campaign_cases_path)
    results = []
    for case in cases_payload["cases"]:
        if case["language"] != "de":
            raise SystemExit(f"RESP-006 accepts German cases only. Got language={case['language']!r}")
        campaign = find_campaign(campaigns, case["campaign_id"])
        if campaign is None:
            raise SystemExit(f"Unknown campaign_id: {case['campaign_id']}")
        results.append(
            run_case(
                case=case,
                campaign=campaign,
                provider_key=args.provider,
                audio_dir=audio_dir,
                live=args.live,
                force_key_missing=args.force_key_missing,
                timeout_seconds=args.timeout_seconds,
            )
        )
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "title": cases_payload.get("title", ""),
        "case_file": project_relative_string(cases_path),
        "campaign_case_file": project_relative_string(campaign_cases_path),
        "provider": args.provider,
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(variant["api_call_made"] for case in results for variant in case["variants"]),
            "requires_api_key": args.live and not args.force_key_missing,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
        },
        "summary": build_summary(results, args.provider, args.live, args.timeout_seconds),
        "cases": results,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    write_text(review_path, render_review(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
