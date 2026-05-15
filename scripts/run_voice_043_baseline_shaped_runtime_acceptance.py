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


EXPERIMENT_ID = "VOICE-043-baseline-shaped-runtime-acceptance"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-043-baseline-shaped-runtime-acceptance.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-043-baseline-shaped-runtime-acceptance"
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


def expectation_met(expected: dict[str, Any], key: str, actual: Any) -> bool:
    if key not in expected:
        return True
    return expected[key] == actual


def validate_case(case: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected", {})
    voice_delivery = packet["voice_delivery"]
    profile = voice_delivery["voice_private_pattern_profile"]
    provider_rendering = voice_delivery["provider_rendering"]
    settings = provider_rendering.get("voice_settings") or {}
    tts = packet["tts_delivery"]
    segment = voice_delivery["segments"][0]
    protected_text_locked = True
    if expected.get("protected_text_locked"):
        protected_text_locked = (
            segment["segment_type"] == expected.get("segment_type")
            and provider_rendering["rendered_text"] == packet["final_response"]
            and provider_rendering["protected_segment_provider_tag_count"] == 0
        )
    runtime_ok = (
        voice_delivery["validation"]["passed"] is True
        and profile["validation"]["passed"] is True
        and tts["validation"]["passed"] is True
        and voice_delivery["provider_calls_made"] is False
        and voice_delivery["customer_audio_uploaded"] is False
        and voice_delivery["voice_cloning_used"] is False
        and tts["provider_calls_made"] is False
        and tts["audio_file_created"] is False
        and tts["customer_audio_uploaded"] is False
        and tts["voice_cloning_used"] is False
        and tts["api_key_value_logged"] is False
        and tts["voice_id_value_logged"] is False
        and profile["runtime_boundary"]["raw_audio_read"] is False
    )
    passed = all(
        [
            expectation_met(expected, "profile_enabled", profile["enabled"]),
            expectation_met(expected, "profile_applied", profile["applied"]),
            expectation_met(expected, "blocked_reason", profile["blocked_reason"]),
            expectation_met(expected, "style_after", settings.get("style")),
            expectation_met(expected, "final_response_unchanged", voice_delivery["final_response_unchanged"]),
            expectation_met(expected, "provider_calls_made", tts["provider_calls_made"]),
            expectation_met(expected, "segment_type", segment["segment_type"]),
            protected_text_locked,
            runtime_ok,
        ]
    )
    return {
        "passed": passed,
        "profile_enabled_met": expectation_met(expected, "profile_enabled", profile["enabled"]),
        "profile_applied_met": expectation_met(expected, "profile_applied", profile["applied"]),
        "blocked_reason_met": expectation_met(expected, "blocked_reason", profile["blocked_reason"]),
        "style_after_met": expectation_met(expected, "style_after", settings.get("style")),
        "final_response_unchanged": voice_delivery["final_response_unchanged"] is True,
        "provider_calls_made_met": expectation_met(expected, "provider_calls_made", tts["provider_calls_made"]),
        "protected_text_locked": protected_text_locked,
        "runtime_boundary_passed": runtime_ok,
    }


def run_case(
    case: dict[str, Any],
    *,
    campaigns: list[dict[str, Any]],
    source_cases_path: Path,
    provider: str,
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
    voice_packet = attach_runtime_voice_delivery(
        guarded_packet,
        campaign,
        provider_key=provider,
        seed=f"{case['case_id']}:voice-043-baseline-lock",
    )
    packet = attach_runtime_tts_delivery(
        voice_packet,
        provider_key=provider,
        live=False,
        force_key_missing=False,
        audio_dir=audio_dir / case["case_id"],
        timeout_seconds=timeout_seconds,
        command_name="scripts/run_voice_043_baseline_shaped_runtime_acceptance.py",
    )
    voice_delivery = packet["voice_delivery"]
    provider_rendering = voice_delivery["provider_rendering"]
    profile = voice_delivery["voice_private_pattern_profile"]
    segment = voice_delivery["segments"][0]
    validation = validate_case(case, packet)
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "language": voice_delivery["language"],
        "source_cases": project_relative_string(source_cases_path),
        "final_response": packet["final_response"],
        "decision_snapshot": packet["decision_snapshot"],
        "segment_type": segment["segment_type"],
        "voice_private_pattern_profile": {
            "enabled": profile["enabled"],
            "applied": profile["applied"],
            "blocked_reason": profile["blocked_reason"],
            "validation": profile["validation"],
            "runtime_boundary": profile["runtime_boundary"],
        },
        "provider_rendering": {
            "provider_key": provider_rendering["provider_key"],
            "rendered_text": provider_rendering["rendered_text"],
            "provider_tag_count": provider_rendering["provider_tag_count"],
            "protected_segment_provider_tag_count": provider_rendering["protected_segment_provider_tag_count"],
            "voice_settings": provider_rendering.get("voice_settings") or {},
        },
        "tts_delivery": compact_tts_delivery(packet["tts_delivery"]),
        "validation": validation,
    }


def summarize(cases: list[dict[str, Any]], config: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    return {
        "case_count": len(cases),
        "baseline_shaped_runtime_preferred": bool(config.get("baseline_shaped_runtime_preferred", True)),
        "private_pattern_profile_promoted": bool(config.get("private_pattern_profile_promoted", False)),
        "voice_private_pattern_profile_applied_count": sum(
            1 for case in cases if case["voice_private_pattern_profile"]["applied"]
        ),
        "provider_calls_made": any(case["tts_delivery"]["provider_calls_made"] for case in cases),
        "audio_files_created": sum(1 for case in cases if case["tts_delivery"]["audio_file_created"]),
        "fallback_count": sum(1 for case in cases if case["tts_delivery"]["fallback_used"]),
        "customer_audio_uploaded": any(case["tts_delivery"]["customer_audio_uploaded"] for case in cases),
        "voice_cloning_used": any(case["tts_delivery"]["voice_cloning_used"] for case in cases),
        "raw_audio_read": any(
            case["voice_private_pattern_profile"]["runtime_boundary"]["raw_audio_read"] for case in cases
        ),
        "synthetic_prompts_only": all(case["tts_delivery"]["synthetic_prompt_only"] for case in cases),
        "timeout_seconds": timeout_seconds,
        "validation_passed": all(case["validation"]["passed"] for case in cases),
        "quality_claim_scope": "baseline preferred over VOICE-041 private-pattern profile in Tarik listening review",
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-043 Baseline Shaped Runtime Acceptance Report",
        "",
        "This report was generated by `scripts/run_voice_043_baseline_shaped_runtime_acceptance.py`.",
        "",
        "VOICE-043 records Tarik's VOICE-042 listening outcome: baseline shaped runtime sounded better than the private-pattern profile.",
        "",
        "The checkpoint keeps VOICE-041 experimental and verifies that the default runtime path does not apply private-pattern provider settings.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Baseline shaped runtime preferred: `{summary['baseline_shaped_runtime_preferred']}`",
        f"- Private-pattern profile promoted: `{summary['private_pattern_profile_promoted']}`",
        f"- VOICE-041 applied count: `{summary['voice_private_pattern_profile_applied_count']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        f"- Audio files created: `{summary['audio_files_created']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Raw audio read: `{summary['raw_audio_read']}`",
        f"- Validation passed: `{summary['validation_passed']}`",
        "",
        "## Results",
    ]
    for case in payload["cases"]:
        profile = case["voice_private_pattern_profile"]
        settings = case["provider_rendering"]["voice_settings"]
        tts = case["tts_delivery"]
        lines.extend(
            [
                "",
                f"### {case['case_id']}: {case['title']}",
                "",
                f"- Campaign: `{case['campaign_id']}`",
                f"- Language: `{case['language']}`",
                f"- Segment type: `{case['segment_type']}`",
                f"- VOICE-041 enabled: `{profile['enabled']}`",
                f"- VOICE-041 applied: `{profile['applied']}`",
                f"- VOICE-041 blocked reason: `{profile['blocked_reason']}`",
                f"- Voice settings: `{settings}`",
                f"- TTS input source: `{tts['tts_input_source']}`",
                f"- Audio created: `{tts['audio_file_created']}`",
                f"- Fallback reason: `{tts['fallback_reason'] or 'not needed'}`",
                f"- Validation passed: `{case['validation']['passed']}`",
                "",
                "Final response:",
                "",
                case["final_response"],
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
            "- Dry-run only.",
            "- No provider calls.",
            "- No raw private audio read.",
            "- No transcription.",
            "- No private or customer audio upload.",
            "- No voice cloning.",
            "- No private-pattern runtime promotion.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-043 baseline shaped runtime acceptance in dry-run mode.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-043 case file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs", help="Provider preview target.")
    parser.add_argument("--audio-dir", default=str(DEFAULT_AUDIO_DIR), help="Dry-run audio output directory placeholder.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    parser.add_argument("--timeout-seconds", type=float, default=8.0, help="Dry-run provider timeout metadata. Must be <= 10.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")
    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    audio_dir = resolve_path(args.audio_dir, DEFAULT_AUDIO_DIR)
    out_path = resolve_path(args.out, DEFAULT_OUT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT_OUT)
    config = load_json(cases_path)
    source_cases_path = resolve_path(config["source_cases"], ROOT / config["source_cases"])
    campaigns, _source_cases = load_realtime_cases(source_cases_path)
    cases = [
        run_case(
            case,
            campaigns=campaigns,
            source_cases_path=source_cases_path,
            provider=args.provider,
            audio_dir=audio_dir,
            timeout_seconds=args.timeout_seconds,
        )
        for case in config["cases"]
    ]
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "title": config["title"],
        "case_file": project_relative_string(cases_path),
        "provider": args.provider,
        "runtime_boundary": {
            "default_mode": "dry-run",
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "raw_audio_read": False,
            "transcription_created": False,
            "private_pattern_profile_promoted": False,
        },
        "summary": summarize(cases, config, args.timeout_seconds),
        "cases": cases,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
