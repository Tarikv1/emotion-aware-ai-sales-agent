#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_021_live_shaped_dialogue_policy_simulation.py"
RUNNER = ROOT / "scripts" / "run_prod_021_live_shaped_dialogue_policy_simulation.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_021_LIVE_SHAPED_DIALOGUE_POLICY_SIMULATION.md"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "prod-021-live-shaped-dialogue-policy-simulation.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-021-live-shaped-dialogue-policy-simulation" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "PROD-021-live-shaped-dialogue-policy-simulation" / "report.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"
AGENTS = ROOT / "AGENTS.md"

CHECKPOINT_ID = "PROD-021-live-shaped-dialogue-policy-simulation"
SOURCE_PROD_011 = "PROD-011-dialogue-policy-hardening"
SOURCE_PROD_020 = "PROD-020-naturalized-customer-turn-evaluation"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    CASE_PATH,
    RESULT_PATH,
    REPORT_PATH,
]

REQUIRED_LABELS = {
    "software_multi_objection_sale",
    "software_procurement_authority_delay",
    "insurance_claim_privacy_escalation",
    "medical_technical_safety_escalation",
    "membership_refusal_end_call",
    "home_service_support_handoff",
    "trust_price_callback",
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
    '"dataset_download_performed": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rate_is_one(payload: dict[str, Any], key: str) -> None:
    assert_condition(payload.get(key) == 1.0, f"{key} must be 1.0, got {payload.get(key)!r}")


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_021_live_shaped_dialogue_policy_simulation.py" in commands, "PROD-021 runner missing from COMMANDS.md")
    assert_condition("validate_prod_021_live_shaped_dialogue_policy_simulation.py" in commands, "PROD-021 validator missing from COMMANDS.md")
    assert_condition("PROD_021_LIVE_SHAPED_DIALOGUE_POLICY_SIMULATION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-021 missing from checkpoint index")
    assert_condition("PROD-021" in ROADMAP.read_text(encoding="utf-8"), "PROD-021 missing from roadmap")
    assert_condition("PROD-021 live-shaped dialogue-policy simulation" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-021 missing from methodology log")
    assert_condition("Keep PROD-021 hooks opt-in" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-021 decision missing from decision log")
    assert_condition("push to GitHub `main`" in AGENTS.read_text(encoding="utf-8"), "checkpoint push-to-main rule missing from AGENTS.md")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-021",
            "live-shaped",
            "multi-turn",
            "dialogue-policy",
            "exact customer turns",
            "exact agent answers",
            "retrieval default enabled: `false`",
            "composer hook flag default enabled: `false`",
            "no provider calls",
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_case(case_data: dict[str, Any]) -> None:
    assert_condition(case_data.get("prod_021_case_id") == CHECKPOINT_ID, case_data.get("prod_021_case_id"))
    assert_condition(SOURCE_PROD_011 in case_data.get("source_checkpoints", []), case_data.get("source_checkpoints"))
    assert_condition(SOURCE_PROD_020 in case_data.get("source_checkpoints", []), case_data.get("source_checkpoints"))
    boundaries = case_data.get("boundaries", {})
    for key in [
        "copied_transcript_text_used",
        "generated_from_single_source_transcript",
        "contains_transcript_derived_prompt_text",
        "provider_calls_made",
        "private_data_read",
        "dataset_download_performed",
    ]:
        assert_condition(boundaries.get(key) is False, f"case boundary {key} must be false")

    calls = case_data.get("calls", [])
    assert_condition(len(calls) >= 7, "case file must include at least 7 calls")
    labels = {call.get("scenario_label") for call in calls}
    assert_condition(REQUIRED_LABELS <= labels, f"missing labels: {sorted(REQUIRED_LABELS - labels)}")
    total_turns = sum(len(call.get("turns", [])) for call in calls)
    assert_condition(total_turns >= 18, f"expected at least 18 live-shaped customer turns, got {total_turns}")
    assert_condition(any(call.get("eligible_for_close") for call in calls), "case file needs at least one sale-eligible call")
    assert_condition(any(not call.get("eligible_for_close") for call in calls), "case file needs non-sale calls")

    for call in calls:
        assert_condition(call.get("source_prod_011_call_id"), f"{call.get('call_id')} missing source PROD-011 call id")
        assert_condition(len(call.get("source_pattern_ids", [])) >= 3, f"{call.get('call_id')} needs at least 3 source pattern ids")
        for index, turn in enumerate(call.get("turns", []), start=1):
            assert_condition(turn.get("turn_position") == index, f"{turn.get('turn_id')} turn_position mismatch")
            assert_condition(turn.get("customer_transcript"), f"{turn.get('turn_id')} missing customer transcript")
            assert_condition(turn.get("expected_policy_action"), f"{turn.get('turn_id')} missing expected policy action")
            assert_condition(turn.get("expected_call_control"), f"{turn.get('turn_id')} missing expected call control")
            assert_condition(turn.get("expected_agent_response_requirements"), f"{turn.get('turn_id')} missing response requirements")


def validate_payload(payload: dict[str, Any], case_data: dict[str, Any]) -> None:
    assert_condition(payload.get("prod_021_id") == CHECKPOINT_ID, payload.get("prod_021_id"))
    assert_condition(payload.get("source_prod_011_case", {}).get("source_checkpoint") == SOURCE_PROD_011, payload.get("source_prod_011_case"))
    assert_condition(payload.get("source_prod_020_result", {}).get("decision") == "keep_naturalized_runtime_hooks_as_opt_in_candidate_not_default", payload.get("source_prod_020_result"))
    assert_condition(payload.get("hypothesis", {}).get("fixed_cases") == "live-shaped PROD-021 case file", payload.get("hypothesis"))
    assert_condition(payload.get("hypothesis", {}).get("runtime_surface_changed") == "none", payload.get("hypothesis"))

    boundaries = payload.get("boundaries", {})
    for key in [
        "provider_calls_made",
        "llm_used",
        "dataset_download_performed",
        "private_data_read",
        "runtime_retrieval_default_enabled",
        "composer_hook_flag_default_enabled",
        "default_runtime_behavior_changed",
        "commercial_runtime_prompt_text_from_callcenteren_allowed",
        "raw_dataset_text_stored",
        "scenario_label_passed_to_composer",
        "source_pattern_ids_passed_to_composer",
    ]:
        assert_condition(boundaries.get(key) is False, f"payload boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("call_count") == len(case_data.get("calls", [])), summary)
    assert_condition(summary.get("customer_turn_count", 0) >= 18, summary)
    assert_condition(summary.get("default_off_answer_drift_count") == 0, summary)
    assert_condition(summary.get("opt_in_hooked_answer_count", 0) > 0, summary)
    assert_condition(summary.get("hook_applied_without_eval_label_count") == summary.get("opt_in_hooked_answer_count"), summary)
    assert_condition(summary.get("opt_in_total_score", 0) >= summary.get("retrieval_only_total_score", 0), summary)
    assert_condition(summary.get("retrieval_only_wins_vs_opt_in") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("runtime_retrieval_default_enabled") is False, summary)
    assert_condition(summary.get("composer_hook_flag_default_enabled") is False, summary)
    rate_is_one(summary, "state_reference_completeness")
    rate_is_one(summary, "protected_context_preservation")
    rate_is_one(summary, "non_sale_correctness")
    rate_is_one(summary, "safe_close_correctness")
    assert_condition(summary.get("hard_failure_rate") == 0.0, summary)
    assert_condition(summary.get("prod_021_checkpoint_completed") is True, summary)
    assert_condition(payload.get("decision") in {
        "keep_live_shaped_hooks_opt_in_candidate_not_default",
        "revise_before_runtime_promotion_keep_hooks_opt_in",
    }, payload.get("decision"))

    turn_results = payload.get("turn_results", [])
    assert_condition(len(turn_results) == summary.get("customer_turn_count"), "turn result count mismatch")
    protected_turns = [turn for turn in turn_results if turn.get("protected_context")]
    hooked_turns = [turn for turn in turn_results if turn.get("hook_applied")]
    assert_condition(protected_turns, "expected at least one protected turn")
    assert_condition(hooked_turns, "expected at least one hooked turn")
    for turn in turn_results:
        assert_condition(turn.get("customer_transcript"), turn)
        assert_condition(turn.get("baseline_answer"), turn)
        assert_condition(turn.get("retrieval_only_answer"), turn)
        assert_condition(turn.get("opt_in_answer"), turn)
        assert_condition(turn.get("state_trace", {}).get("turn_position") == turn.get("turn_position"), turn)
        assert_condition(turn.get("runtime_trace", {}).get("default_off", {}).get("retrieval_status") == "disabled", turn)
        assert_condition(turn.get("runtime_trace", {}).get("default_off", {}).get("composer_hooks_enabled") is False, turn)
        assert_condition(turn.get("runtime_trace", {}).get("opt_in", {}).get("composer_hooks_enabled") is True, turn)
        assert_condition(turn.get("contains_payment_collection") is False, turn)
        assert_condition(turn.get("hard_failure") is False, turn)
        if turn.get("hook_applied"):
            assert_condition(turn.get("composer_hooks", {}).get("no_evaluation_labels_used") is True, turn)
        if turn.get("protected_context"):
            assert_condition(turn.get("composer_hooks", {}).get("applied") is False, turn)
            assert_condition(turn.get("protected_context_preserved") is True, turn)

    combined = json.dumps(payload, ensure_ascii=False).lower() + "\n" + REPORT_PATH.read_text(encoding="utf-8").lower()
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-021 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    case_data = read_json(CASE_PATH)
    payload = read_json(RESULT_PATH)
    validate_case(case_data)
    validate_payload(payload, case_data)
    validate_docs()
    print("PROD-021 live-shaped dialogue-policy simulation validation passed.")


if __name__ == "__main__":
    main()
