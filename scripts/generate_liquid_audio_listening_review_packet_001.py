#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TTS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001" / "result.json"
AUDIO_ROOT = ROOT / "local_artifacts" / "audio_outputs" / "liquid"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


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
        "new_liquid_inference_run": False,
        "new_audio_generated": False,
        "model_download_attempted": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_committed": bool(tracked_audio_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
    }


def main() -> int:
    tts = read_json(TTS_RESULT_PATH)
    cases = [case for case in tts.get("cases", []) if isinstance(case, dict)]
    entries: list[dict[str, Any]] = []
    for case in cases:
        local_path = str(case.get("output_audio_path") or "").replace("\\", "/")
        file_path = ROOT / local_path
        entries.append(
            {
                "case_id": case.get("case_id"),
                "input_text": case.get("input_text"),
                "local_audio_file_path": local_path,
                "absolute_audio_file_path": str(file_path),
                "under_local_artifacts": local_path.startswith("local_artifacts/audio_outputs/liquid/"),
                "file_exists": file_path.is_file(),
                "file_size_bytes": file_path.stat().st_size if file_path.is_file() else None,
                "duration_seconds": case.get("duration_seconds"),
                "sample_rate": case.get("sample_rate"),
                "waveform_hash": case.get("waveform_hash"),
                "latency_seconds": case.get("generation_latency_seconds"),
                "first_audio_latency_seconds": case.get("first_audio_latency_seconds"),
                "real_time_factor": case.get("real_time_factor"),
                "audio_committed": False,
            }
        )

    checklist = [
        "intelligibility",
        "naturalness",
        "voice quality",
        "artifacts/glitches",
        "emotional/prosody suitability for sales",
        "speed/pacing",
        "whether it sounds robotic",
        "whether it is acceptable for thesis demo",
        "whether it is acceptable as product fallback",
        "whether it beats or loses to ElevenLabs",
    ]
    table_lines = [
        "| case_id | intelligibility 1-5 | naturalness 1-5 | sales tone 1-5 | artifact severity 1-5 | notes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for entry in entries:
        table_lines.append(f"| {entry['case_id']} |  |  |  |  |  |")

    result = {
        "experiment_id": "LIQUID-AUDIO-LISTENING-REVIEW-001",
        "generated_at": utc_now(),
        "status": "pass",
        "input_tts_result": rel(TTS_RESULT_PATH),
        "audio_root": rel(AUDIO_ROOT),
        "audio_files_copied_into_public_evidence": False,
        "review_entries": entries,
        "manual_listening_checklist": checklist,
        "manual_review_table_markdown": "\n".join(table_lines),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_committed": bool(tracked_audio_files()),
        "side_effects": side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-LISTENING-REVIEW-001",
                "",
                f"- status: {result['status']}",
                f"- audio_root: `{result['audio_root']}`",
                "- audio_files_copied_into_public_evidence: false",
                f"- review_entry_count: {len(entries)}",
                "- provider_calls_made: false",
                "- live_wiring_allowed: false",
                "- sales_brain_replacement_allowed: false",
                "",
                "## Manual Listening Checklist",
                "",
                *[f"- {item}" for item in checklist],
                "",
                "## Review Table",
                "",
                result["manual_review_table_markdown"],
                "",
                "Audio remains in ignored local artifacts. This packet records paths, metadata, and hashes only.",
            ]
        ),
    )
    print(json.dumps({"status": "pass", "review_entry_count": len(entries), "packet": rel(RESULT_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
