#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "DIALOGUE-REASONER-002"
RUNNER_PATH = ROOT / "scripts" / "run_dialogue_reasoner_002_provider_evaluation.py"
DRY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "dry_run_result.json"
DRY_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "dry_run_report.md"
MISSING_CONFIG_PATH = ROOT / ".tmp" / EXPERIMENT_ID / "missing_config_result.json"
MISSING_CONFIG_ENV_FILE = ROOT / ".tmp" / EXPERIMENT_ID / "missing_dialogue_reasoner.env"
DOC_PATH = ROOT / "docs" / "product" / "DIALOGUE_REASONER_002_LLM_PROVIDER_EVALUATION.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
RUNTIME_MANIFEST = ROOT / "runtime" / "runtime_manifest.json"
ENV_EXAMPLE_PATH = ROOT / "runtime" / "config" / "local" / "dialogue_reasoner.env.example"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in [
        "DIALOGUE_REASONER_API_KEY",
        "DIALOGUE_REASONER_BASE_URL",
        "DIALOGUE_REASONER_MODEL",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "TOGETHER_API_KEY",
        "GROQ_API_KEY",
    ]:
        env.pop(name, None)
    return env


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, env=safe_env(), text=True, capture_output=True, check=False, timeout=240)


def validate_modules() -> None:
    client = importlib.import_module("runtime.providers.dialogue_reasoner_llm_client")
    reasoner = importlib.import_module("runtime.core.dialogue_reasoner")
    for name in [
        "OpenAICompatibleReasonerConfig",
        "build_chat_completions_payload",
        "call_openai_compatible_reasoner",
        "missing_provider_config",
        "normalize_chat_completions_url",
        "redacted_provider_config",
    ]:
        assert_condition(hasattr(client, name), f"provider client missing {name}")
    assert_condition(
        client.normalize_chat_completions_url("http://127.0.0.1:9/v1") == "http://127.0.0.1:9/v1/chat/completions",
        "provider base URL should normalize to chat completions endpoint",
    )
    assert_condition(
        client.normalize_chat_completions_url("http://127.0.0.1:9/v1/chat/completions")
        == "http://127.0.0.1:9/v1/chat/completions",
        "full chat completions URL should stay stable",
    )
    prompt = reasoner.render_strict_json_reasoner_prompt(
        reasoner.build_reasoning_context("__agent_open__", {}, {"language": "en"})
    )
    assert_condition(
        "Classify the current runtime turn" in prompt,
        "provider prompt must not describe every input as a buyer turn",
    )
    assert_condition(
        "__agent_open__ is an internal agent-open sentinel" in prompt,
        "provider prompt must explain the internal agent-open sentinel",
    )
    assert_condition(
        "buyer_intent=start_call" in prompt and "resolved_topic=qualification" in prompt,
        "provider prompt must pin the expected agent-open taxonomy labels",
    )
    for fragment in [
        "Runtime label policy:",
        "Opening greetings resolve to resolved_topic=qualification",
        "Clarification, caller identity, ambiguous negatives, and ASR repairs use sales_stage=repair",
        "Boundary questions use sales_stage=boundary and guarded boundary labels",
        "Use context.resolved_focus to preserve continuity",
        "Topic shifts from an existing focus use dialogue_act=topic_shift and buyer_intent=change_topic",
        "Low-information acknowledgements use response_strategy=proactive_guided_selling",
        "ASR fragments use resolved_topic=asr_quality and safety_boundary=asr_quality_boundary",
    ]:
        assert_condition(fragment in prompt, f"provider prompt missing runtime label policy: {fragment}")


def validate_dry_run() -> None:
    assert_condition(RUNNER_PATH.exists(), "DIALOGUE-REASONER-002 runner missing")
    completed = run_command([sys.executable, str(RUNNER_PATH)])
    assert_condition(
        completed.returncode == 0,
        {"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]},
    )
    assert_condition(DRY_RESULT_PATH.exists(), "dry-run result missing")
    assert_condition(DRY_REPORT_PATH.exists(), "dry-run report missing")
    payload = read_json(DRY_RESULT_PATH)
    assert_condition(payload["experiment_id"] == EXPERIMENT_ID, "wrong experiment id")
    assert_condition(payload["mode"] == "dry-run", "default mode must be dry-run")
    assert_condition(payload["case_count"] == 30, "must evaluate the frozen 30 DIALOGUE-REASONER-001 cases")
    assert_condition(payload["planned_provider_call_count"] == 30, "planned provider call count mismatch")
    assert_condition(payload["provider_calls_made"] is False, "dry run must not call provider")
    assert_condition(payload["text_sent_to_provider"] is False, "dry run must not send transcript text")
    assert_condition(payload["api_key_value_logged"] is False, "API key values must not be logged")
    assert_condition(payload["env_file"]["values_logged"] is False, "env file values must not be logged")
    assert_condition(payload["live_demo_response_behavior_changed"] is False, "provider eval must not change live-demo behavior")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")
    assert_condition(payload["default_live_enabled"] is False, "live provider evaluation must be default-off")
    assert_condition(payload["blocked_reason"] == "dry-run-mode", payload["blocked_reason"])
    assert_condition(payload["llm_results"] == [], "dry run must not fabricate LLM results")
    assert_condition(payload["baseline_reference"]["experiment_id"] == "DIALOGUE-REASONER-001", "missing baseline reference")
    assert_condition(payload["baseline_reference"]["passed_count"] == 30, "baseline reference should be 30/30")


def validate_missing_config_live_guard() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--live",
            "--consent-confirmed",
            "--env-file",
            str(MISSING_CONFIG_ENV_FILE),
            "--out",
            str(MISSING_CONFIG_PATH),
        ]
    )
    assert_condition(
        completed.returncode == 0,
        {"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]},
    )
    payload = read_json(MISSING_CONFIG_PATH)
    assert_condition(payload["mode"] == "live-blocked", payload)
    assert_condition(payload["provider_calls_made"] is False, "missing config must not call provider")
    assert_condition(payload["text_sent_to_provider"] is False, "missing config must not send transcript text")
    assert_condition(payload["api_key_value_logged"] is False, "missing config must not log API key")
    assert_condition(payload["env_file"]["values_logged"] is False, "env file values must not be logged")
    assert_condition(payload["blocked_reason"] == "missing-provider-config", payload["blocked_reason"])
    assert_condition("api_key" in payload["missing_config"], payload["missing_config"])
    assert_condition("base_url" in payload["missing_config"], payload["missing_config"])
    assert_condition("model" in payload["missing_config"], payload["missing_config"])
    serialized = json.dumps(payload, ensure_ascii=False)
    assert_condition("sk-" not in serialized.lower(), "secret-like key leaked in missing config payload")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")


def validate_docs_and_manifest() -> None:
    assert_condition(DOC_PATH.exists(), "DIALOGUE-REASONER-002 doc missing")
    assert_condition(ENV_EXAMPLE_PATH.exists(), "dialogue reasoner env example missing")
    env_example = read_text(ENV_EXAMPLE_PATH)
    for name in ["DIALOGUE_REASONER_API_KEY=", "DIALOGUE_REASONER_BASE_URL=", "DIALOGUE_REASONER_MODEL="]:
        assert_condition(name in env_example, f"env example missing {name}")
    doc = read_text(DOC_PATH)
    for fragment in [
        "DIALOGUE-REASONER-002",
        "runtime/config/local/dialogue_reasoner.env",
        "DIALOGUE_REASONER_API_KEY",
        "DIALOGUE_REASONER_BASE_URL",
        "DIALOGUE_REASONER_MODEL",
        "--live",
        "--consent-confirmed",
        "PROD-102 stays closed",
    ]:
        assert_condition(fragment in doc, f"doc missing {fragment}")

    commands = read_text(COMMANDS_PATH)
    assert_condition("run_dialogue_reasoner_002_provider_evaluation.py" in commands, "COMMANDS missing runner")
    assert_condition("validate_dialogue_reasoner_002_provider_evaluation.py" in commands, "COMMANDS missing validator")

    methodology = read_text(METHODOLOGY_LOG)
    assert_condition("DIALOGUE-REASONER-002" in methodology, "methodology log missing DIALOGUE-REASONER-002")

    manifest = read_json(RUNTIME_MANIFEST)
    paths = {entry.get("path") for entry in manifest.get("runtime_entries", [])}
    assert_condition("runtime/providers/dialogue_reasoner_llm_client.py" in paths, "runtime manifest missing provider client")


def main() -> None:
    validate_modules()
    validate_dry_run()
    validate_missing_config_live_guard()
    validate_docs_and_manifest()


if __name__ == "__main__":
    main()
