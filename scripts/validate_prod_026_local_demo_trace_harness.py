#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "prod_026_local_demo_trace_harness.py"
RUNNER = ROOT / "scripts" / "run_prod_026_local_demo_trace_harness.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_026_LOCAL_DEMO_TRACE_HARNESS.md"
SOURCE_PROD_025_RESULT = ROOT / "research" / "experiments" / "generated" / "PROD-025-bounded-demo-readiness-packet" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-026-local-demo-trace-harness"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TRACE_PACKET_PATH = OUT_DIR / "trace_packet.json"
TRACE_HTML_PATH = OUT_DIR / "trace_harness.html"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

CHECKPOINT_ID = "PROD-026-local-demo-trace-harness"
SOURCE_CHECKPOINT_ID = "PROD-025-bounded-demo-readiness-packet"
EXPECTED_NEXT = "PROD-027-manual-demo-trace-review"

REQUIRED_FILES = [
    MODULE,
    RUNNER,
    DOC_PATH,
    SOURCE_PROD_025_RESULT,
    RESULT_PATH,
    REPORT_PATH,
    TRACE_PACKET_PATH,
    TRACE_HTML_PATH,
]

REQUIRED_SCENARIOS = {
    "software_multi_objection_sale",
    "software_procurement_authority_delay",
    "trust_price_callback",
}

REQUIRED_DECISION_FIELDS = {
    "policy_action",
    "call_control",
    "expected_outcome",
    "source_checkpoint",
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
    '"customer_data_allowed": true',
    '"payment_collection_enabled": true',
    '"live_provider_demo_allowed": true',
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
    assert_condition("run_prod_026_local_demo_trace_harness.py" in commands, "PROD-026 runner missing from COMMANDS.md")
    assert_condition("validate_prod_026_local_demo_trace_harness.py" in commands, "PROD-026 validator missing from COMMANDS.md")
    assert_condition("PROD_026_LOCAL_DEMO_TRACE_HARNESS.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-026 missing from checkpoint index")
    assert_condition("PROD-026-local-demo-trace-harness" in ROADMAP.read_text(encoding="utf-8"), "PROD-026 missing from roadmap")
    assert_condition("PROD-026 local demo trace harness" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-026 missing from methodology log")
    assert_condition("Keep PROD-026 as local trace harness" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-026 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, TRACE_HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-026",
            "PROD-025",
            "local demo trace harness",
            "exact question and answer visible: `true`",
            "decision process visible: `true`",
            "local trace only: `true`",
            "manual review required: `true`",
            "provider calls made: `false`",
            "customer data allowed: `false`",
            "retrieval default enabled: `false`",
            "composer hook default enabled: `false`",
            EXPECTED_NEXT,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def validate_payload(payload: dict[str, Any], source_prod_025: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, payload.get("source_checkpoint_id"))
    assert_condition(payload.get("source_prod_025_result_path") == str(SOURCE_PROD_025_RESULT.relative_to(ROOT)).replace("\\", "/"), payload.get("source_prod_025_result_path"))
    assert_condition(source_prod_025.get("readiness_summary", {}).get("demo_readiness_gate_passed") is True, "source PROD-025 must pass demo readiness")

    boundaries = payload.get("boundaries", {})
    for key in [
        "provider_calls_made",
        "llm_used",
        "private_data_read",
        "dataset_download_performed",
        "runtime_behavior_changed_by_this_checkpoint",
        "runtime_retrieval_default_enabled",
        "composer_hook_flag_default_enabled",
        "live_provider_default_enabled",
        "customer_data_allowed",
        "payment_collection_enabled",
        "customer_facing_claim_allowed",
        "server_started",
    ]:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("harness_summary", {})
    assert_condition(summary.get("trace_card_count") == 3, summary)
    assert_condition(summary.get("source_trace_card_count") == 3, summary)
    assert_condition(summary.get("exact_question_and_answer_visible") is True, summary)
    assert_condition(summary.get("decision_process_visible") is True, summary)
    assert_condition(summary.get("safety_flags_visible") is True, summary)
    assert_condition(summary.get("local_trace_only") is True, summary)
    assert_condition(summary.get("manual_review_required") is True, summary)
    assert_condition(summary.get("local_demo_trace_harness_ready") is True, summary)
    assert_condition(summary.get("production_runtime_promotion_allowed") is False, summary)
    assert_condition(summary.get("live_provider_demo_allowed") is False, summary)
    assert_condition(summary.get("next_checkpoint_recommended") == EXPECTED_NEXT, summary)

    outputs = payload.get("harness_outputs", {})
    assert_condition(outputs.get("trace_packet_path") == str(TRACE_PACKET_PATH.relative_to(ROOT)).replace("\\", "/"), outputs)
    assert_condition(outputs.get("static_html_path") == str(TRACE_HTML_PATH.relative_to(ROOT)).replace("\\", "/"), outputs)
    assert_condition(outputs.get("report_path") == str(REPORT_PATH.relative_to(ROOT)).replace("\\", "/"), outputs)

    trace_cards = payload.get("trace_cards", [])
    assert_condition(len(trace_cards) == 3, "expected three trace cards")
    assert_condition(REQUIRED_SCENARIOS == {card.get("scenario_label") for card in trace_cards}, trace_cards)
    for index, card in enumerate(trace_cards, start=1):
        assert_condition(card.get("card_id") == f"demo-trace-{index:03d}", card)
        for key in ["source_turn_id", "scenario_label", "customer_question", "agent_answer", "review_status"]:
            assert_condition(card.get(key) not in (None, ""), f"trace card missing {key}")
        decision = card.get("decision_process", {})
        assert_condition(REQUIRED_DECISION_FIELDS <= set(decision), decision)
        assert_condition(card.get("safety_flags", {}).get("contains_payment_collection") is False, card)
        assert_condition(card.get("safety_flags", {}).get("hard_failure") is False, card)
        assert_condition(card.get("review_status") == "pending-manual-review", card)

    trace_packet = read_json(TRACE_PACKET_PATH)
    assert_condition(trace_packet.get("checkpoint_id") == CHECKPOINT_ID, trace_packet.get("checkpoint_id"))
    assert_condition(len(trace_packet.get("trace_cards", [])) == 3, trace_packet)

    html = TRACE_HTML_PATH.read_text(encoding="utf-8")
    for card in trace_cards:
        assert_condition(card["source_turn_id"] in html, f"HTML missing {card['source_turn_id']}")
        assert_condition(card["customer_question"] in html, f"HTML missing question for {card['source_turn_id']}")
        assert_condition(card["agent_answer"] in html, f"HTML missing answer for {card['source_turn_id']}")

    assert_condition(payload.get("decision") == "local_trace_harness_ready_pending_manual_review", payload.get("decision"))

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + TRACE_HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-026 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    payload = read_json(RESULT_PATH)
    source_prod_025 = read_json(SOURCE_PROD_025_RESULT)
    validate_payload(payload, source_prod_025)
    validate_docs()
    print("PROD-026 local demo trace harness validation passed.")


if __name__ == "__main__":
    main()
