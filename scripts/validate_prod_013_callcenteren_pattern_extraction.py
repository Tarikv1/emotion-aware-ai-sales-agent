#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "callcenteren_pattern_extraction.py"
RUNNER = ROOT / "scripts" / "run_prod_013_callcenteren_pattern_extraction.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_013_CALLCENTEREN_PATTERN_EXTRACTION.md"
COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
REFERENCE_REGISTRY = ROOT / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md"
TMP_DIR = ROOT / ".tmp" / "prod-013-callcenteren-pattern-extraction"
RAW_DIR = TMP_DIR / "raw"
RESULT_PATH = TMP_DIR / "pattern-bank.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "PROD-013-callcenteren-pattern-extraction"
EXPECTED_DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
EXPECTED_PAPER_URL = "https://arxiv.org/abs/2507.02958"
EXPECTED_LICENSE = "cc-by-nc-4.0"

OPENING_LABELS = {
    "opening_types",
    "greeting_styles",
    "identity_disclosures",
    "company_disclosures",
    "reason_for_call",
    "permission_to_continue",
    "first_question_types",
    "customer_initial_response",
}
CUSTOMER_INTENT_LABELS = {
    "buying_interest",
    "information_request",
    "price_request",
    "complaint",
    "cancellation",
    "technical_problem",
    "billing_issue",
    "appointment_request",
    "not_interested",
    "wrong_person",
    "busy_now",
    "callback_request",
    "hostile_rejection",
}
OBJECTION_LABELS = {
    "too_expensive",
    "not_interested",
    "already_has_provider",
    "needs_to_think",
    "needs_spouse_or_manager",
    "bad_previous_experience",
    "no_time",
    "does_not_trust_agent",
    "confused_about_offer",
    "wants_written_info",
    "contract_fear",
    "payment_fear",
    "hidden_objection",
}
EMOTION_TRANSITION_LABELS = {
    "neutral_to_interested",
    "neutral_to_annoyed",
    "confused_to_clear",
    "annoyed_to_calm",
    "skeptical_to_open",
    "interested_to_hesitant",
    "hesitant_to_committed",
    "angry_to_escalated",
    "angry_to_de_escalated",
}
GOOD_PERSUASION_LABELS = {
    "benefit_framing",
    "pain_point_discovery",
    "cost_savings",
    "urgency",
    "scarcity",
    "social_proof",
    "authority",
    "risk_reversal",
    "trial_close",
    "assumptive_close",
    "contrast_offer",
    "personalization",
    "empathy_first",
    "problem_solution_fit",
}
BAD_PERSUASION_LABELS = {
    "pushy",
    "vague_claim",
    "unsupported_claim",
    "ignores_customer_need",
    "repeats_script",
    "talks_too_much",
    "premature_close",
}
DISCOVERY_LABELS = {
    "current_provider_question",
    "current_problem_question",
    "budget_question",
    "usage_question",
    "decision_maker_question",
    "timeline_question",
    "priority_question",
    "pain_point_question",
    "eligibility_question",
}
STAGE_LABELS = {
    "opening",
    "identity_verification",
    "reason_for_call",
    "rapport",
    "discovery",
    "problem_identification",
    "offer_presentation",
    "objection_handling",
    "clarification",
    "price_discussion",
    "eligibility_check",
    "trial_close",
    "close_attempt",
    "commitment_confirmation",
    "handoff",
    "callback_scheduling",
    "escalation",
    "wrap_up",
}
CLOSE_TYPE_LABELS = {
    "trial_close",
    "soft_close",
    "assumptive_close",
    "summary_close",
    "choice_close",
    "callback_close",
    "handoff_close",
    "sale_ready_close",
}
COMMITMENT_LABELS = {
    "not_interested",
    "mild_interested",
    "information_requested",
    "callback_agreed",
    "verbal_interested",
    "verbal_commitment",
    "sale_ready_outcome",
}
MISTAKE_LABELS = {
    "ignores_customer_emotion",
    "answers_wrong_question",
    "repeats_same_line",
    "over_explains",
    "closes_too_early",
    "does_not_confirm_understanding",
    "fails_to_handle_objection",
    "escalates_unnecessarily",
    "does_not_escalate_when_needed",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_zip() -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / "callcenteren-mini-fixture.zip"
    fixture = {
        "domain": "telecom",
        "topic": "sales_and_service",
        "accent": "us",
        "conversations": [
            {
                "conversation_id": "fixture-opening-sales",
                "domain": "software",
                "topic": "sales",
                "accent": "us",
                "turns": [
                    {"speaker": "agent", "text": "Good morning, this is Maya from Northstar Systems calling about your workflow review. Do you have thirty seconds?", "start": 0.0, "end": 4.2},
                    {"speaker": "customer", "text": "Maybe, what is this about?", "start": 5.0, "end": 6.5},
                    {"speaker": "agent", "text": "We help teams reduce repeated manual work. Who handles provider decisions today?", "start": 7.0, "end": 10.5},
                    {"speaker": "customer", "text": "I need to ask my manager and think about it.", "start": 11.4, "end": 13.2},
                    {"speaker": "agent", "text": "That makes sense. Would a short summary help your manager decide whether it is worth a review?", "start": 14.0, "end": 18.0},
                    {"speaker": "customer", "text": "Yes, send information and we can review later.", "start": 19.5, "end": 22.0},
                ],
            },
            {
                "conversation_id": "fixture-price-provider",
                "domain": "telecom",
                "topic": "plan_upgrade",
                "accent": "uk",
                "turns": [
                    {"speaker": "agent", "text": "Hello, I am Sam with BrightTel. I am calling about internet plan options for your address.", "start": 0.0, "end": 4.0},
                    {"speaker": "customer", "text": "How much is it? It sounds too expensive and I already have a provider.", "start": 4.8, "end": 8.0},
                    {"speaker": "agent", "text": "I understand the price concern. Is the monthly cost, contract length, or service reliability the bigger issue?", "start": 8.8, "end": 13.0},
                    {"speaker": "customer", "text": "The contract worries me, but if there is no risk I could compare.", "start": 15.0, "end": 18.0},
                    {"speaker": "agent", "text": "There is only one spot today, so let us lock it in now.", "start": 18.3, "end": 20.8},
                    {"speaker": "customer", "text": "No, that feels pushy.", "start": 21.7, "end": 23.0},
                ],
            },
            {
                "conversation_id": "fixture-support-boundaries",
                "domain": "insurance",
                "topic": "billing_and_claims",
                "accent": "us",
                "turns": [
                    {"speaker": "customer", "text": "I have a billing issue and want to cancel because nobody fixed my complaint.", "start": 0.0, "end": 4.5},
                    {"speaker": "agent", "text": "I am sorry about that. Let me confirm I understand the billing problem before I transfer you.", "start": 5.8, "end": 10.0},
                    {"speaker": "customer", "text": "Fine, I am calmer now, but I need a real person.", "start": 12.4, "end": 15.4},
                    {"speaker": "agent", "text": "Of course, I will connect you with a billing specialist rather than guessing.", "start": 16.0, "end": 19.2},
                ],
            },
            {
                "conversation_id": "fixture-technical-hostile",
                "domain": "medical_equipment",
                "topic": "technical_support",
                "accent": "au",
                "turns": [
                    {"speaker": "customer", "text": "This device is broken, your last agent was terrible, and I do not trust this call.", "start": 0.0, "end": 4.7},
                    {"speaker": "agent", "text": "I hear the frustration. I can route this to technical support and stay with the handoff.", "start": 6.2, "end": 10.4},
                    {"speaker": "customer", "text": "Okay, that is clearer.", "start": 13.1, "end": 14.2},
                    {"speaker": "agent", "text": "Would Tuesday or Wednesday work for the specialist appointment?", "start": 14.8, "end": 17.0},
                    {"speaker": "customer", "text": "Wednesday at ten works.", "start": 18.4, "end": 19.8},
                ],
            },
            {
                "conversation_id": "fixture-wrong-busy-hostile",
                "domain": "energy",
                "topic": "outbound_offer",
                "accent": "us",
                "turns": [
                    {"speaker": "agent", "text": "Hi, this is Lee from HomeEnergy. I am calling because you requested savings information.", "start": 0.0, "end": 3.8},
                    {"speaker": "customer", "text": "Wrong person. I am busy now, stop calling me.", "start": 4.0, "end": 6.0},
                    {"speaker": "agent", "text": "Understood. I will mark this contact so we do not call again.", "start": 7.5, "end": 10.0},
                    {"speaker": "customer", "text": "Good.", "start": 13.5, "end": 14.0},
                ],
            },
        ],
    }
    word_level_fixture = {
        "domain": "telecom",
        "topic": "outbound_offer",
        "accent": "us",
        "audio_duration": 14_000,
        "words": [
            {"text": "Hello,", "start": 0, "end": 220, "speaker": None},
            {"text": "this", "start": 220, "end": 380, "speaker": None},
            {"text": "is", "start": 380, "end": 500, "speaker": None},
            {"text": "Avery", "start": 500, "end": 760, "speaker": None},
            {"text": "calling", "start": 760, "end": 1040, "speaker": None},
            {"text": "about", "start": 1040, "end": 1240, "speaker": None},
            {"text": "your", "start": 1240, "end": 1400, "speaker": None},
            {"text": "internet", "start": 1400, "end": 1760, "speaker": None},
            {"text": "plan.", "start": 1760, "end": 2100, "speaker": None},
            {"text": "Do", "start": 2480, "end": 2600, "speaker": None},
            {"text": "you", "start": 2600, "end": 2720, "speaker": None},
            {"text": "have", "start": 2720, "end": 2900, "speaker": None},
            {"text": "a", "start": 2900, "end": 2980, "speaker": None},
            {"text": "minute?", "start": 2980, "end": 3340, "speaker": None},
            {"text": "I", "start": 4800, "end": 4920, "speaker": None},
            {"text": "am", "start": 4920, "end": 5060, "speaker": None},
            {"text": "busy", "start": 5060, "end": 5320, "speaker": None},
            {"text": "now,", "start": 5320, "end": 5560, "speaker": None},
            {"text": "but", "start": 5560, "end": 5740, "speaker": None},
            {"text": "how", "start": 5740, "end": 5920, "speaker": None},
            {"text": "much", "start": 5920, "end": 6160, "speaker": None},
            {"text": "does", "start": 6160, "end": 6360, "speaker": None},
            {"text": "it", "start": 6360, "end": 6480, "speaker": None},
            {"text": "cost?", "start": 6480, "end": 6900, "speaker": None},
            {"text": "I", "start": 8500, "end": 8620, "speaker": None},
            {"text": "understand", "start": 8620, "end": 9100, "speaker": None},
            {"text": "the", "start": 9100, "end": 9240, "speaker": None},
            {"text": "price", "start": 9240, "end": 9500, "speaker": None},
            {"text": "question.", "start": 9500, "end": 9900, "speaker": None},
            {"text": "Are", "start": 10_180, "end": 10_320, "speaker": None},
            {"text": "you", "start": 10_320, "end": 10_460, "speaker": None},
            {"text": "comparing", "start": 10_460, "end": 10_880, "speaker": None},
            {"text": "providers", "start": 10_880, "end": 11_260, "speaker": None},
            {"text": "this", "start": 11_260, "end": 11_440, "speaker": None},
            {"text": "month?", "start": 11_440, "end": 11_840, "speaker": None},
            {"text": "Maybe,", "start": 13_100, "end": 13_420, "speaker": None},
            {"text": "send", "start": 13_420, "end": 13_640, "speaker": None},
            {"text": "details.", "start": 13_640, "end": 14_000, "speaker": None},
        ],
    }
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("fixture.json", json.dumps(fixture, ensure_ascii=False))
        archive.writestr("word-level-fixture.json", json.dumps(word_level_fixture, ensure_ascii=False))
    return zip_path


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def names(records: list[dict[str, Any]], field: str) -> set[str]:
    return {str(record.get(field, "")) for record in records}


def load_extraction_module() -> Any:
    spec = importlib.util.spec_from_file_location("callcenteren_pattern_extraction", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load PROD-013 extraction module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules["callcenteren_pattern_extraction"] = module
    spec.loader.exec_module(module)
    return module


def role_signal_word_level_fixture() -> dict[str, Any]:
    return {
        "domain": "telecom",
        "topic": "outbound_offer",
        "accent": "us",
        "words": [
            {"text": "Hello,", "start": 0, "end": 180, "speaker": None},
            {"text": "this", "start": 180, "end": 320, "speaker": None},
            {"text": "is", "start": 320, "end": 430, "speaker": None},
            {"text": "Avery", "start": 430, "end": 700, "speaker": None},
            {"text": "calling", "start": 700, "end": 980, "speaker": None},
            {"text": "about", "start": 980, "end": 1180, "speaker": None},
            {"text": "your", "start": 1180, "end": 1320, "speaker": None},
            {"text": "internet", "start": 1320, "end": 1660, "speaker": None},
            {"text": "plan.", "start": 1660, "end": 1980, "speaker": None},
            {"text": "Do", "start": 3300, "end": 3420, "speaker": None},
            {"text": "you", "start": 3420, "end": 3540, "speaker": None},
            {"text": "have", "start": 3540, "end": 3720, "speaker": None},
            {"text": "a", "start": 3720, "end": 3800, "speaker": None},
            {"text": "minute", "start": 3800, "end": 4080, "speaker": None},
            {"text": "to", "start": 4080, "end": 4200, "speaker": None},
            {"text": "compare", "start": 4200, "end": 4560, "speaker": None},
            {"text": "options?", "start": 4560, "end": 4940, "speaker": None},
            {"text": "I", "start": 6500, "end": 6620, "speaker": None},
            {"text": "am", "start": 6620, "end": 6760, "speaker": None},
            {"text": "busy", "start": 6760, "end": 7020, "speaker": None},
            {"text": "now,", "start": 7020, "end": 7260, "speaker": None},
            {"text": "but", "start": 7260, "end": 7440, "speaker": None},
            {"text": "how", "start": 7440, "end": 7620, "speaker": None},
            {"text": "much", "start": 7620, "end": 7860, "speaker": None},
            {"text": "does", "start": 7860, "end": 8060, "speaker": None},
            {"text": "it", "start": 8060, "end": 8180, "speaker": None},
            {"text": "cost?", "start": 8180, "end": 8580, "speaker": None},
            {"text": "I", "start": 10_000, "end": 10_120, "speaker": None},
            {"text": "understand", "start": 10_120, "end": 10_600, "speaker": None},
            {"text": "the", "start": 10_600, "end": 10_740, "speaker": None},
            {"text": "price", "start": 10_740, "end": 11_000, "speaker": None},
            {"text": "question.", "start": 11_000, "end": 11_400, "speaker": None},
            {"text": "Are", "start": 11_760, "end": 11_900, "speaker": None},
            {"text": "you", "start": 11_900, "end": 12_040, "speaker": None},
            {"text": "comparing", "start": 12_040, "end": 12_460, "speaker": None},
            {"text": "providers", "start": 12_460, "end": 12_840, "speaker": None},
            {"text": "this", "start": 12_840, "end": 13_020, "speaker": None},
            {"text": "month?", "start": 13_020, "end": 13_420, "speaker": None},
            {"text": "Maybe,", "start": 14_900, "end": 15_220, "speaker": None},
            {"text": "send", "start": 15_220, "end": 15_440, "speaker": None},
            {"text": "details.", "start": 15_440, "end": 15_800, "speaker": None},
        ],
    }


def validate_word_level_role_signal_inference() -> None:
    module = load_extraction_module()
    conversations = module.extract_conversations_from_payload("role-signal-outbound.json", role_signal_word_level_fixture())
    assert_condition(len(conversations) == 1, "Role-signal fixture should produce one conversation.")
    speakers = [turn.speaker for turn in conversations[0].turns]
    assert_condition(
        speakers[:5] == ["agent", "agent", "customer", "agent", "customer"],
        {"expected": ["agent", "agent", "customer", "agent", "customer"], "actual": speakers[:5]},
    )


def validate_taxonomy(taxonomy: dict[str, Any]) -> None:
    assert_condition(set(taxonomy["opening_pattern_labels"]) >= OPENING_LABELS, taxonomy)
    assert_condition(set(taxonomy["customer_intent_labels"]) >= CUSTOMER_INTENT_LABELS, taxonomy)
    assert_condition(set(taxonomy["objection_type_labels"]) >= OBJECTION_LABELS, taxonomy)
    assert_condition(set(taxonomy["emotion_transition_labels"]) >= EMOTION_TRANSITION_LABELS, taxonomy)
    assert_condition(set(taxonomy["persuasion_strategy_labels"]) >= GOOD_PERSUASION_LABELS, taxonomy)
    assert_condition(set(taxonomy["bad_persuasion_labels"]) >= BAD_PERSUASION_LABELS, taxonomy)
    assert_condition(set(taxonomy["discovery_question_labels"]) >= DISCOVERY_LABELS, taxonomy)
    assert_condition(set(taxonomy["conversation_stage_labels"]) >= STAGE_LABELS, taxonomy)
    assert_condition(set(taxonomy["close_type_labels"]) >= CLOSE_TYPE_LABELS, taxonomy)
    assert_condition(set(taxonomy["commitment_level_labels"]) >= COMMITMENT_LABELS, taxonomy)
    assert_condition(set(taxonomy["agent_mistake_labels"]) >= MISTAKE_LABELS, taxonomy)


def validate_payload(payload: dict[str, Any], report: str) -> None:
    assert_condition(payload["prod_013_id"] == EXPECTED_ID, payload)
    assert_condition(payload["dataset_source"]["dataset_url"] == EXPECTED_DATASET_URL, payload["dataset_source"])
    assert_condition(payload["dataset_source"]["paper_url"] == EXPECTED_PAPER_URL, payload["dataset_source"])
    assert_condition(payload["dataset_source"]["license"] == EXPECTED_LICENSE, payload["dataset_source"])
    assert_condition(payload["source_characteristics"]["word_level_segmentation_when_needed"] is True, payload["source_characteristics"])
    assert_condition(payload["source_characteristics"]["speaker_role_signal_inference"] is True, payload["source_characteristics"])
    assert_condition(payload["source_characteristics"]["speaker_role_inference_is_ground_truth"] is False, payload["source_characteristics"])
    assert_condition(payload["source_characteristics"]["raw_text_field_exported"] is False, payload["source_characteristics"])
    assert_condition(payload["extraction_config"]["pattern_record_limit_per_category"] == 50, payload["extraction_config"])
    assert_condition(payload["extraction_config"]["record_lists_are_samples"] is True, payload["extraction_config"])
    assert_condition(payload["extraction_config"]["max_conversations"] == 25, payload["extraction_config"])
    assert_condition(payload["reuse_boundary"]["reuse_label"] == "abstract_pattern_extraction_only", payload["reuse_boundary"])
    assert_condition(payload["reuse_boundary"]["raw_transcript_text_stored"] is False, payload["reuse_boundary"])
    assert_condition(payload["reuse_boundary"]["exact_script_storage_allowed"] is False, payload["reuse_boundary"])
    assert_condition(payload["reuse_boundary"]["commercial_runtime_prompt_text_from_transcripts_allowed"] is False, payload["reuse_boundary"])
    assert_condition(payload["summary"]["source_file_count"] >= 2, payload["summary"])
    assert_condition(payload["summary"]["conversation_count"] >= 6, payload["summary"])
    assert_condition(payload["summary"]["turn_count"] >= 24, payload["summary"])
    assert_condition(payload["summary"]["raw_transcript_text_stored"] is False, payload["summary"])
    assert_condition(payload["summary"]["leakage_finding_count"] == 0, payload["summary"])
    assert_condition(payload["leakage_tests"]["exact_source_utterance_storage_check"]["status"] == "pass", payload["leakage_tests"])
    assert_condition(payload["leakage_tests"]["long_transcript_summary_check"]["status"] == "pass", payload["leakage_tests"])

    validate_taxonomy(payload["taxonomy"])

    openings = payload["pattern_bank"]["opening_patterns"]
    intents = payload["pattern_bank"]["customer_intent_patterns"]
    objections = payload["pattern_bank"]["objection_patterns"]
    transitions = payload["pattern_bank"]["emotion_tone_transition_patterns"]
    persuasion = payload["pattern_bank"]["persuasion_strategy_patterns"]
    discovery = payload["pattern_bank"]["discovery_question_patterns"]
    stages = payload["pattern_bank"]["turn_stage_patterns"]
    closes = payload["pattern_bank"]["close_attempt_patterns"]
    safety = payload["pattern_bank"]["safety_compliance_boundary_patterns"]
    timing = payload["pattern_bank"]["timing_speech_naturalness_patterns"]
    domains = payload["pattern_bank"]["domain_specific_scenario_patterns"]
    mistakes = payload["pattern_bank"]["agent_mistake_patterns"]
    scenario_templates = payload["pattern_bank"]["scenario_templates"]
    personas = payload["pattern_bank"]["customer_personas"]

    for field in ["objection_patterns", "emotion_tone_transition_patterns", "persuasion_strategy_patterns", "close_attempt_patterns"]:
        assert_condition(len(payload["pattern_bank"][field]) <= 50, {field: len(payload["pattern_bank"][field])})

    assert_condition(openings, "opening patterns missing")
    opening_keys = set().union(*(set(record["observed_labels"]) for record in openings))
    assert_condition({"greeting_styles", "company_disclosures", "reason_for_call", "permission_to_continue", "first_question_types"} <= opening_keys, openings)

    assert_condition(CUSTOMER_INTENT_LABELS & names(intents, "intent_label"), intents)
    assert_condition({"price_request", "cancellation", "technical_problem", "billing_issue", "appointment_request", "wrong_person", "busy_now", "callback_request", "hostile_rejection"} <= names(intents, "intent_label"), intents)

    objection_types = names(objections, "objection_type")
    assert_condition({"too_expensive", "already_has_provider", "needs_spouse_or_manager", "contract_fear", "does_not_trust_agent", "bad_previous_experience"} <= objection_types, objections)
    for objection in objections:
        for field in ["objection_text_pattern", "objection_type", "emotion_signal", "agent_response_tactic", "response_quality", "resolved", "next_customer_state"]:
            assert_condition(field in objection, objection)

    assert_condition(names(transitions, "transition_label") & EMOTION_TRANSITION_LABELS, transitions)
    for transition in transitions:
        for field in ["customer_emotion_before", "agent_tactic", "customer_emotion_after", "transition_success"]:
            assert_condition(field in transition, transition)

    assert_condition(names(persuasion, "strategy_label") & GOOD_PERSUASION_LABELS, persuasion)
    assert_condition(names(persuasion, "avoid_label") & BAD_PERSUASION_LABELS, persuasion)
    for item in persuasion:
        assert_condition("when_customer_says_pattern" in item, item)
        assert_condition("customer_emotion" in item, item)
        assert_condition("use_strategy" in item, item)
        assert_condition("avoid" in item, item)

    assert_condition(names(discovery, "question_type") & DISCOVERY_LABELS, discovery)
    assert_condition(names(stages, "stage_label") & STAGE_LABELS, stages)
    assert_condition(names(closes, "close_type") & CLOSE_TYPE_LABELS, closes)
    assert_condition(names(closes, "commitment_level") & COMMITMENT_LABELS, closes)
    for item in closes:
        for field in ["close_type", "commitment_level", "customer_response", "safe_close", "close_successful", "follow_up_required"]:
            assert_condition(field in item, item)

    assert_condition(safety, "safety/compliance boundary patterns missing")
    assert_condition(timing["timestamps_available"] is True, timing)
    for field in ["average_agent_turn_words", "average_customer_turn_words", "pause_before_agent_response_ms", "interruption_count", "overlong_agent_monologue_count", "rapid_fire_question_count", "silence_after_offer_count", "silence_after_price_count"]:
        assert_condition(field in timing, timing)
    assert_condition(domains, "domain-specific patterns missing")
    assert_condition(names(mistakes, "mistake_label") & MISTAKE_LABELS, mistakes)
    assert_condition(scenario_templates, "scenario templates missing")
    assert_condition(personas, "customer personas missing")

    combined = json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()
    forbidden_exact = [
        "good morning, this is maya from northstar systems calling about your workflow review",
        "hello, i am sam with brighttel",
        "hi, this is lee from homeenergy",
        "northstar systems",
        "brighttel",
        "homeenergy",
        '"raw_text"',
        '"transcript"',
        "full transcript",
    ]
    for token in forbidden_exact:
        assert_condition(token not in combined, f"Forbidden transcript/company/name material leaked: {token}")
    for name in ["maya", "sam", "lee"]:
        assert_condition(not re.search(rf"\b{name}\b", combined), f"Forbidden agent name leaked: {name}")

    for required in [
        "PROD-013 CallCenterEN Pattern Extraction",
        "opening patterns",
        "objection patterns",
        "emotion/tone transitions",
        "persuasion strategy patterns",
        "discovery question patterns",
        "close attempt patterns",
        "safety/compliance boundaries",
        "timing and speech naturalness",
        "agent mistake patterns",
        "speaker labels are absent",
        "No exact scripts",
    ]:
        assert_condition(required.lower() in report.lower(), required)


def main() -> None:
    for path, label in [
        (MODULE, "PROD-013 module"),
        (RUNNER, "PROD-013 runner"),
        (DOC_PATH, "PROD-013 product doc"),
    ]:
        assert_condition(path.exists(), f"{label} is missing: {path.relative_to(ROOT)}")

    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_013_callcenteren_pattern_extraction.py" in commands, "PROD-013 runner missing from command map.")
    assert_condition("validate_prod_013_callcenteren_pattern_extraction.py" in commands, "PROD-013 validator missing from command map.")
    checkpoint_index = CHECKPOINT_INDEX.read_text(encoding="utf-8")
    assert_condition("PROD_013_CALLCENTEREN_PATTERN_EXTRACTION.md" in checkpoint_index, "PROD-013 missing from checkpoint index.")
    registry = REFERENCE_REGISTRY.read_text(encoding="utf-8")
    assert_condition(EXPECTED_DATASET_URL in registry, "Dataset URL missing from thesis reference registry.")
    assert_condition(EXPECTED_PAPER_URL in registry, "Dataset paper URL missing from thesis reference registry.")
    assert_condition(EXPECTED_LICENSE in registry.lower(), "Dataset license missing from thesis reference registry.")

    validate_word_level_role_signal_inference()

    write_fixture_zip()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--raw-dir",
            str(RAW_DIR),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--max-conversations",
            "25",
            "--record-limit",
            "50",
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    validate_payload(payload, report)
    print("PROD-013 CallCenterEN pattern extraction validation passed.")


if __name__ == "__main__":
    main()
