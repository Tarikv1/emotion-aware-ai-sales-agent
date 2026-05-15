#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_022_prod_021_review_gap_packet.py"
RUNNER = ROOT / "scripts" / "run_prod_022_prod_021_review_gap_packet.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_022_PROD_021_REVIEW_GAP_PACKET.md"
SOURCE_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-021-live-shaped-dialogue-policy-simulation" / "result.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-022-prod-021-review-gap-packet" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-022-prod-021-review-gap-packet" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

CHECKPOINT_ID = "PROD-022-prod-021-review-gap-packet"
SOURCE_CHECKPOINT_ID = "PROD-021-live-shaped-dialogue-policy-simulation"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    SOURCE_RESULT,
    RESULT_PATH,
    REPORT_PATH,
]

REQUIRED_GAP_CATEGORIES = {
    "policy_action_router_gap",
    "call_control_sale_ready_gap",
    "call_control_procurement_delay_gap",
}

REQUIRED_FIX_TARGETS = {
    "runtime_policy_router_specialization",
    "sale_ready_call_control_detector",
    "procurement_review_continuation_guard",
    "keep_composer_hooks_opt_in",
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
    '"runtime_behavior_changed": true',
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
    assert_condition("run_prod_022_prod_021_review_gap_packet.py" in commands, "PROD-022 runner missing from COMMANDS.md")
    assert_condition("validate_prod_022_prod_021_review_gap_packet.py" in commands, "PROD-022 validator missing from COMMANDS.md")
    assert_condition("PROD_022_PROD_021_REVIEW_GAP_PACKET.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-022 missing from checkpoint index")
    assert_condition("PROD-022" in ROADMAP.read_text(encoding="utf-8"), "PROD-022 missing from roadmap")
    assert_condition("PROD-022 PROD-021 review gap packet" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-022 missing from methodology log")
    assert_condition("Keep PROD-021 hooks opt-in after review" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-022 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-022",
            "PROD-021",
            "review gap packet",
            "exact customer turn",
            "exact agent answer",
            "policy action miss",
            "call-control miss",
            "keep composer hooks opt-in",
            "no runtime behavior change",
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_payload(payload: dict[str, Any], source_payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("source_result_path") == str(SOURCE_RESULT.relative_to(ROOT)).replace("\\", "/"), payload.get("source_result_path"))

    boundaries = payload.get("boundaries", {})
    for key in [
        "provider_calls_made",
        "llm_used",
        "private_data_read",
        "dataset_download_performed",
        "runtime_behavior_changed",
        "runtime_retrieval_default_enabled",
        "composer_hook_flag_default_enabled",
        "commercial_runtime_prompt_text_changed",
    ]:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    source_summary = source_payload.get("summary", {})
    assert_condition(summary.get("source_customer_turn_count") == source_summary.get("customer_turn_count") == 19, summary)
    assert_condition(summary.get("source_policy_action_correctness") == source_summary.get("policy_action_correctness") == 0.7368, summary)
    assert_condition(summary.get("source_call_control_correctness") == source_summary.get("call_control_correctness") == 0.7895, summary)
    assert_condition(summary.get("gap_turn_count") == 6, summary)
    assert_condition(summary.get("policy_action_miss_count") == 5, summary)
    assert_condition(summary.get("call_control_miss_count") == 4, summary)
    assert_condition(summary.get("protected_context_gap_count") == 1, summary)
    assert_condition(summary.get("hook_gain_turn_count") == 0, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("runtime_promotion_allowed") is False, summary)
    assert_condition(summary.get("next_checkpoint_recommended") == "PROD-023-runtime-policy-call-control-fix", summary)

    categories = {item.get("category_id") for item in payload.get("gap_categories", [])}
    assert_condition(REQUIRED_GAP_CATEGORIES <= categories, f"missing gap categories: {sorted(REQUIRED_GAP_CATEGORIES - categories)}")

    targets = {item.get("target_id") for item in payload.get("fix_targets", [])}
    assert_condition(REQUIRED_FIX_TARGETS <= targets, f"missing fix targets: {sorted(REQUIRED_FIX_TARGETS - targets)}")

    gap_turns = payload.get("gap_turns", [])
    assert_condition(len(gap_turns) == summary.get("gap_turn_count"), "gap turn count mismatch")
    call_control_misses = [turn for turn in gap_turns if turn.get("call_control_correct") is False]
    assert_condition(len(call_control_misses) == 4, call_control_misses)
    expected_gap_ids = {
        "PROD-021-C01-T02",
        "PROD-021-C01-T04",
        "PROD-021-C02-T01",
        "PROD-021-C03-T01",
        "PROD-021-C07-T01",
        "PROD-021-C07-T03",
    }
    assert_condition({turn.get("turn_id") for turn in gap_turns} == expected_gap_ids, "unexpected gap turn set")

    for turn in gap_turns:
        for key in [
            "turn_id",
            "scenario_label",
            "customer_transcript",
            "expected_policy_action",
            "opt_in_runtime_policy_action",
            "expected_call_control",
            "opt_in_call_control",
            "default_off_answer",
            "retrieval_only_answer",
            "opt_in_answer",
            "recommended_fix_target",
            "why_it_matters",
        ]:
            assert_condition(turn.get(key) not in (None, ""), f"{turn.get('turn_id')} missing {key}")
        if turn.get("turn_id") != "PROD-021-C03-T01":
            assert_condition(turn.get("protected_context") is False, turn)
        assert_condition(turn.get("contains_payment_collection") is False, turn)
        assert_condition(turn.get("hard_failure") is False, turn)

    prioritized = payload.get("prioritized_next_actions", [])
    assert_condition(len(prioritized) >= 3, prioritized)
    assert_condition(prioritized[0].get("target_id") == "runtime_policy_router_specialization", prioritized)
    assert_condition("not hooks" in prioritized[0].get("rationale", "").lower(), prioritized[0])

    combined = json.dumps(payload, ensure_ascii=False).lower() + "\n" + REPORT_PATH.read_text(encoding="utf-8").lower()
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-022 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    payload = read_json(RESULT_PATH)
    source_payload = read_json(SOURCE_RESULT)
    validate_payload(payload, source_payload)
    validate_docs()
    print("PROD-022 PROD-021 review gap packet validation passed.")


if __name__ == "__main__":
    main()
