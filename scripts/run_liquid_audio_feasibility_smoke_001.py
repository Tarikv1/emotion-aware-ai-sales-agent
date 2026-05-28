#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
ENV_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_env_config.json"
ENV_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENVIRONMENT-PROBE-001" / "result.json"
SETUP_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENV-SETUP-001" / "result.json"
MODEL_LOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DECISION_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-DECISION-001"
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"

MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")


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
    return str(os.getenv(name) or "").strip().lower() == expected.strip().lower()


def model_files(model_path: Path) -> list[str]:
    if not model_path.exists():
        return []
    return [
        rel(path)
        for path in model_path.rglob("*")
        if path.is_file() and path.suffix.lower() in MODEL_SUFFIXES
    ][:50]


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


def write_decision(smoke: dict[str, Any]) -> None:
    environment = read_json(ENV_RESULT_PATH)
    setup = read_json(SETUP_RESULT_PATH)
    model_load = read_json(MODEL_LOAD_RESULT_PATH)
    dependency_status = environment.get("dependency_status") if isinstance(environment.get("dependency_status"), dict) else {}
    model_status = environment.get("model_status") if isinstance(environment.get("model_status"), dict) else {}
    hardware = environment.get("hardware") if isinstance(environment.get("hardware"), dict) else {}
    torch_info = hardware.get("torch") if isinstance(hardware.get("torch"), dict) else {}
    environment_status = str(environment.get("status") or "not_available")
    model_present = bool(model_status.get("model_present") or smoke.get("model_present"))
    model_load_succeeded = bool(model_load.get("load_succeeded"))
    environment_ready = environment_status in {"environment_ready_no_model", "ready_for_download_phase", "model_present_ready_for_load", "model_loaded_ready_for_smoke"} and not dependency_status.get("missing_required")
    setup_blocker = str(setup.get("exact_blocker") or "").strip()

    if environment_status == "missing_dependencies":
        recommendation_id = "install_plan_first"
        next_phase = "Install Liquid Audio dependencies in an isolated local audio environment, then rerun the environment probe. Do not download model weights yet."
        if setup_blocker:
            next_phase = f"Resolve Liquid Audio env setup blocker before any download phase: {setup_blocker}"
        download_recommended = False
        smoke_recommended = False
    elif environment_ready and not model_present:
        recommendation_id = "gated_download_phase_next"
        next_phase = "Proceed only to a gated model download and ASR/TTS smoke phase after explicit approval. Keep artifacts under ignored local_artifacts paths."
        download_recommended = True
        smoke_recommended = False
    elif environment_ready and model_present and not model_load_succeeded:
        recommendation_id = "gated_load_probe_next"
        next_phase = "Model files are present; run the gated load-only probe before any ASR/TTS smoke."
        download_recommended = False
        smoke_recommended = False
    elif environment_ready and model_present and model_load_succeeded:
        recommendation_id = "asr_tts_smoke_next"
        next_phase = "Run the gated ASR/TTS smoke with synthetic inputs only; keep Liquid out of live runtime and out of sales-brain decisions."
        download_recommended = False
        smoke_recommended = True
    else:
        recommendation_id = "blocked_or_architecture_only"
        next_phase = "Keep Liquid as architecture inspiration until blockers are resolved."
        download_recommended = False
        smoke_recommended = False

    decision = {
        "experiment_id": "LIQUID-AUDIO-FEASIBILITY-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass",
        "environment_probe_result": rel(ENV_RESULT_PATH) if ENV_RESULT_PATH.is_file() else "",
        "env_setup_result": rel(SETUP_RESULT_PATH) if SETUP_RESULT_PATH.is_file() else "",
        "env_setup_status": setup.get("status", "not_available"),
        "install_success": setup.get("install_success"),
        "exact_blocker": setup_blocker,
        "model_load_result": rel(MODEL_LOAD_RESULT_PATH) if MODEL_LOAD_RESULT_PATH.is_file() else "",
        "model_load_succeeded": model_load_succeeded,
        "smoke_result": rel(RESULT_PATH),
        "environment_status": environment_status,
        "environment_ready": environment_ready,
        "dependency_status": dependency_status,
        "hardware_status": {
            "cuda_available": bool(torch_info.get("cuda_available")),
            "assessment": "cuda_available" if torch_info.get("cuda_available") else "cuda_unavailable_or_unknown_no_source_vram_requirement",
            "explicit_vram_requirement_from_source": "unknown",
        },
        "model_present": model_present,
        "download_phase_recommended": download_recommended,
        "actual_smoke_recommended": smoke_recommended,
        "smoke_status": smoke.get("status"),
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "next_phase_recommendation": next_phase,
        "recommendation_id": recommendation_id,
        "side_effects": side_effects(),
    }
    write_json(DECISION_RESULT_PATH, decision)
    write_text(
        DECISION_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-FEASIBILITY-DECISION-001",
                "",
                f"- status: {decision['status']}",
                f"- environment_status: {decision['environment_status']}",
                f"- env_setup_status: {decision['env_setup_status']}",
                f"- install_success: {str(decision['install_success']).lower()}",
                f"- exact_blocker: {decision['exact_blocker'] or 'none'}",
                f"- model_present: {str(decision['model_present']).lower()}",
                f"- download_phase_recommended: {str(decision['download_phase_recommended']).lower()}",
                f"- actual_smoke_recommended: {str(decision['actual_smoke_recommended']).lower()}",
                f"- smoke_status: {decision['smoke_status']}",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                f"- recommendation_id: `{decision['recommendation_id']}`",
                "",
                "## Recommendation",
                "",
                str(decision["next_phase_recommendation"]),
            ]
        ),
    )


def main() -> int:
    config = read_json(CONFIG_PATH)
    if not config:
        raise AssertionError(f"Missing config: {rel(CONFIG_PATH)}")
    env_config = read_json(ENV_CONFIG_PATH)

    gates = {
        name: {
            "expected": expected,
            "actual": os.getenv(name, ""),
            "enabled": env_flag(name, expected),
        }
        for name, expected in (config.get("env_gates") or {}).items()
    }
    local_audio_enabled = bool(
        gates.get("ENABLE_LOCAL_AUDIO_EXPERIMENT", {}).get("enabled")
        and gates.get("LOCAL_LIQUID_AUDIO_ENABLED", {}).get("enabled")
    )
    download_allowed = bool(gates.get("LOCAL_LIQUID_ALLOW_MODEL_DOWNLOAD", {}).get("enabled"))
    inference_allowed = bool(env_flag("LOCAL_LIQUID_ALLOW_INFERENCE", "1"))
    model_path = ROOT / str(config.get("local_model_path") or "")
    present_files = model_files(model_path)
    model_present = bool(present_files)

    asr_phrases = (config.get("safe_test_inputs") or {}).get("asr_phrases", [])
    tts_utterances = (config.get("safe_test_inputs") or {}).get("tts_utterances", [])

    if not local_audio_enabled:
        status = "not_run"
        blocker = "ENABLE_LOCAL_AUDIO_EXPERIMENT=1 and LOCAL_LIQUID_AUDIO_ENABLED=true are required for smoke execution."
    elif not model_present and not download_allowed:
        status = "model_missing"
        blocker = "Model files are missing and LOCAL_LIQUID_ALLOW_MODEL_DOWNLOAD=1 is not set."
    elif not model_present and download_allowed:
        status = "blocked"
        blocker = "Download gate is enabled, but this Phase 4I1 skeleton does not perform downloads automatically."
    elif model_present and not inference_allowed:
        status = "ready_for_smoke_next"
        blocker = "Model files are present, but LOCAL_LIQUID_ALLOW_INFERENCE=1 is not set; ASR/TTS/S2S smoke remains deferred."
    else:
        status = "blocked"
        blocker = "Model appears present, but Phase 4I1 does not load Liquid or run inference by default."

    result = {
        "experiment_id": "LIQUID-AUDIO-FEASIBILITY-SMOKE-001",
        "generated_at": utc_now(),
        "status": status,
        "blocker": blocker,
        "config": rel(CONFIG_PATH),
        "env_config": rel(ENV_CONFIG_PATH) if ENV_CONFIG_PATH.is_file() else "",
        "active_python_env": sys.executable,
        "expected_audio_env": str(env_config.get("python_executable_expected") or ".venv-audio/Scripts/python.exe").replace("\\", "/"),
        "env_gates": gates,
        "model_id": config.get("model_id"),
        "model_present": model_present,
        "model_files_sample": present_files,
        "model_download_attempted": False,
        "smoke_run": False,
        "asr_smoke": {
            "status": "not_run",
            "synthetic_phrases": asr_phrases,
            "raw_private_audio_used": False,
        },
        "tts_smoke": {
            "status": "not_run",
            "synthetic_utterances": tts_utterances,
            "audio_files_generated": False,
        },
        "interleaved_s2s_smoke": {
            "status": "not_run",
            "reason": "Optional future mode only after model/runtime support and gates are verified.",
        },
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-FEASIBILITY-SMOKE-001",
                "",
                f"- status: {status}",
                f"- blocker: {blocker}",
                f"- model_present: {str(model_present).lower()}",
                f"- model_download_attempted: false",
                f"- smoke_run: false",
                f"- asr_smoke_status: {result['asr_smoke']['status']}",
                f"- tts_smoke_status: {result['tts_smoke']['status']}",
                f"- interleaved_s2s_smoke_status: {result['interleaved_s2s_smoke']['status']}",
                f"- provider_calls_made: false",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "## Synthetic Test Inputs",
                "",
                "ASR phrases:",
                json.dumps(asr_phrases, indent=2),
                "",
                "TTS utterances:",
                json.dumps(tts_utterances, indent=2),
            ]
        ),
    )
    write_decision(result)
    print(json.dumps({"status": status, "blocker": blocker, "model_present": model_present}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
