#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-042-callcenteren-turn-pattern-playbook"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DOC_PATH = ROOT / "docs" / "product" / "PROD_042_CALLCENTEREN_TURN_PATTERN_PLAYBOOK.md"
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
    "source_pattern_index": OUT_DIR / "source_pattern_index.json",
    "raw_parse_summary": OUT_DIR / "raw_parse_summary.json",
    "customer_move_patterns": OUT_DIR / "customer_move_patterns.json",
    "agent_response_tactics": OUT_DIR / "agent_response_tactics.json",
    "agent_response_quality_patterns": OUT_DIR / "agent_response_quality_patterns.json",
    "customer_reaction_patterns": OUT_DIR / "customer_reaction_patterns.json",
    "customer_state_transition_patterns": OUT_DIR / "customer_state_transition_patterns.json",
    "next_best_action_patterns": OUT_DIR / "next_best_action_patterns.json",
    "failure_patterns": OUT_DIR / "failure_patterns.json",
    "recovery_patterns": OUT_DIR / "recovery_patterns.json",
    "sales_playbook_rules": OUT_DIR / "sales_playbook_rules.json",
    "evaluation_rules": OUT_DIR / "evaluation_rules.json",
    "pattern_review_data": OUT_DIR / "pattern_review_data.json",
    "pattern_review_html": OUT_DIR / "pattern_review.html",
}

BOUNDARY_KEYS = {
    "abstract_pattern_only": True,
    "uses_exact_transcript_text": False,
    "uses_source_transcript_sequence": False,
    "uses_dataset_specific_phrasing": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "dataset_download_performed": False,
    "runtime_behavior_changed": False,
    "production_runtime_promotion_allowed": False,
    "retrieval_enabled": False,
    "runtime_agent_modified": False,
}

SYNTHETIC_SCRIPT_MARKERS = {
    "conversation_sequence",
    "interaction_traces",
    "scenario_diversity_traces",
    "agent_text",
    "customer_text",
    "scenario_diversity_review",
}

PHONE_PATTERN = re.compile(r"\b(?:\+?\d[\d\-\(\) ]{7,}\d)\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.\-]+\s+(street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd)\b",
    re.IGNORECASE,
)
PLACEHOLDER_PII_PATTERN = re.compile(r"\[(PERSON_NAME|PHONE_NUMBER|EMAIL|ADDRESS|ORGANIZATION|LOCATION)\]", re.IGNORECASE)
LONG_QUOTED_PATTERN = re.compile(r"\"[^\"]{220,}\"")

SHARED_EVALUATION_CHECK_IDS = {
    "answers_primary_intent_before_extra_discovery",
    "question_storming_absent",
    "low_pressure_boundary_present_when_resistance",
}

RISK_REACTION_CATEGORIES = {
    "rejects",
    "escalates",
    "sets_boundary",
    "asks_for_support",
    "asks_for_cancellation",
    "says_do_not_contact",
    "hostile_rejection",
}

SAFE_BOUNDARY_TACTICS = {
    "low_pressure_boundary",
    "stop_after_refusal",
    "support_boundary_route",
    "handoff_to_specialist",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def all_strings(value: Any) -> list[str]:
    collected: list[str] = []
    if isinstance(value, str):
        collected.append(value)
        return collected
    if isinstance(value, list):
        for item in value:
            collected.extend(all_strings(item))
        return collected
    if isinstance(value, dict):
        for key, item in value.items():
            collected.append(str(key))
            collected.extend(all_strings(item))
        return collected
    return collected


def ensure_files_exist() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_OUTPUTS.values() if not path.exists()]
    assert_condition(not missing, f"missing required PROD-042 output files: {missing}")
    for required_path in (
        DOC_PATH,
        COMMANDS_PATH,
        CHECKPOINT_INDEX_PATH,
        ROADMAP_PATH,
        METHODOLOGY_LOG_PATH,
        DECISION_LOG_PATH,
    ):
        assert_condition(required_path.exists(), f"missing required doc update: {required_path.relative_to(ROOT)}")


def validate_raw_parse(raw_parse_summary: dict[str, Any]) -> None:
    raw_source_dir = ROOT / raw_parse_summary["raw_source_dir"]
    assert_condition(raw_source_dir.exists(), f"raw source directory missing: {raw_source_dir}")
    assert_condition(raw_parse_summary["zip_file_count"] > 0, raw_parse_summary)
    assert_condition(raw_parse_summary["parsed_zip_file_count"] > 0, raw_parse_summary)
    assert_condition(raw_parse_summary["parsed_inner_file_count"] > 0, raw_parse_summary)
    assert_condition(raw_parse_summary["estimated_record_count"] > 0, raw_parse_summary)
    parsed_types = raw_parse_summary.get("parsed_file_type_counts", {})
    assert_condition(any(int(value) > 0 for value in parsed_types.values()), parsed_types)
    assert_condition(raw_parse_summary.get("raw_text_stored_in_outputs") is False, raw_parse_summary)
    assert_condition(raw_parse_summary.get("abstract_pattern_only") is True, raw_parse_summary)


def validate_boundary_flags(result: dict[str, Any]) -> None:
    summary = result.get("summary", {})
    for key, expected in BOUNDARY_KEYS.items():
        assert_condition(summary.get(key) == expected, f"result.summary[{key}] expected {expected} got {summary.get(key)}")
    method = summary.get("support_count_method", "")
    limitations = summary.get("support_count_limitations", "")
    assert_condition(isinstance(method, str) and method.strip(), "result.summary.support_count_method missing")
    assert_condition(isinstance(limitations, str) and limitations.strip(), "result.summary.support_count_limitations missing")


def validate_no_scenario_generation() -> None:
    filenames = {path.name for path in OUT_DIR.iterdir() if path.is_file()}
    forbidden_names = {
        "interaction_traces.json",
        "scenario_diversity_traces.json",
        "scenario_diversity_review.html",
        "conditional_customer_traces.json",
    }
    assert_condition(not (filenames & forbidden_names), f"forbidden scenario-generation artifact found: {filenames & forbidden_names}")
    assert_condition(PROD_041A_DIR.exists(), "PROD-041A artifact directory missing; checkpoint must not delete prior artifacts")


def compute_playbook_sequence_metrics(playbook_rules: list[dict[str, Any]]) -> tuple[int, float]:
    if not playbook_rules:
        return 0, 0.0
    sequence_counter: Counter[tuple[str, ...]] = Counter()
    for rule in playbook_rules:
        sequence_counter[tuple(rule.get("recommended_tactic_sequence", []))] += 1
    most_common_count = sequence_counter.most_common(1)[0][1]
    most_common_rate = round(most_common_count / len(playbook_rules), 4)
    return most_common_count, most_common_rate


def count_unsafe_next_best_actions(nba_patterns: list[dict[str, Any]]) -> int:
    unsafe_count = 0
    for item in nba_patterns:
        reaction = item.get("after_customer_reaction_category", "")
        recommended = item.get("recommended_next_tactic_ids", [])
        if reaction not in RISK_REACTION_CATEGORIES:
            continue
        if not recommended:
            unsafe_count += 1
            continue
        if recommended[0] == "single_discovery_question":
            unsafe_count += 1
            continue
        if not any(tactic_id in SAFE_BOUNDARY_TACTICS for tactic_id in recommended):
            unsafe_count += 1
    return unsafe_count


def require_rule_by_move(playbook_rules: list[dict[str, Any]], move_id: str) -> dict[str, Any]:
    for rule in playbook_rules:
        if move_id in rule.get("when_customer_move_ids", []):
            return rule
    raise AssertionError(f"missing playbook rule for required move: {move_id}")


def validate_playbook_specificity(playbook_rules: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    price_rule = require_rule_by_move(playbook_rules, "price_first")
    price_sequence = price_rule.get("recommended_tactic_sequence", [])
    assert_condition(len(price_sequence) >= 2, f"price_first playbook sequence too short: {price_rule}")
    assert_condition(price_sequence[0] == "answer_directly", f"price_first must start with answer_directly: {price_rule}")
    assert_condition(price_sequence[1] == "low_pressure_boundary", f"price_first second tactic must be low_pressure_boundary: {price_rule}")

    email_rule = require_rule_by_move(playbook_rules, "email_only")
    email_sequence = email_rule.get("recommended_tactic_sequence", [])
    assert_condition("written_info_offer" in email_sequence, f"email_only must include written_info_offer: {email_rule}")
    assert_condition("callback_offer" not in email_sequence, f"email_only must not push callback: {email_rule}")

    not_interested_rule = require_rule_by_move(playbook_rules, "not_interested")
    hostile_rule = require_rule_by_move(playbook_rules, "hostile_rejection")
    assert_condition(
        "single_discovery_question" not in not_interested_rule.get("recommended_tactic_sequence", []),
        f"not_interested must not recommend discovery without permission: {not_interested_rule}",
    )
    assert_condition(
        "single_discovery_question" not in hostile_rule.get("recommended_tactic_sequence", []),
        f"hostile_rejection must not recommend discovery without permission: {hostile_rule}",
    )

    support_rule = require_rule_by_move(playbook_rules, "support_issue")
    cancellation_rule = require_rule_by_move(playbook_rules, "cancellation_request")
    support_tactics = set(support_rule.get("recommended_tactic_sequence", []))
    cancellation_tactics = set(cancellation_rule.get("recommended_tactic_sequence", []))
    assert_condition(
        bool(support_tactics & {"support_boundary_route", "handoff_to_specialist"}),
        f"support_issue must include safe routing/handoff: {support_rule}",
    )
    assert_condition(
        bool(cancellation_tactics & {"support_boundary_route", "handoff_to_specialist"}),
        f"cancellation_request must include safe routing/handoff: {cancellation_rule}",
    )

    technical_rule = require_rule_by_move(playbook_rules, "technical_question")
    security_rule = require_rule_by_move(playbook_rules, "security_review")
    healthcare_rule = require_rule_by_move(playbook_rules, "sensitive_healthcare_concern")
    assert_condition(
        bool(set(technical_rule.get("recommended_tactic_sequence", [])) & {"handoff_to_specialist", "low_pressure_boundary"}),
        f"technical_question must include specialist/handoff or safe boundary logic: {technical_rule}",
    )
    assert_condition(
        bool(set(security_rule.get("recommended_tactic_sequence", [])) & {"handoff_to_specialist", "written_info_offer", "low_pressure_boundary"}),
        f"security_review must include safe specialist/handoff logic: {security_rule}",
    )
    assert_condition(
        bool(set(healthcare_rule.get("recommended_tactic_sequence", [])) & {"handoff_to_specialist", "low_pressure_boundary", "risk_reversal"}),
        f"sensitive_healthcare_concern must include safe specialist/handoff logic: {healthcare_rule}",
    )

    computed_count, computed_rate = compute_playbook_sequence_metrics(playbook_rules)
    assert_condition(summary.get("most_common_playbook_sequence_count") == computed_count, "most_common_playbook_sequence_count mismatch")
    assert_condition(abs(float(summary.get("most_common_playbook_sequence_rate", -1.0)) - computed_rate) < 1e-6, "most_common_playbook_sequence_rate mismatch")
    if len(playbook_rules) >= 5:
        assert_condition(computed_rate < 0.40, f"most_common_playbook_sequence_rate must be < 0.40, got {computed_rate}")


def validate_evaluation_specificity(evaluation_rules: list[dict[str, Any]]) -> None:
    check_sets: Counter[tuple[str, ...]] = Counter()
    for rule in evaluation_rules:
        checks = rule.get("checks", [])
        check_ids = [check.get("check_id", "") for check in checks if isinstance(check, dict)]
        specific_check_ids = [check_id for check_id in check_ids if check_id not in SHARED_EVALUATION_CHECK_IDS]
        assert_condition(len(specific_check_ids) >= 1, f"evaluation rule missing move-specific checks: {rule}")
        declared_specific = rule.get("move_specific_check_count")
        if declared_specific is not None:
            assert_condition(int(declared_specific) >= 1, f"evaluation rule move_specific_check_count must be >=1: {rule}")
        check_key = tuple(sorted(check_ids))
        check_sets[check_key] += 1
    duplicates = [check_key for check_key, count in check_sets.items() if count > 1]
    assert_condition(not duplicates, f"evaluation rules have identical check sets: {duplicates}")


def validate_support_count_metadata_across_payloads(payloads: dict[str, dict[str, Any]]) -> None:
    required_payloads = {
        "source_pattern_index",
        "customer_move_patterns",
        "agent_response_tactics",
        "agent_response_quality_patterns",
        "customer_reaction_patterns",
        "customer_state_transition_patterns",
        "next_best_action_patterns",
        "failure_patterns",
        "recovery_patterns",
        "sales_playbook_rules",
        "evaluation_rules",
        "pattern_review_data",
    }
    for payload_name in required_payloads:
        payload = payloads[payload_name]
        assert_condition(payload.get("support_count_method"), f"{payload_name} missing support_count_method")
        assert_condition(payload.get("support_count_limitations"), f"{payload_name} missing support_count_limitations")


def validate_pattern_ids_and_references(payloads: dict[str, dict[str, Any]], result_summary: dict[str, Any]) -> None:
    move_patterns = payloads["customer_move_patterns"]["customer_move_patterns"]
    tactic_patterns = payloads["agent_response_tactics"]["agent_response_tactics"]
    quality_patterns = payloads["agent_response_quality_patterns"]["agent_response_quality_patterns"]
    reaction_patterns = payloads["customer_reaction_patterns"]["customer_reaction_patterns"]
    state_patterns = payloads["customer_state_transition_patterns"]["customer_state_transition_patterns"]
    nba_patterns = payloads["next_best_action_patterns"]["next_best_action_patterns"]
    failure_patterns = payloads["failure_patterns"]["failure_patterns"]
    recovery_patterns = payloads["recovery_patterns"]["recovery_patterns"]
    playbook_rules = payloads["sales_playbook_rules"]["sales_playbook_rules"]
    evaluation_rules = payloads["evaluation_rules"]["evaluation_rules"]

    move_ids = {item["customer_move_id"] for item in move_patterns}
    tactic_ids = {item["agent_tactic_id"] for item in tactic_patterns}
    failure_ids = {item["failure_pattern_id"] for item in failure_patterns}

    def check_support(item: dict[str, Any], artifact_name: str, pattern_id: str) -> None:
        support = item.get("source_support")
        assert_condition(isinstance(support, dict), f"{artifact_name} missing source_support: {pattern_id}")
        assert_condition("support_count_estimate" in support, f"{artifact_name} missing support_count_estimate: {pattern_id}")
        count = int(support["support_count_estimate"])
        assert_condition("source_pattern_ids" in support and isinstance(support["source_pattern_ids"], list), f"{artifact_name} missing source_pattern_ids: {pattern_id}")
        assert_condition("source_file_refs" in support and isinstance(support["source_file_refs"], list), f"{artifact_name} missing source_file_refs: {pattern_id}")
        for ref in support["source_file_refs"]:
            assert_condition("source_file" in ref and "source_hash" in ref, f"{artifact_name} malformed source_file_ref: {pattern_id}")
            assert_condition("sha256:" in ref["source_hash"], f"{artifact_name} source hash missing sha256 prefix: {pattern_id}")
        if count == 0:
            assert_condition(item.get("confidence") == "low", f"{artifact_name} zero support must be low confidence: {pattern_id}")
        if count > 0:
            assert_condition(len(support["source_pattern_ids"]) > 0, f"{artifact_name} positive support needs source_pattern_ids: {pattern_id}")
            assert_condition(len(support["source_file_refs"]) > 0, f"{artifact_name} positive support needs source_file_refs: {pattern_id}")

    for item in move_patterns:
        assert_condition(item.get("customer_move_id"), item)
        assert_condition(item.get("description"), item)
        assert_condition("confidence" in item, item)
        for boundary_key in ("abstract_pattern_only", "uses_exact_transcript_text", "uses_source_transcript_sequence", "uses_dataset_specific_phrasing"):
            assert_condition(boundary_key in item, f"customer_move missing boundary key {boundary_key}: {item.get('customer_move_id')}")
        check_support(item, "customer_move_patterns", item["customer_move_id"])

    for item in tactic_patterns:
        assert_condition(item.get("agent_tactic_id"), item)
        assert_condition(item.get("description"), item)
        assert_condition("confidence" in item, item)
        for boundary_key in ("abstract_pattern_only", "uses_exact_transcript_text"):
            assert_condition(boundary_key in item, f"agent_tactic missing boundary key {boundary_key}: {item.get('agent_tactic_id')}")
        check_support(item, "agent_response_tactics", item["agent_tactic_id"])
        support_count = int(item["source_support"]["support_count_estimate"])
        unsupported_target = bool(item.get("unsupported_target"))
        if support_count == 0:
            assert_condition(unsupported_target is True, f"zero-support tactic must set unsupported_target=true: {item}")
            assert_condition(item.get("confidence") == "low", f"zero-support tactic must be low confidence: {item}")
        else:
            assert_condition(unsupported_target is False, f"supported tactic must set unsupported_target=false: {item}")

    for item in quality_patterns:
        assert_condition(item["customer_move_id"] in move_ids, f"quality pattern move reference invalid: {item}")
        assert_condition(item["agent_tactic_id"] in tactic_ids, f"quality pattern tactic reference invalid: {item}")
        check_support(item, "agent_response_quality_patterns", item["response_quality_pattern_id"])

    for item in reaction_patterns:
        assert_condition(item["customer_move_id"] in move_ids, f"reaction pattern move reference invalid: {item}")
        assert_condition(item["agent_tactic_id"] in tactic_ids, f"reaction pattern tactic reference invalid: {item}")
        check_support(item, "customer_reaction_patterns", item["customer_reaction_pattern_id"])

    for item in state_patterns:
        assert_condition(item["customer_move_id"] in move_ids, f"state transition move reference invalid: {item}")
        assert_condition(item["agent_tactic_id"] in tactic_ids, f"state transition tactic reference invalid: {item}")
        check_support(item, "customer_state_transition_patterns", item["state_transition_id"])

    for item in nba_patterns:
        assert_condition(item["after_customer_move_id"] in move_ids, f"next_best_action move reference invalid: {item}")
        assert_condition(item["after_agent_tactic_id"] in tactic_ids, f"next_best_action tactic reference invalid: {item}")
        for tactic_id in item.get("recommended_next_tactic_ids", []):
            assert_condition(tactic_id in tactic_ids, f"next_best_action recommended tactic unknown: {item}")
        check_support(item, "next_best_action_patterns", item["next_best_action_id"])

    recovery_by_failure = {item["failure_pattern_id"] for item in recovery_patterns}
    for item in failure_patterns:
        assert_condition(item.get("detectable_signals_abstract"), f"failure pattern missing detectable signals: {item}")
        assert_condition(item["failure_pattern_id"] in failure_ids, item)
        assert_condition(item["failure_pattern_id"] in recovery_by_failure or int(item["source_support"]["support_count_estimate"]) == 0, f"failure pattern missing recovery linkage: {item['failure_pattern_id']}")
        check_support(item, "failure_patterns", item["failure_pattern_id"])

    for item in recovery_patterns:
        assert_condition(item["failure_pattern_id"] in failure_ids, f"recovery pattern references unknown failure: {item}")
        for tactic_id in item.get("recovery_tactic_ids", []):
            assert_condition(tactic_id in tactic_ids, f"recovery pattern references unknown tactic_id: {item}")
        assert_condition("uses_unsupported_target_tactic" in item, f"recovery pattern missing uses_unsupported_target_tactic: {item}")
        assert_condition("unsupported_recovery_tactic_ids" in item, f"recovery pattern missing unsupported_recovery_tactic_ids: {item}")
        assert_condition(
            isinstance(item.get("unsupported_recovery_tactic_ids"), list),
            f"recovery pattern unsupported_recovery_tactic_ids must be list: {item}",
        )
        unsupported_recovery_tactic_ids = item.get("unsupported_recovery_tactic_ids", [])
        for tactic_id in unsupported_recovery_tactic_ids:
            assert_condition(tactic_id in tactic_ids, f"recovery pattern unsupported tactic id unknown: {item}")
            tactic_entry = next((t for t in tactic_patterns if t["agent_tactic_id"] == tactic_id), None)
            assert_condition(tactic_entry is not None, f"recovery unsupported tactic id not found in tactics: {item}")
            assert_condition(
                tactic_entry.get("unsupported_target") is True,
                f"recovery unsupported tactic id must map to unsupported_target=true tactic: {item}",
            )
        uses_unsupported = bool(item.get("uses_unsupported_target_tactic", False))
        assert_condition(
            uses_unsupported == (len(unsupported_recovery_tactic_ids) > 0),
            f"recovery pattern unsupported tactic flags inconsistent: {item}",
        )
        if uses_unsupported:
            assert_condition(item.get("confidence") in {"low", "medium"}, f"recovery with unsupported tactics cannot be high confidence: {item}")
        check_support(item, "recovery_patterns", item["recovery_pattern_id"])

    for item in playbook_rules:
        move_refs = item.get("when_customer_move_ids", [])
        assert_condition(move_refs and all(move_id in move_ids for move_id in move_refs), f"playbook rule move reference invalid: {item}")
        tactic_refs = item.get("recommended_tactic_sequence", [])
        assert_condition(tactic_refs and all(tactic_id in tactic_ids for tactic_id in tactic_refs), f"playbook rule tactic reference invalid: {item}")
        assert_condition(item.get("rag_chunk", {}).get("runtime_enabled_now") is False, f"playbook rule runtime must stay disabled: {item}")

    playbook_ids = {item["playbook_rule_id"] for item in playbook_rules}
    for item in evaluation_rules:
        assert_condition(item["customer_move_id"] in move_ids, f"evaluation rule move reference invalid: {item}")
        assert_condition(item.get("deterministic_only") is True, f"evaluation rule must be deterministic: {item}")
        assert_condition(item.get("llm_judging_required") is False, f"evaluation rule must not require LLM judging: {item}")
        for rule_id in item.get("source_playbook_rule_ids", []):
            assert_condition(rule_id in playbook_ids, f"evaluation rule source_playbook_rule_ids invalid: {item}")

    validate_playbook_specificity(playbook_rules, result_summary)
    validate_evaluation_specificity(evaluation_rules)

    unsafe_next_best_action_count = count_unsafe_next_best_actions(nba_patterns)
    assert_condition(result_summary.get("unsafe_next_best_action_count") == unsafe_next_best_action_count, "unsafe_next_best_action_count mismatch")
    assert_condition(unsafe_next_best_action_count == 0, f"unsafe_next_best_action_count must be 0, got {unsafe_next_best_action_count}")

    supported_tactics = [item for item in tactic_patterns if not item.get("unsupported_target", False)]
    unsupported_tactics = [item for item in tactic_patterns if item.get("unsupported_target", False)]
    unsupported_target_tactic_ids = [item["agent_tactic_id"] for item in unsupported_tactics]
    assert_condition(
        result_summary.get("supported_agent_response_tactic_count") == len(supported_tactics),
        "supported_agent_response_tactic_count mismatch",
    )
    assert_condition(
        result_summary.get("unsupported_agent_response_tactic_count") == len(unsupported_tactics),
        "unsupported_agent_response_tactic_count mismatch",
    )
    assert_condition(
        sorted(result_summary.get("unsupported_target_tactic_ids", [])) == sorted(unsupported_target_tactic_ids),
        "unsupported_target_tactic_ids mismatch",
    )
    recovery_patterns_using_unsupported_tactics_count = sum(
        1 for item in recovery_patterns if bool(item.get("uses_unsupported_target_tactic", False))
    )
    assert_condition(
        result_summary.get("recovery_patterns_using_unsupported_tactics_count") == recovery_patterns_using_unsupported_tactics_count,
        "recovery_patterns_using_unsupported_tactics_count mismatch",
    )

    for payload_name, payload in payloads.items():
        coverage_gaps = payload.get("coverage_gaps")
        assert_condition(isinstance(coverage_gaps, list), f"{payload_name} missing coverage_gaps list")


def validate_leakage(payloads: dict[str, dict[str, Any]]) -> None:
    texts: list[str] = []
    for payload in payloads.values():
        texts.extend(all_strings(payload))
    for text in texts:
        assert_condition(not PHONE_PATTERN.search(text), f"possible phone number leakage detected: {text[:120]}")
        assert_condition(not EMAIL_PATTERN.search(text), f"possible email leakage detected: {text[:120]}")
        assert_condition(not ADDRESS_PATTERN.search(text), f"possible address leakage detected: {text[:120]}")
        assert_condition(not PLACEHOLDER_PII_PATTERN.search(text), f"PII placeholder leakage detected: {text[:120]}")
    joined = "\n".join(texts)
    assert_condition(not LONG_QUOTED_PATTERN.search(joined), "long quoted string detected; possible raw snippet leakage")
    assert_condition("raw transcript text" not in joined.lower() or "uses_exact_transcript_text" in joined.lower(), "unexpected raw transcript phrasing in payload")


def validate_no_script_markers() -> None:
    for path in REQUIRED_OUTPUTS.values():
        if path.suffix.lower() not in {".json", ".html", ".md"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marker in SYNTHETIC_SCRIPT_MARKERS:
            assert_condition(marker not in content, f"forbidden synthetic-script marker detected in {path.name}: {marker}")
        assert_condition("realistic human dialogue" not in content, f"forbidden dialogue-claim phrase detected in {path.name}")


def validate_html(review_html: str) -> None:
    required_sections = [
        "Customer Move Section",
        "Agent Tactic Section",
        "Response Quality Section",
        "Customer Reaction Section",
        "State Transition Section",
        "Next-Best-Action Section",
        "Failure Recovery Section",
        "Playbook Section",
        "Evaluation Rules Section",
        "Coverage Gaps Section",
        "Safety Boundary Summary",
        "Filters",
    ]
    for section in required_sections:
        assert_condition(section.lower() in review_html.lower(), f"missing HTML section: {section}")
    assert_condition("source_quote\": false".lower() in review_html.lower(), "HTML must include sanitized example source_quote markers")
    assert_condition("from_single_transcript\": false".lower() in review_html.lower(), "HTML must include sanitized example transcript-origin markers")
    assert_condition("[person_name]" not in review_html.lower(), "HTML contains redacted placeholder from source")
    assert_condition("support-count note" in review_html.lower(), "HTML missing visible support-count limitation note")
    assert_condition("heuristic aggregate signal counts" in review_html.lower(), "HTML must state support counts are heuristic aggregate counts")
    assert_condition("not verified labeled success counts" in review_html.lower(), "HTML must state support counts are not verified success labels")


def validate_support_count_disclosures(result: dict[str, Any], report_text: str) -> None:
    summary = result.get("summary", {})
    method = str(summary.get("support_count_method", "")).strip()
    limitations = str(summary.get("support_count_limitations", "")).strip()
    assert_condition(method, "result.summary.support_count_method missing")
    assert_condition(limitations, "result.summary.support_count_limitations missing")
    lowered_report = report_text.lower()
    assert_condition("support_count_method" in lowered_report, "report.md missing support_count_method disclosure")
    assert_condition("support_count_limitations" in lowered_report, "report.md missing support_count_limitations disclosure")
    assert_condition("not a verified labeled success count" in lowered_report, "report.md missing explicit support-count limitation wording")


def validate_docs_updates() -> None:
    commands = COMMANDS_PATH.read_text(encoding="utf-8")
    checkpoint_index = CHECKPOINT_INDEX_PATH.read_text(encoding="utf-8")
    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    methodology = METHODOLOGY_LOG_PATH.read_text(encoding="utf-8")
    decisions = DECISION_LOG_PATH.read_text(encoding="utf-8")
    doc = DOC_PATH.read_text(encoding="utf-8")

    assert_condition("run_prod_042_callcenteren_turn_pattern_playbook.py" in commands, "COMMANDS.md missing PROD-042 run command")
    assert_condition("validate_prod_042_callcenteren_turn_pattern_playbook.py" in commands, "COMMANDS.md missing PROD-042 validate command")
    assert_condition("PROD_042_CALLCENTEREN_TURN_PATTERN_PLAYBOOK.md" in checkpoint_index, "CHECKPOINT_INDEX.md missing PROD-042 doc")
    assert_condition("PROD-042" in roadmap, "ROADMAP.md missing PROD-042 entry")
    assert_condition("PROD-042" in methodology, "METHODOLOGY_LOG.md missing PROD-042 entry")
    assert_condition("PROD-042" in decisions, "DECISION_LOG.md missing PROD-042 decision entry")
    if REFERENCE_REGISTRY_PATH.exists():
        registry_text = REFERENCE_REGISTRY_PATH.read_text(encoding="utf-8")
        assert_condition("PROD-042" in registry_text, "THESIS_REFERENCE_REGISTRY.md missing PROD-042 update")
    assert_condition("PROD-043-sales-playbook-runtime-adapter" in doc, "PROD-042 product doc missing next checkpoint reference")
    prod_041a_doc = ROOT / "docs" / "product" / "PROD_041A_CONDITIONAL_SCENARIO_DIVERSITY_EXPANSION.md"
    if prod_041a_doc.exists():
        prod041a = prod_041a_doc.read_text(encoding="utf-8")
        assert_condition("PROD-042" in prod041a and "paused" in prod041a.lower(), "PROD-041A doc missing short pause/supersede note")


def main() -> None:
    ensure_files_exist()

    result = read_json(REQUIRED_OUTPUTS["result"])
    raw_parse_summary = read_json(REQUIRED_OUTPUTS["raw_parse_summary"])
    source_pattern_index = read_json(REQUIRED_OUTPUTS["source_pattern_index"])
    customer_move_patterns = read_json(REQUIRED_OUTPUTS["customer_move_patterns"])
    agent_response_tactics = read_json(REQUIRED_OUTPUTS["agent_response_tactics"])
    agent_response_quality_patterns = read_json(REQUIRED_OUTPUTS["agent_response_quality_patterns"])
    customer_reaction_patterns = read_json(REQUIRED_OUTPUTS["customer_reaction_patterns"])
    customer_state_transition_patterns = read_json(REQUIRED_OUTPUTS["customer_state_transition_patterns"])
    next_best_action_patterns = read_json(REQUIRED_OUTPUTS["next_best_action_patterns"])
    failure_patterns = read_json(REQUIRED_OUTPUTS["failure_patterns"])
    recovery_patterns = read_json(REQUIRED_OUTPUTS["recovery_patterns"])
    sales_playbook_rules = read_json(REQUIRED_OUTPUTS["sales_playbook_rules"])
    evaluation_rules = read_json(REQUIRED_OUTPUTS["evaluation_rules"])
    pattern_review_data = read_json(REQUIRED_OUTPUTS["pattern_review_data"])
    review_html = REQUIRED_OUTPUTS["pattern_review_html"].read_text(encoding="utf-8")
    report_text = REQUIRED_OUTPUTS["report"].read_text(encoding="utf-8")

    payloads = {
        "source_pattern_index": source_pattern_index,
        "raw_parse_summary": raw_parse_summary,
        "customer_move_patterns": customer_move_patterns,
        "agent_response_tactics": agent_response_tactics,
        "agent_response_quality_patterns": agent_response_quality_patterns,
        "customer_reaction_patterns": customer_reaction_patterns,
        "customer_state_transition_patterns": customer_state_transition_patterns,
        "next_best_action_patterns": next_best_action_patterns,
        "failure_patterns": failure_patterns,
        "recovery_patterns": recovery_patterns,
        "sales_playbook_rules": sales_playbook_rules,
        "evaluation_rules": evaluation_rules,
        "pattern_review_data": pattern_review_data,
    }

    assert_condition(result.get("checkpoint_id") == CHECKPOINT_ID, result.get("checkpoint_id"))
    validate_raw_parse(raw_parse_summary)
    validate_boundary_flags(result)
    validate_no_scenario_generation()
    validate_pattern_ids_and_references(payloads, result.get("summary", {}))
    validate_support_count_metadata_across_payloads(payloads)
    validate_leakage(payloads)
    validate_no_script_markers()
    validate_html(review_html)
    validate_support_count_disclosures(result, report_text)
    validate_docs_updates()

    print("PROD-042 callcenteren turn-level pattern playbook validation passed.")


if __name__ == "__main__":
    main()
