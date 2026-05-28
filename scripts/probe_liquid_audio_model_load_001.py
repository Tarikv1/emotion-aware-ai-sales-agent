#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from download_liquid_audio_model_001 import write_model_decision


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_model_probe_config.json"
DOWNLOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-DOWNLOAD-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001"
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


def env_gate_report(required: dict[str, str]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "expected": expected,
            "actual": os.getenv(name, ""),
            "enabled": str(os.getenv(name, "")).strip().lower() == expected.strip().lower(),
        }
        for name, expected in required.items()
    }


def gates_enabled(gates: dict[str, dict[str, Any]]) -> bool:
    return all(bool(item.get("enabled")) for item in gates.values())


def active_python_report(config: dict[str, Any]) -> dict[str, Any]:
    expected_rel = str(config.get("python_executable") or ".venv-audio/Scripts/python.exe")
    expected = (ROOT / expected_rel).resolve()
    active = Path(sys.executable).resolve()
    return {
        "active_python_env": str(active),
        "expected_python_env": expected_rel.replace("\\", "/"),
        "running_inside_audio_env": active == expected,
    }


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


def model_inventory(model_path: Path) -> dict[str, Any]:
    files = [path for path in model_path.rglob("*") if path.is_file()] if model_path.exists() else []
    weight_files = [path for path in files if path.suffix.lower() in MODEL_SUFFIXES]
    return {
        "model_path": rel(model_path),
        "model_path_exists": model_path.exists(),
        "model_file_count": len(files),
        "model_weight_file_count": len(weight_files),
        "total_approx_bytes": sum(path.stat().st_size for path in files),
        "sample_filenames": [rel(path) for path in files[:30]],
        "sample_weight_filenames": [rel(path) for path in weight_files[:30]],
    }


def tracked_forbidden_files() -> dict[str, list[str]]:
    tracked = git_lines(["ls-files"])
    return {
        "model_weights_or_local_artifacts": [
            path for path in tracked if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)
        ],
        "audio_files": [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)],
    }


def side_effects() -> dict[str, bool]:
    return {
        "audio_files_committed": False,
        "audio_files_generated": False,
        "elevenlabs_calls_made": False,
        "inference_run": False,
        "live_runtime_wiring_changed": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": False,
        "model_download_attempted": False,
        "model_downloads_performed": False,
        "model_weights_committed": False,
        "ollama_generation_made": False,
        "openai_api_calls_made": False,
        "provider_calls_made": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
        "response_text_changed": False,
        "runtime_behavior_changed": False,
        "sales_brain_replacement_allowed": False,
        "training_performed": False,
        "live_wiring_allowed": False,
    }


def cpu_memory_mb() -> float | None:
    try:
        import psutil

        process = psutil.Process(os.getpid())
        return round(float(process.memory_info().rss) / (1024**2), 2)
    except Exception:
        return None


def empty_cuda_cache(torch_module: Any) -> None:
    try:
        if torch_module.cuda.is_available():
            torch_module.cuda.empty_cache()
    except Exception:
        return


def gpu_memory_snapshot(torch_module: Any) -> dict[str, Any]:
    if not torch_module.cuda.is_available():
        return {
            "cuda_available": False,
            "device_name": "",
            "memory_allocated_bytes": 0,
            "memory_reserved_bytes": 0,
            "max_memory_allocated_bytes": 0,
            "max_memory_reserved_bytes": 0,
            "mem_get_info_free_bytes": None,
            "mem_get_info_total_bytes": None,
            "peak_reserved_ratio_of_total": None,
        }
    free_bytes, total_bytes = torch_module.cuda.mem_get_info()
    peak_reserved = int(torch_module.cuda.max_memory_reserved())
    return {
        "cuda_available": True,
        "device_name": torch_module.cuda.get_device_name(0),
        "memory_allocated_bytes": int(torch_module.cuda.memory_allocated()),
        "memory_reserved_bytes": int(torch_module.cuda.memory_reserved()),
        "max_memory_allocated_bytes": int(torch_module.cuda.max_memory_allocated()),
        "max_memory_reserved_bytes": peak_reserved,
        "mem_get_info_free_bytes": int(free_bytes),
        "mem_get_info_total_bytes": int(total_bytes),
        "peak_reserved_ratio_of_total": round(float(peak_reserved) / float(total_bytes), 4) if total_bytes else None,
    }


def main() -> int:
    config = read_json(CONFIG_PATH)
    if not config:
        raise AssertionError(f"Missing config: {rel(CONFIG_PATH)}")

    model_path = ROOT / str(config.get("local_model_path") or "")
    gates = env_gate_report(config.get("load_probe_env_required") if isinstance(config.get("load_probe_env_required"), dict) else {})
    active_python = active_python_report(config)
    inventory = model_inventory(model_path)
    blocker = ""
    exact_blocker = ""
    status = "not_run"
    load_attempted = False
    load_succeeded = False
    processor_load_attempted = False
    processor_load_succeeded = False
    full_model_load_attempted = False
    full_model_load_succeeded = False
    processor_load_time_seconds: float | None = None
    full_model_load_time_seconds: float | None = None
    device = "cuda"
    dtype = "bfloat16"
    gpu_memory: dict[str, Any] = {}
    cpu_memory = {"before_mb": cpu_memory_mb(), "after_mb": None}

    if not active_python["running_inside_audio_env"]:
        status = "blocked"
        blocker = "load probe must run with .venv-audio/Scripts/python.exe"
        exact_blocker = blocker
    elif not gates_enabled(gates):
        status = "not_run"
        blocker = "load env gates are disabled"
    elif inventory["model_file_count"] == 0:
        status = "model_missing"
        blocker = "model files are missing from local_artifacts/audio_models/liquid/lfm2.5-audio-1.5b"
    else:
        load_attempted = True
        status = "load_failed"
        model = None
        processor = None
        try:
            import torch
            from liquid_audio import LFM2AudioModel, LFM2AudioProcessor

            if not torch.cuda.is_available():
                device = "cpu"
                dtype = "float32"
                exact_blocker = "cuda_unavailable_full_model_load_skipped"
                processor_load_attempted = True
                start = time.perf_counter()
                processor = LFM2AudioProcessor.from_pretrained(model_path, device="cpu").eval()
                processor_load_time_seconds = round(time.perf_counter() - start, 3)
                processor_load_succeeded = True
                status = "load_failed"
            else:
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
                processor_load_attempted = True
                start = time.perf_counter()
                processor = LFM2AudioProcessor.from_pretrained(model_path, device="cpu").eval()
                processor_load_time_seconds = round(time.perf_counter() - start, 3)
                processor_load_succeeded = True

                full_model_load_attempted = True
                start = time.perf_counter()
                model = LFM2AudioModel.from_pretrained(model_path, dtype=torch.bfloat16, device="cuda").eval()
                full_model_load_time_seconds = round(time.perf_counter() - start, 3)
                full_model_load_succeeded = True
                load_succeeded = True
                status = "load_succeeded"
                gpu_memory = gpu_memory_snapshot(torch)
        except Exception as exc:  # pragma: no cover - depends on local GPU/model
            try:
                import torch

                gpu_memory = gpu_memory_snapshot(torch)
                if isinstance(exc, torch.cuda.OutOfMemoryError) or "out of memory" in str(exc).lower():
                    status = "oom"
            except Exception:
                pass
            exact_blocker = f"{type(exc).__name__}: {exc}"
            blocker = exact_blocker
        finally:
            try:
                del model
                del processor
            except Exception:
                pass
            gc.collect()
            try:
                import torch

                empty_cuda_cache(torch)
                if not gpu_memory:
                    gpu_memory = gpu_memory_snapshot(torch)
            except Exception:
                if not gpu_memory:
                    gpu_memory = {}
            cpu_memory["after_mb"] = cpu_memory_mb()

    result = {
        "experiment_id": "LIQUID-AUDIO-MODEL-LOAD-PROBE-001",
        "generated_at": utc_now(),
        "status": status,
        "config": rel(CONFIG_PATH),
        "model_id": config.get("model_id"),
        **active_python,
        "load_gates": gates,
        "load_gates_enabled": gates_enabled(gates),
        "model_inventory": inventory,
        "load_attempted": load_attempted,
        "load_succeeded": load_succeeded,
        "processor_load_attempted": processor_load_attempted,
        "processor_load_succeeded": processor_load_succeeded,
        "processor_load_time_seconds": processor_load_time_seconds,
        "full_model_load_attempted": full_model_load_attempted,
        "full_model_load_succeeded": full_model_load_succeeded,
        "full_model_load_time_seconds": full_model_load_time_seconds,
        "device": device,
        "dtype": dtype,
        "gpu_memory": gpu_memory,
        "cpu_memory": cpu_memory,
        "exact_blocker": "" if load_succeeded else exact_blocker,
        "blocker": "" if load_succeeded else (blocker or exact_blocker),
        "tracked_forbidden_files": tracked_forbidden_files(),
        "inference_run": False,
        "audio_files_generated": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-MODEL-LOAD-PROBE-001",
                "",
                f"- status: {status}",
                f"- load_attempted: {str(load_attempted).lower()}",
                f"- load_succeeded: {str(load_succeeded).lower()}",
                f"- processor_load_succeeded: {str(processor_load_succeeded).lower()}",
                f"- full_model_load_succeeded: {str(full_model_load_succeeded).lower()}",
                f"- exact_blocker: {result['exact_blocker'] or 'none'}",
                f"- device: {device}",
                f"- dtype: {dtype}",
                f"- processor_load_time_seconds: {processor_load_time_seconds}",
                f"- full_model_load_time_seconds: {full_model_load_time_seconds}",
                f"- gpu_memory_peak_reserved_bytes: {gpu_memory.get('max_memory_reserved_bytes', 0) if isinstance(gpu_memory, dict) else 0}",
                f"- inference_run: false",
                f"- audio_files_generated: false",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
            ]
        ),
    )
    write_model_decision(read_json(DOWNLOAD_RESULT_PATH), result)
    print(json.dumps({"status": status, "load_attempted": load_attempted, "load_succeeded": load_succeeded, "blocker": result["blocker"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
