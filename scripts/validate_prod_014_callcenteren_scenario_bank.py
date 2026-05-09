#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_scenario_bank.py"
RUNNER = ROOT / "scripts" / "run_prod_014_callcenteren_scenario_bank.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_014_CALLCENTEREN_SCENARIO_BANK.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
TMP_DIR = ROOT / ".tmp" / "prod-014-callcenteren-scenario-bank"
PATTERN_BANK = TMP_DIR / "prod-013-pattern-bank-fixture.json"
RESULT_PATH = TMP_DIR / "scenario-bank.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-014-callcenteren-scenario-bank"
EXPECTED_SOURCE_ID = "PROD-013-callcenteren-pattern-extraction"
EXPECTED_DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
EXPECTED_PAPER_URL = "https://arxiv.org/abs/2507.02958"
EXPECTED_LICENSE = "cc-by-nc-4.0"
EXPECTED_LABELS = {
    "sale_eligible",
    "price_objection",
    "callback_request",
    "cancellation_boundary",
    "support_handoff",
    "trust_repair",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_pattern_bank() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "prod_013_id": EXPECTED_SOURCE_ID,
        "dataset_source": {
            "dataset_name": "AIxBlock/92k-real-world-call-center-scripts-english",
            "dataset_url": EXPECTED_DATASET_URL,
            "dataset_file_tree": EXPECTED_DATASET_URL + "/tree/main",
            "paper_url": EXPECTED_PAPER_URL,
            "license": EXPECTED_LICENSE,
        },
        "source_characteristics": {
            "speaker_role_signal_inference": True,
            "speaker_role_inference_is_ground_truth": False,
            "raw_text_field_exported": False,
        },
        "reuse_boundary": {
            "reuse_label": "abstract_pattern_extraction_only",
            "raw_transcript_text_stored": False,
            "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        },
        "summary": {
            "source_file_count": 44,
            "conversation_count": 40,
            "turn_count": 280,
            "leakage_finding_count": 0,
        },
        "pattern_bank": {
            "scenario_templates": [
                {
                    "template_id": "scenario-buying_interest-001",
                    "customer_persona": "uncertain_buyer",
                    "initial_intent": "buying_interest",
                    "likely_objection": "too_expensive",
                    "emotion_state": "interested",
                    "safe_agent_tactic": "ask one discovery question before closing",
                    "avoid": ["vague_claim", "talks_too_much", "premature_close"],
                    "success_label": "verbal_interested",
                    "conversation_flow": ["opening", "discovery", "price_discussion", "trial_close"],
                },
                {
                    "template_id": "scenario-price_request-002",
                    "customer_persona": "price_sensitive_buyer",
                    "initial_intent": "price_request",
                    "likely_objection": "too_expensive",
                    "emotion_state": "skeptical",
                    "safe_agent_tactic": "clarify price versus value blocker",
                    "avoid": ["vague_claim", "talks_too_much", "premature_close"],
                    "success_label": "next_useful_step_agreed",
                    "conversation_flow": ["opening", "discovery", "price_discussion", "objection_handling"],
                },
                {
                    "template_id": "scenario-callback_request-003",
                    "customer_persona": "uncertain_buyer",
                    "initial_intent": "callback_request",
                    "likely_objection": "no_time",
                    "emotion_state": "neutral",
                    "safe_agent_tactic": "confirm callback details",
                    "avoid": ["vague_claim", "talks_too_much", "premature_close"],
                    "success_label": "callback_agreed",
                    "conversation_flow": ["opening", "permission_to_continue", "callback_scheduling"],
                },
                {
                    "template_id": "scenario-cancellation-004",
                    "customer_persona": "boundary_setting_customer",
                    "initial_intent": "cancellation",
                    "likely_objection": "contract_fear",
                    "emotion_state": "annoyed",
                    "safe_agent_tactic": "respect boundary before any retention path",
                    "avoid": ["pushy", "premature_close", "ignores_customer_need"],
                    "success_label": "boundary_respected",
                    "conversation_flow": ["opening", "clarification", "wrap_up"],
                },
                {
                    "template_id": "scenario-technical_problem-005",
                    "customer_persona": "support_first_customer",
                    "initial_intent": "technical_problem",
                    "likely_objection": "bad_previous_experience",
                    "emotion_state": "angry",
                    "safe_agent_tactic": "handoff instead of guessing",
                    "avoid": ["unsupported_claim", "does_not_escalate_when_needed"],
                    "success_label": "handoff_or_issue_path_accepted",
                    "conversation_flow": ["opening", "problem_identification", "handoff"],
                },
                {
                    "template_id": "scenario-billing_issue-006",
                    "customer_persona": "support_first_customer",
                    "initial_intent": "billing_issue",
                    "likely_objection": "does_not_trust_agent",
                    "emotion_state": "annoyed",
                    "safe_agent_tactic": "confirm understanding then route to billing support",
                    "avoid": ["unsupported_claim", "does_not_escalate_when_needed"],
                    "success_label": "handoff_or_issue_path_accepted",
                    "conversation_flow": ["opening", "clarification", "escalation"],
                },
            ],
            "domain_specific_scenario_patterns": [
                {
                    "domain": "insurance",
                    "call_count": 12,
                    "turn_count": 84,
                    "common_customer_intents": {"buying_interest": 8, "price_request": 6, "cancellation": 2},
                    "common_objections": {"too_expensive": 7, "contract_fear": 3, "payment_fear": 2},
                    "common_required_information": ["customer_goal", "budget_or_price_sensitivity", "permission_to_continue"],
                    "common_close_types": {"trial_close": 5, "callback_close": 2},
                    "common_escalation_triggers": {"escalate_or_handoff": 2},
                    "typical_emotional_tone": "neutral",
                },
                {
                    "domain": "home_service",
                    "call_count": 10,
                    "turn_count": 70,
                    "common_customer_intents": {"technical_problem": 5, "callback_request": 3, "buying_interest": 2},
                    "common_objections": {"bad_previous_experience": 4, "no_time": 3},
                    "common_required_information": ["support_context_before_sale", "customer_goal"],
                    "common_close_types": {"handoff_close": 3, "soft_close": 2},
                    "common_escalation_triggers": {"escalate_or_handoff": 4},
                    "typical_emotional_tone": "annoyed",
                },
            ],
            "opening_patterns": [
                {
                    "pattern_id": "opening-agent-led-001",
                    "opening_type": "agent_led_outbound",
                    "greeting_style": "polite_greeting",
                    "permission_to_continue": "permission_or_time_check",
                }
            ],
            "customer_intent_patterns": [
                {"pattern_id": "intent-buying_interest-001", "intent_label": "buying_interest", "count": 8},
                {"pattern_id": "intent-price_request-002", "intent_label": "price_request", "count": 6},
                {"pattern_id": "intent-callback_request-003", "intent_label": "callback_request", "count": 3},
                {"pattern_id": "intent-cancellation-004", "intent_label": "cancellation", "count": 2},
                {"pattern_id": "intent-technical_problem-005", "intent_label": "technical_problem", "count": 5},
                {"pattern_id": "intent-billing_issue-006", "intent_label": "billing_issue", "count": 2},
            ],
            "objection_patterns": [
                {"pattern_id": "objection-too_expensive-001", "objection_type": "too_expensive", "emotion_signal": "skeptical", "agent_response_tactic": "pain_point_discovery"},
                {"pattern_id": "objection-contract_fear-002", "objection_type": "contract_fear", "emotion_signal": "annoyed", "agent_response_tactic": "risk_reversal"},
                {"pattern_id": "objection-bad_previous_experience-003", "objection_type": "bad_previous_experience", "emotion_signal": "angry", "agent_response_tactic": "empathy_first"},
                {"pattern_id": "objection-no_time-004", "objection_type": "no_time", "emotion_signal": "neutral", "agent_response_tactic": "callback_close"},
                {"pattern_id": "objection-does_not_trust_agent-005", "objection_type": "does_not_trust_agent", "emotion_signal": "skeptical", "agent_response_tactic": "empathy_first"},
            ],
            "emotion_tone_transition_patterns": [
                {"pattern_id": "emotion-skeptical_to_open-001", "transition_label": "skeptical_to_open", "agent_tactic": "empathy_first"},
                {"pattern_id": "emotion-angry_to_de_escalated-002", "transition_label": "angry_to_de_escalated", "agent_tactic": "handoff_close"},
            ],
            "persuasion_strategy_patterns": [
                {"pattern_id": "persuasion-pain_point_discovery-001", "strategy_label": "pain_point_discovery", "avoid_label": "premature_close"},
                {"pattern_id": "persuasion-empathy_first-002", "strategy_label": "empathy_first", "avoid_label": "pushy"},
            ],
            "discovery_question_patterns": [
                {"pattern_id": "discovery-current_problem_question-001", "question_type": "current_problem_question", "count": 5},
                {"pattern_id": "discovery-budget_question-002", "question_type": "budget_question", "count": 4},
                {"pattern_id": "discovery-eligibility_question-003", "question_type": "eligibility_question", "count": 3},
            ],
            "turn_stage_patterns": [
                {"pattern_id": "stage-opening-001", "stage_label": "opening", "count": 8},
                {"pattern_id": "stage-discovery-002", "stage_label": "discovery", "count": 7},
                {"pattern_id": "stage-objection_handling-003", "stage_label": "objection_handling", "count": 4},
                {"pattern_id": "stage-callback_scheduling-004", "stage_label": "callback_scheduling", "count": 2},
                {"pattern_id": "stage-escalation-005", "stage_label": "escalation", "count": 2},
            ],
            "close_attempt_patterns": [
                {"pattern_id": "close-trial_close-001", "close_type": "trial_close", "commitment_level": "verbal_interested", "safe_close": True},
                {"pattern_id": "close-callback_close-002", "close_type": "callback_close", "commitment_level": "callback_agreed", "safe_close": True},
                {"pattern_id": "close-handoff_close-003", "close_type": "handoff_close", "commitment_level": "information_requested", "safe_close": True},
            ],
            "safety_compliance_boundary_patterns": [
                {"pattern_id": "safety-escalate_or_handoff-001", "boundary_label": "escalate_or_handoff", "count": 4},
                {"pattern_id": "safety-stop_selling_or_suppress_contact-002", "boundary_label": "stop_selling_or_suppress_contact", "count": 2},
            ],
            "agent_mistake_patterns": [
                {"pattern_id": "mistake-closes_too_early-001", "mistake_label": "closes_too_early", "count": 3},
                {"pattern_id": "mistake-ignores_customer_emotion-002", "mistake_label": "ignores_customer_emotion", "count": 2},
            ],
            "customer_personas": [
                {"pattern_id": "persona-uncertain_buyer-001", "persona_label": "uncertain_buyer", "count": 8},
                {"pattern_id": "persona-support_first_customer-002", "persona_label": "support_first_customer", "count": 5},
            ],
            "timing_speech_naturalness_patterns": {
                "timestamps_available": True,
                "average_agent_turn_words": 11.5,
                "average_customer_turn_words": 7.2,
                "pause_before_agent_response_ms": 840,
                "interruption_count": 0,
                "overlong_agent_monologue_count": 1,
                "rapid_fire_question_count": 1,
                "silence_after_offer_count": 2,
                "silence_after_price_count": 1,
            },
        },
        "leakage_tests": {"findings": []},
    }
    PATTERN_BANK.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=120)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_014_id"] == EXPECTED_ID, payload)
    assert_condition(payload["source_pattern_bank"]["prod_013_id"] == EXPECTED_SOURCE_ID, payload["source_pattern_bank"])
    assert_condition(payload["dataset_source"]["dataset_url"] == EXPECTED_DATASET_URL, payload["dataset_source"])
    assert_condition(payload["dataset_source"]["paper_url"] == EXPECTED_PAPER_URL, payload["dataset_source"])
    assert_condition(payload["dataset_source"]["license"] == EXPECTED_LICENSE, payload["dataset_source"])
    assert_condition(payload["reuse_boundary"]["reuse_label"] == "abstract_scenario_bank_only", payload["reuse_boundary"])
    assert_condition(payload["reuse_boundary"]["raw_transcript_text_stored"] is False, payload["reuse_boundary"])
    assert_condition(payload["reuse_boundary"]["commercial_runtime_prompt_text_from_transcripts_allowed"] is False, payload["reuse_boundary"])

    summary = payload["summary"]
    assert_condition(summary["scenario_count"] >= 48, summary)
    assert_condition(summary["turn_count"] >= 144, summary)
    assert_condition(summary["scenario_count_requested"] >= 48, summary)
    assert_condition(summary["unique_scenario_recipe_count"] >= 24, summary)
    assert_condition(summary["source_pattern_variant_count"] >= 48, summary)
    assert_condition(summary["available_source_pattern_counts"]["objection_patterns"] >= 5, summary)
    assert_condition(summary["available_source_pattern_counts"]["persuasion_strategy_patterns"] >= 2, summary)
    assert_condition(summary["available_source_pattern_counts"]["emotion_tone_transition_patterns"] >= 2, summary)
    assert_condition(summary["available_source_pattern_counts"]["close_attempt_patterns"] >= 3, summary)
    assert_condition(summary["leakage_finding_count"] == 0, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["llm_used"] is False, summary)
    assert_condition(summary["runtime_behavior_changed"] is False, summary)
    assert_condition(summary["ready_for_prod_015_evaluation"] is True, summary)

    leakage = payload["leakage_tests"]
    assert_condition(leakage["exact_transcript_sentence_check"]["status"] == "pass", leakage)
    assert_condition(leakage["high_similarity_paraphrase_check"]["status"] == "pass", leakage)
    assert_condition(leakage["single_source_scenario_check"]["status"] == "pass", leakage)
    assert_condition(leakage["commercial_runtime_prompt_check"]["status"] == "pass", leakage)
    assert_condition(leakage["findings"] == [], leakage)
    scenario_generation = payload["scenario_generation"]
    assert_condition(scenario_generation["mode"] == "expanded_multi_pattern_combinatorial", scenario_generation)
    assert_condition(scenario_generation["default_scenario_count"] >= 240, scenario_generation)
    assert_condition(scenario_generation["uses_objection_variants"] is True, scenario_generation)
    assert_condition(scenario_generation["uses_strategy_variants"] is True, scenario_generation)
    assert_condition(scenario_generation["uses_emotion_variants"] is True, scenario_generation)
    assert_condition(scenario_generation["uses_close_variants"] is True, scenario_generation)

    scenarios = payload["scenario_bank"]
    labels = {scenario["scenario_label"] for scenario in scenarios}
    assert_condition(EXPECTED_LABELS <= labels, labels)
    for scenario in scenarios:
        assert_condition(len(scenario["source_pattern_ids"]) >= 5, scenario)
        assert_condition(scenario["source_pattern_category_count"] >= 4, scenario)
        assert_condition(scenario["generated_from_single_source_transcript"] is False, scenario)
        assert_condition(scenario["copied_transcript_text_used"] is False, scenario)
        assert_condition(scenario["contains_transcript_derived_prompt_text"] is False, scenario)
        assert_condition(scenario["commercial_runtime_prompt_safe"] is True, scenario)
        assert_condition(scenario["expected_outcome"] in {"sale_ready", "callback_agreed", "non_sale_correct", "support_only", "human_handoff", "end_call"}, scenario)
        assert_condition(scenario["safe_close_definition"] == "verbal commitment or sale-ready outcome without payment collection", scenario)
        assert_condition(scenario["turns"], scenario)
        assert_condition(scenario["source_recipe"]["minimum_source_patterns"] >= 5, scenario)
        assert_condition(scenario["source_recipe"]["uses_exact_transcript_text"] is False, scenario)
        assert_condition(len(scenario["source_recipe"]["variant_source_pattern_ids"]) >= 4, scenario)
        assert_condition(scenario["source_recipe"]["variant_index"] >= 0, scenario)
        for turn in scenario["turns"]:
            assert_condition("customer_prompt" in turn and turn["customer_prompt"], turn)
            assert_condition("expected_agent_response_requirements" in turn and turn["expected_agent_response_requirements"], turn)
            assert_condition("avoid" in turn and turn["avoid"], turn)
            assert_condition("stage" in turn and turn["stage"], turn)
            assert_condition("customer_emotion" in turn, turn)

    metrics = payload["metrics"]
    for key in [
        "scenario_quality_score",
        "leakage_failure_rate",
        "safe_close_coverage",
        "non_sale_boundary_coverage",
        "emotion_transition_coverage",
    ]:
        assert_condition(key in metrics and "value" in metrics[key], metrics)
    assert_condition(metrics["scenario_quality_score"]["value"] >= 0.95, metrics["scenario_quality_score"])
    assert_condition(metrics["leakage_failure_rate"]["value"] == 0.0, metrics["leakage_failure_rate"])
    assert_condition(metrics["non_sale_boundary_coverage"]["value"] > 0.0, metrics["non_sale_boundary_coverage"])

    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")
    forbidden = [
        '"raw_transcript_text":',
        '"source_excerpt_text":',
        '"transcript":',
        "data/private",
        "data/private-restricted",
        "good morning, this is",
        "northstar",
        "brighttel",
        "homeenergy",
        "credit card",
        "take your payment",
        "commercial runtime prompt source",
    ]
    for token in forbidden:
        assert_condition(token not in combined, token)

    for required in [
        "PROD-014 CallCenterEN Scenario Bank",
        "scenario bank generated from PROD-013",
        "no exact transcript text",
        "safe close means verbal commitment",
        "ready for PROD-015",
        "leakage tests",
        "source pattern categories",
    ]:
        assert_condition(required.lower() in report.lower(), required)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-014 module"),
        (RUNNER, "PROD-014 runner"),
        (DOC_PATH, "PROD-014 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_014_callcenteren_scenario_bank.py" in commands, "PROD-014 runner missing from command map.")
    assert_condition("validate_prod_014_callcenteren_scenario_bank.py" in commands, "PROD-014 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_014_CALLCENTEREN_SCENARIO_BANK.md" in checkpoint_index, "PROD-014 missing from checkpoint index.")
    registry = REFERENCE_REGISTRY.read_text(encoding="utf-8")
    assert_condition(EXPECTED_DATASET_URL in registry, "Dataset URL missing from thesis reference registry.")
    assert_condition(EXPECTED_PAPER_URL in registry, "Dataset paper URL missing from thesis reference registry.")
    assert_condition(EXPECTED_LICENSE in registry.lower(), "Dataset license missing from thesis reference registry.")

    write_fixture_pattern_bank()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--pattern-bank",
            str(PATTERN_BANK),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--scenario-count",
            "48",
            "--leakage-sentence-limit",
            "0",
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-014 CallCenterEN scenario bank validation passed.")


if __name__ == "__main__":
    main()
