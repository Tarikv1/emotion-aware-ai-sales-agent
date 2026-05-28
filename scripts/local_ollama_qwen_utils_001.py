#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"
CONFIG_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_ollama_backend_benchmark_config.json"
PRUNING_PLAN_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen7b_pruning_experiment_plan.json"
LOCAL_MODEL_PATH = ROOT / "local_artifacts" / "models" / "qwen2.5-7b-instruct"
PRUNED_MODELS_DIR = ROOT / "local_artifacts" / "pruned_models"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_ALIAS = "qwen2.5:latest"
TARGETS_SECONDS = {"p50": 2.0, "p90": 3.0, "p99": 4.0}
EXPERIMENT_ENV_VAR = "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT"
LOCAL_LLM_ENABLED_ENV_VAR = "LOCAL_LLM_ENABLED"
OLLAMA_BENCHMARK_ENV_VAR = "LOCAL_OLLAMA_BENCHMARK_ENABLED"
OLLAMA_PULL_ENV_VAR = "LOCAL_OLLAMA_ALLOW_MODEL_PULL"
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt")


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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def ollama_benchmark_enabled() -> bool:
    return env_flag(EXPERIMENT_ENV_VAR) and env_flag(LOCAL_LLM_ENABLED_ENV_VAR) and env_flag(OLLAMA_BENCHMARK_ENV_VAR)


def env_gate_report() -> dict[str, Any]:
    return {
        EXPERIMENT_ENV_VAR: env_flag(EXPERIMENT_ENV_VAR),
        LOCAL_LLM_ENABLED_ENV_VAR: env_flag(LOCAL_LLM_ENABLED_ENV_VAR),
        OLLAMA_BENCHMARK_ENV_VAR: env_flag(OLLAMA_BENCHMARK_ENV_VAR),
        OLLAMA_PULL_ENV_VAR: env_flag(OLLAMA_PULL_ENV_VAR),
    }


def localhost_url(path: str) -> str:
    base = urllib.parse.urlparse(OLLAMA_BASE_URL)
    if base.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError(f"blocked non-local Ollama host: {base.hostname}")
    return urllib.parse.urljoin(OLLAMA_BASE_URL.rstrip("/") + "/", path.lstrip("/"))


def http_json(path: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout_s: float = 5.0) -> tuple[dict[str, Any] | None, str]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(localhost_url(path), data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            text = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, str(exc)
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"invalid_json:{exc}"
    return decoded if isinstance(decoded, dict) else {"value": decoded}, ""


def command_json(args: list[str], *, timeout_s: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout_s, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    return {
        "available": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def ollama_model_records(tags_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(tags_payload, dict):
        return []
    models = tags_payload.get("models")
    if not isinstance(models, list):
        return []
    return [item for item in models if isinstance(item, dict)]


def ollama_model_names(tags_payload: dict[str, Any] | None) -> list[str]:
    names: list[str] = []
    for item in ollama_model_records(tags_payload):
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and name:
            names.append(name)
    return sorted(set(names))


def qwen_ollama_model_present(tags_payload: dict[str, Any] | None) -> tuple[bool, str, str]:
    for item in ollama_model_records(tags_payload):
        name = str(item.get("name") or item.get("model") or "")
        details = item.get("details") if isinstance(item.get("details"), dict) else {}
        parameter_size = str(details.get("parameter_size") or item.get("parameter_size") or "")
        if name == OLLAMA_MODEL:
            return True, name, parameter_size
        if name == OLLAMA_ALIAS and "7" in parameter_size.lower():
            return True, name, parameter_size
    return False, "", ""


def approx_token_count(text: str) -> int:
    if not text:
        return 0
    # Local Ollama responses may omit token counts. This is only a stable approximation.
    return max(1, math.ceil(len(text) / 4))


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * q)))
    return round(ordered[index], 3)


def avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def mode_target_met(metrics: dict[str, Any]) -> bool:
    p50 = metrics.get("total_generation_latency_p50_s")
    p90 = metrics.get("total_generation_latency_p90_s")
    p99 = metrics.get("total_generation_latency_p99_s")
    return bool(
        isinstance(p50, (int, float))
        and isinstance(p90, (int, float))
        and isinstance(p99, (int, float))
        and p50 <= TARGETS_SECONDS["p50"]
        and p90 <= TARGETS_SECONDS["p90"]
        and p99 <= TARGETS_SECONDS["p99"]
    )


def tracked_model_or_adapter_files() -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [
        line.strip().replace("\\", "/")
        for line in completed.stdout.splitlines()
        if line.strip().lower().endswith(WEIGHT_SUFFIXES) or line.strip().replace("\\", "/").startswith("local_artifacts/")
    ]


def pruned_weight_files() -> list[str]:
    if not PRUNED_MODELS_DIR.exists():
        return []
    return [rel(path) for path in PRUNED_MODELS_DIR.rglob("*") if path.is_file() and path.suffix.lower() in WEIGHT_SUFFIXES]


def runtime_behavior_changed_by_files(files: list[str]) -> bool:
    return any(path.startswith("runtime/") and not path.startswith("runtime/llm_brain/training/") for path in files)


def changed_files() -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def audit_side_effects(*, local_model_calls_made: bool = False, ollama_localhost_calls_made: bool = False, ollama_pull_attempted: bool = False) -> dict[str, Any]:
    return {
        "local_model_calls_made": local_model_calls_made,
        "ollama_localhost_calls_made": ollama_localhost_calls_made,
        "ollama_pull_attempted": ollama_pull_attempted,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "training_rerun": False,
        "actual_pruning_performed": False,
        "pruned_weights_created": False,
        "model_download_attempted": False,
        "model_redownloaded": False,
        "model_weights_committed": False,
        "adapter_files_committed": False,
        "pruned_weights_committed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_transcript_included": False,
        "raw_private_transcript_copied_to_public_evidence": False,
    }
