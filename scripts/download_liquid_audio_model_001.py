#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_model_probe_config.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-DOWNLOAD-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
LOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "result.json"
DECISION_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_DIR / "report.md"

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


def model_inventory(model_path: Path) -> dict[str, Any]:
    files = [path for path in model_path.rglob("*") if path.is_file()] if model_path.exists() else []
    weight_files = [path for path in files if path.suffix.lower() in MODEL_SUFFIXES]
    marker_names = ["config.json", "tokenizer_config.json", "model.safetensors.index.json", "README.md"]
    markers = [rel(model_path / name) for name in marker_names if (model_path / name).is_file()]
    return {
        "model_path": rel(model_path),
        "model_path_exists": model_path.exists(),
        "model_file_count": len(files),
        "model_weight_file_count": len(weight_files),
        "total_approx_bytes": sum(path.stat().st_size for path in files),
        "weight_approx_bytes": sum(path.stat().st_size for path in weight_files),
        "marker_files": markers,
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


def source_urls_present(config: dict[str, Any]) -> bool:
    return all(
        str(config.get(key) or "").startswith("https://")
        for key in ("source_repo", "model_card", "license_docs", "audio_model_docs")
    )


def side_effects() -> dict[str, bool]:
    return {
        "audio_files_committed": False,
        "audio_files_generated": False,
        "elevenlabs_calls_made": False,
        "inference_run": False,
        "live_runtime_wiring_changed": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": False,
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


def write_model_decision(download: dict[str, Any], load: dict[str, Any]) -> None:
    download_status = str(download.get("status") or "not_available")
    load_status = str(load.get("status") or "not_available")
    download_succeeded = bool(download.get("model_download_succeeded"))
    load_succeeded = bool(load.get("load_succeeded"))
    load_attempted = bool(load.get("load_attempted"))
    download_blocker = str(download.get("exact_blocker") or download.get("blocker") or "").strip()
    load_blocker = str(load.get("exact_blocker") or load.get("blocker") or "").strip()

    if download_status == "not_run":
        recommendation_id = "run_gated_download_when_approved"
        recommendation = "Run the gated model download only when ENABLE_LOCAL_AUDIO_EXPERIMENT=1, LOCAL_LIQUID_AUDIO_ENABLED=true, and LOCAL_LIQUID_ALLOW_MODEL_DOWNLOAD=1 are intentionally set."
    elif not download_succeeded:
        recommendation_id = "fix_download_blocker"
        recommendation = f"Fix the model download blocker before load testing: {download_blocker or 'unknown blocker'}"
    elif download_succeeded and not load_attempted:
        recommendation_id = "run_gated_load_probe"
        recommendation = "Run the gated load-only probe with LOCAL_LIQUID_ALLOW_MODEL_LOAD=1 before any ASR/TTS smoke."
    elif load_status == "oom":
        recommendation_id = "oom_architecture_or_server_path"
        recommendation = "Liquid model load hit CUDA OOM; keep it as architecture inspiration or test a smaller, quantized, or server-side path."
    elif load_succeeded:
        recommendation_id = "synthetic_asr_tts_smoke_next"
        recommendation = "Next phase can run ASR/TTS smoke with synthetic or sanitized inputs only. Keep live wiring and sales-brain replacement disabled."
        gpu = load.get("gpu_memory") if isinstance(load.get("gpu_memory"), dict) else {}
        ratio = gpu.get("peak_reserved_ratio_of_total")
        if isinstance(ratio, (int, float)) and ratio >= 0.85:
            recommendation_id = "synthetic_smoke_cautious_memory"
            recommendation = "Model load succeeded but GPU memory was nearly saturated; run only narrow ASR/TTS smoke next and keep live wiring disabled."
    else:
        recommendation_id = "fix_load_blocker"
        recommendation = f"Fix the model load blocker before ASR/TTS smoke: {load_blocker or 'unknown blocker'}"

    decision = {
        "experiment_id": "LIQUID-AUDIO-MODEL-FEASIBILITY-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass",
        "download_result": rel(RESULT_PATH) if RESULT_PATH.is_file() else "",
        "load_probe_result": rel(LOAD_RESULT_PATH) if LOAD_RESULT_PATH.is_file() else "",
        "download_status": download_status,
        "download_attempted": bool(download.get("model_download_attempted")),
        "download_succeeded": download_succeeded,
        "model_present": bool((download.get("model_inventory") or {}).get("model_file_count")),
        "load_status": load_status,
        "load_attempted": load_attempted,
        "load_succeeded": load_succeeded,
        "load_blocker": load_blocker,
        "gpu_memory": load.get("gpu_memory", {}),
        "recommendation_id": recommendation_id,
        "next_phase_recommendation": recommendation,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    write_json(DECISION_RESULT_PATH, decision)
    write_text(
        DECISION_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-MODEL-FEASIBILITY-DECISION-001",
                "",
                f"- status: {decision['status']}",
                f"- download_status: {download_status}",
                f"- download_attempted: {str(decision['download_attempted']).lower()}",
                f"- download_succeeded: {str(download_succeeded).lower()}",
                f"- model_present: {str(decision['model_present']).lower()}",
                f"- load_status: {load_status}",
                f"- load_attempted: {str(load_attempted).lower()}",
                f"- load_succeeded: {str(load_succeeded).lower()}",
                f"- load_blocker: {load_blocker or 'none'}",
                f"- recommendation_id: `{recommendation_id}`",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "## Recommendation",
                "",
                recommendation,
            ]
        ),
    )


def main() -> int:
    config = read_json(CONFIG_PATH)
    if not config:
        raise AssertionError(f"Missing config: {rel(CONFIG_PATH)}")

    model_path = ROOT / str(config.get("local_model_path") or "")
    cache_path = ROOT / str(config.get("cache_path") or "")
    output_audio_path = ROOT / str(config.get("output_audio_path") or "")
    gates = env_gate_report(config.get("download_env_required") if isinstance(config.get("download_env_required"), dict) else {})
    active_python = active_python_report(config)
    path_failures: list[str] = []
    for label, path in (("local_model_path", model_path), ("cache_path", cache_path), ("output_audio_path", output_audio_path)):
        relative = rel(path)
        if not relative.startswith("local_artifacts/"):
            path_failures.append(f"{label} must stay under local_artifacts")
        if not git_check_ignore(relative):
            path_failures.append(f"{label} must be git ignored")

    blocker = ""
    model_download_attempted = False
    model_download_succeeded = False
    status = "not_run"

    if not active_python["running_inside_audio_env"]:
        status = "blocked"
        blocker = "download script must run with .venv-audio/Scripts/python.exe"
    elif path_failures:
        status = "blocked"
        blocker = "; ".join(path_failures)
    elif not gates_enabled(gates):
        status = "not_run"
        blocker = "download env gates are disabled"
    else:
        status = "download_failed"
        model_download_attempted = True
        cache_path.mkdir(parents=True, exist_ok=True)
        model_path.mkdir(parents=True, exist_ok=True)
        os.environ["HF_HOME"] = str(cache_path)
        os.environ["HF_HUB_CACHE"] = str(cache_path / "hub")
        os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_path / "hub")
        try:
            from huggingface_hub import snapshot_download

            snapshot_download(
                str(config.get("model_id")),
                cache_dir=cache_path,
                local_dir=model_path,
                token=False,
                max_workers=4,
            )
            model_download_succeeded = True
            status = "download_succeeded"
        except Exception as exc:  # pragma: no cover - depends on network/HF
            blocker = f"{type(exc).__name__}: {exc}"

    inventory = model_inventory(model_path)
    if not model_download_succeeded and inventory["model_file_count"] > 0 and model_download_attempted:
        blocker = blocker or "download did not report success but model files are present"

    result = {
        "experiment_id": "LIQUID-AUDIO-MODEL-DOWNLOAD-001",
        "generated_at": utc_now(),
        "status": status,
        "config": rel(CONFIG_PATH),
        "model_id": config.get("model_id"),
        **active_python,
        "download_gates": gates,
        "download_gates_enabled": gates_enabled(gates),
        "source_urls_present": source_urls_present(config),
        "source_urls": {
            "source_repo": config.get("source_repo"),
            "model_card": config.get("model_card"),
            "license_docs": config.get("license_docs"),
            "audio_model_docs": config.get("audio_model_docs"),
        },
        "path_status": {
            "local_model_path": rel(model_path),
            "cache_path": rel(cache_path),
            "output_audio_path": rel(output_audio_path),
            "local_model_path_git_ignored": git_check_ignore(rel(model_path)),
            "cache_path_git_ignored": git_check_ignore(rel(cache_path)),
            "output_audio_path_git_ignored": git_check_ignore(rel(output_audio_path)),
            "path_failures": path_failures,
        },
        "model_download_attempted": model_download_attempted,
        "model_download_succeeded": model_download_succeeded,
        "exact_blocker": blocker if not model_download_succeeded else "",
        "blocker": blocker,
        "model_inventory": inventory,
        "tracked_forbidden_files": tracked_forbidden_files(),
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": {
            **side_effects(),
            "model_download_attempted": model_download_attempted,
            "model_downloads_performed": model_download_succeeded,
        },
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-MODEL-DOWNLOAD-001",
                "",
                f"- status: {status}",
                f"- model_id: {config.get('model_id')}",
                f"- download_attempted: {str(model_download_attempted).lower()}",
                f"- download_succeeded: {str(model_download_succeeded).lower()}",
                f"- exact_blocker: {result['exact_blocker'] or 'none'}",
                f"- model_file_count: {inventory['model_file_count']}",
                f"- model_weight_file_count: {inventory['model_weight_file_count']}",
                f"- total_approx_bytes: {inventory['total_approx_bytes']}",
                f"- local_model_path: `{inventory['model_path']}`",
                f"- model_download_attempted: {str(model_download_attempted).lower()}",
                f"- inference_run: false",
                f"- audio_files_generated: false",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "## Source Links",
                "",
                f"- Liquid Audio repo: {config.get('source_repo')}",
                f"- Model card: {config.get('model_card')}",
                f"- License docs: {config.get('license_docs')}",
                f"- Audio model docs: {config.get('audio_model_docs')}",
            ]
        ),
    )
    write_model_decision(result, read_json(LOAD_RESULT_PATH))
    print(json.dumps({"status": status, "download_attempted": model_download_attempted, "download_succeeded": model_download_succeeded, "model_file_count": inventory["model_file_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
