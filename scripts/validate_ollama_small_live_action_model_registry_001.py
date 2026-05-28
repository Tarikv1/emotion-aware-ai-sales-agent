#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    ROOT,
    audit_side_effects,
    changed_files,
    pruned_weight_files,
    read_json,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


REGISTRY_PATH = "runtime/llm_brain/training/ollama_small_live_action_model_registry.json"
VALIDATION_ID = "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-REGISTRY-VALIDATION-001"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PRIMARY_MODELS = {
    "qwen2.5:0.5b",
    "qwen2.5:1.5b",
    "gemma3:270m",
    "gemma3:1b",
    "smollm2:1.7b",
    "llama3.2:1b",
}


def false_flag(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def main() -> int:
    failures: list[str] = []
    registry_file = ROOT / REGISTRY_PATH
    if not registry_file.is_file():
        failures.append(f"missing registry: {REGISTRY_PATH}")
    registry = read_json(registry_file)
    if registry.get("registry_id") != "ollama-small-live-action-model-registry-001":
        failures.append("registry_id is wrong")
    false_flag(registry, "provider_api", failures, "registry")
    false_flag(registry, "live_wiring_allowed", failures, "registry")
    false_flag(registry, "adapter_live_ready", failures, "registry")
    if registry.get("pull_allowed_by_env_only") is not True:
        failures.append("registry.pull_allowed_by_env_only must be true")
    models = registry.get("models") if isinstance(registry.get("models"), list) else []
    by_name = {item.get("model_name"): item for item in models if isinstance(item, dict)}
    missing = sorted(PRIMARY_MODELS - set(by_name))
    if missing:
        failures.append(f"registry missing primary models: {missing}")
    for name in sorted(PRIMARY_MODELS):
        item = by_name.get(name) or {}
        if item.get("role") != "primary_benchmark_candidate":
            failures.append(f"{name}.role must be primary_benchmark_candidate")
        if item.get("benchmark_enabled") is not True:
            failures.append(f"{name}.benchmark_enabled must be true")
        if item.get("pull_allowed_by_env_only") is not True:
            failures.append(f"{name}.pull_allowed_by_env_only must be true")
        if item.get("live_wiring_allowed") is not False:
            failures.append(f"{name}.live_wiring_allowed must be false")
        if not str(item.get("expected_size_from_user_ollama_list") or "").strip():
            failures.append(f"{name}.expected_size_from_user_ollama_list missing")
        if not str(item.get("notes") or "").strip():
            failures.append(f"{name}.notes missing")
    baseline = by_name.get("qwen2.5:7b") or {}
    if baseline.get("role") != "baseline_reference_only":
        failures.append("qwen2.5:7b must be baseline_reference_only")
    if baseline.get("already_benchmarked") is not True:
        failures.append("qwen2.5:7b.already_benchmarked must be true")
    if baseline.get("do_not_rerun_by_default") is not True:
        failures.append("qwen2.5:7b.do_not_rerun_by_default must be true")
    if baseline.get("benchmark_enabled") is not False:
        failures.append("qwen2.5:7b.benchmark_enabled must be false")

    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    pruned = pruned_weight_files()
    if pruned:
        failures.append(f"pruned weights exist but this phase must not create them: {pruned[:20]}")
    files = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files)
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed")
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": VALIDATION_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "registry": REGISTRY_PATH,
        "primary_model_count": len(PRIMARY_MODELS),
        "changed_files": files,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                f"# {VALIDATION_ID}",
                "",
                f"- status: {result['status']}",
                f"- failure_count: {len(failures)}",
                "",
                "## Failures",
                "",
                json.dumps(failures, indent=2, ensure_ascii=False),
            ]
        ),
    )
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
