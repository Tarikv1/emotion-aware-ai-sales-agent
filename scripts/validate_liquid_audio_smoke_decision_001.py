#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DECISION-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DECISION-001" / "report.md"
TTS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001" / "result.json"
ASR_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001" / "result.json"
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
    decision = load_json(RESULT_PATH)
    tts = load_json(TTS_RESULT_PATH)
    asr = load_json(ASR_RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if decision.get("experiment_id") != "LIQUID-AUDIO-SMOKE-DECISION-001":
        failures.append("decision result has wrong experiment_id")
    if decision.get("status") not in {"pass", "not_run", "model_missing", "blocked"}:
        failures.append(f"invalid decision status: {decision.get('status')!r}")
    if decision.get("live_wiring_allowed") is not False:
        failures.append("decision live_wiring_allowed must be false")
    if decision.get("sales_brain_replacement_allowed") is not False:
        failures.append("decision sales_brain_replacement_allowed must be false")
    if not str(decision.get("recommendation_id") or "").strip():
        failures.append("decision recommendation_id must be recorded")
    if not str(decision.get("next_phase_recommendation") or "").strip():
        failures.append("decision next_phase_recommendation must be recorded")
    if not str(decision.get("asr_next_phase_recommendation") or "").strip():
        failures.append("decision asr_next_phase_recommendation must be recorded")

    tts_summary = decision.get("tts_summary") if isinstance(decision.get("tts_summary"), dict) else {}
    asr_summary = decision.get("asr_summary") if isinstance(decision.get("asr_summary"), dict) else {}
    if tts_summary.get("attempted") != tts.get("tts_attempted_count"):
        failures.append("decision TTS attempted count must mirror TTS evidence")
    if tts_summary.get("succeeded") != tts.get("tts_succeeded_count"):
        failures.append("decision TTS succeeded count must mirror TTS evidence")
    if asr_summary.get("attempted") != asr.get("asr_attempted_count"):
        failures.append("decision ASR attempted count must mirror ASR evidence")
    if asr_summary.get("succeeded") != asr.get("asr_succeeded_count"):
        failures.append("decision ASR succeeded count must mirror ASR evidence")
    if asr.get("loopback_only") is True:
        combined = (str(decision.get("asr_next_phase_recommendation") or "") + "\n" + report).lower()
        if "unproven" not in combined or "independent asr" not in combined:
            failures.append("loopback ASR decision must call ASR unproven and recommend independent ASR benchmark")

    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "raw_private_audio_used",
        "raw_private_transcripts_included",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        require_false(decision, key, failures, "decision")

    side_effects = decision.get("side_effects") if isinstance(decision.get("side_effects"), dict) else {}
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
        require_false(side_effects, key, failures, "decision.side_effects")
    if side_effects.get("audio_files_generated") is not False and not allowed_audio:
        failures.append("decision.side_effects.audio_files_generated can be true only for allowed local smoke output")
    if side_effects.get("local_model_generation_made") is not False and not allowed_audio:
        failures.append("decision.side_effects.local_model_generation_made can be true only for allowed local smoke output")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "recommendation_id": decision.get("recommendation_id"),
        "tts_succeeded": tts_summary.get("succeeded"),
        "asr_succeeded": asr_summary.get("succeeded"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
