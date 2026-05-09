#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_guarded_response import build_guarded_response_packet
from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from runtime_voice_delivery import attach_runtime_voice_delivery
from tts_provider_clients import project_relative_string


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "VOICE-044-baseline-delivery-polish"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-044-baseline-delivery-polish.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_OUT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT_OUT = DEFAULT_OUT_DIR / "report.md"


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


def expectation_met(expected: dict[str, Any], key: str, actual: Any) -> bool:
    if key not in expected:
        return True
    return expected[key] == actual


def validate_case(case: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected", {})
    delivery = packet["voice_delivery"]
    polish = delivery["voice_baseline_delivery_polish"]
    profile = delivery["voice_private_pattern_profile"]
    provider = delivery["provider_rendering"]
    settings = provider.get("voice_settings") or {}
    segment = delivery["segments"][0]
    rendered_text = provider["rendered_text"]
    protected_text_locked = True
    if expected.get("protected_text_locked"):
        protected_text_locked = (
            segment["segment_type"] == expected.get("segment_type")
            and rendered_text == packet["final_response"]
            and provider["protected_segment_provider_tag_count"] == 0
            and polish["adjustment_count"] == 0
        )
    required_fragment = expected.get("required_fragment")
    forbidden_fragment = expected.get("forbidden_fragment")
    required_fragment_present = True if required_fragment is None else required_fragment in rendered_text
    forbidden_fragment_absent = True if forbidden_fragment is None else forbidden_fragment not in rendered_text
    runtime_ok = (
        delivery["validation"]["passed"] is True
        and polish["validation"]["passed"] is True
        and profile["validation"]["passed"] is True
        and delivery["provider_calls_made"] is False
        and delivery["customer_audio_uploaded"] is False
        and delivery["voice_cloning_used"] is False
        and profile["runtime_boundary"]["raw_audio_read"] is False
        and polish["runtime_boundary"]["provider_calls_made"] is False
        and polish["runtime_boundary"]["customer_audio_uploaded"] is False
        and polish["runtime_boundary"]["voice_cloning_used"] is False
    )
    passed = all(
        [
            expectation_met(expected, "baseline_polish_applied", polish["applied"]),
            expectation_met(expected, "private_pattern_profile_applied", profile["applied"]),
            expectation_met(expected, "style_after", settings.get("style")),
            expectation_met(expected, "final_response_unchanged", delivery["final_response_unchanged"]),
            expectation_met(expected, "provider_calls_made", delivery["provider_calls_made"]),
            expectation_met(expected, "segment_type", segment["segment_type"]),
            required_fragment_present,
            forbidden_fragment_absent,
            protected_text_locked,
            runtime_ok,
        ]
    )
    return {
        "passed": passed,
        "baseline_polish_applied_met": expectation_met(expected, "baseline_polish_applied", polish["applied"]),
        "private_pattern_profile_applied_met": expectation_met(expected, "private_pattern_profile_applied", profile["applied"]),
        "style_after_met": expectation_met(expected, "style_after", settings.get("style")),
        "final_response_unchanged": delivery["final_response_unchanged"] is True,
        "provider_calls_made_met": expectation_met(expected, "provider_calls_made", delivery["provider_calls_made"]),
        "required_fragment_present": required_fragment_present,
        "forbidden_fragment_absent": forbidden_fragment_absent,
        "protected_text_locked": protected_text_locked,
        "runtime_boundary_passed": runtime_ok,
    }


def run_case(
    case: dict[str, Any],
    *,
    campaigns: list[dict[str, Any]],
    source_cases_path: Path,
    provider: str,
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
    packet = attach_runtime_voice_delivery(
        guarded_packet,
        campaign,
        provider_key=provider,
        seed=f"{case['case_id']}:voice-044-baseline-polish",
    )
    delivery = packet["voice_delivery"]
    provider_rendering = delivery["provider_rendering"]
    polish = delivery["voice_baseline_delivery_polish"]
    profile = delivery["voice_private_pattern_profile"]
    segment = delivery["segments"][0]
    validation = validate_case(case, packet)
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "campaign_id": case["campaign_id"],
        "stage": case["stage"],
        "language": delivery["language"],
        "source_cases": project_relative_string(source_cases_path),
        "final_response": packet["final_response"],
        "decision_snapshot": packet["decision_snapshot"],
        "segment_type": segment["segment_type"],
        "voice_baseline_delivery_polish": {
            "enabled": polish["enabled"],
            "applied": polish["applied"],
            "adjustment_count": polish["adjustment_count"],
            "adjustments": polish["adjustments"],
            "validation": polish["validation"],
            "runtime_boundary": polish["runtime_boundary"],
        },
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
        "validation": validation,
    }


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(cases),
        "baseline_polish_applied_count": sum(
            1 for case in cases if case["voice_baseline_delivery_polish"]["applied"]
        ),
        "private_pattern_profile_applied_count": sum(
            1 for case in cases if case["voice_private_pattern_profile"]["applied"]
        ),
        "provider_calls_made": False,
        "audio_files_created": 0,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "raw_audio_read": False,
        "transcription_created": False,
        "validation_passed": all(case["validation"]["passed"] for case in cases),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-044 Baseline Delivery Polish Report",
        "",
        "This report was generated by `scripts/run_voice_044_baseline_delivery_polish.py`.",
        "",
        "VOICE-044 makes narrow provider-facing polish changes to the accepted baseline shaped runtime while keeping VOICE-041 private-pattern settings off by default.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Baseline polish applied count: `{summary['baseline_polish_applied_count']}`",
        f"- Private-pattern profile applied count: `{summary['private_pattern_profile_applied_count']}`",
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
        polish = case["voice_baseline_delivery_polish"]
        profile = case["voice_private_pattern_profile"]
        settings = case["provider_rendering"]["voice_settings"]
        lines.extend(
            [
                "",
                f"### {case['case_id']}: {case['title']}",
                "",
                f"- Campaign: `{case['campaign_id']}`",
                f"- Language: `{case['language']}`",
                f"- Segment type: `{case['segment_type']}`",
                f"- VOICE-044 applied: `{polish['applied']}`",
                f"- VOICE-044 adjustments: `{polish['adjustment_count']}`",
                f"- VOICE-041 applied: `{profile['applied']}`",
                f"- Voice settings: `{settings}`",
                f"- Validation passed: `{case['validation']['passed']}`",
                "",
                "Final response:",
                "",
                case["final_response"],
                "",
                "Provider-rendered text:",
                "",
                case["provider_rendering"]["rendered_text"],
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
    parser = argparse.ArgumentParser(description="Run VOICE-044 baseline delivery polish in dry-run mode.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-044 case file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs", help="Provider preview target.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_path(args.cases, DEFAULT_CASES)
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
        "summary": summarize(cases),
        "cases": cases,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
