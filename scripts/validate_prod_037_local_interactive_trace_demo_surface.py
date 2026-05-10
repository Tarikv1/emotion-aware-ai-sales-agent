#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-037-local-interactive-trace-demo-surface"
SOURCE_CHECKPOINT_ID = "PROD-036-interactive-demo-readiness-review"
NEXT_CHECKPOINT_ID = "PROD-038-local-demo-surface-review"

MODULE = ROOT / "scripts" / "prod_037_local_interactive_trace_demo_surface.py"
RUNNER = ROOT / "scripts" / "run_prod_037_local_interactive_trace_demo_surface.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_037_LOCAL_INTERACTIVE_TRACE_DEMO_SURFACE.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
SURFACE_PATH = OUT_DIR / "local_interactive_trace_demo_surface.html"
SURFACE_DATA_PATH = OUT_DIR / "local_interactive_trace_demo_surface_data.json"
SOURCE_PACKET_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "interactive_demo_readiness_packet.json"

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
    SURFACE_PATH,
    SURFACE_DATA_PATH,
    SOURCE_PACKET_PATH,
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
    "source_prod_036_overwritten",
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
    '"surface_ready": false',
    '"visible_call_count": 7',
    '"visible_turn_count": 13',
]

REQUIRED_HTML_MARKERS = [
    "PROD-037 Local Interactive Trace Demo Surface",
    "data-checkpoint=\"PROD-037-local-interactive-trace-demo-surface\"",
    "Local synthetic trace replay",
    "call-list",
    "turn-list",
    "opening-panel",
    "customer-context",
    "agent-answer",
    "customer-response",
    "decision-snapshot",
    "state-transition",
    "safety-flags",
    "terminal-outcome",
    "replay-controls",
    "No provider calls",
    "No production runtime promotion",
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
    assert_condition(outputs.get("surface_path") == normalized(SURFACE_PATH), outputs)
    assert_condition(outputs.get("surface_data_path") == normalized(SURFACE_DATA_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("source_demo_card_count") == 8, summary)
    assert_condition(summary.get("surface_call_count") == 8, summary)
    assert_condition(summary.get("surface_turn_count") == 14, summary)
    assert_condition(summary.get("visible_call_count") == 8, summary)
    assert_condition(summary.get("visible_turn_count") == 14, summary)
    assert_condition(summary.get("selectable_call_count") == 8, summary)
    assert_condition(summary.get("selectable_turn_count") == 14, summary)
    assert_condition(summary.get("surface_ready") is True, summary)
    assert_condition(summary.get("static_html_ready") is True, summary)
    assert_condition(summary.get("keyboard_accessible_controls") is True, summary)
    assert_condition(summary.get("exact_customer_text_visible") is True, summary)
    assert_condition(summary.get("exact_agent_answer_visible") is True, summary)
    assert_condition(summary.get("decision_process_visible") is True, summary)
    assert_condition(summary.get("state_transition_visible") is True, summary)
    assert_condition(summary.get("terminal_outcome_visible") is True, summary)
    assert_condition(summary.get("safety_flags_visible") is True, summary)
    assert_condition(summary.get("cold_opening_visible") is True, summary)
    assert_condition(summary.get("replay_controls_visible") is True, summary)
    assert_condition(summary.get("local_synthetic_label_visible") is True, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("server_started") is False, summary)
    assert_condition(summary.get("runtime_behavior_changed") is False, summary)
    assert_condition(summary.get("production_runtime_promotion_allowed") is False, summary)

    surface_data = read_json(SURFACE_DATA_PATH)
    assert_condition(surface_data.get("checkpoint_id") == CHECKPOINT_ID, surface_data.get("checkpoint_id"))
    assert_condition(surface_data.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, surface_data.get("source_checkpoint_id"))
    calls = surface_data.get("calls", [])
    assert_condition(len(calls) == 8, "surface call count")
    assert_condition(sum(len(call.get("turns", [])) for call in calls) == 14, "surface turn count")
    for call in calls:
        assert_condition(call.get("seed_id"), call)
        assert_condition(call.get("persona"), call)
        assert_condition(call.get("opening", {}).get("agent_opening"), call)
        assert_condition(call.get("opening", {}).get("customer_opening_response"), call)
        assert_condition(call.get("terminal_outcome") in {"accepted-deal", "rejected-deal"}, call)
        assert_condition(call.get("terminal_reason"), call)
        for turn in call.get("turns", []):
            assert_condition(turn.get("customer_context"), turn)
            assert_condition(turn.get("agent_answer"), turn)
            assert_condition(turn.get("customer_response"), turn)
            assert_condition(turn.get("decision_snapshot", {}).get("selected_strategy"), turn)
            assert_condition(turn.get("decision_snapshot", {}).get("next_action"), turn)
            assert_condition(isinstance(turn.get("state_delta"), dict), turn)
            assert_condition(isinstance(turn.get("safety_flags"), dict), turn)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_037_local_interactive_trace_demo_surface.py" in commands, "PROD-037 runner missing from COMMANDS.md")
    assert_condition("validate_prod_037_local_interactive_trace_demo_surface.py" in commands, "PROD-037 validator missing from COMMANDS.md")
    assert_condition("PROD_037_LOCAL_INTERACTIVE_TRACE_DEMO_SURFACE.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-037 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-037 missing from roadmap")
    assert_condition("PROD-037 local interactive trace demo surface" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-037 missing from methodology log")
    assert_condition("Keep PROD-037 as a local synthetic trace replay surface" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-037 decision missing from decision log")

    html_text = SURFACE_PATH.read_text(encoding="utf-8")
    for marker in REQUIRED_HTML_MARKERS:
        assert_condition(marker in html_text, f"surface missing marker: {marker}")

    for path in [DOC_PATH, REPORT_PATH, SURFACE_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-037",
            "local interactive trace demo surface",
            "surface ready: `true`",
            "visible calls: `8`",
            "visible turns: `14`",
            "selectable calls: `8`",
            "selectable turns: `14`",
            "static html ready: `true`",
            "keyboard accessible controls: `true`",
            "local synthetic trace replay",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-037 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-037 local interactive trace demo surface validation passed.")


if __name__ == "__main__":
    main()
