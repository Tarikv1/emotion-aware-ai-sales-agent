#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-035-runtime-decision-trace-alignment"
SOURCE_CHECKPOINT_ID = "PROD-034-interactive-post-fix-review"
TRACE_SOURCE_CHECKPOINT_ID = "PROD-033-interactive-simulator-termination-fix"
NEXT_CHECKPOINT_ID = "PROD-036-interactive-demo-readiness-review"

MODULE = ROOT / "scripts" / "prod_035_runtime_decision_trace_alignment.py"
RUNNER = ROOT / "scripts" / "run_prod_035_runtime_decision_trace_alignment.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_035_RUNTIME_DECISION_TRACE_ALIGNMENT.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TRACE_PATH = OUT_DIR / "aligned_interactive_call_traces.json"
TRACE_HTML_PATH = OUT_DIR / "aligned_interactive_call_trace.html"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
SOURCE_TRACE_PATH = ROOT / "research" / "experiments" / "generated" / TRACE_SOURCE_CHECKPOINT_ID / "interactive_call_traces.json"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"
GUARDED_RESPONSE = ROOT / "scripts" / "generate_guarded_response.py"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    TRACE_PATH,
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
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "source_prod_033_overwritten",
    "source_prod_034_overwritten",
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
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
    '"loop_guard_triggered": true',
    '"fixed_turn_limit_used": true',
    '"terminal_outcome": "max-turns"',
    '"decision_snapshot_mismatch_count": 13',
    '"unknown_objection_decision_count": 6',
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
    assert_condition(payload.get("trace_source_checkpoint_id") == TRACE_SOURCE_CHECKPOINT_ID, payload.get("trace_source_checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("trace_path") == normalized(TRACE_PATH), outputs)
    assert_condition(outputs.get("trace_html_path") == normalized(TRACE_HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")
    assert_condition(boundaries.get("runtime_spoken_answer_changed_by_this_checkpoint") is False, boundaries)
    assert_condition(boundaries.get("runtime_decision_trace_alignment_opt_in") is True, boundaries)
    assert_condition(boundaries.get("runtime_decision_trace_default_changed") is False, boundaries)

    summary = payload.get("summary", {})
    assert_condition(summary.get("source_call_count") == 8, summary)
    assert_condition(summary.get("source_turn_count") == 14, summary)
    assert_condition(summary.get("aligned_call_count") == 8, summary)
    assert_condition(summary.get("aligned_turn_count") == 14, summary)
    assert_condition(summary.get("spoken_answer_changed_count") == 0, summary)
    assert_condition(summary.get("customer_response_changed_count") == 0, summary)
    assert_condition(summary.get("terminal_outcome_changed_count") == 0, summary)
    assert_condition(summary.get("decision_snapshot_mismatch_before_count") == 13, summary)
    assert_condition(summary.get("decision_snapshot_mismatch_after_count") == 0, summary)
    assert_condition(summary.get("unknown_objection_decision_before_count") == 6, summary)
    assert_condition(summary.get("unknown_objection_decision_after_count") == 0, summary)
    assert_condition(summary.get("terminal_call_control_mismatch_after_count") == 0, summary)
    assert_condition(summary.get("direct_answer_next_action_count") >= 10, summary)
    assert_condition(summary.get("objection_mapped_count") >= 6, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("first_review_recommendation") == "interactive_demo_readiness_review", summary)

    aligned = read_json(TRACE_PATH)
    assert_condition(aligned.get("checkpoint_id") == CHECKPOINT_ID, aligned.get("checkpoint_id"))
    assert_condition(aligned.get("source_checkpoint_id") == TRACE_SOURCE_CHECKPOINT_ID, aligned.get("source_checkpoint_id"))
    assert_condition(len(aligned.get("calls", [])) == 8, "aligned call count")
    for call in aligned["calls"]:
        assert_condition(call.get("terminal_outcome") in {"accepted-deal", "rejected-deal"}, call)
        assert_condition(call.get("terminal_decision_source") == "customer", call)
        assert_condition(call.get("loop_guard_triggered") is False, call)
        for turn in call.get("turns", []):
            decision = turn.get("decision_snapshot", {})
            assert_condition(not (decision.get("next_action") == "ask-follow-up" and "?" not in turn.get("agent_answer", "")), turn)
            assert_condition(decision.get("sales_difficulty") != "unknown-runtime-signal", turn)
            assert_condition(turn.get("source_agent_answer") == turn.get("agent_answer"), turn)
            assert_condition(turn.get("alignment_change", {}).get("spoken_answer_changed") is False, turn)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + json.dumps(aligned, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_035_runtime_decision_trace_alignment.py" in commands, "PROD-035 runner missing from COMMANDS.md")
    assert_condition("validate_prod_035_runtime_decision_trace_alignment.py" in commands, "PROD-035 validator missing from COMMANDS.md")
    assert_condition("PROD_035_RUNTIME_DECISION_TRACE_ALIGNMENT.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-035 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-035 missing from roadmap")
    assert_condition("PROD-035 runtime decision-trace alignment" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-035 missing from methodology log")
    assert_condition("Keep PROD-035 as the opt-in runtime decision-trace alignment fix" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-035 decision missing from decision log")
    guarded = GUARDED_RESPONSE.read_text(encoding="utf-8")
    assert_condition("align_decision_trace" in guarded, "guarded response generator missing opt-in alignment flag")
    assert_condition("align_decision_snapshot_for_response" in guarded, "guarded response generator missing alignment helper")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-035",
            "runtime decision-trace alignment",
            "spoken answer changed count: `0`",
            "decision snapshot mismatches before: `13`",
            "decision snapshot mismatches after: `0`",
            "unknown-objection decisions before: `6`",
            "unknown-objection decisions after: `0`",
            "runtime decision trace default changed: `false`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-035 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-035 runtime decision-trace alignment validation passed.")


if __name__ == "__main__":
    main()
