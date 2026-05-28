#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_DIR = ROOT / "runtime" / "audio_backends" / "benchmark_plans"
REQUIRED_PLANS = {
    "liquid_audio_feasibility_plan.json": "liquid_audio_lfm25",
    "kokoro_tts_benchmark_plan.json": "kokoro_82m",
    "fish_inspired_prosody_policy_plan.json": "fish_audio_s2",
}
EVIDENCE_DIR = ROOT / "research" / "experiments" / "generated" / "LOCAL-AUDIO-BENCHMARK-PLANS-001"
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


def main() -> int:
    failures: list[str] = []
    for filename, backend_id in REQUIRED_PLANS.items():
        path = PLAN_DIR / filename
        plan = load_json(path)
        if plan.get("candidate_backend_id") != backend_id:
            failures.append(f"{filename} candidate_backend_id must be {backend_id}")
        if plan.get("allowed_in_phase_4I0") is not False:
            failures.append(f"{filename} must not be allowed in Phase 4I0")
        if not isinstance(plan.get("source_urls"), list) or not plan.get("source_urls"):
            failures.append(f"{filename} must include source_urls")
        planned_steps = " ".join(str(item).lower() for item in plan.get("planned_steps", []))
        blocked_steps = " ".join(str(item).lower() for item in plan.get("blocked_steps", []))
        combined = planned_steps + " " + blocked_steps
        if "live" not in blocked_steps or "wiring" not in blocked_steps:
            failures.append(f"{filename} must block live wiring")
        if backend_id == "liquid_audio_lfm25":
            if "no model download unless explicitly gated" not in planned_steps:
                failures.append("Liquid plan must gate model downloads")
            if "asr benchmark" not in planned_steps or "tts benchmark" not in planned_steps:
                failures.append("Liquid plan must include ASR and TTS benchmarks")
        if backend_id == "kokoro_82m":
            for required in ("cold latency", "warm latency", "real-time factor", "subjective quality"):
                if required not in combined:
                    failures.append(f"Kokoro plan missing {required}")
            if "isolated .venv-audio or .venv-tts" not in combined:
                failures.append("Kokoro plan must require isolated audio venv")
        if backend_id == "fish_audio_s2":
            if plan.get("model_install_allowed") is not False or plan.get("model_download_allowed") is not False:
                failures.append("Fish-inspired plan must forbid model install/download")
            if "tag leakage" not in combined:
                failures.append("Fish-inspired plan must validate no tag leakage")

    tracked = git_lines(["ls-files"])
    weights = [path for path in tracked if path.lower().endswith(FORBIDDEN_WEIGHT_SUFFIXES) or path.startswith("local_artifacts/")]
    audio = [path for path in tracked if path.lower().endswith(FORBIDDEN_AUDIO_SUFFIXES)]
    if weights:
        failures.append(f"tracked model/checkpoint files are forbidden: {weights[:20]}")
    if audio:
        failures.append(f"tracked audio files are forbidden: {audio[:20]}")

    for evidence_name in ("result.json", "report.md"):
        if not (EVIDENCE_DIR / evidence_name).is_file():
            failures.append(f"missing evidence: {rel(EVIDENCE_DIR / evidence_name)}")

    result = {
        "status": "pass" if not failures else "fail",
        "plan_dir": rel(PLAN_DIR),
        "plan_count": len(REQUIRED_PLANS),
        "failures": failures,
        "model_downloads_performed": False,
        "provider_calls_made": False,
        "live_runtime_wiring_changed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
