#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001" / "report.md"
ALLOWED_STATUSES = {"pass", "not_run", "model_missing", "blocked"}
AUDIO_ROOT = "local_artifacts/audio_outputs/liquid/"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


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


def require_false(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def main() -> int:
    failures: list[str] = []
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if result.get("experiment_id") != "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001":
        failures.append("TTS result has wrong experiment_id")
    if result.get("status") not in ALLOWED_STATUSES:
        failures.append(f"invalid TTS status: {result.get('status')!r}")
    if result.get("status") in {"not_run", "model_missing", "blocked"} and not str(result.get("blocker") or "").strip():
        failures.append("non-running TTS evidence must record blocker")

    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
        "live_wiring_allowed",
        "sales_brain_replacement_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
        "audio_files_committed",
        "model_weights_committed",
    ):
        require_false(result, key, failures, "tts")

    cases = result.get("cases") if isinstance(result.get("cases"), list) else []
    attempted = int(result.get("tts_attempted_count") or 0)
    succeeded = int(result.get("tts_succeeded_count") or 0)
    if attempted and not cases:
        failures.append("TTS attempted count requires cases")
    if attempted != sum(1 for case in cases if isinstance(case, dict) and case.get("generation_attempted") is True):
        failures.append("TTS attempted count must match cases")
    if succeeded != sum(1 for case in cases if isinstance(case, dict) and case.get("generation_succeeded") is True):
        failures.append("TTS succeeded count must match cases")

    for case in cases:
        if not isinstance(case, dict):
            failures.append("TTS cases must be JSON objects")
            continue
        if case.get("generation_attempted") is not True:
            failures.append(f"{case.get('case_id')} generation_attempted must be true")
        if case.get("generation_succeeded") is True:
            path = str(case.get("output_audio_path") or "").replace("\\", "/")
            if not path.startswith(AUDIO_ROOT):
                failures.append(f"TTS output path must stay under {AUDIO_ROOT}: {path}")
            for key in ("generation_latency_seconds", "duration_seconds", "sample_rate", "real_time_factor"):
                if not isinstance(case.get(key), (int, float)):
                    failures.append(f"{case.get('case_id')}.{key} must be numeric for successful TTS")
            if not str(case.get("waveform_hash") or "").strip():
                failures.append(f"{case.get('case_id')}.waveform_hash must be recorded")
            if case.get("audio_committed") is not False:
                failures.append(f"{case.get('case_id')}.audio_committed must be false")
        elif not str(case.get("exact_blocker") or "").strip():
            failures.append(f"{case.get('case_id')} failed TTS case must record exact_blocker")

    side_effects = result.get("side_effects") if isinstance(result.get("side_effects"), dict) else {}
    allowed_audio = side_effects.get("allowed_local_audio_generation") is True
    for key in (
        "model_download_attempted",
        "model_downloads_performed",
        "audio_files_committed",
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "ollama_generation_made",
        "training_performed",
        "live_runtime_wiring_changed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
        "sales_brain_replacement_allowed",
        "live_wiring_allowed",
    ):
        require_false(side_effects, key, failures, "tts.side_effects")
    if side_effects.get("audio_files_generated") is not False and not allowed_audio:
        failures.append("tts.side_effects.audio_files_generated can be true only for allowed local smoke output")
    if side_effects.get("local_model_generation_made") is not False and not allowed_audio:
        failures.append("tts.side_effects.local_model_generation_made can be true only for allowed local smoke output")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "tts_status": result.get("status"),
        "tts_attempted_count": attempted,
        "tts_succeeded_count": succeeded,
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
