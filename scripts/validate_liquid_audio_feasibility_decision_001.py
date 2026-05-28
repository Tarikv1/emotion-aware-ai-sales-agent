#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-DECISION-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-DECISION-001" / "report.md"
ENV_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENVIRONMENT-PROBE-001" / "result.json"
SMOKE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001" / "result.json"
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


def false_side_effect(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def main() -> int:
    failures: list[str] = []
    decision = load_json(RESULT_PATH)
    environment = load_json(ENV_RESULT_PATH)
    smoke = load_json(SMOKE_RESULT_PATH)
    if not REPORT_PATH.is_file():
        failures.append(f"missing report: {rel(REPORT_PATH)}")

    if decision.get("experiment_id") != "LIQUID-AUDIO-FEASIBILITY-DECISION-001":
        failures.append("decision result has wrong experiment_id")
    if decision.get("status") != "pass":
        failures.append("decision status must be pass")
    for key in ("environment_ready", "model_present", "download_phase_recommended", "actual_smoke_recommended"):
        if not isinstance(decision.get(key), bool):
            failures.append(f"decision.{key} must be boolean")
    if decision.get("live_wiring_allowed") is not False:
        failures.append("decision live_wiring_allowed must be false")
    if decision.get("sales_brain_replacement_allowed") is not False:
        failures.append("decision sales_brain_replacement_allowed must be false")
    if not str(decision.get("next_phase_recommendation") or "").strip():
        failures.append("decision next_phase_recommendation must be present")
    if not str(decision.get("recommendation_id") or "").strip():
        failures.append("decision recommendation_id must be present")
    if "install_success" not in decision:
        failures.append("decision install_success must be recorded")
    if decision.get("install_success") is False and not str(decision.get("exact_blocker") or "").strip():
        failures.append("decision exact_blocker must be recorded when install failed")
    if decision.get("environment_status") != environment.get("status"):
        failures.append("decision environment_status must mirror environment result")
    if decision.get("smoke_status") != smoke.get("status"):
        failures.append("decision smoke_status must mirror smoke result")
    env_model_present = bool((environment.get("model_status") or {}).get("model_present")) if isinstance(environment.get("model_status"), dict) else False
    smoke_model_present = bool(smoke.get("model_present"))
    if decision.get("model_present") is not (env_model_present or smoke_model_present):
        failures.append("decision model_present must mirror environment/smoke evidence")
    if smoke.get("status") in {"not_run", "model_missing", "blocked"} and not str(smoke.get("blocker") or "").strip():
        failures.append("smoke blocker must be recorded when smoke did not run")

    side_effects = decision.get("side_effects") if isinstance(decision.get("side_effects"), dict) else {}
    audio_generation_allowed = bool(smoke.get("status") == "pass" and side_effects.get("allowed_local_audio_generation") is True)
    for key in (
        "model_download_attempted",
        "model_downloads_performed",
        "model_weights_committed",
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
        false_side_effect(side_effects, key, failures, "decision.side_effects")
    if side_effects.get("audio_files_generated") is not False and not audio_generation_allowed:
        failures.append("decision.side_effects.audio_files_generated can be true only for allowed gated local audio generation")
    if side_effects.get("local_model_generation_made") is not False and not audio_generation_allowed:
        failures.append("decision.side_effects.local_model_generation_made can be true only for allowed gated local audio generation")

    tracked = git_lines(["ls-files"])
    weights = [path for path in tracked if path.lower().endswith(FORBIDDEN_WEIGHT_SUFFIXES) or path.startswith("local_artifacts/")]
    audio = [path for path in tracked if path.lower().endswith(FORBIDDEN_AUDIO_SUFFIXES)]
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")

    validation = {
        "status": "pass" if not failures else "fail",
        "recommendation_id": decision.get("recommendation_id"),
        "environment_status": decision.get("environment_status"),
        "smoke_status": decision.get("smoke_status"),
        "failures": failures,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(validation, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
