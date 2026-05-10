#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-038-local-demo-surface-review"
SOURCE_CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
NEXT_CHECKPOINT_ID = "PROD-039-customer-realism-simulator-hardening"

MODULE = ROOT / "scripts" / "prod_038_local_demo_surface_review.py"
RUNNER = ROOT / "scripts" / "run_prod_038_local_demo_surface_review.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_038_LOCAL_DEMO_SURFACE_REVIEW.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
REVIEW_PACKET_PATH = OUT_DIR / "local_demo_surface_review_packet.json"
SOURCE_SURFACE_DATA_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "local_interactive_trace_demo_surface_data.json"

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
    REVIEW_PACKET_PATH,
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
    '"customer_response_realism_accepted": true',
    '"voice_playback_unblocked": true',
    '"public_demo_polish_unblocked": true',
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
    assert_condition(outputs.get("review_packet_path") == normalized(REVIEW_PACKET_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("reviewed_call_count") == 8, summary)
    assert_condition(summary.get("reviewed_turn_count") == 14, summary)
    assert_condition(summary.get("demo_surface_ui_accepted") is True, summary)
    assert_condition(summary.get("customer_response_realism_accepted") is False, summary)
    assert_condition(summary.get("conversation_quality_gate_passed") is False, summary)
    assert_condition(summary.get("customer_response_issue_count") >= 5, summary)
    assert_condition(summary.get("voice_playback_unblocked") is False, summary)
    assert_condition(summary.get("scenario_branching_unblocked") is False, summary)
    assert_condition(summary.get("more_call_seeds_unblocked") is False, summary)
    assert_condition(summary.get("public_demo_polish_unblocked") is False, summary)
    assert_condition(summary.get("next_build_recommendation") == "customer_realism_simulator_hardening", summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)

    packet = read_json(REVIEW_PACKET_PATH)
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("review_decision") == "revise-customer-simulator-before-demo-expansion", packet)
    issues = packet.get("customer_response_issues", [])
    issue_ids = {issue.get("issue_id") for issue in issues}
    for expected in [
        "over-cooperative-acceptance",
        "evaluator-like-wording",
        "too-clean-state-transition",
        "low-friction-follow-up",
        "artificial-boundary-language",
    ]:
        assert_condition(expected in issue_ids, f"missing issue {expected}")


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_038_local_demo_surface_review.py" in commands, "PROD-038 runner missing from COMMANDS.md")
    assert_condition("validate_prod_038_local_demo_surface_review.py" in commands, "PROD-038 validator missing from COMMANDS.md")
    assert_condition("PROD_038_LOCAL_DEMO_SURFACE_REVIEW.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-038 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-038 missing from roadmap")
    assert_condition("PROD-038 local demo surface review" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-038 missing from methodology log")
    assert_condition("Keep PROD-038 as the customer-realism rejection gate" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-038 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-038",
            "local demo surface review",
            "customer response realism accepted: `false`",
            "conversation quality gate passed: `false`",
            "demo surface ui accepted: `true`",
            "next build recommendation: `customer_realism_simulator_hardening`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-038 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-038 local demo surface review validation passed.")


if __name__ == "__main__":
    main()
