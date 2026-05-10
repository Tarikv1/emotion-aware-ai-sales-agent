#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-039-customer-realism-simulator-hardening"
SOURCE_CHECKPOINT_ID = "PROD-038-local-demo-surface-review"
TRACE_SOURCE_CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
NEXT_CHECKPOINT_ID = "PROD-040-customer-realism-demo-surface-rerun"

MODULE = ROOT / "scripts" / "prod_039_customer_realism_simulator_hardening.py"
RUNNER = ROOT / "scripts" / "run_prod_039_customer_realism_simulator_hardening.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_039_CUSTOMER_REALISM_SIMULATOR_HARDENING.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
HARDENED_TRACE_PATH = OUT_DIR / "customer_realism_hardened_traces.json"
COMPARISON_PACKET_PATH = OUT_DIR / "customer_realism_comparison_packet.json"
COMPARISON_HTML_PATH = OUT_DIR / "customer_realism_comparison.html"
SOURCE_REVIEW_PACKET_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "local_demo_surface_review_packet.json"
SOURCE_SURFACE_DATA_PATH = ROOT / "research" / "experiments" / "generated" / TRACE_SOURCE_CHECKPOINT_ID / "local_interactive_trace_demo_surface_data.json"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    HARDENED_TRACE_PATH,
    COMPARISON_PACKET_PATH,
    COMPARISON_HTML_PATH,
    SOURCE_REVIEW_PACKET_PATH,
    SOURCE_SURFACE_DATA_PATH,
]

REQUIRED_FALSE_BOUNDARIES = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "customer_data_allowed",
    "payment_collection_enabled",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "source_prod_037_overwritten",
    "source_prod_038_overwritten",
    "production_runtime_promotion_allowed",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "card number",
    "credit card number",
    '"provider_calls_made": true',
    '"runtime_behavior_changed_by_this_checkpoint": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
    '"voice_playback_unblocked": true',
    '"public_demo_polish_unblocked": true',
]

UNREALISTIC_PHRASES = [
    "accept a non-binding",
    "specialist workflow review",
    "rejecting the deal",
    "rejecting the offer",
    "sales offer",
    "do not handle billing",
    "that answers the cost",
    "that makes sense now",
    "what would i tell my manager if i wanted to accept a review",
    "route me to support. i am rejecting",
    "i am rejecting",
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def normalized(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def count_unrealistic_phrases(text: str) -> int:
    lowered = text.lower()
    return sum(1 for phrase in UNREALISTIC_PHRASES if phrase in lowered)


def all_customer_text(trace: dict[str, Any]) -> str:
    chunks: list[str] = []
    for call in trace.get("calls", []):
        chunks.append(call.get("opening", {}).get("customer_opening_response", ""))
        for turn in call.get("turns", []):
            chunks.append(turn.get("customer_context", ""))
            chunks.append(turn.get("customer_response", ""))
    return "\n".join(chunks)


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("trace_source_checkpoint_id") == TRACE_SOURCE_CHECKPOINT_ID, payload.get("trace_source_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("hardened_trace_path") == normalized(HARDENED_TRACE_PATH), outputs)
    assert_condition(outputs.get("comparison_packet_path") == normalized(COMPARISON_PACKET_PATH), outputs)
    assert_condition(outputs.get("comparison_html_path") == normalized(COMPARISON_HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("fixed_call_count") == 8, summary)
    assert_condition(summary.get("fixed_turn_count") == 14, summary)
    assert_condition(summary.get("customer_response_changed_count") == 14, summary)
    assert_condition(summary.get("customer_opening_changed_count") == 8, summary)
    assert_condition(summary.get("agent_answer_changed_count") == 0, summary)
    assert_condition(summary.get("decision_snapshot_changed_count") == 0, summary)
    assert_condition(summary.get("terminal_outcome_changed_count") == 0, summary)
    assert_condition(summary.get("safety_flag_changed_count") == 0, summary)
    assert_condition(summary.get("baseline_unrealistic_phrase_hits") >= 10, summary)
    assert_condition(summary.get("hardened_unrealistic_phrase_hits") == 0, summary)
    assert_condition(summary.get("naturalness_feature_count") >= 5, summary)
    assert_condition(summary.get("customer_realism_gate_passed") is True, summary)
    assert_condition(summary.get("same_cases_rerun") is True, summary)
    assert_condition(summary.get("one_editable_surface") == "customer_simulator_response_phrasing", summary)
    assert_condition(summary.get("voice_playback_unblocked") is False, summary)
    assert_condition(summary.get("public_demo_polish_unblocked") is False, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("next_build_recommendation") == "customer_realism_demo_surface_rerun", summary)

    hardened = read_json(HARDENED_TRACE_PATH)
    assert_condition(hardened.get("checkpoint_id") == CHECKPOINT_ID, hardened.get("checkpoint_id"))
    assert_condition(len(hardened.get("calls", [])) == 8, "hardened call count")
    assert_condition(sum(len(call.get("turns", [])) for call in hardened.get("calls", [])) == 14, "hardened turn count")
    assert_condition(count_unrealistic_phrases(all_customer_text(hardened)) == 0, "hardened traces still contain unrealistic phrases")
    for call in hardened["calls"]:
        assert_condition(call.get("customer_realism_profile"), call)
        assert_condition(call.get("terminal_outcome") in {"accepted-deal", "rejected-deal"}, call)
        for turn in call.get("turns", []):
            assert_condition(turn.get("customer_context"), turn)
            assert_condition(turn.get("customer_response"), turn)
            assert_condition(turn.get("agent_answer"), turn)
            assert_condition(turn.get("realism_features"), turn)
            assert_condition(turn.get("decision_snapshot"), turn)
            assert_condition(turn.get("safety_flags"), turn)

    packet = read_json(COMPARISON_PACKET_PATH)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("hypothesis") == "More natural customer phrasing improves reviewability without changing agent answers, decisions, safety flags, or terminal outcomes.", packet)
    assert_condition(packet.get("decision") == "keep-for-demo-surface-rerun", packet)
    assert_condition(len(packet.get("comparisons", [])) == 14, "comparison count")
    for comparison in packet["comparisons"]:
        assert_condition(comparison.get("old_customer_response") != comparison.get("new_customer_response"), comparison)
        assert_condition(comparison.get("agent_answer_changed") is False, comparison)
        assert_condition(comparison.get("decision_snapshot_changed") is False, comparison)
        assert_condition(comparison.get("terminal_outcome_changed") is False, comparison)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_039_customer_realism_simulator_hardening.py" in commands, "PROD-039 runner missing from COMMANDS.md")
    assert_condition("validate_prod_039_customer_realism_simulator_hardening.py" in commands, "PROD-039 validator missing from COMMANDS.md")
    assert_condition("PROD_039_CUSTOMER_REALISM_SIMULATOR_HARDENING.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-039 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-039 missing from roadmap")
    assert_condition("PROD-039 customer realism simulator hardening" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-039 missing from methodology log")
    assert_condition("Keep PROD-039 as the customer-realism hardening checkpoint" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-039 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, COMPARISON_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-039",
            "customer realism simulator hardening",
            "customer realism gate passed: `true`",
            "customer response changed count: `14`",
            "customer opening changed count: `8`",
            "agent answer changed count: `0`",
            "decision snapshot changed count: `0`",
            "terminal outcome changed count: `0`",
            "safety flag changed count: `0`",
            "hardened unrealistic phrase hits: `0`",
            "next build recommendation: `customer_realism_demo_surface_rerun`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-039 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-039 customer realism simulator hardening validation passed.")


if __name__ == "__main__":
    main()
