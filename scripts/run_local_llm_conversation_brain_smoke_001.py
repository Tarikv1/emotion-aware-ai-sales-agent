#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_prompts import render_conversation_brain_prompt  # noqa: E402
from runtime.llm_brain.local_conversation_brain import EXPERIMENT_ENV_VAR  # noqa: E402


OUT_DIR = ROOT / ".tmp" / "LOCAL-LLM-CONVERSATION-BRAIN-SMOKE-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def nvidia_summary() -> dict[str, Any]:
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
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "processor": platform.processor(),
        "machine": platform.machine(),
        "nvidia_smi": nvidia_summary(),
    }


def safe_sample_contexts() -> list[dict[str, Any]]:
    return [
        {"normalized_transcript": "coding workflow and probably voice"},
        {"normalized_transcript": "not a team, just me"},
        {"normalized_transcript": "what are these plans"},
        {"normalized_transcript": "that price feels high"},
        {"normalized_transcript": "are you from OpenAI"},
    ]


def run_local_transformers_smoke(model_path: Path) -> list[dict[str, Any]]:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline  # type: ignore

    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(str(model_path), local_files_only=True, device_map="auto")
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
    samples: list[dict[str, Any]] = []
    for context in safe_sample_contexts():
        prompt = render_conversation_brain_prompt(
            {
                **context,
                "prior_state": {},
                "approved_campaign_fact_ids": ["public_plan_names"],
                "campaign_id": "public-openai-chatgpt-plans",
            }
        )
        started = time.perf_counter()
        output = generator(prompt, max_new_tokens=320, do_sample=False, return_full_text=False)
        samples.append(
            {
                "input": context["normalized_transcript"],
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "raw_output": output[0].get("generated_text", "") if output else "",
            }
        )
    return samples


def main() -> int:
    enabled = os.getenv(EXPERIMENT_ENV_VAR) == "1"
    model_path_text = os.getenv("LOCAL_LLM_BRAIN_MODEL_PATH", "")
    provider = os.getenv("LOCAL_LLM_BRAIN_PROVIDER", "local_transformers")
    result: dict[str, Any] = {
        "smoke_id": "LOCAL-LLM-CONVERSATION-BRAIN-SMOKE-001",
        "generated_at": utc_now(),
        "experiment_env_enabled": enabled,
        "provider": provider,
        "model_path_configured": bool(model_path_text),
        "hardware": hardware_summary(),
        "local_model_inference_attempted": False,
        "provider_calls_made": False,
        "samples": [],
        "errors": [],
    }
    print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))
    if not enabled:
        print(f"{EXPERIMENT_ENV_VAR}=1 is required before local model inference. Exiting without model calls.")
        return 0
    model_path = Path(model_path_text)
    if not model_path_text or not model_path.exists():
        print("LOCAL_LLM_BRAIN_MODEL_PATH must point at an existing local model directory. Exiting without model calls.")
        return 0
    if provider != "local_transformers":
        print("Only local_transformers smoke is implemented. Exiting without model calls.")
        return 0

    result["local_model_inference_attempted"] = True
    try:
        result["samples"] = run_local_transformers_smoke(model_path)
    except Exception as exc:
        result["errors"].append(str(exc))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUT_DIR / "result.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote local smoke result to {output_path}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
