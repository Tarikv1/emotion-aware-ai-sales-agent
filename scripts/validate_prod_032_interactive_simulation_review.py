#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-032-interactive-simulation-review"
SOURCE_CHECKPOINT_ID = "PROD-031-interactive-grounded-call-simulation"
NEXT_CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"

MODULE = ROOT / "scripts" / "prod_032_interactive_simulation_review.py"
RUNNER = ROOT / "scripts" / "run_prod_032_interactive_simulation_review.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_032_INTERACTIVE_SIMULATION_REVIEW.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
PACKET_PATH = OUT_DIR / "interactive_simulation_review_packet.json"
TRACE_HTML_PATH = OUT_DIR / "interactive_simulation_review_trace.html"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
SOURCE_TRACE_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "interactive_call_traces.json"

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
    TRACE_HTML_PATH,
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
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "source_prod_031_overwritten",
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
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
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
    assert_condition(outputs.get("trace_html_path") == normalized(TRACE_HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("source_call_count") == 8, summary)
    assert_condition(summary.get("source_turn_count") == 26, summary)
    assert_condition(summary.get("reviewed_call_count") == 8, summary)
    assert_condition(summary.get("reviewed_turn_count") == 26, summary)
    assert_condition(summary.get("raw_finding_count") >= 50, summary)
    assert_condition(summary.get("affected_call_count") == 7, summary)
    assert_condition(summary.get("clean_call_count") == 1, summary)
    assert_condition(summary.get("simulator_design_limit_count") >= 20, summary)
    assert_condition(summary.get("runtime_policy_issue_count") >= 20, summary)
    assert_condition(summary.get("product_grounding_issue_count") == 0, summary)
    assert_condition(summary.get("still_relevant_static_route_gap_count") == 2, summary)
    assert_condition(summary.get("callback_converted_to_sale_ready_count") == 5, summary)
    assert_condition(summary.get("repeated_agent_answer_count") == 12, summary)
    assert_condition(summary.get("repeated_customer_message_count") == 4, summary)
    assert_condition(summary.get("decision_snapshot_mismatch_count") >= 19, summary)
    assert_condition(summary.get("unknown_objection_decision_count") == 6, summary)
    assert_condition(summary.get("premature_close_marker_count") == 3, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("runtime_behavior_changed") is False, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("first_fix_recommendation") == "simulator_termination_and_callback_state_control", summary)

    packet = read_json(PACKET_PATH)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, packet.get("source_checkpoint_id"))
    assert_condition(len(packet.get("call_reviews", [])) == 8, "call review count")
    assert_condition(len(packet.get("raw_findings", [])) == summary.get("raw_finding_count"), "raw finding count")
    assert_condition(len(packet.get("finding_clusters", [])) >= 4, "finding cluster count")
    assert_condition(len(packet.get("fix_recommendations", [])) >= 3, "fix recommendation count")

    categories = {finding["category"] for finding in packet["raw_findings"]}
    assert_condition("simulator-design-limit" in categories, categories)
    assert_condition("runtime-policy-issue" in categories, categories)
    assert_condition("still-relevant-static-route-gap" in categories, categories)

    priorities = [fix["priority"] for fix in packet["fix_recommendations"]]
    assert_condition(priorities[0] == 1, priorities)
    assert_condition(packet["fix_recommendations"][0]["fix_id"] == summary["first_fix_recommendation"], packet["fix_recommendations"][0])

    html = TRACE_HTML_PATH.read_text(encoding="utf-8")
    for marker in [
        "PROD-032 Interactive Simulation Review",
        "simulator-design limits",
        "runtime-policy issues",
        "first fix recommendation",
    ]:
        assert_condition(marker in html, marker)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + json.dumps(packet, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_032_interactive_simulation_review.py" in commands, "PROD-032 runner missing from COMMANDS.md")
    assert_condition("validate_prod_032_interactive_simulation_review.py" in commands, "PROD-032 validator missing from COMMANDS.md")
    assert_condition("PROD_032_INTERACTIVE_SIMULATION_REVIEW.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-032 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-032 missing from roadmap")
    assert_condition("PROD-032 interactive simulation review" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-032 missing from methodology log")
    assert_condition("Keep PROD-032 as the interactive trace review gate" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-032 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-032",
            "interactive simulation review",
            "source checkpoint: `PROD-031-interactive-grounded-call-simulation`",
            "raw findings: `54`",
            "affected calls: `7`",
            "callback converted to sale-ready: `5`",
            "repeated agent answers: `12`",
            "repeated customer messages: `4`",
            "product grounding issues: `0`",
            "first fix recommendation: `simulator_termination_and_callback_state_control`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-032 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-032 interactive simulation review validation passed.")


if __name__ == "__main__":
    main()
