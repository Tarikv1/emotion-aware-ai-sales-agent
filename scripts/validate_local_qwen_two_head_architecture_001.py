#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.live_action_prompt import render_live_action_prompt  # noqa: E402
from runtime.llm_brain.live_action_verifier import allowed_live_action_ids  # noqa: E402
from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    audit_side_effects,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
)


EXPERIMENT_ID = "LOCAL-QWEN-TWO-HEAD-ARCHITECTURE-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
ARCHITECTURE_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_two_head_architecture_spec.json"
LIVE_ACTION_CONTRACT_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_live_action_contract.json"
ANTI_LOOP_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_anti_loop_memory_contract.json"
UNCERTAINTY_PATH = ROOT / "runtime" / "llm_brain" / "training" / "qwen_buyer_facing_uncertainty_policy.json"
PROMPT_PATH = ROOT / "runtime" / "llm_brain" / "live_action_prompt.py"
VERIFIER_PATH = ROOT / "runtime" / "llm_brain" / "live_action_verifier.py"
FILES_TO_SCAN = (
    ARCHITECTURE_PATH,
    LIVE_ACTION_CONTRACT_PATH,
    ANTI_LOOP_PATH,
    UNCERTAINTY_PATH,
    PROMPT_PATH,
    VERIFIER_PATH,
)
BLOCKED_PATTERNS = {
    "provider_client_import": "from openai",
    "provider_client_ctor": "openai.OpenAI",
    "requests_post": "requests.post",
    "httpx_post": "httpx.post",
    "trainer": "Trainer(",
    "training_args": "TrainingArguments",
    "peft_model": "PeftModel",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def validate_no_blocked_patterns(failures: list[str]) -> None:
    for path in FILES_TO_SCAN:
        if not path.is_file():
            failures.append(f"missing required file: {rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in BLOCKED_PATTERNS.items():
            if pattern in text:
                failures.append(f"{rel(path)} contains blocked provider/training pattern: {label}")


def validate_architecture_spec(spec: dict[str, Any], failures: list[str]) -> None:
    correction = spec.get("core_correction") if isinstance(spec.get("core_correction"), dict) else {}
    if correction.get("conversation_brain_owner") != "llm":
        failures.append("conversation brain owner must be llm")
    if correction.get("deterministic_layer_is_conversation_brain") is not False:
        failures.append("deterministic layer must not be conversation brain")
    if correction.get("llm_remains_responsible_for_sales_move_selection") is not True:
        failures.append("LLM must remain responsible for sales move selection")
    if correction.get("llm_remains_responsible_for_buyer_facing_phrasing") is not True:
        failures.append("LLM must remain responsible for buyer-facing phrasing")

    heads = spec.get("heads") if isinstance(spec.get("heads"), dict) else {}
    decision = heads.get("conversation_decision_head") if isinstance(heads.get("conversation_decision_head"), dict) else {}
    wording = heads.get("response_wording_head") if isinstance(heads.get("response_wording_head"), dict) else {}
    deterministic = heads.get("deterministic_memory_verifier_layer") if isinstance(heads.get("deterministic_memory_verifier_layer"), dict) else {}
    if decision.get("owner") != "llm":
        failures.append("conversation decision head owner must be llm")
    if wording.get("owner") != "llm":
        failures.append("response wording head owner must be llm")
    if deterministic.get("is_conversation_brain") is not False:
        failures.append("deterministic memory/verifier layer must be documented as non-brain")
    forbidden = " ".join(str(item) for item in deterministic.get("must_not") or [])
    for phrase in ("choose the final sales move", "canned response", "fixed scripted scenario paths"):
        if phrase not in forbidden:
            failures.append(f"deterministic layer forbidden responsibility missing: {phrase}")

    replan = spec.get("replan_loop") if isinstance(spec.get("replan_loop"), dict) else {}
    if replan.get("max_replans") != 1:
        failures.append("replan loop must allow exactly one replan")
    if replan.get("replan_is_llm_request") is not True:
        failures.append("replan must request the LLM, not replace it deterministically")
    if replan.get("deterministic_replacement_used_for_non_critical_issues") is not False:
        failures.append("non-critical issues must not use deterministic replacement")

    boundary = spec.get("live_runtime_boundary") if isinstance(spec.get("live_runtime_boundary"), dict) else {}
    for key in (
        "live_wiring_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "training_rerun",
        "model_or_adapter_weights_committed",
    ):
        if boundary.get(key) is not False:
            failures.append(f"architecture boundary {key} must be false")


def validate_prompt_builder(failures: list[str]) -> None:
    prompt = render_live_action_prompt(
        sanitized_buyer_utterance="I use it for coding workflow and voice.",
        last_agent_response="What would you mainly use it for?",
        memory_ledger_summary={"known_slots": {"use_case": ["coding workflow", "voice"]}},
        approved_campaign_fact_ids=["public_plan_names"],
        approved_campaign_fact_summaries={"public_plan_names": "ChatGPT public plan categories include Free, Plus, and Pro."},
    )
    for phrase in (
        "Return exactly one small JSON object",
        "Required fields: action_id, slots, memory_updates, uncertainty, say",
        "Slots are open",
    ):
        if phrase not in prompt:
            failures.append(f"live action prompt missing instruction: {phrase}")
    if len(prompt) > 4000:
        failures.append("live action prompt builder output is too large for the minimal live-action contract")
    if not allowed_live_action_ids():
        failures.append("allowed live action IDs were not loaded")


def main() -> int:
    failures: list[str] = []
    for path in FILES_TO_SCAN:
        if not path.is_file():
            failures.append(f"missing file: {rel(path)}")

    spec = read_json(ARCHITECTURE_PATH)
    validate_architecture_spec(spec, failures)
    validate_prompt_builder(failures)
    validate_no_blocked_patterns(failures)

    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    files_changed = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files_changed)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed outside approved offline live-action architecture files")
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": EXPERIMENT_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "architecture_spec": rel(ARCHITECTURE_PATH),
        "live_action_contract": rel(LIVE_ACTION_CONTRACT_PATH),
        "anti_loop_memory_contract": rel(ANTI_LOOP_PATH),
        "buyer_facing_uncertainty_policy": rel(UNCERTAINTY_PATH),
        "prompt_builder": rel(PROMPT_PATH),
        "verifier": rel(VERIFIER_PATH),
        "llm_remains_conversation_brain": spec.get("core_correction", {}).get("conversation_brain_owner") == "llm",
        "deterministic_layer_role": spec.get("core_correction", {}).get("deterministic_layer_role"),
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "local_model_calls_made": False,
        "training_rerun": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": runtime_behavior_changed,
        "response_text_changed": response_text_changed,
        "model_or_adapter_weights_committed": bool(tracked),
        "changed_files": files_changed,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        "\n".join(
            [
                f"# {EXPERIMENT_ID}",
                "",
                f"- status: {result['status']}",
                f"- llm_remains_conversation_brain: {str(result['llm_remains_conversation_brain']).lower()}",
                f"- deterministic_layer_role: {result['deterministic_layer_role']}",
                f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
                f"- runtime_behavior_changed: {str(result['runtime_behavior_changed']).lower()}",
                f"- response_text_changed: {str(result['response_text_changed']).lower()}",
                "",
                "## Failures",
                "",
                json.dumps(failures, indent=2, ensure_ascii=False),
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
