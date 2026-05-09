#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from run_resp_006_german_runtime_version_ab_listening_check import (
    build_runtime_packet,
    new_runtime_spec,
    old_runtime_spec,
)
from runtime_tts_delivery import offline_provider_result, provider_for_key
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
EXPERIMENT_ID = "RESP-007-german-pacing-stability-follow-up"
SOURCE_CHECKPOINT = "RESP-006-german-runtime-version-ab-listening-check"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "resp-007-german-pacing-stability-follow-up.json"
DEFAULT_CAMPAIGN_CASES = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_OUT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT_OUT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_REVIEW_OUT = DEFAULT_OUT_DIR / "human-listening-review.md"
DEFAULT_AUDIO_DIR = DEFAULT_OUT_DIR / "audio"

BREAK_TAG_RE = re.compile(r"\s*<break\s+time=\"[0-9.]+(?:ms|s)\"\s*/?>\s*", re.IGNORECASE)


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


def normalize_content_text(text: str) -> str:
    without_breaks = BREAK_TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", without_breaks).strip()


def insert_break_after_once(text: str, marker: str, break_ms: int) -> str:
    tag = f'{marker} <break time="{break_ms}ms"/>'
    return text.replace(marker, tag, 1)


def build_pacing_text(answer: str, *, opening_ms: int, middle_ms: int, final_ms: int) -> str:
    text = insert_break_after_once(answer, "Gute Frage.", opening_ms)
    text = text.replace(
        "Entscheidung treffen. Die praktische Variante",
        f'Entscheidung treffen. <break time="{middle_ms}ms"/> Die praktische Variante',
        1,
    )
    text = text.replace(
        "irgendetwas weitergeht. Wenn es danach",
        f'irgendetwas weitergeht. <break time="{final_ms}ms"/> Wenn es danach',
        1,
    )
    return text


def audio_filename(case_id: str, language: str, provider_key: str, variant_kind: str, extension: str) -> str:
    return f"{case_id}-{language}-{provider_key}-{variant_kind}.{extension}"


def stabilized_variant_specs(
    *,
    case: dict[str, Any],
    campaign: dict[str, Any],
    provider_key: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    provider = provider_for_key(provider_key)
    source_case = dict(case)
    source_case["case_id"] = case.get("source_resp_006_case_id") or case["case_id"]
    packet = build_runtime_packet(source_case, campaign, provider_key)
    source_old = old_runtime_spec(packet, provider, provider_key)
    source_new = new_runtime_spec(packet)
    answer = packet["final_response"]

    old_settings = dict(source_old.get("voice_settings") or {})
    old_settings["speed"] = 1.02
    old_settings["stability"] = max(float(old_settings.get("stability", 0.45)), 0.48)

    new_settings = dict(source_new.get("voice_settings") or {})
    source_new_speed = float(new_settings.get("speed", 1.0))
    new_settings["speed"] = min(1.02, source_new_speed)
    new_settings["stability"] = max(float(new_settings.get("stability", 0.56)), 0.56)

    variants = [
        {
            "label": "Old runtime stabilized: less rushed opening, less late drag",
            "variant_kind": "old_plain_pacing_stabilized",
            "source_variant_kind": "old_plain_guarded",
            "source_checkpoint": "RESP-006 old_plain_guarded",
            "source_voice_settings": dict(source_old.get("voice_settings") or {}),
            "tts_input_source": "final_response_with_pacing_tags",
            "tts_input_text": build_pacing_text(answer, opening_ms=165, middle_ms=125, final_ms=95),
            "answer_content_text": answer,
            "provider_rendering_used": False,
            "voice_settings": old_settings,
            "pacing_stability": {
                "targets": ["opening_rush_guard", "late_drag_prevention"],
                "editable_surface": "break tags and bounded speed setting only",
                "opening_break_ms": 165,
                "middle_break_ms": 125,
                "final_break_ms": 95,
            },
        },
        {
            "label": "New runtime stabilized: strong opening with late speed cap",
            "variant_kind": "new_shaped_pacing_stabilized",
            "source_variant_kind": "new_shaped_runtime",
            "source_checkpoint": "RESP-006 new_shaped_runtime",
            "source_voice_settings": dict(source_new.get("voice_settings") or {}),
            "tts_input_source": "same_content_with_pacing_tags_and_speed_cap",
            "tts_input_text": build_pacing_text(answer, opening_ms=145, middle_ms=165, final_ms=210),
            "answer_content_text": answer,
            "provider_rendering_used": True,
            "voice_settings": new_settings,
            "pacing_stability": {
                "targets": ["late_speed_cap", "late_answer_spacing"],
                "editable_surface": "break tags and bounded speed setting only",
                "opening_break_ms": 145,
                "middle_break_ms": 165,
                "final_break_ms": 210,
            },
        },
    ]
    for variant in variants:
        variant["normalized_tts_content_text"] = normalize_content_text(variant["tts_input_text"])
        variant["pacing_stability"]["content_changed"] = variant["normalized_tts_content_text"] != answer
    return packet, variants


def run_variant(
    *,
    case: dict[str, Any],
    provider_key: str,
    spec: dict[str, Any],
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    cases_path: Path,
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
        "source_resp_006_case_id": case["source_resp_006_case_id"],
        "question": case["question"],
        "label": spec["label"],
        "variant_kind": spec["variant_kind"],
        "source_variant_kind": spec["source_variant_kind"],
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
        "answer_content_text": spec["answer_content_text"],
        "normalized_tts_content_text": spec["normalized_tts_content_text"],
        "provider_rendering_used": spec["provider_rendering_used"],
        "source_voice_settings": spec["source_voice_settings"],
        "voice_settings": spec["voice_settings"],
        "pacing_stability": spec["pacing_stability"],
        "request_preview": request_preview,
        "audio_filename": audio_path.name,
        "asset_log": {
            "asset_log_id": "RESP-007-generated-audio-asset-log",
            "asset_id": provider_result.get("audio_output_path") or "no-audio-created",
            "output_path": provider_result.get("audio_output_path") or "",
            "status": "needs review" if provider_result.get("audio_file_created") else "not created",
            "provider": provider_key,
            "provider_model": provider["model_id"],
            "provider_voice_env_var": voice_env_var,
            "language": language,
            "source_text_path": project_relative_string(cases_path),
            "input_source_status": "synthetic project-local German test case; same answer content as RESP-006",
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
    cases_path: Path,
) -> dict[str, Any]:
    packet, specs = stabilized_variant_specs(case=case, campaign=campaign, provider_key=provider_key)
    variants = [
        run_variant(
            case=case,
            provider_key=provider_key,
            spec=spec,
            audio_dir=audio_dir,
            live=live,
            force_key_missing=force_key_missing,
            timeout_seconds=timeout_seconds,
            cases_path=cases_path,
        )
        for spec in specs
    ]
    return {
        "case_id": case["case_id"],
        "source_resp_006_case_id": case["source_resp_006_case_id"],
        "title": case["title"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "question": case["question"],
        "final_response": packet["final_response"],
        "answer_content_text": packet["final_response"],
        "runtime_voice_delivery_id": packet["runtime_voice_delivery_id"],
        "editable_surface": case["editable_surface"],
        "pacing_problem": case["pacing_problem"],
        "review_focus": case.get("review_focus", []),
        "variants": variants,
        "quality_review": {
            "human_listening_review_required": True,
            "human_listening_review_recorded": False,
            "quality_claim_allowed": False,
            "voice_personality_selector_unblocked": False,
            "criteria": [
                "old starts less rushed",
                "old avoids late drag",
                "new keeps strong opening",
                "new avoids late speedup",
                "same answer content",
                "German naturalness",
                "trustworthiness",
            ],
        },
    }


def build_summary(cases: list[dict[str, Any]], provider: str, live: bool, timeout_seconds: float) -> dict[str, Any]:
    variants = [variant for case in cases for variant in case["variants"]]
    questions = {case["question"] for case in cases}
    same_content = all(
        variant["normalized_tts_content_text"] == case["answer_content_text"]
        for case in cases
        for variant in case["variants"]
    )
    only_delivery = same_content and all(
        variant["pacing_stability"]["editable_surface"] == "break tags and bounded speed setting only"
        for variant in variants
    )
    return {
        "case_count": len(cases),
        "german_case_count": sum(1 for case in cases if case["language"] == "de"),
        "variant_count": len(variants),
        "same_question_for_all_variants": len(questions) == 1 and all(
            variant["question"] in questions for variant in variants
        ),
        "same_answer_content_for_all_variants": same_content,
        "only_delivery_surface_changed": only_delivery,
        "voice_personality_selector_unblocked": False,
        "old_stabilized_variant_count": sum(1 for variant in variants if variant["variant_kind"] == "old_plain_pacing_stabilized"),
        "new_stabilized_variant_count": sum(1 for variant in variants if variant["variant_kind"] == "new_shaped_pacing_stabilized"),
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
        "# RESP-007 German Pacing-Stability Follow-Up",
        "",
        "This is a German pacing-stability follow-up to RESP-006. It keeps the same answer content and changes only provider-facing delivery surfaces.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- German cases: `{summary['german_case_count']}`",
        f"- Variants: `{summary['variant_count']}`",
        f"- Same question for all variants: `{summary['same_question_for_all_variants']}`",
        f"- Same answer content for all variants: `{summary['same_answer_content_for_all_variants']}`",
        f"- Only delivery surface changed: `{summary['only_delivery_surface_changed']}`",
        f"- Voice-personality selector unblocked: `{summary['voice_personality_selector_unblocked']}`",
        f"- Provider: `{summary['provider']}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Variants",
    ]
    for case in payload["cases"]:
        lines.extend(["", f"### {case['case_id']}", "", f"Question: {case['question']}", ""])
        lines.extend(["Pacing problem:", ""])
        for key, value in case["pacing_problem"].items():
            lines.append(f"- `{key}`: {value}")
        for variant in case["variants"]:
            lines.extend(
                [
                    "",
                    f"#### {variant['variant_kind']}",
                    "",
                    f"- Label: `{variant['label']}`",
                    f"- Source variant: `{variant['source_variant_kind']}`",
                    f"- Source checkpoint: `{variant['source_checkpoint']}`",
                    f"- Pacing targets: `{', '.join(variant['pacing_stability']['targets'])}`",
                    f"- Content changed: `{variant['pacing_stability']['content_changed']}`",
                    f"- Voice settings: `{json.dumps(variant['voice_settings'], ensure_ascii=False, sort_keys=True)}`",
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
            "- The voice-personality selector remains blocked until Tarik records the listening review.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_review(payload: dict[str, Any]) -> str:
    case = payload["cases"][0]
    lines = [
        "# RESP-007 German Pacing-Stability Human Listening Review",
        "",
        "Reviewer: Tarik",
        "",
        "## Input",
        "",
        f"- Question: {case['question']}",
        "- Purpose: check whether the RESP-006 German pacing issue is fixed without changing answer content.",
        "- Blocker: the voice-personality selector remains blocked until this review is accepted.",
        "",
    ]
    for variant in case["variants"]:
        lines.extend(
            [
                f"## {variant['variant_kind']}",
                "",
                f"- Label: `{variant['label']}`",
                f"- Source variant: `{variant['source_variant_kind']}`",
                f"- Audio path: `{variant['audio_output_path'] or 'not created in current dry-run'}`",
                f"- Pacing targets: `{', '.join(variant['pacing_stability']['targets'])}`",
                "",
                "Text:",
                "",
                "```text",
                variant["tts_input_text"],
                "```",
                "",
                "Scores:",
                "",
                "- Opening is not rushed:",
                "- Later answer does not drag or speed up:",
                "- German naturalness:",
                "- Clarity:",
                "- Trustworthiness:",
                "- Overall decision:",
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
            "TODO: accept old_plain_pacing_stabilized, accept new_shaped_pacing_stabilized, accept both, revise again, or run live audio again.",
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
    parser = argparse.ArgumentParser(description="Run RESP-007 German pacing-stability follow-up.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="RESP-007 case JSON.")
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
            raise SystemExit(f"RESP-007 accepts German cases only. Got language={case['language']!r}")
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
                cases_path=cases_path,
            )
        )
    provider_calls_made = any(variant["api_call_made"] for case in results for variant in case["variants"])
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "title": cases_payload.get("title", ""),
        "source_checkpoint": SOURCE_CHECKPOINT,
        "case_file": project_relative_string(cases_path),
        "campaign_case_file": project_relative_string(campaign_cases_path),
        "provider": args.provider,
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": provider_calls_made,
            "requires_api_key": args.live and not args.force_key_missing,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "quality_claim_allowed_without_human_rating": False,
            "voice_personality_selector_unblocked": False,
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
