#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    OLLAMA_MODEL,
    OLLAMA_PULL_ENV_VAR,
    audit_side_effects,
    command_json,
    env_flag,
    env_gate_report,
    http_json,
    ollama_model_names,
    qwen_ollama_model_present,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-OLLAMA-BACKEND-PROBE-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"


def pull_model_if_allowed(model_present: bool, ollama_command_exists: bool) -> dict[str, Any]:
    if model_present:
        return {"attempted": False, "allowed": env_flag(OLLAMA_PULL_ENV_VAR), "reason": "model_already_present"}
    if not env_flag(OLLAMA_PULL_ENV_VAR):
        return {"attempted": False, "allowed": False, "reason": f"{OLLAMA_PULL_ENV_VAR}=1 is required before ollama pull"}
    if not ollama_command_exists:
        return {"attempted": False, "allowed": True, "reason": "ollama command not found"}
    try:
        completed = subprocess.run(
            ["ollama", "pull", OLLAMA_MODEL],
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"attempted": True, "allowed": True, "returncode": None, "stdout": "", "stderr": str(exc)}
    return {
        "attempted": True,
        "allowed": True,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout.strip()[-2000:],
        "stderr_tail": completed.stderr.strip()[-2000:],
    }


def build_probe() -> dict[str, Any]:
    command_path = shutil.which("ollama")
    command_exists = bool(command_path)
    version = command_json(["ollama", "--version"], timeout_s=20) if command_exists else {"available": False, "stdout": "", "stderr": "ollama command not found"}
    tags_payload, tags_error = http_json("/api/tags", timeout_s=5.0)
    api_reachable = tags_payload is not None
    model_present, resolved_model, parameter_size = qwen_ollama_model_present(tags_payload)
    pull = pull_model_if_allowed(model_present, command_exists)
    if pull.get("attempted") is True:
        tags_payload, tags_error = http_json("/api/tags", timeout_s=10.0)
        api_reachable = tags_payload is not None
        model_present, resolved_model, parameter_size = qwen_ollama_model_present(tags_payload)

    status = "pass" if command_exists or api_reachable else "not_available"
    blocker = ""
    if not command_exists and not api_reachable:
        blocker = "ollama command not found and localhost API is not reachable"
    elif not api_reachable:
        blocker = f"localhost Ollama API is not reachable: {tags_error}"
    elif not model_present:
        blocker = f"{OLLAMA_MODEL} is not present locally and pull is disabled unless {OLLAMA_PULL_ENV_VAR}=1"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": status,
        "backend_id": "ollama_local",
        "localhost_api_base": "http://localhost:11434",
        "localhost_only": True,
        "provider_api": False,
        "env_gates": env_gate_report(),
        "ollama_command_exists": command_exists,
        "ollama_command_path": command_path or "",
        "ollama_version": version,
        "ollama_api_reachable": api_reachable,
        "ollama_api_error": tags_error,
        "ollama_localhost_calls_made": api_reachable,
        "local_model_names": ollama_model_names(tags_payload),
        "qwen_model_present": model_present,
        "qwen_resolved_model": resolved_model,
        "qwen_resolved_parameter_size": parameter_size,
        "ollama_pull_attempted": pull.get("attempted") is True,
        "ollama_pull_allowed": pull.get("allowed") is True,
        "ollama_pull_result": pull,
        "benchmark_blocker": blocker,
        "local_model_calls_made": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "training_rerun": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "side_effects": audit_side_effects(
            local_model_calls_made=False,
            ollama_localhost_calls_made=api_reachable,
            ollama_pull_attempted=pull.get("attempted") is True,
        ),
    }


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- ollama_command_exists: {str(result['ollama_command_exists']).lower()}",
        f"- ollama_api_reachable: {str(result['ollama_api_reachable']).lower()}",
        f"- qwen_model_present: {str(result['qwen_model_present']).lower()}",
        f"- qwen_resolved_model: {result['qwen_resolved_model'] or 'none'}",
        f"- ollama_pull_attempted: {str(result['ollama_pull_attempted']).lower()}",
        f"- benchmark_blocker: {result['benchmark_blocker'] or 'none'}",
        f"- provider_calls_made: {str(result['provider_calls_made']).lower()}",
        f"- openai_api_calls_made: {str(result['openai_api_calls_made']).lower()}",
        f"- live_tts_calls_made: {str(result['live_tts_calls_made']).lower()}",
        "",
        "## Local Models",
        "",
        json.dumps(result["local_model_names"], indent=2, ensure_ascii=False),
        "",
        "## Env Gates",
        "",
        json.dumps(result["env_gates"], indent=2, ensure_ascii=False),
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def main() -> int:
    result = build_probe()
    write_json(RESULT_PATH, result)
    write_report(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "ollama_command_exists": result["ollama_command_exists"],
                "ollama_api_reachable": result["ollama_api_reachable"],
                "qwen_model_present": result["qwen_model_present"],
                "ollama_pull_attempted": result["ollama_pull_attempted"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
