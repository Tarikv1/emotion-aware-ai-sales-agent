#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-043-sales-playbook-runtime-adapter"
SOURCE_CHECKPOINT_ID = "PROD-042-callcenteren-turn-pattern-playbook"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
DOC_PATH = ROOT / "docs" / "product" / "PROD_043_SALES_PLAYBOOK_RUNTIME_ADAPTER.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX_PATH = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP_PATH = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG_PATH = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG_PATH = ROOT / "docs" / "thesis" / "DECISION_LOG.md"
REFERENCE_REGISTRY_PATH = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
PROD_041A_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-041A-conditional-scenario-diversity-expansion"

REQUIRED_OUTPUTS = {
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "customer_move_classification_cases": OUT_DIR / "customer_move_classification_cases.json",
    "playbook_retrieval_cases": OUT_DIR / "playbook_retrieval_cases.json",
    "agent_response_evaluation_cases": OUT_DIR / "agent_response_evaluation_cases.json",
    "agent_response_evaluations": OUT_DIR / "agent_response_evaluations.json",
    "runtime_adapter_review_data": OUT_DIR / "runtime_adapter_review_data.json",
    "runtime_adapter_review_html": OUT_DIR / "runtime_adapter_review.html",
}

SOURCE_OUTPUTS = {
    "customer_moves": SOURCE_DIR / "customer_move_patterns.json",
    "tactics": SOURCE_DIR / "agent_response_tactics.json",
    "playbook": SOURCE_DIR / "sales_playbook_rules.json",
    "evaluation": SOURCE_DIR / "evaluation_rules.json",
    "failures": SOURCE_DIR / "failure_patterns.json",
    "recoveries": SOURCE_DIR / "recovery_patterns.json",
    "result": SOURCE_DIR / "result.json",
}

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "retrieval_enabled": False,
    "runtime_agent_modified": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "dataset_download_performed": False,
    "production_runtime_promotion_allowed": False,
    "uses_exact_transcript_text": False,
    "uses_source_transcript_sequence": False,
    "uses_dataset_specific_phrasing": False,
}

SAFETY_MOVE_GROUPS = [
    {"price_first"},
    {"email_only", "send_info"},
    {"not_interested"},
    {"support_issue"},
    {"cancellation_request"},
    {"scam_or_card_fear", "payment_safety_fear"},
    {"sensitive_healthcare_concern", "coverage_confusion"},
]

ABSTRACT_AVOID_TACTICS = {
    "question_storming",
    "feature_dump",
    "hard_close",
    "dodge_question",
    "feature_pitch_before_answer",
    "pressure_after_refusal",
    "unclear_next_step",
    "vague_pitch",
    "unsupported_claim",
    "retention_pressure",
    "discovery",
    "callback_offer",
    "written_info_offer",
    "unsafe_payment_request",
    "overpromised_results",
    "failed_support_boundary",
    "wrong_handoff",
    "failed_identity_repair",
    "failed_existing_provider_objection",
    "failed_manager_approval_path",
    "premature_price_discussion",
    "missed_emotional_signal",
    "callback_offer_before_price_answer",
    "guessing",
    "unsupported technical claims",
    "unsupported security/compliance claims",
    "medical advice",
    "coverage promises",
    "medical_advice",
    "coverage_promises",
    "unsupported claims",
    "sales continuation",
    "retention pressure",
    "single_discovery_question before respecting email-only boundary",
}

FORBIDDEN_FULL_CONVERSATION_KEYS = {
    "interaction_traces",
    "scenario_diversity_traces",
    "conversation_sequence",
    "turns",
    "exchanges",
}

PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\-\(\) ]{7,}\d)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
LONG_QUOTED_PATTERN = re.compile(r"\"[^\"]{220,}\"")


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    assert_condition(isinstance(value, list), f"{key} must be a list")
    return value


def all_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(all_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for key, item in value.items():
            out.append(str(key))
            out.extend(all_strings(item))
        return out
    return []


def all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(all_keys(item))
    return keys


def ensure_files_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_OUTPUTS.values() if not path.exists()]
    assert_condition(not missing, f"missing required PROD-043 outputs: {missing}")
    source_missing = [str(path.relative_to(ROOT)) for path in SOURCE_OUTPUTS.values() if not path.exists()]
    assert_condition(not source_missing, f"missing required PROD-042 inputs: {source_missing}")
    for path in (DOC_PATH, COMMANDS_PATH, CHECKPOINT_INDEX_PATH, ROADMAP_PATH, METHODOLOGY_LOG_PATH, DECISION_LOG_PATH):
        assert_condition(path.exists(), f"missing required doc: {path.relative_to(ROOT)}")


def validate_source_inputs(source: dict[str, Any]) -> None:
    source_summary = source["result"].get("summary", {})
    for key in ("runtime_behavior_changed", "retrieval_enabled", "runtime_agent_modified", "provider_calls_made", "llm_used"):
        assert_condition(source_summary.get(key) is False, f"PROD-042 source boundary failed for {key}")
    assert_condition(source["playbook_rules"], "PROD-042 playbook rules missing")
    assert_condition(source["evaluation_rules"], "PROD-042 evaluation rules missing")


def validate_boundaries(result: dict[str, Any]) -> None:
    summary = result.get("summary", {})
    for key, expected in BOUNDARY_FLAGS.items():
        assert_condition(summary.get(key) == expected, f"result.summary[{key}] expected {expected}, got {summary.get(key)}")
    assert_condition(result.get("source_checkpoint_id") == SOURCE_CHECKPOINT_ID, result)
    assert_condition(result.get("next_checkpoint_recommended") == "PROD-044-core-sales-policy-update", result)


def validate_classifier(data: dict[str, Any], source: dict[str, Any], result: dict[str, Any]) -> None:
    cases = get_items(data, "customer_move_classification_cases")
    outputs = get_items(data, "classifier_outputs")
    move_ids = {item["customer_move_id"] for item in source["customer_moves"]}
    assert_condition(cases and outputs, "classifier cases and outputs must be present")
    assert_condition(len(cases) == len(outputs), "classifier cases/output length mismatch")
    passed = 0
    for case, output in zip(cases, outputs):
        assert_condition(case.get("expected_customer_move_id"), case)
        assert_condition(case.get("example_type") == "synthetic_generic_test_case", case)
        assert_condition(case.get("source_quote") is False and case.get("from_single_transcript") is False, case)
        predicted = output.get("predicted_customer_move_ids", [])
        assert_condition(predicted, output)
        assert_condition(all(move_id in move_ids for move_id in predicted), output)
        if case["expected_customer_move_id"] in predicted:
            passed += 1
    accuracy = round(passed / len(cases), 4)
    assert_condition(accuracy >= 0.80, f"classifier accuracy too low: {accuracy}")
    assert_condition(result["summary"].get("classifier_accuracy") == accuracy, result["summary"])


def validate_retrieval(data: dict[str, Any], source: dict[str, Any], result: dict[str, Any]) -> None:
    cases = get_items(data, "playbook_retrieval_cases")
    playbook_ids = {item["playbook_rule_id"] for item in source["playbook_rules"]}
    eval_ids = {item["evaluation_rule_id"] for item in source["evaluation_rules"]}
    tactic_ids = {item["agent_tactic_id"] for item in source["tactics"]}
    assert_condition(cases, "retrieval cases missing")
    matched = 0
    for case in cases:
        if case.get("retrieval_status") == "matched":
            matched += 1
        assert_condition(all(rule_id in playbook_ids for rule_id in case.get("retrieved_playbook_rule_ids", [])), case)
        assert_condition(all(rule_id in eval_ids for rule_id in case.get("retrieved_evaluation_rule_ids", [])), case)
        assert_condition(all(tactic_id in tactic_ids for tactic_id in case.get("recommended_tactic_sequence", [])), case)
        assert_condition(all(tactic_id in tactic_ids or tactic_id in ABSTRACT_AVOID_TACTICS for tactic_id in case.get("avoid_tactic_ids", [])), case)
    rate = round(matched / len(cases), 4)
    assert_condition(rate >= 0.80, f"retrieval match rate too low: {rate}")
    assert_condition(result["summary"].get("playbook_retrieval_match_rate") == rate, result["summary"])


def validate_evaluations(data: dict[str, Any], source: dict[str, Any], result: dict[str, Any]) -> None:
    cases = get_items(data, "agent_response_evaluation_cases")
    evaluations = get_items(data, "agent_response_evaluations")
    move_ids = {item["customer_move_id"] for item in source["customer_moves"]}
    tactic_ids = {item["agent_tactic_id"] for item in source["tactics"]}
    eval_ids = {item["evaluation_rule_id"] for item in source["evaluation_rules"]}
    assert_condition(cases and evaluations, "evaluation cases and outputs missing")
    assert_condition(len(cases) == len(evaluations), "evaluation case/output length mismatch")
    seen_moves = {case.get("expected_customer_move_id") for case in cases}
    for group in SAFETY_MOVE_GROUPS:
        assert_condition(seen_moves & group, f"missing safety evaluation case for group: {group}")
    matches = 0
    for case, item in zip(cases, evaluations):
        assert_condition(case.get("expected_result") in {"pass", "fail"}, case)
        assert_condition(case.get("example_type") == "synthetic_generic_test_case", case)
        assert_condition(case.get("source_quote") is False and case.get("from_single_transcript") is False, case)
        assert_condition(isinstance(item.get("passed"), bool), item)
        assert_condition(all(move_id in move_ids for move_id in item.get("predicted_customer_move_ids", [])), item)
        assert_condition(all(rule_id in eval_ids for rule_id in item.get("retrieved_evaluation_rule_ids", [])), item)
        assert_condition(all(tactic_id in tactic_ids for tactic_id in item.get("detected_agent_tactic_ids", [])), item)
        if not item["passed"]:
            assert_condition(item.get("failed_check_ids") or item.get("detected_failure_flags"), item)
        if item.get("matches_expected_result"):
            matches += 1
    rate = round(matches / len(evaluations), 4)
    assert_condition(rate >= 0.85, f"expected match rate too low: {rate}")
    assert_condition(result["summary"].get("agent_response_evaluation_expected_match_rate") == rate, result["summary"])


def validate_no_scope_creep() -> None:
    assert_condition(PROD_041A_DIR.exists(), "PROD-041A generated artifacts directory missing")
    forbidden_files = {
        "interaction_traces.json",
        "scenario_diversity_traces.json",
        "scenario_diversity_review.html",
        "scenario_profiles.json",
    }
    existing = {path.name for path in OUT_DIR.iterdir() if path.is_file()}
    assert_condition(not existing & forbidden_files, f"PROD-043 generated forbidden scenario artifact: {existing & forbidden_files}")
    for path in REQUIRED_OUTPUTS.values():
        payload = read_json(path) if path.suffix == ".json" else path.read_text(encoding="utf-8")
        assert_condition(not (all_keys(payload) & FORBIDDEN_FULL_CONVERSATION_KEYS), f"full conversation key found in {path.name}")


def validate_leakage_scan() -> None:
    for path in REQUIRED_OUTPUTS.values():
        text = path.read_text(encoding="utf-8")
        assert_condition(not PHONE_PATTERN.search(text), f"phone-like string found in {path.name}")
        if path.name not in {"runtime_adapter_review.html"}:
            assert_condition(not EMAIL_PATTERN.search(text), f"email-like string found in {path.name}")
        if path.suffix == ".json":
            assert_condition(not LONG_QUOTED_PATTERN.search(text), f"long quoted string found in {path.name}")
        assert_condition("raw transcript quote" not in text.lower(), f"raw transcript quote marker found in {path.name}")


def validate_html() -> None:
    html_text = (OUT_DIR / "runtime_adapter_review.html").read_text(encoding="utf-8").lower()
    for marker in (
        "classifier section",
        "playbook retrieval section",
        "agent evaluation section",
        "safety boundary section",
        "actual agent logic status",
        "filters",
    ):
        assert_condition(marker in html_text, f"missing HTML marker: {marker}")


def validate_docs() -> None:
    for path in (DOC_PATH, COMMANDS_PATH, CHECKPOINT_INDEX_PATH, ROADMAP_PATH, METHODOLOGY_LOG_PATH, DECISION_LOG_PATH):
        text = path.read_text(encoding="utf-8")
        assert_condition("PROD-043" in text or "prod_043" in text, f"missing PROD-043 reference in {path.relative_to(ROOT)}")
    if REFERENCE_REGISTRY_PATH.exists():
        text = REFERENCE_REGISTRY_PATH.read_text(encoding="utf-8")
        assert_condition("PROD-043" in text, "missing PROD-043 reference registry note")


def main() -> None:
    ensure_files_exist()
    source = {
        "customer_moves": get_items(read_json(SOURCE_OUTPUTS["customer_moves"]), "customer_move_patterns"),
        "tactics": get_items(read_json(SOURCE_OUTPUTS["tactics"]), "agent_response_tactics"),
        "playbook_rules": get_items(read_json(SOURCE_OUTPUTS["playbook"]), "sales_playbook_rules"),
        "evaluation_rules": get_items(read_json(SOURCE_OUTPUTS["evaluation"]), "evaluation_rules"),
        "result": read_json(SOURCE_OUTPUTS["result"]),
    }
    result = read_json(REQUIRED_OUTPUTS["result"])
    review = read_json(REQUIRED_OUTPUTS["runtime_adapter_review_data"])
    classifier = read_json(REQUIRED_OUTPUTS["customer_move_classification_cases"])
    retrieval = read_json(REQUIRED_OUTPUTS["playbook_retrieval_cases"])
    eval_cases = read_json(REQUIRED_OUTPUTS["agent_response_evaluation_cases"])
    eval_outputs = read_json(REQUIRED_OUTPUTS["agent_response_evaluations"])
    validate_source_inputs(source)
    validate_boundaries(result)
    validate_classifier(classifier, source, result)
    validate_retrieval(retrieval, source, result)
    validate_evaluations({**eval_cases, **eval_outputs}, source, result)
    validate_no_scope_creep()
    validate_leakage_scan()
    validate_html()
    validate_docs()
    assert_condition(review.get("summary", {}).get("actual_agent_logic_used") == result["summary"]["actual_agent_logic_used"], "review/result actual-agent status mismatch")
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
