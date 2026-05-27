from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.util
import json
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt
from runtime.llm_brain.conversation_brain_schema import (
    LocalConversationBrainConfig,
    PRIMARY_MODEL_ID,
    validate_conversation_brain_output,
)
from runtime.llm_brain.conversation_brain_verifier import verify_conversation_brain_output


ROOT = Path(__file__).resolve().parents[2]


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
    verifier_errors: list[str]
    errors: list[str]
    latency_metrics: dict[str, float | int | None]

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
            "verifier_errors": self.verifier_errors,
            "errors": self.errors,
            "latency_metrics": self.latency_metrics,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def dependency_status(quantization_mode: str = "4bit") -> dict[str, Any]:
    modules = {
        "torch": importlib.util.find_spec("torch") is not None,
        "transformers": importlib.util.find_spec("transformers") is not None,
        "accelerate": importlib.util.find_spec("accelerate") is not None,
        "bitsandbytes": importlib.util.find_spec("bitsandbytes") is not None,
        "huggingface_hub": importlib.util.find_spec("huggingface_hub") is not None,
    }
    required = ["torch", "transformers", "accelerate"]
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


def parse_strict_json(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    stripped = text.strip()
    if not stripped:
        return None, ["model returned empty text"]
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return None, [f"model output was not strict JSON: {exc}"]
    if not isinstance(payload, dict):
        return None, ["model output JSON must be an object"]
    return payload, []


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


def render_qwen_prompt(tokenizer: Any, request_context: dict[str, Any]) -> str:
    prompt = render_conversation_brain_prompt(request_context)
    messages = [
        {
            "role": "user",
            "content": prompt + "\n\nReturn exactly one JSON object and no markdown.",
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
) -> tuple[str, dict[str, float | int | None]]:
    import torch  # type: ignore
    from transformers import TextIteratorStreamer  # type: ignore

    device = "cuda" if config.device in {"cuda", "auto"} and torch.cuda.is_available() else "cpu"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=config.max_input_tokens)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = {
        **inputs,
        "streamer": streamer,
        "max_new_tokens": config.max_output_tokens,
        "do_sample": False,
        "pad_token_id": tokenizer.eos_token_id,
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
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    chunks: list[str] = []
    for chunk in streamer:
        if chunk and first_output_latency_ms is None:
            first_output_latency_ms = round((time.perf_counter() - started) * 1000, 3)
        chunks.append(chunk)
    thread.join(timeout=max(1, config.timeout_ms / 1000))
    if thread.is_alive():
        raise TimeoutError(f"local generation exceeded timeout_ms={config.timeout_ms}")
    if errors:
        raise RuntimeError(str(errors[0]))
    total_ms = round((time.perf_counter() - started) * 1000, 3)
    raw_text = "".join(chunks)
    generated_tokens = len(tokenizer(raw_text, add_special_tokens=False).get("input_ids", []))
    return raw_text, {
        "first_output_latency_ms": first_output_latency_ms,
        "total_generation_latency_ms": total_ms,
        "tokens_generated": generated_tokens,
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
    prompt = render_conversation_brain_prompt(request_context)
    prompt_rendered = bool(prompt)
    load_started = time.perf_counter()
    load_ms: float | None = None
    raw_output = ""
    planner_output: dict[str, Any] | None = None
    model_call_made = False
    schema_errors: list[str] = []
    verifier_errors: list[str] = []
    errors: list[str] = []
    generation_metrics: dict[str, float | int | None] = {
        "model_load_time_ms": None,
        "first_output_latency_ms": None,
        "total_generation_latency_ms": None,
        "tokens_generated": None,
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
        qwen_prompt = render_qwen_prompt(tokenizer, request_context)
        model_call_made = True
        raw_output, run_metrics = generate_text(model, tokenizer, qwen_prompt, config)
        generation_metrics.update(run_metrics)
        planner_output, strict_errors = parse_strict_json(raw_output)
        errors.extend(strict_errors)
        if planner_output is not None:
            schema_errors = validate_conversation_brain_output(planner_output)
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
        verifier_errors=verifier_errors,
        errors=errors,
        latency_metrics=generation_metrics,
    )
