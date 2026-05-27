#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import (  # noqa: E402
    PRIMARY_MODEL_ID,
    validate_conversation_brain_output,
)
from runtime.llm_brain.local_conversation_brain import (  # noqa: E402
    default_local_conversation_brain_config,
)


EXPERIMENT_ID = "LOCAL-QWEN-CONVERSATION-BRAIN-SMOKE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SMOKE_SCRIPT = ROOT / "scripts" / "run_local_qwen_conversation_brain_smoke_001.py"

REQUIRED_GITIGNORE_PATTERNS = {
    "local_artifacts/",
    "models/",
    "hf-cache/",
    "llm-checkpoints/",
    "*.gguf",
    "*.safetensors",
    "*.pt",
    "*.pth",
    "*.bin",
}

EXPECTED_DEFAULTS = {
    "enabled": False,
    "provider": "local_transformers",
    "model_id": "Qwen/Qwen2.5-7B-Instruct",
    "model_path": "local_artifacts/models/qwen2.5-7b-instruct",
    "cache_dir": "local_artifacts/cache/huggingface",
    "quantization_mode": "4bit",
    "device": "cuda",
}

FILES_WITH_NO_PROVIDER_CALLS = [
    ROOT / "runtime" / "llm_brain" / "local_conversation_brain.py",
    ROOT / "runtime" / "llm_brain" / "conversation_brain_schema.py",
    ROOT / "runtime" / "llm_brain" / "conversation_brain_prompts.py",
    ROOT / "runtime" / "llm_brain" / "local_transformers_runner.py",
    SMOKE_SCRIPT,
]

BLOCKED_PROVIDER_PATTERNS = {
    "openai import": re.compile(r"(^|\n)\s*(from\s+openai\b|import\s+openai\b)", re.I),
    "anthropic import": re.compile(r"(^|\n)\s*(from\s+anthropic\b|import\s+anthropic\b)", re.I),
    "elevenlabs import": re.compile(r"(^|\n)\s*(from\s+elevenlabs\b|import\s+elevenlabs\b)", re.I),
    "cartesia import": re.compile(r"(^|\n)\s*(from\s+cartesia\b|import\s+cartesia\b)", re.I),
    "requests call": re.compile(r"\brequests\.(get|post|put|patch|delete)\s*\(", re.I),
    "httpx call": re.compile(r"\bhttpx\.(get|post|put|patch|delete|Client|AsyncClient)\s*\(", re.I),
    "urllib urlopen": re.compile(r"\burllib\.request\.urlopen\s*\(", re.I),
    "email smtp": re.compile(r"\bsmtplib\b", re.I),
    "calendar api": re.compile(r"\bgoogleapiclient\b|\bgoogle\.oauth\b", re.I),
}

LIVE_RUNTIME_WIRING_PATTERNS = (
    "local_transformers_runner",
    "run_local_qwen_conversation_brain_smoke_001",
    "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT",
    "LOCAL_LLM_ENABLED",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_gitignore_patterns() -> set[str]:
    gitignore = ROOT / ".gitignore"
    if not gitignore.is_file():
        return set()
    patterns: set[str] = set()
    for raw in gitignore.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped and not stripped.startswith("#"):
            patterns.add(stripped.replace("\\", "/"))
    return patterns


def is_project_local_relative(path_text: str) -> bool:
    path = Path(path_text)
    if path.is_absolute():
        return False
    return ".." not in path.parts


def validate_static_contract(failures: list[str]) -> None:
    if not SMOKE_SCRIPT.is_file():
        failures.append(f"missing smoke script: {rel(SMOKE_SCRIPT)}")

    config = default_local_conversation_brain_config()
    for key, expected in EXPECTED_DEFAULTS.items():
        actual = getattr(config, key, None)
        if actual != expected:
            failures.append(f"default config {key} expected {expected!r}, got {actual!r}")

    model_path = getattr(config, "model_path", "")
    cache_dir = getattr(config, "cache_dir", "")
    if not is_project_local_relative(str(model_path)):
        failures.append(f"model_path must be project-local relative, got {model_path!r}")
    if not str(model_path).replace("\\", "/").startswith("local_artifacts/models/"):
        failures.append(f"model_path must live under local_artifacts/models/, got {model_path!r}")
    if not is_project_local_relative(str(cache_dir)):
        failures.append(f"cache_dir must be project-local relative, got {cache_dir!r}")
    if not str(cache_dir).replace("\\", "/").startswith("local_artifacts/cache/"):
        failures.append(f"cache_dir must live under local_artifacts/cache/, got {cache_dir!r}")

    gitignore_patterns = read_gitignore_patterns()
    missing = sorted(REQUIRED_GITIGNORE_PATTERNS - gitignore_patterns)
    if missing:
        failures.append(f".gitignore missing local model artifact pattern(s): {missing}")


def validate_no_provider_calls(failures: list[str]) -> None:
    for path in FILES_WITH_NO_PROVIDER_CALLS:
        if not path.is_file():
            failures.append(f"missing local LLM file for provider-call scan: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PROVIDER_PATTERNS.items():
            if pattern.search(text):
                failures.append(f"{rel(path)} contains blocked provider/network pattern: {label}")


def validate_no_live_runtime_wiring(failures: list[str]) -> None:
    live_dirs = [
        ROOT / "runtime" / "core",
        ROOT / "runtime" / "entrypoints",
        ROOT / "runtime" / "voice",
        ROOT / "runtime" / "providers",
    ]
    for live_dir in live_dirs:
        if not live_dir.is_dir():
            continue
        for path in live_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in LIVE_RUNTIME_WIRING_PATTERNS:
                if pattern in text:
                    failures.append(f"live runtime file references local Qwen smoke wiring: {rel(path)} -> {pattern}")


def validate_evidence(failures: list[str]) -> str:
    if not RESULT_PATH.exists() and not REPORT_PATH.exists():
        return "not_run"
    if not RESULT_PATH.is_file():
        failures.append(f"missing result evidence: {rel(RESULT_PATH)}")
        return "invalid"
    if not REPORT_PATH.is_file():
        failures.append(f"missing report evidence: {rel(REPORT_PATH)}")
    try:
        result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"result.json invalid JSON: {exc}")
        return "invalid"
    if not isinstance(result, dict):
        failures.append("result.json must be a JSON object")
        return "invalid"

    required_fields = {
        "experiment_id",
        "runner_implemented",
        "primary_model",
        "local_model_path",
        "cache_path",
        "dependencies_available",
        "model_artifact_found",
        "model_download_attempted",
        "inference_attempted",
        "model_loaded",
        "dependency_status",
        "cuda_available",
        "gpu_name",
        "quantization_mode",
        "smoke_case_count",
        "schema_valid_count",
        "verifier_pass_count",
        "failed_cases",
        "latency_metrics",
        "local_model_calls_made",
        "provider_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "wsl_required",
        "wsl_optional_for_future_training",
    }
    missing = sorted(required_fields - set(result))
    if missing:
        failures.append(f"result.json missing field(s): {missing}")
    if result.get("experiment_id") != EXPERIMENT_ID:
        failures.append(f"result.json experiment_id mismatch: {result.get('experiment_id')!r}")
    if result.get("primary_model") != PRIMARY_MODEL_ID:
        failures.append(f"primary_model must be {PRIMARY_MODEL_ID!r}")
    if result.get("runner_implemented") is not True:
        failures.append("runner_implemented must be true once evidence exists")
    for key, expected in {
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "wsl_required": False,
        "wsl_optional_for_future_training": True,
    }.items():
        if result.get(key) is not expected:
            failures.append(f"result.json {key} must be {expected!r}")
    if not result.get("inference_attempted"):
        if result.get("model_loaded") is not False:
            failures.append("model_loaded must stay false when inference_attempted is false")
        if result.get("local_model_calls_made") is not False:
            failures.append("local_model_calls_made must stay false when inference_attempted is false")
    if result.get("status") == "model_missing_download_not_allowed":
        if result.get("model_artifact_found") is not False:
            failures.append("model_missing_download_not_allowed requires model_artifact_found=false")
        if result.get("model_download_attempted") is not False:
            failures.append("model_missing_download_not_allowed requires model_download_attempted=false")

    cases = result.get("cases", [])
    if cases is None:
        cases = []
    if not isinstance(cases, list):
        failures.append("result.json cases must be a list when present")
        return "invalid"
    for index, case_result in enumerate(cases, start=1):
        if not isinstance(case_result, dict):
            failures.append(f"cases[{index}] must be an object")
            continue
        planner_output = case_result.get("planner_output")
        schema_errors = case_result.get("schema_errors", [])
        if planner_output is not None:
            if not isinstance(planner_output, dict):
                failures.append(f"cases[{index}].planner_output must be an object or null")
            else:
                actual_schema_errors = validate_conversation_brain_output(planner_output)
                if actual_schema_errors != schema_errors:
                    failures.append(
                        f"cases[{index}] schema_errors mismatch: expected {actual_schema_errors!r}, got {schema_errors!r}"
                    )

    return str(result.get("status") or "present")


def main() -> int:
    failures: list[str] = []
    validate_static_contract(failures)
    validate_no_provider_calls(failures)
    validate_no_live_runtime_wiring(failures)
    evidence_status = validate_evidence(failures)

    summary: dict[str, Any] = {
        "validator": "validate_local_qwen_conversation_brain_smoke_001",
        "status": "pass" if not failures else "fail",
        "evidence_status": evidence_status,
        "failures": failures,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
