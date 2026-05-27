from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.util
from importlib import metadata as importlib_metadata
import json
import platform
from queue import Empty
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt
from runtime.llm_brain.conversation_brain_schema import (
    COMPACT_PLANNER_SCHEMA_MODE,
    FULL_PLANNER_SCHEMA_MODE,
    LocalConversationBrainConfig,
    PRIMARY_MODEL_ID,
    expand_compact_planner_output,
    validate_compact_conversation_brain_output,
    validate_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PlannerRepairDiagnostics:
    parse_errors: list[str]
    raw_schema_errors_before_repair: list[str]
    schema_errors_after_repair: list[str]
    repair_applied: bool
    repair_types: list[str]
    needs_fact_check_before_repair: bool | None
    needs_fact_check_after_repair: bool | None
    planner_schema_mode: str
    compact_planner_output: dict[str, Any] | None
    compact_schema_errors: list[str]
    compact_adapter_errors: list[str]
    compact_adapter_applied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "parse_errors": self.parse_errors,
            "raw_schema_errors_before_repair": self.raw_schema_errors_before_repair,
            "schema_errors_after_repair": self.schema_errors_after_repair,
            "repair_applied": self.repair_applied,
            "repair_types": self.repair_types,
            "needs_fact_check_before_repair": self.needs_fact_check_before_repair,
            "needs_fact_check_after_repair": self.needs_fact_check_after_repair,
            "planner_schema_mode": self.planner_schema_mode,
            "compact_planner_output": self.compact_planner_output,
            "compact_schema_errors": self.compact_schema_errors,
            "compact_adapter_errors": self.compact_adapter_errors,
            "compact_adapter_applied": self.compact_adapter_applied,
        }


@dataclass(frozen=True)
class LocalTransformersCaseResult:
    case_id: str
    status: str
    prompt_rendered: bool
    inference_attempted: bool
    local_model_calls_made: bool
    planner_output: dict[str, Any] | None
    raw_output_excerpt: str
    schema_errors: list[str]
    raw_schema_errors_before_repair: list[str]
    schema_errors_after_repair: list[str]
    verifier_errors: list[str]
    verifier_errors_before_repair: list[str]
    verifier_errors_after_repair: list[str]
    repair_applied: bool
    repair_types: list[str]
    needs_fact_check_before_repair: bool | None
    needs_fact_check_after_repair: bool | None
    planner_schema_mode: str
    compact_planner_output: dict[str, Any] | None
    compact_schema_errors: list[str]
    compact_adapter_errors: list[str]
    compact_adapter_applied: bool
    errors: list[str]
    latency_metrics: dict[str, float | int | bool | None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "status": self.status,
            "prompt_rendered": self.prompt_rendered,
            "inference_attempted": self.inference_attempted,
            "local_model_calls_made": self.local_model_calls_made,
            "planner_output": self.planner_output,
            "raw_output_excerpt": self.raw_output_excerpt,
            "schema_errors": self.schema_errors,
            "raw_schema_errors_before_repair": self.raw_schema_errors_before_repair,
            "schema_errors_after_repair": self.schema_errors_after_repair,
            "verifier_errors": self.verifier_errors,
            "verifier_errors_before_repair": self.verifier_errors_before_repair,
            "verifier_errors_after_repair": self.verifier_errors_after_repair,
            "repair_applied": self.repair_applied,
            "repair_types": self.repair_types,
            "needs_fact_check_before_repair": self.needs_fact_check_before_repair,
            "needs_fact_check_after_repair": self.needs_fact_check_after_repair,
            "planner_schema_mode": self.planner_schema_mode,
            "compact_planner_output": self.compact_planner_output,
            "compact_schema_errors": self.compact_schema_errors,
            "compact_adapter_errors": self.compact_adapter_errors,
            "compact_adapter_applied": self.compact_adapter_applied,
            "errors": self.errors,
            "latency_metrics": self.latency_metrics,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def package_version(module_name: str) -> str | None:
    package_names = {
        "huggingface_hub": "huggingface-hub",
    }
    if importlib.util.find_spec(module_name) is None:
        return None
    try:
        return importlib_metadata.version(package_names.get(module_name, module_name))
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def dependency_status(quantization_mode: str = "4bit") -> dict[str, Any]:
    modules = {
        "torch": importlib.util.find_spec("torch") is not None,
        "transformers": importlib.util.find_spec("transformers") is not None,
        "accelerate": importlib.util.find_spec("accelerate") is not None,
        "bitsandbytes": importlib.util.find_spec("bitsandbytes") is not None,
        "safetensors": importlib.util.find_spec("safetensors") is not None,
        "huggingface_hub": importlib.util.find_spec("huggingface_hub") is not None,
    }
    versions = {name: package_version(name) for name in modules}
    required = ["torch", "transformers", "accelerate", "safetensors", "huggingface_hub"]
    if quantization_mode in {"4bit", "8bit"}:
        required.append("bitsandbytes")
    missing_required = [name for name in required if not modules[name]]
    install_notes = []
    if missing_required:
        install_notes.append(
            "Install the missing local inference packages in this project environment before enabling inference."
        )
    if not modules["bitsandbytes"] and quantization_mode == "4bit":
        install_notes.append(
            "4-bit loading needs bitsandbytes; set LOCAL_LLM_QUANTIZATION=none only if you accept higher VRAM use."
        )
    return {
        "modules": modules,
        "versions": versions,
        "required": required,
        "missing_required": missing_required,
        "ready": not missing_required,
        "install_notes": install_notes,
    }


def nvidia_smi_summary() -> dict[str, Any]:
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,memory.total",
        "--format=csv,noheader",
    ]
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
    except FileNotFoundError:
        return {"available": False, "error": "nvidia-smi not found"}
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def hardware_summary() -> dict[str, Any]:
    nvidia = nvidia_smi_summary()
    summary: dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "torch_available": importlib.util.find_spec("torch") is not None,
        "cuda_available": False,
        "gpu_name": None,
        "vram_total_bytes": None,
        "nvidia_smi": nvidia,
    }
    if nvidia.get("available") and nvidia.get("stdout"):
        first_line = str(nvidia["stdout"]).splitlines()[0]
        parts = [part.strip() for part in first_line.split(",")]
        if parts:
            summary["gpu_name"] = parts[0]
        if len(parts) >= 2:
            summary["nvidia_driver_version"] = parts[1]
        if len(parts) >= 3:
            summary["nvidia_vram_total"] = parts[2]
            memory_parts = parts[2].split()
            if len(memory_parts) == 2 and memory_parts[1].lower() == "mib":
                try:
                    summary["vram_total_bytes"] = int(memory_parts[0]) * 1024 * 1024
                except ValueError:
                    pass
    if not summary["torch_available"]:
        return summary
    try:
        import torch  # type: ignore

        summary["torch_version"] = getattr(torch, "__version__", None)
        summary["torch_cuda_version"] = getattr(getattr(torch, "version", None), "cuda", None)
        summary["cuda_available"] = bool(torch.cuda.is_available())
        if summary["cuda_available"]:
            device_index = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device_index)
            summary["gpu_name"] = torch.cuda.get_device_name(device_index)
            summary["vram_total_bytes"] = int(props.total_memory)
    except Exception as exc:
        summary["torch_error"] = str(exc)
    return summary


def project_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must be project-relative: {relative_path!r}")
    return ROOT / path


def model_path_status(config: LocalConversationBrainConfig) -> dict[str, Any]:
    path = project_path(config.model_path)
    marker_names = {
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "model.safetensors.index.json",
        "pytorch_model.bin.index.json",
    }
    markers = [name for name in marker_names if (path / name).is_file()]
    weight_count = 0
    if path.is_dir():
        weight_count = sum(1 for pattern in ("*.safetensors", "*.bin", "*.gguf") for _ in path.glob(pattern))
    return {
        "configured_path": config.model_path,
        "absolute_path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "markers": sorted(markers),
        "weight_file_count": weight_count,
        "available": path.is_dir() and bool(markers) and weight_count > 0,
    }


def ensure_model_available(
    config: LocalConversationBrainConfig,
    *,
    allow_model_download: bool,
) -> dict[str, Any]:
    status = model_path_status(config)
    status["download_attempted"] = False
    status["download_allowed"] = allow_model_download
    if status["available"] or not allow_model_download:
        return status
    if importlib.util.find_spec("huggingface_hub") is None:
        status["error"] = "huggingface_hub is required for LOCAL_LLM_ALLOW_MODEL_DOWNLOAD=1"
        return status

    from huggingface_hub import snapshot_download  # type: ignore

    model_path = project_path(config.model_path)
    cache_dir = project_path(config.cache_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    status["download_attempted"] = True
    downloaded_path = snapshot_download(
        repo_id=config.model_id,
        local_dir=str(model_path),
        cache_dir=str(cache_dir),
    )
    status["downloaded_path"] = downloaded_path
    return model_path_status(config) | {
        "download_attempted": True,
        "download_allowed": True,
        "downloaded_path": downloaded_path,
    }


MARKDOWN_FENCE_RE = re.compile(r"^\s*```(?:json|JSON)?\s*|\s*```\s*", re.M)

LIST_FIELD_PATHS = {
    "semantic_frame.object_mentions",
    "state_update.use_case_values",
    "state_update.blocked_updates",
    "response_plan.must_include",
    "response_plan.must_not_include",
    "response_plan.campaign_facts_needed",
    "response_plan.buyer_words_to_preserve",
    "reasons",
}

BOOL_FIELD_PATHS = {
    "state_update.should_update_adoption_state",
    "state_update.should_update_use_case",
    "state_update.should_update_usage_intensity",
    "state_update.should_update_team_state",
    "state_update.should_update_recommendation",
    "state_update.should_update_close_readiness",
    "sales_strategy.should_answer_directly",
    "sales_strategy.should_ask_question",
    "sales_strategy.should_recommend",
    "sales_strategy.should_reframe_objection",
    "sales_strategy.should_close",
    "sales_strategy.should_disqualify",
    "safety_flags.needs_fact_check",
    "safety_flags.unsupported_product_claim_risk",
    "safety_flags.side_effect_claim_risk",
    "safety_flags.affiliation_claim_risk",
    "safety_flags.internal_policy_language_risk",
    "safety_flags.raw_url_risk",
    "safety_flags.campaign_leakage_risk",
}


def _without_markdown_fences(text: str) -> tuple[str, bool]:
    if "```" not in text:
        return text, False
    return MARKDOWN_FENCE_RE.sub("", text), True


def _first_json_object(text: str) -> tuple[dict[str, Any] | None, str | None, bool, list[str]]:
    stripped = text.strip()
    if not stripped:
        return None, None, False, ["model returned empty text"]
    decoder = json.JSONDecoder()
    index = stripped.find("{")
    if index == -1:
        return None, None, False, ["model output was not strict JSON or recoverable first JSON object"]
    try:
        payload, end_index = decoder.raw_decode(stripped[index:])
    except json.JSONDecodeError as exc:
        return None, None, False, [f"model output first JSON object is incomplete or invalid: {exc}"]
    if not isinstance(payload, dict):
        return None, None, False, ["model output JSON must be an object"]
    object_text = stripped[index : index + end_index]
    extracted = index != 0 or bool(stripped[index + end_index :].strip())
    return payload, object_text, extracted, []


def _nested_parent(payload: dict[str, Any], dotted_path: str) -> tuple[dict[str, Any] | None, str]:
    parts = dotted_path.split(".")
    if len(parts) == 1:
        return payload, parts[0]
    parent: Any = payload
    for part in parts[:-1]:
        if not isinstance(parent, dict):
            return None, parts[-1]
        parent = parent.get(part)
    return (parent, parts[-1]) if isinstance(parent, dict) else (None, parts[-1])


def _needs_fact_check(payload: dict[str, Any] | None) -> bool | None:
    if not isinstance(payload, dict):
        return None
    safety = payload.get("safety_flags")
    if not isinstance(safety, dict):
        return None
    value = safety.get("needs_fact_check")
    return value if isinstance(value, bool) else None


def _repair_planner_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    repaired = deepcopy(payload)
    repair_types: list[str] = []

    strategy = repaired.get("sales_strategy")
    if isinstance(strategy, dict) and "should_reframe_objction" in strategy:
        typo_value = strategy.pop("should_reframe_objction")
        if "should_reframe_objection" not in strategy:
            strategy["should_reframe_objection"] = typo_value
        repair_types.append("known_key_typo:sales_strategy.should_reframe_objction->should_reframe_objection")

    for dotted_path in sorted(LIST_FIELD_PATHS):
        parent, key = _nested_parent(repaired, dotted_path)
        if parent is not None and isinstance(parent.get(key), str):
            parent[key] = [parent[key]]
            repair_types.append(f"list_coercion:{dotted_path}")

    for dotted_path in sorted(BOOL_FIELD_PATHS):
        parent, key = _nested_parent(repaired, dotted_path)
        value = parent.get(key) if parent is not None else None
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            parent[key] = value.strip().lower() == "true"
            repair_types.append(f"boolean_string_coercion:{dotted_path}")

    confidence = repaired.get("confidence")
    if isinstance(confidence, str):
        try:
            repaired["confidence"] = float(confidence.strip())
            repair_types.append("confidence_number_string_coercion")
        except ValueError:
            pass

    return repaired, repair_types


def parse_and_repair_planner_output(
    text: str,
    *,
    schema_mode: str = FULL_PLANNER_SCHEMA_MODE,
) -> tuple[dict[str, Any] | None, PlannerRepairDiagnostics]:
    parse_repair_types: list[str] = []
    cleaned, removed_fence = _without_markdown_fences(text)
    if removed_fence:
        parse_repair_types.append("markdown_code_fence_removed")
    payload, _object_text, extracted, parse_errors = _first_json_object(cleaned)
    if extracted:
        parse_repair_types.append("first_json_object_extracted")
    if payload is None:
        diagnostics = PlannerRepairDiagnostics(
            parse_errors=parse_errors,
            raw_schema_errors_before_repair=[],
            schema_errors_after_repair=[],
            repair_applied=bool(parse_repair_types),
            repair_types=parse_repair_types,
            needs_fact_check_before_repair=None,
            needs_fact_check_after_repair=None,
            planner_schema_mode=schema_mode,
            compact_planner_output=None,
            compact_schema_errors=[],
            compact_adapter_errors=[],
            compact_adapter_applied=False,
        )
        return None, diagnostics

    if schema_mode == COMPACT_PLANNER_SCHEMA_MODE:
        compact_schema_errors = validate_compact_conversation_brain_output(payload)
        if compact_schema_errors:
            diagnostics = PlannerRepairDiagnostics(
                parse_errors=parse_errors,
                raw_schema_errors_before_repair=compact_schema_errors,
                schema_errors_after_repair=compact_schema_errors,
                repair_applied=bool(parse_repair_types),
                repair_types=parse_repair_types,
                needs_fact_check_before_repair=None,
                needs_fact_check_after_repair=None,
                planner_schema_mode=schema_mode,
                compact_planner_output=payload,
                compact_schema_errors=compact_schema_errors,
                compact_adapter_errors=[],
                compact_adapter_applied=False,
            )
            return None, diagnostics
        expanded, adapter_errors = expand_compact_planner_output(payload)
        diagnostics = PlannerRepairDiagnostics(
            parse_errors=parse_errors,
            raw_schema_errors_before_repair=compact_schema_errors,
            schema_errors_after_repair=adapter_errors,
            repair_applied=bool(parse_repair_types),
            repair_types=parse_repair_types,
            needs_fact_check_before_repair=None,
            needs_fact_check_after_repair=_needs_fact_check(expanded),
            planner_schema_mode=schema_mode,
            compact_planner_output=payload,
            compact_schema_errors=compact_schema_errors,
            compact_adapter_errors=adapter_errors,
            compact_adapter_applied=True,
        )
        return expanded, diagnostics

    raw_schema_errors = validate_conversation_brain_output(payload)
    repaired, repair_types = _repair_planner_payload(payload)
    all_repair_types = [*parse_repair_types, *repair_types]
    schema_errors_after_repair = validate_conversation_brain_output(repaired)
    diagnostics = PlannerRepairDiagnostics(
        parse_errors=parse_errors,
        raw_schema_errors_before_repair=raw_schema_errors,
        schema_errors_after_repair=schema_errors_after_repair,
        repair_applied=bool(all_repair_types),
        repair_types=all_repair_types,
        needs_fact_check_before_repair=_needs_fact_check(payload),
        needs_fact_check_after_repair=_needs_fact_check(repaired),
        planner_schema_mode=schema_mode,
        compact_planner_output=None,
        compact_schema_errors=[],
        compact_adapter_errors=[],
        compact_adapter_applied=False,
    )
    return repaired, diagnostics


def parse_strict_json(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    payload, diagnostics = parse_and_repair_planner_output(text)
    return payload, diagnostics.parse_errors


def _reset_peak_memory() -> None:
    if importlib.util.find_spec("torch") is None:
        return
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except Exception:
        return


def _peak_memory_bytes() -> int | None:
    if importlib.util.find_spec("torch") is None:
        return None
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return int(torch.cuda.max_memory_allocated())
    except Exception:
        return None
    return None


def load_local_transformers_model(
    config: LocalConversationBrainConfig,
    *,
    allow_model_download: bool,
) -> tuple[Any, Any, dict[str, Any]]:
    if config.model_id != PRIMARY_MODEL_ID:
        raise ValueError(f"only {PRIMARY_MODEL_ID} is supported in this phase")
    deps = dependency_status(config.quantization_mode)
    if deps["missing_required"]:
        raise RuntimeError(f"missing local inference dependencies: {', '.join(deps['missing_required'])}")

    import torch  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    model_status = ensure_model_available(config, allow_model_download=allow_model_download)
    if not model_status["available"]:
        raise FileNotFoundError(
            f"local model files not found under {config.model_path}; set LOCAL_LLM_ALLOW_MODEL_DOWNLOAD=1 to download"
        )

    model_ref = str(project_path(config.model_path))
    cache_dir = str(project_path(config.cache_dir))
    local_files_only = not allow_model_download
    quantization_kwargs: dict[str, Any] = {}
    if config.quantization_mode == "4bit":
        quantization_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    elif config.quantization_mode == "8bit":
        quantization_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)

    tokenizer = AutoTokenizer.from_pretrained(
        model_ref,
        cache_dir=cache_dir,
        local_files_only=local_files_only,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_ref,
        cache_dir=cache_dir,
        local_files_only=local_files_only,
        device_map="auto" if config.device in {"cuda", "auto"} else None,
        torch_dtype="auto",
        low_cpu_mem_usage=True,
        **quantization_kwargs,
    )
    model.eval()
    return model, tokenizer, model_status


def render_qwen_prompt(
    tokenizer: Any,
    request_context: dict[str, Any],
    *,
    schema_mode: str = FULL_PLANNER_SCHEMA_MODE,
) -> str:
    prompt = render_conversation_brain_prompt(request_context, schema_mode=schema_mode)
    messages = [
        {
            "role": "user",
            "content": prompt + "\n\nReturn exactly one minified single-line JSON object and no markdown.",
        }
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return str(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
        except Exception:
            return prompt
    return prompt


def generate_text(
    model: Any,
    tokenizer: Any,
    prompt: str,
    config: LocalConversationBrainConfig,
) -> tuple[str, dict[str, float | int | bool | None]]:
    import torch  # type: ignore
    from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer  # type: ignore

    device = "cuda" if config.device in {"cuda", "auto"} and torch.cuda.is_available() else "cpu"
    tokenized = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=config.max_input_tokens)
    prompt_token_count = int(tokenized["input_ids"].shape[-1])
    prompt_truncated = prompt_token_count >= config.max_input_tokens
    inputs = {key: value.to(device) for key, value in tokenized.items()}
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=1.0)
    deadline = time.perf_counter() + (config.timeout_ms / 1000)
    stop_after_json_object = threading.Event()

    class WallClockStoppingCriteria(StoppingCriteria):
        def __call__(self, input_ids: Any, scores: Any, **kwargs: Any) -> bool:
            return stop_after_json_object.is_set() or time.perf_counter() >= deadline

    generation_kwargs = {
        **inputs,
        "streamer": streamer,
        "max_new_tokens": config.max_output_tokens,
        "do_sample": False,
        "pad_token_id": tokenizer.eos_token_id,
        "stopping_criteria": StoppingCriteriaList([WallClockStoppingCriteria()]),
    }
    errors: list[BaseException] = []

    def target() -> None:
        try:
            model.generate(**generation_kwargs)
        except BaseException as exc:
            errors.append(exc)

    _reset_peak_memory()
    started = time.perf_counter()
    first_output_latency_ms: float | None = None
    completed_json_object = False
    stopped_after_first_json_object = False
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    chunks: list[str] = []
    iterator = iter(streamer)
    while True:
        try:
            chunk = next(iterator)
        except StopIteration:
            break
        except Empty:
            if not thread.is_alive():
                break
            if time.perf_counter() >= deadline:
                break
            continue
        if chunk and first_output_latency_ms is None:
            first_output_latency_ms = round((time.perf_counter() - started) * 1000, 3)
        chunks.append(chunk)
        if not completed_json_object:
            cleaned_so_far, _removed = _without_markdown_fences("".join(chunks))
            first_object, _object_text, _extracted, _parse_errors = _first_json_object(cleaned_so_far)
            if first_object is not None:
                completed_json_object = True
                stopped_after_first_json_object = True
                stop_after_json_object.set()
        if time.perf_counter() >= deadline:
            break
    thread.join(timeout=5)
    if thread.is_alive():
        raise TimeoutError(f"local generation exceeded timeout_ms={config.timeout_ms}")
    if errors:
        raise RuntimeError(str(errors[0]))
    total_ms = round((time.perf_counter() - started) * 1000, 3)
    raw_text = "".join(chunks)
    generated_tokens = len(tokenizer(raw_text, add_special_tokens=False).get("input_ids", []))
    timed_out = time.perf_counter() >= deadline and not completed_json_object
    output_truncated = generated_tokens >= config.max_output_tokens and not completed_json_object
    return raw_text, {
        "prompt_token_count": prompt_token_count,
        "prompt_truncated": prompt_truncated,
        "max_output_tokens": config.max_output_tokens,
        "timeout_ms": config.timeout_ms,
        "first_output_latency_ms": first_output_latency_ms,
        "total_generation_latency_ms": total_ms,
        "tokens_generated": generated_tokens,
        "completed_json_object": completed_json_object,
        "stopped_after_first_json_object": stopped_after_first_json_object,
        "output_truncated": output_truncated,
        "timed_out": timed_out,
        "peak_gpu_memory_bytes": _peak_memory_bytes(),
    }


def run_single_conversation_brain_case(
    *,
    config: LocalConversationBrainConfig,
    request_context: dict[str, Any],
    case: dict[str, Any],
    allow_model_download: bool,
    model: Any | None = None,
    tokenizer: Any | None = None,
) -> LocalTransformersCaseResult:
    case_id = str(case.get("case_id") or "single_case")
    prompt = render_conversation_brain_prompt(request_context, schema_mode=config.planner_schema_mode)
    prompt_rendered = bool(prompt)
    load_started = time.perf_counter()
    load_ms: float | None = None
    raw_output = ""
    planner_output: dict[str, Any] | None = None
    model_call_made = False
    schema_errors: list[str] = []
    raw_schema_errors_before_repair: list[str] = []
    verifier_errors: list[str] = []
    verifier_errors_before_repair: list[str] = []
    repair_diagnostics = PlannerRepairDiagnostics(
        parse_errors=[],
        raw_schema_errors_before_repair=[],
        schema_errors_after_repair=[],
        repair_applied=False,
        repair_types=[],
        needs_fact_check_before_repair=None,
        needs_fact_check_after_repair=None,
        planner_schema_mode=config.planner_schema_mode,
        compact_planner_output=None,
        compact_schema_errors=[],
        compact_adapter_errors=[],
        compact_adapter_applied=False,
    )
    errors: list[str] = []
    generation_metrics: dict[str, float | int | bool | None] = {
        "model_load_time_ms": None,
        "prompt_token_count": None,
        "prompt_truncated": None,
        "max_output_tokens": config.max_output_tokens,
        "timeout_ms": config.timeout_ms,
        "first_output_latency_ms": None,
        "total_generation_latency_ms": None,
        "tokens_generated": None,
        "completed_json_object": None,
        "stopped_after_first_json_object": None,
        "output_truncated": None,
        "timed_out": None,
        "peak_gpu_memory_bytes": None,
    }
    try:
        if model is None or tokenizer is None:
            model, tokenizer, _model_status = load_local_transformers_model(
                config,
                allow_model_download=allow_model_download,
            )
            load_ms = round((time.perf_counter() - load_started) * 1000, 3)
        else:
            load_ms = 0.0
        generation_metrics["model_load_time_ms"] = load_ms
        qwen_prompt = render_qwen_prompt(tokenizer, request_context, schema_mode=config.planner_schema_mode)
        model_call_made = True
        raw_output, run_metrics = generate_text(model, tokenizer, qwen_prompt, config)
        generation_metrics.update(run_metrics)
        planner_output, repair_diagnostics = parse_and_repair_planner_output(
            raw_output,
            schema_mode=config.planner_schema_mode,
        )
        errors.extend(repair_diagnostics.parse_errors)
        raw_schema_errors_before_repair = repair_diagnostics.raw_schema_errors_before_repair
        schema_errors = repair_diagnostics.schema_errors_after_repair
        if planner_output is not None:
            raw_cleaned, _removed_fence = _without_markdown_fences(raw_output)
            raw_payload, _object_text, _extracted, _raw_parse_errors = _first_json_object(raw_cleaned)
            if (
                raw_payload is not None
                and not raw_schema_errors_before_repair
                and config.planner_schema_mode == COMPACT_PLANNER_SCHEMA_MODE
            ):
                raw_expanded, raw_adapter_errors = expand_compact_planner_output(raw_payload)
                if not raw_adapter_errors:
                    verifier_errors_before_repair = verify_conversation_brain_output(raw_expanded, case)
            elif raw_payload is not None and not raw_schema_errors_before_repair:
                verifier_errors_before_repair = verify_conversation_brain_output(raw_payload, case)
            verifier_errors = verify_conversation_brain_output(planner_output, case)
    except Exception as exc:
        errors.append(str(exc))

    status = "pass" if not errors and not schema_errors and not verifier_errors else "fail"
    return LocalTransformersCaseResult(
        case_id=case_id,
        status=status,
        prompt_rendered=prompt_rendered,
        inference_attempted=True,
        local_model_calls_made=model_call_made,
        planner_output=planner_output,
        raw_output_excerpt=raw_output[:1200],
        schema_errors=schema_errors,
        raw_schema_errors_before_repair=raw_schema_errors_before_repair,
        schema_errors_after_repair=schema_errors,
        verifier_errors=verifier_errors,
        verifier_errors_before_repair=verifier_errors_before_repair,
        verifier_errors_after_repair=verifier_errors,
        repair_applied=repair_diagnostics.repair_applied,
        repair_types=repair_diagnostics.repair_types,
        needs_fact_check_before_repair=repair_diagnostics.needs_fact_check_before_repair,
        needs_fact_check_after_repair=repair_diagnostics.needs_fact_check_after_repair,
        planner_schema_mode=config.planner_schema_mode,
        compact_planner_output=repair_diagnostics.compact_planner_output,
        compact_schema_errors=repair_diagnostics.compact_schema_errors,
        compact_adapter_errors=repair_diagnostics.compact_adapter_errors,
        compact_adapter_applied=repair_diagnostics.compact_adapter_applied,
        errors=errors,
        latency_metrics=generation_metrics,
    )
