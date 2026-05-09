#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from generate_guarded_response import build_guarded_response_packet
from realtime_turn_cli import find_campaign
from run_realtime_turn_simulation import load_realtime_cases
from runtime_voice_delivery import attach_runtime_voice_delivery


ROOT = Path(__file__).resolve().parents[1]
VOICE_PRIVATE_PATTERN_PROFILE_RUNTIME_ID = "VOICE-041-private-pattern-profile"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-041-private-pattern-profile.json"
DEFAULT_RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-041-private-pattern-profile"
DEFAULT_OUT = DEFAULT_RUN_DIR / "result.json"
DEFAULT_REPORT_OUT = DEFAULT_RUN_DIR / "report.md"


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
    voice_delivery = packet["voice_delivery"]
    profile = voice_delivery["voice_private_pattern_profile"]
    rendering = voice_delivery["provider_rendering"]
    settings = rendering.get("voice_settings") or {}
    runtime_ok = (
        voice_delivery["validation"]["passed"] is True
        and profile["validation"]["passed"] is True
        and voice_delivery["provider_calls_made"] is False
        and voice_delivery["customer_audio_uploaded"] is False
        and voice_delivery["voice_cloning_used"] is False
        and profile["runtime_boundary"]["raw_audio_read"] is False
        and profile["runtime_boundary"]["transcription_created"] is False
    )
    passed = all(
        [
            expectation_met(expected, "profile_applied", profile["applied"]),
            expectation_met(expected, "blocked_reason", profile["blocked_reason"]),
            expectation_met(expected, "style_after", settings.get("style")),
            expectation_met(expected, "presence_action", profile["presence_action"]),
            expectation_met(expected, "rhythm_density_action", profile["rhythm_density_action"]),
            expectation_met(expected, "final_response_unchanged", voice_delivery["final_response_unchanged"]),
            runtime_ok,
        ]
    )
    return {
        "passed": passed,
        "profile_applied_met": expectation_met(expected, "profile_applied", profile["applied"]),
        "blocked_reason_met": expectation_met(expected, "blocked_reason", profile["blocked_reason"]),
        "style_after_met": expectation_met(expected, "style_after", settings.get("style")),
        "presence_action_met": expectation_met(expected, "presence_action", profile["presence_action"]),
        "rhythm_density_action_met": expectation_met(expected, "rhythm_density_action", profile["rhythm_density_action"]),
        "final_response_unchanged": voice_delivery["final_response_unchanged"] is True,
        "runtime_boundary_passed": runtime_ok,
    }


def run_case(
    case: dict[str, Any],
    *,
    campaigns: list[dict[str, Any]],
    source_cases_path: Path,
    provider: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    campaign = deepcopy(find_campaign(campaigns, case["campaign_id"]))
    campaign["voice_private_pattern_profile"] = deepcopy(profile)
    guarded_packet = build_guarded_response_packet(
        campaign=campaign,
        stage=case["stage"],
        input_type=case.get("input_type", "speech-final"),
        transcript=case.get("transcript", ""),
        silence_count=int(case.get("silence_count", 0)),
        candidate_response_override=case.get("candidate_response"),
    )
    packet = attach_runtime_voice_delivery(guarded_packet, campaign, provider_key=provider)
    voice_delivery = packet["voice_delivery"]
    profile_result = voice_delivery["voice_private_pattern_profile"]
    provider_rendering = voice_delivery["provider_rendering"]
    validation = validate_case(case, packet)
    return {
        "case_id": case["case_id"],
        "title": case["title"],
        "campaign_id": case["campaign_id"],
        "language": voice_delivery["language"],
        "source_cases": str(source_cases_path.relative_to(ROOT)),
        "final_response": packet["final_response"],
        "decision_snapshot": packet["decision_snapshot"],
        "voice_private_pattern_profile": {
            "enabled": profile_result["enabled"],
            "applied": profile_result["applied"],
            "blocked_reason": profile_result["blocked_reason"],
            "rhythm_density_action": profile_result["rhythm_density_action"],
            "presence_action": profile_result["presence_action"],
            "setting_adjustments": profile_result["setting_adjustments"],
            "validation": profile_result["validation"],
            "runtime_boundary": profile_result["runtime_boundary"],
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


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(results),
        "applied_count": sum(1 for result in results if result["voice_private_pattern_profile"]["applied"]),
        "blocked_count": sum(1 for result in results if not result["voice_private_pattern_profile"]["applied"]),
        "provider_calls_made": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "raw_audio_read": False,
        "transcription_created": False,
        "generated_audio_created": False,
        "validation_passed": all(result["validation"]["passed"] for result in results),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-041 Private Pattern Profile Report",
        "",
        "This report was generated by `scripts/run_voice_041_private_pattern_profile.py`.",
        "",
        "VOICE-041 applies only accepted abstract private speech-pattern hints to eligible provider settings. It does not read raw private audio, transcribe speech, upload audio, clone voices, or rewrite guarded text.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Applied: `{summary['applied_count']}`",
        f"- Blocked: `{summary['blocked_count']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        f"- Raw audio read: `{summary['raw_audio_read']}`",
        f"- Transcription created: `{summary['transcription_created']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Validation passed: `{summary['validation_passed']}`",
        "",
        "## Results",
    ]
    for result in payload["results"]:
        profile = result["voice_private_pattern_profile"]
        settings = result["provider_rendering"]["voice_settings"]
        lines.extend(
            [
                "",
                f"### {result['case_id']}: {result['title']}",
                "",
                f"- Campaign: `{result['campaign_id']}`",
                f"- Language: `{result['language']}`",
                f"- Applied: `{profile['applied']}`",
                f"- Blocked reason: `{profile['blocked_reason']}`",
                f"- Rhythm density action: `{profile['rhythm_density_action']}`",
                f"- Presence action: `{profile['presence_action']}`",
                f"- Voice settings: `{settings}`",
                f"- Validation passed: `{result['validation']['passed']}`",
                "",
                "Final response:",
                "",
                result["final_response"],
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No provider calls.",
            "- No raw private audio read.",
            "- No transcription.",
            "- No voice cloning.",
            "- No guarded response rewrite.",
            "- Protected segments block the profile.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-041 private pattern profile through RESP-002 in dry-run mode.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-041 case file.")
    parser.add_argument("--provider", choices=["elevenlabs", "cartesia"], default="elevenlabs", help="Provider preview target.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON output.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    if cases_path is None or out_path is None or report_path is None:
        raise SystemExit("Cases, output, and report paths are required.")
    config = load_json(cases_path)
    source_cases_path = resolve_project_path(config["source_cases"])
    if source_cases_path is None:
        raise SystemExit("VOICE-041 source_cases path is required.")
    campaigns, _source_cases = load_realtime_cases(source_cases_path)
    results = [
        run_case(
            case,
            campaigns=campaigns,
            source_cases_path=source_cases_path,
            provider=args.provider,
            profile=config["voice_private_pattern_profile"],
        )
        for case in config["cases"]
    ]
    payload = {
        "voice_private_pattern_profile_runtime_id": VOICE_PRIVATE_PATTERN_PROFILE_RUNTIME_ID,
        "title": config["title"],
        "provider": args.provider,
        "source_cases": config["source_cases"],
        "summary": summarize(results),
        "results": results,
        "quality_claim_allowed": False,
        "human_listening_review_required": True,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
