#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_env_config.json"
FEASIBILITY_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENV-SETUP-001"
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


def command_display(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def tail(text: str, limit: int = 8000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_command(command: list[str], *, timeout: int = 1800) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command_display(command),
            "returncode": completed.returncode,
            "stdout_tail": tail(completed.stdout.strip()),
            "stderr_tail": tail(completed.stderr.strip()),
            "success": completed.returncode == 0,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "command": command_display(command),
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": f"{type(exc).__name__}: {exc}",
            "success": False,
        }


def package_report(python_executable: Path, import_name: str, distribution_name: str) -> dict[str, Any]:
    script = (
        "import importlib.metadata, importlib.util, json\n"
        f"import_name={import_name!r}\n"
        f"dist_name={distribution_name!r}\n"
        "spec=importlib.util.find_spec(import_name)\n"
        "try:\n"
        "    version=importlib.metadata.version(dist_name)\n"
        "except importlib.metadata.PackageNotFoundError:\n"
        "    version=None\n"
        "print(json.dumps({'import_name': import_name, 'distribution_name': dist_name, 'module_found': spec is not None, 'version': version}))\n"
    )
    completed = subprocess.run(
        [str(python_executable), "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "import_name": import_name,
            "distribution_name": distribution_name,
            "module_found": False,
            "version": None,
            "error": completed.stderr.strip(),
        }
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def torch_report(python_executable: Path) -> dict[str, Any]:
    script = (
        "import json\n"
        "report={'installed': False, 'version': None, 'cuda_available': False, 'cuda_version': None, 'device_count': 0, 'devices': [], 'import_error': ''}\n"
        "try:\n"
        "    import torch\n"
        "    report['installed']=True\n"
        "    report['version']=getattr(torch, '__version__', None)\n"
        "    report['cuda_available']=bool(torch.cuda.is_available())\n"
        "    report['cuda_version']=getattr(torch.version, 'cuda', None)\n"
        "    if report['cuda_available']:\n"
        "        report['device_count']=int(torch.cuda.device_count())\n"
        "        for index in range(report['device_count']):\n"
        "            props=torch.cuda.get_device_properties(index)\n"
        "            report['devices'].append({'index': index, 'name': props.name, 'total_memory_gb': round(float(props.total_memory)/(1024**3), 2)})\n"
        "except Exception as exc:\n"
        "    report['import_error']=type(exc).__name__ + ': ' + str(exc)\n"
        "print(json.dumps(report))\n"
    )
    completed = subprocess.run(
        [str(python_executable), "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "installed": False,
            "version": None,
            "cuda_available": False,
            "cuda_version": None,
            "device_count": 0,
            "devices": [],
            "import_error": completed.stderr.strip(),
        }
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def nvidia_smi_report() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
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


def choose_venv_creator(env_dir: Path) -> tuple[list[str], str]:
    py_launcher = shutil.which("py")
    if py_launcher:
        probe = subprocess.run(
            [py_launcher, "-3.11", "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if probe.returncode == 0:
            return [py_launcher, "-3.11", "-m", "venv", str(env_dir)], "py -3.11"
    return [sys.executable, "-m", "venv", str(env_dir)], "current python"


def find_forbidden_tracked_files() -> dict[str, list[str]]:
    tracked = git_lines(["ls-files"])
    return {
        "weights_or_local_artifacts": [
            path
            for path in tracked
            if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)
        ],
        "audio_files": [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)],
        "venv_audio_files": [path for path in tracked if path.startswith(".venv-audio/")],
    }


def main() -> int:
    config = read_json(CONFIG_PATH)
    feasibility_config = read_json(FEASIBILITY_CONFIG_PATH)
    if not config:
        raise AssertionError(f"Missing config: {rel(CONFIG_PATH)}")

    env_name = str(config.get("env_name") or ".venv-audio")
    env_dir = ROOT / env_name
    expected_python = ROOT / str(config.get("python_executable_expected") or ".venv-audio/Scripts/python.exe")
    setup_attempted = True
    venv_existed_before = expected_python.is_file()
    venv_created = False
    exact_blocker = ""
    install_steps: list[dict[str, Any]] = []

    venv_command_source = ""
    if not expected_python.is_file():
        create_command, venv_command_source = choose_venv_creator(env_dir)
        create_result = run_command(create_command, timeout=300)
        install_steps.append({"step": "create_venv", **create_result})
        venv_created = bool(create_result.get("success") and expected_python.is_file())
        if not expected_python.is_file():
            exact_blocker = "failed_to_create_venv: " + str(create_result.get("stderr_tail") or create_result.get("stdout_tail") or create_result.get("returncode"))
    else:
        venv_command_source = "existing .venv-audio"

    pip_version_result: dict[str, Any] = {}
    ensurepip_result: dict[str, Any] = {}
    pip_upgrade_result: dict[str, Any] = {}
    torch_result: dict[str, Any] = {}
    liquid_result: dict[str, Any] = {}
    torch_install_attempted = False
    torchaudio_install_attempted = False
    liquid_audio_install_attempted = False

    if expected_python.is_file():
        pip_version_result = run_command([str(expected_python), "-m", "pip", "--version"], timeout=60)
        install_steps.append({"step": "pip_version_before_or_after", **pip_version_result})
        if not pip_version_result.get("success"):
            ensurepip_result = run_command([str(expected_python), "-m", "ensurepip", "--upgrade", "--default-pip"], timeout=300)
            install_steps.append({"step": "ensurepip_repair", **ensurepip_result})
            pip_version_result = run_command([str(expected_python), "-m", "pip", "--version"], timeout=60)
            install_steps.append({"step": "pip_version_after_ensurepip", **pip_version_result})
        if not pip_version_result.get("success") and not exact_blocker:
            exact_blocker = "pip_unavailable_after_ensurepip: " + str(pip_version_result.get("stderr_tail") or pip_version_result.get("stdout_tail"))
        if not exact_blocker:
            pip_upgrade_result = run_command([str(expected_python), "-m", "pip", "install", "--upgrade", "pip"], timeout=600)
            install_steps.append({"step": "pip_upgrade", **pip_upgrade_result})
            if not pip_upgrade_result.get("success") and not exact_blocker:
                exact_blocker = "pip_upgrade_failed: " + str(pip_upgrade_result.get("stderr_tail") or pip_upgrade_result.get("stdout_tail"))

    if expected_python.is_file() and not exact_blocker:
        pytorch_install = config.get("pytorch_install") if isinstance(config.get("pytorch_install"), dict) else {}
        index_url = str(pytorch_install.get("index_url") or "https://download.pytorch.org/whl/cu128")
        torch_command = [str(expected_python), "-m", "pip", "install", "torch", "torchaudio", "--index-url", index_url]
        torch_install_attempted = True
        torchaudio_install_attempted = True
        torch_result = run_command(torch_command, timeout=2400)
        install_steps.append({"step": "install_torch_torchaudio", **torch_result})
        if not torch_result.get("success"):
            exact_blocker = "torch_torchaudio_install_failed: " + str(torch_result.get("stderr_tail") or torch_result.get("stdout_tail"))

    if expected_python.is_file() and not exact_blocker:
        liquid_audio_install_attempted = True
        liquid_result = run_command([str(expected_python), "-m", "pip", "install", "liquid-audio"], timeout=1800)
        install_steps.append({"step": "install_liquid_audio", **liquid_result})
        if not liquid_result.get("success"):
            exact_blocker = "liquid_audio_install_failed: " + str(liquid_result.get("stderr_tail") or liquid_result.get("stdout_tail"))

    package_versions: dict[str, Any] = {}
    torch_info: dict[str, Any] = {
        "installed": False,
        "version": None,
        "cuda_available": False,
        "cuda_version": None,
        "device_count": 0,
        "devices": [],
        "import_error": "venv python missing",
    }
    flash_attn = {"module_found": False, "version": None}
    if expected_python.is_file():
        package_versions = {
            "torch": package_report(expected_python, "torch", "torch"),
            "torchaudio": package_report(expected_python, "torchaudio", "torchaudio"),
            "liquid_audio": package_report(expected_python, "liquid_audio", "liquid-audio"),
        }
        flash_attn = package_report(expected_python, "flash_attn", "flash-attn")
        torch_info = torch_report(expected_python)

    required_ok = all(
        bool((package_versions.get(name) or {}).get("module_found"))
        for name in ("torch", "torchaudio", "liquid_audio")
    )
    install_success = bool(required_ok and not exact_blocker)
    source_urls_present = all(
        str(feasibility_config.get(key) or config.get("liquid_audio_install", {}).get(key) or "").startswith("https://")
        for key in ("source_repo", "model_card", "license_docs", "audio_model_docs")
    )
    if not source_urls_present and not exact_blocker:
        exact_blocker = "source_or_license_urls_missing"
        install_success = False

    forbidden = find_forbidden_tracked_files()
    gpu_info = nvidia_smi_report()
    result = {
        "experiment_id": "LIQUID-AUDIO-ENV-SETUP-001",
        "generated_at": utc_now(),
        "status": "pass" if install_success else "blocked",
        "config": rel(CONFIG_PATH),
        "feasibility_config": rel(FEASIBILITY_CONFIG_PATH),
        "setup_attempted": setup_attempted,
        "venv_existed_before": venv_existed_before,
        "venv_created": venv_created,
        "venv_command_source": venv_command_source,
        "python_executable": str(expected_python),
        "python_executable_exists": expected_python.is_file(),
        "python_version": run_command([str(expected_python), "--version"], timeout=30) if expected_python.is_file() else {},
        "system_python_version": sys.version,
        "platform": platform.platform(),
        "pip_version": pip_version_result.get("stdout_tail", ""),
        "ensurepip_repair_attempted": bool(ensurepip_result),
        "pip_upgrade_attempted": bool(pip_upgrade_result),
        "torch_install_attempted": torch_install_attempted,
        "torchaudio_install_attempted": torchaudio_install_attempted,
        "liquid_audio_install_attempted": liquid_audio_install_attempted,
        "install_success": install_success,
        "exact_blocker": "" if install_success else exact_blocker,
        "install_steps": install_steps,
        "package_versions": package_versions,
        "torch_cuda_available": bool(torch_info.get("cuda_available")),
        "torch_cuda_version": torch_info.get("cuda_version"),
        "torch": torch_info,
        "gpu": gpu_info,
        "gpu_name": ", ".join(gpu.get("name", "") for gpu in gpu_info.get("gpus", [])),
        "vram_total": ", ".join(gpu.get("memory_total", "") for gpu in gpu_info.get("gpus", [])),
        "flash_attn_installed": bool(flash_attn.get("module_found")),
        "flash_attn_install_attempted": False,
        "demo_extra_install_attempted": False,
        "model_download_attempted": False,
        "model_downloads_performed": False,
        "model_weights_committed": False,
        "audio_files_generated": False,
        "audio_files_committed": False,
        "tracked_forbidden_files": forbidden,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "inference_run": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-ENV-SETUP-001",
                "",
                f"- status: {result['status']}",
                f"- venv_created: {str(venv_created).lower()}",
                f"- python_executable: `{expected_python}`",
                f"- install_success: {str(install_success).lower()}",
                f"- exact_blocker: {result['exact_blocker'] or 'none'}",
                f"- torch_install_attempted: {str(torch_install_attempted).lower()}",
                f"- torchaudio_install_attempted: {str(torchaudio_install_attempted).lower()}",
                f"- liquid_audio_install_attempted: {str(liquid_audio_install_attempted).lower()}",
                f"- torch_cuda_available: {str(result['torch_cuda_available']).lower()}",
                f"- torch_cuda_version: {result['torch_cuda_version'] or 'unknown'}",
                f"- gpu_name: {result['gpu_name'] or 'unknown'}",
                f"- vram_total: {result['vram_total'] or 'unknown'}",
                f"- flash_attn_installed: {str(result['flash_attn_installed']).lower()}",
                f"- model_download_attempted: false",
                f"- provider_calls_made: false",
                f"- runtime_behavior_changed: false",
                f"- response_text_changed: false",
                "",
                "## Package Versions",
                "",
                json.dumps(package_versions, indent=2, sort_keys=True),
                "",
                "## Source Links",
                "",
                "- Liquid Audio repo: https://github.com/Liquid4All/liquid-audio",
                "- LFM2.5-Audio model card: https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B",
                "- Liquid license docs: https://docs.liquid.ai/lfm/help/model-license",
                "- Liquid audio model docs: https://docs.liquid.ai/lfm/models/audio-models",
                "- PyTorch local install selector: https://pytorch.org/get-started/locally/",
            ]
        ),
    )
    print(json.dumps({"status": result["status"], "install_success": install_success, "exact_blocker": result["exact_blocker"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
