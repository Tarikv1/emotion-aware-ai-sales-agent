#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-036-interactive-demo-readiness-review"
SOURCE_CHECKPOINT_ID = "PROD-035-runtime-decision-trace-alignment"
NEXT_CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"

MODULE = ROOT / "scripts" / "prod_036_interactive_demo_readiness_review.py"
RUNNER = ROOT / "scripts" / "run_prod_036_interactive_demo_readiness_review.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_036_INTERACTIVE_DEMO_READINESS_REVIEW.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PACKET_PATH = OUT_DIR / "interactive_demo_readiness_packet.json"
DEMO_HTML_PATH = OUT_DIR / "interactive_demo_readiness_preview.html"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
SOURCE_TRACE_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "aligned_interactive_call_traces.json"

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
    PACKET_PATH,
    DEMO_HTML_PATH,
    SOURCE_RESULT_PATH,
    SOURCE_TRACE_PATH,
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
    "runtime_decision_trace_default_changed",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "source_prod_035_overwritten",
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
    '"runtime_behavior_changed_by_this_checkpoint": true',
    '"runtime_decision_trace_default_changed": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
    '"demo_blocker_count": 1',
    '"local_interactive_demo_ready": false',
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


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("packet_path") == normalized(PACKET_PATH), outputs)
    assert_condition(outputs.get("demo_html_path") == normalized(DEMO_HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("source_call_count") == 8, summary)
    assert_condition(summary.get("source_turn_count") == 14, summary)
    assert_condition(summary.get("reviewed_call_count") == 8, summary)
    assert_condition(summary.get("reviewed_turn_count") == 14, summary)
    assert_condition(summary.get("demo_card_count") == 8, summary)
    assert_condition(summary.get("demo_ready_call_count") == 8, summary)
    assert_condition(summary.get("demo_blocker_count") == 0, summary)
    assert_condition(summary.get("local_interactive_demo_ready") is True, summary)
    assert_condition(summary.get("exact_customer_text_visible") is True, summary)
    assert_condition(summary.get("exact_agent_answer_visible") is True, summary)
    assert_condition(summary.get("decision_process_visible") is True, summary)
    assert_condition(summary.get("state_transition_visible") is True, summary)
    assert_condition(summary.get("terminal_outcome_visible") is True, summary)
    assert_condition(summary.get("safety_flags_visible") is True, summary)
    assert_condition(summary.get("cold_opening_visible") is True, summary)
    assert_condition(summary.get("decision_snapshot_mismatch_count") == 0, summary)
    assert_condition(summary.get("unknown_objection_decision_count") == 0, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("first_build_recommendation") == "local_interactive_trace_demo_surface", summary)

    packet = read_json(PACKET_PATH)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, packet.get("source_checkpoint_id"))
    cards = packet.get("demo_cards", [])
    assert_condition(len(cards) == 8, "demo card count")
    assert_condition(len(packet.get("demo_requirements", [])) >= 8, "demo requirements missing")
    assert_condition(packet.get("go_no_go", {}).get("decision") == "go-local-trace-demo", packet.get("go_no_go"))
    for card in cards:
        assert_condition(card.get("demo_ready") is True, card)
        assert_condition(card.get("opening", {}).get("agent_opening"), card)
        assert_condition(card.get("opening", {}).get("customer_opening_response"), card)
        assert_condition(card.get("turns"), card)
        assert_condition(card.get("terminal_outcome") in {"accepted-deal", "rejected-deal"}, card)
        for turn in card["turns"]:
            assert_condition(turn.get("customer_context"), turn)
            assert_condition(turn.get("agent_answer"), turn)
            decision = turn.get("decision_snapshot", {})
            assert_condition(decision.get("sales_difficulty") != "unknown-runtime-signal", turn)
            assert_condition(not (decision.get("next_action") == "ask-follow-up" and "?" not in turn.get("agent_answer", "")), turn)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + json.dumps(packet, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + DEMO_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_036_interactive_demo_readiness_review.py" in commands, "PROD-036 runner missing from COMMANDS.md")
    assert_condition("validate_prod_036_interactive_demo_readiness_review.py" in commands, "PROD-036 validator missing from COMMANDS.md")
    assert_condition("PROD_036_INTERACTIVE_DEMO_READINESS_REVIEW.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-036 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-036 missing from roadmap")
    assert_condition("PROD-036 interactive demo readiness review" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-036 missing from methodology log")
    assert_condition("Keep PROD-036 as the local interactive demo readiness gate" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-036 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, DEMO_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-036",
            "interactive demo readiness review",
            "local interactive demo ready: `true`",
            "demo blocker count: `0`",
            "demo-ready calls: `8`",
            "decision snapshot mismatches: `0`",
            "unknown-objection decisions: `0`",
            "first build recommendation: `local_interactive_trace_demo_surface`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-036 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-036 interactive demo readiness review validation passed.")


if __name__ == "__main__":
    main()
