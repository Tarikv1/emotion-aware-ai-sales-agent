#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import statistics
import time
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-042-callcenteren-turn-pattern-playbook"
CHECKPOINT_NAME = "CallCenterEN Turn-Level Sales Pattern Playbook"
NEXT_CHECKPOINT_ID = "PROD-043-sales-playbook-runtime-adapter"
SOURCE_CHECKPOINTS = [
    "PROD-013-callcenteren-pattern-extraction",
    "PROD-014-callcenteren-scenario-bank",
]
RAW_SOURCE_DIR = ROOT / "data" / "external" / "callcenteren" / "raw"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PROD_013_PATTERN_BANK = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINTS[0] / "pattern-bank.json"
PROD_014_SCENARIO_BANK = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINTS[1] / "scenario-bank.json"

BOUNDARY_FLAGS = {
    "abstract_pattern_only": True,
    "uses_exact_transcript_text": False,
    "uses_source_transcript_sequence": False,
    "uses_dataset_specific_phrasing": False,
}

SUPPORT_COUNT_METHOD = "heuristic aggregate signal count from parsed raw CallCenterEN files and abstract cross-check artifacts"
SUPPORT_COUNT_LIMITATIONS = "Not a verified labeled success count; counts may reflect broad lexical/category matches."

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

SUPPORTED_EXTENSIONS = {".csv", ".json", ".jsonl", ".txt", ".tsv"}
MAX_PARSED_RECORDS = 16_000
MAX_PARSED_RECORDS_PER_ZIP = 2_000
MAX_PARSE_FAILURES = 50
MAX_DETECTED_KEYS = 200
MAX_TEXT_LENGTH = 12_000
MAX_SEGMENTS_PER_RECORD = 180
MAX_SOURCE_REFS_PER_PATTERN = 10
MAX_PATTERN_IDS_PER_PATTERN = 8
NOISE_MEMBER_PREFIXES = ("__MACOSX/",)
NOISE_MEMBER_NAMES = {".ds_store"}

SPEAKER_HINT_AGENT = (
    "this is",
    "how may i help",
    "can i",
    "let me",
    "i can",
    "we can",
    "i will",
    "i'll",
    "reason for my call",
    "calling because",
    "would you like",
    "i understand",
)
SPEAKER_HINT_CUSTOMER = (
    "i need",
    "i'm not interested",
    "not interested",
    "how much",
    "what does it cost",
    "who are you",
    "we already have",
    "i already have",
    "email only",
    "send me",
    "no thanks",
    "stop calling",
)

MOVE_TARGETS: dict[str, dict[str, Any]] = {
    "price_first": {
        "name": "Price before pitch",
        "description": "Customer asks about price before allowing broader discovery.",
        "customer_intent": ["screen budget fit", "avoid wasted time", "test directness"],
        "emotional_signal": ["skeptical", "rushed"],
        "common_contexts": ["B2B software calls", "consumer service calls"],
        "trigger_signals_abstract": ["asks price", "asks cost", "asks monthly amount", "asks budget fit"],
        "sales_risk": ["customer may reject if price is dodged", "friction rises when answer is vague"],
        "preferred_agent_tactic_ids": ["answer_directly", "low_pressure_boundary", "one_concrete_relevance_point"],
        "tactics_to_avoid": ["dodge_question", "question_storming", "feature_pitch_before_answer"],
        "likely_customer_reactions_if_handled_well": ["clarity_gain", "asks_for_details", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["repeats_question", "friction_increase", "rejects_call"],
        "keywords": ["price", "cost", "monthly", "budget", "how much"],
    },
    "send_info": {
        "name": "Send information request",
        "description": "Customer asks for written details before continuing.",
        "customer_intent": ["review asynchronously", "reduce call pressure", "involve another reviewer"],
        "emotional_signal": ["calm", "cautious"],
        "common_contexts": ["B2B procurement", "consumer service checks"],
        "trigger_signals_abstract": ["send info", "send details", "send information", "share summary"],
        "sales_risk": ["conversation may stall without clear next step"],
        "preferred_agent_tactic_ids": ["written_info_offer", "low_pressure_boundary", "single_discovery_question"],
        "tactics_to_avoid": ["hard_close", "question_storming"],
        "likely_customer_reactions_if_handled_well": ["asks_for_written_info", "accepts_low_pressure_next_step"],
        "likely_customer_reactions_if_mishandled": ["rejects", "sets_boundary"],
        "keywords": ["send", "details", "information", "summary", "write"],
    },
    "email_only": {
        "name": "Email-only boundary",
        "description": "Customer requests email-only follow-up and avoids live discussion.",
        "customer_intent": ["control channel", "limit time", "reduce pressure"],
        "emotional_signal": ["rushed", "skeptical"],
        "common_contexts": ["busy manager", "consumer interruption"],
        "trigger_signals_abstract": ["email only", "just email", "no call"],
        "sales_risk": ["safe-close can be false if boundary is ignored"],
        "preferred_agent_tactic_ids": ["written_info_offer", "stop_after_refusal", "low_pressure_boundary"],
        "tactics_to_avoid": ["pressure_after_refusal", "callback_offer"],
        "likely_customer_reactions_if_handled_well": ["sets_boundary", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["email only", "just email", "email me", "no call"],
    },
    "not_interested": {
        "name": "Not interested signal",
        "description": "Customer states low willingness to continue.",
        "customer_intent": ["end call quickly", "avoid pressure"],
        "emotional_signal": ["calm", "irritated"],
        "common_contexts": ["outbound call screening"],
        "trigger_signals_abstract": ["not interested", "no thanks", "not looking"],
        "sales_risk": ["pressure can trigger do-not-contact outcome"],
        "preferred_agent_tactic_ids": ["stop_after_refusal", "low_pressure_boundary"],
        "tactics_to_avoid": ["hard_close", "question_storming"],
        "likely_customer_reactions_if_handled_well": ["sets_boundary", "rejects"],
        "likely_customer_reactions_if_mishandled": ["escalates", "rejects"],
        "keywords": ["not interested", "no thanks", "not looking", "not now"],
    },
    "busy_now": {
        "name": "Busy now",
        "description": "Customer says they have limited time right now.",
        "customer_intent": ["reduce call length", "defer discussion"],
        "emotional_signal": ["rushed"],
        "common_contexts": ["front desk", "operations manager", "consumer daytime call"],
        "trigger_signals_abstract": ["busy now", "only a minute", "can't talk"],
        "sales_risk": ["over-questioning increases friction"],
        "preferred_agent_tactic_ids": ["time_respectful", "callback_offer", "low_pressure_boundary"],
        "tactics_to_avoid": ["feature_dump", "question_storming"],
        "likely_customer_reactions_if_handled_well": ["requests_callback", "accepts_low_pressure_next_step"],
        "likely_customer_reactions_if_mishandled": ["rejects", "sets_boundary"],
        "keywords": ["busy", "minute", "can't talk", "cant talk", "short on time"],
    },
    "callback_request": {
        "name": "Callback request",
        "description": "Customer requests a callback instead of continuing now.",
        "customer_intent": ["control timing", "defer detail"],
        "emotional_signal": ["rushed", "neutral"],
        "common_contexts": ["outbound prospecting", "service follow-up"],
        "trigger_signals_abstract": ["call back", "callback", "later"],
        "sales_risk": ["callback can fail if no concrete window"],
        "preferred_agent_tactic_ids": ["callback_offer", "time_respectful", "low_pressure_boundary"],
        "tactics_to_avoid": ["unclear_next_step", "pressure_after_refusal"],
        "likely_customer_reactions_if_handled_well": ["requests_callback", "accepts_low_pressure_next_step"],
        "likely_customer_reactions_if_mishandled": ["rejects"],
        "keywords": ["call back", "callback", "later today", "next week", "another time"],
    },
    "who_are_you": {
        "name": "Identity clarification request",
        "description": "Customer asks who the caller is or what they are selling.",
        "customer_intent": ["verify legitimacy", "understand context"],
        "emotional_signal": ["skeptical", "distrustful"],
        "common_contexts": ["cold outbound", "unknown number"],
        "trigger_signals_abstract": ["who are you", "what are you selling", "which company"],
        "sales_risk": ["trust drops if identity is vague"],
        "preferred_agent_tactic_ids": ["answer_directly", "reason_first", "trust_repair"],
        "tactics_to_avoid": ["vague_pitch", "question_storming"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "softens"],
        "likely_customer_reactions_if_mishandled": ["asks_identity_again", "rejects"],
        "keywords": ["who are you", "what are you selling", "which company", "why are you calling"],
    },
    "scam_or_card_fear": {
        "name": "Scam or card fear",
        "description": "Customer worries about fraud or card/payment risk.",
        "customer_intent": ["protect finances", "verify safety"],
        "emotional_signal": ["anxious", "distrustful"],
        "common_contexts": ["consumer outbound", "insurance/telecom"],
        "trigger_signals_abstract": ["scam", "card", "fraud"],
        "sales_risk": ["unsafe requests can force immediate rejection"],
        "preferred_agent_tactic_ids": ["payment_safety_boundary", "trust_repair", "low_pressure_boundary"],
        "tactics_to_avoid": ["unsafe_payment_request", "pressure_after_refusal"],
        "likely_customer_reactions_if_handled_well": ["sets_boundary", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["scam", "card", "fraud", "credit card", "payment details"],
    },
    "payment_safety_fear": {
        "name": "Payment safety concern",
        "description": "Customer avoids payment details or commitments on call.",
        "customer_intent": ["avoid unsafe payment handling", "delay commitment"],
        "emotional_signal": ["anxious", "skeptical"],
        "common_contexts": ["consumer services", "membership plans"],
        "trigger_signals_abstract": ["not giving payment", "no payment details", "not sharing card"],
        "sales_risk": ["pressure creates immediate trust loss"],
        "preferred_agent_tactic_ids": ["payment_safety_boundary", "written_info_offer", "stop_after_refusal"],
        "tactics_to_avoid": ["unsafe_payment_request", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["sets_boundary", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["payment", "card details", "not giving", "not sharing card", "billing info"],
    },
    "existing_provider": {
        "name": "Existing provider objection",
        "description": "Customer says they already use another provider.",
        "customer_intent": ["avoid redundant switch", "test relevance"],
        "emotional_signal": ["skeptical", "calm"],
        "common_contexts": ["B2B software", "service contracts"],
        "trigger_signals_abstract": ["already have a provider", "already covered", "already with"],
        "sales_risk": ["generic pitch can end call quickly"],
        "preferred_agent_tactic_ids": ["objection_isolation", "one_concrete_relevance_point", "trust_repair"],
        "tactics_to_avoid": ["feature_dump", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["rejects"],
        "keywords": ["already have", "already with", "current provider", "existing provider"],
    },
    "needs_manager_approval": {
        "name": "Needs manager approval",
        "description": "Customer says manager approval is required before proceeding.",
        "customer_intent": ["defer decision", "protect decision process"],
        "emotional_signal": ["calm", "cautious"],
        "common_contexts": ["B2B team purchase"],
        "trigger_signals_abstract": ["manager approval", "ask my manager", "need approval"],
        "sales_risk": ["next step fails if manager path is unclear"],
        "preferred_agent_tactic_ids": ["manager_review_offer", "written_info_offer", "low_pressure_boundary"],
        "tactics_to_avoid": ["hard_close", "pressure_after_refusal"],
        "likely_customer_reactions_if_handled_well": ["asks_for_manager_review", "accepts_low_pressure_next_step"],
        "likely_customer_reactions_if_mishandled": ["rejects"],
        "keywords": ["manager", "approval", "procurement", "leadership", "boss"],
    },
    "needs_spouse_or_partner_input": {
        "name": "Needs spouse or partner input",
        "description": "Customer says another household decision-maker must review.",
        "customer_intent": ["shared decision", "avoid immediate commitment"],
        "emotional_signal": ["calm", "cautious"],
        "common_contexts": ["B2C home/insurance decisions"],
        "trigger_signals_abstract": ["spouse", "partner", "need to ask"],
        "sales_risk": ["pressure can trigger rejection"],
        "preferred_agent_tactic_ids": ["written_info_offer", "callback_offer", "low_pressure_boundary"],
        "tactics_to_avoid": ["hard_close", "pressure_after_refusal"],
        "likely_customer_reactions_if_handled_well": ["asks_for_written_info", "requests_callback"],
        "likely_customer_reactions_if_mishandled": ["rejects"],
        "keywords": ["spouse", "partner", "family decision", "need to ask at home"],
    },
    "technical_question": {
        "name": "Technical question",
        "description": "Customer asks integration or technical feasibility questions.",
        "customer_intent": ["validate fit", "avoid implementation risk"],
        "emotional_signal": ["curious", "skeptical"],
        "common_contexts": ["B2B software and operations"],
        "trigger_signals_abstract": ["integration", "api", "technical", "setup"],
        "sales_risk": ["wrong answer can reduce trust quickly"],
        "preferred_agent_tactic_ids": ["simple_explanation", "handoff_to_specialist", "proof_without_unsupported_claim"],
        "tactics_to_avoid": ["unsupported_claim", "vague_pitch"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "asks_for_handoff"],
        "likely_customer_reactions_if_mishandled": ["gets_confused", "rejects"],
        "keywords": ["integration", "api", "technical", "setup", "implementation"],
    },
    "security_review": {
        "name": "Security review request",
        "description": "Customer asks for security details or review process.",
        "customer_intent": ["risk control", "compliance gate"],
        "emotional_signal": ["skeptical", "cautious"],
        "common_contexts": ["B2B SaaS procurement"],
        "trigger_signals_abstract": ["security", "compliance", "review"],
        "sales_risk": ["unsupported security claims can trigger rejection"],
        "preferred_agent_tactic_ids": ["proof_without_unsupported_claim", "handoff_to_specialist", "manager_review_offer"],
        "tactics_to_avoid": ["unsupported_claim", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["asks_for_manager_review", "asks_for_handoff"],
        "likely_customer_reactions_if_mishandled": ["challenges_claim", "rejects"],
        "keywords": ["security", "compliance", "audit", "soc 2", "review"],
    },
    "support_issue": {
        "name": "Support issue on sales call",
        "description": "Customer raises support problem instead of sales discussion.",
        "customer_intent": ["resolve current issue first"],
        "emotional_signal": ["irritated", "anxious"],
        "common_contexts": ["service inbound", "existing account call"],
        "trigger_signals_abstract": ["support issue", "service issue", "billing issue", "problem not fixed"],
        "sales_risk": ["selling through support issue breaks trust"],
        "preferred_agent_tactic_ids": ["support_boundary_route", "handoff_to_specialist", "acknowledge_emotion"],
        "tactics_to_avoid": ["hard_close", "feature_dump"],
        "likely_customer_reactions_if_handled_well": ["asks_for_handoff", "softens"],
        "likely_customer_reactions_if_mishandled": ["escalates", "rejects"],
        "keywords": ["support", "issue", "problem", "billing", "complaint"],
    },
    "cancellation_request": {
        "name": "Cancellation boundary",
        "description": "Customer wants cancellation/termination support path.",
        "customer_intent": ["end service", "resolve account state"],
        "emotional_signal": ["irritated", "hostile"],
        "common_contexts": ["service retention calls"],
        "trigger_signals_abstract": ["cancel", "cancellation", "terminate"],
        "sales_risk": ["pressure creates do-not-contact risk"],
        "preferred_agent_tactic_ids": ["support_boundary_route", "stop_after_refusal", "acknowledge_emotion"],
        "tactics_to_avoid": ["pressure_after_refusal", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["sets_boundary", "asks_for_handoff"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["cancel", "cancellation", "terminate", "close account"],
    },
    "confused_fit": {
        "name": "Confused fit question",
        "description": "Customer is unclear about relevance or fit.",
        "customer_intent": ["understand offer quickly"],
        "emotional_signal": ["confused", "skeptical"],
        "common_contexts": ["cold outbound"],
        "trigger_signals_abstract": ["not sure i follow", "sounds vague", "what do you mean"],
        "sales_risk": ["continued vagueness causes rejection"],
        "preferred_agent_tactic_ids": ["simple_explanation", "one_concrete_relevance_point", "single_discovery_question"],
        "tactics_to_avoid": ["vague_pitch", "feature_dump"],
        "likely_customer_reactions_if_handled_well": ["clarity_gain", "asks_for_details"],
        "likely_customer_reactions_if_mishandled": ["gets_confused", "rejects"],
        "keywords": ["not sure", "sounds vague", "confused", "what do you mean"],
    },
    "skeptical_proof_request": {
        "name": "Proof request",
        "description": "Customer asks for proof or credibility evidence.",
        "customer_intent": ["reduce perceived risk", "test credibility"],
        "emotional_signal": ["skeptical"],
        "common_contexts": ["outbound sales", "provider switch"],
        "trigger_signals_abstract": ["proof", "evidence", "case", "how do i know"],
        "sales_risk": ["unsupported claim can break trust"],
        "preferred_agent_tactic_ids": ["safe_social_proof", "proof_without_unsupported_claim", "written_info_offer"],
        "tactics_to_avoid": ["unsupported_claim", "overpromised_results"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["challenges_claim", "rejects"],
        "keywords": ["proof", "evidence", "case study", "how do i know"],
    },
    "bad_previous_experience": {
        "name": "Bad previous experience",
        "description": "Customer references prior bad vendor or support experience.",
        "customer_intent": ["avoid repeating mistakes", "test trust repair"],
        "emotional_signal": ["irritated", "distrustful"],
        "common_contexts": ["renewal and switch conversations"],
        "trigger_signals_abstract": ["bad experience", "last time", "didn't work"],
        "sales_risk": ["ignoring history worsens trust"],
        "preferred_agent_tactic_ids": ["trust_repair", "acknowledge_emotion", "low_pressure_boundary"],
        "tactics_to_avoid": ["hard_close", "unsupported_claim"],
        "likely_customer_reactions_if_handled_well": ["softens", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["bad experience", "last time", "didn't work", "wasted"],
    },
    "competitor_comparison": {
        "name": "Competitor comparison",
        "description": "Customer compares offer against another provider.",
        "customer_intent": ["evaluate differences", "avoid switch cost"],
        "emotional_signal": ["skeptical", "curious"],
        "common_contexts": ["B2B procurement", "consumer plan switch"],
        "trigger_signals_abstract": ["competitor", "compare", "other option"],
        "sales_risk": ["aggressive claims can reduce trust"],
        "preferred_agent_tactic_ids": ["one_concrete_relevance_point", "objection_isolation", "written_info_offer"],
        "tactics_to_avoid": ["unsupported_claim", "feature_dump"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["rejects"],
        "keywords": ["competitor", "compare", "another vendor", "other option"],
    },
    "contract_fear": {
        "name": "Contract fear",
        "description": "Customer fears lock-in or long commitment.",
        "customer_intent": ["avoid commitment risk"],
        "emotional_signal": ["anxious", "skeptical"],
        "common_contexts": ["subscription sales"],
        "trigger_signals_abstract": ["contract", "locked in", "commitment"],
        "sales_risk": ["hard-close can force rejection"],
        "preferred_agent_tactic_ids": ["risk_reversal", "low_pressure_boundary", "written_info_offer"],
        "tactics_to_avoid": ["hard_close", "pressure_after_refusal"],
        "likely_customer_reactions_if_handled_well": ["asks_for_written_info", "softens"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["contract", "locked in", "commitment", "term length"],
    },
    "setup_timeline": {
        "name": "Setup timeline concern",
        "description": "Customer asks setup duration or timing impact.",
        "customer_intent": ["plan operational impact"],
        "emotional_signal": ["curious", "skeptical"],
        "common_contexts": ["implementation planning"],
        "trigger_signals_abstract": ["timeline", "how long", "setup time"],
        "sales_risk": ["vague timeline lowers trust"],
        "preferred_agent_tactic_ids": ["simple_explanation", "one_concrete_relevance_point", "callback_offer"],
        "tactics_to_avoid": ["vague_pitch", "unsupported_claim"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "requests_callback"],
        "likely_customer_reactions_if_mishandled": ["gets_confused", "rejects"],
        "keywords": ["timeline", "how long", "setup", "implementation time"],
    },
    "coverage_confusion": {
        "name": "Coverage confusion",
        "description": "Customer is unclear about what's covered.",
        "customer_intent": ["clarify scope and exclusions"],
        "emotional_signal": ["confused", "anxious"],
        "common_contexts": ["insurance/plan calls"],
        "trigger_signals_abstract": ["covered", "coverage", "included", "not included"],
        "sales_risk": ["overpromising creates compliance risk"],
        "preferred_agent_tactic_ids": ["simple_explanation", "proof_without_unsupported_claim", "written_info_offer"],
        "tactics_to_avoid": ["unsupported_claim", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["clarity_gain", "asks_for_written_info"],
        "likely_customer_reactions_if_mishandled": ["gets_confused", "rejects"],
        "keywords": ["coverage", "covered", "included", "exclusion"],
    },
    "sensitive_healthcare_concern": {
        "name": "Sensitive healthcare concern",
        "description": "Customer raises sensitive health or care concern during call.",
        "customer_intent": ["safe handling", "accurate boundaries"],
        "emotional_signal": ["anxious", "distrustful"],
        "common_contexts": ["healthcare inbound/outbound"],
        "trigger_signals_abstract": ["medical", "health", "diagnosis", "care"],
        "sales_risk": ["unsupported advice is hard failure risk"],
        "preferred_agent_tactic_ids": ["support_boundary_route", "acknowledge_emotion", "handoff_to_specialist"],
        "tactics_to_avoid": ["unsupported_claim", "overpromised_results"],
        "likely_customer_reactions_if_handled_well": ["asks_for_handoff", "sets_boundary"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["medical", "health", "doctor", "diagnosis", "treatment"],
    },
    "hostile_rejection": {
        "name": "Hostile rejection",
        "description": "Customer rejects call with hostile language or hard boundary.",
        "customer_intent": ["end contact immediately"],
        "emotional_signal": ["hostile", "irritated"],
        "common_contexts": ["unsolicited calls"],
        "trigger_signals_abstract": ["stop calling", "leave me alone", "don't call again"],
        "sales_risk": ["any pressure can trigger do-not-contact"],
        "preferred_agent_tactic_ids": ["stop_after_refusal", "low_pressure_boundary"],
        "tactics_to_avoid": ["pressure_after_refusal", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["sets_boundary", "rejects"],
        "likely_customer_reactions_if_mishandled": ["escalates", "rejects"],
        "keywords": ["stop calling", "dont call", "leave me alone", "go away", "not calling again"],
    },
    "low_fit_signal": {
        "name": "Low fit signal",
        "description": "Customer indicates offer may not fit their needs.",
        "customer_intent": ["qualify out quickly"],
        "emotional_signal": ["calm", "skeptical"],
        "common_contexts": ["discovery qualification"],
        "trigger_signals_abstract": ["not a fit", "doesn't fit", "not relevant"],
        "sales_risk": ["false safe close if mismatch ignored"],
        "preferred_agent_tactic_ids": ["qualify_out", "low_pressure_boundary", "single_discovery_question"],
        "tactics_to_avoid": ["hard_close", "feature_dump"],
        "likely_customer_reactions_if_handled_well": ["rejects", "sets_boundary"],
        "likely_customer_reactions_if_mishandled": ["rejects", "escalates"],
        "keywords": ["not a fit", "doesnt fit", "not relevant", "wrong fit"],
    },
    "sale_ready_interest": {
        "name": "Sale-ready interest",
        "description": "Customer expresses active interest and asks next-step logistics.",
        "customer_intent": ["progress quickly with low risk"],
        "emotional_signal": ["curious", "positive"],
        "common_contexts": ["late-call progression"],
        "trigger_signals_abstract": ["sounds good", "what's next", "ready to proceed"],
        "sales_risk": ["unclear next step can stall conversion"],
        "preferred_agent_tactic_ids": ["callback_offer", "written_info_offer", "low_pressure_boundary"],
        "tactics_to_avoid": ["unclear_next_step", "feature_dump"],
        "likely_customer_reactions_if_handled_well": ["accepts_low_pressure_next_step"],
        "likely_customer_reactions_if_mishandled": ["gets_confused", "rejects"],
        "keywords": ["ready", "sounds good", "next step", "proceed", "move forward"],
    },
    "discovery_needed": {
        "name": "Discovery needed",
        "description": "Customer requests context/discovery before deciding.",
        "customer_intent": ["understand fit before commitment"],
        "emotional_signal": ["calm", "curious"],
        "common_contexts": ["early B2B discovery"],
        "trigger_signals_abstract": ["need more context", "need to understand", "tell me more first"],
        "sales_risk": ["question storming can feel interrogative"],
        "preferred_agent_tactic_ids": ["single_discovery_question", "one_concrete_relevance_point", "simple_explanation"],
        "tactics_to_avoid": ["question_storming", "hard_close"],
        "likely_customer_reactions_if_handled_well": ["asks_for_details", "softens"],
        "likely_customer_reactions_if_mishandled": ["gets_confused", "rejects"],
        "keywords": ["need more context", "understand first", "tell me more", "how does this work"],
    },
}

AGENT_TACTIC_TARGETS: dict[str, dict[str, Any]] = {
    "answer_directly": {
        "name": "Answer direct question first",
        "description": "Agent answers the explicit customer question before additional discovery.",
        "keywords": ["price is", "cost is", "it costs", "starts at", "here's the answer", "quick answer"],
    },
    "acknowledge_emotion": {"name": "Acknowledge emotion", "description": "Agent validates customer emotion signal.", "keywords": ["i understand", "i hear", "sorry", "that makes sense"]},
    "permission_first": {"name": "Permission-first open", "description": "Agent asks permission or timing before pitch.", "keywords": ["bad time", "do you have", "can i take", "okay if i"]},
    "reason_first": {"name": "Reason-first open", "description": "Agent states reason for call clearly.", "keywords": ["reason for my call", "calling because", "reaching out because"]},
    "time_respectful": {"name": "Time respectful", "description": "Agent keeps turn brief and respects timing boundary.", "keywords": ["keep this brief", "twenty seconds", "i'll be brief", "short version"]},
    "low_pressure_boundary": {"name": "Low-pressure boundary", "description": "Agent removes pressure and keeps optional next step.", "keywords": ["no pressure", "optional", "no obligation", "we can stop"]},
    "one_concrete_relevance_point": {"name": "One relevance point", "description": "Agent gives one concrete reason this might matter.", "keywords": ["the only reason this matters", "one thing to check", "relevant only if"]},
    "simple_explanation": {"name": "Simple explanation", "description": "Agent explains in plain language without jargon.", "keywords": ["in plain terms", "simple version", "basically", "in short"]},
    "objection_isolation": {"name": "Objection isolation", "description": "Agent isolates and addresses one main objection.", "keywords": ["is the main concern", "is it mostly", "to confirm the blocker"]},
    "trust_repair": {"name": "Trust repair", "description": "Agent acknowledges distrust and clarifies boundaries.", "keywords": ["you don't need to commit", "i won't ask for payment", "totally fair to be cautious"]},
    "risk_reversal": {"name": "Risk reversal", "description": "Agent reduces perceived risk without guaranteeing outcomes.", "keywords": ["no long contract", "can cancel", "no commitment today"]},
    "safe_social_proof": {"name": "Safe social proof", "description": "Agent references credibility without unverifiable claims.", "keywords": ["teams like yours", "common issue we see", "typical workflow"]},
    "written_info_offer": {"name": "Written info offer", "description": "Agent offers concise written follow-up.", "keywords": ["i can send", "email summary", "written details"]},
    "callback_offer": {"name": "Callback offer", "description": "Agent offers callback window with customer control.", "keywords": ["callback", "time slots", "next week", "schedule a short call"]},
    "manager_review_offer": {"name": "Manager review offer", "description": "Agent offers manager-ready summary or review packet.", "keywords": ["manager summary", "forward to your manager", "procurement review"]},
    "handoff_to_specialist": {"name": "Handoff to specialist", "description": "Agent routes to the correct specialist safely.", "keywords": ["specialist", "handoff", "route this", "connect you to support"]},
    "support_boundary_route": {"name": "Support boundary route", "description": "Agent routes support/cancellation issue before sales.", "keywords": ["support team", "billing team", "cancellation desk", "service desk"]},
    "qualify_out": {"name": "Qualify out", "description": "Agent qualifies out when fit is low.", "keywords": ["might not be the right fit", "better to stop here", "not a fit right now"]},
    "single_discovery_question": {"name": "Single discovery question", "description": "Agent asks one focused discovery question.", "keywords": ["one quick question", "before i suggest next step", "single question"]},
    "proof_without_unsupported_claim": {"name": "Proof without unsupported claim", "description": "Agent gives bounded proof context safely.", "keywords": ["i can share examples", "we can send references", "documented process"]},
    "payment_safety_boundary": {"name": "Payment safety boundary", "description": "Agent explicitly avoids payment collection on call.", "keywords": ["no payment on this call", "no card details needed", "not collecting payment"]},
    "stop_after_refusal": {"name": "Stop after refusal", "description": "Agent respects refusal and closes cleanly.", "keywords": ["i'll stop here", "understood, we can end this", "won't call again"]},
}

QUALITY_DIMENSIONS = ["directness", "specificity", "low_pressure", "empathy", "relevance", "brevity", "safety", "progression"]

REACTION_KEYWORDS: dict[str, list[str]] = {
    "softens": ["okay", "alright", "that helps", "fair enough", "got it"],
    "asks_for_details": ["what exactly", "how does", "tell me more", "details"],
    "repeats_question": ["i asked", "you didn't answer", "still haven't", "that doesn't answer"],
    "rejects": ["not interested", "no thanks", "stop calling", "i'm done"],
    "asks_for_written_info": ["send it", "email it", "written", "send me details"],
    "requests_callback": ["call me later", "callback", "next week", "another time"],
    "escalates": ["this is annoying", "you are not listening", "don't call again", "ridiculous"],
    "gets_confused": ["not sure i follow", "sounds vague", "i'm confused"],
    "sets_boundary": ["email only", "keep it short", "no payment", "no commitment"],
    "asks_for_manager_review": ["my manager", "procurement", "need approval"],
    "asks_for_handoff": ["specialist", "support team", "someone technical"],
    "accepts_low_pressure_next_step": ["that works", "send times", "we can do that"],
    "challenges_claim": ["how can you prove", "that sounds like a claim", "is that guaranteed"],
    "asks_identity_again": ["who are you again", "which company again"],
}

FAILURE_TARGETS: dict[str, dict[str, Any]] = {
    "dodged_direct_question": {"description": "Agent avoids direct question and pivots away."},
    "asked_too_many_questions": {"description": "Agent asks multiple questions before answering key intent."},
    "repeated_answer": {"description": "Agent repeats the same answer with no progress."},
    "ignored_customer_input": {"description": "Agent response does not address latest customer input."},
    "pressure_after_refusal": {"description": "Agent continues pressure after clear refusal."},
    "unsupported_claim": {"description": "Agent makes unsupported legal/medical/financial/security claim."},
    "premature_price_discussion": {"description": "Agent leads with price before context where inappropriate."},
    "failed_support_boundary": {"description": "Agent fails to route support/cancellation boundary safely."},
    "unsafe_payment_request": {"description": "Agent requests payment/card details unsafely."},
    "vague_pitch": {"description": "Agent uses vague pitch without concrete relevance."},
    "missed_emotional_signal": {"description": "Agent ignores clear emotional signal."},
    "overpromised_results": {"description": "Agent overpromises guaranteed outcomes."},
    "wrong_handoff": {"description": "Agent routes to wrong path or skips required specialist."},
    "unclear_next_step": {"description": "Agent next step is ambiguous or not actionable."},
    "feature_dump": {"description": "Agent gives long feature list without intent alignment."},
    "failed_identity_repair": {"description": "Agent fails identity clarification when asked."},
    "failed_existing_provider_objection": {"description": "Agent mishandles existing-provider objection."},
    "failed_manager_approval_path": {"description": "Agent mishandles manager-approval path."},
}

RECOVERY_BY_FAILURE: dict[str, list[str]] = {
    "dodged_direct_question": ["acknowledge_emotion", "answer_directly", "low_pressure_boundary"],
    "asked_too_many_questions": ["answer_directly", "time_respectful", "single_discovery_question"],
    "repeated_answer": ["acknowledge_emotion", "one_concrete_relevance_point", "low_pressure_boundary"],
    "ignored_customer_input": ["objection_isolation", "answer_directly", "low_pressure_boundary"],
    "pressure_after_refusal": ["stop_after_refusal", "low_pressure_boundary"],
    "unsupported_claim": ["trust_repair", "proof_without_unsupported_claim", "written_info_offer"],
    "premature_price_discussion": ["permission_first", "reason_first", "single_discovery_question"],
    "failed_support_boundary": ["support_boundary_route", "handoff_to_specialist", "acknowledge_emotion"],
    "unsafe_payment_request": ["payment_safety_boundary", "trust_repair", "stop_after_refusal"],
    "vague_pitch": ["simple_explanation", "one_concrete_relevance_point"],
    "missed_emotional_signal": ["acknowledge_emotion", "trust_repair"],
    "overpromised_results": ["risk_reversal", "proof_without_unsupported_claim"],
    "wrong_handoff": ["handoff_to_specialist", "manager_review_offer"],
    "unclear_next_step": ["low_pressure_boundary", "written_info_offer", "callback_offer"],
    "feature_dump": ["time_respectful", "single_discovery_question", "one_concrete_relevance_point"],
    "failed_identity_repair": ["answer_directly", "reason_first"],
    "failed_existing_provider_objection": ["objection_isolation", "one_concrete_relevance_point"],
    "failed_manager_approval_path": ["manager_review_offer", "written_info_offer"],
}

RECOVERY_TACTIC_REPLACEMENTS = {
    "next_step_close": "low_pressure_boundary",
    "brevity_reset": "time_respectful",
}

SIMPLE_EMOTION_STATES = {
    "skeptical",
    "confused",
    "rushed",
    "irritated",
    "anxious",
    "distrustful",
    "curious",
    "calm",
}


@dataclass(frozen=True)
class ParsedRecord:
    zip_name: str
    source_hash: str
    member_name: str
    ext: str
    text: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class Segment:
    text: str
    role: str


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel_path(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def lower_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def normalize_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def contains_any(text: str, phrases: Iterable[str]) -> bool:
    lowered = lower_text(text)
    return any(phrase in lowered for phrase in phrases)


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", lower_text(text)))


def safe_confidence(support_count: int) -> str:
    if support_count >= 90:
        return "high"
    if support_count >= 20:
        return "medium"
    return "low"


def member_is_noise(member_name: str) -> bool:
    lowered = member_name.lower()
    if any(lowered.startswith(prefix.lower()) for prefix in NOISE_MEMBER_PREFIXES):
        return True
    short_name = lowered.split("/")[-1]
    if short_name in NOISE_MEMBER_NAMES:
        return True
    if short_name.startswith("._"):
        return True
    return False


def extension_of(member_name: str) -> str:
    lower = member_name.lower()
    for ext in SUPPORTED_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    return ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def parse_json_bytes(raw: bytes) -> list[dict[str, Any]]:
    decoded = raw.decode("utf-8", errors="ignore")
    stripped = decoded.strip()
    if not stripped:
        return []
    try:
        loaded = json.loads(stripped)
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
        return records
    if isinstance(loaded, dict):
        return [loaded]
    if isinstance(loaded, list):
        return [entry for entry in loaded if isinstance(entry, dict)]
    return []


def parse_jsonl_bytes(raw: bytes) -> list[dict[str, Any]]:
    decoded = raw.decode("utf-8", errors="ignore")
    rows: list[dict[str, Any]] = []
    for line in decoded.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def parse_csv_like_bytes(raw: bytes, delimiter: str) -> list[dict[str, Any]]:
    decoded = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
    rows: list[dict[str, Any]] = []
    for row in reader:
        rows.append({str(key or "").strip(): value for key, value in row.items()})
    return rows


def parse_txt_bytes(raw: bytes) -> list[dict[str, Any]]:
    decoded = raw.decode("utf-8", errors="ignore")
    if not decoded.strip():
        return []
    return [{"text": decoded}]


def parse_zip_member(raw: bytes, ext: str) -> list[dict[str, Any]]:
    if ext == ".json":
        return parse_json_bytes(raw)
    if ext == ".jsonl":
        return parse_jsonl_bytes(raw)
    if ext == ".csv":
        return parse_csv_like_bytes(raw, ",")
    if ext == ".tsv":
        return parse_csv_like_bytes(raw, "\t")
    if ext == ".txt":
        return parse_txt_bytes(raw)
    return []


def extract_text_from_record(record: dict[str, Any]) -> str:
    for key in ("text", "transcript", "content", "utterance", "message", "normalized_text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:MAX_TEXT_LENGTH]
    words = record.get("words")
    if isinstance(words, list):
        chunks: list[str] = []
        for item in words:
            if not isinstance(item, dict):
                continue
            token = item.get("text")
            if isinstance(token, str) and token.strip():
                chunks.append(token.strip())
            if len(chunks) >= 1500:
                break
        if chunks:
            return " ".join(chunks)[:MAX_TEXT_LENGTH]
    return ""


def split_into_segments(text: str) -> list[str]:
    cleaned = re.sub(r"\[[A-Z_]+\]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []
    raw_parts = re.split(r"(?<=[\.\?\!])\s+|[\r\n]+", cleaned)
    parts: list[str] = []
    for part in raw_parts:
        normalized = re.sub(r"\s+", " ", part).strip(" -\t\r\n")
        if len(normalized) < 2:
            continue
        parts.append(normalized)
        if len(parts) >= MAX_SEGMENTS_PER_RECORD:
            break
    return parts


def infer_segment_role(segment_text: str, index: int, previous_role: str | None) -> str:
    lowered = lower_text(segment_text)
    if contains_any(lowered, SPEAKER_HINT_AGENT):
        return "agent"
    if contains_any(lowered, SPEAKER_HINT_CUSTOMER):
        return "customer"
    if previous_role == "agent":
        return "customer"
    if previous_role == "customer":
        return "agent"
    return "agent" if index % 2 == 0 else "customer"


def classify_customer_moves(segment_text: str) -> list[str]:
    lowered = lower_text(segment_text)
    matches: list[str] = []
    for move_id, config in MOVE_TARGETS.items():
        keywords = config.get("keywords", [])
        if contains_any(lowered, keywords):
            matches.append(move_id)
    return matches


def classify_agent_tactics(segment_text: str) -> list[str]:
    lowered = lower_text(segment_text)
    matches: list[str] = []
    for tactic_id, config in AGENT_TACTIC_TARGETS.items():
        if contains_any(lowered, config.get("keywords", [])):
            matches.append(tactic_id)
    if "?" in segment_text and len(matches) == 0:
        matches.append("single_discovery_question")
    return sorted(set(matches))


def classify_reaction(segment_text: str) -> list[str]:
    lowered = lower_text(segment_text)
    matches: list[str] = []
    for reaction_id, keywords in REACTION_KEYWORDS.items():
        if contains_any(lowered, keywords):
            matches.append(reaction_id)
    if "?" in segment_text and "asks_for_details" not in matches:
        matches.append("asks_for_details")
    return sorted(set(matches))


def detect_customer_emotion(segment_text: str) -> str:
    lowered = lower_text(segment_text)
    if any(token in lowered for token in ("angry", "annoy", "frustrat", "stop calling")):
        return "irritated"
    if any(token in lowered for token in ("confused", "not sure", "unclear", "vague")):
        return "confused"
    if any(token in lowered for token in ("scam", "fraud", "trust", "distrust", "card")):
        return "distrustful"
    if any(token in lowered for token in ("busy", "minute", "short on time")):
        return "rushed"
    if any(token in lowered for token in ("worried", "concerned", "anxious")):
        return "anxious"
    if "?" in segment_text:
        return "curious"
    return "calm"


def quality_dimensions_for_agent_text(agent_text: str, move_id: str | None) -> dict[str, str]:
    lowered = lower_text(agent_text)
    tokens = token_set(agent_text)
    word_count = len(tokens)
    directness = "high" if any(token in lowered for token in ("price is", "cost is", "i can", "yes", "no")) else "medium"
    if move_id == "price_first" and not any(token in lowered for token in ("price", "cost", "$", "starts at", "budget")):
        directness = "low"
    specificity = "high" if re.search(r"\b\d+\b", lowered) else "medium"
    low_pressure = "high" if any(token in lowered for token in ("no pressure", "optional", "no obligation", "we can stop")) else "medium"
    empathy = "high" if any(token in lowered for token in ("i understand", "i hear", "sorry", "fair point")) else "low"
    relevance = "high" if move_id and any(token in lowered for token in MOVE_TARGETS[move_id]["keywords"][:3]) else "medium"
    brevity = "high" if word_count <= 22 else "medium"
    safety = "high"
    if any(token in lowered for token in ("guaranteed", "100%", "credit card now", "bank details now")):
        safety = "low"
    progression = "high" if any(token in lowered for token in ("next step", "send", "callback", "review", "handoff")) else "medium"
    return {
        "directness": directness,
        "specificity": specificity,
        "low_pressure": low_pressure,
        "empathy": empathy,
        "relevance": relevance,
        "brevity": brevity,
        "safety": safety,
        "progression": progression,
    }


def dominant_quality(values: list[str]) -> str:
    if not values:
        return "medium"
    counts = Counter(values)
    return counts.most_common(1)[0][0]


def reaction_state_delta(reaction_id: str) -> tuple[dict[str, int], str]:
    mapping = {
        "softens": ({"trust": 1, "patience": 0, "clarity": 1, "interest": 1, "friction": -1}, "skeptical_or_cautious"),
        "asks_for_details": ({"trust": 0, "patience": 0, "clarity": 1, "interest": 1, "friction": 0}, "curious"),
        "repeats_question": ({"trust": -1, "patience": -1, "clarity": -1, "interest": -1, "friction": 1}, "skeptical"),
        "rejects": ({"trust": -2, "patience": -1, "clarity": 0, "interest": -2, "friction": 2}, "more_resistant"),
        "asks_for_written_info": ({"trust": 0, "patience": 0, "clarity": 1, "interest": 0, "friction": -1}, "cautious"),
        "requests_callback": ({"trust": 0, "patience": 0, "clarity": 0, "interest": 0, "friction": 0}, "unchanged"),
        "escalates": ({"trust": -2, "patience": -2, "clarity": -1, "interest": -2, "friction": 2}, "escalated"),
        "gets_confused": ({"trust": -1, "patience": -1, "clarity": -2, "interest": -1, "friction": 1}, "confused"),
        "sets_boundary": ({"trust": 0, "patience": 0, "clarity": 0, "interest": -1, "friction": 0}, "unchanged"),
        "asks_for_manager_review": ({"trust": 0, "patience": 0, "clarity": 1, "interest": 0, "friction": 0}, "cautious"),
        "asks_for_handoff": ({"trust": 0, "patience": 0, "clarity": 1, "interest": 0, "friction": 0}, "reassured"),
        "accepts_low_pressure_next_step": ({"trust": 1, "patience": 0, "clarity": 1, "interest": 1, "friction": -1}, "more_trusting"),
        "challenges_claim": ({"trust": -1, "patience": -1, "clarity": 0, "interest": -1, "friction": 1}, "skeptical"),
        "asks_identity_again": ({"trust": -1, "patience": -1, "clarity": -1, "interest": -1, "friction": 1}, "distrustful"),
    }
    return mapping.get(reaction_id, ({"trust": 0, "patience": 0, "clarity": 0, "interest": 0, "friction": 0}, "unchanged"))


def failure_signals(
    move_id: str | None,
    move_text: str,
    tactic_ids: list[str],
    agent_text: str,
    previous_agent_text: str | None,
    customer_reaction_ids: list[str],
) -> list[str]:
    lowered = lower_text(agent_text)
    failures: list[str] = []
    if move_id in {"price_first", "who_are_you", "technical_question"} and "answer_directly" not in tactic_ids:
        failures.append("dodged_direct_question")
    if agent_text.count("?") >= 2:
        failures.append("asked_too_many_questions")
    if previous_agent_text:
        prev_tokens = token_set(previous_agent_text)
        now_tokens = token_set(agent_text)
        if prev_tokens and now_tokens:
            overlap = len(prev_tokens & now_tokens) / max(len(prev_tokens), len(now_tokens))
            if overlap >= 0.86 and len(agent_text.split()) > 8:
                failures.append("repeated_answer")
    if move_id and tactic_ids == []:
        failures.append("ignored_customer_input")
    if move_id in {"not_interested", "hostile_rejection"} and not any(tid in tactic_ids for tid in ("stop_after_refusal", "low_pressure_boundary")):
        if any(token in lowered for token in ("let's book", "lock this in", "just say yes", "don't miss")):
            failures.append("pressure_after_refusal")
    if any(token in lowered for token in ("guaranteed", "100%", "always approved", "covered no matter what")):
        failures.append("unsupported_claim")
    if move_id is None and any(token in lowered for token in ("price", "cost")) and "reason_first" not in tactic_ids:
        failures.append("premature_price_discussion")
    if move_id in {"support_issue", "cancellation_request", "sensitive_healthcare_concern"} and not any(
        tid in tactic_ids for tid in ("support_boundary_route", "handoff_to_specialist", "acknowledge_emotion")
    ):
        failures.append("failed_support_boundary")
    if any(token in lowered for token in ("credit card number", "card details now", "bank account right now")):
        failures.append("unsafe_payment_request")
    if any(token in lowered for token in ("great offer", "amazing opportunity", "best solution ever")):
        failures.append("vague_pitch")
    if move_id in {"bad_previous_experience", "hostile_rejection", "scam_or_card_fear"} and "acknowledge_emotion" not in tactic_ids:
        failures.append("missed_emotional_signal")
    if any(token in lowered for token in ("guaranteed results", "instant results", "zero risk guaranteed")):
        failures.append("overpromised_results")
    if move_id in {"technical_question", "security_review"} and "handoff_to_specialist" not in tactic_ids and "simple_explanation" not in tactic_ids:
        failures.append("wrong_handoff")
    if not any(token in lowered for token in ("next step", "send", "email", "callback", "handoff", "review", "stop")):
        failures.append("unclear_next_step")
    if len(agent_text.split()) >= 55:
        failures.append("feature_dump")
    if move_id == "who_are_you" and not any(tid in tactic_ids for tid in ("answer_directly", "reason_first", "trust_repair")):
        failures.append("failed_identity_repair")
    if move_id == "existing_provider" and not any(tid in tactic_ids for tid in ("objection_isolation", "one_concrete_relevance_point", "trust_repair")):
        failures.append("failed_existing_provider_objection")
    if move_id == "needs_manager_approval" and not any(
        tid in tactic_ids for tid in ("manager_review_offer", "written_info_offer", "low_pressure_boundary")
    ):
        failures.append("failed_manager_approval_path")
    if "rejects" in customer_reaction_ids and any(tid in tactic_ids for tid in ("hard_close",)):
        failures.append("pressure_after_refusal")
    return sorted(set(failures))


def parse_raw_sources(raw_source_dir: Path) -> tuple[dict[str, Any], list[ParsedRecord], dict[str, str]]:
    zip_files = sorted(path for path in raw_source_dir.glob("*.zip") if path.is_file())
    zip_hashes = {path.name: sha256_file(path) for path in zip_files}

    parse_summary = {
        "checkpoint_id": CHECKPOINT_ID,
        "raw_source_dir": rel_path(raw_source_dir),
        "zip_file_count": len(zip_files),
        "parsed_zip_file_count": 0,
        "unsupported_zip_file_count": 0,
        "parsed_inner_file_count": 0,
        "parsed_file_type_counts": {"csv": 0, "json": 0, "jsonl": 0, "txt": 0, "tsv": 0},
        "estimated_record_count": 0,
        "detected_columns_or_keys": [],
        "parse_failures": [],
        "raw_text_stored_in_outputs": False,
        "abstract_pattern_only": True,
        "coverage_gaps": [],
    }

    detected_keys: set[str] = set()
    parsed_records: list[ParsedRecord] = []
    parse_failures: list[dict[str, str]] = []
    total_parsed_records = 0

    for zip_path in zip_files:
        parsed_this_zip = False
        parsed_records_this_zip = 0
        try:
            with zipfile.ZipFile(zip_path) as archive:
                members = archive.infolist()
                for info in members:
                    member_name = info.filename
                    ext = extension_of(member_name)
                    if not ext:
                        continue
                    if member_is_noise(member_name):
                        continue
                    parse_summary["estimated_record_count"] += 1
                    if total_parsed_records >= MAX_PARSED_RECORDS or parsed_records_this_zip >= MAX_PARSED_RECORDS_PER_ZIP:
                        continue
                    try:
                        raw = archive.read(member_name)
                        rows = parse_zip_member(raw, ext)
                    except Exception as exc:  # pragma: no cover - defensive parsing
                        if len(parse_failures) < MAX_PARSE_FAILURES:
                            parse_failures.append(
                                {
                                    "zip_file": zip_path.name,
                                    "member": member_name,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )
                        continue
                    parse_summary["parsed_inner_file_count"] += 1
                    parse_summary["parsed_file_type_counts"][ext[1:]] += 1
                    parsed_this_zip = True
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        text = extract_text_from_record(row)
                        if not text:
                            continue
                        keys = tuple(sorted(str(key) for key in row.keys() if key))
                        for key in keys:
                            if len(detected_keys) < MAX_DETECTED_KEYS:
                                detected_keys.add(key)
                        parsed_records.append(
                            ParsedRecord(
                                zip_name=zip_path.name,
                                source_hash=zip_hashes[zip_path.name],
                                member_name=member_name,
                                ext=ext[1:],
                                text=text,
                                keys=keys,
                            )
                        )
                        total_parsed_records += 1
                        parsed_records_this_zip += 1
                        if total_parsed_records >= MAX_PARSED_RECORDS or parsed_records_this_zip >= MAX_PARSED_RECORDS_PER_ZIP:
                            break
                    if total_parsed_records >= MAX_PARSED_RECORDS or parsed_records_this_zip >= MAX_PARSED_RECORDS_PER_ZIP:
                        continue
        except zipfile.BadZipFile as exc:
            parse_summary["unsupported_zip_file_count"] += 1
            if len(parse_failures) < MAX_PARSE_FAILURES:
                parse_failures.append({"zip_file": zip_path.name, "member": "", "error": f"BadZipFile: {exc}"})
            continue
        if parsed_this_zip:
            parse_summary["parsed_zip_file_count"] += 1
        else:
            parse_summary["unsupported_zip_file_count"] += 1

    parse_summary["detected_columns_or_keys"] = sorted(detected_keys)
    parse_summary["parse_failures"] = parse_failures
    return parse_summary, parsed_records, zip_hashes


def build_existing_pattern_index(pattern_bank_path: Path, scenario_bank_path: Path) -> dict[str, Any]:
    existing_artifacts_available = {"prod_013": pattern_bank_path.exists(), "prod_014": scenario_bank_path.exists()}
    pattern_records: list[dict[str, str]] = []

    if pattern_bank_path.exists():
        payload = json.loads(pattern_bank_path.read_text(encoding="utf-8"))
        bank = payload.get("pattern_bank", {})
        for section_name, section_value in bank.items():
            if isinstance(section_value, list):
                for item in section_value:
                    if not isinstance(item, dict):
                        continue
                    pid = str(item.get("pattern_id") or item.get("template_id") or "")
                    if not pid:
                        continue
                    text_blob = json.dumps(item, ensure_ascii=False).lower()
                    pattern_records.append({"id": pid, "blob": text_blob, "source": SOURCE_CHECKPOINTS[0], "section": section_name})

    if scenario_bank_path.exists():
        payload = json.loads(scenario_bank_path.read_text(encoding="utf-8"))
        raw_scenarios = payload.get("scenario_bank", [])
        if isinstance(raw_scenarios, dict):
            packets = raw_scenarios.get("scenario_packets", [])
        elif isinstance(raw_scenarios, list):
            packets = raw_scenarios
        else:
            packets = []
        for packet in packets:
            if not isinstance(packet, dict):
                continue
            pid = str(packet.get("scenario_id") or "")
            if not pid:
                continue
            text_blob = json.dumps(packet.get("source_pattern_ids", []), ensure_ascii=False).lower() + " " + json.dumps(
                packet.get("scenario_labels", []), ensure_ascii=False
            ).lower()
            pattern_records.append({"id": pid, "blob": text_blob, "source": SOURCE_CHECKPOINTS[1], "section": "scenario_packets"})

    return {
        "available": existing_artifacts_available,
        "records": pattern_records,
    }


def pick_existing_pattern_ids(existing_index: dict[str, Any], keywords: list[str], limit: int = MAX_PATTERN_IDS_PER_PATTERN) -> list[str]:
    records = existing_index.get("records", [])
    chosen: list[str] = []
    for record in records:
        blob = record.get("blob", "")
        if any(keyword in blob for keyword in keywords):
            chosen.append(str(record["id"]))
            if len(chosen) >= limit:
                break
    return chosen


def analyze_records(
    parsed_records: list[ParsedRecord], existing_index: dict[str, Any]
) -> tuple[
    dict[str, Any],
    Counter[str],
    Counter[str],
    Counter[tuple[str, str]],
    dict[tuple[str, str], list[dict[str, str]]],
    Counter[tuple[str, str, str]],
    Counter[tuple[str, str, str, str]],
    Counter[str],
    dict[str, list[str]],
    Counter[tuple[str, str]],
    dict[tuple[str, str], set[str]],
    dict[str, set[str]],
]:
    move_counts: Counter[str] = Counter()
    tactic_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    pair_quality: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    reaction_counts: Counter[tuple[str, str, str]] = Counter()
    next_action_counts: Counter[tuple[str, str, str, str]] = Counter()
    failure_counts: Counter[str] = Counter()
    recovery_links: dict[str, list[str]] = defaultdict(list)
    state_transition_counts: Counter[tuple[str, str]] = Counter()
    pattern_source_files: dict[tuple[str, str], set[str]] = defaultdict(set)
    category_source_files: dict[str, set[str]] = defaultdict(set)

    summary = {
        "records_analyzed": len(parsed_records),
        "segments_analyzed": 0,
        "customer_segments": 0,
        "agent_segments": 0,
    }

    for record in parsed_records:
        segments_text = split_into_segments(record.text)
        if not segments_text:
            continue
        segments: list[Segment] = []
        previous_role: str | None = None
        for idx, part in enumerate(segments_text):
            role = infer_segment_role(part, idx, previous_role)
            segments.append(Segment(text=part, role=role))
            previous_role = role
        summary["segments_analyzed"] += len(segments)

        previous_agent_text: str | None = None
        current_move: str | None = None
        last_agent_tactics: list[str] = []

        for seg_index, segment in enumerate(segments):
            if segment.role == "customer":
                summary["customer_segments"] += 1
                move_ids = classify_customer_moves(segment.text)
                if move_ids:
                    current_move = move_ids[0]
                    for move_id in move_ids:
                        move_counts[move_id] += 1
                        pattern_source_files[("customer_move", move_id)].add(record.zip_name)
                        category_source_files["customer_move"].add(record.zip_name)
                if current_move and last_agent_tactics:
                    reaction_ids = classify_reaction(segment.text)
                    if not reaction_ids:
                        reaction_ids = ["asks_for_details"] if "?" in segment.text else ["softens"]
                    for reaction_id in reaction_ids:
                        reaction_counts[(current_move, last_agent_tactics[0], reaction_id)] += 1
                        pattern_source_files[("customer_reaction", reaction_id)].add(record.zip_name)
                        category_source_files["customer_reaction"].add(record.zip_name)
                    emotion = detect_customer_emotion(segment.text)
                    for reaction_id in reaction_ids:
                        delta, _emotion_to = reaction_state_delta(reaction_id)
                        transition_key = (current_move, last_agent_tactics[0])
                        state_transition_counts[transition_key] += 1
                        pattern_source_files[("state_transition", f"{current_move}:{last_agent_tactics[0]}")].add(record.zip_name)
                        category_source_files["state_transition"].add(record.zip_name)
                        failures = failure_signals(current_move, segment.text, last_agent_tactics, previous_agent_text or "", previous_agent_text, reaction_ids)
                        for failure_id in failures:
                            failure_counts[failure_id] += 1
                            pattern_source_files[("failure", failure_id)].add(record.zip_name)
                            category_source_files["failure"].add(record.zip_name)
                            for recovery in RECOVERY_BY_FAILURE.get(failure_id, []):
                                recovery_links[failure_id].append(recovery)
                        _ = delta
                        _ = emotion
                continue

            summary["agent_segments"] += 1
            tactic_ids = classify_agent_tactics(segment.text)
            if not tactic_ids:
                if "?" in segment.text:
                    tactic_ids = ["single_discovery_question"]
                elif any(token in lower_text(segment.text) for token in ("send", "email")):
                    tactic_ids = ["written_info_offer"]
                elif any(token in lower_text(segment.text) for token in ("callback", "call back")):
                    tactic_ids = ["callback_offer"]
                else:
                    tactic_ids = ["simple_explanation"]
            for tactic_id in tactic_ids:
                tactic_counts[tactic_id] += 1
                pattern_source_files[("agent_tactic", tactic_id)].add(record.zip_name)
                category_source_files["agent_tactic"].add(record.zip_name)
            if current_move:
                pair = (current_move, tactic_ids[0])
                pair_counts[pair] += 1
                pattern_source_files[("move_tactic", f"{pair[0]}:{pair[1]}")].add(record.zip_name)
                category_source_files["move_tactic"].add(record.zip_name)
                pair_quality[pair].append(quality_dimensions_for_agent_text(segment.text, current_move))
                next_customer_reactions = classify_reaction(segments[seg_index + 1].text) if seg_index + 1 < len(segments) and segments[seg_index + 1].role == "customer" else []
                if not next_customer_reactions:
                    next_customer_reactions = ["asks_for_details"]
                lookahead_tactics: list[str] = []
                for look_idx in range(seg_index + 1, min(seg_index + 5, len(segments))):
                    if segments[look_idx].role != "agent":
                        continue
                    lookahead_tactics = classify_agent_tactics(segments[look_idx].text)
                    if lookahead_tactics:
                        break
                next_tactic = lookahead_tactics[0] if lookahead_tactics else "low_pressure_boundary"
                for reaction_id in next_customer_reactions:
                    next_action_counts[(current_move, tactic_ids[0], reaction_id, next_tactic)] += 1
                    pattern_source_files[("next_action", f"{current_move}:{tactic_ids[0]}:{reaction_id}:{next_tactic}")].add(record.zip_name)
                    category_source_files["next_action"].add(record.zip_name)
            last_agent_tactics = tactic_ids
            previous_agent_text = segment.text

    extracted = {
        "records_analyzed": summary["records_analyzed"],
        "segments_analyzed": summary["segments_analyzed"],
        "customer_segments": summary["customer_segments"],
        "agent_segments": summary["agent_segments"],
        "existing_pattern_refs_used": len(existing_index.get("records", [])),
    }
    return (
        extracted,
        move_counts,
        tactic_counts,
        pair_counts,
        pair_quality,
        reaction_counts,
        next_action_counts,
        failure_counts,
        recovery_links,
        state_transition_counts,
        pattern_source_files,
        category_source_files,
    )


def source_refs_for(
    key: tuple[str, str], pattern_source_files: dict[tuple[str, str], set[str]], zip_hashes: dict[str, str]
) -> list[dict[str, str]]:
    refs = []
    for source_name in sorted(pattern_source_files.get(key, set()))[:MAX_SOURCE_REFS_PER_PATTERN]:
        refs.append({"source_file": source_name, "source_hash": zip_hashes.get(source_name, "sha256:unknown")})
    return refs


def ensure_boundary_fields(payload: dict[str, Any]) -> dict[str, Any]:
    payload.update(BOUNDARY_FLAGS)
    return add_support_count_metadata(payload)


def build_source_pattern_index(
    parse_summary: dict[str, Any],
    existing_index: dict[str, Any],
    move_counts: Counter[str],
    tactic_counts: Counter[str],
    reaction_counts: Counter[tuple[str, str, str]],
    failure_counts: Counter[str],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    indexed_patterns: list[dict[str, Any]] = []

    def add_indexed(category: str, label: str, count: int) -> None:
        pattern_id = f"raw-derived-{category}-{normalize_id(label)}-001"
        refs = source_refs_for((category, label), pattern_source_files, zip_hashes)
        indexed_patterns.append(
            {
                "source_pattern_id": pattern_id,
                "source_type": "raw_aggregate",
                "abstract_category": category,
                "normalized_label": label,
                "support_count_estimate": int(count),
                "source_file_refs": refs,
                "abstract_pattern_only": True,
            }
        )

    for move_id, count in sorted(move_counts.items(), key=lambda item: item[1], reverse=True):
        add_indexed("customer_move", move_id, count)
    for tactic_id, count in sorted(tactic_counts.items(), key=lambda item: item[1], reverse=True):
        add_indexed("agent_tactic", tactic_id, count)
    reaction_label_counts: Counter[str] = Counter()
    for (_, _, reaction_id), count in reaction_counts.items():
        reaction_label_counts[reaction_id] += count
    for reaction_id, count in sorted(reaction_label_counts.items(), key=lambda item: item[1], reverse=True):
        add_indexed("customer_reaction", reaction_id, count)
    for failure_id, count in sorted(failure_counts.items(), key=lambda item: item[1], reverse=True):
        add_indexed("failure", failure_id, count)

    category_counts = {
        "customer_move": len(move_counts),
        "agent_tactic": len(tactic_counts),
        "customer_reaction": len(reaction_label_counts),
        "outcome": len(reaction_label_counts),
        "failure": len(failure_counts),
        "recovery": len([key for key, values in RECOVERY_BY_FAILURE.items() if values]),
        "safety": 3,
        "emotion": len(SIMPLE_EMOTION_STATES),
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_checkpoints": SOURCE_CHECKPOINTS,
        "raw_source_dir": parse_summary["raw_source_dir"],
        "source_files": sorted(zip_hashes.keys()),
        "source_file_hashes": [{"source_file": name, "source_hash": digest} for name, digest in sorted(zip_hashes.items())],
        "source_pattern_count": len(indexed_patterns),
        "raw_derived_pattern_count": len(indexed_patterns),
        "existing_abstract_pattern_count": len(existing_index.get("records", [])),
        "pattern_categories": category_counts,
        "indexed_patterns": indexed_patterns,
        "source_reliability": {
            "raw_zip_parse_successful": parse_summary["parsed_zip_file_count"] > 0 and parse_summary["parsed_inner_file_count"] > 0,
            "existing_prod_013_available": bool(existing_index["available"]["prod_013"]),
            "existing_prod_014_available": bool(existing_index["available"]["prod_014"]),
            "existing_artifacts_used_for_cross_check": len(existing_index.get("records", [])) > 0,
            "preferred_source_when_conflict": "raw_aggregate_patterns",
        },
        "source_use_boundaries": {
            **BOUNDARY_FLAGS,
            "provider_calls_made": False,
            "llm_used": False,
        },
        "coverage_gaps": [],
    }
    return add_support_count_metadata(payload)


def support_payload(
    support_count: int, source_pattern_ids: list[str], source_refs: list[dict[str, str]], include_low_support_note: bool = False
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "support_count_estimate": int(support_count),
        "source_pattern_ids": source_pattern_ids,
        "source_file_refs": source_refs,
    }
    if include_low_support_note and support_count == 0:
        payload["support_note"] = "weak_support"
    return payload


def add_standard_boundaries(item: dict[str, Any]) -> dict[str, Any]:
    item["abstract_pattern_only"] = True
    item["uses_exact_transcript_text"] = False
    item["uses_source_transcript_sequence"] = False
    item["uses_dataset_specific_phrasing"] = False
    return item


def add_support_count_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    payload["support_count_method"] = SUPPORT_COUNT_METHOD
    payload["support_count_limitations"] = SUPPORT_COUNT_LIMITATIONS
    return payload


def unique_ordered_tactics(tactic_ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for tactic_id in tactic_ids:
        if not tactic_id or tactic_id in seen:
            continue
        seen.add(tactic_id)
        ordered.append(tactic_id)
    return ordered


def safe_boundary_sequence_for_move(move_id: str) -> list[str]:
    if move_id in {"support_issue", "cancellation_request"}:
        return ["support_boundary_route", "handoff_to_specialist", "low_pressure_boundary"]
    if move_id in {"technical_question", "security_review", "sensitive_healthcare_concern"}:
        return ["handoff_to_specialist", "low_pressure_boundary", "stop_after_refusal"]
    if move_id in {"email_only", "send_info"}:
        return ["low_pressure_boundary", "written_info_offer", "stop_after_refusal"]
    return ["low_pressure_boundary", "stop_after_refusal", "handoff_to_specialist"]


def build_customer_move_patterns(
    move_counts: Counter[str],
    existing_index: dict[str, Any],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for move_id, cfg in MOVE_TARGETS.items():
        support_count = int(move_counts.get(move_id, 0))
        source_pattern_ids = [f"raw-derived-customer-move-{normalize_id(move_id)}-001"] + pick_existing_pattern_ids(
            existing_index, [normalize_id(move_id).replace("-", "_"), *cfg.get("keywords", [])]
        )
        refs = source_refs_for(("customer_move", move_id), pattern_source_files, zip_hashes)
        confidence = safe_confidence(support_count)
        if support_count == 0:
            coverage_gaps.append(
                {
                    "target_id": move_id,
                    "artifact": "customer_move_patterns",
                    "reason": "Insufficient source support found in parsed raw zip files.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
        pattern = {
            "customer_move_id": move_id,
            "name": cfg["name"],
            "description": cfg["description"],
            "customer_intent": cfg["customer_intent"],
            "emotional_signal": cfg["emotional_signal"],
            "common_contexts": cfg["common_contexts"],
            "trigger_signals_abstract": cfg["trigger_signals_abstract"],
            "sales_risk": cfg["sales_risk"],
            "preferred_agent_tactic_ids": cfg["preferred_agent_tactic_ids"],
            "tactics_to_avoid": cfg["tactics_to_avoid"],
            "likely_customer_reactions_if_handled_well": cfg["likely_customer_reactions_if_handled_well"],
            "likely_customer_reactions_if_mishandled": cfg["likely_customer_reactions_if_mishandled"],
            "source_support": support_payload(support_count, source_pattern_ids[:MAX_PATTERN_IDS_PER_PATTERN], refs, include_low_support_note=True),
            "confidence": confidence,
            "confidence_reason": "derived from aggregate raw counts and abstract pattern cross-check; no transcript text copied",
        }
        patterns.append(add_standard_boundaries(pattern))
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "customer_move_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
    }
    return add_support_count_metadata(payload)


def build_agent_response_tactics(
    tactic_counts: Counter[str],
    existing_index: dict[str, Any],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for tactic_id, cfg in AGENT_TACTIC_TARGETS.items():
        support_count = int(tactic_counts.get(tactic_id, 0))
        unsupported_target = support_count == 0
        source_pattern_ids = [f"raw-derived-agent-tactic-{normalize_id(tactic_id)}-001"] + pick_existing_pattern_ids(
            existing_index, [normalize_id(tactic_id).replace("-", "_"), *cfg.get("keywords", [])]
        )
        refs = source_refs_for(("agent_tactic", tactic_id), pattern_source_files, zip_hashes)
        if unsupported_target:
            coverage_gaps.append(
                {
                    "target_id": tactic_id,
                    "artifact": "agent_response_tactics",
                    "reason": "Insufficient source support found in parsed raw zip files.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
        pattern = {
            "agent_tactic_id": tactic_id,
            "name": cfg["name"],
            "description": cfg["description"],
            "best_used_for_customer_moves": [move_id for move_id, move_cfg in MOVE_TARGETS.items() if tactic_id in move_cfg["preferred_agent_tactic_ids"]][:8],
            "not_recommended_for": ["hostile_rejection", "cancellation_request"] if tactic_id in {"hard_close", "feature_dump"} else ["hostile_rejection_after_do_not_contact"],
            "response_structure_abstract": ["acknowledge customer move", "provide one clear response", "keep boundaries explicit", "offer optional next step"],
            "max_questions_before_answer": 0 if tactic_id == "answer_directly" else 1,
            "safety_boundaries": ["no unsupported claims", "no payment collection", "no pressure after refusal"],
            "common_failure_if_missing": ["customer repeats question", "customer loses trust"],
            "source_support": support_payload(support_count, source_pattern_ids[:MAX_PATTERN_IDS_PER_PATTERN], refs, include_low_support_note=True),
            "unsupported_target": unsupported_target,
            "confidence": "low" if unsupported_target else safe_confidence(support_count),
        }
        patterns.append(add_standard_boundaries(pattern))
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_response_tactics": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
    }
    return add_support_count_metadata(payload)


def build_agent_response_quality_patterns(
    pair_counts: Counter[tuple[str, str]],
    pair_quality: dict[tuple[str, str], list[dict[str, str]]],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for move_id in MOVE_TARGETS.keys():
        related_pairs = [pair for pair in pair_counts.keys() if pair[0] == move_id]
        if not related_pairs:
            coverage_gaps.append(
                {
                    "target_id": move_id,
                    "artifact": "agent_response_quality_patterns",
                    "reason": "No move+tactic pair observed for quality aggregation.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
            continue
        for move_tactic in sorted(related_pairs):
            support_count = int(pair_counts[move_tactic])
            qualities = pair_quality.get(move_tactic, [])
            dims = {
                dim: dominant_quality([quality.get(dim, "medium") for quality in qualities])
                for dim in QUALITY_DIMENSIONS
            }
            pattern_id = f"quality-{normalize_id(move_tactic[0])}-{normalize_id(move_tactic[1])}"
            refs = source_refs_for(("move_tactic", f"{move_tactic[0]}:{move_tactic[1]}"), pattern_source_files, zip_hashes)
            pattern = {
                "response_quality_pattern_id": pattern_id,
                "customer_move_id": move_tactic[0],
                "agent_tactic_id": move_tactic[1],
                "quality_dimensions": dims,
                "likely_effect": ["clarity_gain", "friction_reduction"] if dims["directness"] != "low" else ["friction_increase"],
                "risk_if_low_quality": ["customer repeats question", "customer becomes impatient"],
                "source_support": support_payload(
                    support_count,
                    [f"raw-derived-quality-{normalize_id(move_tactic[0])}-{normalize_id(move_tactic[1])}-001"],
                    refs,
                    include_low_support_note=True,
                ),
                "confidence": safe_confidence(support_count),
            }
            patterns.append(add_standard_boundaries(pattern))
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_response_quality_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
    }
    return add_support_count_metadata(payload)


def build_customer_reaction_patterns(
    reaction_counts: Counter[tuple[str, str, str]],
    quality_patterns: dict[str, Any],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    by_move_tactic: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for (move_id, tactic_id, reaction_id), count in reaction_counts.items():
        by_move_tactic[(move_id, tactic_id)][reaction_id] += count

    quality_by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)
    for item in quality_patterns["agent_response_quality_patterns"]:
        pair = (item["customer_move_id"], item["agent_tactic_id"])
        quality_by_pair[pair].append(item["response_quality_pattern_id"])

    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for move_id in MOVE_TARGETS.keys():
        pairs = [pair for pair in by_move_tactic.keys() if pair[0] == move_id]
        if not pairs:
            coverage_gaps.append(
                {
                    "target_id": move_id,
                    "artifact": "customer_reaction_patterns",
                    "reason": "No source-supported customer reaction observed for this move.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
            continue
        for pair in sorted(pairs):
            total = sum(by_move_tactic[pair].values())
            top_reactions = [reaction for reaction, _count in by_move_tactic[pair].most_common(4)]
            tendency = {
                "continuation": round(sum(count for reaction, count in by_move_tactic[pair].items() if reaction in {"softens", "asks_for_details", "asks_for_written_info"}) / total, 4),
                "valid_next_step": round(sum(count for reaction, count in by_move_tactic[pair].items() if reaction in {"requests_callback", "asks_for_written_info", "accepts_low_pressure_next_step"}) / total, 4),
                "written_info": round(by_move_tactic[pair].get("asks_for_written_info", 0) / total, 4),
                "callback": round(by_move_tactic[pair].get("requests_callback", 0) / total, 4),
                "rejection": round(by_move_tactic[pair].get("rejects", 0) / total, 4),
                "friction_increase": round(sum(count for reaction, count in by_move_tactic[pair].items() if reaction in {"repeats_question", "escalates", "rejects"}) / total, 4),
                "clarity_gain": round(sum(count for reaction, count in by_move_tactic[pair].items() if reaction in {"softens", "asks_for_details", "asks_for_written_info"}) / total, 4),
                "trust_repair": round(sum(count for reaction, count in by_move_tactic[pair].items() if reaction in {"softens", "accepts_low_pressure_next_step"}) / total, 4),
            }
            refs = source_refs_for(("customer_reaction", top_reactions[0] if top_reactions else "asks_for_details"), pattern_source_files, zip_hashes)
            pattern = {
                "customer_reaction_pattern_id": f"reaction-{normalize_id(pair[0])}-{normalize_id(pair[1])}",
                "customer_move_id": pair[0],
                "agent_tactic_id": pair[1],
                "response_quality_pattern_ids": quality_by_pair.get(pair, []),
                "likely_reaction_categories": top_reactions,
                "outcome_tendency": tendency,
                "source_support": support_payload(
                    total,
                    [f"raw-derived-reaction-{normalize_id(pair[0])}-{normalize_id(pair[1])}-001"],
                    refs,
                    include_low_support_note=True,
                ),
                "confidence": safe_confidence(total),
                "confidence_reason": "estimated from aggregate sequence counts; no per-transcript script reuse",
            }
            patterns.append(add_standard_boundaries(pattern))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "customer_reaction_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_customer_state_transition_patterns(
    reaction_patterns: dict[str, Any],
    state_transition_counts: Counter[tuple[str, str]],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for reaction_pattern in reaction_patterns["customer_reaction_patterns"]:
        move_id = reaction_pattern["customer_move_id"]
        tactic_id = reaction_pattern["agent_tactic_id"]
        support_count = int(state_transition_counts.get((move_id, tactic_id), reaction_pattern["source_support"]["support_count_estimate"]))
        reactions = reaction_pattern["likely_reaction_categories"]
        if not reactions:
            coverage_gaps.append(
                {
                    "target_id": f"{move_id}:{tactic_id}",
                    "artifact": "customer_state_transition_patterns",
                    "reason": "No dominant reaction for transition estimate.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
            continue
        deltas = [reaction_state_delta(reaction_id)[0] for reaction_id in reactions]
        aggregate = {
            dim: int(round(statistics.mean(delta[dim] for delta in deltas)))
            for dim in ("trust", "clarity", "friction", "patience", "interest")
        }
        emotion_to = reaction_state_delta(reactions[0])[1]
        refs = source_refs_for(("state_transition", f"{move_id}:{tactic_id}"), pattern_source_files, zip_hashes)
        pattern = {
            "state_transition_id": f"state-{normalize_id(move_id)}-{normalize_id(tactic_id)}-001",
            "customer_move_id": move_id,
            "agent_tactic_id": tactic_id,
            "response_quality_pattern_ids": reaction_pattern["response_quality_pattern_ids"],
            "state_delta": aggregate,
            "emotion_shift": {"from": "skeptical", "to": emotion_to},
            "reason": "estimated from dominant customer reaction categories after tactic",
            "source_support": support_payload(
                support_count,
                [f"raw-derived-state-{normalize_id(move_id)}-{normalize_id(tactic_id)}-001"],
                refs,
                include_low_support_note=True,
            ),
            "confidence": safe_confidence(support_count),
        }
        patterns.append(add_standard_boundaries(pattern))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "customer_state_transition_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_next_best_action_patterns(
    next_action_counts: Counter[tuple[str, str, str, str]],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    for (move_id, tactic_id, reaction_id, next_tactic), count in next_action_counts.items():
        grouped[(move_id, tactic_id, reaction_id)][next_tactic] += count
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for move_id in MOVE_TARGETS.keys():
        keys = [key for key in grouped.keys() if key[0] == move_id]
        if not keys:
            coverage_gaps.append(
                {
                    "target_id": move_id,
                    "artifact": "next_best_action_patterns",
                    "reason": "No observed move+tactic+reaction sequence with next tactic.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
            continue
        for key in sorted(keys):
            counts = grouped[key]
            total = sum(counts.values())
            observed_first_tactic = counts.most_common(1)[0][0] if counts else "low_pressure_boundary"
            recommended = [tactic_id for tactic_id, _count in counts.most_common(4) if tactic_id in AGENT_TACTIC_TARGETS]
            if not recommended:
                recommended = [tactic_id for tactic_id in MOVE_TARGETS[key[0]]["preferred_agent_tactic_ids"] if tactic_id in AGENT_TACTIC_TARGETS]
            if key[2] in RISK_REACTION_CATEGORIES:
                recommended = unique_ordered_tactics(safe_boundary_sequence_for_move(key[0]) + recommended)
                if key[2] in {"rejects", "escalates", "hostile_rejection", "says_do_not_contact"}:
                    recommended = [tactic_id for tactic_id in recommended if tactic_id != "single_discovery_question"]
            recommended = recommended[:4]
            avoid = ["feature_dump", "question_storming", "hard_close"]
            if key[2] in RISK_REACTION_CATEGORIES:
                avoid = unique_ordered_tactics(["single_discovery_question", "feature_dump", "question_storming", "hard_close"])
            first_ref_tactic = observed_first_tactic if observed_first_tactic in AGENT_TACTIC_TARGETS else (recommended[0] if recommended else "low_pressure_boundary")
            refs = source_refs_for(("next_action", f"{key[0]}:{key[1]}:{key[2]}:{first_ref_tactic}"), pattern_source_files, zip_hashes)
            pattern = {
                "next_best_action_id": f"nba-{normalize_id(key[0])}-{normalize_id(key[1])}-{normalize_id(key[2])}-001",
                "after_customer_move_id": key[0],
                "after_agent_tactic_id": key[1],
                "after_customer_reaction_category": key[2],
                "recommended_next_tactic_ids": recommended,
                "avoid_next_tactic_ids": avoid,
                "max_questions_next_turn": 1,
                "safety_boundaries": ["no pressure", "no unsupported claims"],
                "source_support": support_payload(
                    total,
                    [f"raw-derived-nba-{normalize_id(key[0])}-{normalize_id(key[1])}-{normalize_id(key[2])}-001"],
                    refs,
                    include_low_support_note=True,
                ),
                "confidence": safe_confidence(total),
            }
            patterns.append(add_standard_boundaries(pattern))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "next_best_action_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_failure_patterns(
    failure_counts: Counter[str],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    failure_signal_templates = {
        "dodged_direct_question": ["customer asked explicit question", "agent did not provide direct answer", "agent pivoted to discovery"],
        "asked_too_many_questions": ["agent asked multiple questions before answer", "customer intent unresolved"],
        "repeated_answer": ["high token overlap with prior agent answer", "no new information"],
        "ignored_customer_input": ["customer intent changed", "agent response did not address latest intent"],
        "pressure_after_refusal": ["clear refusal detected", "agent continued push"],
        "unsupported_claim": ["unverifiable guarantee language", "unsupported certainty language"],
        "premature_price_discussion": ["agent led with price", "customer did not ask price first"],
        "failed_support_boundary": ["support/cancellation cue present", "agent did not route support path"],
        "unsafe_payment_request": ["card/payment detail request in unsafe context"],
        "vague_pitch": ["generic value statement with no concrete relevance"],
        "missed_emotional_signal": ["emotional cue present", "no empathy/acknowledgement marker"],
        "overpromised_results": ["result guarantee marker present"],
        "wrong_handoff": ["specialist/handoff needed", "agent gave wrong or no route"],
        "unclear_next_step": ["next step missing concrete action"],
        "feature_dump": ["long feature-heavy monologue"],
        "failed_identity_repair": ["customer asked identity", "agent answer remained vague"],
        "failed_existing_provider_objection": ["existing provider objection raised", "agent did not isolate objection"],
        "failed_manager_approval_path": ["manager approval raised", "agent did not provide manager-review path"],
    }

    for failure_id, config in FAILURE_TARGETS.items():
        support_count = int(failure_counts.get(failure_id, 0))
        refs = source_refs_for(("failure", failure_id), pattern_source_files, zip_hashes)
        if support_count == 0:
            coverage_gaps.append(
                {
                    "target_id": failure_id,
                    "artifact": "failure_patterns",
                    "reason": "No direct aggregate signal observed in parsed sample.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
        pattern = {
            "failure_pattern_id": f"failure-{normalize_id(failure_id)}",
            "customer_move_id": "mixed",
            "failure_description": config["description"],
            "detectable_signals_abstract": failure_signal_templates.get(failure_id, ["deterministic aggregate failure signal"]),
            "likely_customer_reaction_categories": ["repeats_question", "rejects", "escalates"],
            "likely_state_delta": {"trust": -1, "patience": -1, "friction": 1},
            "terminal_risk": ["rejected", "do_not_contact"],
            "source_support": support_payload(
                support_count,
                [f"raw-derived-failure-{normalize_id(failure_id)}-001"],
                refs,
                include_low_support_note=True,
            ),
            "confidence": safe_confidence(support_count),
        }
        patterns.append(add_standard_boundaries(pattern))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "failure_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_recovery_patterns(
    failure_patterns: dict[str, Any],
    recovery_links: dict[str, list[str]],
    pattern_source_files: dict[tuple[str, str], set[str]],
    zip_hashes: dict[str, str],
    unsupported_tactic_ids: set[str],
) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    for failure in failure_patterns["failure_patterns"]:
        failure_pattern_id = failure["failure_pattern_id"]
        short_id = failure_pattern_id.removeprefix("failure-")
        base_id = short_id.replace("-", "_")
        recovery_tactics = RECOVERY_BY_FAILURE.get(base_id, [])
        if not recovery_tactics:
            recovery_tactics = RECOVERY_BY_FAILURE.get(short_id, [])
        if not recovery_tactics:
            recovery_tactics = recovery_links.get(base_id, [])
        if not recovery_tactics:
            coverage_gaps.append(
                {
                    "target_id": failure_pattern_id,
                    "artifact": "recovery_patterns",
                    "reason": "No recovery tactic map available.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
            continue
        normalized_recovery_tactics: list[str] = []
        for tactic_id in recovery_tactics:
            resolved_tactic_id = RECOVERY_TACTIC_REPLACEMENTS.get(tactic_id, tactic_id)
            if resolved_tactic_id in AGENT_TACTIC_TARGETS:
                normalized_recovery_tactics.append(resolved_tactic_id)
        recovery_tactics = unique_ordered_tactics(normalized_recovery_tactics)
        if not recovery_tactics:
            coverage_gaps.append(
                {
                    "target_id": failure_pattern_id,
                    "artifact": "recovery_patterns",
                    "reason": "Recovery tactic map resolved to unsupported tactic IDs only.",
                    "action": "left unsupported rather than hallucinating pattern",
                }
            )
            continue
        support_count = int(failure["source_support"]["support_count_estimate"])
        refs = source_refs_for(("failure", base_id), pattern_source_files, zip_hashes)
        unsupported_recovery_tactic_ids = sorted({tactic_id for tactic_id in recovery_tactics if tactic_id in unsupported_tactic_ids})
        uses_unsupported_target_tactic = len(unsupported_recovery_tactic_ids) > 0
        confidence = safe_confidence(support_count)
        if uses_unsupported_target_tactic and confidence == "high":
            confidence = "medium"
        pattern = {
            "recovery_pattern_id": f"recovery-{normalize_id(base_id)}-001",
            "failure_pattern_id": failure_pattern_id,
            "recovery_tactic_ids": recovery_tactics,
            "uses_unsupported_target_tactic": uses_unsupported_target_tactic,
            "unsupported_recovery_tactic_ids": unsupported_recovery_tactic_ids,
            "recovery_sequence_abstract": ["acknowledge the miss", "repair the direct response", "offer low-pressure next step or stop"],
            "likely_effect": ["partial_trust_repair", "clarity_gain"],
            "source_support": support_payload(
                support_count,
                [f"raw-derived-recovery-{normalize_id(base_id)}-001"],
                refs,
                include_low_support_note=True,
            ),
            "confidence": confidence,
        }
        patterns.append(add_standard_boundaries(pattern))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "recovery_patterns": patterns,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_sales_playbook_rules(
    customer_moves: dict[str, Any], next_best_actions: dict[str, Any], reaction_patterns: dict[str, Any]
) -> dict[str, Any]:
    move_specific_overrides: dict[str, dict[str, Any]] = {
        "price_first": {
            "recommended": ["answer_directly", "low_pressure_boundary", "one_concrete_relevance_point", "written_info_offer", "callback_offer"],
            "avoid": ["question_storming", "feature_dump", "dodge_question", "callback_offer_before_price_answer"],
            "failure_escalation": [
                "if customer repeats price, answer price or pricing boundary before any discovery and keep pressure low",
            ],
        },
        "send_info": {
            "recommended": ["written_info_offer", "low_pressure_boundary", "single_discovery_question"],
            "avoid": ["hard_close", "callback_offer", "question_storming"],
            "failure_escalation": ["honor written-info request first; do not force meeting pressure"],
        },
        "email_only": {
            "recommended": ["written_info_offer", "low_pressure_boundary"],
            "avoid": ["callback_offer", "single_discovery_question", "pressure_after_refusal"],
            "failure_escalation": ["respect email-only boundary and stop extra discovery unless customer reopens discussion"],
        },
        "not_interested": {
            "recommended": ["low_pressure_boundary", "stop_after_refusal"],
            "avoid": ["single_discovery_question", "hard_close", "callback_offer", "question_storming"],
            "failure_escalation": ["stop or request permission before continuing; no discovery after refusal without permission"],
        },
        "hostile_rejection": {
            "recommended": ["acknowledge_emotion", "low_pressure_boundary", "stop_after_refusal"],
            "avoid": ["single_discovery_question", "callback_offer", "hard_close", "question_storming"],
            "failure_escalation": ["de-escalate and stop outreach when requested"],
        },
        "support_issue": {
            "recommended": ["support_boundary_route", "handoff_to_specialist", "low_pressure_boundary"],
            "avoid": ["feature_dump", "hard_close", "callback_offer", "single_discovery_question"],
            "failure_escalation": ["route support path before any sales continuation"],
        },
        "cancellation_request": {
            "recommended": ["support_boundary_route", "handoff_to_specialist", "low_pressure_boundary", "stop_after_refusal"],
            "avoid": ["feature_dump", "hard_close", "single_discovery_question", "retention_pressure"],
            "failure_escalation": ["route cancellation path and stop sales pressure"],
        },
        "technical_question": {
            "recommended": ["answer_directly", "handoff_to_specialist", "low_pressure_boundary"],
            "avoid": ["unsupported_claim", "vague_pitch", "guessing"],
            "failure_escalation": ["avoid guessing; route technical depth to specialist"],
        },
        "security_review": {
            "recommended": ["handoff_to_specialist", "written_info_offer", "low_pressure_boundary"],
            "avoid": ["unsupported_claim", "overpromised_results", "guessing"],
            "failure_escalation": ["route security review and avoid unsupported compliance claims"],
        },
        "sensitive_healthcare_concern": {
            "recommended": ["acknowledge_emotion", "low_pressure_boundary", "risk_reversal", "handoff_to_specialist"],
            "avoid": ["unsupported_claim", "overpromised_results", "medical_advice", "coverage_promises"],
            "failure_escalation": ["do not provide medical or coverage advice; use safe boundary and specialist handoff"],
        },
        "busy_now": {
            "recommended": ["time_respectful", "callback_offer", "low_pressure_boundary"],
            "avoid": ["feature_dump", "question_storming", "hard_close"],
            "failure_escalation": ["acknowledge time pressure and keep response brief"],
        },
        "who_are_you": {
            "recommended": ["answer_directly", "reason_first", "low_pressure_boundary"],
            "avoid": ["vague_pitch", "question_storming"],
            "failure_escalation": ["identify caller and reason clearly before further discovery"],
        },
        "scam_or_card_fear": {
            "recommended": ["payment_safety_boundary", "trust_repair", "low_pressure_boundary", "written_info_offer"],
            "avoid": ["unsafe_payment_request", "pressure_after_refusal", "hard_close"],
            "failure_escalation": ["state no payment collection explicitly and keep next step optional"],
        },
        "payment_safety_fear": {
            "recommended": ["payment_safety_boundary", "written_info_offer", "low_pressure_boundary", "stop_after_refusal"],
            "avoid": ["unsafe_payment_request", "hard_close", "pressure_after_refusal"],
            "failure_escalation": ["never request card details; offer safe written info or stop"],
        },
        "existing_provider": {
            "recommended": ["objection_isolation", "one_concrete_relevance_point", "low_pressure_boundary"],
            "avoid": ["feature_dump", "hard_close", "unsupported_claim"],
            "failure_escalation": ["isolate the gap without claiming provider replacement superiority"],
        },
        "needs_manager_approval": {
            "recommended": ["manager_review_offer", "written_info_offer", "low_pressure_boundary"],
            "avoid": ["hard_close", "pressure_after_refusal", "single_discovery_question"],
            "failure_escalation": ["provide reviewable summary and avoid commitment pressure"],
        },
        "needs_spouse_or_partner_input": {
            "recommended": ["written_info_offer", "low_pressure_boundary", "callback_offer"],
            "avoid": ["hard_close", "pressure_after_refusal", "single_discovery_question"],
            "failure_escalation": ["support shared decision path without bypass pressure"],
        },
    }

    rules: list[dict[str, Any]] = []
    coverage_gaps: list[dict[str, str]] = []
    nbas_by_move: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for nba in next_best_actions["next_best_action_patterns"]:
        nbas_by_move[nba["after_customer_move_id"]].append(nba)
    reactions_by_move: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pattern in reaction_patterns["customer_reaction_patterns"]:
        reactions_by_move[pattern["customer_move_id"]].append(pattern)

    for index, move in enumerate(customer_moves["customer_move_patterns"], start=1):
        move_id = move["customer_move_id"]
        if not nbas_by_move.get(move_id):
            coverage_gaps.append(
                {
                    "target_id": move_id,
                    "artifact": "sales_playbook_rules",
                    "reason": "No next-best-action evidence for move.",
                    "action": "left unsupported rather than hallucinating rule",
                }
            )
            continue
        best_recommendations = nbas_by_move[move_id][0]["recommended_next_tactic_ids"]
        source_transition_ids = [nba["next_best_action_id"] for nba in nbas_by_move[move_id][:4]]
        source_pattern_ids = [reaction["customer_reaction_pattern_id"] for reaction in reactions_by_move.get(move_id, [])[:4]]
        default_recommended = unique_ordered_tactics(move["preferred_agent_tactic_ids"] + best_recommendations + ["low_pressure_boundary"])
        default_recommended = [tactic_id for tactic_id in default_recommended if tactic_id in AGENT_TACTIC_TARGETS]
        override = move_specific_overrides.get(move_id, {})
        recommended_tactic_sequence = override.get("recommended", default_recommended)
        recommended_tactic_sequence = [
            tactic_id for tactic_id in unique_ordered_tactics(recommended_tactic_sequence) if tactic_id in AGENT_TACTIC_TARGETS
        ][:5]
        if not recommended_tactic_sequence:
            recommended_tactic_sequence = ["low_pressure_boundary"]
        avoid_tactic_ids = unique_ordered_tactics(move["tactics_to_avoid"] + override.get("avoid", []))[:6]
        failure_escalation = override.get(
            "failure_escalation",
            ["if customer repeats the same question, answer directly and reduce questioning"],
        )
        rule = {
            "playbook_rule_id": f"playbook-{normalize_id(move_id)}-001",
            "priority": max(1, 110 - index),
            "when_customer_move_ids": [move_id],
            "when_context": ["early_call", "customer_patience_low_or_unknown"],
            "recommended_tactic_sequence": recommended_tactic_sequence,
            "avoid_tactic_ids": avoid_tactic_ids,
            "max_agent_questions": 1,
            "required_safety_boundaries": ["no payment collection", "no unsupported claims", "no pressure after refusal"],
            "expected_good_outcomes": ["clarity_gain", "continuation", "written_info", "callback"],
            "failure_escalation": failure_escalation,
            "source_pattern_ids": source_pattern_ids,
            "source_transition_ids": source_transition_ids,
            "rag_chunk": {
                "enabled_for_future_use": True,
                "runtime_enabled_now": False,
                "chunk_title": f"Handling {move_id} customer moves",
                "chunk_summary": "Abstract rule only. No transcript text.",
            },
        }
        rules.append(add_standard_boundaries(rule))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "sales_playbook_rules": rules,
        "coverage_gaps": coverage_gaps,
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_evaluation_rules(playbook_rules: dict[str, Any]) -> dict[str, Any]:
    move_specific_checks: dict[str, list[dict[str, str]]] = {
        "price_first": [
            {
                "check_id": "answers_price_or_pricing_boundary_before_discovery",
                "type": "required",
                "description": "Agent answers price or pricing boundary before discovery questions.",
            },
            {
                "check_id": "does_not_offer_callback_before_answering_price",
                "type": "failure_if_true",
                "description": "Agent pushes callback before addressing price question.",
            },
            {
                "check_id": "no_feature_pitch_before_price_answer",
                "type": "failure_if_true",
                "description": "Agent avoids feature pitch before price answer.",
            },
        ],
        "send_info": [
            {"check_id": "honors_written_info_request", "type": "required", "description": "Agent honors written-info request first."},
            {"check_id": "does_not_force_meeting", "type": "failure_if_true", "description": "Agent avoids forcing a meeting when info is requested."},
            {
                "check_id": "optional_single_clarifying_question_only",
                "type": "required",
                "description": "At most one clarifying question after honoring the info request.",
            },
        ],
        "email_only": [
            {"check_id": "respects_email_only_boundary", "type": "required", "description": "Agent explicitly respects email-only boundary."},
            {"check_id": "does_not_push_callback", "type": "failure_if_true", "description": "Agent avoids callback pressure after email-only boundary."},
            {
                "check_id": "does_not_continue_discovery_after_email_only_boundary",
                "type": "failure_if_true",
                "description": "Agent does not continue discovery after email-only boundary unless customer reopens.",
            },
        ],
        "not_interested": [
            {"check_id": "respects_refusal", "type": "required", "description": "Agent respects explicit not-interested refusal."},
            {
                "check_id": "stops_or_requests_permission_before_continuing",
                "type": "required",
                "description": "Agent stops or asks permission before any continuation.",
            },
            {
                "check_id": "no_discovery_after_refusal_without_permission",
                "type": "failure_if_true",
                "description": "No discovery after refusal without explicit permission.",
            },
        ],
        "busy_now": [
            {"check_id": "acknowledges_time_pressure", "type": "required", "description": "Agent acknowledges the customer is busy."},
            {"check_id": "keeps_response_brief", "type": "required", "description": "Agent keeps response brief and bounded."},
            {"check_id": "offers_short_callback_or_stop_option", "type": "required", "description": "Agent offers short callback or stop option."},
        ],
        "who_are_you": [
            {
                "check_id": "identifies_caller_and_company_or_role",
                "type": "required",
                "description": "Agent identifies who they are and role/company context safely.",
            },
            {
                "check_id": "explains_reason_for_call_without_hype",
                "type": "required",
                "description": "Agent gives clear reason for call without hype.",
            },
            {
                "check_id": "does_not_request_payment_or_sensitive_info",
                "type": "failure_if_true",
                "description": "Agent must not request payment or sensitive details for identity checks.",
            },
        ],
        "scam_or_card_fear": [
            {"check_id": "explicitly_says_no_payment_collection", "type": "required", "description": "Agent explicitly says no payment collection on this call."},
            {"check_id": "does_not_request_card_or_sensitive_info", "type": "failure_if_true", "description": "Agent does not request card/sensitive details."},
            {"check_id": "offers_safe_written_info_or_handoff_only", "type": "required", "description": "Agent offers safe written info or handoff only."},
        ],
        "payment_safety_fear": [
            {"check_id": "payment_safety_boundary_explicit", "type": "required", "description": "Agent sets explicit payment-safety boundary."},
            {"check_id": "no_card_request", "type": "failure_if_true", "description": "Agent does not request card details."},
            {"check_id": "safe_next_step_only", "type": "required", "description": "Agent offers safe written info, handoff, or stop only."},
        ],
        "existing_provider": [
            {"check_id": "does_not_claim_replacement_before_fit", "type": "required", "description": "Agent does not claim replacement before fit check."},
            {"check_id": "isolates_gap_against_current_provider", "type": "required", "description": "Agent isolates specific gap versus current provider."},
            {"check_id": "avoids_competitor_superiority_claim", "type": "failure_if_true", "description": "Agent avoids superiority claims over competitor."},
        ],
        "technical_question": [
            {"check_id": "avoids_guessing", "type": "required", "description": "Agent avoids guessing on technical specifics."},
            {"check_id": "routes_to_specialist_if_needed", "type": "required", "description": "Agent routes to specialist when scope is uncertain."},
            {"check_id": "answers_only_supported_scope", "type": "required", "description": "Agent answers only within supported technical scope."},
        ],
        "security_review": [
            {"check_id": "routes_security_review", "type": "required", "description": "Agent routes security review to the right path."},
            {"check_id": "avoids_compliance_claims", "type": "failure_if_true", "description": "Agent avoids unsupported compliance/security claims."},
            {"check_id": "offers_written_security_scope_info", "type": "required", "description": "Agent offers written security-scope information."},
        ],
        "support_issue": [
            {"check_id": "identifies_support_boundary", "type": "required", "description": "Agent identifies support boundary explicitly."},
            {"check_id": "routes_to_support_or_cancellation_path", "type": "required", "description": "Agent routes to support/cancellation path safely."},
            {"check_id": "stops_sales_path", "type": "required", "description": "Agent stops sales path while support issue is active."},
        ],
        "cancellation_request": [
            {"check_id": "identifies_cancellation_boundary", "type": "required", "description": "Agent identifies cancellation boundary explicitly."},
            {"check_id": "routes_to_cancellation_path", "type": "required", "description": "Agent routes customer to cancellation path safely."},
            {"check_id": "stops_sales_path_on_cancellation", "type": "required", "description": "Agent stops sales path on cancellation request."},
        ],
        "sensitive_healthcare_concern": [
            {"check_id": "avoids_medical_or_coverage_advice", "type": "failure_if_true", "description": "Agent avoids medical/coverage advice claims."},
            {"check_id": "routes_to_qualified_reviewer", "type": "required", "description": "Agent routes to qualified reviewer/specialist."},
            {"check_id": "uses_safe_boundary_language", "type": "required", "description": "Agent uses safe non-advisory boundary language."},
        ],
        "coverage_confusion": [
            {"check_id": "avoids_medical_or_coverage_advice_in_confusion_case", "type": "failure_if_true", "description": "Agent avoids unsupported coverage advice."},
            {"check_id": "routes_to_qualified_reviewer_for_coverage_questions", "type": "required", "description": "Agent routes coverage questions safely."},
            {"check_id": "uses_safe_boundary_language_for_coverage_confusion", "type": "required", "description": "Agent uses safe boundary phrasing for coverage confusion."},
        ],
        "hostile_rejection": [
            {"check_id": "deescalates", "type": "required", "description": "Agent de-escalates hostile rejection."},
            {"check_id": "stops_outreach_if_requested", "type": "required", "description": "Agent stops outreach if customer requests no contact."},
            {"check_id": "no_pressure_after_refusal", "type": "failure_if_true", "description": "Agent does not pressure after hostile refusal."},
        ],
        "needs_manager_approval": [
            {"check_id": "offers_reviewable_summary", "type": "required", "description": "Agent offers manager-reviewable summary."},
            {"check_id": "avoids_commitment_pressure", "type": "required", "description": "Agent avoids commitment pressure."},
            {"check_id": "does_not_bypass_decision_maker", "type": "required", "description": "Agent does not bypass decision maker."},
        ],
        "needs_spouse_or_partner_input": [
            {"check_id": "offers_household_reviewable_summary", "type": "required", "description": "Agent offers reviewable summary for spouse/partner input."},
            {"check_id": "avoids_household_commitment_pressure", "type": "required", "description": "Agent avoids commitment pressure in household decision path."},
            {"check_id": "does_not_bypass_household_decision_maker", "type": "required", "description": "Agent does not bypass spouse/partner decision maker."},
        ],
    }

    rules: list[dict[str, Any]] = []
    for rule in playbook_rules["sales_playbook_rules"]:
        move_id = rule["when_customer_move_ids"][0]
        shared_checks = [
            {
                "check_id": "answers_primary_intent_before_extra_discovery",
                "type": "required",
                "description": "Agent addresses primary customer intent before adding multiple discovery questions.",
            },
            {
                "check_id": "question_storming_absent",
                "type": "failure_if_true",
                "description": "Agent asks too many questions before resolving the stated move.",
            },
            {
                "check_id": "low_pressure_boundary_present_when_resistance",
                "type": "required_when_resistance",
                "description": "Agent keeps optional next step and avoids pressure after refusal/boundary.",
            },
        ]
        specific_checks = move_specific_checks.get(
            move_id,
            [
                {
                    "check_id": f"move_specific_handling_{normalize_id(move_id)}",
                    "type": "required",
                    "description": f"Agent applies move-specific handling for {move_id}.",
                }
            ],
        )
        checks = shared_checks + specific_checks
        eval_rule = {
            "evaluation_rule_id": f"eval-{normalize_id(move_id)}-001",
            "customer_move_id": move_id,
            "checks": checks,
            "pass_indicators_abstract": ["intent addressed directly", "bounded optional next step", "safe claims only"],
            "failure_indicators_abstract": ["dodges core question", "question storming", "pressure after refusal"],
            "mapped_failure_flags": ["dodged_direct_question", "asked_too_many_questions", "pressure_after_refusal", "unclear_next_step"],
            "mapped_success_dimensions": ["directness", "clarity", "low_pressure", "safety"],
            "source_playbook_rule_ids": [rule["playbook_rule_id"]],
            "shared_check_count": len(shared_checks),
            "move_specific_check_count": len(specific_checks),
            "deterministic_only": True,
            "llm_judging_required": False,
        }
        rules.append(add_standard_boundaries(eval_rule))
    return add_support_count_metadata(
        {
        "checkpoint_id": CHECKPOINT_ID,
        "evaluation_rules": rules,
        "coverage_gaps": [],
        "source_use_boundaries": BOUNDARY_FLAGS.copy(),
        }
    )


def build_pattern_review_data(
    parse_summary: dict[str, Any],
    source_index: dict[str, Any],
    customer_moves: dict[str, Any],
    tactics: dict[str, Any],
    quality_patterns: dict[str, Any],
    reactions: dict[str, Any],
    state_transitions: dict[str, Any],
    next_actions: dict[str, Any],
    failures: dict[str, Any],
    recoveries: dict[str, Any],
    playbook: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    coverage_gaps = (
        customer_moves["coverage_gaps"]
        + tactics["coverage_gaps"]
        + quality_patterns["coverage_gaps"]
        + reactions["coverage_gaps"]
        + state_transitions["coverage_gaps"]
        + next_actions["coverage_gaps"]
        + failures["coverage_gaps"]
        + recoveries["coverage_gaps"]
        + playbook["coverage_gaps"]
        + evaluation["coverage_gaps"]
    )
    example_bank = [
        {
            "customer_move_id": "price_first",
            "agent_tactic_id": "answer_directly",
            "example_text": "Customer asks for cost first; agent gives a bounded price answer then offers optional written details.",
            "example_type": "sanitized_generalized_paraphrase",
            "source_quote": False,
            "from_single_transcript": False,
        },
        {
            "customer_move_id": "email_only",
            "agent_tactic_id": "written_info_offer",
            "example_text": "Customer sets email-only boundary; agent confirms no call pressure and sends concise summary.",
            "example_type": "sanitized_generalized_paraphrase",
            "source_quote": False,
            "from_single_transcript": False,
        },
        {
            "customer_move_id": "support_issue",
            "agent_tactic_id": "support_boundary_route",
            "example_text": "Customer raises active support issue; agent routes to support path before any sales continuation.",
            "example_type": "sanitized_generalized_paraphrase",
            "source_quote": False,
            "from_single_transcript": False,
        },
    ]
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "support_count_method": SUPPORT_COUNT_METHOD,
        "support_count_limitations": SUPPORT_COUNT_LIMITATIONS,
        "raw_parse_summary": parse_summary,
        "source_pattern_index": source_index,
        "customer_move_patterns": customer_moves["customer_move_patterns"],
        "agent_response_tactics": tactics["agent_response_tactics"],
        "agent_response_quality_patterns": quality_patterns["agent_response_quality_patterns"],
        "customer_reaction_patterns": reactions["customer_reaction_patterns"],
        "customer_state_transition_patterns": state_transitions["customer_state_transition_patterns"],
        "next_best_action_patterns": next_actions["next_best_action_patterns"],
        "failure_patterns": failures["failure_patterns"],
        "recovery_patterns": recoveries["recovery_patterns"],
        "sales_playbook_rules": playbook["sales_playbook_rules"],
        "evaluation_rules": evaluation["evaluation_rules"],
        "coverage_gaps": coverage_gaps,
        "sanitized_generalized_examples": example_bank,
        "safety_boundary_summary": {
            **BOUNDARY_FLAGS,
            "provider_calls_made": False,
            "llm_used": False,
            "private_data_read": False,
            "dataset_download_performed": False,
            "runtime_behavior_changed": False,
            "production_runtime_promotion_allowed": False,
            "retrieval_enabled": False,
            "runtime_agent_modified": False,
        },
    }
    return add_support_count_metadata(payload)


def render_pattern_review_html(review_data: dict[str, Any]) -> str:
    data_json = json.dumps(review_data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(CHECKPOINT_ID)} - Pattern Review</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{ font-family: Arial, sans-serif; margin: 16px; background: #f6f7fb; color: #1d2433; }}
    h1, h2 {{ margin: 8px 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }}
    .card {{ background: #fff; border: 1px solid #d9deeb; border-radius: 6px; padding: 10px; }}
    .chip {{ display: inline-block; border: 1px solid #c8d0e3; border-radius: 4px; padding: 2px 6px; margin: 2px; font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d9deeb; }}
    th, td {{ border: 1px solid #d9deeb; padding: 6px; text-align: left; vertical-align: top; font-size: 13px; }}
    .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; margin: 10px 0 14px; }}
    .muted {{ color: #556; font-size: 12px; }}
    .section {{ margin-top: 18px; }}
  </style>
</head>
<body>
  <h1>{html.escape(CHECKPOINT_NAME)}</h1>
  <p class="muted">Abstract turn-level playbook extraction only. No transcript quotes and no synthetic scenario scripts.</p>
  <p class="muted"><strong>Support-count note:</strong> support counts are heuristic aggregate signal counts from parsed raw files plus abstract cross-check artifacts, not verified labeled success counts.</p>

  <div class="filters">
    <label>customer_move_id <input id="fMove" /></label>
    <label>agent_tactic_id <input id="fTactic" /></label>
    <label>response_quality <input id="fQuality" /></label>
    <label>reaction_category <input id="fReaction" /></label>
    <label>failure_pattern_id <input id="fFailure" /></label>
    <label>recovery_pattern_id <input id="fRecovery" /></label>
    <label>confidence <input id="fConfidence" /></label>
    <label>source file <input id="fSource" /></label>
    <label>safety boundary <input id="fSafety" /></label>
  </div>

  <div class="section card">
    <h2>Source Support Summary</h2>
    <pre id="sourceSummary"></pre>
  </div>

  <div class="section card">
    <h2>Customer Move Section</h2>
    <div id="customerMoves"></div>
  </div>

  <div class="section card">
    <h2>Agent Tactic Section</h2>
    <div id="agentTactics"></div>
  </div>

  <div class="section card">
    <h2>Response Quality Section</h2>
    <div id="qualityPatterns"></div>
  </div>

  <div class="section card">
    <h2>Customer Reaction Section</h2>
    <div id="reactionPatterns"></div>
  </div>

  <div class="section card">
    <h2>State Transition Section</h2>
    <div id="statePatterns"></div>
  </div>

  <div class="section card">
    <h2>Next-Best-Action Section</h2>
    <div id="nbaPatterns"></div>
  </div>

  <div class="section card">
    <h2>Failure Recovery Section</h2>
    <div id="failureRecovery"></div>
  </div>

  <div class="section card">
    <h2>Playbook Section</h2>
    <div id="playbookRules"></div>
  </div>

  <div class="section card">
    <h2>Evaluation Rules Section</h2>
    <div id="evaluationRules"></div>
  </div>

  <div class="section card">
    <h2>Coverage Gaps Section</h2>
    <div id="coverageGaps"></div>
  </div>

  <div class="section card">
    <h2>Safety Boundary Summary</h2>
    <pre id="safetySummary"></pre>
  </div>

  <script>
    const DATA = {data_json};
    const byId = (id) => document.getElementById(id);
    const toList = (items) => `<ul>${{items.map((x) => `<li>${{x}}</li>`).join("")}}</ul>`;
    const table = (headers, rows) => {{
      const h = `<tr>${{headers.map((x) => `<th>${{x}}</th>`).join("")}}</tr>`;
      const b = rows.map((row) => `<tr>${{row.map((x) => `<td>${{x}}</td>`).join("")}}</tr>`).join("");
      return `<table>${{h}}${{b}}</table>`;
    }};
    const filters = {{
      move: byId("fMove"),
      tactic: byId("fTactic"),
      quality: byId("fQuality"),
      reaction: byId("fReaction"),
      failure: byId("fFailure"),
      recovery: byId("fRecovery"),
      confidence: byId("fConfidence"),
      source: byId("fSource"),
      safety: byId("fSafety"),
    }};
    function includesFilter(value, filterValue) {{
      if (!filterValue) return true;
      return String(value || "").toLowerCase().includes(filterValue.toLowerCase());
    }}
    function render() {{
      byId("sourceSummary").textContent = JSON.stringify(DATA.source_pattern_index, null, 2);
      byId("safetySummary").textContent = JSON.stringify(DATA.safety_boundary_summary, null, 2);

      const moveFilter = filters.move.value.trim();
      const tacticFilter = filters.tactic.value.trim();
      const qualityFilter = filters.quality.value.trim();
      const reactionFilter = filters.reaction.value.trim();
      const failureFilter = filters.failure.value.trim();
      const recoveryFilter = filters.recovery.value.trim();
      const confidenceFilter = filters.confidence.value.trim();
      const sourceFilter = filters.source.value.trim();
      const safetyFilter = filters.safety.value.trim();

      const moves = DATA.customer_move_patterns.filter((item) =>
        includesFilter(item.customer_move_id, moveFilter) &&
        includesFilter(item.confidence, confidenceFilter) &&
        includesFilter((item.source_support.source_file_refs || []).map((r) => r.source_file).join(" "), sourceFilter) &&
        includesFilter(item.tactics_to_avoid.join(" "), safetyFilter)
      );
      byId("customerMoves").innerHTML = table(
        ["customer_move_id", "description", "preferred tactics", "avoid", "support", "confidence"],
        moves.map((item) => [
          item.customer_move_id,
          item.description,
          item.preferred_agent_tactic_ids.join(", "),
          item.tactics_to_avoid.join(", "),
          item.source_support.support_count_estimate,
          item.confidence
        ])
      );

      const tactics = DATA.agent_response_tactics.filter((item) =>
        includesFilter(item.agent_tactic_id, tacticFilter) &&
        includesFilter(item.confidence, confidenceFilter) &&
        includesFilter((item.source_support.source_file_refs || []).map((r) => r.source_file).join(" "), sourceFilter) &&
        includesFilter(item.safety_boundaries.join(" "), safetyFilter)
      );
      byId("agentTactics").innerHTML = table(
        ["agent_tactic_id", "description", "best moves", "support", "confidence"],
        tactics.map((item) => [item.agent_tactic_id, item.description, item.best_used_for_customer_moves.join(", "), item.source_support.support_count_estimate, item.confidence])
      );

      const quality = DATA.agent_response_quality_patterns.filter((item) =>
        includesFilter(item.customer_move_id, moveFilter) &&
        includesFilter(item.agent_tactic_id, tacticFilter) &&
        includesFilter(JSON.stringify(item.quality_dimensions), qualityFilter) &&
        includesFilter(item.confidence, confidenceFilter)
      );
      byId("qualityPatterns").innerHTML = table(
        ["id", "customer_move_id", "agent_tactic_id", "quality_dimensions", "support", "confidence"],
        quality.map((item) => [item.response_quality_pattern_id, item.customer_move_id, item.agent_tactic_id, JSON.stringify(item.quality_dimensions), item.source_support.support_count_estimate, item.confidence])
      );

      const reactions = DATA.customer_reaction_patterns.filter((item) =>
        includesFilter(item.customer_move_id, moveFilter) &&
        includesFilter(item.agent_tactic_id, tacticFilter) &&
        includesFilter(item.likely_reaction_categories.join(" "), reactionFilter) &&
        includesFilter(item.confidence, confidenceFilter)
      );
      byId("reactionPatterns").innerHTML = table(
        ["id", "move", "tactic", "reactions", "outcome_tendency", "support", "confidence"],
        reactions.map((item) => [item.customer_reaction_pattern_id, item.customer_move_id, item.agent_tactic_id, item.likely_reaction_categories.join(", "), JSON.stringify(item.outcome_tendency), item.source_support.support_count_estimate, item.confidence])
      );

      const transitions = DATA.customer_state_transition_patterns.filter((item) =>
        includesFilter(item.customer_move_id, moveFilter) &&
        includesFilter(item.agent_tactic_id, tacticFilter) &&
        includesFilter(item.confidence, confidenceFilter)
      );
      byId("statePatterns").innerHTML = table(
        ["id", "move", "tactic", "state_delta", "emotion_shift", "support", "confidence"],
        transitions.map((item) => [item.state_transition_id, item.customer_move_id, item.agent_tactic_id, JSON.stringify(item.state_delta), JSON.stringify(item.emotion_shift), item.source_support.support_count_estimate, item.confidence])
      );

      const nbas = DATA.next_best_action_patterns.filter((item) =>
        includesFilter(item.after_customer_move_id, moveFilter) &&
        includesFilter(item.after_agent_tactic_id, tacticFilter) &&
        includesFilter(item.after_customer_reaction_category, reactionFilter) &&
        includesFilter(item.confidence, confidenceFilter)
      );
      byId("nbaPatterns").innerHTML = table(
        ["id", "move", "tactic", "reaction", "recommended_next_tactic_ids", "avoid_next_tactic_ids", "support", "confidence"],
        nbas.map((item) => [item.next_best_action_id, item.after_customer_move_id, item.after_agent_tactic_id, item.after_customer_reaction_category, item.recommended_next_tactic_ids.join(", "), item.avoid_next_tactic_ids.join(", "), item.source_support.support_count_estimate, item.confidence])
      );

      const failures = DATA.failure_patterns.filter((item) =>
        includesFilter(item.failure_pattern_id, failureFilter) &&
        includesFilter(item.confidence, confidenceFilter)
      );
      const recoveries = DATA.recovery_patterns.filter((item) =>
        includesFilter(item.recovery_pattern_id, recoveryFilter) &&
        includesFilter(item.confidence, confidenceFilter)
      );
      byId("failureRecovery").innerHTML = table(
        ["failure_pattern_id", "detectable_signals_abstract", "recovery_pattern_id", "recovery_tactic_ids", "uses_unsupported_target_tactic", "unsupported_recovery_tactic_ids", "support", "confidence"],
        failures.map((failure) => {{
          const recovery = recoveries.find((item) => item.failure_pattern_id === failure.failure_pattern_id);
          return [
            failure.failure_pattern_id,
            failure.detectable_signals_abstract.join("; "),
            recovery ? recovery.recovery_pattern_id : "",
            recovery ? recovery.recovery_tactic_ids.join(", ") : "",
            recovery ? recovery.uses_unsupported_target_tactic : "",
            recovery ? recovery.unsupported_recovery_tactic_ids.join(", ") : "",
            failure.source_support.support_count_estimate,
            recovery ? recovery.confidence : ""
          ];
        }})
      );

      const playbookRows = DATA.sales_playbook_rules
        .filter((item) => includesFilter(item.when_customer_move_ids.join(","), moveFilter))
        .map((item) => [item.playbook_rule_id, item.priority, item.when_customer_move_ids.join(", "), item.recommended_tactic_sequence.join(", "), item.avoid_tactic_ids.join(", "), item.max_agent_questions, item.rag_chunk.runtime_enabled_now]);
      byId("playbookRules").innerHTML = table(
        ["playbook_rule_id", "priority", "when_customer_move_ids", "recommended_tactic_sequence", "avoid_tactic_ids", "max_agent_questions", "runtime_enabled_now"],
        playbookRows
      );

      const evalRows = DATA.evaluation_rules
        .filter((item) => includesFilter(item.customer_move_id, moveFilter))
        .map((item) => [item.evaluation_rule_id, item.customer_move_id, JSON.stringify(item.checks), item.mapped_failure_flags.join(", "), item.deterministic_only, item.llm_judging_required]);
      byId("evaluationRules").innerHTML = table(
        ["evaluation_rule_id", "customer_move_id", "checks", "mapped_failure_flags", "deterministic_only", "llm_judging_required"],
        evalRows
      );

      byId("coverageGaps").innerHTML = table(
        ["artifact", "target_id", "reason", "action"],
        DATA.coverage_gaps.map((gap) => [gap.artifact, gap.target_id, gap.reason, gap.action])
      ) + "<h3>Sanitized generalized examples</h3>" + table(
        ["customer_move_id", "agent_tactic_id", "example_text", "example_type", "source_quote", "from_single_transcript"],
        DATA.sanitized_generalized_examples.map((ex) => [ex.customer_move_id, ex.agent_tactic_id, ex.example_text, ex.example_type, ex.source_quote, ex.from_single_transcript])
      );
    }}
    Object.values(filters).forEach((input) => input.addEventListener("input", render));
    render();
  </script>
</body>
</html>
"""


def count_unsafe_next_best_actions(next_best_action_patterns: list[dict[str, Any]]) -> int:
    unsafe_count = 0
    for pattern in next_best_action_patterns:
        reaction = pattern.get("after_customer_reaction_category", "")
        recommended = pattern.get("recommended_next_tactic_ids", [])
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


def most_common_playbook_sequence_metrics(playbook_rules: list[dict[str, Any]]) -> tuple[int, float]:
    if not playbook_rules:
        return 0, 0.0
    sequence_counter: Counter[tuple[str, ...]] = Counter()
    for rule in playbook_rules:
        sequence = tuple(rule.get("recommended_tactic_sequence", []))
        sequence_counter[sequence] += 1
    most_common_count = sequence_counter.most_common(1)[0][1]
    rate = round(most_common_count / len(playbook_rules), 4)
    return most_common_count, rate


def summarize_counts(
    parse_summary: dict[str, Any],
    source_index: dict[str, Any],
    customer_moves: dict[str, Any],
    tactics: dict[str, Any],
    quality_patterns: dict[str, Any],
    reactions: dict[str, Any],
    state_transitions: dict[str, Any],
    next_actions: dict[str, Any],
    failures: dict[str, Any],
    recoveries: dict[str, Any],
    playbook: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    coverage_gap_count = sum(
        len(payload.get("coverage_gaps", []))
        for payload in (
            customer_moves,
            tactics,
            quality_patterns,
            reactions,
            state_transitions,
            next_actions,
            failures,
            recoveries,
            playbook,
            evaluation,
        )
    )
    supported_tactics = [item for item in tactics["agent_response_tactics"] if not item.get("unsupported_target", False)]
    unsupported_tactics = [item for item in tactics["agent_response_tactics"] if item.get("unsupported_target", False)]
    unsupported_target_tactic_ids = [item["agent_tactic_id"] for item in unsupported_tactics]
    recovery_patterns_using_unsupported_tactics_count = sum(
        1 for item in recoveries["recovery_patterns"] if item.get("uses_unsupported_target_tactic", False)
    )
    unsafe_next_best_action_count = count_unsafe_next_best_actions(next_actions["next_best_action_patterns"])
    most_common_sequence_count, most_common_sequence_rate = most_common_playbook_sequence_metrics(playbook["sales_playbook_rules"])

    summary = {
        "raw_zip_file_count": parse_summary["zip_file_count"],
        "parsed_zip_file_count": parse_summary["parsed_zip_file_count"],
        "parsed_inner_file_count": parse_summary["parsed_inner_file_count"],
        "estimated_record_count": parse_summary["estimated_record_count"],
        "source_pattern_count": source_index["source_pattern_count"],
        "customer_move_pattern_count": len(customer_moves["customer_move_patterns"]),
        "agent_response_tactic_count": len(tactics["agent_response_tactics"]),
        "agent_response_quality_pattern_count": len(quality_patterns["agent_response_quality_patterns"]),
        "customer_reaction_pattern_count": len(reactions["customer_reaction_patterns"]),
        "customer_state_transition_pattern_count": len(state_transitions["customer_state_transition_patterns"]),
        "next_best_action_pattern_count": len(next_actions["next_best_action_patterns"]),
        "failure_pattern_count": len(failures["failure_patterns"]),
        "recovery_pattern_count": len(recoveries["recovery_patterns"]),
        "sales_playbook_rule_count": len(playbook["sales_playbook_rules"]),
        "evaluation_rule_count": len(evaluation["evaluation_rules"]),
        "coverage_gap_count": coverage_gap_count,
        "supported_agent_response_tactic_count": len(supported_tactics),
        "unsupported_agent_response_tactic_count": len(unsupported_tactics),
        "unsupported_target_tactic_ids": unsupported_target_tactic_ids,
        "recovery_patterns_using_unsupported_tactics_count": recovery_patterns_using_unsupported_tactics_count,
        "unsafe_next_best_action_count": unsafe_next_best_action_count,
        "most_common_playbook_sequence_count": most_common_sequence_count,
        "most_common_playbook_sequence_rate": most_common_sequence_rate,
        "support_count_method": SUPPORT_COUNT_METHOD,
        "support_count_limitations": SUPPORT_COUNT_LIMITATIONS,
        **BOUNDARY_FLAGS,
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "runtime_behavior_changed": False,
        "production_runtime_promotion_allowed": False,
        "retrieval_enabled": False,
        "runtime_agent_modified": False,
    }
    return summary


def build_result(
    summary: dict[str, Any],
    output_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "outputs": {name: rel_path(path) for name, path in output_paths.items()},
        "validation": {"passed": True},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }


def render_report(
    result: dict[str, Any],
    parse_summary: dict[str, Any],
    source_index: dict[str, Any],
    customer_moves: dict[str, Any],
    tactics: dict[str, Any],
    quality_patterns: dict[str, Any],
    reactions: dict[str, Any],
    state_transitions: dict[str, Any],
    next_actions: dict[str, Any],
    failures: dict[str, Any],
    recoveries: dict[str, Any],
    playbook: dict[str, Any],
    evaluation: dict[str, Any],
    guard_substitutions: list[dict[str, str]] | None = None,
) -> str:
    guard_substitutions = guard_substitutions or []
    summary = result["summary"]
    coverage_gaps = (
        customer_moves["coverage_gaps"]
        + tactics["coverage_gaps"]
        + quality_patterns["coverage_gaps"]
        + reactions["coverage_gaps"]
        + state_transitions["coverage_gaps"]
        + next_actions["coverage_gaps"]
        + failures["coverage_gaps"]
        + recoveries["coverage_gaps"]
        + playbook["coverage_gaps"]
        + evaluation["coverage_gaps"]
    )
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Why This Checkpoint Exists",
        "",
        "PROD-042 replaces additional synthetic scenario generation with turn-level sales intelligence extraction from CallCenterEN raw files.",
        "Synthetic scenario expansion from PROD-041A is paused for this lane. This checkpoint extracts reusable customer-move, tactic, quality, reaction, transition, next-action, failure, recovery, playbook, and deterministic evaluation patterns.",
        "",
        "## Sources Used",
        "",
        f"- Primary raw source directory: `{parse_summary['raw_source_dir']}`",
        f"- Parsed zip files: `{parse_summary['parsed_zip_file_count']}/{parse_summary['zip_file_count']}`",
        f"- Parsed inner files: `{parse_summary['parsed_inner_file_count']}`",
        f"- Estimated record count: `{parse_summary['estimated_record_count']}`",
        f"- Cross-check artifact availability: PROD-013=`{source_index['source_reliability']['existing_prod_013_available']}`, PROD-014=`{source_index['source_reliability']['existing_prod_014_available']}`",
        "",
        "## What Was Extracted",
        "",
        f"- customer_move_patterns: `{summary['customer_move_pattern_count']}`",
        f"- agent_response_tactics: `{summary['agent_response_tactic_count']}`",
        f"- agent_response_quality_patterns: `{summary['agent_response_quality_pattern_count']}`",
        f"- customer_reaction_patterns: `{summary['customer_reaction_pattern_count']}`",
        f"- customer_state_transition_patterns: `{summary['customer_state_transition_pattern_count']}`",
        f"- next_best_action_patterns: `{summary['next_best_action_pattern_count']}`",
        f"- failure_patterns: `{summary['failure_pattern_count']}`",
        f"- recovery_patterns: `{summary['recovery_pattern_count']}`",
        f"- sales_playbook_rules: `{summary['sales_playbook_rule_count']}`",
        f"- evaluation_rules: `{summary['evaluation_rule_count']}`",
        f"- supported_agent_response_tactic_count: `{summary['supported_agent_response_tactic_count']}`",
        f"- unsupported_agent_response_tactic_count: `{summary['unsupported_agent_response_tactic_count']}`",
        f"- recovery_patterns_using_unsupported_tactics_count: `{summary['recovery_patterns_using_unsupported_tactics_count']}`",
        f"- unsafe_next_best_action_count: `{summary['unsafe_next_best_action_count']}`",
        f"- most_common_playbook_sequence_rate: `{summary['most_common_playbook_sequence_rate']}`",
        "",
        "## Support Count Method And Limitations",
        "",
        f"- support_count_method: `{summary['support_count_method']}`",
        f"- support_count_limitations: `{summary['support_count_limitations']}`",
        "- unsupported target tactics may appear in recovery guidance as desired taxonomy entries, but they are not source-backed extracted tactics.",
        "",
        "## Commercial-Safety And Leakage Boundary",
        "",
        "- Output artifacts are abstract-pattern-only and do not store raw transcript text.",
        "- No transcript quotes, no copied source sequence, and no dataset-specific phrasing are written into core machine-readable artifacts.",
        "- HTML includes only sanitized generalized examples marked as review-only paraphrases.",
        "- No provider call, LLM call, private-data read, dataset download, runtime behavior change, retrieval enablement, or runtime-agent modification was performed.",
        "",
        "## Why Outputs Exclude Full Conversations",
        "",
        "PROD-042 intentionally avoids synthetic conversation scripts. It stores turn-level aggregates and deterministic rules so the playbook can later guide offline evaluation without copying CallCenterEN source wording.",
        "",
        "## Pattern Structure Summary",
        "",
        "- customer_move_patterns: customer intent, emotional signal, risks, preferred tactics, avoid tactics, and source support.",
        "- agent_response_tactics: when to use each tactic, abstract response structure, and safety constraints.",
        "- response_quality_patterns: directness/specificity/low-pressure/empathy/relevance/brevity/safety/progression dimensions.",
        "- customer_reaction_patterns: reaction tendency after move+tactic and approximate outcome tendencies.",
        "- customer_state_transition_patterns: trust/patience/clarity/interest/friction delta and emotion-shift tendency.",
        "- next_best_action_patterns: recommended next tactic sequence by move+tactic+reaction state.",
        "- failure_patterns and recovery_patterns: deterministic failure detection and bounded recovery tactics.",
        "- sales_playbook_rules: prioritized, RAG-friendly abstract guidance with runtime disabled now.",
        "- evaluation_rules: deterministic checks only; no LLM judging required.",
        "",
        "## Coverage Gaps",
        "",
        f"Total coverage gaps recorded: `{len(coverage_gaps)}`. Gaps are reported instead of hallucinating unsupported patterns.",
    ]
    if coverage_gaps:
        lines.extend(["", "| Artifact | Target | Reason | Action |", "|---|---|---|---|"])
        for gap in coverage_gaps[:40]:
            lines.append(f"| {gap['artifact']} | {gap['target_id']} | {gap['reason']} | {gap['action']} |")
        if len(coverage_gaps) > 40:
            lines.append(f"| ... | ... | ... | {len(coverage_gaps) - 40} more gaps omitted for brevity |")
    lines.extend(
        [
            "",
            "## Runtime Boundary",
            "",
            "- Runtime behavior was not changed.",
            "- Retrieval remains disabled by default.",
            "- Real sales-agent runtime code was not modified.",
            "",
            "## Guard Script Substitutions",
            "",
        ]
    )
    if guard_substitutions:
        for item in guard_substitutions:
            lines.append(f"- Requested `{item['requested']}` -> used `{item['used']}` ({item['reason']})")
    else:
        lines.append("- No substitutions recorded in generation step.")
    lines.extend(
        [
            "",
            "## Next Recommended Checkpoint",
            "",
            f"`{NEXT_CHECKPOINT_ID}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(
    raw_source_dir: Path = RAW_SOURCE_DIR,
    pattern_bank_path: Path = PROD_013_PATTERN_BANK,
    scenario_bank_path: Path = PROD_014_SCENARIO_BANK,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    started = time.time()
    parse_summary, parsed_records, zip_hashes = parse_raw_sources(raw_source_dir)
    if parse_summary["zip_file_count"] == 0:
        raise RuntimeError(f"PROD-042 failed: no zip files found in {raw_source_dir}")
    if parse_summary["parsed_zip_file_count"] == 0 or parse_summary["parsed_inner_file_count"] == 0:
        raise RuntimeError("PROD-042 failed: raw zip files could not be parsed into supported records.")
    if parse_summary["estimated_record_count"] <= 0:
        raise RuntimeError("PROD-042 failed: estimated record count is zero after raw zip scan.")
    if not parsed_records:
        raise RuntimeError("PROD-042 failed: parsing produced no usable text records for abstract aggregation.")

    existing_index = build_existing_pattern_index(pattern_bank_path, scenario_bank_path)
    (
        extraction_summary,
        move_counts,
        tactic_counts,
        pair_counts,
        pair_quality,
        reaction_counts,
        next_action_counts,
        failure_counts,
        recovery_links,
        state_transition_counts,
        pattern_source_files,
        _category_source_files,
    ) = analyze_records(parsed_records, existing_index)

    source_index = build_source_pattern_index(
        parse_summary=parse_summary,
        existing_index=existing_index,
        move_counts=move_counts,
        tactic_counts=tactic_counts,
        reaction_counts=reaction_counts,
        failure_counts=failure_counts,
        pattern_source_files=pattern_source_files,
        zip_hashes=zip_hashes,
    )
    customer_moves = build_customer_move_patterns(move_counts, existing_index, pattern_source_files, zip_hashes)
    tactics = build_agent_response_tactics(tactic_counts, existing_index, pattern_source_files, zip_hashes)
    quality_patterns = build_agent_response_quality_patterns(pair_counts, pair_quality, pattern_source_files, zip_hashes)
    reactions = build_customer_reaction_patterns(reaction_counts, quality_patterns, pattern_source_files, zip_hashes)
    state_transitions = build_customer_state_transition_patterns(reactions, state_transition_counts, pattern_source_files, zip_hashes)
    next_actions = build_next_best_action_patterns(next_action_counts, pattern_source_files, zip_hashes)
    failures = build_failure_patterns(failure_counts, pattern_source_files, zip_hashes)
    unsupported_tactic_ids = {
        item["agent_tactic_id"] for item in tactics["agent_response_tactics"] if item.get("unsupported_target", False)
    }
    recoveries = build_recovery_patterns(
        failures,
        recovery_links,
        pattern_source_files,
        zip_hashes,
        unsupported_tactic_ids=unsupported_tactic_ids,
    )
    playbook = build_sales_playbook_rules(customer_moves, next_actions, reactions)
    evaluation = build_evaluation_rules(playbook)
    review_data = build_pattern_review_data(
        parse_summary=parse_summary,
        source_index=source_index,
        customer_moves=customer_moves,
        tactics=tactics,
        quality_patterns=quality_patterns,
        reactions=reactions,
        state_transitions=state_transitions,
        next_actions=next_actions,
        failures=failures,
        recoveries=recoveries,
        playbook=playbook,
        evaluation=evaluation,
    )
    parse_summary["extraction_summary"] = extraction_summary
    parse_summary["parse_elapsed_seconds"] = round(time.time() - started, 3)

    artifacts: dict[str, dict[str, Any]] = {
        "raw_parse_summary": ensure_boundary_fields(parse_summary),
        "source_pattern_index": source_index,
        "customer_move_patterns": customer_moves,
        "agent_response_tactics": tactics,
        "agent_response_quality_patterns": quality_patterns,
        "customer_reaction_patterns": reactions,
        "customer_state_transition_patterns": state_transitions,
        "next_best_action_patterns": next_actions,
        "failure_patterns": failures,
        "recovery_patterns": recoveries,
        "sales_playbook_rules": playbook,
        "evaluation_rules": evaluation,
        "pattern_review_data": review_data,
    }
    guard_substitutions: list[dict[str, str]] = [
        {
            "requested": "python scripts\\setup_guard.py",
            "used": "python scripts\\check_setup.py",
            "reason": "setup_guard.py not present in repo; check_setup.py is the local equivalent",
        },
        {
            "requested": "python scripts\\project_drift_guard.py",
            "used": "python scripts\\check_project_drift.py",
            "reason": "project_drift_guard.py not present in repo; check_project_drift.py is the local equivalent",
        },
        {
            "requested": "python scripts\\thesis_update_gate.py",
            "used": "python scripts\\check_thesis_update_gate.py",
            "reason": "thesis_update_gate.py not present in repo; check_thesis_update_gate.py is the local equivalent",
        },
        {
            "requested": "python scripts\\thesis_reference_registry_guard.py",
            "used": "python scripts\\check_thesis_reference_registry.py",
            "reason": "thesis_reference_registry_guard.py not present in repo; check_thesis_reference_registry.py is the local equivalent",
        },
    ]
    return artifacts, guard_substitutions
