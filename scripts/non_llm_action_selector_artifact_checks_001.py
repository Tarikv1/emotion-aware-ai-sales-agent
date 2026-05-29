from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIR = ROOT / "research" / "experiments" / "generated"

DATA_SOURCES_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-DATA-SOURCES-001"
DATASET_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-DATASET-001"
EVAL_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-EVAL-001"
COMPARISON_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-COMPARISON-001"
DECISION_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-DECISION-001"
SHADOW_REPLAY_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-SHADOW-REPLAY-001"
SHADOW_MODE_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-SHADOW-MODE-001"
SHADOW_SAFETY_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-SHADOW-SAFETY-AUDIT-001"
SHADOW_DECISION_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-SHADOW-DECISION-001"
RUNTIME_SHADOW_POINTS_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-POINTS-001"
RUNTIME_SHADOW_LOG_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-LOG-001"
RUNTIME_SHADOW_REPLAY_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-REPLAY-001"
RUNTIME_SHADOW_AUDIT_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-AUDIT-001"
RUNTIME_SHADOW_DECISION_DIR = GENERATED_DIR / "NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-DECISION-001"

LABELS_PATH = ROOT / "runtime" / "action_selector" / "action_selector_labels.json"
CONTRACT_PATH = ROOT / "runtime" / "action_selector" / "action_selector_contract.py"
SELECTOR_PATH = ROOT / "runtime" / "action_selector" / "non_llm_action_selector.py"
SHADOW_CONTRACT_PATH = ROOT / "runtime" / "action_selector" / "shadow_mode_contract.py"
SHADOW_EVALUATOR_PATH = ROOT / "runtime" / "action_selector" / "shadow_mode_evaluator.py"
RUNTIME_SHADOW_CONFIG_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_logging_config.json"
RUNTIME_SHADOW_LOGGER_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_logger.py"
RUNTIME_SHADOW_HOOK_PATH = ROOT / "runtime" / "action_selector" / "shadow_runtime_hook.py"

REQUESTED_SOURCE_PATHS = [
    ROOT / "scripts" / "build_non_llm_action_selector_dataset_001.py",
    ROOT / "scripts" / "train_eval_non_llm_action_selector_001.py",
    ROOT / "scripts" / "compare_non_llm_action_selector_to_small_models_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_dataset_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_eval_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_comparison_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_decision_001.py",
    ROOT / "scripts" / "build_non_llm_action_selector_shadow_replay_001.py",
    ROOT / "scripts" / "run_non_llm_action_selector_shadow_mode_001.py",
    ROOT / "scripts" / "audit_non_llm_action_selector_shadow_safety_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_shadow_replay_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_shadow_mode_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_shadow_safety_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_shadow_decision_001.py",
    ROOT / "scripts" / "run_non_llm_action_selector_runtime_shadow_replay_001.py",
    ROOT / "scripts" / "audit_non_llm_action_selector_runtime_shadow_logging_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_runtime_shadow_points_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_runtime_shadow_replay_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_runtime_shadow_audit_001.py",
    ROOT / "scripts" / "validate_non_llm_action_selector_runtime_shadow_decision_001.py",
    CONTRACT_PATH,
    SELECTOR_PATH,
    SHADOW_CONTRACT_PATH,
    SHADOW_EVALUATOR_PATH,
    RUNTIME_SHADOW_LOGGER_PATH,
    RUNTIME_SHADOW_HOOK_PATH,
]

WEIGHT_SUFFIXES = (
    ".bin",
    ".ckpt",
    ".gguf",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
)

FORBIDDEN_IMPORT_ROOTS = {
    "elevenlabs",
    "httpx",
    "openai",
    "requests",
    "ultravox",
    "urllib",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{line_number} is not a JSON object")
        rows.append(payload)
    return rows


def write_status(name: str, failures: list[str], extra: dict[str, Any] | None = None) -> int:
    payload = {
        "validator": name,
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
    }
    if extra:
        payload.update(extra)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failures else 1


def load_action_labels() -> dict[str, dict[str, Any]]:
    payload = read_json(LABELS_PATH)
    labels = payload.get("labels")
    if not isinstance(labels, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for item in labels:
        if isinstance(item, dict) and isinstance(item.get("action_id"), str):
            result[item["action_id"]] = item
    return result


def dataset_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        split: read_jsonl(DATASET_DIR / f"{split}.jsonl")
        for split in ("train", "validation", "test")
    }


def shadow_replay_rows() -> list[dict[str, Any]]:
    return read_jsonl(SHADOW_REPLAY_DIR / "replay.jsonl")


def runtime_shadow_log_rows() -> list[dict[str, Any]]:
    return read_jsonl(RUNTIME_SHADOW_LOG_DIR / "result.jsonl")


def normalized_text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def exact_overlap_failures(rows_by_split: dict[str, list[dict[str, Any]]]) -> list[str]:
    failures: list[str] = []
    train_texts = {
        normalized_text(row.get("buyer_utterance_text"))
        for row in rows_by_split.get("train", [])
        if normalized_text(row.get("buyer_utterance_text"))
    }
    train_ids = {str(row.get("case_id") or "") for row in rows_by_split.get("train", [])}
    for split in ("validation", "test"):
        split_texts = {
            normalized_text(row.get("buyer_utterance_text"))
            for row in rows_by_split.get(split, [])
            if normalized_text(row.get("buyer_utterance_text"))
        }
        split_ids = {str(row.get("case_id") or "") for row in rows_by_split.get(split, [])}
        text_overlap = sorted(train_texts & split_texts)
        id_overlap = sorted(train_ids & split_ids)
        if text_overlap:
            failures.append(f"{split} buyer-text overlap with train: {text_overlap[:5]}")
        if id_overlap:
            failures.append(f"{split} case-id overlap with train: {id_overlap[:5]}")
    return failures


def no_private_or_audio_failures(rows_by_split: dict[str, list[dict[str, Any]]]) -> list[str]:
    failures: list[str] = []
    audio_keys = {"audio", "audio_path", "audio_file", "wav_path", "mp3_path", "generated_audio"}
    for split, rows in rows_by_split.items():
        for index, row in enumerate(rows, start=1):
            label = f"{split}[{index}]"
            if row.get("sanitized") is not True:
                failures.append(f"{label}.sanitized is not true")
            if row.get("raw_private_data") is not False:
                failures.append(f"{label}.raw_private_data is not false")
            present_audio = sorted(audio_keys & set(row))
            if present_audio:
                failures.append(f"{label} contains audio field(s): {present_audio}")
            source = normalized_text(row.get("source_file"))
            if "data/private" in source or "private-restricted" in source:
                failures.append(f"{label}.source_file references private data: {row.get('source_file')}")
    return failures


def imported_modules(path: Path) -> set[str]:
    if not path.is_file() or path.suffix != ".py":
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def forbidden_import_failures(paths: list[Path] | None = None) -> list[str]:
    failures: list[str] = []
    for path in paths or REQUESTED_SOURCE_PATHS:
        found = sorted(imported_modules(path) & FORBIDDEN_IMPORT_ROOTS)
        if found:
            failures.append(f"{path.relative_to(ROOT)} imports forbidden provider/network module(s): {found}")
    return failures


def tracked_weight_failures() -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return [f"git ls-files unavailable: {exc}"]
    if completed.returncode != 0:
        return [f"git ls-files failed: {completed.stderr.strip()}"]
    weights = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip().lower().endswith(WEIGHT_SUFFIXES)
    ]
    local_artifacts = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip().replace("\\", "/").startswith("local_artifacts/")
    ]
    failures: list[str] = []
    if weights:
        failures.append(f"model weight files tracked by git: {weights[:10]}")
    if local_artifacts:
        failures.append(f"local_artifacts files tracked by git: {local_artifacts[:10]}")
    return failures


def false_flag_failures(payload: dict[str, Any], keys: list[str], label: str) -> list[str]:
    failures: list[str] = []
    for key in keys:
        if payload.get(key) is not False:
            failures.append(f"{label}.{key} must be false")
    return failures


def controlled_label_failures(rows_by_split: dict[str, list[dict[str, Any]]] | None = None) -> list[str]:
    failures: list[str] = []
    labels = load_action_labels()
    if not labels:
        return ["action labels are missing or empty"]
    for action_id, item in labels.items():
        if item.get("renderer_required") is not True:
            failures.append(f"{action_id}.renderer_required must be true")
        if item.get("can_generate_text") is not False:
            failures.append(f"{action_id}.can_generate_text must be false")
    if rows_by_split is None:
        return failures
    allowed = set(labels)
    for split, rows in rows_by_split.items():
        for index, row in enumerate(rows, start=1):
            action_id = str(row.get("target_action_id") or "")
            if action_id not in allowed:
                failures.append(f"{split}[{index}].target_action_id is not controlled: {action_id}")
    return failures


def no_shadow_text_or_runtime_change_failures(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    false_keys = [
        "side_effects_allowed",
        "buyer_facing_text_generated",
        "live_runtime_wiring_allowed",
        "response_text_changed",
        "runtime_behavior_changed",
        "provider_calls_made",
        "openai_api_calls_made",
        "ultravox_calls_made",
        "elevenlabs_calls_made",
        "local_llm_calls_made",
        "ollama_calls_made",
    ]
    failures.extend(false_flag_failures(payload, false_keys, label))
    if payload.get("should_not_change_runtime") is not True:
        failures.append(f"{label}.should_not_change_runtime must be true")
    return failures


def no_private_or_audio_shadow_failures(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    audio_keys = {"audio", "audio_path", "audio_file", "wav_path", "mp3_path", "generated_audio"}
    for index, row in enumerate(rows, start=1):
        label = f"shadow_replay[{index}]"
        if row.get("sanitized") is not True:
            failures.append(f"{label}.sanitized is not true")
        if row.get("raw_private_data") is not False:
            failures.append(f"{label}.raw_private_data is not false")
        present_audio = sorted(audio_keys & set(row))
        if present_audio:
            failures.append(f"{label} contains audio field(s): {present_audio}")
        source = normalized_text(row.get("source_file"))
        if "data/private" in source or "private-restricted" in source:
            failures.append(f"{label}.source_file references private data: {row.get('source_file')}")
    return failures
