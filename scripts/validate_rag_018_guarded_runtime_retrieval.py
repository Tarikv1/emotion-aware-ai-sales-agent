#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GUARDED_RESPONSE = ROOT / "scripts" / "generate_guarded_response.py"
REGISTRY_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-017-runtime-knowledge-registry" / "result.json"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_018_GUARDED_RUNTIME_RETRIEVAL.md"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def ensure_registry() -> None:
    rag016b = run_command([sys.executable, str(ROOT / "scripts" / "run_rag_016b_voice_delivery_decision_slice.py")])
    assert_condition(rag016b.returncode == 0, rag016b.stderr)
    registry = run_command([sys.executable, str(ROOT / "scripts" / "run_rag_017_runtime_knowledge_registry.py")])
    assert_condition(registry.returncode == 0, registry.stderr)


def main() -> None:
    assert_condition(GUARDED_RESPONSE.exists(), "Guarded response script is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-018 product doc is missing.")
    ensure_registry()

    default_run = run_command(
        [
            sys.executable,
            str(GUARDED_RESPONSE),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
            "--cases",
            str(CASES_PATH),
        ]
    )
    assert_condition(default_run.returncode == 0, default_run.stderr)
    default_payload = parse_stdout_json(default_run)
    assert_condition(default_payload["retrieval"]["enabled"] is False, default_payload["retrieval"])
    assert_condition(default_payload["retrieval"]["retrieval_used_in_runtime"] is False, default_payload["retrieval"])

    enabled_run = run_command(
        [
            sys.executable,
            str(GUARDED_RESPONSE),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
            "--cases",
            str(CASES_PATH),
            "--retrieval-enabled",
            "--retrieval-registry",
            str(REGISTRY_PATH),
            "--retrieval-max-results",
            "4",
        ]
    )
    assert_condition(enabled_run.returncode == 0, enabled_run.stderr)
    enabled_payload = parse_stdout_json(enabled_run)
    retrieval = enabled_payload["retrieval"]
    assert_condition(retrieval["status"] == "influenced", retrieval)
    assert_condition(retrieval["retrieval_used_in_runtime"] is True, retrieval)
    assert_condition(retrieval["influenced_response"] is True, retrieval)
    assert_condition(retrieval["retrieved_item_ids"], retrieval)
    assert_condition(retrieval["citation_trace"], retrieval)
    assert_condition(enabled_payload["validation"]["passed"] is True, enabled_payload["validation"])

    blocked_run = run_command(
        [
            sys.executable,
            str(GUARDED_RESPONSE),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            "Bitte rufen Sie mich nicht mehr an.",
            "--cases",
            str(CASES_PATH),
            "--retrieval-enabled",
            "--retrieval-registry",
            str(REGISTRY_PATH),
        ]
    )
    assert_condition(blocked_run.returncode == 0, blocked_run.stderr)
    blocked_payload = parse_stdout_json(blocked_run)
    blocked = blocked_payload["retrieval"]
    assert_condition(blocked["status"] == "blocked", blocked)
    assert_condition(blocked["retrieval_used_in_runtime"] is False, blocked)
    assert_condition(blocked["retrieved_item_ids"] == [], blocked)

    combined_text = (default_run.stdout + enabled_run.stdout + blocked_run.stdout).lower().replace("\\", "/")
    assert_condition("data/private" not in combined_text, "Private path leaked.")
    assert_condition('"source_excerpt_text":' not in combined_text, "Source excerpt field leaked.")
    for phrase in ("you are anxious", "you are angry", "i can tell you feel"):
        assert_condition(phrase not in combined_text, f"Hidden-emotion claim leaked: {phrase}")

    print("RAG-018 guarded runtime retrieval validation passed.")


if __name__ == "__main__":
    main()
