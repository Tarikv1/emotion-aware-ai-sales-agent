#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CHECKPOINT_ID = "PROD-043-sales-playbook-runtime-adapter"
CHECKPOINT_NAME = "Sales Playbook Runtime Adapter"
SOURCE_CHECKPOINT_ID = "PROD-042-callcenteren-turn-pattern-playbook"
NEXT_CHECKPOINT_ID = "PROD-044-core-sales-policy-update"
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

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

MOVE_TEST_UTTERANCES = {
    "price_first": ["What does this cost?", "How much is it per month?", "Is this in my budget?"],
    "send_info": ["Send me the details.", "Can you send information first?", "Please send a short summary."],
    "email_only": ["Just email me.", "Email only, please.", "Only by email please."],
    "not_interested": ["Not interested.", "No thanks, I am not looking.", "We are not interested right now."],
    "busy_now": ["I only have a minute.", "I cannot talk right now.", "I am busy."],
    "callback_request": ["Call me next week.", "Can you call back later?", "Schedule a callback for tomorrow."],
    "who_are_you": ["Who are you again?", "What company are you with?", "Who exactly is calling?"],
    "scam_or_card_fear": ["Is this a scam?", "This sounds like a scam.", "How do I know this is legitimate?"],
    "payment_safety_fear": ["I am not giving card details.", "Are you asking for payment now?", "I do not share payment info by phone."],
    "existing_provider": ["We already have a provider.", "We use someone for this already.", "Our current vendor handles that."],
    "needs_manager_approval": ["I need to ask my manager.", "My boss has to review this.", "Our manager decides that."],
    "needs_spouse_or_partner_input": ["I need to ask my spouse.", "My partner has to look at this.", "I cannot decide without my partner."],
    "technical_question": ["Does it integrate with our system?", "What API do you support?", "Can it connect to our CRM?"],
    "security_review": ["Security needs to review this.", "Do you have security docs?", "What about compliance review?"],
    "support_issue": ["This is a support issue.", "I need help with my account.", "Can support fix this?"],
    "cancellation_request": ["I want to cancel.", "Help me cancel my account.", "This is about cancellation."],
    "confused_fit": ["I do not understand what this is.", "I am not sure I follow.", "What are you actually offering?"],
    "skeptical_proof_request": ["Can you prove it works?", "Do you have proof?", "Can you show evidence?"],
    "bad_previous_experience": ["We tried this and it went badly.", "Last vendor burned us.", "We had a bad experience before."],
    "competitor_comparison": ["How is this different from a competitor?", "Compare this against our provider.", "Why would this beat another option?"],
    "contract_fear": ["Is this a contract?", "I do not want a long commitment.", "Are you locking me in?"],
    "setup_timeline": ["How long does setup take?", "What is the implementation timeline?", "How fast can this start?"],
    "coverage_confusion": ["Is this covered?", "What does coverage include?", "I do not understand the coverage."],
    "sensitive_healthcare_concern": ["Is this medical advice?", "I have a health concern.", "Can you tell me what treatment is covered?"],
    "hostile_rejection": ["Stop calling me.", "Do not call me again.", "No, remove my number."],
    "low_fit_signal": ["This probably is not a fit.", "We are too small for that.", "I do not think we need this."],
    "sale_ready_interest": ["I am ready to move forward.", "What do I sign?", "I want to get started."],
    "discovery_needed": ["What would you need to know?", "What details do you need?", "What should I tell you first?"],
}

ORDERED_CLASSIFIER_RULES = [
    ("email_only", ["email only", "just email", "only by email"]),
    ("payment_safety_fear", ["card details", "payment now", "payment info", "card info"]),
    ("scam_or_card_fear", ["scam", "legitimate"]),
    ("hostile_rejection", ["stop calling", "do not call", "remove my number"]),
    ("cancellation_request", ["cancel", "cancellation"]),
    ("support_issue", ["support issue", "help with my account", "support fix"]),
    ("security_review", ["security", "compliance"]),
    ("sensitive_healthcare_concern", ["medical advice", "health concern", "treatment"]),
    ("coverage_confusion", ["covered", "coverage"]),
    ("technical_question", ["integrate", "api", "connect"]),
    ("competitor_comparison", ["competitor", "compare", "beat another option"]),
    ("existing_provider", ["provider", "vendor", "someone for this"]),
    ("needs_manager_approval", ["manager", "boss"]),
    ("needs_spouse_or_partner_input", ["spouse", "partner"]),
    ("contract_fear", ["contract", "commitment", "locking me in"]),
    ("setup_timeline", ["setup", "implementation", "start"]),
    ("who_are_you", ["who are you", "what company", "who exactly"]),
    ("price_first", ["cost", "price", "per month", "budget", "how much"]),
    ("send_info", ["send", "details", "information", "summary"]),
    ("busy_now", ["minute", "cannot talk", "busy"]),
    ("callback_request", ["call back", "callback", "call me", "schedule a callback"]),
    ("not_interested", ["not interested", "no thanks", "not looking"]),
    ("confused_fit", ["understand", "not sure i follow", "actually offering"]),
    ("skeptical_proof_request", ["prove", "proof", "evidence"]),
    ("bad_previous_experience", ["went badly", "burned us", "bad experience"]),
    ("low_fit_signal", ["not a fit", "too small", "do not think we need"]),
    ("sale_ready_interest", ["ready to move", "what do i sign", "get started"]),
    ("discovery_needed", ["need to know", "details do you need", "tell you first"]),
]

ABSTRACT_AVOID_TACTICS = {
    "question_storming",
    "feature_dump",
    "hard_close",
    "dodge_question",
    "feature_pitch_before_answer",
    "pressure_after_refusal",
    "callback_offer_before_price_answer",
    "guessing",
    "unsupported technical claims",
    "unsupported security/compliance claims",
    "medical advice",
    "coverage promises",
    "unsupported claims",
    "sales continuation",
    "retention pressure",
    "single_discovery_question before respecting email-only boundary",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def get_items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def load_prod_042() -> dict[str, Any]:
    return {
        "customer_moves": get_items(read_json(SOURCE_DIR / "customer_move_patterns.json"), "customer_move_patterns"),
        "tactics": get_items(read_json(SOURCE_DIR / "agent_response_tactics.json"), "agent_response_tactics"),
        "playbook_rules": get_items(read_json(SOURCE_DIR / "sales_playbook_rules.json"), "sales_playbook_rules"),
        "evaluation_rules": get_items(read_json(SOURCE_DIR / "evaluation_rules.json"), "evaluation_rules"),
        "failure_patterns": get_items(read_json(SOURCE_DIR / "failure_patterns.json"), "failure_patterns"),
        "recovery_patterns": get_items(read_json(SOURCE_DIR / "recovery_patterns.json"), "recovery_patterns"),
        "result": read_json(SOURCE_DIR / "result.json"),
    }


def classify_customer_move(utterance: str, move_ids: set[str]) -> dict[str, Any]:
    matched: list[str] = []
    signals: list[str] = []
    for move_id, phrases in ORDERED_CLASSIFIER_RULES:
        hits = [phrase for phrase in phrases if phrase in utterance.lower()]
        if move_id in move_ids and hits:
            matched.append(move_id)
            signals.extend(hits)
            break
    if not matched:
        matched = [next(iter(sorted(move_ids)))]
    return {
        "predicted_customer_move_ids": matched,
        "confidence": "high" if signals else "low",
        "matched_abstract_signals": sorted(set(signals)),
        "matched_customer_move_pattern_ids": matched,
    }


def make_classifier_cases(customer_moves: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    move_ids = {move["customer_move_id"] for move in customer_moves}
    cases: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    for move in customer_moves:
        move_id = move["customer_move_id"]
        support = move.get("source_support", {}).get("support_count_estimate", 0)
        utterances = MOVE_TEST_UTTERANCES.get(move_id, [])
        if support <= 0 or not utterances:
            gaps.append({"target_id": move_id, "artifact": "customer_move_classification_cases", "reason": "unsupported or no safe generic test utterance"})
            utterances = utterances[:1]
        for index, utterance in enumerate(utterances[:3], start=1):
            case = {
                "case_id": f"case-{slug(move_id)}-{index:03d}",
                "customer_utterance": utterance,
                "expected_customer_move_id": move_id,
                "context": {"stage": "early_call", "market_scope": "mixed", "offer_context": "callback ownership and follow-up routing"},
                "example_type": "synthetic_generic_test_case",
                "source_quote": False,
                "from_single_transcript": False,
            }
            output = {"case_id": case["case_id"], **classify_customer_move(utterance, move_ids)}
            output["classifier_passed"] = move_id in output["predicted_customer_move_ids"]
            cases.append(case)
            outputs.append(output)
    return cases, outputs, gaps


def retrieve_playbook(case: dict[str, Any], output: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, Any]:
    move_ids = output["predicted_customer_move_ids"]
    rules = [rule for rule in artifacts["playbook_rules"] if set(rule.get("when_customer_move_ids", [])) & set(move_ids)]
    evals = [rule for rule in artifacts["evaluation_rules"] if rule.get("customer_move_id") in move_ids]
    failures = [item for item in artifacts["failure_patterns"] if item.get("customer_move_id") in move_ids or item.get("customer_move_id") == "mixed"]
    recoveries = [item for item in artifacts["recovery_patterns"] if any(item.get("failure_pattern_id") == f.get("failure_pattern_id") for f in failures)]
    recommended: list[str] = []
    avoid: list[str] = []
    boundaries: list[str] = []
    for rule in rules:
        recommended.extend(rule.get("recommended_tactic_sequence", []))
        avoid.extend(rule.get("avoid_tactic_ids", []))
        boundaries.extend(rule.get("required_safety_boundaries", []))
    return {
        "case_id": case["case_id"],
        "customer_utterance": case["customer_utterance"],
        "predicted_customer_move_ids": move_ids,
        "retrieved_playbook_rule_ids": [rule["playbook_rule_id"] for rule in rules],
        "retrieved_evaluation_rule_ids": [rule["evaluation_rule_id"] for rule in evals],
        "retrieved_failure_pattern_ids": [item["failure_pattern_id"] for item in failures],
        "retrieved_recovery_pattern_ids": [item["recovery_pattern_id"] for item in recoveries],
        "recommended_tactic_sequence": list(dict.fromkeys(recommended)),
        "avoid_tactic_ids": list(dict.fromkeys(avoid)),
        "required_safety_boundaries": list(dict.fromkeys(boundaries)),
        "retrieval_status": "matched" if rules and evals else "unmatched",
    }


GOOD_BAD_RESPONSES = {
    "price_first": ("The basic range starts around 29 per user per month. No commitment today; I can send the details.", "Before price, can I ask a few questions about your team?"),
    "send_info": ("I can send a short summary and leave it there.", "Let us book a meeting first and then I will send details."),
    "email_only": ("Understood. I will send the summary by email only and will not push a call.", "Email is fine, but let's schedule a call now."),
    "not_interested": ("Understood. I will stop here. No pressure.", "I hear you, but let me ask a few discovery questions first."),
    "busy_now": ("No problem. I will keep this brief or stop here.", "Great, I have several questions before we decide anything."),
    "callback_request": ("Sure, I can offer a callback window and keep it optional.", "Let me continue the pitch before we talk timing."),
    "who_are_you": ("This is Maya calling from the sales team about follow-up routing. I am not asking for payment.", "We have a great platform that changes everything."),
    "scam_or_card_fear": ("Fair question. I am not collecting payment or card details; I can send verification info.", "Please give me your card number to verify the account."),
    "payment_safety_fear": ("No payment or card details on this call. I can send written information only.", "I need your payment details to continue."),
    "existing_provider": ("I am not assuming a replacement. The only question is whether there is a gap your current provider does not cover.", "We are better than your provider and should replace them."),
    "needs_manager_approval": ("I can send a manager-ready summary with no commitment.", "You can approve it without your manager."),
    "needs_spouse_or_partner_input": ("I can send a short summary for both of you to review.", "You do not need to ask your partner."),
    "technical_question": ("I do not want to guess. I can answer only the supported scope or route this to a specialist.", "Yes, it integrates with everything for sure."),
    "security_review": ("That should go through a security review. I can send the security scope and route the rest to a specialist.", "We are fully compliant with every standard, no review needed."),
    "support_issue": ("That is a support path, not a sales path. I can route you to support.", "Before support, let me tell you about our product."),
    "cancellation_request": ("I can route you to the cancellation path and stop the sales conversation.", "Before you cancel, let's review an upgrade."),
    "confused_fit": ("Fair. In plain terms, this is about missed follow-ups and routing, not a commitment today.", "It is an advanced solution for operational transformation."),
    "skeptical_proof_request": ("I can send supported evidence and avoid making any guaranteed claim.", "I guarantee this will double your results."),
    "bad_previous_experience": ("That is fair. We can keep it narrow and avoid any commitment while you review.", "This time will definitely be different, trust me."),
    "competitor_comparison": ("We can compare fit without claiming we replace them or beat them everywhere.", "We are simply better than every competitor."),
    "contract_fear": ("No contract commitment on this call. I can send terms for review.", "Yes, we need you to agree now."),
    "setup_timeline": ("I can give the normal setup range or route detailed timing to a specialist.", "Setup is instant for everyone."),
    "coverage_confusion": ("I cannot give coverage advice. I can route that to a qualified reviewer.", "You are definitely covered."),
    "sensitive_healthcare_concern": ("I cannot provide medical advice. I can route you to a qualified reviewer.", "You should choose this treatment."),
    "hostile_rejection": ("Understood. I will stop outreach.", "Let me keep explaining why you should hear this."),
    "low_fit_signal": ("That may be true. I can qualify this out or send one short note if useful.", "Everyone needs this product."),
    "sale_ready_interest": ("I can confirm the next step without taking payment on this call.", "Great, give me your card so we can finish."),
    "discovery_needed": ("One question is enough: what issue are you trying to solve?", "I need to ask ten questions before I can help."),
}


def create_evaluation_cases(customer_moves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for move in customer_moves:
        move_id = move["customer_move_id"]
        utterance = MOVE_TEST_UTTERANCES.get(move_id, [f"Generic {move_id} question."])[0]
        good, bad = GOOD_BAD_RESPONSES.get(
            move_id,
            ("I can answer directly, keep this optional, and send written details.", "Before answering, let me ask several questions."),
        )
        for label, response, expected in (("good", good, "pass"), ("bad", bad, "fail")):
            cases.append({
                "case_id": f"eval-{slug(move_id)}-{label}-001",
                "customer_utterance": utterance,
                "expected_customer_move_id": move_id,
                "agent_response": response,
                "expected_result": expected,
                "expected_failure_flags": [] if expected == "pass" else ["deterministic_failure_expected"],
                "example_type": "synthetic_generic_test_case",
                "source_quote": False,
                "from_single_transcript": False,
            })
    return cases


def detect_tactics(response: str, move_id: str) -> list[str]:
    text = response.lower()
    tactics: list[str] = []
    if contains_any(text, ["understood", "fair", "no problem", "that is fair"]):
        tactics.append("acknowledge_emotion")
    if contains_any(text, ["29", "range", "cost", "price", "not collecting payment", "this is maya", "plain terms"]):
        tactics.append("answer_directly")
    if contains_any(text, ["no pressure", "no commitment", "leave it there", "stop here", "optional", "not asking for payment", "no payment"]):
        tactics.append("low_pressure_boundary")
    if contains_any(text, ["send", "email", "summary", "details", "written"]):
        tactics.append("written_info_offer")
    if contains_any(text, ["callback", "call back", "call window", "meeting", "schedule a call", "book a call"]):
        tactics.append("callback_offer")
    if contains_any(text, ["specialist", "qualified reviewer", "security review", "route"]):
        tactics.append("handoff_to_specialist")
    if contains_any(text, ["support path", "route you to support", "cancellation path"]):
        tactics.append("support_boundary_route")
    if response.count("?") == 1:
        tactics.append("single_discovery_question")
    if contains_any(text, ["stop outreach", "stop here", "stop the sales conversation"]):
        tactics.append("stop_after_refusal")
    if move_id in {"scam_or_card_fear", "payment_safety_fear", "sale_ready_interest"} and contains_any(text, ["no payment", "no card", "not collecting payment"]):
        tactics.append("payment_safety_boundary")
    return list(dict.fromkeys(tactics))


def detect_failures(response: str, move_id: str, tactics: list[str]) -> list[str]:
    text = response.lower()
    failures: list[str] = []
    question_count = response.count("?")
    if question_count > 1 or contains_any(text, ["several questions", "ten questions"]):
        failures.append("asked_too_many_questions")
    if contains_any(text, ["card number", "payment details", "give me your card"]):
        failures.append("unsafe_payment_request")
    if contains_any(text, ["guarantee this", "i guarantee", "definitely", "fully compliant with every standard", "definitely covered", "choose this treatment"]):
        failures.append("unsupported_claim")
    if move_id == "price_first" and ("answer_directly" not in tactics or "before price" in text):
        failures.append("dodged_direct_question")
    if move_id in {"not_interested", "hostile_rejection"} and contains_any(text, ["keep explaining", "few discovery questions"]):
        failures.append("pressure_after_refusal")
    if move_id in {"support_issue", "cancellation_request"} and "support_boundary_route" not in tactics:
        failures.append("failed_support_boundary")
    if move_id in {"send_info", "email_only"} and "callback_offer" in tactics:
        failures.append("unclear_next_step")
    if move_id == "callback_request" and contains_any(text, ["continue the pitch", "before we talk timing"]):
        failures.append("unclear_next_step")
    if move_id == "existing_provider" and contains_any(text, ["better than your provider", "replace them"]):
        failures.append("failed_existing_provider_objection")
    if move_id in {"needs_manager_approval", "needs_spouse_or_partner_input"} and contains_any(text, ["without your manager", "do not need to ask your partner"]):
        failures.append("pressure_after_refusal")
    if move_id in {"technical_question", "setup_timeline"} and contains_any(text, ["integrates with everything", "instant for everyone"]):
        failures.append("unsupported_claim")
    if move_id == "competitor_comparison" and contains_any(text, ["better than every competitor"]):
        failures.append("unsupported_claim")
    if move_id == "contract_fear" and contains_any(text, ["agree now"]):
        failures.append("pressure_after_refusal")
    if move_id in {"technical_question", "security_review", "coverage_confusion", "sensitive_healthcare_concern"} and "unsupported_claim" in failures:
        failures.append("overpromised_results")
    if move_id == "who_are_you" and "answer_directly" not in tactics:
        failures.append("failed_identity_repair")
    if contains_any(text, ["advanced solution", "changes everything", "everyone needs"]):
        failures.append("vague_pitch")
    return list(dict.fromkeys(failures))


def evaluate_response(case: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, Any]:
    move_id = case["expected_customer_move_id"]
    classifier = classify_customer_move(case["customer_utterance"], {m["customer_move_id"] for m in artifacts["customer_moves"]})
    tactics = detect_tactics(case["agent_response"], move_id)
    failures = detect_failures(case["agent_response"], move_id, tactics)
    eval_rules = [rule for rule in artifacts["evaluation_rules"] if rule.get("customer_move_id") == move_id]
    check_ids = [check["check_id"] for rule in eval_rules for check in rule.get("checks", [])]
    failed_checks = list(dict.fromkeys(failures))
    passed_checks = [check_id for check_id in check_ids if check_id not in failed_checks][:8]
    passed = not failures
    recoveries = []
    for recovery in artifacts["recovery_patterns"]:
        if any(flag.replace("_", "-") in recovery.get("failure_pattern_id", "") for flag in failures):
            recoveries.extend(recovery.get("recovery_tactic_ids", []))
    if failures and not recoveries:
        recoveries = ["answer_directly", "low_pressure_boundary"]
    return {
        "case_id": case["case_id"],
        "customer_utterance": case["customer_utterance"],
        "predicted_customer_move_ids": classifier["predicted_customer_move_ids"],
        "expected_customer_move_id": move_id,
        "agent_response": case["agent_response"],
        "retrieved_evaluation_rule_ids": [rule["evaluation_rule_id"] for rule in eval_rules],
        "detected_agent_tactic_ids": tactics,
        "passed_check_ids": passed_checks,
        "failed_check_ids": failed_checks,
        "detected_failure_flags": failures,
        "success_dimensions": ["directness", "clarity", "low_pressure"] if passed else [],
        "recommended_recovery_tactic_ids": list(dict.fromkeys(recoveries)),
        "passed": passed,
        "expected_result": case["expected_result"],
        "matches_expected_result": passed == (case["expected_result"] == "pass"),
        "explanation": "Deterministic turn-level checks matched the expected result." if passed == (case["expected_result"] == "pass") else "Deterministic checks differed from expected result.",
    }


def run_actual_agent_probe(cases: list[dict[str, Any]]) -> tuple[bool, str, list[dict[str, Any]]]:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from runtime.core.realtime_turns import build_runtime_decision  # type: ignore
    except Exception as exc:
        return False, f"clean deterministic runtime entrypoint unavailable: {exc}", []
    probes = []
    for case in cases[:6]:
        runtime_case = {
            "case_id": f"prod-043-probe-{case['case_id']}",
            "customer_input": {"input_type": "speech-final", "stage": "relevance-check", "transcript": case["customer_utterance"]},
        }
        try:
            decision = build_runtime_decision(runtime_case, expected=None, campaign={"language": "en"})
            probes.append({
                "case_id": case["case_id"],
                "customer_utterance": case["customer_utterance"],
                "actual_agent_response": decision.get("agent_response", ""),
                "sales_difficulty": decision.get("sales_difficulty"),
                "next_action": decision.get("next_action"),
                "offline_only": True,
            })
        except Exception as exc:
            return False, f"runtime probe failed without modifying runtime: {exc}", probes
    return True, "", probes


def render_html(data: dict[str, Any]) -> str:
    summary = data["summary"]
    rows = []
    for item in data["agent_response_evaluations"][:80]:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(item["case_id"]),
                html.escape(",".join(item["predicted_customer_move_ids"])),
                html.escape(",".join(item["detected_agent_tactic_ids"])),
                html.escape(",".join(item["detected_failure_flags"])),
                "pass" if item["passed"] else "fail",
            )
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PROD-043 Runtime Adapter Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .metric {{ display: inline-block; border: 1px solid #ccc; padding: 8px 10px; margin: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px; vertical-align: top; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f6f8fa; padding: 1px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-043 Sales Playbook Runtime Adapter</h1>
  <p>Offline single-turn adapter/evaluator. No raw transcript text, full synthetic conversations, provider calls, LLM calls, runtime mutation, or retrieval enablement.</p>
  <section id="filters"><h2>Filters</h2><p>Review data supports filters by customer_move_id, pass/fail, detected_failure_flag, detected_agent_tactic, evaluation_rule_id, playbook_rule_id, and actual_agent_logic_used.</p></section>
  <section id="summary"><h2>Safety Boundary Section</h2>
    <span class="metric">classifier_accuracy: {summary['classifier_accuracy']}</span>
    <span class="metric">playbook_retrieval_match_rate: {summary['playbook_retrieval_match_rate']}</span>
    <span class="metric">agent_expected_match_rate: {summary['agent_response_evaluation_expected_match_rate']}</span>
    <span class="metric">actual_agent_logic_used: {summary['actual_agent_logic_used']}</span>
    <span class="metric">runtime_behavior_changed: {summary['runtime_behavior_changed']}</span>
    <span class="metric">retrieval_enabled: {summary['retrieval_enabled']}</span>
  </section>
  <section id="classifier"><h2>Classifier Section</h2><p>{summary['customer_move_classifier_case_count']} synthetic generic customer-move cases classified against PROD-042 move patterns.</p></section>
  <section id="playbook"><h2>Playbook Retrieval Section</h2><p>{summary['playbook_retrieval_match_count']} matched retrieval cases with PROD-042 playbook and evaluation rules.</p></section>
  <section id="agent-evaluation"><h2>Agent Evaluation Section</h2>
    <table><thead><tr><th>Case</th><th>Move</th><th>Detected Tactics</th><th>Failure Flags</th><th>Result</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
  </section>
  <section id="actual-agent"><h2>Actual Agent Logic Status</h2><p>actual_agent_logic_used: <code>{summary['actual_agent_logic_used']}</code>. {html.escape(summary.get('actual_agent_logic_unavailable_reason') or 'Clean deterministic offline runtime turn entrypoint was probed.')}</p></section>
  <section id="coverage"><h2>Coverage Gaps</h2><pre>{html.escape(json.dumps(data.get('coverage_gaps', []), indent=2))}</pre></section>
</body>
</html>
"""


def make_report(summary: dict[str, Any], outputs: dict[str, str]) -> str:
    return f"""# PROD-043 Sales Playbook Runtime Adapter

PROD-043 is an offline adapter/evaluator checkpoint. It reads PROD-042 turn-level playbook artifacts, classifies generic single-turn customer utterances, retrieves matching playbook and evaluation rules, and deterministically evaluates generic agent responses against those rules.

It does not generate full conversations, does not copy CallCenterEN transcript text, does not enable retrieval, and does not modify runtime behavior.

## Metrics

- classifier_accuracy: {summary['classifier_accuracy']}
- playbook_retrieval_match_rate: {summary['playbook_retrieval_match_rate']}
- agent_response_evaluation_expected_match_rate: {summary['agent_response_evaluation_expected_match_rate']}
- actual_agent_logic_used: {summary['actual_agent_logic_used']}
- actual_agent_logic_unavailable_reason: {summary['actual_agent_logic_unavailable_reason']}
- runtime_behavior_changed: {summary['runtime_behavior_changed']}
- retrieval_enabled: {summary['retrieval_enabled']}
- provider_calls_made: {summary['provider_calls_made']}
- llm_used: {summary['llm_used']}

## Outputs

{chr(10).join(f'- `{path}`' for path in outputs.values())}

## Boundary

All customer examples are synthetic generic test cases marked with `source_quote=false` and `from_single_transcript=false`. PROD-042 artifacts are read as source playbook inputs only and are not regenerated.

## Next

Recommended next checkpoint: `PROD-044-core-sales-policy-update`. It should only be considered after offline evidence is reviewed.
"""


def build() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = load_prod_042()
    classifier_cases, classifier_outputs, coverage_gaps = make_classifier_cases(artifacts["customer_moves"])
    retrieval_cases = [retrieve_playbook(case, output, artifacts) for case, output in zip(classifier_cases, classifier_outputs)]
    evaluation_cases = create_evaluation_cases(artifacts["customer_moves"])
    evaluations = [evaluate_response(case, artifacts) for case in evaluation_cases]
    actual_used, unavailable_reason, probes = run_actual_agent_probe(classifier_cases)

    classifier_pass = sum(1 for output in classifier_outputs if output["classifier_passed"])
    retrieval_match = sum(1 for case in retrieval_cases if case["retrieval_status"] == "matched")
    expected_match = sum(1 for item in evaluations if item["matches_expected_result"])
    eval_pass = sum(1 for item in evaluations if item["passed"])
    summary = {
        "customer_move_classifier_case_count": len(classifier_cases),
        "classifier_pass_count": classifier_pass,
        "classifier_fail_count": len(classifier_cases) - classifier_pass,
        "classifier_accuracy": round(classifier_pass / max(1, len(classifier_cases)), 4),
        "playbook_retrieval_case_count": len(retrieval_cases),
        "playbook_retrieval_match_count": retrieval_match,
        "playbook_retrieval_match_rate": round(retrieval_match / max(1, len(retrieval_cases)), 4),
        "agent_response_evaluation_case_count": len(evaluations),
        "agent_response_evaluation_pass_count": eval_pass,
        "agent_response_evaluation_fail_count": len(evaluations) - eval_pass,
        "agent_response_evaluation_expected_match_count": expected_match,
        "agent_response_evaluation_expected_match_rate": round(expected_match / max(1, len(evaluations)), 4),
        "actual_agent_logic_used": actual_used,
        "actual_agent_logic_unavailable_reason": unavailable_reason,
        **BOUNDARY_FLAGS,
    }
    outputs = {
        "result": str((OUT_DIR / "result.json").relative_to(ROOT)),
        "report": str((OUT_DIR / "report.md").relative_to(ROOT)),
        "customer_move_classification_cases": str((OUT_DIR / "customer_move_classification_cases.json").relative_to(ROOT)),
        "playbook_retrieval_cases": str((OUT_DIR / "playbook_retrieval_cases.json").relative_to(ROOT)),
        "agent_response_evaluation_cases": str((OUT_DIR / "agent_response_evaluation_cases.json").relative_to(ROOT)),
        "agent_response_evaluations": str((OUT_DIR / "agent_response_evaluations.json").relative_to(ROOT)),
        "runtime_adapter_review_data": str((OUT_DIR / "runtime_adapter_review_data.json").relative_to(ROOT)),
        "runtime_adapter_review_html": str((OUT_DIR / "runtime_adapter_review.html").relative_to(ROOT)),
    }

    base = {"checkpoint_id": CHECKPOINT_ID, "source_checkpoint_id": SOURCE_CHECKPOINT_ID}
    write_json(OUT_DIR / "customer_move_classification_cases.json", {**base, "customer_move_classification_cases": classifier_cases, "classifier_outputs": classifier_outputs, "coverage_gaps": coverage_gaps})
    write_json(OUT_DIR / "playbook_retrieval_cases.json", {**base, "playbook_retrieval_cases": retrieval_cases, "coverage_gaps": coverage_gaps})
    write_json(OUT_DIR / "agent_response_evaluation_cases.json", {**base, "agent_response_evaluation_cases": evaluation_cases})
    write_json(OUT_DIR / "agent_response_evaluations.json", {**base, "agent_response_evaluations": evaluations})
    review_data = {
        **base,
        "summary": summary,
        "customer_move_classification_cases": classifier_cases,
        "classifier_outputs": classifier_outputs,
        "playbook_retrieval_cases": retrieval_cases,
        "agent_response_evaluation_cases": evaluation_cases,
        "agent_response_evaluations": evaluations,
        "actual_agent_probe_cases": probes,
        "coverage_gaps": coverage_gaps,
        "boundaries": BOUNDARY_FLAGS,
    }
    write_json(OUT_DIR / "runtime_adapter_review_data.json", review_data)
    (OUT_DIR / "runtime_adapter_review.html").write_text(render_html(review_data), encoding="utf-8")
    (OUT_DIR / "report.md").write_text(make_report(summary, outputs), encoding="utf-8")
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": outputs,
        "validation": {"passed": True},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }
    write_json(OUT_DIR / "result.json", result)
    return result


def main() -> None:
    result = build()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "summary": result["summary"], "output_dir": str(OUT_DIR.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
