#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-031-interactive-grounded-call-simulation"
SOURCE_SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-05-09-interactive-grounded-call-simulation-design.md"
NEXT_CHECKPOINT_ID = "PROD-032-interactive-simulation-review"

MODULE = ROOT / "scripts" / "prod_031_interactive_grounded_call_simulation.py"
RUNNER = ROOT / "scripts" / "run_prod_031_interactive_grounded_call_simulation.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TRACE_PATH = OUT_DIR / "interactive_call_traces.json"
HTML_PATH = OUT_DIR / "interactive_call_trace.html"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_FILES = [
    SOURCE_SPEC,
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    TRACE_PATH,
    HTML_PATH,
]

REQUIRED_FALSE_BOUNDARIES = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "raw_transcript_text_stored",
    "copied_transcript_text_used",
    "commercial_runtime_prompt_text_from_transcripts_allowed",
    "customer_data_allowed",
    "payment_collection_enabled",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "production_runtime_promotion_allowed",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "take your payment",
    "card number",
    "credit card number",
    '"provider_calls_made": true',
    '"llm_used": true',
    '"private_data_read": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))
    assert_condition(payload.get("source_spec_path") == normalized(SOURCE_SPEC), payload.get("source_spec_path"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("trace_path") == normalized(TRACE_PATH), outputs)
    assert_condition(outputs.get("html_path") == normalized(HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("deterministic_simulator") is True, summary)
    assert_condition(summary.get("call_seed_count") >= 8, summary)
    assert_condition(summary.get("call_count") >= 8, summary)
    assert_condition(summary.get("total_turn_count") >= 24, summary)
    assert_condition(summary.get("reactive_customer_turn_count") >= 16, summary)
    assert_condition(summary.get("reactive_state_transition_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("exact_customer_agent_state_trace_visible") is True, summary)
    assert_condition(summary.get("agent_answer_depends_on_customer_state") is True, summary)
    assert_condition(summary.get("customer_reply_depends_on_prior_agent_answer") is True, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("question_overuse_count") <= 2, summary)
    assert_condition(summary.get("interactive_realism_score") >= 0.75, summary)
    assert_condition(summary.get("safe_close_rate") >= 0.75, summary)
    assert_condition(summary.get("non_sale_correctness") == 1.0, summary)

    metrics = payload.get("metrics", {})
    for metric in [
        "safe_close_rate",
        "non_sale_correctness",
        "average_trust_delta",
        "average_interest_delta",
        "average_clarity_delta",
        "average_friction_delta",
        "interactive_realism_score",
        "hard_failure_rate",
        "question_overuse_rate",
    ]:
        assert_condition(metric in metrics, f"missing metric {metric}")
        assert_condition(isinstance(metrics[metric].get("value"), (int, float)), metrics[metric])

    traces = read_json(TRACE_PATH)
    assert_condition(traces.get("checkpoint_id") == CHECKPOINT_ID, traces.get("checkpoint_id"))
    calls = traces.get("calls", [])
    assert_condition(len(calls) == summary.get("call_count"), "call count mismatch")
    for call in calls:
        assert_condition(call.get("seed_id"), call)
        assert_condition(call.get("terminal_outcome"), call)
        assert_condition(call.get("turns"), call)
        assert_condition(len(call["turns"]) <= 8, call)
        first_turn_seen = False
        for turn in call["turns"]:
            assert_condition("customer_message" in turn, turn)
            assert_condition("agent_answer" in turn, turn)
            assert_condition("state_before" in turn, turn)
            assert_condition("state_after" in turn, turn)
            assert_condition("customer_reaction_reason" in turn, turn)
            assert_condition("state_delta" in turn, turn)
            assert_condition("safety_flags" in turn, turn)
            assert_condition(turn["safety_flags"]["hard_failure"] is False, turn)
            if first_turn_seen:
                assert_condition(turn.get("reactive_to_previous_agent_answer") is True, turn)
            first_turn_seen = True

    html = HTML_PATH.read_text(encoding="utf-8")
    for marker in [
        "PROD-031 Interactive Grounded Call Simulation",
        "customer state -> customer turn -> agent answer -> customer state changes -> reactive customer turn",
        "State before",
        "State after",
        "Reaction reason",
    ]:
        assert_condition(marker in html, marker)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_031_interactive_grounded_call_simulation.py" in commands, "PROD-031 runner missing from COMMANDS.md")
    assert_condition("validate_prod_031_interactive_grounded_call_simulation.py" in commands, "PROD-031 validator missing from COMMANDS.md")
    assert_condition("PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-031 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-031 missing from roadmap")
    assert_condition("PROD-031 interactive grounded call simulation" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-031 missing from methodology log")
    assert_condition("Keep PROD-031 as interactive evaluation evidence" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-031 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-031",
            "interactive grounded call simulation",
            "deterministic simulator: `true`",
            "call seed count:",
            "reactive customer turn count:",
            "customer reply depends on prior agent answer: `true`",
            "provider calls made: `false`",
            "runtime behavior changed: `false`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-031 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-031 interactive grounded call simulation validation passed.")


if __name__ == "__main__":
    main()
