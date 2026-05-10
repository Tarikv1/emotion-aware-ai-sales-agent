#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-041-conditional-simulation-review"
SOURCE_CHECKPOINT_ID = "PROD-041A-conditional-scenario-diversity-expansion"

MODULE = ROOT / "scripts" / "prod_041_conditional_simulation_review.py"
RUNNER = ROOT / "scripts" / "run_prod_041_conditional_simulation_review.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_041_CONDITIONAL_SIMULATION_REVIEW.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
REVIEW_PACKET_PATH = OUT_DIR / "conditional_simulation_review_packet.json"
SOURCE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "result.json"
SOURCE_TRACE_PATH = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID / "scenario_diversity_traces.json"

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
    SOURCE_RESULT_PATH,
    SOURCE_TRACE_PATH,
]

REQUIRED_FALSE_BOUNDARIES = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "source_prod_041a_modified",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "payment_collection_enabled",
    "production_runtime_promotion_allowed",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "api key",
    "card number",
    '"provider_calls_made": true',
    '"llm_used": true',
    '"source_prod_041a_modified": true',
    '"runtime_behavior_changed_by_this_checkpoint": true',
    '"production_runtime_promotion_allowed": true',
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


def validate_payload(payload: dict[str, Any], packet: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(packet.get("checkpoint_id") == CHECKPOINT_ID, packet.get("checkpoint_id"))
    assert_condition(packet.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, packet.get("source_checkpoint_id"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("review_packet_path") == normalized(REVIEW_PACKET_PATH), outputs)
    source_inputs = payload.get("source_inputs", {})
    assert_condition(source_inputs.get("source_result_path") == normalized(SOURCE_RESULT_PATH), source_inputs)
    assert_condition(source_inputs.get("source_trace_path") == normalized(SOURCE_TRACE_PATH), source_inputs)

    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(payload.get("boundaries", {}).get(key) is False, f"boundary {key} must be false")

    source_metrics = payload.get("source_metrics_locked", {})
    assert_condition(source_metrics.get("call_count") == 40, source_metrics)
    assert_condition(source_metrics.get("b2b_call_count") == 24, source_metrics)
    assert_condition(source_metrics.get("b2c_call_count") == 16, source_metrics)
    assert_condition(source_metrics.get("scenario_label_count") == 40, source_metrics)
    assert_condition(source_metrics.get("hard_failure_count") == 0, source_metrics)
    assert_condition(source_metrics.get("payment_collection_count") == 0, source_metrics)
    assert_condition(source_metrics.get("unsupported_claim_count") == 0, source_metrics)
    assert_condition(source_metrics.get("leakage_finding_count") == 0, source_metrics)

    summary = payload.get("summary", {})
    assert_condition(summary.get("reviewed_call_count") == 40, summary)
    assert_condition(summary.get("reviewed_b2b_call_count") == 24, summary)
    assert_condition(summary.get("reviewed_b2c_call_count") == 16, summary)
    assert_condition(summary.get("prod_041a_locked") is True, summary)
    assert_condition(summary.get("remaining_deterministic_phrasing_acceptable") == "offline-review-only", summary)
    assert_condition(summary.get("safe_close_outcomes_earned") == "partially", summary)
    assert_condition(summary.get("targeted_rewrite_required_before_voice_or_demo") is True, summary)
    assert_condition(summary.get("voice_playback_unblocked") is False, summary)
    assert_condition(summary.get("public_demo_polish_unblocked") is False, summary)
    assert_condition(summary.get("provider_calls_made") is False, summary)
    assert_condition(summary.get("llm_used") is False, summary)
    assert_condition(summary.get("rewrite_candidate_count", 0) >= 8, summary)
    assert_condition(summary.get("template_like_turn_count", 0) >= 8, summary)

    decision = packet.get("review_decision", {})
    assert_condition(decision.get("prod_041a_locked") is True, decision)
    assert_condition(decision.get("do_not_expand_prod_041a") is True, decision)
    assert_condition(decision.get("voice_playback_unblocked") is False, decision)
    assert_condition(decision.get("public_demo_polish_unblocked") is False, decision)
    assert_condition(decision.get("scenario_branching_unblocked") is False, decision)

    findings = packet.get("manual_review_findings", [])
    finding_ids = {finding.get("finding_id") for finding in findings}
    for expected in [
        "deterministic-phrasing-still-audible",
        "template-like-customer-turns-remain",
        "safe-close-outcomes-only-partly-earned",
        "targeted-rewrites-required-before-voice",
    ]:
        assert_condition(expected in finding_ids, f"missing finding {expected}")

    rewrite_candidates = packet.get("rewrite_candidates", [])
    assert_condition(len(rewrite_candidates) == summary.get("rewrite_candidate_count"), rewrite_candidates)
    assert_condition(all(candidate.get("scenario_label") for candidate in rewrite_candidates), rewrite_candidates)
    assert_condition(all(candidate.get("reason") for candidate in rewrite_candidates), rewrite_candidates)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_041_conditional_simulation_review.py" in commands, "PROD-041 runner missing from COMMANDS.md")
    assert_condition("validate_prod_041_conditional_simulation_review.py" in commands, "PROD-041 validator missing from COMMANDS.md")
    assert_condition("PROD_041_CONDITIONAL_SIMULATION_REVIEW.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-041 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-041 missing from roadmap")
    assert_condition("PROD-041 conditional simulation review" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-041 missing from methodology log")
    assert_condition("Complete PROD-041 human review without expanding PROD-041A" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-041 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-041",
            "conditional simulation review",
            "PROD-041A locked",
            "remaining deterministic phrasing acceptable: `offline-review-only`",
            "safe close outcomes earned: `partially`",
            "targeted rewrite required before voice or demo: `true`",
            "voice playback unblocked: `false`",
            "public demo polish unblocked: `false`",
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-041 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH), read_json(REVIEW_PACKET_PATH))
    validate_docs()
    print("PROD-041 conditional simulation review validation passed.")


if __name__ == "__main__":
    main()
