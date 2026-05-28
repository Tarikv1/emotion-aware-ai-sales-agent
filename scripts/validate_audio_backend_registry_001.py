#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.audio_backends.audio_backend_registry import validate_audio_backend_candidate_shape

REGISTRY_PATH = ROOT / "runtime" / "audio_backends" / "audio_backend_candidates.json"
REQUIRED_BACKENDS = {
    "elevenlabs_existing_provider",
    "liquid_audio_lfm25",
    "fish_audio_s2",
    "kokoro_82m",
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


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def runtime_behavior_changed(files: list[str]) -> bool:
    for path in files:
        if not path.startswith("runtime/"):
            continue
        if path.startswith(ALLOWED_RUNTIME_RESEARCH_PREFIXES):
            continue
        return True
    return False


def false_flag(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def main() -> int:
    failures: list[str] = []
    registry = load_json(REGISTRY_PATH)
    if registry.get("registry_id") != "local-audio-backend-registry-001":
        failures.append("registry_id must be local-audio-backend-registry-001")
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        failures.append("registry.candidates must be a list")
        candidates = []
    by_id = {item.get("backend_id"): item for item in candidates if isinstance(item, dict)}
    missing = sorted(REQUIRED_BACKENDS - set(by_id))
    if missing:
        failures.append(f"missing backend entries: {missing}")

    for candidate in candidates:
        if not isinstance(candidate, dict):
            failures.append("candidate entries must be objects")
            continue
        failures.extend(validate_audio_backend_candidate_shape(candidate))
        backend_id = candidate.get("backend_id")
        for field_name in ("license_name", "license_summary", "commercial_use_status", "license_url", "source_evidence"):
            if field_name not in candidate or candidate.get(field_name) in ("", None, []):
                failures.append(f"{backend_id}.{field_name} must be present")

    liquid = by_id.get("liquid_audio_lfm25", {})
    if liquid.get("live_runtime_allowed") is not False:
        failures.append("Liquid must not be live-runtime allowed")
    if liquid.get("integration_classification") != "integration_candidate":
        failures.append("Liquid must be an integration/feasibility candidate")
    liquid_role = str(liquid.get("role_in_project") or "").lower()
    if "sales brain" not in liquid_role or "must not replace" not in liquid_role:
        failures.append("Liquid role must explicitly keep it out of the sales brain")
    for required_capability in ("ASR", "TTS", "speech-to-speech"):
        if required_capability not in liquid.get("capability_classification", []):
            failures.append(f"Liquid missing capability classification: {required_capability}")

    fish = by_id.get("fish_audio_s2", {})
    if fish.get("live_runtime_allowed") is not False:
        failures.append("Fish must not be live-runtime allowed")
    if fish.get("integration_classification") != "architecture_inspiration_only":
        failures.append("Fish must be architecture_inspiration_only")
    fish_categories = set(fish.get("backend_categories", []))
    if not {"prosody_control_inspiration", "research_only"}.issubset(fish_categories):
        failures.append("Fish must be marked prosody inspiration and research-only")
    if "commercial_use_requires" not in str(fish.get("commercial_use_status") or ""):
        failures.append("Fish commercial-use status must record separate license requirement")

    kokoro = by_id.get("kokoro_82m", {})
    if kokoro.get("live_runtime_allowed") is not False:
        failures.append("Kokoro must not be live-runtime allowed")
    if kokoro.get("integration_classification") != "benchmark_candidate":
        failures.append("Kokoro must be a benchmark candidate")
    if "local_tts" not in kokoro.get("backend_categories", []):
        failures.append("Kokoro must be local_tts")
    if "Apache-2.0" not in str(kokoro.get("license_name") or ""):
        failures.append("Kokoro license must be Apache-2.0")

    flags = registry.get("boundary_flags") if isinstance(registry.get("boundary_flags"), dict) else {}
    for key in (
        "model_downloads_performed",
        "model_weights_committed",
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
        "raw_private_transcripts_included",
    ):
        false_flag(flags, key, failures, "registry.boundary_flags")

    weights, audio = tracked_forbidden_files()
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")

    files = changed_files()
    if runtime_behavior_changed(files):
        failures.append("runtime behavior changed outside runtime/audio_backends and runtime manifest")
    if any(path.startswith("data/private") or path.startswith("data/private-restricted") for path in files):
        failures.append("private data path changed")

    result = {
        "status": "pass" if not failures else "fail",
        "registry": rel(REGISTRY_PATH),
        "backend_count": len(candidates),
        "changed_files": files,
        "failures": failures,
        "model_downloads_performed": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
