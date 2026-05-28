#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LISTENING_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001"
TEMPLATE_JSON_PATH = OUT_DIR / "manual_review_template.json"
TEMPLATE_MD_PATH = OUT_DIR / "manual_review_template.md"
PLAYBACK_RESULT_PATH = OUT_DIR / "playback_helper_result.json"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
RATING_FIELDS = [
    "intelligibility_1_to_5",
    "naturalness_1_to_5",
    "voice_quality_1_to_5",
    "sales_tone_1_to_5",
    "pacing_1_to_5",
    "artifact_severity_1_to_5",
    "robotic_sound_1_to_5",
    "thesis_demo_suitability_1_to_5",
    "product_fallback_suitability_1_to_5",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def tracked_model_files() -> list[str]:
    return [
        path
        for path in git_lines(["ls-files"])
        if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)
    ]


def tracked_audio_files() -> list[str]:
    return [path for path in git_lines(["ls-files"]) if path.lower().endswith(AUDIO_SUFFIXES)]


def side_effects() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "liquid_inference_run": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "model_download_attempted": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_committed": bool(tracked_audio_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
    }


def template_entries(listening: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in listening.get("review_entries") or []:
        if not isinstance(entry, dict):
            continue
        item: dict[str, Any] = {
            "case_id": entry.get("case_id"),
            "local_audio_path": entry.get("local_audio_file_path"),
            "input_text": entry.get("input_text"),
            "duration_seconds": entry.get("duration_seconds"),
            "sample_rate": entry.get("sample_rate"),
            "waveform_hash": entry.get("waveform_hash"),
            "latency_seconds": entry.get("latency_seconds"),
            "real_time_factor": entry.get("real_time_factor"),
        }
        for field in RATING_FIELDS:
            item[field] = None
        item["compared_to_elevenlabs"] = ""
        item["notes"] = ""
        entries.append(item)
    return entries


def write_template(listening: dict[str, Any]) -> dict[str, Any]:
    entries = template_entries(listening)
    template = {
        "experiment_id": "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001",
        "generated_at": utc_now(),
        "status": "template_ready",
        "source_listening_review": rel(LISTENING_RESULT_PATH),
        "audio_files_copied_into_public_evidence": False,
        "instructions": "Create manual_review_filled.json beside this template, fill ratings from 1 to 5, and keep audio files in local_artifacts only.",
        "rating_scale": {
            "1": "poor_or_unusable",
            "2": "weak",
            "3": "acceptable_with_caveats",
            "4": "good",
            "5": "excellent",
            "artifact_severity_and_robotic_sound": "For these two fields, 1 means low severity and 5 means severe.",
        },
        "entries": entries,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "provider_calls_made": False,
        "liquid_inference_run": False,
        "audio_files_copied": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "side_effects": side_effects(),
    }
    write_json(TEMPLATE_JSON_PATH, template)

    lines = [
        "# LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001",
        "",
        "Fill `manual_review_filled.json` using the same entries and 1-5 rating fields. Do not move or copy audio files.",
        "",
        "| case_id | local_audio_path | intelligibility | naturalness | voice quality | sales tone | pacing | artifact severity | robotic sound | thesis demo | product fallback | ElevenLabs comparison | notes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for entry in entries:
        lines.append(
            "| {case_id} | `{path}` |  |  |  |  |  |  |  |  |  |  |  |".format(
                case_id=entry.get("case_id"),
                path=entry.get("local_audio_path"),
            )
        )
    write_text(TEMPLATE_MD_PATH, "\n".join(lines))
    return template


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print or open local Liquid TTS review files.")
    parser.add_argument("--open", action="store_true", help="Open the containing folder for the local TTS files.")
    parser.add_argument("--open-files", action="store_true", help="Open each local TTS file. Implies --open behavior for files only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    listening = read_json(LISTENING_RESULT_PATH)
    template = write_template(listening)
    entries = template.get("entries") if isinstance(template.get("entries"), list) else []
    paths = [str(entry.get("local_audio_path") or "").replace("\\", "/") for entry in entries if isinstance(entry, dict)]
    opened: list[str] = []
    open_errors: list[str] = []

    print("Liquid TTS local review files:")
    for index, path in enumerate(paths, start=1):
        print(f"{index}. {path}")

    if args.open_files:
        for path in paths:
            absolute = ROOT / path
            try:
                os.startfile(str(absolute))  # type: ignore[attr-defined]
                opened.append(path)
            except Exception as exc:  # pragma: no cover - manual helper path
                open_errors.append(f"{path}: {type(exc).__name__}: {exc}")
    elif args.open:
        folders = sorted({str((ROOT / path).parent) for path in paths})
        for folder in folders:
            try:
                os.startfile(folder)  # type: ignore[attr-defined]
                opened.append(folder)
            except Exception as exc:  # pragma: no cover - manual helper path
                open_errors.append(f"{folder}: {type(exc).__name__}: {exc}")

    result = {
        "experiment_id": "LIQUID-AUDIO-LISTENING-REVIEW-MANUAL-001-PLAYBACK-HELPER",
        "generated_at": utc_now(),
        "status": "pass",
        "source_listening_review": rel(LISTENING_RESULT_PATH),
        "manual_review_template_json": rel(TEMPLATE_JSON_PATH),
        "manual_review_template_md": rel(TEMPLATE_MD_PATH),
        "printed_paths": paths,
        "review_entries_count": len(paths),
        "open_requested": bool(args.open or args.open_files),
        "opened": opened,
        "open_errors": open_errors,
        "audio_files_copied": False,
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "liquid_inference_run": False,
        "new_audio_generated": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    write_json(PLAYBACK_RESULT_PATH, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
