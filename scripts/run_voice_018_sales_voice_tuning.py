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
from runtime.voice.sales_voice_tuning import apply_sales_voice_tuning


VOICE_MILESTONE = "VOICE-018"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-018-sales-voice-tuning.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-018-sales-voice-tuning.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-018-sales-voice-tuning-report.md"


def resolve_project_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def selected_cases(source_payload: dict[str, Any], selected_ids: list[str]) -> list[dict[str, Any]]:
    cases_by_id = {case["case_id"]: case for case in source_payload["cases"]}
    return [cases_by_id[case_id] for case_id in selected_ids]


def selected_provider_variants(case: dict[str, Any], provider_keys: list[str]) -> list[dict[str, Any]]:
    variants_by_key = {variant["provider_key"]: variant for variant in case["provider_variants"]}
    return [variants_by_key[key] for key in provider_keys]


def tune_case(case: dict[str, Any], provider_keys: list[str], profile: dict[str, Any]) -> dict[str, Any]:
    variants = [
        apply_sales_voice_tuning(case, provider_variant, profile)
        for provider_variant in selected_provider_variants(case, provider_keys)
    ]
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "language": case["language"],
        "prosody_cue_count": case["prosody_cue_count"],
        "prosody_cue_counts": case["prosody_cue_counts"],
        "plain_text": case["plain_text"],
        "debug_text": case.get("debug_text"),
        "sales_voice_variants": variants,
        "validation": {
            "passed": all(variant["validation"]["passed"] for variant in variants),
            "provider_validations": {
                variant["provider_key"]: variant["validation"] for variant in variants
            },
        },
    }


def aggregate(cases: list[dict[str, Any]], provider_keys: list[str]) -> dict[str, Any]:
    variants = [variant for case in cases for variant in case["sales_voice_variants"]]
    segments = [segment for variant in variants for segment in variant["segment_delivery_plan"]]
    tuned_segments = [segment for segment in segments if segment["tuned"]]
    speed_values = [segment["speed_ratio"] for segment in tuned_segments]
    languages: dict[str, int] = {}
    for case in cases:
        languages[case["language"]] = languages.get(case["language"], 0) + 1

    return {
        "case_count": len(cases),
        "languages": languages,
        "provider_count": len(provider_keys),
        "providers": provider_keys,
        "sales_tuned_variant_count": len(variants),
        "segment_count": len(segments),
        "tuned_segment_count": len(tuned_segments),
        "protected_segment_count": sum(1 for segment in segments if segment["protected"]),
        "pause_compression_count": sum(segment["pause_compression_count"] for segment in segments),
        "average_eligible_speed_ratio": round(sum(speed_values) / len(speed_values), 3) if speed_values else 1.0,
        "max_speed_ratio": max(speed_values) if speed_values else 1.0,
        "emotion_intents": sorted({segment["emotion_intent"] for segment in tuned_segments}),
        "pitch_intents": sorted({segment["pitch_intent"] for segment in tuned_segments}),
        "protected_segment_text_changes": sum(
            len(variant["validation"]["protected_segment_text_changes"]) for variant in variants
        ),
        "validation_passed": sum(1 for variant in variants if variant["validation"]["passed"]),
        "validation_failed": sum(1 for variant in variants if not variant["validation"]["passed"]),
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
        "# VOICE-018 Sales Voice Tuning Report",
        "",
        "This report was generated by `scripts/run_voice_018_sales_voice_tuning.py`.",
        "",
        "VOICE-018 is offline and no-key. It tunes provider preview text and request metadata for faster professional-sales delivery, but it does not generate audio or make provider calls.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- German cases: `{summary['languages'].get('de', 0)}`",
        f"- English cases: `{summary['languages'].get('en', 0)}`",
        f"- Providers: `{', '.join(summary['providers'])}`",
        f"- Sales-tuned variants: `{summary['sales_tuned_variant_count']}`",
        f"- Tuned segments: `{summary['tuned_segment_count']}`",
        f"- Protected segments: `{summary['protected_segment_count']}`",
        f"- Pause compressions: `{summary['pause_compression_count']}`",
        f"- Average eligible speed ratio: `{summary['average_eligible_speed_ratio']}`",
        f"- Max speed ratio: `{summary['max_speed_ratio']}`",
        f"- Emotion intents: `{', '.join(summary['emotion_intents'])}`",
        f"- Pitch intents: `{', '.join(summary['pitch_intents'])}`",
        f"- Protected text changes: `{summary['protected_segment_text_changes']}`",
        f"- Validation passed: `{summary['validation_passed']} / {summary['sales_tuned_variant_count']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Voice cloning used: `{summary['voice_cloning_used']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Product Meaning",
        "",
        "The tuning target is a professional sales agent: a little faster, more confident, and less flat, while preserving exact protected campaign and compliance text. This is not a live audio quality claim yet.",
        "",
        "## Case Results",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                "",
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Language: `{case['language']}`",
                f"- Source prosody cues: `{case['prosody_cue_count']}`",
            ]
        )
        for variant in case["sales_voice_variants"]:
            lines.extend(
                [
                    f"- `{variant['provider_key']}` tuned segments: `{variant['tuned_segment_count']}`",
                    f"- `{variant['provider_key']}` average speed: `{variant['average_speed_ratio']}`",
                    f"- `{variant['provider_key']}` emotion intents: `{', '.join(variant['emotion_intents']) or 'none'}`",
                    f"- `{variant['provider_key']}` validation passed: `{variant['validation']['passed']}`",
                    f"- `{variant['provider_key']}` tuned text: {variant['sales_tuned_text']}",
                ]
            )
    return "\n".join(lines) + "\n"


def build_payload(cases_path: Path) -> dict[str, Any]:
    config = load_json(cases_path)
    source_path = resolve_project_path(config["source_artifact"])
    if source_path is None:
        raise SystemExit("VOICE-018 source artifact could not be resolved.")
    source_payload = load_json(source_path)
    provider_keys = list(config["providers"])
    cases = [
        tune_case(case, provider_keys, config["sales_voice_profile"])
        for case in selected_cases(source_payload, config["selected_source_case_ids"])
    ]
    return {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": config["experiment_scope"],
        "case_file": project_relative_string(cases_path),
        "source_artifact": project_relative_string(source_path),
        "sales_voice_profile": config["sales_voice_profile"],
        "summary": aggregate(cases, provider_keys),
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
    parser = argparse.ArgumentParser(description="Run VOICE-018 offline professional-sales voice tuning.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-018 case/config file.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Path to write JSON results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    if cases_path is None or out_path is None or report_path is None:
        raise SystemExit("Cases, output, and report paths are required.")

    payload = build_payload(cases_path)
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
