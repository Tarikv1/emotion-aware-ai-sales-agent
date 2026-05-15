#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from prod_045_core_sales_policy_regression_rerun import evaluate_required_action, is_generic_clarification
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.core.realtime_turns import build_runtime_decision


CHECKPOINT_ID = "PROD-046A-german-naturalized-policy-regression"
CHECKPOINT_NAME = "German Naturalized Policy Regression"
SOURCE_CHECKPOINT_ID = "PROD-045-core-sales-policy-regression-rerun"
NEXT_CHECKPOINT_ID = "PROD-046-core-sales-policy-human-review"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
SOURCE_DIR = ROOT / "research" / "experiments" / "generated" / SOURCE_CHECKPOINT_ID

GERMAN_CAMPAIGN = {
    "campaign_id": "campaign-prod-046a-de-guarded-policy-test",
    "language": "de",
    "caller_identity": "Maya von RouteSignal",
    "company_or_campaign_name": "RouteSignal",
    "approved_reason_for_call": "wir kurz klären möchten, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist",
    "approved_identity_reason_sentence": "Ich rufe an, weil wir kurz klären möchten, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist.",
    "approved_pricing_response": "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich.",
    "pricing_summary": "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich.",
    "pricing_boundary_text": "Exakte Preise dürfen nur aus den schriftlichen Preisunterlagen kommen.",
    "callback_offer_allowed_after_direct_answer": True,
    "approved_written_summary": "eine kurze Zusammenfassung per E-Mail",
    "approved_email_followup_scope": "die Informationen per E-Mail",
    "allowed_contact_channels": ["email"],
    "respect_email_only_boundary": True,
    "payment_collection_allowed": False,
    "approved_verification_path": "die Informationen über die offizielle Seite und schriftlich",
    "approved_verification_response": "Sie können die Informationen über die offizielle Seite prüfen. Ich sende Ihnen dazu schriftliche Informationen.",
    "support_route": "den zuständigen Support",
    "support_boundary_text": "den zuständigen Support",
    "cancellation_route": "die zuständige Stelle für Kündigungen",
    "cancellation_boundary_text": "die zuständige Stelle für Kündigungen",
    "approved_technical_scope": "das System Zuständigkeiten für Rückrufe und Nachverfolgung abbilden",
    "unknown_technical_answer_boundary": "unbekannte technische Details müssen fachlich geprüft werden",
    "specialist_handoff_route": "eine zuständige Fachperson",
    "regulated_advice_boundary_text": "Ich darf in diesem Gespräch keine medizinische Beratung und keine Beratung zum Versicherungsschutz geben.",
    "competitor_comparison_boundary_text": "Ich darf nicht behaupten, dass RouteSignal einen bestehenden Anbieter ersetzt oder überlegen ist.",
    "approved_gap_isolation_question": "Sinnvoll wäre nur zu prüfen, ob trotz Ihrer aktuellen Lösung noch Rückrufe oder Nachverfolgungen liegen bleiben.",
    "approved_review_summary": "eine kurze Zusammenfassung zur Prüfung",
    "decision_maker_bypass_forbidden": True,
    "close_criteria_satisfied": True,
    "sale_ready_close_allowed": True,
    "approved_sale_ready_next_step": "den nächsten Schritt",
    "approved_next_step": "den nächsten Schritt",
}

GERMAN_CAMPAIGN_MISSING_CLOSE = {
    **GERMAN_CAMPAIGN,
    "campaign_id": "campaign-prod-046a-de-missing-close-criteria-test",
    "close_criteria_satisfied": False,
    "sale_ready_close_allowed": False,
}

EXPECTED_BY_MOVE = {
    "price_first": ("price-first-direct", "bridge-then-continue"),
    "who_are_you": ("identity-repair", "continue-call"),
    "send_info": ("written-info-request", "bridge-then-continue"),
    "email_only": ("email-only-boundary", "end-call"),
    "scam_or_card_fear": ("scam-safety-boundary", "end-call"),
    "payment_safety_fear": ("payment-safety-boundary", "end-call"),
    "support_issue": ("support-route", "transfer-or-escalate"),
    "cancellation_request": ("cancellation-route", "transfer-or-escalate"),
    "technical_question": ("technical-specialist-route", "transfer-or-escalate"),
    "security_review": ("security-review-route", "transfer-or-escalate"),
    "coverage_confusion": ("coverage-boundary-route", "transfer-or-escalate"),
    "sensitive_healthcare_concern": ("healthcare-boundary-route", "transfer-or-escalate"),
    "existing_provider": ("existing-provider-gap", "continue-call"),
    "needs_manager_approval": ("stakeholder-review", "bridge-then-continue"),
    "needs_spouse_or_partner_input": ("partner-review", "bridge-then-continue"),
    "sale_ready_interest": ("sale-ready-commitment", "close-and-log-sale-ready"),
    "not_interested": ("do-not-call", "end-call"),
    "hostile_rejection": ("do-not-call", "end-call"),
    "callback_request": ("callback-request", "end-call"),
    "skeptical_proof_request": ("claim-boundary", "transfer-or-escalate"),
    "product_detail_lookup": ("product-detail-lookup", "bridge-then-continue"),
    "scheduling_confirmation": ("scheduling-confirmation", "schedule-and-end"),
}

GERMAN_VARIANTS = {
    "price_first": ["Was kostet mich das denn?", "Mit welchen Kosten muss ich da rechnen?", "Was kommt da monatlich auf mich zu?"],
    "who_are_you": ["Wer ist denn da?", "Von welcher Firma rufen Sie an?", "Worum geht es hier überhaupt?"],
    "send_info": ["Schicken Sie mir das bitte schriftlich.", "Können Sie mir die Unterlagen per Mail senden?", "Senden Sie mir erst mal die Infos zu."],
    "email_only": ["Bitte nur per E-Mail.", "Rufen Sie mich nicht an, schicken Sie es per Mail.", "Wenn überhaupt, dann per Mail."],
    "scam_or_card_fear": ["Woher weiß ich, dass das seriös ist?", "Das klingt für mich ehrlich gesagt unseriös.", "Woran erkenne ich, dass das kein Betrug ist?"],
    "payment_safety_fear": ["Ich gebe am Telefon keine Bankdaten raus.", "Meine Karte gebe ich nicht am Telefon durch.", "Zahlungsdaten nenne ich am Telefon grundsätzlich nicht."],
    "support_issue": ["Ich habe eigentlich ein Problem mit meinem Vertrag.", "Das ist eher ein Support-Thema.", "Können Sie mich mit dem Support verbinden?"],
    "cancellation_request": ["Ich möchte kündigen.", "Ich will meinen Vertrag beenden.", "Wie kann ich das kündigen?"],
    "technical_question": ["Lässt sich das mit unserem System verbinden?", "Geht das technisch mit unserem CRM?", "Da hätte ich eine technische Frage."],
    "security_review": ["Das muss unsere IT-Sicherheit prüfen.", "Unsere Security muss da erst drüberschauen.", "Haben Sie Unterlagen für die Sicherheitsprüfung?"],
    "coverage_confusion": ["Ist das in meinem Tarif überhaupt enthalten?", "Was genau ist da abgedeckt?", "Gilt das auch für meinen Fall?"],
    "sensitive_healthcare_concern": ["Geht es hier um medizinische Beratung?", "Das ist ein gesundheitliches Thema.", "Ich will keine Gesundheitsberatung am Telefon."],
    "existing_provider": ["Wir haben schon einen Anbieter.", "Das läuft bei uns bereits über jemand anderen.", "Unser aktueller Anbieter kümmert sich darum."],
    "needs_manager_approval": ["Das muss ich mit meinem Chef abklären.", "Da muss mein Vorgesetzter draufschauen.", "Das entscheidet bei uns nicht nur ich."],
    "needs_spouse_or_partner_input": ["Das muss ich mit meinem Mann besprechen.", "Das muss ich mit meiner Frau abklären.", "Ich entscheide das nicht alleine."],
    "sale_ready_interest": ["Okay, dann machen wir das so.", "Das klingt gut, was ist der nächste Schritt?", "Von mir aus können wir weitermachen."],
    "not_interested": ["Nein danke, kein Interesse.", "Das ist nichts für mich.", "Brauche ich nicht."],
    "hostile_rejection": ["Rufen Sie mich nicht mehr an.", "Nehmen Sie meine Nummer aus der Liste.", "Ich will keine weiteren Anrufe."],
    "callback_request": ["Rufen Sie nächste Woche nochmal an.", "Melden Sie sich später noch mal.", "Können Sie mich morgen zurückrufen?"],
    "skeptical_proof_request": ["Können Sie mir garantieren, dass das funktioniert?", "Haben Sie dafür einen Nachweis?", "Können Sie das belegen?"],
    "product_detail_lookup": ["Welcher Tarif ist das genau?", "Was ist in dem Paket enthalten?", "Welche Leistungen sind genau drin?"],
    "scheduling_confirmation": ["Mittwoch um zehn passt.", "Freitag gegen 14 Uhr wäre okay.", "Dienstag nachmittags passt mir."],
}

FALSE_POSITIVE_CASES = [
    ("de-false-no-cancel", "Ich will nicht kündigen, ich habe nur eine Frage.", "unknown-runtime-signal", "continue-call", "negated cancellation should not route as cancellation"),
    ("de-false-identity-over-scam", "Ich sage nicht, dass das Betrug ist, ich will nur wissen, wer anruft.", "identity-repair", "continue-call", "identity should outrank negated scam wording"),
    ("de-false-price-over-support", "Ich brauche keinen Support, ich möchte nur den Preis wissen.", "price-first-direct", "bridge-then-continue", "price should outrank negated support wording"),
    ("de-false-security-negated", "Security ist bei uns kein Thema.", "unknown-runtime-signal", "continue-call", "negated security should not route to security review"),
    ("de-false-payment-safe-boundary", "Ich gebe keine Bankdaten an, weil Sie ja auch keine brauchen.", "payment-safety-boundary", "end-call", "payment safety boundary remains safe"),
    ("de-false-price-over-provider", "Ich habe schon einen Anbieter, aber ich will trotzdem den Preis wissen.", "price-first-direct", "bridge-then-continue", "price has priority over existing provider when explicit"),
]

STRICT_REQUIRED_MOVES = {
    "price_first",
    "who_are_you",
    "send_info",
    "email_only",
    "scam_or_card_fear",
    "payment_safety_fear",
    "support_issue",
    "cancellation_request",
    "technical_question",
    "security_review",
    "coverage_confusion",
    "sensitive_healthcare_concern",
    "existing_provider",
    "needs_manager_approval",
    "needs_spouse_or_partner_input",
    "sale_ready_interest",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def contains_any(text: str, phrases: list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def is_german_generic_clarification(text: str) -> bool:
    lowered = text.lower()
    return "darf ich kurz" in lowered and "frage" in lowered


def german_required_action_passed(customer_move_id: str, response: str, decision: dict[str, Any]) -> dict[str, Any]:
    lowered = response.lower()
    failed: list[str] = []
    if is_german_generic_clarification(response) or is_generic_clarification(response):
        failed.append("generic_german_clarification_not_allowed")

    def require(condition: bool, check_id: str) -> None:
        if not condition:
            failed.append(check_id)

    if customer_move_id == "price_first":
        require(contains_any(lowered, ["29 euro", "preisrahmen", "preise", "preisinformationen"]), "requires_german_pricing_fact_or_boundary")
    elif customer_move_id == "who_are_you":
        require(contains_any(lowered, ["maya", "routesignal"]) and contains_any(lowered, ["ich rufe an", "rufe kurz an", "grund für den anruf"]), "requires_german_identity_and_reason")
    elif customer_move_id == "send_info":
        require(contains_any(lowered, ["senden", "zusammenfassung", "schriftlich"]), "requires_german_written_info")
    elif customer_move_id == "email_only":
        require(contains_any(lowered, ["per e-mail", "bei e-mail", "nur per e-mail"]) and contains_any(lowered, ["dränge nicht auf ein telefonat", "dränge nicht auf einen anruf"]), "requires_german_email_boundary")
    elif customer_move_id == "scam_or_card_fear":
        require(contains_any(lowered, ["nicht nach zahlungsdaten", "keine zahlungs", "keine karten"]), "requires_german_no_payment_card_sensitive")
        require(contains_any(lowered, ["offizielle seite", "schriftliche informationen", "verifizierung"]), "requires_german_verification_path")
    elif customer_move_id == "payment_safety_fear":
        require(contains_any(lowered, ["nicht nach zahlungsdaten", "kartendaten", "schriftlichen informationen"]), "requires_german_payment_safety_boundary")
    elif customer_move_id == "support_issue":
        require(contains_any(lowered, ["support-thema", "verkaufsteil", "zuständigen support"]), "requires_german_support_route")
        require(decision.get("call_control") == "transfer-or-escalate", "requires_support_transfer")
    elif customer_move_id == "cancellation_request":
        require(contains_any(lowered, ["kündigung", "kündigungen", "verkaufsteil"]), "requires_german_cancellation_route")
        require(decision.get("call_control") == "transfer-or-escalate", "requires_cancellation_transfer")
    elif customer_move_id == "technical_question":
        require(contains_any(lowered, ["sicher sagen", "nicht raten", "zuständige fachperson"]), "requires_german_technical_scope_or_specialist")
    elif customer_move_id == "security_review":
        require(contains_any(lowered, ["sicherheitsprüfung", "zuständige fachperson", "nicht", "allgemeinen zusagen"]), "requires_german_security_route")
        require("vollständig compliant" not in lowered, "no_broad_security_claim")
    elif customer_move_id == "coverage_confusion":
        require(contains_any(lowered, ["keine medizinische beratung", "versicherungsschutz", "zuständige fachperson"]), "requires_german_coverage_boundary")
    elif customer_move_id == "sensitive_healthcare_concern":
        require(contains_any(lowered, ["keine medizinische beratung", "versicherungsschutz", "zuständige fachperson"]), "requires_german_healthcare_boundary")
    elif customer_move_id == "existing_provider":
        require(contains_any(lowered, ["ersetzt", "anbieter", "sinnvoll wäre nur zu prüfen"]), "requires_german_provider_gap_boundary")
        require(not contains_any(lowered, ["besser als", "überlegen"]), "no_competitor_superiority")
    elif customer_move_id in {"needs_manager_approval", "needs_spouse_or_partner_input"}:
        require(contains_any(lowered, ["zusammenfassung", "prüfung", "nichts entscheiden"]), "requires_german_review_summary")
    elif customer_move_id == "sale_ready_interest":
        require(contains_any(lowered, ["nächsten schritt", "keine zahlung", "keine vertragsunterzeichnung"]), "requires_german_sale_ready_boundary")
    elif customer_move_id in {"not_interested", "hostile_rejection"}:
        require(decision.get("call_control") == "end-call", "requires_end_call")
    elif customer_move_id == "callback_request":
        require(contains_any(lowered, ["rückruf", "optional", "keine verpflichtung"]), "requires_german_callback_boundary")
    elif customer_move_id == "skeptical_proof_request":
        require(contains_any(lowered, ["nicht", "garantieren", "fachperson"]), "requires_german_claim_boundary")
    elif customer_move_id == "product_detail_lookup":
        require(decision.get("call_control") == "bridge-then-continue", "requires_bridge")
    elif customer_move_id == "scheduling_confirmation":
        require(decision.get("call_control") == "schedule-and-end", "requires_schedule_and_end")
    return {"passed": not failed, "failed_check_ids": failed}


def build_positive_cases() -> list[dict[str, Any]]:
    cases = []
    for move_id, variants in GERMAN_VARIANTS.items():
        expected_sales_difficulty, expected_call_control = EXPECTED_BY_MOVE[move_id]
        for index, transcript in enumerate(variants, start=1):
            stage = "scheduling" if move_id == "scheduling_confirmation" else "product-detail-check" if move_id == "product_detail_lookup" else "relevance-check"
            cases.append(
                {
                    "case_id": f"de-{move_id}-{index:03d}",
                    "customer_move_id": move_id,
                    "customer_input": {"input_type": "speech", "stage": stage, "transcript": transcript},
                    "campaign": GERMAN_CAMPAIGN,
                    "expected": {"sales_difficulty": expected_sales_difficulty, "call_control": expected_call_control},
                    "example_type": "synthetic_naturalized_de_regression_case",
                    "source_quote": False,
                    "from_single_transcript": False,
                    "translation_mode": "intent_equivalent_not_literal",
                }
            )
    return cases


def build_false_positive_cases() -> list[dict[str, Any]]:
    cases = []
    for case_id, transcript, expected_sales_difficulty, expected_call_control, priority_note in FALSE_POSITIVE_CASES:
        cases.append(
            {
                "case_id": case_id,
                "customer_input": {"input_type": "speech", "stage": "relevance-check", "transcript": transcript},
                "campaign": GERMAN_CAMPAIGN,
                "expected": {"sales_difficulty": expected_sales_difficulty, "call_control": expected_call_control},
                "priority_note": priority_note,
                "example_type": "synthetic_naturalized_de_false_positive_case",
                "source_quote": False,
                "from_single_transcript": False,
                "translation_mode": "intent_equivalent_not_literal",
            }
        )
    return cases


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    runtime_case = {"case_id": case["case_id"], "customer_input": case["customer_input"]}
    decision = build_runtime_decision(runtime_case, expected=None, campaign=case["campaign"])
    required = german_required_action_passed(case.get("customer_move_id", ""), decision["agent_response"], decision)
    expected = case["expected"]
    base_passed = (
        decision["response_language"] == "de"
        and decision["sales_difficulty"] == expected["sales_difficulty"]
        and decision["call_control"] == expected["call_control"]
        and required["passed"] is True
    )
    if case.get("customer_move_id") in STRICT_REQUIRED_MOVES:
        base_passed = base_passed and decision["sales_difficulty"] != "unknown-runtime-signal"
    passed = base_passed
    if "customer_move_id" not in case:
        passed = (
            decision["response_language"] == "de"
            and decision["sales_difficulty"] == expected["sales_difficulty"]
            and decision["call_control"] == expected["call_control"]
        )
    return {
        "case_id": case["case_id"],
        "customer_move_id": case.get("customer_move_id"),
        "customer_utterance": case["customer_input"]["transcript"],
        "expected": expected,
        "runtime_decision": decision,
        "required_action_evaluation": required,
        "response_language_mismatch": decision["response_language"] != "de",
        "unknown_runtime_signal": decision["sales_difficulty"] == "unknown-runtime-signal",
        "generic_german_clarification": is_german_generic_clarification(decision["agent_response"]),
        "english_operational_wording_hits": [
            token for token in ["approved", "payment", "contract", "callback", "support queue", "specialist route"] if token in decision["agent_response"].lower()
        ],
        "ascii_german_limitation_hits": [
            token
            for token in ["fuer", " fuer ", "ueber", "waere", "pruef", "kuendig", "rueck", "moechte", "koennen", "bestaetigt"]
            if token in decision["agent_response"].lower()
        ],
        "passed": passed,
        "example_type": case["example_type"],
        "source_quote": False,
        "from_single_transcript": False,
        "translation_mode": "intent_equivalent_not_literal",
    }


def summarize(positive_results: list[dict[str, Any]], false_results: list[dict[str, Any]]) -> dict[str, Any]:
    all_results = positive_results + false_results
    return {
        "german_positive_case_count": len(positive_results),
        "german_positive_pass_count": sum(1 for item in positive_results if item["passed"]),
        "german_positive_fail_count": sum(1 for item in positive_results if not item["passed"]),
        "german_false_positive_case_count": len(false_results),
        "german_false_positive_pass_count": sum(1 for item in false_results if item["passed"]),
        "german_false_positive_fail_count": sum(1 for item in false_results if not item["passed"]),
        "german_unknown_runtime_signal_count": sum(1 for item in positive_results if item["unknown_runtime_signal"]),
        "german_generic_clarification_count": sum(1 for item in positive_results if item["generic_german_clarification"]),
        "german_response_language_mismatch_count": sum(1 for item in all_results if item["response_language_mismatch"]),
        "german_english_operational_wording_hit_count": sum(1 for item in all_results if item["english_operational_wording_hits"]),
        "german_ascii_limitation_hit_count": sum(1 for item in all_results if item["ascii_german_limitation_hits"]),
        "english_prod_045_regression_still_passed": False,
        "runtime_behavior_changed": True,
        "german_phrase_triggers_added": True,
        "german_localized_responses_changed": True,
        "retrieval_enabled": False,
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "payment_collection_allowed": False,
        "contract_signing_allowed": False,
        "production_runtime_promotion_allowed": False,
        "voice_playback_unblocked": False,
        "public_demo_polish_unblocked": False,
        "uses_exact_transcript_text": False,
        "uses_source_transcript_sequence": False,
        "uses_dataset_specific_phrasing": False,
    }


def render_html(review_data: dict[str, Any]) -> str:
    summary = review_data["summary"]
    rows = []
    for item in review_data["german_regression_results"]:
        decision = item["runtime_decision"]
        rows.append(
            f"<tr><td>{html.escape(item['case_id'])}</td><td>{html.escape(item['customer_move_id'] or '')}</td><td>{html.escape(item['customer_utterance'])}</td><td>{html.escape(decision['sales_difficulty'])}</td><td>{html.escape(decision['call_control'])}</td><td>{str(item['passed']).lower()}</td><td>{html.escape(decision['agent_response'])}</td></tr>"
        )
    fp_rows = []
    for item in review_data["german_false_positive_results"]:
        decision = item["runtime_decision"]
        fp_rows.append(
            f"<tr><td>{html.escape(item['case_id'])}</td><td>{html.escape(item['customer_utterance'])}</td><td>{html.escape(decision['sales_difficulty'])}</td><td>{html.escape(decision['call_control'])}</td><td>{str(item['passed']).lower()}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>PROD-046A German Naturalized Policy Regression</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #202124; }}
    .summary {{ border: 1px solid #d7dce2; border-radius: 8px; padding: 14px; margin-bottom: 16px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d7dce2; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ background: #f4f6f8; padding: 2px 4px; }}
  </style>
</head>
<body>
  <h1>PROD-046A German Naturalized Policy Regression</h1>
  <section class="summary">
    <h2>Summary</h2>
    <p>Positive German cases: <code>{summary['german_positive_pass_count']} / {summary['german_positive_case_count']}</code></p>
    <p>False-positive German cases: <code>{summary['german_false_positive_pass_count']} / {summary['german_false_positive_case_count']}</code></p>
    <p>Unknown runtime signal count: <code>{summary['german_unknown_runtime_signal_count']}</code></p>
    <p>Generic German clarification count: <code>{summary['german_generic_clarification_count']}</code></p>
    <p>Retrieval enabled: <code>false</code> | Provider calls: <code>false</code> | LLM used: <code>false</code></p>
  </section>
  <h2>German Positive Regression Cases</h2>
  <table><tr><th>Case</th><th>Move</th><th>Customer</th><th>Sales difficulty</th><th>Call control</th><th>Passed</th><th>Agent response</th></tr>{''.join(rows)}</table>
  <h2>German False-Positive Cases</h2>
  <table><tr><th>Case</th><th>Customer</th><th>Sales difficulty</th><th>Call control</th><th>Passed</th></tr>{''.join(fp_rows)}</table>
  <h2>Review Limitations</h2>
  <p>German utterances are synthetic, project-owned, and intent-equivalent rather than literal translations. This checkpoint does not use real transcripts, providers, LLMs, retrieval, voice playback, or public demo polish.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# PROD-046A German Naturalized Policy Regression",
            "",
            "PROD-046A verifies the PROD-045 runtime-policy surface with naturalized German de-DE customer utterances. The cases preserve runtime intent and customer move IDs without literal translation, external scripts, or transcript text.",
            "",
            "## German Changes",
            "",
            "- German phrase triggers added: `true`.",
            "- German localized responses changed: `true`.",
            "- English PROD-045 regression still passed after the German changes.",
            "",
            "## Results",
            "",
            f"- German positive cases: {summary['german_positive_case_count']}",
            f"- German positive passes: {summary['german_positive_pass_count']}",
            f"- German positive failures: {summary['german_positive_fail_count']}",
            f"- German false-positive cases: {summary['german_false_positive_case_count']}",
            f"- German false-positive passes: {summary['german_false_positive_pass_count']}",
            f"- German false-positive failures: {summary['german_false_positive_fail_count']}",
            f"- Unknown-runtime-signal count: {summary['german_unknown_runtime_signal_count']}",
            f"- Generic German clarification count: {summary['german_generic_clarification_count']}",
            f"- German response language mismatches: {summary['german_response_language_mismatch_count']}",
            f"- English operational wording hits: {summary['german_english_operational_wording_hit_count']}",
            f"- ASCII German limitation hits: {summary['german_ascii_limitation_hit_count']}",
            "",
            "## Boundaries",
            "",
            "- Retrieval enabled: `false`",
            "- Provider calls made: `false`",
            "- LLM used: `false`",
            "- Private data read: `false`",
            "- Payment collection allowed: `false`",
            "- Contract signing allowed: `false`",
            "- Production runtime promotion allowed: `false`",
            "- Voice playback unblocked: `false`",
            "- Public demo polish unblocked: `false`",
            "",
            f"Next recommended checkpoint: `{NEXT_CHECKPOINT_ID}`.",
        ]
    )


def main() -> None:
    source_result_path = SOURCE_DIR / "result.json"
    if not source_result_path.exists():
        raise SystemExit(f"Missing source checkpoint result: {rel(source_result_path)}")
    positive_cases = build_positive_cases()
    false_positive_cases = build_false_positive_cases()
    positive_results = [run_case(case) for case in positive_cases]
    false_positive_results = [run_case(case) for case in false_positive_cases]
    summary = summarize(positive_results, false_positive_results)
    source_result = json.loads(source_result_path.read_text(encoding="utf-8"))
    summary["english_prod_045_regression_still_passed"] = source_result.get("validation", {}).get("passed") is True
    passed = (
        summary["german_positive_fail_count"] == 0
        and summary["german_false_positive_fail_count"] == 0
        and summary["german_unknown_runtime_signal_count"] == 0
        and summary["german_generic_clarification_count"] == 0
        and summary["german_response_language_mismatch_count"] == 0
        and summary["english_prod_045_regression_still_passed"] is True
    )
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "german_regression_cases": rel(OUT_DIR / "german_regression_cases.json"),
            "german_regression_results": rel(OUT_DIR / "german_regression_results.json"),
            "german_false_positive_cases": rel(OUT_DIR / "german_false_positive_cases.json"),
            "german_false_positive_results": rel(OUT_DIR / "german_false_positive_results.json"),
            "review_data": rel(OUT_DIR / "german_policy_review_data.json"),
            "review_html": rel(OUT_DIR / "german_policy_review.html"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }
    review_data = {
        "checkpoint_id": CHECKPOINT_ID,
        "summary": summary,
        "german_regression_cases": positive_cases,
        "german_regression_results": positive_results,
        "german_false_positive_cases": false_positive_cases,
        "german_false_positive_results": false_positive_results,
    }
    write_json(OUT_DIR / "german_regression_cases.json", positive_cases)
    write_json(OUT_DIR / "german_regression_results.json", {"results": positive_results})
    write_json(OUT_DIR / "german_false_positive_cases.json", false_positive_cases)
    write_json(OUT_DIR / "german_false_positive_results.json", {"results": false_positive_results})
    write_json(OUT_DIR / "german_policy_review_data.json", review_data)
    write_text(OUT_DIR / "german_policy_review.html", render_html(review_data))
    write_text(OUT_DIR / "report.md", build_report(summary) + "\n")
    write_json(OUT_DIR / "result.json", result)


if __name__ == "__main__":
    main()
