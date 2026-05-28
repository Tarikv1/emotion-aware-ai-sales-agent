#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
ENV_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_env_config.json"
ENV_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENVIRONMENT-PROBE-001"
ENV_RESULT_PATH = ENV_OUT_DIR / "result.json"
ENV_REPORT_PATH = ENV_OUT_DIR / "report.md"
SETUP_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENV-SETUP-001" / "result.json"
SMOKE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001" / "result.json"
DECISION_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"

MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
REQUIRED_PACKAGES = {
    "liquid_audio": "liquid-audio",
    "torch": "torch",
    "torchaudio": "torchaudio",
}
OPTIONAL_PACKAGES = {
    "flash_attn": "flash-attn",
}
ALLOWED_STATUSES = {
    "not_run",
    "missing_dependencies",
    "model_missing",
    "environment_ready_no_model",
    "ready_for_download_phase",
    "blocked",
}


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


def env_flag(name: str, expected: str) -> bool:
    actual = str(os.getenv(name) or "").strip().lower()
    return actual == expected.strip().lower()


def package_report(import_name: str, distribution_name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(import_name)
    version = None
    try:
        version = importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {
        "import_name": import_name,
        "distribution_name": distribution_name,
        "module_found": spec is not None,
        "version": version,
    }


def torch_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "installed": False,
        "version": None,
        "cuda_available": False,
        "cuda_version": None,
        "device_count": 0,
        "devices": [],
        "import_error": "",
    }
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local machine
        report["import_error"] = f"{type(exc).__name__}: {exc}"
        return report

    report["installed"] = True
    report["version"] = getattr(torch, "__version__", None)
    report["cuda_available"] = bool(torch.cuda.is_available())
    report["cuda_version"] = getattr(torch.version, "cuda", None)
    if report["cuda_available"]:
        try:
            report["device_count"] = int(torch.cuda.device_count())
            for index in range(report["device_count"]):
                props = torch.cuda.get_device_properties(index)
                report["devices"].append(
                    {
                        "index": index,
                        "name": props.name,
                        "total_memory_gb": round(float(props.total_memory) / (1024**3), 2),
                    }
                )
        except Exception as exc:  # pragma: no cover - depends on local machine
            report["device_error"] = f"{type(exc).__name__}: {exc}"
    return report


def nvidia_smi_report() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "error": str(exc), "gpus": []}
    if completed.returncode != 0:
        return {"available": False, "error": completed.stderr.strip(), "gpus": []}
    gpus = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 2:
            gpus.append({"name": parts[0], "memory_total": parts[1]})
    return {"available": True, "error": "", "gpus": gpus}


def git_check_ignore(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return completed.returncode == 0


def path_report(relative_path: str, *, expected_under_local_artifacts: bool) -> dict[str, Any]:
    path = ROOT / relative_path
    normalized = relative_path.replace("\\", "/")
    model_files: list[str] = []
    if path.exists():
        model_files = [
            rel(item)
            for item in path.rglob("*")
            if item.is_file() and item.suffix.lower() in MODEL_SUFFIXES
        ][:50]
    return {
        "path": normalized,
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "under_local_artifacts": normalized.startswith("local_artifacts/"),
        "expected_under_local_artifacts": expected_under_local_artifacts,
        "git_ignored": git_check_ignore(normalized),
        "model_file_count": len(model_files),
        "model_files_sample": model_files,
    }


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        raise AssertionError(f"Missing config: {rel(CONFIG_PATH)}")
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("Liquid config must be a JSON object")
    return payload


def audio_env_report(env_config: dict[str, Any]) -> dict[str, Any]:
    expected_rel = str(env_config.get("python_executable_expected") or ".venv-audio/Scripts/python.exe")
    expected_path = (ROOT / expected_rel).resolve()
    active_path = Path(sys.executable).resolve()
    return {
        "env_config": rel(ENV_CONFIG_PATH) if ENV_CONFIG_PATH.is_file() else "",
        "env_name": env_config.get("env_name", ".venv-audio"),
        "active_python_env": str(active_path),
        "expected_audio_env": expected_rel.replace("\\", "/"),
        "expected_audio_env_absolute": str(expected_path),
        "running_inside_audio_env": active_path == expected_path,
    }


def side_effects() -> dict[str, bool]:
    return {
        "model_download_attempted": False,
        "model_downloads_performed": False,
        "model_weights_committed": False,
        "audio_files_generated": False,
        "audio_files_committed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": False,
        "ollama_generation_made": False,
        "training_performed": False,
        "live_runtime_wiring_changed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
        "sales_brain_replacement_allowed": False,
        "live_wiring_allowed": False,
    }


def decide_status(
    dependencies_missing: list[str],
    model_present: bool,
    path_failures: list[str],
    env_gates_enabled: bool,
    download_gate_enabled: bool,
) -> str:
    if path_failures:
        return "blocked"
    if dependencies_missing:
        return "missing_dependencies"
    if model_present:
        return "environment_ready_no_model"
    if env_gates_enabled and download_gate_enabled:
        return "ready_for_download_phase"
    if env_gates_enabled:
        return "model_missing"
    return "environment_ready_no_model"


def decision_from_environment(environment: dict[str, Any]) -> dict[str, Any]:
    status = str(environment.get("status") or "")
    dependency_status = environment.get("dependency_status") if isinstance(environment.get("dependency_status"), dict) else {}
    model_status = environment.get("model_status") if isinstance(environment.get("model_status"), dict) else {}
    hardware = environment.get("hardware") if isinstance(environment.get("hardware"), dict) else {}
    smoke = read_json(SMOKE_RESULT_PATH)
    setup = read_json(SETUP_RESULT_PATH)

    environment_ready = status in {"environment_ready_no_model", "ready_for_download_phase"} and not dependency_status.get("missing_required")
    model_present = bool(model_status.get("model_present"))
    cuda_available = bool((hardware.get("torch") or {}).get("cuda_available")) if isinstance(hardware.get("torch"), dict) else False
    hardware_note = "cuda_available" if cuda_available else "cuda_unavailable_or_unknown_no_source_vram_requirement"
    setup_blocker = str(setup.get("exact_blocker") or "").strip()

    if status == "missing_dependencies":
        recommendation_id = "install_plan_first"
        next_phase = "Install Liquid Audio dependencies in an isolated local audio environment, then rerun the environment probe. Do not download model weights yet."
        if setup_blocker:
            next_phase = f"Resolve Liquid Audio env setup blocker before any download phase: {setup_blocker}"
        download_recommended = False
        smoke_recommended = False
    elif environment_ready and not model_present:
        recommendation_id = "gated_download_phase_next"
        next_phase = "Proceed only to a gated download and ASR/TTS smoke phase after explicit approval. Keep artifacts under ignored local_artifacts paths."
        download_recommended = True
        smoke_recommended = False
    elif environment_ready and model_present:
        recommendation_id = "asr_tts_smoke_next"
        next_phase = "Run the gated ASR/TTS smoke script with synthetic inputs only; do not wire Liquid into live runtime."
        download_recommended = False
        smoke_recommended = True
    else:
        recommendation_id = "blocked_or_architecture_only"
        next_phase = "Keep Liquid as architecture inspiration until blockers are resolved."
        download_recommended = False
        smoke_recommended = False

    if hardware_note.startswith("cuda_unavailable") and environment_ready:
        next_phase += " Hardware remains unproven locally because CUDA is unavailable or not detected."

    return {
        "experiment_id": "LIQUID-AUDIO-FEASIBILITY-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass",
        "environment_probe_result": rel(ENV_RESULT_PATH),
        "smoke_result": rel(SMOKE_RESULT_PATH) if SMOKE_RESULT_PATH.is_file() else "",
        "environment_status": status,
        "env_setup_result": rel(SETUP_RESULT_PATH) if SETUP_RESULT_PATH.is_file() else "",
        "env_setup_status": setup.get("status", "not_available"),
        "install_success": setup.get("install_success"),
        "exact_blocker": setup_blocker,
        "environment_ready": environment_ready,
        "dependency_status": dependency_status,
        "hardware_status": {
            "cuda_available": cuda_available,
            "assessment": hardware_note,
            "explicit_vram_requirement_from_source": "unknown",
        },
        "model_present": model_present,
        "download_phase_recommended": download_recommended,
        "actual_smoke_recommended": smoke_recommended,
        "smoke_status": smoke.get("status", "not_available"),
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "next_phase_recommendation": next_phase,
        "recommendation_id": recommendation_id,
        "side_effects": side_effects(),
    }


def write_decision(environment: dict[str, Any]) -> None:
    decision = decision_from_environment(environment)
    write_json(DECISION_RESULT_PATH, decision)
    report = "\n".join(
        [
            "# LIQUID-AUDIO-FEASIBILITY-DECISION-001",
            "",
            f"- status: {decision['status']}",
            f"- environment_status: {decision['environment_status']}",
            f"- env_setup_status: {decision['env_setup_status']}",
            f"- install_success: {str(decision['install_success']).lower()}",
            f"- exact_blocker: {decision['exact_blocker'] or 'none'}",
            f"- environment_ready: {str(decision['environment_ready']).lower()}",
            f"- model_present: {str(decision['model_present']).lower()}",
            f"- download_phase_recommended: {str(decision['download_phase_recommended']).lower()}",
            f"- actual_smoke_recommended: {str(decision['actual_smoke_recommended']).lower()}",
            f"- live_wiring_allowed: {str(decision['live_wiring_allowed']).lower()}",
            f"- sales_brain_replacement_allowed: {str(decision['sales_brain_replacement_allowed']).lower()}",
            f"- recommendation_id: `{decision['recommendation_id']}`",
            "",
            "## Recommendation",
            "",
            str(decision["next_phase_recommendation"]),
        ]
    )
    write_text(DECISION_REPORT_PATH, report)


def main() -> int:
    config = load_config()
    env_config = read_json(ENV_CONFIG_PATH)
    active_env = audio_env_report(env_config)
    required = {name: package_report(name, dist) for name, dist in REQUIRED_PACKAGES.items()}
    optional = {name: package_report(name, dist) for name, dist in OPTIONAL_PACKAGES.items()}
    torch_info = torch_report()
    nvidia_info = nvidia_smi_report()

    env_gate_values = {
        name: {
            "expected": expected,
            "actual": os.getenv(name, ""),
            "enabled": env_flag(name, expected),
        }
        for name, expected in (config.get("env_gates") or {}).items()
    }
    env_gates_enabled = bool(
        env_gate_values.get("ENABLE_LOCAL_AUDIO_EXPERIMENT", {}).get("enabled")
        and env_gate_values.get("LOCAL_LIQUID_AUDIO_ENABLED", {}).get("enabled")
    )
    download_gate_enabled = bool(env_gate_values.get("LOCAL_LIQUID_ALLOW_MODEL_DOWNLOAD", {}).get("enabled"))

    local_model = path_report(str(config.get("local_model_path") or ""), expected_under_local_artifacts=True)
    cache = path_report(str(config.get("cache_path") or ""), expected_under_local_artifacts=True)
    output_audio = path_report(str(config.get("output_audio_path") or ""), expected_under_local_artifacts=True)

    path_failures = []
    for label, item in (("local_model_path", local_model), ("cache_path", cache), ("output_audio_path", output_audio)):
        if not item["under_local_artifacts"]:
            path_failures.append(f"{label} must stay under local_artifacts")
        if not item["git_ignored"]:
            path_failures.append(f"{label} must be ignored by git")

    source_urls_present = all(
        str(config.get(key) or "").startswith("https://")
        for key in ("source_repo", "model_card", "license_docs", "audio_model_docs")
    )
    if not source_urls_present:
        path_failures.append("source/license URLs are incomplete")

    missing_required = [name for name, item in required.items() if not item["module_found"]]
    model_present = bool(local_model["model_file_count"] > 0)
    status = decide_status(
        missing_required,
        model_present,
        path_failures,
        env_gates_enabled,
        download_gate_enabled,
    )
    assert status in ALLOWED_STATUSES

    result = {
        "experiment_id": "LIQUID-AUDIO-ENVIRONMENT-PROBE-001",
        "generated_at": utc_now(),
        "status": status,
        "config": rel(CONFIG_PATH),
        "env_config": rel(ENV_CONFIG_PATH) if ENV_CONFIG_PATH.is_file() else "",
        "active_python_env": active_env["active_python_env"],
        "expected_audio_env": active_env["expected_audio_env"],
        "running_inside_audio_env": active_env["running_inside_audio_env"],
        "audio_env": active_env,
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "platform": platform.platform(),
        },
        "source_urls": {
            "source_repo": config.get("source_repo"),
            "model_card": config.get("model_card"),
            "license_docs": config.get("license_docs"),
            "audio_model_docs": config.get("audio_model_docs"),
        },
        "env_gates": env_gate_values,
        "env_gates_enabled": env_gates_enabled,
        "download_gate_enabled": download_gate_enabled,
        "dependency_status": {
            "required": required,
            "optional": optional,
            "package_versions": {name: item.get("version") for name, item in required.items()},
            "liquid_audio_import_ok": bool(required["liquid_audio"]["module_found"]),
            "torchaudio_import_ok": bool(required["torchaudio"]["module_found"]),
            "missing_required": missing_required,
            "missing_optional": [name for name, item in optional.items() if not item["module_found"]],
        },
        "hardware": {
            "torch": torch_info,
            "nvidia_smi": nvidia_info,
            "explicit_vram_requirement_from_source": "unknown",
        },
        "path_status": {
            "local_model_path": local_model,
            "cache_path": cache,
            "output_audio_path": output_audio,
            "path_failures": path_failures,
        },
        "model_status": {
            "model_id": config.get("model_id"),
            "model_present": model_present,
            "model_files_present": local_model["model_file_count"],
            "model_download_attempted": False,
            "model_download_allowed_by_default": False,
        },
        "license_tracking": config.get("license_tracking"),
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }

    write_json(ENV_RESULT_PATH, result)
    report = "\n".join(
        [
            "# LIQUID-AUDIO-ENVIRONMENT-PROBE-001",
            "",
            f"- status: {status}",
            f"- active_python_env: `{active_env['active_python_env']}`",
            f"- expected_audio_env: `{active_env['expected_audio_env']}`",
            f"- running_inside_audio_env: {str(active_env['running_inside_audio_env']).lower()}",
            f"- missing_required: {', '.join(missing_required) if missing_required else 'none'}",
            f"- torch_installed: {str(torch_info.get('installed')).lower()}",
            f"- cuda_available: {str(torch_info.get('cuda_available')).lower()}",
            f"- model_present: {str(model_present).lower()}",
            f"- model_download_attempted: false",
            f"- local_model_path_ignored: {str(local_model.get('git_ignored')).lower()}",
            f"- output_audio_path_ignored: {str(output_audio.get('git_ignored')).lower()}",
            f"- live_wiring_allowed: false",
            f"- sales_brain_replacement_allowed: false",
            "",
            "## Source Links",
            "",
            f"- Liquid Audio repo: {config.get('source_repo')}",
            f"- Model card: {config.get('model_card')}",
            f"- License docs: {config.get('license_docs')}",
            f"- Audio model docs: {config.get('audio_model_docs')}",
            "",
            "## Blockers",
            "",
            json.dumps(path_failures + [f'missing dependency: {item}' for item in missing_required], indent=2),
        ]
    )
    write_text(ENV_REPORT_PATH, report)
    write_decision(result)
    print(json.dumps({"status": status, "missing_required": missing_required, "model_present": model_present}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
