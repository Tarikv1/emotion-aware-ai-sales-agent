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

EXPERIMENT_ID = "DIALOGUE-REASONER-003"
RUNNER_PATH = ROOT / "scripts" / "run_dialogue_reasoner_003_hybrid_gate.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "dialogue-reasoner-003-hybrid-gate.json"
DRY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "dry_run_result.json"
DRY_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "dry_run_report.md"
MISSING_CONFIG_PATH = ROOT / ".tmp" / EXPERIMENT_ID / "missing_config_result.json"
MISSING_CONFIG_ENV_FILE = ROOT / ".tmp" / EXPERIMENT_ID / "missing_dialogue_reasoner.env"
DOC_PATH = ROOT / "docs" / "product" / "DIALOGUE_REASONER_003_HYBRID_GATE_EVALUATION.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
RUNTIME_MANIFEST = ROOT / "runtime" / "runtime_manifest.json"


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
    module = importlib.import_module("runtime.core.dialogue_reasoner_hybrid")
    for name in [
        "HYBRID_REASONING_SCHEMA_FIELDS",
        "should_call_llm_reasoning",
        "render_hybrid_reasoning_prompt",
        "validate_hybrid_reasoning_packet",
        "score_hybrid_reasoning_case",
    ]:
        assert_condition(hasattr(module, name), f"hybrid module missing {name}")
    assert_condition("dialogue_act" not in module.HYBRID_REASONING_SCHEMA_FIELDS, "LLM reasoning schema must not own dialogue_act")
    assert_condition("sales_stage" not in module.HYBRID_REASONING_SCHEMA_FIELDS, "LLM reasoning schema must not own sales_stage")


def validate_case_file() -> None:
    assert_condition(CASES_PATH.exists(), "DIALOGUE-REASONER-003 cases missing")
    payload = read_json(CASES_PATH)
    assert_condition(payload["experiment_id"] == EXPERIMENT_ID, "wrong case experiment id")
    assert_condition(payload["guard_case_source"].endswith("dialogue-reasoner-001-live-demo-failures.json"), "wrong guard source")
    invocation = payload["invocation_gate_cases"]
    reasoning = payload["reasoning_quality_cases"]
    assert_condition(len(invocation) == 30, f"expected 30 invocation cases, got {len(invocation)}")
    assert_condition(len(reasoning) == 40, f"expected 40 reasoning cases, got {len(reasoning)}")
    blocked = [case for case in invocation if case["expected_provider_call_allowed"] is False]
    allowed = [case for case in invocation if case["expected_provider_call_allowed"] is True]
    assert_condition(len(blocked) == 15, f"expected 15 blocked invocation cases, got {len(blocked)}")
    assert_condition(len(allowed) == 15, f"expected 15 allowed invocation cases, got {len(allowed)}")
    for case in invocation + reasoning:
        assert_condition("case_id" in case and case["case_id"], f"case missing id: {case}")
        assert_condition("transcript" in case and case["transcript"], f"case missing transcript: {case}")
        assert_condition(isinstance(case.get("prior_turns", []), list), f"case prior_turns must be a list: {case['case_id']}")


def validate_dry_run() -> None:
    assert_condition(RUNNER_PATH.exists(), "DIALOGUE-REASONER-003 runner missing")
    completed = run_command([sys.executable, str(RUNNER_PATH)])
    assert_condition(completed.returncode == 0, {"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]})
    assert_condition(DRY_RESULT_PATH.exists(), "dry-run result missing")
    assert_condition(DRY_REPORT_PATH.exists(), "dry-run report missing")
    payload = read_json(DRY_RESULT_PATH)
    assert_condition(payload["experiment_id"] == EXPERIMENT_ID, "wrong experiment id")
    assert_condition(payload["mode"] == "dry-run", "default mode must be dry-run")
    assert_condition(payload["case_count"] == 100, payload["case_count"])
    assert_condition(payload["guard_summary"]["passed_count"] == 30, payload["guard_summary"])
    assert_condition(payload["guard_summary"]["case_count"] == 30, payload["guard_summary"])
    assert_condition(payload["invocation_gate_summary"]["passed_count"] == 30, payload["invocation_gate_summary"])
    assert_condition(payload["invocation_gate_summary"]["case_count"] == 30, payload["invocation_gate_summary"])
    assert_condition(payload["reasoning_quality_summary"]["planned_case_count"] == 40, payload["reasoning_quality_summary"])
    assert_condition(payload["reasoning_quality_summary"]["provider_case_count"] == 0, payload["reasoning_quality_summary"])
    blocked_reasoning = [case["case_id"] for case in payload["planned_reasoning_cases"] if case["provider_call_allowed"] is not True]
    assert_condition(not blocked_reasoning, {"reasoning_cases_not_provider_eligible": blocked_reasoning})
    assert_condition(payload["provider_calls_made"] is False, "dry run must not call provider")
    assert_condition(payload["text_sent_to_provider"] is False, "dry run must not send transcript text")
    assert_condition(payload["api_key_value_logged"] is False, "API key values must not be logged")
    assert_condition(payload["live_demo_response_behavior_changed"] is False, "hybrid eval must not alter live-demo response behavior")
    assert_condition(payload["runtime_route_override_allowed"] is False, "LLM must not override runtime route labels")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")


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
    assert_condition(completed.returncode == 0, {"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]})
    payload = read_json(MISSING_CONFIG_PATH)
    assert_condition(payload["mode"] == "live-blocked", payload)
    assert_condition(payload["blocked_reason"] == "missing-provider-config", payload["blocked_reason"])
    assert_condition(payload["guard_summary"]["passed_count"] == 30, payload["guard_summary"])
    assert_condition(payload["invocation_gate_summary"]["passed_count"] == 30, payload["invocation_gate_summary"])
    assert_condition(payload["provider_calls_made"] is False, "missing config must not call provider")
    assert_condition(payload["text_sent_to_provider"] is False, "missing config must not send transcript text")
    assert_condition(payload["api_key_value_logged"] is False, "missing config must not log API key")
    serialized = json.dumps(payload, ensure_ascii=False)
    assert_condition("sk-" not in serialized.lower(), "secret-like key leaked in missing config payload")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")


def validate_docs_and_manifest() -> None:
    assert_condition(DOC_PATH.exists(), "DIALOGUE-REASONER-003 doc missing")
    doc = read_text(DOC_PATH)
    for fragment in [
        "DIALOGUE-REASONER-003",
        "hybrid gate",
        "30 guard",
        "30 invocation",
        "40 reasoning",
        "PROD-102 stays closed",
    ]:
        assert_condition(fragment in doc, f"doc missing {fragment}")
    commands = read_text(COMMANDS_PATH)
    assert_condition("run_dialogue_reasoner_003_hybrid_gate.py" in commands, "COMMANDS missing DIALOGUE-REASONER-003 runner")
    assert_condition("validate_dialogue_reasoner_003_hybrid_gate.py" in commands, "COMMANDS missing DIALOGUE-REASONER-003 validator")
    index = read_text(CHECKPOINT_INDEX)
    assert_condition("DIALOGUE-REASONER-003" in index, "checkpoint index missing DIALOGUE-REASONER-003")
    methodology = read_text(METHODOLOGY_LOG)
    assert_condition("DIALOGUE-REASONER-003" in methodology, "methodology log missing DIALOGUE-REASONER-003")
    manifest = read_json(RUNTIME_MANIFEST)
    paths = {entry.get("path") for entry in manifest.get("runtime_entries", [])}
    assert_condition("runtime/core/dialogue_reasoner_hybrid.py" in paths, "runtime manifest missing hybrid reasoner")


def main() -> None:
    validate_modules()
    validate_case_file()
    validate_dry_run()
    validate_missing_config_live_guard()
    validate_docs_and_manifest()


if __name__ == "__main__":
    main()
