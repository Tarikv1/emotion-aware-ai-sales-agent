#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import wave
from pathlib import Path
from typing import Any

from raw_audio_speech_features import (
    RAW_AUDIO_FEATURES_ID,
    SUPPORTED_AUDIO_EXTENSIONS,
    analyze_wav_file,
    discover_audio_files,
    stable_audio_id,
    write_synthetic_wav,
)


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030-raw-audio-local-reader.json"
DEFAULT_GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-030A-raw-audio-local-reader"
DEFAULT_OUT = DEFAULT_GENERATED_DIR / "results.json"
DEFAULT_REPORT_OUT = DEFAULT_GENERATED_DIR / "report.md"
SYNTHETIC_AUDIO_DIR = ROOT / ".tmp" / "voice-030a-synthetic-audio"
PRIVATE_ROOT = ROOT / "data" / "private"
DEFAULT_PRIVATE_OUT = PRIVATE_ROOT / "tarik-speech-samples" / "derived" / "raw-audio-features-draft.json"
DEFAULT_PRIVATE_REPORT = PRIVATE_ROOT / "tarik-speech-samples" / "derived" / "raw-audio-features-draft.md"


def resolve_project_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
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


def build_synthetic_audio(case: dict[str, Any]) -> list[dict[str, Any]]:
    run_audio_dir = SYNTHETIC_AUDIO_DIR / f"run-{os.getpid()}"
    if run_audio_dir.exists():
        shutil.rmtree(run_audio_dir)
    run_audio_dir.mkdir(parents=True, exist_ok=True)
    audio_inputs = []
    for fixture in case.get("synthetic_audio_fixtures", []):
        sample_id = str(fixture["sample_id"])
        path = run_audio_dir / f"{sample_id}.wav"
        write_synthetic_wav(path, fixture)
        audio_inputs.append(
            {
                "audio_id": sample_id,
                "language": fixture.get("language", "unknown"),
                "source": "synthetic_audio_fixture",
                "path": path,
                "private": False,
            }
        )
    return audio_inputs


def build_directory_audio_inputs(input_dir: Path, *, private: bool) -> list[dict[str, Any]]:
    audio_inputs = []
    for path in discover_audio_files(input_dir):
        audio_inputs.append(
            {
                "audio_id": stable_audio_id(path.name),
                "language": "unknown",
                "source": "private_raw_audio" if private else "local_audio_directory",
                "path": path,
                "private": private,
            }
        )
    return audio_inputs


def analyze_audio_inputs(audio_inputs: list[dict[str, Any]], analysis_config: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for audio_input in audio_inputs:
        path: Path = audio_input["path"]
        extension = path.suffix.lower()
        result = {
            "audio_id": audio_input["audio_id"],
            "language": audio_input["language"],
            "source": audio_input["source"],
            "private": audio_input["private"],
            "supported": extension in SUPPORTED_AUDIO_EXTENSIONS,
            "file_extension": extension,
        }
        if extension not in SUPPORTED_AUDIO_EXTENSIONS:
            result["error"] = "unsupported_audio_format_for_voice_030a"
            result["features"] = None
            results.append(result)
            continue
        try:
            result["features"] = analyze_wav_file(
                path,
                frame_ms=int(analysis_config.get("frame_ms", 20)),
                silence_threshold=float(analysis_config.get("silence_threshold", 0.025)),
                min_pause_ms=int(analysis_config.get("min_pause_ms", 180)),
            )
        except (OSError, ValueError, wave.Error) as exc:
            result["supported"] = False
            result["error"] = f"wav_decode_failed: {exc}"
            result["features"] = None
        results.append(result)
    return results


def summarize(results: list[dict[str, Any]], *, safe_public_artifact: bool) -> dict[str, Any]:
    languages: dict[str, int] = {}
    total_duration = 0.0
    total_pause_count = 0
    supported = 0
    unsupported = 0
    for result in results:
        languages[result["language"]] = languages.get(result["language"], 0) + 1
        if result["supported"]:
            supported += 1
            features = result["features"] or {}
            total_duration += float(features.get("duration_seconds", 0.0))
            total_pause_count += int(features.get("pause_count", 0))
        else:
            unsupported += 1
    return {
        "audio_file_count": len(results),
        "supported_file_count": supported,
        "unsupported_file_count": unsupported,
        "languages": dict(sorted(languages.items())),
        "total_duration_seconds": round(total_duration, 3),
        "total_pause_count": total_pause_count,
        "safe_public_artifact": safe_public_artifact,
    }


def build_payload(
    *,
    case: dict[str, Any],
    audio_results: list[dict[str, Any]],
    source_mode: str,
    private_input_read: bool,
) -> dict[str, Any]:
    safe_public_artifact = not private_input_read
    return {
        "voice_milestone": "VOICE-030A",
        "raw_audio_features_id": RAW_AUDIO_FEATURES_ID,
        "source_mode": source_mode,
        "summary": summarize(audio_results, safe_public_artifact=safe_public_artifact),
        "privacy_boundary": {
            "private_input_read": private_input_read,
            "raw_audio_decoded": any(result["supported"] for result in audio_results),
            "raw_private_audio_decoded": private_input_read and any(result["supported"] for result in audio_results),
            "provider_calls_made": False,
            "transcription_created": False,
            "raw_transcript_exported": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "human_review_required_before_runtime_use": True,
            "safe_for_public_generated_artifacts": safe_public_artifact,
        },
        "audio_analysis": case.get("audio_analysis", {}),
        "audio_results": [
            {key: value for key, value in result.items() if key != "path"}
            for result in audio_results
        ],
        "runtime_profile_proposal": {
            "apply_to_runtime_by_default": False,
            "requires_human_review": True,
            "safe_next_step": "Combine reviewed audio timing features with VOICE-029 transcript-pattern features before runtime tuning.",
            "not_inferred": [
                "words",
                "meaning",
                "identity",
                "speaker voiceprint",
                "private personal facts",
            ],
        },
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    boundary = payload["privacy_boundary"]
    lines = [
        "# VOICE-030A Raw Audio Local Reader Report",
        "",
        "This report was generated by `scripts/run_voice_030_raw_audio_reader.py`.",
        "",
        "VOICE-030A decodes local WAV audio to extract acoustic timing and energy features. It does not transcribe audio, call providers, clone voices, or apply runtime settings.",
        "",
        "## Summary",
        "",
        f"- Source mode: `{payload['source_mode']}`",
        f"- Audio files: `{summary['audio_file_count']}`",
        f"- Supported files: `{summary['supported_file_count']}`",
        f"- Unsupported files: `{summary['unsupported_file_count']}`",
        f"- Languages: `{summary['languages']}`",
        f"- Total duration seconds: `{summary['total_duration_seconds']}`",
        f"- Total pause count: `{summary['total_pause_count']}`",
        f"- Safe public artifact: `{summary['safe_public_artifact']}`",
        f"- Private input read: `{boundary['private_input_read']}`",
        f"- Raw audio decoded: `{boundary['raw_audio_decoded']}`",
        f"- Raw private audio decoded: `{boundary['raw_private_audio_decoded']}`",
        f"- Provider calls made: `{boundary['provider_calls_made']}`",
        f"- Transcription created: `{boundary['transcription_created']}`",
        f"- Voice cloning used: `{boundary['voice_cloning_used']}`",
        f"- Runtime profile applied: `{boundary['runtime_profile_applied']}`",
        "",
        "## Audio Results",
        "",
    ]
    for result in payload["audio_results"]:
        lines.extend(
            [
                f"### {result['audio_id']}",
                "",
                f"- Language: `{result['language']}`",
                f"- Source: `{result['source']}`",
                f"- Supported: `{result['supported']}`",
                f"- File extension: `{result['file_extension']}`",
            ]
        )
        if result["features"] is None:
            lines.append(f"- Error: `{result.get('error', 'unknown')}`")
            lines.append("")
            continue
        features = result["features"]
        lines.extend(
            [
                f"- Duration seconds: `{features['duration_seconds']}`",
                f"- Sample rate: `{features['sample_rate_hz']}`",
                f"- Pause ratio: `{features['pause_ratio']}`",
                f"- Pause count: `{features['pause_count']}`",
                f"- Longest pause ms: `{features['longest_pause_ms']}`",
                f"- Speech burst count: `{features['speech_burst_count']}`",
                f"- Mean speech RMS: `{features['mean_speech_rms']}`",
                f"- Energy variation: `{features['energy_variation']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "No transcript text, raw audio path, provider request, speaker identity, or voiceprint is included in this report.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VOICE-030A local raw WAV audio feature extraction.")
    parser.add_argument("--case", default=str(CASE_PATH), help="VOICE-030 case/config JSON.")
    parser.add_argument("--input-dir", help="Optional private raw-audio directory to analyze.")
    parser.add_argument(
        "--allow-private-read",
        action="store_true",
        help="Required when --input-dir is under data/private. Outputs must stay under data/private.",
    )
    parser.add_argument("--out", help="Output JSON path.")
    parser.add_argument("--report-out", help="Output Markdown report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_path = resolve_project_path(args.case, CASE_PATH)
    case = load_json(case_path)
    input_dir = resolve_project_path(args.input_dir, Path("")) if args.input_dir else None

    if input_dir is None:
        audio_inputs = build_synthetic_audio(case)
        source_mode = "synthetic_audio_fixture"
        private_input_read = False
        out_path = resolve_project_path(args.out, DEFAULT_OUT)
        report_path = resolve_project_path(args.report_out, DEFAULT_REPORT_OUT)
    else:
        private_input_read = is_under(input_dir, PRIVATE_ROOT)
        if not private_input_read:
            raise SystemExit("VOICE-030A only accepts explicit private raw audio input under data/private.")
        if not args.allow_private_read:
            raise SystemExit("Refusing to read data/private raw audio without --allow-private-read.")
        if not input_dir.is_dir():
            raise SystemExit(f"Input directory does not exist: {input_dir}")
        out_path = resolve_project_path(args.out, DEFAULT_PRIVATE_OUT)
        report_path = resolve_project_path(args.report_out, DEFAULT_PRIVATE_REPORT)
        if not is_under(out_path, PRIVATE_ROOT) or not is_under(report_path, PRIVATE_ROOT):
            raise SystemExit("Private raw-audio outputs must stay under data/private until reviewed export exists.")
        audio_inputs = build_directory_audio_inputs(input_dir, private=True)
        source_mode = "private_raw_audio"

    audio_results = analyze_audio_inputs(audio_inputs, case.get("audio_analysis", {}))
    payload = build_payload(
        case=case,
        audio_results=audio_results,
        source_mode=source_mode,
        private_input_read=private_input_read,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(f"Wrote VOICE-030A results to {project_relative(out_path)}")
    print(f"Wrote VOICE-030A report to {project_relative(report_path)}")


if __name__ == "__main__":
    main()
