#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_023_runtime_policy_call_control_fix.py"
RUNNER = ROOT / "scripts" / "run_prod_023_runtime_policy_call_control_fix.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_023_RUNTIME_POLICY_CALL_CONTROL_FIX.md"
SOURCE_GAP_PACKET = ROOT / "research" / "experiments" / "generated" / "PROD-022-prod-021-review-gap-packet" / "result.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-023-runtime-policy-call-control-fix" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-023-runtime-policy-call-control-fix" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

CHECKPOINT_ID = "PROD-023-runtime-policy-call-control-fix"
SOURCE_CHECKPOINT_ID = "PROD-022-prod-021-review-gap-packet"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    SOURCE_GAP_PACKET,
    RESULT_PATH,
    REPORT_PATH,
]

EXPECTED_FIXED_GAP_IDS = {
    "PROD-021-C01-T01",
    "PROD-021-C01-T02",
    "PROD-021-C01-T03",
    "PROD-021-C01-T04",
    "PROD-021-C02-T01",
    "PROD-021-C02-T02",
    "PROD-021-C02-T03",
    "PROD-021-C07-T01",
    "PROD-021-C07-T02",
    "PROD-021-C07-T03",
}

EXPECTED_POLICY_ACTIONS = {
    "PROD-021-C01-T01": "value-clarify",
    "PROD-021-C01-T02": "fair-compare",
    "PROD-021-C01-T03": "autonomy-check",
    "PROD-021-C01-T04": "close-and-log-sale-ready",
    "PROD-021-C02-T01": "stakeholder-review",
    "PROD-021-C02-T02": "procurement-review",
    "PROD-021-C02-T03": "procurement-review",
    "PROD-021-C07-T01": "trust-repair",
    "PROD-021-C07-T02": "value-clarify",
    "PROD-021-C07-T03": "autonomy-check",
}

EXPECTED_CALL_CONTROLS = {
    "PROD-021-C01-T04": "close-and-log-sale-ready",
    "PROD-021-C02-T02": "continue-call",
    "PROD-021-C02-T03": "continue-call",
}

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
    assert_condition("run_prod_023_runtime_policy_call_control_fix.py" in commands, "PROD-023 runner missing from COMMANDS.md")
    assert_condition("validate_prod_023_runtime_policy_call_control_fix.py" in commands, "PROD-023 validator missing from COMMANDS.md")
    assert_condition("PROD_023_RUNTIME_POLICY_CALL_CONTROL_FIX.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-023 missing from checkpoint index")
    assert_condition("PROD-023" in ROADMAP.read_text(encoding="utf-8"), "PROD-023 missing from roadmap")
    assert_condition("PROD-023 runtime-policy and call-control fix" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-023 missing from methodology log")
    assert_condition("Keep PROD-023 as local runtime-policy fix" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-023 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-023",
            "runtime-policy",
            "call-control",
            "PROD-022",
            "policy action correctness: `1.0`",
            "call-control correctness: `1.0`",
            "close-and-log-sale-ready",
            "keep composer hooks opt-in",
            "retrieval default enabled: `false`",
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_payload(payload: dict[str, Any], source_packet: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("source_gap_packet_path") == str(SOURCE_GAP_PACKET.relative_to(ROOT)).replace("\\", "/"), payload.get("source_gap_packet_path"))

    boundaries = payload.get("boundaries", {})
    assert_condition(boundaries.get("runtime_policy_changed") is True, boundaries)
    for key in [
        "provider_calls_made",
        "llm_used",
        "private_data_read",
        "dataset_download_performed",
        "runtime_retrieval_default_enabled",
        "composer_hook_flag_default_enabled",
        "callcenteren_transcript_text_added_to_prompt",
    ]:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("source_gap_turn_count") == source_packet.get("summary", {}).get("gap_turn_count") == 10, summary)
    assert_condition(summary.get("fixed_gap_turn_count") == 10, summary)
    assert_condition(summary.get("closed_policy_action_miss_count") == 10, summary)
    assert_condition(summary.get("closed_call_control_miss_count") == 3, summary)
    assert_condition(summary.get("remaining_policy_action_miss_count") == 0, summary)
    assert_condition(summary.get("remaining_call_control_miss_count") == 0, summary)
    assert_condition(summary.get("policy_action_correctness") == 1.0, summary)
    assert_condition(summary.get("call_control_correctness") == 1.0, summary)
    assert_condition(summary.get("protected_context_preservation") == 1.0, summary)
    assert_condition(summary.get("non_sale_correctness") == 1.0, summary)
    assert_condition(summary.get("safe_close_correctness") == 1.0, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("runtime_promotion_allowed") is False, summary)
    assert_condition(summary.get("next_checkpoint_recommended") == "PROD-024-live-shaped-post-fix-rerun", summary)

    fixed_turns = payload.get("fixed_gap_turns", [])
    assert_condition({turn.get("turn_id") for turn in fixed_turns} == EXPECTED_FIXED_GAP_IDS, "unexpected fixed gap turn set")
    for turn in fixed_turns:
        turn_id = turn["turn_id"]
        assert_condition(turn.get("policy_action_correct") is True, turn)
        assert_condition(turn.get("call_control_correct") is True, turn)
        assert_condition(turn.get("post_fix_policy_action") == EXPECTED_POLICY_ACTIONS[turn_id], turn)
        if turn_id in EXPECTED_CALL_CONTROLS:
            assert_condition(turn.get("post_fix_call_control") == EXPECTED_CALL_CONTROLS[turn_id], turn)
        assert_condition(turn.get("contains_payment_collection") is False, turn)
        assert_condition(turn.get("hard_failure") is False, turn)
        for key in ["customer_transcript", "post_fix_answer", "source_miss_policy_action", "source_miss_call_control"]:
            assert_condition(turn.get(key) not in (None, ""), f"{turn_id} missing {key}")

    changed = {item.get("surface_id") for item in payload.get("changed_surfaces", [])}
    assert_condition(
        {"runtime_input_classifier", "call_control_contract", "runtime_policy_action_mapping"} <= changed,
        changed,
    )

    combined = json.dumps(payload, ensure_ascii=False).lower() + "\n" + REPORT_PATH.read_text(encoding="utf-8").lower()
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-023 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    payload = read_json(RESULT_PATH)
    source_packet = read_json(SOURCE_GAP_PACKET)
    validate_payload(payload, source_packet)
    validate_docs()
    print("PROD-023 runtime-policy and call-control fix validation passed.")


if __name__ == "__main__":
    main()
