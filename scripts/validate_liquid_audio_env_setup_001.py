#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_env_config.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENV-SETUP-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENV-SETUP-001" / "report.md"
FORBIDDEN_WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
FORBIDDEN_AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


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


def git_check_ignore(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.returncode == 0


def false_value(payload: dict[str, Any], key: str, failures: list[str]) -> None:
    if payload.get(key) is not False:
        failures.append(f"setup.{key} must be false")


def main() -> int:
    failures: list[str] = []
    config = load_json(CONFIG_PATH)
    result = load_json(RESULT_PATH)
    if not REPORT_PATH.is_file():
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if config.get("env_name") != ".venv-audio":
        failures.append("config env_name must be .venv-audio")
    if config.get("python_executable_expected") != ".venv-audio/Scripts/python.exe":
        failures.append("config python_executable_expected must target .venv-audio")
    if config.get("install_scope") != "isolated_audio_experiment":
        failures.append("config install_scope must be isolated_audio_experiment")
    for key in (
        "install_flash_attn_by_default",
        "install_demo_extra_by_default",
        "model_download_allowed_by_default",
        "inference_allowed_by_default",
        "live_wiring_allowed",
        "sales_brain_replacement_allowed",
    ):
        if config.get(key) is not False:
            failures.append(f"config.{key} must be false")
    if not git_check_ignore(".venv-audio/"):
        failures.append(".venv-audio/ must be git ignored")

    if result.get("experiment_id") != "LIQUID-AUDIO-ENV-SETUP-001":
        failures.append("setup result has wrong experiment_id")
    if result.get("setup_attempted") is not True:
        failures.append("setup_attempted must be true")
    if result.get("python_executable") and ".venv-audio" not in str(result.get("python_executable")).replace("\\", "/"):
        failures.append("setup python_executable must be inside .venv-audio")
    if result.get("install_success") is False and not str(result.get("exact_blocker") or "").strip():
        failures.append("failed install must record exact_blocker")
    if result.get("install_success") is True:
        versions = result.get("package_versions") if isinstance(result.get("package_versions"), dict) else {}
        for name in ("torch", "torchaudio", "liquid_audio"):
            item = versions.get(name) if isinstance(versions.get(name), dict) else {}
            if not item.get("version"):
                failures.append(f"successful install must record {name} version")
            if item.get("module_found") is not True:
                failures.append(f"successful install must import {name}")
    versions = result.get("package_versions") if isinstance(result.get("package_versions"), dict) else {}
    if (versions.get("torch") or {}).get("module_found") is True:
        if "torch_cuda_available" not in result:
            failures.append("torch CUDA status must be recorded")
        if "torch_cuda_version" not in result:
            failures.append("torch CUDA version must be recorded")

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
        "inference_run",
        "runtime_behavior_changed",
        "response_text_changed",
        "live_wiring_allowed",
        "sales_brain_replacement_allowed",
        "flash_attn_install_attempted",
        "demo_extra_install_attempted",
    ):
        false_value(result, key, failures)

    tracked = git_lines(["ls-files"])
    tracked_weights = [
        path
        for path in tracked
        if path.startswith("local_artifacts/") or path.lower().endswith(FORBIDDEN_WEIGHT_SUFFIXES)
    ]
    tracked_audio = [path for path in tracked if path.lower().endswith(FORBIDDEN_AUDIO_SUFFIXES)]
    tracked_audio_env = [path for path in tracked if path.startswith(".venv-audio/")]
    if tracked_weights:
        failures.append(f"tracked model/checkpoint/local_artifacts files are forbidden: {tracked_weights[:20]}")
    if tracked_audio:
        failures.append(f"tracked audio files are forbidden: {tracked_audio[:20]}")
    if tracked_audio_env:
        failures.append(f".venv-audio files must not be committed: {tracked_audio_env[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "install_success": result.get("install_success"),
        "venv_created": result.get("venv_created"),
        "torch_cuda_available": result.get("torch_cuda_available"),
        "failures": failures,
        "model_download_attempted": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
