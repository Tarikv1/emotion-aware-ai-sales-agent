#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001" / "report.md"
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

    if result.get("experiment_id") != "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001":
        failures.append("ASR result has wrong experiment_id")
    if result.get("status") not in ALLOWED_STATUSES:
        failures.append(f"invalid ASR status: {result.get('status')!r}")
    if result.get("status") in {"not_run", "model_missing", "blocked"} and not str(result.get("blocker") or "").strip():
        failures.append("non-running ASR evidence must record blocker")

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
        require_false(result, key, failures, "asr")

    cases = result.get("cases") if isinstance(result.get("cases"), list) else []
    roundtrip_cases = result.get("roundtrip_cases") if isinstance(result.get("roundtrip_cases"), list) else []
    all_cases = cases + roundtrip_cases
    attempted = int(result.get("asr_attempted_count") or 0)
    succeeded = int(result.get("asr_succeeded_count") or 0)
    if attempted and not all_cases:
        failures.append("ASR attempted count requires cases")
    if attempted != sum(1 for case in all_cases if isinstance(case, dict) and case.get("asr_attempted") is True):
        failures.append("ASR attempted count must match cases")
    if succeeded != sum(1 for case in all_cases if isinstance(case, dict) and case.get("asr_succeeded") is True):
        failures.append("ASR succeeded count must match cases")

    for case in all_cases:
        if not isinstance(case, dict):
            failures.append("ASR cases must be JSON objects")
            continue
        if case.get("audio_source_type") == "liquid_tts_loopback":
            path = str(case.get("audio_input_path") or "").replace("\\", "/")
            if not path.startswith(AUDIO_ROOT):
                failures.append(f"ASR loopback audio path must stay under {AUDIO_ROOT}: {path}")
        if case.get("asr_attempted") is True:
            for key in ("transcript", "normalized_transcript", "critical_term_preserved"):
                if key not in case:
                    failures.append(f"{case.get('case_id')}.{key} must be present")
            if not isinstance(case.get("exact_match"), bool):
                failures.append(f"{case.get('case_id')}.exact_match must be boolean")
            if not isinstance(case.get("fuzzy_match_score"), (int, float)):
                failures.append(f"{case.get('case_id')}.fuzzy_match_score must be numeric")
            if case.get("asr_succeeded") is True and not isinstance(case.get("latency_seconds"), (int, float)):
                failures.append(f"{case.get('case_id')}.latency_seconds must be numeric when ASR succeeds")
            if case.get("asr_succeeded") is not True and not str(case.get("exact_blocker") or "").strip():
                failures.append(f"{case.get('case_id')} failed ASR case must record exact_blocker")
        elif not str(case.get("exact_blocker") or "").strip():
            failures.append(f"{case.get('case_id')} skipped ASR case must record exact_blocker")

    if result.get("loopback_only") is True:
        report_lower = report.lower()
        if "loopback" not in report_lower or "not a final asr quality test" not in report_lower:
            failures.append("loopback ASR report must say loopback and not final ASR quality test")
        if result.get("asr_quality_claim") != "unproven_loopback_only":
            failures.append("loopback ASR must not overclaim quality")

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
        require_false(side_effects, key, failures, "asr.side_effects")
    if side_effects.get("audio_files_generated") is not False and not allowed_audio:
        failures.append("asr.side_effects.audio_files_generated can be true only for allowed local loopback output")
    if side_effects.get("local_model_generation_made") is not False and not allowed_audio:
        failures.append("asr.side_effects.local_model_generation_made can be true only for allowed local loopback output")

    tracked = git_lines(["ls-files"])
    tracked_weights = [path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)]
    tracked_audio = [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "asr_status": result.get("status"),
        "asr_attempted_count": attempted,
        "asr_succeeded_count": succeeded,
        "asr_source_type": result.get("asr_source_type"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
