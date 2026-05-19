#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "DIALOGUE-REASONER-001"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "dialogue-reasoner-001-live-demo-failures.json"
RUNNER_PATH = ROOT / "scripts" / "run_dialogue_reasoner_001_baseline.py"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID / "report.md"
DOC_PATH = ROOT / "docs" / "product" / "DIALOGUE_REASONER_001_STRUCTURED_RUNTIME_REASONER.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
RUNTIME_MANIFEST = ROOT / "runtime" / "runtime_manifest.json"

EXPECTED_FIELDS = {
    "dialogue_act",
    "buyer_intent",
    "resolved_topic",
    "sales_stage",
    "response_strategy",
    "must_include",
    "must_avoid",
    "safety_boundary",
    "confidence",
}

REQUIRED_COVERAGE = {
    "agent_open",
    "opening_greeting",
    "caller_identity_question",
    "previous_question_clarification",
    "ambiguous_negative",
    "callback_request",
    "callback_time",
    "price_question",
    "plan_question",
    "product_question",
    "workflow_question",
    "manual_tracking_objection",
    "selected_gap",
    "fit_question",
    "timing_objection",
    "effort_objection",
    "integration_question",
    "security_question",
    "specialist_request",
    "topic_shift",
    "low_information_acknowledgement",
    "asr_fragment",
    "unknown",
    "recommendation_request",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_cases() -> dict[str, Any]:
    assert_condition(CASES_PATH.exists(), "DIALOGUE-REASONER-001 cases are missing")
    payload = read_json(CASES_PATH)
    assert_condition(payload["experiment_id"] == EXPERIMENT_ID, "wrong experiment id in case file")
    assert_condition(payload["source_boundary"]["uses_provider_calls"] is False, "cases must not require providers")
    assert_condition(payload["source_boundary"]["uses_private_audio"] is False, "cases must not use private audio")
    assert_condition(payload["source_boundary"]["opens_prod_102"] is False, "cases must not open PROD-102")
    cases = payload["cases"]
    assert_condition(len(cases) == 30, f"expected 30 frozen cases, got {len(cases)}")
    case_ids = [case["case_id"] for case in cases]
    assert_condition(len(case_ids) == len(set(case_ids)), "case ids must be unique")
    coverage = {case["expected"]["dialogue_act"] for case in cases}
    assert_condition(REQUIRED_COVERAGE.issubset(coverage), f"missing dialogue-act coverage: {REQUIRED_COVERAGE - coverage}")
    return payload


def validate_runtime_module() -> None:
    module = importlib.import_module("runtime.core.dialogue_reasoner")
    for name in [
        "DIALOGUE_REASONER_ID",
        "REASONER_SCHEMA_FIELDS",
        "reason_about_turn",
        "validate_reasoning_packet",
        "render_strict_json_reasoner_prompt",
        "provider_boundary_packet",
    ]:
        assert_condition(hasattr(module, name), f"dialogue reasoner missing {name}")
    assert_condition(module.DIALOGUE_REASONER_ID == EXPERIMENT_ID, "wrong reasoner id")
    assert_condition(set(module.REASONER_SCHEMA_FIELDS) == EXPECTED_FIELDS, "reasoner schema field mismatch")
    boundary = module.provider_boundary_packet(mode="baseline")
    assert_condition(boundary["provider_calls_made"] is False, "baseline reasoner must not call a provider")
    assert_condition(boundary["text_sent_to_provider"] is False, "baseline reasoner must not send transcript text")
    assert_condition(boundary["llm_default_enabled"] is False, "LLM reasoner must remain default-off")


def run_baseline() -> None:
    assert_condition(RUNNER_PATH.exists(), "DIALOGUE-REASONER-001 runner is missing")
    completed = subprocess.run(
        [sys.executable, str(RUNNER_PATH)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    assert_condition(
        completed.returncode == 0,
        {
            "message": "DIALOGUE-REASONER-001 runner failed",
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        },
    )


def validate_result(case_payload: dict[str, Any]) -> None:
    assert_condition(RESULT_PATH.exists(), "DIALOGUE-REASONER-001 result is missing")
    assert_condition(REPORT_PATH.exists(), "DIALOGUE-REASONER-001 report is missing")
    result = read_json(RESULT_PATH)
    assert_condition(result["experiment_id"] == EXPERIMENT_ID, "wrong result id")
    assert_condition(result["mode"] == "baseline", "validator must run baseline mode")
    assert_condition(result["default_llm_enabled"] is False, "LLM must remain default-off")
    assert_condition(result["provider_calls_made"] is False, "baseline run must not call providers")
    assert_condition(result["text_sent_to_provider"] is False, "baseline run must not send text to providers")
    assert_condition(result["opens_prod_102"] is False, "must not open PROD-102")
    assert_condition(result["live_demo_response_behavior_changed"] is False, "reasoner baseline must not change heard demo behavior")
    assert_condition(set(result["reasoner_schema"]["fields"]) == EXPECTED_FIELDS, "result schema mismatch")
    assert_condition(result["case_count"] == 30, "result must include 30 cases")
    assert_condition(result["passed_count"] == 30, result["failed_cases"])
    assert_condition(result["failed_cases"] == [], result["failed_cases"])
    assert_condition(result["baseline_live_demo_001_preserved"] == "not-run-by-reasoner-runner", "runner should not hide LIVE-DEMO-001 validation")

    expected_by_id = {case["case_id"]: case["expected"] for case in case_payload["cases"]}
    for case_result in result["case_results"]:
        case_id = case_result["case_id"]
        assert_condition(case_id in expected_by_id, f"unexpected case result {case_id}")
        assert_condition(case_result["pass"] is True, case_result)
        reasoning = case_result["reasoning"]
        assert_condition(set(reasoning.keys()) == EXPECTED_FIELDS, reasoning)
        expected = expected_by_id[case_id]
        for key in ["dialogue_act", "buyer_intent", "resolved_topic", "sales_stage", "response_strategy", "safety_boundary"]:
            assert_condition(reasoning[key] == expected[key], {"case_id": case_id, "key": key, "reasoning": reasoning, "expected": expected})
        assert_condition(isinstance(reasoning["must_include"], list), reasoning)
        assert_condition(isinstance(reasoning["must_avoid"], list), reasoning)
        assert_condition(0.0 <= float(reasoning["confidence"]) <= 1.0, reasoning)

    assert_condition(REQUIRED_COVERAGE.issubset(set(result["coverage"]["dialogue_acts"])), result["coverage"])
    assert_condition("integration_claim_boundary" in result["coverage"]["safety_boundaries"], result["coverage"])
    assert_condition("security_claim_boundary" in result["coverage"]["safety_boundaries"], result["coverage"])
    assert_condition("agency_preservation_boundary" in result["coverage"]["safety_boundaries"], result["coverage"])
    assert_condition("runtime.core.live_voice_session_policy" in result["runtime_dependencies"], result["runtime_dependencies"])
    assert_condition("runtime.core.dialogue_reasoner" in result["runtime_modules_added"], result["runtime_modules_added"])
    assert_condition("PROD-102" not in json.dumps(result["case_results"], ensure_ascii=False), "case output must not mention PROD-102")


def validate_docs_and_manifest() -> None:
    assert_condition(DOC_PATH.exists(), "DIALOGUE-REASONER-001 doc is missing")
    doc = read_text(DOC_PATH)
    assert_condition(EXPERIMENT_ID in doc, "doc missing experiment id")
    assert_condition("runtime/core/dialogue_reasoner.py" in doc, "doc missing runtime module")
    assert_condition("default-off" in doc.lower(), "doc must state LLM default-off boundary")
    assert_condition("PROD-102 stays closed" in doc, "doc must keep PROD-102 closed")

    commands = read_text(COMMANDS_PATH)
    assert_condition("run_dialogue_reasoner_001_baseline.py" in commands, "COMMANDS missing runner")
    assert_condition("validate_dialogue_reasoner_001.py" in commands, "COMMANDS missing validator")

    methodology = read_text(METHODOLOGY_LOG)
    assert_condition("DIALOGUE-REASONER-001" in methodology, "methodology log missing DIALOGUE-REASONER-001")

    manifest = read_json(RUNTIME_MANIFEST)
    paths = {entry.get("path") for entry in manifest.get("runtime_entries", [])}
    assert_condition("runtime/core/dialogue_reasoner.py" in paths, "runtime manifest missing dialogue reasoner")


def main() -> None:
    cases = validate_cases()
    validate_runtime_module()
    run_baseline()
    validate_result(cases)
    validate_docs_and_manifest()


if __name__ == "__main__":
    main()
