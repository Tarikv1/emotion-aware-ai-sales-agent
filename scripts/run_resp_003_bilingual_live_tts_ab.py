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
from run_resp_002_bilingual_voice_parity import PARITY_CASES
from runtime_tts_delivery import attach_runtime_tts_delivery, offline_provider_result, provider_for_key
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
EXPERIMENT_ID = "RESP-003-bilingual-live-tts-ab"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def audio_filename(case_id: str, language: str, provider_key: str, variant_kind: str, extension: str) -> str:
    cleaned_case_id = case_id.replace("RESP-002-PARITY-", "RESP-003-AB-")
    return f"{cleaned_case_id}-{language}-{provider_key}-{variant_kind}.{extension}"


def build_runtime_packet(case: dict[str, Any], campaign: dict[str, Any], provider_key: str) -> dict[str, Any]:
    guarded = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["transcript"],
        silence_count=0,
        candidate_response_override=case["candidate_response"],
    )
    voice_packet = attach_runtime_voice_delivery(
        guarded,
        campaign,
        provider_key=provider_key,
        seed=case["case_id"],
    )
    return attach_runtime_tts_delivery(
        voice_packet,
        provider_key=provider_key,
        live=False,
        command_name="scripts/run_resp_003_bilingual_live_tts_ab.py",
    )


def base_voice_settings(provider: dict[str, Any], provider_key: str) -> dict[str, Any]:
    if provider_key != "elevenlabs":
        return {}
    return dict(provider.get("base_voice_settings", {}))


def variant_spec(packet: dict[str, Any], provider: dict[str, Any], provider_key: str, variant_kind: str) -> dict[str, Any]:
    if variant_kind == "plain_guarded":
        return {
            "tts_input_source": "final_response",
            "tts_input_text": packet["final_response"],
            "provider_rendering_used": False,
            "voice_settings": base_voice_settings(provider, provider_key),
            "source_checkpoint": "RESP-001 guarded final_response",
        }
    delivery = packet["tts_delivery"]
    return {
        "tts_input_source": delivery["tts_input_source"],
        "tts_input_text": delivery["tts_input_text"],
        "provider_rendering_used": delivery["provider_rendering_used"],
        "voice_settings": dict(delivery.get("voice_settings") or {}),
        "source_checkpoint": "RESP-002 shaped provider-rendered TTS input",
    }


def run_variant(
    case: dict[str, Any],
    packet: dict[str, Any],
    provider_key: str,
    variant_kind: str,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    provider = provider_for_key(provider_key)
    language = packet["tts_delivery"]["language"]
    spec = variant_spec(packet, provider, provider_key, variant_kind)
    voice_id, voice_env_var = resolve_voice_id(provider, language, force_key_missing)
    api_key = None if force_key_missing else os.environ.get(provider["api_key_env_var"])
    can_call_live = live and bool(api_key) and bool(voice_id)
    audio_path = audio_dir / audio_filename(case["case_id"], language, provider_key, variant_kind, provider["audio_extension"])
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
        "provider_key": provider_key,
        "provider_id": provider["provider_id"],
        "provider_name": provider["provider_name"],
        "endpoint_type": provider["endpoint_type"],
        "model_id": provider["model_id"],
        "variant_kind": variant_kind,
        "source_checkpoint": spec["source_checkpoint"],
        "language": language,
        "source_case_id": case["case_id"],
        "api_key_env_var": provider["api_key_env_var"],
        "selected_voice_id_env_var": voice_env_var,
        "api_key_present": bool(api_key),
        "voice_id_present": bool(voice_id),
        "api_key_value_logged": False,
        "voice_id_value_logged": False,
        "customer_audio_uploaded": False,
        "generated_text_sent_to_provider": provider_result["api_call_made"],
        "synthetic_prompt_only": True,
        "voice_cloning_used": False,
        "custom_voice_used": False,
        "timeout_seconds": timeout_seconds,
        "tts_input_source": spec["tts_input_source"],
        "tts_input_text": spec["tts_input_text"],
        "tts_input_chars": len(spec["tts_input_text"]),
        "provider_rendering_used": spec["provider_rendering_used"],
        "voice_settings": spec["voice_settings"],
        "request_preview": request_preview,
        "audio_filename": audio_path.name,
        **provider_result,
    }


def run_case(
    case: dict[str, Any],
    campaign: dict[str, Any],
    provider_key: str,
    audio_dir: Path,
    live: bool,
    force_key_missing: bool,
    timeout_seconds: float,
) -> dict[str, Any]:
    packet = build_runtime_packet(case, campaign, provider_key)
    tts_delivery = packet["tts_delivery"]
    results = [
        run_variant(case, packet, provider_key, "plain_guarded", audio_dir, live, force_key_missing, timeout_seconds),
        run_variant(case, packet, provider_key, "shaped_runtime", audio_dir, live, force_key_missing, timeout_seconds),
    ]
    return {
        "case_id": case["case_id"].replace("RESP-002-PARITY", "RESP-003-AB"),
        "source_case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "transcript": case["transcript"],
        "final_response": packet["final_response"],
        "runtime_tts_input_source": tts_delivery["tts_input_source"],
        "runtime_tts_input_text": tts_delivery["tts_input_text"],
        "runtime_voice_delivery_id": packet["runtime_voice_delivery_id"],
        "runtime_tts_delivery_id": packet["runtime_tts_delivery_id"],
        "provider_rendering_changed": tts_delivery["tts_input_text"] != packet["final_response"],
        "ab_results": results,
        "quality_review": {
            "human_listening_review_required": True,
            "human_listening_review_recorded": False,
            "quality_claim_allowed": False,
            "criteria": [
                "naturalness",
                "sales-call pacing",
                "clarity",
                "language pronunciation",
                "AI-obviousness",
                "emotional appropriateness without pretending to know internal state",
                "trustworthiness",
                "plain guarded vs RESP-002 shaped preference",
            ],
        },
    }


def build_summary(cases: list[dict[str, Any]], provider_key: str, live: bool, timeout_seconds: float) -> dict[str, Any]:
    results = [result for case in cases for result in case["ab_results"]]
    by_language = {
        language: [case for case in cases if case["language"] == language]
        for language in sorted({case["language"] for case in cases})
    }
    by_pair = {
        pair_id: [case for case in cases if case["pair_id"] == pair_id]
        for pair_id in sorted({case["pair_id"] for case in cases})
    }
    return {
        "case_count": len(cases),
        "matched_pair_count": sum(
            1 for pair_cases in by_pair.values()
            if {case["language"] for case in pair_cases} == {"de", "en"}
        ),
        "english_case_count": len(by_language.get("en", [])),
        "german_case_count": len(by_language.get("de", [])),
        "provider_count": 1,
        "providers": [provider_key],
        "ab_variant_count": len(results),
        "plain_variant_count": sum(1 for result in results if result["variant_kind"] == "plain_guarded"),
        "shaped_variant_count": sum(1 for result in results if result["variant_kind"] == "shaped_runtime"),
        "live_call_requested": live,
        "api_calls_made": sum(1 for result in results if result["api_call_made"]),
        "audio_files_created": sum(1 for result in results if result["audio_file_created"]),
        "fallback_count": sum(1 for result in results if result["fallback_used"]),
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "synthetic_prompts_only": True,
        "timeout_seconds": timeout_seconds,
        "human_listening_review_recorded": False,
        "quality_claim_allowed": False,
        "all_shaped_inputs_differ_from_plain": all(case["provider_rendering_changed"] for case in cases),
        "max_time_to_first_audio_ms": max(
            (result["time_to_first_audio_ms"] for result in results if result["time_to_first_audio_ms"] is not None),
            default=None,
        ),
        "max_total_provider_latency_ms": max((result["total_provider_latency_ms"] for result in results), default=0),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RESP-003 Bilingual Live TTS A/B Report",
        "",
        "This report was generated by `scripts/run_resp_003_bilingual_live_tts_ab.py`.",
        "",
        "It compares Plain guarded text against RESP-002 shaped provider-ready TTS input for matched English/German sales scenarios.",
        "",
        "Default mode is dry-run. Live mode requires `--live`, provider environment variables, and a bounded timeout.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Matched scenario pairs: `{summary['matched_pair_count']}`",
        f"- German cases: `{summary['german_case_count']}`",
        f"- English cases: `{summary['english_case_count']}`",
        f"- Provider: `{', '.join(summary['providers'])}`",
        f"- A/B variants: `{summary['ab_variant_count']}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- API calls made: `{summary['api_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Human listening review recorded: `{summary['human_listening_review_recorded']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Case Results",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                "",
                f"### {case['case_id']}",
                "",
                f"- Pair: `{case['pair_id']}`",
                f"- Language: `{case['language']}`",
                f"- Campaign: `{case['campaign_id']}`",
                f"- RESP-002 changed TTS input: `{case['provider_rendering_changed']}`",
            ]
        )
        for result in case["ab_results"]:
            lines.extend(
                [
                    f"- `{result['variant_kind']}`:",
                    f"  audio created: `{result['audio_file_created']}`",
                    f"  audio path: `{result['audio_output_path'] or 'not created'}`",
                    f"  API call made: `{result['api_call_made']}`",
                    f"  fallback reason: `{result['fallback_reason'] or 'not needed'}`",
                    f"  source checkpoint: `{result['source_checkpoint']}`",
                    f"  time to first audio: `{result['time_to_first_audio_ms']}`",
                    f"  total latency: `{result['total_provider_latency_ms']} ms`",
                ]
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "No audio quality claim is allowed until a human listening review is recorded for the generated A/B audio.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RESP-003 matched bilingual plain-vs-shaped live-capable TTS A/B harness.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Campaign case file.")
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

    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    audio_dir = resolve_path(args.audio_dir, DEFAULT_AUDIO_DIR)
    out_path = resolve_path(args.out, DEFAULT_OUT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT_OUT)
    campaigns, _cases = load_realtime_cases(cases_path)
    results: list[dict[str, Any]] = []
    for parity_case in PARITY_CASES:
        campaign = find_campaign(campaigns, parity_case["campaign_id"])
        results.append(
            run_case(
                parity_case,
                campaign,
                args.provider,
                audio_dir,
                args.live,
                args.force_key_missing,
                args.timeout_seconds,
            )
        )
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "case_file": project_relative_string(cases_path),
        "provider": args.provider,
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": any(result["api_call_made"] for case in results for result in case["ab_results"]),
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
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
