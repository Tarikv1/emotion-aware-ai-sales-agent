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

EXPERIMENT_ID = "DIALOGUE-REASONER-004"
RUNNER_PATH = ROOT / "scripts" / "run_dialogue_reasoner_004_async_enrichment.py"
DRY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "dry_run_result.json"
DRY_REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "dry_run_report.md"
MISSING_CONFIG_PATH = ROOT / ".tmp" / EXPERIMENT_ID / "missing_config_result.json"
MISSING_CONFIG_ENV_FILE = ROOT / ".tmp" / EXPERIMENT_ID / "missing_dialogue_reasoner.env"
DOC_PATH = ROOT / "docs" / "product" / "DIALOGUE_REASONER_004_ASYNC_ENRICHMENT.md"
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
    module = importlib.import_module("runtime.core.dialogue_reasoner_async_enrichment")
    for name in [
        "ASYNC_ENRICHMENT_REASONER_ID",
        "async_enrichment_boundary_packet",
        "build_async_enrichment_request",
        "render_async_enrichment_prompt",
        "complete_async_enrichment",
        "response_fingerprint",
    ]:
        assert_condition(hasattr(module, name), f"async enrichment module missing {name}")
    boundary = module.async_enrichment_boundary_packet()
    assert_condition(boundary["reasoner_id"] == EXPERIMENT_ID, boundary)
    assert_condition(boundary["default_enabled"] is False, boundary)
    assert_condition(boundary["customer_response_blocked_on_provider"] is False, boundary)
    assert_condition(boundary["runtime_route_override_allowed"] is False, boundary)
    assert_condition(boundary["mutates_final_response"] is False, boundary)
    assert_condition(boundary["opens_prod_102"] is False, boundary)


def validate_dry_run() -> None:
    assert_condition(RUNNER_PATH.exists(), "DIALOGUE-REASONER-004 runner missing")
    completed = run_command([sys.executable, str(RUNNER_PATH)])
    assert_condition(completed.returncode == 0, {"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]})
    assert_condition(DRY_RESULT_PATH.exists(), "dry-run result missing")
    assert_condition(DRY_REPORT_PATH.exists(), "dry-run report missing")
    payload = read_json(DRY_RESULT_PATH)
    assert_condition(payload["experiment_id"] == EXPERIMENT_ID, "wrong experiment id")
    assert_condition(payload["mode"] == "dry-run", payload["mode"])
    assert_condition(payload["case_count"] == 100, payload["case_count"])
    assert_condition(payload["guard_summary"]["passed_count"] == 30, payload["guard_summary"])
    assert_condition(payload["invocation_gate_summary"]["passed_count"] == 30, payload["invocation_gate_summary"])
    summary = payload["async_enrichment_summary"]
    assert_condition(summary["planned_case_count"] == 40, summary)
    assert_condition(summary["queued_count"] == 40, summary)
    assert_condition(summary["provider_case_count"] == 0, summary)
    assert_condition(summary["completed_count"] == 0, summary)
    assert_condition(summary["failed_count"] == 0, summary)
    assert_condition(summary["deterministic_customer_response_available_before_provider_count"] == 40, summary)
    assert_condition(summary["customer_response_blocked_count"] == 0, summary)
    assert_condition(summary["provider_result_applied_after_response_count"] == 0, summary)
    assert_condition(payload["provider_calls_made"] is False, "dry run must not call provider")
    assert_condition(payload["text_sent_to_provider"] is False, "dry run must not send transcript text")
    assert_condition(payload["api_key_value_logged"] is False, "API key values must not be logged")
    assert_condition(payload["runtime_route_override_allowed"] is False, "LLM must not override runtime route labels")
    assert_condition(payload["live_demo_response_behavior_changed"] is False, "async layer must not alter audible demo behavior")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")
    for record in payload["planned_async_enrichment"]:
        assert_condition(record["status"] == "queued", record)
        assert_condition(record["provider_call_allowed"] is True, record)
        assert_condition(record["provider_call_made"] is False, record)
        assert_condition(record["customer_response_blocked_on_provider"] is False, record)
        assert_condition(record["provider_result_applied_after_response"] is False, record)
        assert_condition(record["runtime_route_override_allowed"] is False, record)
        snapshot = record["customer_response_snapshot"]
        assert_condition(snapshot["available_before_provider"] is True, record)
        assert_condition(snapshot["text_logged"] is False, record)
        assert_condition(bool(snapshot["text_fingerprint"]), record)
        assert_condition(snapshot["char_count"] > 0, record)


def validate_missing_config_live_guard() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--live",
            "--consent-confirmed",
            "--env-file",
            str(MISSING_CONFIG_ENV_FILE),
            "--max-reasoning-cases",
            "1",
            "--out",
            str(MISSING_CONFIG_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, {"stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]})
    payload = read_json(MISSING_CONFIG_PATH)
    assert_condition(payload["mode"] == "live-blocked", payload)
    assert_condition(payload["blocked_reason"] == "missing-provider-config", payload["blocked_reason"])
    assert_condition(payload["provider_calls_made"] is False, "missing config must not call provider")
    assert_condition(payload["text_sent_to_provider"] is False, "missing config must not send transcript text")
    assert_condition(payload["api_key_value_logged"] is False, "missing config must not log API key")
    summary = payload["async_enrichment_summary"]
    assert_condition(summary["planned_case_count"] == 1, summary)
    assert_condition(summary["queued_count"] == 1, summary)
    assert_condition(summary["deterministic_customer_response_available_before_provider_count"] == 1, summary)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert_condition("sk-" not in serialized.lower(), "secret-like key leaked in missing config payload")
    assert_condition(payload["opens_prod_102"] is False, "must not open PROD-102")


def validate_docs_and_manifest() -> None:
    assert_condition(DOC_PATH.exists(), "DIALOGUE-REASONER-004 doc missing")
    doc = read_text(DOC_PATH)
    for fragment in [
        "DIALOGUE-REASONER-004",
        "async enrichment",
        "customer response is not blocked",
        "deterministic routing remains in control",
        "PROD-102 stays closed",
    ]:
        assert_condition(fragment in doc, f"doc missing {fragment}")
    commands = read_text(COMMANDS_PATH)
    assert_condition("run_dialogue_reasoner_004_async_enrichment.py" in commands, "COMMANDS missing DIALOGUE-REASONER-004 runner")
    assert_condition("validate_dialogue_reasoner_004_async_enrichment.py" in commands, "COMMANDS missing DIALOGUE-REASONER-004 validator")
    index = read_text(CHECKPOINT_INDEX)
    assert_condition("DIALOGUE-REASONER-004" in index, "checkpoint index missing DIALOGUE-REASONER-004")
    methodology = read_text(METHODOLOGY_LOG)
    assert_condition("DIALOGUE-REASONER-004" in methodology, "methodology log missing DIALOGUE-REASONER-004")
    manifest = read_json(RUNTIME_MANIFEST)
    paths = {entry.get("path") for entry in manifest.get("runtime_entries", [])}
    assert_condition("runtime/core/dialogue_reasoner_async_enrichment.py" in paths, "runtime manifest missing async enrichment module")


def main() -> None:
    validate_modules()
    validate_dry_run()
    validate_missing_config_live_guard()
    validate_docs_and_manifest()


if __name__ == "__main__":
    main()
