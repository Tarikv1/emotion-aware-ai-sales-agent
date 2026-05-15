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
from runtime.voice.runtime_voice_delivery import attach_runtime_voice_delivery


VOICE_MILESTONE = "VOICE-034"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-034-pacing-calibration-v2.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-034-pacing-calibration-v2"


def resolve_project_path(path_text: str | None, default: Path | None = None) -> Path:
    if path_text:
        path = Path(path_text)
        return path if path.is_absolute() else ROOT / path
    if default is None:
        raise SystemExit("Missing required path.")
    return default


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_case_result(case: dict[str, Any], campaign: dict[str, Any], provider: str) -> dict[str, Any]:
    guarded_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type="speech-final",
        transcript=case["transcript"],
        silence_count=int(case.get("silence_count", 0)),
        candidate_response_override=case.get("candidate_response"),
    )
    packet = attach_runtime_voice_delivery(guarded_packet, campaign, provider_key=provider)
    calibration = packet["voice_delivery"]["voice_pacing_calibration"]
    provider_rendering = packet["voice_delivery"]["provider_rendering"]
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "language": packet["voice_delivery"]["language"],
        "expected_pacing": case["expected_pacing"],
        "segment_type": packet["voice_delivery"]["segments"][0]["segment_type"],
        "final_response_unchanged": packet["voice_delivery"]["final_response_unchanged"],
        "pacing_calibration": calibration,
        "provider_rendering": {
            "provider_key": provider_rendering["provider_key"],
            "rendered_text": provider_rendering["rendered_text"],
            "voice_settings": provider_rendering.get("voice_settings") or {},
            "pacing_calibrated": provider_rendering.get("pacing_calibrated", False),
            "provider_tag_count": provider_rendering.get("provider_tag_count", 0),
        },
        "validation": {
            "passed": calibration["validation"]["passed"] and packet["voice_delivery"]["validation"]["passed"],
            "runtime_voice_validation_passed": packet["voice_delivery"]["validation"]["passed"],
            "pacing_validation_passed": calibration["validation"]["passed"],
        },
    }


def aggregate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    german_cases = [case for case in cases if case["language"] == "de"]
    speed_values = [
        float(case["provider_rendering"]["voice_settings"].get("speed", 1.0))
        for case in cases
        if case["provider_rendering"].get("pacing_calibrated")
    ]
    return {
        "case_count": len(cases),
        "german_cases": len(german_cases),
        "english_cases": sum(1 for case in cases if case["language"] == "en"),
        "tuned_case_count": sum(1 for case in cases if case["pacing_calibration"]["tuned_segment_count"] > 0),
        "protected_case_count": sum(1 for case in cases if case["pacing_calibration"]["tuned_segment_count"] == 0),
        "average_voice_speed": round(sum(speed_values) / len(speed_values), 3) if speed_values else 1.0,
        "german_word_gap_reduction_cases": sum(
            1 for case in cases if case["pacing_calibration"]["german_word_gap_reduction_applied"]
        ),
        "validation_passed": sum(1 for case in cases if case["validation"]["passed"]),
        "provider_calls_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "quality_claim_allowed": False,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-034 Pacing Calibration V2 Report",
        "",
        "This report was generated by `scripts/run_voice_034_pacing_calibration.py`.",
        "",
        "VOICE-034 is offline and no-key. It tunes provider-rendered pacing metadata and break tags, but it does not generate audio or make provider calls.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- German cases: `{summary['german_cases']}`",
        f"- English cases: `{summary['english_cases']}`",
        f"- Tuned cases: `{summary['tuned_case_count']}`",
        f"- Protected cases: `{summary['protected_case_count']}`",
        f"- Average voice speed: `{summary['average_voice_speed']}`",
        f"- German word-gap reduction cases: `{summary['german_word_gap_reduction_cases']}`",
        f"- Validation passed: `{summary['validation_passed']} / {summary['case_count']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        "",
        "## Case Results",
        "",
    ]
    for case in payload["cases"]:
        calibration = case["pacing_calibration"]
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Segment type: `{case['segment_type']}`",
                f"- Expected pacing: `{case['expected_pacing']}`",
                f"- Tuned segments: `{calibration['tuned_segment_count']}`",
                f"- German gap reduction: `{calibration['german_word_gap_reduction_applied']}`",
                f"- Avg break before: `{calibration['average_break_duration_before_ms']}` ms",
                f"- Avg break after: `{calibration['average_break_duration_after_ms']}` ms",
                f"- Voice speed: `{case['provider_rendering']['voice_settings'].get('speed', 1.0)}`",
                f"- Validation passed: `{case['validation']['passed']}`",
                f"- Rendered text: {case['provider_rendering']['rendered_text']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- No provider calls.",
            "- No generated audio.",
            "- No customer/private audio.",
            "- No voice cloning.",
            "- No runtime text or protected-text rewriting.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(cases_path: Path) -> dict[str, Any]:
    config = load_json(cases_path)
    source_cases_path = resolve_project_path(config["source_cases"])
    campaigns, _runtime_cases = load_realtime_cases(source_cases_path)
    provider = config.get("provider", "elevenlabs")
    cases = [
        build_case_result(case, find_campaign(campaigns, case["campaign_id"]), provider)
        for case in config["runtime_cases"]
    ]
    return {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": config["experiment_scope"],
        "case_file": project_relative(cases_path),
        "source_cases": project_relative(source_cases_path),
        "pacing_policy": config["pacing_policy"],
        "summary": aggregate(cases),
        "runtime_boundary": {
            "offline_preview_only": True,
            "provider_calls_made": False,
            "requires_api_key": False,
            "customer_audio_uploaded": False,
            "voice_cloning_used": False,
            "generated_audio_created": False,
            "quality_claim_allowed_without_human_rating": False,
        },
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-034 offline pacing calibration v2.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-034 case/config file.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for results.json and report.md.")
    parser.add_argument("--print-json", action="store_true", help="Print the full payload after writing artifacts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases, DEFAULT_CASES)
    out_dir = resolve_project_path(args.out_dir, DEFAULT_OUT_DIR)
    payload = build_payload(cases_path)
    write_json(out_dir / "results.json", payload)
    write_text(out_dir / "report.md", render_report(payload))
    if args.print_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
