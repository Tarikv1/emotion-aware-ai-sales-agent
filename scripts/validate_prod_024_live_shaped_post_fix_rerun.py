#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_024_live_shaped_post_fix_rerun.py"
RUNNER = ROOT / "scripts" / "run_prod_024_live_shaped_post_fix_rerun.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_024_LIVE_SHAPED_POST_FIX_RERUN.md"
SOURCE_PROD_023_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-023-runtime-policy-call-control-fix" / "result.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-024-live-shaped-post-fix-rerun" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-024-live-shaped-post-fix-rerun" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

CHECKPOINT_ID = "PROD-024-live-shaped-post-fix-rerun"
SOURCE_CHECKPOINT_ID = "PROD-023-runtime-policy-call-control-fix"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    SOURCE_PROD_023_RESULT,
    RESULT_PATH,
    REPORT_PATH,
]

EXPECTED_TURN_COUNT = 19
EXPECTED_CALL_COUNT = 7

BLOCKED_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "credit card",
    "card number",
    "take your payment",
    '"provider_calls_made": true',
    '"private_data_read": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_024_live_shaped_post_fix_rerun.py" in commands, "PROD-024 runner missing from COMMANDS.md")
    assert_condition("validate_prod_024_live_shaped_post_fix_rerun.py" in commands, "PROD-024 validator missing from COMMANDS.md")
    assert_condition("PROD_024_LIVE_SHAPED_POST_FIX_RERUN.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-024 missing from checkpoint index")
    assert_condition("PROD-024-live-shaped-post-fix-rerun" in ROADMAP.read_text(encoding="utf-8"), "PROD-024 missing from roadmap")
    assert_condition("PROD-024 live-shaped post-fix rerun" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-024 missing from methodology log")
    assert_condition("Keep PROD-024 as post-fix evidence gate" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-024 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-024",
            "PROD-023",
            "live-shaped post-fix rerun",
            "policy action correctness: `1.0`",
            "call-control correctness: `1.0`",
            "post-fix gate passed: `true`",
            "legacy PROD-021 gate passed: `false`",
            "close-and-log-sale-ready",
            "keep composer hooks opt-in",
            "retrieval default enabled: `false`",
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_payload(payload: dict[str, Any], source_prod_023: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("source_prod_023_result_path") == str(SOURCE_PROD_023_RESULT.relative_to(ROOT)).replace("\\", "/"), payload.get("source_prod_023_result_path"))
    assert_condition(source_prod_023.get("summary", {}).get("policy_action_correctness") == 1.0, "source PROD-023 must be clean")

    boundaries = payload.get("boundaries", {})
    for key in [
        "provider_calls_made",
        "llm_used",
        "private_data_read",
        "dataset_download_performed",
        "runtime_behavior_changed_by_this_checkpoint",
        "runtime_retrieval_default_enabled",
        "composer_hook_flag_default_enabled",
        "callcenteren_transcript_text_added_to_prompt",
    ]:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("call_count") == EXPECTED_CALL_COUNT, summary)
    assert_condition(summary.get("customer_turn_count") == EXPECTED_TURN_COUNT, summary)
    assert_condition(summary.get("policy_action_correct_count") == EXPECTED_TURN_COUNT, summary)
    assert_condition(summary.get("call_control_correct_count") == EXPECTED_TURN_COUNT, summary)
    assert_condition(summary.get("policy_action_correctness") == 1.0, summary)
    assert_condition(summary.get("call_control_correctness") == 1.0, summary)
    assert_condition(summary.get("protected_context_preservation") == 1.0, summary)
    assert_condition(summary.get("non_sale_correctness") == 1.0, summary)
    assert_condition(summary.get("safe_close_correctness") == 1.0, summary)
    assert_condition(summary.get("state_reference_completeness") == 1.0, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("post_fix_gate_passed") is True, summary)
    assert_condition(summary.get("legacy_prod_021_gate_passed") is False, summary)
    assert_condition(summary.get("runtime_promotion_allowed") is False, summary)
    assert_condition(summary.get("bounded_demo_discussion_allowed") is True, summary)
    assert_condition(summary.get("next_checkpoint_recommended") == "PROD-025-bounded-demo-readiness-packet", summary)

    turn_results = payload.get("post_fix_turn_results", [])
    assert_condition(len(turn_results) == EXPECTED_TURN_COUNT, f"expected {EXPECTED_TURN_COUNT} post-fix turns")
    for turn in turn_results:
        assert_condition(turn.get("policy_action_correct") is True, turn)
        assert_condition(turn.get("call_control_correct") is True, turn)
        assert_condition(turn.get("contains_payment_collection") is False, turn)
        assert_condition(turn.get("hard_failure") is False, turn)
        for key in ["turn_id", "customer_transcript", "post_fix_answer", "post_fix_policy_action", "post_fix_call_control"]:
            assert_condition(turn.get(key) not in (None, ""), f"turn missing {key}")

    calls = payload.get("post_fix_call_results", [])
    assert_condition(len(calls) == EXPECTED_CALL_COUNT, f"expected {EXPECTED_CALL_COUNT} post-fix calls")
    assert_condition(payload.get("decision") == "keep_hooks_opt_in_prepare_bounded_demo_readiness_packet", payload.get("decision"))

    combined = json.dumps(payload, ensure_ascii=False).lower() + "\n" + REPORT_PATH.read_text(encoding="utf-8").lower()
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-024 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    payload = read_json(RESULT_PATH)
    source_prod_023 = read_json(SOURCE_PROD_023_RESULT)
    validate_payload(payload, source_prod_023)
    validate_docs()
    print("PROD-024 live-shaped post-fix rerun validation passed.")


if __name__ == "__main__":
    main()
