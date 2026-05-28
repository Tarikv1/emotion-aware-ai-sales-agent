#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
ENV_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_env_config.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENVIRONMENT-PROBE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENVIRONMENT-PROBE-001" / "report.md"
ALLOWED_STATUSES = {
    "not_run",
    "missing_dependencies",
    "model_missing",
    "environment_ready_no_model",
    "ready_for_download_phase",
    "model_present_ready_for_load",
    "model_loaded_ready_for_smoke",
    "blocked",
}
FORBIDDEN_WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
FORBIDDEN_AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
ALLOWED_RUNTIME_RESEARCH_PREFIXES = (
    "runtime/audio_backends/",
    "runtime/runtime_manifest.json",
)


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


def tracked_forbidden_files() -> tuple[list[str], list[str]]:
    tracked = git_lines(["ls-files"])
    weights = [path for path in tracked if path.lower().endswith(FORBIDDEN_WEIGHT_SUFFIXES) or path.startswith("local_artifacts/")]
    audio = [path for path in tracked if path.lower().endswith(FORBIDDEN_AUDIO_SUFFIXES)]
    return weights, audio


def runtime_behavior_changed(files: list[str]) -> bool:
    for path in files:
        if not path.startswith("runtime/"):
            continue
        if path.startswith(ALLOWED_RUNTIME_RESEARCH_PREFIXES):
            continue
        return True
    return False


def false_side_effect(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def main() -> int:
    failures: list[str] = []
    config = load_json(CONFIG_PATH)
    env_config = load_json(ENV_CONFIG_PATH)
    result = load_json(RESULT_PATH)
    if not REPORT_PATH.is_file():
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    for key in ("source_repo", "model_card", "license_docs", "audio_model_docs"):
        if not str(config.get(key) or "").startswith("https://"):
            failures.append(f"config.{key} must be an https source URL")
    if config.get("backend_id") != "liquid_audio_lfm25":
        failures.append("config backend_id must be liquid_audio_lfm25")
    boundaries = config.get("runtime_boundaries") if isinstance(config.get("runtime_boundaries"), dict) else {}
    for key in (
        "live_wiring_allowed",
        "sales_brain_replacement_allowed",
        "model_download_allowed_by_default",
        "provider_calls_allowed",
        "elevenlabs_calls_allowed",
        "live_tts_calls_allowed",
        "raw_private_audio_allowed",
        "raw_private_transcripts_allowed",
        "model_weights_committable",
        "generated_audio_committable",
    ):
        if boundaries.get(key) is not False:
            failures.append(f"runtime_boundaries.{key} must be false")

    if result.get("experiment_id") != "LIQUID-AUDIO-ENVIRONMENT-PROBE-001":
        failures.append("environment result has wrong experiment_id")
    if result.get("status") not in ALLOWED_STATUSES:
        failures.append(f"invalid environment status: {result.get('status')!r}")
    if result.get("live_wiring_allowed") is not False:
        failures.append("environment live_wiring_allowed must be false")
    if result.get("sales_brain_replacement_allowed") is not False:
        failures.append("environment sales_brain_replacement_allowed must be false")
    if not str(result.get("active_python_env") or "").strip():
        failures.append("environment active_python_env must be recorded")
    if result.get("expected_audio_env") != env_config.get("python_executable_expected"):
        failures.append("environment expected_audio_env must mirror audio env config")
    if not isinstance(result.get("running_inside_audio_env"), bool):
        failures.append("environment running_inside_audio_env must be boolean")
    dependency_status = result.get("dependency_status") if isinstance(result.get("dependency_status"), dict) else {}
    for key in ("package_versions", "liquid_audio_import_ok", "torchaudio_import_ok"):
        if key not in dependency_status:
            failures.append(f"environment dependency_status.{key} must be recorded")

    path_status = result.get("path_status") if isinstance(result.get("path_status"), dict) else {}
    for name in ("local_model_path", "cache_path", "output_audio_path"):
        item = path_status.get(name) if isinstance(path_status.get(name), dict) else {}
        if item.get("under_local_artifacts") is not True:
            failures.append(f"{name} must be under local_artifacts")
        if item.get("git_ignored") is not True:
            failures.append(f"{name} must be git ignored")

    side_effects = result.get("side_effects") if isinstance(result.get("side_effects"), dict) else {}
    for key in (
        "model_download_attempted",
        "model_downloads_performed",
        "model_weights_committed",
        "audio_files_generated",
        "audio_files_committed",
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "local_model_generation_made",
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
        false_side_effect(side_effects, key, failures, "environment.side_effects")

    weights, audio = tracked_forbidden_files()
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")
    changed = git_lines(["diff", "--name-only", "HEAD"])
    if runtime_behavior_changed(changed):
        failures.append("runtime behavior changed outside audio backend research files")
    if any(path.startswith("data/private") or path.startswith("data/private-restricted") for path in changed):
        failures.append("private data path changed")

    validation = {
        "status": "pass" if not failures else "fail",
        "environment_status": result.get("status"),
        "model_present": (result.get("model_status") or {}).get("model_present") if isinstance(result.get("model_status"), dict) else None,
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
