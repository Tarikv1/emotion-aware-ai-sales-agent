#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_guarded_response import build_guarded_response_packet
from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from runtime_tts_delivery import attach_runtime_tts_delivery
from runtime_voice_delivery import attach_runtime_voice_delivery


ROOT = Path(__file__).resolve().parents[1]
VOICE_SEMANTIC_EMPHASIS_RUNTIME_ID = "VOICE-039-runtime-semantic-emphasis"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-039-runtime-semantic-emphasis.json"
DEFAULT_RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-039-runtime-semantic-emphasis"
DEFAULT_OUT = DEFAULT_RUN_DIR / "result.json"
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


def compact_tts_delivery(tts: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "runtime_tts_delivery_id",
        "source_runtime_voice_delivery_id",
        "provider_key",
        "provider_name",
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


def validate_case(case: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected", {})
    voice_delivery = packet["voice_delivery"]
    semantic = voice_delivery["voice_semantic_emphasis"]
    tts = packet["tts_delivery"]
    semantic_expected = expected.get("semantic_rewrite_applied")
    semantic_ok = (
        True
        if semantic_expected is None
        else (semantic["rewrite_count"] > 0) is bool(semantic_expected)
    )
    source_ok = (
        True
        if not expected.get("tts_input_source")
        else tts["tts_input_source"] == expected["tts_input_source"]
    )
    minimum_chars = int(expected.get("minimum_tts_chars", 0))
    chars_ok = len(tts["tts_input_text"]) >= minimum_chars
    final_response_ok = voice_delivery["final_response_unchanged"] is True
    protected_ok = not expected.get("protected_text_locked") or semantic["rewrite_count"] == 0
    german_ok = not expected.get("german_text_locked") or semantic["language"] == "de" and semantic["rewrite_count"] == 0
    runtime_ok = (
        voice_delivery["validation"]["passed"] is True
        and semantic["validation"]["passed"] is True
        and tts["validation"]["passed"] is True
        and tts["api_key_value_logged"] is False
        and tts["voice_id_value_logged"] is False
        and tts["customer_audio_uploaded"] is False
        and tts["voice_cloning_used"] is False
    )
    passed = all([semantic_ok, source_ok, chars_ok, final_response_ok, protected_ok, german_ok, runtime_ok])
    return {
        "passed": passed,
        "semantic_expectation_met": semantic_ok,
        "tts_input_source_met": source_ok,
        "minimum_tts_chars_met": chars_ok,
        "final_response_unchanged": final_response_ok,
        "protected_text_locked": protected_ok,
        "german_language_locked": german_ok,
        "runtime_boundary_passed": runtime_ok,
    }


def run_case(
    case: dict[str, Any],
    *,
    campaigns: list[dict[str, Any]],
    source_cases_path: Path,
    provider: str,
    live: bool,
    force_key_missing: bool,
    audio_dir: Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    campaign = find_campaign(campaigns, case["campaign_id"])
    guarded_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type=case.get("input_type", "speech-final"),
        transcript=case.get("transcript", ""),
        silence_count=int(case.get("silence_count", 0)),
        candidate_response_override=case.get("candidate_response"),
    )
    voice_packet = attach_runtime_voice_delivery(guarded_packet, campaign, provider_key=provider)
    packet = attach_runtime_tts_delivery(
        voice_packet,
        provider_key=provider,
        live=live,
        force_key_missing=force_key_missing,
        audio_dir=audio_dir,
        timeout_seconds=timeout_seconds,
        command_name="scripts/run_voice_039_runtime_semantic_emphasis.py",
    )
    semantic = packet["voice_delivery"]["voice_semantic_emphasis"]
    tts = packet["tts_delivery"]
    provider_rendering = packet["voice_delivery"]["provider_rendering"]
    validation = validate_case(case, packet)
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "language": packet["voice_delivery"]["language"],
        "source_cases": str(source_cases_path.relative_to(ROOT)),
        "final_response": packet["final_response"],
        "decision_snapshot": packet["decision_snapshot"],
        "voice_semantic_emphasis": semantic,
        "provider_rendering": {
            "provider_key": provider_rendering["provider_key"],
            "rendered_text": provider_rendering["rendered_text"],
            "semantic_emphasis_candidate_applied": provider_rendering.get("semantic_emphasis_candidate_applied", False),
            "provider_tag_count": provider_rendering["provider_tag_count"],
            "protected_segment_provider_tag_count": provider_rendering["protected_segment_provider_tag_count"],
            "voice_settings": provider_rendering.get("voice_settings") or {},
        },
        "tts_delivery": compact_tts_delivery(tts),
        "long_script_tts_chars": len(tts["tts_input_text"]),
        "validation": validation,
    }


def summarize(results: list[dict[str, Any]], *, live: bool, timeout_seconds: float) -> dict[str, Any]:
    return {
        "case_count": len(results),
        "live_call_requested": live,
        "provider_calls_made": any(result["tts_delivery"]["provider_calls_made"] for result in results),
        "audio_files_created": sum(1 for result in results if result["tts_delivery"]["audio_file_created"]),
        "fallback_count": sum(1 for result in results if result["tts_delivery"]["fallback_used"]),
        "semantic_rewrite_count": sum(result["voice_semantic_emphasis"]["rewrite_count"] for result in results),
        "protected_rewrite_count": sum(
            result["voice_semantic_emphasis"]["rewrite_count"]
            for result in results
            if result["voice_semantic_emphasis"]["protected_segment_count"] > 0
        ),
        "final_response_change_count": sum(
            0 if result["voice_semantic_emphasis"]["validation"]["plain_text_changed"] is False else 1
            for result in results
        ),
        "customer_audio_uploaded": any(result["tts_delivery"]["customer_audio_uploaded"] for result in results),
        "voice_cloning_used": any(result["tts_delivery"]["voice_cloning_used"] for result in results),
        "synthetic_prompts_only": all(result["tts_delivery"]["synthetic_prompt_only"] for result in results),
        "raw_voice_ids_logged": any(result["tts_delivery"]["voice_id_value_logged"] for result in results),
        "api_key_values_logged": any(result["tts_delivery"]["api_key_value_logged"] for result in results),
        "validation_passed": all(result["validation"]["passed"] for result in results),
        "timeout_seconds": timeout_seconds,
        "max_total_provider_latency_ms": max(
            (result["tts_delivery"]["total_provider_latency_ms"] for result in results),
            default=0,
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-039 Runtime Semantic Emphasis Report",
        "",
        "This report was generated by `scripts/run_voice_039_runtime_semantic_emphasis.py`.",
        "",
        "VOICE-039 promotes the VOICE-038 clear/simple wording candidate into the full guarded RESP-002/RESP-003 runtime path as provider-facing TTS text only.",
        "",
        "The guarded `final_response` remains unchanged. Protected campaign, compliance, handoff, hangup, and do-not-call text remains locked.",
        "",
        "Live mode requires `--live`, `--limit-cases`, a provider API key in the current shell, a voice ID in the current shell or ignored local config, and a timeout of 10 seconds or less.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Live call requested: `{summary['live_call_requested']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Fallback count: `{summary['fallback_count']}`",
        f"- Semantic rewrites: `{summary['semantic_rewrite_count']}`",
        f"- Protected rewrites: `{summary['protected_rewrite_count']}`",
        f"- Final response changes: `{summary['final_response_change_count']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Raw voice IDs logged: `{summary['raw_voice_ids_logged']}`",
        f"- API key values logged: `{summary['api_key_values_logged']}`",
        f"- Validation passed: `{summary['validation_passed']}`",
        "",
        "## Results",
    ]
    for result in payload["results"]:
        semantic = result["voice_semantic_emphasis"]
        tts = result["tts_delivery"]
        lines.extend(
            [
                "",
                f"### {result['case_id']}: {result['title']}",
                "",
                f"- Campaign: `{result['campaign_id']}`",
                f"- Language: `{result['language']}`",
                f"- Semantic rewrites: `{semantic['rewrite_count']}`",
                f"- TTS input source: `{tts['tts_input_source']}`",
                f"- Provider rendering used: `{tts['provider_rendering_used']}`",
                f"- TTS input chars: `{result['long_script_tts_chars']}`",
                f"- Audio created: `{tts['audio_file_created']}`",
                f"- Audio path: `{tts['audio_output_path'] or 'not created'}`",
                f"- Fallback reason: `{tts['fallback_reason'] or 'not needed'}`",
                f"- Validation passed: `{result['validation']['passed']}`",
                "",
                "Final response:",
                "",
                result["final_response"],
                "",
                "TTS input:",
                "",
                tts["tts_input_text"],
            ]
        )
    lines.extend(
        [
            "",
            "## Human Listening Notes",
            "",
            "- Preferred pattern to confirm: clearer opening, simple clause, natural emphasis around `review is worth your time`.",
            "- Listen for: no wrong emphasis on abstract words, no robotic break around the promoted clause, no compliance or policy drift.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-039 runtime semantic emphasis through RESP-002/RESP-003.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-039 case file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs", help="Provider preview/live target.")
    parser.add_argument("--limit-cases", type=int, help="Limit case count. Required with --live to bound provider calls.")
    parser.add_argument("--live", action="store_true", help="Allow live provider API calls when env gates are satisfied.")
    parser.add_argument("--force-key-missing", action="store_true", help="Force missing-key fallback for live safety validation.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Directory for generated live audio.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Provider request timeout. Must be <= 10.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")
    if args.live and args.limit_cases is None:
        raise SystemExit("--live requires --limit-cases to bound provider calls.")

    cases_path = resolve_project_path(args.cases)
    audio_dir = resolve_project_path(args.audio_dir)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    if cases_path is None or audio_dir is None or out_path is None or report_path is None:
        raise SystemExit("Cases, audio, output, and report paths are required.")

    config = load_json(cases_path)
    source_cases_path = resolve_project_path(config["source_cases"])
    if source_cases_path is None:
        raise SystemExit("VOICE-039 source_cases path is required.")
    campaigns, _source_cases = load_realtime_cases(source_cases_path)
    selected_cases = list(config["cases"])
    if args.limit_cases is not None:
        selected_cases = selected_cases[: args.limit_cases]

    results = [
        run_case(
            case,
            campaigns=campaigns,
            source_cases_path=source_cases_path,
            provider=args.provider,
            live=args.live,
            force_key_missing=args.force_key_missing,
            audio_dir=audio_dir,
            timeout_seconds=args.timeout_seconds,
        )
        for case in selected_cases
    ]
    payload = {
        "voice_semantic_emphasis_runtime_id": VOICE_SEMANTIC_EMPHASIS_RUNTIME_ID,
        "title": config["title"],
        "provider": args.provider,
        "source_cases": config["source_cases"],
        "summary": summarize(results, live=args.live, timeout_seconds=args.timeout_seconds),
        "results": results,
        "quality_claim_allowed": False,
        "human_listening_review_required": True,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
